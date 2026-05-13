from __future__ import annotations

import re
from typing import Any

from backend.constants import GENERATION_MODE_IDS
from backend.modes.base import ModeContext, ModeSpec, build_instruction_common, error, strip_markdown_fence

MODE_ID = GENERATION_MODE_IDS["PRODUCT_DETAIL_SHOTS"]
MODE_LABEL = "Shot chi tiet san pham"
MODE_PURPOSE = "Tao cac shot can canh va shot tham chieu de lam ro chi tiet san pham."
MODE_USAGE = "Nhap ten san pham, chat lieu va chi tiet can zoom nhu logo, nhan, nut ao, duong may, texture. Nen tai anh san pham that de tao shot close-up sac net hon."

TASK_BLOCK = """Task:
Create exactly 9 commercial product photography shot prompts.
Use the exact shot list and exact section labels below.
Each shot must include the product details, style, aspect ratio, resolution, and quality."""

FORMAT_BLOCK = """Priority phrases to use naturally where relevant:
- Extreme close-up focusing on...
- Macro detail shot highlighting...
- Close-up texture shot of...
- Tight crop emphasizing...
- Manual focus pull across...
- Shallow depth of field
- Ultra-sharp detail
- Crisp texture visibility
- Centered symmetry
- Commercial product photography

Required shot list:
1. Hero product shot
2. Three-quarter angle shot
3. Side profile shot
4. Top-down shot
5. Extreme close-up detail shot
6. Macro texture shot
7. Logo or label detail shot
8. In-hand shot
9. Usage shot

Required format for every shot:
Shot [number]: [shot name]
SUBJECT:
CAMERA+COMPOSITION:
LIGHTING:
STYLE:
DETAIL EMPHASIS:
INDUSTRY CONTEXT:"""

DOMAIN_VOCAB = """Domain vocabulary:
- Surface: matte, glossy, satin, brushed, anodized, leather grain, woven texture, porcelain, glass refraction.
- Lighting: softbox key, fill bounce, rim light separation, polarizer, light tent, gradient backdrop.
- Backdrop: pure white sweep, seamless paper, gradient grey, contextual lifestyle, complementary color.
- Industry shots: flat-lay knolling, hero with shadow, hand model, scale comparison, before-after, in-context lifestyle."""

EXAMPLE_BLOCK = """Example shot, do NOT copy values:
Shot 1: Hero product shot
SUBJECT: Placeholder product centered with clean visible silhouette.
CAMERA+COMPOSITION: 85mm lens, eye-level, centered symmetry, controlled crop.
LIGHTING: Large softbox key with subtle rim separation.
STYLE: Commercial product photography on neutral seamless background.
DETAIL EMPHASIS: Crisp texture visibility and exact material finish.
INDUSTRY CONTEXT: Best for marketplace hero listing and brand catalog cover."""

LENGTH_GUIDANCE = """Length guidance:
- Each sub-label is 1-2 concise sentences.
- CAMERA+COMPOSITION always includes lens, angle, and framing.
- LIGHTING always includes a named setup.
- STYLE states backdrop and post-process tone."""

AVOID_LIST = """Avoid:
- Avoid phrases like beautiful product or high quality background.
- Do not repeat the same setup across all 9 shots.
- Shot 8 In-hand and Shot 9 Usage must describe different contexts."""

SYSTEM_PERSONA = (
    "You are a commercial product photographer specializing in e-commerce and brand photography. "
    "You write shot lists used by professional studios worldwide."
)
PROMPT_VERSION = f"{MODE_ID}/v2"

SUB_LABELS = ["SUBJECT", "CAMERA\\+COMPOSITION", "LIGHTING", "STYLE", "DETAIL EMPHASIS", "INDUSTRY CONTEXT"]


def build_instruction(ctx: ModeContext) -> str:
    return build_instruction_common(ctx, TASK_BLOCK, FORMAT_BLOCK, DOMAIN_VOCAB, EXAMPLE_BLOCK, LENGTH_GUIDANCE, AVOID_LIST)


def validate_output(text: str) -> dict[str, Any] | None:
    clean = strip_markdown_fence(text)
    matches = list(re.finditer(r"^Shot\s+(\d+):", clean, flags=re.IGNORECASE | re.MULTILINE))
    numbers = [int(match.group(1)) for match in matches]
    if sorted(numbers) != list(range(1, 10)) or len(set(numbers)) != 9:
        return error("INVALID_SHOT_COUNT", "Expected exactly Shot 1 through Shot 9.", clean)
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(clean)
        block = clean[match.start() : end]
        missing = [label.replace("\\", "") + ":" for label in SUB_LABELS if not re.search(rf"\b{label}\s*:", block, re.IGNORECASE)]
        if missing:
            return error("MISSING_SHOT_LABELS", f"Shot {match.group(1)} missing labels: {', '.join(missing)}", clean)
    return None


SPEC = ModeSpec(
    MODE_ID,
    MODE_LABEL,
    MODE_PURPOSE,
    MODE_USAGE,
    "text",
    True,
    0.7,
    4096,
    build_instruction,
    validate_output,
    SYSTEM_PERSONA,
    PROMPT_VERSION,
)
