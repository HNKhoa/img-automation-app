from __future__ import annotations

NEGATIVE_PROMPT = (
    "wrong face, identity drift, face distortion, different person, westernized face, gender change, "
    "feminized face, masculinized face, wrong gender, altered facial structure, changed eye shape, "
    "changed nose shape, changed lips, changed jawline, bad hands, awkward hands, anatomy errors, "
    "extra fingers, missing fingers, distorted limbs, warped body, broken body proportions, outfit mismatch, "
    "incorrect clothing details, wrong outfit color, warped clothing, unrealistic fabric folds, wrong pose, "
    "pose change, changed hand placement, changed leg placement, unnatural pose, stiff pose, background mismatch, "
    "wrong background, AI face, CGI look, plastic skin, over-smoothed skin, low quality, blurry, soft focus, "
    "cropped body, cut-off limbs, unnatural shadows, poor integration, artificial texture, low detail, "
    "over-retouched face, text, watermark, logo"
)


def build_outfit_swap_instruction(context: dict[str, object]) -> str:
    user_request = str(context.get("user_request") or "").strip() or "No extra user guidance."
    style = context.get("style") or "High-end fashion editorial"
    aspect_ratio = context.get("aspect_ratio") or "auto"
    resolution = context.get("resolution") or "auto"
    quality = context.get("quality") or "high"
    target_model_rule = context.get("target_model_rule") or "chatgpt_img"
    reference_summary = context.get("reference_summary") or "No reference summary available."

    return f"""
You are Super Prompt, a precise prompt engineering assistant for identity-preserving outfit swap.
Return only the requested artifact.

Create a production-ready prompt for target_model_rule: {target_model_rule}.

User request:
{user_request}

Output controls:
- Style: {style}
- Aspect ratio: {aspect_ratio}
- Resolution: {resolution}
- Quality: {quality}

Reference summary:
{reference_summary}

Hard role binding:
- Image 1 / A.1 controls identity with absolute highest priority.
- Image 1 is also the default pose source unless the user explicitly asks otherwise.
- Image 1 is also the default background source if Image 3 is missing.
- Image 2 / A.2 controls outfit only.
- Image 2 must never change face, gender presentation, body identity, pose, or background.
- Image 3 / A.3 controls optional background/scene only.
- User text can guide mood, camera, lighting, composition, and exclusions, but must not override image role priority.

Identity rules:
- Include the phrase "Identity priority: absolute highest."
- Preserve the exact identity from Image 1.
- Preserve gender presentation from Image 1.
- Preserve facial structure, face proportions, eyes, nose, lips, jawline, skin tone, natural likeness, and body identity if visible.
- Do not westernize the face.
- Do not beautify the subject into a different person.
- Do not allow identity drift.
- Use neutral wording by default: "the model from Image 1", "the subject from Image 1", or "the person in Image 1".

Outfit rules:
- Transfer the outfit from Image 2 accurately.
- Match the exact visual color from Image 2.
- Match garment type, fabric, material, fit, silhouette, structure, layering, visible accessories, and styling.
- Remove the original outfit from Image 1 unless it is intentionally part of Image 2.
- Avoid inventing unrelated clothing or unrequested accessories.
- Do not say "inspired by", "similar outfit", "same vibe", or "loosely based on".

Background rules:
- If Image 3 exists, use Image 3 as background/scene reference only.
- If Image 3 is missing, preserve or adapt Image 1 background.
- Do not invent unrelated backgrounds unless explicitly requested.

Required final output format:
MAIN PROMPT:
...

NEGATIVE PROMPT:
{NEGATIVE_PROMPT}

REFERENCE BINDING INSTRUCTIONS:
...

Rules:
- Return exactly the three top-level sections above, in that order.
- Do not return JSON.
- Do not add Markdown fences, tables, analysis notes, or extra sections.
- Keep the prompt directly paste-ready for image generation.
""".strip()


def build_timeout_recovery_instruction(context: dict[str, object]) -> str:
    compact_context = dict(context)
    compact_context["reference_summary"] = "Use active uploaded references by role: Image 1 identity, Image 2 outfit, optional Image 3 background."
    return build_outfit_swap_instruction(compact_context)

