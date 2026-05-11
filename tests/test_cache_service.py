from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.services.cache_service import CacheService


class CacheServiceTests(unittest.TestCase):
    def test_round_trip_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            svc = CacheService(Path(tmp))
            svc.set("analysis", "abc", {"x": 1, "nested": [1, 2]})
            self.assertEqual(svc.get("analysis", "abc"), {"x": 1, "nested": [1, 2]})

    def test_round_trip_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            svc = CacheService(Path(tmp))
            svc.set("final", "k1", {"output": "MAIN PROMPT:\n..."})
            self.assertIn("output", svc.get("final", "k1"))

    def test_miss_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(CacheService(Path(tmp)).get("final", "missing"))

    def test_atomic_write_no_leftover_tmp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            svc = CacheService(Path(tmp))
            svc.set("final", "k", {"v": "x"})
            self.assertFalse(list(Path(tmp).rglob("*.tmp")))

    def test_unknown_tier_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                CacheService(Path(tmp)).get("bogus", "k")


if __name__ == "__main__":
    unittest.main()
