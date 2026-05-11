// LocalStorage-backed history (max 10 entries; no images, no API key).
const KEY = "iaa_history_v1";
const MAX = 10;

export function loadHistory() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function pushHistory(entry) {
  const items = loadHistory();
  items.unshift({
    id: crypto.randomUUID(),
    ts: Date.now(),
    user_request: entry.user_request || "",
    target: entry.target_model_rule || "",
    model: entry.model || "",
    output_summary: (entry.output || "").slice(0, 200),
    output: entry.output || "",
  });
  localStorage.setItem(KEY, JSON.stringify(items.slice(0, MAX)));
}

export function clearHistory() {
  localStorage.removeItem(KEY);
}

export function findHistory(id) {
  return loadHistory().find((item) => item.id === id) || null;
}
