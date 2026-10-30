import { h, icon, clear, fmtDate } from "./dom.js";
import { get } from "./api.js";
import { stars } from "./dom.js";
import { go } from "./router.js";
import { kpi, heat, bars, skeleton, empty } from "./widgets.js";

const VZ = { AC: "通過", WA: "答案錯誤", PE: "格式錯誤", TLE: "超過時間", RE: "執行錯誤", CE: "語法錯誤", MLE: "記憶體超過" };
const VC = { AC: "var(--ok)", WA: "var(--bad)", PE: "var(--warn)", TLE: "var(--warn)", RE: "var(--bad)", CE: "var(--text-3)", MLE: "var(--bad)" };

export async function mountStats(view) {
  view.append(h("div", { class: "page" }, h("div", { class: "card pad" }, skeleton(5))));
  let s, cal, wk; try { [s, cal, wk] = await Promise.all([get("/api/stats"), get("/api/calibration"), get("/api/weakness")]); } catch (e) { clear(view); view.append(h("div", { class: "page" }, empty("alert", e.message))); return; }
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
    weakCard(wk),
    calibration(cal),
    h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", { text: "考試紀錄" })),
      s.exams.length ? h("table", { class: "t" }, h("thead", null, h("tr", null, ["日期", "類型", "答對", "罰時", ""].map((t) => h("th", { text: t })))),
        h("tbody", null, [...s.exams].reverse().map((e) => h("tr", null, h("td", { class: "mono", text: e.date }), h("td", { text: { mock: "全真模擬", short: "短測驗", weekly: "每週重寫", gate: "單元檢核" }[e.kind] || e.kind }), h("td", { text: `${e.solved}/${e.total}` }), h("td", { text: `${e.penalty} 分` }), h("td", { class: "small muted", text: e.percentile ? `超過約 ${e.percentile.beats}% 考生` : (e.past ? "歷屆 " + e.past : "") }))))) : empty("target", "還沒有考試紀錄。到「考試」頁開始一場。")));
  view.append(page);
}

function calibration(c) {
  const lab = { "比標示難": "bad", "比標示簡單": "ok", "接近標示": "" };
  return h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", { text: "難度校準：這些題對你實際多難" }), c.enough ? h("span", { class: "pill info", text: `速度係數 ×${c.factor}` }) : null),
    c.rows.length ? [
      h("p", { class: "muted small", text: "用你『到第一次通過為止』的實際投入（工作分鐘 + 每多一次嘗試 4 分 + 每次提示 6 分）換算成星等，和題目標示（官方答對率或我的估計）並排。資料點少、也受當天狀態影響，只當參考。" + (c.note ? " " + c.note : "") }),
      h("div", { class: "row wrap small mb" }, Object.entries(c.by_star).map(([k, v]) => h("span", { class: "pill", text: `標示 ${stars(+k)}：${v.n} 題，中位數 ${v.median} 分（預設 ${v.prior}）` }))),
      h("div", { class: "tablewrap" }, h("table", { class: "t" }, h("thead", null, h("tr", null, ["題目", "標示", "對你", "投入", ""].map((t) => h("th", { text: t })))),
        h("tbody", null, c.rows.slice(0, 12).map((r) => h("tr", null, h("td", null, h("span", { class: "mono", text: r.id }), " ", r.title), h("td", { text: `${stars(r.listed)}${r.source === "official" ? "（官方）" : ""}` }), h("td", { text: stars(r.mine) }),
          h("td", { class: "small", text: `${r.effort_min} 分・${r.attempts} 次・${r.hints} 提示` }), h("td", null, h("span", { class: "pill " + (lab[r.label] || ""), text: r.label }))))))),
    ] : empty("chart", "解出幾題之後，這裡會顯示每題對你的實際難度。"));
}

const LV = { weak: ["bad", "弱點"], watch: ["warn", "留意"], ok: ["ok", "穩"], unknown: ["", "資料不足"] };
export function weakRows(wk) {
  return h("div", { class: "col" }, wk.families.filter((r) => r.n).map((r) => {
    const [tone, label] = LV[r.level] || ["", ""];
    return h("div", { class: "weakrow" }, h("span", { class: "wname", text: r.name }), h("span", { class: "pill " + tone, text: label }),
      h("div", { class: "tr", title: `分數 ${r.score}（越高越卡）` }, h("i", { style: { "--p": Math.round(100 * r.score) + "%", "--c": tone === "bad" ? "var(--bad)" : tone === "warn" ? "var(--warn)" : "var(--ok)" } })),
      h("span", { class: "muted xs wmeta", text: `${r.n} 題・首次通過 ${Math.round(100 * r.first_try_rate)}%・提示 ${r.avg_hints}` }));
  }));
}
export function weakSuggest(wk) {
  return wk.suggestions.length ? h("div", { class: "mt" }, h("h4", { text: "建議加練" }), h("ul", { class: "list" }, wk.suggestions.map((w) => h("li", null, h("button", { class: "li", onclick: () => go("/practice/" + w.id) },
    h("span", { class: "mono", text: w.id }), h("span", { class: "grow", text: w.title }), h("span", { class: "tag", text: w.family_name }), h("span", { class: "stars", text: stars(w.difficulty) }))))))
    : (wk.flagged.length ? h("p", { class: "muted small mt", text: "這些主題目前沒有可練的未完成題。可以到『考試』頁匯入更多歷屆題。" }) : null);
}
function weakCard(wk) {
  return h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", { text: "主題弱點" }), wk.weak.length ? h("span", { class: "pill bad", text: `${wk.weak.length} 個弱點` }) : null),
    wk.problems_seen ? [h("p", { class: "muted small", text: "依你每題的失敗次數、提示、放棄與重練失敗算出『卡關程度』，每個主題至少要有 3 題紀錄才會下結論。今日計畫會自動多排弱主題的題。" }), weakRows(wk), weakSuggest(wk)]
      : empty("chart", wk.note || "還沒有紀錄。"));
}
