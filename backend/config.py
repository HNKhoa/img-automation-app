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

    for raw_line in path.read_text(encoding="utf-8").splitlines():
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

        endpoints_raw = get("POLLINATIONS_ENDPOINTS") or get("POLLINATIONS_ENDPOINT")
        endpoints = _parse_endpoints(endpoints_raw)

        return cls(
            pollinations_api_key=get("POLLINATIONS_API_KEY"),
            pollinations_endpoints=endpoints,
            default_model=get("DEFAULT_MODEL", "gpt-5.4-nano"),
            request_timeout_seconds=timeout,
        )

    def public_dict(self) -> dict[str, object]:
        return {
            "has_api_key": bool(self.pollinations_api_key),
            "endpoints": list(self.pollinations_endpoints),
            "endpoint_count": len(self.pollinations_endpoints),
            "default_model": self.default_model,
            "request_timeout_seconds": self.request_timeout_seconds,
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
