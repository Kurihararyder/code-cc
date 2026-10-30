"""每日計畫：給定今天有幾分鐘，從「重練、做到一半的題、新題、單元檢核、每週測驗、工程任務」排出順序。"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from . import bank as bank_mod
from . import calibrate, course as course_mod, eng, mock, pastexams, srs
from .store import Workspace

DAY = 86400.0
KIND_ZH = {"review": "重練", "continue": "續做", "new": "新題", "gate": "檢核", "weekly": "每週測驗", "eng": "工程", "exam": "考試", "past": "歷屆"}


def _today(ws: Workspace) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(ws.now()))


def build(ws: Workspace, minutes: int = 30) -> Dict[str, Any]:
    bank = bank_mod.load_bank(ws)
    course = course_mod.load()
    st, now, events = ws.state(), ws.now(), ws.events()
    cal = calibrate.calibrate(ws, bank)
    ef, factor = calibrate.efforts(events), cal["factor"]
    today = _today(ws)
    ac_today = {e["problem"] for e in events if e["kind"] == "test" and e["verdict"] == "AC" and time.strftime("%Y-%m-%d", time.localtime(e["ts"])) == today}
    exam = ws.exam()
    if exam:
        left = max(0, int(mock.remaining_seconds(exam, now) // 60))
        return {"minutes": minutes, "items": [{"kind": "exam", "id": None, "title": "完成進行中的考試並交卷", "est": left, "why": "考試期間其他事先放著", "done": False}],
                "later": [], "total_est": left, "done_min": 0, "factor": factor, "date": today}
    pool: List[Dict[str, Any]] = []
    later: List[Dict[str, Any]] = []

    def item(kind, pid, title, est, why, done=False):
        return {"kind": kind, "id": pid, "title": title, "est": est, "why": why, "done": done}

    for pid, p in srs.due_list(st, now):                                   # 1. 到期重練（越久越優先）
        pool.append(item("review", pid, bank_mod.resolve(bank, pid)["title"], calibrate.est_minutes(bank, pid, ef, factor, review=True),
                         f"無提示重寫（第 {p['review_stage'] + 1}/3 次）", pid in ac_today))
    u = course_mod.current_unit(ws, course)
    if u:
        _, todo = course_mod.unit_progress(ws, u)
        started = [pid for pid in todo if st["problems"].get(pid, {}).get("attempts")]
        for pid in started:                                                # 2. 做到一半的題
            spent = ef.get(pid, {}).get("active_min", 0)
            pool.append(item("continue", pid, bank_mod.resolve(bank, pid)["title"], calibrate.est_minutes(bank, pid, ef, factor, spent=min(spent, 15)),
                             "你已經試過了，先把它做完", pid in ac_today))
        pp = pastexams.unit_pool(ws, bank, u["n"])                         # 3. 這個單元的歷屆題（有測資、還沒解過的，由易到難）
        if pp and not todo:
            nxt = [p for p in pp["items"] if p["has_tests"] and not p["solved"]][:2]
            for p in nxt:
                pool.append(item("past", p["id"], p["title"], calibrate.est_minutes(bank, p["id"], ef, factor), f"歷屆題（全體答對率 {p['accuracy']:g}%）", p["id"] in ac_today))
        if u["gate"] and not todo:                                         # 4. 檢核
            mins = u["gate"].get("minutes", 90 if u["gate"].get("kind") == "short" else 180)
            (pool if minutes >= mins else later).append(item("gate", None, f"單元 {u['n']} 檢核", mins, "必做練習都完成了" + ("" if minutes >= mins else "；需要連續 %d 分鐘，建議另外安排" % mins)))
        for pid in [x for x in todo if x not in started]:                  # 3b. 新題
            pool.append(item("new", pid, bank_mod.resolve(bank, pid)["title"], calibrate.est_minutes(bank, pid, ef, factor), f"單元 {u['n']} 必做", pid in ac_today))
    solved = srs.counts(st)["solved"]                                      # 5. 每週無 AI 測驗
    wk = [e for e in events if e["kind"] == "exam_start" and e.get("exam_kind") == "weekly"]
    if solved >= mock.WEEKLY_COUNT and (not wk or now - wk[-1]["ts"] > 7 * DAY):
        (pool if minutes >= 60 else later).append(item("weekly", None, "每週無 AI 重寫測驗", 60, "這週還沒做；連續 60 分鐘" + ("" if minutes >= 60 else "，建議週末安排")))
    stage = int(ws.config()["stage"])                                      # 6. 工程任務（每週一次）
    t = eng.next_task(ws, stage)
    last_eng = [e for e in events if e["kind"] in ("eng_start", "eng_verify")]
    if t and (not last_eng or now - last_eng[-1]["ts"] > 6 * DAY):
        pool.append(item("eng", t["n"], t["title"], 30, "工程能力線：每週一次，累積作品集"))

    listed = {i["id"] for i in pool if i["id"]}
    for pid in sorted(ac_today - listed):                                  # 今天已經完成、不再出現在清單裡的題
        sp = st["problems"].get(pid, {})
        fresh = sp.get("first_pass") is not None and time.strftime("%Y-%m-%d", time.localtime(sp["first_pass"])) == today
        pool.append(item("new" if fresh else "review", pid, bank_mod.resolve(bank, pid)["title"], calibrate.est_minutes(bank, pid, ef, factor, review=not fresh),
                         "今天完成", True))
    chosen, used = [], 0
    for it in pool:
        if it["done"]:
            chosen.append(it)                                              # 今天已完成的也列出來，讓你看到進度
            continue
        if used + it["est"] <= minutes:
            chosen.append(it)
            used += it["est"]
        elif not any(not c["done"] for c in chosen):                       # 一件都放不下：至少給第一件，標示會超時
            it = dict(it, over=True, why=it["why"] + "（預估超過今天的時間，可以只做一半，明天接著做）")
            chosen.append(it)
            used += it["est"]
        else:
            later.append(dict(it, why=it["why"] + "（今天的時間放不下）"))
    done_min = sum(i["est"] for i in chosen if i["done"])
    return {"minutes": minutes, "items": chosen, "later": later, "total_est": used, "done_min": done_min, "factor": factor, "date": today,
            "calibrated": cal["enough"]}
