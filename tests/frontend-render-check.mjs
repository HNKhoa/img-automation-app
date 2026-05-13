import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";

const root = process.cwd();
const artifactDir = path.join(root, ".test-artifacts");
fs.mkdirSync(artifactDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1365, height: 900 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.join(root, "frontend", "index.html")).href);

const checks = await page.evaluate(() => {
  const selectors = [".desktop-frame", ".app-topbar", ".upload-control", ".upload-grid", ".content-grid", ".output-panel", "#heroGenerateBtn", "#settingsBtn"];
  return selectors.map((selector) => {
    const node = document.querySelector(selector);
    const rect = node?.getBoundingClientRect();
    return {
      selector,
      exists: Boolean(node),
      width: rect?.width || 0,
      height: rect?.height || 0,
    };
  });
});

const failed = checks.filter((item) => !item.exists || item.width < 20 || item.height < 20);
if (failed.length) {
  throw new Error(`Render check failed: ${JSON.stringify(failed)}`);
}

if (await page.locator(".profile-column").count()) {
  throw new Error("Chrome profile sidebar should not render in the current UX.");
}

if (await page.locator(".window-bar").count()) {
  throw new Error("The old fake browser/window header should not render.");
}

await page.locator("#settingsBtn").click();
if (!(await page.locator("#apiKeyInput").isVisible())) {
  throw new Error("API key input should be visible after opening Settings.");
}
await page.locator("#closeSettingsBtn").click();

if (await page.locator(".metric-grid").count()) {
  throw new Error("Static metric cards should not render in the productivity layout.");
}

await page.evaluate(() => {
  window.GenerationModes.applyModeUI(
    {
      id: "character-json",
      kind: "generic",
      output_type: "json",
      allow_images: true,
      purpose: "Tao JSON nhan vat.",
      usage: "Upload reference neu can.",
    },
    {
      outfitOnlySection: document.getElementById("outfitOnlySection"),
      genericReferenceUpload: document.getElementById("genericReferenceUpload"),
      targetField: document.getElementById("targetField"),
      handoffBtn: document.getElementById("handoffBtn"),
      modePurpose: document.querySelector("#modeHelper .mode-purpose"),
      modeUsage: document.querySelector("#modeHelper .mode-usage"),
      genericRefHint: document.getElementById("genericRefHint"),
      outputSections: document.getElementById("outputSections"),
    },
  );
});

if (!(await page.locator("#genericReferenceUpload").isVisible())) {
  throw new Error("Generic reference upload should render after switching to a generic image mode.");
}

await page.screenshot({ path: path.join(artifactDir, "frontend-render.png") });
await browser.close();

console.log("frontend render check ok");
