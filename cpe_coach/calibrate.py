"""難度校準：用你自己的解題紀錄（時間、嘗試次數、提示）估計每題對你有多難，並和標示的星等比較。

這是很粗的估計：資料點少、而且「花了多久」受當天狀態影響很大。所以只在有足夠資料時才調整時間預估，
並且永遠同時顯示原本的星等。"""
from __future__ import annotations

import statistics
from typing import Any, Dict, List, Optional

from .store import Workspace

PRIOR_MIN = {1: 8, 2: 20, 3: 45, 4: 90}      # 各星等「預期」要花的分鐘（先驗）
GAP = 20 * 60                                 # 同一題兩次動作間隔超過 20 分鐘，視為中途離開
BASE_MIN = 5                                  # 第一次提交之前讀題與寫第一版的時間（沒有紀錄，用固定值）
THRESHOLDS = [(12, 1), (30, 2), (70, 3)]      # 投入分鐘 → 對你而言的星等（其餘 4）


def _stars(minutes: float) -> int:
    return next((s for lim, s in THRESHOLDS if minutes <= lim), 4)


def efforts(events: List[dict]) -> Dict[str, Dict[str, Any]]:
    """每一題「到第一次通過為止」的投入。"""
    per: Dict[str, List[dict]] = {}
    for e in events:
        if e.get("problem") and e["kind"] in ("test", "hint", "ask", "giveup"):
            per.setdefault(e["problem"], []).append(e)
    out: Dict[str, Dict[str, Any]] = {}
    for pid, evs in per.items():
        evs.sort(key=lambda e: e["ts"])
        first_ac = next((i for i, e in enumerate(evs) if e["kind"] == "test" and e["verdict"] == "AC"), None)
        if first_ac is None:
            continue
        upto = evs[:first_ac + 1]
        tests = [e for e in upto if e["kind"] == "test"]
        hints = [e for e in upto if e["kind"] in ("hint", "giveup") or (e["kind"] == "ask" and e.get("ask_kind") != "explain")]
        active = BASE_MIN + sum((b["ts"] - a["ts"]) / 60 for a, b in zip(upto, upto[1:]) if b["ts"] - a["ts"] <= GAP)
        attempts = len(tests)
        out[pid] = {"attempts": attempts, "hints": len(hints), "active_min": round(active, 1),
                    "effort_min": round(active + 4 * (attempts - 1) + 6 * len(hints), 1), "solved_ts": upto[-1]["ts"]}
    return out


def calibrate(ws: Workspace, bank: Dict[str, dict]) -> Dict[str, Any]:
    ef = efforts(ws.events())
    rows = []
    for pid, e in ef.items():
        b = bank.get(pid, {})
        listed = int(b.get("difficulty", 2))
        mine = _stars(e["effort_min"])
        rows.append({"id": pid, "title": b.get("title", pid), "listed": listed, "mine": mine, "delta": mine - listed,
                     "source": b.get("difficulty_source") or "估計", "accuracy": b.get("official_accuracy"), **e,
                     "label": "比標示難" if mine - listed >= 1 else "比標示簡單" if mine - listed <= -1 else "接近標示"})
    rows.sort(key=lambda r: (-abs(r["delta"]), -r["effort_min"]))
    ratios = [r["effort_min"] / PRIOR_MIN[r["listed"]] for r in rows]
    factor = 1.0
    if len(ratios) >= 3:
        factor = max(0.5, min(2.5, statistics.median(ratios)))
    by_star = {}
    for s in (1, 2, 3, 4):
        xs = [r["effort_min"] for r in rows if r["listed"] == s]
        if xs:
            by_star[s] = {"n": len(xs), "median": round(statistics.median(xs), 1), "prior": PRIOR_MIN[s]}
    return {"rows": rows, "factor": round(factor, 2), "by_star": by_star, "solved": len(rows),
            "enough": len(rows) >= 3, "note": "資料少於 3 題時不會調整時間預估。" if len(rows) < 3 else ""}


def est_minutes(bank: Dict[str, dict], pid: str, ef: Dict[str, Dict[str, Any]], factor: float, review: bool = False, spent: float = 0.0) -> int:
    """預估這題要花幾分鐘：重寫用過去投入的 60%；沒解過的用星等先驗 × 你的速度係數。"""
    if review and pid in ef:
        return max(5, int(round(ef[pid]["effort_min"] * 0.6)))
    stars = int(bank.get(pid, {}).get("difficulty", 2))
    base = PRIOR_MIN.get(stars, 20) * factor
    return max(5, int(round(base - spent)))
