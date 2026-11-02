// 登入閘門：學號＋密碼、首次改密碼、授權／IP 被拒、必須更新。全螢幕，背景是院館照片。
import { h, icon, clear, toast } from "./dom.js";
import { get, post } from "./api.js";

const ORG = "靜宜大學 晶片設計學士學位學程";
const REASON_TITLE = { inactive: "帳號尚未開通", not_started: "授權期間還沒開始", expired: "授權已到期", ip_denied: "目前的網路位址不被允許", ip_unknown: "無法判斷網路位址", no_profile: "找不到帳號資料", offline_expired: "太久沒有連線驗證", offline_never: "需要連上網路" };

export const fmtT = (s) => (s ? new Date(s).toLocaleString("zh-TW", { hour12: false }) : "—");

export function brandHeader() {
  return h("header", { class: "gate-top" }, h("img", { class: "gate-logo", src: "/static/img/icd-logo.png", alt: ORG, width: 330, height: 68 }));
}

let root = null;
function mountGate() {
  if (root) return root;
  root = h("div", { class: "gate", role: "dialog", "aria-modal": "true", "aria-label": "登入" });
  document.body.append(root);
  document.body.classList.add("gated");
  return root;
}
function unmountGate() { root?.remove(); root = null; document.body.classList.remove("gated"); }

// 取得授權：回傳時一定是已通過（或雲端功能未啟用）。
export async function ensureAccess() {
  for (;;) {
    let st;
    try { st = await get("/api/cloud/status"); } catch (e) { st = { enabled: true, logged_in: false, allowed: false, error: e.message, app: {} }; }
    if (!st.enabled || st.allowed) { unmountGate(); return st; }
    await showStep(st);
  }
}

function showStep(st) {
  return new Promise((resolve) => {
    const box = mountGate(); clear(box);
    const card = h("main", { class: "gate-card" });
    box.append(brandHeader(), card, h("footer", { class: "gate-foot", text: `${ORG} · CPE 練功系統 ${st.version || ""}` }));
    const done = () => resolve();
    const msg = h("div", { class: "gate-msg", role: "alert", "aria-live": "polite" });
    const busy = async (btn, fn) => { btn.disabled = true; msg.textContent = ""; try { await fn(); } catch (e) { msg.textContent = e.message; btn.disabled = false; } };

    if (st.need_update) return card.append(updateStep(st, done, msg, busy));
    if (!st.logged_in) return card.append(loginStep(st, done, msg, busy));
    if (st.must_change_pw) return card.append(passwordStep(st, done, msg, busy));
    return card.append(deniedStep(st, done, msg, busy));
  });
}

function header(title, sub) {
  return h("div", { class: "gate-h" }, h("div", { class: "gate-kicker", text: "CPE 練功系統" }), h("h1", { text: title }), sub ? h("p", { class: "muted", text: sub }) : null);
}
function announce(st) {
  const a = (st.app || {}).announcement;
  return a ? h("div", { class: "gate-note" }, icon("bulb"), h("span", { text: a })) : null;
}

function loginStep(st, done, msg, busy) {
  const sid = h("input", { type: "text", autocomplete: "username", autocapitalize: "none", spellcheck: "false", placeholder: "學號", "aria-label": "學號", autofocus: true });
  const pw = h("input", { type: "password", autocomplete: "current-password", placeholder: "密碼", "aria-label": "密碼" });
  const btn = h("button", { class: "btn primary lg", type: "submit" }, "登入");
  const form = h("form", { class: "col", onsubmit: (e) => { e.preventDefault(); busy(btn, async () => { await post("/api/cloud/login", { sid: sid.value, password: pw.value }); done(); }); } },
    h("label", { class: "field" }, "學號", sid), h("label", { class: "field" }, "密碼", pw), btn, msg);
  return [header("登入", "使用學號與密碼。帳號由學程管理員開通；第一次登入需要連上網路。"), form, announce(st),
    st.last_error ? h("p", { class: "xs muted", text: st.last_error }) : null, h("p", { class: "xs muted", text: "忘記密碼或尚未開通？請洽學程管理員。" })];
}

function passwordStep(st, done, msg, busy) {
  const a = h("input", { type: "password", autocomplete: "new-password", placeholder: "新密碼（至少 8 個字）", "aria-label": "新密碼", autofocus: true });
  const b = h("input", { type: "password", autocomplete: "new-password", placeholder: "再輸入一次", "aria-label": "確認新密碼" });
  const btn = h("button", { class: "btn primary lg", type: "submit" }, "設定新密碼並繼續");
  const form = h("form", { class: "col", onsubmit: (e) => { e.preventDefault(); if (a.value !== b.value) { msg.textContent = "兩次輸入的密碼不一樣"; return; } busy(btn, async () => { await post("/api/cloud/password", { new: a.value }); done(); }); } },
    h("label", { class: "field" }, "新密碼", a), h("label", { class: "field" }, "確認新密碼", b), btn, msg,
    h("button", { class: "btn ghost sm", type: "button", onclick: async () => { await post("/api/cloud/logout"); done(); } }, "改用別的帳號"));
  return [header("第一次登入：請設定新密碼", `${(st.user || {}).name || (st.user || {}).student_id || ""}，你的初始密碼只用這一次。`), form];
}

function deniedStep(st, done, msg, busy) {
  const u = st.user || {};
  const lines = [];
  if (st.reason === "expired" || st.reason === "not_started") lines.push(`授權期間：${fmtT(u.valid_from)} ～ ${fmtT(u.valid_until)}`);
  if (st.reason === "ip_denied") lines.push(`伺服器看到的你的位址：${(st.access || {}).ip || "未知"}`);
  const again = h("button", { class: "btn primary", onclick: (e) => busy(e.currentTarget, async () => { await post("/api/cloud/recheck"); done(); }) }, icon("refresh"), "重新檢查");
  return [header(REASON_TITLE[st.reason] || "目前無法使用", st.message || "請洽學程管理員。"), h("ul", { class: "small muted" }, lines.map((l) => h("li", { text: l }))),
    h("div", { class: "row wrap" }, again, h("button", { class: "btn", onclick: async () => { await post("/api/cloud/logout"); done(); } }, "登出")), msg, announce(st)];
}

// ---- 更新 ----
export async function runUpdate(setMsg) {
  setMsg("更新中…請不要關閉視窗");
  const r = await post("/api/update/apply");
  if (r.status === "updated") {
    setMsg(`已更新到 ${r.new_version || "新版"}，正在重新啟動…`);
    await post("/api/restart");
    const t0 = Date.now();
    await new Promise((res) => setTimeout(res, 1800));
    while (Date.now() - t0 < 40000) {
      try { const p = await fetch("/api/ping"); if (p.ok) { location.reload(); return r; } } catch { /* 還在重啟 */ }
      await new Promise((res) => setTimeout(res, 800));
    }
    setMsg("請手動重新開啟程式。");
  } else if (r.status === "up_to_date") setMsg("已經是最新版。");
  else setMsg(r.reason || "無法自動更新：" + r.status);
  return r;
}

function updateStep(st, done, msg, busy) {
  const info = st.app || {};
  const btn = h("button", { class: "btn primary lg", onclick: (e) => busy(e.currentTarget, async () => { await runUpdate((m) => { msg.textContent = m; }); }) }, icon("refresh"), "立即更新");
  return [header("需要更新才能繼續", `學程要求的最低版本是 ${info.min_version}，你目前是 ${st.version}。`), info.update_note ? h("p", { class: "small", text: info.update_note }) : null,
    btn, msg, h("p", { class: "xs muted", text: "更新不會動到你的學習進度。若自動更新失敗，請依安裝教學重新安裝，或洽管理員。" })];
}

// 使用中途被擋（授權到期、被停用、IP 變了）：回到閘門，通過後重新載入。
let reauth = false;
window.addEventListener("cpe:auth", async () => {
  if (reauth || root) return;
  reauth = true;
  try { await ensureAccess(); location.reload(); } finally { reauth = false; }
});
