// 「選取文字 → 問 AI」：彈出選單、AI 對話串、引用驗證的呈現。
import { h, icon, clear, toast, $ } from "./dom.js";
import { get, post } from "./api.js";
import { render as md } from "./md.js";

export const KIND = {
  explain: { label: "這是什麼意思？", sub: "解釋詞彙或語法，不算提示", icon: "help" },
  question: { label: "考我這一段", sub: "AI 針對這一段出題・算 L2 提示", icon: "sparkle" },
  mismatch: { label: "預期和實際不同", sub: "針對失敗測資的差異・算 L4 提示", icon: "neq" },
};
const DICT = "https://dictionary.cambridge.org/dictionary/english-chinese-traditional/";
export const dictUrl = (w) => DICT + encodeURIComponent(w.toLowerCase());
// 選到的是單一英文單字（去掉頭尾標點）→ 回傳該字，否則 null。
export function singleWord(text) {
  const w = text.trim().replace(/^["'(\[]+|[.,;:!?)"'\]]+$/g, "");
  return /^[A-Za-z][A-Za-z'’-]{1,29}$/.test(w) ? w : null;
}
const SRC = { statement: "題目", code: "程式", output: "測試結果", trace: "追蹤" };

export function domSelection(root) {
  const sel = window.getSelection(); if (!sel || sel.isCollapsed || !sel.rangeCount) return null;
  const text = sel.toString(); if (text.trim().length < 2) return null;
  let n = sel.anchorNode; if (!n) return null; if (n.nodeType === 3) n = n.parentElement;
  const host = n?.closest?.("[data-src]"); if (!host || !root.contains(host)) return null;
  const r = sel.getRangeAt(0).getBoundingClientRect();
  return { source: host.dataset.src, text, line_start: null, line_end: null, rect: { left: r.left, top: r.top, bottom: r.bottom, right: r.right } };
}

export function highlightText(host, quote) {
  const q = quote.trim(); if (!q) return false;
  const w = document.createTreeWalker(host, NodeFilter.SHOW_TEXT);
  while (w.nextNode()) {
    const n = w.currentNode, i = n.nodeValue.indexOf(q);
    if (i >= 0) { const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + q.length); const s = getSelection(); s.removeAllRanges(); s.addRange(r); n.parentElement.scrollIntoView({ block: "center", behavior: "smooth" }); return true; }
  }
  return false;
}

export class AskUI {
  // ctx: { getId, getView, getEditor, getTraceText, root, onAsked, goTab, locate(src, quote, line) }
  constructor(ctx) { this.ctx = ctx; this.pop = null; this.pending = null; this.threads = []; this.listEl = h("div"); this.open = new Set(); this.waiting = null; this.bind(); }
  bind() {
    this._up = () => setTimeout(() => this.maybeShow(), 10);
    this._sc = () => { clearTimeout(this._t); this._t = setTimeout(() => this.maybeShow(true), 380); };
    this._down = (e) => { if (this.pop && !this.pop.contains(e.target)) this.hide(); };
    this._key = (e) => {
      if (e.key === "Escape" && this.pop) { this.dismissed = this.popKey; this.hide(); }
      if (e.altKey && e.key === "Enter" && this.pop) { e.preventDefault(); this.pop.querySelector("button:not([disabled])")?.focus(); }
      if (this.pop && ["ArrowDown", "ArrowUp"].includes(e.key) && this.pop.contains(document.activeElement)) {
        e.preventDefault(); const b = [...this.pop.querySelectorAll("button:not([disabled])")]; const i = b.indexOf(document.activeElement);
        b[(i + (e.key === "ArrowDown" ? 1 : -1) + b.length) % b.length]?.focus();
      }
    };
    document.addEventListener("mouseup", this._up); document.addEventListener("touchend", this._sc);
    document.addEventListener("selectionchange", this._sc); document.addEventListener("mousedown", this._down); document.addEventListener("keydown", this._key);
  }
  destroy() { for (const [ev, fn] of [["mouseup", this._up], ["touchend", this._sc], ["selectionchange", this._sc], ["mousedown", this._down], ["keydown", this._key]]) document.removeEventListener(ev, fn); this.hide(); }

  currentSelection() {
    const ed = this.ctx.getEditor();
    if (ed && document.activeElement === ed.ta) { const s = ed.selection(); if (s && s.text.trim().length >= 2) return s; return null; }
    return domSelection(this.ctx.root);
  }
  maybeShow(fromSelectionChange = false) {
    if (this.pop && this.pop.contains(document.activeElement)) return;
    if (document.activeElement && document.activeElement.closest?.(".reply, .modal, .palette")) return;
    const s = this.currentSelection();
    if (!s) { this.dismissed = null; if (!fromSelectionChange) this.hide(); return; }
    const key = `${s.source}|${s.line_start}|${s.text}`;
    if (this.dismissed === key) return;                    // 使用者按 Esc 關掉的同一段選取，不要再彈出
    if (this.pop && this.popKey === key) return;          // 同一段選取：不要重建（避免閃爍）
    this.pending = s; this.show(s); this.popKey = key;   // show() 會先 hide()，所以 key 要在它之後設
  }
  reasons() {
    const v = this.ctx.getView(); if (!v) return {};
    const r = {};
    if (v.exam) { for (const k of Object.keys(KIND)) r[k] = "考試中，AI 已鎖定"; return r; }
    if (!(this.ctx.ai().available)) { for (const k of Object.keys(KIND)) r[k] = "尚未設定 API 金鑰"; return r; }
    if (v.attempts < 1) r.question = "先跑過一次測試";
    else if (v.hint_level >= 2 && v.attempts_since_hint < 1) r.question = "上一題問完後，先改一版再測試";
    if (!v.last_verdict || v.last_verdict === "AC") r.mismatch = "最近一次測試要是失敗的";
    else if (v.hint_level >= 3 && v.attempts_since_hint < 1) r.mismatch = "先改一版再測試";
    return r;
  }
  show(sel) {
    this.hide(); const why = this.reasons();
    const note = h("input", { type: "text", placeholder: "（選填）先寫下你的猜測或疑問", "aria-label": "你的猜測", maxlength: 300 });
    const opts = Object.entries(KIND).map(([k, m]) => {
      const dis = !!why[k];
      return h("button", { class: "opt", disabled: dis, title: dis ? why[k] : "", onclick: () => { const info = this.pending; this.hide(); this.ask(k, info, note.value); } },
        icon(m.icon, "lg"), h("div", null, h("b", { text: m.label }), h("span", { text: dis ? "🔒 " + why[k] : m.sub })));
    });
    const q = sel.text.trim().replace(/\s+/g, " ");
    const word = sel.source === "statement" ? singleWord(sel.text) : null;   // 字典只對題目文字提供（程式裡的識別字不是要查的單字）
    const dict = word ? [
      h("button", { class: "opt", onclick: () => { this.hide(); window.open(dictUrl(word), "_blank", "noopener,noreferrer"); } },
        icon("book", "lg"), h("div", null, h("b", { text: `查字典：${word}` }), h("span", { text: "Cambridge 英漢（新分頁）" }))),
      h("button", { class: "opt", onclick: async () => { this.hide(); try { const r = await post("/api/vocab/add", { word, problem: this.ctx.getId() }); toast(`已加入單字本：${r.word}`, "ok", 2200); } catch (e) { toast(e.message, "bad"); } } },
        icon("list", "lg"), h("div", null, h("b", { text: "加入單字本" }), h("span", { text: "之後可在『考試』頁複習、匯出" })))] : [];
    this.pop = h("div", { class: "pop", role: "dialog", "aria-label": "要問這一段嗎？" },
      h("div", { class: "muted xs", text: `要問這一段嗎？${sel.line_start ? `（第 ${sel.line_start}${sel.line_end > sel.line_start ? "–" + sel.line_end : ""} 行）` : `（${SRC[sel.source] || ""}）`}` }),
      h("div", { class: "q", text: q.length > 120 ? q.slice(0, 120) + "…" : q }), h("div", { class: "opts" }, dict, opts), note);
    document.body.append(this.pop);
    const r = sel.rect, pw = 300, ph = this.pop.offsetHeight, vw = innerWidth, vh = innerHeight;
    let left = Math.min(Math.max(8, r.left), vw - pw - 8), top = r.bottom + 10, up = false;
    if (top + ph > vh - 8) { top = Math.max(8, r.top - ph - 10); up = true; }
    this.pop.style.left = left + "px"; this.pop.style.top = top + "px"; this.pop.classList.toggle("up", up);
    this.pop.style.setProperty("--ax", Math.min(Math.max(16, r.left - left + 8), pw - 28) + "px");
  }
  hide() { this.pop?.remove(); this.pop = null; this.popKey = null; }

  // ---- 呼叫 ----
  async ask(kind, info, note) {
    const id = this.ctx.getId(), ed = this.ctx.getEditor();
    this.waiting = { kind, info, at: Date.now() }; this.paint(); this.ctx.goTab?.("ai");
    try {
      const r = await post("/api/ask", { id, code: ed && ed.getValue() ? ed.getValue() : undefined, kind, source: info.source, selection: info.text, line_start: info.line_start,
        line_end: info.line_end, note: note || "", trace_text: this.ctx.getTraceText() });
      this.open = new Set([r.thread]); this.waiting = null; await this.load(); this.ctx.onAsked?.();
    } catch (e) { this.waiting = null; this.paint(); toast(e.message, e.status === 409 ? "warn" : "bad", 7000); }
  }
  async reply(threadId, text, btn) {
    if (!text.trim()) return; btn.disabled = true; this.waiting = { thread: threadId }; this.paint();
    try {
      const ed = this.ctx.getEditor();
      await post("/api/ask", { id: this.ctx.getId(), code: ed ? ed.getValue() : undefined, thread: threadId, reply: text, trace_text: this.ctx.getTraceText() });
      this.waiting = null; await this.load();
    } catch (e) { this.waiting = null; this.paint(); toast(e.message, "warn", 7000); }
  }
  async load() { try { this.threads = (await get("/api/chat", { id: this.ctx.getId() })).threads; } catch { this.threads = []; } this.paint(); }

  // ---- 畫面 ----
  paint() {
    const box = this.listEl; clear(box);
    const T = [...this.threads].reverse();
    if (this.waiting && !this.waiting.thread) {
      box.append(h("div", { class: "thread" }, h("div", { class: "thread-h" }, icon(KIND[this.waiting.kind].icon), h("b", { text: KIND[this.waiting.kind].label })),
        h("div", { class: "quote", text: this.waiting.info.text.slice(0, 200) }), h("div", { class: "msg ai" }, h("div", { class: "av", text: "AI" }), h("div", { class: "body" }, h("div", { class: "typing" }, h("i"), h("i"), h("i"))))));
    }
    if (!T.length && !this.waiting) { box.append(this.tip()); return; }
    T.forEach((t, i) => box.append(this.threadEl(t, i === 0 && this.open.size === 0 || this.open.has(t.id))));
  }
  tip() {
    return h("div", { class: "tip" }, h("p", null, icon("sparkle"), " ", h("b", { text: "用滑鼠選一段文字" })),
      h("p", { class: "small", text: "在題目、程式、測試結果或追蹤表上選取想問的地方，旁邊會跳出『要問這一段嗎？』。" }),
      h("ul", { class: "small" }, h("li", { text: "AI 必須逐字引用你選的內容，系統會驗證。" }), h("li", { text: "你先寫下猜測，效果比直接問答案好。" }), h("li", { text: "對錯永遠由測試決定，AI 只評論你的推理。" })));
  }
  threadEl(t, isOpen) {
    const k = KIND[t.kind] || KIND.question; const loc = t.line_start ? ` · 第 ${t.line_start}${t.line_end > t.line_start ? "–" + t.line_end : ""} 行` : "";
    const last = t.messages[t.messages.length - 1]; const waitingHere = this.waiting?.thread === t.id;
    const head = h("button", { class: "thread-h", "aria-expanded": String(isOpen), onclick: () => { isOpen ? this.open.delete(t.id) : this.open.add(t.id); if (!isOpen && this.open.size === 0) this.open.add(t.id); this.paint(); } },
      icon(k.icon), h("b", { text: k.label }), h("span", { class: "muted", text: `· ${SRC[t.source] || t.source}${loc}` }), h("span", { class: "grow" }), icon("chevron"));
    const el = h("div", { class: "thread" }, head);
    if (!isOpen) { el.append(h("div", { class: "quote", text: t.selection.slice(0, 80) })); return el; }
    el.append(h("div", { class: "quote", text: t.selection.slice(0, 400) }));
    t.messages.forEach((m, i) => {
      if (i === 0) return;
      if (m.role === "user") el.append(h("div", { class: "msg" }, h("div", { class: "av", text: "你" }), h("div", { class: "body" }, h("div", { class: "who", text: "你的回答" }), h("p", { text: m.display }))));
      else el.append(h("div", { class: "msg ai" }, h("div", { class: "av", text: "AI" }), h("div", { class: "body" }, h("div", { class: "who", text: "AI" + (m.type ? " · " + ({ predict: "預測", locate: "定位", counterexample: "反例", complexity: "複雜度", explain: "解釋", feedback: "回饋" }[m.type] || m.type) : "") }),
        md(m.display), this.evidence(m), m.warning ? h("div", { class: "callout warn mt" }, icon("alert"), h("span", { text: m.warning })) : null)));
    });
    if (waitingHere) el.append(h("div", { class: "msg ai" }, h("div", { class: "av", text: "AI" }), h("div", { class: "body" }, h("div", { class: "typing" }, h("i"), h("i"), h("i")))));
    else if (last && last.role === "assistant" && t.kind !== "explain" || (t.kind === "explain" && last?.role === "assistant")) {
      const ta = h("textarea", { rows: 2, placeholder: "用自己的話回答。AI 只評論你的推理，不評論程式對錯。", "aria-label": "你的回答" });
      const btn = h("button", { class: "btn primary icon", "aria-label": "送出", onclick: () => this.reply(t.id, ta.value, btn) }, icon("send"));
      ta.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); btn.click(); } });
      el.append(h("div", { class: "reply" }, ta, btn));
    }
    return el;
  }
  evidence(m) {
    if (!m.evidence?.length) return null;
    return h("div", { class: "evi" }, m.evidence.map((e) => e.ok
      ? h("button", { class: "chip", title: "點一下，在原處標出這段", onclick: () => this.ctx.locate(e.source, e.quote, e.line) }, icon("check"), e.source === "code" && e.line ? `第 ${e.line} 行：` : (SRC[e.source] || e.source) + "：", h("code", { text: e.quote.slice(0, 36) }))
      : h("span", { class: "chip bad", title: "系統在原文中找不到這段引用，已標為無效" }, icon("x"), h("code", { text: e.quote.slice(0, 36) }))));
  }
}
