from __future__ import annotations

from typing import Any

from backend.config import AppConfig
from backend.constants import (
    ACTIVE_ROLES,
    IMAGE_MIME_ALLOWLIST,
    MAX_TOTAL_IMAGE_PAYLOAD_BYTES,
    MODEL_WHITELIST,
    ROLE_LABELS,
    TARGET_RULES,
)
from backend.prompts.outfit_swap import build_outfit_swap_instruction, build_timeout_recovery_instruction
from backend.services.pollinations_client import PollinationsClient, PollinationsError


class PromptWorkflow:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.client = PollinationsClient.from_config(config)

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        api_key = (payload.get("api_key") or self.config.pollinations_api_key or "").strip()
        model = payload.get("model") or self.config.default_model
        mode = payload.get("mode") or "outfit-swap-json"
        target_rule = payload.get("target_model_rule") or "chatgpt_img"

        if mode != "outfit-swap-json":
            return self._error("UNSUPPORTED_MODE", "Hiện app ưu tiên mode outfit_swap theo yêu cầu. Các mode khác để mở rộng sau.")

        if model not in MODEL_WHITELIST:
            return self._error("UNSUPPORTED_MODEL", f"Model không được hỗ trợ: {model}")

        if target_rule not in TARGET_RULES:
            return self._error("UNSUPPORTED_TARGET", f"Đích không hợp lệ: {target_rule}")

        try:
            references = self._normalize_references(payload.get("images") or [])
            self._validate_outfit_references(references)
            limited_references = self._limit_payload(references)
        except ValueError as exc:
            return self._error("VALIDATION_ERROR", str(exc))

        context = self._build_context(payload, model, limited_references)
        instruction = build_outfit_swap_instruction(context)
        body = self._build_request_body(model, instruction, limited_references)

        custom_relay_endpoint = (payload.get("custom_relay_endpoint") or "").strip()
        original_client = self.client
        if custom_relay_endpoint.startswith(("http://", "https://")):
            endpoints = (custom_relay_endpoint, *self.config.pollinations_endpoints)
            self.client = PollinationsClient(endpoints, self.config.request_timeout_seconds)

        try:
            output = self.client.chat_completion(api_key, body)
        except PollinationsError as exc:
            if exc.status == 504:
                recovery_instruction = build_timeout_recovery_instruction(context)
                recovery_body = self._build_request_body(model, recovery_instruction, limited_references, max_tokens=2600)
                try:
                    output = self.client.chat_completion(api_key, recovery_body)
                except PollinationsError as recovery_exc:
                    return self._pollinations_error(recovery_exc)
            else:
                return self._pollinations_error(exc)
        finally:
            if custom_relay_endpoint.startswith(("http://", "https://")):
                self.client = original_client

        validation = self._validate_output(output)
        if validation:
            return validation

        return {
            "ok": True,
            "mode": "outfit_swap",
            "models": {"prompt_builder": model},
            "result": {
                "output": output,
                "final_prompt": output,
                "reference_count": len(limited_references),
            },
        }

    def test_api_key(self, api_key: str) -> dict[str, Any]:
        try:
            self.client.chat_completion(
                api_key,
                {
                    "model": self.config.default_model,
                    "messages": [
                        {"role": "system", "content": "Return only OK."},
                        {"role": "user", "content": "Say OK."},
                    ],
                    "temperature": 0,
                    "max_tokens": 8,
                    "stream": False,
                },
            )
            return {"ok": True, "message": "API key hoạt động."}
        except PollinationsError as exc:
            return self._pollinations_error(exc)

    def _build_context(self, payload: dict[str, Any], model: str, references: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "user_request": payload.get("user_request") or "",
            "style": payload.get("style") or "High-end fashion editorial",
            "aspect_ratio": payload.get("aspect_ratio") or "1:1",
            "resolution": payload.get("resolution") or "2K",
            "quality": payload.get("quality") or "high",
            "target_model_rule": payload.get("target_model_rule") or "chatgpt_img",
            "selected_model": model,
            "has_reference_images": bool(references),
            "reference_image_count": len(references),
            "reference_summary": self._reference_summary(references),
        }

    def _build_request_body(self, model: str, instruction: str, references: list[dict[str, Any]], max_tokens: int = 5000) -> dict[str, Any]:
        content: list[dict[str, Any]] = [{"type": "text", "text": instruction}]
        for image in references:
            content.append({"type": "text", "text": ROLE_LABELS[image["role"]]})
            content.append({"type": "image_url", "image_url": {"url": image["data_url"]}})

        return {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are Super Prompt, a precise prompt engineering assistant. Return only the requested artifact.",
                },
                {"role": "user", "content": content},
            ],
            "temperature": 0.35,
            "max_tokens": max_tokens,
            "stream": False,
        }

    @staticmethod
    def _normalize_references(images: list[dict[str, Any]]) -> list[dict[str, Any]]:
        references: list[dict[str, Any]] = []
        for item in images:
            role = item.get("role")
            data_url = item.get("dataUrl") or item.get("data_url")
            if not isinstance(data_url, str) or not data_url.startswith("data:image/"):
                continue
            mime_type = data_url.split(";", 1)[0].removeprefix("data:")
            if role not in ACTIVE_ROLES or mime_type not in IMAGE_MIME_ALLOWLIST:
                continue
            references.append(
                {
                    "role": role,
                    "name": item.get("name") or role,
                    "type": item.get("type") or "image/jpeg",
                    "payload_bytes": len(data_url.encode("utf-8")),
                    "data_url": data_url,
                }
            )
        return references

    @staticmethod
    def _validate_outfit_references(references: list[dict[str, Any]]) -> None:
        roles = {image["role"] for image in references}
        missing = []
        if "model" not in roles:
            missing.append("A.1 model identity")
        if "outfit" not in roles:
            missing.append("A.2 outfit")
        if missing:
            raise ValueError("Thiếu ảnh bắt buộc cho outfit_swap: " + ", ".join(missing))

    @staticmethod
    def _limit_payload(references: list[dict[str, Any]]) -> list[dict[str, Any]]:
        total = 0
        accepted: list[dict[str, Any]] = []
        for image in references:
            size = int(image["payload_bytes"])
            if total + size <= MAX_TOTAL_IMAGE_PAYLOAD_BYTES:
                accepted.append(image)
                total += size

        if not accepted:
            raise ValueError("Payload ảnh quá lớn. Hãy giảm kích thước ảnh hoặc dùng ít ảnh hơn.")

        required_roles = {image["role"] for image in accepted}
        if "model" not in required_roles or "outfit" not in required_roles:
            raise ValueError("Payload ảnh quá lớn khiến ảnh model/outfit không được gửi. Hãy giảm kích thước ảnh.")
        return accepted

    @staticmethod
    def _reference_summary(references: list[dict[str, Any]]) -> str:
        lines = []
        for image in references:
            role_name = {"model": "A.1 model identity", "outfit": "A.2 outfit", "background": "A.3 background"}.get(image["role"], image["role"])
            lines.append(f"- {role_name}: {image['name']} ({image['type']}, {image['payload_bytes']} bytes)")
        return "\n".join(lines)

    @staticmethod
    def _validate_output(output: str) -> dict[str, Any] | None:
        required = ["MAIN PROMPT:", "NEGATIVE PROMPT:", "REFERENCE BINDING INSTRUCTIONS:"]
        missing = [section for section in required if section not in output]
        if missing:
            return {
                "ok": False,
                "error": {
                    "code": "INVALID_MODEL_OUTPUT",
                    "message": "API trả output thiếu section bắt buộc: " + ", ".join(missing),
                    "raw_output": output,
                },
            }
        return None

    @staticmethod
    def _pollinations_error(exc: PollinationsError) -> dict[str, Any]:
        return {"ok": False, "error": {"code": exc.code, "message": exc.message, "status": exc.status}}

    @staticmethod
    def _error(code: str, message: str) -> dict[str, Any]:
        return {"ok": False, "error": {"code": code, "message": message}}
