const state = {
  images: [],
  outputText: "",
  cfRetryCount: 0,
};

const $ = (id) => document.getElementById(id);

function renderSelectOptions(selectId, items, options = {}) {
  const element = $(selectId);
  if (!element || !Array.isArray(items)) return;

  const valueKey = options.valueKey || "value";
  const labelKey = options.labelKey || "label";
  const selectedValue = options.selectedValue;

  element.innerHTML = items
    .map((item) => {
      const value = typeof item === "string" ? item : item?.[valueKey] ?? "";
      const label = typeof item === "string" ? item : item?.[labelKey] ?? value;
      return `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`;
    })
    .join("");

  if (selectedValue && items.some((item) => (typeof item === "string" ? item === selectedValue : item?.[valueKey] === selectedValue))) {
    element.value = selectedValue;
  }
}

const roleUploads = {
  model: { input: $("modelUpload"), thumbs: $("modelThumbs") },
  outfit: { input: $("outfitUpload"), thumbs: $("outfitThumbs") },
  background: { input: $("backgroundUpload"), thumbs: $("backgroundThumbs") },
};

function setStatus(text, tone = "neutral") {
  const pill = $("statusPill");
  pill.textContent = text;
  pill.dataset.tone = tone;
}

function showMessage(text, tone = "neutral") {
  const banner = $("messageBanner");
  banner.textContent = text || "";
  banner.dataset.tone = tone;
  banner.hidden = !text;
}

function showCloudflareMessage(error) {
  const banner = $("messageBanner");
  const template = $("cfBannerTemplate");
  banner.innerHTML = "";
  banner.dataset.tone = "error";
  banner.hidden = false;
  const body = template.content.cloneNode(true);
  const paragraph = body.querySelector("p");
  paragraph.textContent = formatError(error);
  const input = body.querySelector('[data-action="cf-relay-input"]');
  input.value = localStorage.getItem("custom_relay_url") || "";
  body.querySelector('[data-action="cf-retry"]').addEventListener("click", () => retryCloudflareGenerate(0));
  body.querySelector('[data-action="cf-set-relay"]').addEventListener("click", () => {
    const value = input.value.trim();
    if (!value.startsWith("http://") && !value.startsWith("https://")) {
      setStatus("Relay URL không hợp lệ", "error");
      return;
    }
    localStorage.setItem("custom_relay_url", value);
    setStatus("Đã lưu Custom Relay", "ok");
  });
  body.querySelector('[data-action="cf-dismiss"]').addEventListener("click", () => showMessage(""));
  banner.appendChild(body);
}

function parsePromptSections(text) {
  const labels = ["MAIN PROMPT", "NEGATIVE PROMPT", "REFERENCE BINDING INSTRUCTIONS"];
  const pattern = /(MAIN PROMPT|NEGATIVE PROMPT|REFERENCE BINDING INSTRUCTIONS)\s*:/gi;
  const matches = [...text.matchAll(pattern)];
  if (!matches.length) return [{ title: "Prompt", body: text.trim() }];

  return matches.map((match, index) => {
    const start = match.index + match[0].length;
    const end = matches[index + 1]?.index ?? text.length;
    const rawTitle = labels.find((label) => label.toLowerCase() === match[1].toLowerCase()) || match[1];
    return {
      title: rawTitle,
      body: text.slice(start, end).trim(),
    };
  }).filter((section) => section.body);
}

function renderOutput() {
  const container = $("outputSections");
  container.innerHTML = "";
  $("outputBox").textContent = state.outputText;

  if (!state.outputText.trim()) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.innerHTML = `
      <div class="empty-icon">↗</div>
      <strong>Tải ảnh và bấm Tạo prompt</strong>
      <p>Kết quả sẽ hiển thị tại đây theo từng phần để dễ kiểm tra và copy.</p>
    `;
    container.appendChild(empty);
    return;
  }

  for (const section of parsePromptSections(state.outputText)) {
    const details = document.createElement("details");
    details.className = "prompt-section";
    details.open = true;

    const summary = document.createElement("summary");
    const title = document.createElement("span");
    title.textContent = section.title;
    const copy = document.createElement("button");
    copy.type = "button";
    copy.className = "section-copy";
    copy.textContent = "Copy";
    copy.addEventListener("click", async (event) => {
      event.preventDefault();
      event.stopPropagation();
      await navigator.clipboard.writeText(section.body);
      setStatus("Đã copy section", "ok");
    });
    summary.append(title, copy);

    const body = document.createElement("pre");
    body.textContent = section.body;
    details.append(summary, body);
    container.appendChild(details);
  }
}

function setOutput(text) {
  state.outputText = text || "";
  renderOutput();
}

async function bootstrap() {
  if (!window.pywebview?.api) {
    setStatus("pywebview API chưa sẵn sàng", "error");
    return;
  }

  const data = await window.pywebview.api.get_bootstrap();
  if (data.config?.has_api_key) {
    $("apiKeyInput").placeholder = "Đang dùng sk key từ .env";
  }

  renderSelectOptions("modelSelect", data.model_options || [], {
    valueKey: "value",
    labelKey: "label",
    selectedValue: data.config?.default_model,
  });
  renderSelectOptions("targetSelect", data.target_options || [], {
    valueKey: "value",
    labelKey: "label",
    selectedValue: "chatgpt_img",
  });
  renderSelectOptions("qualitySelect", data.quality_profiles || [], {
    valueKey: "value",
    labelKey: "label",
    selectedValue: "high",
  });
  renderSelectOptions("aspectSelect", data.aspect_ratio_options || [], { selectedValue: "1:1" });
  renderSelectOptions("resolutionSelect", data.resolution_options || [], { selectedValue: "2K" });
  renderSelectOptions("styleSelect", data.style_options || [], { selectedValue: "High-end fashion editorial" });
}

async function handleUpload(role, files) {
  showMessage("");
  setStatus("Đang nén ảnh...");
  for (const file of Array.from(files)) {
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      showMessage(`Bỏ qua file không hỗ trợ: ${file.name}`, "error");
      continue;
    }
    const dataUrl = await compressImage(file);
    state.images.push({
      id: crypto.randomUUID(),
      role,
      name: file.name,
      type: "image/jpeg",
      dataUrl,
      payloadSize: new Blob([dataUrl]).size,
    });
  }
  renderThumbs();
  setStatus("Ảnh đã sẵn sàng", "ok");
}

function clearRole(role) {
  state.images = state.images.filter((item) => item.role !== role);
  renderThumbs();
  setStatus(`Đã xóa ${role}`, "ok");
}

function renderThumbs() {
  for (const [role, refs] of Object.entries(roleUploads)) {
    refs.thumbs.innerHTML = "";
    for (const image of state.images.filter((item) => item.role === role)) {
      const thumb = document.createElement("div");
      thumb.className = "thumb";
      thumb.innerHTML = `<img src="${image.dataUrl}" alt="${escapeHtml(image.name)}"><button type="button" title="Remove" aria-label="Xóa ảnh">×</button>`;
      thumb.querySelector("button").addEventListener("click", () => {
        state.images = state.images.filter((item) => item.id !== image.id);
        renderThumbs();
      });
      refs.thumbs.appendChild(thumb);
    }
  }
}

function compressImage(file) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const reader = new FileReader();
    reader.onload = () => {
      image.onload = () => {
        const maxSide = 1280;
        const scale = Math.min(1, maxSide / Math.max(image.width, image.height));
        const canvas = document.createElement("canvas");
        canvas.width = Math.max(1, Math.round(image.width * scale));
        canvas.height = Math.max(1, Math.round(image.height * scale));
        const ctx = canvas.getContext("2d", { alpha: false });
        ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL("image/jpeg", 0.78));
      };
      image.onerror = () => reject(new Error(`Cannot read image: ${file.name}`));
      image.src = reader.result;
    };
    reader.onerror = () => reject(new Error(`Cannot read file: ${file.name}`));
    reader.readAsDataURL(file);
  });
}

function buildPayload() {
  const payload = {
    api_key: $("apiKeyInput").value.trim(),
    mode: "outfit-swap-json",
    model: $("modelSelect").value,
    target_model_rule: $("targetSelect").value,
    style: $("styleSelect").value,
    aspect_ratio: $("aspectSelect").value,
    resolution: $("resolutionSelect").value,
    quality: $("qualitySelect").value,
    user_request: $("userRequestInput").value.trim(),
    images: state.images,
  };
  const customRelay = (localStorage.getItem("custom_relay_url") || "").trim();
  if (customRelay) {
    payload.custom_relay_endpoint = customRelay;
  }
  return payload;
}

async function generatePrompt() {
  const roles = new Set(state.images.map((item) => item.role));
  if (!roles.has("model") || !roles.has("outfit")) {
    setStatus("Thiếu A.1 hoặc A.2", "error");
    showMessage("Cần upload tối thiểu A.1 Model identity và A.2 Outfit source.", "error");
    return;
  }

  showMessage("");
  setStatus("Đang gọi API...");
  setGenerateDisabled(true);
  try {
    const response = await window.pywebview.api.generate_prompt(buildPayload());
    if (!response.ok) {
      setStatus(response.error?.code || "API error", "error");
      if (response.error?.code === "CLOUDFLARE_ACCESS_DENIED") {
        showCloudflareMessage(response.error);
        retryCloudflareGenerate(5000);
      } else {
        showMessage(formatError(response.error), "error");
      }
      return;
    }
    state.cfRetryCount = 0;
    setStatus("Hoàn tất", "ok");
    setOutput(response.result.output);
  } finally {
    setGenerateDisabled(false);
  }
}

function setGenerateDisabled(disabled) {
  $("heroGenerateBtn").disabled = disabled;
  $("topGenerateBtn").disabled = disabled;
}

function retryCloudflareGenerate(delayMs) {
  if (state.cfRetryCount >= 3) {
    setStatus("Cloudflare retry limit", "error");
    return;
  }
  state.cfRetryCount += 1;
  setStatus(`Thử lại Cloudflare ${state.cfRetryCount}/3`);
  window.setTimeout(() => generatePrompt(), delayMs);
}

function formatError(error) {
  if (!error) return "Unknown error.";
  if (error.code === "CLOUDFLARE_ACCESS_DENIED") {
    return [
      "Tất cả endpoint Pollinations đang bị chặn (đã thử nhiều profiles và nhiều endpoints).",
      "App sẽ tự thử lại.",
      "Nếu vẫn lỗi, dán Custom Relay URL trong API Settings.",
    ].join(" ");
  }
  const raw = error.raw_output ? String(error.raw_output).slice(0, 240) : "";
  const detail = raw ? ` Raw output: ${raw}` : "";
  return `${error.code || "ERROR"}: ${error.message || "No message."}${detail}`;
}

async function testApi() {
  showMessage("");
  setStatus("Đang test API...");
  const response = await window.pywebview.api.test_api_key({ api_key: $("apiKeyInput").value.trim() });
  if (response.ok) {
    setStatus("API OK", "ok");
  } else {
    setStatus(response.error?.code || "API error", "error");
    showMessage(formatError(response.error), "error");
  }
}

async function copyOutput() {
  const text = state.outputText.trim();
  if (!text) return;
  await navigator.clipboard.writeText(text);
  setStatus("Đã copy", "ok");
}

function downloadOutput() {
  const text = state.outputText.trim();
  if (!text) return;
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "outfit_swap_prompt.txt";
  link.click();
  URL.revokeObjectURL(url);
}

async function handoff() {
  const promptText = state.outputText.trim();
  const response = await window.pywebview.api.open_chatgpt({
    profile_id: null,
    prompt_text: promptText,
  });
  if (response.ok) {
    setStatus("Đã mở ChatGPT", "ok");
    showMessage(response.prompt_file ? `Đã lưu handoff: ${response.prompt_file}` : "Đã mở ChatGPT.", "ok");
  } else {
    setStatus("Không mở được Chrome", "error");
    showMessage(response.error || "Không mở được ChatGPT.", "error");
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[char]);
}

for (const [role, refs] of Object.entries(roleUploads)) {
  refs.input.addEventListener("change", (event) => handleUpload(role, event.target.files));
}

$("heroGenerateBtn").addEventListener("click", generatePrompt);
$("topGenerateBtn").addEventListener("click", generatePrompt);
$("testApiBtn").addEventListener("click", testApi);
$("copyBtn").addEventListener("click", copyOutput);
$("downloadBtn").addEventListener("click", downloadOutput);
$("handoffBtn").addEventListener("click", handoff);
$("clearModelBtn").addEventListener("click", () => clearRole("model"));
$("clearOutfitBtn").addEventListener("click", () => clearRole("outfit"));
$("clearBackgroundBtn").addEventListener("click", () => clearRole("background"));
$("clearOutputBtn").addEventListener("click", () => {
  showMessage("");
  setOutput("");
});
$("toggleKeyBtn").addEventListener("click", () => {
  const input = $("apiKeyInput");
  input.type = input.type === "password" ? "text" : "password";
  $("toggleKeyBtn").textContent = input.type === "password" ? "Hiện key" : "Ẩn key";
});

window.addEventListener("pywebviewready", bootstrap);
renderOutput();
