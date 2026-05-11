"""Pillow-based preprocess: strip EXIF, normalize orientation, resize, encode JPEG."""
from __future__ import annotations

import base64
import hashlib
import io
from dataclasses import dataclass
from typing import cast

from PIL import Image, ImageOps

PROFILE_LONG_SIDE = {"draft": 1024, "balanced": 1280, "high": 1536}
PROFILE_JPEG_Q = {"draft": 80, "balanced": 85, "high": 88}


@dataclass(frozen=True)
class ProcessedImage:
    jpeg_bytes: bytes
    sha256: str
    width: int
    height: int
    payload_bytes: int

    def to_data_url(self) -> str:
        b64 = base64.b64encode(self.jpeg_bytes).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"


def preprocess(data_url: str, profile: str = "balanced") -> ProcessedImage:
    if not isinstance(data_url, str) or not data_url.startswith("data:image/"):
        raise ValueError("data_url must start with data:image/")
    if "," not in data_url:
        raise ValueError("data_url missing base64 payload")
    _header, b64 = data_url.split(",", 1)
    try:
        raw = base64.b64decode(b64, validate=False)
    except Exception as exc:
        raise ValueError(f"invalid base64 payload: {exc}") from exc

    img = cast(Image.Image, Image.open(io.BytesIO(raw)))
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")

    long_side = PROFILE_LONG_SIDE.get(profile, 1280)
    width, height = img.size
    scale = min(1.0, long_side / float(max(width, height)))
    if scale < 1.0:
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    quality = PROFILE_JPEG_Q.get(profile, 85)
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    jpeg = buf.getvalue()

    return ProcessedImage(
        jpeg_bytes=jpeg,
        sha256=hashlib.sha256(jpeg).hexdigest(),
        width=img.size[0],
        height=img.size[1],
        payload_bytes=len(jpeg),
    )
