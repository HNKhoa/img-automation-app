# Img automation App - Tai lieu chi tiet

## 1. Tong quan

`Img automation App` la ung dung desktop cross-platform dung `pywebview`, gom:

- Backend Python trong `app.py` va thu muc `backend/`.
- Frontend HTML/CSS/JavaScript trong `frontend/`.
- Workflow tao prompt bang Pollinations/OpenAI-compatible endpoint.
- Workflow tu dong mo ChatGPT, upload anh tham chieu, gui prompt va tai anh ket qua bang request thong qua Chromium Automation.

MVP cua app la mode `outfit-swap-json`: tao prompt thay trang phuc giu identity tu anh mau, anh outfit va tuy chon anh background. Cac mode khac chay theo dang plugin/generic mode de tao prompt hoac JSON cho nhieu nhu cau sang tao.

## 2. Kien truc hien tai

```text
Nguoi dung
  |
  v
Pywebview Desktop Window
  |
  | window.pywebview.api
  v
DesktopApi trong app.py
  |
  +-- PromptWorkflow
  |     +-- Outfit swap workflow
  |     +-- Generic generation modes
  |     +-- PollinationsClient
  |
  +-- ChatGptImageAutomationService
  |     +-- Profile Manager: http://127.0.0.1:58001
  |     +-- Chromium Automation Port: http://127.0.0.1:<dynamic-port>
  |     +-- ChatGPT web session
  |
  +-- ChromeProfileService
        +-- Danh sach profile Chromium/Chrome tren may
```

Luu y quan trong:

- `app.py` hien mo frontend bang `frontend/index.html` thong qua `file://` trong cua so pywebview.
- Cac chuc nang day du can `window.pywebview.api`, nen khong nen mo truc tiep `frontend/index.html` bang browser thuong de dung that.
- `http://127.0.0.1:58001` la Profile Manager cho Chromium Automation, khong phai web server chinh cua app.
- Chromium Automation moi lan mo profile co the tra ve mot `automation_port` dong. App co co che fallback sang port cau hinh neu Profile Manager tra ve port chet.

## 3. Chuc nang chinh

### 3.1 Tao prompt outfit swap

Mode `outfit-swap-json` dung 3 nhom anh:

- `A.1 Model identity`: anh nguoi mau, bat buoc.
- `A.2 Outfit source`: anh trang phuc nguon, bat buoc.
- `A.3 Background`: anh nen, tuy chon.

Ket qua tra ve dang 3 section:

```text
MAIN PROMPT:
...

NEGATIVE PROMPT:
...

REFERENCE BINDING INSTRUCTIONS:
...
```

Prompt duoc toi uu de:

- Giu identity cua nguoi mau.
- Phan tich va chuyen outfit tu anh tham chieu.
- Khoa vai tro tung anh tham chieu.
- Tao prompt de dung voi ChatGPT Image hoac cac model anh tuong thich.

### 3.2 Generation modes

Danh sach mode hien co duoc backend tra ve qua `DesktopApi.get_bootstrap()` va frontend render dong trong dropdown.

| Mode ID | Nhan hien thi | Kieu output | Anh dau vao | Muc dich |
| --- | --- | --- | --- | --- |
| `outfit-swap-json` | Thay trang phuc | text | A.1/A.2 bat buoc, A.3 tuy chon | Tao prompt thay trang phuc giu identity |
| `character-json` | JSON nhan vat | json | Toi da 5 reference | Tao JSON mo ta nhan vat/portrait |
| `product-detail-shots` | Shot chi tiet san pham | text | Toi da 5 reference | Tao 9 shot san pham |
| `storyboard-unified` | Storyboard thong nhat | json | Toi da 5 reference | Tao storyboard 3-12 scene, gom image prompt va video motion prompt |
| `reference-pack` | Bo anh tham chieu | text | Toi da 5 reference | Tao goi reference Character/Background/Product |
| `image-to-video` | Prompt anh sang video | json | Toi da 5 reference | Tao prompt chuyen anh sang video |
| `json-to-natural-prompt` | JSON sang prompt tu nhien | text | Khong gui anh | Chuyen JSON thanh prompt tu nhien |

Khi chon mode generic:

- Cum upload A.1/A.2/A.3 se an di.
- App dung upload reference chung neu mode cho phep anh.
- Payload generic chi gui role `reference`, khong gui role outfit-specific.
- Style mac dinh co the la `None` de tranh bias phong cach khong can thiet.

### 3.3 Tu dong tao anh tren ChatGPT Img2

App co workflow tu dong:

1. Lay prompt vua tao trong app.
2. Lay cac anh tham chieu dang co trong UI.
3. Mo hoac ket noi Chromium profile da dang nhap ChatGPT.
4. Dieu huong toi `https://chatgpt.com/`.
5. Upload anh theo thu tu.
6. Xac nhan moi anh upload xong bang network request.
7. Nhap prompt vao ChatGPT.
8. Bam gui.
9. Cho ket qua anh that su xuat hien qua request `backend-api/estuary/content`.
10. Tai anh ve bang request, khong phu thuoc nut download tren giao dien.
11. Kiem tra file tai ve co magic bytes cua anh PNG/JPEG/WebP/GIF truoc khi bao thanh cong.

Ket qua mac dinh luu trong:

```text
C:\Users\hongu\Documents\tool_vibe_code\app prompt\downloads
```

Neu cau hinh `CHROMIUM_DOWNLOAD_DIR` trong `.env`, app se uu tien thu muc do.

## 4. Cau hinh `.env`

Tao file `.env` tai root project:

```env
POLLINATIONS_API_KEY=sk_your_secret_key_here
POLLINATIONS_ENDPOINTS=https://gen.pollinations.ai/v1/chat/completions,https://text.pollinations.ai/openai
DEFAULT_MODEL=gpt-5.4-nano
REQUEST_TIMEOUT_SECONDS=90

CHROMIUM_PROFILE_MANAGER_URL=http://127.0.0.1:58001
CHROMIUM_PROFILE_ID=
CHROMIUM_AUTOMATION_PORT=0
CHROMIUM_STARTUP_TIMEOUT_MS=30000
CHROMIUM_REQUEST_TIMEOUT_MS=15000
CHROMIUM_DEFAULT_TAB_ID=0
CHROMIUM_DOWNLOAD_DIR=
CHROMIUM_GENERATION_TIMEOUT_MS=240000
```

Y nghia cac bien quan trong:

| Bien | Muc dich |
| --- | --- |
| `POLLINATIONS_API_KEY` | Secret key dung de goi Pollinations API |
| `POLLINATIONS_ENDPOINTS` | Danh sach endpoint cach nhau bang dau phay, app co failover |
| `DEFAULT_MODEL` | Model mac dinh khi app khoi dong |
| `REQUEST_TIMEOUT_SECONDS` | Timeout request Pollinations, clamp trong backend |
| `CHROMIUM_PROFILE_MANAGER_URL` | URL Profile Manager, mac dinh `http://127.0.0.1:58001` |
| `CHROMIUM_PROFILE_ID` | Profile Chromium da dang nhap ChatGPT |
| `CHROMIUM_AUTOMATION_PORT` | Port automation co dinh khi debug/test |
| `CHROMIUM_DOWNLOAD_DIR` | Thu muc luu anh ChatGPT tai ve |
| `CHROMIUM_GENERATION_TIMEOUT_MS` | Thoi gian cho ChatGPT tao anh |

Bao mat:

- Khong commit `.env`.
- Khong dua API key vao file tai lieu, README, test snapshot hoac log.
- Khong in signed URL cua ChatGPT content request ra log cong khai.

## 5. Cach chay app

### 5.1 Chay bang script co san

```powershell
cd "C:\Users\hongu\Documents\tool_vibe_code\app prompt"
.\run_app.ps1
```

### 5.2 Chay truc tiep bang Python trong virtualenv

```powershell
cd "C:\Users\hongu\Documents\tool_vibe_code\app prompt"
.\.venv\Scripts\python.exe app.py
```

### 5.3 Cai dependencies neu tao moi moi truong

```powershell
cd "C:\Users\hongu\Documents\tool_vibe_code\app prompt"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## 6. Luong request backend noi bo

Frontend goi backend qua `window.pywebview.api`.

### 6.1 Bootstrap

```javascript
const bootstrap = await window.pywebview.api.get_bootstrap();
```

Response gom:

- `config`
- `model_options`
- `target_options`
- `quality_profiles`
- `style_options`
- `aspect_ratio_options`
- `resolution_options`
- `generation_modes`
- `profiles`

### 6.2 Tao prompt

Payload outfit:

```json
{
  "api_key": "sk_...",
  "mode": "outfit-swap-json",
  "model": "gpt-5.4-nano",
  "target_model_rule": "chatgpt_img",
  "style": "High-end fashion editorial",
  "aspect_ratio": "1:1",
  "resolution": "2K",
  "quality": "High",
  "user_request": "Giu mat mau, bam sat outfit goc, anh sang studio mem.",
  "images": [
    {
      "role": "model",
      "name": "model.jpg",
      "type": "image/jpeg",
      "dataUrl": "data:image/jpeg;base64,..."
    },
    {
      "role": "outfit",
      "name": "outfit.jpg",
      "type": "image/jpeg",
      "dataUrl": "data:image/jpeg;base64,..."
    },
    {
      "role": "background",
      "name": "background.jpg",
      "type": "image/jpeg",
      "dataUrl": "data:image/jpeg;base64,..."
    }
  ]
}
```

Payload generic:

```json
{
  "api_key": "sk_...",
  "mode": "character-json",
  "model": "gpt-5.4-nano",
  "style": "None",
  "aspect_ratio": "1:1",
  "resolution": "2K",
  "quality": "High",
  "user_request": "Tao nhan vat cyber fashion portrait.",
  "images": [
    {
      "role": "reference",
      "name": "ref.jpg",
      "type": "image/jpeg",
      "dataUrl": "data:image/jpeg;base64,..."
    }
  ]
}
```

### 6.3 Tu dong tao anh ChatGPT

```javascript
const result = await window.pywebview.api.auto_generate_chatgpt_image({
  prompt_text: outputText,
  images: currentImages,
  chromium_profile_id: "profile-id-da-dang-nhap-chatgpt",
  chromium_automation_port: "48019",
  download_dir: "C:\\Users\\hongu\\Documents\\tool_vibe_code\\app prompt\\downloads"
});
```

Response thanh cong:

```json
{
  "ok": true,
  "url": "https://chatgpt.com/",
  "automation_port": 48019,
  "uploaded_count": 3,
  "auto_submitted": true,
  "downloaded_path": "C:\\Users\\hongu\\Documents\\tool_vibe_code\\app prompt\\downloads\\chatgpt-img2-20260516-214643.png",
  "download_method": "request",
  "image_verified": true
}
```

## 7. Cau truc thu muc quan trong

```text
app prompt/
├─ app.py
├─ backend/
│  ├─ config.py
│  ├─ constants.py
│  ├─ modes/
│  ├─ prompts/
│  └─ services/
│     ├─ prompt_workflow.py
│     ├─ pollinations_client.py
│     ├─ chatgpt_image_automation.py
│     ├─ chrome_profiles.py
│     ├─ image_preprocess.py
│     ├─ cache_service.py
│     └─ cache_keys.py
├─ frontend/
│  ├─ index.html
│  ├─ app.js
│  ├─ modes.js
│  ├─ styles.css
│  ├─ i18n-runtime.js
│  └─ assets/
├─ tests/
├─ relay/
├─ tools/
├─ downloads/
└─ .env
```

## 8. Xu ly loi thuong gap

### 8.1 `window.pywebview.api` khong san sang

Nguyen nhan thuong gap:

- Mo `frontend/index.html` truc tiep bang browser thuong.
- Pywebview chua attach API kip luc frontend bootstrap.

Cach dung dung:

```powershell
.\.venv\Scripts\python.exe app.py
```

### 8.2 Pollinations bi Cloudflare chan

App da co:

- `curl_cffi` impersonation.
- Multi-endpoint failover.
- Ho tro custom relay endpoint.

Kiem tra `.env`:

```env
POLLINATIONS_ENDPOINTS=https://gen.pollinations.ai/v1/chat/completions,https://text.pollinations.ai/openai
```

Neu can relay rieng, xem:

```text
relay/README.md
```

### 8.3 ChatGPT automation bao thanh cong qua som

Workflow moi chi bao thanh cong khi:

- Da submit prompt.
- Bat duoc request ket qua moi sau thoi diem submit.
- Request ket qua la 2xx.
- File tai ve co dinh dang anh hop le.

Neu van gap loi, kiem tra:

- Profile da dang nhap ChatGPT chua.
- `CHROMIUM_PROFILE_ID` dung chua.
- `CHROMIUM_AUTOMATION_PORT` con song khong.
- Thu muc download co quyen ghi khong.

### 8.4 Upload anh len ChatGPT khong dung thu tu

Workflow upload tung anh mot:

1. Clear network capture.
2. Upload anh hien tai.
3. Cho request upload 2xx.
4. Doi them `UPLOAD_SETTLE_SECONDS`.
5. Moi upload anh tiep theo.

Neu ChatGPT UI thay doi selector, can cap nhat `TEXTBOX_XPATHS`, `FILE_INPUT_XPATHS`, `SEND_BUTTON_XPATHS` trong:

```text
backend/services/chatgpt_image_automation.py
```

## 9. Kiem thu

Chay test backend:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Chay lint Python:

```powershell
.\.venv\Scripts\python.exe -m ruff check app.py backend tests
```

Chay test frontend:

```powershell
npm run test:static
npm run test:unit
```

Chay render check frontend:

```powershell
npm run test:render
```

Test rieng ChatGPT automation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_chatgpt_image_automation.py -q
```

## 10. Ghi chu phat trien tiep

Huong nang cap nen uu tien:

1. Chuan hoa lai encoding tieng Viet trong cac file cu dang bi mojibake.
2. Tach tai lieu build/installer ra thu muc `docs/`.
3. Them man hinh cai dat tap trung cho API key, relay, Chromium profile va download dir.
4. Them log an toan cho ChatGPT automation: chi log event code, khong log prompt day du, API key hoac signed content URL.
5. Them cache cho generic modes neu nhu cau goi lai prompt lap nhieu.

