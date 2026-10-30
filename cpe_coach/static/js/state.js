// 全域狀態與偏好（偏好存在 localStorage；不可用時退回記憶體）。
const mem = {};
export const pref = {
  get(k, d) { try { const v = localStorage.getItem("cpe." + k); return v == null ? (k in mem ? mem[k] : d) : JSON.parse(v); } catch { return k in mem ? mem[k] : d; } },
  set(k, v) { mem[k] = v; try { localStorage.setItem("cpe." + k, JSON.stringify(v)); } catch { /* 隱私模式 */ } },
};
export const S = { ai: { available: false, model: "" }, exam: null, due: 0, unit: null, examAt: 0 };
const subs = new Set();
export const subscribe = (fn) => { subs.add(fn); return () => subs.delete(fn); };
export const emit = () => subs.forEach((f) => f(S));

export function applyTheme(t = pref.get("theme", "auto")) {
  document.documentElement.dataset.theme = t === "auto" ? "auto" : t;
}
export function stageColor(stage) { return `var(--s${Math.max(0, Math.min(5, stage ?? 0))})`; }
