# SKILL: Identity-Preserving Outfit Swap Prompt System

## 1. Mục tiêu

Skill này dùng cho hệ thống tạo prompt thay trang phục cho mẫu dựa trên nhiều ảnh tham chiếu.

Người dùng chỉ cần cung cấp:

- Ảnh A: ảnh mẫu / identity reference
- Ảnh B: ảnh trang phục / outfit reference
- Ảnh C: ảnh makeup, optional
- Ảnh D: ảnh pose / dáng / thần thái, optional
- Ảnh E: ảnh nền / background, optional
- `user_request`: yêu cầu ngắn của người dùng
- `target_model_rule`: `chatgpt_img`, `gg_banana2`, hoặc `gpt_image`

Hệ thống phải tự:

1. Phân tích từng ảnh theo đúng vai trò.
2. Bảo toàn nhân dạng mẫu từ ảnh A.
3. Bám sát outfit từ ảnh B.
4. Áp makeup từ ảnh C nếu có, nhưng không làm đổi mặt mẫu.
5. Áp pose từ ảnh D nếu có, nhưng không làm đổi identity.
6. Áp background từ ảnh E nếu có, nhưng bỏ người trong ảnh nền.
7. Tạo `final_prompt`, `negative_prompt`, `reference_binding_instructions`.
8. Tối ưu token bằng cache `analysis_json` theo `image_hash`.

---

## 2. Nguyên tắc bất biến

Luôn áp dụng các rule sau trong mọi prompt, mọi model, mọi mode:

```text
Only Image A controls identity.
Image B controls outfit only.
Image C controls makeup only.
Image D controls pose only.
Image E controls background only.
All non-identity images are attribute-only references and must not replace the face or likeness from Image A.
```

Thứ tự ưu tiên khi có xung đột:

```text
1. Preserve identity from Image A.
2. Preserve outfit fidelity from Image B.
3. Apply makeup from Image C without identity drift.
4. Apply pose from Image D with realistic anatomy.
5. Apply background from Image E while ignoring any person.
```

Không được dùng các mô tả mơ hồ cho outfit như:

```text
inspired by the outfit
similar outfit
same vibe
loosely based on
```

Phải dùng wording mạnh:

```text
Reproduce the outfit from Image B with maximum fidelity.
Match the garment structure, silhouette, layering, neckline, sleeves, fit, closures, fabric impression, trims, accessories, and color distribution as closely as possible.
Do not simplify, redesign, restyle, or loosely reinterpret the outfit.
Keep the outfit details intact.
```

---

## 3. Vai trò ảnh tham chiếu

### Image A — Identity Reference

Dùng để giữ:

- face identity
- facial structure
- face shape
- skin tone
- skin texture
- eyes
- eyebrows
- nose
- lips
- jawline
- expression
- hairline
- hair style
- overall likeness

Không dùng Image A để suy luận outfit nếu Image B có sẵn outfit reference.

### Image B — Outfit Reference

Dùng để lấy chính xác:

- garment category
- silhouette
- construction
- layer order
- neckline
- collar
- shoulder structure
- sleeve type and length
- cuffs
- fit
- waist shape
- hemline
- closures: buttons, zippers, hooks, lacing
- seams
- pocket placement
- trims
- ornaments
- fabric type
- texture
- finish
- drape
- folds
- color distribution
- jewelry, belt, bag, gloves, stockings, shoes nếu thuộc outfit

Không lấy mặt, pose, background, body identity từ Image B, trừ khi user yêu cầu rõ.

### Image C — Makeup Reference

Dùng để lấy:

- makeup tone
- base
- skin finish
- eyeliner
- eyeshadow
- lashes
- brows
- blush
- contour
- highlight
- lip color
- lip finish
- gloss level
- makeup intensity

Không lấy identity từ Image C.

### Image D — Pose Reference

Dùng để lấy:

- body orientation
- torso
- shoulders
- arms
- hands
- hips
- legs
- feet
- head angle
- chin position
- eye gaze
- expression energy
- attitude / thần thái

Không lấy identity từ Image D.

### Image E — Background Reference

Dùng để lấy:

- scene type
- background-only description
- objects
- colors
- lighting environment
- depth
- mood
- composition

Nếu ảnh nền có người, phải bỏ người và chỉ tách nền.

---

## 4. Kiến trúc xử lý

Dùng pipeline 2 call AI + cache:

```text
User upload A/B/C/D/E + user_request + target_model_rule
        ↓
Backend validate + resize/compress ảnh
        ↓
Compute normalized image_hash cho từng ảnh
        ↓
Check analysis_cache theo role_hashes
        ↓
Nếu cache miss:
    Call 1: Vision Model nhận nhiều ảnh → analysis_json
Nếu cache hit:
    Lấy analysis_json từ cache
        ↓
Check final_prompt_cache theo analysis_key + user_request + target_model_rule
        ↓
Nếu cache miss:
    Call 2: Prompt Builder Model text-only → final_prompt
Nếu cache hit:
    Lấy final_prompt từ cache
        ↓
Return final_prompt + negative_prompt + reference instructions
```

Không gửi ảnh lại cho Prompt Builder. Prompt Builder chỉ nhận text/JSON.

---

## 5. Model routing

Nếu chỉ có các model sau thì dùng cấu hình này:

```json
{
  "cheap": {
    "vision_model": "Gemini 2.5 Flash Lite",
    "prompt_builder_model": "Mistral Small 3.1",
    "critic_model": null
  },
  "balanced": {
    "vision_model": "Gemini 2.5 Flash Lite",
    "prompt_builder_model": "GPT-5.4 Nano",
    "critic_model": null
  },
  "quality": {
    "vision_model": "Gemini 3.1 Flash Lite",
    "prompt_builder_model": "GPT-5.4 Nano",
    "critic_model": "Mistral Small 3.1"
  }
}
```

Default nên dùng:

```text
Vision Model: Gemini 2.5 Flash Lite
Prompt Builder Model: GPT-5.4 Nano
Critic: Off
```

Pro mode:

```text
Vision Model: Gemini 3.1 Flash Lite
Prompt Builder Model: GPT-5.4 Nano
Critic Model: Mistral Small 3.1
```

Không dùng các model sau cho pipeline chính:

```text
Qwen3Guard 8B: chỉ dùng kiểm tra safety.
Qwen3 Coder 30B: chỉ dùng viết code.
Perplexity Sonar: chỉ dùng search/trend/web info.
```

---

## 6. Token / pollen strategy

Thứ tự tốn token/pollen:

```text
1. Số lượng ảnh gửi lên Vision Model.
2. Kích thước ảnh.
3. Vision JSON quá chi tiết.
4. Prompt Builder output quá dài.
5. Bật thêm Critic Model.
```

Tối ưu bắt buộc:

```text
- Resize ảnh long side về 1024–1280px ở balanced mode.
- Compress JPG/WebP quality 80–85.
- Chỉ gửi ảnh cần thiết.
- Vision 1 call nhận nhiều ảnh.
- Builder 1 call text-only.
- Cache analysis_json theo image_hash.
- Cache final_prompt theo analysis_key + user_request + target_model_rule.
- Không bật critic mặc định.
```

Mức sử dụng tương đối:

```text
1–2 ảnh: trung bình.
3–5 ảnh: trung bình cao.
5 ảnh + detailed schema + critic: cao.
Ảnh cũ + request mới: thấp/trung bình vì bỏ qua Vision.
Ảnh cũ + request cũ: gần như 0 model token vì trả cache.
```

---

## 7. Cache design

### 7.1. Normalize ảnh trước khi hash

Hash nên tính trên ảnh đã normalize:

```text
original image
→ strip metadata
→ exif transpose
→ convert RGB
→ resize/compress
→ normalized_image_bytes
→ sha256(normalized_image_bytes)
```

Khuyến nghị:

```text
cheap: max_side=1024, quality=80
balanced: max_side=1280, quality=85
quality: max_side=1536, quality=88
```

### 7.2. analysis_cache key

Phụ thuộc vào:

```text
- role_hashes:
  - A_identity
  - B_outfit
  - C_makeup
  - D_pose
  - E_background
- vision_model
- vision_prompt_version
- analysis_mode
```

Không nên phụ thuộc vào `user_request` quá nhiều, để cùng bộ ảnh có thể dùng lại cho nhiều request.

### 7.3. final_prompt_cache key

Phụ thuộc vào:

```text
- analysis_cache_key
- user_request
- target_model_rule
- builder_model
- builder_prompt_version
```

### 7.4. Cache invalidation

Mỗi khi sửa prompt hệ thống, phải tăng version:

```text
vision_v1_compact
vision_v2_outfit_strict
builder_v1_outfit_lock
builder_v2_outfit_lock_strict
```

Nếu không đổi version, hệ thống có thể lấy prompt cũ từ cache.

---

## 8. Vision Model Prompt

### 8.1. Vision System Prompt

```text
You are a multi-reference visual analysis engine for reference-based image generation.

Reference roles:
- Image A = identity reference
- Image B = outfit reference
- Image C = makeup reference, optional
- Image D = pose reference, optional
- Image E = background reference, optional

Core mission:
Build a precise visual analysis that preserves the exact identity from Image A and the exact outfit details from Image B.

Hard priority:
1. Identity from Image A must be preserved exactly.
2. Outfit from Image B must be reproduced as faithfully as possible.
3. Makeup from Image C must be adapted without changing identity.
4. Pose from Image D must be adapted without changing identity.
5. Background from Image E must be used without keeping any original person from that image.

Critical global rule:
Only Image A controls identity.
Image B controls outfit only.
Image C controls makeup only.
Image D controls pose only.
Image E controls background only.
All non-identity images are attribute-only references and must not replace the face or likeness from Image A.

Critical outfit fidelity rules:
- Treat Image B as an exact outfit reference, not as loose inspiration.
- Extract the outfit with maximum fidelity.
- Do not simplify or generalize clothing details.
- Capture garment category, silhouette, construction, layer order, neckline, collar shape, shoulder shape, sleeve type and length, cuff details, fit, waist shape, hemline, closures, buttons, zippers, seams, pocket placement, drape, folds, fabric type, texture, finish, embellishments, trims, accessories, and color distribution.
- Capture whether the outfit is fitted, relaxed, oversized, cropped, tailored, structured, draped, or body-skimming.
- Capture how the garment sits on the body.
- Capture visible jewelry, belt, bag, gloves, stockings, shoes, or other accessories if present.
- If some outfit detail is unclear, mark it as "unclear" rather than inventing.

Critical identity rules:
- Preserve facial structure, face shape, skin tone, eyes, nose, lips, jawline, expression, hairline, hair, and recognizable identity cues from Image A.
- Do not transfer face identity from Image B, C, D, or E.

Critical makeup rules:
- Extract makeup style, tone, finish, and layer details only.
- Adapt makeup onto Image A identity without changing face shape or likeness.

Critical pose rules:
- Extract body pose, hands, legs, head angle, gaze, and attitude only.
- Adapt pose onto Image A identity with realistic anatomy and natural proportions.

Critical background rules:
- If Image E contains a person, ignore the person and describe the background only.

Return JSON only.
Do not explain.
Do not invent details that are not visible.
If unclear, write "unclear".
```

### 8.2. Vision User Prompt Template

```text
Analyze the uploaded references for an identity-preserving outfit swap workflow.

User request:
{{USER_REQUEST}}

Target model rule:
{{TARGET_MODEL_RULE}}

Uploaded image roles:
- Image A = identity reference
- Image B = outfit reference
- Image C = makeup reference, optional
- Image D = pose reference, optional
- Image E = background reference, optional

Important instructions:
1. Preserve the exact face identity from Image A.
2. Reproduce the outfit from Image B with maximum fidelity.
3. Treat Image B as an exact outfit source, not as loose inspiration.
4. Extract outfit details with strong precision, including garment structure, silhouette, layering, neckline, sleeves, fit, closures, fabric, texture, trims, accessories, and color distribution.
5. If Image C is present, extract only the makeup and adapt it onto the identity from Image A without changing identity.
6. If Image D is present, extract only the pose and adapt it onto the identity from Image A with realistic anatomy.
7. If Image E is present, extract only the background and ignore any person.
8. Return JSON only using the exact schema.
```

### 8.3. Vision Output Schema

```json
{
  "input_summary": {
    "available_references": {
      "identity_image_A": true,
      "outfit_image_B": true,
      "makeup_image_C": false,
      "pose_image_D": false,
      "background_image_E": false
    },
    "target_model_rule": "",
    "user_request_summary": "",
    "analysis_mode": "compact"
  },
  "identity_analysis": {
    "overall_likeness": "",
    "face_shape": "",
    "facial_structure": "",
    "skin_tone": "",
    "skin_texture": "",
    "eyes": "",
    "eyebrows": "",
    "nose": "",
    "lips": "",
    "jawline": "",
    "expression": "",
    "hair": {
      "style": "",
      "color": "",
      "parting": "",
      "texture": "",
      "hairline_details": ""
    },
    "identity_preservation_notes": []
  },
  "outfit_analysis": {
    "overall_outfit_summary": "",
    "style_category": "",
    "silhouette": "",
    "layering_order": "",
    "top": {
      "garment_type": "",
      "neckline": "",
      "collar": "",
      "shoulder_construction": "",
      "sleeves": "",
      "cuffs": "",
      "fit": "",
      "closure": "",
      "length": "",
      "fabric": "",
      "texture": "",
      "color": "",
      "pattern": "",
      "details": []
    },
    "bottom": {
      "garment_type": "",
      "waist": "",
      "fit": "",
      "length": "",
      "closure": "",
      "fabric": "",
      "texture": "",
      "color": "",
      "pattern": "",
      "details": []
    },
    "dress": {
      "garment_type": "",
      "neckline": "",
      "sleeves": "",
      "waist": "",
      "length": "",
      "fit": "",
      "fabric": "",
      "texture": "",
      "color": "",
      "pattern": "",
      "details": []
    },
    "outerwear": {
      "garment_type": "",
      "fit": "",
      "length": "",
      "closure": "",
      "fabric": "",
      "texture": "",
      "color": "",
      "details": []
    },
    "shoes": {
      "type": "",
      "shape": "",
      "material": "",
      "color": "",
      "details": []
    },
    "accessories": {
      "jewelry": [],
      "belt": "",
      "bag": "",
      "other": []
    },
    "material_finish": "",
    "construction_details": [],
    "ornaments_and_trims": [],
    "visible_folds_and_drape": "",
    "outfit_lock": {
      "non_negotiable_items": [],
      "non_negotiable_structure": [],
      "non_negotiable_accessories": [],
      "non_negotiable_colors": [],
      "non_negotiable_material_impressions": []
    },
    "outfit_fidelity_notes": [],
    "must_not_change": []
  },
  "makeup_analysis": {
    "available": false,
    "overall_makeup_style": "",
    "tone": "",
    "base": "",
    "skin_finish": "",
    "eyeshadow": "",
    "eyeliner": "",
    "lashes": "",
    "brows": "",
    "blush": "",
    "contour": "",
    "highlight": "",
    "lips": "",
    "makeup_intensity": "",
    "adaptation_notes": []
  },
  "pose_analysis": {
    "available": false,
    "overall_pose": "",
    "body_orientation": "",
    "torso": "",
    "shoulders": "",
    "arms": "",
    "hands": "",
    "hips": "",
    "legs": "",
    "feet": "",
    "head_angle": "",
    "chin": "",
    "gaze": "",
    "expression_energy": "",
    "attitude": "",
    "pose_notes": []
  },
  "background_analysis": {
    "available": false,
    "scene_type": "",
    "background_only_description": "",
    "key_objects": [],
    "color_palette": "",
    "depth": "",
    "lighting_environment": "",
    "mood": "",
    "background_extraction_prompt": ""
  },
  "camera_lighting_style": {
    "shot_type": "",
    "camera_angle": "",
    "framing": "",
    "crop": "",
    "lens_feel": "",
    "aspect_ratio_guess": "",
    "lighting_type": "",
    "lighting_direction": "",
    "contrast_level": "",
    "shadow_style": "",
    "highlight_style": "",
    "retouching_style": "",
    "realism_level": ""
  },
  "fusion_rules": {
    "must_preserve_identity_from_A": [],
    "must_preserve_outfit_from_B": [],
    "must_apply_makeup_from_C": [],
    "must_apply_pose_from_D": [],
    "must_apply_background_from_E": [],
    "must_avoid": [],
    "conflict_warnings": [],
    "non_negotiable_rules": []
  }
}
```

---

## 9. Prompt Builder Model Prompt

### 9.1. Prompt Builder System Prompt

```text
You are an expert prompt engineer for identity-preserving outfit swap and reference-based image generation.

Your task:
Convert structured visual analysis plus the user's short request into a production-ready final prompt.

Core objective:
- Preserve the exact identity from Image A.
- Reproduce the outfit from Image B as faithfully as possible.
- Apply optional makeup from Image C.
- Apply optional pose from Image D.
- Apply optional background from Image E.

Hard priorities:
1. Exact identity preservation from Image A.
2. Exact outfit fidelity from Image B.
3. Makeup from Image C without changing identity.
4. Pose from Image D without changing identity.
5. Background from Image E.

Hard binding rules:
- Only Image A controls the final face and likeness.
- Image B controls outfit only.
- Image C controls makeup only.
- Image D controls pose only.
- Image E controls background only.
- Makeup, pose, or background references must not alter identity.
- Background reference must not keep any original person.

Hard outfit fidelity rules:
- Do not restyle or reinterpret the outfit.
- Do not replace the garment type with a similar garment.
- Do not simplify the silhouette.
- Do not change neckline, sleeve type, fit, layering, closure, trim, fabric impression, or accessory logic unless the user explicitly asks for it.
- Preserve the visual logic of the original outfit from Image B as closely as possible.
- Use outfit_lock fields as non-negotiable constraints.
- Make the outfit description specific and concrete.
- Explicitly instruct the final generation prompt to keep the outfit details intact.

Hard identity rules:
- The final prompt must state identity preservation clearly near the beginning.
- Preserve same facial structure, face shape, facial proportions, eyes, nose, lips, jawline, skin tone, expression, hairline, and recognizable identity cues.

Prompt quality rules:
- Clearly separate what to preserve and what to change.
- Avoid vague wording such as "inspired by" or "similar to" for the outfit.
- Use strong wording such as "match closely", "reproduce faithfully", "preserve exact garment logic", and "keep outfit details intact".
- Include realism safeguards for anatomy, hands, clothing folds, and face consistency.

Target model rules:
- If target_model_rule = "chatgpt_img":
  write strong, clear natural English prose, easy to paste directly into ChatGPT Image.
- If target_model_rule = "gg_banana2":
  write a structured JSON-style prompt with clearly separated sections.
- If target_model_rule = "gpt_image":
  write concise production English, less verbose than chatgpt_img, but still strict on identity and outfit.

Return JSON only.
```

### 9.2. Prompt Builder User Prompt Template

```text
Build a final image-generation prompt from the following inputs.

target_model_rule:
{{TARGET_MODEL_RULE}}

user_request:
{{USER_REQUEST}}

visual_analysis_json:
{{ANALYSIS_JSON}}

Production requirements:

1. Identity preservation
- Preserve the exact person from Image A.
- Keep the same facial structure, face shape, eyes, nose, lips, jawline, skin tone, expression, hairline, hair cues, and recognizable facial identity.

2. Outfit fidelity
- Reproduce the outfit from Image B as faithfully as possible.
- Use outfit_lock as non-negotiable.
- Keep the same garment logic, silhouette, layering, fit, neckline, sleeves, hemline, closures, trims, accessories, and material impression.
- Keep the color logic and styling logic intact unless the user explicitly requests changes.
- Do not rewrite the outfit into a simplified or generalized version.
- Do not use vague wording like "similar outfit" or "inspired look".
- Use explicit, concrete, production-ready wording.

3. Makeup adaptation
- If makeup analysis exists, apply the makeup onto the person from Image A without changing identity.

4. Pose adaptation
- If pose analysis exists, apply the pose, hand placement, leg placement, head angle, gaze, and attitude from Image D while preserving identity and realistic anatomy.

5. Background adaptation
- If background analysis exists, apply only the background and do not keep any original person from Image E.

6. Final prompt structure priority
- main objective
- identity preservation
- outfit fidelity
- makeup
- pose
- background
- lighting
- camera and composition
- realism and quality safeguards

7. Mandatory safeguards
Include protection against:
- changed identity
- distorted face
- facial drift
- wrong outfit details
- simplified clothing
- missing accessories
- wrong garment structure
- bad hands
- extra fingers
- extra limbs
- warped anatomy
- unnatural folds
- text
- watermark
- logo
- low quality
- blur

Return JSON only using this exact structure:

{
  "target_model_rule": "",
  "prompt_strategy": "",
  "reference_binding_instructions": {
    "upload_order": [],
    "role_binding": [],
    "important_binding_notes": []
  },
  "final_prompt": "",
  "negative_prompt": "",
  "background_only_prompt": "",
  "quality_checks": [],
  "risk_warnings": []
}
```

---

## 10. Output style theo target model

### 10.1. `chatgpt_img`

Final prompt phải là English prose, dễ paste:

```text
Create a realistic high-end fashion editorial image.

Preserve the exact same person from Image A with very high identity fidelity. Keep the same facial structure, face shape, skin tone, eyes, nose, lips, jawline, expression, hairline, and overall likeness.

Reproduce the outfit from Image B with maximum fidelity. Match the exact garment logic, silhouette, layering, neckline, sleeve design, fit, closures, hemline, accessories, fabric impression, texture, and color distribution as closely as possible. Do not simplify, redesign, restyle, or loosely reinterpret the outfit. Keep the outfit details intact.

Apply the makeup style from Image C only as a transferable beauty reference, without changing the person’s identity. Apply the pose from Image D with realistic anatomy, correct hand placement, natural body proportions, and the same pose attitude. Use the background from Image E only, excluding any original person from that image.

Maintain realistic skin texture, accurate anatomy, natural clothing folds, and consistent identity. Avoid face drift, outfit drift, missing outfit details, distorted hands, extra fingers, extra limbs, warped anatomy, text, watermark, logo, blur, or low quality.
```

### 10.2. `gg_banana2`

Final prompt nên là JSON-style structured prompt:

```json
{
  "task": "reference-based identity-preserving outfit transfer",
  "subject": {
    "identity_priority": "absolute",
    "source": "Image A",
    "instruction": "Preserve the exact same person from Image A",
    "identity_rules": [
      "keep same facial structure",
      "keep same facial proportions",
      "keep same skin tone",
      "keep same eyes, nose, lips, jawline",
      "keep same expression and likeness"
    ]
  },
  "outfit": {
    "source": "Image B",
    "fidelity_priority": "absolute",
    "instruction": "Reproduce the outfit as faithfully as possible",
    "rules": [
      "match garment type",
      "match silhouette",
      "match layering",
      "match neckline",
      "match sleeves",
      "match fit",
      "match closures",
      "match accessories",
      "match fabric impression",
      "match color distribution",
      "do not simplify or redesign the outfit"
    ]
  },
  "makeup": {
    "source": "Image C",
    "instruction": "Apply makeup style only, without changing identity"
  },
  "pose": {
    "source": "Image D",
    "instruction": "Apply pose and attitude with realistic anatomy"
  },
  "background": {
    "source": "Image E",
    "instruction": "Use background only, ignore any original person"
  },
  "quality_rules": [
    "realistic anatomy",
    "natural hands",
    "natural folds",
    "visible outfit details preserved",
    "no identity drift",
    "no outfit drift"
  ]
}
```

### 10.3. `gpt_image`

Final prompt nên ngắn hơn `chatgpt_img`:

```text
Create a realistic identity-preserving fashion image. Use Image A as the only source for the subject's face and likeness. Preserve the same facial structure, skin tone, eyes, nose, lips, jawline, expression, and hair cues.

Reproduce the outfit from Image B with maximum fidelity, preserving garment type, silhouette, layering, neckline, sleeves, fit, closures, fabric impression, accessories, and color distribution. Do not simplify, redesign, or reinterpret the outfit.

Apply optional makeup, pose, and background references only as attribute references. Maintain realistic anatomy, natural hands, natural clothing folds, consistent lighting, and no face or outfit drift.
```

---

## 11. Negative prompt mặc định

Luôn dùng hoặc merge vào output:

```text
changed identity, different face, facial drift, distorted face, wrong facial structure, plastic skin, over-smoothed skin, wrong outfit details, simplified clothing, redesigned outfit, missing accessories, wrong garment structure, wrong neckline, wrong sleeves, wrong silhouette, unnatural clothing folds, bad hands, distorted hands, extra fingers, missing fingers, extra limbs, warped anatomy, incorrect body proportions, text, watermark, logo, blurry, low quality, overexposed, underexposed
```

---

## 12. Response JSON trả về frontend

```json
{
  "ok": true,
  "mode": "balanced",
  "models": {
    "vision": "gemini-2.5-flash-lite",
    "prompt_builder": "gpt-5.4-nano",
    "critic": null
  },
  "cache": {
    "analysis_cached": false,
    "prompt_cached": false,
    "analysis_cache_key": "",
    "prompt_cache_key": ""
  },
  "result": {
    "final_prompt": "",
    "negative_prompt": "",
    "background_only_prompt": "",
    "reference_binding_instructions": {
      "upload_order": [
        "Image A - identity reference",
        "Image B - outfit reference",
        "Image C - makeup reference, optional",
        "Image D - pose reference, optional",
        "Image E - background reference, optional"
      ],
      "role_binding": [
        "Image A controls identity only.",
        "Image B controls outfit only.",
        "Image C controls makeup only.",
        "Image D controls pose only.",
        "Image E controls background only."
      ],
      "important_binding_notes": [
        "Only Image A controls identity.",
        "All other images are attribute-only references.",
        "Do not copy face identity from outfit, makeup, pose, or background images.",
        "Outfit from Image B must be reproduced with maximum fidelity."
      ]
    },
    "quality_checks": [
      "Identity from Image A is stated near the beginning.",
      "Outfit from Image B is described as exact/fidelity reference, not inspiration.",
      "Outfit lock items are included.",
      "Makeup does not override identity.",
      "Pose does not override identity.",
      "Background excludes any original person.",
      "Negative prompt includes face drift and outfit drift protection."
    ],
    "risk_warnings": []
  },
  "usage_level_estimate": {
    "vision": "high_if_3_to_5_images",
    "prompt_builder": "medium_text_only",
    "total": "medium_high_first_run_low_after_cache"
  }
}
```

---

## 13. Critic mode optional

Chỉ bật khi user chọn Pro / Improve Prompt.

Critic model dùng `Mistral Small 3.1`.

### Critic System Prompt

```text
You are a prompt critic for identity-preserving outfit swap prompts.

Review the final prompt for:
- weak identity preservation
- weak outfit fidelity
- missing outfit details
- conflicting reference roles
- makeup causing identity drift
- pose causing anatomy issues
- background keeping unwanted people
- vague language
- missing negative prompt protections

Return JSON only:
{
  "detected_issues": [],
  "improved_final_prompt": "",
  "improved_negative_prompt": "",
  "quality_score": 0
}
```

### Critic User Prompt

```text
Review and improve this prompt.

target_model_rule:
{{TARGET_MODEL_RULE}}

final_prompt:
{{FINAL_PROMPT}}

negative_prompt:
{{NEGATIVE_PROMPT}}

reference_binding_instructions:
{{REFERENCE_BINDING_INSTRUCTIONS}}

Rules:
- Preserve all correct details.
- Strengthen identity preservation.
- Strengthen outfit fidelity.
- Remove contradictions.
- Keep the output production-ready.
- Return JSON only.
```

---

## 14. Implementation notes

### 14.1. API endpoint nên có

```http
POST /api/prompts/generate
```

Multipart fields:

```text
user_request: string
target_model_rule: chatgpt_img | gg_banana2 | gpt_image
mode: cheap | balanced | quality
identity_image: required
outfit_image: required
makeup_image: optional
pose_image: optional
background_image: optional
```

### 14.2. Backend files đề xuất

```text
backend/
├─ app/
│  ├─ main.py
│  ├─ api/
│  │  └─ prompt_routes.py
│  ├─ services/
│  │  ├─ image_preprocess.py
│  │  ├─ cache_keys.py
│  │  ├─ cache_service.py
│  │  ├─ pollinations_client.py
│  │  └─ prompt_workflow.py
│  ├─ prompts/
│  │  ├─ vision_prompts.py
│  │  ├─ builder_prompts.py
│  │  └─ critic_prompts.py
│  └─ config.py
├─ requirements.txt
└─ .env
```

### 14.3. Test command

```bash
curl -X POST "http://localhost:8000/api/prompts/generate" \
  -F "user_request=Giữ mặt mẫu, bám sát outfit gốc, makeup nhẹ, nền studio đỏ" \
  -F "target_model_rule=chatgpt_img" \
  -F "mode=balanced" \
  -F "identity_image=@./samples/identity.jpg" \
  -F "outfit_image=@./samples/outfit.jpg" \
  -F "makeup_image=@./samples/makeup.jpg" \
  -F "pose_image=@./samples/pose.jpg" \
  -F "background_image=@./samples/background.jpg"
```

Expected cache behavior:

```text
First run:
analysis_cached = false
prompt_cached = false

Second run with same images and same request:
analysis_cached = true
prompt_cached = true

Same images but different request:
analysis_cached = true
prompt_cached = false
```

---

## 15. Checklist bắt buộc trước khi trả final prompt

Trước khi output cho user, hệ thống phải tự kiểm tra:

```text
[ ] Final prompt có câu giữ identity từ Image A ở đầu.
[ ] Final prompt nói rõ Image A là nguồn identity duy nhất.
[ ] Final prompt nói rõ outfit từ Image B phải bám sát tối đa.
[ ] Outfit không bị mô tả kiểu "inspired by".
[ ] Có nhắc garment structure / silhouette / fit / fabric / color / accessories.
[ ] Makeup nếu có chỉ là style transfer, không đổi mặt.
[ ] Pose nếu có chỉ là body/attitude transfer, không đổi mặt.
[ ] Background nếu có không giữ người trong ảnh nền.
[ ] Negative prompt có changed identity / outfit drift / wrong outfit details.
[ ] Không có instruction mâu thuẫn.
```

---

## 16. Default production configuration

```json
{
  "mode": "balanced",
  "vision_model": "Gemini 2.5 Flash Lite",
  "prompt_builder_model": "GPT-5.4 Nano",
  "critic_model": null,
  "image_preprocess": {
    "max_side": 1280,
    "quality": 85,
    "format": "jpeg",
    "strip_metadata": true
  },
  "cache": {
    "analysis_cache_ttl_days": 30,
    "final_prompt_cache_ttl_days": 7
  },
  "prompt_versions": {
    "vision": "vision_v1_outfit_strict",
    "builder": "builder_v1_outfit_lock"
  }
}
```
