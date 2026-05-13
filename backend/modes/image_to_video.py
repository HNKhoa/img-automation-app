from __future__ import annotations

from typing import Any

from backend.constants import GENERATION_MODE_IDS
from backend.modes.base import (
    ModeContext,
    ModeSpec,
    build_instruction_common,
    error,
    parse_json_strict,
    require_dict_keys,
    strip_markdown_fence,
)

MODE_ID = GENERATION_MODE_IDS["IMAGE_TO_VIDEO"]
MODE_LABEL = "Prompt anh sang video"
MODE_PURPOSE = "Chuyen mo ta hoac anh thanh prompt chuyen dong de dung cho cong cu tao video AI."
MODE_USAGE = "Nhap prompt anh hien co hoac tai anh tham chieu. He thong se tao chuyen dong nhe cho nhan vat, camera, boi canh va san pham de han che lech mat, lech do, meo san pham."

TASK_BLOCK = """Task:
Create a valid JSON image-to-video prompt.
Do not include Markdown. Do not include explanations."""

SCHEMA_BLOCK = """Required JSON schema:
{
  "duration": "",
  "main_subject": "",
  "motion_intensity": "STATIC|MICRO|SUBTLE|MODERATE",
  "target_tools": ["Veo", "Kling", "Seedance", "Runway", "Pika"],
  "character_motion": "",
  "camera_movement": "",
  "background_motion": "",
  "product_motion": "",
  "lighting_motion": "",
  "first_frame_lock": "",
  "last_frame_goal": "",
  "constraints": [],
  "negative_prompt": []
}

Requirements:
- Use subtle motion that preserves face, outfit, anatomy, product shape, logo, and material.
- Camera movement should be realistic and controlled.
- Avoid aggressive changes, morphing, identity drift, extra fingers, warped products, logo distortion, and unstable clothing.
- Include style, aspect ratio, resolution, and quality."""

DOMAIN_VOCAB = """Domain vocabulary:
- Motion: ease-in/ease-out, parallax, micro-tremor, subtle drift, breathing motion, controlled push-in.
- Camera: locked-off, slow dolly in, gentle orbit, gimbal push, parallax slide, rack focus.
- Tools: Veo realistic motion, Kling hand stability, Seedance short clip, Runway image lock, Pika stylized motion.
- Product motion: turntable, hand reveal, label catchlight, steam drift, liquid swirl, fabric sway."""

EXAMPLE_BLOCK = """Mini example, do NOT copy values:
{
  "duration": "5s",
  "motion_intensity": "SUBTLE",
  "target_tools": ["Veo", "Kling"],
  "main_subject": "Placeholder product on a clean surface",
  "negative_prompt": ["identity drift", "morphing", "warped hands", "logo distortion", "jitter", "extra limbs", "text artifacts", "blur"]
}"""

LENGTH_GUIDANCE = """Length guidance:
- Motion fields: 1 concise sentence each.
- constraints: at least 3 items.
- negative_prompt: at least 8 items."""

AVOID_LIST = """Avoid:
- Avoid aggressive morphing or identity changes.
- Do not use dramatic camera motion unless user asks.
- Do not let product logos, faces, or hands deform."""

SYSTEM_PERSONA = (
    "You are an image-to-video director for AI video tools. You convert still images into stable, "
    "subtle motion prompts that preserve identity, product shape, and first-frame consistency."
)
PROMPT_VERSION = f"{MODE_ID}/v2"

REQUIRED_KEYS = [
    "duration",
    "main_subject",
    "motion_intensity",
    "target_tools",
    "character_motion",
    "camera_movement",
    "background_motion",
    "product_motion",
    "lighting_motion",
    "first_frame_lock",
    "last_frame_goal",
    "constraints",
    "negative_prompt",
]


def build_instruction(ctx: ModeContext) -> str:
    return build_instruction_common(ctx, TASK_BLOCK, SCHEMA_BLOCK, DOMAIN_VOCAB, EXAMPLE_BLOCK, LENGTH_GUIDANCE, AVOID_LIST)


def validate_output(text: str) -> dict[str, Any] | None:
    clean = strip_markdown_fence(text)
    obj, parse_error = parse_json_strict(text, original=text)
    if parse_error:
        return parse_error
    shape_error = require_dict_keys(obj, REQUIRED_KEYS, clean)
    if shape_error:
        return shape_error
    import re

    if not isinstance(obj["duration"], str) or not re.match(r"^(?:PT)?\d+S?$|^\d+s$", obj["duration"], re.IGNORECASE):
        return error("INVALID_JSON_SHAPE", "duration must look like 5s or PT5S.", clean)
    if obj["motion_intensity"] not in {"STATIC", "MICRO", "SUBTLE", "MODERATE"}:
        return error("INVALID_JSON_SHAPE", "motion_intensity must be STATIC, MICRO, SUBTLE, or MODERATE.", clean)
    if not isinstance(obj["target_tools"], list) or not obj["target_tools"]:
        return error("INVALID_JSON_SHAPE", "target_tools must be a non-empty list.", clean)
    if not isinstance(obj["constraints"], list) or len(obj["constraints"]) < 3:
        return error("INVALID_JSON_SHAPE", "constraints must be a list with at least 3 items.", clean)
    if not isinstance(obj["negative_prompt"], list) or len(obj["negative_prompt"]) < 8:
        return error("INVALID_JSON_SHAPE", "negative_prompt must be a list with at least 8 items.", clean)
    return None


SPEC = ModeSpec(
    MODE_ID,
    MODE_LABEL,
    MODE_PURPOSE,
    MODE_USAGE,
    "json",
    True,
    0.65,
    4096,
    build_instruction,
    validate_output,
    SYSTEM_PERSONA,
    PROMPT_VERSION,
)
