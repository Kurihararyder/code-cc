// DOM 小工具：不使用 innerHTML 組動態內容，避免 XSS，也符合嚴格 CSP。
// 安全網：Element.append 忽略 null／false 並展開陣列（避免把 "null" 當文字畫出來）。
const nativeAppend = Element.prototype.append;
Element.prototype.append = function (...kids) { return nativeAppend.apply(this, kids.flat(Infinity).filter((k) => k != null && k !== false)); };

export const $ = (s, r = document) => r.querySelector(s);
export const $$ = (s, r = document) => [...r.querySelectorAll(s)];

export function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  if (attrs) {
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "text") el.textContent = v;
      else if (k === "style") for (const [p, val] of Object.entries(v)) el.style.setProperty(p, val);
      else if (k === "dataset") Object.assign(el.dataset, v);
      else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v);
      else if (v === true) el.setAttribute(k, "");
      else el.setAttribute(k, v);
    }
  }
  append(el, kids);
  return el;
}
export function append(el, kids) {
  for (const k of kids.flat(Infinity)) {
    if (k == null || k === false) continue;
    el.append(k.nodeType ? k : document.createTextNode(String(k)));
  }
  return el;
}
export function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); return el; }
export function icon(name, cls = "") {
  const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  s.setAttribute("class", "ic " + cls); s.setAttribute("aria-hidden", "true");
  const u = document.createElementNS("http://www.w3.org/2000/svg", "use");
  u.setAttribute("href", "#i-" + name); s.append(u); return s;
}
export const pct = (a, b) => (b ? Math.round((100 * a) / b) : 0);
export function fmtDur(sec) {
  sec = Math.max(0, Math.floor(sec)); const h_ = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
  const p = (n) => String(n).padStart(2, "0");
  return h_ ? `${h_}:${p(m)}:${p(s)}` : `${p(m)}:${p(s)}`;
}
export function fmtDate(ts) { const d = new Date(ts * 1000); return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`; }
export function stars(n) { return "★".repeat(Math.max(1, Math.min(4, n || 1))); }
export const VERDICT_ZH = { AC: "通過", WA: "答案錯誤", PE: "格式錯誤", TLE: "超過時間", RE: "執行錯誤", CE: "語法／編譯錯誤" };

// ---- toast ----
export function toast(msg, kind = "", ms = 4500) {
  const box = $("#toasts");
  const t = h("div", { class: "toast " + kind, role: kind === "bad" ? "alert" : "status" },
    h("span", { text: msg }), h("button", { "aria-label": "關閉", onclick: () => t.remove() }, icon("x")));
  box.append(t);
  if (ms) setTimeout(() => t.remove(), ms);
  return t;
}

// ---- modal / drawer ----
const layer = () => $("#layer");
const openLayers = new Set();
export function closeAllLayers() { [...openLayers].forEach((c) => c()); }
export function modal({ title, body, actions = [], wide = false, onClose, label }) {
  const prev = document.activeElement;
  const close = () => { if (!openLayers.delete(close)) return; back.remove(); document.removeEventListener("keydown", onKey, true); prev?.focus?.(); onClose?.(); };
  openLayers.add(close);
  const box = h("div", { class: "modal" + (wide ? " wide" : ""), role: "dialog", "aria-modal": "true", "aria-label": label || title },
    title ? h("div", { class: "modal-h" }, h("h2", { text: title }), h("button", { class: "btn ghost icon sm", "aria-label": "關閉", onclick: close }, icon("x"))) : null,
    h("div", { class: "modal-b" }, body),
    actions.length ? h("div", { class: "modal-f" }, actions.map((a) => h("button", { class: "btn " + (a.kind || ""), onclick: async () => { const r = await a.onClick?.(close); if (r !== false && !a.keep) close(); } }, a.label))) : null);
  const back = h("div", { class: "backdrop", onmousedown: (e) => { if (e.target === back) close(); } }, box);
  const onKey = (e) => {
    if (e.key === "Escape") { e.stopPropagation(); close(); }
    if (e.key === "Tab") {
      const f = $$("button,[href],input,select,textarea,[tabindex]:not([tabindex='-1'])", box).filter((x) => !x.disabled && x.offsetParent !== null);
      if (!f.length) return; const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  };
  document.addEventListener("keydown", onKey, true);
  layer().append(back);
  (box.querySelector("[autofocus]") || box.querySelector(".modal-f .primary") || box.querySelector("button, input"))?.focus();
  return { close, el: box };
}
export function drawer(content, onClose) {
  const prev = document.activeElement;
  const close = () => { if (!openLayers.delete(close)) return; wrap.remove(); document.removeEventListener("keydown", onKey, true); prev?.focus?.(); onClose?.(); };
  openLayers.add(close);
  const d = h("aside", { class: "drawer", role: "dialog", "aria-modal": "true" }, content(close));
  const wrap = h("div", { class: "scrim", onmousedown: (e) => { if (e.target === wrap) close(); } }, d);
  const onKey = (e) => { if (e.key === "Escape") close(); };
  document.addEventListener("keydown", onKey, true);
  layer().append(wrap); d.querySelector("button")?.focus();
  return { close, el: d };
}
export function confirmDialog(title, text, okLabel = "確定", kind = "primary") {
  return new Promise((res) => {
    let done = false;
    modal({ title, body: h("p", { text }), onClose: () => { if (!done) res(false); },
      actions: [{ label: "取消", onClick: () => { done = true; res(false); } }, { label: okLabel, kind, onClick: () => { done = true; res(true); } }] });
  });
}
export function debounce(fn, ms) { let t; const w = (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; w.flush = (...a) => { clearTimeout(t); return fn(...a); }; return w; }
