"""Builder tier (gpt-5.4-nano), text-only. Switches output by target_model_rule."""
from __future__ import annotations

import json
from typing import Any

from backend.prompts.negative_prompts import DEFAULT_NEGATIVE

BUILDER_PROMPT_VERSION = "v1"
BUILDER_MODEL = "gpt-5.4-nano"


def build_builder_instruction(
    analysis_json: dict[str, Any],
    user_request: str,
    target_rule: str,
    style: str,
    aspect_ratio: str,
    resolution: str,
    quality: str,
) -> str:
    base = (
        "You are Super Prompt. Use the analysis JSON below as the only source of truth "
        "about the references (do NOT request more images).\n\n"
        f"User request: {user_request or '(none)'}\n"
        f"Style: {style} | Aspect: {aspect_ratio} | Resolution: {resolution} | Quality: {quality}\n\n"
        f"Analysis JSON:\n{json.dumps(analysis_json, ensure_ascii=False)}\n\n"
    )

    if target_rule == "gg_banana2":
        return base + (
            "Return ONLY a JSON object (no markdown fences) with keys:\n"
            '  "subject", "outfit", "background", "main_prompt", '
            '"negative_prompt", "reference_binding".\n'
            "Each value must be a string."
        )

    if target_rule == "gpt_image":
        return base + (
            "Return three top-level sections, in this order:\n"
            "MAIN PROMPT: (<= 250 words, terse, no restating obvious rules)\n"
            "NEGATIVE PROMPT:\n"
            "REFERENCE BINDING INSTRUCTIONS:\n"
            "If NEGATIVE PROMPT is missing identity/outfit-mismatch keywords from the default "
            f"negative list ({DEFAULT_NEGATIVE[:120]}...), add the missing ones."
        )

    return base + (
        "Return three top-level sections, in this order:\n"
        "MAIN PROMPT:\nNEGATIVE PROMPT:\nREFERENCE BINDING INSTRUCTIONS:\n"
        "Use the existing chatgpt_img conventions: identity-priority phrasing, "
        "explicit outfit transfer, paste-ready text."
    )
