"""File-JSON 2-tier cache (analysis/, final/) with atomic writes + TTL."""
from __future__ import annotations

import json
import os
import platform
import tempfile
import time
from pathlib import Path
from typing import Any

TTL_SECONDS = {
    "analysis": 30 * 24 * 3600,
    "final": 7 * 24 * 3600,
}
TIERS = frozenset(TTL_SECONDS)


def default_cache_dir() -> Path:
    override = os.environ.get("CACHE_DIR")
    if override:
        return Path(override)
    if platform.system().lower() == "windows":
        local = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        return local / "ImgAutomationApp" / "cache"
    return Path.home() / ".cache" / "img-automation-app"


class CacheService:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or default_cache_dir()
        for tier in TIERS:
            (self.root / tier).mkdir(parents=True, exist_ok=True)

    def get(self, tier: str, key: str) -> dict[str, Any] | None:
        self._validate_tier(tier)
        path = self._path(tier, key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        ts = float(payload.get("_ts", 0))
        if time.time() - ts > TTL_SECONDS[tier]:
            return None
        value = payload.get("value")
        return value if isinstance(value, dict) else None

    def set(self, tier: str, key: str, value: dict[str, Any]) -> None:
        self._validate_tier(tier)
        path = self._path(tier, key)
        envelope = {"_ts": time.time(), "value": value}
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            delete=False,
            suffix=".tmp",
        ) as tmp:
            json.dump(envelope, tmp, ensure_ascii=False)
            tmp_path = tmp.name
        os.replace(tmp_path, path)

    def delete(self, tier: str, key: str) -> None:
        self._validate_tier(tier)
        try:
            self._path(tier, key).unlink(missing_ok=True)
        except OSError:
            pass

    @staticmethod
    def _validate_tier(tier: str) -> None:
        if tier not in TIERS:
            raise ValueError(f"unknown tier: {tier}")

    def _path(self, tier: str, key: str) -> Path:
        safe = "".join(ch for ch in key if ch.isalnum() or ch in ("-", "_"))[:64]
        return self.root / tier / f"{safe}.json"
