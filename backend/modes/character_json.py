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

MODE_ID = GENERATION_MODE_IDS["CHARACTER_JSON"]
MODE_LABEL = "JSON nhan vat"
MODE_PURPOSE = "Tao JSON chi tiet cho mot nhan vat hoac mot anh chan dung."
MODE_USAGE = "Nhap mo ta nhan vat, trang phuc, dang dung, bieu cam va boi canh. Co the tai anh tham chieu de AI bam sat khuon mat, toc va outfit."

TASK_BLOCK = """Task:
Create exactly one image prompt as valid JSON for a single character or portrait.
Do not include Markdown. Do not include explanations."""

SCHEMA_BLOCK = """Required JSON schema with leaf type hints:
{
  "subject": {
    "identity": "string, 1-2 sentences",
    "age_range": "string|null",
    "gender_presentation": "string",
    "face": "string, structure/skin/eyes/nose/lips/jawline",
    "hair": "string, color/length/style",
    "body": "string, build/posture",
    "expression": "string",
    "outfit": "string, garment/material/color/fit",
    "styling": "string, makeup/grooming/accessories layering"
  },
  "accessories": { "items": ["string"], "notes": "string" },
  "photography": {
    "lens": "string, e.g. '85mm portrait'",
    "aperture": "string, e.g. 'f/2.8 shallow DoF'",
    "camera_angle": "string",
    "framing": "string, e.g. 'medium close-up, headroom 5%'",
    "lighting": "string, named setup",
    "aspect_ratio": "string",
    "resolution": "string",
    "quality": "string",
    "render_detail": "string"
  },
  "background": { "location": "string", "palette": ["string"], "atmosphere": "string", "depth": "string" },
  "the_vibe": { "mood": "string", "art_direction": "string", "aesthetic": "string" },
  "constraints": ["string", "min 4 items, identity/anatomy/outfit/composition"],
  "negative_prompt": ["string", "min 8 items"]
}

Return exactly these 7 top-level keys."""

DOMAIN_VOCAB = """Domain vocabulary:
- Lens: 50mm natural, 85mm portrait, 100mm macro, shallow depth of field, clean headroom.
- Lighting: rembrandt, butterfly, split, three-point, ring light, golden hour, blue hour, neon edge.
- Expression: subtle smile, contemplative, candid laugh, stoic, intense gaze, relaxed confidence.
- Genre: editorial, lookbook, lifestyle, corporate headshot, character art, fantasy, sci-fi, realistic, anime-influenced."""

EXAMPLE_BLOCK = """Mini example shape, do NOT copy values:
{
  "subject": {"identity": "Test character placeholder, not final content.", "age_range": "25-30"},
  "constraints": ["preserve identity", "clean anatomy", "consistent outfit", "balanced composition"],
  "negative_prompt": ["deformed hands", "distorted face", "bad anatomy", "extra limbs", "warped clothing", "wrong logos", "text artifacts", "low resolution"]
}"""

LENGTH_GUIDANCE = """Length guidance:
- Leaf strings: one concise sentence, maximum 25 words.
- the_vibe total: 2-3 short phrases.
- constraints and negative_prompt must be concrete and production-safe."""

AVOID_LIST = """Avoid:
- Avoid generic praise words: beautiful, stunning, amazing.
- Do not repeat subject.identity inside the_vibe.
- Do not return fewer than 8 negative_prompt items."""

SYSTEM_PERSONA = (
    "You are a senior portrait art director with 15 years of experience in editorial photography, "
    "character design, and brand mascot creation. You write production-ready prompts that preserve "
    "identity and character consistency."
)
PROMPT_VERSION = f"{MODE_ID}/v2"

REQUIRED_KEYS = ["subject", "accessories", "photography", "background", "the_vibe", "constraints", "negative_prompt"]


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
    for key in ("subject", "accessories", "photography", "background", "the_vibe"):
        if not isinstance(obj[key], dict):
            return error("INVALID_JSON_SHAPE", f"{key} must be an object.", clean)
    subject_identity = obj["subject"].get("identity")
    if not isinstance(subject_identity, str) or not subject_identity.strip():
        return error("INVALID_JSON_SHAPE", "subject.identity must be a non-empty string.", clean)
    if not isinstance(obj["constraints"], list) or len(obj["constraints"]) < 4:
        return error("INVALID_JSON_SHAPE", "constraints must be a list with at least 4 items.", clean)
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
    0.7,
    4096,
    build_instruction,
    validate_output,
    SYSTEM_PERSONA,
    PROMPT_VERSION,
)
