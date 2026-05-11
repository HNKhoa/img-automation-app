from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.config import AppConfig
from backend.services.chrome_profiles import ChromeProfileService
from backend.services.pollinations_client import PollinationsClient, PollinationsError
from backend.services.prompt_workflow import PromptWorkflow

VALID_OUTPUT = """MAIN PROMPT:
Identity priority: absolute highest. Preserve the model from Image 1 and reproduce the outfit from Image 2.

NEGATIVE PROMPT:
wrong face, identity drift, outfit mismatch

REFERENCE BINDING INSTRUCTIONS:
Image 1 controls identity only. Image 2 controls outfit only."""


class FakeClient:
    def __init__(self, output: str = VALID_OUTPUT) -> None:
        self.output = output
        self.calls = []

    def chat_completion(self, api_key: str, body: dict) -> str:
        self.calls.append({"api_key": api_key, "body": body})
        return self.output


def config() -> AppConfig:
    return AppConfig(
        pollinations_api_key="sk_env_key",
        pollinations_endpoints=("https://example.test/v1/chat/completions",),
        default_model="gpt-5.4-nano",
        request_timeout_seconds=30,
    )


def image(role: str, name: str = "ref.jpg") -> dict:
    return {
        "role": role,
        "name": name,
        "type": "image/jpeg",
        "dataUrl": "data:image/jpeg;base64," + ("a" * 128),
    }


class PromptWorkflowTests(unittest.TestCase):
    def test_generate_outfit_swap_success_builds_image_payload(self) -> None:
        workflow = PromptWorkflow(config())
        fake = FakeClient()
        workflow.client = fake

        result = workflow.generate(
            {
                "api_key": "sk_user_key",
                "mode": "outfit-swap-json",
                "model": "gpt-5.4-nano",
                "user_request": "Giữ mặt mẫu, nền studio.",
                "images": [image("model"), image("outfit"), image("background")],
            }
        )

        self.assertTrue(result["ok"])
        self.assertIn("MAIN PROMPT:", result["result"]["output"])
        body = fake.calls[0]["body"]
        self.assertEqual(body["temperature"], 0.35)
        user_content = body["messages"][1]["content"]
        self.assertEqual(sum(1 for item in user_content if item.get("type") == "image_url"), 3)

    def test_generate_requires_model_and_outfit_images(self) -> None:
        workflow = PromptWorkflow(config())
        workflow.client = FakeClient()

        result = workflow.generate({"mode": "outfit-swap-json", "images": [image("model")]})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("A.2 outfit", result["error"]["message"])

    def test_generate_rejects_invalid_model_output(self) -> None:
        workflow = PromptWorkflow(config())
        workflow.client = FakeClient("not the required sections")

        result = workflow.generate({"mode": "outfit-swap-json", "images": [image("model"), image("outfit")]})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "INVALID_MODEL_OUTPUT")
        self.assertIn("MAIN PROMPT:", result["error"]["message"])

    def test_unsupported_mode_is_explicit(self) -> None:
        workflow = PromptWorkflow(config())

        result = workflow.generate({"mode": "general", "images": [image("model"), image("outfit")]})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "UNSUPPORTED_MODE")

    def test_unsupported_model_is_rejected(self) -> None:
        workflow = PromptWorkflow(config())
        workflow.client = FakeClient()

        result = workflow.generate({"mode": "outfit-swap-json", "model": "unknown-model", "images": [image("model"), image("outfit")]})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "UNSUPPORTED_MODEL")
        self.assertIn("unknown-model", result["error"]["message"])

    def test_test_api_key_maps_pollinations_error(self) -> None:
        workflow = PromptWorkflow(config())

        class ErrorClient:
            def chat_completion(self, api_key: str, body: dict) -> str:
                raise PollinationsError("UNAUTHORIZED", "bad key", 401)

        workflow.client = ErrorClient()
        result = workflow.test_api_key("sk_bad")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["status"], 401)

    def test_custom_relay_endpoint_prepended(self) -> None:
        workflow = PromptWorkflow(config())
        created: list[tuple[str, ...]] = []

        class RecordingClient:
            def __init__(self, endpoints: tuple[str, ...], timeout_seconds: int) -> None:
                self.endpoints = endpoints
                self.timeout_seconds = timeout_seconds
                created.append(endpoints)

            def chat_completion(self, api_key: str, body: dict) -> str:
                return VALID_OUTPUT

        with patch("backend.services.prompt_workflow.PollinationsClient", RecordingClient):
            workflow.client = RecordingClient(config().pollinations_endpoints, 30)
            result = workflow.generate(
                {
                    "api_key": "sk_user_key",
                    "mode": "outfit-swap-json",
                    "model": "gpt-5.4-nano",
                    "custom_relay_endpoint": "https://my-relay.test/x",
                    "images": [image("model"), image("outfit")],
                }
            )

        self.assertTrue(result["ok"])
        self.assertEqual(created[-1][0], "https://my-relay.test/x")


class PollinationsClientTests(unittest.TestCase):
    def test_requires_secret_key_prefix(self) -> None:
        client = PollinationsClient(("https://example.test",), 30)

        with self.assertRaises(PollinationsError) as ctx:
            client.chat_completion("pk_old_key", {})

        self.assertEqual(ctx.exception.code, "INVALID_API_KEY_FORMAT")

    def test_maps_cloudflare_access_denied_without_raw_json(self) -> None:
        body = '{"type":"https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/","title":"Error 1010: Access denied","status":403,"detail":"The site owner has blocked access based on your browser signature.","cloudflare_error":true}'

        error = PollinationsClient._map_http_error(403, body, None)

        self.assertEqual(error.code, "CLOUDFLARE_ACCESS_DENIED")
        self.assertNotIn("ray_id", error.message)
        self.assertNotIn("cloudflare_error", error.message)

    def test_extracts_openai_style_content(self) -> None:
        raw = '{"choices":[{"message":{"content":"hello"}}]}'
        self.assertEqual(PollinationsClient._extract_text(raw), "hello")

    def test_rejects_empty_response(self) -> None:
        with self.assertRaises(PollinationsError):
            PollinationsClient._extract_text("  ")


class _Response:
    def __init__(self, status_code: int, text: str, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}


class PollinationsClientFailoverTests(unittest.TestCase):
    def test_failover_to_next_endpoint_on_cloudflare(self) -> None:
        endpoints = ("https://blocked.test/openai", "https://ok.test/openai")
        client = PollinationsClient(endpoints, 30)
        calls = []

        def fake_post(endpoint: str, **kwargs: object) -> _Response:
            calls.append((endpoint, kwargs.get("impersonate")))
            if endpoint == endpoints[0]:
                return _Response(403, '{"cloudflare_error":true,"detail":"access denied"}')
            return _Response(200, '{"choices":[{"message":{"content":"OK"}}]}')

        with patch("backend.services.pollinations_client.cffi_requests") as cffi:
            cffi.post.side_effect = fake_post
            cffi.errors.RequestsError = Exception
            self.assertEqual(client.chat_completion("sk_key", {"model": "x"}), "OK")

        self.assertEqual(calls.count((endpoints[1], "chrome124")), 1)
        self.assertEqual(client._preferred_endpoint, endpoints[1])

    def test_subsequent_call_uses_preferred_endpoint_first(self) -> None:
        endpoints = ("https://blocked.test/openai", "https://ok.test/openai")
        client = PollinationsClient(endpoints, 30)
        client._preferred_endpoint = endpoints[1]
        calls = []

        def fake_post(endpoint: str, **kwargs: object) -> _Response:
            calls.append(endpoint)
            return _Response(200, '{"choices":[{"message":{"content":"OK"}}]}')

        with patch("backend.services.pollinations_client.cffi_requests") as cffi:
            cffi.post.side_effect = fake_post
            cffi.errors.RequestsError = Exception
            client.chat_completion("sk_key", {"model": "x"})

        self.assertEqual(calls[0], endpoints[1])

    def test_no_failover_on_unauthorized(self) -> None:
        client = PollinationsClient(("https://bad.test/openai", "https://ok.test/openai"), 30)
        with patch("backend.services.pollinations_client.cffi_requests") as cffi:
            cffi.post.return_value = _Response(401, '{"error":"bad key"}')
            cffi.errors.RequestsError = Exception
            with self.assertRaises(PollinationsError) as ctx:
                client.chat_completion("sk_key", {"model": "x"})

        self.assertEqual(ctx.exception.code, "UNAUTHORIZED")
        self.assertEqual(cffi.post.call_count, 1)

    def test_failover_on_legacy_model_not_found(self) -> None:
        endpoints = ("https://legacy.test/openai", "https://ok.test/v1/chat/completions")
        client = PollinationsClient(endpoints, 30)
        calls = []

        def fake_post(endpoint: str, **kwargs: object) -> _Response:
            calls.append(endpoint)
            if endpoint == endpoints[0]:
                return _Response(404, '{"error":"Model not found: gpt-5.4-nano. This is our legacy API"}')
            return _Response(200, '{"choices":[{"message":{"content":"OK"}}]}')

        with patch("backend.services.pollinations_client.cffi_requests") as cffi:
            cffi.post.side_effect = fake_post
            cffi.errors.RequestsError = Exception
            self.assertEqual(client.chat_completion("sk_key", {"model": "gpt-5.4-nano"}), "OK")

        self.assertEqual(calls, [endpoints[0], endpoints[1]])

    def test_all_profiles_tried_within_one_endpoint_before_moving(self) -> None:
        endpoints = ("https://blocked-a.test/openai", "https://blocked-b.test/openai")
        client = PollinationsClient(endpoints, 30)
        with patch("backend.services.pollinations_client.cffi_requests") as cffi:
            cffi.post.return_value = _Response(403, "Error 1010: Access denied cf-ray")
            cffi.errors.RequestsError = Exception
            with self.assertRaises(PollinationsError):
                client.chat_completion("sk_key", {"model": "x"})

        self.assertEqual(cffi.post.call_count, len(endpoints) * len(PollinationsClient.IMPERSONATE_PROFILES))

    def test_retryable_5xx_retries_once_same_profile_same_endpoint(self) -> None:
        client = PollinationsClient(("https://flaky.test/openai",), 30)
        with patch("backend.services.pollinations_client.time.sleep"), patch("backend.services.pollinations_client.cffi_requests") as cffi:
            cffi.post.side_effect = [
                _Response(503, "temporary"),
                _Response(200, '{"choices":[{"message":{"content":"OK"}}]}'),
            ]
            cffi.errors.RequestsError = Exception
            self.assertEqual(client.chat_completion("sk_key", {"model": "x"}), "OK")

        self.assertEqual(cffi.post.call_count, 2)

    def test_missing_curl_cffi_raises_explicit_error(self) -> None:
        client = PollinationsClient(("https://example.test/openai",), 30)
        with patch("backend.services.pollinations_client.cffi_requests", None):
            with self.assertRaises(PollinationsError) as ctx:
                client.chat_completion("sk_key", {"model": "x"})

        self.assertEqual(ctx.exception.code, "MISSING_CURL_CFFI")


class ChromeProfileServiceTests(unittest.TestCase):
    def test_lists_profiles_from_temp_chrome_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "Chrome User Data"
            default = root / "Default"
            profile_1 = root / "Profile 1"
            default.mkdir(parents=True)
            profile_1.mkdir()
            (default / "Preferences").write_text("{}", encoding="utf-8")
            (profile_1 / "Preferences").write_text("{}", encoding="utf-8")
            (root / "Local State").write_text(
                '{"profile":{"info_cache":{"Default":{"name":"Main"},"Profile 1":{"name":"Shop"}}}}',
                encoding="utf-8",
            )

            service = ChromeProfileService()
            with patch.object(
                service,
                "_browser_roots",
                return_value=[{"name": "Chrome", "user_data_dir": root, "executable": None}],
            ):
                profiles = service.list_profiles()

        self.assertEqual([profile["name"] for profile in profiles], ["Main", "Shop"])

    def test_permission_denied_path_is_treated_as_missing(self) -> None:
        class DeniedPath:
            def exists(self) -> bool:
                raise PermissionError("denied")

        self.assertFalse(ChromeProfileService._path_exists(DeniedPath()))


if __name__ == "__main__":
    unittest.main()
