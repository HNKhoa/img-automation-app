from __future__ import annotations

import unittest

from backend.prompts.builder_prompts import build_builder_instruction


def _ctx(rule: str) -> str:
    return build_builder_instruction(
        analysis_json={"identity": {}, "outfit": {}, "background": None, "notes": []},
        user_request="x",
        target_rule=rule,
        style="High-end fashion editorial",
        aspect_ratio="1:1",
        resolution="2K",
        quality="high",
    )


class BuilderTargetSwitchTests(unittest.TestCase):
    def test_chatgpt_img_three_sections(self) -> None:
        out = _ctx("chatgpt_img")
        self.assertIn("MAIN PROMPT:", out)
        self.assertIn("NEGATIVE PROMPT:", out)
        self.assertIn("REFERENCE BINDING INSTRUCTIONS:", out)

    def test_gpt_image_constrains_length(self) -> None:
        self.assertIn("<= 250 words", _ctx("gpt_image"))

    def test_gg_banana2_requires_json(self) -> None:
        self.assertIn("JSON object", _ctx("gg_banana2"))


if __name__ == "__main__":
    unittest.main()
