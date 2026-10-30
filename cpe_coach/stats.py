"""學習統計：用客觀指標（無提示重寫、模擬考題數）取代『感覺』，避免能力錯覺。"""
from __future__ import annotations

import time
from collections import Counter
from typing import Any, Dict, List

from . import srs

DAY = 86400.0


def _day(ts: float) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def summarize(st: Dict[str, Any], events: List[Dict[str, Any]], now: float) -> Dict[str, Any]:
    tests = [e for e in events if e["kind"] == "test"]
    week = [e for e in tests if now - e["ts"] <= 7 * DAY]
    hints = Counter(e["level"] for e in events if e["kind"] == "hint")
    reviews = [e for e in tests if e.get("review_attempt")]
    clean_reviews = [e for e in reviews if e["verdict"] == "AC" and e.get("clean")]
    day_set = {_day(e["ts"]) for e in tests}
    streak, t = 0, now
    if _day(now) not in day_set:           # 今天還沒練不算中斷
        t -= DAY
    while _day(t) in day_set:
        streak += 1
        t -= DAY
    return {
        "counts": srs.counts(st),
        "attempts_total": len(tests),
        "attempts_week": len(week),
        "verdicts_total": dict(Counter(e["verdict"] for e in tests)),
        "verdicts_week": dict(Counter(e["verdict"] for e in week)),
        "hints_by_level": dict(sorted(hints.items())),
        "giveups": sum(1 for e in events if e["kind"] == "giveup"),
        "external_ai": sum(1 for e in events if e["kind"] == "external_ai"),
        "review_attempts": len(reviews),
        "review_clean_passes": len(clean_reviews),
        "practice_days": len(day_set),
        "streak": streak,
        "exams": st["exams"],
    }
