import { h, clear, toast } from "./dom.js";
import { get, post } from "./api.js";
import { go } from "./router.js";
import { skeleton, empty, progress } from "./widgets.js";
import { render as md, codeBlock } from "./md.js";

const TRACK = { py: "Python", cpp: "C++", verilog: "Verilog", tcl: "Tcl" };

export async function mountGuide(view, params) {
  view.append(h("div", { class: "page" }, h("div", { class: "card pad" }, skeleton(5))));
  try {
    if (!params[0]) return await listView(view);
    return await quizView(view, params[0], params[1] || "all");
  } catch (e) { clear(view); view.append(h("div", { class: "page" }, empty("alert", e.message))); }
}

async function listView(view) {
  const { guides } = await get("/api/guides");
  clear(view);
  const page = h("div", { class: "page" }, h("div", { class: "page-head" }, h("div", null, h("h1", { text: "學習指南測驗" }),
    h("p", { text: "每份指南是一個階段的重點整理＋單選模擬題；完整文字版在 docs/guides/。作答後立刻看到解析，錯題可以單獨重做。" }))));
  if (!guides.length) page.append(empty("book", "還沒有學習指南"));
  guides.forEach((g) => page.append(h("section", { class: "card pad mt" },
    h("div", { class: "card-h" }, h("h3", { text: g.title }), h("span", { class: "pill", text: TRACK[g.track] || g.track })),
    h("div", { class: "row" }, h("div", { class: "grow" }, progress(g.correct, g.questions)), h("span", { class: "small muted", text: `答對 ${g.correct}/${g.questions}・已作答 ${g.answered}${g.wrong ? `・錯題 ${g.wrong}` : ""}` })),
    h("div", { class: "row wrap mt" }, g.groups.map((x, i) => h("button", { class: "btn", onclick: () => go(`/guide/${g.id}/${i}`) }, `${x.title}（${x.n}）`)),
      h("button", { class: "btn primary", onclick: () => go(`/guide/${g.id}/all`) }, "全部"),
      g.wrong ? h("button", { class: "btn", onclick: () => go(`/guide/${g.id}/wrong`) }, `只做錯題（${g.wrong}）`) : null))));
  view.append(page);
}

async function quizView(view, gid, group) {
  const S = await get("/api/guide", { id: gid, group });
  clear(view);
  const page = h("div", { class: "page" });
  view.append(page);
  if (!S.items.length) { page.append(h("div", { class: "page-head" }, h("h1", { text: S.title })), empty("check", "這一組沒有題目（或錯題都已答對）。"), h("button", { class: "btn", onclick: () => go("/guide") }, "回指南列表")); return; }
  let idx = 0, right = 0;
  const box = h("div");
  page.append(h("div", { class: "page-head" }, h("div", null, h("h1", { text: S.title }), h("p", { class: "muted", id: "gq-sec" })), h("button", { class: "btn", onclick: () => go("/guide") }, "離開")), box);
  const show = () => {
    clear(box);
    if (idx >= S.items.length) {
      box.append(h("div", { class: "card pad" }, h("h2", { text: `完成：${right}/${S.items.length}` }), h("p", { class: "muted", text: right === S.items.length ? "全對！" : "錯的題目可以回列表按『只做錯題』再練一次。" }),
        h("div", { class: "row mt" }, h("button", { class: "btn primary", onclick: () => go("/guide") }, "回指南列表"))));
      return;
    }
    const q = S.items[idx];
    document.getElementById("gq-sec").textContent = `${q.section}・第 ${idx + 1}/${S.items.length} 題`;
    const fb = h("div", { class: "mt", "aria-live": "polite" });
    const opts = q.options.map((o, k) => h("button", { class: "btn block opt", style: { textAlign: "left", whiteSpace: "normal" }, onclick: async () => {
      opts.forEach((b) => (b.disabled = true));
      try {
        const r = await post("/api/guide/answer", { id: gid, group: q.group, i: q.i, choice: k });
        if (r.correct) right++;
        opts[r.answer].classList.add("ok"); if (!r.correct) opts[k].classList.add("bad");
        fb.replaceChildren(h("div", { class: "callout" }, h("b", { text: r.correct ? "答對了　" : `答錯了，正確答案是 ${"ABCD"[r.answer]}　` }), md(r.why)),
          h("button", { class: "btn primary mt", onclick: () => { idx++; show(); } }, idx + 1 < S.items.length ? "下一題" : "看結果"));
      } catch (e) { opts.forEach((b) => (b.disabled = false)); toast(e.message, "bad"); }
    } }, `${"ABCD"[k]}. ${o}`));
    box.append(h("div", { class: "card pad" }, h("p", null, md(q.stem)), q.code ? codeBlock(q.code, q.lang) : null, h("div", { class: "col mt" }, opts), fb));
  };
  show();
}
