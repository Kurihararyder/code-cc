"""儀表板、課程地圖、統計所需的資料（純資料，不含畫面）。"""
from __future__ import annotations

import datetime as dt
import time
from collections import Counter
from typing import Any, Dict, List, Optional

from . import bank as bank_mod
from . import course as course_mod
from . import mock, pastexams, srs, stats, weakness
from .judge import VERDICT_ZH
from .store import Workspace

DAY = 86400.0
STAGE_NAMES = {0: "Python 基礎", 1: "競程 I/O", 2: "資料結構", 3: "圖論與 DP", 4: "進階與 C++", 5: "衝刺"}
STAGE_GOALS = {0: "打好語法", 1: "CPE 2 題", 2: "CPE 3 題", 3: "CPE 4 題", 4: "CPE 5 題", 5: "CPE 6 題"}


def _day(ts: float) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def heatmap(events: List[dict], now: float, days: int = 84) -> List[Dict[str, Any]]:
    """最近 days 天，每天的提交次數（含今天）。"""
    cnt = Counter(_day(e["ts"]) for e in events if e["kind"] == "test")
    out = []
    for i in range(days - 1, -1, -1):
        d = _day(now - i * DAY)
        out.append({"d": d, "n": cnt.get(d, 0)})
    return out


def activity(events: List[dict], limit: int = 8) -> List[Dict[str, Any]]:
    items = []
    for e in reversed(events):
        k = e["kind"]
        if k == "test":
            text = f"{e['problem']} {'通過 ✓' if e['verdict'] == 'AC' else VERDICT_ZH.get(e['verdict'], e['verdict'])}"
            tone = "ok" if e["verdict"] == "AC" else "bad"
        elif k == "ask":
            text = f"{e['problem']} 問了 AI（{ {'explain': '解釋', 'question': '考我', 'mismatch': '預期不同'}.get(e.get('ask_kind'), '詢問') }）"
            tone = "info"
        elif k == "hint":
            text = f"{e['problem']} 用了提示 L{e['level']}"
            tone = "warn"
        elif k == "unit_done":
            text = f"完成單元 {e['unit']} 🎉"
            tone = "ok"
        elif k == "exam_finish":
            text = f"交卷：{e.get('solved', 0)}/{e.get('total', 0)} 題"
            tone = "info"
        elif k == "giveup":
            text = f"{e['problem']} 放棄"
            tone = "warn"
        else:
            continue
        items.append({"ts": e["ts"], "text": text, "tone": tone})
        if len(items) >= limit:
            break
    return items


def _unit_stub(u: Dict[str, Any]) -> Dict[str, Any]:
    a, b = course_mod.week_range(u)
    return {"n": u["n"], "title": u["title"], "stage": u["stage"], "weeks": [a, b], "lang": u["lang"],
            "has_gate": bool(u["gate"])}


def dashboard(ws: Workspace, bank: Dict[str, dict], course: Dict[str, Any], ai: Dict[str, Any], start: dt.date) -> Dict[str, Any]:
    st, now, events = ws.state(), ws.now(), ws.events()
    summary = stats.summarize(st, events, now)
    u = course_mod.current_unit(ws, course)
    wk = course_mod.expected_week(start, dt.date.fromtimestamp(now))
    unit = None
    nxt = None
    gate_ready = False
    if u:
        done, todo = course_mod.unit_progress(ws, u)
        gate_ready = bool(u["gate"]) and not todo
        unit = {**_unit_stub(u), "goal": u["goal"], "progress": {"done": len(done), "total": len(u["drills"])},
                "gate_ready": gate_ready, "gate": u["gate"]}
        pid = todo[0] if todo else next((a for a in u["anchors"] if not (st["problems"].get(a) and st["problems"][a]["first_pass"])), None)
        if pid:
            p = bank_mod.resolve(bank, pid)
            nxt = {"id": pid, "title": p["title"], "topic": p.get("topic", ""), "difficulty": p.get("difficulty", 1),
                   "role": "必做" if pid in u["drills"] else "真題"}
        eu = course_mod.expected_unit(course, wk)
        unit["pace"] = eu["n"] - u["n"]            # >0 落後、<0 超前
        unit["expected_unit"] = eu["n"]
    week_tests = [e for e in events if e["kind"] == "test" and now - e["ts"] <= 7 * DAY]
    exam = ws.exam()
    return {
        "date": _day(now), "week": wk, "unit": unit, "next": nxt,
        "due": [{"id": pid, "title": bank_mod.resolve(bank, pid)["title"]} for pid, _ in srs.due_list(st, now)],
        "stats": {**summary["counts"], "streak": summary["streak"], "practice_days": summary["practice_days"],
                  "attempts_week": len(week_tests), "ac_week": sum(1 for e in week_tests if e["verdict"] == "AC"),
                  "review_attempts": summary["review_attempts"], "review_clean_passes": summary["review_clean_passes"]},
        "predict": {"total": summary["predict_total"], "correct": summary["predict_correct"]},
        "heatmap": heatmap(events, now),
        "activity": activity(events),
        "exam": exam_view(ws, exam),
        "ai": ai,
        "first_run": not events and not st["problems"],
    }


def exam_view(ws: Workspace, exam: Optional[Dict[str, Any]], bank: Optional[Dict[str, dict]] = None) -> Optional[Dict[str, Any]]:
    if not exam:
        return None
    bank = bank if bank is not None else bank_mod.load_bank(ws)
    board = mock.scoreboard(exam, bank, pastexams.load_all(ws)["distribution"])
    rows = {r["id"]: r for r in board["rows"]}
    return {"kind": exam["kind"], "minutes": exam["minutes"], "left": int(mock.remaining_seconds(exam, ws.now())),
            "lang": exam.get("lang", "py"), "gate": exam.get("gate"), "past": exam.get("past"), "board": board,
            "problems": [{"id": pid, "wrong": r["wrong"], "solved": r["ac_min"] is not None, "ac_min": r["ac_min"],
                          "title": rows[pid]["title"], "stars": rows[pid]["stars"], "accuracy": rows[pid]["accuracy"]}
                         for pid, r in exam["results"].items()]}


def course_map(ws: Workspace, course: Dict[str, Any], start: dt.date) -> Dict[str, Any]:
    st = ws.state()
    cur = st["course"]["unit"]
    done = set(st["course"]["done"])
    wk = course_mod.expected_week(start, dt.date.fromtimestamp(ws.now()))
    stages = []
    for sn in range(6):
        units = []
        for u in course["units"]:
            if u["stage"] != sn:
                continue
            status = "done" if u["n"] in done else ("current" if u["n"] == cur else "upcoming")
            units.append({**_unit_stub(u), "status": status})
        a = min(x["weeks"][0] for x in units)
        b = max(x["weeks"][1] for x in units)
        stages.append({"stage": sn, "name": STAGE_NAMES[sn], "goal": STAGE_GOALS[sn], "weeks": [a, b], "units": units,
                       "done": sum(1 for x in units if x["status"] == "done")})
    return {"stages": stages, "current": cur, "week": wk, "total_weeks": course["total_weeks"],
            "done": len(done), "total": len(course["units"])}


def unit_detail(ws: Workspace, bank: Dict[str, dict], course: Dict[str, Any], n: int) -> Dict[str, Any]:
    u = course_mod.get_unit(course, n)
    if not u:
        raise ValueError(f"單元只有 1–{len(course['units'])}")
    st = ws.state()
    ev = ws.events()

    def prob(pid: str, role: str) -> Dict[str, Any]:
        p = bank_mod.resolve(bank, pid)
        sp = st["problems"].get(pid)
        return {"id": pid, "title": p["title"], "topic": p.get("topic", ""), "difficulty": p.get("difficulty", 1), "role": role,
                "done": course_mod.passed_in_lang(ev, pid, u["lang"]) if role != "真題" else bool(sp and sp["first_pass"]),
                "has_tests": bank_mod.is_drill(pid) or any((ws.tests / pid).glob("*.in")), "url": p.get("url")}

    gate = None
    if u["gate"]:
        g = u["gate"]
        gate = {**g, "problems": [prob(x, "檢核") for x in g.get("problems", [])]}
    return {**_unit_stub(u), "goal": u["goal"], "learn": u["learn"], "pitfalls": u["pitfalls"], "check": u["check"],
            "read": u.get("read", []), "pool": u["pool"], "eng": u["eng"],
            "resources": [course["resources"][r] for r in u["resources"]],
            "drills": [prob(d, "必做") for d in u["drills"]], "anchors": [prob(a, "真題") for a in u["anchors"]],
            "gate": gate, "past_pool": pastexams.unit_pool(ws, bank, n),
            "weak": (lambda a: dict(a, suggestions=weakness.suggestions(ws, bank, course, a, per_family=3, families=4)))(weakness.analyze(ws, bank, course)) if n == 49 else None,
            "status": "done" if n in st["course"]["done"] else ("current" if n == st["course"]["unit"] else "upcoming")}


def stats_view(ws: Workspace) -> Dict[str, Any]:
    st, now, events = ws.state(), ws.now(), ws.events()
    s = stats.summarize(st, events, now)
    tests = [e for e in events if e["kind"] == "test"]
    by_day = Counter(_day(e["ts"]) for e in tests)
    return {**{k: s[k] for k in ("counts", "attempts_total", "attempts_week", "verdicts_total", "verdicts_week",
                                 "hints_by_level", "giveups", "external_ai", "review_attempts", "review_clean_passes",
                                 "practice_days", "streak", "predict_total", "predict_correct", "asks", "asks_verified")},
            "exams": st["exams"][-12:], "heatmap": heatmap(events, now, 168), "best_day": max(by_day.values(), default=0)}
