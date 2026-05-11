from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app


class DesktopApiTests(unittest.TestCase):
    def test_bootstrap_returns_config_and_profiles(self) -> None:
        api = app.DesktopApi()
        api.chrome_profiles.list_profiles = lambda: [{"id": "Chrome::Default", "name": "Default"}]

        result = api.get_bootstrap()

        self.assertTrue(result["ok"])
        self.assertIn("config", result)
        self.assertIn("model_options", result)
        self.assertIn("target_options", result)
        self.assertIn("quality_profiles", result)
        self.assertEqual(result["profiles"][0]["id"], "Chrome::Default")

    def test_generate_prompt_wraps_unexpected_exception(self) -> None:
        api = app.DesktopApi()

        class BrokenWorkflow:
            def generate(self, payload: dict) -> dict:
                raise RuntimeError("boom")

        api.workflow = BrokenWorkflow()
        result = api.generate_prompt({})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "UNEXPECTED_ERROR")

    def test_open_chatgpt_writes_prompt_handoff_file(self) -> None:
        api = app.DesktopApi()
        api.chrome_profiles.find_profile = lambda profile_id: {"id": profile_id}
        api.chrome_profiles.open_chatgpt = lambda profile: {"ok": True, "profile": profile}

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(app, "APP_ROOT", Path(tmp)):
                result = api.open_chatgpt({"profile_id": "Chrome::Default", "prompt_text": "MAIN PROMPT:\nhello"})

        self.assertTrue(result["ok"])
        self.assertTrue(result["prompt_file"].endswith("chatgpt_img2_prompt.txt"))


if __name__ == "__main__":
    unittest.main()

