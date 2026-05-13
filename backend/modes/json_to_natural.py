from __future__ import annotations

import re
from typing import Any

from backend.constants import GENERATION_MODE_IDS
from backend.modes.base import ModeContext, ModeSpec, build_instruction_common, error, strip_markdown_fence

MODE_ID = GENERATION_MODE_IDS["JSON_TO_NATURAL"]
MODE_LABEL = "JSON sang prompt tu nhien"
MODE_PURPOSE = "Chuyen JSON prompt thanh cau lenh tu nhien, de dung cho AI tao anh hoac video."
MODE_USAGE = "Dan JSON prompt vao o nhap. He thong se chuyen thanh prompt van xuoi tieng Anh, giu lai cac chi tiet quan trong va negative prompt."

TASK_BLOCK = """Task:
Convert the pasted JSON prompt into natural English prompt text.
Return exactly two sections and no extra sections."""

FORMAT_BLOCK = """Required output:
NATURAL PROMPT:
[one polished natural-language prompt, preserving all important visual details, style, aspect ratio, resolution, camera, lighting, quality, subject, background, constraints, and reference consistency]

NEGATIVE PROMPT:
[a concise negative prompt preserving all negative_prompt and constraint details]

Fallback rule:
If the input is not valid JSON, infer the intended structure from the text and still return the two required sections."""

DOMAIN_VOCAB = """Domain vocabulary:
- Natural prompt flow: subject, environment, camera, lighting, material detail, motion or pose, style, constraints.
- Translation: preserve JSON keys without exposing raw key names unless useful.
- Negative prompt: merge negative_prompt, constraints, and avoid fields into one concise list."""

EXAMPLE_BLOCK = """Example shape, do NOT copy values:
NATURAL PROMPT:
A production-ready natural prompt built from the pasted JSON.

NEGATIVE PROMPT:
bad anatomy, warped details, text artifacts"""

LENGTH_GUIDANCE = """Length guidance:
- NATURAL PROMPT: one dense paragraph, 80-180 words.
- NEGATIVE PROMPT: one comma-separated line.
- Preserve all important input details without adding new facts."""

AVOID_LIST = """Avoid:
- Do not add a third heading.
- Do not summarize away constraints.
- Do not send or request images for this mode."""

SYSTEM_PERSONA = (
    "You are a prompt editor who converts structured JSON prompts into natural production-ready language "
    "without losing details."
)
PROMPT_VERSION = f"{MODE_ID}/v2"

SECTION_RE = re.compile(r"^([A-Z][A-Z\s]+):", re.MULTILINE)


def build_instruction(ctx: ModeContext) -> str:
    return build_instruction_common(ctx, TASK_BLOCK, FORMAT_BLOCK, DOMAIN_VOCAB, EXAMPLE_BLOCK, LENGTH_GUIDANCE, AVOID_LIST)


def validate_output(text: str) -> dict[str, Any] | None:
    clean = strip_markdown_fence(text)
    matches = list(SECTION_RE.finditer(clean))
    titles = [re.sub(r"\s+", " ", match.group(1).upper()).strip() for match in matches]
    if titles != ["NATURAL PROMPT", "NEGATIVE PROMPT"]:
        return error("INVALID_SECTIONS", "Expected exactly NATURAL PROMPT then NEGATIVE PROMPT.", clean)
    return None


SPEC = ModeSpec(
    MODE_ID,
    MODE_LABEL,
    MODE_PURPOSE,
    MODE_USAGE,
    "text",
    False,
    0.45,
    2048,
    build_instruction,
    validate_output,
    SYSTEM_PERSONA,
    PROMPT_VERSION,
)
