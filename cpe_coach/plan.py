"""每日計畫：給定今天有幾分鐘，從「重練、做到一半的題、新題、單元檢核、每週測驗、工程任務」排出順序。"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from . import bank as bank_mod
from . import calibrate, concepts, cpeset, course as course_mod, eng, knowledge, memory, mock, pastexams, srs, weakness
from .store import Workspace

DAY = 86400.0
KIND_ZH = {"review": "重練", "continue": "續做", "new": "新題", "gate": "檢核", "weekly": "每週測驗", "eng": "工程", "exam": "考試", "past": "歷屆", "weak": "弱點"}


def _today(ws: Workspace) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(ws.now()))


def _interleave(pool: List[Dict[str, Any]], bank: Dict[str, dict]) -> List[Dict[str, Any]]:
    """交錯練習：相鄰兩題盡量不要是同一個知識點（交錯比連續練同類型，長期記憶效果通常更好）。只重排『新題／複習／弱點／歷屆』這類題目，順序的大方向（到期的複習在前）不變。"""
    movable = ("review", "weak", "continue", "new", "past")

    def cs(it: Dict[str, Any]) -> set:
        return set(concepts.of_problem(bank[it["id"]])) if it.get("id") in bank else set()
    out: List[Dict[str, Any]] = []
    rest = list(pool)
    while rest:
        prev = cs(out[-1]) if out and out[-1]["kind"] in movable else set()
        pick = 0
        if prev and rest[0]["kind"] in movable and cs(rest[0]) & prev:
            for i, it in enumerate(rest[:4]):                                  # 只往前看 4 個，避免把重要的東西推得太後面
                if it["kind"] in movable and not cs(it) & prev:
                    pick = i
                    break
        out.append(rest.pop(pick))
    return out


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
    rp, mfit = memory.build(ws, bank)                                      # 1b. 記憶排程：所有解出過的題（含一次就過的），預測保留率降到 90% 的先複習
    srs_ids = {pid for pid, _ in srs.due_list(st, now)}
    for di in [d for d in memory.due_now(rp.cards, now, mfit.k, due_fn=memory.make_due_fn(ws)) if d.pid not in srs_ids and d.pid in bank][:5]:
        pool.append(item("review", di.pid, bank_mod.resolve(bank, di.pid)["title"], calibrate.est_minutes(bank, di.pid, ef, factor, review=True),
                         f"記憶排程：預測保留率約 {round(100 * di.r_now)}%（降到 90% 以下就該複習）", di.pid in ac_today))
    u = course_mod.current_unit(ws, course)
    wk_analysis = weakness.analyze(ws, bank, course)
    weak_sugg = weakness.suggestions(ws, bank, course, wk_analysis, per_family=2 if u and u["n"] == 49 else 1, families=3 if u and u["n"] == 49 else 2)

    def weak_item(w):
        rate = "—" if w["first_try_rate"] is None else f"{round(100 * w['first_try_rate'])}%"
        return item("weak", w["id"], w["title"], calibrate.est_minutes(bank, w["id"], ef, factor),
                    f"弱點加練：{w['family_name']}（首次通過率 {rate}）", w["id"] in ac_today)

    if u:
        _, todo = course_mod.unit_progress(ws, u)
        started = [pid for pid in todo if st["problems"].get(pid, {}).get("attempts")]
        for pid in started:                                                # 2. 做到一半的題
            spent = ef.get(pid, {}).get("active_min", 0)
            pool.append(item("continue", pid, bank_mod.resolve(bank, pid)["title"], calibrate.est_minutes(bank, pid, ef, factor, spent=min(spent, 15)),
                             "你已經試過了，先把它做完", pid in ac_today))
        severe = [w for w in weak_sugg if w["level"] == "weak"]
        for w in severe[:2 if u["n"] != 49 else 6]:                        # 2b. 嚴重弱點的加練（排在新題之前）
            pool.append(weak_item(w))
        pp = pastexams.unit_pool(ws, bank, u["n"])                         # 3. 這個單元的歷屆題（有測資、還沒解過的，由易到難）
        if pp and not todo:
            nxt = [p for p in pp["items"] if p["has_tests"] and not p["solved"]][:2]
            for p in nxt:
                pool.append(item("past", p["id"], p["title"], calibrate.est_minutes(bank, p["id"], ef, factor), f"歷屆題（全體答對率 {p['accuracy']:g}%）", p["id"] in ac_today))
        cp = cpeset.unit_pool(ws, bank, u["n"])                            # 3a. 這個單元的 CPE 原題（一星／二星／歷屆題單；匯入後才有測資）
        if cp and not todo:
            for p in [p for p in cp["items"] if p["has_tests"] and not p["solved"]][:2]:
                pool.append(item("past", p["id"], p["title"], calibrate.est_minutes(bank, p["id"], ef, factor), "CPE 原題：" + cp["label"].split("（")[0], p["id"] in ac_today))
        if u["gate"] and not todo:                                         # 4. 檢核
            mins = u["gate"].get("minutes", 90 if u["gate"].get("kind") == "short" else 180)
            (pool if minutes >= mins else later).append(item("gate", None, f"單元 {u['n']} 檢核", mins, "必做練習都完成了" + ("" if minutes >= mins else "；需要連續 %d 分鐘，建議另外安排" % mins)))
        for pid in [x for x in todo if x not in started]:                  # 3b. 新題
            pool.append(item("new", pid, bank_mod.resolve(bank, pid)["title"], calibrate.est_minutes(bank, pid, ef, factor), f"單元 {u['n']} 必做", pid in ac_today))
    if u:
        shown = {i["id"] for i in pool if i["id"]}
        for w in [w for w in weak_sugg if w["level"] == "watch" and w["id"] not in shown][:1 if u["n"] != 49 else 4]:   # 輕度弱點：排在新題之後
            pool.append(weak_item(w))
    solved = srs.counts(st)["solved"]                                      # 5. 每週無 AI 測驗
    wk = [e for e in events if e["kind"] == "exam_start" and e.get("exam_kind") == "weekly"]
    if solved >= mock.WEEKLY_COUNT and (not wk or now - wk[-1]["ts"] > 7 * DAY):
        (pool if minutes >= 60 else later).append(item("weekly", None, "每週無 AI 重寫測驗", 60, "這週還沒做；連續 60 分鐘" + ("" if minutes >= 60 else "，建議週末安排")))
    stage = int(ws.config()["stage"])                                      # 6. 工程任務（每週一次）
    t = eng.next_task(ws, stage)
    last_eng = [e for e in events if e["kind"] in ("eng_start", "eng_verify")]
    if t and (not last_eng or now - last_eng[-1]["ts"] > 6 * DAY):
        pool.append(item("eng", t["n"], t["title"], 30, "工程能力線：每週一次，累積作品集"))

    if u and not any(i["kind"] in ("new", "continue") and not i["done"] for i in pool):      # 沒有必做的新題時，依掌握度推薦「成功率約 70%」的題
        for r in knowledge.recommend(ws, bank, 1, current_unit=u["n"]):
            pool.append(item("new", r["id"], r["title"], calibrate.est_minutes(bank, r["id"], ef, factor), "推薦：" + r["why"], r["id"] in ac_today))
    seen_ids, deduped = set(), []
    for it in pool:                                                        # 同一題只出現一次（以先排的為準）
        if it["id"] and it["kind"] != "eng":
            if it["id"] in seen_ids:
                continue
            seen_ids.add(it["id"])
        deduped.append(it)
    pool = _interleave(deduped, bank)
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
