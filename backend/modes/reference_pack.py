from __future__ import annotations

import re
from typing import Any

from backend.constants import GENERATION_MODE_IDS
from backend.modes.base import ModeContext, ModeSpec, build_instruction_common, error, strip_markdown_fence

MODE_ID = GENERATION_MODE_IDS["REFERENCE_PACK"]
MODE_LABEL = "Bo anh tham chieu"
MODE_PURPOSE = "Tao bo prompt anh tham chieu de giu dong nhat nhan vat, boi canh va san pham."
MODE_USAGE = "Nhap mo ta nhan vat, boi canh va san pham; hoac tai anh tham chieu de tao cac goc front view, side view, 3/4 view, close-up, texture va hero shot."

TASK_BLOCK = """Task:
Create a complete reference image prompt pack with exactly 3 groups."""

FORMAT_BLOCK = """Required groups:
=== Character Reference Pack ===
View 1 - front view:
[prompt 30-50 words including lens, lighting, angle, framing, aspect, resolution, style, negative cue]

=== Background Reference Pack ===
View 1 - wide establishing:
[prompt 30-50 words including lens, lighting, angle, framing, aspect, resolution, style, negative cue]

=== Product Reference Pack ===
View 1 - hero product:
[prompt 30-50 words including lens, lighting, angle, framing, aspect, resolution, style, negative cue]

Each group must include at least 4 views."""

DOMAIN_VOCAB = """Domain vocabulary:
- Character views: front, three-quarter, side, back, facial close-up, expression sheet, full-body hero, action pose.
- Background views: wide establishing, empty plate, hero angle, texture macro, day variant, night variant, camera-matched.
- Product views: hero, front, side, three-quarter, top-down, macro logo, scale reference, in-context, in-use.
- Lighting consistency: same key direction across views, controlled fill, neutral grey card reference."""

EXAMPLE_BLOCK = """Example view, do NOT copy values:
View 1 - front view:
Clean front reference of the placeholder subject, 50mm lens, eye-level framing, softbox key from camera left, neutral grey sweep, 1:1, 2K, precise color matching, avoid identity drift and warped details."""

LENGTH_GUIDANCE = """Length guidance:
- Each view prompt should be 30-50 words.
- Every view includes lens, lighting, angle, framing, aspect ratio, resolution, style, and one negative cue.
- Avoid short placeholder prompts."""

AVOID_LIST = """Avoid:
- Do not write view prompts shorter than 20 words.
- Do not repeat identical lighting and aspect in every view inside one group.
- Do not omit negative cue from any view."""

SYSTEM_PERSONA = (
    "You are a production designer and visual development artist. You assemble reference sheets that "
    "lock down characters, environments, and products for downstream production teams."
)
PROMPT_VERSION = f"{MODE_ID}/v2"

HEADINGS = ["Character Reference Pack", "Background Reference Pack", "Product Reference Pack"]


def build_instruction(ctx: ModeContext) -> str:
    return build_instruction_common(ctx, TASK_BLOCK, FORMAT_BLOCK, DOMAIN_VOCAB, EXAMPLE_BLOCK, LENGTH_GUIDANCE, AVOID_LIST)


def validate_output(text: str) -> dict[str, Any] | None:
    clean = strip_markdown_fence(text)
    lower = clean.lower()
    missing = [heading for heading in HEADINGS if heading.lower() not in lower]
    if missing:
        return error("MISSING_SECTIONS", "Missing required groups: " + ", ".join(missing), clean)
    group_matches = list(re.finditer(r"^===\s*(Character|Background|Product)\s+Reference Pack\s*===", clean, re.IGNORECASE | re.MULTILINE))
    if len(group_matches) != 3:
        group_matches = list(re.finditer(r"^(?:\d+\.\s*)?(Character|Background|Product)\s+Reference Pack\b.*$", clean, re.IGNORECASE | re.MULTILINE))
    for index, match in enumerate(group_matches):
        end = group_matches[index + 1].start() if index + 1 < len(group_matches) else len(clean)
        block = clean[match.end() : end]
        views = list(re.finditer(r"^View\s+\d+\s+-\s*[^:\n]+:\s*(.*)$", block, re.IGNORECASE | re.MULTILINE))
        if len(views) < 4:
            return error("MISSING_VIEWS", f"{match.group(0).strip()} must include at least 4 views.", clean)
        for view_index, view in enumerate(views):
            view_end = views[view_index + 1].start() if view_index + 1 < len(views) else len(block)
            prompt = (view.group(1) + block[view.end() : view_end]).strip()
            if len(prompt) < 20:
                return error("VIEW_TOO_SHORT", "Each reference view prompt must be at least 20 characters.", clean)
    return None


SPEC = ModeSpec(
    MODE_ID,
    MODE_LABEL,
    MODE_PURPOSE,
    MODE_USAGE,
    "text",
    True,
    0.7,
    4096,
    build_instruction,
    validate_output,
    SYSTEM_PERSONA,
    PROMPT_VERSION,
)
