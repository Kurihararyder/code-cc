import { h, icon, clear, toast, stars, confirmDialog, debounce, fmtDate, modal, VERDICT_ZH, $ } from "./dom.js";
import { get, post, openPdf } from "./api.js";
import { go } from "./router.js";
import { S, pref } from "./state.js";
import { Editor } from "./editor.js";
import { render as md, inline } from "./md.js";
import { AskUI, highlightText } from "./ask.js";
import { skeleton, empty, notify, progress } from "./widgets.js";
import { renderStep } from "./viz.js";

const LEVELS = [
  ["理解題意", "把題目重述一遍的檢查清單；不談解法。", "free"],
  ["方向", "只告訴你這題屬於哪一類。", "needs-attempt"],
  ["關鍵觀察", "用一句話點出核心觀念。", "needs-attempt"],
  ["虛擬碼骨架", "給輸入→處理→輸出的結構（需要 AI）。", "needs-attempt"],
  ["錯誤定位", "根據失敗的測資指出問題所在（需要失敗的測試）。", "needs-attempt"],
];

export async function mountWorkspace(view, params) {
  let pid = params[0];
  if (!pid) {
    try { const d = await get("/api/dashboard"); pid = d.next?.id || (await get("/api/unit")).drills[0]?.id; } catch { /* 下面處理 */ }
    if (!pid) { view.append(h("div", { class: "page" }, empty("code", "找不到可練習的題目。按 Ctrl/⌘K 搜尋題號，例如 d001。"))); return; }
    return go("/practice/" + pid);
  }
  view.append(h("div", { class: "page" }, h("div", { class: "card pad" }, skeleton(5))));
  let V, unit;
  try { [V, unit] = await Promise.all([get("/api/problem", { id: pid }), get("/api/unit").catch(() => null)]); }
  catch (e) { clear(view); view.append(h("div", { class: "page" }, empty("alert", e.message))); return; }
  clear(view);
  return new Workspace(view, pid, V, unit).mount();
}

class Workspace {
  constructor(view, pid, V, unit) {
    this.view = view; this.pid = pid; this.V = V; this.unit = unit; this.traceText = ""; this.busy = false; this.hintTexts = {}; this.lastResult = null;
    this.editor = new Editor({ lang: V.lang, onChange: () => this.onEdit(), onRun: () => this.run(), onSave: () => this.save(true), onSelect: () => this.ask?.maybeShow() });
    this.editor.setFontSize(pref.get("fontSize", 14));
    // 編輯行為：只數次數與時間，不記打了什麼字（隱私）。按「執行」時隨結果送出，供伺服器判斷是不是卡住了。
    this.beh = { edits: 0, deletes: 0, pastes: 0, active_s: 0, max_pause_s: 0, runs: 0, opened: Date.now(), last: 0 };
    this.editor.ta.addEventListener("input", (e) => {
      const b = this.beh, now = Date.now(); b.edits++;
      if ((e.inputType || "").startsWith("delete")) b.deletes++;
      if ((e.inputType || "") === "insertFromPaste") b.pastes++;
      if (b.last) { const gap = (now - b.last) / 1000; if (gap < 60) b.active_s += gap; b.max_pause_s = Math.max(b.max_pause_s, gap); }
      b.last = now;
    });
    this.saveSoon = debounce(() => this.save(false), 900); this.dirty = false;
    if (V.exam) this.examMode();
  }
  // 考場模式（考試進行中）：禁止貼上、回報離開考試視窗的次數（只記次數與秒數，不記去了哪裡）；可以按鈕進入全螢幕。交卷時計分板會顯示離開次數。
  examMode() {
    this.editor.ta.addEventListener("paste", (e) => { e.preventDefault(); toast("考場模式：不能貼上（比照真實考試）", "warn", 2500); });
    let hiddenAt = 0;
    this._vis = () => {
      if (document.hidden) { hiddenAt = Date.now(); return; }
      if (hiddenAt) { const sec = Math.round((Date.now() - hiddenAt) / 1000); hiddenAt = 0; post("/api/exam/focus", { seconds: sec }).then((r) => { if (r.active) toast(`你離開了考試視窗（${r.count} 次，會記在成績單上）`, "warn", 3500); }).catch(() => {}); }
    };
    document.addEventListener("visibilitychange", this._vis);
  }
  // ---------- 掛載 ----------
  mount() {
    const V = this.V;
    this.stmtBox = h("div", { class: "stmt", dataset: { src: "statement" } });
    this.unitBox = h("div", { class: "pad" });
    this.p1Body = h("div", { class: "pane-b" }, this.stmtBox);
    this.probbar = h("div", { class: "probbar", role: "tablist", "aria-label": "本單元題目" });
    const t1 = h("div", { class: "tabs", role: "tablist" }, this.tabBtn("題目敘述", "stmt", true), this.tabBtn("本單元", "unit"));
    this.p1 = h("section", { class: "pane", id: "p1", "aria-label": "題目" }, this.probbar, t1, this.p1Body);
    this.t1 = t1;

    this.saveStat = h("span", { class: "muted xs", text: "" });
    this.runBtn = h("button", { class: "btn primary", onclick: () => this.run(), title: "Ctrl/⌘ + Enter" }, icon("play"), h("span", { text: "執行測試" }));
    this.predict = h("select", { "aria-label": "先預測結果", title: "先預測再執行：統計你預測自己程式的準確度" },
      [["", "預測：—"], ["AC", "預測：通過"], ["WA", "預測：答案錯"], ["TLE", "預測：超時"], ["RE", "預測：執行錯誤"]].map(([v, t]) => h("option", { value: v, text: t })));
    this.traceBtn = h("button", { class: "btn", onclick: () => this.trace(), title: "逐行顯示變數怎麼變" }, icon("list"), h("span", { class: "hide-m", text: "逐行追蹤" }));
    this.fuzzBtn = h("button", { class: "btn", onclick: () => this.fuzz(), title: "寫一個暴力解，自動找出你的解答在範例附近的錯，存成新測資" }, icon("neq"), h("span", { class: "hide-m", text: "對拍補測資" }));
    this.ladder = h("div", { class: "ladder", title: "提示使用程度；用了提示通過的題目，之後要無提示重寫" }, [0, 1, 2, 3, 4].map(() => h("i")));
    const fs = h("div", { class: "row gap-sm hide-m" }, h("button", { class: "btn ghost sm icon", "aria-label": "縮小字體", onclick: () => this.font(-1) }, "A−"), h("button", { class: "btn ghost sm icon", "aria-label": "放大字體", onclick: () => this.font(1) }, "A+"));
    this.langPill = h("span", { class: "pill accent", text: V.lang === "cpp" ? "C++" : "Python" });
    const bar = h("div", { class: "toolbar" }, this.runBtn, this.predict, this.traceBtn, this.fuzzBtn, h("span", { class: "grow" }), this.langPill);
    this.startBox = h("div", { class: "pane-b" });
    this.edwrap = h("div", { class: "edwrap" }, bar, this.editor.el, h("div", { class: "edfoot" }, h("div", { class: "grow" }, this.ladder), this.saveStat, fs));
    this.resTabs = h("div", { class: "tabs", role: "tablist" }, this.resTab("結果", "res", true), this.resTab("追蹤", "trace"), this.resTab("提醒", "lint"));
    this.resBody = h("div", { class: "pane-b" });
    this.res = h("div", { class: "res", hidden: true }, this.resTabs, this.resBody);
    this.p2 = h("section", { class: "pane", id: "p2", "aria-label": "程式" }, this.edwrap, this.res, this.startBox);

    this.aiTabs = h("div", { class: "tabs", role: "tablist" }, this.aiTab("AI 詢問", "ask", true), this.aiTab("提示階梯", "hints"));
    this.aiBody = h("div", { class: "pane-b" });
    this.p3 = h("section", { class: "pane", id: "p3", "aria-label": "AI 與提示" }, this.aiTabs, this.aiBody);

    this.ws = h("div", { class: "ws", dataset: { tab: "code" } }, this.p1, this.splitter(1), this.p2, this.splitter(2), this.p3);
    this.ws.style.setProperty("--w1", pref.get("w1", 27) + "%"); this.ws.style.setProperty("--w3", pref.get("w3", 31) + "%");
    const mt = h("div", { class: "mtabs", role: "tablist" }, [["stmt", "題目"], ["code", "程式"], ["ai", "AI"]].map(([k, t]) => h("button", { role: "tab", "aria-selected": String(k === "code"), dataset: { t: k }, onclick: () => this.tab(k) }, t)));
    this.mt = mt;
    this.view.append(h("div", { class: "wsm", style: { height: "100%", display: "flex", "flex-direction": "column" } }, mt, this.ws));
    this.view.style.overflow = "hidden";

    this.ask = new AskUI({ root: this.view, getId: () => this.pid, getView: () => this.V, getEditor: () => (this.V.code !== null ? this.editor : null),
      getTraceText: () => this.traceText, ai: () => S.ai, goTab: () => { this.tab("ai"); this.setAi("ask"); }, onAsked: () => this.reloadView(), locate: (s, q, l) => this.locate(s, q, l) });

    this.paintProblem(); this.paintProbbar(); this.paintUnit(); this.setAi("ask"); this.ask.load();
    this.setTabDefault();
    return () => this.destroy();
  }
  setTabDefault() { this.ws.dataset.tab = this.V.code === null ? "stmt" : "code"; this.mt.querySelectorAll("button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.t === this.ws.dataset.tab))); }
  destroy() { this.ask?.destroy(); if (this._vis) document.removeEventListener("visibilitychange", this._vis); if (this.dirty) this.save(false); this.view.style.overflow = ""; }
  tab(k) { this.ws.dataset.tab = k; this.mt.querySelectorAll("button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.t === k))); }

  tabBtn(label, k, sel) { return h("button", { role: "tab", "aria-selected": String(!!sel), onclick: (e) => this.setLeft(k, e.currentTarget.parentElement) }, label); }
  setLeft(k, tabs) { [...tabs.children].forEach((b) => b.setAttribute("aria-selected", String(b.textContent === (k === "stmt" ? "題目敘述" : "本單元")))); clear(this.p1Body); this.p1Body.append(k === "stmt" ? this.stmtBox : this.unitBox); }
  resTab(label, k, sel) { return h("button", { role: "tab", dataset: { k }, "aria-selected": String(!!sel), onclick: () => this.setRes(k) }, label); }
  aiTab(label, k, sel) { return h("button", { role: "tab", dataset: { k }, "aria-selected": String(!!sel), onclick: () => this.setAi(k) }, label); }
  setRes(k) { this.resK = k; [...this.resTabs.children].forEach((b) => b.setAttribute("aria-selected", String(b.dataset.k === k))); this.paintRes(); }
  setAi(k) { this.aiK = k; [...this.aiTabs.children].forEach((b) => b.setAttribute("aria-selected", String(b.dataset.k === k))); this.paintAi(); }
  splitter(n) {
    const el = h("div", { class: "splitter", role: "separator", "aria-orientation": "vertical", "aria-label": "調整欄寬", tabindex: 0 });
    const apply = (x) => {
      const r = this.ws.getBoundingClientRect(); const pct = (v) => Math.round(Math.max(18, Math.min(45, v)) * 10) / 10;
      if (n === 1) { const w = pct(((x - r.left) / r.width) * 100); this.ws.style.setProperty("--w1", w + "%"); pref.set("w1", w); }
      else { const w = pct(((r.right - x) / r.width) * 100); this.ws.style.setProperty("--w3", w + "%"); pref.set("w3", w); }
    };
    el.addEventListener("pointerdown", (e) => { el.setPointerCapture(e.pointerId); el.classList.add("drag"); const mv = (ev) => apply(ev.clientX); const up = () => { el.classList.remove("drag"); el.removeEventListener("pointermove", mv); el.removeEventListener("pointerup", up); }; el.addEventListener("pointermove", mv); el.addEventListener("pointerup", up); });
    el.addEventListener("keydown", (e) => { if (e.key === "ArrowLeft" || e.key === "ArrowRight") { const r = this.ws.getBoundingClientRect(); const cur = n === 1 ? pref.get("w1", 27) : pref.get("w3", 31); const d = (e.key === "ArrowRight" ? 1 : -1) * (n === 1 ? 1 : -1) * 2; apply(r.left + ((n === 1 ? cur + d : 100 - cur - d) / 100) * r.width); } });
    return el;
  }
  font(d) { const v = Math.max(11, Math.min(22, pref.get("fontSize", 14) + d)); pref.set("fontSize", v); this.editor.setFontSize(v); }

  // ---------- 題目 ----------
  async reloadView() { try { this.V = await get("/api/problem", { id: this.pid }); this.paintBadges(); this.paintLadder(); if (this.aiK === "hints") this.paintAi(); } catch { /* 忽略 */ } }
  paintStatement() {
    const V = this.V;
    clear(this.stmtBox);
    this.head = h("div", { class: "row wrap", style: { "margin-bottom": "10px" } });
    this.stmtBox.append(this.head);
    if (V.has_pdf) this.stmtBox.append(h("div", { class: "row wrap", style: { "margin-bottom": "8px" } },
      h("button", { class: "btn sm", title: "算式、表格、圖在文字版可能擷取得不完整，請對照原 PDF", onclick: async () => { try { await openPdf("/api/statement.pdf?id=" + encodeURIComponent(V.id)); } catch (e) { toast(e.message, "bad"); } } }, icon("book"), "開啟原 PDF 對照")));
    if (V.statement) this.stmtBox.append(md(V.statement));
    else this.stmtBox.append(h("div", { class: "callout" }, icon("book"), h("div", null, "這題沒有內建的題目敘述。", V.url ? [" 請到 ", h("a", { href: V.url, target: "_blank", rel: "noopener noreferrer", text: "題目頁" }), " 閱讀，把文字存成檔案後用 ", h("code", { text: `cpe import ${V.id} 檔案` }), " 匯入範例測資。"] : null)));
    this.paintBadges(); this.paintLadder();
    if (V.code === null) this.stmtBox.append(this.startCta());
  }
  async setLang(mode) {
    try { await post("/api/settings", { statement_lang: mode }); this.V = await get("/api/problem", { id: this.pid }); this.paintStatement(); }
    catch (e) { toast(e.message, "bad"); }
  }
  paintProblem() {
    const V = this.V;
    this.paintStatement();
    if (V.code === null) this.showStart(); else { this.startBox.hidden = true; this.edwrap.hidden = false; this.editor.setValue(V.code, V.lang); this.editor.setReadOnly(false); this.statusLine("已載入"); }
    // 初次載入也跑一次陷阱提醒（不提示解法，只列語法上的常見坑）
  }
  paintBadges() {
    const V = this.V; clear(this.head);
    this.head.append(h("span", { class: "pill", text: V.id }), h("span", { class: "stars", text: stars(V.difficulty) }), h("span", { class: "tag", text: V.topic || "" }),
      V.solved ? h("span", { class: "pill ok" }, icon("check"), V.review_stage === 3 || V.review_stage == null ? "精熟" : "已通過（待無提示重寫）") : null,
      V.exam ? h("span", { class: "pill bad", text: "考試中" }) : null,
      V.title_en ? h("span", { class: "muted small", text: V.title_en }) : null,
      V.has_english && !V.exam ? h("div", { class: "seg langseg", role: "group", "aria-label": "題目語言", title: "階段 0 中文 → 階段 1 中英對照 → 之後英文（考場是英文）" },
        [["auto", "自動"], ["zh", "中"], ["bi", "對照"], ["en", "EN"]].map(([k, t]) => h("button", { "aria-pressed": String(V.lang_setting === k), title: { auto: `自動（目前：${{ zh: "中文", bi: "中英對照", en: "English" }[V.lang_mode]}）`, zh: "中文", bi: "中英對照", en: "English" }[k], onclick: () => this.setLang(k) }, t))) : null);
  }
  paintLadder() { [...this.ladder.children].forEach((el, i) => el.classList.toggle("on", this.V.hint_level >= 0 && i <= this.V.hint_level)); }
  fuzz() {
    if (this.V.exam) { toast("考試中不能對拍。", "warn"); return; }
    const key = "cpe.brute." + this.pid;
    let saved = ""; try { saved = localStorage.getItem(key) || ""; } catch { /* 隱私模式 */ }
    const ta = h("textarea", { rows: 12, spellcheck: "false", "aria-label": "暴力解程式碼", placeholder: "# 最直白、一定對的解法（讀 stdin、寫 stdout）。慢沒關係。\n# 它必須先通過這題現有的所有測資，才會被拿來當標準答案。",
      style: { "font-family": "var(--mono)", width: "100%" } });
    ta.value = saved;
    const rounds = h("input", { type: "number", min: 20, max: 2000, value: 300, "aria-label": "嘗試次數", style: { width: "100px" } });
    const keep = h("input", { type: "checkbox", checked: true, id: "fuzzSave" });
    const out = h("div", { class: "mt", "aria-live": "polite" });
    let busy = false;
    const m = modal({ title: "對拍補測資", wide: true, body: h("div", { class: "col" },
      h("p", { class: "muted small", text: "官方只給範例時，通過範例不代表正確。貼上你的暴力解，系統會拿現有測資的輸入當種子，在原本的結構內變動數值（含邊界值），和你的解答對拍；不一致的輸入縮小後可存成新測資。" }),
      ta, h("div", { class: "row wrap" }, h("label", { class: "row gap-sm small" }, "嘗試次數", rounds), h("label", { class: "row gap-sm small", for: "fuzzSave" }, keep, "把差異存成測資")),
      h("p", { class: "muted xs", text: "它不知道題目的限制條件；極少數情況下變異出的輸入可能不合法，請自己確認後再保留。" }), out),
    actions: [{ label: "關閉" }, { label: "開始對拍", kind: "primary", keep: true, onClick: async (close) => {
      if (busy) return false; busy = true; clear(out); out.append(h("span", { class: "muted", text: "對拍中…（最多約一分鐘）" }));
      try {
        try { localStorage.setItem(key, ta.value); } catch { /* 隱私模式 */ }
        const r = await post("/api/fuzz", { id: this.pid, code: this.editor.getValue(), brute: ta.value, rounds: +rounds.value || 300, save: keep.checked });
        clear(out);
        out.append(h("div", { class: "muted small", text: `變異 ${r.tried} 組（暴力解自己跑不動而略過 ${r.skipped} 組）` }));
        if (!r.found.length) out.append(h("div", { class: "callout mt" }, icon("check"), h("span", { text: "沒有發現不一致。這只代表範例附近的變化沒問題，不代表一定正確。" })));
        r.found.forEach((f, i) => out.append(h("div", { class: "callout warn mt" }, icon("alert"), h("div", null, h("b", { text: `差異 ${i + 1}（${f.verdict}）` }),
          h("div", { class: "small" }, "輸入"), h("pre", { class: "small", text: f.input }), h("div", { class: "small" }, "暴力解"), h("pre", { class: "small", text: f.brute_out }), h("div", { class: "small" }, "你的解"), h("pre", { class: "small", text: f.sol_out })))));
        if (r.saved.length) { out.append(h("div", { class: "callout ok mt" }, icon("check"), h("span", { text: `已存成 ${r.saved.join("、")}。之後『執行測試』會一起跑。` }))); notify(); this.reloadView(); }
      } catch (e) { clear(out); out.append(h("div", { class: "callout bad" }, icon("x"), h("span", { text: e.message }))); }
      finally { busy = false; }
      return false;
    } }] });
  }
  async begin(lang) {
    try { this.V = await post("/api/new", { id: this.pid, lang }); this.paintProblem(); this.tab("code"); this.editor.focus(); notify(); }
    catch (e) { toast(e.message, "bad"); }
  }
  startCta() {   // 手機版：程式欄是隱藏的，所以在題目底部也放開始按鈕（桌面版 CSS 隱藏）
    return h("div", { class: "startcta" }, h("button", { class: "btn primary lg", onclick: () => this.begin("py") }, icon("code"), "讀完了，用 Python 開始"),
      h("button", { class: "btn ghost", onclick: () => this.begin("cpp") }, "改用 C++"));
  }
  showStart() {
    this.edwrap.hidden = true; this.res.hidden = true; this.startBox.hidden = false; clear(this.startBox);
    this.startBox.append(h("div", { class: "empty", style: { padding: "48px 20px" } }, icon("code", "xl"), h("h2", { text: "開始這題" }), h("p", { class: "muted", text: "先讀題，再建立解答檔。測資已經準備好了。" }),
      h("div", { class: "row wrap", style: { "justify-content": "center" } },
        h("button", { class: "btn lg primary", onclick: () => this.begin("py") }, icon("code"), "用 Python 開始"), h("button", { class: "btn lg", onclick: () => this.begin("cpp") }, icon("code"), "用 C++ 開始"))));
  }
  paintProbbar() {
    clear(this.probbar); const u = this.unit; if (!u) return;
    const all = [...u.drills, ...(u.gate?.problems || []).filter((p) => !u.drills.find((d) => d.id === p.id)), ...u.anchors.filter((a) => a.has_tests)];
    all.forEach((p) => this.probbar.append(h("button", { class: "pchip" + (p.id === this.pid ? " cur" : "") + (p.done ? " solved" : ""), role: "tab", "aria-selected": String(p.id === this.pid), title: p.title + (p.role === "檢核" ? "（檢核題）" : ""), onclick: () => go("/practice/" + p.id) }, p.id, p.done ? icon("check") : null)));
    this.probbar.hidden = all.length === 0;
  }
  paintUnit() {
    const u = this.unit; clear(this.unitBox); if (!u) return;
    this.unitBox.append(h("h3", { text: u.title }), h("p", { class: "muted small", text: u.goal }), h("h4", { class: "mt", text: "要學的" }), h("ul", { class: "small" }, u.learn.map((x) => h("li", null, inline(x)))),
      u.pitfalls.length ? [h("h4", { text: "常見陷阱" }), h("ul", { class: "small" }, u.pitfalls.map((x) => h("li", null, inline(x))))] : null,
      u.check.length ? [h("h4", { text: "自我檢查（不看資料回答）" }), h("ul", { class: "small" }, u.check.map((x) => h("li", null, inline(x))))] : null,
      u.read?.length ? [h("h4", { text: "要讀的章節" }), h("ul", { class: "small" }, u.read.map((x) => h("li", { text: x })))] : null);
  }

  // ---------- 編輯與儲存 ----------
  onEdit() { this.dirty = true; this.statusLine("未儲存…"); this.saveSoon(); }
  statusLine(t) { this.saveStat.textContent = t; }
  async save(manual) {
    if (this.V.code === null) return; const code = this.editor.getValue();
    try { await post("/api/save", { id: this.pid, code }); this.dirty = false; this.statusLine("已儲存 " + new Date().toLocaleTimeString("zh-TW", { hour12: false })); if (manual) toast("已儲存", "ok", 1200); }
    catch (e) { this.statusLine("儲存失敗"); if (manual) toast(e.message, "bad"); }
  }

  // ---------- 執行測試 ----------
  async run() {
    if (this.busy || this.V.code === null) return; this.busy = true; this.runBtn.disabled = true;
    const lab = this.runBtn.querySelector("span"); lab.textContent = "判題中…"; this.runBtn.prepend(h("i", { class: "spin" }));
    this.res.hidden = false; this.setRes("res"); clear(this.resBody); this.resBody.append(skeleton(3));
    const predicted = this.predict.value || undefined;
    try {
      const b = this.beh; b.runs++;
      const r = await post("/api/test", { id: this.pid, code: this.editor.getValue(), predicted,
        beh: { edits: b.edits, deletes: b.deletes, pastes: b.pastes, active_s: Math.round(b.active_s), max_pause_s: Math.round(b.max_pause_s), since_open_s: Math.round((Date.now() - b.opened) / 1000), runs: b.runs } }); this.dirty = false; this.lastResult = r; this.predicted = predicted;
      this.editor.clearMarks(); if (r.error_line) this.editor.mark("err", [r.error_line]); this.editor.mark("lint", (r.lint || []).map((x) => x.line));
      if (r.error_line) this.editor.mark("err", [r.error_line]);
      this.predict.value = ""; await this.reloadView(); this.paintRes(); notify();
      if (r.verdict === "AC" && !r.setup_error) toast(this.V.exam ? "通過（考試計分已記錄）" : "通過 🎉", "ok", 2200);
      if (r.exam_note) toast(r.exam_note, "", 5000);
    } catch (e) { clear(this.resBody); this.resBody.append(h("div", { class: "callout bad" }, icon("alert"), h("span", { text: e.message }))); }
    finally { this.busy = false; this.runBtn.disabled = false; this.runBtn.querySelector(".spin")?.remove(); lab.textContent = "執行測試"; }
  }
  paintRes() {
    const k = this.resK || "res"; const r = this.lastResult; clear(this.resBody);
    const nHints = (r?.lint?.length || 0) + (r?.static?.length || 0);
    const lintTab = this.resTabs.querySelector('[data-k="lint"]'); lintTab.textContent = "提醒" + (nHints ? ` (${nHints})` : "");
    if (k === "trace") return this.paintTrace();
    if (!r) { this.resBody.append(empty("play", "按「執行測試」看結果")); return; }
    if (k === "lint") {
      if (!r.lint?.length && !r.static?.length) { this.resBody.append(empty("check", "沒有偵測到常見陷阱。")); return; }
      const row = (x, msg) => h("li", null, h("button", { class: "li", onclick: () => this.editor.flash(x.line) }, icon("alert"), h("span", { class: "mono muted", text: "L" + x.line }), h("span", { class: "grow", text: msg })));
      if (r.lint?.length) this.resBody.append(h("p", { class: "muted small", text: "這些是『語法合法、但初學者最常踩』的寫法，不一定是你的錯誤原因。" }), h("ul", { class: "list" }, r.lint.map((x) => row(x, x.message))));
      if (r.static?.length) this.resBody.append(h("p", { class: "muted small", text: "靜態分析：常見的慢寫法與風險（只看程式碼，可能誤報）。" }), h("ul", { class: "list" }, r.static.map((x) => row(x, x.msg))));
      return;
    }
    if (r.setup_error) { this.resBody.append(h("div", { class: "callout warn" }, icon("alert"), h("span", { text: r.message }))); return; }
    const ok = r.verdict === "AC";
    this.resBody.append(h("div", { class: "verdict" }, h("span", { class: "badge " + (ok ? "AC" : "bad") }, icon(ok ? "check" : "x"), `${r.verdict} ${r.verdict_zh}`),
      this.predicted ? h("span", { class: "small " + (this.predicted === r.verdict ? "ok" : "warn"), text: this.predicted === r.verdict ? `你預測 ${this.predicted}，猜對了` : `你預測 ${this.predicted}，實際是 ${r.verdict}` }) : null));
    if (r.message && !ok) this.resBody.append(h("div", { class: "callout bad mt", dataset: { src: "output" } }, icon("alert"), h("div", null, h("span", { text: r.message }), r.error_line ? h("div", null, h("a", { href: "#", onclick: (e) => { e.preventDefault(); this.editor.flash(r.error_line); }, text: `跳到第 ${r.error_line} 行` })) : null)));
    this.resBody.append(h("div", { class: "cases" }, r.cases.map((c) => h("span", { class: "case " + c.verdict }, h("span", { text: c.name }), h("b", { text: c.verdict }), h("span", { class: "muted", text: `${c.seconds}s` })))));
    if (r.failing) this.resBody.append(this.failBlock(r));
    if (!ok && r.cause) this.resBody.append(h("div", { class: "callout warn mt" }, icon("alert"), h("div", null, h("b", { text: "可能的錯因：" + r.cause }), r.cause_advice ? h("div", { class: "small", text: r.cause_advice }) : null,
      h("div", { class: "xs muted", text: "這是規則判斷，可能分錯；錯誤本在指令列 cpe err。" }))));
    (r.behavior || []).forEach((b) => this.resBody.append(h("div", { class: "callout mt" }, icon("clock"), h("span", { text: b.msg }))));
    if (ok) this.resBody.append(this.nextCard(r));
    if (r.exam_note) this.resBody.append(h("div", { class: "callout mt" }, icon("clock"), h("span", { text: r.exam_note })));
    if (!ok && r.error_line && r.failing?.verdict === "RE") this.resBody.append(h("p", { class: "small muted mt", text: "提示：選取錯誤訊息或那一行，按「預期和實際不同」可以讓 AI 針對它發問。" }));
  }
  failBlock(r) {
    const f = r.failing; const exp = f.expected.replace(/\n+$/, "").split("\n"), act = (f.actual || "").replace(/\n+$/, "").split("\n");
    let first = -1; for (let i = 0; i < Math.max(exp.length, act.length); i++) { if ((exp[i] ?? "").trimEnd() !== (act[i] ?? "").trimEnd()) { first = i; break; } }
    const lines = (arr) => h("pre", null, arr.slice(0, 40).map((l, i) => h("span", { class: i === first ? "dl-bad" : "dl-ok", text: l || " " })));
    const box = h("div", { class: "mt", dataset: { src: "output" } },
      h("div", { class: "small muted", text: `第一個失敗的測資：${f.name}（選取下面的文字可以問 AI）` }),
      h("div", { class: "io" }, h("h4", { text: "輸入" }), h("pre", { text: f.input.length > 1500 ? f.input.slice(0, 1500) + "\n…" : f.input })),
      h("div", { class: "diff" }, h("div", null, h("h4", { text: "預期輸出" }), lines(exp)), h("div", null, h("h4", { text: "你的輸出" }), f.actual ? lines(act) : h("pre", { text: "（空）" }))));
    if (first >= 0 && f.verdict !== "TLE") box.append(h("p", { class: "small muted", text: `第一個差異在輸出的第 ${first + 1} 行。` }));
    if (f.verdict === "PE") box.append(h("div", { class: "callout warn" }, icon("alert"), h("span", { text: "內容相同，但空白或換行不同。檢查行尾空白、組間空行、小數位數。" })));
    if (f.verdict === "TLE") box.append(h("div", { class: "callout warn" }, icon("clock"), h("span", { text: "超過時間。估算一下複雜度：n 多大？有沒有巢狀迴圈可用前綴和／排序／dict 取代？" })));
    if (f.stderr?.trim()) box.append(h("div", { class: "io" }, h("h4", { text: "錯誤訊息" }), h("pre", { text: f.stderr.trim().slice(-600) })));
    return box;
  }
  nextCard(r) {
    const u = this.unit; const box = h("div", { class: "callout ok mt" }, icon("check"), h("div", { class: "grow" }, h("b", { text: r.info?.mastered ? "精熟！這題無提示通過。" : "通過。" }),
      r.review && r.review.stage != null && r.review.stage < 3 ? h("div", { class: "small", text: "因為用過提示，這題之後要『從空白檔、不看提示』重寫通過才算學會。" }) : null));
    const nxt = u ? [...u.drills, ...(u.gate?.problems || [])].find((p) => !p.done && p.id !== this.pid) : null;
    if (nxt && !this.V.exam) box.append(h("button", { class: "btn primary", onclick: () => go("/practice/" + nxt.id) }, "下一題：" + nxt.id, icon("chevron")));
    else if (!this.V.exam) box.append(h("a", { class: "btn", href: "#/home", text: "回到今日" }));
    return box;
  }

  // ---------- 追蹤 ----------
  async trace() {
    if (this.V.code === null) return; this.res.hidden = false; this.setRes("trace"); clear(this.resBody); this.resBody.append(skeleton(4));
    try { this.traceData = await post("/api/trace", { id: this.pid, code: this.editor.getValue() }); this.dirty = false; const t = this.traceData;
      this.traceText = t.steps.map((s) => `第${s.line}行 ${s.text} | ${Object.entries(s.vars).map(([k, v]) => k + "=" + v).join(", ")}`).join("\n"); this.paintTrace(); }
    catch (e) { clear(this.resBody); this.resBody.append(h("div", { class: "callout bad" }, icon("alert"), h("span", { text: e.message }))); }
  }
  paintTrace() {
    clear(this.resBody); const t = this.traceData; if (!t) { this.resBody.append(empty("list", "按「逐行追蹤」，逐行看每個變數怎麼變。先在心裡猜，再看答案。")); return; }
    this.resBody.append(h("p", { class: "small muted" }, "追蹤的輸入：", h("code", { text: t.input.slice(0, 60).replace(/\n/g, " ⏎ ") }), t.truncated ? `（只顯示前 ${t.steps.length} 步）` : "", t.error && !t.truncated ? `；結束於 ${t.error}` : "", " 選取任一列可以問 AI。"));
    const modeBtn = (k, label) => h("button", { class: "btn sm" + (this.traceView === k ? " primary" : ""), onclick: () => { this.traceView = k; this.paintTrace(); } }, label);
    this.resBody.append(h("div", { class: "row gap-sm", style: { "margin-bottom": "6px" } }, modeBtn("table", "表格"), modeBtn("viz", "圖像（一步一步看變數）")));
    if (this.traceView === "viz") {
      const steps = t.steps; const firstWithVars = Math.max(0, steps.findIndex((x) => Object.keys(x.vars).length)); const i = Math.min(this.vizStep ?? firstWithVars, steps.length - 1);
      const slider = h("input", { type: "range", min: 0, max: Math.max(steps.length - 1, 0), value: i, "aria-label": "追蹤的步驟", oninput: (e) => { this.vizStep = +e.target.value; this.paintTrace(); } });
      const s0 = steps[i];
      this.resBody.append(h("div", { class: "vz-step" }, h("button", { class: "btn sm", disabled: i <= 0, onclick: () => { this.vizStep = i - 1; this.paintTrace(); } }, "◀"), slider,
        h("button", { class: "btn sm", disabled: i >= steps.length - 1, onclick: () => { this.vizStep = i + 1; this.paintTrace(); } }, "▶"), h("span", { class: "small muted", text: `${i + 1}/${steps.length}` })),
      h("div", { class: "small mono mb" }, `第 ${s0.line} 行　${s0.text}`), renderStep(s0.vars, i > 0 ? steps[i - 1].vars : {}),
      h("p", { class: "xs muted mt", text: "有變動的格子會上色。比較複雜的物件（類別、很長的資料）會顯示原本的文字。" }));
      this.editor.flash(s0.line);
      return;
    }
    const tb = h("table", { class: "trace" }, h("thead", null, h("tr", null, h("th", { text: "行" }), h("th", { text: "程式" }), h("th", { text: "變數" }))),
      h("tbody", null, t.steps.map((s) => h("tr", { onclick: () => this.editor.flash(s.line) }, h("td", { text: s.line }), h("td", { text: s.text }), h("td", { text: Object.entries(s.vars).map(([k, v]) => `${k}=${v}`).join("，") })))));
    this.resBody.append(h("div", { dataset: { src: "trace" } }, tb));
  }

  // ---------- 提示階梯 ----------
  paintAi() {
    clear(this.aiBody);
    if (this.aiK === "ask") { this.aiBody.append(this.ask.listEl); return; }
    const V = this.V; const why = (i) => (V.exam ? "考試中鎖定" : i === 0 ? "" : V.attempts < 1 ? "先跑過一次測試" : i > Math.max(V.hint_level, 0) + 1 ? "要一級一級來" : i > V.hint_level && V.attempts_since_hint < 1 ? "先改一版再測試" : i === 4 && (!V.last_verdict || V.last_verdict === "AC") ? "最近一次要是失敗的" : "");
    this.aiBody.append(h("div", { class: "pad" }, h("p", { class: "muted small", text: "提示會讓這題之後需要『無提示重寫』。L0 只是釐清題意，不算提示。" })));
    LEVELS.forEach(([name, desc], i) => {
      const unlocked = i <= V.hint_level || (i === 0 && V.hint_level >= 0); const reason = why(i); const open = unlocked;
      const txt = this.hintTexts[i];
      this.aiBody.append(h("div", { class: "step" + (open ? " open" : "") + (!open && reason ? " locked" : "") }, h("div", { class: "lv", text: "L" + i }),
        h("div", { class: "grow" }, h("b", { text: name }), h("div", { class: "muted small", text: desc }),
          txt ? h("div", { class: "txt", text: txt }) : null,
          !txt ? h("div", { class: "mt" }, h("button", { class: "btn sm", disabled: !!reason && !unlocked, title: reason, onclick: () => this.getHint(i) }, icon(unlocked ? "eye" : "lock"), unlocked ? "查看" : reason ? "🔒 " + reason : "解鎖")) : null)));
    });
    this.aiBody.append(this.giveupBlock());
  }
  async getHint(i) {
    try { const r = await post("/api/hint", { id: this.pid, level: i }); this.hintTexts[i] = r.text; await this.reloadView(); this.paintAi(); }
    catch (e) { toast(e.message, "warn", 6000); }
  }
  giveupBlock() {
    const V = this.V; const box = h("div", { class: "pad" }, h("h4", { text: "真的卡住了？" }));
    if (!V.giveup_at) box.append(h("p", { class: "small muted", text: "放棄後要冷卻 24 小時才能看解法講解，之後還要從空白檔重寫。" }), h("button", { class: "btn danger sm", disabled: V.exam, onclick: async () => {
      if (!(await confirmDialog("放棄這題？", "冷卻 24 小時後才能看解法講解；看完之後必須從空白檔重寫並通過。", "放棄這題", "danger"))) return;
      try { await post("/api/giveup", { id: this.pid }); await this.reloadView(); toast("已記錄。睡一覺再回來。", "", 3000); this.paintAi(); } catch (e) { toast(e.message, "bad"); } } }, "放棄這題"));
    else if (V.now < V.unlock_at) box.append(h("div", { class: "callout warn" }, icon("lock"), h("span", { text: `冷卻中，${fmtDate(V.unlock_at)} 後可看解法講解。` })));
    else box.append(h("button", { class: "btn", onclick: async () => { try { const r = await post("/api/solution", { id: this.pid }); this.hintTexts.solution = r.text; this.paintAi(); } catch (e) { toast(e.message, "warn", 6000); } } }, icon("book"), "查看解法講解"),
      this.hintTexts.solution ? h("div", { class: "txt mt", style: { "white-space": "pre-wrap" } }, md(this.hintTexts.solution)) : null);
    return box;
  }

  // ---------- 引用定位 ----------
  locate(src, quote, line) {
    if (src === "code") { this.tab("code"); if (line) this.editor.flash(line); return; }
    if (src === "statement") { this.tab("stmt"); this.setLeft("stmt", this.t1); highlightText(this.stmtBox, quote); return; }
    this.tab("code"); const host = this.resBody.querySelector(`[data-src="${src}"]`); if (host) highlightText(host, quote);
  }
}
