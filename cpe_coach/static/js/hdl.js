import { h, clear, toast } from "./dom.js";
import { get, post } from "./api.js";
import { go } from "./router.js";
import { skeleton, empty, notify } from "./widgets.js";
import { render as md } from "./md.js";

export async function mountHdl(view, params) {
  view.append(h("div", { class: "page" }, h("div", { class: "card pad" }, skeleton(5))));
  const id = params[0];
  if (!id) {
    let L; try { L = await get("/api/hdl"); } catch (e) { clear(view); view.append(h("div", { class: "page" }, empty("alert", e.message))); return; }
    clear(view);
    view.append(h("div", { class: "page" }, h("div", { class: "page-head" }, h("div", null, h("h1", { text: "Verilog／Tcl 練習題" }),
      h("p", { text: `判題工具：iverilog ${L.tools.verilog ? "已安裝" : "未安裝"}、tclsh ${L.tools.tcl ? "已安裝" : "未安裝"}` }))),
      h("div", { class: "card pad" }, h("ul", { class: "list" }, L.problems.map((p) => h("li", null,
        h("button", { class: "li", onclick: () => go("/hdl/" + p.id) }, h("span", { class: "status" + (p.done ? " done" : "") }, p.done ? "✓" : ""), h("span", { class: "mono", text: p.id }),
          h("span", { class: "grow", text: p.title }), h("span", { class: "tag", text: p.track }))))))));
    return;
  }
  let P; try { P = await get("/api/hdl/problem", { id }); } catch (e) { clear(view); view.append(h("div", { class: "page" }, empty("alert", e.message))); return; }
  clear(view);
  const ta = h("textarea", { class: "mono", spellcheck: "false", rows: 22, style: { width: "100%", tabSize: 4 }, "aria-label": "程式碼" });
  ta.value = P.saved ?? P.template;
  const out = h("pre", { class: "mono small", style: { whiteSpace: "pre-wrap" } });
  const verdict = h("div");
  const run = async () => {
    verdict.textContent = "判題中…";
    try {
      const r = await post("/api/hdl/run", { id, code: ta.value });
      verdict.replaceChildren(h("span", { class: "pill " + (r.verdict === "AC" ? "ok" : "bad"), text: r.verdict }), " " + r.message);
      out.textContent = r.log || "";
      notify();
    } catch (e) { verdict.textContent = ""; toast(e.message, "bad"); }
  };
  ta.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); run(); }
    if (e.key === "Tab") { e.preventDefault(); const s = ta.selectionStart; ta.setRangeText("    ", s, ta.selectionEnd, "end"); }
  });
  view.append(h("div", { class: "page" },
    h("div", { class: "page-head" }, h("div", null, h("h1", { text: `${P.id} ${P.title}` }), h("p", { class: "muted", text: `${P.track}・單元 ${P.unit}` })),
      h("button", { class: "btn", onclick: () => go("/hdl") }, "全部題目")),
    P.tools[P.track] ? null : h("div", { class: "callout" }, h("span", { text: P.track === "verilog" ? "找不到 iverilog／vvp，無法判題。請先安裝 Icarus Verilog。" : "找不到 tclsh，無法判題。" })),
    h("div", { class: "card pad" }, md(P.statement)),
    h("div", { class: "card pad mt" }, ta, h("div", { class: "row wrap mt" }, h("button", { class: "btn primary", onclick: run }, "送出判題（Ctrl+Enter）"), verdict), out)));
}
