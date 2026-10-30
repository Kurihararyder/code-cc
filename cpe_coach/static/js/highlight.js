// 小型語法上色器（Python / C++）。輸出每一行的 HTML 字串；所有文字都經過跳脫。
const PY_KW = new Set("and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield True False None".split(" "));
const PY_BI = new Set("print input len range int str float list dict set tuple sum min max abs sorted reversed enumerate zip map filter any all bool bytes chr ord divmod pow round open isinstance type id iter next frozenset bin hex oct super object Exception ValueError IndexError KeyError EOFError sys math collections heapq bisect itertools".split(" "));
const CPP_KW = new Set("alignas and auto bool break case catch char class const constexpr continue default delete do double else enum explicit extern false float for friend goto if inline int long mutable namespace new noexcept nullptr operator or private protected public register return short signed sizeof static struct switch template this throw true try typedef typename union unsigned using virtual void volatile while override final".split(" "));
const CPP_BI = new Set("std vector string map set unordered_map unordered_set multiset pair tuple queue deque stack priority_queue array bitset cin cout cerr endl size_t int64_t uint64_t long ll sort lower_bound upper_bound min max swap reverse accumulate iota make_pair getline ios sync_with_stdio tie begin end size push_back pop_back emplace_back".split(" "));

const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const RULES = {
  py: [
    ["cm", /#[^\n]*/y],
    ["str", /[rRbBfFuU]{0,2}(?:"""[\s\S]*?(?:"""|$)|'''[\s\S]*?(?:'''|$))/y],
    ["str", /[rRbBfFuU]{0,2}(?:"(?:\\.|[^"\\\n])*"?|'(?:\\.|[^'\\\n])*'?)/y],
    ["deco", /@[A-Za-z_][\w.]*/y],
    ["num", /(?:0[xX][\da-fA-F_]+|0[bB][01_]+|(?:\d[\d_]*\.?[\d_]*|\.\d[\d_]*)(?:[eE][+-]?\d+)?)/y],
    ["id", /[A-Za-z_]\w*/y],
  ],
  cpp: [
    ["cm", /\/\/[^\n]*/y], ["cm", /\/\*[\s\S]*?(?:\*\/|$)/y],
    ["deco", /#\s*[A-Za-z_]+/y],
    ["str", /"(?:\\.|[^"\\\n])*"?/y], ["str", /'(?:\\.|[^'\\\n])*'?/y],
    ["num", /(?:0[xX][\da-fA-F']+|(?:\d[\d']*\.?[\d']*|\.\d+)(?:[eE][+-]?\d+)?[uUlLfF]*)/y],
    ["id", /[A-Za-z_]\w*/y],
  ],
};

export function highlightLines(code, lang = "py") {
  const rules = RULES[lang === "cpp" ? "cpp" : "py"];
  const KW = lang === "cpp" ? CPP_KW : PY_KW, BI = lang === "cpp" ? CPP_BI : PY_BI;
  const lines = [""]; let prevKw = "";
  const push = (text, cls) => {
    const parts = text.split("\n");
    parts.forEach((p, i) => {
      if (i > 0) lines.push("");
      if (!p) return;
      lines[lines.length - 1] += cls ? `<span class="hl-${cls}">${esc(p)}</span>` : esc(p);
    });
  };
  let i = 0, plain = "";
  const flush = () => { if (plain) { push(plain, ""); plain = ""; } };
  while (i < code.length) {
    let hit = null;
    for (const [cls, re] of rules) {
      re.lastIndex = i; const m = re.exec(code);
      if (m && m.index === i && m[0].length) { hit = [cls, m[0]]; break; }
    }
    if (!hit) { plain += code[i]; i++; continue; }
    flush();
    let [cls, text] = hit;
    if (cls === "id") {
      if (KW.has(text)) cls = "kw"; else if (BI.has(text)) cls = "bi";
      else if (prevKw === "def" || prevKw === "class") cls = "fn"; else cls = "";
      prevKw = text;
    } else if (!/^\s+$/.test(text)) prevKw = "";
    push(text, cls); i += text.length;
  }
  flush();
  return lines;
}
export const highlightHtml = (code, lang) => highlightLines(code, lang).join("\n");
