// 指令面板（Ctrl/⌘ + K）：跳頁、切換主題、搜尋題目。
import { h, icon, modal, clear, debounce, stars } from "./dom.js";
import { get } from "./api.js";
import { go } from "./router.js";
import { pref, applyTheme } from "./state.js";

const ACTIONS = [
  { label: "前往：今日", hint: "首頁", run: () => go("/home") },
  { label: "前往：練習", hint: "工作區", run: () => go("/practice") },
  { label: "前往：課程地圖", hint: "52 個單元", run: () => go("/course") },
  { label: "前往：統計", hint: "學習紀錄", run: () => go("/stats") },
  { label: "前往：設定", hint: "AI 金鑰、外觀", run: () => go("/settings") },
  { label: "切換深色／淺色", hint: "外觀", run: () => { const cur = document.documentElement.dataset.theme; const next = cur === "dark" ? "light" : "dark"; pref.set("theme", next); applyTheme(next); } },
];

export function openPalette() {
  const input = h("input", { type: "search", placeholder: "輸入題號、題目名稱，或指令…", "aria-label": "搜尋", autofocus: true, autocomplete: "off" });
  const list = h("ul", { class: "list", role: "listbox" }); let items = [], idx = 0;
  const paint = () => {
    clear(list); let lastGrp = "";
    items.forEach((it, i) => {
      if (it.grp !== lastGrp) { list.append(h("li", { class: "grp", text: it.grp })); lastGrp = it.grp; }
      list.append(h("li", { role: "option" }, h("button", { class: "li", "aria-selected": i === idx ? "true" : "false", "aria-current": i === idx ? "true" : "false", onclick: () => choose(it), onmousemove: () => { idx = i; mark(); } },
        icon(it.icon || "chevron"), h("span", { class: "grow", text: it.label }), it.hint ? h("span", { class: "muted xs", text: it.hint }) : null)));
    });
    if (!items.length) list.append(h("li", { class: "empty", text: "沒有符合的結果" }));
  };
  const mark = () => list.querySelectorAll("button.li").forEach((b, i) => b.setAttribute("aria-current", i === idx ? "true" : "false"));
  let m;
  const choose = (it) => { m.close(); it.run(); };
  let stale = false;
  const search = debounce(async () => {
    const q = input.value.trim().toLowerCase(); stale = false;
    const acts = ACTIONS.filter((a) => !q || a.label.toLowerCase().includes(q) || (a.hint || "").includes(q)).map((a) => ({ ...a, grp: "指令", icon: "cmd" }));
    let probs = [];
    try { probs = (await get("/api/search", { q })).results.map((p) => ({ grp: "題目", icon: "code", label: `${p.id}　${p.title}`, hint: stars(p.difficulty) + " " + p.topic, run: () => go("/practice/" + p.id) })); } catch { /* 連線中斷時只顯示指令 */ }
    items = q ? [...probs, ...acts] : [...acts, ...probs.slice(0, 8)]; idx = 0; paint();
  }, 120);
  input.addEventListener("input", () => { stale = true; search(); });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); idx = Math.min(items.length - 1, idx + 1); mark(); list.querySelectorAll("button.li")[idx]?.scrollIntoView({ block: "nearest" }); }
    if (e.key === "ArrowUp") { e.preventDefault(); idx = Math.max(0, idx - 1); mark(); list.querySelectorAll("button.li")[idx]?.scrollIntoView({ block: "nearest" }); }
    if (e.key === "Enter") { e.preventDefault(); (async () => { if (stale) await search.flush(); if (items[idx]) choose(items[idx]); })(); }
  });
  const body = h("div", { class: "palette modal" }, input, list);
  m = modal({ body: h("div"), label: "指令面板" });
  const box = m.el; box.className = "palette modal"; clear(box); box.append(input, list); input.focus(); search.flush();
}
