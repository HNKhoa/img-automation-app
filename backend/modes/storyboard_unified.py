from __future__ import annotations

import contextvars
from typing import Any

from backend.constants import GENERATION_MODE_IDS
from backend.modes.base import (
    ModeContext,
    ModeSpec,
    build_instruction_common,
    coerce_scene_count,
    coerce_scene_number,
    error,
    parse_json_strict,
    require_list_keys,
    strip_markdown_fence,
)

MODE_ID = GENERATION_MODE_IDS["STORYBOARD_UNIFIED"]
MODE_LABEL = "Storyboard hop nhat"
MODE_PURPOSE = "Tao storyboard da nang cho image prompt va image-to-video prompt trong cung mot JSON."
MODE_USAGE = "Nhap y tuong video ngan. Co the ghi 6 canh, 9 scenes, 12 frames de chon so scene tu 3 den 12."

SYSTEM_PERSONA = (
    "You are a senior film storyboard artist and director with experience in commercial advertising, "
    "social-first content, and image-to-video AI workflows. You ensure narrative continuity, "
    "cinematic pacing, and identity preservation across scenes."
)
PROMPT_VERSION = f"{MODE_ID}/v2"

TASK_BLOCK = """Task:
Create a storyboard. Number of scenes is derived from the user input.
Return a valid JSON array only. Each scene has both a still-image prompt and a video animation prompt.

SCENE COUNT:
- If user input mentions an explicit number between 3 and 12, use that number.
- If user input mentions 3x3 or storyboard 9, use 9.
- Otherwise, default to 9 scenes.
- Hard limits: minimum 3, maximum 12. Clamp if user requests outside this range.
- The chosen number must equal the array length and the highest scene_number."""

SCHEMA_BLOCK = """Each scene object must include exactly these keys:
{
  "scene_number": "integer, 1..N unique",
  "scene_title": "string, 3-6 words",
  "scene_purpose": "string, 1 sentence narrative role",
  "image_prompt": "string, complete still-image prompt with subject, background, camera, lighting, style, aspect, resolution, quality",
  "video_animation_prompt": "string, subtle motion with subject motion, camera motion, background motion, lighting shift, product handling",
  "continuity_notes": "string, what carries over from previous scene",
  "duration_hint": "string, e.g. '2-3s'",
  "negative_prompt": "string, scene-specific issues to avoid"
}"""

DOMAIN_VOCAB = """Domain vocabulary:
- Narrative: cold open, establishing, inciting moment, mid-arc beat, climax, denouement, button shot.
- Cinematography: wide, medium close-up, close-up, POV, dolly in, tracking, pan, tilt, gimbal, drone.
- Motion: STATIC, MICRO, SUBTLE, MODERATE. Default to SUBTLE unless user requests more.
- Tools: Veo realistic camera, Kling stable hand motion, Seedance short clips, Runway parallax, Pika subject lock."""

EXAMPLE_BLOCK = """Example scene, do NOT copy values:
{
  "scene_number": 1,
  "scene_title": "Cold Open Reveal",
  "scene_purpose": "Opening hook that introduces the product and setting.",
  "image_prompt": "Placeholder subject in a clean studio, 35mm lens, soft key light, 16:9, 2K, high detail.",
  "video_animation_prompt": "Subtle push-in while the subject breathes naturally and the background light shifts softly.",
  "continuity_notes": "Carry the same outfit, product color, and blue accent palette.",
  "duration_hint": "2-3s",
  "negative_prompt": "identity drift, warped hands, product morphing, text artifacts"
}"""

LENGTH_GUIDANCE = """Length guidance:
- scene_purpose: maximum 20 words.
- image_prompt: 30-60 words.
- video_animation_prompt: 20-40 words, subtle motion by default.
- continuity_notes: maximum 25 words.
- negative_prompt: 5-10 short comma-separated phrases."""

AVOID_LIST = """Avoid:
- Do not use the same lighting, lens, or angle for every scene.
- Do not repeat image_prompt content inside continuity_notes.
- Do not include more than 3 motion verbs in one video_animation_prompt.
- Avoid DRAMATIC motion unless user asks for it.
- Final scene must have a clear closing or button shot."""

REQUIRED_KEYS = [
    "scene_number",
    "scene_title",
    "scene_purpose",
    "image_prompt",
    "video_animation_prompt",
    "continuity_notes",
    "duration_hint",
    "negative_prompt",
]

_EXPECTED_SCENE_COUNT: contextvars.ContextVar[int] = contextvars.ContextVar("storyboard_expected_scene_count", default=9)


def build_instruction(ctx: ModeContext) -> str:
    expected = coerce_scene_count(ctx.user_input)
    _EXPECTED_SCENE_COUNT.set(expected)
    scene_note = f"Backend parsed expected scene count: {expected}. The JSON array length must be exactly {expected}."
    return build_instruction_common(
        ctx,
        TASK_BLOCK,
        SCHEMA_BLOCK,
        DOMAIN_VOCAB,
        EXAMPLE_BLOCK,
        LENGTH_GUIDANCE,
        AVOID_LIST,
        scene_note,
    )


def validate_output(text: str) -> dict[str, Any] | None:
    clean = strip_markdown_fence(text)
    arr, parse_error = parse_json_strict(text, original=text)
    if parse_error:
        return parse_error
    if not isinstance(arr, list):
        return error("INVALID_JSON_SHAPE", "Expected a JSON array.", clean)
    expected = _EXPECTED_SCENE_COUNT.get()
    if len(arr) != expected:
        return error("INVALID_SCENE_COUNT", f"Expected exactly {expected} scenes.", clean)
    seen: set[int] = set()
    for index, item in enumerate(arr, start=1):
        shape_error = require_list_keys(item, REQUIRED_KEYS, clean, f"Scene {index}")
        if shape_error:
            return shape_error
        number = coerce_scene_number(item.get("scene_number"))
        if number is None or number < 1 or number > expected or number in seen:
            return error("INVALID_SCENE_NUMBER", f"scene_number must be unique integers 1..{expected}.", clean)
        if not str(item.get("image_prompt") or "").strip():
            return error("INVALID_JSON_SHAPE", f"Scene {index} image_prompt must be non-empty.", clean)
        if not str(item.get("video_animation_prompt") or "").strip():
            return error("INVALID_JSON_SHAPE", f"Scene {index} video_animation_prompt must be non-empty.", clean)
        if not str(item.get("negative_prompt") or "").strip():
            return error("INVALID_JSON_SHAPE", f"Scene {index} negative_prompt must be non-empty.", clean)
        seen.add(number)
    return None


SPEC = ModeSpec(
    MODE_ID,
    MODE_LABEL,
    MODE_PURPOSE,
    MODE_USAGE,
    "json",
    True,
    0.7,
    5000,
    build_instruction,
    validate_output,
    SYSTEM_PERSONA,
    PROMPT_VERSION,
)
