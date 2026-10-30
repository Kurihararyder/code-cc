import { h, icon, clear, toast, stars, drawer, confirmDialog } from "./dom.js";
import { get, post } from "./api.js";
import { go } from "./router.js";
import { stageColor } from "./state.js";
import { progress, skeleton, empty, notify, startGate } from "./widgets.js";
import { inline } from "./md.js";
import { engPanel } from "./engtasks.js";

export async function mountCourse(view, params) {
  view.append(h("div", { class: "page" }, h("div", { class: "card pad" }, skeleton(6))));
  let C;
  try { C = await get("/api/course"); } catch (e) { clear(view); view.append(h("div", { class: "page" }, empty("alert", e.message))); return; }
  clear(view);
  const page = h("div", { class: "page" });
  const tabs = h("div", { class: "seg", role: "tablist", "aria-label": "課程內容" },
    h("button", { role: "tab", "aria-selected": String(params[0] !== "eng"), onclick: () => go("/course") }, "課程地圖"),
    h("button", { role: "tab", "aria-selected": String(params[0] === "eng"), onclick: () => go("/course/eng") }, "工程任務"));
  if (params[0] === "eng") {
    page.append(h("div", { class: "page-head" }, h("div", null, h("h1", { text: "工程任務" }), h("p", { text: "從刷題進到真實工程：測試、對拍、SQL、CLI、API、部署、作品集。" })), tabs));
    page.append(await engPanel()); view.append(page); return;
  }
  page.append(h("div", { class: "page-head" }, h("div", null, h("h1", { text: "課程地圖" }), h("p", { text: `126 週・52 個單元・6 個階段。依課表你現在在第 ${C.week} 週。` })),
    h("div", { class: "row wrap" }, tabs, h("div", { style: { width: "180px" } }, progress(C.done, C.total)), h("span", { class: "small muted", text: `${C.done}/${C.total} 單元完成` }))));
  C.stages.forEach((s) => {
    const sc = stageColor(s.stage);
    page.append(h("section", { class: "stage", style: { "--sc": sc }, "aria-label": `階段 ${s.stage}` },
      h("div", { class: "stage-h" }, h("span", { class: "bar" }), h("h2", { text: `階段 ${s.stage} · ${s.name}` }), h("span", { class: "pill", text: `第 ${s.weeks[0]}–${s.weeks[1]} 週` }), h("span", { class: "pill accent", text: s.goal }), h("span", { class: "muted small", text: `${s.done}/${s.units.length} 完成` })),
      h("div", { class: "units" }, s.units.map((u) => unitCard(u, C.current)))));
  });
  view.append(page);
  if (params[0] && /^\d+$/.test(params[0])) openUnit(+params[0]);
}

function unitCard(u, cur) {
  const st = u.status;
  return h("button", { class: "unit " + st, onclick: () => openUnit(u.n), "aria-label": `單元 ${u.n} ${u.title}，${{ done: "已完成", current: "目前", upcoming: "尚未開始" }[st]}` },
    h("span", { class: "n", text: `單元 ${u.n}${u.lang === "cpp" ? " · C++" : ""}` }), h("span", { class: "t", text: u.title }),
    h("span", { class: "muted xs", text: `第 ${u.weeks[0]}${u.weeks[1] > u.weeks[0] ? "–" + u.weeks[1] : ""} 週${u.has_gate ? " · 有檢核" : ""}` }),
    h("span", { class: "st" }, st === "done" ? h("span", { class: "status done" }, icon("check")) : st === "current" ? h("span", { class: "pill accent", text: "目前" }) : null));
}

async function openUnit(n) {
  let D; try { D = await get("/api/unit", { n }); } catch (e) { toast(e.message, "bad"); return; }
  drawer((close) => {
    const sc = stageColor(D.stage);
    const probRow = (p) => h("li", null, h("button", { class: "li", onclick: () => { close(); go("/practice/" + p.id); }, disabled: !p.has_tests && false },
      h("span", { class: "status" + (p.done ? " done" : "") }, p.done ? icon("check") : null), h("span", { class: "mono", text: p.id }), h("span", { class: "grow", text: p.title }),
      !p.has_tests ? h("span", { class: "tag", text: "需匯入範例" }) : null, h("span", { class: "stars", text: stars(p.difficulty) })));
    const sec = (title, items) => items?.length ? h("div", { class: "mt" }, h("h4", { text: title }), h("ul", { class: "small" }, items.map((x) => h("li", null, inline(x))))) : null;
    const g = D.gate;
    return h("div", { class: "pad" },
      h("div", { class: "row" }, h("span", { class: "stagedot", style: { "--sc": sc } }), h("span", { class: "muted small", text: `階段 ${D.stage} · 單元 ${D.n} · 第 ${D.weeks[0]}${D.weeks[1] > D.weeks[0] ? "–" + D.weeks[1] : ""} 週` }), h("span", { class: "grow" }), h("button", { class: "btn ghost icon", "aria-label": "關閉", onclick: close }, icon("x"))),
      h("h2", { text: D.title, style: { margin: "8px 0 4px" } }), h("p", { class: "muted", text: D.goal }),
      h("div", { class: "row wrap" }, D.status === "done" ? h("span", { class: "pill ok", text: "已完成" }) : D.status === "current" ? h("span", { class: "pill accent", text: "目前單元" }) : h("span", { class: "pill", text: "尚未開始" }), D.lang === "cpp" ? h("span", { class: "pill info", text: "C++" }) : null),
      sec("要學的", D.learn),
      D.drills.length ? h("div", { class: "mt" }, h("h4", { text: "必做練習" }), h("ul", { class: "list" }, D.drills.map(probRow))) : null,
      D.anchors.length ? h("div", { class: "mt" }, h("h4", { text: "真題（選做）" }), h("ul", { class: "list" }, D.anchors.map(probRow)), h("p", { class: "muted xs", text: "真題需要自己匯入範例：cpe import <題號> <題目文字檔>" })) : null,
      D.past_pool ? pastPool(D.past_pool, close) : null,
      g ? h("div", { class: "callout mt" }, icon("target"), h("div", null, h("b", { text: "單元檢核" }), h("div", { class: "small", text: g.type === "mock" ? `模擬考（${g.kind}），至少答對 ${g.need} 題` : `${g.minutes} 分鐘、不看提示，${g.problems.map((p) => p.id).join("、")}，至少答對 ${g.need} 題${g.lang === "cpp" ? "（C++）" : ""}` }))) : h("div", { class: "callout mt" }, icon("flag" in {} ? "flag" : "target"), h("span", { text: "這個單元的檢核是實際報考 CPE。" })),
      sec("常見陷阱", D.pitfalls), sec("自我檢查（不看資料回答）", D.check), sec("要讀的章節", D.read), sec("延伸題庫", D.pool),
      D.resources.length ? h("div", { class: "mt" }, h("h4", { text: "教材" }), h("ul", { class: "small" }, D.resources.map((r) => h("li", null, h("a", { href: r.url, target: "_blank", rel: "noopener noreferrer" }, r.name, " ", icon("external")))))) : null,
      h("div", { class: "row wrap mt-lg" },
        D.status === "current" ? h("button", { class: "btn primary", onclick: () => { close(); go("/practice"); } }, icon("play"), "去練習") : null,
        D.status !== "current" ? h("button", { class: "btn", onclick: async () => { if (!(await confirmDialog(`跳到單元 ${D.n}？`, "之前的單元會被視為已完成。已有基礎時才建議跳關。", "跳到這裡"))) return; try { await post("/api/course/goto", { n: D.n }); notify(); close(); go("/home"); } catch (e) { toast(e.message, "bad"); } } }, "跳到這個單元") : null));
  });
}

function pastPool(pp, close) {
  const rows = pp.items.slice(0, 12).map((p) => h("li", null, h("button", { class: "li", disabled: !p.has_tests, onclick: () => { close(); go("/practice/" + p.id); } },
    h("span", { class: "status" + (p.solved ? " done" : "") }, p.solved ? icon("check") : null), h("span", { class: "mono", text: p.id }), h("span", { class: "grow", text: p.title }),
    !p.has_tests ? h("span", { class: "tag", text: "需貼上題目" }) : null, h("span", { class: "muted xs", text: p.accuracy + "%" }), h("span", { class: "stars", text: "★".repeat(p.stars || 1) }))));
  return h("div", { class: "mt" }, h("h4", { text: "歷屆題庫" }), h("p", { class: "muted xs", text: pp.label + (pp.items.length ? `（已匯入 ${pp.items.length} 題，${pp.ready} 題可練，${pp.solved} 題已解）` : "") }),
    pp.items.length ? h("ul", { class: "list" }, rows) : h("p", { class: "small muted", text: "還沒有匯入符合的歷屆題。到『考試』頁匯入歷屆清單與題目文字後，這裡會自動列出。" }),
    pp.items.length > 12 ? h("p", { class: "muted xs", text: `另有 ${pp.items.length - 12} 題` }) : null);
}
