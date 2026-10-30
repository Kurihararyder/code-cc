// 「今日計畫」：給定今天有幾分鐘，自動排出重練、續做、新題、檢核、每週測驗與工程任務。
import { h, icon, clear, toast } from "./dom.js";
import { get, post } from "./api.js";
import { go } from "./router.js";
import { pref } from "./state.js";
import { skeleton, empty, startMockDialog } from "./widgets.js";

const KIND = { review: ["重練", "bad"], continue: ["續做", "warn"], new: ["新題", "accent"], past: ["歷屆", "info"], gate: ["檢核", "ok"], weekly: ["每週測驗", "info"], eng: ["工程", ""], exam: ["考試", "bad"] };
const BUDGETS = [15, 30, 60, 90];

export function planCard() {
  const box = h("section", { class: "card pad mt", "aria-label": "今日計畫" });
  const paint = async () => {
    const minutes = pref.get("planMin", 30);
    clear(box); box.append(skeleton(3));
    let p; try { p = await get("/api/plan", { minutes }); } catch (e) { clear(box); box.append(empty("alert", e.message)); return; }
    clear(box);
    box.append(h("div", { class: "card-h" }, h("h3", null, icon("clock"), "今日計畫"),
      h("div", { class: "seg", role: "group", "aria-label": "今天有多少分鐘" }, BUDGETS.map((m) => h("button", { "aria-pressed": String(m === minutes), onclick: () => { pref.set("planMin", m); paint(); } }, `${m} 分`)))));
    if (!p.items.length) box.append(empty("check", "今天沒有必做的事。可以自由挑一題，或到『課程』看下一個單元。"));
    else box.append(h("ol", { class: "plan" }, p.items.map((it, i) => item(it, i + 1))));
    box.append(h("div", { class: "row wrap mt small muted" }, h("span", { text: `合計約 ${p.total_est} 分鐘` }), p.done_min ? h("span", { text: `· 已完成 ${p.done_min} 分鐘的份量` }) : null,
      !p.calibrated ? h("span", { text: "· 預估時間用預設值，解出 3 題後會依你的速度調整" }) : h("span", { text: `· 依你的速度調整（×${p.factor}）` })));
    p.later.forEach((it) => box.append(h("div", { class: "callout mt" }, icon("clock"), h("div", null, h("b", { text: it.title }), `（約 ${it.est} 分）— ${it.why}`))));
  };
  paint();
  return box;
}

function item(it, n) {
  const [label, tone] = KIND[it.kind] || [it.kind, ""];
  const go_ = async () => {
    try {
      if (it.kind === "review") { try { await post("/api/new", { id: it.id, fresh: true }); } catch { /* 沒有舊檔也沒關係 */ } go("/practice/" + it.id); }
      else if (it.id && ["continue", "new", "past"].includes(it.kind)) go("/practice/" + it.id);
      else if (it.kind === "gate") go("/course");
      else if (it.kind === "weekly") startMockDialog();
      else if (it.kind === "eng") go("/course/eng");
      else if (it.kind === "exam") go("/exam");
    } catch (e) { toast(e.message, "bad"); }
  };
  return h("li", { class: it.done ? "done" : "" }, h("button", { class: "li", onclick: go_ },
    h("span", { class: "status" + (it.done ? " done" : "") }, it.done ? icon("check") : h("span", { class: "xs", text: String(n) })),
    h("span", { class: "pill " + tone, text: label }), it.id && it.kind !== "eng" ? h("span", { class: "mono small", text: it.id }) : null,
    h("span", { class: "grow" }, h("span", { text: it.title }), h("div", { class: "muted xs", text: it.why })),
    h("span", { class: "muted small", text: `~${it.est} 分` }), icon("chevron")));
}
