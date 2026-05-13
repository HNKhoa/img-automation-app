from __future__ import annotations

import unittest

from backend.constants import GENERIC_MODE_IDS
from backend.modes import REGISTRY, list_generation_modes


class ModeRegistryTests(unittest.TestCase):
    def test_registry_covers_all_generic_ids(self) -> None:
        self.assertEqual(set(REGISTRY), set(GENERIC_MODE_IDS))

    def test_specs_are_valid(self) -> None:
        for spec in REGISTRY.values():
            self.assertTrue(callable(spec.build_instruction))
            self.assertTrue(callable(spec.validate_output))
            self.assertIn(spec.output_type, {"json", "text"})
            self.assertGreaterEqual(spec.default_temperature, 0)
            self.assertLessEqual(spec.default_temperature, 2)
            self.assertGreaterEqual(spec.max_output_tokens, 256)

    def test_bootstrap_shape_is_json_serializable(self) -> None:
        modes = list_generation_modes()
        self.assertEqual(len(modes), 7)
        self.assertEqual(modes[0]["kind"], "outfit")
        self.assertEqual(sum(1 for item in modes if item["kind"] == "generic"), 6)


if __name__ == "__main__":
    unittest.main()
