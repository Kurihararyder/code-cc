"""課程軌道：py（現有的 CPE 主線）、cpp、verilog、tcl。非 py 軌道各自記進度（state["tracks"][軌道]）。

非 py 軌道的「待新增題目」還沒有題目與判題器，所以單元用手動標記完成；
有現成練習題（C++ 的 drills）的單元會同時顯示練習通過數。
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

from . import bank as bank_mod
from . import course as course_mod
from . import hdl as hdl_mod
from .store import Workspace

NAMES = {"py": "Python（CPE 主線）", "cpp": "C++（到演算法工程師）", "verilog": "Verilog／SystemVerilog（到晶片設計工程師）", "tcl": "Tcl（EDA 腳本）"}
ORDER = ["py", "cpp", "verilog", "tcl"]


def _check(track: str) -> str:
    if track not in course_mod.TRACKS:
        raise ValueError("軌道只有：" + "、".join(ORDER))
    return track


def _tstate(ws: Workspace, track: str) -> Dict[str, Any]:
    st = ws.state()
    if track == "py":
        return st["course"]
    return st.setdefault("tracks", {}).setdefault(track, {"unit": 1, "done": []})


def _save(ws: Workspace, track: str, ts: Dict[str, Any]) -> None:
    st = ws.state()
    if track == "py":
        st["course"] = ts
    else:
        st.setdefault("tracks", {})[track] = ts
    ws.save_state(st)


def overview(ws: Workspace) -> List[Dict[str, Any]]:
    out = []
    for t in ORDER:
        c = course_mod.load(t)
        ts = _tstate(ws, t)
        out.append({"track": t, "name": NAMES[t], "units": len(c["units"]), "weeks": c["total_weeks"],
                    "done": len(ts["done"]), "current": ts["unit"]})
    return out


def _stage_info(c: Dict[str, Any], i: int) -> Dict[str, str]:
    s = c["stages"][i]
    return {"name": s.get("title") or s.get("name", ""), "goal": s.get("goal", "")}


def course_map(ws: Workspace, track: str, start: dt.date) -> Dict[str, Any]:
    _check(track)
    c = course_mod.load(track)
    ts = _tstate(ws, track)
    done = set(ts["done"])
    wk = course_mod.expected_week(start, dt.date.fromtimestamp(ws.now()))
    stages = []
    for i in sorted({u["stage"] for u in c["units"]}):
        units = []
        for u in c["units"]:
            if u["stage"] != i:
                continue
            a, b = course_mod.week_range(u)
            status = "done" if u["n"] in done else ("current" if u["n"] == ts["unit"] else "upcoming")
            units.append({"n": u["n"], "title": u["title"], "stage": i, "weeks": [a, b], "lang": u.get("lang", track),
                          "has_gate": bool(u.get("gate")), "status": status})
        stages.append({"stage": i, **_stage_info(c, i), "weeks": [min(x["weeks"][0] for x in units), max(x["weeks"][1] for x in units)],
                       "units": units, "done": sum(1 for x in units if x["status"] == "done")})
    return {"track": track, "name": NAMES[track], "stages": stages, "current": ts["unit"], "week": wk,
            "total_weeks": c["total_weeks"], "done": len(done), "total": len(c["units"]), "advice": advice(ws, track, start)}


def unit_detail(ws: Workspace, bank: Dict[str, dict], track: str, n: int) -> Dict[str, Any]:
    _check(track)
    c = course_mod.load(track)
    u = course_mod.get_unit(c, n)
    if not u:
        raise ValueError(f"單元只有 1–{len(c['units'])}")
    ts = _tstate(ws, track)
    ev = ws.events()
    lang = u.get("lang", track)
    drills = [{"id": d, "title": bank_mod.resolve(bank, d)["title"], "done": course_mod.passed_in_lang(ev, d, lang)} for d in u.get("drills", [])]
    keys = list(u.get("resources") or [])
    keys += [r["src"] for r in u.get("readings", []) if r.get("src") not in keys]
    res = [c["resources"][r] for r in keys if r in c["resources"]]
    a, b = course_mod.week_range(u)
    avail = hdl_mod.load()
    passed = {e["problem"] for e in ev if e["kind"] == "test" and e.get("verdict") == "AC" and e.get("lang") in ("verilog", "tcl")}
    planned = [{**p, "available": p["id"] in avail, "done": p["id"] in passed} for p in u.get("planned", [])]
    return {"track": track, "n": u["n"], "title": u["title"], "stage": u["stage"], "weeks": [a, b], "goal": u["goal"], "learn": u["learn"],
            "pitfalls": u.get("pitfalls", []), "check": u.get("check", []), "build": u.get("build", []),
            "planned": planned, "drills": drills, "gate": u.get("gate"),
            "readings": u.get("readings", []), "weekly": u.get("weekly", []),
            "resources": [{"name": r[0], "url": r[1]} if isinstance(r, (list, tuple)) else r for r in res],
            "status": "done" if n in ts["done"] else ("current" if n == ts["unit"] else "upcoming")}


def mark_done(ws: Workspace, track: str, n: int) -> Dict[str, Any]:
    """標記單元完成並前進。有現成練習題的單元要先全部通過。"""
    _check(track)
    c = course_mod.load(track)
    u = course_mod.get_unit(c, n)
    if not u:
        raise ValueError(f"單元只有 1–{len(c['units'])}")
    ev = ws.events()
    todo = [d for d in u.get("drills", []) if not course_mod.passed_in_lang(ev, d, u.get("lang", track))]
    avail = hdl_mod.load()
    todo += [p["id"] for p in u.get("planned", []) if p["id"] in avail and p["id"] not in
             {e["problem"] for e in ev if e["kind"] == "test" and e.get("verdict") == "AC" and e.get("lang") == track}]
    if todo:
        raise ValueError(f"還有必做練習沒通過：{', '.join(todo)}。")
    ts = _tstate(ws, track)
    if n not in ts["done"]:
        ts["done"].append(n)
    nxt = course_mod.get_unit(c, n + 1)
    if nxt and ts["unit"] <= n:
        ts["unit"] = nxt["n"]
    _save(ws, track, ts)
    ws.log("unit_done", unit=n, track=track)
    return {"next": nxt["n"] if nxt else None}


def goto(ws: Workspace, track: str, n: int) -> Dict[str, Any]:
    _check(track)
    c = course_mod.load(track)
    u = course_mod.get_unit(c, n)
    if not u:
        raise ValueError(f"單元只有 1–{len(c['units'])}")
    ts = _tstate(ws, track)
    ts["unit"] = n
    ts["done"] = sorted(set(ts["done"]) | set(range(1, n)))
    _save(ws, track, ts)
    return {"unit": n, "title": u["title"]}


def assignment_progress(ws: Workspace, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """學生端：依本機進度算每份作業的完成狀況（伺服器端用同步的摘要算同一件事）。"""
    from .cloud import summarize
    s = summarize(ws)
    done_ids, td = set(s["done_ids"]), s["track_done"]
    out = []
    for a in assignments:
        units_left = [u for u in a.get("units", []) if u not in td.get(a.get("track"), [])]
        probs_left = [q for q in a.get("problems", []) if q not in done_ids]
        out.append({**a, "units_left": units_left, "problems_left": probs_left, "done": not units_left and not probs_left})
    return out


def advice(ws: Workspace, track: str, start: dt.date) -> List[Dict[str, Any]]:
    """依實際做題結果給學習路徑建議：可直接完成的單元、卡關要回頭複習的單元、落後課表。"""
    _check(track)
    c = course_mod.load(track)
    ts = _tstate(ws, track)
    ev = ws.events()
    avail = hdl_mod.load()
    ac = {e["problem"] for e in ev if e["kind"] == "test" and e.get("verdict") == "AC" and e.get("lang") in ("verilog", "tcl")}
    fails: Dict[str, int] = {}
    for e in ev:
        if e["kind"] == "test" and e.get("lang") == track and e.get("verdict") != "AC" and e["problem"] not in ac:
            fails[e["problem"]] = fails.get(e["problem"], 0) + 1
    owner = {p["id"]: u for u in c["units"] for p in u.get("planned", [])}
    out: List[Dict[str, Any]] = []
    for u in c["units"]:
        ids = [p["id"] for p in u.get("planned", []) if p["id"] in avail]
        if ids and u["n"] not in ts["done"] and all(i in ac for i in ids):
            out.append({"kind": "can_finish", "unit": u["n"], "text": f"單元 {u['n']}《{u['title']}》的練習題都通過了，可以標記完成。"})
    for pid, n in sorted(fails.items(), key=lambda x: -x[1]):
        if n >= 3 and pid in owner:
            u = owner[pid]
            out.append({"kind": "review", "unit": u["n"], "text": f"{pid} 已失敗 {n} 次。回頭重讀單元 {u['n']}《{u['title']}》的閱讀與重點，再試一次。"})
    wk = course_mod.expected_week(start, dt.date.fromtimestamp(ws.now()))
    exp = course_mod.expected_unit(c, wk)
    if exp["n"] > ts["unit"] + 1:
        out.append({"kind": "behind", "unit": exp["n"], "text": f"依課表現在該在單元 {exp['n']}，你在單元 {ts['unit']}；已有把握的單元可以用『跳到這個單元』或標記完成追上。"})
    return out[:6]
