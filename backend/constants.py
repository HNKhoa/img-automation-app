from __future__ import annotations

MODEL_OPTIONS = [
    {"value": "gpt-5.4-nano", "label": "GPT-5.4 Nano", "supports_images": True, "tier": "balanced"},
    {"value": "gpt-5-nano", "label": "GPT-5 Nano", "supports_images": True, "tier": "balanced"},
    {"value": "gemini-flash-lite-3.1", "label": "Gemini 2.5 Flash Lite", "supports_images": True, "tier": "vision"},
    {"value": "mistral-small-3.1", "label": "Mistral Small 3.1", "supports_images": False, "tier": "critic"},
]
MODEL_OPTIONS_BY_VALUE = {item["value"]: item for item in MODEL_OPTIONS}
MODEL_WHITELIST = frozenset(MODEL_OPTIONS_BY_VALUE)

TARGET_OPTIONS = [
    {"value": "chatgpt_img", "label": "ChatGPT Image"},
    {"value": "gpt_image", "label": "GPT Image"},
    {"value": "gg_banana2", "label": "GG Banana2"},
]
TARGET_RULES = frozenset(item["value"] for item in TARGET_OPTIONS)

QUALITY_PROFILES = [
    {"value": "high", "label": "High"},
    {"value": "balanced", "label": "Balanced"},
    {"value": "draft", "label": "Draft"},
]

STYLE_OPTIONS = [
    "High-end fashion editorial",
    "E-commerce clean studio",
    "Luxury lookbook",
    "Soft cinematic portrait",
]

ASPECT_RATIO_OPTIONS = ["1:1", "2:3", "3:4", "9:16", "16:9"]

RESOLUTION_OPTIONS = ["2K", "1024px", "1536px", "4K"]

ACTIVE_ROLES = ("model", "outfit", "background")
IMAGE_MIME_ALLOWLIST = {"image/jpeg", "image/png", "image/webp"}
ROLE_LABELS = {
    "model": "REFERENCE 1 - A.1 model identity / final Image 1. Absolute highest priority. Locked identity, face, skin tone, facial structure, body proportion if visible, and natural likeness.",
    "outfit": "REFERENCE 2 - A.2 outfit / final Image 2. Very high priority. Outfit source only: garment type, fabric, exact visual color, fit, silhouette, layering, styling, and visible accessories.",
    "background": "REFERENCE 3 - A.3 optional background / final Image 3. Scene type, environment, lighting, perspective, depth, atmosphere, palette, and mood. If missing, fallback to Image 1 background.",
}
MAX_TOTAL_IMAGE_PAYLOAD_BYTES = 1_200_000
