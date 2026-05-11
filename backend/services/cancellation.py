"""Per-request cancellation flag, checked at workflow checkpoints."""
from __future__ import annotations

import threading
from dataclasses import dataclass


@dataclass
class _Flag:
    cancelled: bool = False


class WorkflowCancellation:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._flags: dict[str, _Flag] = {}

    def register(self, request_id: str) -> None:
        with self._lock:
            self._flags[request_id] = _Flag()

    def cancel(self, request_id: str) -> bool:
        with self._lock:
            flag = self._flags.get(request_id)
            if flag is None:
                return False
            flag.cancelled = True
            return True

    def is_cancelled(self, request_id: str) -> bool:
        with self._lock:
            flag = self._flags.get(request_id)
            return bool(flag and flag.cancelled)

    def discard(self, request_id: str) -> None:
        with self._lock:
            self._flags.pop(request_id, None)
