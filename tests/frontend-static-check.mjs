import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const html = fs.readFileSync(path.join(root, "frontend", "index.html"), "utf8");
const js = fs.readFileSync(path.join(root, "frontend", "app.js"), "utf8");
const css = fs.readFileSync(path.join(root, "frontend", "styles.css"), "utf8");

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
