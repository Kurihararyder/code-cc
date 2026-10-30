import { h, icon, clear, fmtDate } from "./dom.js";
import { get } from "./api.js";
import { kpi, heat, bars, skeleton, empty } from "./widgets.js";

const VZ = { AC: "通過", WA: "答案錯誤", PE: "格式錯誤", TLE: "超過時間", RE: "執行錯誤", CE: "語法錯誤" };
const VC = { AC: "var(--ok)", WA: "var(--bad)", PE: "var(--warn)", TLE: "var(--warn)", RE: "var(--bad)", CE: "var(--text-3)" };

export async function mountStats(view) {
  view.append(h("div", { class: "page" }, h("div", { class: "card pad" }, skeleton(5))));
  let s; try { s = await get("/api/stats"); } catch (e) { clear(view); view.append(h("div", { class: "page" }, empty("alert", e.message))); return; }
  clear(view);
  const rows = (o) => Object.entries(o).sort((a, b) => b[1] - a[1]).map(([k, n]) => ({ label: VZ[k] || k, n, color: VC[k] }));
  const rt = s.review_attempts;
  const page = h("div", { class: "page" }, h("div", { class: "page-head" }, h("div", null, h("h1", { text: "學習統計" }), h("p", { text: "用客觀指標取代「我覺得我會了」。" }))),
    h("div", { class: "kpis" }, kpi("check", s.counts.solved, "已通過"), kpi("target", s.counts.mastered, "精熟", "ok"), kpi("flame", s.streak, "連續天數"), kpi("chart", s.attempts_total, "累計提交")),
    h("div", { class: "grid-2 mt" },
      h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", { text: "最近 24 週" })), heat(s.heatmap)),
      h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", { text: "自我校準" })),
        h("dl", { class: "dl" }, h("dt", { text: "無提示重寫通過率" }), h("dd", { text: rt ? `${s.review_clean_passes}/${rt}（${Math.round((100 * s.review_clean_passes) / rt)}%）` : "尚無資料" }),
          h("dt", { text: "預測準確度" }), h("dd", { text: s.predict_total ? `${s.predict_correct}/${s.predict_total}（${Math.round((100 * s.predict_correct) / s.predict_total)}%）` : "尚無資料" }),
          h("dt", { text: "AI 詢問" }), h("dd", { text: s.asks ? `${s.asks} 次（引用全數驗證 ${s.asks_verified} 次）` : "尚無資料" }),
          h("dt", { text: "放棄" }), h("dd", { text: `${s.giveups} 次` }), h("dt", { text: "外部 AI" }), h("dd", { text: `${s.external_ai} 次` })))),
    h("div", { class: "grid-3 mt" },
      h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", { text: "判題結果（累計）" })), Object.keys(s.verdicts_total).length ? bars(rows(s.verdicts_total)) : empty("chart", "還沒有提交")),
      h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", { text: "判題結果（本週）" })), Object.keys(s.verdicts_week).length ? bars(rows(s.verdicts_week)) : empty("chart", "本週還沒有提交")),
      h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", { text: "提示使用" })), Object.keys(s.hints_by_level).length ? bars(Object.entries(s.hints_by_level).map(([k, n]) => ({ label: "L" + k, n, color: "var(--warn)" }))) : empty("bulb", "沒用過提示 👏"))),
    h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", { text: "考試紀錄" })),
      s.exams.length ? h("table", { class: "t" }, h("thead", null, h("tr", null, ["日期", "類型", "答對", "罰時"].map((t) => h("th", { text: t })))),
        h("tbody", null, [...s.exams].reverse().map((e) => h("tr", null, h("td", { class: "mono", text: e.date }), h("td", { text: { mock: "全真模擬", short: "短測驗", weekly: "每週重寫", gate: "單元檢核" }[e.kind] || e.kind }), h("td", { text: `${e.solved}/${e.total}` }), h("td", { text: `${e.penalty} 分` }))))) : empty("target", "還沒有考試紀錄。到「今日」按「模擬考」試試。")));
  view.append(page);
}
