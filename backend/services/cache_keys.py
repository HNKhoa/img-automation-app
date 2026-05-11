"""Cache key derivation for analysis + final tiers."""
from __future__ import annotations

import hashlib
import re

_WS = re.compile(r"\s+")
_ROLES_ORDER = ("model", "outfit", "background")


def _hash(*parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return digest[:32]


def normalize_user_request(text: str | None) -> str:
    return _WS.sub(" ", (text or "").strip().lower())


def analysis_key(
    role_hashes: dict[str, str],
    vision_model: str,
    vision_prompt_version: str,
    quality_profile: str,
) -> str:
    role_part = "|".join(f"{r}:{role_hashes.get(r, '-')}" for r in _ROLES_ORDER)
    return _hash("analysis", role_part, vision_model, vision_prompt_version, quality_profile)


def final_key(
    analysis_k: str,
    user_request_normalized: str,
    target_rule: str,
    builder_model: str,
    builder_prompt_version: str,
    critic_flag: bool,
) -> str:
    return _hash(
        "final",
        analysis_k,
        user_request_normalized,
        target_rule,
        builder_model,
        builder_prompt_version,
        "critic=1" if critic_flag else "critic=0",
    )
