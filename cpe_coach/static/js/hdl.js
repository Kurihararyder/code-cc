import { h, clear, toast } from "./dom.js";
import { get, post } from "./api.js";
import { go } from "./router.js";
import { skeleton, empty, notify } from "./widgets.js";
import { render as md } from "./md.js";
import { tutorBox } from "./tracks.js";

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
  const wavebox = h("div", { class: "wavebox", style: { overflowX: "auto" } });
  const showWave = async () => {
    wavebox.textContent = "產生波形中…";
    try {
      const r = await post("/api/hdl/wave", { id, code: ta.value });
      if (!r.ok) { wavebox.replaceChildren(h("pre", { class: "mono small", text: r.message + "\n" + (r.log || "") })); return; }
      wavebox.replaceChildren(drawWave(r));
    } catch (e) { wavebox.textContent = ""; toast(e.message, "bad"); }
  };
  view.append(h("div", { class: "page" },
    h("div", { class: "page-head" }, h("div", null, h("h1", { text: `${P.id} ${P.title}` }), h("p", { class: "muted", text: `${P.track}・單元 ${P.unit}` })),
      h("button", { class: "btn", onclick: () => go("/hdl") }, "全部題目")),
    P.tools[P.track] ? null : h("div", { class: "callout" }, h("span", { text: P.track === "verilog" ? "找不到 iverilog／vvp，無法判題。請先安裝 Icarus Verilog。" : "找不到 tclsh，無法判題。" })),
    h("div", { class: "card pad" }, md(P.statement)),
    h("div", { class: "card pad mt" }, tutorBox(P.track, P.unit, () => ({ pid: P.id, code: ta.value, log: out.textContent }))),
    h("div", { class: "card pad mt" }, ta, h("div", { class: "row wrap mt" }, h("button", { class: "btn primary", onclick: run }, "送出判題（Ctrl+Enter）"),
      P.track === "verilog" ? h("button", { class: "btn", onclick: showWave }, "看波形") : null, verdict), out, wavebox)));
}

const NS = "http://www.w3.org/2000/svg";
const el = (n, a, t) => { const e = document.createElementNS(NS, n); for (const k in a || {}) e.setAttribute(k, a[k]); if (t != null) e.textContent = t; return e; };

// 以「有變化的時間點」為等距的橫軸；z_r／z_d 這類 _r（參考）與 _d（你的）成對的訊號放在一起，方便對照。
export function drawWave(w) {
  const L = 130, step = 46, rowH = 30, n = w.times.length;
  const order = [...w.signals].sort((a, b) => (a.name.replace(/_[dr]$/, "") === b.name.replace(/_[dr]$/, "") ? a.name.localeCompare(b.name) : 0));
  const svg = el("svg", { width: L + step * n + 10, height: 22 + rowH * order.length, role: "img", "aria-label": "模擬波形（_r 是參考設計，_d 是你的設計）", class: "wave" });
  w.times.forEach((t, i) => svg.append(el("text", { x: L + i * step + 2, y: 12, "font-size": 9, fill: "currentColor", opacity: 0.55 }, (t / 1000) + "ns")));
  order.forEach((s, r) => {
    const y0 = 20 + r * rowH, v = w.values[s.name];
    svg.append(el("text", { x: 4, y: y0 + 18, "font-size": 12, fill: "currentColor", "font-family": "monospace" }, s.name + (s.width > 1 ? `[${s.width - 1}:0]` : "")));
    for (let i = 0; i < n; i++) {
      const x = L + i * step, val = v[i], bad = /[xz]/.test(val);
      if (s.width === 1) {
        const y = val === "1" ? y0 + 4 : y0 + 22;
        svg.append(el("line", { x1: x, x2: x + step, y1: y, y2: y, stroke: bad ? "#d33" : "currentColor", "stroke-width": 2 }));
        if (i && v[i - 1] !== val) svg.append(el("line", { x1: x, x2: x, y1: y0 + 4, y2: y0 + 22, stroke: "currentColor", "stroke-width": 1, opacity: 0.6 }));
      } else {
        svg.append(el("rect", { x: x + 1, y: y0 + 4, width: step - 2, height: 18, fill: "none", stroke: bad ? "#d33" : "currentColor", opacity: 0.8 }));
        const hex = bad ? "x" : parseInt(val, 2).toString(16);
        svg.append(el("text", { x: x + step / 2, y: y0 + 17, "font-size": 10, "text-anchor": "middle", fill: "currentColor", "font-family": "monospace" }, hex.length > 6 ? hex.slice(-6) : hex));
      }
    }
  });
  return svg;
}
