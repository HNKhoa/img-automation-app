from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.config import AppConfig
from backend.services.chatgpt_image_automation import ChatGptAutomationError, ChatGptImageAutomationService


def config(port: int = 43153) -> AppConfig:
    return AppConfig(
        pollinations_api_key="sk_env_key",
        pollinations_endpoints=("https://example.test/v1/chat/completions",),
        default_model="gpt-5.4-nano",
        request_timeout_seconds=30,
        chromium_automation_port=port,
        chromium_startup_timeout_ms=5000,
        chromium_request_timeout_ms=3000,
    )


def profile_config() -> AppConfig:
    return AppConfig(
        pollinations_api_key="sk_env_key",
        pollinations_endpoints=("https://example.test/v1/chat/completions",),
        default_model="gpt-5.4-nano",
        request_timeout_seconds=30,
        chromium_automation_port=43153,
        chromium_profile_id="profile_from_env",
        chromium_profile_manager_url="http://127.0.0.1:58001",
        chromium_startup_timeout_ms=5000,
        chromium_request_timeout_ms=3000,
    )


class FakeAutomationService(ChatGptImageAutomationService):
    def __init__(self, app_root: Path, *, fail_path: str | None = None) -> None:
        super().__init__(config(), app_root)
        self.calls: list[tuple[str, str, str, dict | None]] = []
        self.fail_path = fail_path

    def _request_json(self, method: str, base_url: str, path: str, body: dict | None, *, timeout: float) -> dict:
        self.calls.append((method, base_url, path, body))
        if path == self.fail_path:
            raise ChatGptAutomationError("FORCED_FAIL", f"forced failure at {path}")
        if path == "/status":
            return {"ok": True, "hasBrowser": True}
        if path == "/wait":
            return {"ok": True}
        if path == "/download":
            save_path = Path(body.get("savePath") if body else "")
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(b"\x89PNG\r\n\x1a\nfake-image")
            return {"ok": True, "path": str(save_path)}
        if path == "/network/get":
            return {
                "ok": True,
                "requests": [
                    {
                        "method": "POST",
                        "url": "https://chatgpt.com/backend-api/files/upload",
                        "status": 200,
                        "netError": 0,
                        "duration": 123.4,
                    },
                    {
                        "method": "GET",
                        "url": "https://chatgpt.com/backend-api/estuary/content?id=file_123",
                        "status": 200,
                        "netError": 0,
                        "duration": 45.6,
                    }
                ],
            }
        return {"ok": True}


class FakeProfileManagerService(FakeAutomationService):
    def __init__(self, app_root: Path) -> None:
        ChatGptImageAutomationService.__init__(self, profile_config(), app_root)
        self.calls: list[tuple[str, str, str, dict | None]] = []
        self.fail_path = None

    def _request_json(self, method: str, base_url: str, path: str, body: dict | None, *, timeout: float) -> dict:
        self.calls.append((method, base_url, path, body))
        if path.startswith("/profiles/") and path.endswith("/open"):
            return {"success": True, "data": {"automation_port": 45678}}
        return super()._request_json(method, base_url, path, body, timeout=timeout)


class ChatGptImageAutomationTests(unittest.TestCase):
    def test_generate_image_uses_direct_port_and_submits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = FakeAutomationService(Path(tmp))
            result = service.generate_image(
                {
                    "prompt_text": "MAIN PROMPT:\nhello",
                    "images": [
                        {
                            "role": "model",
                            "type": "image/jpeg",
                            "dataUrl": "data:image/jpeg;base64,aGVsbG8=",
                        }
                    ],
                }
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["automation_port"], 43153)
        self.assertEqual(result["uploaded_count"], 1)
        self.assertTrue(result["downloaded_path"])
        self.assertEqual(result["download_method"], "request")
        self.assertTrue(result["image_verified"])
        paths = [call[2] for call in service.calls]
        self.assertIn("/navigate", paths)
        self.assertIn("/upload", paths)
        self.assertIn("/type", paths)
        self.assertIn("/click", paths)
        self.assertIn("/download", paths)
        self.assertNotIn("/download/arm", paths)
        self.assertNotIn("/download/wait", paths)
        self.assertIn("/network/start", paths)
        self.assertIn("/network/get", paths)
        self.assertTrue(any(call[1] == "http://127.0.0.1:43153" for call in service.calls))

    def test_uploads_images_one_by_one_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = FakeAutomationService(Path(tmp))
            service.generate_image(
                {
                    "prompt_text": "MAIN PROMPT:\nhello",
                    "images": [
                        {"role": "model", "type": "image/jpeg", "dataUrl": "data:image/jpeg;base64,YTE="},
                        {"role": "outfit", "type": "image/jpeg", "dataUrl": "data:image/jpeg;base64,YTI="},
                        {"role": "background", "type": "image/jpeg", "dataUrl": "data:image/jpeg;base64,YTM="},
                    ],
                }
            )

        upload_calls = [call for call in service.calls if call[2] == "/upload"]
        self.assertEqual(len(upload_calls), 3)
        self.assertEqual([Path(call[3]["paths"][0]).name for call in upload_calls], ["A1_model.jpg", "A2_outfit.jpg", "A3_background.jpg"])
        self.assertTrue(all(len(call[3]["paths"]) == 1 for call in upload_calls))
        network_get_indices = [index for index, call in enumerate(service.calls) if call[2] == "/network/get"]
        upload_indices = [index for index, call in enumerate(service.calls) if call[2] == "/upload"]
        self.assertTrue(upload_indices[0] < network_get_indices[0] < upload_indices[1])
        self.assertTrue(upload_indices[1] < network_get_indices[1] < upload_indices[2])

    def test_profile_manager_override_opens_selected_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = FakeProfileManagerService(Path(tmp))
            result = service.generate_image(
                {
                    "prompt_text": "MAIN PROMPT:\nhello",
                    "images": [],
                    "chromium_profile_manager_url": "http://127.0.0.1:58001",
                    "chromium_profile_id": "selected_profile",
                    "chromium_automation_port": "",
                }
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["automation_port"], 45678)
        self.assertIn(("POST", "http://127.0.0.1:58001", "/profiles/selected_profile/open", None), service.calls)

    def test_empty_prompt_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = FakeAutomationService(Path(tmp))
            with self.assertRaises(ChatGptAutomationError) as ctx:
                service.generate_image({"prompt_text": " "})
        self.assertEqual(ctx.exception.code, "CHATGPT_PROMPT_EMPTY")

    def test_upload_failure_keeps_debug_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = FakeAutomationService(Path(tmp), fail_path="/upload")
            with self.assertRaises(ChatGptAutomationError) as ctx:
                service.generate_image(
                    {
                        "prompt_text": "hello",
                        "images": [{"role": "outfit", "dataUrl": "data:image/jpeg;base64,aGVsbG8="}],
                    }
                )
            self.assertEqual(ctx.exception.code, "CHATGPT_UPLOAD_FAILED")
            self.assertTrue(ctx.exception.debug_dir)
            self.assertTrue(Path(ctx.exception.debug_dir).exists())

    def test_download_requires_created_file(self) -> None:
        class BrokenDownloadService(FakeAutomationService):
            def _request_json(self, method: str, base_url: str, path: str, body: dict | None, *, timeout: float) -> dict:
                if path == "/download":
                    self.calls.append((method, base_url, path, body))
                    return {"ok": True, "path": body.get("savePath") if body else ""}
                return super()._request_json(method, base_url, path, body, timeout=timeout)

        with tempfile.TemporaryDirectory() as tmp:
            service = BrokenDownloadService(Path(tmp))
            with self.assertRaises(ChatGptAutomationError) as ctx:
                service._download_result("http://127.0.0.1:43153", str(Path(tmp) / "downloads"), content_url="https://chatgpt.com/backend-api/estuary/content?id=file_1")

        self.assertEqual(ctx.exception.code, "CHATGPT_DOWNLOAD_VERIFY_FAILED")

    def test_download_rejects_non_image_response_file(self) -> None:
        class NonImageDownloadService(FakeAutomationService):
            def _request_json(self, method: str, base_url: str, path: str, body: dict | None, *, timeout: float) -> dict:
                if path == "/download":
                    self.calls.append((method, base_url, path, body))
                    save_path = Path(body.get("savePath") if body else "")
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    save_path.write_text("not an image", encoding="utf-8")
                    return {"ok": True, "path": str(save_path)}
                return super()._request_json(method, base_url, path, body, timeout=timeout)

        with tempfile.TemporaryDirectory() as tmp:
            service = NonImageDownloadService(Path(tmp))
            with self.assertRaises(ChatGptAutomationError) as ctx:
                service._download_result(
                    "http://127.0.0.1:43153",
                    str(Path(tmp) / "downloads"),
                    content_url="https://chatgpt.com/backend-api/estuary/content?id=file_1",
                )

        self.assertEqual(ctx.exception.code, "CHATGPT_DOWNLOAD_VERIFY_FAILED")

    def test_generation_wait_ignores_304_and_stale_content_requests(self) -> None:
        class ContentRequestService(FakeAutomationService):
            def _request_json(self, method: str, base_url: str, path: str, body: dict | None, *, timeout: float) -> dict:
                if path == "/network/get":
                    self.calls.append((method, base_url, path, body))
                    return {
                        "ok": True,
                        "requests": [
                            {
                                "method": "GET",
                                "url": "https://chatgpt.com/backend-api/estuary/content?id=old_cached",
                                "status": 304,
                                "netError": 0,
                                "startTimeMs": 2000,
                            },
                            {
                                "method": "GET",
                                "url": "https://chatgpt.com/backend-api/estuary/content?id=old_200",
                                "status": 200,
                                "netError": 0,
                                "startTimeMs": 1000,
                            },
                            {
                                "method": "GET",
                                "url": "https://chatgpt.com/backend-api/estuary/content?id=new_200",
                                "status": 200,
                                "netError": 0,
                                "startTimeMs": 3000,
                            },
                        ],
                    }
                return super()._request_json(method, base_url, path, body, timeout=timeout)

        with tempfile.TemporaryDirectory() as tmp:
            service = ContentRequestService(Path(tmp))
            event = service._wait_generation_complete("http://127.0.0.1:43153", network_enabled=True, after_ms=2500)

        self.assertIn("new_200", event["content_url"])
        self.assertEqual(event["network_status"], 200)


if __name__ == "__main__":
    unittest.main()
