from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.config import AppConfig


class ConfigTests(unittest.TestCase):
    def test_env_file_with_utf8_bom_loads_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("\ufeffPOLLINATIONS_API_KEY=sk_test\n", encoding="utf-8")
            config = AppConfig.from_env(env_path)
        self.assertEqual(config.pollinations_api_key, "sk_test")


if __name__ == "__main__":
    unittest.main()
