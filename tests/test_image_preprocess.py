from __future__ import annotations

import base64
import io
import unittest

from PIL import Image

from backend.services.image_preprocess import preprocess


def _make_data_url(fmt: str, size: tuple[int, int] = (2000, 1500), mode: str = "RGB") -> str:
    img = Image.new(mode, size, (200, 100, 50) if mode == "RGB" else (200, 100, 50, 255))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    payload = base64.b64encode(buf.getvalue()).decode("ascii")
    mime = {"JPEG": "jpeg", "PNG": "png", "WEBP": "webp"}[fmt]
    return f"data:image/{mime};base64,{payload}"


class ImagePreprocessTests(unittest.TestCase):
    def test_resizes_long_side_for_balanced(self) -> None:
        out = preprocess(_make_data_url("JPEG"), "balanced")
        self.assertLessEqual(max(out.width, out.height), 1280)

    def test_long_side_for_high(self) -> None:
        out = preprocess(_make_data_url("JPEG"), "high")
        self.assertLessEqual(max(out.width, out.height), 1536)

    def test_sha256_stable_across_calls(self) -> None:
        url = _make_data_url("PNG")
        self.assertEqual(preprocess(url).sha256, preprocess(url).sha256)

    def test_rgba_normalized_to_rgb(self) -> None:
        out = preprocess(_make_data_url("PNG", mode="RGBA"))
        self.assertGreater(out.payload_bytes, 0)

    def test_invalid_data_url_rejected(self) -> None:
        with self.assertRaises(ValueError):
            preprocess("not-a-data-url")


if __name__ == "__main__":
    unittest.main()
