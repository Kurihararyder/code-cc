"""目標與動機、考試能力、提醒、教練檔、自我實驗。"""
import contextlib
import datetime as dt
import io
import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from cpe_coach import bank as bank_mod
from cpe_coach import cli, coach, experiment, memory, planning, reminder
from cpe_coach.store import Workspace, new_problem_state

DAY = 86400.0


class Clock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t


def noon(y, m, d):
    return time.mktime((y, m, d, 12, 0, 0, 0, 0, -1))


def make_ws(start=None):
    tmp = tempfile.TemporaryDirectory()
    clock = Clock(start or noon(2026, 11, 2))
    return tmp, Workspace.create(Path(tmp.name), "2026-11-01", clock), clock


def solve(ws, clock, pid, clean=True):
    ws.log("test", problem=pid, verdict="AC", lang="py", clean=clean)
    st = ws.state()
    p = st["problems"].setdefault(pid, new_problem_state())
    p["first_pass"] = clock.t
    p["attempts"] += 1
    ws.save_state(st)


class GoalTests(unittest.TestCase):
    def test_set_goal_validates(self):
        tmp, ws, clock = make_ws()
        with tmp:
            for date, n in (("not-a-date", 10), ("2026-11-01", 10), ("2027-01-01", 0), ("2027-01-01", 5000)):
                with self.assertRaises(ValueError):
                    planning.set_goal(ws, date, n)
            g = planning.set_goal(ws, "2027-02-01", 30)
            self.assertEqual(ws.config()["goal"]["problems"], 30)
            self.assertEqual(g["date"], "2027-02-01")

    def test_status_without_goal_and_with_little_data(self):
        tmp, ws, clock = make_ws()
        with tmp:
            self.assertEqual(planning.goal_status(ws), {"set": False})
            planning.set_goal(ws, "2027-02-01", 30)
            s = planning.goal_status(ws)
            self.assertEqual((s["status"], s["remaining"], s["enough_data"]), ("unknown", 30, False))
            self.assertIn("14 天", s["message"])
            self.assertGreater(s["daily_minutes"], 0)

    def test_ahead_and_behind_depend_on_pace(self):
        for per_day, want in ((3, {"ahead", "on_track"}), (0.2, {"behind"})):
            tmp, ws, clock = make_ws()
            with tmp:
                clock.t -= 30 * DAY
                n = 0
                for d in range(30):
                    clock.t += DAY
                    for _ in range(int(per_day) if per_day >= 1 else (1 if d % 5 == 0 else 0)):
                        solve(ws, clock, f"p{n}")
                        n += 1
                planning.set_goal(ws, (dt.date.fromtimestamp(clock.t) + dt.timedelta(days=40)).isoformat(), n + 60)
                s = planning.goal_status(ws)
                self.assertIn(s["status"], want, s)
                self.assertTrue(s["enough_data"])

    def test_forecast_is_deterministic_and_handles_edges(self):
        a = planning.forecast_done([2, 0, 1, 3, 0, 1, 2], 20)
        self.assertEqual(a, planning.forecast_done([2, 0, 1, 3, 0, 1, 2], 20))
        self.assertLessEqual(a["p10"], a["p50"])
        self.assertLessEqual(a["p50"], a["p90"])
        self.assertTrue(10 <= a["p50"] <= 20)
        self.assertEqual(planning.forecast_done([1, 1], 0)["p50"], 0)
        z = planning.forecast_done([0, 0, 0], 5)
        self.assertFalse(z["possible"])
        self.assertIsNone(z["p50"])
        self.assertFalse(planning.forecast_done([], 5)["possible"])
        fast = planning.forecast_done([5] * 14, 10)
        self.assertLessEqual(fast["p90"], 2)


class AchievementTests(unittest.TestCase):
    def test_unlock_by_quality(self):
        tmp, ws, clock = make_ws()
        with tmp:
            bank = bank_mod.load_bank(ws)
            ach = {a["id"]: a for a in planning.achievements(ws, bank)}
            self.assertFalse(any(a["unlocked"] for a in ach.values()))
            solve(ws, clock, "d001")
            ws.log("test", problem="d002", verdict="WA", lang="py")
            ws.log("err", problem="d002", cause="越界", verdict="WA")
            clock.t += 60
            solve(ws, clock, "d002", clean=False)
            clock.t += 8 * DAY
            ws.log("test", problem="d001", verdict="AC", lang="py", clean=True)
            ws.log("note", note_kind="recall", problem="d001", text="x")
            ws.log("quiz", theta=0.1)
            ach = {a["id"]: a for a in planning.achievements(ws, bank)}
            for k in ("first-clean", "remembered-week", "from-error", "reflect", "recall", "diagnosed"):
                self.assertTrue(ach[k]["unlocked"], k)
            self.assertFalse(ach["clean-10"]["unlocked"])
            self.assertFalse(ach["varied-notes"]["unlocked"])

    def test_steady_week_does_not_require_every_day(self):
        tmp, ws, clock = make_ws()
        with tmp:
            for d in (0, 1, 3, 5):
                clock.t = noon(2026, 11, 2) + d * DAY
                ws.log("test", problem="d001", verdict="WA", lang="py")
            a = {x["id"]: x for x in planning.achievements(ws)}
            self.assertTrue(a["steady-week"]["unlocked"])


class ReportTests(unittest.TestCase):
    def test_weekly_report_counts(self):
        tmp, ws, clock = make_ws()
        with tmp:
            solve(ws, clock, "d001")
            ws.log("hint", problem="d002", level=1)
            ws.log("err", problem="d002", cause="越界", verdict="RE")
            ws.log("note", note_kind="think", text="x")
            clock.t += 3 * DAY
            r = planning.report(ws, 7, bank_mod.load_bank(ws))
            self.assertEqual((r["new_solved"], r["hints"], r["notes"], r["active_days"]), (1, 1, 1, 1))
            self.assertEqual(r["top_errors"][0]["cause"], "越界")
            old = planning.report(ws, 1, bank_mod.load_bank(ws))
            self.assertEqual((old["new_solved"], old["active_days"]), (0, 0))


def exam(solved_minutes, wrongs=None):
    """solved_minutes: {pid: ac_min 或 None}；回傳模擬考的 summary（和 state['exams'] 的格式一樣）。"""
    detail = {pid: {"ac_min": m, "wrong": (wrongs or {}).get(pid, 0)} for pid, m in solved_minutes.items()}
    return {"kind": "mock", "solved": sum(1 for m in solved_minutes.values() if m is not None), "total": len(detail), "penalty": 0, "problems": list(detail), "detail": detail}


class ExamAbilityTests(unittest.TestCase):
    def test_time_strategy_needs_two_mocks_then_gives_specific_advice(self):
        tmp, ws, clock = make_ws()
        with tmp:
            self.assertFalse(planning.time_strategy(ws)["enough"])
            st = ws.state()
            st["exams"] = [exam({"a": 30, "b": 50, "c": None, "d": 160}, {"c": 3}), exam({"a": 25, "b": 160, "c": None, "d": None}, {"c": 2, "a": 1})]
            ws.save_state(st)
            t = planning.time_strategy(ws)
            self.assertTrue(t["enough"])
            text = "\n".join(t["advice"])
            self.assertIn("中位數", text)
            self.assertIn("罰時", text)
            self.assertIn("最後 30 分鐘", text)

    def test_pressure_compares_exam_with_practice(self):
        tmp, ws, clock = make_ws()
        with tmp:
            self.assertFalse(planning.pressure(ws, {})["enough"])
            for i in range(8):
                ws.log("test", problem=f"p{i}", verdict="AC", lang="py", clean=True)
                clock.t += 3600
            st = ws.state()
            st["exams"] = [exam({f"p{i}": (30 if i < 3 else None) for i in range(8)})]
            ws.save_state(st)
            p = planning.pressure(ws, {})
            self.assertTrue(p["enough"])
            self.assertAlmostEqual(p["exam_rate"], 3 / 8, places=2)
            self.assertAlmostEqual(p["normal_rate"], 1.0, places=2)
            self.assertAlmostEqual(p["factor"], 0.4, delta=0.01)                       # 下限
            self.assertIn("明顯較差", p["note"])

    def test_poisson_binomial(self):
        d = planning._poisson_binomial([0.5, 0.5])
        self.assertEqual([round(x, 6) for x in d], [0.25, 0.5, 0.25])
        self.assertAlmostEqual(sum(planning._poisson_binomial([0.9, 0.2, 0.6, 0.3, 0.7, 0.1, 0.5])), 1.0, places=9)
        self.assertEqual(planning._poisson_binomial([1.0, 1.0]), [0.0, 0.0, 1.0])

    def test_score_prediction_improves_with_better_records_and_is_honest(self):
        tmp, ws, clock = make_ws()
        with tmp:
            bank = bank_mod.load_bank(ws)
            base = planning.score_prediction(ws, bank)
            self.assertAlmostEqual(sum(base["distribution"]), 1.0, delta=0.01)
            self.assertFalse(base["enough"])
            self.assertIn("樣本還不多", base["caveat"])
            self.assertEqual(base["pressure_factor"], 0.85)
            for pid, p in sorted(bank.items())[:60]:
                if round(p.get("difficulty", 2)) in (3, 4) and not pid.startswith("uva"):
                    solve(ws, clock, pid)
                    clock.t += 3600
            better = planning.score_prediction(ws, bank)
            self.assertGreater(better["expected"], base["expected"])
            self.assertGreater(better["per_star"][3], base["per_star"][3])
            self.assertLess(max(better["per_star"].values()), 1.0)

    def test_final_checklist(self):
        tmp, ws, clock = make_ws()
        with tmp:
            for pid in ("d001", "d002", "d003"):
                solve(ws, clock, pid)
            clock.t += 30 * DAY
            ws.log("err", problem="d001", cause="差一（邊界）", verdict="WA")
            c = planning.final_checklist(ws, bank_mod.load_bank(ws), days_left=3)
            ids = [i["id"] for i in c["items"]]
            self.assertTrue({"env", "weak", "forget", "errors", "mock", "sleep", "strategy"} <= set(ids))
            self.assertTrue(c["forgetting"])
            far = planning.final_checklist(ws, bank_mod.load_bank(ws), days_left=60)
            self.assertNotIn("env", [i["id"] for i in far["items"]])


class ExperimentTests(unittest.TestCase):
    def test_arm_is_stable_balanced_and_off_by_default(self):
        tmp, ws, clock = make_ws()
        with tmp:
            self.assertFalse(experiment.enabled(ws))
            self.assertEqual({experiment.arm(ws, f"p{i}") for i in range(20)}, {"fsrs"})
            experiment.set_enabled(ws, True)
            arms = [experiment.arm(ws, f"p{i}") for i in range(200)]
            self.assertEqual(arms, [experiment.arm(ws, f"p{i}") for i in range(200)])
            self.assertTrue(70 < arms.count("fixed") < 130)
            experiment.set_enabled(ws, False)
            self.assertEqual(experiment.arm(ws, "p1"), "fsrs")

    def test_fixed_ladder_grows_and_resets_on_lapse(self):
        log = [(0.0, 3, -1.0)]
        self.assertEqual(experiment.fixed_due(log), 1 * DAY)
        log.append((DAY, 3, 0.9))
        self.assertEqual(experiment.fixed_due(log), DAY + 3 * DAY)
        log.append((4 * DAY, 3, 0.9))
        self.assertEqual(experiment.fixed_due(log), 4 * DAY + 7 * DAY)
        log.append((11 * DAY, 1, 0.5))
        self.assertEqual(experiment.fixed_due(log), 11 * DAY + 1 * DAY)
        long = [(0.0, 3, -1.0)] + [(float(i), 3, 0.9) for i in range(1, 12)]
        self.assertEqual(experiment.fixed_due(long), 11.0 + 60 * DAY)

    def test_wilson_interval(self):
        lo, hi = experiment.wilson(8, 10)
        self.assertTrue(0.4 < lo < 0.8 < hi < 1.0)
        self.assertEqual(experiment.wilson(0, 0), (0.0, 1.0))
        lo2, hi2 = experiment.wilson(80, 100)
        self.assertLess(hi2 - lo2, hi - lo)

    def test_scheduler_uses_the_fixed_ladder_only_for_the_fixed_arm(self):
        tmp, ws, clock = make_ws()
        with tmp:
            experiment.set_enabled(ws, True)
            cards = {}
            for i in range(40):
                c = memory.Card()
                c.review(clock.t, memory.EASY)
                cards[f"p{i}"] = c
            fn = memory.make_due_fn(ws)
            for pid, c in cards.items():
                want = c.last + DAY if experiment.arm(ws, pid) == "fixed" else c.due(1.0)
                self.assertAlmostEqual(fn(pid, c, 1.0), want, places=3)
            experiment.set_enabled(ws, False)
            self.assertIsNone(memory.make_due_fn(ws))

    def test_analysis_says_not_enough_data(self):
        tmp, ws, clock = make_ws()
        with tmp:
            experiment.set_enabled(ws, True)
            r = experiment.analyze(ws, {})
            self.assertIn("資料不夠", r["conclusion"])
            self.assertEqual(r["arms"]["fsrs"]["reviews"], 0)

    def test_analysis_with_plenty_of_data(self):
        tmp, ws, clock = make_ws()
        with tmp:
            experiment.set_enabled(ws, True)
            cards = {}
            for i in range(120):
                c = memory.Card()
                c.review(0.0, memory.GOOD)
                gap = 12 if experiment.arm(ws, f"p{i}") == "fsrs" else 3
                for j in range(1, 4):
                    c.review(j * gap * DAY, memory.GOOD if (i + j) % 7 else memory.AGAIN)
                cards[f"p{i}"] = c
            r = experiment.analyze(ws, cards)
            self.assertGreater(r["arms"]["fsrs"]["median_gap_days"], r["arms"]["fixed"]["median_gap_days"])
            self.assertNotIn("資料不夠", r["conclusion"])


class ReminderTests(unittest.TestCase):
    def test_check_notifies_once_then_waits(self):
        tmp, ws, clock = make_ws(noon(2026, 11, 2))
        with tmp:
            solve(ws, clock, "d001")
            clock.t += 20 * DAY
            sent = []
            fake = lambda t, m: (sent.append((t, m)) or (True, "fake"))        # noqa: E731
            r = reminder.check(ws, fake)
            self.assertTrue(r["notified"])
            self.assertIn("d001", sent[0][1])
            again = reminder.check(ws, fake)
            self.assertFalse(again["notified"])
            self.assertEqual(again["reason"], "剛提醒過")
            clock.t += 9 * 3600
            self.assertTrue(reminder.check(ws, fake)["notified"])
            self.assertEqual(len(sent), 2)

    def test_nothing_due_quiet_hours_and_failure(self):
        tmp, ws, clock = make_ws()
        with tmp:
            fake = lambda t, m: (True, "fake")        # noqa: E731
            r = reminder.check(ws, fake)
            self.assertEqual((r["notified"], r["reason"]), (False, "沒有到期的複習"))
            solve(ws, clock, "d001")
            clock.t = time.mktime((2026, 12, 20, 23, 30, 0, 0, 0, -1))
            self.assertEqual(reminder.check(ws, fake)["reason"], "安靜時段")
            self.assertTrue(reminder.in_quiet_hours(time.mktime((2026, 12, 20, 3, 0, 0, 0, 0, -1))))
            self.assertFalse(reminder.in_quiet_hours(time.mktime((2026, 12, 20, 12, 0, 0, 0, 0, -1))))
            clock.t = noon(2026, 12, 21)
            bad = reminder.check(ws, lambda t, m: (False, "no daemon"))
            self.assertEqual((bad["notified"], bad["reason"]), (False, "no daemon"))
            self.assertTrue(reminder.check(ws, fake, force=True)["notified"])

    def test_install_plans_per_platform_and_validation(self):
        tmp, ws, clock = make_ws()
        with tmp:
            lin = reminder.install_plan(ws, 20, 5, "linux", "/usr/bin/python3")
            self.assertTrue(lin["line"].startswith("5 20 * * * cd "))
            self.assertIn("remind check", lin["line"])
            mac = reminder.install_plan(ws, 8, 0, "macos", "/usr/bin/python3")
            self.assertIn("StartCalendarInterval", mac["content"])
            self.assertIn("<integer>8</integer>", mac["content"])
            self.assertTrue(mac["path"].endswith("com.cpe-coach.remind.plist"))
            win = reminder.install_plan(ws, 9, 30, "windows", "C:\\Python\\python.exe")
            self.assertIn("/ST", win["command"])
            self.assertIn("09:30", win["command"])
            for bad in ((24, 0), (-1, 0), (1, 60)):
                with self.assertRaises(ValueError):
                    reminder.install_plan(ws, *bad)

    def test_notify_never_raises(self):
        ok, why = reminder.notify("t", "m")
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(why, str)


class CoachTests(unittest.TestCase):
    def test_export_has_no_code_or_statements_and_escapes_html(self):
        tmp, ws, clock = make_ws()
        with tmp:
            solve(ws, clock, "d001")
            ws.log("note", note_kind="think", problem="d001", text="<script>alert(1)</script> my secret idea")
            sol = ws.root / "solutions"
            sol.mkdir(exist_ok=True)
            (sol / "d001.py").write_text("SECRET_CODE_MARKER = 1\n", encoding="utf-8")
            out = coach.export(ws, Path(tmp.name) / "out")
            html = Path(out["html"]).read_text(encoding="utf-8")
            data = json.loads(Path(out["json"]).read_text(encoding="utf-8"))
            self.assertNotIn("SECRET_CODE_MARKER", html + json.dumps(data))
            self.assertNotIn("my secret idea", html)                                    # 沒同意就不附筆記
            self.assertNotIn("notes", data)
            with_notes = coach.export(ws, Path(tmp.name) / "out2", with_notes=True)
            h2 = Path(with_notes["html"]).read_text(encoding="utf-8")
            self.assertIn("my secret idea", h2)
            self.assertNotIn("<script>", h2)
            self.assertIn("&lt;script&gt;", h2)
            self.assertIn("學習報告", html)

    def test_import_comments_validates_and_limits(self):
        tmp, ws, clock = make_ws()
        with tmp:
            f = Path(tmp.name) / "c.json"
            f.write_text(json.dumps({"from": "王老師", "comments": [{"text": "加油", "problem": "d001"}, {"text": "  "}, {"nope": 1}, "x", {"text": "y" * 5000}]}), encoding="utf-8")
            self.assertEqual(coach.import_comments(ws, f), 2)
            cs = coach.comments(ws)
            self.assertEqual(len(cs), 2)
            self.assertEqual(len(cs[0]["text"]), coach.MAX_LEN)
            self.assertEqual(cs[1]["from"], "王老師")
            f.write_text("not json", encoding="utf-8")
            with self.assertRaises(ValueError):
                coach.import_comments(ws, f)
            f.write_text(json.dumps({"comments": "x"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                coach.import_comments(ws, f)
            f.write_text(json.dumps({"comments": [{"text": str(i)} for i in range(200)]}), encoding="utf-8")
            self.assertEqual(coach.import_comments(ws, f), coach.MAX_COMMENTS)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = cli.main(list(args))
        return rc, buf.getvalue()

    def test_commands_run(self):
        tmp, ws, clock = make_ws()
        with tmp:
            old = os.getcwd()
            os.chdir(ws.root)
            try:
                self.assertIn("還沒有設定目標", self.run_cli("goal")[1])
                self.assertNotEqual(self.run_cli("goal", "set")[0], 0)
                rc, out = self.run_cli("goal", "set", "--date", (dt.date.today() + dt.timedelta(days=60)).isoformat(), "--problems", "40")
                self.assertEqual(rc, 0, out)
                self.assertIn("還差 40 題", out)
                self.assertIn("最近 7 天", self.run_cli("report")[1])
                rc, out = self.run_cli("report", "--out", str(Path(tmp.name) / "r"))
                self.assertTrue((Path(tmp.name) / "r" / "cpe-report.html").exists())
                self.assertIn("成就", self.run_cli("achievements")[1])
                self.assertIn("模擬考還不到", self.run_cli("strategy")[1])
                rc, out = self.run_cli("predict")
                self.assertIn("預期答對", out)
                self.assertIn("□", self.run_cli("final", "--days", "3")[1])
                self.assertIn("沒有通知", self.run_cli("remind", "check")[1])
                rc, out = self.run_cli("remind", "install", "--hour", "7")
                self.assertIn("沒有 --apply" if False else "加 --apply", out)
                self.assertNotEqual(self.run_cli("remind", "install", "--hour", "99")[0], 0)
                self.assertIn("沒有開啟", self.run_cli("exp")[1])
                self.assertIn("進行中", self.run_cli("exp", "start")[1])
                self.assertIn("沒有開啟", self.run_cli("exp", "stop")[1])
                f = Path(tmp.name) / "c.json"
                f.write_text(json.dumps({"from": "老師", "comments": [{"text": "做得好"}]}), encoding="utf-8")
                self.assertIn("已匯入 1 則", self.run_cli("coach", "import", str(f))[1])
                self.assertIn("做得好", self.run_cli("coach")[1])
                self.assertTrue((Path(tmp.name) / "co" / "cpe-report.html").exists() or self.run_cli("coach", "export", str(Path(tmp.name) / "co"))[0] == 0)
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main()
