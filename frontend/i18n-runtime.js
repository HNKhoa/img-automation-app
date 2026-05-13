(function () {
  const embedded = {
  "vi": {
    "app.title": "Img automation App",
    "app.subtitle": "Không gian tạo prompt thay trang phục",
    "settings.title": "Cài đặt",
    "settings.subtitle": "API key, ngôn ngữ và tuỳ chọn kết nối.",
    "settings.close": "Đóng cài đặt",
    "settings.language": "Ngôn ngữ",
    "settings.language.vi": "Tiếng Việt",
    "settings.language.en": "English",
    "settings.api_key": "Secret API key",
    "settings.show_key": "Hiện key",
    "settings.hide_key": "Ẩn key",
    "status.ready": "Sẵn sàng",
    "status.pywebview_unavailable": "pywebview API chưa sẵn sàng",
    "status.image_compressing": "Đang nén ảnh...",
    "status.images_ready": "Ảnh đã sẵn sàng",
    "status.reference_ready": "Ảnh tham chiếu đã sẵn sàng",
    "status.generating": "Đang gọi API...",
    "status.done": "Hoàn tất",
    "status.generate_error": "Lỗi tạo prompt",
    "status.api_testing": "Đang kiểm tra API...",
    "status.api_ok": "API OK",
    "status.copied": "Đã copy",
    "status.section_copied": "Đã copy section",
    "status.chatgpt_opened": "Đã mở ChatGPT",
    "status.chrome_error": "Không mở được Chrome",
    "status.too_many_images": "Quá 5 ảnh",
    "status.missing_outfit_images": "Thiếu A.1 hoặc A.2",
    "status.relay_invalid": "Relay URL không hợp lệ",
    "status.relay_saved": "Đã lưu Custom Relay",
    "btn.test_api": "Test API",
    "btn.settings": "Cài đặt",
    "btn.generate": "Tạo prompt",
    "btn.generating": "Đang tạo prompt",
    "btn.copy": "Copy",
    "btn.download": "Tải TXT",
    "btn.open_chatgpt": "Mở ChatGPT",
    "btn.close": "Đóng",
    "btn.retry": "Thử lại",
    "btn.set_custom_relay": "Đặt Custom Relay",
    "label.mode": "Chế độ tạo prompt",
    "label.model": "Model",
    "label.target": "Đích",
    "label.style": "Phong cách",
    "label.aspect": "Tỷ lệ",
    "label.quality": "Chất lượng",
    "label.resolution": "Độ phân giải",
    "label.extra_notes": "Nội dung bổ sung",
    "label.reference_images": "Ảnh tham chiếu",
    "label.config": "Cấu hình",
    "label.output": "Prompt Preview",
    "helper.mode": "Trợ giúp mode",
    "hint.config": "Model và thông số render.",
    "hint.extra_notes": "Mood, camera, lighting, background hoặc ràng buộc thêm.",
    "hint.output": "Kết quả API trả về để copy sang ChatGPT Image.",
    "hint.empty_title": "Tải ảnh và bấm Tạo prompt",
    "hint.empty_body": "Kết quả sẽ hiển thị tại đây theo từng phần để dễ kiểm tra và copy.",
    "hint.storyboard": "Gợi ý: sẽ tạo {count} cảnh (mặc định 9, giới hạn 3-12).",
    "placeholder.loading": "Đang tải...",
    "placeholder.api_from_env": "Đang dùng sk key từ .env",
    "placeholder.extra_notes": "Ví dụ: giữ mặt mẫu, bám sát outfit gốc, ánh sáng studio mềm, nền tối giản.",
    "error.unsupported_file": "Bỏ qua file không hỗ trợ: {name}",
    "error.max_generic_images": "Generic mode chỉ nhận tối đa 5 ảnh tham chiếu.",
    "error.missing_outfit_images": "Cần upload tối thiểu A.1 Model identity và A.2 Outfit source.",
    "error.open_chatgpt": "Không mở được ChatGPT.",
    "message.hidden_outfit": "Còn {count} ảnh outfit đang ẩn; chúng sẽ không được gửi cho mode hiện tại.",
    "message.hidden_generic": "Còn {count} ảnh reference generic đang ẩn; chúng sẽ không được gửi cho outfit mode.",
    "message.saved_handoff": "Đã lưu handoff: {file}",
    "message.chatgpt_opened": "Đã mở ChatGPT.",
    "message.cf_error": "Tất cả endpoint Pollinations đang bị chặn (đã thử nhiều profiles và nhiều endpoints). App sẽ tự thử lại. Nếu vẫn lỗi, dán Custom Relay URL trong Cài đặt.",
    "message.cf_body": "Tất cả endpoint Pollinations đang bị chặn. App sẽ tự thử lại, hoặc bạn có thể dán URL relay riêng.",
    "message.cf_meta": "Custom Relay sẽ được lưu cục bộ trên máy này.",
    "mode.outfit-swap-json.label": "Thay trang phục",
    "mode.character-json.label": "JSON nhân vật",
    "mode.product-detail-shots.label": "Shot chi tiết sản phẩm",
    "mode.storyboard-unified.label": "Storyboard",
    "mode.reference-pack.label": "Bộ ảnh tham chiếu",
    "mode.image-to-video.label": "Prompt ảnh sang video",
    "mode.json-to-natural-prompt.label": "JSON sang prompt tự nhiên"
  },
  "en": {
    "app.title": "Img automation App",
    "app.subtitle": "Outfit swap prompt workspace",
    "settings.title": "Settings",
    "settings.subtitle": "API key, language, and connection options.",
    "settings.close": "Close settings",
    "settings.language": "Language",
    "settings.language.vi": "Tiếng Việt",
    "settings.language.en": "English",
    "settings.api_key": "Secret API key",
    "settings.show_key": "Show key",
    "settings.hide_key": "Hide key",
    "status.ready": "Ready",
    "status.pywebview_unavailable": "pywebview API is not ready",
    "status.image_compressing": "Compressing images...",
    "status.images_ready": "Images ready",
    "status.reference_ready": "Reference images ready",
    "status.generating": "Calling API...",
    "status.done": "Done",
    "status.generate_error": "Generate error",
    "status.api_testing": "Testing API...",
    "status.api_ok": "API OK",
    "status.copied": "Copied",
    "status.section_copied": "Section copied",
    "status.chatgpt_opened": "ChatGPT opened",
    "status.chrome_error": "Could not open Chrome",
    "status.too_many_images": "Too many images",
    "status.missing_outfit_images": "Missing A.1 or A.2",
    "status.relay_invalid": "Invalid Relay URL",
    "status.relay_saved": "Custom Relay saved",
    "btn.test_api": "Test API",
    "btn.settings": "Settings",
    "btn.generate": "Generate prompt",
    "btn.generating": "Generating prompt",
    "btn.copy": "Copy",
    "btn.download": "Download TXT",
    "btn.open_chatgpt": "Open ChatGPT",
    "btn.close": "Close",
    "btn.retry": "Retry",
    "btn.set_custom_relay": "Set Custom Relay",
    "label.mode": "Generation mode",
    "label.model": "Model",
    "label.target": "Target",
    "label.style": "Style",
    "label.aspect": "Aspect ratio",
    "label.quality": "Quality",
    "label.resolution": "Resolution",
    "label.extra_notes": "Extra notes",
    "label.reference_images": "Reference images",
    "label.config": "Configuration",
    "label.output": "Prompt Preview",
    "helper.mode": "Mode help",
    "hint.config": "Model and render parameters.",
    "hint.extra_notes": "Mood, camera, lighting, background, or extra constraints.",
    "hint.output": "API result ready to copy into ChatGPT Image.",
    "hint.empty_title": "Upload images and click Generate prompt",
    "hint.empty_body": "Results will appear here in sections for review and copy.",
    "hint.storyboard": "Hint: will create {count} scenes (default 9, range 3-12).",
    "placeholder.loading": "Loading...",
    "placeholder.api_from_env": "Using sk key from .env",
    "placeholder.extra_notes": "Example: preserve the model face, follow the original outfit, soft studio lighting, minimal background.",
    "error.unsupported_file": "Skipped unsupported file: {name}",
    "error.max_generic_images": "Generic modes accept up to 5 reference images.",
    "error.missing_outfit_images": "Upload at least A.1 Model identity and A.2 Outfit source.",
    "error.open_chatgpt": "Could not open ChatGPT.",
    "message.hidden_outfit": "{count} outfit images are hidden and will not be sent to the current mode.",
    "message.hidden_generic": "{count} generic reference images are hidden and will not be sent to outfit mode.",
    "message.saved_handoff": "Saved handoff: {file}",
    "message.chatgpt_opened": "ChatGPT opened.",
    "message.cf_error": "All Pollinations endpoints are blocked (multiple profiles and endpoints were tried). The app will retry automatically. If it still fails, paste a Custom Relay URL in Settings.",
    "message.cf_body": "All Pollinations endpoints are blocked. The app will retry automatically, or you can paste your own relay URL.",
    "message.cf_meta": "Custom Relay will be saved locally on this machine.",
    "mode.outfit-swap-json.label": "Outfit swap",
    "mode.character-json.label": "Character JSON",
    "mode.product-detail-shots.label": "Product detail shots",
    "mode.storyboard-unified.label": "Storyboard",
    "mode.reference-pack.label": "Reference pack",
    "mode.image-to-video.label": "Image-to-video prompt",
    "mode.json-to-natural-prompt.label": "JSON to natural prompt"
  }
};
  const dicts = {};
  let current = localStorage.getItem("iaa_lang") || "vi";

  function format(value, params) {
    return String(value).replace(/\{(\w+)\}/g, (_, key) => params?.[key] ?? "");
  }

  async function loadDict(lang) {
    if (dicts[lang]) return dicts[lang];
    if (embedded[lang]) {
      dicts[lang] = embedded[lang];
      return dicts[lang];
    }
    const res = await fetch("./i18n/" + lang + ".json");
    if (!res.ok) throw new Error("i18n load failed: " + lang);
    dicts[lang] = await res.json();
    return dicts[lang];
  }

  function t(key, fallback, params) {
    const value = dicts[current]?.[key] ?? embedded[current]?.[key] ?? fallback ?? key;
    return format(value, params);
  }

  function apply() {
    document.documentElement.lang = current;
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      node.textContent = t(node.dataset.i18n, node.textContent);
    });
    document.querySelectorAll("[data-i18n-aria]").forEach((node) => {
      node.setAttribute("aria-label", t(node.dataset.i18nAria, node.getAttribute("aria-label") || ""));
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
      node.setAttribute("placeholder", t(node.dataset.i18nPlaceholder, node.getAttribute("placeholder") || ""));
    });
  }

  async function setLang(lang) {
    current = lang;
    localStorage.setItem("iaa_lang", lang);
    await loadDict(lang);
    apply();
    document.dispatchEvent(new CustomEvent("i18n:changed", { detail: { lang } }));
  }

  async function bootstrap() {
    await loadDict(current);
    apply();
  }

  window.I18n = {
    apply,
    bootstrap,
    getLang: () => current,
    loadDict,
    setLang,
    t,
  };
})();
