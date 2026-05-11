---
name: super-prompt-extension
description: Use this skill when porting, rebuilding, modifying, testing, packaging, or explaining the Super Prompt Chrome Extension, including its Manifest V3 side panel architecture, Pollinations prompt generation, outfit-swap MVP, image role system, model configuration, payload behavior, ChatGPT Img 2 handoff, and regression checks.
---

# Super Prompt Extension Skill

Use this file as the complete technical handoff for moving the Super Prompt extension logic into another project.

The current product is a Chrome Extension, Manifest V3, implemented with plain HTML, CSS, and JavaScript. It runs mainly as a side panel and helps users generate AI prompts from text plus reference images. The MVP focus is the fashion workflow **Thay trang phuc**: create a production-ready outfit-swap prompt for ChatGPT Img 2 from:

- Image 1 / A.1: model identity reference.
- Image 2 / A.2: outfit or clothing reference.
- Image 3 / A.3: optional background or scene reference.

The extension does not generate the final image itself. It generates a prompt and can hand off the prompt plus images to ChatGPT Img 2.

## Product Scope

Primary product name:

```text
Super Prompt - Outfit Prompt Builder
```

Primary value proposition:

```text
Create outfit swap prompts for ChatGPT Img 2 from a model image, an outfit image, and an optional background.
```

Target users:

- Fashion sellers.
- TikTok Shop and Shopee sellers.
- AI image creators.
- Small studios.
- Lookbook creators.
- Shop owners who need product/model visuals quickly.

Current MVP scope is intentionally narrow. Do not turn the product into a general prompt lab unless explicitly requested. The strongest path is to make outfit identity lock, outfit fidelity, and ChatGPT handoff reliable.

## Project Files

Core files:

- `manifest.json`: Manifest V3 metadata, extension permissions, side panel entry, background service worker, and host permissions.
- `background.js`: background/service-worker logic, action click handling, side panel setup, tab/script support.
- `popup.html`: side panel markup. It should not hard-code prompt mode options.
- `popup.css`: dark neon UI styling for the side panel.
- `popup.js`: main UI orchestrator, DOM binding, runtime state, storage, upload handling, image compression, Pollinations API calls, output actions, and ChatGPT handoff.
- `modes.js`: prompt mode registry, mode metadata, prompt templates, and output validation helpers.
- `chatgpt-img2-content.js`: injected content script that uploads images sequentially to ChatGPT and fills the composer.
- `TEST_CASES.md`: manual and regression test cases.
- `ADD_MODE_GUIDE.md`: guide for adding prompt modes.
- `GO_TO_MARKET.md`: launch and market notes.
- `PROJECT_HANDOFF.md`: short project handoff summary.
- `SKILL.md`: this long technical handoff and operating guide.

When moving to another project, port these first:

1. `manifest.json`
2. `background.js`
3. `popup.html`
4. `popup.css`
5. `popup.js`
6. `modes.js`
7. `chatgpt-img2-content.js`
8. `TEST_CASES.md`
9. `ADD_MODE_GUIDE.md`
10. `PROJECT_HANDOFF.md`
11. `SKILL.md`

## Runtime Architecture

The extension uses:

- Chrome Manifest V3.
- Side panel UI.
- ES modules for popup logic.
- No framework.
- No bundler.
- No npm dependency for runtime.
- `chrome.storage.local` for API key and UI config.
- Pollinations Chat Completions API for prompt generation.
- Content-script injection for ChatGPT Img 2 handoff.

High-level flow:

1. User opens the extension side panel.
2. `popup.js` binds DOM elements and events.
3. `modes.js` validates and renders prompt modes.
4. User enters optional text guidance.
5. User uploads active reference images.
6. Images are compressed and stored in runtime state as data URLs.
7. User chooses model, style, aspect ratio, resolution, and quality.
8. `popup.js` builds a context object.
9. Selected mode's `buildPrompt(context)` creates the instruction sent to Pollinations.
10. Pollinations returns the generated prompt artifact.
11. Extension validates output.
12. User copies/downloads output or sends it to ChatGPT Img 2.
13. ChatGPT handoff opens/focuses ChatGPT, injects `chatgpt-img2-content.js`, uploads images one by one, then fills the prompt.

## Manifest Requirements

The extension requires Manifest V3:

```json
{
  "manifest_version": 3,
  "name": "Super Prompt",
  "version": "1.0.0",
  "action": {
    "default_title": "Super Prompt"
  },
  "background": {
    "service_worker": "background.js"
  },
  "side_panel": {
    "default_path": "popup.html"
  },
  "permissions": [
    "sidePanel",
    "storage",
    "tabs",
    "scripting"
  ],
  "host_permissions": [
    "https://gen.pollinations.ai/*",
    "https://chatgpt.com/*",
    "https://chat.openai.com/*"
  ]
}
```

Keep `scripting`, `tabs`, and ChatGPT host permissions if the handoff feature remains. Keep Pollinations host permission if API calls are made directly from the extension.

## Mode Registry

Prompt modes live in `modes.js` inside:

```js
export const PROMPT_MODES = [...]
```

`popup.js` imports:

```js
import { PROMPT_MODES, RESOLUTION_PRESETS, getModeById, validatePromptModes } from "./modes.js";
```

Every mode object must include:

```js
{
  id: "mode-id",
  label: "Visible label",
  purpose: "Short description",
  usage: "Usage help text",
  outputType: "text", // or "json"
  allowImages: true,
  defaultTemperature: 0.7,
  maxOutputTokens: 4096, // optional
  buildPrompt(context) {
    return "...";
  }
}
```

Optional:

```js
buildTimeoutRecoveryPrompt(context) {
  return "...";
}
```

Rules:

- Long prompt templates belong in `modes.js`, not `popup.js`.
- `popup.js` should orchestrate, not contain long product prompt logic.
- Do not hard-code mode dropdown options in `popup.html`.
- Use `validatePromptModes()` after mode edits.
- Valid `outputType` values are only `text` and `json`.
- `defaultTemperature` must be a number from 0 to 2.
- `maxOutputTokens`, if present, must be at least 256.
- Mode IDs must be unique.

## Active MVP Mode

The main MVP mode currently keeps a legacy ID:

```js
id: "outfit-swap-json"
label: "Thay trang phuc"
outputType: "text"
allowImages: true
defaultTemperature: 0.35
maxOutputTokens: 5000
```

Important: despite the `json` suffix, this mode is now text output. It must not return JSON.

Required final output format:

```text
MAIN PROMPT:
...

NEGATIVE PROMPT:
...

REFERENCE BINDING INSTRUCTIONS:
...
```

There must be exactly these three top-level sections, in this order. Do not add Markdown fences, tables, JSON, analysis notes, or extra top-level sections.

## Image Roles

All role definitions exist in `popup.js`:

```js
const IMAGE_ROLES = [
  { id: "model", ... },
  { id: "outfit", ... },
  { id: "makeup", ... },
  { id: "pose", ... },
  { id: "background", ... }
];
```

Only these roles are active in MVP:

```js
const ACTIVE_IMAGE_ROLE_IDS = ["model", "outfit", "background"];
```

Visible MVP roles:

- `model`: A.1 model / identity. Required for best results.
- `outfit`: A.2 outfit / clothing. Required for best results.
- `background`: A.3 background / scene. Optional.

Hidden future roles:

- `makeup`
- `pose`

Rules for hidden roles:

- Do not show them in the MVP UI.
- Do not send them to Pollinations.
- Do not include them in `getAllReferenceImages()`.
- Do not include them in `getReferenceSummary()`.
- Do not include them in ChatGPT Img 2 handoff.
- Keep future-ready code if useful, but inactive.

## Outfit Swap Semantics

Role priority:

1. A.1 model identity: absolute highest priority. Non-negotiable identity lock.
2. A.2 outfit: very high priority for clothing transfer only.
3. A.3 background: medium priority when provided. If missing, use Image 1 background.

Image role meaning:

- Image 1 / A.1 is the locked identity source.
- Image 1 is also the default pose source unless the user explicitly requests a different pose.
- Image 1 is also the default background source if Image 3 is missing.
- Image 2 / A.2 is only the outfit source.
- Image 2 must not change face, gender presentation, body identity, pose, or background.
- Image 3 / A.3 is only the optional background/scene source.

User text is high-value creative guidance for:

- Mood.
- Styling direction.
- Camera.
- Lighting.
- Composition.
- Background atmosphere.
- Excluded items.
- Commercial/editorial feel.

User text must not override:

- Image 1 identity lock.
- Image 2 outfit-only role.
- Image role priority.
- Safety constraints.
- Required output format.

## Identity Rules

The outfit-swap prompt must include these ideas:

- `Identity priority: absolute highest.`
- Preserve the exact identity from Image 1.
- Preserve gender presentation from Image 1.
- Preserve facial structure.
- Preserve face proportions.
- Preserve eyes.
- Preserve nose.
- Preserve lips.
- Preserve jawline.
- Preserve skin tone.
- Preserve natural likeness.
- Preserve overall recognizability.
- Preserve body identity if visible.
- Do not westernize the face.
- Do not beautify the subject into a different person.
- Do not allow identity drift.

Gender-neutral language rule:

- Do not default to `woman`, `female`, `her`, or `she`.
- Use neutral wording by default:
  - `the model from Image 1`
  - `the subject from Image 1`
  - `the person in Image 1`
- Use gendered wording only if the user explicitly requests it or the visual reference safely supports it.

## Outfit Transfer Rules

Image 2 is only for clothing.

The prompt should instruct the image model to:

- Transfer the outfit from Image 2 accurately.
- Match the exact visual color from Image 2.
- Match garment type, fabric, material, fit, silhouette, structure, layering, and visible accessories.
- Remove the original outfit from Image 1 unless it is intentionally part of Image 2.
- Avoid inventing unrelated clothing.
- Avoid inventing unrequested accessories.
- Avoid over-describing guessed colors. If color is uncertain, say to match Image 2 visually.

Image 2 must not alter:

- Face.
- Gender presentation.
- Body identity.
- Pose.
- Background.
- Camera identity cues from Image 1.

## Pose And Background Fallbacks

Pose:

- Preserve the exact pose from Image 1 unless the user explicitly provides a different pose.
- If no pose role exists in MVP, Image 1 remains the default pose source.
- Preserve hand placement, leg placement, stance, torso direction, body orientation, and expression unless the user asks for a simple adjustment.

Background:

- If Image 3 exists, use it as the background/scene reference.
- If Image 3 is missing, preserve or adapt the background from Image 1.
- Do not invent unrelated backgrounds unless explicitly requested by the user.
- Background details should support product/fashion readability.

## Negative Prompt Requirements

The outfit-swap negative prompt must include strong failure blockers. Keep it comma-separated and directly usable.

Required concepts:

- wrong face
- identity drift
- face distortion
- different person
- westernized face
- gender change
- feminized face
- masculinized face
- wrong gender
- altered facial structure
- changed eye shape
- changed nose shape
- changed lips
- changed jawline
- bad hands
- awkward hands
- anatomy errors
- extra fingers
- missing fingers
- distorted limbs
- warped body
- broken body proportions
- outfit mismatch
- incorrect clothing details
- wrong outfit color
- warped clothing
- unrealistic fabric folds
- wrong pose
- pose change
- standing pose if original is seated
- changed hand placement
- changed leg placement
- unnatural pose
- stiff pose
- background mismatch
- wrong background
- AI face
- CGI look
- plastic skin
- over-smoothed skin
- low quality
- blurry
- soft focus
- cropped body
- cut-off limbs
- unnatural shadows
- poor integration
- artificial texture
- low detail
- over-retouched face

## Model Configuration

Model options are defined in `popup.js`:

```js
const MODEL_OPTIONS = [
  {
    label: "GPT-5.4 Nano",
    value: "gpt-5.4-nano",
    supportsImages: true
  },
  {
    label: "GPT-5 Nano",
    value: "gpt-5-nano",
    supportsImages: true
  },
  {
    label: "Gemini 2.5 Flash Lite",
    value: "gemini-flash-lite-3.1",
    supportsImages: true
  }
];
```

User-facing labels must remain exactly:

- `GPT-5.4 Nano`
- `GPT-5 Nano`
- `Gemini 2.5 Flash Lite`

Internal model values may change if Pollinations changes its model names, but keep the mapping clear and centralized.

If a selected model does not support images:

- Do not send images.
- Mark `referenceImagesUnavailable` in context.
- Make the prompt explicitly state that reference images were unavailable.
- Prefer models with image support for outfit swap.

## Pollinations API

Endpoint:

```text
POST https://gen.pollinations.ai/v1/chat/completions
```

Authentication:

```http
Authorization: Bearer <Pollinations API key>
Content-Type: application/json
Accept: application/json
```

API key storage:

```js
chrome.storage.local.set({ superPromptConfig: config });
chrome.storage.local.get("superPromptConfig");
```

Request body shape:

```js
{
  model: selectedModel.value,
  messages: [
    {
      role: "system",
      content: "You are Super Prompt, a precise prompt engineering assistant. Return only the requested artifact."
    },
    {
      role: "user",
      content: [
        { type: "text", text: promptText },
        { type: "text", text: "REFERENCE 1 - ..." },
        { type: "image_url", image_url: { url: image.dataUrl } }
      ]
    }
  ],
  temperature: options.temperature ?? mode.defaultTemperature ?? 0.7,
  max_tokens: options.maxTokens ?? mode.maxOutputTokens ?? 4096,
  stream: false
}
```

Response extraction supports:

- `data.output_text`
- `data.choices[].message.content`
- `data.choices[].text`
- `data.text`
- raw text if the response is non-JSON but HTTP OK.

## Pollinations Error Handling

Required behavior:

- Missing API key: show a clear message asking for a secret `sk_` key.
- 400/422: invalid request or payload.
- 401/403: API key invalid, expired, unauthorized, or model not allowed.
- 402: insufficient balance.
- 404 or invalid model: selected model or endpoint issue.
- 413: payload/image too large. Do not retry without images.
- 429: rate limit.
- 502: Cloudflare/provider bad gateway.
- 503: provider unavailable or overloaded.
- 504: upstream/provider timeout.
- Empty response: show a clear error.
- Network failure: show connection error.

Retry rules:

- Retry 502 and 503 once after `retry_after`, clamped between 5 and 90 seconds.
- Do not drop reference images during retry.
- For 504 timeout, try one compact recovery prompt if the selected mode supports it or use fallback compact instructions.
- Do not retry 413 by silently removing images.

## Image Upload And Compression

Supported MIME types:

```js
const SUPPORTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];
```

Supported file extensions in user messaging:

- jpg
- jpeg
- png
- webp

Image constraints:

```js
const MAX_REFERENCE_IMAGES = 5; // per role group
const MAX_IMAGE_DIMENSION = 1280;
const IMAGE_JPEG_QUALITY = 0.78;
const MAX_TOTAL_IMAGE_PAYLOAD_BYTES = 850 * 1024;
```

Upload behavior:

- User can upload multiple images per active role group.
- Each image is read with `FileReader`.
- Each image is converted to data URL.
- Each image is compressed via canvas when possible.
- Images larger than 1280px on the longest side are resized down.
- PNG under about 180 KB may remain PNG.
- Other large images are converted to JPEG quality `0.78` if smaller.
- Each stored image record includes:

```js
{
  id: crypto.randomUUID(),
  role,
  name,
  type,
  size,
  payloadSize,
  dataUrl
}
```

Payload limit behavior:

- `limitImagePayload(referenceImages)` accepts images until total payload reaches 850 KB.
- If all images are rejected because payload is too large, throw 413.
- Do not generate a final prompt that pretends missing reference images were sent.
- For outfit swap, model and outfit images are expected for reliable results.

Preview behavior:

- Render thumbnail previews for each role.
- Show role badge.
- Allow removing each image.
- Allow clearing all reference images.

## Reference Image Labels

When calling Pollinations, each image is preceded by a text label. For outfit swap:

- `model`: A.1 model identity / final Image 1.
- `outfit`: A.2 outfit / final Image 2.
- `background`: A.3 background / optional final Image 3.
- `makeup`: future disabled role; must not be active in MVP.
- `pose`: future disabled role; must not be active in MVP.

The label is part of the model instruction. It must reinforce role separation.

Model label must say:

- Absolute highest priority.
- Locked identity.
- Face, skin tone, facial structure, face proportions, body proportion if visible, natural likeness.
- Becomes final ChatGPT Img 2 Image 1.

Outfit label must say:

- Very high priority.
- Outfit source only.
- Garment type, fabric, exact visual color, fit, silhouette, layering, styling, visible accessories.
- Becomes final ChatGPT Img 2 Image 2.
- Color should be matched from image, not guessed from text.

Background label must say:

- Optional background reference.
- Scene type, environment, lighting, perspective, depth, atmosphere, palette, and mood.
- If missing, fallback to Image 1 background.

## Context Object

`popup.js` builds a context object before calling `mode.buildPrompt(context)`:

```js
{
  userInput,
  style,
  aspectRatio,
  resolution,
  quality,
  selectedModel,
  hasReferenceImages,
  referenceImagesUnavailable,
  referenceImageCount,
  referenceSummary,
  language: "English",
  modeId,
  modeLabel,
  maxOutputTokens
}
```

Mode prompt builders should depend on this context, not on DOM state.

## Output Validation

For `outfit-swap-json`:

- Output must be non-empty.
- Output must include:
  - `MAIN PROMPT:`
  - `NEGATIVE PROMPT:`
  - `REFERENCE BINDING INSTRUCTIONS:`

For JSON modes:

- Output must be non-empty.
- Output must parse with `JSON.parse`.
- If parsing fails, show a useful error indicating possible token truncation.

## UI Behavior

UI direction:

- Side-panel friendly.
- Dark neon style.
- Compact settings.
- Output always visible and scrollable.

Required controls:

- API settings toggle.
- API key field.
- API key visibility toggle.
- Model dropdown.
- Test API button.
- Mode dropdown rendered from `PROMPT_MODES`.
- Mode helper show/hide toggle.
- User input textarea.
- Image upload groups for active roles.
- Clear images button.
- Style selector.
- Aspect ratio selector.
- Resolution selector.
- Quality selector.
- Generate button.
- Output box.
- Copy output button.
- Copy IMG2 prompt button.
- Send to ChatGPT Img 2 button.
- Download TXT button.
- Clear output button.

Do not show makeup/pose upload cards in the MVP unless they are reactivated.

Outfit helper text should clearly say:

- A.1 model and A.2 outfit are recommended/required for best results.
- A.3 background is optional.
- Makeup and pose are not part of the current MVP.
- Final ChatGPT Img 2 step uses Image 1, Image 2, and optional Image 3.

## ChatGPT Img 2 Handoff

The handoff feature must not auto-submit. It only uploads images and fills the prompt.

Expected handoff flow:

1. User generates or has output text.
2. User clicks the ChatGPT Img 2 handoff button.
3. `popup.js` builds handoff image list from active roles only.
4. It validates at least model and outfit images exist.
5. It opens or focuses `https://chatgpt.com/`.
6. It injects `chatgpt-img2-content.js`.
7. It sends a message with type:

```js
{
  type: "SUPER_PROMPT_IMG2_HANDOFF_V2",
  images,
  promptText
}
```

8. Content script waits for composer.
9. Content script uploads images one at a time.
10. It waits for each attachment to settle before uploading the next.
11. It fills the prompt after all images settle.
12. User manually reviews and clicks Send.

Sequential upload is mandatory. Do not upload all images in one batch.

Content script version marker:

```js
const CONTENT_VERSION = "SUPER_PROMPT_IMG2_SEQUENTIAL_V2";
```

Content script message type:

```js
"SUPER_PROMPT_IMG2_HANDOFF_V2"
```

Content script selectors:

- Composer candidates:
  - `[data-testid="prompt-textarea"]`
  - `#prompt-textarea`
  - `textarea[placeholder]`
  - `textarea`
  - `div[contenteditable="true"]`
- File input:
  - `input[type="file"]`
  - Accepts image, `.png`, `.jpg`, `.jpeg`, `.webp`
- Attachment count:
  - blob/data images
  - attachment/file data-testid
  - attachment/remove aria labels
  - remove buttons
- Upload busy detection:
  - `[aria-busy="true"]`
  - upload/progress test ids
  - `role="progressbar"`
  - buttons with labels such as stop, cancel upload, uploading, remove uploading

Settle timing:

- Wait for expected attachment count.
- Wait until upload is not busy.
- Require about 2.6 seconds stable time.
- Add about 0.9 seconds after settle.

If ChatGPT UI changes, update `chatgpt-img2-content.js` first.

## Copy And Download Behavior

The extension should support:

- Copy full output.
- Copy IMG2 prompt if the output is JSON from old modes and contains nested copy-ready fields.
- Download output as `.txt`.
- Clear output.

Outfit-swap MVP output is plain text, so the full output can be copied directly.

Legacy JSON extraction may check:

- `final_image_prompt.chatgpt_img2.copy_ready_prompt`
- `final_image_prompt.chatgpt_img2_copy_ready_prompt`
- `chatgpt_img2_prompt.copy_ready_prompt`
- matching negative prompt fields

Keep this for backward compatibility if older JSON modes remain.

## Settings Persistence

Store config in:

```js
chrome.storage.local
```

Storage key:

```js
superPromptConfig
```

Expected saved config includes:

- API key.
- Selected model.
- Selected mode.
- Style.
- Aspect ratio.
- Resolution.
- Quality.
- Collapsed/expanded UI preferences if implemented.

Do not store uploaded images permanently unless explicitly adding a history feature.

## Resolution And Quality

`modes.js` exports `RESOLUTION_PRESETS`. The UI resolves final resolution from:

- aspect ratio
- resolution preset
- quality

Prompt builders should include:

- selected style
- aspect ratio
- resolved resolution
- quality

Do not hard-code resolution text inside a mode when the context already provides it.

## Common Modes

The repository may include additional modes besides outfit swap:

- Character JSON.
- Product detail shots.
- Storyboard 3x3.
- Advanced storyboard.
- Reference pack.
- Image-to-video.
- JSON-to-natural-prompt.

Rules for non-MVP modes:

- Preserve existing behavior unless asked.
- JSON modes must return parseable JSON only.
- Text modes must return plain text only.
- Image-enabled modes may use active reference images as consistency references.

## Change Playbooks

### Change Outfit Swap Prompt

Edit `modes.js`, specifically the outfit-swap text prompt builder.

Keep:

- Three required sections.
- Plain text only.
- No JSON.
- No Markdown fences.
- Gender-neutral default wording.
- Image 1 identity lock.
- Image 2 outfit-only role.
- Optional Image 3 background.
- Image 1 pose/background fallback.
- Strong negative prompt blockers.

Then update `TEST_CASES.md`.

### Add A New Mode

1. Add a mode object to `PROMPT_MODES`.
2. Put long templates in `modes.js`.
3. Do not modify `popup.html` for dropdown options.
4. Set `outputType` correctly.
5. Set `allowImages` correctly.
6. Add `maxOutputTokens` if the output is long.
7. Run syntax checks.
8. Update `TEST_CASES.md`.

### Reactivate Makeup Or Pose

Do not rewrite the upload system.

1. Add the role id back to `ACTIVE_IMAGE_ROLE_IDS`.
2. Show the matching UI card.
3. Update image role labels.
4. Update reference summaries.
5. Update `getReferenceImageLabel`.
6. Update outfit prompt rules.
7. Update ChatGPT handoff role order if the final generation should upload those images.
8. Update tests.

Important: if makeup or pose are only analysis roles, do not upload them to ChatGPT final generation. Convert them into text instructions first.

### Change Pollinations Models

1. Update `MODEL_OPTIONS` in `popup.js`.
2. Keep user-facing labels stable if the product requirement still says so.
3. Update internal `value` slugs only after verifying Pollinations supports them.
4. Update notes if a model requires paid access or image support changes.
5. Test API with every listed model.

### Fix API Errors

Check:

- API key exists.
- Model slug is valid.
- Payload is under size limits.
- Images are valid data URLs.
- Endpoint host permission exists.
- Pollinations is not returning 502/503/504.

Do not solve 413 by dropping images silently. That breaks the product promise.

### Fix ChatGPT Handoff

Check:

- ChatGPT tab opens.
- User is logged in.
- Content script injects.
- Message type matches.
- File input selector still works.
- Composer selector still works.
- Attachment count increases after each upload.
- Busy/progress selector reflects current UI.
- Prompt fills only after all images settle.
- Extension does not auto-click Send.

## Testing Requirements

Syntax checks:

```powershell
node --check popup.js
node --check modes.js
node --check background.js
node --check chatgpt-img2-content.js
node -e "JSON.parse(require('fs').readFileSync('manifest.json','utf8')); console.log('manifest ok')"
```

Manual extension checks:

- Load unpacked extension in Chrome.
- Open the side panel.
- Confirm no layout break.
- Confirm mode dropdown renders from `PROMPT_MODES`.
- Confirm outfit mode shows only active MVP roles.
- Confirm makeup/pose are hidden.
- Upload A.1 model image.
- Upload A.2 outfit image.
- Optionally upload A.3 background image.
- Confirm thumbnails and role badges render.
- Remove an image and confirm state updates.
- Clear all images and confirm state resets.
- Test API key connection.
- Generate outfit prompt.
- Confirm output has exactly:
  - `MAIN PROMPT:`
  - `NEGATIVE PROMPT:`
  - `REFERENCE BINDING INSTRUCTIONS:`
- Confirm output is not JSON.
- Confirm no Markdown code fence.
- Confirm it does not default to `woman`, `female`, `her`, or `she`.
- Confirm it says preserve gender presentation from Image 1.
- Confirm Image 2 is outfit-only.
- Confirm Image 3 is optional background only.
- Confirm 413 or compression failure stops generation clearly.
- Confirm 502/503 retry keeps images.
- Confirm 504 compact retry keeps images.
- Confirm ChatGPT handoff uploads images one by one.
- Confirm ChatGPT prompt is filled after uploads.
- Confirm the extension does not click Send.

Recommended browser automation tools:

- Node.js.
- Playwright.
- Chrome or Edge real browser executable.
- Persistent browser profile for extension tests.
- Fixture images for model, outfit, and background.
- Screenshot checks for side panel UI.
- DOM checks for active role cards and generated output.

## Packaging Checklist

Before Chrome Web Store packaging:

- Verify manifest version and extension version.
- Verify no dev-only files are referenced by runtime.
- Verify no secret API keys are committed.
- Verify host permissions are minimal and justified.
- Verify side panel opens on action click.
- Verify all text and UI states are understandable.
- Verify privacy story: BYO Pollinations key, no backend.
- Verify `TEST_CASES.md` covers current MVP behavior.
- Remove or ignore local screenshots/test profiles from package if not needed.

## Privacy And Data Handling

Current design:

- BYO Pollinations API key.
- API key stored locally in `chrome.storage.local`.
- Uploaded images are held in runtime memory state as data URLs.
- Images are sent to Pollinations only when generating a prompt with an image-capable mode/model.
- Images are sent to ChatGPT only when user triggers handoff.
- No backend owned by this extension.
- No automatic final ChatGPT submission.

If adding history, cloud sync, analytics, or backend processing later, update privacy messaging and permission scope.

## Important Non-Negotiables

- MVP is outfit swap, not general prompt lab.
- `outfit-swap-json` is text output despite legacy ID.
- Outfit output must have exactly three top-level sections.
- Do not return JSON for outfit mode.
- Do not default to female wording.
- Image 1 identity has absolute highest priority.
- Image 2 is outfit only.
- Image 3 is optional background only.
- Makeup and pose are inactive in MVP.
- Hidden roles must not be sent to API or ChatGPT.
- Do not retry image failures by silently dropping images.
- Do not upload all ChatGPT handoff images at once.
- Do not auto-submit in ChatGPT.
