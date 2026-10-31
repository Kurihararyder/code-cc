"""目標與進度：目標倒推的計畫、完成日期預測（附信賴區間）、健康的成就、週報月報、考試時間策略、落點預測、壓力下的表現、考前清單。

誠實的限制：預測都是用你自己的紀錄粗估，資料少的時候（少於 14 天、少於 5 場模擬考）會直接說「資料不足」而不是硬給數字；
落點預測假設考試有 7 題、難度大致為 ★1×2、★2×2、★3×2、★4×1，這個難度配置是我的假設，不是官方公布的。
"""
from __future__ import annotations

import datetime as dt
import math
import random
import statistics
import time
from typing import Any, Dict, List, Optional

from . import calibrate, knowledge, memory, pastexams

DAY = 86400.0
EXAM_SLOTS = [1, 1, 2, 2, 3, 3, 4]                       # 假設的考試難度配置（★）


# ---------- 目標 ----------
def set_goal(ws, date: str, problems: int) -> Dict[str, Any]:
    try:
        d = dt.date.fromisoformat(date)
    except ValueError:
        raise ValueError("日期格式要是 YYYY-MM-DD")
    if problems < 1 or problems > 2000:
        raise ValueError("目標題數要在 1 到 2000 之間")
    if d <= dt.date.fromtimestamp(ws.now()):
        raise ValueError("目標日期要在今天之後")
    cfg = ws.config()
    cfg["goal"] = {"date": date, "problems": int(problems), "set_at": ws.now()}
    ws.save_config(cfg)
    ws.log("goal", date=date, problems=int(problems))
    return cfg["goal"]


def _solved_ts(ws) -> List[float]:
    return sorted(float(p["first_pass"]) for p in ws.state()["problems"].values() if p.get("first_pass"))


def _median_minutes(ws) -> float:
    ef = calibrate.efforts(ws.events())
    xs = [e["effort_min"] for e in ef.values()]
    return statistics.median(xs) if len(xs) >= 3 else 25.0


def pace(ws, window_days: int = 28) -> Dict[str, Any]:
    now = ws.now()
    ts = _solved_ts(ws)
    first = min([float(e["ts"]) for e in ws.events()[:1]] + [now])
    span = min(window_days, max(1, int((now - first) // DAY) + 1))
    daily = [0] * span
    for t in ts:
        k = int((now - t) // DAY)
        if 0 <= k < span:
            daily[k] += 1
    return {"daily": daily, "days": span, "per_week": round(sum(daily) / span * 7, 2), "enough": span >= 14}


def forecast_done(daily: List[int], remaining: int, trials: int = 1000, seed: int = 1) -> Dict[str, Any]:
    """用最近每天解題數的分布做自助法（bootstrap）模擬：還要幾天才能完成 remaining 題。回傳 10／50／90 百分位。"""
    if remaining <= 0:
        return {"p10": 0, "p50": 0, "p90": 0, "possible": True}
    if not daily or sum(daily) == 0:
        return {"p10": None, "p50": None, "p90": None, "possible": False}
    rng = random.Random(seed)
    days = []
    for _ in range(trials):
        total = d = 0
        while total < remaining and d < 1500:
            total += rng.choice(daily)
            d += 1
        days.append(d)
    days.sort()
    q = lambda p: days[min(len(days) - 1, int(p * len(days)))]      # noqa: E731
    return {"p10": q(0.10), "p50": q(0.50), "p90": q(0.90), "possible": True}


def goal_status(ws) -> Dict[str, Any]:
    cfg = ws.config()
    g = cfg.get("goal")
    if not g:
        return {"set": False}
    now = ws.now()
    solved = len(_solved_ts(ws))
    remaining = max(0, g["problems"] - solved)
    left_days = max(0, (dt.date.fromisoformat(g["date"]) - dt.date.fromtimestamp(now)).days)
    pc = pace(ws)
    need_week = round(remaining / max(left_days / 7, 1 / 7), 2) if left_days else float("inf")
    per_problem = _median_minutes(ws)
    fc = forecast_done(pc["daily"], remaining) if pc["enough"] else None
    status = "done" if remaining == 0 else "overdue" if left_days == 0 else None
    if status is None:
        if not pc["enough"]:
            status = "unknown"
        elif fc and fc["possible"] and fc["p90"] <= left_days:
            status = "ahead"
        elif fc and fc["possible"] and fc["p50"] <= left_days:
            status = "on_track"
        else:
            status = "behind"
    daily_min = None if not left_days else math.ceil(remaining * per_problem / left_days)
    msg = {"done": "目標題數已經達成。", "overdue": "目標日期到了。", "unknown": "你的紀錄還不到 14 天，沒辦法可靠地預測；先照需要的速度走。",
           "ahead": "照目前的速度，有很大把握（90%）在目標日期前完成。", "on_track": "照目前的速度，有一半的把握在目標日期前完成；再快一點會比較穩。",
           "behind": "照目前的速度趕不上：要增加每週題數、減少目標，或把日期往後延。"}[status]
    return {"set": True, "date": g["date"], "target": g["problems"], "solved": solved, "remaining": remaining, "days_left": left_days,
            "need_per_week": need_week if left_days else None, "pace_per_week": pc["per_week"], "enough_data": pc["enough"], "forecast_days": fc, "status": status,
            "daily_minutes": daily_min, "minutes_per_problem": round(per_problem, 1), "message": msg}


# ---------- 成就（看品質，不看刷題量；沒有「斷了就歸零」的連續紀錄） ----------
def achievements(ws, bank: Optional[Dict[str, dict]] = None) -> List[Dict[str, Any]]:
    ev = ws.events()
    tests = [e for e in ev if e.get("kind") == "test" and e.get("verdict") not in (None, "SETUP")]
    rp = memory.replay(ev, bank or {})
    out: List[Dict[str, Any]] = []

    def add(aid: str, name: str, desc: str, ts: Optional[float]) -> None:
        out.append({"id": aid, "name": name, "desc": desc, "unlocked": ts is not None, "ts": ts})
    clean_ac = [e for e in tests if e["verdict"] == "AC" and e.get("clean", True)]
    add("first-clean", "第一次無提示通過", "不看提示、不放棄，自己解出一題。", clean_ac[0]["ts"] if clean_ac else None)
    distinct_clean = []
    seen = set()
    for e in clean_ac:
        if e["problem"] not in seen:
            seen.add(e["problem"])
            distinct_clean.append(e["ts"])
    add("clean-10", "十題無提示", "累積 10 道不同的題目是無提示通過的。", distinct_clean[9] if len(distinct_clean) >= 10 else None)
    long_review = next((c.log[i][0] for c in rp.cards.values() for i in range(1, len(c.log)) if c.log[i][1] != memory.AGAIN and c.log[i][0] - c.log[i - 1][0] >= 7 * DAY), None)
    add("remembered-week", "一週後還記得", "隔了 7 天以上再做一次，仍然通過。", long_review)
    fixed = None
    err_probs = {}
    for e in ev:
        if e.get("kind") == "err":
            err_probs.setdefault(e["problem"], e["ts"])
        elif e.get("kind") == "test" and e.get("verdict") == "AC" and e.get("problem") in err_probs and fixed is None:
            fixed = e["ts"]
    add("from-error", "從錯誤中學會", "一題先失敗，後來自己修好並通過。", fixed)
    notes = [e for e in ev if e.get("kind") == "note"]
    kinds = {e.get("note_kind") for e in notes}
    add("reflect", "寫下想法", "寫過思路、回想或反思筆記。", notes[0]["ts"] if notes else None)
    add("explain", "用自己的話解釋", "做過一次自我解釋。", next((e["ts"] for e in notes if e.get("note_kind") == "explain"), None))
    add("recall", "先回想再看答案", "做過回想練習。", next((e["ts"] for e in notes if e.get("note_kind") == "recall"), None))
    add("varied-notes", "三種筆記", "思路、回想、反思都寫過。", max(e["ts"] for e in notes) if len(kinds & {"think", "recall", "reflect"}) >= 3 else None)
    quizzes = [e for e in ev if e.get("kind") == "quiz"]
    add("diagnosed", "做過適性診斷", "完成一次適性診斷。", quizzes[0]["ts"] if quizzes else None)
    days = sorted({time.strftime("%Y-%m-%d", time.localtime(float(e["ts"]))) for e in tests})
    week_days = 0
    ts_wk = None
    for i, d in enumerate(days):
        d0 = dt.date.fromisoformat(d)
        n = sum(1 for x in days[i:] if (dt.date.fromisoformat(x) - d0).days < 7)
        if n >= 4:
            week_days, ts_wk = n, float(dt.datetime.combine(d0 + dt.timedelta(days=6), dt.time()).timestamp())
            break
    add("steady-week", "穩定的一週", "任意連續 7 天裡有 4 天以上有練習（不用每天，休息也是學習的一部分）。", ts_wk if week_days else None)
    touched = {c for c in rp.concept_cards}
    add("breadth-8", "八個知識點", "解出過 8 個不同知識點的題目。", max((c.last for c in rp.concept_cards.values()), default=None) if len(touched) >= 8 else None)
    return out


# ---------- 週報／月報 ----------
def report(ws, days: int = 7, bank: Optional[Dict[str, dict]] = None) -> Dict[str, Any]:
    from . import errbook, habits
    now = ws.now()
    since = now - days * DAY
    ev = [e for e in ws.events() if float(e["ts"]) >= since]
    tests = [e for e in ev if e.get("kind") == "test" and e.get("verdict") not in (None, "SETUP")]
    active_days = len({time.strftime("%Y-%m-%d", time.localtime(float(e["ts"]))) for e in ev})
    attempts = [a for a in knowledge.attempts(ev)]
    minutes = round(sum(s["end"] - s["start"] + 120 for s in habits.sessions(ev)) / 60)          # 每段至少算 2 分鐘
    solved_new = sum(1 for p in ws.state()["problems"].values() if p.get("first_pass") and float(p["first_pass"]) >= since)
    rp = memory.replay(ws.events(), bank or {})
    reviews = [(ts, g) for c in rp.cards.values() for ts, g, r in c.log if r >= 0 and ts >= since]
    err = errbook.summary(ev, bank)
    return {"days": days, "active_days": active_days, "minutes": minutes, "submissions": len(tests), "attempts": len(attempts), "first_try_correct": sum(1 for a in attempts if a["correct"]),
            "new_solved": solved_new, "reviews": len(reviews), "reviews_passed": sum(1 for _, g in reviews if g != memory.AGAIN), "hints": sum(1 for e in ev if e.get("kind") == "hint"),
            "top_errors": [{"cause": c["cause"], "count": c["count"]} for c in err["causes"][:3]], "notes": sum(1 for e in ev if e.get("kind") == "note"),
            "time_of_day": habits.by_time_of_day(ev)["note"], "range": [time.strftime("%Y-%m-%d", time.localtime(since)), time.strftime("%Y-%m-%d", time.localtime(now))]}


# ---------- 考試：時間策略、落點、壓力 ----------
def _mocks(ws) -> List[Dict[str, Any]]:
    return [x for x in ws.state()["exams"] if x.get("total") == 7 or x.get("kind") in ("mock", "past")]


def time_strategy(ws) -> Dict[str, Any]:
    ex = _mocks(ws)
    if len(ex) < 2:
        return {"enough": False, "advice": ["模擬考還不到 2 場，沒辦法從你的歷史分析；先做幾場。通用建議：先把全部題目讀一遍（約 10 分鐘），先做最有把握的，卡 25 分鐘沒進展就換題。"], "need": 2 - len(ex)}
    solved_min = [r["ac_min"] for e in ex for r in e["detail"].values() if r["ac_min"] is not None]
    unsolved = [r for e in ex for r in e["detail"].values() if r["ac_min"] is None]
    wrong_unsolved = sum(r["wrong"] for r in unsolved)
    wrong_solved = sum(r["wrong"] for e in ex for r in e["detail"].values() if r["ac_min"] is not None)
    med = statistics.median(solved_min) if solved_min else None
    advice = []
    if med is not None:
        cap = int(max(15, min(60, med * 1.8)))
        advice.append(f"你解出的題目中位數花 {int(med)} 分鐘；建議一題卡超過約 {cap} 分鐘沒進展就換題（比中位數多 80% 通常代表走錯方向）。")
    if unsolved:
        advice.append(f"沒解出的題平均錯了 {wrong_unsolved / len(unsolved):.1f} 次；在這些題上的重複嘗試（每次罰 20 分鐘）通常不划算，錯兩次還沒頭緒就先放。")
    if wrong_solved:
        advice.append(f"解出的題平均罰時來自 {wrong_solved / max(len(solved_min), 1):.1f} 次錯誤；提交前先用範例和一個自己造的邊界測資檢查一次，可以省下罰時。")
    late = [m for m in solved_min if m > 150]
    if solved_min and len(late) / len(solved_min) > 0.3:
        advice.append("超過三成的通過發生在最後 30 分鐘：前面太慢或太晚才開始做最難的題；先做簡單題、守住分數。")
    return {"enough": True, "mocks": len(ex), "median_ac_min": med, "advice": advice}


def _poisson_binomial(ps: List[float]) -> List[float]:
    dist = [1.0]
    for p in ps:
        nxt = [0.0] * (len(dist) + 1)
        for k, v in enumerate(dist):
            nxt[k] += v * (1 - p)
            nxt[k + 1] += v * p
        dist = nxt
    return dist


PRIOR = {1: 0.85, 2: 0.6, 3: 0.35, 4: 0.15}


def score_prediction(ws, bank: Dict[str, dict]) -> Dict[str, Any]:
    """用你的解題紀錄（依難度星等的一次通過率，貝氏更新）和模擬考的壓力係數，推測真實考試答對題數的分布。"""
    ev = ws.events()
    att = knowledge.attempts(ev)
    rates: Dict[int, Dict[str, float]] = {}
    for star in (1, 2, 3, 4):
        k = n = 0
        for a in att:
            b = bank.get(a["problem"])
            if b and round(b.get("difficulty", 2)) == star:
                n += 1
                k += 1 if a["correct"] else 0
        prior_n = 4
        rates[star] = {"p": (PRIOR[star] * prior_n + k) / (prior_n + n), "n": n}
    pr = pressure(ws, bank)
    factor = pr["factor"] if pr["enough"] else 0.85
    ps = [min(0.97, rates[s]["p"] * factor) for s in EXAM_SLOTS]
    dist = _poisson_binomial(ps)
    official = pastexams.load_all(ws)["distribution"]
    top4 = round(sum(dist[4:]), 3)
    exp = round(sum(k * v for k, v in enumerate(dist)), 2)
    enough_data = sum(r["n"] for r in rates.values()) >= 20
    return {"distribution": [round(x, 3) for x in dist], "expected": exp, "p_at_least_4": top4, "p_at_least_6": round(sum(dist[6:]), 3), "pressure_factor": round(factor, 2),
            "slot_stars": EXAM_SLOTS, "per_star": {s: round(r["p"], 2) for s, r in rates.items()}, "samples": {s: r["n"] for s, r in rates.items()},
            "official_top_share_4plus": round(sum(v for k, v in official.items() if k >= 4), 1), "enough": enough_data,
            "caveat": "粗估：假設考試 7 題的難度為 ★1×2、★2×2、★3×2、★4×1（我的假設，不是官方公布），各題獨立，並用你的一次通過率與壓力係數推算；" + ("你的作答樣本還不多，數字會偏向我設定的先驗。" if not enough_data else "樣本夠多時比較有參考價值，但仍不是承諾。")}


def pressure(ws, bank: Dict[str, dict]) -> Dict[str, Any]:
    """限時模擬考的通過率，對比同一批題目平常練習時的一次通過率。factor = 考試／平常（上限 1.2、下限 0.4）。"""
    ex = _mocks(ws)
    exam_solved = exam_total = 0
    normal_ok = normal_n = 0
    first_try = {a["problem"]: a["correct"] for a in reversed(knowledge.attempts(ws.events()))}
    for e in ex:
        for pid, r in e["detail"].items():
            exam_total += 1
            exam_solved += 1 if r["ac_min"] is not None else 0
            if pid in first_try:
                normal_n += 1
                normal_ok += 1 if first_try[pid] else 0
    if exam_total < 5 or normal_n < 5:
        return {"enough": False, "factor": 0.85, "exam_rate": None, "normal_rate": None, "note": "限時模擬的題數（至少 5 題）或對照的平常紀錄還不夠，先用預設的 0.85。"}
    er, nr = exam_solved / exam_total, normal_ok / normal_n
    f = max(0.4, min(1.2, er / nr)) if nr > 0 else 0.85
    note = f"限時模擬通過率 {round(100 * er)}%，同一批題目平常一次通過率 {round(100 * nr)}%：" + ("壓力下的表現明顯較差，多練限時。" if f < 0.8 else "壓力下的表現和平常差不多。" if f < 1.05 else "限時反而更好（可能是挑的題比較簡單）。")
    return {"enough": True, "factor": round(f, 2), "exam_rate": round(er, 3), "normal_rate": round(nr, 3), "note": note}


# ---------- 考前清單 ----------
def final_checklist(ws, bank: Dict[str, dict], days_left: Optional[int] = None) -> Dict[str, Any]:
    now = ws.now()
    rp, ft = memory.build(ws, bank)
    m = knowledge.mastery(ws, bank)
    weak = sorted([(c, v) for c, v in m.items() if v["touched"]], key=lambda kv: kv[1]["effective"])[:5]
    forgetting = sorted(((pid, c.r_at(now, ft.k)) for pid, c in rp.cards.items()), key=lambda x: x[1])[:8]
    from . import errbook
    err = errbook.summary(ws.events(), bank)
    items = []
    if days_left is None or days_left <= 7:
        items.append({"id": "env", "text": "確認考試用的環境：語言版本、編輯器、輸入輸出（標準輸入）的寫法，用一題完整跑過一次。"})
    items.append({"id": "weak", "text": "最後一週優先複習最弱的知識點：" + ("、".join(v["name"] for _, v in weak[:3]) or "（還沒有足夠紀錄）")})
    if forgetting:
        items.append({"id": "forget", "text": "最容易忘的題（預測保留率最低）：" + "、".join(f"{pid}（{round(100 * r)}%）" for pid, r in forgetting[:5]) + "；各重做一次。"})
    if err["causes"]:
        items.append({"id": "errors", "text": f"你最常犯的錯是「{err['causes'][0]['cause']}」：" + (err["advice"] or "")})
    items += [{"id": "mock", "text": "考前 3–5 天做最後一場完整模擬（比照考場：限時、不看提示、英文題目）。"}, {"id": "sleep", "text": "考前一晚不要熬夜刷題；睡眠對記憶鞏固的幫助比多做幾題大。"},
              {"id": "strategy", "text": "先把全部題目讀一遍，由簡單到困難排順序；每題設停損時間，卡住就換題（用 cpe strategy 看你的建議時間）。"}]
    return {"items": items, "weak": [{"concept": c, "name": v["name"], "effective": v["effective"]} for c, v in weak], "forgetting": [{"id": p, "retention": round(r, 3)} for p, r in forgetting]}
