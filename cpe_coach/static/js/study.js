// 學習頁：洞察（記憶、知識點、錯誤、預測）、工坊（診斷與練習）、筆記、目標與匯出。
import { h, icon, clear, toast } from "./dom.js";
import { get, post, download } from "./api.js";
import { go } from "./router.js";
import { t } from "./i18n.js";
import { bars, empty, skeleton, kpi } from "./widgets.js";

const TABS = [["insights", "洞察"], ["lab", "工坊"], ["notes", "筆記"], ["goal", "目標"]];
const LEVEL_COLOR = ["var(--text-3)", "var(--warn)", "var(--accent)", "var(--ok)", "var(--ok)"];

export async function mountStudy(view, params) {
  const tab = TABS.some(([k]) => k === params[0]) ? params[0] : "insights";
  const body = h("div", { id: "studyBody" }, h("div", { class: "card pad" }, skeleton(5)));
  const tabs = h("div", { class: "seg", role: "tablist", "aria-label": t("學習") }, TABS.map(([k, label]) => h("button", { role: "tab", "aria-selected": String(k === tab), onclick: () => go("/study/" + k) }, t(label))));
  view.append(h("div", { class: "page" }, h("div", { class: "page-head" }, h("div", null, h("h1", { text: t("學習") }), h("p", { text: "記憶、知識點、診斷、練習、目標，都從你的紀錄算出來。" }))), tabs, body));
  try {
    const fn = { insights, lab, notes, goal }[tab];
    await fn(body);
  } catch (e) { clear(body); body.append(empty("alert", e.message)); }
}

const sec = (title, ...kids) => h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", { text: t(title) })), ...kids);
const muted = (text) => h("p", { class: "muted small", text });
const pill = (text, cls = "") => h("span", { class: "pill " + cls, text });

// ---------- 洞察 ----------
async function insights(body) {
  const D = await get("/api/insights");
  clear(body);
  const M = D.memory, now = D.week;
  body.append(h("div", { class: "kpis mt" }, kpi("clock", M.due.length, t("現在該複習")), kpi("check", M.cards, "納入記憶排程的題"), kpi("flame", now.active_days, t("最近 7 天") + "：練習天數"), kpi("target", D.prediction.expected, "預期答對題數（粗估）")));
  const dueList = M.due.length ? h("ul", { class: "list" }, M.due.map((d) => h("li", null, h("button", { class: "li", onclick: () => go("/practice/" + d.id) }, h("span", { class: "mono", text: d.id }), h("span", { class: "grow", text: d.title }), pill(`保留率 ${Math.round(100 * d.retention)}%`, d.retention < 0.7 ? "warn" : "info"))))) : muted(t("目前沒有到期的複習。"));
  body.append(sec("現在該複習", dueList, muted(M.personalized ? `已用你的 ${M.reviews} 次複習個人化（k=${M.k}）。` : `個人化還沒啟用（需要至少 ${M.need} 次複習，目前 ${M.reviews} 次），先用 FSRS-4.5 預設參數。`),
    h("h4", { class: "mt", text: t("未來 14 天的複習量") }), M.forecast.some((n) => n > 0) ? bars(M.forecast.map((n, i) => ({ label: i === 0 ? "今天" : `+${i}`, n, color: "var(--accent)" }))) : muted("未來 14 天沒有排定的複習。")));
  const lv = h("table", { class: "t" }, h("thead", null, h("tr", null, ["知識點", "層級", "P(會)", "保留率"].map((x) => h("th", { text: x === "知識點" || x === "層級" || x === "保留率" ? t(x) : x })))),
    h("tbody", null, D.mastery.filter((m) => m.touched || m.level > 0).map((m) => h("tr", null, h("td", { text: m.name }), h("td", null, h("span", { style: { color: LEVEL_COLOR[m.level] }, text: m.label })),
      h("td", { text: Math.round(100 * m.p_know) + "%" }), h("td", { text: m.retention == null ? "—" : Math.round(100 * m.retention) + "%" + (m.needs_review ? " ⚠" : "") })))));
  body.append(sec("知識點掌握", D.mastery.some((m) => m.touched) ? h("div", { class: "tablewrap" }, lv) : muted("解出第一題之後，這裡會顯示每個知識點的掌握程度。"), muted("P(會)：貝氏知識追蹤的推測；層級：接觸 → 理解 → 應用（2 題無提示）→ 變化（3 題無提示且隔天複習還對）。")));
  body.append(sec("下一題推薦", D.recommend.length ? h("ul", { class: "list" }, D.recommend.map((r) => h("li", null, h("button", { class: "li", onclick: () => go("/practice/" + r.id) }, h("span", { class: "mono", text: r.id }), h("span", { class: "grow", text: r.title }), pill(`成功率約 ${Math.round(100 * r.p_success)}%`, "info"))))) : muted("目前沒有可以推薦的題。"),
    muted("挑「推測一次通過的機率最接近 70%」的題：太簡單學不到、太難會挫折。難度是估計值。")));
  const E = D.errors;
  body.append(sec("錯誤本", E.total ? [bars(E.causes.slice(0, 6).map((c) => ({ label: c.cause, n: c.count, color: "var(--bad)" }))), E.advice ? h("div", { class: "callout mt" }, icon("bulb"), h("span", { text: E.advice })) : null, muted("分類是規則判斷，可能分錯；指令列 cpe err tag 可以修正。")] : muted("還沒有沒通過的紀錄。")));
  const hb = D.habits;
  body.append(sec("習慣與疲勞", hb.note ? muted(hb.note) : null, D.fatigue.map((f) => h("div", { class: "callout " + (f.level === "warn" ? "warn" : "") + " mt" }, icon("alert"), h("span", { text: f.msg }))), D.behavior.patterns.length ? muted("編輯行為（只記次數）：" + D.behavior.patterns.map((p) => `${p.id}×${p.count}`).join("、")) : null));
  body.append(sec("成就", h("div", { class: "chips" }, D.achievements.map((a) => h("span", { class: "pill " + (a.unlocked ? "ok" : ""), title: a.desc, text: (a.unlocked ? "✓ " : "· ") + a.name }))), muted("看做法的品質（無提示、回想、複習），不是刷題量；沒有「斷了就歸零」的連續紀錄。")));
  const P = D.prediction;
  body.append(sec("落點預測", bars(P.distribution.map((v, k) => ({ label: `${k} 題`, n: Math.round(100 * v), color: k >= 4 ? "var(--ok)" : "var(--accent)" }))), h("p", { class: "small", text: `預期答對 ${P.expected} 題；至少 4 題的機率約 ${Math.round(100 * P.p_at_least_4)}%。` }), muted(P.caveat)));
  body.append(sec("考試時間策略", D.strategy.advice.map((a) => h("p", { class: "small", text: "・" + a })), D.pressure && D.pressure.note ? muted(D.pressure.note) : null));
  body.append(sec("考前清單", h("ul", { class: "small" }, D.final.items.map((i) => h("li", { text: i.text })))));
  const X = D.experiment;
  body.append(sec("自我實驗", muted("用資料檢驗 FSRS 排程是不是比固定間隔好。開啟後約一半的題會改用固定間隔；資料不夠時不會下結論。"), h("p", { class: "small", text: X.conclusion }),
    h("button", { class: "btn sm", onclick: async () => { try { await post("/api/exp", { on: !X.enabled }); go("/study/insights"); } catch (e) { toast(e.message, "bad"); } } }, X.enabled ? "關閉實驗" : "開啟實驗")));
  if (D.coach_comments.length) body.append(sec("老師的留言", h("ul", { class: "small" }, D.coach_comments.map((c) => h("li", { text: `${c.from || "老師"}：${c.text}` })))));
}

// ---------- 工坊 ----------
async function lab(body) {
  const I = await get("/api/lab/index");
  clear(body);
  const area = h("div", null);
  const sel = (items, label) => h("select", { class: "input", "aria-label": label }, items.map(([v, txt]) => h("option", { value: v, text: txt })));
  const conceptOpts = Object.entries(I.concepts);
  // 適性診斷與知識點練習
  const quizBox = h("div", { "aria-live": "polite" });
  const showQ = (q, onAnswer) => {
    clear(quizBox);
    quizBox.append(h("p", { class: "q", text: q.q }), q.code ? h("pre", { class: "code", text: q.code }) : null, q.stdin ? muted("輸入：" + q.stdin.trim().replace(/\n/g, " ⏎ ")) : null,
      h("div", { class: "col" }, q.choices.map((c, i) => h("button", { class: "btn choice", onclick: () => onAnswer(i) }, h("b", { text: "ABCD"[i] + ". " }), h("span", { class: "pre", text: c })))));
  };
  const feedback = (r, next) => { quizBox.append(h("div", { class: "callout " + (r.correct ? "ok" : "bad") + " mt" }, icon(r.correct ? "check" : "x"), h("div", null, h("b", { text: r.correct ? "答對了" : "答案是 " + "ABCD"[r.answer] }), h("div", { class: "small", text: r.why }))), next); };
  const startCat = async () => {
    let r = await post("/api/lab/quiz/start", {}); let state = r.state;
    const ask = (q) => showQ(q, async (i) => {
      quizBox.querySelectorAll("button").forEach((b) => { b.disabled = true; });
      const a = await post("/api/lab/quiz/answer", { state, id: q.id, choice: i }); state = a.state;
      feedback(a, h("button", { class: "btn primary mt", onclick: () => { if (a.result) showResult(a.result); else ask(a.question); } }, a.result ? "看結果" : t("下一題")));
    });
    ask(r.question);
  };
  const showResult = (res) => { clear(quizBox); quizBox.append(h("h4", { text: `程度：${res.level}（答對 ${res.correct}/${res.answered}）` }), res.weak.length ? h("p", { text: "建議先補：" + res.weak.map((w) => `${w.name}（單元 ${w.unit}）`).join("、") }) : null, h("p", { text: res.why }), muted(res.caveat),
    h("button", { class: "btn mt", onclick: () => go("/course") }, "到課程地圖")); };
  const conceptSel = sel(conceptOpts, "知識點");
  const startPractice = async () => {
    const r = await post("/api/lab/quiz/practice", { concept: conceptSel.value, n: 5 }); let i = 0, right = 0;
    const next = () => { if (i >= r.questions.length) { clear(quizBox); quizBox.append(h("h4", { text: `${right}/${r.questions.length} 題答對` })); return; }
      const q = r.questions[i]; showQ(q, async (c) => { quizBox.querySelectorAll("button").forEach((b) => { b.disabled = true; }); const g = await post("/api/lab/grade", { id: q.id, choice: c }); right += g.correct ? 1 : 0; i++; feedback(g, h("button", { class: "btn primary mt", onclick: next }, t("下一題"))); }); };
    next();
  };
  body.append(sec("適性診斷", muted("最多 12 題，依你的答對情況調整難度，找出該從哪裡開始補。題目難度是我估的，結果是大略的建議。"), h("button", { class: "btn primary", onclick: () => startCat().catch((e) => toast(e.message, "bad")) }, t("開始診斷")),
    h("div", { class: "row wrap mt" }, h("span", { text: t("知識點練習") + "：" }), conceptSel, h("button", { class: "btn", onclick: () => startPractice().catch((e) => toast(e.message, "bad")) }, "開始")), quizBox));
  // 微課
  const lessonSel = sel(I.lessons.map((l) => [l.concept, `${l.title}（${l.minutes} 分）`]), "微課");
  const lessonOut = h("div", { class: "mt" });
  const showLesson = async () => { const L = await get("/api/lab/lesson", { concept: lessonSel.value }); clear(lessonOut); lessonOut.append(h("ul", null, L.points.map((p) => h("li", { text: p }))), h("pre", { class: "code", text: L.code }), muted("輸出：" + L.output), h("p", { class: "small" }, h("b", { text: "常見陷阱：" }), L.pitfall)); };
  body.append(sec("微課", h("div", { class: "row wrap" }, lessonSel, h("button", { class: "btn", onclick: () => showLesson().catch((e) => toast(e.message, "bad")) }, "看")), lessonOut));
  // 示範題與空白練習
  const wSel = sel(I.worked.map((w) => [w.id, w.title]), "示範題"); const lvl = h("input", { type: "number", min: 0, max: 3, value: 1, class: "input", "aria-label": "留白步數", style: { width: "70px" } });
  const wOut = h("div", { class: "mt" });
  const showWorked = async () => {
    const W = await get("/api/lab/worked", { id: wSel.value, level: lvl.value }); const F = W.faded; clear(wOut);
    wOut.append(h("p", { text: W.problem }), F.given.map((s) => h("div", null, muted(s.say), h("pre", { class: "code", text: s.code }))));
    if (F.blank.length) { const ta = h("textarea", { class: "input code", rows: 6, "aria-label": "你寫的程式", placeholder: "接在上面程式後面的部分" }); const res = h("div", { "aria-live": "polite" });
      wOut.append(F.blank.map((s) => muted("（請你寫）" + s.say)), ta, h("button", { class: "btn primary mt", onclick: async () => { const r = await post("/api/lab/faded/check", { id: W.id, level: F.level, answer: ta.value }); clear(res); res.append(r.ok ? h("div", { class: "callout ok" }, icon("check"), "通過所有測資") : h("div", null, h("div", { class: "callout bad" }, icon("x"), "還沒通過"), r.results.filter((x) => !x.ok).slice(0, 2).map((x) => h("pre", { class: "code", text: `輸入 ${JSON.stringify(x.input)}\n預期 ${JSON.stringify(x.expected)}\n得到 ${JSON.stringify(x.got)} ${x.error}` })), r.solution ? h("details", null, h("summary", { text: "看參考解" }), h("pre", { class: "code", text: r.solution })) : null)); } }, t("檢查")), res); }
  };
  body.append(sec("示範題與空白練習", muted("先看完整示範（留白 0），再逐步增加留白：自己寫最後一步、最後兩步…。"), h("div", { class: "row wrap" }, wSel, h("span", { text: "留白步數" }), lvl, h("button", { class: "btn", onclick: () => showWorked().catch((e) => toast(e.message, "bad")) }, "開始")), wOut));
  // Parsons
  const pSel = sel(I.worked.map((w) => [w.id, w.title]), "排序題"); const pOut = h("div", { class: "mt" });
  const showParsons = async () => {
    const P = await get("/api/lab/parsons", { id: pSel.value, seed: 1 }); clear(pOut);
    const rows = P.lines.map((l) => ({ ...l, use: true })); const list = h("div", { class: "col" }); const res = h("div", { "aria-live": "polite" });
    const paint = () => { clear(list); rows.forEach((r, i) => list.append(h("div", { class: "row gap-sm" }, h("input", { type: "checkbox", checked: r.use, "aria-label": "使用這一行", onchange: (e) => { r.use = e.target.checked; } }),
      h("button", { class: "btn sm", "aria-label": "上移", disabled: i === 0, onclick: () => { [rows[i - 1], rows[i]] = [rows[i], rows[i - 1]]; paint(); } }, "▲"), h("button", { class: "btn sm", "aria-label": "下移", disabled: i === rows.length - 1, onclick: () => { [rows[i + 1], rows[i]] = [rows[i], rows[i + 1]]; paint(); } }, "▼"), h("pre", { class: "code grow", style: { margin: 0 }, text: r.text })))); };
    paint();
    pOut.append(h("p", { text: P.problem }), muted("把行排成正確的程式；有些行是多餘的，取消勾選就是不用。縮排是程式的一部分。"), list, h("button", { class: "btn primary mt", onclick: async () => { const r = await post("/api/lab/parsons/check", { id: P.id, seed: 1, order: rows.filter((x) => x.use).map((x) => x.id) }); clear(res); res.append(h("div", { class: "callout " + (r.ok ? "ok" : "bad") }, icon(r.ok ? "check" : "x"), r.ok ? "通過所有測資" : "還沒通過，再調整看看")); } }, t("檢查")), res);
  };
  body.append(sec("排序題", h("div", { class: "row wrap" }, pSel, h("button", { class: "btn", onclick: () => showParsons().catch((e) => toast(e.message, "bad")) }, "開始")), pOut));
  // 找 bug
  const bSel = sel(I.bugs.map((b) => [b.id, b.title]), "找 bug"); const bOut = h("div", { class: "mt" });
  const showBug = async () => {
    const B = await get("/api/lab/bug", { id: bSel.value }); clear(bOut); const res = h("div", { "aria-live": "polite" });
    bOut.append(h("p", { text: B.statement }), muted("這個程式在某些輸入會答錯或當掉。點你覺得有問題的那一行。"), h("div", { class: "col" }, B.code.split("\n").map((ln, i) => h("button", { class: "btn sm line", onclick: async () => { const r = await post("/api/lab/bug/check", { id: B.id, line: i + 1 }); clear(res); res.append(h("div", { class: "callout " + (r.found ? "ok" : "warn") }, icon(r.found ? "check" : "alert"), r.found ? "找到了！" + r.why : "不是第 " + (i + 1) + " 行，再看看。")); } }, h("span", { class: "mono muted", text: String(i + 1).padStart(2) + "  " }), h("span", { class: "mono", text: ln })))), res);
  };
  body.append(sec("找 bug", h("div", { class: "row wrap" }, bSel, h("button", { class: "btn", onclick: () => showBug().catch((e) => toast(e.message, "bad")) }, "開始")), bOut));
  // 預測輸出
  const pdSel = sel(I.predict.map((p) => [p.id, p.id]), "預測輸出"); const pdOut = h("div", { class: "mt" });
  const showPredict = async () => {
    const P = await get("/api/lab/predict", { id: pdSel.value }); clear(pdOut); const ta = h("textarea", { class: "input code", rows: 2, "aria-label": "你預測的輸出" }); const res = h("div", { "aria-live": "polite" });
    pdOut.append(h("pre", { class: "code", text: P.code }), P.stdin ? muted("輸入：" + P.stdin.trim()) : null, ta, h("button", { class: "btn primary mt", onclick: async () => { const r = await post("/api/lab/predict/check", { id: P.id, answer: ta.value }); clear(res); res.append(h("div", { class: "callout " + (r.correct ? "ok" : "bad") }, icon(r.correct ? "check" : "x"), h("div", null, r.correct ? "對了" : "不一樣", h("pre", { class: "code", text: "實際輸出：\n" + r.output })))); } }, t("檢查")), res);
  };
  body.append(sec("預測輸出", muted("先在心裡（或紙上）寫出答案，再看實際輸出。這是訓練「讀懂程式」最快的方法之一。"), h("div", { class: "row wrap" }, pdSel, h("button", { class: "btn", onclick: () => showPredict().catch((e) => toast(e.message, "bad")) }, "開始")), pdOut));
  // 解法比較
  const cSel = sel(I.compare.map((c) => [c.id, c.title]), "解法比較"); const cOut = h("div", { class: "mt" });
  const showCompare = async () => { const C = await get("/api/lab/compare", { id: cSel.value }); clear(cOut); cOut.append(h("p", { text: C.problem }), C.approaches.map((a) => h("div", { class: "card pad mt" }, h("b", { text: `${a.name}（${a.complexity}）` }), muted(a.note), h("pre", { class: "code", text: a.code })))); };
  body.append(sec("解法比較", h("div", { class: "row wrap" }, cSel, h("button", { class: "btn", onclick: () => showCompare().catch((e) => toast(e.message, "bad")) }, "看")), cOut));
  // 術語表
  const q = h("input", { type: "search", class: "input", placeholder: "例如 subsequence、連續", "aria-label": t("搜尋") }); const gOut = h("div", { class: "mt" });
  const doSearch = async () => { const r = await get("/api/lab/glossary", { q: q.value }); clear(gOut); gOut.append(h("ul", { class: "list" }, r.items.map((x) => h("li", { class: "small" }, h("b", { text: x.en }), "　" + x.zh + (x.note ? "　" + x.note : ""))))); };
  q.addEventListener("input", () => { doSearch().catch(() => {}); });
  body.append(sec("英文題目術語表", q, gOut)); doSearch().catch(() => {});
  body.append(area);
}

// ---------- 筆記 ----------
async function notes(body) {
  clear(body);
  const kind = h("select", { class: "input", "aria-label": "種類" }, [["think", t("思路")], ["recall", t("回想")], ["reflect", t("反思")]].map(([v, x]) => h("option", { value: v, text: x })));
  const prob = h("input", { class: "input", placeholder: "題號（可省略，例如 d001）", "aria-label": "題號", style: { width: "180px" } });
  const text = h("textarea", { class: "input", rows: 4, "aria-label": "筆記內容", placeholder: "回想：不看程式，寫下解法大綱、為什麼、複雜度。反思：這週最卡的是什麼？" });
  const out = h("div", { "aria-live": "polite" }); const list = h("div", { class: "mt" });
  const reload = async () => { const r = await get("/api/notes"); clear(list); list.append(r.notes.length ? h("ul", { class: "list" }, r.notes.map((n) => h("li", { class: "small" }, h("b", { text: `[${n.note_kind}] ` }), n.problem ? h("span", { class: "mono", text: n.problem + " " }) : null, n.text.slice(0, 160)))) : muted("還沒有筆記。")); };
  body.append(sec("寫筆記", h("div", { class: "row wrap" }, kind, prob), text, h("button", { class: "btn primary mt", onclick: async () => { try { const r = await post("/api/notes/add", { kind: kind.value, text: text.value, problem: prob.value.trim() || undefined }); text.value = ""; clear(out); out.append(h("div", { class: "callout ok" }, icon("check"), r.compare ? h("div", null, "已記下。對照這題的關鍵洞察：" + r.compare.insight, h("div", { class: "small", text: r.compare.check.message + "（" + r.compare.check.note + "）" })) : "已記下。")); await reload(); } catch (e) { toast(e.message, "bad"); } } }, t("送出")), out));
  const ep = h("input", { class: "input", placeholder: "題號（要有內建提示的題，例如 uva10009）", "aria-label": "題號", style: { width: "260px" } }); const et = h("textarea", { class: "input", rows: 4, "aria-label": "你的解釋" }); const eo = h("div", { "aria-live": "polite" });
  body.append(sec("自我解釋", muted(t("用你自己的話解釋這題的解法") + "。有 AI 金鑰時由 AI 評分，否則用關鍵詞比對（只能看有沒有提到重點，看不懂對不對）。"), ep, et, h("button", { class: "btn primary mt", onclick: async () => { try { const r = await post("/api/explain", { problem: ep.value.trim(), text: et.value }); clear(eo); eo.append(h("div", { class: "callout" }, icon("bulb"), h("div", null, h("b", { text: `評分（${r.mode}）：${r.score}` }), h("div", { class: "small", text: r.message }), r.missed && r.missed.length ? h("div", { class: "small", text: "可能漏掉：" + r.missed.join("、") }) : null, muted(r.note))));  } catch (e) { toast(e.message, "bad"); } } }, t("送出")), eo));
  body.append(sec("最近的筆記", list)); await reload();
}

// ---------- 目標與匯出 ----------
async function goal(body) {
  const D = await get("/api/insights"); clear(body);
  const G = D.goal;
  const date = h("input", { type: "date", class: "input", "aria-label": "目標日期", value: G.set ? G.date : "" }); const n = h("input", { type: "number", class: "input", min: 1, max: 2000, "aria-label": "目標題數", value: G.set ? G.target : 40, style: { width: "100px" } });
  body.append(sec("設定目標", h("div", { class: "row wrap" }, h("span", { text: "在" }), date, h("span", { text: "之前累積解出" }), n, h("span", { text: "題" }), h("button", { class: "btn primary", onclick: async () => { try { await post("/api/goal/set", { date: date.value, problems: +n.value }); go("/study/goal"); } catch (e) { toast(e.message, "bad"); } } }, t("設定目標")))));
  if (G.set) {
    const f = G.forecast_days;
    body.append(sec("目標", h("div", { class: "kpis" }, kpi("target", `${G.solved}/${G.target}`, "已解出／目標"), kpi("clock", G.days_left, "剩幾天"), kpi("flame", G.pace_per_week, "你最近的速度（題／週）"), kpi("chart", G.need_per_week == null ? "—" : G.need_per_week.toFixed(1), t("每週需要") + "（題）")),
      h("p", { text: G.message }), f && f.possible ? h("p", { class: "small", text: `${t("完成日期預測")}（還要幾天，10%／50%／90%）：${f.p10}／${f.p50}／${f.p90}` }) : null, G.daily_minutes ? h("p", { class: "small", text: `平均每題約 ${G.minutes_per_problem} 分鐘 → 為了趕上，平均每天約 ${G.daily_minutes} 分鐘。` }) : null));
  }
  const W = D.week, Mo = D.month;
  body.append(sec("最近 7 天", h("p", { class: "small", text: `練習 ${W.active_days} 天、約 ${W.minutes} 分鐘；新解出 ${W.new_solved} 題；複習通過 ${W.reviews_passed}/${W.reviews}；用提示 ${W.hints} 次；筆記 ${W.notes} 則。` }),
    h("p", { class: "small muted", text: `最近 30 天：練習 ${Mo.active_days} 天；新解出 ${Mo.new_solved} 題。` })));
  const dl = (path, name) => h("button", { class: "btn", onclick: async () => { try { await download(path, name); } catch (e) { toast(e.message, "bad"); } } }, icon("save"), name);
  body.append(sec("匯出", muted("Anki 卡片、xAPI 學習紀錄、給老師的 HTML 報告（只含統計數字，不含程式碼與題目文字）。"), h("div", { class: "row wrap" }, dl("/api/export/anki", "cpe-anki.tsv"), dl("/api/export/xapi", "cpe-xapi.json"), dl("/api/export/report", "cpe-report.html"))));
  const ct = h("textarea", { class: "input", rows: 3, "aria-label": "老師的留言", placeholder: "貼上老師的留言（一行一則）" }); const from = h("input", { class: "input", placeholder: "老師的名字", "aria-label": "老師的名字", style: { width: "160px" } });
  body.append(sec("教練模式", muted("把報告傳給老師，老師的留言貼在這裡（或用 cpe coach import 匯入檔案）。"), h("div", { class: "row wrap" }, from), ct, h("button", { class: "btn mt", onclick: async () => { try { const r = await post("/api/coach/import", { from: from.value, comments: ct.value.split("\n").filter((x) => x.trim()).map((x) => ({ text: x })) }); ct.value = ""; toast(`已匯入 ${r.imported} 則留言`, "ok"); } catch (e) { toast(e.message, "bad"); } } }, "匯入留言")));
  body.append(sec("提醒", muted(D.reminder.due ? `現在有 ${D.reminder.due} 題到期。要每天自動提醒：在終端機執行 cpe remind install（會列出各系統的設定方式；加 --apply 才會真的安裝）。` : "目前沒有到期的複習。每天自動提醒：cpe remind install。")));
}
