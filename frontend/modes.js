(function () {
  const MODE_KIND = { OUTFIT: "outfit", GENERIC: "generic" };

  function applyModeUI(modeSpec, dom) {
    if (!modeSpec) return;
    const isOutfit = modeSpec.kind === MODE_KIND.OUTFIT;
    document.querySelectorAll("[data-outfit-only]").forEach((element) => {
      element.classList.toggle("is-collapsed", !isOutfit);
      element.setAttribute("aria-hidden", String(!isOutfit));
      element.querySelectorAll("input, select, textarea, button").forEach((control) => {
        control.tabIndex = isOutfit ? 0 : -1;
      });
    });
    if (dom.outfitOnlySection) {
      dom.outfitOnlySection.classList.toggle("is-collapsed", !isOutfit);
      dom.outfitOnlySection.setAttribute("aria-hidden", String(!isOutfit));
    }
    if (dom.targetField) {
      dom.targetField.classList.toggle("is-collapsed", !isOutfit);
      dom.targetField.setAttribute("aria-hidden", String(!isOutfit));
    }
    dom.genericReferenceUpload.hidden = isOutfit || !modeSpec.allow_images;
    dom.modePurpose.textContent = modeSpec.purpose || "";
    dom.modeUsage.textContent = modeSpec.usage || "";
    dom.genericRefHint.textContent = modeSpec.allow_images
      ? "Upload toi da 5 anh reference. Anh chi dung cho visual consistency."
      : "Mode nay chi dung text, khong gui anh len API.";
  }

  function buildGenericPayload({ modeSpec, model, userInput, style, aspectRatio, resolution, quality, apiKey, images, customRelay }) {
    const payload = {
      api_key: apiKey,
      mode: modeSpec.id,
      model,
      style,
      aspect_ratio: aspectRatio,
      resolution,
      quality,
      user_request: userInput,
      images: modeSpec.allow_images ? images.map((item) => ({ ...item, role: "reference" })) : [],
    };
    if (customRelay) payload.custom_relay_endpoint = customRelay;
    return payload;
  }

  function parseTwoSections(text) {
    const match = String(text || "").match(/NATURAL PROMPT\s*:\s*([\s\S]*?)\s*NEGATIVE PROMPT\s*:\s*([\s\S]*)/i);
    return match ? { natural: match[1].trim(), negative: match[2].trim() } : { natural: String(text || "").trim(), negative: "" };
  }

  function parseShotList(text) {
    const matches = [...String(text || "").matchAll(/^Shot\s+(\d+):\s*([^\n]*)/gim)];
    return matches.map((match, index) => {
      const end = matches[index + 1]?.index ?? text.length;
      return {
        number: Number(match[1]),
        title: match[2].trim() || `Shot ${match[1]}`,
        body: text.slice(match.index + match[0].length, end).trim(),
      };
    });
  }

  function parseReferencePack(text) {
    const source = String(text || "");
    const matches = [...source.matchAll(/^(?:\d+\.\s*)?(Character|Background|Product)\s+Reference Pack\b[^\n]*/gim)];
    if (!matches.length) return [{ title: "Reference Pack", body: source.trim() }];
    return matches.map((match, index) => {
      const end = matches[index + 1]?.index ?? source.length;
      return {
        title: match[0].trim(),
        body: source.slice(match.index + match[0].length, end).trim(),
      };
    });
  }

  function parseSceneCount(text) {
    const source = String(text || "");
    if (/\b3\s*x\s*3\b/i.test(source) || /\bstoryboard\s+9\b/i.test(source)) return 9;
    const match = source.match(/\b(\d+)\s*(?:scenes?|canh|cảnh|frames?|khung|panels?)\b/i);
    if (!match) return 9;
    return Math.max(3, Math.min(12, Number(match[1])));
  }

  function renderJsonObject(envelope, dom) {
    const output = envelope.result?.output || "";
    const parsed = envelope.result?.parsed || tryParseJson(output);
    appendDetails(dom.outputSections, "Raw JSON", output);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      for (const [key, value] of Object.entries(parsed)) {
        appendDetails(dom.outputSections, key, typeof value === "string" ? value : JSON.stringify(value, null, 2));
      }
    }
  }

  function renderTextCards(text, dom, parser) {
    const sections = parser(text);
    for (const section of sections) {
      const title = section.number != null ? `Shot ${section.number}: ${section.title || ""}`.trim() : section.title;
      appendDetails(dom.outputSections, title || "Section", section.body || "");
    }
  }

  function renderStoryboardArray(envelope, dom) {
    const scenes = envelope.result?.parsed || tryParseJson(envelope.result?.output || "") || [];
    const grid = document.createElement("div");
    grid.className = "scene-grid";
    for (const scene of Array.isArray(scenes) ? scenes : []) {
      const sceneNumber = scene.scene_number ?? "";
      const sceneTitle = scene.scene_title || scene.scene_purpose || "Scene";
      const body = Object.entries(scene)
        .map(([key, value]) => `${key}:\n${typeof value === "string" ? value : JSON.stringify(value, null, 2)}`)
        .join("\n\n");
      const card = document.createElement("div");
      card.className = "scene-card";
      appendDetails(card, `Scene ${sceneNumber}: ${sceneTitle}`, body);
      grid.appendChild(card);
    }
    dom.outputSections.appendChild(grid);
  }

  function appendDetails(container, titleText, bodyText) {
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
      await navigator.clipboard.writeText(bodyText || "");
    });
    summary.append(title, copy);
    const pre = document.createElement("pre");
    pre.textContent = bodyText || "";
    details.append(summary, pre);
    container.appendChild(details);
  }

  function tryParseJson(text) {
    try {
      return JSON.parse(text);
    } catch {
      return null;
    }
  }

  function renderResult(envelope, modeSpec, dom, fallbackRenderer) {
    dom.outputSections.innerHTML = "";
    if (!envelope?.ok) return;
    if (modeSpec.output_type === "json") {
      if (modeSpec.id === "storyboard-unified") {
        renderStoryboardArray(envelope, dom);
        return;
      }
      renderJsonObject(envelope, dom);
      return;
    }
    const text = envelope.result?.output || "";
    if (modeSpec.id === "product-detail-shots") {
      renderTextCards(text, dom, parseShotList);
      return;
    }
    if (modeSpec.id === "json-to-natural-prompt") {
      const sections = parseTwoSections(text);
      renderTextCards(text, dom, () => [
        { title: "NATURAL PROMPT", body: sections.natural },
        { title: "NEGATIVE PROMPT", body: sections.negative },
      ]);
      return;
    }
    if (modeSpec.id === "reference-pack") {
      renderTextCards(text, dom, parseReferencePack);
      return;
    }
    fallbackRenderer(text);
  }

  window.GenerationModes = {
    MODE_KIND,
    applyModeUI,
    buildGenericPayload,
    renderResult,
    parseTwoSections,
    parseShotList,
    parseReferencePack,
    parseSceneCount,
  };
})();
