"""Vision tier instruction (gemini-flash-lite-3.1) - outputs analysis JSON."""
from __future__ import annotations

VISION_PROMPT_VERSION = "v1"
VISION_MODEL = "gemini-flash-lite-3.1"

_SYSTEM = (
    "You are a precise multimodal analyst. Look at the labeled reference images and "
    "return ONLY a compact JSON object describing identity, outfit, and background. "
    "Do NOT invent details. Do NOT include markdown fences or commentary."
)

_SCHEMA_HINT = """{
  "identity":   {"face": "...", "skin_tone": "...", "hair": "...", "body": "...", "gender_presentation": "..."},
  "outfit":     {"items": ["..."], "colors": ["..."], "fabrics": ["..."], "fit": "...", "accessories": ["..."]},
  "background": {"scene": "...", "lighting": "...", "palette": "...", "mood": "..."} ,
  "notes":      ["..."]
}"""


def build_vision_instruction(quality_profile: str = "balanced", analysis_mode: str = "full") -> str:
    detail = "Be exhaustive on every leaf." if analysis_mode == "full" else "Be terse: <= 25 words per leaf field."
    return (
        f"{_SYSTEM}\n\n"
        f"Quality profile: {quality_profile}. Mode: {analysis_mode}. {detail}\n"
        f"Return JSON exactly matching this schema (no extra keys; use null for missing background):\n"
        f"{_SCHEMA_HINT}"
    )
