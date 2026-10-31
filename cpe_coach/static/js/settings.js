import { h, icon, clear, toast } from "./dom.js";
import { get, post, download } from "./api.js";
import { S, pref, applyTheme } from "./state.js";
import { refreshState, paintTop } from "./shell.js";
import { skeleton, empty } from "./widgets.js";
import { lang as uiLang, applyA11y } from "./i18n.js";

export async function mountSettings(view) {
  view.append(h("div", { class: "page" }, h("div", { class: "card pad" }, skeleton(5))));
  let st; try { st = await get("/api/settings"); } catch (e) { clear(view); view.append(h("div", { class: "page" }, empty("alert", e.message))); return; }
  clear(view);
  const key = h("input", { type: "password", placeholder: S.ai.available ? "（已設定；留空表示不變）" : "sk-…", autocomplete: "off", "aria-label": "OpenAI API 金鑰" });
  const model = h("input", { type: "text", value: st.model || "", placeholder: "gpt-4o", "aria-label": "模型" });
  const status = h("div", { class: "small mt", "aria-live": "polite" });
  const show = h("button", { class: "btn ghost icon", "aria-label": "顯示／隱藏金鑰", onclick: () => { key.type = key.type === "password" ? "text" : "password"; } }, icon("eye"));
  const saveAi = async () => { try { const r = await post("/api/key", { key: key.value || undefined, model: model.value }); key.value = ""; await refreshState(); status.textContent = r.available ? "✓ 已儲存。金鑰只存在這個程式的記憶體，不會寫進任何檔案。" : "沒有可用的金鑰。"; status.className = "small mt " + (r.available ? "ok" : "warn"); } catch (e) { toast(e.message, "bad"); } };
  const testAi = async (btn) => { btn.disabled = true; status.textContent = "測試中…"; status.className = "small mt muted"; try { const r = await post("/api/ai/test"); status.textContent = r.ok ? `✓ 連線成功（${r.model}，${r.ms} ms）` : "✗ " + r.error; status.className = "small mt " + (r.ok ? "ok" : "bad"); } catch (e) { status.textContent = "✗ " + e.message; status.className = "small mt bad"; } finally { btn.disabled = false; } };
  const testBtn = h("button", { class: "btn", onclick: (e) => testAi(e.currentTarget) }, icon("refresh"), "測試連線");

  const upd = h("div", { class: "small mt", id: "updResult", "aria-live": "polite" });
  const checkUpdate = async (btn) => {
    btn.disabled = true; upd.className = "small mt muted"; upd.textContent = "檢查中…";
    try {
      const r = await post("/api/update/check");
      clear(upd);
      if (r.status === "up_to_date") { upd.className = "small mt ok"; upd.textContent = `✓ 已經是最新版（${r.version}）。`; }
      else if (r.status === "available") {
        upd.className = "small mt";
        upd.append(h("div", { class: "warn", text: `有 ${r.behind} 個新的更新：` }), h("ul", null, r.commits.map((c) => h("li", null, h("span", { class: "mono", text: c.sha + " " }), c.subject))),
          h("div", null, "在終端機執行 ", h("code", { text: "cpe update" }), "，完成後結束這個網頁服務（Ctrl+C）再重新執行 ", h("code", { text: "cpe web" }), "。學習進度不會被動到。"));
      } else { upd.className = "small mt warn"; upd.textContent = r.reason || "無法檢查更新"; }
    } catch (e) { upd.className = "small mt bad"; upd.textContent = e.message; } finally { btn.disabled = false; }
  };

  const theme = h("div", { class: "seg", role: "group", "aria-label": "外觀" }, [["auto", "跟隨系統"], ["light", "淺色"], ["dark", "深色"]].map(([k, t]) => h("button", { "aria-pressed": String(pref.get("theme", "auto") === k), onclick: (e) => { pref.set("theme", k); applyTheme(k); paintTop(); [...e.currentTarget.parentElement.children].forEach((b) => b.setAttribute("aria-pressed", String(b === e.currentTarget))); } }, t)));
  const fs = h("input", { type: "number", min: 11, max: 22, value: pref.get("fontSize", 14), "aria-label": "編輯器字體大小", style: { width: "90px" }, onchange: (e) => { pref.set("fontSize", Math.max(11, Math.min(22, +e.target.value || 14))); toast("下次開啟題目時套用", "", 1600); } });
  const timeout = h("input", { type: "number", min: 0.5, max: 120, step: 0.5, value: st.timeout_sec, "aria-label": "每筆測資時限", style: { width: "110px" } });
  const start = h("input", { type: "date", value: st.start_date || "", "aria-label": "開始日期", style: { width: "180px" } });
  const lang = h("select", { "aria-label": "內建練習題的題目語言", style: { width: "220px" } }, [["auto", "自動（中文 → 中英對照 → 英文）"], ["zh", "全部中文"], ["bi", "全部中英對照"], ["en", "全部英文"]].map(([k, t]) => h("option", { value: k, text: t, selected: st.statement_lang === k })));
  const saveLearn = async () => { try { await post("/api/settings", { timeout_sec: +timeout.value, start_date: start.value || undefined, statement_lang: lang.value }); toast("已儲存", "ok", 1500); } catch (e) { toast(e.message, "bad"); } };

  view.append(h("div", { class: "page", style: { "max-width": "820px" } }, h("div", { class: "page-head" }, h("div", null, h("h1", { text: "設定" }))),
    h("section", { class: "card pad" }, h("div", { class: "card-h" }, h("h3", null, icon("sparkle"), "AI（OpenAI）")),
      h("p", { class: "muted small", text: "按下詢問時，你的程式與題目敘述會傳給 OpenAI，並產生 API 費用（每次約一兩千 token）。金鑰只保存在這個程式的記憶體；也可以改用環境變數 OPENAI_API_KEY。" }),
      h("div", { class: "col" }, h("label", { class: "field" }, "API 金鑰", h("div", { class: "row" }, key, show)), h("label", { class: "field" }, "模型", model, h("small", { text: "填你帳號可用的聊天模型名稱。" }))),
      h("div", { class: "row mt" }, h("button", { class: "btn primary", onclick: saveAi }, "儲存"), testBtn), status),
    h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", { text: "外觀與編輯器" })),
      h("div", { class: "col" }, h("div", { class: "row wrap" }, h("span", { class: "grow", text: "外觀" }), theme),
        h("div", { class: "row wrap" }, h("span", { class: "grow", text: "介面語言（英文只涵蓋導覽列與「學習」頁）" }), h("div", { class: "seg", role: "group", "aria-label": "介面語言" }, [["zh", "中文"], ["en", "English"]].map(([k, x]) => h("button", { "aria-pressed": String(uiLang() === k), onclick: () => { pref.set("lang", k); applyA11y(); location.reload(); } }, x)))),
        h("div", { class: "row wrap" }, h("span", { class: "grow", text: "色盲友善配色（通過／失敗改用藍與橘）" }), h("div", { class: "seg", role: "group", "aria-label": "色盲友善配色" }, [[false, "關"], [true, "開"]].map(([k, x]) => h("button", { "aria-pressed": String(pref.get("colorblind", false) === k), onclick: (e) => { pref.set("colorblind", k); applyA11y(); [...e.currentTarget.parentElement.children].forEach((b) => b.setAttribute("aria-pressed", String(b === e.currentTarget))); } }, x)))), h("div", { class: "row wrap" }, h("span", { class: "grow", text: "編輯器字體大小（px）" }), fs))),
    h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", { text: "學習" })),
      h("div", { class: "col" }, h("label", { class: "field" }, "每筆測資時限（秒）", timeout, h("small", { text: "Python 比 C++ 慢；本機電腦慢時可以調高。" })), h("label", { class: "field" }, "課程開始日期", start, h("small", { text: "用來計算『依課表你應該在第幾週』。" })), h("label", { class: "field" }, "內建練習題的題目語言", lang, h("small", { text: "自動：階段 0 中文、階段 1 中英對照、之後純英文。考場是英文，所以越後面越該習慣讀英文。比照考場的模擬考一律英文。" }))), h("div", { class: "mt" }, h("button", { class: "btn primary", onclick: saveLearn }, "儲存"))),
    h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", { text: "備份與搬家" })),
      h("p", { class: "muted small", text: "把所有進度、解答、測資、對話與單字本打包成一個 zip。換電腦時：cpe restore <檔案> --dir <新資料夾>。系統也會每小時自動留一份進度快照（.cpe/backups，保留最近 24 份）。" }),
      h("div", { class: "row wrap" }, h("button", { class: "btn", onclick: async (e) => { const b = e.currentTarget; b.disabled = true; try { await download("/api/backup", "cpe-backup.zip"); toast("已下載備份", "ok", 2500); } catch (err) { toast(err.message, "bad"); } finally { b.disabled = false; } } }, icon("save"), "下載備份 (.zip)")),
      h("p", { class: "muted xs mt", text: "備份不包含 API 金鑰（金鑰只存在記憶體）。" })),
    h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", { text: "版本與更新" })),
      h("dl", { class: "dl" }, h("dt", { text: "目前版本" }), h("dd", { class: "mono", text: st.version || "—" })),
      h("p", { class: "muted small", text: "更新在終端機執行 cpe update（只做 fast-forward，失敗會自動退回）。這裡只檢查有沒有新版本，不會改任何檔案。" }),
      h("div", { class: "row" }, h("button", { class: "btn", onclick: (e) => checkUpdate(e.currentTarget) }, icon("refresh"), "檢查更新")), upd),
    h("section", { class: "card pad mt" }, h("div", { class: "card-h" }, h("h3", { text: "環境" })),
      h("dl", { class: "dl" }, h("dt", { text: "工作區" }), h("dd", { class: "mono small", text: st.workspace }), h("dt", { text: "g++（C++ 判題）" }), h("dd", null, st["g++"] ? h("span", { class: "ok", text: "已安裝" }) : h("span", { class: "warn", text: "找不到。階段 4 起需要安裝（Windows 可裝 MSYS2/MinGW）" })), h("dt", { text: "快速鍵" }), h("dd", null, h("kbd", { text: "?" }), " 查看全部"))),
  ));
}
