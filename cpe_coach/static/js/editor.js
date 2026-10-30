// 程式編輯器：textarea（輸入）疊在上色層（顯示）之上。支援行裝飾、自動縮排、縮排／取消縮排、註解切換。
import { h } from "./dom.js";
import { highlightLines } from "./highlight.js";

export class Editor {
  constructor({ lang = "py", onChange, onRun, onSave, onSelect } = {}) {
    this.lang = lang; this.cb = { onChange, onRun, onSave, onSelect };
    this.marks = { err: new Set(), lint: new Set(), focus: new Set() }; this.cur = 1; this.lineEls = []; this.gEls = [];
    this.gi = h("div", { class: "gi" }); this.gutter = h("div", { class: "gutter", "aria-hidden": "true" }, this.gi);
    this.hlInner = h("div", { class: "gi" }); this.hl = h("div", { class: "hl", "aria-hidden": "true" }, this.hlInner);
    this.ta = h("textarea", { class: "ta", spellcheck: "false", autocapitalize: "off", autocomplete: "off", autocorrect: "off",
      "aria-label": "程式碼編輯區", wrap: "off" });
    this.el = h("div", { class: "editor" }, this.gutter, h("div", { class: "stack" }, this.hl, this.ta));
    this.ta.addEventListener("input", () => { this.render(); this.cb.onChange?.(this.getValue()); });
    this.ta.addEventListener("scroll", () => this.syncScroll());
    this.ta.addEventListener("keydown", (e) => this.onKey(e));
    this.ta.addEventListener("keyup", () => { this.trackCursor(); if (this.ta.selectionStart !== this.ta.selectionEnd) this.cb.onSelect?.(); });
    this.ta.addEventListener("mouseup", () => { this.trackCursor(); setTimeout(() => this.cb.onSelect?.(), 0); });
    this.ta.addEventListener("touchend", () => setTimeout(() => this.cb.onSelect?.(), 350));
    this.ta.addEventListener("select", () => { if (this.ta.selectionStart !== this.ta.selectionEnd) this.cb.onSelect?.(); });
    this.ta.addEventListener("click", () => this.trackCursor());
    this._lh = 22; this._cw = 8.4;
  }
  // ---- 內容 ----
  setValue(code, lang) { if (lang) this.lang = lang; this.ta.value = code ?? ""; this.marks = { err: new Set(), lint: new Set(), focus: new Set() }; this.render(); this.ta.scrollTop = 0; this.syncScroll(); }
  getValue() { return this.ta.value; }
  setReadOnly(v) { this.ta.readOnly = !!v; }
  setFontSize(px) {
    px = Math.max(11, Math.min(22, +px || 14));
    if (matchMedia("(pointer: coarse)").matches) px = Math.max(16, px);   // iOS 對小於 16px 的輸入框會自動放大
    this._lh = Math.round(px * 1.6);
    this.el.style.setProperty("--ed-size", px + "px"); this.el.style.setProperty("--ed-lh", this._lh + "px");
    const c = document.createElement("canvas").getContext("2d"); c.font = `${px}px ui-monospace, Menlo, Consolas, monospace`;
    this._cw = c.measureText("M").width || px * 0.6;
  }
  focus() { this.ta.focus(); }
  // ---- 渲染 ----
  render() {
    const code = this.ta.value; const lines = highlightLines(code, this.lang);
    this.hlInner.innerHTML = lines.map((l) => `<span class="l">${l}</span>`).join("");   // l 已由 highlight 跳脫
    this.lineEls = [...this.hlInner.children];
    const n = lines.length;
    if (this.gEls.length !== n) {
      this.gi.textContent = ""; this.gEls = [];
      for (let i = 1; i <= n; i++) { const g = h("div", { class: "g", text: String(i) }); this.gEls.push(g); this.gi.append(g); }
    }
    this.paintMarks(); this.syncScroll();
  }
  paintMarks() {
    this.lineEls.forEach((el, i) => {
      const n = i + 1;
      el.classList.toggle("err", this.marks.err.has(n)); el.classList.toggle("lint", this.marks.lint.has(n) && !this.marks.err.has(n));
      el.classList.toggle("focus", this.marks.focus.has(n)); el.classList.toggle("cur", n === this.cur && document.activeElement === this.ta);
      this.gEls[i]?.classList.toggle("err", this.marks.err.has(n)); this.gEls[i]?.classList.toggle("lint", this.marks.lint.has(n) && !this.marks.err.has(n));
      this.gEls[i]?.classList.toggle("cur", n === this.cur);
    });
  }
  mark(kind, lines) { this.marks[kind] = new Set(lines || []); this.paintMarks(); }
  clearMarks() { this.marks = { err: new Set(), lint: new Set(), focus: new Set() }; this.paintMarks(); }
  syncScroll() {
    const y = -this.ta.scrollTop + "px", x = -this.ta.scrollLeft + "px";
    this.hlInner.style.setProperty("--sy", y); this.hlInner.style.setProperty("--sx", x); this.gi.style.setProperty("--sy", y);
  }
  trackCursor() {
    const before = this.ta.value.slice(0, this.ta.selectionStart);
    const n = before.split("\n").length; if (n !== this.cur) { this.cur = n; this.paintMarks(); }
  }
  // ---- 行操作 ----
  scrollToLine(n) {
    const top = (n - 1) * this._lh, v = this.ta.clientHeight;
    if (top < this.ta.scrollTop + this._lh || top > this.ta.scrollTop + v - this._lh * 2) this.ta.scrollTop = Math.max(0, top - v / 3);
    this.syncScroll();
  }
  selectLines(a, b = a) {
    const lines = this.ta.value.split("\n"); let s = 0; for (let i = 0; i < a - 1 && i < lines.length; i++) s += lines[i].length + 1;
    let e = s; for (let i = a - 1; i < b && i < lines.length; i++) e += lines[i].length + 1; e = Math.max(s, e - 1);
    this.ta.focus({ preventScroll: true }); this.ta.setSelectionRange(s, e); this.scrollToLine(a);
  }
  flash(a, b = a) {
    const set = new Set(); for (let i = a; i <= b; i++) set.add(i);
    this.marks.focus = set; this.paintMarks(); this.scrollToLine(a);
    clearTimeout(this._ft); this._ft = setTimeout(() => { this.marks.focus = new Set(); this.paintMarks(); }, 2200);
  }
  // ---- 選取資訊（給「問 AI」選單用）----
  selection() {
    const { selectionStart: s, selectionEnd: e, value } = this.ta; if (s === e) return null;
    const text = value.slice(s, e); const a = value.slice(0, s).split("\n").length; const b = a + text.replace(/\n$/, "").split("\n").length - 1;
    const colStart = s - (value.lastIndexOf("\n", s - 1) + 1);
    const r = this.ta.getBoundingClientRect();
    const top = r.top + 10 + (a - 1) * this._lh - this.ta.scrollTop, left = r.left + 14 + colStart * this._cw - this.ta.scrollLeft;
    const bottom = r.top + 10 + b * this._lh - this.ta.scrollTop;
    return { source: "code", text, line_start: a, line_end: b,
      rect: { left: Math.max(r.left, Math.min(left, r.right - 20)), top: Math.max(r.top, Math.min(top, r.bottom - 20)), bottom: Math.max(r.top + 10, Math.min(bottom, r.bottom)), right: left + 40 } };
  }
  // ---- 編輯輔助 ----
  edit(start, end, text, selStart, selEnd) {
    const ta = this.ta; ta.focus(); ta.setSelectionRange(start, end);
    let ok = false; try { ok = document.execCommand("insertText", false, text); } catch { ok = false; }
    if (!ok) { ta.setRangeText(text, start, end, "end"); ta.dispatchEvent(new Event("input", { bubbles: true })); }
    if (selStart != null) ta.setSelectionRange(selStart, selEnd ?? selStart);
  }
  lineBounds(pos) { const v = this.ta.value; const s = v.lastIndexOf("\n", pos - 1) + 1; let e = v.indexOf("\n", pos); if (e < 0) e = v.length; return [s, e]; }
  onKey(e) {
    const ta = this.ta, v = ta.value, s = ta.selectionStart, en = ta.selectionEnd, mod = e.ctrlKey || e.metaKey;
    if (mod && e.key === "Enter") { e.preventDefault(); this.cb.onRun?.(); return; }
    if (mod && e.key.toLowerCase() === "s") { e.preventDefault(); this.cb.onSave?.(); return; }
    if (mod && e.key === "/") { e.preventDefault(); this.toggleComment(); return; }
    if (e.key === "Tab" && !mod) {
      e.preventDefault();
      if (s !== en && v.slice(s, en).includes("\n") || e.shiftKey) { this.shiftLines(e.shiftKey ? -1 : 1); return; }
      this.edit(s, en, "    "); return;
    }
    if (e.key === "Enter" && !mod && !e.shiftKey && s === en) {
      const [ls] = this.lineBounds(s); const before = v.slice(ls, s); const indent = before.match(/^[ \t]*/)[0];
      const t = before.trimEnd();
      const extra = (this.lang === "py" ? t.endsWith(":") : t.endsWith("{")) ? "    " : "";
      if (this.lang === "cpp" && t.endsWith("{") && v[s] === "}") { e.preventDefault(); this.edit(s, s, "\n" + indent + "    \n" + indent, s + 1 + indent.length + 4); return; }
      e.preventDefault(); this.edit(s, en, "\n" + indent + extra); return;
    }
    if (e.key === "Backspace" && s === en && s > 0) {
      const [ls] = this.lineBounds(s); const before = v.slice(ls, s);
      if (before.length >= 4 && /^ +$/.test(before) && before.length % 4 === 0) { e.preventDefault(); this.edit(s - 4, s, ""); }
    }
  }
  shiftLines(dir) {
    const v = this.ta.value, s = this.ta.selectionStart, en = this.ta.selectionEnd; const [a] = this.lineBounds(s); const [, b] = this.lineBounds(en > s && v[en - 1] === "\n" ? en - 1 : en);
    const block = v.slice(a, b); const out = block.split("\n").map((l) => dir > 0 ? "    " + l : l.replace(/^( {1,4}|\t)/, "")).join("\n");
    this.edit(a, b, out, a, a + out.length);
  }
  toggleComment() {
    const mark = this.lang === "cpp" ? "// " : "# ", v = this.ta.value, s = this.ta.selectionStart, en = this.ta.selectionEnd;
    const [a] = this.lineBounds(s); const [, b] = this.lineBounds(en > s && v[en - 1] === "\n" ? en - 1 : en);
    const lines = v.slice(a, b).split("\n"); const all = lines.filter((l) => l.trim()).every((l) => l.trimStart().startsWith(mark.trim()));
    const out = lines.map((l) => { if (!l.trim()) return l; const ind = l.match(/^\s*/)[0]; const rest = l.slice(ind.length);
      return all ? ind + rest.replace(new RegExp("^" + mark.trim().replace(/[/]/g, "\\/") + " ?"), "") : ind + mark + rest; }).join("\n");
    this.edit(a, b, out, a, a + out.length);
  }
}
