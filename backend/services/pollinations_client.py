from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

cffi_requests: Any = None
_CURL_CFFI_IMPORT_ERROR: ImportError | None = None

try:
    from curl_cffi import requests as _imported_cffi_requests
except ImportError as exc:
    _CURL_CFFI_IMPORT_ERROR = exc
else:
    cffi_requests = cast(Any, _imported_cffi_requests)

if TYPE_CHECKING:
    from backend.config import AppConfig


@dataclass
class PollinationsError(Exception):
    code: str
    message: str
    status: int | None = None
    retry_after: int | None = None


class PollinationsClient:
    IMPERSONATE_PROFILES = ("chrome124", "chrome120", "chrome110", "edge101", "safari17_0")
    CLOUDFLARE_MARKERS = (
        "cloudflare_error",
        "error 1010",
        "error 1020",
        "access denied",
        "attention required",
        "cf-ray",
        "cf-chl-bypass",
    )
    RETRYABLE_STATUSES = (502, 503, 504)

    def __init__(self, endpoints: tuple[str, ...], timeout_seconds: int) -> None:
        if not endpoints:
            raise ValueError("PollinationsClient requires at least one endpoint.")
        self.endpoints = endpoints
        self.timeout_seconds = timeout_seconds
        self._preferred_endpoint: str | None = None

    @classmethod
    def from_config(cls, config: AppConfig) -> PollinationsClient:
        return cls(config.pollinations_endpoints, config.request_timeout_seconds)

    def chat_completion(self, api_key: str, body: dict[str, Any]) -> str:
        if not api_key:
            raise PollinationsError("MISSING_API_KEY", "Thieu Secret API key. Nhap key dang sk_ trong API Settings hoac file .env.")
        if not api_key.startswith("sk_"):
            raise PollinationsError("INVALID_API_KEY_FORMAT", "API key nen la secret key bat dau bang sk_.")

        last_error: PollinationsError | None = None
        for endpoint in self._ordered_endpoints():
            try:
                output = self._try_endpoint(endpoint, api_key, body)
            except PollinationsError as exc:
                if exc.code in {"CLOUDFLARE_ACCESS_DENIED", "NETWORK_ERROR", "TIMEOUT", "NOT_FOUND"}:
                    last_error = exc
                    continue
                raise
            self._preferred_endpoint = endpoint
            return output

        if last_error is not None:
            raise last_error
        raise PollinationsError("NO_ENDPOINT_AVAILABLE", "Khong co endpoint Pollinations kha dung.", 503)

    def _ordered_endpoints(self) -> list[str]:
        ordered: list[str] = []
        if self._preferred_endpoint and self._preferred_endpoint in self.endpoints:
            ordered.append(self._preferred_endpoint)
        for endpoint in self.endpoints:
            if endpoint not in ordered:
                ordered.append(endpoint)
        return ordered

    def _try_endpoint(self, endpoint: str, api_key: str, body: dict[str, Any]) -> str:
        last_error: PollinationsError | None = None
        for profile in self.IMPERSONATE_PROFILES:
            try:
                return self._request_with_profile(endpoint, profile, api_key, body)
            except PollinationsError as exc:
                if exc.code == "CLOUDFLARE_ACCESS_DENIED":
                    last_error = exc
                    continue
                raise
        if last_error is not None:
            raise last_error
        raise PollinationsError("CLOUDFLARE_ACCESS_DENIED", "Tat ca TLS impersonation profiles deu bi Cloudflare chan.", 403)

    def _request_with_profile(self, endpoint: str, profile: str, api_key: str, body: dict[str, Any]) -> str:
        if cffi_requests is None:
            raise PollinationsError(
                "MISSING_CURL_CFFI",
                "Cai dat thieu curl_cffi. Chay: pip install -r requirements.txt",
                500,
            ) from _CURL_CFFI_IMPORT_ERROR

        try:
            response = cffi_requests.post(
                endpoint,
                json=body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/plain, */*",
                },
                impersonate=cast(Any, profile),
                timeout=self.timeout_seconds,
                allow_redirects=True,
            )
            if response.status_code == 200:
                return self._extract_text(response.text)

            retry_after = self._parse_retry_after(response.headers.get("retry-after"))
            if response.status_code in self.RETRYABLE_STATUSES:
                time.sleep(max(1, min(10, retry_after or 2)))
                retry_response = cffi_requests.post(
                    endpoint,
                    json=body,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/plain, */*",
                    },
                    impersonate=cast(Any, profile),
                    timeout=self.timeout_seconds,
                    allow_redirects=True,
                )
                if retry_response.status_code == 200:
                    return self._extract_text(retry_response.text)
                retry_after = self._parse_retry_after(retry_response.headers.get("retry-after"))
                raise self._map_http_error(retry_response.status_code, retry_response.text, retry_after)

            raise self._map_http_error(response.status_code, response.text, retry_after)
        except PollinationsError:
            raise
        except cffi_requests.errors.RequestsError as exc:
            raise PollinationsError("NETWORK_ERROR", f"Loi ket noi Pollinations: {exc}") from exc
        except TimeoutError as exc:
            raise PollinationsError("TIMEOUT", "Request toi Pollinations bi timeout.", 504) from exc
        except Exception as exc:
            raise PollinationsError("UNEXPECTED_TRANSPORT_ERROR", str(exc)) from exc

    @staticmethod
    def _extract_text(raw: str) -> str:
        text = raw.strip()
        if not text:
            raise PollinationsError("EMPTY_RESPONSE", "Pollinations tra ve response rong.")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return text

        if isinstance(data, dict):
            output_text = data.get("output_text")
            if isinstance(output_text, str):
                return output_text.strip()
            for choice in data.get("choices", []) or []:
                if isinstance(choice, dict):
                    message = choice.get("message") or {}
                    content = message.get("content") if isinstance(message, dict) else None
                    if isinstance(content, str):
                        return content.strip()
                    choice_text = choice.get("text")
                    if isinstance(choice_text, str):
                        return choice_text.strip()
            text_value = data.get("text")
            if isinstance(text_value, str):
                return text_value.strip()
        raise PollinationsError("UNREADABLE_RESPONSE", "Khong doc duoc text tu response Pollinations.")

    @staticmethod
    def _parse_retry_after(value: str | None) -> int | None:
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    @classmethod
    def _map_http_error(cls, status: int, body_text: str, retry_after: int | None) -> PollinationsError:
        detail = cls._extract_error_detail(body_text)
        lower_body = body_text.lower()
        if status in (403, 503) and any(marker in lower_body for marker in cls.CLOUDFLARE_MARKERS):
            return PollinationsError(
                "CLOUDFLARE_ACCESS_DENIED",
                "Tat ca endpoint Pollinations dang bi Cloudflare chan. Hay dung Custom Relay URL hoac relay mac dinh da deploy.",
                status,
                retry_after,
            )
        mapping = {
            400: ("BAD_REQUEST", "Payload khong hop le hoac model khong nhan request nay."),
            401: ("UNAUTHORIZED", "API key sai, het han, hoac khong duoc quyen dung model."),
            403: ("FORBIDDEN", "API key khong duoc phep goi endpoint/model nay."),
            402: ("INSUFFICIENT_BALANCE", "Tai khoan khong du balance."),
            404: ("NOT_FOUND", "Endpoint hoac model khong ton tai."),
            413: ("PAYLOAD_TOO_LARGE", "Payload anh qua lon. Giam so anh hoac kich thuoc anh."),
            422: ("UNPROCESSABLE_ENTITY", "Payload bi tu choi vi sai schema hoac du lieu anh."),
            429: ("RATE_LIMITED", "Bi rate limit. Cho mot luc roi thu lai."),
            502: ("BAD_GATEWAY", "Provider/Pollinations bad gateway. App se retry mot lan."),
            503: ("SERVICE_UNAVAILABLE", "Provider dang qua tai hoac khong san sang. App se retry mot lan."),
            504: ("UPSTREAM_TIMEOUT", "Provider timeout. Thu prompt ngan hon hoac it anh hon."),
        }
        code, message = mapping.get(status, ("HTTP_ERROR", f"Pollinations HTTP {status}."))
        if detail:
            message = f"{message} Chi tiet: {detail}"
        return PollinationsError(code, message, status, retry_after)

    @staticmethod
    def _extract_error_detail(body_text: str) -> str:
        if not body_text:
            return ""
        try:
            data = json.loads(body_text)
        except json.JSONDecodeError:
            return body_text[:220]

        if isinstance(data, dict):
            for key in ("error", "message", "detail", "title"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()[:220]
        return body_text[:220]
