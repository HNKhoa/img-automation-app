import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const html = fs.readFileSync(path.join(root, "frontend", "index.html"), "utf8");
const js = fs.readFileSync(path.join(root, "frontend", "app.js"), "utf8");
const css = fs.readFileSync(path.join(root, "frontend", "styles.css"), "utf8");
const constants = fs.readFileSync(path.join(root, "backend", "constants.py"), "utf8");

const ids = [...js.matchAll(/\$\("([^"]+)"\)/g)].map((match) => match[1]);
const missing = ids.filter((id) => !html.includes(`id="${id}"`));

if (missing.length) {
  throw new Error(`Missing DOM ids referenced by frontend/app.js: ${missing.join(", ")}`);
}

for (const required of ["heroGenerateBtn", "outputBox", "modelUpload", "outfitUpload", "backgroundUpload", "apiKeyInput"]) {
  if (!html.includes(`id="${required}"`)) {
    throw new Error(`Required UI element not found: ${required}`);
  }
}

for (const required of [
  "modeSelect",
  "modeHelper",
  "genericReferenceUpload",
  "genericRefInput",
  "genericRefThumbs",
  "clearGenericRefBtn",
  "outfitOnlySection",
]) {
  if (!html.includes(`id="${required}"`)) {
    throw new Error(`Generation mode UI element not found: ${required}`);
  }
}

for (const selectId of ["modelSelect", "targetSelect", "styleSelect", "aspectSelect", "qualitySelect", "resolutionSelect"]) {
  const match = html.match(new RegExp(`<select id="${selectId}"[\\s\\S]*?<\\/select>`));
  if (!match) throw new Error(`Select not found: ${selectId}`);
  const optionCount = (match[0].match(/<option/g) || []).length;
  if (optionCount > 1) {
    throw new Error(`Select ${selectId} should not contain hard-coded options before bootstrap.`);
  }
}

const outfitOnlyCount = (html.match(/data-outfit-only/g) || []).length;
if (outfitOnlyCount < 2) {
  throw new Error("Expected outfit-only elements to use data-outfit-only.");
}

for (const required of ["chromiumManagerInput", "chromiumProfileIdInput", "chromiumPortInput", "downloadDirInput"]) {
  if (!html.includes(`id="${required}"`)) {
    throw new Error(`Chromium automation setting not found: ${required}`);
  }
}

if (!html.includes("Content-Security-Policy")) {
  throw new Error("CSP meta tag missing.");
}

if (!css.includes(".is-collapsed")) {
  throw new Error("Expected smooth collapse selector .is-collapsed in CSS.");
}

if (!constants.match(/STYLE_OPTIONS\s*=\s*\[\s*["']None["']/)) {
  throw new Error('STYLE_OPTIONS should start with "None".');
}

for (const action of ['data-action="cf-retry"', 'data-action="cf-set-relay"']) {
  if (!html.includes(action)) {
    throw new Error(`Cloudflare recovery action missing: ${action}`);
  }
}

for (const removed of ["profileList", "profileSearchInput", "refreshProfilesBtn"]) {
  if (html.includes(`id="${removed}"`) || js.includes(`"${removed}"`)) {
    throw new Error(`Chrome profile UI should be hidden for now: ${removed}`);
  }
}

if (html.includes("window-bar")) {
  throw new Error("Old fake browser/window header should be removed.");
}

for (const token of ["--blue", "--cyan", "--violet", "--bg-card", "backdrop-filter", "radial-gradient", "linear-gradient"]) {
  if (!css.includes(token)) {
    throw new Error(`Expected Neurom UI token missing: ${token}`);
  }
}

console.log("frontend static check ok");
