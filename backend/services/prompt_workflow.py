from __future__ import annotations

import json
from typing import Any

from backend.config import AppConfig
from backend.constants import (
    ACTIVE_ROLES,
    GENERATION_MODE_IDS,
    GENERIC_MODE_IDS,
    GENERIC_REFERENCE_LABEL_TEMPLATE,
    GENERIC_REFERENCE_ROLE,
    IMAGE_MIME_ALLOWLIST,
    MAX_GENERIC_REFERENCE_IMAGES,
    MAX_TOTAL_IMAGE_PAYLOAD_BYTES,
    MODEL_OPTIONS_BY_VALUE,
    MODEL_WHITELIST,
    ROLE_LABELS,
    TARGET_RULES,
)
from backend.modes import REGISTRY
from backend.modes.base import ModeContext, ModeSpec, get_cached_json, strip_markdown_fence
from backend.prompts.outfit_swap import build_outfit_swap_instruction, build_timeout_recovery_instruction
from backend.services._workflow_helpers import invalid_model_output, pollinations_error, workflow_error
from backend.services.pollinations_client import PollinationsClient, PollinationsError


class OutfitSwapWorkflow:
    def __init__(self, config: AppConfig, client: PollinationsClient) -> None:
        self.config = config
        self.client = client

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        api_key = (payload.get("api_key") or self.config.pollinations_api_key or "").strip()
        model = payload.get("model") or self.config.default_model
        mode = payload.get("mode") or "outfit-swap-json"
        target_rule = payload.get("target_model_rule") or "chatgpt_img"

        if mode != "outfit-swap-json":
            return self._error("UNSUPPORTED_MODE", "Mode khong duoc ho tro cho outfit workflow.")

        if model not in MODEL_WHITELIST:
            return self._error("UNSUPPORTED_MODEL", f"Model khong duoc ho tro: {model}")

        if target_rule not in TARGET_RULES:
            return self._error("UNSUPPORTED_TARGET", f"Dich khong hop le: {target_rule}")

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
                    return pollinations_error(recovery_exc)
            else:
                return pollinations_error(exc)
        finally:
            if custom_relay_endpoint.startswith(("http://", "https://")):
                self.client = original_client

        validation = self._validate_output(output)
        if validation:
            return validation

        return {
            "ok": True,
            "mode": "outfit_swap",
            "kind": "outfit",
            "models": {"prompt_builder": model},
            "warnings": [],
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
            return {"ok": True, "message": "API key hoat dong."}
        except PollinationsError as exc:
            return pollinations_error(exc)

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
            raise ValueError("Thieu anh bat buoc cho outfit_swap: " + ", ".join(missing))

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
            raise ValueError("Payload anh qua lon. Hay giam kich thuoc anh hoac dung it anh hon.")

        required_roles = {image["role"] for image in accepted}
        if "model" not in required_roles or "outfit" not in required_roles:
            raise ValueError("Payload anh qua lon khien anh model/outfit khong duoc gui. Hay giam kich thuoc anh.")
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
                    "message": "API tra output thieu section bat buoc: " + ", ".join(missing),
                    "raw_output": output,
                },
            }
        return None

    @staticmethod
    def _error(code: str, message: str) -> dict[str, Any]:
        return workflow_error(code, message)


class GenericModeWorkflow:
    def __init__(self, config: AppConfig, client: PollinationsClient, registry: dict[str, ModeSpec]) -> None:
        self.config = config
        self.client = client
        self.registry = registry

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        api_key = (payload.get("api_key") or self.config.pollinations_api_key or "").strip()
        mode_id = payload.get("mode") or ""
        model = payload.get("model") or self.config.default_model

        if model not in MODEL_WHITELIST:
            return self._error("UNSUPPORTED_MODEL", f"Model khong duoc ho tro: {model}")
        spec = self.registry.get(mode_id)
        if spec is None:
            return self._error("UNSUPPORTED_MODE", f"Mode khong ho tro: {mode_id}")

        selected_model_meta = dict(MODEL_OPTIONS_BY_VALUE[model])
        references, warnings = self._normalize_generic_references(
            payload.get("images") or [],
            allow_images=spec.allow_images,
            model_supports_images=bool(selected_model_meta.get("supports_images")),
        )
        limited_references, trim_warning = self._limit_payload_generic(references)
        if trim_warning:
            warnings.append(trim_warning)

        ctx = self._build_context(payload, selected_model_meta, limited_references, spec, bool(references) and not limited_references)
        instruction = spec.build_instruction(ctx)
        body = self._build_request_body(model, instruction, limited_references, spec)

        custom_relay_endpoint = (payload.get("custom_relay_endpoint") or "").strip()
        original_client = self.client
        if custom_relay_endpoint.startswith(("http://", "https://")):
            endpoints = (custom_relay_endpoint, *self.config.pollinations_endpoints)
            self.client = PollinationsClient(endpoints, self.config.request_timeout_seconds)

        try:
            output = self.client.chat_completion(api_key, body)
        except PollinationsError as exc:
            if exc.status == 504:
                compact_body = self._build_request_body(model, "BE CONCISE. Use minimum tokens to deliver a valid result.\n\n" + instruction, limited_references, spec)
                compact_body["max_tokens"] = max(1024, int(spec.max_output_tokens * 0.6))
                try:
                    output = self.client.chat_completion(api_key, compact_body)
                except PollinationsError as compact_exc:
                    return pollinations_error(compact_exc)
            else:
                return pollinations_error(exc)
        finally:
            if custom_relay_endpoint.startswith(("http://", "https://")):
                self.client = original_client

        output_clean = strip_markdown_fence(output)
        repaired = False
        validation_error = spec.validate_output(output_clean)
        if validation_error:
            repaired = True
            repair_instruction = self._build_repair_instruction(instruction, validation_error)
            repair_body = self._build_request_body(model, repair_instruction, limited_references, spec)
            try:
                output = self.client.chat_completion(api_key, repair_body)
            except PollinationsError as exc:
                return pollinations_error(exc)
            output_clean = strip_markdown_fence(output)
            validation_error = spec.validate_output(output_clean)
            if validation_error:
                return invalid_model_output(validation_error)

        parsed = None
        output_value = output_clean
        if spec.output_type == "json":
            parsed = get_cached_json(output_clean) or json.loads(output_clean)
            output_value = json.dumps(parsed, ensure_ascii=False, indent=2)

        return {
            "ok": True,
            "mode": mode_id,
            "kind": "generic",
            "models": {"prompt_builder": model},
            "warnings": warnings,
            "meta": {"repaired": repaired, "prompt_version": spec.prompt_version},
            "result": {
                "output_type": spec.output_type,
                "output": output_value,
                "parsed": parsed,
                "reference_count": len(limited_references),
                "reference_images_unavailable": any(warning["code"] == "IMAGES_UNAVAILABLE_FOR_MODEL" for warning in warnings),
            },
        }

    @staticmethod
    def _normalize_generic_references(
        images: list[dict[str, Any]],
        *,
        allow_images: bool,
        model_supports_images: bool,
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        uploaded = [item for item in images if item.get("dataUrl") or item.get("data_url")]
        warnings: list[dict[str, str]] = []
        if uploaded and not allow_images:
            return [], [
                {
                    "code": "IMAGES_DROPPED_FOR_TEXT_MODE",
                    "message": "Mode nay khong dung anh; anh upload da duoc bo qua.",
                }
            ]
        if uploaded and not model_supports_images:
            return [], [
                {
                    "code": "IMAGES_UNAVAILABLE_FOR_MODEL",
                    "message": "Model dang chon khong ho tro anh; app chi gui text prompt.",
                }
            ]

        references: list[dict[str, Any]] = []
        for item in uploaded[:MAX_GENERIC_REFERENCE_IMAGES]:
            data_url = item.get("dataUrl") or item.get("data_url")
            if not isinstance(data_url, str) or not data_url.startswith("data:image/"):
                continue
            mime_type = data_url.split(";", 1)[0].removeprefix("data:")
            if mime_type not in IMAGE_MIME_ALLOWLIST:
                warnings.append(
                    {
                        "code": "IMAGE_MIME_REJECTED",
                        "message": f"Bo qua anh khong ho tro: {item.get('name') or 'reference'} ({mime_type}).",
                    }
                )
                continue
            references.append(
                {
                    "role": GENERIC_REFERENCE_ROLE,
                    "name": item.get("name") or "reference",
                    "type": item.get("type") or "image/jpeg",
                    "payload_bytes": len(data_url.encode("utf-8")),
                    "data_url": data_url,
                }
            )
        if len(uploaded) > MAX_GENERIC_REFERENCE_IMAGES:
            warnings.append(
                {
                    "code": "IMAGES_TRIMMED_BY_LIMIT",
                    "message": f"Chi gui toi da {MAX_GENERIC_REFERENCE_IMAGES} anh tham chieu.",
                }
            )
        return references, warnings

    @staticmethod
    def _limit_payload_generic(references: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str] | None]:
        total = 0
        accepted: list[dict[str, Any]] = []
        for image in references:
            size = int(image["payload_bytes"])
            if total + size <= MAX_TOTAL_IMAGE_PAYLOAD_BYTES:
                accepted.append(image)
                total += size
        if len(accepted) < len(references):
            return accepted, {
                "code": "IMAGES_TRIMMED_BY_PAYLOAD",
                "message": "Mot so anh bi bo qua vi vuot gioi han payload.",
            }
        return accepted, None

    def _build_context(
        self,
        payload: dict[str, Any],
        selected_model_meta: dict[str, Any],
        references: list[dict[str, Any]],
        spec: ModeSpec,
        references_unavailable: bool,
    ) -> ModeContext:
        return ModeContext(
            user_input=payload.get("user_request") or "",
            style=payload.get("style") or "None",
            aspect_ratio=payload.get("aspect_ratio") or "1:1",
            resolution=payload.get("resolution") or "2K",
            quality=payload.get("quality") or "high",
            selected_model=selected_model_meta,
            has_reference_images=bool(references),
            reference_images_unavailable=references_unavailable,
            reference_image_count=len(references),
            reference_summary=self._reference_summary(references),
            mode_id=spec.id,
            mode_label=spec.label,
            max_output_tokens=spec.max_output_tokens,
            output_type=spec.output_type,
            prompt_version=spec.prompt_version,
        )

    @staticmethod
    def _build_request_body(model: str, instruction: str, references: list[dict[str, Any]], spec: ModeSpec) -> dict[str, Any]:
        content: list[dict[str, Any]] = [{"type": "text", "text": instruction}]
        for index, image in enumerate(references, start=1):
            content.append({"type": "text", "text": GENERIC_REFERENCE_LABEL_TEMPLATE.format(index=index)})
            content.append({"type": "image_url", "image_url": {"url": image["data_url"]}})
        return {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": spec.system_persona,
                },
                {"role": "user", "content": content},
            ],
            "temperature": spec.default_temperature,
            "max_tokens": spec.max_output_tokens,
            "stream": False,
        }

    @staticmethod
    def _reference_summary(references: list[dict[str, Any]]) -> str:
        return "\n".join(
            f"- Reference image {index}: {image['name']} ({image['type']}, {image['payload_bytes']} bytes)"
            for index, image in enumerate(references, start=1)
        )

    @staticmethod
    def _build_repair_instruction(original_instruction: str, validation_error: dict[str, Any]) -> str:
        return "\n\n".join(
            [
                original_instruction,
                "The previous response failed validation.",
                f"Validation code: {validation_error.get('code', 'INVALID_MODEL_OUTPUT')}",
                f"Validation message: {validation_error.get('message', 'Output did not match the required schema.')}",
                "Regenerate the complete artifact now. Return only the required final content, with no markdown fences and no explanation.",
            ]
        )

    @staticmethod
    def _error(code: str, message: str) -> dict[str, Any]:
        return workflow_error(code, message)


class PromptWorkflow:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._client = PollinationsClient.from_config(config)
        self.outfit = OutfitSwapWorkflow(config, self._client)
        self.generic = GenericModeWorkflow(config, self._client, REGISTRY)

    @property
    def client(self) -> PollinationsClient:
        return self._client

    @client.setter
    def client(self, value: PollinationsClient) -> None:
        self._client = value
        self.outfit.client = value
        self.generic.client = value

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        mode_id = payload.get("mode") or GENERATION_MODE_IDS["OUTFIT_SWAP"]
        if mode_id == GENERATION_MODE_IDS["OUTFIT_SWAP"]:
            return self.outfit.generate(payload)
        if mode_id in GENERIC_MODE_IDS:
            return self.generic.generate(payload)
        return self._error("UNSUPPORTED_MODE", f"Mode khong ho tro: {mode_id}")

    def test_api_key(self, api_key: str) -> dict[str, Any]:
        return self.outfit.test_api_key(api_key)

    @staticmethod
    def _error(code: str, message: str) -> dict[str, Any]:
        return workflow_error(code, message)
