import { $, h, toast, modal } from "./dom.js";
import { S, applyTheme, pref } from "./state.js";
import { route, render, go } from "./router.js";
import { buildShell, refreshState } from "./shell.js";
import { openPalette } from "./palette.js";
import { mountHome } from "./home.js";
import { mountWorkspace } from "./workspace.js";
import { mountCourse } from "./course.js";
import { mountStats } from "./stats.js";
import { mountSettings } from "./settings.js";
import { mountExam } from "./exam.js";

applyTheme();
route("home", mountHome); route("practice", mountWorkspace); route("course", mountCourse); route("exam", mountExam); route("stats", mountStats); route("settings", mountSettings);

document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openPalette(); return; }
  const t = e.target; const typing = t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable);
  if (!typing && e.key === "?") { e.preventDefault(); shortcuts(); }
});
function shortcuts() {
  const rows = [["Ctrl/⌘ + K", "搜尋題目與指令"], ["Ctrl/⌘ + Enter", "執行測試"], ["Ctrl/⌘ + S", "儲存"], ["Tab／Shift+Tab", "縮排／取消縮排"], ["Ctrl/⌘ + /", "切換註解"], ["選取文字", "跳出『問 AI』選單"], ["Esc", "關閉選單或視窗"], ["?", "顯示這份說明"]];
  modal({ title: "鍵盤快速鍵", body: h("dl", { class: "dl" }, rows.flatMap(([k, v]) => [h("dt", null, h("kbd", { text: k })), h("dd", { text: v })])), actions: [{ label: "關閉", kind: "primary" }] });
}

buildShell();
await refreshState();
await render();
window.addEventListener("cpe:changed", refreshState);
