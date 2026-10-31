// 「考試」頁：歷屆場次、整場模擬、成績分布、單字本。
import { h, icon, clear, toast, modal, confirmDialog, stars } from "./dom.js";
import { get, post } from "./api.js";
import { go } from "./router.js";
import { skeleton, empty, examPanel, startMockDialog, notify, bars } from "./widgets.js";
import { dictUrl } from "./ask.js";


export async function mountExam(view) {
  view.append(h("div", { class: "page" }, h("div", { class: "card pad" }, skeleton(5))));
  const paint = async () => {
    let P, V, st, C;
    try { [P, V, st, C] = await Promise.all([get("/api/past"), get("/api/vocab"), get("/api/state"), get("/api/cpe")]); } catch (e) { clear(view); view.append(h("div", { class: "page" }, empty("alert", e.message))); return; }
    clear(view); view.append(build(P, V.words, st.exam, paint, C));
  };
  await paint();
  const onChange = () => paint();
  window.addEventListener("cpe:changed", onChange);
  const t = setInterval(() => { const el = document.getElementById("examBig"); const top = document.getElementById("examLeft"); if (el && top) el.textContent = top.textContent; }, 1000);
  return () => { window.removeEventListener("cpe:changed", onChange); clearInterval(t); };
}

function build(P, words, exam, repaint, C) {
  const page = h("div", { class: "page" });
  page.append(h("div", { class: "page-head" }, h("div", null, h("h1", { text: "考試" }), h("p", { text: "歷屆場次、整場模擬、單字本。考場是 3 小時 7 題，ICPC 計分（罰時 20 分鐘）。" })),
    h("div", { class: "row wrap" }, h("button", { class: "btn", onclick: () => importDialog(repaint) }, icon("list"), "匯入歷屆清單"), h("button", { class: "btn primary", onclick: startMockDialog }, icon("target"), "開始模擬考"))));
  if (exam) page.append(examPanel(exam));

  const allReady = P.exams.filter((e) => e.complete).length;
  page.append(h("div", { class: "callout mt" }, icon("help"), h("div", null,
    h("b", { text: "關於歷屆題目資料" }),
    h("div", { class: "small", text: "內建資料只包含研究報告明確列出的場次與答對率（沒有題目文字，也沒有測資；題目有版權，不能內建）。要整場模擬，需要你把場次清單與題目文字匯入：先『匯入歷屆清單』，再在各題按『貼上題目』（題目文字裡的 Sample Input／Output 會自動變成測資）。" }),
    h("div", { class: "small", text: P.exams.length ? `目前有題目資料的 ${P.exams.filter((e) => e.problems.length).length} 場，其中 ${allReady} 場已可整場模擬。` : "目前沒有任何場次。" }))));

  page.append(cpeCard(C, repaint));
  P.exams.filter((e) => e.problems.length).forEach((e) => page.append(examCard(e, repaint, !!exam)));
  const bare = P.exams.filter((e) => !e.problems.length);
  if (bare.length) page.append(h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", null, icon("chart"), "只有統計數字的場次")),
    h("p", { class: "muted small", text: "研究報告只給了這些場次的平均答對題數，沒有列出題目。用『匯入歷屆清單』補上題目後，會變成可以整場模擬的場次。" }),
    h("div", { class: "row wrap" }, bare.map((e) => h("span", { class: "pill info", text: `${e.date}　平均 ${e.avg_solved ?? "—"} 題` })))));

  const total = P.distribution ? Object.entries(P.distribution).sort((a, b) => +a[0] - +b[0]) : [];
  page.append(h("div", { class: "grid-2 mt" },
    h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", { text: "歷年考生答對題數分布（2015–2024）" })),
      bars(total.map(([k, v]) => ({ label: `${k} 題`, n: +v, color: +k >= 4 ? "var(--ok)" : "var(--accent)" }))),
      h("p", { class: "muted xs mt", text: "數字是占考生的 %。交卷後會顯示你的成績落在哪個位置。來源：研究報告整理的官方統計。" })),
    h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", { text: "近期各場平均答對題數" })),
      P.trend.length ? h("table", { class: "t" }, h("thead", null, h("tr", null, h("th", { text: "場次" }), h("th", { text: "平均答對" }))),
        h("tbody", null, [...P.trend].reverse().map((t) => h("tr", null, h("td", { class: "mono", text: t.date }), h("td", { text: t.avg.toFixed(2) + " 題" }))))) : empty("chart", "沒有資料"))));

  page.append(vocabCard(words, repaint));
  return page;
}

const STATUS = { ac: ["ok", "✓"], wrong: ["bad", "✗"], open: ["", ""] };

// CPE 原題：社群整理的一星 49／二星 15／歷屆 31 題。題目文字不在這個程式裡，按鈕才從 GitHub 下載到你的電腦並轉成題目與範例測資。
function cpeCard(C, repaint) {
  const bar = h("div", { class: "muted small", hidden: true, role: "status", "aria-live": "polite" });
  let filter = { q: "", only: "all" };
  const btn = h("button", { class: "btn" + (C.ready ? "" : " primary"), onclick: async () => {
    btn.disabled = true; const old = btn.textContent; bar.hidden = false; bar.textContent = "連線到 GitHub 下載中…";
    try {
      let j = await post("/api/cpe/import", { force: false });
      while (j.state === "download" || j.state === "convert") {
        bar.textContent = j.state === "download" ? "從 GitHub 下載中…" : `轉換中 ${j.done}/${j.total}　${j.current || ""}`;
        await new Promise((r) => setTimeout(r, 700));
        j = await get("/api/cpe/progress");
      }
      if (j.state === "error") throw new Error(j.error);
      const r = j.report, bad = r.failed.length;
      toast(`匯入 ${r.imported} 題（範例測資 ${r.samples} 組）` + (r.skipped ? `；${r.skipped} 題本來就有` : "") + (bad ? `；${bad} 題失敗` : "") + (r.changed.length ? `；${r.changed.length} 題的 PDF 和驗證時不同` : ""), bad || r.changed.length ? "warn" : "ok", 8000);
      bar.hidden = true; notify(); repaint();
    } catch (e) { bar.hidden = true; toast(e.message, "bad", 10000); btn.disabled = false; btn.textContent = old; }
  } }, icon("refresh"), C.ready ? "再匯入（補沒有的）" : "從 GitHub 匯入");
  const row = (p) => h("li", { dataset: { cpe: p.id } }, h("button", { class: "li", disabled: !p.has_tests, onclick: () => go("/practice/" + p.id) },
    h("span", { class: "status" + (p.solved ? " done" : "") }, p.solved ? icon("check") : null), h("span", { class: "mono", text: p.id }), h("span", { class: "grow", text: p.title }),
    p.tags && p.tags.length ? h("span", { class: "muted xs cpe-tags", text: p.tags.slice(0, 3).join("・") }) : null,
    !p.has_tests ? h("span", { class: "tag", text: p.no_pdf ? "該 repo 沒有 PDF，需貼上題目" : "尚未匯入" }) : null));
  const match = (p) => (!filter.q || `${p.id} ${p.title} ${(p.tags || []).join(" ")}`.toLowerCase().includes(filter.q))
    && (filter.only === "all" || (filter.only === "todo" && !p.solved) || (filter.only === "ready" && p.has_tests && !p.solved) || (filter.only === "solved" && p.solved) || (filter.only === "missing" && !p.has_tests));
  const lists = h("div", null);
  const paint = () => {
    clear(lists);
    C.sets.forEach((g) => {
      const rows = g.problems.filter(match);
      lists.append(h("details", { class: "mt", open: !!filter.q || filter.only !== "all" || (g.key === "one" && g.ready > 0) }, h("summary", { class: "small" }, h("b", { text: g.name }), `　${g.count} 題　可練 ${g.ready}　已通過 ${g.solved}` + (rows.length !== g.count ? `　（符合 ${rows.length}）` : "")),
        rows.length ? h("ul", { class: "list" }, rows.map(row)) : h("p", { class: "muted small", text: "沒有符合的題目" })));
    });
  };
  const search = h("input", { type: "search", class: "input", placeholder: "搜尋題號、標題或類型（例如 bfs、字串）", "aria-label": "搜尋 CPE 原題", style: { "max-width": "300px" }, oninput: (e) => { filter.q = e.target.value.trim().toLowerCase(); paint(); } });
  const pick = h("select", { class: "input", "aria-label": "篩選", onchange: (e) => { filter.only = e.target.value; paint(); } },
    [["all", "全部"], ["todo", "還沒通過"], ["ready", "已匯入、還沒通過"], ["solved", "已通過"], ["missing", "尚未匯入"]].map(([v, t]) => h("option", { value: v, text: t })));
  paint();
  return h("section", { class: "card pad mt", id: "cpeSets" },
    h("div", { class: "card-h" }, h("h3", null, icon("target"), "CPE 原題"), h("span", { class: "pill " + (C.ready ? "ok" : "info"), text: `可練 ${C.ready}/${C.total}` }), h("span", { class: "grow" }), btn),
    bar,
    h("p", { class: "muted small", text: "社群整理的 CPE 題單：一星題、二星題、歷屆試題（UVa 原題，英文）。題目文字的著作權屬於各題作者，不放在這個程式裡：按『從 GitHub 匯入』才會把 PDF 下載到你的電腦，只供你自己練習，轉成題目文字與範例測資（原 PDF 也留在工作區的 statements/）。範例只是最基本的測資，通過後請自己再補邊界測資。" }),
    h("div", { class: "row wrap gap-sm mt" }, search, pick),
    lists,
    h("p", { class: "muted xs mt" }, "清單來源：", h("a", { href: C.source.repo, target: "_blank", rel: "noopener noreferrer" }, "LuckyPigeon/CPE_Previous_Questions ", icon("external")), `（提交 ${String(C.source.commit).slice(0, 7)}）。每題的類型、先修單元與提示是我依題意寫的，沒有官方核對。算式、表格、圖擷取得不好的地方，練習頁有「開啟原 PDF 對照」。`));
}

function examCard(e, repaint, busy) {
  const rows = e.problems.map((p) => h("tr", null,
    h("td", { class: "mono", text: String(p.order) }),
    h("td", null, p.title, p.uva ? h("span", { class: "muted xs", text: ` · UVA ${p.uva}${p.uva_verified === false ? "（題號待核對）" : ""}` }) : h("span", { class: "muted xs", text: " · 無 UVA 題號" })),
    h("td", { class: "stars", text: p.stars ? stars(p.stars) : "—" }),
    h("td", { text: p.accuracy != null ? p.accuracy + "%" : "—" }),
    h("td", null, p.solved ? h("span", { class: "pill ok", text: "已解出" }) : p.has_tests ? h("span", { class: "pill info", text: "有測資" }) : p.has_statement ? h("span", { class: "pill warn", text: "沒有範例" }) : h("span", { class: "pill", text: "缺題目" }),
      p.has_statement && !p.english ? h("span", { class: "pill warn", text: "非英文", title: "考場是英文題目" }) : null),
    h("td", null, h("div", { class: "row gap-sm" },
      h("button", { class: "btn sm", onclick: () => statementDialog(p, repaint) }, p.has_statement ? "更新題目" : "貼上題目"),
      p.has_tests ? h("button", { class: "btn sm ghost", onclick: () => go("/practice/" + p.id) }, "練習") : null))));
  const start = async (partial) => {
    const ok = await confirmDialog(`開始 ${e.date} 這場？`, `180 分鐘，${partial ? e.ready : e.count} 題，ICPC 計分，AI 與提示全部鎖定。\n\n準備好再開始。`, "開始", "primary");
    if (!ok) return;
    try { await post("/api/past/start", { date: e.date, partial }); notify(); toast("考試開始", "ok"); go("/exam"); } catch (err) { toast(err.message, "bad", 9000); }
  };
  return h("section", { class: "card pad mt" },
    h("div", { class: "card-h" }, h("h3", null, icon("book"), `${e.date} 場`), e.avg_solved != null ? h("span", { class: "pill info", text: `平均答對 ${e.avg_solved} 題` }) : null,
      e.complete ? h("span", { class: "pill ok", text: "可整場模擬" }) : h("span", { class: "pill warn", text: `${e.ready}/${e.count} 題有測資` }), e.solved ? h("span", { class: "pill accent", text: `已解 ${e.solved}` }) : null,
      h("span", { class: "grow" }), e.complete ? h("button", { class: "btn primary sm", disabled: busy, title: busy ? "已有進行中的考試" : "", onclick: () => start(false) }, icon("play"), "開始整場") : h("button", { class: "btn sm", disabled: !e.ready || busy, onclick: () => start(true), title: busy ? "已有進行中的考試" : e.ready ? "" : "至少要有一題有測資" }, "只出有測資的題目")),
    h("div", { class: "tablewrap" }, h("table", { class: "t" }, h("thead", null, h("tr", null, ["#", "題目", "星等", "全體答對率", "狀態", ""].map((t) => h("th", { text: t })))), h("tbody", null, rows))),
    e.source ? h("p", { class: "muted xs mt", text: "資料來源：" + e.source }) : null);
}

function importDialog(repaint) {
  const ta = h("textarea", { rows: 10, placeholder: "date,order,uva,title,accuracy\n2020-10-20,1,10050,Hartals,37.94", "aria-label": "歷屆清單", spellcheck: "false", style: { "font-family": "var(--mono)", width: "100%" } });
  const out = h("div", { class: "small mt", "aria-live": "polite" });
  const m = modal({ title: "匯入歷屆清單", wide: true, body: h("div", { class: "col" },
    h("pre", { class: "small", style: { "white-space": "pre-wrap", margin: 0 }, text: "每行一題，欄位用逗號或 Tab 分隔：\ndate,order,uva,title,accuracy\n- order 是該場第幾題（1–7）；uva 不知道就留空；accuracy 是全體答對率（%）可留空\n- 另外可用一行記錄該場平均：# 2020-10-20 avg=1.09\n可以直接從 Excel／Google 試算表複製貼上。" }),
    ta, out),
  actions: [{ label: "取消" }, { label: "匯入", kind: "primary", keep: true, onClick: async () => {
    try {
      const r = await post("/api/past/import", { text: ta.value });
      toast(`匯入 ${r.exams} 場、${r.problems} 題` + (r.errors.length ? `（${r.errors.length} 行有問題）` : ""), r.errors.length ? "warn" : "ok", 6000);
      if (r.errors.length) { out.className = "small mt warn"; out.textContent = r.errors.slice(0, 5).join("\n"); out.style.whiteSpace = "pre-wrap"; repaint(); return false; }
      m.close(); repaint(); notify();
    } catch (e) { out.className = "small mt bad"; out.style.whiteSpace = "pre-wrap"; out.textContent = e.message; return false; }
  } }] });
}

function statementDialog(p, repaint) {
  const ta = h("textarea", { rows: 14, placeholder: "貼上這題的英文題目全文（含 Sample Input／Sample Output）", "aria-label": "題目文字", spellcheck: "false", style: { "font-family": "var(--mono)", width: "100%" } });
  const file = h("input", { type: "file", accept: ".txt,.md,.html,.htm,text/plain,text/html", "aria-label": "選擇題目檔", onchange: async (e) => { const f = e.target.files[0]; if (f) ta.value = await f.text(); } });
  const out = h("div", { class: "small mt", "aria-live": "polite" });
  const m = modal({ title: `${p.title}（${p.id}）`, wide: true, body: h("div", { class: "col" },
    h("p", { class: "muted small", text: "貼上你自己取得的題目文字。系統會把 Sample Input／Sample Output 變成測資（只有範例，沒有官方完整測資；通過範例不代表一定正確，請另外用 cpe addtest 補自己的測資）。" }),
    file, ta, out),
  actions: [{ label: "取消" }, { label: "儲存", kind: "primary", keep: true, onClick: async () => {
    if (!ta.value.trim()) { out.className = "small mt warn"; out.textContent = "請先貼上題目文字"; return false; }
    try {
      const r = await post("/api/past/statement", { id: p.id, text: ta.value });
      toast(`已儲存。範例 ${r.samples} 組` + (r.english ? "" : "；這份題目不是英文（比照考場模式不會出這題）"), r.samples ? (r.english ? "ok" : "warn") : "warn", 7000);
      m.close(); repaint(); notify();
    } catch (e) { out.className = "small mt bad"; out.textContent = e.message; return false; }
  } }] });
}

function vocabCard(words, repaint) {
  const csv = () => {
    const rows = [["word", "count", "problems", "note"], ...words.map((w) => [w.word, w.count, (w.problems || []).join(" "), (w.note || "").replace(/\n/g, " ")])];
    const text = rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
    const a = h("a", { href: URL.createObjectURL(new Blob(["﻿" + text], { type: "text/csv" })), download: "vocab.csv" }); document.body.append(a); a.click(); a.remove();
  };
  return h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", null, icon("book"), "單字本"), h("span", { class: "pill", text: `${words.length} 個` }), h("span", { class: "grow" }),
    words.length ? h("button", { class: "btn sm", onclick: csv }, "匯出 CSV") : null),
  h("p", { class: "muted small", text: "在題目文字上雙擊一個英文單字 → 跳出的選單可以『查字典』或『加入單字本』。" }),
  words.length ? h("ul", { class: "list" }, words.map((w) => h("li", null, h("div", { class: "li" }, h("b", { class: "mono", text: w.word }), h("span", { class: "grow muted small", text: [w.count > 1 ? `查過 ${w.count} 次` : "", (w.problems || []).join("、"), w.note].filter(Boolean).join(" · ") }),
    h("a", { class: "btn sm ghost", href: dictUrl(w.word), target: "_blank", rel: "noopener noreferrer" }, "字典 ", icon("external")),
    h("button", { class: "btn sm ghost icon", "aria-label": `刪除 ${w.word}`, onclick: async () => { try { await post("/api/vocab/remove", { word: w.word }); repaint(); } catch (e) { toast(e.message, "bad"); } } }, icon("x")))))) : empty("book", "還沒有單字。"));
}
