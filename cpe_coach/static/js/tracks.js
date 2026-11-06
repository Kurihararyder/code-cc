import { h, icon, clear, toast, drawer, confirmDialog } from "./dom.js";
import { get, post } from "./api.js";
import { go } from "./router.js";
import { stageColor } from "./state.js";
import { progress, skeleton, empty } from "./widgets.js";
import { inline } from "./md.js";

export const TRACKS = [["py", "Python"], ["cpp", "C++"], ["verilog", "Verilog"], ["tcl", "Tcl"]];

export function trackTabs(cur) {
  return h("div", { class: "seg", role: "tablist", "aria-label": "課程軌道" },
    TRACKS.map(([k, n]) => h("button", { role: "tab", "aria-selected": String(k === cur), onclick: () => go(k === "py" ? "/course" : "/course/" + k) }, n)));
}

export async function mountTrack(view, params) {
  const track = params[0];
  view.append(h("div", { class: "page" }, h("div", { class: "card pad" }, skeleton(6))));
  let C;
  try { C = await get("/api/track", { track }); } catch (e) { clear(view); view.append(h("div", { class: "page" }, empty("alert", e.message))); return; }
  clear(view);
  const page = h("div", { class: "page" });
  page.append(h("div", { class: "page-head" }, h("div", null, h("h1", { text: C.name }),
    h("p", { text: `${C.total_weeks} 週・${C.total} 個單元・${C.stages.length} 個階段。這條軌道的練習題還在規劃中，單元讀完、做完專題後手動標記完成。` })),
    h("div", { class: "row wrap" }, trackTabs(track), h("div", { style: { width: "180px" } }, progress(C.done, C.total)), h("span", { class: "small muted", text: `${C.done}/${C.total} 單元完成` }))));
  if (C.advice && C.advice.length) page.append(h("section", { class: "card pad mt", "aria-label": "學習路徑建議" }, h("h3", { text: "學習路徑建議" }),
    h("ul", { class: "small" }, C.advice.map((a) => h("li", null, h("button", { class: "linkish", onclick: () => openTrackUnit(track, a.unit) }, a.text))))));
  C.stages.forEach((s) => {
    page.append(h("section", { class: "stage", style: { "--sc": stageColor(s.stage) }, "aria-label": `階段 ${s.stage}` },
      h("div", { class: "stage-h" }, h("span", { class: "bar" }), h("h2", { text: s.name }), h("span", { class: "pill", text: `第 ${s.weeks[0]}–${s.weeks[1]} 週` }), h("span", { class: "pill accent", text: s.goal }), h("span", { class: "muted small", text: `${s.done}/${s.units.length} 完成` })),
      h("div", { class: "units" }, s.units.map((u) => h("button", { class: "unit " + u.status, onclick: () => openTrackUnit(track, u.n), "aria-label": `單元 ${u.n} ${u.title}` },
        h("span", { class: "n", text: `單元 ${u.n}` }), h("span", { class: "t", text: u.title }),
        h("span", { class: "muted xs", text: `第 ${u.weeks[0]}${u.weeks[1] > u.weeks[0] ? "–" + u.weeks[1] : ""} 週` }),
        h("span", { class: "st" }, u.status === "done" ? h("span", { class: "status done" }, icon("check")) : u.status === "current" ? h("span", { class: "pill accent", text: "目前" }) : null))))));
  });
  view.append(page);
  if (params[1] && /^\d+$/.test(params[1])) openTrackUnit(track, +params[1]);
}

async function openTrackUnit(track, n) {
  let D; try { D = await get("/api/track/unit", { track, n }); } catch (e) { toast(e.message, "bad"); return; }
  const sec = (title, items) => items?.length ? h("div", { class: "mt" }, h("h4", { text: title }), h("ul", { class: "small" }, items.map((x) => h("li", null, inline(x))))) : null;
  drawer((close) => h("div", { class: "pad" },
    h("div", { class: "row" }, h("span", { class: "muted small", text: `階段 ${D.stage} · 單元 ${D.n} · 第 ${D.weeks[0]}${D.weeks[1] > D.weeks[0] ? "–" + D.weeks[1] : ""} 週` }), h("span", { class: "grow" }), h("button", { class: "btn ghost icon", "aria-label": "關閉", onclick: close }, icon("x"))),
    h("h2", { text: D.title, style: { margin: "8px 0 4px" } }), h("p", { class: "muted", text: D.goal }),
    sec("要學的", D.learn),
    D.drills.length ? h("div", { class: "mt" }, h("h4", { text: "必做練習" }), h("ul", { class: "list" }, D.drills.map((p) => h("li", null, h("button", { class: "li", onclick: () => { close(); go("/practice/" + p.id); } },
      h("span", { class: "status" + (p.done ? " done" : "") }, p.done ? icon("check") : null), h("span", { class: "mono", text: p.id }), h("span", { class: "grow", text: p.title })))))) : null,
    D.planned.length ? h("div", { class: "mt" }, h("h4", { text: "題目" }), h("ul", { class: "small" }, D.planned.map((p) => h("li", null, p.available ? h("button", { class: "linkish", onclick: () => { close(); go("/hdl/" + p.id); } }, (p.done ? "✓ " : "") + p.id + " " + p.title + "（可練）") : h("span", { class: "mono", text: p.id }), p.available ? "：" : " " + p.title + "（規劃中）：", inline(p.topic))))) : null,
    sec("專題", D.build),
    D.readings.length ? h("div", { class: "mt" }, h("h4", { text: "要讀的章節與重點" }), h("ul", { class: "small" }, D.readings.map((r) => h("li", null, inline(r.label || r.where), r.focus?.length ? h("div", { class: "muted xs", text: "重點：" + r.focus.join("；") }) : null)))) : null,
    D.weekly.length ? h("div", { class: "mt" }, h("h4", { text: "每週安排" }), h("ul", { class: "small" }, D.weekly.map((w) => h("li", null, h("b", { text: `第 ${w.week} 週` }), "　", inline([...(w.readings || []), ...(w.learn || [])].join("；"))))) ) : null,
    sec("常見陷阱", D.pitfalls), sec("自我檢查（不看資料回答）", D.check),
    D.resources.length ? h("div", { class: "mt" }, h("h4", { text: "教材" }), h("ul", { class: "small" }, D.resources.map((r) => h("li", null, r.url ? h("a", { href: r.url, target: "_blank", rel: "noopener noreferrer" }, r.name, " ", icon("external")) : r.name)))) : null,
    tutorBox(track, D.n),
    h("div", { class: "row wrap mt-lg" },
      D.status !== "done" ? h("button", { class: "btn primary", onclick: async () => { try { await post("/api/track/done", { track, n: D.n }); close(); go("/course/" + track); location.reload(); } catch (e) { toast(e.message, "bad"); } } }, icon("check"), "標記完成") : null,
      D.status === "upcoming" ? h("button", { class: "btn", onclick: async () => { if (!(await confirmDialog(`跳到單元 ${D.n}？`, "之前的單元會視為已完成。", "跳到這裡"))) return; try { await post("/api/track/goto", { track, n: D.n }); close(); location.reload(); } catch (e) { toast(e.message, "bad"); } } }, "跳到這個單元") : null)));
}

export function tutorBox(track, n, ctx) {
  const q = h("textarea", { rows: 3, maxlength: 2000, style: { width: "100%" }, placeholder: "卡住了？用自己的話問 AI 助教（它會引導你，不會直接給完整答案）", "aria-label": "問 AI 助教" });
  const out = h("div", { class: "small mt", "aria-live": "polite", style: { whiteSpace: "pre-wrap" } });
  const btn = h("button", { class: "btn", onclick: async () => {
    if (!q.value.trim()) { toast("先輸入問題", "bad"); return; }
    btn.disabled = true; out.textContent = "思考中…";
    try { const r = await post("/api/tutor", { track, n, question: q.value, ...(ctx ? ctx() : {}) }); out.textContent = r.answer; } catch (e) { out.textContent = ""; toast(e.message, "bad"); }
    btn.disabled = false;
  } }, "問 AI 助教");
  return h("div", { class: "mt" }, h("h4", { text: "AI 助教" }), q, h("div", { class: "row mt" }, btn), out);
}
