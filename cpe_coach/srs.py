"""間隔重練：靠提示或放棄才完成的題目，1／3／7 天後必須『無提示重寫』通過才算精熟。"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .judge import AC

DAY = 86400.0
INTERVALS_DAYS = [1, 3, 7]
MASTERED = 3


def is_dirty(p: Dict[str, Any]) -> bool:
    """這一輪是否借助了提示（L1 以上）或放棄看解答。L0 只是釐清題意，不算。"""
    return p["hint_level"] >= 1 or p["giveup_at"] is not None


def review_pending(p: Dict[str, Any]) -> bool:
    return p["review_stage"] is not None and p["review_stage"] < MASTERED


def review_due(p: Dict[str, Any], now: float) -> bool:
    return review_pending(p) and p["review_due"] is not None and now >= p["review_due"]


def record_result(p: Dict[str, Any], verdict: str, now: float) -> Dict[str, Any]:
    """依一次判題結果更新單題狀態，回傳說明（供 CLI 顯示與寫入事件紀錄）。"""
    info = {"review_attempt": review_due(p, now), "clean": not is_dirty(p), "advanced": False, "mastered": False}
    p["attempts"] += 1
    p["attempts_since_hint"] += 1
    p["last_verdict"] = verdict

    if verdict != AC:
        if info["review_attempt"]:   # 到期的重寫失敗：重新從 1 天後開始
            p["review_stage"] = 0
            p["review_due"] = now + INTERVALS_DAYS[0] * DAY
        return info

    p["passes"] += 1
    first = p["first_pass"] is None
    if first:
        p["first_pass"] = now
        if is_dirty(p):
            p["review_stage"], p["review_due"] = 0, now + INTERVALS_DAYS[0] * DAY
        else:
            p["review_stage"], p["review_due"] = MASTERED, None
            info["mastered"] = True
    elif info["review_attempt"]:
        if is_dirty(p):
            p["review_stage"], p["review_due"] = 0, now + INTERVALS_DAYS[0] * DAY
        else:
            p["review_stage"] += 1
            if p["review_stage"] >= MASTERED:
                p["review_stage"], p["review_due"] = MASTERED, None
                info["mastered"] = True
            else:
                p["review_due"] = now + INTERVALS_DAYS[p["review_stage"]] * DAY
            info["advanced"] = True
    p["last_pass"] = now
    # 新的一輪：提示與放棄紀錄歸零
    p["hint_level"] = -1
    p["attempts_since_hint"] = 0
    p["giveup_at"] = None
    return info


def due_list(st: Dict[str, Any], now: float) -> List[Tuple[str, Dict[str, Any]]]:
    items = [(pid, p) for pid, p in st["problems"].items() if review_due(p, now)]
    items.sort(key=lambda kv: kv[1]["review_due"])
    return items


def counts(st: Dict[str, Any]) -> Dict[str, int]:
    probs = st["problems"].values()
    return {
        "solved": sum(1 for p in probs if p["first_pass"] is not None),
        "mastered": sum(1 for p in probs if p["review_stage"] == MASTERED),
        "reviewing": sum(1 for p in probs if review_pending(p)),
    }
