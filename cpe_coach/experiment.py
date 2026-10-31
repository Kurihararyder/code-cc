"""自我實驗框架：用資料檢驗一個功能是不是真的有效，而不是憑感覺。

目前只有一個實驗：複習排程「FSRS（預設）」對「固定間隔 1／3／7／14／30／60 天」。需要自己開啟（cpe exp start），
因為它會刻意讓大約一半的題用另一種排程。分組用題號的雜湊（穩定、不能自己挑），結果用 Wilson 信賴區間，樣本不夠就明說看不出差別。

要特別注意的限制：單人、題數少，統計檢定力很低；兩組的間隔本來就不同，所以比較的是「間隔」與「複習時還記得的比例」兩個數字，
不能只看成功率（間隔短當然成功率高）。除非兩個數字同時有明確差異，否則結論就是「看不出差別」。
"""
from __future__ import annotations

import hashlib
import math
import statistics
from typing import Any, Dict, List, Tuple

LADDER = [1, 3, 7, 14, 30, 60]
MIN_PER_ARM = 30


def enabled(ws) -> bool:
    return bool(ws.config().get("experiments", {}).get("scheduler"))


def set_enabled(ws, on: bool) -> None:
    cfg = ws.config()
    ex = dict(cfg.get("experiments", {}))
    ex["scheduler"] = bool(on)
    if on and "salt" not in ex:
        ex["salt"] = hashlib.sha1(str(ws.root).encode("utf-8")).hexdigest()[:8]
    cfg["experiments"] = ex
    ws.save_config(cfg)
    ws.log("experiment", name="scheduler", on=bool(on))


def arm(ws, pid: str) -> str:
    """穩定的分組：同一題永遠在同一組（不會因為成績而被換組）。實驗沒開時全部是 fsrs。"""
    if not enabled(ws):
        return "fsrs"
    salt = ws.config().get("experiments", {}).get("salt", "")
    return "fixed" if hashlib.sha1((salt + pid).encode("utf-8")).digest()[0] % 2 else "fsrs"


def fixed_due(log: List[Tuple[float, int, float]]) -> float:
    """固定間隔排程：從最近一次遺忘（或第一次）算起，連續成功幾次就用階梯上的第幾個間隔。log 是 Card.log。"""
    streak = 0
    for _, g, _r in log:
        streak = 0 if g == 1 else streak + 1
    k = min(max(streak - 1, 0), len(LADDER) - 1)
    return log[-1][0] + LADDER[k] * 86400.0


def wilson(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def analyze(ws, cards: Dict[str, Any]) -> Dict[str, Any]:
    arms: Dict[str, Dict[str, Any]] = {a: {"reviews": 0, "ok": 0, "gaps": []} for a in ("fsrs", "fixed")}
    for pid, c in cards.items():
        a = arm(ws, pid)
        for i in range(1, len(c.log)):
            ts, g, _ = c.log[i]
            arms[a]["reviews"] += 1
            arms[a]["ok"] += 1 if g != 1 else 0
            arms[a]["gaps"].append((ts - c.log[i - 1][0]) / 86400.0)
    out: Dict[str, Any] = {"enabled": enabled(ws), "arms": {}}
    for a, d in arms.items():
        lo, hi = wilson(d["ok"], d["reviews"])
        out["arms"][a] = {"reviews": d["reviews"], "recall_rate": round(d["ok"] / d["reviews"], 3) if d["reviews"] else None, "ci": [round(lo, 3), round(hi, 3)],
                          "median_gap_days": round(statistics.median(d["gaps"]), 1) if d["gaps"] else None}
    f, x = out["arms"]["fsrs"], out["arms"]["fixed"]
    if min(f["reviews"], x["reviews"]) < MIN_PER_ARM:
        out["conclusion"] = f"每組至少要有 {MIN_PER_ARM} 次複習才有意義（目前 FSRS {f['reviews']} 次、固定 {x['reviews']} 次）：資料不夠，看不出差別。"
    else:
        sep_rate = f["ci"][0] > x["ci"][1] or x["ci"][0] > f["ci"][1]
        gap_f, gap_x = f["median_gap_days"] or 0, x["median_gap_days"] or 0
        if not sep_rate:
            out["conclusion"] = f"兩組複習時記得的比例的信賴區間重疊（FSRS {f['recall_rate']}、固定 {x['recall_rate']}）：看不出差別；比較間隔：FSRS 中位數 {gap_f} 天、固定 {gap_x} 天。"
        elif f["recall_rate"] >= x["recall_rate"] and gap_f >= gap_x:
            out["conclusion"] = "FSRS 組記得的比例不比固定組低，而且間隔更長（更省力）：這份資料支持 FSRS。"
        else:
            out["conclusion"] = "兩組的記得比例有差異，但要和間隔一起看（間隔短自然記得比較多），不能直接說誰比較好。"
    return out
