from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.config import AppConfig
from backend.constants import GENERIC_MODE_IDS
from backend.services.prompt_workflow import PromptWorkflow
from tests.test_mode_validators import character_json, image_to_video, product_shots, reference_pack, storyboard


def config() -> AppConfig:
    return AppConfig(
        pollinations_api_key="sk_env_key",
        pollinations_endpoints=("https://example.test/v1/chat/completions",),
        default_model="gpt-5.4-nano",
        request_timeout_seconds=30,
    )


def image(role: str = "reference") -> dict:
    return {
        "role": role,
        "name": "ref.jpg",
        "type": "image/jpeg",
        "dataUrl": "data:image/jpeg;base64," + ("a" * 128),
    }


class FakeClient:
    def __init__(self, output: str) -> None:
        self.outputs = [output]
        self.calls: list[dict] = []

    def chat_completion(self, api_key: str, body: dict) -> str:
        self.calls.append(body)
        if len(self.outputs) > 1:
            return self.outputs.pop(0)
        return self.outputs[0]


VALID_BY_MODE = {
    "character-json": character_json(),
    "product-detail-shots": product_shots(),
    "storyboard-unified": storyboard(9),
    "reference-pack": reference_pack(),
    "image-to-video": image_to_video(),
    "json-to-natural-prompt": "NATURAL PROMPT:\nA polished prompt.\n\nNEGATIVE PROMPT:\nbad anatomy",
}


class GenericWorkflowTests(unittest.TestCase):
    def test_happy_path_each_generic_mode(self) -> None:
        for mode_id in GENERIC_MODE_IDS:
            with self.subTest(mode_id=mode_id):
                workflow = PromptWorkflow(config())
                fake = FakeClient(VALID_BY_MODE[mode_id])
                workflow.client = fake
                result = workflow.generate({"mode": mode_id, "model": "gpt-5.4-nano", "images": [image()]})
                self.assertTrue(result["ok"], result)
                self.assertEqual(result["kind"], "generic")
                self.assertEqual(result["mode"], mode_id)

    def test_outfit_mode_dispatches_to_outfit_workflow(self) -> None:
        workflow = PromptWorkflow(config())
        with patch.object(workflow.outfit, "generate", return_value={"ok": True, "kind": "outfit"}) as outfit_generate:
            with patch.object(workflow.generic, "generate", return_value={"ok": True}) as generic_generate:
                result = workflow.generate({"mode": "outfit-swap-json"})
        self.assertTrue(result["ok"])
        outfit_generate.assert_called_once()
        generic_generate.assert_not_called()

    def test_json_to_natural_does_not_send_images(self) -> None:
        workflow = PromptWorkflow(config())
        fake = FakeClient(VALID_BY_MODE["json-to-natural-prompt"])
        workflow.client = fake
        result = workflow.generate({"mode": "json-to-natural-prompt", "model": "gpt-5.4-nano", "images": [image("model")]})
        self.assertTrue(result["ok"])
        content = fake.calls[0]["messages"][1]["content"]
        self.assertFalse(any(item.get("type") == "image_url" for item in content))
        self.assertEqual(result["warnings"][0]["code"], "IMAGES_DROPPED_FOR_TEXT_MODE")

    def test_image_mode_with_text_only_model_warns_and_drops_images(self) -> None:
        workflow = PromptWorkflow(config())
        fake = FakeClient(VALID_BY_MODE["character-json"])
        workflow.client = fake
        result = workflow.generate({"mode": "character-json", "model": "mistral-small-3.1", "images": [image()]})
        self.assertTrue(result["ok"])
        content = fake.calls[0]["messages"][1]["content"]
        self.assertFalse(any(item.get("type") == "image_url" for item in content))
        self.assertEqual(result["warnings"][0]["code"], "IMAGES_UNAVAILABLE_FOR_MODEL")
        self.assertTrue(result["result"]["reference_images_unavailable"])

    def test_invalid_model_and_mode(self) -> None:
        workflow = PromptWorkflow(config())
        self.assertEqual(workflow.generate({"mode": "character-json", "model": "invalid-x"})["error"]["code"], "UNSUPPORTED_MODEL")
        self.assertEqual(workflow.generate({"mode": "unknown"})["error"]["code"], "UNSUPPORTED_MODE")

    def test_generic_reference_label_does_not_leak_outfit_roles(self) -> None:
        workflow = PromptWorkflow(config())
        fake = FakeClient(VALID_BY_MODE["character-json"])
        workflow.client = fake
        result = workflow.generate({"mode": "character-json", "model": "gpt-5.4-nano", "images": [image()]})
        self.assertTrue(result["ok"])
        text_items = [item["text"] for item in fake.calls[0]["messages"][1]["content"] if item.get("type") == "text"]
        self.assertTrue(any("REFERENCE IMAGE 1" in text for text in text_items))
        self.assertFalse(any("A.1 model identity" in text or "A.2 outfit" in text for text in text_items))

    def test_invalid_generic_output_retries_once_with_repair_instruction(self) -> None:
        workflow = PromptWorkflow(config())
        fake = FakeClient("{bad json")
        fake.outputs.append(VALID_BY_MODE["storyboard-unified"])
        workflow.client = fake
        result = workflow.generate({"mode": "storyboard-unified", "model": "gpt-5.4-nano"})
        self.assertTrue(result["ok"], result)
        self.assertEqual(len(fake.calls), 2)
        self.assertTrue(result["meta"]["repaired"])
        repair_text = fake.calls[1]["messages"][1]["content"][0]["text"]
        self.assertIn("previous response failed validation", repair_text)

    def test_invalid_generic_output_keeps_outer_invalid_model_output_code(self) -> None:
        workflow = PromptWorkflow(config())
        fake = FakeClient("{bad json")
        fake.outputs.append("{still bad")
        workflow.client = fake
        result = workflow.generate({"mode": "character-json", "model": "gpt-5.4-nano"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "INVALID_MODEL_OUTPUT")
        self.assertEqual(result["error"]["detail"]["code"], "INVALID_JSON")

    def test_invalid_mime_warns(self) -> None:
        workflow = PromptWorkflow(config())
        fake = FakeClient(VALID_BY_MODE["character-json"])
        workflow.client = fake
        bad = image()
        bad["dataUrl"] = "data:image/gif;base64,aaaa"
        bad["name"] = "bad.gif"
        result = workflow.generate({"mode": "character-json", "model": "gpt-5.4-nano", "images": [bad]})
        self.assertTrue(result["ok"])
        self.assertEqual(result["warnings"][0]["code"], "IMAGE_MIME_REJECTED")

    def test_count_limit_warning_is_distinct_from_payload_trim(self) -> None:
        workflow = PromptWorkflow(config())
        fake = FakeClient(VALID_BY_MODE["character-json"])
        workflow.client = fake
        result = workflow.generate({"mode": "character-json", "model": "gpt-5.4-nano", "images": [image() for _ in range(6)]})
        self.assertTrue(result["ok"])
        self.assertIn("IMAGES_TRIMMED_BY_LIMIT", [warning["code"] for warning in result["warnings"]])

    def test_storyboard_unified_respects_scene_count_from_user_input(self) -> None:
        workflow = PromptWorkflow(config())
        fake = FakeClient(storyboard(6))
        workflow.client = fake
        ok = workflow.generate({"mode": "storyboard-unified", "model": "gpt-5.4-nano", "user_request": "tao 6 canh"})
        self.assertTrue(ok["ok"], ok)

        workflow = PromptWorkflow(config())
        fake = FakeClient(storyboard(9))
        fake.outputs.append(storyboard(9))
        workflow.client = fake
        bad = workflow.generate({"mode": "storyboard-unified", "model": "gpt-5.4-nano", "user_request": "tao 6 canh"})
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["error"]["code"], "INVALID_MODEL_OUTPUT")

    def test_response_meta_contains_prompt_version(self) -> None:
        workflow = PromptWorkflow(config())
        fake = FakeClient(VALID_BY_MODE["character-json"])
        workflow.client = fake
        result = workflow.generate({"mode": "character-json", "model": "gpt-5.4-nano"})
        self.assertEqual(result["meta"]["prompt_version"], "character-json/v2")

    def test_system_persona_per_mode_is_used(self) -> None:
        workflow = PromptWorkflow(config())
        fake = FakeClient(VALID_BY_MODE["product-detail-shots"])
        workflow.client = fake
        result = workflow.generate({"mode": "product-detail-shots", "model": "gpt-5.4-nano"})
        self.assertTrue(result["ok"])
        self.assertIn("commercial product photographer", fake.calls[0]["messages"][0]["content"])
        self.assertNotEqual(
            fake.calls[0]["messages"][0]["content"],
            "You are Super Prompt, a precise prompt engineering assistant. Return only the requested artifact.",
        )


if __name__ == "__main__":
    unittest.main()
