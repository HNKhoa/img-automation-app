from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ENDPOINTS = (
    "https://gen.pollinations.ai/v1/chat/completions",
    "https://text.pollinations.ai/openai",
)


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


@dataclass(frozen=True)
class AppConfig:
    pollinations_api_key: str
    pollinations_endpoints: tuple[str, ...]
    default_model: str
    request_timeout_seconds: int
    chromium_profile_manager_url: str = "http://127.0.0.1:58001"
    chromium_automation_port: int = 0
    chromium_profile_id: str = ""
    chromium_startup_timeout_ms: int = 30000
    chromium_request_timeout_ms: int = 15000
    chromium_default_tab_id: int = 0
    chromium_download_dir: str = ""
    chromium_generation_timeout_ms: int = 240000

    @classmethod
    def from_env(cls, env_path: Path) -> AppConfig:
        file_values = _load_env_file(env_path)

        def get(name: str, default: str = "") -> str:
            return os.environ.get(name) or file_values.get(name) or default

        timeout_raw = get("REQUEST_TIMEOUT_SECONDS", "90")
        try:
            timeout = max(10, min(180, int(timeout_raw)))
        except ValueError:
            timeout = 90
        chromium_port = _parse_int(get("CHROMIUM_AUTOMATION_PORT"), 0, 0, 65535)
        chromium_startup_timeout = _parse_int(get("CHROMIUM_STARTUP_TIMEOUT_MS"), 30000, 5000, 120000)
        chromium_request_timeout = _parse_int(get("CHROMIUM_REQUEST_TIMEOUT_MS"), 15000, 3000, 60000)
        chromium_tab_id = _parse_int(get("CHROMIUM_DEFAULT_TAB_ID"), 0, 0, 100)
        chromium_generation_timeout = _parse_int(get("CHROMIUM_GENERATION_TIMEOUT_MS"), 240000, 30000, 600000)

        endpoints_raw = get("POLLINATIONS_ENDPOINTS") or get("POLLINATIONS_ENDPOINT")
        endpoints = _parse_endpoints(endpoints_raw)

        return cls(
            pollinations_api_key=get("POLLINATIONS_API_KEY"),
            pollinations_endpoints=endpoints,
            default_model=get("DEFAULT_MODEL", "gpt-5.4-nano"),
            request_timeout_seconds=timeout,
            chromium_profile_manager_url=get("CHROMIUM_PROFILE_MANAGER_URL", "http://127.0.0.1:58001").rstrip("/"),
            chromium_automation_port=chromium_port,
            chromium_profile_id=get("CHROMIUM_PROFILE_ID"),
            chromium_startup_timeout_ms=chromium_startup_timeout,
            chromium_request_timeout_ms=chromium_request_timeout,
            chromium_default_tab_id=chromium_tab_id,
            chromium_download_dir=get("CHROMIUM_DOWNLOAD_DIR"),
            chromium_generation_timeout_ms=chromium_generation_timeout,
        )

    def public_dict(self) -> dict[str, object]:
        return {
            "has_api_key": bool(self.pollinations_api_key),
            "endpoints": list(self.pollinations_endpoints),
            "endpoint_count": len(self.pollinations_endpoints),
            "default_model": self.default_model,
            "request_timeout_seconds": self.request_timeout_seconds,
            "chromium_profile_manager_url": self.chromium_profile_manager_url,
            "chromium_automation_port": self.chromium_automation_port,
            "chromium_profile_id": self.chromium_profile_id,
            "has_chromium_profile_id": bool(self.chromium_profile_id),
            "chromium_download_dir": self.chromium_download_dir,
        }


def _parse_endpoints(value: str | None) -> tuple[str, ...]:
    raw_items = value.split(",") if value else list(DEFAULT_ENDPOINTS)
    endpoints: list[str] = []
    seen: set[str] = set()
    for raw in raw_items:
        endpoint = raw.strip()
        if not endpoint or endpoint in seen:
            continue
        if not endpoint.startswith(("http://", "https://")):
            continue
        endpoints.append(endpoint)
        seen.add(endpoint)
    if not endpoints:
        raise ValueError("POLLINATIONS_ENDPOINTS must include at least one http(s) endpoint.")
    return tuple(endpoints)


def _parse_int(value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))
