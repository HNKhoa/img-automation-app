# Img automation App

[![Built with Pollinations](https://img.shields.io/badge/Built%20with-Pollinations-8a2be2?style=for-the-badge)](https://pollinations.ai)

## Cloudflare resilience

Pollinations requests use three layers:

- L1: `curl_cffi` TLS/H2 impersonation.
- L2: multi-endpoint failover via `POLLINATIONS_ENDPOINTS`.
- L3: optional Cloudflare Worker relay in `relay/`.

Example `.env`:

```text
POLLINATIONS_API_KEY=sk_your_secret_key_here
POLLINATIONS_ENDPOINTS=https://relay.your-domain.com/v1/chat/completions,https://gen.pollinations.ai/v1/chat/completions,https://text.pollinations.ai/openai
DEFAULT_MODEL=gpt-5.4-nano
REQUEST_TIMEOUT_SECONDS=90
```

Old `.env` files using `POLLINATIONS_ENDPOINT=` still work as a single endpoint. After adding or updating `curl_cffi`, rebuild the PyInstaller app because old `.exe` builds do not contain the new transport dependencies. Relay deploy steps are in `relay/README.md`.

## Native build báº±ng Nuitka

Build native binary/app bundle báº±ng Nuitka:

- Windows: `build.bat`
- macOS: `chmod +x build.sh && ./build.sh`

Chi tiáº¿t cÃ i Ä‘áº·t theo tá»«ng OS á»Ÿ [BUILD_NUITKA.md](BUILD_NUITKA.md).

## One-click Installer cho Windows

Táº¡o installer cho ngÆ°á»i dÃ¹ng cuá»‘i:

```bat
build_installer.bat
```

Chi tiáº¿t á»Ÿ [INSTALLER_WINDOWS.md](INSTALLER_WINDOWS.md).

Desktop app cross-platform dÃ¹ng `pywebview`: Python backend + HTML/CSS/JS frontend. MVP táº­p trung mode `outfit_swap` theo `SKILL.md` vÃ  `outfit_swap_skill.md`.

## Generation modes

App hiá»‡n cÃ³ 7 mode trong dropdown `Cháº¿ Ä‘á»™ táº¡o prompt`. `outfit-swap-json` váº«n lÃ  MVP vÃ  giá»¯ nguyÃªn payload/validator cÅ©; 6 mode cÃ²n láº¡i cháº¡y theo plugin track generic vá»›i role áº£nh `reference`.

| mode_id | Output | áº¢nh | Ghi chÃº |
| --- | --- | --- | --- |
| `outfit-swap-json` | text | A.1/A.2 báº¯t buá»™c, A.3 tÃ¹y chá»n | Thay trang phá»¥c giá»¯ identity |
| `character-json` | json | tá»‘i Ä‘a 5 reference | JSON nhÃ¢n váº­t/portrait |
| `product-detail-shots` | text | tá»‘i Ä‘a 5 reference | 9 shot chi tiáº¿t sáº£n pháº©m |
| `storyboard-unified` | json | tá»‘i Ä‘a 5 reference | Storyboard 3-12 scene, gá»“m image prompt + video motion prompt |
| `reference-pack` | text | tá»‘i Ä‘a 5 reference | Character/Background/Product reference pack |
| `image-to-video` | json | tá»‘i Ä‘a 5 reference | Prompt chuyá»ƒn áº£nh sang video |
| `json-to-natural-prompt` | text | khÃ´ng gá»­i áº£nh | Chuyá»ƒn JSON sang prompt tá»± nhiÃªn |

Ghi chÃº UI: khi chá»n mode generic, cá»¥m A.1/A.2/A.3, trÆ°á»ng `ÄÃ­ch` vÃ  nÃºt handoff ChatGPT sáº½ collapse má»m. Style máº·c Ä‘á»‹nh cá»§a generic lÃ  `None` Ä‘á»ƒ trÃ¡nh bias fashion; riÃªng `storyboard-unified` cÃ³ hint sá»‘ scene dÆ°á»›i Ã´ ná»™i dung, vÃ­ dá»¥ `6 canh`, `9 scenes`, `12 frames`.

VÃ­ dá»¥ payload generic:

```json
{
  "api_key": "sk_...",
  "mode": "character-json",
  "model": "gpt-5.4-nano",
  "style": "High-end fashion editorial",
  "aspect_ratio": "1:1",
  "resolution": "2K",
  "quality": "high",
  "user_request": "Create a cyber fashion portrait.",
  "images": [
    { "role": "reference", "name": "ref.jpg", "type": "image/jpeg", "dataUrl": "data:image/jpeg;base64,..." }
  ]
}
```

## Cháº¡y app

```powershell
.\run_app.ps1
```

Náº¿u Ä‘Ã£ cÃ³ Python há»‡ thá»‘ng:

```powershell
pip install -r requirements.txt
python app.py
```

## Cáº¥u hÃ¬nh API

Táº¡o file `.env` tá»« `.env.example`:

```text
POLLINATIONS_API_KEY=sk_your_key_here
POLLINATIONS_ENDPOINTS=https://gen.pollinations.ai/v1/chat/completions,https://text.pollinations.ai/openai
DEFAULT_MODEL=gpt-5.4-nano
REQUEST_TIMEOUT_SECONDS=90
```

CÃ³ thá»ƒ nháº­p API key trá»±c tiáº¿p trong UI. Key nháº­p trong UI chá»‰ dÃ¹ng cho request hiá»‡n táº¡i.

## Request backend ná»™i bá»™

Frontend gá»i `window.pywebview.api.generate_prompt(payload)`:

```json
{
  "api_key": "sk_...",
  "mode": "outfit-swap-json",
  "model": "gpt-5.4-nano",
  "target_model_rule": "chatgpt_img",
  "style": "High-end fashion editorial",
  "aspect_ratio": "1:1",
  "resolution": "2K",
  "quality": "high",
  "user_request": "Giá»¯ máº·t máº«u, bÃ¡m sÃ¡t outfit gá»‘c, ná»n studio má»m.",
  "images": [
    { "role": "model", "name": "model.jpg", "type": "image/jpeg", "dataUrl": "data:image/jpeg;base64,..." },
    { "role": "outfit", "name": "outfit.jpg", "type": "image/jpeg", "dataUrl": "data:image/jpeg;base64,..." }
  ]
}
```

Response thÃ nh cÃ´ng:

```json
{
  "ok": true,
  "mode": "outfit_swap",
  "models": { "prompt_builder": "gpt-5.4-nano" },
  "result": {
    "output": "MAIN PROMPT:\n...\n\nNEGATIVE PROMPT:\n...\n\nREFERENCE BINDING INSTRUCTIONS:\n...",
    "reference_count": 2
  }
}
```
