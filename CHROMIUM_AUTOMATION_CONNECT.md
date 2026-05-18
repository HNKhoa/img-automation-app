# Hướng Dẫn Kết Nối Chromium Automation Cho App

Tài liệu này mô tả cách app kết nối với Chromium Automation để tạo profile, mở browser, lấy `automation_port`, rồi điều khiển web bằng HTTP API.

## 1. Kiến Trúc Kết Nối

```text
App của bạn
  |
  | HTTP REST
  v
Profile Manager: http://127.0.0.1:58001
  |
  | POST /profiles/{id}/open
  v
Chromium Automation Port: http://127.0.0.1:{automation_port}
  |
  | /navigate /click /type /scroll /wait /cookie /network ...
  v
Chromium browser profile
```

Có 2 lớp API:

1. `Profile Manager` cố định ở `http://127.0.0.1:58001`
2. `Chromium Automation API` nằm ở port động, ví dụ `http://127.0.0.1:41917`

`automation_port` thay đổi mỗi lần mở profile, nên app phải lưu `profile_id` và gọi `/open` để lấy port mới.

## 2. Cấu Hình Đề Xuất Cho App

Đưa các giá trị này vào `.env` hoặc config của app:

```env
CHROMIUM_PROFILE_MANAGER_URL=http://127.0.0.1:58001
CHROMIUM_STARTUP_TIMEOUT_MS=30000
CHROMIUM_REQUEST_TIMEOUT_MS=15000
CHROMIUM_DEFAULT_TAB_ID=0
```

Không hard-code `automation_port` nếu app tự tạo/mở profile. Chỉ dùng port cố định khi debug hoặc khi user nhập port có sẵn.

## 3. Flow Chuẩn

### Bước 1: Tạo Profile

Request:

```http
POST http://127.0.0.1:58001/profiles
Content-Type: application/json

{
  "name": "app-auto-profile",
  "browser": "chromium",
  "language": "vi-VN,vi",
  "timezone": "Asia/Ho_Chi_Minh"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "9e073bc2ad7c41799366e289602f3ed1",
    "name": "app-auto-profile",
    "automation_port": null
  }
}
```

App cần lưu lại:

```text
profile_id = data.id
```

### Bước 2: Mở Profile Và Lấy Port

Request:

```http
POST http://127.0.0.1:58001/profiles/{profile_id}/open
```

Response:

```json
{
  "success": true,
  "data": {
    "automation_port": 41917
  }
}
```

App tạo base URL:

```text
automation_url = http://127.0.0.1:41917
```

### Bước 3: Chờ Automation API Sẵn Sàng

Gọi lặp `GET /status` đến khi `ok=true`.

Request:

```http
GET http://127.0.0.1:41917/status
```

Response:

```json
{
  "ok": true,
  "version": "1",
  "hasBrowser": true,
  "browser": "chromium"
}
```

Khuyến nghị:

```text
timeout tổng: 30 giây
interval retry: 500-1000ms
```

### Bước 4: Điều Khiển Web

Mở web:

```http
POST http://127.0.0.1:41917/navigate
Content-Type: application/json

{
  "tabId": 0,
  "url": "https://www.24h.com.vn/"
}
```

Chờ DOM sẵn sàng:

```http
POST http://127.0.0.1:41917/wait
Content-Type: application/json

{
  "tabId": 0,
  "condition": "domready",
  "timeout": 15000
}
```

Click link:

```http
POST http://127.0.0.1:41917/click
Content-Type: application/json

{
  "tabId": 0,
  "xpath": "(//a[@href])[4]",
  "native": false
}
```

Scroll:

```http
POST http://127.0.0.1:41917/scroll
Content-Type: application/json

{
  "tabId": 0,
  "y": 900,
  "native": false
}
```

### Bước 5: Đóng Profile Khi Xong

```http
POST http://127.0.0.1:58001/profiles/{profile_id}/close
```

Nếu profile không chạy, API có thể trả HTTP `409 profile_not_running`. App nên coi lỗi này là non-fatal khi cleanup.

## 4. Endpoint Cần Dùng Nhiều Nhất

### Profile

```text
POST   /profiles
GET    /profiles/{id}
PATCH  /profiles/{id}
DELETE /profiles/{id}
POST   /profiles/{id}/open
POST   /profiles/{id}/close
```

### Browser/Tab

```text
GET  /status
GET  /tabs
GET  /url
POST /navigate
POST /reload
POST /back
POST /forward
POST /stop
POST /tabs/new
POST /tabs/close
POST /tabs/activate
POST /window/bounds
```

### Wait

```text
POST /wait
```

Condition hỗ trợ:

```text
visible, hidden, exists, notexists, text, value, url, load, domready, enabled, disabled
```

### DOM

```text
POST /find
POST /findall
POST /element
POST /dom/interactive
POST /dom/snapshot
POST /source
```

### Input

```text
POST /click
POST /mouse/move
POST /scroll
POST /scrollto
POST /type
POST /sendkey
```

### Session/Data

```text
POST /cookie/get
POST /cookie/set
POST /cookie/clear
POST /storage/get
POST /storage/set
POST /storage/clear
```

### File/Network

```text
POST /upload
POST /screenshot
POST /download
POST /download/arm
POST /download/wait
POST /download/list
POST /download/move
POST /network/start
POST /network/get
POST /network/clear
POST /network/stop
```

## 5. Go Client Tối Thiểu

Ví dụ này dùng `net/http` chuẩn của Go, không cần dependency ngoài.

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

func postJSON(baseURL, path string, body any, timeout time.Duration) (map[string]any, error) {
	payload, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}

	client := &http.Client{Timeout: timeout}
	req, err := http.NewRequest("POST", baseURL+path, bytes.NewReader(payload))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json; charset=utf-8")

	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(raw))
	}

	var out map[string]any
	if err := json.Unmarshal(raw, &out); err != nil {
		return nil, err
	}
	return out, nil
}

func getJSON(baseURL, path string, timeout time.Duration) (map[string]any, error) {
	client := &http.Client{Timeout: timeout}
	resp, err := client.Get(baseURL + path)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(raw))
	}

	var out map[string]any
	if err := json.Unmarshal(raw, &out); err != nil {
		return nil, err
	}
	return out, nil
}
```

## 6. Go Flow Tạo Profile Và Mở Web

```go
managerURL := "http://127.0.0.1:58001"

created, err := postJSON(managerURL, "/profiles", map[string]any{
	"name":    "app-auto-profile",
	"browser": "chromium",
}, 15*time.Second)
if err != nil {
	return err
}

data := created["data"].(map[string]any)
profileID := data["id"].(string)

opened, err := postJSON(managerURL, "/profiles/"+profileID+"/open", map[string]any{}, 45*time.Second)
if err != nil {
	return err
}

openData := opened["data"].(map[string]any)
automationPort := int(openData["automation_port"].(float64))
automationURL := fmt.Sprintf("http://127.0.0.1:%d", automationPort)

// Retry GET /status trước khi thao tác.
for i := 0; i < 30; i++ {
	status, err := getJSON(automationURL, "/status", 3*time.Second)
	if err == nil && status["ok"] == true {
		break
	}
	time.Sleep(time.Second)
}

_, err = postJSON(automationURL, "/navigate", map[string]any{
	"tabId": 0,
	"url":   "https://www.24h.com.vn/",
}, 60*time.Second)
if err != nil {
	return err
}
```

## 7. Test Nhanh Bằng PowerShell

Tạo profile:

```powershell
$manager = "http://127.0.0.1:58001"
$profile = Invoke-RestMethod -Method Post -Uri "$manager/profiles" `
  -ContentType "application/json; charset=utf-8" `
  -Body '{"name":"ps-test","browser":"chromium"}'

$profileId = $profile.data.id
```

Mở profile:

```powershell
$opened = Invoke-RestMethod -Method Post -Uri "$manager/profiles/$profileId/open"
$port = $opened.data.automation_port
$auto = "http://127.0.0.1:$port"
```

Kiểm tra automation:

```powershell
Invoke-RestMethod -Method Get -Uri "$auto/status"
```

Mở web, click, scroll:

```powershell
Invoke-RestMethod -Method Post -Uri "$auto/navigate" `
  -ContentType "application/json; charset=utf-8" `
  -Body '{"tabId":0,"url":"https://www.24h.com.vn/"}'

Invoke-RestMethod -Method Post -Uri "$auto/wait" `
  -ContentType "application/json; charset=utf-8" `
  -Body '{"tabId":0,"condition":"domready","timeout":15000}'

Invoke-RestMethod -Method Post -Uri "$auto/click" `
  -ContentType "application/json; charset=utf-8" `
  -Body '{"tabId":0,"xpath":"(//a[@href])[4]","native":false}'

Invoke-RestMethod -Method Post -Uri "$auto/scroll" `
  -ContentType "application/json; charset=utf-8" `
  -Body '{"tabId":0,"y":900,"native":false}'
```

## 8. Quy Ước XPath

API dùng XPath, không dùng CSS selector.

Ví dụ:

```text
//button
//input[@name='email']
//button[normalize-space()='Login']
(//a[@href])[4]
//*[@data-testid='submit']
```

Iframe dùng `>>`:

```text
//iframe[@id='login-frame'] >> //input[@name='email']
//iframe[1] >> //iframe[1] >> //button
```

## 9. Native Mode

`native:false` là lựa chọn mặc định cho app automation:

```json
{
  "native": false
}
```

Ưu điểm:

- Chạy được ở background.
- Không cần browser foreground.
- Có thể chạy nhiều profile song song.
- Không di chuyển chuột thật của Windows.

Dùng `native:true` khi cần input giống người dùng thật hơn, nhưng phải chấp nhận browser foreground và không phù hợp chạy song song nhiều profile.

## 10. Xử Lý Lỗi Bắt Buộc

App nên xử lý các lỗi này rõ ràng:

```text
Connection refused 58001
  -> Profile Manager chưa chạy.

POST /profiles/{id}/open timeout
  -> Browser mở chậm, tăng timeout hoặc retry.

GET /status chưa ok
  -> Đợi thêm, không gọi /navigate quá sớm.

404 element not found
  -> XPath sai hoặc element chưa render, dùng /wait trước.

409 profile_not_running khi close
  -> Cleanup có thể bỏ qua nếu profile đã đóng.

HTTP 4xx/5xx từ automation
  -> Log raw response body để debug.
```

## 11. Checklist Tích Hợp Vào App

- Tạo cấu hình `CHROMIUM_PROFILE_MANAGER_URL`.
- Có hàm HTTP client dùng timeout.
- Có hàm `createProfile`.
- Có hàm `openProfile` trả `automation_url`.
- Có hàm `waitAutomationReady`.
- Có hàm `postAutomation(path, body)`.
- Luôn gọi `/wait` trước khi click/type element động.
- Log đủ `profile_id`, `automation_port`, endpoint, request body, response/error.
- Cleanup bằng `/profiles/{id}/close` khi task xong nếu app tự tạo profile.
- Không expose `58001` hoặc `automation_port` ra network ngoài máy.

## 12. Lệnh Test File Go Hiện Có

Repo này đang có file Go mẫu:

```text
tools/open_24h_chromium.go
```

Build:

```powershell
go build -o .\tools\open_24h_chromium.exe .\tools\open_24h_chromium.go
```

Chạy tự tạo profile:

```powershell
.\tools\open_24h_chromium.exe -close-on-finish
```

Chạy với automation port có sẵn:

```powershell
.\tools\open_24h_chromium.exe -automation-port 41917
```
