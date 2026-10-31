"""作答習慣：一天中哪個時段你答得好、有沒有疲勞或卡關的跡象。全部從事件紀錄算出，沒有額外收集。

誠實的限制：時段分析需要足夠的作答（每個時段 ≥ 8 次才下結論）；疲勞偵測是簡單規則，會誤報也會漏報。
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from . import knowledge

SLOTS = [("清晨", 5, 9), ("上午", 9, 12), ("下午", 12, 18), ("晚上", 18, 24), ("深夜", 0, 5)]
MIN_PER_SLOT = 8


def slot_of(ts: float) -> str:
    h = time.localtime(ts).tm_hour
    for name, a, b in SLOTS:
        if a <= h < b:
            return name
    return "深夜"


def by_time_of_day(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = {name: {"slot": name, "attempts": 0, "correct": 0} for name, _, _ in SLOTS}
    for a in knowledge.attempts(events):
        r = rows[slot_of(a["ts"])]
        r["attempts"] += 1
        r["correct"] += 1 if a["correct"] else 0
    out = []
    for name, _, _ in SLOTS:
        r = rows[name]
        r["rate"] = round(r["correct"] / r["attempts"], 3) if r["attempts"] else None
        r["enough"] = r["attempts"] >= MIN_PER_SLOT
        out.append(r)
    enough = [r for r in out if r["enough"]]
    best = max(enough, key=lambda r: r["rate"]) if len(enough) >= 2 else None
    worst = min(enough, key=lambda r: r["rate"]) if len(enough) >= 2 else None
    note = None
    if best and worst and best["rate"] - worst["rate"] >= 0.15:
        note = f"你在「{best['slot']}」一次通過率 {round(100 * best['rate'])}%，「{worst['slot']}」只有 {round(100 * worst['rate'])}%：新題排在{best['slot']}，複習排在其他時段。"
    elif not best:
        note = "每個時段至少要有 8 次作答才會下結論；資料還不夠。"
    return {"slots": out, "best": best["slot"] if best else None, "note": note}


def sessions(events: List[Dict[str, Any]], gap: float = 20 * 60.0) -> List[Dict[str, Any]]:
    """把相隔不超過 gap 的操作連成一次「連續學習」。"""
    ts = sorted(float(e["ts"]) for e in events if e.get("kind") in ("test", "hint", "ask", "giveup", "solution_viewed"))
    out: List[Dict[str, Any]] = []
    for t in ts:
        if out and t - out[-1]["end"] <= gap:
            out[-1]["end"] = t
            out[-1]["n"] += 1
        else:
            out.append({"start": t, "end": t, "n": 1})
    return out


def fatigue(events: List[Dict[str, Any]], now: float) -> List[Dict[str, str]]:
    """目前有沒有該休息的跡象。每一條都附原因，方便你自己判斷。"""
    signals: List[Dict[str, str]] = []
    recent = [e for e in events if e.get("kind") == "test" and e.get("verdict") not in (None, "SETUP") and now - float(e["ts"]) <= 90 * 60]
    streak = 0
    for e in reversed(recent):
        if e["verdict"] == "AC":
            break
        streak += 1
    if streak >= 6:
        signals.append({"id": "fail-streak", "level": "warn", "msg": f"最近連續 {streak} 次沒通過：休息 10 分鐘，或換一題、先看提示；硬撐的效率通常很低。"})
    ss = sessions(events)
    if ss and now - ss[-1]["end"] <= 20 * 60 and ss[-1]["end"] - ss[-1]["start"] >= 2 * 3600:
        signals.append({"id": "long-session", "level": "warn", "msg": f"已經連續學了約 {int((ss[-1]['end'] - ss[-1]['start']) / 60)} 分鐘：站起來動一動、喝水，休息 15 分鐘再繼續。"})
    h = time.localtime(now).tm_hour
    if 0 <= h < 5 and ss and now - ss[-1]["end"] <= 30 * 60:
        signals.append({"id": "late-night", "level": "info", "msg": "現在是深夜：睡眠對記憶的鞏固很重要，今天先到這裡通常比硬做更划算。"})
    same = [e["problem"] for e in recent]
    if same:
        top = max(set(same), key=same.count)
        if same.count(top) >= 10:
            signals.append({"id": "stuck-one", "level": "warn", "msg": f"最近 90 分鐘在 {top} 上提交了 {same.count(top)} 次：卡太久了，看提示或先換題，之後再回來。"})
    return signals
