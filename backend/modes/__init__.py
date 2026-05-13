from __future__ import annotations

from backend.constants import GENERATION_MODE_IDS
from backend.modes.base import ModeSpec
from backend.modes.character_json import SPEC as CHARACTER_JSON
from backend.modes.image_to_video import SPEC as IMAGE_TO_VIDEO
from backend.modes.json_to_natural import SPEC as JSON_TO_NATURAL
from backend.modes.product_detail_shots import SPEC as PRODUCT_DETAIL_SHOTS
from backend.modes.reference_pack import SPEC as REFERENCE_PACK
from backend.modes.storyboard_unified import SPEC as STORYBOARD_UNIFIED

REGISTRY: dict[str, ModeSpec] = {
    spec.id: spec
    for spec in (
        CHARACTER_JSON,
        PRODUCT_DETAIL_SHOTS,
        STORYBOARD_UNIFIED,
        REFERENCE_PACK,
        IMAGE_TO_VIDEO,
        JSON_TO_NATURAL,
    )
}

OUTFIT_MODE_META: dict[str, object] = {
    "id": GENERATION_MODE_IDS["OUTFIT_SWAP"],
    "label": "Thay trang phuc",
    "kind": "outfit",
    "output_type": "text",
    "allow_images": True,
    "default_temperature": 0.35,
    "max_output_tokens": 5000,
    "purpose": "Tao prompt thay trang phuc giu identity tu anh mau.",
    "usage": "Upload A.1 model identity va A.2 outfit source; A.3 background la tuy chon.",
}


def get_mode_spec(mode_id: str) -> ModeSpec | None:
    return REGISTRY.get(mode_id)


def list_generation_modes() -> list[dict[str, object]]:
    generic_modes = [
        {
            "id": spec.id,
            "label": spec.label,
            "purpose": spec.purpose,
            "usage": spec.usage,
            "kind": "generic",
            "output_type": spec.output_type,
            "allow_images": spec.allow_images,
            "default_temperature": spec.default_temperature,
            "max_output_tokens": spec.max_output_tokens,
            "prompt_version": spec.prompt_version,
        }
        for spec in REGISTRY.values()
    ]
    return [OUTFIT_MODE_META, *generic_modes]
