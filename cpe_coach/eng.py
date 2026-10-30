"""工程能力線：每個任務都有自動驗收，通過才算完成（不是自己勾）。

驗收分三種：auto（程式實際執行你的作品來檢查）、semi（靜態檢查＋盡量執行）、manual（需要你提供證據連結，例如 PR 網址）。
"""
from __future__ import annotations

import ast
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import judge
from .roadmap import ENGINEERING
from .store import Workspace

Result = Tuple[bool, str]
ID_RE = re.compile(r"\b(d\d{3}|e\d{3}|uva\d+|cpe\d{8}q\d)\b")
MUTATIONS = [(" + ", " - "), ("<=", "<"), (">=", ">"), (" == ", " != "), (" < ", " > "), (" * ", " + "), ("+ 1", "+ 2"), (" max(", " min(")]


# ---------- 小工具 ----------
def _run(cmd: List[str], cwd: Path, timeout: int = 120) -> Tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)
    except subprocess.TimeoutExpired:
        return 124, f"執行超過 {timeout} 秒"
    except FileNotFoundError as e:
        return 127, str(e)


def _have_pytest() -> bool:
    return _run([sys.executable, "-c", "import pytest"], Path("."), 20)[0] == 0


# 沒有安裝 pytest 時的備援：照 pytest 的慣例（test_*.py 裡 test 開頭的函式、用 assert）跑，不支援 fixture。
MINI_RUNNER = r"""
import importlib.util, inspect, sys, traceback
from pathlib import Path
d = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(d))
ran = failed = 0
for f in sorted(d.glob("test_*.py")):
    spec = importlib.util.spec_from_file_location(f.stem, f)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        traceback.print_exc()
        print("FAILED to import", f.name)
        sys.exit(1)
    for name, fn in sorted(vars(mod).items()):
        if name.startswith("test") and inspect.isfunction(fn):
            if inspect.signature(fn).parameters:
                print(name, "needs fixtures: install pytest (python -m pip install pytest)")
                failed += 1
                continue
            ran += 1
            try:
                fn()
            except BaseException:
                failed += 1
                print("FAILED", f.name + "::" + name)
                traceback.print_exc(limit=3)
print(ran, "ran,", failed, "failed")
sys.exit(1 if failed or not ran else 0)
"""


def _test_cmd(folder: Path) -> List[str]:
    if _have_pytest():
        return [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", str(folder)]
    return [sys.executable, "-c", MINI_RUNNER, str(folder)]


def _tail(text: str, n: int = 8) -> str:
    return "\n".join(text.strip().splitlines()[-n:])


def _parse(path: Path) -> Optional[ast.AST]:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError, UnicodeDecodeError):
        return None


def _test_stats(files: List[Path]) -> Dict[str, Any]:
    tests = asserts = 0
    ids = set()
    for f in files:
        tree = _parse(f)
        if tree is None:
            continue
        ids |= set(ID_RE.findall(f.read_text(encoding="utf-8")))
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test"):
                tests += 1
            if isinstance(n, ast.Assert):
                asserts += 1
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr.startswith("assert"):
                asserts += 1
    return {"tests": tests, "asserts": asserts, "ids": ids}


# ---------- 檢查項 ----------
def check_git_days(ws: Workspace, days: int) -> Result:
    if shutil.which("git") is None:
        return False, "找不到 git。先安裝 git（https://git-scm.com），再在工作區裡 git init。"
    if not (ws.root / ".git").exists():
        return False, "工作區還不是 git 倉庫。在工作區資料夾執行：git init && git add -A && git commit -m \"first\""
    rc, out = _run(["git", "log", "--format=%ad", "--date=short", "--", "solutions"], ws.root, 30)
    ds = sorted(set(out.split()))
    return (len(ds) >= days, f"solutions/ 的 commit 分布在 {len(ds)} 個不同日期（需要 ≥ {days}）：{', '.join(ds[-5:]) or '無'}")


def check_tests(ws: Workspace, folder: str = "eng", min_tests: int = 3, min_problems: int = 3, mutate: bool = True) -> List[Tuple[str, bool, str]]:
    d = ws.root / folder
    files = sorted(d.glob("test_*.py")) if d.is_dir() else []
    out: List[Tuple[str, bool, str]] = []
    if not files:
        return [("有測試檔", False, f"{folder}/ 底下找不到 test_*.py。先用 cpe eng start 建立範本。")]
    st = _test_stats(files)
    out.append((f"至少 {min_tests} 個測試函式", st["tests"] >= min_tests, f"目前 {st['tests']} 個"))
    out.append((f"至少 {min_tests * 2} 個斷言（含邊界案例）", st["asserts"] >= min_tests * 2, f"目前 {st['asserts']} 個"))
    real = sorted(i for i in st["ids"] if (ws.root / "solutions" / f"{i}.py").exists())
    out.append((f"測試涵蓋至少 {min_problems} 題（對應 solutions/ 內存在的解答）", len(real) >= min_problems, f"涵蓋：{', '.join(real) or '無'}"))
    rc, log = _run(_test_cmd(d), ws.root)
    out.append(("測試全部通過", rc == 0, "通過" if rc == 0 else _tail(log)))
    if mutate and rc == 0 and real:
        killed, tried = [], 0
        with tempfile.TemporaryDirectory(prefix="cpe-mut-") as td:
            tmp = Path(td)
            shutil.copytree(d, tmp / folder, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
            (tmp / "solutions").mkdir()
            for pid in real[:4]:
                f = tmp / "solutions" / f"{pid}.py"
                shutil.copyfile(ws.root / "solutions" / f"{pid}.py", f)
                src = f.read_text(encoding="utf-8")
                for old, new in MUTATIONS:
                    if old in src:
                        tried += 1
                        f.write_text(src.replace(old, new, 1), encoding="utf-8")
                        if _run(_test_cmd(tmp / folder), tmp, 120)[0] != 0:
                            killed.append(pid)
                        f.write_text(src, encoding="utf-8")
                        break
        ok = (len(killed) >= min(2, tried)) if tried else True
        out.append(("測試抓得到錯誤（把解答改壞，測試要變紅）", ok,
                    f"{len(killed)}/{tried} 題的壞版本被你的測試抓到" + ("" if ok else "。測試要用相對路徑呼叫 solutions/<題號>.py（見 eng/solhelp.py），否則改壞的版本不會被測到")))
    return out


def check_stress(ws: Workspace, rounds: int = 100) -> List[Tuple[str, bool, str]]:
    base = ws.root / "eng" / "stress"
    dirs = [d for d in sorted(base.iterdir()) if d.is_dir() and not d.name.startswith("_")] if base.is_dir() else []
    if not dirs:
        return [("對拍資料夾", False, "找不到 eng/stress/<題號>/ （要有 gen.py 與 brute.py）。見 eng/stress/README.md")]
    d = dirs[0]
    sol, gen, brute = ws.root / "solutions" / f"{d.name}.py", d / "gen.py", d / "brute.py"
    missing = [str(p.relative_to(ws.root)) for p in (sol, gen, brute) if not p.exists()]
    if missing:
        return [("檔案齊全", False, "缺少：" + "、".join(missing))]
    out: List[Tuple[str, bool, str]] = [("檔案齊全", True, f"題目 {d.name}")]
    outs = set()
    for seed in range(1, 21):
        rc, txt = _run([sys.executable, str(gen), str(seed)], ws.root, 10)
        if rc != 0:
            return out + [("產生器可以執行", False, _tail(txt))]
        outs.add(txt)
    out.append(("產生器每個 seed 產生不同輸入", len(outs) >= 10, f"20 個 seed 產生 {len(outs)} 種不同輸入"))
    out.append(("暴力解與正解不是同一份程式", sol.read_text(encoding="utf-8").strip() != brute.read_text(encoding="utf-8").strip(), ""))
    try:
        r = judge.stress(sol, brute, gen, rounds)
        out.append((f"對拍 {rounds} 組沒有發現不一致", r is None, "全部一致" if r is None else f"seed={r[0]} 不一致（{r[4]}）"))
    except RuntimeError as e:
        out.append((f"對拍 {rounds} 組", False, str(e)))
    return out


def check_project(ws: Workspace, name: str = "", need_argparse: bool = False, min_hints: int = 0, need_pyproject: bool = False, tests: int = 0) -> List[Tuple[str, bool, str]]:
    base = ws.root / "projects"
    dirs = [d for d in sorted(base.iterdir()) if d.is_dir() and not d.name.startswith("_")] if base.is_dir() else []
    if name:
        dirs = [d for d in dirs if d.name == name] or dirs
    if not dirs:
        return [("專案資料夾", False, "找不到 projects/<名稱>/")]
    d = dirs[0]
    files = [f for f in d.rglob("*.py") if "tests" not in f.parts and not f.name.startswith("test_") and "__pycache__" not in f.parts]
    out: List[Tuple[str, bool, str]] = [("專案資料夾", True, d.name)]
    if need_pyproject:
        pp = d / "pyproject.toml"
        out.append(("pyproject.toml 有 [project] 與 name", pp.exists() and "[project]" in pp.read_text(encoding="utf-8") and re.search(r"(?m)^name\s*=", pp.read_text(encoding="utf-8")) is not None, ""))
    if min_hints:
        n = 0
        for f in files:
            t = _parse(f)
            for node in ast.walk(t) if t else []:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    n += (node.returns is not None) + sum(1 for a in node.args.args if a.annotation is not None)
        out.append((f"型別標註至少 {min_hints} 處", n >= min_hints, f"目前 {n} 處"))
    if need_argparse:
        found = any("argparse" in f.read_text(encoding="utf-8") or "typer" in f.read_text(encoding="utf-8") for f in files)
        out.append(("使用 argparse（或 typer）", found, ""))
    if tests:
        tf = [f for f in d.rglob("test_*.py")]
        st = _test_stats(tf)
        out.append((f"至少 {tests} 個測試", st["tests"] >= tests, f"目前 {st['tests']} 個"))
        rc, log = _run(_test_cmd(d), d)
        out.append(("專案的測試全部通過", rc == 0, "通過" if rc == 0 else _tail(log)))
    rc, log = _run([sys.executable, "-m", "compileall", "-q", str(d)], ws.root, 60)
    out.append(("所有檔案語法正確", rc == 0, _tail(log) if rc else ""))
    return out


def check_sqlite(ws: Workspace) -> List[Tuple[str, bool, str]]:
    script, sql, db = ws.root / "eng" / "progress_db.py", ws.root / "eng" / "queries.sql", ws.root / "eng" / "progress.db"
    if not script.exists():
        return [("eng/progress_db.py", False, "找不到。用 cpe eng start 6 建立範本。")]
    if db.exists():
        db.unlink()
    rc, log = _run([sys.executable, str(script)], ws.root, 60)
    out: List[Tuple[str, bool, str]] = [("progress_db.py 可以執行", rc == 0, "" if rc == 0 else _tail(log))]
    if rc != 0 or not db.exists():
        return out + [("產生 eng/progress.db", False, "執行後沒有產生資料庫檔")]
    con = sqlite3.connect(str(db))
    try:
        tables = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
        n_events = len(ws.events())
        rows = con.execute("select count(*) from events").fetchone()[0] if "events" in tables else -1
    finally:
        con.close()
    out.append(("資料庫有 events 資料表", "events" in tables, f"資料表：{', '.join(tables) or '無'}"))
    out.append(("events 的筆數與 .cpe/events.jsonl 相同", rows == n_events, f"資料庫 {rows} 筆／事件紀錄 {n_events} 筆"))
    q = sql.read_text(encoding="utf-8").upper() if sql.exists() else ""
    out.append(("queries.sql 有 GROUP BY", "GROUP BY" in q, ""))
    out.append(("queries.sql 有 JOIN（需要第二張表，例如 problems）", "JOIN" in q, ""))
    return out


def check_webapi(ws: Workspace) -> List[Tuple[str, bool, str]]:
    base = ws.root / "projects"
    cands = [d for d in sorted(base.iterdir()) if d.is_dir() and any(re.search(r"fastapi|flask", f.read_text(encoding="utf-8", errors="ignore"), re.I) for f in d.rglob("*.py"))] if base.is_dir() else []
    if not cands:
        return [("Web API 專案", False, "projects/ 底下找不到使用 fastapi 或 flask 的專案")]
    d = cands[0]
    routes = 0
    for f in d.rglob("*.py"):
        t = _parse(f)
        for n in ast.walk(t) if t else []:
            if isinstance(n, ast.FunctionDef):
                routes += sum(1 for dec in n.decorator_list if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in ("get", "post", "put", "delete", "route"))
    out = [("Web API 專案", True, d.name), ("至少 2 個路由", routes >= 2, f"目前 {routes} 個")]
    tf = list(d.rglob("test_*.py"))
    out.append(("有測試", bool(tf) and _test_stats(tf)["tests"] >= 2, f"{len(tf)} 個測試檔"))
    return out


def check_url_evidence(evidence: Optional[str], pattern: str, label: str) -> List[Tuple[str, bool, str]]:
    ok = bool(evidence and re.match(pattern, evidence.strip()))
    return [(label, ok, "已提供" if ok else "請提供網址")]


def check_llm_app(ws: Workspace) -> List[Tuple[str, bool, str]]:
    base = ws.root / "projects"
    srcs = [f for f in base.rglob("*.py") if "test" not in f.name] if base.is_dir() else []
    txt = "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in srcs)
    out = [("找到使用 LLM API 的程式", bool(re.search(r"openai|anthropic|chat/completions|/v1/messages", txt, re.I)), "")]
    out.append(("金鑰從環境變數讀取、沒有寫死", "environ" in txt or "getenv" in txt, ""))
    out.append(("沒有把 sk- 開頭的金鑰寫在程式裡", not re.search(r"sk-[A-Za-z0-9]{16,}", txt), ""))
    out.append(("有錯誤處理與逾時（try/except 與 timeout）", "except" in txt and "timeout" in txt, ""))
    return out


def check_portfolio(ws: Workspace) -> List[Tuple[str, bool, str]]:
    base = ws.root / "projects"
    dirs = [d for d in sorted(base.iterdir()) if d.is_dir() and not d.name.startswith("_")] if base.is_dir() else []
    good = []
    for d in dirs:
        rd = d / "README.md"
        heads = len(re.findall(r"(?m)^#+\s", rd.read_text(encoding="utf-8"))) if rd.exists() else 0
        if heads >= 3 and list(d.rglob("test_*.py")):
            good.append(d.name)
    return [("至少 3 個專案各有 README（≥3 個標題）與測試", len(good) >= 3, f"符合的專案：{', '.join(good) or '無'}")]


# ---------- 任務表 ----------
SOLHELP = '''"""測試輔助：用子行程執行 solutions/<題號>.py，餵 stdin，回傳 stdout。
路徑用「相對於這個檔案」來算，驗收時才能把解答改壞來確認你的測試抓得到。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(pid: str, text: str, timeout: float = 5.0) -> str:
    p = subprocess.run([sys.executable, str(ROOT / "solutions" / f"{pid}.py")], input=text,
                       capture_output=True, text=True, timeout=timeout)
    return p.stdout
'''
TEST_SKEL = '''"""為你已經通過的 3 題以上寫測試。每題至少一個『一般案例』和一個『邊界案例』。
執行：python -m pytest eng    （沒有 pytest 時：python -m unittest discover -s eng）"""
from solhelp import run


def test_d001_basic():
    assert run("d001", "Alice\\n") == "Hello, Alice!\\n"


# TODO: 再加 2 題以上（把 d002、d003 換成你解過的題號），每題都要有邊界案例
# def test_d002_negative_numbers():
#     assert run("d002", "-5 3\\n") == "-2\\n"
'''
STRESS_README = """# 對拍（stress testing）

把一題你已經通過的題目，寫成：

    eng/stress/<題號>/gen.py     # python gen.py <seed> → 印出一組隨機輸入（小範圍）
    eng/stress/<題號>/brute.py   # 最直白、一定對的暴力解

驗收會用不同的 seed 跑 20 次確認輸入有變化，再拿 solutions/<題號>.py 對拍 100 組，必須完全一致。
"""
DB_SKEL = '''"""把 .cpe/events.jsonl 讀進 SQLite（eng/progress.db），之後用 queries.sql 分析。
要求：資料表 events（筆數要和 events.jsonl 相同）與第二張表（例如 problems）。"""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
con = sqlite3.connect(ROOT / "eng" / "progress.db")
# TODO: create table events(...), 讀入 ROOT / ".cpe" / "events.jsonl" 的每一行
# TODO: create table problems(id, title, ...)，例如從 solutions/ 檔名建立
con.commit()
con.close()
'''
SQL_SKEL = "-- 每種判題結果各有幾次（GROUP BY）\n-- select verdict, count(*) from events where kind='test' group by verdict;\n-- 每題的提交次數與標題（JOIN）\n-- select p.id, p.title, count(*) from events e join problems p on p.id = e.problem group by p.id;\n"
CLI_SKEL = '''"""一個小型命令列工具（例如：統計 .cpe/events.jsonl）。用 argparse，並在 tests/ 寫至少 3 個測試。"""
import argparse


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="TODO")
    ap.add_argument("path")
    args = ap.parse_args(argv)
    # TODO
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

TASKS: Dict[int, Dict[str, Any]] = {
    1: {"kind": "auto", "scaffold": {}, "run": lambda ws, ev: [("solutions/ 的 commit 分布在 ≥ 3 個日期", *check_git_days(ws, 3))]},
    2: {"kind": "manual", "scaffold": {}, "run": lambda ws, ev: check_url_evidence(ev, r"^https://github\.com/[^/]+/[^/]+/pull/\d+/?$", "提供自己倉庫的 PR 網址（https://github.com/…/pull/N）")},
    3: {"kind": "auto", "scaffold": {"eng/solhelp.py": SOLHELP, "eng/test_solutions.py": TEST_SKEL}, "run": lambda ws, ev: check_tests(ws)},
    4: {"kind": "auto", "scaffold": {"eng/stress/README.md": STRESS_README}, "run": lambda ws, ev: check_stress(ws)},
    5: {"kind": "semi", "scaffold": {}, "run": lambda ws, ev: check_project(ws, need_pyproject=True, min_hints=5)},
    6: {"kind": "auto", "scaffold": {"eng/progress_db.py": DB_SKEL, "eng/queries.sql": SQL_SKEL}, "run": lambda ws, ev: check_sqlite(ws)},
    7: {"kind": "auto", "scaffold": {"projects/cli/main.py": CLI_SKEL, "projects/cli/tests/test_main.py": "from main import main\n\n\n# TODO: 至少 3 個測試\n"},
        "run": lambda ws, ev: check_project(ws, name="cli", need_argparse=True, tests=3)},
    8: {"kind": "semi", "scaffold": {}, "run": lambda ws, ev: check_webapi(ws)},
    9: {"kind": "manual", "scaffold": {}, "run": lambda ws, ev: check_url_evidence(ev, r"^https://[^\s]+\.[^\s]+$", "提供部署後的網址（https://…）")},
    10: {"kind": "semi", "scaffold": {}, "run": lambda ws, ev: check_llm_app(ws)},
    11: {"kind": "semi", "scaffold": {}, "run": lambda ws, ev: check_portfolio(ws)},
}
KIND_ZH = {"auto": "自動驗收", "semi": "半自動（靜態檢查）", "manual": "需提供證據"}


def tasks(ws: Workspace) -> List[Dict[str, Any]]:
    st = ws.state()
    last: Dict[int, dict] = {}
    for e in ws.events():
        if e["kind"] == "eng_verify":
            last[e["task"]] = e
    out = []
    for t in ENGINEERING:
        cfg = TASKS.get(t["n"], {"kind": "manual", "scaffold": {}})
        out.append({"n": t["n"], "min_stage": t["min_stage"], "title": t["task"], "kind": cfg["kind"], "kind_zh": KIND_ZH[cfg["kind"]],
                    "done": t["n"] in st["eng_done"], "has_scaffold": bool(cfg["scaffold"]),
                    "last": {"ts": last[t["n"]]["ts"], "ok": last[t["n"]]["ok"]} if t["n"] in last else None})
    return out


def next_task(ws: Workspace, stage: int) -> Optional[Dict[str, Any]]:
    return next((t for t in tasks(ws) if t["min_stage"] <= stage and not t["done"]), None)


def start(ws: Workspace, n: int) -> List[str]:
    cfg = TASKS.get(n)
    if cfg is None:
        raise ValueError("沒有這個任務編號")
    made = []
    for rel, content in cfg["scaffold"].items():
        f = ws.root / rel
        if f.exists():
            continue
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
        made.append(rel)
    ws.log("eng_start", task=n)
    return made


def verify(ws: Workspace, n: int, evidence: Optional[str] = None) -> Dict[str, Any]:
    cfg = TASKS.get(n)
    if cfg is None:
        raise ValueError("沒有這個任務編號")
    results = [{"label": lab, "ok": bool(ok), "msg": msg} for lab, ok, msg in cfg["run"](ws, evidence)]
    ok = all(r["ok"] for r in results)
    ws.log("eng_verify", task=n, ok=ok)
    if ok:
        st = ws.state()
        if n not in st["eng_done"]:
            st["eng_done"].append(n)
            ws.save_state(st)
    return {"n": n, "ok": ok, "results": results}
