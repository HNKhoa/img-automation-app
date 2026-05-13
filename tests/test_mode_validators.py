from __future__ import annotations

import json
import unittest

from backend.modes import REGISTRY
from backend.modes.base import COMMON_RULES, ModeContext, coerce_scene_count


def _ctx(mode_id: str, style: str = "High-end fashion editorial", user_input: str = "test") -> ModeContext:
    spec = REGISTRY[mode_id]
    return ModeContext(
        user_input=user_input,
        style=style,
        aspect_ratio="1:1",
        resolution="2K",
        quality="high",
        selected_model={"value": "gpt-5.4-nano", "label": "GPT-5.4 Nano", "supports_images": True},
        has_reference_images=False,
        reference_images_unavailable=False,
        reference_image_count=0,
        reference_summary="",
        mode_id=spec.id,
        mode_label=spec.label,
        max_output_tokens=spec.max_output_tokens,
        output_type=spec.output_type,
        prompt_version=spec.prompt_version,
    )


def character_json() -> str:
    return json.dumps(
        {
            "subject": {
                "identity": "A confident young creator with consistent facial structure.",
                "age_range": "25-30",
                "gender_presentation": "masculine",
                "face": "oval face, warm skin, focused eyes",
                "hair": "short black hair",
                "body": "average build, upright posture",
                "expression": "calm focus",
                "outfit": "black jacket, clean fit",
                "styling": "minimal grooming",
            },
            "accessories": {"items": ["watch"], "notes": "simple metal watch"},
            "photography": {
                "lens": "85mm portrait",
                "aperture": "f/2.8",
                "camera_angle": "eye-level",
                "framing": "medium close-up",
                "lighting": "softbox key",
                "aspect_ratio": "1:1",
                "resolution": "2K",
                "quality": "high",
                "render_detail": "natural skin texture",
            },
            "background": {"location": "studio", "palette": ["cyan", "black"], "atmosphere": "quiet", "depth": "soft"},
            "the_vibe": {"mood": "focused", "art_direction": "editorial", "aesthetic": "clean"},
            "constraints": ["preserve identity", "clean anatomy", "consistent outfit", "balanced composition"],
            "negative_prompt": [
                "deformed hands",
                "distorted face",
                "bad anatomy",
                "extra limbs",
                "warped clothing",
                "wrong logos",
                "text artifacts",
                "low resolution",
            ],
        }
    )


def product_shots() -> str:
    return "\n\n".join(
        "\n".join(
            [
                f"Shot {i}: Name",
                "SUBJECT:",
                "product on seamless surface",
                "CAMERA+COMPOSITION:",
                "85mm lens, centered symmetry, eye-level crop",
                "LIGHTING:",
                "large softbox key with rim separation",
                "STYLE:",
                "commercial product photography on neutral backdrop",
                "DETAIL EMPHASIS:",
                "crisp material texture and precise edge detail",
                "INDUSTRY CONTEXT:",
                "best for marketplace listing and brand catalog use",
            ]
        )
        for i in range(1, 10)
    )


def storyboard(count: int = 9) -> str:
    return json.dumps(
        [
            {
                "scene_number": i,
                "scene_title": f"Scene {i}",
                "scene_purpose": "A clear narrative beat.",
                "image_prompt": "A complete still image prompt with subject, background, camera, lighting, style, aspect, resolution, quality.",
                "video_animation_prompt": "Subtle push-in with natural subject motion and soft background parallax.",
                "continuity_notes": "Keep identity, outfit, product color, and palette consistent.",
                "duration_hint": "2-3s",
                "negative_prompt": "identity drift, warped hands, product morphing, text artifacts, blur",
            }
            for i in range(1, count + 1)
        ]
    )


def reference_pack() -> str:
    groups = ["Character Reference Pack", "Background Reference Pack", "Product Reference Pack"]
    return "\n\n".join(
        "=== "
        + group
        + " ===\n"
        + "\n\n".join(
            f"View {i} - view {i}:\nClean reference prompt with 50mm lens, softbox lighting, eye-level angle, 1:1 aspect, 2K resolution, consistent style, avoid warped details."
            for i in range(1, 5)
        )
        for group in groups
    )


def image_to_video() -> str:
    return json.dumps(
        {
            "duration": "5s",
            "main_subject": "A product hero image on a clean surface.",
            "motion_intensity": "SUBTLE",
            "target_tools": ["Veo", "Kling"],
            "character_motion": "Subtle breathing motion only.",
            "camera_movement": "Slow controlled push-in.",
            "background_motion": "Soft parallax drift.",
            "product_motion": "Tiny label catchlight shift.",
            "lighting_motion": "Gentle highlight roll.",
            "first_frame_lock": "Match the input frame exactly.",
            "last_frame_goal": "End on a stable hero frame.",
            "constraints": ["preserve shape", "preserve logo", "stable first frame"],
            "negative_prompt": [
                "identity drift",
                "morphing",
                "warped hands",
                "logo distortion",
                "jitter",
                "extra limbs",
                "text artifacts",
                "blur",
            ],
        }
    )


NATURAL = "NATURAL PROMPT:\nA polished prompt.\n\nNEGATIVE PROMPT:\nbad anatomy"


class ModeValidatorTests(unittest.TestCase):
    def test_all_instructions_start_with_common_rules(self) -> None:
        for mode_id, spec in REGISTRY.items():
            self.assertTrue(spec.build_instruction(_ctx(mode_id)).startswith(COMMON_RULES))

    def test_style_none_skips_style_line(self) -> None:
        instruction = REGISTRY["character-json"].build_instruction(_ctx("character-json", style="None"))
        self.assertNotIn("Style: None", instruction)

    def test_coerce_scene_count(self) -> None:
        cases = {
            "": 9,
            "tao 6 canh": 6,
            "make 9 scenes": 9,
            "12 frames": 12,
            "20 scene": 12,
            "1 scene": 3,
            "storyboard 3x3": 9,
            "10 panels": 10,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(coerce_scene_count(text), expected)

    def test_character_json(self) -> None:
        spec = REGISTRY["character-json"]
        valid = character_json()
        self.assertIsNone(spec.validate_output(valid))
        self.assertIsNone(spec.validate_output(f"```json\n{valid}\n```"))
        obj = json.loads(valid)
        obj["constraints"] = ["too short"]
        self.assertEqual(spec.validate_output(json.dumps(obj))["code"], "INVALID_JSON_SHAPE")
        obj = json.loads(valid)
        obj["negative_prompt"] = ["too short"]
        self.assertEqual(spec.validate_output(json.dumps(obj))["code"], "INVALID_JSON_SHAPE")

    def test_product_detail_shots(self) -> None:
        spec = REGISTRY["product-detail-shots"]
        valid = product_shots()
        self.assertIsNone(spec.validate_output(valid))
        self.assertIsNone(spec.validate_output(f"```text\n{valid}\n```"))
        self.assertEqual(spec.validate_output(valid.replace("Shot 9:", "Shot 8:"))["code"], "INVALID_SHOT_COUNT")
        self.assertEqual(spec.validate_output(valid.replace("INDUSTRY CONTEXT:", "INDUSTRY:", 1))["code"], "MISSING_SHOT_LABELS")

    def test_storyboard_unified(self) -> None:
        spec = REGISTRY["storyboard-unified"]
        spec.build_instruction(_ctx("storyboard-unified", user_input="default"))
        self.assertIsNone(spec.validate_output(storyboard(9)))
        self.assertIsNone(spec.validate_output(f"```json\n{storyboard(9)}\n```"))
        spec.build_instruction(_ctx("storyboard-unified", user_input="tao 6 canh"))
        self.assertIsNone(spec.validate_output(storyboard(6)))
        self.assertEqual(spec.validate_output(storyboard(9))["code"], "INVALID_SCENE_COUNT")
        spec.build_instruction(_ctx("storyboard-unified", user_input="12 frames"))
        self.assertIsNone(spec.validate_output(storyboard(12)))
        spec.build_instruction(_ctx("storyboard-unified", user_input="20 scene"))
        self.assertIsNone(spec.validate_output(storyboard(12)))
        spec.build_instruction(_ctx("storyboard-unified", user_input="1 scene"))
        self.assertIsNone(spec.validate_output(storyboard(3)))
        duplicate = json.loads(storyboard(9))
        duplicate[1]["scene_number"] = 1
        spec.build_instruction(_ctx("storyboard-unified"))
        self.assertEqual(spec.validate_output(json.dumps(duplicate))["code"], "INVALID_SCENE_NUMBER")

    def test_reference_pack(self) -> None:
        spec = REGISTRY["reference-pack"]
        valid = reference_pack()
        self.assertIsNone(spec.validate_output(valid))
        self.assertIsNone(spec.validate_output(f"```text\n{valid}\n```"))
        self.assertEqual(spec.validate_output("Character Reference Pack")["code"], "MISSING_SECTIONS")
        self.assertEqual(spec.validate_output(valid.replace("View 4 -", "Missing 4 -", 1))["code"], "MISSING_VIEWS")

    def test_image_to_video(self) -> None:
        spec = REGISTRY["image-to-video"]
        valid = image_to_video()
        self.assertIsNone(spec.validate_output(valid))
        self.assertIsNone(spec.validate_output(f"```json\n{valid}\n```"))
        obj = json.loads(valid)
        obj["motion_intensity"] = "DRAMATIC"
        self.assertEqual(spec.validate_output(json.dumps(obj))["code"], "INVALID_JSON_SHAPE")
        obj = json.loads(valid)
        obj["duration"] = "five seconds"
        self.assertEqual(spec.validate_output(json.dumps(obj))["code"], "INVALID_JSON_SHAPE")

    def test_json_to_natural(self) -> None:
        spec = REGISTRY["json-to-natural-prompt"]
        self.assertIsNone(spec.validate_output(NATURAL))
        self.assertIsNone(spec.validate_output(f"```text\n{NATURAL}\n```"))
        self.assertEqual(spec.validate_output("NEGATIVE PROMPT:\nx\n\nNATURAL PROMPT:\ny")["code"], "INVALID_SECTIONS")
        self.assertEqual(spec.validate_output("NATURAL PROMPT:\nx\n\nEXTRA NOTES:\ny\n\nNEGATIVE PROMPT:\nz")["code"], "INVALID_SECTIONS")


if __name__ == "__main__":
    unittest.main()
