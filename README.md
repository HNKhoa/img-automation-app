# Img automation App

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

Desktop app cross-platform dùng `pywebview`: Python backend + HTML/CSS/JS frontend. MVP tập trung mode `outfit_swap` theo `SKILL.md` và `outfit_swap_skill.md`.

## Chạy app

```powershell
.\run_app.ps1
```

Nếu đã có Python hệ thống:

```powershell
pip install -r requirements.txt
python app.py
```

## Cấu hình API

Tạo file `.env` từ `.env.example`:

```text
POLLINATIONS_API_KEY=sk_your_key_here
POLLINATIONS_ENDPOINTS=https://gen.pollinations.ai/v1/chat/completions,https://text.pollinations.ai/openai
DEFAULT_MODEL=gpt-5.4-nano
REQUEST_TIMEOUT_SECONDS=90
```

Có thể nhập API key trực tiếp trong UI. Key nhập trong UI chỉ dùng cho request hiện tại.

## Request backend nội bộ

Frontend gọi `window.pywebview.api.generate_prompt(payload)`:

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
  "user_request": "Giữ mặt mẫu, bám sát outfit gốc, nền studio mềm.",
  "images": [
    { "role": "model", "name": "model.jpg", "type": "image/jpeg", "dataUrl": "data:image/jpeg;base64,..." },
    { "role": "outfit", "name": "outfit.jpg", "type": "image/jpeg", "dataUrl": "data:image/jpeg;base64,..." }
  ]
}
```

Response thành công:

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
