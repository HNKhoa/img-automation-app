// Lightweight i18n loader. Exposes loadDict/setLang/getLang/t.
const dicts = {};
let current = localStorage.getItem("iaa_lang") || "vi";

export async function loadDict(lang) {
  if (dicts[lang]) return dicts[lang];
  const res = await fetch(`./i18n/${lang}.json`);
  if (!res.ok) throw new Error(`i18n load failed: ${lang}`);
  dicts[lang] = await res.json();
  return dicts[lang];
}

export function t(key) {
  return dicts[current]?.[key] ?? key;
}

export async function setLang(lang) {
  current = lang;
  localStorage.setItem("iaa_lang", lang);
  await loadDict(lang);
  document.documentElement.lang = lang;
  document.dispatchEvent(new CustomEvent("i18n:changed", { detail: { lang } }));
}

export function getLang() {
  return current;
}

export async function bootstrapI18n() {
  await loadDict(current);
  document.documentElement.lang = current;
}
