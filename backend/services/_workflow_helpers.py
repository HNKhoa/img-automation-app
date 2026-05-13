from __future__ import annotations

from typing import Any

from backend.services.pollinations_client import PollinationsError


def workflow_error(code: str, message: str, **extra: Any) -> dict[str, Any]:
    error = {"code": code, "message": message}
    error.update(extra)
    return {"ok": False, "error": error}


def pollinations_error(exc: PollinationsError) -> dict[str, Any]:
    return {"ok": False, "error": {"code": exc.code, "message": exc.message, "status": exc.status}}


def invalid_model_output(validation_error: dict[str, Any]) -> dict[str, Any]:
    raw_output = validation_error.get("raw_output")
    payload: dict[str, Any] = {
        "code": "INVALID_MODEL_OUTPUT",
        "message": validation_error.get("message", "Model output did not match the required schema."),
        "detail": validation_error,
    }
    if raw_output is not None:
        payload["raw_output"] = raw_output
    return {"ok": False, "error": payload}
