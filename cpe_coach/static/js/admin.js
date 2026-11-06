// 管理後台（只有管理員看得到；伺服器端仍會逐項驗證管理員身分）。
import { h, icon, clear, toast, modal, drawer, confirmDialog, debounce } from "./dom.js";
import { post, get } from "./api.js";
import { skeleton, empty } from "./widgets.js";
import { fmtT } from "./gate.js";
import { CLOUD, loadCloud } from "./account.js";

const rpc = async (name, args) => (await post("/api/admin/rpc", { name, args: args || {} })).result;
const fn = (body) => post("/api/admin/fn", body);
const STATUS = { ok: ["使用中", "ok"], inactive: ["待開通", "warn"], expired: ["已到期", "bad"], not_started: ["尚未開始", "info"], no_profile: ["無資料", "bad"] };
const day = (s) => (s ? fmtT(s).split(" ")[0] : "不限");
const dateVal = (s) => { if (!s) return ""; const d = new Date(s); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
const startOf = (v) => (v ? new Date(v + "T00:00:00").toISOString() : null);
const endOf = (v) => (v ? new Date(v + "T23:59:59").toISOString() : null);
const lines = (t) => t.split(/[\n,;]+/).map((x) => x.trim()).filter(Boolean);
const ago = (ts) => { if (!ts) return "—"; const m = Math.round((Date.now() / 1000 - ts) / 60); return m < 1 ? "剛剛" : m < 60 ? m + " 分鐘前" : m < 1440 ? Math.round(m / 60) + " 小時前" : Math.round(m / 1440) + " 天前"; };

function csvDownload(name, rows) {
  // 試算表公式注入：學員可控的欄位（姓名、備註、回報內容）若以 = + - @ 開頭，Excel 會當成公式執行；前面補一個單引號
  const esc = (v) => { v = v == null ? "" : String(v); if (/^[=+\-@\t\r]/.test(v) && !/^-?\d+(\.\d+)?$/.test(v)) v = "'" + v; return /[",\n\r]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
  const blob = new Blob(["﻿" + rows.map((r) => r.map(esc).join(",")).join("\r\n")], { type: "text/csv;charset=utf-8" });
  const a = h("a", { href: URL.createObjectURL(blob), download: name }); document.body.append(a); a.click(); a.remove();
}
const sw = (checked, onchange, label) => h("label", { class: "switch" }, h("input", { type: "checkbox", checked, onchange: (e) => onchange(e.target.checked) }), h("span", { class: "sw" }), label ? h("span", { text: label }) : null);

const TABS = [["overview", "總覽", "chart"], ["users", "學員帳號", "users"], ["insights", "學習分析", "target"], ["network", "授權與網路", "lock"], ["ai", "AI 與金鑰", "sparkle"], ["release", "版本與公告", "bulb"], ["reports", "題目回報", "alert"], ["audit", "稽核紀錄", "list"]];

export async function mountAdmin(view, params) {
  if (!CLOUD.is_admin) { view.append(h("div", { class: "page" }, empty("lock", "只有管理員可以使用"))); return; }
  const tab = params[0] || "overview";
  const body = h("div", { class: "admin-body" });
  view.append(h("div", { class: "page wide" }, h("div", { class: "page-head" }, h("div", null, h("h1", null, icon("shield"), " 管理後台"), h("p", { text: "靜宜大學 晶片設計學士學位學程 · CPE 練功系統" }))),
    h("div", { class: "tabs admin-tabs", role: "tablist" }, TABS.map(([k, t, ic]) => h("button", { role: "tab", "aria-selected": String(k === tab), onclick: () => { location.hash = "#/admin/" + k; } }, icon(ic), t))), body));
  body.append(h("div", { class: "card pad mt" }, skeleton(6)));
  try { clear(body); await ({ overview, users, insights, network, ai, release, reports, audit }[tab] || overview)(body); } catch (e) { clear(body); body.append(empty("alert", e.message)); }
}

// ---------------- 總覽 ----------------
async function overview(body) {
  const [o, bad, ai, exp] = await Promise.all([rpc("admin_overview"), rpc("admin_audit", { p_limit: 8, p_action: "login" }), rpc("admin_ai_usage", { p_days: 1 }), rpc("admin_expiring", { p_days: 14 })]);
  const an = await rpc("admin_anomalies");
  const kpi = (v, l, ic, cls = "") => h("div", { class: "card kpi" }, icon(ic), h("div", { class: "v " + cls, text: String(v) }), h("div", { class: "l", text: l }));
  body.append(h("div", { class: "kpis mt" }, kpi(o.students, "學員帳號", "users"), kpi(o.active, "目前可使用", "check", "ok"), kpi(o.pending, "待開通", "clock", o.pending ? "warn" : ""), kpi(o.expired, "授權已到期", "alert", o.expired ? "bad" : "")),
    h("div", { class: "kpis mt" }, kpi(o.expiring_7d, "7 天內到期", "clock", o.expiring_7d ? "warn" : ""), kpi(o.logins_24h, "24 小時登入次數", "code"), kpi(o.denied_24h, "24 小時被拒絕", "lock", o.denied_24h ? "bad" : ""), kpi(o.ai_allowed, "已授權 AI 的學員", "sparkle")),
    h("div", { class: "grid2 mt" },
      h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", { text: "班級／屆別" })),
        o.cohorts.length ? h("ul", { class: "list" }, o.cohorts.map((c) => h("li", { class: "li static" }, h("span", { class: "grow", text: c.cohort || "（未分班）" }), h("b", { text: c.n + " 人" })))) : empty("users", "還沒有學員，先到「學員帳號」批次新增。")),
      h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", { text: "AI 使用（24 小時）" }), h("span", { class: "muted small", text: `${o.ai_calls_24h} 次 · 近 7 天 ${o.ai_tokens_7d.toLocaleString()} tokens` })),
        ai.length ? h("ul", { class: "list" }, ai.slice(0, 8).map((a) => h("li", { class: "li static" }, h("span", { class: "grow mono", text: a.student_id }), h("span", { text: `${a.calls} 次` })))) : empty("sparkle", "最近沒有人使用 AI。"))),
    (an.multi_ip.length || an.denied.length || an.open_reports) ? h("section", { class: "card pad mt anomaly" }, h("div", { class: "card-h" }, h("h3", null, icon("alert"), "需要留意")),
      h("ul", { class: "list" }, an.multi_ip.map((a) => h("li", { class: "li static" }, h("span", { class: "mono", text: a.student_id }), h("span", { class: "warn", text: `24 小時內從 ${a.ips} 個不同 IP 登入：${a.list.join("、")}（可能帳號外流）` }))),
        an.denied.map((a) => h("li", { class: "li static" }, h("span", { class: "mono", text: a.student_id }), h("span", { class: "bad", text: `1 小時內被拒絕 ${a.n} 次` }))),
        an.open_reports ? h("li", { class: "li static" }, h("a", { href: "#/admin/reports", text: `${an.open_reports} 則題目回報還沒處理` })) : null)) : null,
    exp.length ? h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", null, icon("clock"), "即將到期或剛到期（14 天內）"),
      h("button", { class: "btn sm primary", onclick: async () => { if (!(await confirmDialog("延長授權", `把這 ${exp.length} 位的授權都延長 30 天？`, "延長"))) return; for (const u of exp) { const base = u.valid_until && new Date(u.valid_until) > new Date() ? new Date(u.valid_until) : new Date(); base.setDate(base.getDate() + 30); await rpc("admin_update_user", { p_id: u.id, p: { valid_until: base.toISOString(), active: true } }); } toast("已延長 30 天", "ok", 2000); location.reload(); } }, "全部延長 30 天")),
      h("ul", { class: "list" }, exp.map((u) => h("li", { class: "li static" }, h("span", { class: "mono", text: u.student_id }), h("span", { class: "grow", text: `${u.name}　${u.cohort || ""}` }), h("span", { class: new Date(u.valid_until) < new Date() ? "bad" : "warn", text: (new Date(u.valid_until) < new Date() ? "已到期 " : "到期 ") + day(u.valid_until) }))))) : null,
    h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", { text: "最近登入" }), h("button", { class: "btn sm", onclick: exportBackup }, icon("save"), "匯出完整備份 (JSON)")), logTable(bad)));
}

async function exportBackup() {
  try {
    const d = await rpc("admin_export");
    const blob = new Blob([JSON.stringify(d)], { type: "application/json" });
    const a = h("a", { href: URL.createObjectURL(blob), download: `cpe-備份-${new Date().toISOString().slice(0, 10)}.json` }); document.body.append(a); a.click(); a.remove();
    toast("已下載（學員名單、設定、進度摘要與稽核紀錄；不含 API 金鑰、密碼與學員的程式碼）。名單含個資，請妥善保管。", "ok", 7000);
  } catch (e) { toast(e.message, "bad"); }
}

// ---------------- 題目回報 ----------------
async function reports(body) {
  let showDone = false;
  const box = h("div", { class: "card mt" });
  const load = async () => {
    const rows = await rpc("admin_reports", { p_resolved: showDone }); clear(box);
    if (!rows.length) return box.append(empty("check", showDone ? "沒有已處理的回報" : "沒有待處理的回報"));
    box.append(h("div", { class: "tablewrap" }, h("table", { class: "tbl" }, h("thead", null, h("tr", null, ["時間", "學號", "題號", "說明", ""].map((x) => h("th", { text: x })))),
      h("tbody", null, rows.map((r) => h("tr", null, h("td", { text: fmtT(r.at).slice(0, 16) }), h("td", { class: "mono", text: r.student_id || "" }), h("td", { class: "mono", text: r.problem_id }),
        h("td", { text: r.body, style: { "white-space": "pre-wrap", "max-width": "520px" } }),
        h("td", null, h("button", { class: "btn sm", onclick: async () => { await rpc("admin_resolve_report", { p_id: r.id, p: !showDone }); await load(); } }, showDone ? "重新開啟" : "標記已處理"))))))));
  };
  body.append(h("div", { class: "row wrap mt" }, h("div", { class: "seg" }, [[false, "待處理"], [true, "已處理"]].map(([k, t]) => h("button", { "aria-pressed": String(showDone === k), onclick: async (e) => { showDone = k; [...e.currentTarget.parentElement.children].forEach((b) => b.setAttribute("aria-pressed", String(b === e.currentTarget))); await load(); } }, t))),
    h("span", { class: "muted small", text: "學員在左下角選單「回報題目問題」送出的勘誤" })), box);
  await load();
}

// ---------------- 學習分析 ----------------
async function insights(body) {
  const d = await rpc("admin_insights");
  const kpi = (v, l) => h("div", { class: "card kpi" }, h("div", { class: "v", text: String(v) }), h("div", { class: "l", text: l }));
  const maxW = Math.max(1, ...d.weekly.map((w) => w.active)), maxU = Math.max(1, ...d.units.map((u) => u.n));
  const bar = (v, m, label) => h("div", { class: "barrow" }, h("span", { class: "bl", text: label }), h("span", { class: "bar" }, h("i", { style: { width: Math.round((100 * v) / m) + "%" } })), h("b", { text: String(v) }));
  body.append(h("div", { class: "kpis mt" }, kpi(d.solved_avg, "平均已解題數"), kpi(d.inactive.length, "14 天沒有學習的學員"), kpi(d.stuck.length, "有人卡關的題目"), kpi(d.units.reduce((a, u) => a + u.n, 0), "有同步過進度的學員")),
    h("div", { class: "grid2 mt" },
      h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", { text: "每週有學習的學員數" })), d.weekly.map((w) => bar(w.active, maxW, w.week_ago === 0 ? "本週" : w.week_ago + " 週前"))),
      h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", { text: "學員目前所在單元" })), d.units.length ? d.units.map((u) => bar(u.n, maxU, "單元 " + u.unit)) : empty("chart", "還沒有進度資料"))),
    h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", null, icon("alert"), "全班卡關的題目"), h("span", { class: "muted small", text: "嘗試 4 次以上仍未通過；人數越多越該在課堂講解" })),
      d.stuck.length ? h("div", { class: "tablewrap" }, h("table", { class: "tbl" }, h("thead", null, h("tr", null, ["題號", "卡關人數", "總嘗試次數"].map((x) => h("th", { text: x })))), h("tbody", null, d.stuck.map((r) => h("tr", null, h("td", { class: "mono", text: r.id }), h("td", { text: r.students }), h("td", { text: r.attempts })))))) : empty("check", "目前沒有明顯卡關的題目（或學員還沒同步進度）")),
    h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", null, icon("clock"), "14 天沒有學習的學員")),
      d.inactive.length ? h("div", { class: "tablewrap short" }, h("table", { class: "tbl" }, h("thead", null, h("tr", null, ["學號", "姓名", "班級", "最後學習", "最後登入"].map((x) => h("th", { text: x })))),
        h("tbody", null, d.inactive.map((r) => h("tr", null, h("td", { class: "mono", text: r.student_id }), h("td", { text: r.name }), h("td", { text: r.cohort }), h("td", { text: r.last_active ? ago(r.last_active) : "從未" }), h("td", { text: r.last_login ? fmtT(r.last_login).slice(0, 16) : "從未" })))))) : empty("check", "大家都有在學習")));
}

function logTable(rows) {
  if (!rows.length) return empty("list", "沒有紀錄");
  return h("div", { class: "tablewrap" }, h("table", { class: "tbl" }, h("thead", null, h("tr", null, ["時間", "學號", "動作", "IP", "結果", "細節"].map((x) => h("th", { text: x })))),
    h("tbody", null, rows.map((r) => h("tr", null, h("td", { text: fmtT(r.at) }), h("td", { class: "mono", text: r.student_id || "" }), h("td", { text: r.action }), h("td", { class: "mono", text: r.ip || "" }),
      h("td", null, h("span", { class: "pill " + (r.ok ? "ok" : "bad"), text: r.ok ? "成功" : "拒絕" })), h("td", { class: "xs muted", text: r.detail ? JSON.stringify(r.detail).slice(0, 90) : "" }))))));
}

// ---------------- 學員 ----------------
async function users(body) {
  let all = await rpc("admin_list_users");
  const sel = new Set();
  const f = { q: "", cohort: "", status: "" };
  const list = h("div", { class: "tablewrap" });
  const bar = h("div", { class: "bulkbar", hidden: true });
  const q = h("input", { type: "search", placeholder: "搜尋學號／姓名", "aria-label": "搜尋", oninput: debounce((e) => { f.q = e.target.value.trim().toLowerCase(); paint(); }, 150) });
  const cohortSel = h("select", { "aria-label": "班級", onchange: (e) => { f.cohort = e.target.value; paint(); } });
  const statusSel = h("select", { "aria-label": "狀態", onchange: (e) => { f.status = e.target.value; paint(); } }, [["", "全部狀態"], ["ok", "使用中"], ["inactive", "待開通"], ["expired", "已到期"], ["not_started", "尚未開始"], ["archived", "已封存"]].map(([k, t]) => h("option", { value: k, text: t })));
  const refresh = async () => { all = await rpc("admin_list_users"); [...sel].forEach((i) => { if (!all.find((u) => u.id === i)) sel.delete(i); }); paint(); };
  const shown = () => all.filter((u) => u.role === "student" && (f.status === "archived" ? u.archived : !u.archived) && (!f.cohort || u.cohort === f.cohort) && (!f.status || f.status === "archived" || u.status === f.status) && (!f.q || (u.student_id + " " + u.name).toLowerCase().includes(f.q)));
  const admins = () => all.filter((u) => u.role === "admin");

  const bulk = async (patch, label) => {
    if (!sel.size) return;
    if (!(await confirmDialog(label, `要對選取的 ${sel.size} 位學員執行「${label}」嗎？`, "執行"))) return;
    if (sel.size >= 20 && prompt(`影響 ${sel.size} 人。請輸入「確認」才會執行`) !== "確認") { toast("已取消", "", 1500); return; }
    try { const n = await rpc("admin_bulk_update", { p_ids: [...sel], p: patch }); toast(`已更新 ${n} 位`, "ok", 2500); await refresh(); } catch (e) { toast(e.message, "bad"); }
  };
  const windowDialog = () => {
    const a = h("input", { type: "date", "aria-label": "開始日" }), b = h("input", { type: "date", "aria-label": "結束日" });
    modal({ title: `設定授權期間（${sel.size} 人）`, body: h("div", { class: "col" }, h("label", { class: "field" }, "開始日（空白＝不限）", a), h("label", { class: "field" }, "結束日（含當天；空白＝不限）", b),
      h("div", { class: "row wrap" }, [["本學期（+4 個月）", 4], ["一學年（+12 個月）", 12]].map(([t, m]) => h("button", { class: "btn sm", onclick: () => { const d = new Date(); a.value = dateVal(d.toISOString()); d.setMonth(d.getMonth() + m); b.value = dateVal(d.toISOString()); } }, t)))),
      actions: [{ label: "取消" }, { label: "套用", kind: "primary", onClick: async () => { await rpc("admin_bulk_update", { p_ids: [...sel], p: { valid_from: startOf(a.value), valid_until: endOf(b.value) } }); toast("已設定授權期間", "ok", 2000); await refresh(); } }] });
  };
  const extendDialog = () => {
    const n = h("input", { type: "number", min: 1, max: 730, value: 30, "aria-label": "天數" });
    modal({ title: `延長授權（${sel.size} 人）`, body: h("label", { class: "field" }, "往後延長幾天（從原本到期日算起；沒有到期日的從今天算起）", n), actions: [{ label: "取消" }, { label: "延長", kind: "primary", onClick: async () => {
      for (const id of sel) { const u = all.find((x) => x.id === id); const base = u.valid_until && new Date(u.valid_until) > new Date() ? new Date(u.valid_until) : new Date(); base.setDate(base.getDate() + (+n.value || 0)); await rpc("admin_update_user", { p_id: id, p: { valid_until: base.toISOString() } }); }
      toast("已延長", "ok", 2000); await refresh(); } }] });
  };
  const cohortDialog = () => { const c = h("input", { type: "text", placeholder: "例如 114 級", "aria-label": "班級" }); modal({ title: "設定班級／屆別", body: h("label", { class: "field" }, "班級", c), actions: [{ label: "取消" }, { label: "套用", kind: "primary", onClick: async () => { await rpc("admin_bulk_update", { p_ids: [...sel], p: { cohort: c.value.trim() } }); await refresh(); } }] }); };
  const ipDialog = () => {
    const m = h("select", { "aria-label": "IP 模式" }, [["inherit", "跟隨全域設定"], ["any", "不限制（任何 IP）"], ["list", "只允許下列 IP"]].map(([k, t]) => h("option", { value: k, text: t })));
    const t = h("textarea", { rows: 4, placeholder: "每行一個，例如 203.0.113.0/24 或 203.0.113.5" });
    modal({ title: `IP 限制（${sel.size} 人）`, body: h("div", { class: "col" }, h("label", { class: "field" }, "模式", m), h("label", { class: "field" }, "允許的 IP／網段（僅「只允許下列 IP」使用）", t)), actions: [{ label: "取消" }, { label: "套用", kind: "primary", onClick: async () => { try { await rpc("admin_bulk_update", { p_ids: [...sel], p: { ip_mode: m.value, allowed_ips: lines(t.value) } }); await refresh(); } catch (e) { toast(e.message, "bad"); return false; } } }] });
  };

  function paintBar() {
    clear(bar); bar.hidden = !sel.size; if (!sel.size) return;
    bar.append(h("b", { text: `已選 ${sel.size} 位` }), h("button", { class: "btn sm", onclick: () => bulk({ active: true }, "啟用帳號") }, "啟用"), h("button", { class: "btn sm", onclick: () => bulk({ active: false }, "停用帳號") }, "停用"),
      h("button", { class: "btn sm", onclick: windowDialog }, icon("clock"), "授權期間"), h("button", { class: "btn sm", onclick: extendDialog }, "延長"),
      h("button", { class: "btn sm", onclick: () => bulk({ ai_allowed: true }, "開放 AI") }, icon("sparkle"), "開放 AI"), h("button", { class: "btn sm", onclick: () => bulk({ ai_allowed: false }, "關閉 AI") }, "關閉 AI"),
      h("button", { class: "btn sm", onclick: ipDialog }, "IP 限制"), h("button", { class: "btn sm", onclick: cohortDialog }, "班級"), h("button", { class: "btn sm", onclick: async () => { const arch = f.status !== "archived"; if (!(await confirmDialog(arch ? "封存" : "還原", arch ? `封存 ${sel.size} 位？帳號會被停用、從清單隱藏，但資料與進度保留，隨時可還原。` : `還原 ${sel.size} 位（還原後仍是停用狀態，需再啟用）？`, arch ? "封存" : "還原"))) return; try { await rpc("admin_set_archived", { p_ids: [...sel], p: arch }); sel.clear(); await refresh(); } catch (e) { toast(e.message, "bad"); } } }, f.status === "archived" ? "還原" : "封存"), h("button", { class: "btn sm ghost", onclick: () => { sel.clear(); paint(); } }, "取消選取"));
  }
  function paint() {
    const rows = shown();
    const cohorts = [...new Set(all.filter((u) => u.role === "student").map((u) => u.cohort))].sort();
    if (cohortSel.options.length !== cohorts.length + 1) { clear(cohortSel); cohortSel.append(h("option", { value: "", text: "全部班級" }), cohorts.map((c) => h("option", { value: c, text: c || "（未分班）", selected: c === f.cohort }))); }
    paintBar(); clear(list);
    if (!rows.length) { list.append(empty("users", all.some((u) => u.role === "student") ? "沒有符合的學員" : "還沒有學員，按「批次新增」貼上名單。")); return; }
    const allSel = rows.every((u) => sel.has(u.id));
    const head = h("input", { type: "checkbox", checked: allSel, "aria-label": "全選目前篩選結果", onchange: (e) => { rows.forEach((u) => (e.target.checked ? sel.add(u.id) : sel.delete(u.id))); paint(); } });
    list.append(h("table", { class: "tbl" }, h("thead", null, h("tr", null, h("th", null, head), ["學號", "姓名", "班級", "狀態", "授權期間", "IP", "AI", "進度", "最後上線", ""].map((x) => h("th", { text: x })))),
      h("tbody", null, rows.map((u) => { const [st, cls] = STATUS[u.status] || [u.status, ""]; const s = u.summary || {};
        return h("tr", { class: sel.has(u.id) ? "sel" : "" },
          h("td", null, h("input", { type: "checkbox", checked: sel.has(u.id), "aria-label": "選取 " + u.student_id, onchange: (e) => { e.target.checked ? sel.add(u.id) : sel.delete(u.id); paintBar(); } })),
          h("td", { class: "mono", text: u.student_id }), h("td", { text: u.name }), h("td", { text: u.cohort }), h("td", null, h("span", { class: "pill " + cls, text: st })),
          h("td", { class: "xs", text: u.valid_from || u.valid_until ? `${day(u.valid_from)} ～ ${day(u.valid_until)}` : "不限" }),
          h("td", { class: "xs", text: { inherit: "跟隨全域", any: "不限", list: `指定 ${u.allowed_ips.length} 組` }[u.ip_mode] }),
          h("td", null, u.ai_allowed ? h("span", { class: "pill accent", text: "開放" }) : h("span", { class: "muted", text: "—" })),
          h("td", { class: "xs", text: s.solved != null ? `解 ${s.solved} 題 · 單元 ${s.unit}` : "—" }), h("td", { class: "xs", text: u.last_login_at ? fmtT(u.last_login_at).slice(0, 16) : "從未" }),
          h("td", null, h("button", { class: "btn sm", onclick: () => edit(u) }, "編輯"))); }))));
  }
  function edit(u) {
    drawer((close) => {
      const name = h("input", { type: "text", value: u.name, "aria-label": "姓名" }), cohort = h("input", { type: "text", value: u.cohort, "aria-label": "班級" }), note = h("textarea", { rows: 2, "aria-label": "備註" }, u.note || "");
      const vf = h("input", { type: "date", value: dateVal(u.valid_from), "aria-label": "開始日" }), vu = h("input", { type: "date", value: dateVal(u.valid_until), "aria-label": "結束日" });
      const ipm = h("select", { "aria-label": "IP 模式" }, [["inherit", "跟隨全域設定"], ["any", "不限制（任何 IP）"], ["list", "只允許下列 IP"]].map(([k, t]) => h("option", { value: k, text: t, selected: u.ip_mode === k })));
      const ips = h("textarea", { rows: 3, placeholder: "每行一個，例如 203.0.113.0/24" }, (u.allowed_ips || []).join("\n"));
      let active = u.active, ai = u.ai_allowed, role = u.role;
      const s = u.summary || {};
      return h("div", { class: "drawer-in" },
        h("div", { class: "modal-h" }, h("h2", { text: `${u.student_id}　${u.name}` }), h("button", { class: "btn ghost icon sm", "aria-label": "關閉", onclick: close }, icon("x"))),
        h("div", { class: "modal-b col" },
          h("div", { class: "row wrap" }, sw(active, (v) => (active = v), "帳號啟用"), sw(ai, (v) => (ai = v), "可使用 AI")),
          h("label", { class: "field" }, "姓名", name), h("label", { class: "field" }, "班級／屆別", cohort),
          h("div", { class: "row" }, h("label", { class: "field grow" }, "授權開始", vf), h("label", { class: "field grow" }, "授權結束（含當天）", vu)),
          h("label", { class: "field" }, "IP 限制", ipm), h("label", { class: "field" }, "允許的 IP／網段", ips), h("label", { class: "field" }, "備註", note),
          h("dl", { class: "dl small" }, ...row2("最近登入", `${u.last_login_at ? fmtT(u.last_login_at) : "從未"}　${u.last_ip || ""}`), ...row2("登入次數", u.login_count), ...row2("進度更新", u.progress_at ? fmtT(u.progress_at) : "從未同步"),
            ...row2("學習進度", s.solved != null ? `已解 ${s.solved} 題、嘗試 ${s.attempted} 題、單元 ${s.unit}、活躍 ${s.active_days} 天、考試 ${s.exams} 次` : "尚無資料"), ...row2("最後學習", s.last_active ? ago(s.last_active) : "—"), ...row2("24 小時 AI", u.ai_calls_24h + " 次")),
          h("div", { class: "row wrap" },
            h("button", { class: "btn", onclick: async () => { if (!(await confirmDialog("重設密碼", `產生 ${u.student_id} 的新密碼？對方下次登入需要再改。`, "重設"))) return; try { const r = await fn({ action: "reset_password", id: u.id }); modal({ title: "新密碼", body: h("div", null, h("p", { text: "請交給學員（只會顯示這一次）：" }), h("p", { class: "bigpw mono", text: r.password })), actions: [{ label: "複製", onClick: () => { navigator.clipboard?.writeText(r.password); toast("已複製", "ok", 1200); return false; }, keep: true }, { label: "完成", kind: "primary" }] }); } catch (e) { toast(e.message, "bad"); } } }, icon("lock"), "重設密碼"),
            h("button", { class: "btn danger", onclick: async () => { if (!(await confirmDialog("刪除帳號", `永久刪除 ${u.student_id} 與他的雲端進度？無法復原。（只想暫時隱藏請用「封存」）`, "刪除", "danger"))) return; if (prompt(`再確認一次：請輸入學號 ${u.student_id}`) !== u.student_id) { toast("學號不符，已取消", "bad"); return; } try { await fn({ action: "delete_user", id: u.id }); toast("已刪除", "ok", 2000); close(); await refresh(); } catch (e) { toast(e.message, "bad"); } } }, "刪除帳號"))),
        h("div", { class: "modal-f" }, h("button", { class: "btn", onclick: close }, "取消"), h("button", { class: "btn primary", onclick: async () => {
          try { await rpc("admin_update_user", { p_id: u.id, p: { name: name.value.trim(), cohort: cohort.value.trim(), note: note.value, active, ai_allowed: ai, valid_from: startOf(vf.value), valid_until: endOf(vu.value), ip_mode: ipm.value, allowed_ips: lines(ips.value) } }); toast("已儲存", "ok", 1500); close(); await refresh(); } catch (e) { toast(e.message, "bad"); } } }, "儲存")));
    });
  }
  const row2 = (k, v) => [h("dt", { text: k }), h("dd", { text: String(v) })];

  function createDialog() {
    const t = h("textarea", { rows: 8, placeholder: "每行一位：學號, 姓名\n例如：\n114001, 王小明\n114002, 李小華\n（可直接從 Excel 貼上兩欄）", "aria-label": "名單" });
    const cohort = h("input", { type: "text", placeholder: "例如 114 級", "aria-label": "班級" }), a = h("input", { type: "date", "aria-label": "開始日" }), b = h("input", { type: "date", "aria-label": "結束日" });
    const file = h("input", { type: "file", accept: ".csv,.txt,text/csv", "aria-label": "匯入 CSV", onchange: async (e) => { const f = e.target.files[0]; if (!f) return; let txt = await f.text(); txt = txt.replace(/^\ufeff/, ""); const rows = txt.split(/\r?\n/).filter((l) => l.trim()); if (/學號|student/i.test(rows[0] || "")) rows.shift(); t.value = rows.join("\n"); } });
    let act = true, ai = false;
    modal({ title: "批次新增學員", wide: true, body: h("div", { class: "col" }, h("label", { class: "field" }, "名單（學號, 姓名；第三欄可寫班級）", t),
      h("div", { class: "row wrap" }, h("label", { class: "field grow" }, "或匯入 CSV／Excel 另存的 CSV（欄位：學號, 姓名[, 班級]）", file), h("button", { class: "btn sm", onclick: () => csvDownload("學員名單範本.csv", [["學號", "姓名", "班級"], ["114001", "王小明", "114"], ["114002", "李小華", "114"]]) }, icon("save"), "下載範本")),
      h("div", { class: "row wrap" }, h("label", { class: "field grow" }, "班級／屆別", cohort), h("label", { class: "field" }, "授權開始", a), h("label", { class: "field" }, "授權結束", b)),
      h("div", { class: "row wrap" }, sw(act, (v) => (act = v), "建立後立即啟用"), sw(ai, (v) => (ai = v), "開放 AI")),
      h("p", { class: "xs muted", text: "系統會為每個人產生一組隨機初始密碼，學員第一次登入必須改密碼。學號用英數字（3–24 字），系統一律轉小寫。" })),
      actions: [{ label: "取消" }, { label: "建立", kind: "primary", keep: true, onClick: async (close) => {
        const us = t.value.split("\n").map((l) => l.trim()).filter(Boolean).map((l) => { const p = l.split(/[,\t，;]+/).map((x) => x.trim()); return { student_id: p[0], name: p[1] || "", cohort: p[2] || "" }; });
        if (!us.length) { toast("名單是空的", "bad"); return false; }
        try { const r = await fn({ action: "create_users", users: us, cohort: cohort.value.trim(), active: act, ai_allowed: ai, valid_from: startOf(a.value), valid_until: endOf(b.value) }); close(); resultDialog(r.results); await refresh(); } catch (e) { toast(e.message, "bad"); return false; } } }] });
  }
  function resultDialog(res) {
    const ok = res.filter((r) => r.ok), bad = res.filter((r) => !r.ok);
    modal({ title: `已建立 ${ok.length} 位${bad.length ? `，${bad.length} 位失敗` : ""}`, wide: true, body: h("div", null, h("p", { class: "warn small", text: "初始密碼只會顯示這一次，請現在下載或複製。" }),
      h("div", { class: "tablewrap short" }, h("table", { class: "tbl" }, h("thead", null, h("tr", null, ["學號", "姓名", "初始密碼／錯誤"].map((x) => h("th", { text: x })))), h("tbody", null, res.map((r) => h("tr", null, h("td", { class: "mono", text: r.student_id }), h("td", { text: r.name || "" }), h("td", { class: r.ok ? "mono" : "bad", text: r.ok ? r.password : r.error }))))))),
      actions: [{ label: "下載 CSV", keep: true, onClick: () => { csvDownload("初始密碼.csv", [["學號", "姓名", "初始密碼"], ...ok.map((r) => [r.student_id, r.name, r.password])]); return false; } },
        { label: "複製", keep: true, onClick: () => { navigator.clipboard?.writeText(ok.map((r) => `${r.student_id}\t${r.name}\t${r.password}`).join("\n")); toast("已複製", "ok", 1200); return false; } }, { label: "完成", kind: "primary" }] });
  }
  const exportCsv = () => csvDownload("學員名單.csv", [["學號", "姓名", "班級", "狀態", "啟用", "授權開始", "授權結束", "AI", "IP模式", "已解題數", "單元", "最後登入", "備註"],
    ...shown().map((u) => [u.student_id, u.name, u.cohort, (STATUS[u.status] || [u.status])[0], u.active, u.valid_from || "", u.valid_until || "", u.ai_allowed, u.ip_mode, (u.summary || {}).solved ?? "", (u.summary || {}).unit ?? "", u.last_login_at || "", u.note])]);

  body.append(h("div", { class: "row wrap mt" }, q, cohortSel, statusSel, h("span", { class: "grow" }), h("button", { class: "btn", onclick: exportCsv }, icon("save"), "匯出 CSV"), h("button", { class: "btn primary", onclick: createDialog }, icon("users"), "批次新增")), bar, h("div", { class: "card mt" }, list),
    admins().length ? h("p", { class: "xs muted mt", text: "管理員帳號：" + admins().map((a) => a.student_id).join("、") + "（不受 IP 與授權期間限制；不能在這裡改自己的角色）" }) : null);
  paint();
}

// ---------------- 授權與網路 ----------------
async function network(body) {
  const [S, me] = await Promise.all([rpc("admin_get_settings"), get("/api/cloud/status")]);
  const ip = S.ip_policy || { enabled: false, cidrs: [] }, off = S.offline || { grace_hours: 72 };
  let on = !!ip.enabled;
  const t = h("textarea", { rows: 6, placeholder: "每行一個，例如：\n203.0.113.0/24\n198.51.100.7", "aria-label": "允許的 IP" }, (ip.cidrs || []).join("\n"));
  const grace = h("input", { type: "number", min: 0, max: 720, value: off.grace_hours, "aria-label": "離線寬限（小時）", style: { width: "120px" } });
  const myip = (me.access || {}).ip;
  body.append(h("div", { class: "grid2 mt" },
    h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", null, icon("lock"), "IP 限制（全域）")),
      h("p", { class: "muted small", text: "IP 由伺服器判斷（學員無法自報）。啟用後，「跟隨全域」的學員只有從下列 IP／網段才能登入、同步、用 AI；管理員不受限制。個別學員可在帳號設定裡覆寫。" }),
      h("div", { class: "col" }, sw(on, (v) => (on = v), "啟用全域 IP 限制"), t,
        h("div", { class: "row wrap" }, myip ? h("button", { class: "btn sm", onclick: () => { const v = lines(t.value); if (!v.includes(myip)) v.push(myip); t.value = v.join("\n"); } }, icon("target"), `加入我目前的 IP（${myip}）`) : null, h("span", { class: "xs muted", text: "校內多半是一段網段，例如 140.128.x.0/24；請向校網中心確認。" })),
        h("div", { class: "gate-note" }, icon("alert"), h("span", { text: "啟用前請先加入你目前的 IP 並確認學員的網路（宿舍、行動網路、VPN 會不同）。清單留空且啟用時，所有「跟隨全域」的學員都會被擋住。" })),
        h("div", null, h("button", { class: "btn primary", onclick: async () => { try { await rpc("admin_set_setting", { p_key: "ip_policy", p_value: { enabled: on, cidrs: lines(t.value) } }); toast("已儲存 IP 設定", "ok", 2000); } catch (e) { toast(e.message, "bad"); } } }, "儲存")))),
    h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", null, icon("clock"), "離線寬限")),
      h("p", { class: "muted small", text: "學員電腦連不上伺服器時，最多可以用「上一次驗證通過」的結果繼續練習幾小時。超過就必須連網重新驗證。0＝每次都必須連網。授權到期時間不會被寬限延長。" }),
      h("div", { class: "row" }, grace, h("span", { text: "小時" }), h("button", { class: "btn primary", onclick: async () => { try { await rpc("admin_set_setting", { p_key: "offline", p_value: { grace_hours: Math.max(0, +grace.value || 0) } }); toast("已儲存", "ok", 1500); } catch (e) { toast(e.message, "bad"); } } }, "儲存")),
      h("div", { class: "gate-note mt" }, icon("bulb"), h("span", { text: "提醒：這些限制由伺服器強制執行的是「雲端進度、AI 額度與金鑰」。程式本身在學員電腦上，會寫程式的人可以改掉本機的檢查；題目與測資是隨程式安裝的。" })))));
}

// ---------------- AI ----------------
async function ai(body) {
  const [S, sec, usage] = await Promise.all([rpc("admin_get_settings"), rpc("admin_secret_status"), rpc("admin_ai_usage", { p_days: 7 })]);
  const c = S.ai || { enabled: false, model: "gpt-4o", daily_calls: 60, max_tokens: 1500 };
  let on = !!c.enabled;
  const model = h("input", { type: "text", value: c.model, list: "models", "aria-label": "模型" }), models = h("datalist", { id: "models" }, ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"].map((m) => h("option", { value: m })));
  const daily = h("input", { type: "number", min: 1, max: 1000, value: c.daily_calls, "aria-label": "每人每日次數", style: { width: "120px" } }), maxt = h("input", { type: "number", min: 100, max: 8000, value: c.max_tokens, "aria-label": "每次最大輸出 token", style: { width: "120px" } });
  const monthly = h("input", { type: "number", min: 0, max: 1000000, value: c.monthly_calls || 0, "aria-label": "每月全學程總次數", style: { width: "140px" } });
  const mode = h("select", { "aria-label": "AI 模式" }, [["normal", "一般（可直接講解與給範例）"], ["socratic", "蘇格拉底（只引導提問，不直接給完整答案）"]].map(([k, t]) => h("option", { value: k, text: t, selected: (c.mode || "normal") === k })));
  const key = h("input", { type: "password", autocomplete: "off", placeholder: sec.set ? "（已設定；輸入新金鑰可取代）" : "sk-…", "aria-label": "OpenAI API 金鑰" });
  const keyMsg = h("div", { class: "small mt", "aria-live": "polite" });
  body.append(h("div", { class: "grid2 mt" },
    h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", null, icon("sparkle"), "AI 授權")),
      h("p", { class: "muted small", text: "金鑰只存在資料庫，由學程伺服器代為呼叫 OpenAI；學員電腦上從來沒有金鑰，也看不到。要使用 AI，需要同時：① 這裡開放 ② 該學員被授權。" }),
      h("div", { class: "col" }, sw(on, (v) => (on = v), "開放學程學員使用 AI（總開關）"), h("label", { class: "field" }, "模型", model, models),
        h("div", { class: "row wrap" }, h("label", { class: "field" }, "每人每 24 小時上限（次）", daily), h("label", { class: "field" }, "每次最大輸出 tokens", maxt), h("label", { class: "field" }, "每月全學程總次數（0＝不限）", monthly)),
        h("label", { class: "field" }, "AI 模式", mode),
        h("div", null, h("button", { class: "btn primary", onclick: async () => { try { await rpc("admin_set_setting", { p_key: "ai", p_value: { enabled: on, model: model.value.trim() || "gpt-4o", daily_calls: Math.max(1, +daily.value || 60), max_tokens: Math.max(100, +maxt.value || 1500), monthly_calls: Math.max(0, +monthly.value || 0), mode: mode.value } }); toast("已儲存 AI 設定", "ok", 2000); } catch (e) { toast(e.message, "bad"); } } }, "儲存")))),
    h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", null, icon("lock"), "OpenAI API 金鑰")),
      h("p", { class: "small", text: sec.set ? `已設定（結尾 ${sec.last4}，更新於 ${fmtT(sec.updated_at)}）` : "尚未設定金鑰。" }),
      h("div", { class: "col" }, key, h("div", { class: "row wrap" },
        h("button", { class: "btn primary", onclick: async () => { if (!key.value.trim()) { keyMsg.textContent = "請先輸入金鑰"; return; } try { await rpc("admin_set_secret", { p_value: key.value }); key.value = ""; toast("金鑰已儲存到資料庫", "ok", 2500); await mountSelf(body); } catch (e) { keyMsg.textContent = e.message; } } }, "儲存金鑰"),
        sec.set ? h("button", { class: "btn danger", onclick: async () => { if (await confirmDialog("清除金鑰", "清除後所有學員的 AI 都會停用。", "清除", "danger")) { await rpc("admin_set_secret", { p_value: "" }); await mountSelf(body); } } }, "清除金鑰") : null,
        h("button", { class: "btn", onclick: async (e) => { const b = e.currentTarget; b.disabled = true; keyMsg.textContent = "測試中…"; keyMsg.className = "small mt muted"; try { const r = await post("/api/admin/ai_test"); keyMsg.textContent = r.ok ? `✓ 成功（${r.model}）：${r.reply}` : "✗ " + r.error; keyMsg.className = "small mt " + (r.ok ? "ok" : "bad"); } finally { b.disabled = false; } } }, icon("refresh"), "測試呼叫")), keyMsg)),
    h("section", { class: "card pad", style: { "grid-column": "1/-1" } }, h("div", { class: "card-h" }, h("h3", { text: "近 7 天用量" })),
      usage.length ? h("div", { class: "tablewrap" }, h("table", { class: "tbl" }, h("thead", null, h("tr", null, ["學號", "次數", "輸入 tokens", "輸出 tokens", "最後使用"].map((x) => h("th", { text: x })))), h("tbody", null, usage.map((u) => h("tr", null, h("td", { class: "mono", text: u.student_id }), h("td", { text: u.calls }), h("td", { text: (u.tokens_in || 0).toLocaleString() }), h("td", { text: (u.tokens_out || 0).toLocaleString() }), h("td", { text: fmtT(u.last) })))))) : empty("sparkle", "還沒有使用紀錄"))));
}
async function mountSelf(body) { clear(body); await ai(body); }

// ---------------- 版本與公告 ----------------
async function release(body) {
  const S = await rpc("admin_get_settings"); const a = S.app || {};
  const ver = h("input", { type: "text", value: a.latest_version || "", "aria-label": "最新版本" }), min = h("input", { type: "text", value: a.min_version || "", "aria-label": "最低版本" });
  const welcome = h("textarea", { rows: 3, "aria-label": "歡迎訊息" }, a.welcome || "");
  const ann = h("textarea", { rows: 3, "aria-label": "公告" }, a.announcement || ""), note = h("textarea", { rows: 3, "aria-label": "更新說明" }, a.update_note || "");
  body.append(h("section", { class: "card pad mt", style: { "max-width": "760px" } }, h("div", { class: "card-h" }, h("h3", null, icon("bulb"), "版本與公告")),
    h("p", { class: "muted small", text: "每位學員的程式每次開啟（以及之後每 30 分鐘）都會連網檢查：有新版本會提示更新；低於「最低版本」就無法使用，必須先更新。公告會在登入頁與使用中顯示一次。" }),
    h("div", { class: "col" }, h("div", { class: "row wrap" }, h("label", { class: "field" }, "最新版本", ver), h("label", { class: "field" }, "最低可使用版本（強制更新）", min)),
      h("label", { class: "field" }, "公告（登入頁與使用中顯示；留空＝不顯示）", ann), h("label", { class: "field" }, "更新說明（強制更新畫面顯示）", note), h("label", { class: "field" }, "歡迎訊息（每位學員第一次進入時顯示一次；留空＝不顯示）", welcome),
      h("div", null, h("button", { class: "btn primary", onclick: async () => { try { await rpc("admin_set_setting", { p_key: "app", p_value: { latest_version: ver.value.trim(), min_version: min.value.trim(), announcement: ann.value.trim(), update_note: note.value.trim(), welcome: welcome.value.trim() } }); toast("已儲存", "ok", 1800); } catch (e) { toast(e.message, "bad"); } } }, "儲存")),
      h("div", { class: "row wrap" }, h("button", { class: "btn", onclick: async () => { const d = +prompt("封存授權已到期超過幾天的學員？", "30"); if (!d) return; if (!(await confirmDialog("自動封存", `封存授權到期超過 ${d} 天的學員？（可還原）`, "封存"))) return; try { const n = await rpc("admin_auto_archive", { p_days: d }); toast(`已封存 ${n} 位`, "ok", 2500); } catch (e) { toast(e.message, "bad"); } } }, "封存過期學員…")),
      h("p", { class: "xs muted", text: "提醒：把最低版本設得比大家目前的版本高，所有人都會被擋在更新畫面。發布新版後再調高。" }))),
    noticesCard(S.notices && S.notices.items ? S.notices.items : []));
}

// 分班、排程的公告（每則可指定班級與顯示期間）
function noticesCard(items) {
  items = items.map((x) => ({ ...x }));
  const box = h("div", { class: "col" });
  const paint = () => {
    clear(box);
    items.forEach((it, i) => {
      const txt = h("textarea", { rows: 2, "aria-label": "公告內容", oninput: (e) => { it.text = e.target.value; } }, it.text || "");
      const co = h("input", { type: "text", value: it.cohort || "", placeholder: "班級（空白＝全部）", "aria-label": "班級", oninput: (e) => { it.cohort = e.target.value.trim(); } });
      const fr = h("input", { type: "date", value: dateVal(it.from), "aria-label": "開始顯示", onchange: (e) => { it.from = startOf(e.target.value) || ""; } });
      const un = h("input", { type: "date", value: dateVal(it.until), "aria-label": "結束顯示", onchange: (e) => { it.until = endOf(e.target.value) || ""; } });
      box.append(h("div", { class: "notice-item" }, txt, h("div", { class: "row wrap" }, co, h("label", { class: "xs muted" }, "從 ", fr), h("label", { class: "xs muted" }, "到 ", un), h("span", { class: "grow" }), h("button", { class: "btn sm danger", onclick: () => { items.splice(i, 1); paint(); } }, "刪除"))));
    });
    if (!items.length) box.append(h("p", { class: "muted small", text: "目前沒有分班／排程公告。" }));
  };
  paint();
  return h("section", { class: "card pad mt", style: { "max-width": "760px" } }, h("div", { class: "card-h" }, h("h3", null, icon("bulb"), "分班與排程公告")),
    h("p", { class: "muted small", text: "每則公告可以只給某個班級，並設定顯示期間；學員登入後在左下角選單看得到，第一次出現時也會彈出提示。" }), box,
    h("div", { class: "row mt" }, h("button", { class: "btn", onclick: () => { items.push({ id: String(Date.now()), text: "", cohort: "", from: "", until: "" }); paint(); } }, "新增公告"),
      h("button", { class: "btn primary", onclick: async () => { try { await rpc("admin_set_notices", { p: { items: items.filter((x) => (x.text || "").trim()) } }); toast("已儲存公告", "ok", 1800); } catch (e) { toast(e.message, "bad"); } } }, "儲存公告")));
}

// ---------------- 稽核 ----------------
async function audit(body) {
  const stu = h("input", { type: "search", placeholder: "學號", "aria-label": "學號", style: { width: "140px" } });
  const act = h("select", { "aria-label": "動作" }, [["", "全部動作"], ["login", "登入"], ["check", "授權被拒"], ["admin_update", "修改帳號"], ["admin_setting", "修改設定"], ["admin_secret", "金鑰"], ["admin_create_users", "批次新增"], ["admin_reset_password", "重設密碼"], ["admin_delete_user", "刪除帳號"]].map(([k, t]) => h("option", { value: k, text: t })));
  const out = h("div", { class: "card mt" }); let rows = [];
  const load = async () => { rows = await rpc("admin_audit", { p_limit: 300, p_student: stu.value.trim().toLowerCase() || null, p_action: act.value || null }); clear(out); out.append(logTable(rows)); };
  stu.addEventListener("change", load); act.addEventListener("change", load);
  body.append(h("div", { class: "row wrap mt" }, stu, act, h("button", { class: "btn", onclick: load }, icon("refresh"), "重新整理"), h("span", { class: "grow" }), h("button", { class: "btn", onclick: () => csvDownload("稽核紀錄.csv", [["時間", "學號", "動作", "IP", "結果", "細節"], ...rows.map((r) => [r.at, r.student_id, r.action, r.ip, r.ok, JSON.stringify(r.detail || {})])]) }, icon("save"), "匯出 CSV")), out);
  await load();
}
