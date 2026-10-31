"""不含列印的核心動作：CLI 與網頁介面共用。"""
from __future__ import annotations

import ast
import builtins
import html.parser
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import bank as bank_mod
from . import mock, srs
from .judge import AC, VERDICT_ZH, find_cases, judge
from .store import Workspace


# ---------- 路徑 ----------
def solution_file(ws: Workspace, pid: str, lang: Optional[str] = None) -> Path:
    """考試中的題目用考試檔；否則依 lang 或最近修改的 .py/.cpp。"""
    exam = ws.exam()
    if exam and not lang:
        p = mock.solution_path(ws, exam, pid)
        if p:
            return p
    py, cpp = ws.solutions / f"{pid}.py", ws.solutions / f"{pid}.cpp"
    if lang:
        return cpp if lang == "cpp" else py
    existing = [f for f in (py, cpp) if f.exists()]
    return max(existing, key=lambda f: f.stat().st_mtime) if existing else py


def fail_path(ws: Workspace, pid: str) -> Path:
    return ws.meta / "last_fail" / f"{pid}.json"


def trunc(text: str, n: int = 400) -> str:
    text = text.rstrip()
    return text if len(text) <= n else text[:n] + f"\n…（共 {len(text)} 字元，已截斷）"


def load_failure(ws: Workspace, pid: str) -> Optional[Dict[str, Any]]:
    fp = fail_path(ws, pid)
    return json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else None


# ---------- 建立解答檔 ----------
def create_solution(ws: Workspace, bank: Dict[str, dict], pid: str, lang: str = "py", fresh: bool = False) -> Dict[str, Any]:
    f = solution_file(ws, pid, lang)
    note = None
    if bank_mod.is_drill(pid):
        bank_mod.install_drill(ws, pid)
    elif pid not in bank:
        note = f"{pid} 不在題庫，當作自訂題目。範例測資請用 cpe import 或 cpe addtest 加入"
    ws.solutions.mkdir(exist_ok=True)
    if f.exists():
        if not fresh:
            raise ValueError(f"{f.name} 已存在。要從空白重寫請加 --fresh（舊檔會備份到 solutions/archive/）")
        arc = ws.solutions / "archive"
        arc.mkdir(exist_ok=True)
        stamp = time.strftime("%Y%m%d%H%M%S", time.localtime(ws.now()))
        shutil.move(str(f), str(arc / f"{f.stem}-{stamp}{f.suffix}"))
    f.write_text(mock.template(lang), encoding="utf-8")
    (ws.tests / pid).mkdir(parents=True, exist_ok=True)
    return {"path": f, "tests": len(find_cases(ws.tests / pid)), "note": note, "drill": bank_mod.is_drill(pid)}


# ---------- 判題 ----------
def error_line(res_message: str, stderr: str, solution_name: str) -> Optional[int]:
    """從語法錯誤訊息、Python traceback、g++ 錯誤中抓出出事的行號。"""
    m = re.match(r"第 (\d+) 行", res_message or "")
    if m:
        return int(m.group(1))
    hits = re.findall(r'File "[^"]*%s", line (\d+)' % re.escape(solution_name), stderr or "")
    if hits:
        return int(hits[-1])
    m = re.search(r"%s:(\d+):\d+: error" % re.escape(solution_name), (res_message or "") + "\n" + (stderr or ""))
    return int(m.group(1)) if m else None


def run_test(ws: Workspace, pid: str, lang: Optional[str] = None, predicted: Optional[str] = None) -> Dict[str, Any]:
    sol = solution_file(ws, pid, lang)
    cfg = ws.config()
    res = judge(sol, ws.tests / pid, float(cfg["timeout_sec"]), int(cfg.get("memory_mb", 1024)))
    out: Dict[str, Any] = {"setup_error": res.setup_error, "message": res.message, "verdict": res.verdict,
                           "verdict_zh": VERDICT_ZH[res.verdict], "cases": [], "failing": None, "info": {},
                           "exam_note": "", "review": None, "lang": "cpp" if sol.suffix == ".cpp" else "py",
                           "error_line": None}
    if res.setup_error:
        return out
    if res.verdict != AC:
        stderr_first = res.failing.stderr if res.failing else ""
        out["error_line"] = error_line(res.message, stderr_first, sol.name)
    out["cases"] = [{"name": c.name, "verdict": c.verdict, "seconds": round(c.seconds, 3)} for c in res.cases]
    f = res.failing
    if f:
        out["failing"] = {"name": f.name, "verdict": f.verdict, "input": f.input_text, "expected": f.expected,
                          "actual": f.actual, "stderr": f.stderr}
        fp = fail_path(ws, pid)
        fp.parent.mkdir(exist_ok=True)
        fp.write_text(json.dumps({k: out["failing"][k] for k in ("verdict", "input", "expected", "actual", "stderr")},
                                 ensure_ascii=False), encoding="utf-8")
    elif fail_path(ws, pid).exists():
        fail_path(ws, pid).unlink()

    st = ws.state()
    p = ws.problem(st, pid)
    info = srs.record_result(p, res.verdict, ws.now())
    ws.save_state(st)
    extra = {"predicted": predicted} if predicted else {}
    ws.log("test", problem=pid, verdict=res.verdict, lang=out["lang"], **info, **extra)
    out["info"] = info
    out["review"] = {"stage": p["review_stage"], "due": p["review_due"]}
    exam = ws.exam()
    if exam:
        out["exam_note"] = mock.record(ws, exam, pid, res.verdict)
    return out


# ---------- 逐行追蹤（Python） ----------
_TRACER = r'''
import json, runpy, sys
path, inp, out, limit = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
steps = []
OK = (int, float, str, bool, type(None))
def snap(d):
    r = {}
    for k, v in d.items():
        if k.startswith("__") or callable(v) or type(v).__name__ in ("module", "function"):
            continue
        if isinstance(v, OK):
            s = repr(v)
        elif isinstance(v, (list, tuple, set, dict)):
            s = repr(v)
        else:
            continue
        r[k] = s if len(s) <= 60 else s[:57] + "..."
    return r
class Stop(Exception):
    pass
def tracer(frame, event, arg):
    if frame.f_code.co_filename != path:
        return None
    if event == "line":
        steps.append({"line": frame.f_lineno, "vars": snap(frame.f_locals)})
        if len(steps) >= limit:
            raise Stop()
    return tracer
sys.stdin = open(inp, encoding="utf-8")
sys.settrace(tracer)
err = None
try:
    runpy.run_path(path, run_name="__main__")
except Stop:
    err = "truncated"
except SystemExit:
    pass
except BaseException as e:
    err = type(e).__name__ + ": " + str(e)[:200]
finally:
    sys.settrace(None)
json.dump({"steps": steps, "error": err}, open(out, "w", encoding="utf-8"))
'''


def pick_trace_input(ws: Workspace, pid: str) -> Optional[Path]:
    """優先追蹤失敗的那筆測資；否則最小的一筆。大測資追蹤沒有意義，所以挑小的。"""
    cases = [f for f, _ in find_cases(ws.tests / pid)]
    if not cases:
        return None
    fail = load_failure(ws, pid)
    if fail:
        tmp = ws.meta / "trace_input.txt"
        tmp.write_text(fail["input"], encoding="utf-8")
        if len(fail["input"]) < 4000:
            return tmp
    return min(cases, key=lambda f: f.stat().st_size)


def trace_program(ws: Workspace, pid: str, limit: int = 200) -> Dict[str, Any]:
    sol = solution_file(ws, pid)
    if sol.suffix != ".py":
        raise ValueError("逐行追蹤目前只支援 Python")
    if not sol.exists():
        raise ValueError("還沒有解答檔")
    inp = pick_trace_input(ws, pid)
    if inp is None:
        raise ValueError("沒有測資可追蹤")
    with tempfile.TemporaryDirectory() as d:
        runner, out = Path(d) / "tracer.py", Path(d) / "out.json"
        runner.write_text(_TRACER, encoding="utf-8")
        try:
            subprocess.run([sys.executable, str(runner), str(sol), str(inp), str(out), str(limit)],
                           capture_output=True, timeout=15)
        except subprocess.TimeoutExpired:
            raise ValueError("追蹤超時（程式可能有無窮迴圈）")
        if not out.exists():
            raise ValueError("追蹤失敗")
        data = json.loads(out.read_text(encoding="utf-8"))
    src = sol.read_text(encoding="utf-8").splitlines()
    for s in data["steps"]:
        s["text"] = src[s["line"] - 1].strip() if 0 < s["line"] <= len(src) else ""
    data["input"] = inp.read_text(encoding="utf-8")[:2000]
    data["truncated"] = data.get("error") == "truncated"
    return data


# ---------- 常見陷阱（靜態檢查，不用 AI）----------
BUILTIN_NAMES = {n for n in dir(builtins) if not n.startswith("_") and n[0].islower()}
SHADOW_WATCH = {"list", "dict", "set", "str", "int", "sum", "max", "min", "len", "map", "input", "print",
                "sorted", "range", "abs", "all", "any", "tuple", "id", "type", "next", "iter", "filter"}


def _list_like(e: ast.AST) -> bool:
    if isinstance(e, (ast.List, ast.ListComp)):
        return True
    return isinstance(e, ast.BinOp) and isinstance(e.op, ast.Mult) and (isinstance(e.left, ast.List) or isinstance(e.right, ast.List))


def lint(code: str) -> List[Dict[str, Any]]:
    """只抓『初學者最常見、而且語法上完全合法』的陷阱。每筆回傳 line / tag / message。"""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    out: List[Dict[str, Any]] = []

    def add(node, tag, msg):
        out.append({"line": getattr(node, "lineno", 1), "tag": tag, "message": msg})

    for node in ast.walk(tree):
        # 1. 把內建名稱當變數：sum = 0 之後再呼叫 sum(...)
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        elif isinstance(node, (ast.For, ast.comprehension)):
            targets = [node.target]
        for t in targets:
            for n in ast.walk(t):
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id in SHADOW_WATCH:
                    add(n, "shadow-builtin", f"變數名稱 `{n.id}` 蓋掉了 Python 內建的 `{n.id}()`；之後再呼叫 {n.id}(...) 會出錯")
        # 2. [[0]*n]*m：每一列是同一個 list
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            for a in (node.left, node.right):
                if isinstance(a, ast.List) and any(_list_like(e) for e in a.elts):
                    add(node, "alias-list", "`[[...]] * m` 讓每一列指向同一個 list，改一格會全部一起變；改用 `[[0]*C for _ in range(R)]`")
                    break
        # 3. x = a.sort()：sort() 回傳 None
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
            if node.value.func.attr in ("sort", "append", "reverse", "extend", "remove"):
                add(node, "none-return", f"`.{node.value.func.attr}()` 會直接修改 list 並回傳 None；這樣賦值會讓變數變成 None")
        # 4. list.pop(0) / insert(0, …)：O(n)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "pop" and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == 0:
                add(node, "slow-pop0", "`list.pop(0)` 是 O(n)；在迴圈裡用會很慢，改用 `collections.deque.popleft()`")
            if node.func.attr == "insert" and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == 0:
                add(node, "slow-insert0", "`list.insert(0, x)` 是 O(n)；在迴圈裡用會很慢，改用 deque.appendleft()")
        # 5. `in` 對 list 字面量變數在迴圈中：交給人判斷，不檢查
        # 6. 可變預設參數
        if isinstance(node, ast.FunctionDef):
            for d in node.args.defaults:
                if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                    add(d, "mutable-default", "預設參數用了 list／dict／set：它在函式定義時只建立一次，會跨呼叫累積")
        # 7. input() 直接拿來比大小或運算（沒有 int）
        if isinstance(node, ast.Compare):
            for side in [node.left] + node.comparators:
                if isinstance(side, ast.Call) and isinstance(side.func, ast.Name) and side.func.id == "input":
                    add(side, "input-str", "`input()` 讀到的是字串；直接比較大小會變成字典序比較（'10' < '9'）")
    seen, uniq = set(), []
    for o in sorted(out, key=lambda o: o["line"]):
        k = (o["line"], o["tag"])
        if k not in seen:
            seen.add(k)
            uniq.append(o)
    return uniq


def statement_for(ws: Workspace, pid: str) -> str:
    """題目敘述的唯一來源：內建練習題依語言設定即時組出（切換語言立刻生效）；你自己匯入的題目讀 statements/。"""
    txt = ws.root / "statements" / f"{pid}.txt"
    if bank_mod.is_drill(pid) and not txt.exists():                 # 你用 cpe import 覆蓋過的內建題才讀檔
        return bank_mod.drill_statement(pid, bank_mod.resolve_lang(ws, pid))
    for ext in ("md", "txt"):
        f = ws.root / "statements" / f"{pid}.{ext}"
        if f.exists():
            return f.read_text(encoding="utf-8")
    return ""


# ---------- 單題畫面資料 ----------
def problem_view(ws: Workspace, bank: Dict[str, dict], pid: str) -> Dict[str, Any]:
    p = bank_mod.resolve(bank, pid)
    sol = solution_file(ws, pid)
    st = ws.state()
    sp = st["problems"].get(pid)
    stmt = statement_for(ws, pid)
    drill = bank_mod.is_drill(pid)
    return {"id": pid, "title": p.get("title", pid), "title_en": p.get("title_en"),
            "lang_mode": bank_mod.resolve_lang(ws, pid) if drill else ("en" if statement_is_english(stmt) else "zh"),
            "has_english": bank_mod.has_english(pid), "lang_setting": ws.config().get("statement_lang", "auto"), "topic": p.get("topic", ""), "difficulty": p.get("difficulty", 1),
            "url": p.get("url"), "statement": stmt, "code": sol.read_text(encoding="utf-8") if sol.exists() else None,
            "lang": "cpp" if sol.suffix == ".cpp" else "py", "file": str(sol.relative_to(ws.root)) if sol.exists() else None,
            "tests": len(find_cases(ws.tests / pid)),
            "attempts": sp["attempts"] if sp else 0, "hint_level": sp["hint_level"] if sp else -1,
            "attempts_since_hint": sp["attempts_since_hint"] if sp else 0,
            "last_verdict": sp["last_verdict"] if sp else None,
            "solved": bool(sp and sp["first_pass"] is not None),
            "review_stage": sp["review_stage"] if sp else None,
            "giveup_at": sp["giveup_at"] if sp else None,
            "unlock_at": (sp["giveup_at"] + 24 * 3600) if sp and sp["giveup_at"] else None,
            "now": ws.now(),
            "exam": ws.exam_active()}


# ---------- 題目匯入（範例 → 測資）----------
SAMPLE_IN = re.compile(r"^\s*(?:#+\s*)?(?:sample\s+input|範例\s*輸入|輸入\s*範例|測試\s*輸入)\b.*$", re.I)
SAMPLE_OUT = re.compile(r"^\s*(?:#+\s*)?(?:sample\s+output|範例\s*輸出|輸出\s*範例|測試\s*輸出)\b.*$", re.I)


def parse_samples(text: str) -> List[tuple]:
    """從題目文字找出 (範例輸入, 範例輸出) 配對。支援 Sample Input/Output、範例輸入/輸出。"""
    marks = []
    lines_ = text.replace("\r\n", "\n").split("\n")
    for i, ln in enumerate(lines_):
        if SAMPLE_IN.match(ln):
            marks.append((i, "in"))
        elif SAMPLE_OUT.match(ln):
            marks.append((i, "out"))
    blocks = []
    for k, (i, kind) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines_)
        body = lines_[i + 1:end]
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        if body and body[0].strip().startswith("```"):          # Markdown 的程式碼區塊圍欄不是資料
            body.pop(0)
            for j in range(len(body) - 1, -1, -1):
                if body[j].strip().startswith("```"):
                    body = body[:j]
                    break
        blocks.append((kind, "\n".join(body)))
    out, pending = [], None
    for kind, body in blocks:
        if kind == "in":
            pending = body
        elif pending is not None:
            out.append((pending, body))
            pending = None
    return out




class _TextOnly(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: List[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4", "pre"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        if tag in ("p", "div", "pre", "li", "tr"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_to_text(text: str) -> str:
    t = _TextOnly()
    t.feed(text)
    return re.sub(r"\n{3,}", "\n\n", "".join(t.parts))


def looks_like_html(text: str) -> bool:
    return bool(re.search(r"<(html|body|div|p|pre|br|table|h[1-6])[\s>/]", text[:4000], re.I))


def read_statement_file(path: Path) -> str:
    """讀題目檔；.html 會先轉成純文字（保留 pre 內的換行）；.pdf（UVa 的題目 PDF）用內建的擷取器轉成文字。"""
    if path.suffix.lower() == ".pdf":
        from . import uvastatement
        return uvastatement.from_pdf(path.read_bytes()).text
    text = path.read_text(encoding="utf-8", errors="replace")
    return html_to_text(text) if path.suffix.lower() in (".html", ".htm") else text


def add_test(ws: Workspace, pid: str, inp: str, out: str) -> str:
    d = ws.tests / pid
    d.mkdir(parents=True, exist_ok=True)
    n = len(list(d.glob("*.in"))) + 1
    while (d / f"case{n:02d}.in").exists():
        n += 1
    name = f"case{n:02d}"
    (d / f"{name}.in").write_text(inp if inp.endswith("\n") else inp + "\n", encoding="utf-8")
    (d / f"{name}.out").write_text(out if out.endswith("\n") else out + "\n", encoding="utf-8")
    return name


def import_statement(ws: Workspace, pid: str, text: str) -> int:
    """存下題目文字並把範例建成測資 sample01…（重新匯入會取代舊的 sample*，不會重複）。回傳範例組數。"""
    if looks_like_html(text):                      # 從網頁複製／上傳的 HTML：先轉成純文字
        text = html_to_text(text)
    (ws.root / "statements").mkdir(exist_ok=True)
    (ws.root / "statements" / f"{pid}.txt").write_text(text, encoding="utf-8")
    d = ws.tests / pid
    for old in list(d.glob("sample*")) if d.is_dir() else []:
        old.unlink()
    samples = parse_samples(text)
    if samples:
        d.mkdir(parents=True, exist_ok=True)
    for i, (inp, out) in enumerate(samples, 1):
        (d / f"sample{i:02d}.in").write_text(inp if inp.endswith("\n") else inp + "\n", encoding="utf-8")
        (d / f"sample{i:02d}.out").write_text(out if out.endswith("\n") else out + "\n", encoding="utf-8")
    return len(samples)


def statement_is_english(text: str) -> bool:
    """題目文字是不是（主要）英文：中日韓字元少於 3%，且有足夠的英文字母。"""
    cjk = len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return latin >= 80 and cjk / max(1, cjk + latin) < 0.03
