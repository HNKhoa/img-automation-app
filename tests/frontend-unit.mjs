import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const src = fs.readFileSync("frontend/app.js", "utf8");

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
