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
            "total_weeks": c["total_weeks"], "done": len(done), "total": len(c["units"])}


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
