"""學習洞察與學習工坊的網頁端點（記憶、知識點、診斷、目標、成就、測驗、示範題、筆記、匯出）。"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from . import aggregate, behavior, coach, concepts, errbook, exchange, experiment, habits, knowledge, lab, memory, notes, planning, reminder
from . import bank as bank_mod
from .llm import detect_client
from .service import statement_for

PID = re.compile(r"^[A-Za-z0-9_\-]{1,40}$")


def _pid(p: Any) -> str:
    if not isinstance(p, str) or not PID.match(p):
        raise ValueError("題號格式不正確")
    return p


class SciMixin:
    """需要 self.ws()、self.key（由 web.App 提供）。"""

    # ---------- 洞察 ----------
    def insights(self) -> Dict[str, Any]:
        ws = self.ws()
        bank = bank_mod.load_bank(ws)
        now = ws.now()
        rp, ft = memory.build(ws, bank)
        fn = memory.make_due_fn(ws)
        m = knowledge.mastery(ws, bank)
        ev = ws.events()
        goal = planning.goal_status(ws)
        days_left = goal.get("days_left") if goal.get("set") else None
        due = memory.due_now(rp.cards, now, ft.k, due_fn=fn)
        pr = planning.pressure(ws, bank)
        cs = concepts.load()
        return {
            "mastery": [{"id": cid, **v} for cid, v in sorted(m.items(), key=lambda kv: cs[kv[0]]["unit"])],
            "recommend": knowledge.recommend(ws, bank, 5),
            "memory": {"cards": len(rp.cards), "reviews": len(rp.pairs), "k": round(ft.k, 3), "personalized": ft.enabled, "need": memory.MIN_REVIEWS_FOR_FIT,
                       "due": [{"id": d.pid, "title": bank.get(d.pid, {}).get("title", d.pid), "retention": round(d.r_now, 2), "overdue_days": round(d.overdue_days, 1)} for d in due[:12]],
                       "forecast": memory.forecast(rp.cards, now, 14, ft.k, due_fn=fn)},
            "errors": errbook.summary(ev, bank), "habits": habits.by_time_of_day(ev), "fatigue": habits.fatigue(ev, now), "behavior": behavior.summary(ev),
            "goal": goal, "achievements": planning.achievements(ws, bank), "week": planning.report(ws, 7, bank), "month": planning.report(ws, 30, bank),
            "prediction": planning.score_prediction(ws, bank), "pressure": pr, "strategy": planning.time_strategy(ws), "final": planning.final_checklist(ws, bank, days_left),
            "coach_comments": coach.comments(ws), "experiment": experiment.analyze(ws, rp.cards), "reminder": reminder.summary(ws),
            "calibrated": {k: len(v) for k, v in aggregate.load_calibration(ws).items()},
        }

    def goal_set(self, body: Dict[str, Any]) -> Dict[str, Any]:
        planning.set_goal(self.ws(), str(body.get("date", "")), int(body.get("problems", 0)))
        return planning.goal_status(self.ws())

    def exp_set(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        experiment.set_enabled(ws, bool(body.get("on")))
        rp, _ = memory.build(ws, bank_mod.load_bank(ws))
        return experiment.analyze(ws, rp.cards)

    # ---------- 筆記 ----------
    def notes_list(self, q: Dict[str, str]) -> Dict[str, Any]:
        return {"notes": notes.listing(self.ws(), q.get("kind") or None, q.get("problem") or None, 50)}

    def notes_add(self, body: Dict[str, Any]) -> Dict[str, Any]:
        problem = _pid(body["problem"]) if body.get("problem") else None
        e = notes.add(self.ws(), str(body.get("kind", "")), str(body.get("text", "")), problem)
        out: Dict[str, Any] = {"ok": True, "ts": e["ts"]}
        if body.get("kind") == "recall" and problem:
            p = bank_mod.resolve(bank_mod.load_bank(self.ws()), problem)
            if p.get("hint_insight"):
                out["compare"] = {"insight": p["hint_insight"], "check": notes.score_offline(str(body.get("text", "")), p["hint_insight"], p.get("hint_category", ""))}
        return out

    def explain(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        pid = _pid(body.get("problem"))
        p = bank_mod.resolve(bank_mod.load_bank(ws), pid)
        insight = p.get("hint_insight") or ""
        if not insight:
            raise ValueError("這題沒有內建的關鍵洞察可以對照；改用筆記就好。")
        text = str(body.get("text", ""))
        res = None
        if not body.get("offline"):
            client = detect_client(ws.config(), key=getattr(self, "key", None))
            if client is not None:
                try:
                    res = notes.score_with_ai(client, text, insight, statement_for(ws, pid))
                except Exception:                                       # AI 失敗就退回離線評分
                    res = None
        res = res or notes.score_offline(text, insight, p.get("hint_category", ""))
        notes.add(ws, "explain", text, pid, score=res["score"], mode=res["mode"])
        return res

    # ---------- 學習工坊 ----------
    def lab_index(self) -> Dict[str, Any]:
        return {"worked": [{"id": w["id"], "title": w["title"], "concept": w["concept"]} for w in lab.items("worked")],
                "bugs": [{"id": b["id"], "title": b["title"], "concept": b["concept"]} for b in lab.items("bugs")],
                "predict": [{"id": p["id"], "concept": p["concept"]} for p in lab.items("predict")],
                "compare": [{"id": c["id"], "title": c["title"]} for c in lab.items("compare")],
                "lessons": [{"concept": x["concept"], "title": x["title"], "minutes": x["minutes"]} for x in lab.items("lessons")],
                "glossary": len(lab.items("glossary")), "concepts": {cid: c["name"] for cid, c in concepts.load().items()}}

    def lab_lesson(self, q: Dict[str, str]) -> Dict[str, Any]:
        return lab.lesson(q.get("concept", ""))

    def lab_worked(self, q: Dict[str, str]) -> Dict[str, Any]:
        w = lab.by_id("worked", "id", q.get("id", ""))
        return {"id": w["id"], "title": w["title"], "problem": w["problem"], "steps": w["steps"], "faded": lab.faded(w, int(q.get("level", 1)))}

    def lab_parsons(self, q: Dict[str, str]) -> Dict[str, Any]:
        w = lab.by_id("worked", "id", q.get("id", ""))
        p = lab.parsons(w, int(q.get("seed", 0)))
        return {"id": p["id"], "problem": p["problem"], "lines": p["lines"], "title": w["title"]}

    def lab_bug(self, q: Dict[str, str]) -> Dict[str, Any]:
        b = lab.by_id("bugs", "id", q.get("id", ""))
        return {"id": b["id"], "title": b["title"], "statement": b["statement"], "code": b["buggy"], "tests": b["tests"]}

    def lab_predict(self, q: Dict[str, str]) -> Dict[str, Any]:
        p = lab.by_id("predict", "id", q.get("id", ""))
        return {"id": p["id"], "code": p["code"], "stdin": p["stdin"]}

    def lab_compare(self, q: Dict[str, str]) -> Dict[str, Any]:
        return lab.by_id("compare", "id", q.get("id", ""))

    def lab_glossary(self, q: Dict[str, str]) -> Dict[str, Any]:
        return {"items": lab.search_glossary(q.get("q", ""), 40)}

    def lab_quiz_start(self, body: Dict[str, Any]) -> Dict[str, Any]:
        lab.set_calibration(aggregate.load_calibration(self.ws())["quiz"])
        st = lab.cat_new()
        return {"state": st, "question": lab.cat_next(st)}

    def lab_quiz_answer(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        lab.set_calibration(aggregate.load_calibration(ws)["quiz"])
        st = body.get("state")
        if not isinstance(st, dict) or not isinstance(st.get("asked"), list):
            raise ValueError("診斷狀態不正確")
        st = {"asked": [{k: a[k] for k in ("id", "concept", "correct", "choice")} for a in st["asked"] if isinstance(a, dict)], "theta": 0.0, "se": 1.2, "done": False}
        for a in st["asked"]:                                           # 不信任用戶端送來的能力值：每次都從作答紀錄重算
            lab.by_id("quiz", "id", a["id"])
        st.update(lab.estimate(st["asked"]) if st["asked"] else {})
        r = lab.cat_answer(st, str(body.get("id", "")), int(body.get("choice", -1)))
        out = {"state": st, "correct": r["correct"], "answer": r["answer"], "why": r["why"], "question": None, "result": None}
        if st["done"]:
            out["result"] = lab.cat_result(st)
            ws.log("quiz", theta=st["theta"], answered=len(st["asked"]), correct=sum(1 for a in st["asked"] if a["correct"]), start_unit=out["result"]["start_unit"],
                   items=[{"id": a["id"], "correct": a["correct"]} for a in st["asked"]])
        else:
            out["question"] = lab.cat_next(st)
        return out

    def lab_quiz_practice(self, body: Dict[str, Any]) -> Dict[str, Any]:
        c = str(body.get("concept", ""))
        if c not in concepts.load():
            raise ValueError("沒有這個知識點")
        return {"questions": lab.practice(c, max(1, min(int(body.get("n", 5)), 10)))}

    def lab_grade(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return lab.grade(str(body.get("id", "")), int(body.get("choice", -1)))

    def lab_faded_check(self, body: Dict[str, Any]) -> Dict[str, Any]:
        w = lab.by_id("worked", "id", str(body.get("id", "")))
        return lab.check_faded(w, int(body.get("level", 1)), str(body.get("answer", ""))[:20000])

    def lab_parsons_check(self, body: Dict[str, Any]) -> Dict[str, Any]:
        w = lab.by_id("worked", "id", str(body.get("id", "")))
        order = body.get("order", [])
        if not isinstance(order, list):
            raise ValueError("order 要是陣列")
        return lab.check_parsons(w, int(body.get("seed", 0)), [int(x) for x in order][:200])

    def lab_bug_check(self, body: Dict[str, Any]) -> Dict[str, Any]:
        b = lab.by_id("bugs", "id", str(body.get("id", "")))
        fixed = body.get("fixed")
        return lab.check_bug(b, int(body.get("line", 0)), str(fixed)[:20000] if isinstance(fixed, str) and fixed.strip() else None)

    def lab_predict_check(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return lab.check_predict(lab.by_id("predict", "id", str(body.get("id", ""))), str(body.get("answer", ""))[:2000])

    # ---------- 匯出（下載）----------
    def export_text(self, kind: str) -> Dict[str, Any]:
        ws = self.ws()
        if kind == "anki":
            return {"body": exchange.anki_tsv(ws).encode("utf-8"), "type": "text/tab-separated-values; charset=utf-8"}
        if kind == "xapi":
            import json
            return {"body": json.dumps(exchange.xapi(ws), ensure_ascii=False, indent=1).encode("utf-8"), "type": "application/json"}
        if kind == "report":
            return {"body": coach.to_html(coach.build(ws, False)).encode("utf-8"), "type": "text/html; charset=utf-8"}
        raise ValueError("沒有這種匯出")

    def coach_import(self, body: Dict[str, Any]) -> Dict[str, Any]:
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "c.json"
            f.write_text(json.dumps({"from": body.get("from", ""), "comments": body.get("comments", [])}, ensure_ascii=False), encoding="utf-8")
            n = coach.import_comments(self.ws(), f)
        return {"imported": n, "comments": coach.comments(self.ws())}
