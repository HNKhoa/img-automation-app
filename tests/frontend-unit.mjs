import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

// Normalize line endings because GitHub Actions checks out text files as CRLF on
// windows-latest, while the helper extraction regexes are line-oriented.
const src = fs.readFileSync("frontend/app.js", "utf8").replace(/\r\n/g, "\n");
const modesSrc = fs.readFileSync("frontend/modes.js", "utf8").replace(/\r\n/g, "\n");

const ctx = vm.createContext({
  document: { getElementById: () => null },
  window: {},
  crypto: globalThis.crypto,
});

const helperMatch = src.match(/function parsePromptSections[\s\S]+?\n\}\n/);
if (!helperMatch) throw new Error("parsePromptSections not found in app.js");
vm.runInContext(
  helperMatch[0] + "\nglobalThis.parsePromptSections = parsePromptSections;",
  ctx,
);

const formatStart = src.indexOf("function formatError");
const formatEnd = src.indexOf("async function testApi");
if (formatStart === -1 || formatEnd === -1) throw new Error("formatError not found in app.js");
vm.runInContext(src.slice(formatStart, formatEnd) + "\nglobalThis.formatError = formatError;", ctx);

test("parsePromptSections: three labeled sections", () => {
  const out = ctx.parsePromptSections(
    "MAIN PROMPT:\nA\n\nNEGATIVE PROMPT:\nB\n\nREFERENCE BINDING INSTRUCTIONS:\nC",
  );
  assert.equal(out.length, 3);
  assert.equal(out[0].title, "MAIN PROMPT");
  assert.equal(out[1].title, "NEGATIVE PROMPT");
  assert.equal(out[2].title, "REFERENCE BINDING INSTRUCTIONS");
});

test("parsePromptSections: case-insensitive label", () => {
  const out = ctx.parsePromptSections("main prompt:\nA");
  assert.equal(out[0].title, "MAIN PROMPT");
});

test("parsePromptSections: fallback when no labels", () => {
  const out = ctx.parsePromptSections("just text");
  assert.equal(out.length, 1);
  assert.equal(out[0].title, "Prompt");
});

test("formatError: cloudflare message mentions endpoint and Custom Relay", () => {
  const out = ctx.formatError({ code: "CLOUDFLARE_ACCESS_DENIED" });
  assert.match(out, /endpoint/i);
  assert.match(out, /Custom Relay/i);
});

const modeCtx = vm.createContext({
  window: {},
  document: { querySelectorAll: () => [] },
  navigator: { clipboard: { writeText: async () => {} } },
});
vm.runInContext(modesSrc, modeCtx);

function element() {
  const classes = new Set();
  return {
    hidden: false,
    attributes: {},
    classList: {
      toggle(name, force) {
        if (force) classes.add(name);
        else classes.delete(name);
      },
      contains(name) {
        return classes.has(name);
      },
    },
    setAttribute(name, value) {
      this.attributes[name] = value;
    },
    querySelectorAll() {
      return [];
    },
  };
}

function dom() {
  return {
    outfitOnlySection: element(),
    genericReferenceUpload: element(),
    targetField: element(),
    handoffBtn: element(),
    modePurpose: { textContent: "" },
    modeUsage: { textContent: "" },
    genericRefHint: { textContent: "" },
    outputSections: { innerHTML: "", appendChild() {} },
  };
}

test("applyModeUI: outfit shows outfit controls", () => {
  const d = dom();
  modeCtx.window.GenerationModes.applyModeUI({ kind: "outfit", allow_images: true, purpose: "p", usage: "u" }, d);
  assert.equal(d.outfitOnlySection.classList.contains("is-collapsed"), false);
  assert.equal(d.genericReferenceUpload.hidden, true);
  assert.equal(d.handoffBtn.classList.contains("is-collapsed"), false);
});

test("applyModeUI: generic image mode shows generic upload", () => {
  const d = dom();
  modeCtx.window.GenerationModes.applyModeUI({ kind: "generic", allow_images: true, purpose: "p", usage: "u" }, d);
  assert.equal(d.outfitOnlySection.classList.contains("is-collapsed"), true);
  assert.equal(d.genericReferenceUpload.hidden, false);
  assert.equal(d.handoffBtn.classList.contains("is-collapsed"), false);
});

test("applyModeUI: json-to-natural hides upload", () => {
  const d = dom();
  modeCtx.window.GenerationModes.applyModeUI({ kind: "generic", allow_images: false, purpose: "p", usage: "u" }, d);
  assert.equal(d.outfitOnlySection.classList.contains("is-collapsed"), true);
  assert.equal(d.genericReferenceUpload.hidden, true);
});

test("buildGenericPayload excludes outfit-only fields", () => {
  const payload = modeCtx.window.GenerationModes.buildGenericPayload({
    modeSpec: { id: "character-json", allow_images: true },
    model: "gpt-5.4-nano",
    userInput: "x",
    style: "s",
    aspectRatio: "1:1",
    resolution: "2K",
    quality: "high",
    apiKey: "sk_x",
    images: [{ role: "model", dataUrl: "data:image/jpeg;base64,a" }],
  });
  assert.equal(payload.mode, "character-json");
  assert.equal(payload.images[0].role, "reference");
  assert.equal("target_model_rule" in payload, false);
  assert.equal("quality_profile" in payload, false);
  assert.equal("critic_enabled" in payload, false);
});

test("parseTwoSections returns natural and negative", () => {
  const out = modeCtx.window.GenerationModes.parseTwoSections("NATURAL PROMPT:\nfoo\n\nNEGATIVE PROMPT:\nbar");
  assert.equal(out.natural, "foo");
  assert.equal(out.negative, "bar");
});

test("parseTwoSections tolerates same-line negative heading", () => {
  const out = modeCtx.window.GenerationModes.parseTwoSections("NATURAL PROMPT: foo NEGATIVE PROMPT: bar");
  assert.equal(out.natural, "foo");
  assert.equal(out.negative, "bar");
});

test("parseShotList counts nine shots", () => {
  const text = Array.from({ length: 9 }, (_, i) => `Shot ${i + 1}: Name\nSUBJECT:\nx`).join("\n\n");
  assert.equal(modeCtx.window.GenerationModes.parseShotList(text).length, 9);
});

test("parseReferencePack splits three groups", () => {
  const text = "1. Character Reference Pack\nA\n\n2. Background Reference Pack\nB\n\n3. Product Reference Pack\nC";
  const out = modeCtx.window.GenerationModes.parseReferencePack(text);
  assert.equal(out.length, 3);
  assert.match(out[0].title, /Character/);
  assert.match(out[1].title, /Background/);
  assert.match(out[2].title, /Product/);
});

test("parseSceneCount clamps and defaults", () => {
  assert.equal(modeCtx.window.GenerationModes.parseSceneCount("tao 6 canh"), 6);
  assert.equal(modeCtx.window.GenerationModes.parseSceneCount("twelve"), 9);
  assert.equal(modeCtx.window.GenerationModes.parseSceneCount("20 frames"), 12);
  assert.equal(modeCtx.window.GenerationModes.parseSceneCount("1 scene"), 3);
});
