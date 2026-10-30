"""範例變異對拍：不需要輸入產生器。

官方只給範例時，通過範例不代表正確。這裡拿現有測資（範例）的輸入當種子，保持原本的行與欄位結構，
只變動數值（在該欄位觀察到的範圍內，加上邊界值），再拿你的『暴力解』當標準答案和你的解對拍；
不一致的輸入縮小後存成新測資（tests/<題號>/fuzzNN.*），之後 cpe test 會一起跑。

限制（誠實說明）：
- 變異只改數值與同一行內的順序，不會改變筆數、字串長度這類『結構』，所以它補的是邊界與特殊值，不是大規模測資。
- 它不知道題目的限制條件。極少數情況下變異出來的輸入可能不合法；差異輸出會附上輸入，請自己確認合法再保留。
- 暴力解必須先通過所有現有測資，否則不會開始（避免用錯的標準答案污染測資）。
"""
from __future__ import annotations

import random
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from . import judge
from .judge import AC, RE, TLE, MLE, WA, compare, prepare, run_program

INT = re.compile(r"^[+-]?\d+$")
Lines = List[List[str]]


def parse(text: str) -> Lines:
    return [ln.split() for ln in text.replace("\r\n", "\n").split("\n")]


def render(lines: Lines) -> str:
    while lines and not lines[-1]:
        lines = lines[:-1]
    return "\n".join(" ".join(ln) for ln in lines) + "\n"


def _is_int(tok: str) -> bool:
    return bool(INT.match(tok)) and len(tok.lstrip("+-")) <= 18


def structural(lines: Lines) -> Set[Tuple[int, int]]:
    """看起來是『後面有幾筆資料』的計數 token：改了就會讓輸入結構壞掉，所以不動。"""
    out: Set[Tuple[int, int]] = set()
    non_empty = [i for i, ln in enumerate(lines) if ln]
    for i, ln in enumerate(lines):
        for j, tok in enumerate(ln):
            if not _is_int(tok) or int(tok) < 0:
                continue
            v = int(tok)
            nxt = lines[i + 1] if i + 1 < len(lines) else []
            after = sum(1 for k in non_empty if k > i)
            if (v >= 1 and len(nxt) == v) or (v >= 1 and after == v) or (v >= 1 and after == v + 1 and j == 0) or (v == 0 and not nxt and i + 1 < len(lines)):
                out.add((i, j))
            elif j == 0 and len(ln) >= 2 and v == len(ln) - 1:
                out.add((i, j))                                  # 同一行『個數＋資料』
    return out


def _column_rows(lines: Lines) -> Set[int]:
    """屬於『多行同欄數』表格（例如邊 u v w）的行：每一欄有各自的意義，不能打亂順序。"""
    by_len: Dict[int, List[int]] = {}
    for i, ln in enumerate(lines):
        if ln and all(_is_int(t) for t in ln):
            by_len.setdefault(len(ln), []).append(i)
    return {i for idxs in by_len.values() if len(idxs) >= 3 for i in idxs}


def _groups(lines: Lines) -> Dict[Tuple[int, int], Tuple[int, int]]:
    """每個整數 token → 允許的範圍 (lo, hi)。同樣欄數的行超過 2 行就用『欄位』的範圍（例如邊 u v w），否則用整行的範圍。"""
    by_len: Dict[int, List[int]] = {}
    for i, ln in enumerate(lines):
        if ln and all(_is_int(t) for t in ln):
            by_len.setdefault(len(ln), []).append(i)
    rng_of: Dict[Tuple[int, int], Tuple[int, int]] = {}
    for n, idxs in by_len.items():
        if len(idxs) >= 3:
            for j in range(n):
                col = [int(lines[i][j]) for i in idxs]
                for i in idxs:
                    rng_of[(i, j)] = (min(col), max(col))
        else:
            for i in idxs:
                vals = [int(t) for t in lines[i]]
                for j in range(n):
                    rng_of[(i, j)] = (min(vals), max(vals))
    return rng_of


def mutate(lines: Lines, rng: random.Random, fixed: Set[Tuple[int, int]], ranges: Dict[Tuple[int, int], Tuple[int, int]]) -> Lines:
    out = [list(ln) for ln in lines]
    cells = [(i, j) for i, ln in enumerate(out) for j, t in enumerate(ln) if _is_int(t) and (i, j) not in fixed]
    if not cells:
        return out
    for _ in range(rng.choice((1, 1, 2, 3))):
        i, j = rng.choice(cells)
        v = int(out[i][j])
        lo, hi = ranges.get((i, j), (min(0, v), max(1, v)))
        lo, hi = min(lo, v), max(hi, v)
        pick = rng.choice(("edge", "edge", "near", "rand", "rand"))
        if pick == "edge":
            new = rng.choice((lo, hi, lo + 1, hi - 1, (lo + hi) // 2))
        elif pick == "near":
            new = v + rng.choice((-1, 1))
        else:
            new = rng.randint(lo, hi) if lo <= hi else v
        out[i][j] = str(min(hi, max(lo, new)))
    if rng.random() < 0.25:                                      # 同一行全是整數、又不是計數行：打亂順序（陣列題的順序特例）
        table = _column_rows(out)
        rows = [i for i, ln in enumerate(out) if i not in table and len(ln) >= 3 and all(_is_int(t) for t in ln) and not any((i, j) in fixed for j in range(len(ln)))]
        if rows:
            r = rng.choice(rows)
            rng.shuffle(out[r])
    return out


class FuzzError(RuntimeError):
    pass


def _verdict(rs, rb) -> Optional[str]:
    if rs.timed_out:
        return TLE
    if rs.mle:
        return MLE
    if rs.rc != 0:
        return RE
    return WA if compare(rs.out, rb.out) != AC else None


def fuzz(solution: Path, brute: Path, tests_dir: Path, rounds: int = 300, seed: int = 1, max_found: int = 3,
         timeout: float = 3.0, mem_mb: int = judge.DEFAULT_MEM_MB, deadline_s: float = 60.0) -> Dict[str, Any]:
    import time
    cases = judge.find_cases(tests_dir)
    if not cases:
        raise FuzzError("沒有現有測資可當種子。先用 cpe import／cpe addtest 加入範例。")
    cmd_s, tmp_s, err_s = prepare(solution)
    cmd_b, tmp_b, err_b = prepare(brute)
    try:
        if err_s or err_b:
            raise FuzzError(err_s or err_b)
        for fin, fout in cases:                                   # 暴力解要先通過現有測資，才有資格當標準答案
            r = run_program(brute, fin.read_text(encoding="utf-8"), timeout, cmd_b, mem_mb)
            if r.timed_out or r.rc != 0 or compare(r.out, fout.read_text(encoding="utf-8")) != AC:
                raise FuzzError(f"你的暴力解沒有通過現有測資 {fin.name}，不能拿來當標準答案。先把暴力解修好。")
        seeds = []
        for fin, _ in cases:
            lines = parse(fin.read_text(encoding="utf-8"))
            seeds.append((lines, structural(lines), _groups(lines)))
        known = {render(s[0]) for s in seeds}
        rng = random.Random(seed)
        found: List[Dict[str, Any]] = []
        skipped = tried = 0
        start = time.time()

        def check(text: str) -> Optional[Dict[str, Any]]:
            rb = run_program(brute, text, timeout, cmd_b, mem_mb)
            if rb.timed_out or rb.rc != 0:
                return {"skip": True}
            rs = run_program(solution, text, timeout, cmd_s, mem_mb)
            v = _verdict(rs, rb)
            return {"skip": False, "verdict": v, "brute_out": rb.out, "sol_out": rs.out, "sol_err": rs.err} if v else {"skip": False, "verdict": None}

        for _ in range(rounds):
            if len(found) >= max_found or time.time() - start > deadline_s:
                break
            lines, fixed, ranges = rng.choice(seeds)
            text = render(mutate(lines, rng, fixed, ranges))
            if text in known:
                continue
            known.add(text)
            tried += 1
            res = check(text)
            if res["skip"]:
                skipped += 1
                continue
            if not res["verdict"]:
                continue
            small = _shrink(text, res, check, fixed, ranges)
            if small["input"] in {f["input"] for f in found}:
                continue
            found.append(small)
        return {"tried": tried, "skipped": skipped, "found": found, "seeds": len(seeds)}
    finally:
        for t in (tmp_s, tmp_b):
            if t:
                shutil.rmtree(t, ignore_errors=True)


def _shrink(text: str, res: Dict[str, Any], check, fixed, ranges, budget: int = 60) -> Dict[str, Any]:
    """把差異輸入裡的數字盡量換成較小的值（0、1、一半），只要仍然不一致就保留。"""
    lines = parse(text)
    best = dict(res, input=text)
    for i, ln in enumerate(lines):
        for j, tok in enumerate(ln):
            if budget <= 0:
                return best
            if not _is_int(tok) or (i, j) in fixed:
                continue
            v = int(tok)
            lo = ranges.get((i, j), (0, v))[0]
            for cand in dict.fromkeys([lo, 0 if lo <= 0 else lo, 1 if lo <= 1 else lo, v // 2 if abs(v) > 1 else v]):
                if cand == v or cand < min(lo, 0):
                    continue
                trial = [list(x) for x in lines]
                trial[i][j] = str(cand)
                t = render(trial)
                budget -= 1
                r = check(t)
                if not r["skip"] and r["verdict"]:
                    lines = trial
                    best = dict(r, input=t)
                    break
                if budget <= 0:
                    return best
    return best


def save(ws, pid: str, found: List[Dict[str, Any]]) -> List[str]:
    """差異輸入存成 tests/<id>/fuzzNN.in/.out（預期輸出用暴力解的結果）。"""
    d = ws.tests / pid
    d.mkdir(parents=True, exist_ok=True)
    names = []
    n = len(list(d.glob("fuzz*.in")))
    for f in found:
        n += 1
        while (d / f"fuzz{n:02d}.in").exists():
            n += 1
        name = f"fuzz{n:02d}"
        (d / f"{name}.in").write_text(f["input"], encoding="utf-8")
        (d / f"{name}.out").write_text(f["brute_out"] if f["brute_out"].endswith("\n") else f["brute_out"] + "\n", encoding="utf-8")
        names.append(name)
    return names
