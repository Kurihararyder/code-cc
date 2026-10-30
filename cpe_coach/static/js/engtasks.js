// 工程能力任務：每個任務有『建立範本』與『驗收』；通過驗收才算完成。
import { h, icon, clear, toast, modal } from "./dom.js";
import { get, post } from "./api.js";
import { skeleton, empty, notify } from "./widgets.js";
import { stageColor } from "./state.js";

export async function engPanel() {
  const box = h("div", { class: "col gap-lg" }, h("div", { class: "card pad" }, skeleton(5)));
  const paint = async () => {
    let T; try { T = await get("/api/eng"); } catch (e) { clear(box); box.append(empty("alert", e.message)); return; }
    clear(box);
    const done = T.tasks.filter((t) => t.done).length;
    box.append(h("div", { class: "callout" }, icon("help"), h("div", null, h("b", { text: `工程能力 ${done}/${T.tasks.length}` }),
      h("div", { class: "small", text: "每週撥 20–30% 的時間做一個任務。『驗收』會真的執行你的作品來檢查（例如跑你寫的 pytest、把解答改壞看測試會不會變紅），通過才算完成，不是自己打勾。" }))));
    T.tasks.forEach((t) => box.append(card(t, paint)));
  };
  await paint();
  return box;
}

function card(t, repaint) {
  const failed = t.last && !t.last.ok && !t.done;
  return h("section", { class: "card pad", style: { "--sc": stageColor(t.min_stage) } },
    h("div", { class: "row wrap" }, h("span", { class: "status" + (t.done ? " done" : "") }, t.done ? icon("check") : null), h("b", { class: "mono", text: "#" + t.n }), h("span", { class: "pill", text: "階段 " + t.min_stage + "+" }),
      h("span", { class: "pill " + (t.kind === "auto" ? "ok" : t.kind === "semi" ? "info" : "warn"), text: t.kind_zh }), failed ? h("span", { class: "pill bad", text: "上次驗收沒過" }) : null),
    h("p", { style: { margin: "8px 0 10px" }, text: t.title }),
    h("div", { class: "row wrap" },
      t.has_scaffold ? h("button", { class: "btn sm", onclick: async () => { try { const r = await post("/api/eng/start", { n: t.n }); toast(r.created.length ? "已建立：" + r.created.join("、") : "範本檔已存在，沒有覆蓋", "ok", 6000); } catch (e) { toast(e.message, "bad"); } } }, icon("code"), "建立範本") : null,
      h("button", { class: "btn sm primary", onclick: (e) => verify(t, e.currentTarget, repaint) }, icon("check"), t.done ? "重新驗收" : "驗收")));
}

async function verify(t, btn, repaint) {
  let evidence;
  if (t.kind === "manual") {
    evidence = await askEvidence(t); if (evidence == null) return;
  }
  const label = btn.lastChild.textContent; btn.disabled = true; btn.lastChild.textContent = "驗收中…（可能要一兩分鐘）";
  try {
    const r = await post("/api/eng/verify", { n: t.n, evidence });
    notify();
    modal({ title: r.ok ? `✅ 任務 #${t.n} 通過驗收` : `任務 #${t.n} 還沒過`, body: h("div", { class: "col" }, h("ul", { class: "checks" }, r.results.map((x) => h("li", { class: x.ok ? "ok" : "bad" }, icon(x.ok ? "check" : "x"), h("div", null, h("div", { text: x.label }), !x.ok && x.msg ? h("pre", { class: "small checkmsg", text: x.msg }) : (x.msg ? h("div", { class: "muted xs", text: x.msg }) : null)))))),
      actions: [{ label: "關閉", kind: "primary" }] });
    repaint();
  } catch (e) { toast(e.message, "bad", 8000); } finally { btn.disabled = false; btn.lastChild.textContent = label; }
}

function askEvidence(t) {
  return new Promise((res) => {
    const input = h("input", { type: "url", placeholder: "https://…", "aria-label": "證據網址", autofocus: true });
    let done = false;
    modal({ title: `任務 #${t.n}：提供證據`, body: h("div", { class: "col" }, h("p", { class: "small muted", text: t.n === 2 ? "貼上你在自己倉庫開的 PR 網址（https://github.com/…/pull/N）。" : "貼上可以公開開啟的網址（https://…）。" }), input),
      onClose: () => { if (!done) res(null); },
      actions: [{ label: "取消", onClick: () => { done = true; res(null); } }, { label: "驗收", kind: "primary", onClick: () => { done = true; res(input.value.trim()); } }] });
  });
}
