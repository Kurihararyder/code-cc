// 共用小元件與考試流程（首頁、課程、練習都會用到）。
import { h, icon, modal, toast, confirmDialog, fmtDur, VERDICT_ZH } from "./dom.js";
import { post } from "./api.js";
import { go } from "./router.js";

export const notify = () => window.dispatchEvent(new CustomEvent("cpe:changed"));

export function progress(done, total, color) {
  return h("div", { class: "progress", role: "progressbar", "aria-valuemin": 0, "aria-valuemax": total, "aria-valuenow": done },
    h("i", { style: { "--p": (total ? (100 * done) / total : 0) + "%", "--c": color || "var(--accent)" } }));
}
export function kpi(iconName, value, label, tone) {
  return h("div", { class: "card kpi" }, h("div", { class: "row gap-sm" }, icon(iconName), h("span", { class: "muted small", text: label })),
    h("div", { class: "v" + (tone ? " " + tone : ""), text: String(value) }));
}
export function skeleton(lines = 3) { return h("div", { class: "col" }, Array.from({ length: lines }, (_, i) => h("div", { class: "skel", style: { height: i === 0 ? "26px" : "14px", width: `${100 - i * 12}%` } }))); }
export function empty(iconName, text, action) { return h("div", { class: "empty" }, icon(iconName), h("div", { text }), action || null); }

const level = (n) => (n <= 0 ? 0 : n <= 2 ? 1 : n <= 5 ? 2 : n <= 9 ? 3 : 4);
export function heat(data) {
  const first = new Date(data[0].d + "T00:00:00"); const pad = (first.getDay() + 6) % 7;   // 週一為第一列
  const cells = [];
  for (let i = 0; i < pad; i++) cells.push(h("i", { style: { visibility: "hidden" } }));
  data.forEach((d) => cells.push(h("i", { dataset: { l: level(d.n) }, title: `${d.d}：${d.n} 次提交`, role: "img", "aria-label": `${d.d}：${d.n} 次提交` })));
  return h("div", null, h("div", { class: "heat" }, cells),
    h("div", { class: "legend mt" }, "少", [0, 1, 2, 3, 4].map((l) => h("i", { class: "heatleg", style: { background: `var(--heat${l})` } })), "多"));
}

export function bars(rows, color) {
  const max = Math.max(1, ...rows.map((r) => r.n));
  return h("div", { class: "bars" }, rows.map((r) => h("div", { class: "bar-row" }, h("span", { text: r.label }),
    h("div", { class: "tr" }, h("i", { style: { "--p": (100 * r.n) / max + "%", "--c": r.color || color || "var(--accent)" } })), h("span", { class: "muted", text: String(r.n) }))));
}

export function verdictTone(v) { return v === "AC" ? "ok" : "bad"; }

// ---- 考試流程 ----
export async function startGate(unit) {
  const g = unit.gate; if (!g) return;
  const desc = g.type === "mock" ? `模擬考（${g.kind === "short" ? "3 題 90 分鐘" : "7 題 3 小時"}），至少答對 ${g.need} 題` : `${g.minutes} 分鐘、${g.problems.length} 題，至少答對 ${g.need} 題`;
  const ok = await confirmDialog("開始單元檢核？", `${desc}。\n\n規則：從空白檔開始、AI 詢問與提示全部鎖定、時間到之後的提交不計分。準備好再開始。`, "開始檢核", "primary");
  if (!ok) return;
  try { await post("/api/gate"); notify(); toast("檢核開始，加油！", "ok"); go("/home"); } catch (e) { toast(e.message, "bad", 8000); }
}
export function startMockDialog() {
  const kinds = [["short", "短測驗", "3 題・90 分鐘"], ["mock", "全真模擬", "7 題・3 小時・ICPC 計分"], ["weekly", "每週重寫", "從空白檔重寫 3 題舊題・60 分鐘"]];
  const box = h("div", { class: "col" }, h("p", { class: "muted small", text: "只會出已有測資的題目（內建練習題或你匯入過的題）。考試期間 AI 與提示全部鎖定。" }),
    kinds.map(([k, t, d]) => h("button", { class: "li card", style: { padding: "14px 16px" }, onclick: async () => { try { await post("/api/mock", { kind: k }); m.close(); notify(); toast("考試開始", "ok"); go("/home"); } catch (e) { toast(e.message, "bad", 8000); } } },
      icon("target", "lg"), h("div", { class: "grow" }, h("b", { text: t }), h("div", { class: "muted small", text: d })), icon("chevron"))));
  const m = modal({ title: "開始模擬考", body: box });
}
export async function finishExam() {
  const ok = await confirmDialog("交卷？", "交卷後這場考試就結束，成績會被記錄。", "交卷", "primary"); if (!ok) return;
  try {
    const r = await post("/api/exam/finish"); const s = r.summary; notify();
    const rows = s.problems.map((pid) => { const d = s.detail[pid]; return h("tr", null, h("td", { class: "mono", text: pid }), h("td", null, d.ac_min != null ? h("span", { class: "ok", text: `✓ 第 ${d.ac_min} 分鐘` }) : h("span", { class: "muted", text: "—" })), h("td", { text: d.wrong ? `錯 ${d.wrong} 次` : "" })); });
    modal({ title: s.solved >= (s.gate?.need ?? 99) ? "🎉 交卷完成" : "交卷完成", wide: false,
      body: h("div", { class: "col" }, h("div", { class: "row" }, h("div", { class: "kpi", style: { padding: 0 } }, h("div", { class: "v", text: `${s.solved}/${s.total}` }), h("div", { class: "l", text: "答對題數" })), h("div", { class: "kpi", style: { padding: 0 } }, h("div", { class: "v", text: String(s.penalty) }), h("div", { class: "l", text: "罰時（分鐘）" }))),
        r.message ? h("div", { class: "callout " + (r.message.startsWith("✅") || r.message.startsWith("🎓") ? "ok" : "warn") }, h("span", { text: r.message })) : null,
        h("table", { class: "t" }, h("thead", null, h("tr", null, h("th", { text: "題目" }), h("th", { text: "結果" }), h("th", { text: "" }))), h("tbody", null, rows)),
        h("p", { class: "muted small", text: "考後檢討：現在 AI 詢問與提示已解鎖，沒做出的題目可以走提示階梯。" })),
      actions: [{ label: "回到今日", kind: "primary", onClick: () => { go("/home"); } }] });
  } catch (e) { toast(e.message, "bad", 8000); }
}
export function examPanel(exam) {
  const left = Math.max(0, exam.left);
  return h("div", { class: "card examcard pad mt" },
    h("div", { class: "row wrap" }, icon("clock", "xl"), h("div", { class: "grow" }, h("h2", { text: exam.gate ? "單元檢核進行中" : "考試進行中" }), h("div", { class: "muted small", text: "AI 詢問與提示已鎖定。時間到之後的提交不計分。" })),
      h("div", { class: "timer", id: "examBig", "data-left": left, text: fmtDur(left) }),
      h("button", { class: "btn primary", onclick: finishExam }, "交卷")),
    h("div", { class: "chips mt" }, exam.problems.map((p) => h("button", { class: "pchip" + (p.solved ? " solved" : ""), onclick: () => go("/practice/" + p.id) },
      p.id, p.solved ? icon("check") : (p.wrong ? h("span", { class: "bad", text: "✗" + p.wrong }) : null)))));
}
