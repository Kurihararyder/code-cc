// 左下角「人員」：個人資料與授權狀態、同步、改密碼、登出；管理員多一個「管理後台」。更新提醒也在這裡。
import { h, icon, $, toast, modal, clear } from "./dom.js";
import { get, post } from "./api.js";
import { go } from "./router.js";
import { pref } from "./state.js";
import { fmtT, runUpdate } from "./gate.js";

export let CLOUD = { enabled: false };

export async function loadCloud() {
  try { CLOUD = await get("/api/cloud/status"); } catch { /* 離線時維持舊值 */ }
  return CLOUD;
}

export function userButton() {
  if (!CLOUD.enabled) return null;
  const u = CLOUD.user || {};
  const label = (u.name || u.student_id || "人員").slice(0, 4);
  const b = h("button", { class: "navbtn", id: "userBtn", "aria-haspopup": "menu", title: `${u.name || ""} ${u.student_id || ""}`.trim(), onclick: (e) => { e.stopPropagation(); openMenu(b); } },
    icon(CLOUD.is_admin ? "shield" : "user"), h("span", { text: label }), CLOUD.update && CLOUD.update.behind > 0 ? h("span", { class: "dot", text: "!" }) : null);
  return b;
}

function row(k, v) { return [h("dt", { text: k }), h("dd", null, v)]; }

function openMenu(anchor) {
  document.querySelectorAll(".usermenu").forEach((m) => m.remove());
  const u = CLOUD.user || {}, a = CLOUD.access || {};
  const menu = h("div", { class: "usermenu", role: "menu" },
    h("div", { class: "um-head" }, h("div", { class: "um-av" }, icon(CLOUD.is_admin ? "shield" : "user")),
      h("div", null, h("b", { text: u.name || u.student_id }), h("div", { class: "xs muted", text: `${u.student_id}${u.cohort ? " · " + u.cohort : ""}${CLOUD.is_admin ? " · 管理員" : ""}` }))),
    h("dl", { class: "dl um-dl" },
      row("授權期間", u.valid_until || u.valid_from ? `${u.valid_from ? fmtT(u.valid_from).split(" ")[0] : "不限"} ～ ${u.valid_until ? fmtT(u.valid_until).split(" ")[0] : "不限"}` : "不限期"),
      row("AI", CLOUD.ai && CLOUD.ai.available ? h("span", { class: "ok", text: "已授權" }) : h("span", { class: "muted", text: (CLOUD.ai || {}).why || "未授權" })),
      row("雲端同步", CLOUD.offline ? h("span", { class: "warn", text: `離線中（寬限剩 ${a.grace_left_h ?? "?"} 小時）` }) : CLOUD.last_error ? h("span", { class: "warn", text: CLOUD.last_error }) : CLOUD.last_sync ? h("span", { class: "ok", text: "已同步 " + new Date(CLOUD.last_sync.at * 1000).toLocaleTimeString("zh-TW", { hour12: false }) }) : h("span", { class: "muted", text: "尚未同步" }))),
    CLOUD.app && CLOUD.app.announcement ? h("div", { class: "gate-note um-note" }, icon("bulb"), h("span", { text: CLOUD.app.announcement })) : null,
    CLOUD.is_admin ? h("button", { role: "menuitem", class: "um-item", onclick: () => { menu.remove(); go("/admin"); } }, icon("shield"), "管理後台") : null,
    h("button", { role: "menuitem", class: "um-item", onclick: async (e) => { const b = e.currentTarget; b.disabled = true; try { const r = await post("/api/cloud/sync"); toast(`已同步（拉回 ${r.sync.pulled_events} 筆、上傳 ${r.sync.pushed_events} 筆紀錄）`, "ok", 3000); await loadCloud(); menu.remove(); } catch (err) { toast(err.message, "bad"); b.disabled = false; } } }, icon("refresh"), "立即同步進度"),
    CLOUD.update && CLOUD.update.behind > 0 ? h("button", { role: "menuitem", class: "um-item", onclick: () => { menu.remove(); updateDialog(); } }, icon("external"), `有新版本（${CLOUD.update.behind} 項更新）`) : null,
    h("button", { role: "menuitem", class: "um-item", onclick: () => { menu.remove(); passwordDialog(); } }, icon("lock"), "變更密碼"),
    h("button", { role: "menuitem", class: "um-item bad", onclick: async () => { menu.remove(); try { await post("/api/cloud/logout"); } catch { /* ignore */ } location.reload(); } }, icon("x"), "登出"));
  document.body.append(menu);
  const r = anchor.getBoundingClientRect();
  menu.style.left = Math.min(r.right + 8, innerWidth - menu.offsetWidth - 8) + "px";
  menu.style.bottom = Math.max(8, innerHeight - r.bottom) + "px";
  const off = (e) => { if (!menu.contains(e.target)) { menu.remove(); document.removeEventListener("mousedown", off, true); } };
  setTimeout(() => document.addEventListener("mousedown", off, true), 0);
  document.addEventListener("keydown", function esc(e) { if (e.key === "Escape") { menu.remove(); document.removeEventListener("keydown", esc); } });
}

export function passwordDialog() {
  const a = h("input", { type: "password", autocomplete: "new-password", "aria-label": "新密碼", autofocus: true }), b = h("input", { type: "password", autocomplete: "new-password", "aria-label": "確認新密碼" });
  const msg = h("div", { class: "small bad" });
  modal({ title: "變更密碼", body: h("div", { class: "col" }, h("label", { class: "field" }, "新密碼（至少 8 個字）", a), h("label", { class: "field" }, "再輸入一次", b), msg),
    actions: [{ label: "取消" }, { label: "變更", kind: "primary", onClick: async () => {
      if (a.value !== b.value) { msg.textContent = "兩次輸入的密碼不一樣"; return false; }
      try { await post("/api/cloud/password", { new: a.value }); toast("密碼已變更", "ok", 2500); } catch (e) { msg.textContent = e.message; return false; } } }] });
}

export function updatePill() {
  const up = CLOUD.update || {};
  if (!CLOUD.enabled && !(up.behind > 0)) return null;
  if (!(up.behind > 0)) return null;
  return h("button", { class: "pill warn", onclick: updateDialog, title: "有新版本可以更新" }, icon("refresh"), h("span", { class: "hide-m", text: "有新版本" }));
}

export function updateDialog() {
  const up = CLOUD.update || {};
  const msg = h("div", { class: "small mt", "aria-live": "polite" });
  modal({ title: "更新 CPE 練功系統", body: h("div", null, h("p", { text: `目前版本 ${CLOUD.version || ""}，有 ${up.behind || 0} 項更新：` }),
    h("ul", { class: "small" }, (up.commits || []).map((c) => h("li", null, h("span", { class: "mono", text: c.sha + " " }), c.subject))),
    h("p", { class: "muted small", text: "更新會自動重新啟動程式；學習進度與雲端資料不受影響。若更新失敗會自動退回舊版。" }), msg),
    actions: [{ label: "稍後" }, { label: "立即更新", kind: "primary", keep: true, onClick: async () => { try { await runUpdate((m) => { msg.textContent = m; }); } catch (e) { msg.textContent = e.message; } return false; } }] });
}

// 公告：每一則只彈一次
export function showAnnouncement() {
  const a = CLOUD.app && CLOUD.app.announcement;
  if (!a) return;
  const key = "ann." + a.length + ":" + a.slice(0, 24);
  if (pref.get(key, false)) return;
  pref.set(key, true);
  toast("📢 " + a, "", 12000);
}
