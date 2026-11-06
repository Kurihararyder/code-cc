// 管理後台：班級總覽與作業。資料來自學生同步的摘要（只有題號與單元編號，沒有程式碼）。
import { h, icon, toast, drawer, confirmDialog } from "./dom.js";
import { post } from "./api.js";
import { empty } from "./widgets.js";
import { fmtT } from "./gate.js";
import { csvDownload } from "./admin.js";

const rpc = async (name, args) => (await post("/api/admin/rpc", { name, args: args || {} })).result;
const TRACKS = { py: "Python", cpp: "C++", verilog: "Verilog", tcl: "Tcl" };
const ago = (ts) => { if (!ts) return "從未"; const d = Math.floor((Date.now() / 1000 - ts) / 86400); return d < 1 ? "今天" : d + " 天前"; };
const lines = (t) => t.split(/[\n,;、\s]+/).map((x) => x.trim()).filter(Boolean);

export async function classView(body) {
  const rows = await rpc("admin_class_overview");
  const kpi = (v, l) => h("div", { class: "card kpi" }, h("div", { class: "v", text: String(v) }), h("div", { class: "l", text: l }));
  const idle = rows.filter((r) => !r.last_active || Date.now() / 1000 - r.last_active > 14 * 86400).length;
  const thisWeek = rows.filter((r) => (r.weekly[3] || 0) > 0).length;
  const f = { q: "", cohort: "" };
  const cohorts = [...new Set(rows.map((r) => r.cohort).filter(Boolean))].sort();
  const tbl = h("div", { class: "tablewrap" });
  const paint = () => {
    const sel = rows.filter((r) => (!f.cohort || r.cohort === f.cohort) && (!f.q || (r.student_id + r.name).toLowerCase().includes(f.q)));
    tbl.replaceChildren(sel.length ? h("table", { class: "tbl" }, h("thead", null, h("tr", null, ["學號", "姓名", "班級", "最後學習", "近四週活躍天數", "已解題", ...Object.values(TRACKS).map((t) => t + " 完成單元"), "逾期作業", "卡關"].map((x) => h("th", { text: x })))),
      h("tbody", null, sel.map((r) => h("tr", null, h("td", { class: "mono", text: r.student_id }), h("td", { text: r.name }), h("td", { text: r.cohort }), h("td", { text: ago(r.last_active) }),
        h("td", { class: "mono", text: r.weekly.join(" · ") }), h("td", { text: String(r.solved) }), ...Object.keys(TRACKS).map((k) => h("td", { text: String(r.tracks[k] || 0) })),
        h("td", null, r.overdue ? h("span", { class: "pill bad", text: String(r.overdue) }) : "—"), h("td", { class: "xs muted", text: r.stuck.map((s) => s.id).join("、") }))))) : empty("users", "沒有符合的學員"));
  };
  body.append(h("div", { class: "kpis mt" }, kpi(rows.length, "使用中的學員"), kpi(thisWeek, "本週有學習"), kpi(idle, "14 天沒學習"), kpi(rows.reduce((a, r) => a + r.overdue, 0), "逾期未完成（人次）")),
    h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", null, icon("users"), "班級總覽"),
      h("div", { class: "row wrap" }, h("input", { type: "search", placeholder: "搜尋學號／姓名", "aria-label": "搜尋", oninput: (e) => { f.q = e.target.value.trim().toLowerCase(); paint(); } }),
        h("select", { "aria-label": "班級", onchange: (e) => { f.cohort = e.target.value; paint(); } }, [h("option", { value: "", text: "全部班級" }), ...cohorts.map((c) => h("option", { value: c, text: c }))]),
        h("button", { class: "btn", onclick: () => csvDownload("class-overview.csv", [["學號", "姓名", "班級", "最後學習", "已解題", ...Object.values(TRACKS), "逾期作業"],
          ...rows.map((r) => [r.student_id, r.name, r.cohort, r.last_active ? new Date(r.last_active * 1000).toISOString().slice(0, 10) : "", r.solved, ...Object.keys(TRACKS).map((k) => r.tracks[k] || 0), r.overdue])]) }, "匯出 CSV"))), tbl));
  paint();
}

export async function assignView(body) {
  const list = await rpc("admin_assign_list");
  const wrap = h("div");
  const reload = async () => { wrap.replaceChildren(); body.replaceChildren(); await assignView(body); };
  const edit = (a) => {
    const f = Object.assign({ id: null, title: "", track: "verilog", units: [], problems: [], due_at: null, cohort: "" }, a || {});
    const title = h("input", { value: f.title, maxlength: 120, "aria-label": "標題", placeholder: "例：第 3 週 組合電路" });
    const track = h("select", { "aria-label": "軌道" }, Object.entries(TRACKS).map(([k, t]) => h("option", { value: k, text: t, selected: k === f.track })));
    const units = h("input", { value: f.units.join(", "), "aria-label": "單元", placeholder: "單元編號，如 2, 3" });
    const probs = h("input", { value: f.problems.join(", "), "aria-label": "題號", placeholder: "題號，如 v004, v005" });
    const due = h("input", { type: "date", value: f.due_at ? new Date(f.due_at).toISOString().slice(0, 10) : "", "aria-label": "期限" });
    const cohort = h("input", { value: f.cohort, "aria-label": "班級", placeholder: "留空＝全部班級" });
    drawer((close) => h("div", { class: "pad" }, h("h3", { text: f.id ? "編輯作業" : "新增作業" }),
      h("label", { class: "fld" }, "標題", title), h("label", { class: "fld" }, "軌道", track), h("label", { class: "fld" }, "要完成的單元", units),
      h("label", { class: "fld" }, "要通過的題目", probs), h("label", { class: "fld" }, "期限（當天 23:59）", due), h("label", { class: "fld" }, "班級", cohort),
      h("div", { class: "row mt" }, h("button", { class: "btn primary", onclick: async () => {
        const us = lines(units.value).map(Number), ps = lines(probs.value);
        if (!title.value.trim() || us.some((n) => !Number.isInteger(n) || n < 1) || (!us.length && !ps.length)) { toast("標題必填，且單元與題目至少要填一項（單元要是正整數）", "bad"); return; }
        try {
          const r = await rpc("admin_assign_save", { p_id: f.id, p_title: title.value.trim(), p_track: track.value, p_units: us, p_problems: ps, p_due: due.value ? new Date(due.value + "T23:59:59").toISOString() : null, p_cohort: cohort.value.trim(), p_archived: false });
          if (!r.ok) throw new Error("沒有儲存（至少要有一個單元或題目）");
          close(); toast("已儲存", "ok"); reload();
        } catch (e) { toast(e.message, "bad"); }
      } }, "儲存"), h("button", { class: "btn", onclick: close }, "取消"))));
  };
  const card = (a) => {
    const pct = a.total ? Math.round((100 * a.done) / a.total) : 0;
    return h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", { text: a.title }),
      h("div", { class: "row wrap" }, h("span", { class: "pill", text: TRACKS[a.track] }), a.cohort ? h("span", { class: "pill info", text: a.cohort }) : null,
        a.due_at ? h("span", { class: "pill " + (Date.parse(a.due_at) < Date.now() ? "bad" : "info"), text: "期限 " + fmtT(a.due_at).split(" ")[0] }) : null,
        h("button", { class: "btn", onclick: () => edit(a) }, "編輯"),
        h("button", { class: "btn", onclick: async () => { if (await confirmDialog("刪除這份作業？", "學生端會立刻看不到，無法復原。", "刪除")) { await rpc("admin_assign_delete", { p_id: a.id }); reload(); } } }, "刪除"))),
      h("p", { class: "small muted", text: [a.units.length ? "單元 " + a.units.join("、") : "", a.problems.length ? "題目 " + a.problems.join("、") : ""].filter(Boolean).join("；") }),
      h("div", { class: "barrow" }, h("span", { class: "bl", text: "完成" }), h("span", { class: "bar" }, h("i", { style: { width: pct + "%" } })), h("b", { text: `${a.done}/${a.total}` })),
      a.missing.length ? h("details", null, h("summary", { class: "small", text: `尚未完成（${a.missing.length}）` }), h("p", { class: "small", text: a.missing.map((m) => m.student_id + (m.name ? " " + m.name : "")).join("、") })) : null);
  };
  body.append(h("div", { class: "row mt" }, h("button", { class: "btn primary", onclick: () => edit() }, "＋ 新增作業"),
    h("span", { class: "muted small", text: "完成狀況來自學生最近一次同步；學生端打開首頁就會看到作業與倒數。" })),
    list.length ? list.map(card) : empty("list", "還沒有作業"), wrap);
}
