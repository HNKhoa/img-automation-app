const state = {
  images: [],
  genericImages: [],
  outputText: "",
  currentEnvelope: null,
  cfRetryCount: 0,
  generationModes: [],
  modeIndex: {},
  styleTouched: false,
};

const $ = (id) => document.getElementById(id);
const tr = (key, fallback, params) => window.I18n?.t(key, fallback, params) ?? fallback ?? key;

const roleUploads = {
  model: { input: $("modelUpload"), thumbs: $("modelThumbs") },
  outfit: { input: $("outfitUpload"), thumbs: $("outfitThumbs") },
  background: { input: $("backgroundUpload"), thumbs: $("backgroundThumbs") },
};

const modeDom = {
  outfitOnlySection: $("outfitOnlySection"),
  genericReferenceUpload: $("genericReferenceUpload"),
  storyboardSceneHint: $("storyboardSceneHint"),
  targetField: $("targetField"),
  handoffBtn: $("handoffBtn"),
  modeHelper: $("modeHelper"),
  modePurpose: document.querySelector("#modeHelper .mode-purpose"),
  modeUsage: document.querySelector("#modeHelper .mode-usage"),
  genericRefHint: $("genericRefHint"),
  outputSections: $("outputSections"),
};

function currentModeSpec() {
  return state.modeIndex[$("modeSelect").value] || state.generationModes[0] || { id: "outfit-swap-json", kind: "outfit", output_type: "text", allow_images: true };
}

function localizedMode(mode) {
  return { ...mode, label: tr(`mode.${mode.id}.label`, mode.label) };
}

function renderModeOptions(selectedValue) {
  renderSelectOptions("modeSelect", state.generationModes.map(localizedMode), {
    valueKey: "id",
    labelKey: "label",
    selectedValue: selectedValue || $("modeSelect").value || "outfit-swap-json",
  });
}

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

function showWarnings(warnings) {
  if (!warnings?.length) return;
  const banner = $("messageBanner");
  banner.innerHTML = `<ul>${warnings.map((warning) => `<li>${escapeHtml(warning.code)}: ${escapeHtml(warning.message)}</li>`).join("")}</ul>`;
  banner.dataset.tone = "warn";
  banner.hidden = false;
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
      setStatus(tr("status.relay_invalid", "Relay URL kh?ng h?p l?"), "error");
      return;
    }
    localStorage.setItem("custom_relay_url", value);
    setStatus(tr("status.relay_saved", "?? l?u Custom Relay"), "ok");
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
      <div class="empty-icon">?</div>
      <strong>${escapeHtml(tr("hint.empty_title", "T?i ?nh v? b?m T?o prompt"))}</strong>
      <p>${escapeHtml(tr("hint.empty_body", "K?t qu? s? hi?n th? t?i ??y theo t?ng ph?n ?? d? ki?m tra v? copy."))}</p>
    `;
    container.appendChild(empty);
    return;
  }

  for (const section of parsePromptSections(state.outputText)) {
    appendPromptSection(container, section.title, section.body);
  }
}

function appendPromptSection(container, titleText, bodyText) {
  const details = document.createElement("details");
  details.className = "prompt-section";
  details.open = true;

  const summary = document.createElement("summary");
  const title = document.createElement("span");
  title.textContent = titleText;
  const copy = document.createElement("button");
  copy.type = "button";
  copy.className = "section-copy";
  copy.textContent = "Copy";
  copy.addEventListener("click", async (event) => {
    event.preventDefault();
    event.stopPropagation();
    await navigator.clipboard.writeText(bodyText);
    setStatus(tr("status.section_copied", "?? copy section"), "ok");
  });
  summary.append(title, copy);

  const body = document.createElement("pre");
  body.textContent = bodyText;
  details.append(summary, body);
  container.appendChild(details);
}

function renderGenericEnvelope(envelope, spec) {
  const output = envelope.result?.output || "";
  $("outputBox").textContent = output;
  $("outputSections").innerHTML = "";
  window.GenerationModes.renderResult(envelope, spec, modeDom, (text) => {
    for (const section of parsePromptSections(text)) {
      appendPromptSection($("outputSections"), section.title, section.body);
    }
  });
}

function setOutput(text) {
  state.outputText = text || "";
  state.currentEnvelope = null;
  updateOutputActions();
  renderOutput();
}

async function bootstrap(retries = 5) {
  await window.I18n?.bootstrap?.();
  if ($("languageSelect")) $("languageSelect").value = window.I18n?.getLang?.() || "vi";
  if (!window.pywebview?.api) {
    if (retries > 0) {
      window.setTimeout(() => bootstrap(retries - 1), 200);
      return;
    }
    setStatus(tr("status.pywebview_unavailable", "pywebview API ch?a s?n s?ng"), "error");
    return;
  }

  const data = await window.pywebview.api.get_bootstrap();
  if (data.config?.has_api_key) {
    $("apiKeyInput").placeholder = tr("placeholder.api_from_env", "?ang d?ng sk key t? .env");
  }

  state.generationModes = data.generation_modes || [];
  state.modeIndex = Object.fromEntries(state.generationModes.map((mode) => [mode.id, mode]));
  const storedMode = localStorage.getItem("lastModeId");
  const migratedMode = storedMode === "storyboard-3x3" || storedMode === "advanced-storyboard" ? "storyboard-unified" : storedMode;
  if (migratedMode && migratedMode !== storedMode) {
    localStorage.setItem("lastModeId", migratedMode);
  }
  renderModeOptions(migratedMode || "outfit-swap-json");

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
  renderSelectOptions("styleSelect", data.style_options || [], { selectedValue: currentModeSpec().kind === "generic" ? "None" : "High-end fashion editorial" });
  applyCurrentModeUI();
}

function applyCurrentModeUI(options = {}) {
  const spec = currentModeSpec();
  window.GenerationModes.applyModeUI(spec, modeDom);
  if (!state.styleTouched) {
    $("styleSelect").value = spec.kind === "generic" ? "None" : "High-end fashion editorial";
  }
  updateStoryboardHint();
  if (options.userChanged) {
    $("modeHelper").hidden = false;
    $("modeHelpToggle").setAttribute("aria-expanded", "true");
    const hiddenOutfitCount = state.images.length;
    const hiddenGenericCount = state.genericImages.length;
    if (spec.kind === "generic" && hiddenOutfitCount) {
      showMessage(tr("message.hidden_outfit", "C?n {count} ?nh outfit ?ang ?n; ch?ng s? kh?ng ???c g?i cho mode hi?n t?i.", { count: hiddenOutfitCount }), "info");
    } else if (spec.kind === "outfit" && hiddenGenericCount) {
      showMessage(tr("message.hidden_generic", "C?n {count} ?nh reference generic ?ang ?n; ch?ng s? kh?ng ???c g?i cho outfit mode.", { count: hiddenGenericCount }), "info");
    }
  }
  setOutput("");
}

function updateStoryboardHint() {
  const hint = $("storyboardSceneHint");
  const spec = currentModeSpec();
  if (!hint) return;
  if (spec.id !== "storyboard-unified") {
    hint.hidden = true;
    return;
  }
  const count = window.GenerationModes.parseSceneCount($("userRequestInput").value);
  hint.textContent = tr("hint.storyboard", "G?i ?: s? t?o {count} c?nh (m?c ??nh 9, gi?i h?n 3-12).", { count });
  hint.hidden = false;
}

async function handleUpload(role, files) {
  showMessage("");
  setStatus(tr("status.image_compressing", "?ang n?n ?nh..."));
  for (const file of Array.from(files)) {
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      showMessage(tr("error.unsupported_file", "B? qua file kh?ng h? tr?: {name}", { name: file.name }), "error");
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
  setStatus(tr("status.images_ready", "?nh ?? s?n s?ng"), "ok");
}

async function handleGenericUpload(files) {
  showMessage("");
  if (state.genericImages.length + files.length > 5) {
    showMessage(tr("error.max_generic_images", "Generic mode ch? nh?n t?i ?a 5 ?nh tham chi?u."), "error");
    setStatus(tr("status.too_many_images", "Qu? 5 ?nh"), "error");
    return;
  }
  setStatus(tr("status.image_compressing", "?ang n?n ?nh..."));
  for (const file of Array.from(files)) {
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      showMessage(tr("error.unsupported_file", "B? qua file kh?ng h? tr?: {name}", { name: file.name }), "error");
      continue;
    }
    const dataUrl = await compressImage(file);
    state.genericImages.push({
      id: crypto.randomUUID(),
      role: "reference",
      name: file.name,
      type: "image/jpeg",
      dataUrl,
      payloadSize: new Blob([dataUrl]).size,
    });
  }
  renderGenericThumbs();
  setStatus(tr("status.reference_ready", "?nh tham chi?u ?? s?n s?ng"), "ok");
}

function clearRole(role) {
  state.images = state.images.filter((item) => item.role !== role);
  renderThumbs();
  setStatus(`Da xoa ${role}`, "ok");
}

function renderThumbs() {
  for (const [role, refs] of Object.entries(roleUploads)) {
    refs.thumbs.innerHTML = "";
    for (const image of state.images.filter((item) => item.role === role)) {
      refs.thumbs.appendChild(createThumb(image, () => {
        state.images = state.images.filter((item) => item.id !== image.id);
        renderThumbs();
      }));
    }
  }
}

function renderGenericThumbs() {
  const container = $("genericRefThumbs");
  container.innerHTML = "";
  for (const image of state.genericImages) {
    container.appendChild(createThumb(image, () => {
      state.genericImages = state.genericImages.filter((item) => item.id !== image.id);
      renderGenericThumbs();
    }));
  }
}

function createThumb(image, onRemove) {
  const thumb = document.createElement("div");
  thumb.className = "thumb";
  thumb.innerHTML = `<img src="${image.dataUrl}" alt="${escapeHtml(image.name)}"><button type="button" title="Remove" aria-label="Xoa anh">×</button>`;
  thumb.querySelector("button").addEventListener("click", onRemove);
  return thumb;
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
  const spec = currentModeSpec();
  const customRelay = (localStorage.getItem("custom_relay_url") || "").trim();
  if (spec.kind === "generic") {
    return window.GenerationModes.buildGenericPayload({
      modeSpec: spec,
      model: $("modelSelect").value,
      userInput: $("userRequestInput").value.trim(),
      style: $("styleSelect").value,
      aspectRatio: $("aspectSelect").value,
      resolution: $("resolutionSelect").value,
      quality: $("qualitySelect").value,
      apiKey: $("apiKeyInput").value.trim(),
      images: state.genericImages,
      customRelay,
    });
  }
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
  if (customRelay) payload.custom_relay_endpoint = customRelay;
  return payload;
}

async function generatePrompt() {
  const spec = currentModeSpec();
  if (spec.kind === "outfit") {
    const roles = new Set(state.images.map((item) => item.role));
    if (!roles.has("model") || !roles.has("outfit")) {
      setStatus(tr("status.missing_outfit_images", "Thi?u A.1 ho?c A.2"), "error");
      showMessage(tr("error.missing_outfit_images", "C?n upload t?i thi?u A.1 Model identity v? A.2 Outfit source."), "error");
      return;
    }
  }

  if (spec.kind === "generic" && spec.allow_images && state.genericImages.length > 5) {
    setStatus(tr("status.too_many_images", "Qu? 5 ?nh"), "error");
    showMessage(tr("error.max_generic_images", "Generic mode ch? nh?n t?i ?a 5 ?nh tham chi?u."), "error");
    return;
  }

  showMessage("");
  setStatus(tr("status.generating", "?ang g?i API..."));
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
    state.currentEnvelope = response;
    state.outputText = response.result.output || "";
    updateOutputActions();
    setStatus(tr("status.done", "Ho?n t?t"), "ok");
    if (response.kind === "generic") {
      renderGenericEnvelope(response, spec);
    } else {
      renderOutput();
    }
    showWarnings(response.warnings);
  } catch (err) {
    setStatus(tr("status.generate_error", "L?i t?o prompt"), "error");
    showMessage(err?.message || String(err), "error");
  } finally {
    setGenerateDisabled(false);
  }
}

function setGenerateDisabled(disabled) {
  $("heroGenerateBtn").disabled = disabled;
  $("heroGenerateBtn").classList.toggle("is-loading", disabled);
  $("heroGenerateBtn").textContent = disabled ? tr("btn.generating", "?ang t?o prompt") : tr("btn.generate", "T?o prompt");
}

function retryCloudflareGenerate(delayMs) {
  if (state.cfRetryCount >= 3) {
    setStatus("Cloudflare retry limit", "error");
    return;
  }
  state.cfRetryCount += 1;
  setStatus(`Thu lai Cloudflare ${state.cfRetryCount}/3`);
  window.setTimeout(() => generatePrompt(), delayMs);
}

function formatError(error) {
  if (!error) return "Unknown error.";
  const translate = window.I18n?.t ? window.I18n.t.bind(window.I18n) : (_key, fallback) => fallback;
  if (error.code === "CLOUDFLARE_ACCESS_DENIED") {
    return translate("message.cf_error", "Tất cả endpoint Pollinations đang bị chặn (đã thử nhiều profiles và nhiều endpoints). App sẽ tự thử lại. Nếu vẫn lỗi, dán Custom Relay URL trong Cài đặt.");
  }
  const raw = error.raw_output ? String(error.raw_output).slice(0, 1200) : "";
  const detail = raw ? ` Raw output: ${raw}` : "";
  return `${error.code || "ERROR"}: ${error.message || "No message."}${detail}`;
}

async function testApi() {
  showMessage("");
  setStatus(tr("status.api_testing", "?ang ki?m tra API..."));
  const response = await window.pywebview.api.test_api_key({ api_key: $("apiKeyInput").value.trim() });
  if (response.ok) {
    setStatus(tr("status.api_ok", "API OK"), "ok");
  } else {
    setStatus(response.error?.code || "API error", "error");
    showMessage(formatError(response.error), "error");
  }
}

async function copyOutput() {
  const text = state.outputText.trim();
  if (!text) return;
  await navigator.clipboard.writeText(text);
  setStatus(tr("status.copied", "?? copy"), "ok");
}

function downloadOutput() {
  const text = state.outputText.trim();
  if (!text) return;
  const spec = currentModeSpec();
  const isJson = spec.output_type === "json";
  const blob = new Blob([text], { type: isJson ? "application/json;charset=utf-8" : "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${spec.id || "prompt"}.${isJson ? "json" : "txt"}`;
  link.click();
  URL.revokeObjectURL(url);
}

async function handoff() {
  const promptText = state.outputText.trim();
  if (!promptText) return;
  const response = await window.pywebview.api.open_chatgpt({
    profile_id: null,
    prompt_text: promptText,
  });
  if (response.ok) {
    setStatus(tr("status.chatgpt_opened", "?? m? ChatGPT"), "ok");
    showMessage(response.prompt_file ? tr("message.saved_handoff", "?? l?u handoff: {file}", { file: response.prompt_file }) : tr("message.chatgpt_opened", "?? m? ChatGPT."), "ok");
  } else {
    setStatus(tr("status.chrome_error", "Kh?ng m? ???c Chrome"), "error");
    showMessage(response.error || tr("error.open_chatgpt", "Kh?ng m? ???c ChatGPT."), "error");
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

function updateOutputActions() {
  const hasOutput = Boolean(state.outputText.trim());
  $("handoffBtn").disabled = !hasOutput;
  $("copyBtn").disabled = !hasOutput;
  $("downloadBtn").disabled = !hasOutput;
}

for (const [role, refs] of Object.entries(roleUploads)) {
  refs.input.addEventListener("change", (event) => handleUpload(role, event.target.files));
}

$("genericRefInput").addEventListener("change", (event) => handleGenericUpload(event.target.files));
$("clearGenericRefBtn").addEventListener("click", () => {
  state.genericImages = [];
  renderGenericThumbs();
});
$("modeSelect").addEventListener("change", () => {
  localStorage.setItem("lastModeId", $("modeSelect").value);
  setStatus(`Mode: ${localizedMode(currentModeSpec()).label} ${tr("status.ready", "s?n s?ng").toLowerCase()}`, "ok");
  applyCurrentModeUI({ userChanged: true });
});
$("styleSelect").addEventListener("change", () => {
  state.styleTouched = true;
});
$("userRequestInput").addEventListener("input", updateStoryboardHint);
$("modeHelpToggle").addEventListener("click", () => {
  $("modeHelper").hidden = !$("modeHelper").hidden;
  $("modeHelpToggle").setAttribute("aria-expanded", String(!$("modeHelper").hidden));
});
$("heroGenerateBtn").addEventListener("click", generatePrompt);
$("settingsBtn").addEventListener("click", () => {
  $("settingsModal").hidden = false;
});
$("closeSettingsBtn").addEventListener("click", () => {
  $("settingsModal").hidden = true;
});
$("settingsModal").addEventListener("click", (event) => {
  if (event.target === $("settingsModal")) {
    $("settingsModal").hidden = true;
  }
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !$("settingsModal").hidden) {
    $("settingsModal").hidden = true;
  }
});
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
  $("toggleKeyBtn").textContent = input.type === "password" ? tr("settings.show_key", "Hi?n key") : tr("settings.hide_key", "?n key");
});

document.addEventListener("i18n:changed", () => {
  renderModeOptions($("modeSelect").value);
  setGenerateDisabled($("heroGenerateBtn").disabled);
  renderOutput();
});
$("languageSelect").addEventListener("change", async () => {
  await window.I18n.setLang($("languageSelect").value);
  $("languageSelect").value = window.I18n.getLang();
});

window.addEventListener("pywebviewready", bootstrap);
window.I18n?.bootstrap?.().then(() => {
  $("languageSelect").value = window.I18n.getLang();
  setStatus(tr("status.ready", "S?n s?ng"), "neutral");
  renderOutput();
});
renderOutput();
updateOutputActions();
