"""診斷工具：把會讓你的程式出錯的輸入縮到最小（delta debugging）、實測時間複雜度、判斷解法屬於哪一類演算法。

誠實的限制：
- 縮小輸入只保證「縮小後仍然讓你的程式出同樣的錯」，縮小後的輸入不一定符合題目的限制（例如資料筆數和第一行的 n 對不上）。
  所以一定要有判斷標準：有暴力解就用「和暴力解的輸出不同」；沒有暴力解，就只能縮小「執行錯誤／逾時」這類不需要標準答案的失敗。
- 複雜度是用幾個輸入大小實測再擬合，Python 啟動時間與機器雜訊會影響，結果是估計不是證明；輸入的樣子（隨機）也可能避開最壞情況。
- 演算法類型是看語法特徵的啟發式判斷，不是理解你的程式。
"""
from __future__ import annotations

import ast
import math
import random
import re
import shutil
import statistics
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import judge
from .judge import AC, compare, prepare, run_program


# ---------- 21. 反例縮小 ----------
def ddmin(items: List[Any], fails: Callable[[List[Any]], bool], budget: int = 200) -> List[Any]:
    """標準的 delta debugging：找一個盡量小的子序列，使 fails 仍然為真。budget 是最多呼叫 fails 的次數。"""
    calls = [0]

    def test(xs: List[Any]) -> bool:
        if calls[0] >= budget:
            return False
        calls[0] += 1
        return fails(xs)
    n = 2
    cur = list(items)
    while len(cur) >= 2 and calls[0] < budget:
        size = max(1, len(cur) // n)
        chunks = [cur[i:i + size] for i in range(0, len(cur), size)]
        reduced = False
        for i, ch in enumerate(chunks):
            if test(ch):
                cur, n, reduced = ch, 2, True
                break
        if not reduced:
            for i in range(len(chunks)):
                comp = [x for j, c in enumerate(chunks) if j != i for x in c]
                if comp and test(comp):
                    cur, n, reduced = comp, max(n - 1, 2), True
                    break
        if not reduced:
            if n >= len(cur):
                break
            n = min(len(cur), n * 2)
    return cur


def minimize_input(text: str, fails: Callable[[str], bool], budget: int = 150) -> str:
    """縮小輸入：先刪行，再刪一行裡的字，最後把數字換成較小的值。fails(text) 為真代表這個輸入仍然讓程式出同樣的錯。"""
    if not fails(text):
        return text
    lines = text.replace("\r\n", "\n").rstrip("\n").split("\n")
    lines = ddmin(lines, lambda xs: fails("\n".join(xs) + "\n"), budget // 2)
    for i in range(len(lines)):
        toks = lines[i].split()
        if len(toks) > 1:
            def trial(ts: List[str], i: int = i) -> bool:
                return fails("\n".join(lines[:i] + [" ".join(ts)] + lines[i + 1:]) + "\n")
            lines[i] = " ".join(ddmin(toks, trial, 20))
    for i in range(len(lines)):
        toks = lines[i].split()
        for j, t in enumerate(toks):
            if re.fullmatch(r"-?\d{2,}", t):
                for cand in ("0", "1", str(int(t) // 2)):
                    if cand == t:
                        continue
                    tr = toks[:j] + [cand] + toks[j + 1:]
                    if fails("\n".join(lines[:i] + [" ".join(tr)] + lines[i + 1:]) + "\n"):
                        toks = tr
                        break
        lines[i] = " ".join(toks)
    return "\n".join(lines) + "\n"


def _err_kind(stderr: str) -> str:
    last = [ln for ln in stderr.strip().splitlines() if ln.strip()]
    return re.split(r"[:\s]", last[-1].strip(), 1)[0] if last else ""


def shrink_failure(solution: Path, failing_input: str, brute: Optional[Path] = None, timeout: float = 3.0,
                   mem_mb: int = judge.DEFAULT_MEM_MB, budget: int = 150) -> Dict[str, Any]:
    cmd_s, tmp_s, err_s = prepare(solution)
    cmd_b, tmp_b, err_b = prepare(brute) if brute else (None, None, None)
    try:
        if err_s or err_b:
            raise ValueError(err_s or err_b)
        first = run_program(solution, failing_input, timeout, cmd_s, mem_mb)
        kind = "TLE" if first.timed_out else ("RE" if first.rc != 0 else "WA")
        sig = _err_kind(first.err) if kind == "RE" else ""
        if kind == "WA" and not brute:
            raise ValueError("這個輸入你的程式沒有出錯，或是答案錯但沒有暴力解可以比對：加上 --brute 暴力解.py 才能縮小答案錯誤的輸入。")

        def fails(text: str) -> bool:
            if not text.strip():
                return False
            if brute:
                rb = run_program(brute, text, timeout, cmd_b, mem_mb)
                if rb.timed_out or rb.rc != 0:
                    return False                                         # 暴力解自己都答不出來的輸入不算（可能不合法）
            rs = run_program(solution, text, timeout, cmd_s, mem_mb)
            if kind == "TLE":
                return rs.timed_out
            if kind == "RE":
                return rs.rc != 0 and not rs.timed_out and _err_kind(rs.err) == sig
            return not rs.timed_out and rs.rc == 0 and compare(rs.out, rb.out) != AC
        if not fails(failing_input):
            raise ValueError("這個輸入用現在的程式已經不會出同樣的錯了。")
        small = minimize_input(failing_input, fails, budget)
        return {"kind": kind, "error": sig, "original": failing_input, "minimal": small,
                "original_size": len(failing_input), "minimal_size": len(small)}
    finally:
        for t in (tmp_s, tmp_b):
            if t:
                shutil.rmtree(t, ignore_errors=True)


# ---------- 23. 複雜度實測 ----------
MODELS: List[Tuple[str, Callable[[float], float]]] = [
    ("O(1)", lambda n: 1.0), ("O(log n)", lambda n: math.log2(n + 1)), ("O(n)", lambda n: n), ("O(n log n)", lambda n: n * math.log2(n + 1)),
    ("O(n²)", lambda n: n * n), ("O(n³)", lambda n: n ** 3)]


def fit_complexity(points: List[Tuple[int, float]], baseline: float = 0.0) -> Dict[str, Any]:
    """points：(輸入大小, 秒數)。扣掉啟動時間後，對每個模型 t = c·f(n)+0 在對數空間做最小平方，選殘差最小的。"""
    floor = max(0.01, 0.4 * baseline)                         # 比啟動時間多不了多少的量測只是雜訊，不拿來擬合
    pts = [(n, t - baseline) for n, t in points if t - baseline >= floor]
    if len(pts) < 3:
        return {"error": f"輸入太小：程式的執行時間幾乎都是啟動時間（約 {baseline * 1000:.0f} ms），量不出成長趨勢。請用 --sizes 給更大的輸入大小。", "points": points}
    scores = []
    for name, f in MODELS:
        logs = [math.log(t) - math.log(f(n)) for n, t in pts]
        c = sum(logs) / len(logs)
        err = math.sqrt(sum((x - c) ** 2 for x in logs) / len(logs))
        scores.append((err, name))
    scores.sort()
    xs, ys = [math.log(n) for n, _ in pts], [math.log(t) for _, t in pts]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / max(sum((x - mx) ** 2 for x in xs), 1e-12)
    margin = scores[1][0] - scores[0][0]
    return {"best": scores[0][1], "runner_up": scores[1][1], "slope": round(slope, 2), "margin": round(margin, 3), "confident": margin > 0.08 and len(pts) >= 4,
            "scores": {name: round(err, 3) for err, name in scores}}


def auto_input(sample: str, n: int, rng: random.Random) -> Optional[str]:
    """從範例輸入推測結構並放大到 n：支援『第一行 n，之後 n 個數字（同一行或 n 行）』。看不懂就回傳 None，請用 --gen。"""
    lines = [ln.split() for ln in sample.strip().split("\n") if ln.strip()]
    if not lines or len(lines[0]) != 1 or not re.fullmatch(r"\d+", lines[0][0]):
        return None
    nums = [int(t) for ln in lines[1:] for t in ln if re.fullmatch(r"-?\d+", t)]
    if not nums or len(nums) != sum(len(ln) for ln in lines[1:]):
        return None
    lo, hi = min(nums), max(nums)
    hi = max(hi, lo + 1)
    if len(lines) == 2 and len(lines[1]) == int(lines[0][0]):
        return f"{n}\n" + " ".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"
    if len(lines) == int(lines[0][0]) + 1 and len({len(ln) for ln in lines[1:]}) == 1:
        w = len(lines[1])
        return f"{n}\n" + "\n".join(" ".join(str(rng.randint(lo, hi)) for _ in range(w)) for _ in range(n)) + "\n"
    return None


def measure_complexity(solution: Path, make_input: Callable[[int], Optional[str]], sizes: List[int], timeout: float = 10.0,
                       repeat: int = 3, budget_s: float = 40.0, mem_mb: int = judge.DEFAULT_MEM_MB) -> Dict[str, Any]:
    cmd, tmp, err = prepare(solution)
    try:
        if err:
            raise ValueError(err)
        small = make_input(sizes[0])
        if small is None:
            raise ValueError("看不懂範例輸入的結構，沒辦法自動放大。請用 --gen 產生器.py（執行時收到一個參數 n，把大小為 n 的輸入印到標準輸出）。")
        base = min(_timed(solution, make_input(1) or small, cmd, timeout, mem_mb) for _ in range(2))
        pts: List[Tuple[int, float]] = []
        start = time.time()
        scale = 1
        for attempt in range(3):                                   # 量不出趨勢（時間都被啟動時間蓋過）就把輸入放大 4 倍再量
            for n in sizes:
                n = n * scale
                text = make_input(n)
                ts = []
                for _ in range(repeat):
                    t = _timed(solution, text, cmd, timeout, mem_mb)
                    if t is None:
                        res = fit_complexity(pts, base or 0) if len(pts) >= 3 else {}
                        return {**res, "error": f"n={n} 時逾時或出錯", "points": pts}
                    ts.append(t)
                pts.append((n, statistics.median(ts)))
                if time.time() - start > budget_s:
                    break
            res = fit_complexity(pts, base or 0.0)
            if "error" not in res or time.time() - start > budget_s * 0.6:
                break
            pts, scale = [], scale * 4
        res.update(points=pts or res.get("points", []), baseline=round(base or 0.0, 4))
        return res
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def _timed(solution: Path, text: str, cmd, timeout: float, mem_mb: int) -> Optional[float]:
    r = run_program(solution, text, timeout, cmd, mem_mb)
    if r.timed_out or r.rc != 0:
        return None
    return r.elapsed


def estimate_for_n_max(best: str, n_max: int, seconds_per_unit: float = 1e-7) -> Optional[str]:
    """如果題目的 n 上限是 n_max，這個複雜度大約要多久（粗估：每個基本操作 1e-7 秒，Python 通常更慢）。"""
    f = dict(MODELS).get(best)
    if f is None:
        return None
    ops = f(float(n_max))
    if ops > 5e9:
        return f"n={n_max} 時約 {ops:.1e} 次操作：幾乎一定會逾時（一般 1 秒大約 10⁷–10⁸ 次簡單操作）。"
    if ops > 2e8:
        return f"n={n_max} 時約 {ops:.1e} 次操作：Python 很可能逾時，C++ 才有機會。"
    return f"n={n_max} 時約 {ops:.1e} 次操作：通常來得及。"


# ---------- 24. 演算法簽名 ----------
CONCEPT_LABELS = {
    "sorting": {"排序"}, "greedy": {"排序", "貪心"}, "prefix_bs": {"二分", "前綴和"}, "two_ptr": {"雙指標"}, "stack_q": {"佇列／stack"},
    "heap": {"堆"}, "graph": {"圖搜尋", "佇列／stack"}, "dsu": {"並查集"}, "shortest": {"堆", "圖搜尋"}, "dp": {"動態規劃"}, "recursion": {"遞迴"},
    "bitmask": {"位元運算"}, "dict_set": {"雜湊"}, "numtheory": {"數學"}, "arith": {"數學"}, "base": {"位元運算", "數學"}, "bignum": {"數學"}}


def signature(code: str) -> Dict[str, Any]:
    """從語法特徵猜解法的類型。回傳 {labels, brute_force, depth, notes}。"""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"labels": [], "brute_force": False, "depth": 0, "notes": ["語法錯誤，無法分析"]}
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    imports = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    recursive = any(isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == f.name for f in funcs for c in ast.walk(f))

    def depth(node: ast.AST, d: int = 0) -> int:
        best = d
        for ch in ast.iter_child_nodes(node):
            best = max(best, depth(ch, d + 1 if isinstance(ch, (ast.For, ast.While)) else d))
        return best
    dp = depth(tree)
    labels = set()
    notes: List[str] = []
    if "sort" in names or "sorted" in names:
        labels.add("排序")
    if "heapq" in imports or {"heappush", "heappop"} & names:
        labels.add("堆")
    if "deque" in names or "popleft" in names:
        labels.add("佇列／stack")
    if "bisect" in imports or {"bisect_left", "bisect_right"} & names:
        labels.add("二分")
    if "lru_cache" in names or "cache" in names or "memo" in {n.lower() for n in names if isinstance(n, str)}:
        labels.add("動態規劃")
    if "accumulate" in names or "prefix" in {n.lower()[:6] for n in names if isinstance(n, str)}:
        labels.add("前綴和")
    if any(isinstance(n, ast.BinOp) and isinstance(n.op, (ast.BitAnd, ast.BitOr, ast.BitXor, ast.LShift, ast.RShift)) for n in ast.walk(tree)):
        labels.add("位元運算")
    if any(isinstance(n, (ast.Dict, ast.Set, ast.DictComp, ast.SetComp)) for n in ast.walk(tree)) or {"defaultdict", "Counter", "set", "dict"} & names:
        labels.add("雜湊")
    if recursive:
        labels.add("遞迴")
    if {"find", "parent", "union"} & {n.lower() for n in names if isinstance(n, str)}:
        labels.add("並查集")
    if "gcd" in names or "isqrt" in names or "sqrt" in names or any(isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Mod, ast.Pow)) for n in ast.walk(tree)):
        labels.add("數學")
    if any(isinstance(n, ast.Assign) and isinstance(n.value, (ast.ListComp,)) and isinstance(n.value.elt, ast.ListComp) for n in ast.walk(tree)) or \
            any(isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult) and isinstance(n.left, ast.List) and isinstance(n.right, ast.Name) for n in ast.walk(tree)):
        if dp >= 1 and ("min" in names or "max" in names or "dp" in {n.lower() for n in names if isinstance(n, str)}):
            labels.add("動態規劃")
    if "dp" in {n.lower() for n in names if isinstance(n, str)}:
        labels.add("動態規劃")
    if {"permutations", "combinations", "product"} & names:
        labels.add("暴力枚舉")
        notes.append("用 itertools 枚舉排列／組合：n 稍大就會爆炸（n! 或 2ⁿ）。")
    if dp >= 3:
        labels.add("暴力枚舉")
        notes.append(f"最深有 {dp} 層巢狀迴圈：可能是 O(n³) 的暴力解。")
    if dp == 0 and not recursive and not labels:
        labels.add("數學")
    brute = "暴力枚舉" in labels
    return {"labels": sorted(labels), "brute_force": brute, "depth": dp, "notes": notes}


def compare_with_expected(sig: Dict[str, Any], concept_ids: List[str]) -> Dict[str, Any]:
    expected = set()
    for c in concept_ids:
        expected |= CONCEPT_LABELS.get(c, set())
    got = set(sig["labels"])
    overlap = expected & got
    if not expected:
        verdict = "這題沒有可對照的預期類型。"
    elif overlap:
        verdict = "你的解法用到的技巧（" + "、".join(sorted(overlap)) + "）和這題的預期類型相符。"
    elif sig["brute_force"]:
        verdict = "你的解法看起來是暴力枚舉，而這題預期的是 " + "、".join(sorted(expected)) + "：小資料能過，輸入大時可能逾時。"
    else:
        verdict = "你的解法看起來和預期的類型（" + "、".join(sorted(expected)) + "）不同：可能是另一種可行的做法，也可能有誤判，請自己看看。"
    return {"verdict": verdict, "expected": sorted(expected), "got": sorted(got)}
