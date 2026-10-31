"""學習工坊：概念測驗（含適性診斷）、示範題與漸進空白練習、Parsons 排序題、找 bug、預測輸出、微課、術語表、解法比較。

題目內容在 data/lab/*.json，由 dev/gen_lab.py 實際執行過原始碼產生（答案與輸出都是跑出來的，不是手寫的）。
適性診斷用 3PL 模型（猜對機率固定 0.25）；題目難度 b 是我估的、沒有用真實作答資料校準，所以診斷結果是「大略的起點建議」。
"""
from __future__ import annotations

import json
import math
import random
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import concepts
from .judge import run_program

DATA = Path(__file__).parent / "data" / "lab"
_cache: Dict[str, List[Dict[str, Any]]] = {}
GUESS = 0.25
MAX_Q, MIN_Q, SE_STOP = 12, 6, 0.45


def items(name: str) -> List[Dict[str, Any]]:
    if name not in _cache:
        _cache[name] = json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))["items"]
    return _cache[name]


def by_id(name: str, key: str, value: Any) -> Dict[str, Any]:
    for it in items(name):
        if it[key] == value:
            return it
    raise ValueError(f"找不到 {name} 的 {value}")


# ---------- 適性診斷（CAT） ----------
def _p(theta: float, b: float) -> float:
    return GUESS + (1 - GUESS) / (1 + math.exp(-(theta - b)))


def _info(theta: float, b: float) -> float:
    s = 1 / (1 + math.exp(-(theta - b)))
    p = GUESS + (1 - GUESS) * s
    dp = (1 - GUESS) * s * (1 - s)
    return dp * dp / (p * (1 - p))


def estimate(asked: List[Dict[str, Any]]) -> Dict[str, float]:
    """MAP 估計（先驗 N(0, 1.2²)，避免全對或全錯時估到無限大）；格點搜尋，穩定又好測。"""
    quiz = {q["id"]: q for q in items("quiz")}
    best, best_ll = 0.0, -1e18
    for i in range(-60, 61):
        th = i * 0.05
        ll = -(th * th) / (2 * 1.2 ** 2)
        for a in asked:
            p = _p(th, quiz[a["id"]]["b"])
            ll += math.log(p) if a["correct"] else math.log(1 - p)
        if ll > best_ll:
            best, best_ll = th, ll
    inf = 1 / 1.2 ** 2 + sum(_info(best, quiz[a["id"]]["b"]) for a in asked)
    return {"theta": round(best, 2), "se": round(1 / math.sqrt(inf), 2)}


def cat_new() -> Dict[str, Any]:
    return {"asked": [], "theta": 0.0, "se": 1.2, "done": False}


def cat_next(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if state["done"]:
        return None
    seen = {a["id"] for a in state["asked"]}
    seen_c = {a["concept"] for a in state["asked"]}
    pool = [q for q in items("quiz") if q["id"] not in seen]
    if not pool:
        return None
    th = state["theta"]
    best = max(pool, key=lambda q: (_info(th, q["b"]) * (1.15 if q["concept"] not in seen_c else 1.0), -abs(q["b"] - th)))
    return {k: best[k] for k in ("id", "concept", "q", "code", "stdin", "choices")}


def cat_answer(state: Dict[str, Any], qid: str, choice: int) -> Dict[str, Any]:
    q = by_id("quiz", "id", qid)
    if any(a["id"] == qid for a in state["asked"]):
        raise ValueError("這題已經回答過了")
    if not 0 <= choice < len(q["choices"]):
        raise ValueError("選項不存在")
    correct = choice == q["answer"]
    state["asked"].append({"id": qid, "concept": q["concept"], "correct": correct, "choice": choice})
    state.update(estimate(state["asked"]))
    n = len(state["asked"])
    if n >= MAX_Q or (n >= MIN_Q and state["se"] <= SE_STOP) or n >= len(items("quiz")):
        state["done"] = True
    return {"correct": correct, "answer": q["answer"], "why": q["why"], "state": state}


def cat_result(state: Dict[str, Any]) -> Dict[str, Any]:
    cs = concepts.load()
    wrong = sorted({a["concept"] for a in state["asked"] if not a["correct"]}, key=lambda c: cs[c]["unit"])
    right = sorted({a["concept"] for a in state["asked"] if a["correct"]} - set(wrong), key=lambda c: cs[c]["unit"])
    if wrong:
        start = max(1, cs[wrong[0]]["unit"])
        why = f"從第一個答錯的知識點「{cs[wrong[0]]['name']}」（單元 {start}）開始補起。"
    elif right:
        start = max(cs[c]["unit"] for c in right)
        why = f"測到的知識點都答對了：可以從單元 {start} 附近開始（測驗題數很少，保守一點可以往前翻幾個單元）。"
    else:
        start, why = 1, "還沒有作答。"
    level = "初學" if state["theta"] < -0.8 else "基礎" if state["theta"] < 0.2 else "中階" if state["theta"] < 1.0 else "進階"
    return {"theta": state["theta"], "se": state["se"], "level": level, "answered": len(state["asked"]), "correct": sum(1 for a in state["asked"] if a["correct"]),
            "weak": [{"concept": c, "name": cs[c]["name"], "unit": cs[c]["unit"]} for c in wrong], "strong": [{"concept": c, "name": cs[c]["name"]} for c in right],
            "start_unit": start, "why": why, "caveat": f"只問了 {len(state['asked'])} 題，題目難度是我估的，這只是大略的起點建議；誤差約 ±{state['se']}。"}


def practice(concept: str, n: int = 5, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    pool = [q for q in items("quiz") if q["concept"] == concept]
    rng = random.Random(seed)
    rng.shuffle(pool)
    return [{k: q[k] for k in ("id", "concept", "q", "code", "stdin", "choices")} for q in sorted(pool[:n], key=lambda q: q["b"])]


def grade(qid: str, choice: int) -> Dict[str, Any]:
    q = by_id("quiz", "id", qid)
    return {"correct": choice == q["answer"], "answer": q["answer"], "why": q["why"]}


# ---------- 執行學習者的程式 ----------
def run_tests(code: str, tests: List[Dict[str, str]], timeout: float = 5.0) -> Dict[str, Any]:
    """用題目的測試輸入跑 code，和預期輸出比（忽略行尾空白與結尾換行）。"""
    results = []
    with tempfile.TemporaryDirectory(prefix="cpe-lab-") as d:
        f = Path(d) / "p.py"
        f.write_text(code + "\n", encoding="utf-8")
        for t in tests:
            r = run_program(f, t["in"], timeout)
            got = "\n".join(ln.rstrip() for ln in r.out.rstrip("\n").split("\n"))
            want = "\n".join(ln.rstrip() for ln in t["out"].rstrip("\n").split("\n"))
            ok = r.rc == 0 and not r.timed_out and got == want
            results.append({"ok": ok, "input": t["in"], "expected": want, "got": got, "error": "逾時" if r.timed_out else ((r.err.strip().splitlines() or [""])[-1] if r.rc != 0 else "")})
    return {"ok": all(x["ok"] for x in results), "results": results}


# ---------- 示範題 → 漸進空白 → Parsons ----------
def faded(w: Dict[str, Any], level: int) -> Dict[str, Any]:
    """level 0 = 完整示範；1 = 最後一步留白；2 = 最後兩步留白…；最多留白到只剩第一步。"""
    n = len(w["steps"])
    level = max(0, min(level, n - 1))
    keep = n - level
    return {"id": w["id"], "level": level, "max_level": n - 1, "problem": w["problem"],
            "given": [{"say": s["say"], "code": s["code"]} for s in w["steps"][:keep]],
            "blank": [{"say": s["say"]} for s in w["steps"][keep:]], "tests": w["tests"][:1] if level else w["tests"]}


def check_faded(w: Dict[str, Any], level: int, answer: str) -> Dict[str, Any]:
    f = faded(w, level)
    code = "\n".join(s["code"] for s in f["given"]) + "\n" + answer
    r = run_tests(code, w["tests"])
    r["solution"] = "\n".join(s["code"] for s in w["steps"]) if not r["ok"] else None
    return r


def parsons(w: Dict[str, Any], seed: int = 0) -> Dict[str, Any]:
    """把標準解答的每一行（保留縮排）打亂，另外混進幾行干擾行；學習者排出正確順序（可以不用干擾行）。"""
    lines = [ln for s in w["steps"] for ln in s["code"].split("\n") if ln.strip()]
    pool = [{"text": ln, "distractor": False} for ln in lines] + [{"text": d, "distractor": True} for d in w.get("distractors", [])]
    rng = random.Random(seed)
    rng.shuffle(pool)
    return {"id": w["id"], "problem": w["problem"], "lines": [{"id": i, "text": x["text"]} for i, x in enumerate(pool)],
            "_answer_ids": [i for i, x in enumerate(pool) if not x["distractor"]], "_text": [x["text"] for x in pool]}


def check_parsons(w: Dict[str, Any], seed: int, order: List[int]) -> Dict[str, Any]:
    p = parsons(w, seed)
    if any(not isinstance(i, int) or not 0 <= i < len(p["lines"]) for i in order) or len(set(order)) != len(order):
        raise ValueError("排序裡有不存在或重複的行")
    code = "\n".join(p["_text"][i] for i in order)
    r = run_tests(code, w["tests"])
    r["exact"] = [p["_text"][i] for i in order] == [ln for s in w["steps"] for ln in s["code"].split("\n") if ln.strip()]
    return r


# ---------- 找 bug／預測輸出 ----------
def check_bug(b: Dict[str, Any], line: int, fixed_code: Optional[str] = None) -> Dict[str, Any]:
    res: Dict[str, Any] = {"found": line in b["bug_lines"], "bug_lines": b["bug_lines"], "why": b["why"]}
    if fixed_code is not None:
        res["fix"] = run_tests(fixed_code, b["tests"])
    return res


def check_predict(p: Dict[str, Any], answer: str) -> Dict[str, Any]:
    norm = lambda s: "\n".join(" ".join(ln.split()) for ln in s.strip().split("\n"))      # noqa: E731
    return {"correct": norm(answer) == norm(p["output"]), "output": p["output"]}


# ---------- 查詢 ----------
def lesson(concept: str) -> Dict[str, Any]:
    return by_id("lessons", "concept", concept)


def search_glossary(q: str, limit: int = 20) -> List[Dict[str, str]]:
    q = q.strip().lower()
    rows = items("glossary")
    if not q:
        return rows[:limit]
    scored = []
    for r in rows:
        en, zh, note = r["en"].lower(), r["zh"], r["note"].lower()
        if en == q:
            scored.append((0, r))
        elif en.startswith(q) or q in en.split():
            scored.append((1, r))
        elif q in en or q in zh or q in note:
            scored.append((2, r))
    return [r for _, r in sorted(scored, key=lambda x: (x[0], x[1]["en"]))][:limit]
