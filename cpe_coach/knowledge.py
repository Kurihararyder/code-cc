"""知識追蹤：用貝氏知識追蹤（BKT）推測每個知識點你「會」的機率，加上掌握層級與下一題推薦。

誠實的限制：BKT 的四個參數（初始、學會、失誤、猜對）是常見的預設值，沒有用你的資料訓練；單人資料太少，訓練也不可靠。
推薦用的「題目難度」是我估的星等（或官方答對率換算），不是用大量作答資料校準的。所以這些數字是「合理的排序依據」，不是精準的機率。
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from . import bank as bank_mod
from . import concepts, memory
from .pastexams import has_tests

P_INIT, P_LEARN, P_SLIP, P_GUESS = 0.25, 0.12, 0.10, 0.20
CLUSTER = 30 * 60.0                       # 30 分鐘內對同一題的連續提交算一次「作答」


def _bkt_step(p: float, correct: bool) -> float:
    if correct:
        pc = p * (1 - P_SLIP) + (1 - p) * P_GUESS
        post = p * (1 - P_SLIP) / pc
    else:
        pn = p * P_SLIP + (1 - p) * (1 - P_GUESS)
        post = p * P_SLIP / pn
    return post + (1 - post) * P_LEARN


def attempts(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """把連續提交收成「一次作答」：{problem, ts, correct（沒失敗過、沒用提示就過）, solved, clean}。"""
    out: List[Dict[str, Any]] = []
    cur: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        if ev.get("kind") != "test" or not ev.get("problem") or ev.get("verdict") in (None, "SETUP"):
            continue
        pid, ts, ok = ev["problem"], float(ev["ts"]), ev["verdict"] == "AC"
        a = cur.get(pid)
        if a is None or ts - a["last"] > CLUSTER:
            a = {"problem": pid, "ts": ts, "last": ts, "fails": 0, "solved": False, "clean": True}
            cur[pid] = a
            out.append(a)
        a["last"] = ts
        if ok:
            a["solved"] = True
            a["clean"] = a["clean"] and bool(ev.get("clean", True))
        else:
            a["fails"] += 1
    for a in out:
        a["correct"] = a["solved"] and a["fails"] == 0 and a["clean"]
    return out


def bkt(events: List[Dict[str, Any]], bank: Dict[str, dict]) -> Dict[str, float]:
    ps: Dict[str, float] = {}
    for a in attempts(events):
        p = bank.get(a["problem"])
        if p is None:
            continue
        for c in concepts.of_problem(p):
            ps[c] = _bkt_step(ps.get(c, P_INIT), a["correct"])
    return ps


LEVELS = ["未接觸", "接觸", "理解", "應用", "變化"]


def levels(events: List[Dict[str, Any]], bank: Dict[str, dict], rp: memory.Replay, now: float, k: float = 1.0) -> Dict[str, Dict[str, Any]]:
    """每個知識點的掌握層級：
    接觸＝試過；理解＝解出過；應用＝至少 2 道不同的題無提示解出；變化＝至少 3 道無提示解出，而且隔了一天以上的複習還答對過。"""
    tried: Dict[str, set] = {}
    solved: Dict[str, set] = {}
    clean: Dict[str, set] = {}
    for a in attempts(events):
        p = bank.get(a["problem"])
        if p is None:
            continue
        for c in concepts.of_problem(p):
            tried.setdefault(c, set()).add(a["problem"])
            if a["solved"]:
                solved.setdefault(c, set()).add(a["problem"])
            if a["solved"] and a["clean"]:
                clean.setdefault(c, set()).add(a["problem"])
    out: Dict[str, Dict[str, Any]] = {}
    for cid in concepts.load():
        cc = rp.concept_cards.get(cid)
        reviewed_ok = bool(cc and any(g != memory.AGAIN and r >= 0 for _, g, r in cc.log))
        lv = 0
        if tried.get(cid):
            lv = 1
        if solved.get(cid):
            lv = 2
        if len(clean.get(cid, ())) >= 2:
            lv = 3
        if len(clean.get(cid, ())) >= 3 and reviewed_ok:
            lv = 4
        ret = cc.r_at(now, k) if cc else None
        out[cid] = {"level": lv, "label": LEVELS[lv], "retention": None if ret is None else round(ret, 3),
                    "needs_review": ret is not None and ret < 0.8, "solved": len(solved.get(cid, ())), "clean": len(clean.get(cid, ()))}
    return out


def mastery(ws, bank: Dict[str, dict]) -> Dict[str, Dict[str, Any]]:
    events = ws.events()
    rp, ft = memory.build(ws, bank)
    now = ws.now()
    ps = bkt(events, bank)
    lv = levels(events, bank, rp, now, ft.k)
    out = {}
    for cid, c in concepts.load().items():
        p = ps.get(cid, P_INIT)
        ret = lv[cid]["retention"]
        eff = p * (0.7 + 0.3 * ret) if ret is not None else p
        out[cid] = {"name": c["name"], "unit": c["unit"], "p_know": round(p, 3), "effective": round(eff, 3), "touched": cid in ps, **lv[cid]}
    return out


def unlocked(cid: str, m: Dict[str, Dict[str, Any]], current_unit: int = 0, threshold: float = 0.45) -> bool:
    """先修都掌握了（或課程已經走過那個單元）才算解鎖。"""
    cs = concepts.load()
    for pre in cs[cid]["pre"]:
        if cs[pre]["unit"] <= current_unit - 1:
            continue
        if not m.get(pre, {}).get("touched") or m[pre]["effective"] < threshold:
            return False
    return True


def _logit(p: float) -> float:
    p = min(max(p, 0.02), 0.98)
    return math.log(p / (1 - p))


def predict_success(m: Dict[str, Dict[str, Any]], problem: Dict[str, Any], b_calibrated: Optional[float] = None) -> float:
    """這題你一次通過的推測機率：知識點掌握度（log-odds 平均）減題目難度。難度星等 1→−0.8、2→0、3→+0.8、4→+1.6。"""
    cs = concepts.of_problem(problem)
    theta = sum(_logit(m[c]["effective"]) for c in cs) / len(cs)
    b = b_calibrated if b_calibrated is not None else (float(problem.get("difficulty", 2)) - 2) * 0.8      # 有校準過的難度（cpe calibrate-merge）就用它
    return 1 / (1 + math.exp(-(theta - b + 0.6)))


def recommend(ws, bank: Dict[str, dict], n: int = 5, target: float = 0.7, current_unit: Optional[int] = None) -> List[Dict[str, Any]]:
    """下一題：挑「推測成功率最接近 70%」的未解題（太簡單學不到、太難會挫折），先修要解鎖，而且已經有測資。"""
    from . import aggregate
    calib = aggregate.load_calibration(ws)["problems"]
    m = mastery(ws, bank)
    st = ws.state()["problems"]
    if current_unit is None:
        current_unit = int(ws.state().get("course", {}).get("unit", 1))
    rows = []
    for pid, p in bank.items():
        if st.get(pid, {}).get("first_pass") or not (bank_mod.is_drill(pid) or has_tests(ws, pid)):
            continue
        cs = concepts.of_problem(p)
        if not all(unlocked(c, m, current_unit) for c in cs):
            continue
        ps = predict_success(m, p, calib.get(pid))
        rows.append({"id": pid, "title": p.get("title", pid), "p_success": round(ps, 2), "concepts": [concepts.load()[c]["name"] for c in cs],
                     "difficulty": p.get("difficulty"), "gap": abs(ps - target)})
    rows.sort(key=lambda r: (r["gap"], r["difficulty"] or 0, r["id"]))
    for r in rows:
        r.pop("gap")
        r["why"] = f"推測一次通過的機率約 {round(100 * r['p_success'])}%（目標 {round(100 * target)}%）；知識點：{'、'.join(r['concepts'])}"
    return rows[:n]
