"""Default negative prompt + helper to ensure required keywords are present."""
from __future__ import annotations

DEFAULT_NEGATIVE = (
    "wrong face, identity drift, face distortion, different person, westernized face, "
    "gender change, feminized face, masculinized face, altered facial structure, "
    "outfit mismatch, wrong outfit color, warped clothing, unrealistic fabric folds, "
    "wrong pose, pose change, background mismatch, AI face, plastic skin, "
    "over-smoothed skin, low quality, blurry, soft focus, text, watermark, logo"
)

REQUIRED_KEYWORDS = ("wrong face", "outfit mismatch", "identity drift")


def ensure_keywords(negative_section: str) -> str:
    text = (negative_section or "").strip()
    lower = text.lower()
    missing = [kw for kw in REQUIRED_KEYWORDS if kw not in lower]
    if not missing:
        return text
    if not text:
        return ", ".join(missing)
    return text.rstrip(",.") + ", " + ", ".join(missing)
