from __future__ import annotations

import base64
import json
import shutil
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.config import AppConfig

CHATGPT_URL = "https://chatgpt.com/"

TEXTBOX_XPATHS = (
    '//*[@data-slate-editor="true"]',
    '//*[@contenteditable="true"]',
    '//*[@role="textbox"]',
    "//textarea",
)
FILE_INPUT_XPATHS = (
    "//input[@type='file']",
    "//button[contains(@aria-label,'Attach')]",
    "//button[contains(@aria-label,'Upload')]",
)
SEND_BUTTON_XPATHS = (
    '//*[@data-testid="send-button"]',
    "//button[@aria-label='Send prompt']",
    "//button[contains(@aria-label,'Send')]",
    "//button[contains(@aria-label,'Gửi')]",
)
UPLOAD_REQUEST_MARKERS = (
    "upload",
    "file",
    "attachment",
    "usercontent",
)
CONTENT_REQUEST_MARKERS = (
    "backend-api/estuary/content",
)
IMAGE_MAGIC_BYTES = (
    b"\x89PNG\r\n\x1a\n",
    b"\xff\xd8\xff",
    b"RIFF",
    b"GIF87a",
    b"GIF89a",
)
UPLOAD_SETTLE_SECONDS = 2.5
UPLOAD_VERIFY_TIMEOUT_SECONDS = 75
UPLOAD_POLL_SECONDS = 1.0


class ChatGptAutomationError(Exception):
    def __init__(self, code: str, message: str, *, debug_dir: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.debug_dir = debug_dir

    def to_response(self) -> dict[str, Any]:
        error: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.debug_dir:
            error["debug_dir"] = self.debug_dir
        return {"ok": False, "error": error}


class ChatGptImageAutomationService:
    def __init__(self, config: AppConfig, app_root: Path) -> None:
        self.config = config
        self.app_root = app_root
        self.tab_id = config.chromium_default_tab_id
        self.request_timeout = max(1, config.chromium_request_timeout_ms / 1000)

    def generate_image(self, payload: dict[str, Any]) -> dict[str, Any]:
        prompt_text = (payload.get("prompt_text") or "").strip()
        if not prompt_text:
            raise ChatGptAutomationError("CHATGPT_PROMPT_EMPTY", "Prompt hiện tại đang trống.")

        request_id = uuid.uuid4().hex[:12]
        handoff_dir = self.app_root / ".handoff" / "chatgpt_img2" / request_id
        image_paths = self._materialize_images(payload.get("images") or [], handoff_dir)
        debug_dir = str(handoff_dir) if handoff_dir.exists() else None

        try:
            automation_url = self._resolve_automation_url(payload)
            self._wait_automation_ready(automation_url)
            self._post_auto(automation_url, "/window/bounds", {"width": 1320, "height": 860}, timeout=10)
            self._post_auto(automation_url, "/navigate", {"tabId": self.tab_id, "url": CHATGPT_URL}, timeout=60)
            self._post_auto(automation_url, "/wait", {"tabId": self.tab_id, "condition": "domready", "timeout": 20000}, timeout=25)

            textbox_xpath = self._find_first(automation_url, TEXTBOX_XPATHS, code="CHATGPT_LOGIN_REQUIRED")
            network_enabled = self._start_network_capture(automation_url)
            if not network_enabled:
                raise ChatGptAutomationError(
                    "CHATGPT_NETWORK_CAPTURE_REQUIRED",
                    "Khong bat duoc network capture nen khong the xac nhan upload/tai anh bang request.",
                )
            upload_events: list[dict[str, Any]] = []
            if image_paths:
                upload_events = self._upload_images(automation_url, image_paths, network_enabled=network_enabled)
            self._post_auto(
                automation_url,
                "/type",
                {"tabId": self.tab_id, "xpath": textbox_xpath, "text": prompt_text, "atomic": True},
                timeout=45,
            )
            self._clear_network(automation_url)
            submitted_after_ms = int(time.time() * 1000)
            self._submit_prompt(automation_url)
            generation_event = self._wait_generation_complete(
                automation_url,
                network_enabled=network_enabled,
                after_ms=submitted_after_ms,
            )
            downloaded_path = self._download_result(
                automation_url,
                payload.get("download_dir"),
                content_url=str(generation_event.get("content_url") or ""),
            )

            shutil.rmtree(handoff_dir, ignore_errors=True)
            return {
                "ok": True,
                "url": CHATGPT_URL,
                "automation_port": self._automation_port_from_url(automation_url),
                "uploaded_count": len(image_paths),
                "upload_events": upload_events,
                "generation_event": generation_event,
                "auto_submitted": True,
                "downloaded_path": downloaded_path,
                "download_method": "request",
                "image_verified": bool(downloaded_path),
            }
        except ChatGptAutomationError as exc:
            if debug_dir and "debug_dir" not in exc.to_response()["error"]:
                exc.debug_dir = debug_dir
            raise
        except Exception as exc:
            raise ChatGptAutomationError("CHATGPT_AUTOMATION_FAILED", str(exc), debug_dir=debug_dir) from exc

    def _resolve_automation_url(self, payload: dict[str, Any] | None = None) -> str:
        payload = payload or {}
        profile_id = str(payload.get("chromium_profile_id") or self.config.chromium_profile_id or "").strip()
        override_port = self._parse_port(payload.get("chromium_automation_port"))
        if profile_id and override_port and self._is_automation_url_ready(f"http://127.0.0.1:{override_port}"):
            return f"http://127.0.0.1:{override_port}"
        if override_port and not profile_id:
            return f"http://127.0.0.1:{override_port}"

        if not payload.get("chromium_profile_id") and self.config.chromium_automation_port:
            return f"http://127.0.0.1:{self.config.chromium_automation_port}"
        if not profile_id:
            raise ChatGptAutomationError(
                "CHROMIUM_PROFILE_NOT_CONFIGURED",
                "Thiếu CHROMIUM_AUTOMATION_PORT hoặc CHROMIUM_PROFILE_ID trong .env.",
            )

        manager_url = str(payload.get("chromium_profile_manager_url") or self.config.chromium_profile_manager_url).strip().rstrip("/")

        opened = self._request_json(
            "POST",
            manager_url,
            f"/profiles/{profile_id}/open",
            None,
            timeout=max(10, self.config.chromium_startup_timeout_ms / 1000),
        )
        data = self._unwrap_manager(opened, "open profile")
        port = int(data.get("automation_port") or 0)
        if port <= 0:
            raise ChatGptAutomationError("CHROMIUM_AUTOMATION_NOT_READY", "Profile không trả về automation_port.")
        automation_url = f"http://127.0.0.1:{port}"
        if self._is_automation_url_ready(automation_url):
            return automation_url
        fallback_port = override_port or self.config.chromium_automation_port
        fallback_url = f"http://127.0.0.1:{fallback_port}" if fallback_port else ""
        if fallback_url and self._is_automation_url_ready(fallback_url):
            return fallback_url
        return automation_url

    @staticmethod
    def _parse_port(value: Any) -> int:
        try:
            port = int(str(value or "").strip())
        except (TypeError, ValueError):
            return 0
        return port if 0 < port <= 65535 else 0

    def _wait_automation_ready(self, automation_url: str) -> None:
        deadline = time.time() + max(5, self.config.chromium_startup_timeout_ms / 1000)
        last_error = ""
        while time.time() < deadline:
            try:
                status = self._request_json("GET", automation_url, "/status", None, timeout=3)
                if status.get("ok") and status.get("hasBrowser"):
                    return
                last_error = json.dumps(status, ensure_ascii=False)
            except Exception as exc:
                last_error = str(exc)
            time.sleep(0.8)
        raise ChatGptAutomationError(
            "CHROMIUM_AUTOMATION_NOT_READY",
            f"Không kết nối được Chromium automation: {automation_url}. {last_error}",
        )

    def _is_automation_url_ready(self, automation_url: str) -> bool:
        try:
            status = self._request_json("GET", automation_url, "/status", None, timeout=2)
        except Exception:
            return False
        return bool(status.get("ok") and status.get("hasBrowser"))

    def _find_first(self, automation_url: str, xpaths: tuple[str, ...], *, code: str) -> str:
        for xpath in xpaths:
            try:
                self._post_auto(
                    automation_url,
                    "/wait",
                    {"tabId": self.tab_id, "condition": "visible", "xpath": xpath, "timeout": 7000},
                    timeout=10,
                )
                return xpath
            except Exception:
                continue
        raise ChatGptAutomationError(code, "Không tìm thấy ô nhập prompt. Hãy kiểm tra profile đã đăng nhập ChatGPT.")

    def _upload_images(self, automation_url: str, image_paths: list[str], *, network_enabled: bool) -> list[dict[str, Any]]:
        upload_events: list[dict[str, Any]] = []
        for position, image_path in enumerate(image_paths, start=1):
            last_error = ""
            uploaded = False
            self._clear_network(automation_url)
            for xpath_index, xpath in enumerate(FILE_INPUT_XPATHS):
                body: dict[str, Any] = {"tabId": self.tab_id, "xpath": xpath, "paths": [image_path]}
                if xpath_index > 0:
                    body["mode"] = "b"
                try:
                    self._post_auto(automation_url, "/upload", body, timeout=45)
                    upload_events.append(
                        self._wait_upload_complete(
                            automation_url,
                            image_path=image_path,
                            position=position,
                            network_enabled=network_enabled,
                        )
                    )
                    uploaded = True
                    break
                except Exception as exc:
                    last_error = str(exc)
            if not uploaded:
                raise ChatGptAutomationError(
                    "CHATGPT_UPLOAD_FAILED",
                    f"Không upload được ảnh A{position} vào ChatGPT. {last_error}",
                )
        return upload_events

    def _submit_prompt(self, automation_url: str) -> None:
        for xpath in SEND_BUTTON_XPATHS:
            try:
                self._post_auto(
                    automation_url,
                    "/wait",
                    {"tabId": self.tab_id, "condition": "enabled", "xpath": xpath, "timeout": 7000},
                    timeout=10,
                )
                self._post_auto(automation_url, "/click", {"tabId": self.tab_id, "xpath": xpath, "native": False}, timeout=15)
                return
            except Exception:
                continue
        try:
            self._post_auto(automation_url, "/sendkey", {"tabId": self.tab_id, "key": "Enter", "native": False}, timeout=10)
        except Exception as exc:
            raise ChatGptAutomationError("CHATGPT_SUBMIT_FAILED", f"Không bấm gửi được trên ChatGPT. {exc}") from exc

    def _download_result(self, automation_url: str, requested_dir: str | None, *, content_url: str = "") -> str | None:
        download_dir = self._resolve_download_dir(requested_dir)
        if download_dir is None:
            return None
        download_dir.mkdir(parents=True, exist_ok=True)

        save_path = download_dir / f"chatgpt-img2-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
        content_url = content_url or self._wait_content_request_url(automation_url)
        downloaded = self._post_auto(
            automation_url,
            "/download",
            {"tabId": self.tab_id, "url": content_url, "savePath": str(save_path), "timeout": 120000},
            timeout=130,
        )
        downloaded_path = Path(str(downloaded.get("path") or downloaded.get("savedTo") or save_path))
        if not self._is_valid_downloaded_image(downloaded_path):
            raise ChatGptAutomationError(
                "CHATGPT_DOWNLOAD_VERIFY_FAILED",
                f"Da bat request anh nhung file tai ve khong phai anh hop le: {downloaded_path}",
            )
        return str(downloaded_path)

    def _wait_content_request_url(self, automation_url: str) -> str:
        deadline = time.time() + (self.config.chromium_generation_timeout_ms / 1000)
        last_error = ""
        while time.time() < deadline:
            try:
                records = self._network_records(automation_url, limit=300)
                candidates = [
                    record
                    for record in records
                    if self._matches_network_record(record, CONTENT_REQUEST_MARKERS)
                    and self._is_new_image_content_record(record)
                ]
                if candidates:
                    return str(candidates[-1].get("url") or candidates[-1].get("originalUrl") or "")
            except Exception as exc:
                last_error = str(exc)
            time.sleep(0.8)
        raise ChatGptAutomationError(
            "CHATGPT_CONTENT_REQUEST_NOT_FOUND",
            f"Khong bat duoc request anh backend-api/estuary/content tu ChatGPT. {last_error}",
        )

    def _start_network_capture(self, automation_url: str) -> bool:
        try:
            self._post_auto(
                automation_url,
                "/network/start",
                {"tabId": self.tab_id, "captureBody": False, "maxBodyBytes": 0},
                timeout=8,
            )
            return True
        except Exception:
            return False

    def _clear_network(self, automation_url: str) -> None:
        try:
            self._post_auto(automation_url, "/network/clear", {"tabId": self.tab_id}, timeout=5)
        except Exception:
            pass

    def _network_records(self, automation_url: str, *, limit: int = 120) -> list[dict[str, Any]]:
        try:
            response = self._post_auto(automation_url, "/network/get", {"tabId": self.tab_id, "limit": limit}, timeout=8)
        except Exception:
            return []
        records = response.get("requests")
        return records if isinstance(records, list) else []

    def _wait_upload_complete(
        self,
        automation_url: str,
        *,
        image_path: str,
        position: int,
        network_enabled: bool,
    ) -> dict[str, Any]:
        if not network_enabled:
            raise ChatGptAutomationError(
                "CHATGPT_NETWORK_CAPTURE_REQUIRED",
                f"Khong bat duoc network capture nen khong the xac nhan upload anh A{position}.",
            )

        deadline = time.time() + UPLOAD_VERIFY_TIMEOUT_SECONDS
        seen_candidates = 0
        while time.time() < deadline:
            records = self._network_records(automation_url)
            candidates = [record for record in records if self._matches_network_record(record, UPLOAD_REQUEST_MARKERS)]
            seen_candidates = max(seen_candidates, len(candidates))
            completed = [record for record in candidates if self._is_2xx_record(record)]
            if completed:
                last = completed[-1]
                time.sleep(UPLOAD_SETTLE_SECONDS)
                return {
                    "position": position,
                    "path": image_path,
                    "detected_by": "network",
                    "url": self._sanitize_network_url(str(last.get("url") or "")),
                    "status": last.get("status"),
                    "duration": last.get("duration"),
                    "settle_seconds": UPLOAD_SETTLE_SECONDS,
                }
            time.sleep(UPLOAD_POLL_SECONDS)

        raise ChatGptAutomationError(
            "CHATGPT_UPLOAD_VERIFY_TIMEOUT",
            f"Da goi upload A{position} nhung khong bat duoc request upload 2xx hoan tat. Candidate requests: {seen_candidates}.",
        )

    def _wait_generation_complete(self, automation_url: str, *, network_enabled: bool, after_ms: int = 0) -> dict[str, Any]:
        if not network_enabled:
            raise ChatGptAutomationError(
                "CHATGPT_NETWORK_CAPTURE_REQUIRED",
                "Khong bat duoc network capture nen khong the tai anh bang request.",
            )
        deadline = time.time() + (self.config.chromium_generation_timeout_ms / 1000)
        while time.time() < deadline:
            for record in self._network_records(automation_url, limit=300):
                if (
                    self._matches_network_record(record, CONTENT_REQUEST_MARKERS)
                    and self._is_after(record, after_ms)
                    and self._is_new_image_content_record(record)
                ):
                    return {
                        "detected_by": "content_request",
                        "content_url": str(record.get("url") or record.get("originalUrl") or ""),
                        "network_status": record.get("status"),
                        "start_time_ms": record.get("startTimeMs"),
                    }
            time.sleep(1.0)
        raise ChatGptAutomationError(
            "CHATGPT_CONTENT_REQUEST_NOT_FOUND",
            "Khong bat duoc request anh backend-api/estuary/content tu ChatGPT.",
        )

    @classmethod
    def _is_valid_downloaded_image(cls, path: Path) -> bool:
        if not path.exists() or path.stat().st_size <= 0:
            return False
        try:
            head = path.read_bytes()[:16]
        except OSError:
            return False
        if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
            return True
        return any(head.startswith(prefix) for prefix in IMAGE_MAGIC_BYTES if prefix != b"RIFF")

    @staticmethod
    def _matches_network_record(record: dict[str, Any], markers: tuple[str, ...]) -> bool:
        method = str(record.get("method") or "").upper()
        if method not in {"GET", "POST", "PUT", "PATCH"}:
            return False
        url = str(record.get("url") or record.get("originalUrl") or "").lower()
        return any(marker in url for marker in markers)

    @staticmethod
    def _is_2xx_record(record: dict[str, Any]) -> bool:
        try:
            status = int(record.get("status") or 0)
            net_error = int(record.get("netError") or 0)
        except (TypeError, ValueError):
            return False
        return 200 <= status < 300 and net_error == 0

    @classmethod
    def _is_new_image_content_record(cls, record: dict[str, Any]) -> bool:
        if not cls._is_2xx_record(record):
            return False
        if bool(record.get("fromCache")):
            return False
        mime = str(record.get("mimeType") or record.get("responseHeader.Content-Type") or "").lower()
        content_disposition = str(record.get("responseHeader.Content-Disposition") or "").lower()
        if mime and not mime.startswith("image/") and "application/octet-stream" not in mime:
            return False
        return not content_disposition or "filename=" in content_disposition or "attachment" in content_disposition

    @staticmethod
    def _is_after(record: dict[str, Any], after_ms: int) -> bool:
        if after_ms <= 0:
            return True
        try:
            start_ms = int(float(record.get("startTimeMs") or record.get("endTimeMs") or 0))
        except (TypeError, ValueError):
            return True
        return start_ms <= 0 or start_ms >= after_ms

    @staticmethod
    def _sanitize_network_url(url: str) -> str:
        return url.split("?", 1)[0][:180]

    def _post_auto(self, automation_url: str, path: str, body: dict[str, Any], *, timeout: float | None = None) -> dict[str, Any]:
        response = self._request_json("POST", automation_url, path, body, timeout=timeout or self.request_timeout)
        if response.get("ok") is False:
            raise ChatGptAutomationError("CHROMIUM_AUTOMATION_ERROR", f"{path} failed: {response}")
        return response

    def _resolve_download_dir(self, requested_dir: str | None) -> Path | None:
        value = (requested_dir or self.config.chromium_download_dir or "").strip()
        if not value:
            return self.app_root / "downloads"
        return Path(value).expanduser()

    def _request_json(self, method: str, base_url: str, path: str, body: dict[str, Any] | None, *, timeout: float) -> dict[str, Any]:
        url = base_url.rstrip("/") + path
        data = None
        headers = {"Accept": "application/json, text/plain, */*"}
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ChatGptAutomationError("CHROMIUM_HTTP_ERROR", f"{method} {url} failed HTTP {exc.code}: {detail}") from exc
        except OSError as exc:
            raise ChatGptAutomationError("CHROMIUM_CONNECTION_ERROR", f"Không kết nối được {url}: {exc}") from exc

        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ChatGptAutomationError("CHROMIUM_INVALID_JSON", f"{method} {url} trả về JSON không hợp lệ.") from exc

    @staticmethod
    def _unwrap_manager(response: dict[str, Any], action: str) -> dict[str, Any]:
        if response.get("success"):
            data = response.get("data")
            return data if isinstance(data, dict) else {}
        raise ChatGptAutomationError("CHROMIUM_MANAGER_ERROR", f"{action} failed: {response.get('error')}")

    @staticmethod
    def _materialize_images(images: list[dict[str, Any]], handoff_dir: Path) -> list[str]:
        paths: list[str] = []
        for index, image in enumerate(images, start=1):
            data_url = image.get("dataUrl") or image.get("data_url")
            if not isinstance(data_url, str) or "," not in data_url:
                continue
            header, payload = data_url.split(",", 1)
            if not header.startswith("data:image/"):
                continue
            suffix = ".jpg"
            if "image/png" in header:
                suffix = ".png"
            elif "image/webp" in header:
                suffix = ".webp"
            role = str(image.get("role") or f"reference_{index}")
            stem = {
                "model": "A1_model",
                "outfit": "A2_outfit",
                "background": "A3_background",
                "reference": f"reference_{index}",
            }.get(role, f"reference_{index}")
            try:
                raw = base64.b64decode(payload, validate=False)
            except Exception:
                continue
            handoff_dir.mkdir(parents=True, exist_ok=True)
            path = handoff_dir / f"{stem}{suffix}"
            path.write_bytes(raw)
            paths.append(str(path.resolve()))
        return paths

    @staticmethod
    def _automation_port_from_url(automation_url: str) -> int | None:
        try:
            return int(automation_url.rsplit(":", 1)[1])
        except (ValueError, IndexError):
            return None
