// 外殼：左側導覽、頂列、全域狀態更新與考試倒數。
import { h, icon, $, clear, fmtDur, toast } from "./dom.js";
import { get, onConnection } from "./api.js";
import { S, emit, pref, applyTheme, stageColor } from "./state.js";
import { go, where } from "./router.js";
import { openPalette } from "./palette.js";

const NAV = [["home", "今日", "home"], ["practice", "練習", "code"], ["course", "課程", "map"], ["stats", "統計", "chart"], ["settings", "設定", "settings"]];
let tick = null;

export function buildShell() {
  const rail = $("#rail"); clear(rail);
  rail.append(h("a", { class: "brand", href: "#/home", "aria-label": "CPE 教練", title: "CPE 教練" }, icon("code", "lg")));
  NAV.forEach(([k, label, ic], i) => {
    if (k === "settings") rail.append(h("div", { class: "spacer" }));
    rail.append(h("a", { class: "navbtn", href: "#/" + k, dataset: { nav: k } }, icon(ic), h("span", { text: label }), k === "home" ? h("span", { class: "dot", id: "dueDot", hidden: true }) : null));
  });
  onConnection((ok) => { $("#offline").hidden = ok; });
  window.addEventListener("routechange", markNav);
  paintTop();
}

function markNav() {
  const cur = where().name;
  document.querySelectorAll("[data-nav]").forEach((a) => { if (a.dataset.nav === cur) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
}

export function paintTop() {
  const top = $("#topbar"); clear(top);
  const u = S.unit;
  top.append(
    h("div", { class: "crumb grow" }, u ? [h("span", { class: "stagedot", style: { "--sc": stageColor(u.stage) } }),
      h("span", { class: "hide-m muted", text: `單元 ${u.n}/${u.total}` }), h("b", { text: u.title }), h("span", { class: "hide-m muted", text: `· 第 ${u.weeks[0]}${u.weeks[1] > u.weeks[0] ? "–" + u.weeks[1] : ""} 週` })]
      : h("b", { text: "課程已完成 🎓" })),
    S.exam ? h("button", { class: "pill bad", id: "examChip", onclick: () => go("/home"), title: "考試進行中" }, icon("clock"), h("span", { id: "examLeft", text: fmtDur(examLeft()) })) : null,
    h("button", { class: "pill " + (S.ai.available ? "ok" : "warn"), onclick: () => go("/settings"), title: S.ai.available ? "AI 就緒" : "尚未設定 API 金鑰" },
      h("span", { class: "led" + (S.ai.available ? " on" : "") }), h("span", { class: "hide-m", text: S.ai.available ? S.ai.model : "AI 未設定" })),
    h("button", { class: "searchbtn", onclick: openPalette, "aria-label": "搜尋與指令" }, icon("search"), h("span", { class: "t", text: "搜尋題目與指令" }), h("kbd", { text: navigator.platform.includes("Mac") ? "⌘K" : "Ctrl K" })),
    h("button", { class: "btn ghost icon", onclick: cycleTheme, "aria-label": "切換外觀", title: "外觀：" + { auto: "跟隨系統", light: "淺色", dark: "深色" }[pref.get("theme", "auto")] },
      icon(effectiveDark() ? "moon" : "sun")));
  const dot = $("#dueDot"); if (dot) { dot.hidden = !S.due; dot.textContent = S.due; }
}

const effectiveDark = () => { const t = document.documentElement.dataset.theme; return t === "dark" || (t === "auto" && matchMedia("(prefers-color-scheme: dark)").matches); };
function cycleTheme() {
  const order = ["auto", "light", "dark"]; const next = order[(order.indexOf(pref.get("theme", "auto")) + 1) % 3];
  pref.set("theme", next); applyTheme(next); paintTop(); toast("外觀：" + { auto: "跟隨系統", light: "淺色", dark: "深色" }[next], "", 1400);
}

const examLeft = () => Math.max(0, (S.exam?.left ?? 0) - Math.floor((Date.now() - S.examAt) / 1000));

export async function refreshState() {
  try {
    const s = await get("/api/state");
    S.ai = s.ai; S.unit = s.unit; S.due = s.due; S.exam = s.exam; S.examAt = Date.now();
  } catch { /* 離線時保留舊狀態 */ }
  paintTop(); markNav(); emit(); armTimer();
}
function armTimer() {
  clearInterval(tick); tick = null;
  if (!S.exam) return;
  tick = setInterval(() => {
    const el = $("#examLeft"); const left = examLeft();
    if (el) el.textContent = fmtDur(left);
    if (left === 0 && !S._notified) { S._notified = true; toast("考試時間到了。之後的提交不計分，請交卷。", "warn", 9000); }
  }, 1000);
  S._notified = false;
}
