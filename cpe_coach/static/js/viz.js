// 資料結構視覺化：把「逐行追蹤」裡 Python 的 repr 字串（list／dict／set／tuple／數字／字串）畫成方格與表格，變動的格子標出來。
import { h } from "./dom.js";

// 解析 Python repr。解析不了（物件、很長、遞迴）就回傳 null，呼叫端退回純文字。
export function parsePy(src) {
  let i = 0; const s = String(src);
  const ws = () => { while (i < s.length && /\s/.test(s[i])) i++; };
  const fail = () => { throw new Error("parse"); };
  function val(depth) {
    if (depth > 6) fail(); ws();
    const c = s[i];
    if (c === "[" || c === "(" || c === "{") return coll(c, depth);
    if (c === "'" || c === '"') return str(c);
    const m = /^(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?|True|False|None|nan|inf|-inf)/.exec(s.slice(i, i + 40));
    if (!m) fail(); i += m[0].length;
    return m[0] === "True" ? true : m[0] === "False" ? false : m[0] === "None" ? null : isNaN(Number(m[0])) ? { raw: m[0] } : Number(m[0]);
  }
  function str(q) {
    let out = ""; i++;
    while (i < s.length && s[i] !== q) { if (s[i] === "\\") { i++; } out += s[i++]; if (out.length > 200) fail(); }
    if (s[i] !== q) fail(); i++; return { str: out };
  }
  function coll(open, depth) {
    const close = { "[": "]", "(": ")", "{": "}" }[open]; i++; const items = []; let isDict = false; ws();
    if (s.slice(i, i + 3) === "set" ) fail();
    while (i < s.length && s[i] !== close) {
      const k = val(depth + 1); ws();
      if (s[i] === ":") { isDict = true; i++; items.push([k, val(depth + 1)]); } else items.push(k);
      ws(); if (s[i] === ",") i++; ws(); if (items.length > 400) fail();
    }
    if (s[i] !== close) fail(); i++;
    return isDict ? { dict: items } : { list: items, kind: open === "[" ? "list" : open === "(" ? "tuple" : "set" };
  }
  try { const v = val(0); ws(); return i === s.length ? v : null; } catch { return null; }
}

const show = (v) => v === null ? "None" : v === true ? "True" : v === false ? "False" : typeof v === "number" ? String(v) : v && v.str !== undefined ? v.str : v && v.raw ? v.raw : "…";
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

function cellBox(v, changed, idx) {
  return h("div", { class: "vz-c" + (changed ? " chg" : "") }, h("div", { class: "vz-i", text: idx === undefined ? "" : String(idx) }), h("div", { class: "vz-v", text: show(v) }));
}

function render1(v, prev) {
  if (v && v.list) {
    const is2d = v.list.length > 0 && v.list.every((r) => r && r.list) && v.kind === "list";
    if (is2d) {
      return h("div", { class: "vz-grid" }, v.list.slice(0, 30).map((row, r) => h("div", { class: "vz-row" }, row.list.slice(0, 30).map((x, c) => cellBox(x, !(prev && prev.list && prev.list[r] && prev.list[r].list && same(prev.list[r].list[c], x)), c)))));
    }
    return h("div", { class: "vz-row", title: v.kind }, v.list.slice(0, 60).map((x, k) => (x && (x.list || x.dict)) ? h("div", { class: "vz-nest", text: JSON.stringify(x).slice(0, 40) }) : cellBox(x, !(prev && prev.list && same(prev.list[k], x)), v.kind === "set" ? undefined : k)), v.list.length > 60 ? h("div", { class: "vz-more", text: `…共 ${v.list.length} 個` }) : null);
  }
  if (v && v.dict) {
    const pm = new Map(prev && prev.dict ? prev.dict.map(([k, x]) => [JSON.stringify(k), x]) : []);
    return h("table", { class: "vz-dict" }, h("tbody", null, v.dict.slice(0, 40).map(([k, x]) => h("tr", { class: pm.has(JSON.stringify(k)) && same(pm.get(JSON.stringify(k)), x) ? "" : "chg" }, h("td", { text: show(k) }), h("td", { text: (x && (x.list || x.dict)) ? JSON.stringify(x).slice(0, 50) : show(x) })))));
  }
  return h("span", { class: "vz-s" + (same(v, prev) ? "" : " chg"), text: show(v) });
}

// 一步的所有變數：vars 與 prevVars 都是 {名稱: repr 字串}；解析不了的變數就顯示原字串。
export function renderStep(vars, prevVars = {}) {
  const names = Object.keys(vars);
  if (!names.length) return h("p", { class: "muted small", text: "（這一步還沒有變數）" });
  return h("div", { class: "vz" }, names.map((n) => {
    const v = parsePy(vars[n]); const pv = prevVars[n] !== undefined ? parsePy(prevVars[n]) : undefined;
    return h("div", { class: "vz-var" }, h("div", { class: "vz-name mono", text: n }), v === null ? h("code", { class: "vz-raw", text: String(vars[n]).slice(0, 120) }) : render1(v, pv));
  }));
}
