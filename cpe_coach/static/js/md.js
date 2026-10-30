// 安全的 Markdown 子集：以 DOM 節點輸出（不使用 innerHTML 處理不受信任的文字）。
import { h, icon, toast } from "./dom.js";
import { highlightHtml } from "./highlight.js";

export function inline(text) {
  const out = []; const re = /`([^`]+)`|\*\*([^*]+)\*\*|\*([^*\s][^*]*)\*/g; let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index));
    if (m[1] != null) out.push(h("code", { text: m[1] })); else if (m[2] != null) out.push(h("strong", { text: m[2] })); else out.push(h("em", { text: m[3] }));
    last = re.lastIndex;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

export function codeBlock(code, lang) {
  const pre = h("pre"); const L = (lang || "").toLowerCase();
  if (["py", "python", "cpp", "c++", "c", "cc"].includes(L)) pre.innerHTML = highlightHtml(code, L.startsWith("c") ? "cpp" : "py"); // 已跳脫
  else pre.textContent = code;
  const btn = h("button", { class: "btn sm icon ghost copy", "aria-label": "複製", title: "複製",
    onclick: async () => { try { await navigator.clipboard.writeText(code); toast("已複製", "ok", 1400); } catch { toast("無法複製", "bad"); } } }, icon("copy"));
  return h("div", { class: "codeblock" }, pre, btn);
}

export function render(src) {
  const frag = document.createDocumentFragment(); const L = String(src || "").replace(/\r/g, "").split("\n");
  let i = 0;
  while (i < L.length) {
    const ln = L[i]; let m;
    if ((m = ln.match(/^```\s*([\w+#-]*)\s*$/))) {
      const buf = []; i++;
      while (i < L.length && !L[i].startsWith("```")) buf.push(L[i++]);
      i++; frag.append(codeBlock(buf.join("\n"), m[1])); continue;
    }
    if ((m = ln.match(/^(#{1,4})\s+(.*)$/))) { frag.append(h("h" + m[1].length, null, inline(m[2]))); i++; continue; }
    if (/^\s*[-*]\s+/.test(ln)) {
      const ul = h("ul"); while (i < L.length && /^\s*[-*]\s+/.test(L[i])) ul.append(h("li", null, inline(L[i++].replace(/^\s*[-*]\s+/, "")))); frag.append(ul); continue;
    }
    if (/^\s*\d+[.)]\s+/.test(ln)) {
      const ol = h("ol"); while (i < L.length && /^\s*\d+[.)]\s+/.test(L[i])) ol.append(h("li", null, inline(L[i++].replace(/^\s*\d+[.)]\s+/, "")))); frag.append(ol); continue;
    }
    if (/^>\s?/.test(ln)) { const buf = []; while (i < L.length && /^>\s?/.test(L[i])) buf.push(L[i++].replace(/^>\s?/, "")); frag.append(h("blockquote", { class: "quote" }, inline(buf.join(" ")))); continue; }
    if (/^\s*-{3,}\s*$/.test(ln)) { frag.append(h("hr")); i++; continue; }
    if (!ln.trim()) { i++; continue; }
    const buf = [ln]; i++;
    while (i < L.length && L[i].trim() && !/^(```|#{1,4}\s|\s*[-*]\s|\s*\d+[.)]\s|>|\s*-{3,}\s*$)/.test(L[i])) buf.push(L[i++]);
    frag.append(h("p", null, inline(buf.join("\n"))));
  }
  return frag;
}
