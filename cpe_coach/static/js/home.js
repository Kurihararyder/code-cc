import { h, icon, clear, toast, stars, fmtDate, modal } from "./dom.js";
import { get, post } from "./api.js";
import { go } from "./router.js";
import { S, pref, stageColor } from "./state.js";
import { kpi, progress, heat, skeleton, empty, examPanel, startGate, startMockDialog, notify } from "./widgets.js";
import { refreshState } from "./shell.js";
import { planCard } from "./plan.js";

const greet = () => { const hr = new Date().getHours(); return hr < 5 ? "夜深了" : hr < 12 ? "早安" : hr < 18 ? "午安" : "晚安"; };

export async function mountHome(view) {
  view.append(h("div", { class: "page" }, h("div", { class: "card pad" }, skeleton(4))));
  let d;
  try { d = await get("/api/dashboard"); } catch (e) { clear(view); view.append(h("div", { class: "page" }, empty("alert", "讀取失敗：" + e.message))); return; }
  clear(view); view.append(build(d));
  if (d.first_run && !pref.get("onboarded", false)) onboarding();
  const t = setInterval(() => { const el = document.getElementById("examBig"); if (!el) return; /* 倒數由頂列負責；這裡只同步顯示 */ const top = document.getElementById("examLeft"); if (top) el.textContent = top.textContent; }, 1000);
  return () => clearInterval(t);
}

function build(d) {
  const u = d.unit; const page = h("div", { class: "page" });
  page.append(h("div", { class: "page-head" }, h("div", null, h("h1", { text: `${greet()}，繼續加油` }), h("p", { text: `${d.date} · 第 ${d.week} 週` })),
    h("div", { class: "row" }, h("button", { class: "btn", onclick: startMockDialog }, icon("target"), "模擬考"))));
  if (d.exam) page.append(examPanel(d.exam));

  if (!d.exam) page.append(planCard());
  if (u) {
    const pace = u.pace > 0 ? h("span", { class: "pill warn", text: `落後課表 ${u.pace} 個單元` }) : u.pace < 0 ? h("span", { class: "pill ok", text: `超前課表 ${-u.pace} 個單元` }) : h("span", { class: "pill info", text: "進度與課表同步" });
    page.append(h("section", { class: "card hero mt", "aria-label": "目前單元" },
      h("div", { class: "eyebrow" }, h("span", { class: "stagedot", style: { "--sc": stageColor(u.stage) } }), `階段 ${u.stage} · 單元 ${u.n}`, h("span", { class: "muted", text: `課表第 ${u.weeks[0]}${u.weeks[1] > u.weeks[0] ? "–" + u.weeks[1] : ""} 週` }), pace, u.lang === "cpp" ? h("span", { class: "pill accent", text: "C++" }) : null),
      h("h2", { class: "hero-t", text: u.title }), h("p", { class: "muted", text: u.goal }),
      h("div", { class: "row mt" }, h("div", { class: "grow" }, progress(u.progress.done, u.progress.total, stageColor(u.stage))), h("span", { class: "small muted", text: `必做 ${u.progress.done}/${u.progress.total}` })),
      h("div", { class: "actions" },
        d.next ? h("button", { class: "btn primary lg", onclick: () => go("/practice/" + d.next.id) }, icon("play"), `${u.progress.done ? "繼續" : "開始"}：${d.next.id} ${d.next.title}`) : null,
        u.gate_ready ? h("button", { class: "btn lg" + (d.next ? "" : " primary"), onclick: () => startGate(u) }, icon("target"), "開始單元檢核") : null,
        !u.has_gate ? h("button", { class: "btn lg", onclick: async () => { try { await post("/api/course/next"); notify(); go("/home"); } catch (e) { toast(e.message, "bad"); } } }, "標記單元完成（實際報考後）") : null,
        h("button", { class: "btn lg ghost", onclick: () => go("/course/" + u.n) }, "單元內容"))));
  } else page.append(h("div", { class: "card hero mt" }, h("h2", { class: "hero-t", text: "🎓 課程全部完成" }), h("p", { text: "你已經走完 126 週。接下來每週做一次全真模擬，並規劃報考。" })));

  page.append(h("div", { class: "kpis mt" },
    kpi("check", d.stats.solved, "已通過題數"), kpi("target", d.stats.mastered, "精熟題數", "ok"), kpi("flame", d.stats.streak, "連續練習天數"),
    kpi("chart", d.stats.attempts_week ? Math.round((100 * d.stats.ac_week) / d.stats.attempts_week) + "%" : "—", `本週通過率（${d.stats.attempts_week} 次提交）`)));

  const left = h("div", { class: "col gap-lg" }), right = h("div", { class: "col gap-lg" });
  left.append(h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", null, icon("refresh"), "到期重練"), d.due.length ? h("span", { class: "pill bad", text: `${d.due.length} 題` }) : null),
    d.due.length ? h("ul", { class: "list" }, d.due.map((p) => h("li", null, h("button", { class: "li", onclick: async () => { try { await post("/api/new", { id: p.id, fresh: true }); } catch (e) { /* 沒有舊檔也沒關係 */ } go("/practice/" + p.id); } }, icon("refresh"), h("span", { class: "mono", text: p.id }), h("span", { class: "grow", text: p.title }), h("span", { class: "muted small", text: "從空白重寫" }), icon("chevron")))))
      : empty("check", "沒有到期的重練 👍"),
    h("p", { class: "muted small mt", text: "用了提示才通過的題目，隔天起要『從空白檔、不看提示』重寫通過，才算真正學會。" })));
  left.append(h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", null, icon("list"), "最近活動")),
    d.activity.length ? h("div", { class: "feed" }, d.activity.map((a) => h("div", { class: "it " + a.tone }, h("span", { class: "b" }), h("span", { class: "grow", text: a.text }), h("span", { class: "muted xs", text: fmtDate(a.ts) })))) : empty("code", "還沒有紀錄。從上面的『開始』按鈕做第一題吧。")));

  right.append(h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", null, icon("flame"), "最近 12 週")), heat(d.heatmap)));
  const rt = d.stats.review_attempts, pr = d.predict;
  right.append(h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", null, icon("eye"), "自我校準")),
    h("dl", { class: "dl" },
      h("dt", { text: "無提示重寫通過率" }), h("dd", { text: rt ? `${d.stats.review_clean_passes}/${rt}（${Math.round((100 * d.stats.review_clean_passes) / rt)}%）` : "尚無資料" }),
      h("dt", { text: "提交前預測準確度" }), h("dd", { text: pr.total ? `${pr.correct}/${pr.total}（${Math.round((100 * pr.correct) / pr.total)}%）` : "尚無資料" })),
    h("p", { class: "muted small mt", text: "這兩個數字比『我覺得我會了』可靠。預測越準，代表你越清楚自己的程式在做什麼。" })));
  page.append(h("div", { class: "grid-2 mt" }, left, right));
  if (!d.ai.available) page.append(h("div", { class: "callout warn mt" }, icon("alert"), h("div", null, "還沒有設定 AI 金鑰，『選取文字問 AI』無法使用。", h("a", { href: "#/settings", text: " 前往設定 →" }))));
  return page;
}

function onboarding() {
  let i = 0; const total = 3; const body = h("div"); let m;
  const slides = [
    () => [h("p", { text: "這是一套從零基礎到 CPE 一次 6 題的自學系統：126 週課程、100 多題內建練習題、本地判題。" }),
      h("ul", null, h("li", { text: "每個單元都有必做題與限時檢核，通過才前進。" }), h("li", { text: "AI 只負責『提問』，對錯永遠由測資決定。" }), h("li", { text: "用了提示的題目，隔天要無提示重寫。" })),
      h("p", { class: "muted small", text: "6 題是全國前 1% 的成績，沒有人能保證你達成；真實的 CPE 成績才是最終檢核。" })],
    () => { const key = h("input", { type: "password", placeholder: "sk-…", autocomplete: "off", "aria-label": "OpenAI API 金鑰" }); const st = h("div", { class: "small muted mt", text: S.ai.available ? "AI 已就緒。" : "沒有金鑰也能用其他功能，之後可以在『設定』補上。" });
      return [h("p", { text: "要用『選取文字問 AI』，需要你自己的 OpenAI API 金鑰。金鑰只存在這個程式的記憶體，不會寫進檔案。" }), h("label", { class: "field" }, "OpenAI API 金鑰", key),
        h("button", { class: "btn mt", onclick: async () => { try { await post("/api/key", { key: key.value }); await refreshState(); st.textContent = S.ai.available ? "✓ 已儲存。可到設定頁按『測試連線』確認。" : "沒有輸入金鑰。"; } catch (e) { st.textContent = e.message; } } }, "儲存金鑰"), st]; },
    () => [h("p", { text: "最重要的一個動作：" }), h("div", { class: "callout" }, icon("sparkle"), h("div", null, h("b", { text: "在題目、程式或測試結果上，用滑鼠（或手指長按）選一段文字。" }), h("div", { text: "旁邊會跳出『要問這一段嗎？』的選單。" }))),
      h("ul", null, h("li", { text: "這是什麼意思？— 解釋詞彙，隨時可用" }), h("li", { text: "考我這一段 — AI 針對你選的那段出題（要先跑過一次測試）" }), h("li", { text: "預期和實際不同 — 針對失敗的測資發問" })),
      h("p", { class: "muted small", text: "AI 必須逐字引用你的程式，系統會驗證引用是否真的存在。按 ? 可隨時查看快速鍵。" })],
  ];
  const paint = () => { clear(body); body.append(h("div", { class: "muted small", text: `${i + 1} / ${total}` }), h("h2", { text: ["歡迎", "設定 AI（選用）", "從細節來學"][i] }), ...slides[i]()); back.disabled = i === 0; next.textContent = i === total - 1 ? "開始第一題" : "下一步"; };
  const back = h("button", { class: "btn", onclick: () => { i = Math.max(0, i - 1); paint(); } }, "上一步");
  const next = h("button", { class: "btn primary", onclick: () => { if (i < total - 1) { i++; paint(); } else { pref.set("onboarded", true); m.close(); go("/practice"); } } });
  m = modal({ body, label: "歡迎使用", onClose: () => pref.set("onboarded", true) });
  const f = h("div", { class: "modal-f" }, h("button", { class: "btn ghost", onclick: () => { pref.set("onboarded", true); m.close(); } }, "略過"), back, next);
  m.el.append(f); paint();
}
