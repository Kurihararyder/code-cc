"""學習科學模組：記憶（FSRS）、知識點、BKT、掌握層級、推薦、錯誤本、靜態分析、習慣與疲勞、計畫整合。"""
import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

from cpe_coach import bank as bank_mod
from cpe_coach import cli, concepts, errbook, habits, knowledge, lint, memory
from cpe_coach import plan as plan_mod
from cpe_coach.store import Workspace

DAY = 86400.0


class Clock:
    def __init__(self, t=1_800_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


def make_ws():
    tmp = tempfile.TemporaryDirectory()
    clock = Clock()
    return tmp, Workspace.create(Path(tmp.name), "2026-11-01", clock), clock


def test_event(ws, clock, pid, verdict, clean=True):
    ws.log("test", problem=pid, verdict=verdict, lang="py", clean=clean)


class MemoryFormulaTests(unittest.TestCase):
    def test_retrievability_at_stability_is_the_target(self):
        for s in (0.5, 3.0, 40.0):
            self.assertAlmostEqual(memory.retrievability(s, s), 0.9, places=6)           # 定義：經過 S 天，保留率剛好 90%
            self.assertAlmostEqual(memory.interval_days(s, 0.9), s, places=6)
        self.assertGreater(memory.retrievability(0, 5), memory.retrievability(10, 5))

    def test_first_review_grades_set_the_stability(self):
        c = memory.Card()
        c.review(0, memory.GOOD)
        self.assertAlmostEqual(c.s, memory.W[2], places=6)
        e = memory.Card()
        e.review(0, memory.EASY)
        self.assertGreater(e.s, c.s)
        h = memory.Card()
        h.review(0, memory.HARD)
        self.assertLess(h.s, c.s)

    def test_success_grows_and_lapse_shrinks_stability(self):
        c = memory.Card()
        c.review(0, memory.GOOD)
        s0 = c.s
        c.review(s0 * DAY, memory.GOOD)
        self.assertGreater(c.s, s0 * 2)                                                  # 到期才複習通過：穩定度明顯增加
        s1 = c.s
        c.review(c.last + 5 * s1 * DAY, memory.AGAIN)
        self.assertLess(c.s, s1)
        self.assertEqual(c.lapses, 1)

    def test_reviewing_later_helps_more_than_reviewing_early(self):
        def after(delay_days):
            c = memory.Card()
            c.review(0, memory.GOOD)
            c.review(delay_days * DAY, memory.GOOD)
            return c.s
        self.assertGreater(after(10), after(1))

    def test_difficulty_stays_in_range_and_moves_with_grades(self):
        c = memory.Card()
        c.review(0, memory.GOOD)
        for _ in range(30):
            c.review(c.last + DAY * 2, memory.AGAIN)
        self.assertLessEqual(c.d, 10.0)
        self.assertGreaterEqual(c.d, 1.0)
        d_hard = c.d
        for _ in range(30):
            c.review(c.last + DAY * 2, memory.EASY)
        self.assertLess(c.d, d_hard)

    def test_personal_fit_needs_enough_data_and_moves_k_the_right_way(self):
        self.assertFalse(memory.fit([(0.9, 1)] * 5).enabled)
        self.assertEqual(memory.fit([(0.9, 1)] * 5).k, 1.0)
        better = memory.fit([(0.8, 1)] * 40)                    # 預測 80% 但每次都記得：你比預設好 → k < 1（R^k 變大）
        self.assertTrue(better.enabled)
        self.assertLess(better.k, 1.0)
        self.assertLess(better.loss_fit, better.loss_default)
        worse = memory.fit([(0.9, 0)] * 40)
        self.assertGreater(worse.k, 1.0)
        calibrated = memory.fit([(0.9, 1)] * 9 + [(0.9, 0)])
        self.assertAlmostEqual(calibrated.k, 1.0, delta=0.15)

    def test_k_changes_the_due_time(self):
        c = memory.Card()
        c.review(0, memory.GOOD)
        self.assertGreater(c.due(0.5), c.due(1.0))
        self.assertLess(c.due(2.0), c.due(1.0))
        self.assertGreaterEqual(c.due(3.0), 0.5 * DAY)


class ReplayTests(unittest.TestCase):
    def test_first_pass_and_failures_before_it(self):
        tmp, ws, clock = make_ws()
        with tmp:
            test_event(ws, clock, "d001", "WA")
            test_event(ws, clock, "d001", "WA")
            self.assertEqual(memory.replay(ws.events()).cards, {})                       # 還沒解出來：不是複習
            clock.t += 60
            test_event(ws, clock, "d001", "AC")
            c = memory.replay(ws.events()).cards["d001"]
            self.assertEqual((c.reps, c.log[0][1]), (1, memory.GOOD))                    # 失敗過才過 → Good，不是 Easy
            tmp2, ws2, clock2 = make_ws()
            with tmp2:
                test_event(ws2, clock2, "d001", "AC")
                self.assertEqual(memory.replay(ws2.events()).cards["d001"].log[0][1], memory.EASY)
                test_event(ws2, clock2, "d002", "AC", clean=False)
                self.assertEqual(memory.replay(ws2.events()).cards["d002"].log[0][1], memory.HARD)

    def test_all_solved_problems_enter_review_even_without_hints(self):
        tmp, ws, clock = make_ws()
        with tmp:
            test_event(ws, clock, "d001", "AC")                                          # 一次就過、沒用提示：舊的 srs 不會排重練
            rp = memory.replay(ws.events())
            due = memory.schedule(rp.cards, clock.t)
            self.assertEqual([d.pid for d in due], ["d001"])
            self.assertGreater(due[0].due_ts, clock.t + 5 * DAY)
            clock.t += 20 * DAY
            self.assertEqual([d.pid for d in memory.due_now(rp.cards, clock.t)], ["d001"])

    def test_resubmits_within_six_hours_are_one_review(self):
        tmp, ws, clock = make_ws()
        with tmp:
            test_event(ws, clock, "d001", "AC")
            clock.t += 3600
            test_event(ws, clock, "d001", "AC")
            test_event(ws, clock, "d001", "WA")
            self.assertEqual(memory.replay(ws.events()).cards["d001"].reps, 1)
            clock.t += 3 * DAY
            test_event(ws, clock, "d001", "WA")                                          # 隔幾天再做卻沒過：遺忘
            c = memory.replay(ws.events()).cards["d001"]
            self.assertEqual((c.reps, c.lapses), (2, 1))

    def test_replay_gives_pairs_for_fitting_and_concepts(self):
        tmp, ws, clock = make_ws()
        with tmp:
            bank = bank_mod.load_bank(ws)
            test_event(ws, clock, "d001", "AC")
            clock.t += 4 * DAY
            test_event(ws, clock, "d001", "AC")
            rp = memory.replay(ws.events(), bank)
            self.assertEqual(len(rp.pairs), 1)
            self.assertEqual(rp.pairs[0][1], 1)
            self.assertIn("io", rp.concept_cards)
            rep = memory.concept_report(rp.concept_cards, clock.t)
            self.assertEqual(rep[0]["id"], "io")

    def test_replay_is_deterministic_and_ignores_junk_events(self):
        tmp, ws, clock = make_ws()
        with tmp:
            test_event(ws, clock, "d001", "AC")
            ws.log("hint", problem="d001", level=1)
            ws.log("test", problem=None, verdict="AC")
            ws.log("test", problem="d009", verdict="SETUP")
            a = memory.replay(ws.events()).cards
            b = memory.replay(list(ws.events())).cards
            self.assertEqual({k: (v.s, v.d) for k, v in a.items()}, {k: (v.s, v.d) for k, v in b.items()})
            self.assertEqual(list(a), ["d001"])


class ScheduleTests(unittest.TestCase):
    def test_load_balancing_caps_a_day_and_forecast_counts_everything(self):
        now = 1_800_000_000.0
        cards = {}
        for i in range(20):
            c = memory.Card()
            c.review(now - 10 * DAY, memory.GOOD)               # 20 題同一天到期
            cards[f"p{i}"] = c
        sched = memory.schedule(cards, now, cap=8, spread=2)
        per_day = {}
        for it in sched:
            per_day[it.day] = per_day.get(it.day, 0) + 1
        self.assertLessEqual(per_day[0], 8)
        self.assertEqual(sum(per_day.values()), 20)
        self.assertEqual(sum(memory.forecast(cards, now, days=30, cap=8)), 20)
        self.assertEqual(len(memory.due_now(cards, now, cap=8)), 8)


class ConceptTests(unittest.TestCase):
    def test_graph_is_valid_and_topological(self):
        self.assertEqual(concepts.validate(), [])
        order = concepts.topo_order()
        cs = concepts.load()
        for c in order:
            for p in cs[c]["pre"]:
                self.assertLess(order.index(p), order.index(c))
        self.assertIn("graph", concepts.prereq_closure("shortest"))
        self.assertEqual(len(order), len(cs))

    def test_every_bank_problem_gets_a_concept_and_known_ones_map_correctly(self):
        tmp, ws, _ = make_ws()
        with tmp:
            bank = bank_mod.load_bank(ws)
            for pid, p in bank.items():
                cs = concepts.of_problem(p)
                self.assertTrue(cs and all(c in concepts.load() for c in cs), pid)
            self.assertIn("shortest", concepts.of_problem(bank["uva544"]))
            self.assertIn("dp", concepts.of_problem(bank["uva10036"]))
            self.assertIn("dsu", concepts.of_problem(bank["uva10583"]))
            self.assertIn("geometry", concepts.of_problem(bank["uva10065"]))


class KnowledgeTests(unittest.TestCase):
    def test_bkt_rises_with_clean_successes_and_falls_with_failures(self):
        tmp, ws, clock = make_ws()
        with tmp:
            bank = bank_mod.load_bank(ws)
            base = knowledge.bkt(ws.events(), bank)
            self.assertEqual(base, {})
            for pid in ("d001", "d002", "d003"):
                test_event(ws, clock, pid, "AC")
                clock.t += 3600
            up = knowledge.bkt(ws.events(), bank)["io"]
            self.assertGreater(up, 0.5)
            tmp2, ws2, clock2 = make_ws()
            with tmp2:
                for pid in ("d001", "d002", "d003"):
                    test_event(ws2, clock2, pid, "WA")
                    clock2.t += 3600
                self.assertLess(knowledge.bkt(ws2.events(), bank)["io"], up)

    def test_a_struggle_in_one_sitting_is_one_incorrect_attempt(self):
        tmp, ws, clock = make_ws()
        with tmp:
            for v in ("WA", "WA", "WA", "AC"):
                test_event(ws, clock, "d001", v)
                clock.t += 60
            a = knowledge.attempts(ws.events())
            self.assertEqual(len(a), 1)
            self.assertTrue(a[0]["solved"] and not a[0]["correct"])

    def test_levels_progress_from_touched_to_varied(self):
        tmp, ws, clock = make_ws()
        with tmp:
            bank = bank_mod.load_bank(ws)
            a, b, c, e = [pid for pid in sorted(bank) if "io" in concepts.of_problem(bank[pid])][:4]

            def lv():
                rp, ft = memory.build(ws, bank)
                return knowledge.levels(ws.events(), bank, rp, clock.t, ft.k)["io"]["level"]
            self.assertEqual(lv(), 0)
            test_event(ws, clock, a, "WA")
            self.assertEqual(lv(), 1)
            clock.t += 3600
            test_event(ws, clock, a, "AC", clean=False)
            self.assertEqual(lv(), 2)
            clock.t += 3600
            test_event(ws, clock, b, "AC")
            test_event(ws, clock, c, "AC")
            self.assertEqual(lv(), 3)
            test_event(ws, clock, e, "AC")
            clock.t += 3 * DAY
            test_event(ws, clock, b, "AC")                                               # 隔了幾天的複習還答對
            self.assertEqual(lv(), 4)

    def test_recommend_prefers_the_target_probability_and_respects_prerequisites(self):
        tmp, ws, clock = make_ws()
        with tmp:
            bank = bank_mod.load_bank(ws)
            rec = knowledge.recommend(ws, bank, 5, current_unit=1)
            self.assertTrue(rec)
            self.assertTrue(all(r["id"] not in ("uva544", "uva10036") for r in rec))       # 圖、DP 的先修還沒解鎖
            self.assertLessEqual(abs(rec[0]["p_success"] - 0.7), abs(rec[-1]["p_success"] - 0.7) + 1e-9)
            for r in rec:
                self.assertIn("推測", r["why"])
            far = knowledge.recommend(ws, bank, 200, current_unit=40)
            self.assertGreater(len(far), len(knowledge.recommend(ws, bank, 200, current_unit=1)))

    def test_solved_problems_are_not_recommended(self):
        tmp, ws, clock = make_ws()
        with tmp:
            bank = bank_mod.load_bank(ws)
            st = ws.state()
            ws.problem(st, "d001")["first_pass"] = clock.t
            ws.save_state(st)
            self.assertNotIn("d001", [r["id"] for r in knowledge.recommend(ws, bank, 300, current_unit=52)])


class ErrbookTests(unittest.TestCase):
    CASES = [
        ("TLE", None, "時間複雜度太高"), ("MLE", None, "記憶體不足"), ("CE", None, "編譯錯誤"), ("AC", None, None),
        ("RE", {"stderr": "IndexError: list index out of range"}, "越界"),
        ("RE", {"stderr": "RecursionError: maximum recursion depth exceeded"}, "遞迴過深"),
        ("RE", {"stderr": "EOFError: EOF when reading a line"}, "讀入超過輸入"),
        ("RE", {"stderr": "ValueError: invalid literal for int() with base 10: 'a'"}, "輸入解析"),
        ("RE", {"stderr": "ZeroDivisionError: division by zero"}, "除以零"),
        ("RE", {"stderr": "KeyError: 3"}, "字典沒有鍵"),
        ("RE", {"stderr": "NameError: name 'x' is not defined"}, "語法或名稱錯誤"),
        ("RE", {"stderr": "weird"}, "其他執行錯誤"),
        ("WA", {"expected": "1 2 3\n", "actual": ""}, "沒有輸出"),
        ("WA", {"expected": "1 2 3\n", "actual": "1\n2\n3\n"}, "輸出格式"),
        ("WA", {"expected": "Yes\n", "actual": "yes\n"}, "大小寫"),
        ("WA", {"expected": "5\n7\n", "actual": "4\n7\n"}, "差一（邊界）"),
        ("WA", {"expected": "3.14159\n", "actual": "3.14\n"}, "浮點精度"),
        ("WA", {"expected": "1\n2\n3\n", "actual": "1\n2\n"}, "輸出不完整"),
        ("WA", {"expected": "1\n2\n", "actual": "1\n2\n3\n"}, "輸出多餘"),
        ("WA", {"expected": "10\n", "actual": "99\n"}, "邏輯錯誤"),
    ]

    def test_classification_table(self):
        for verdict, failing, want in self.CASES:
            self.assertEqual(errbook.classify(verdict, failing), want, (verdict, failing))

    def test_every_cause_has_advice_and_is_listed(self):
        for _, _, c in self.CASES:
            if c:
                self.assertIn(c, errbook.CAUSES)
        self.assertEqual(set(errbook.CAUSES), set(errbook.ADVICE))

    def test_summary_counts_and_manual_retag(self):
        tmp, ws, clock = make_ws()
        with tmp:
            for pid, cause in (("d001", "越界"), ("d001", "越界"), ("d002", "差一（邊界）")):
                ws.log("err", problem=pid, cause=cause, verdict="RE")
                clock.t += 10
            s = errbook.summary(ws.events())
            self.assertEqual((s["total"], s["causes"][0]["cause"], s["causes"][0]["count"]), (3, "越界", 2))
            self.assertEqual(s["worst_problems"][0]["id"], "d001")
            self.assertIn("索引", s["advice"])
            last = [e for e in ws.events() if e["kind"] == "err"][-1]
            ws.log("errtag", target_ts=last["ts"], problem="d002", cause="邏輯錯誤")
            s = errbook.summary(ws.events())
            self.assertIn("邏輯錯誤", [c["cause"] for c in s["causes"]])
            self.assertNotIn("差一（邊界）", [c["cause"] for c in s["causes"]])
            self.assertEqual(errbook.summary([])["total"], 0)


class LintTests(unittest.TestCase):
    def codes(self, src, lang="py"):
        return {f["code"] for f in lint.lint(src, lang)}

    def test_python_rules(self):
        self.assertIn("pop0", self.codes("q=[1]\nwhile q:\n    q.pop(0)\n"))
        self.assertIn("insert0", self.codes("a=[]\nfor i in range(9):\n    a.insert(0,i)\n"))
        self.assertIn("deep-loop", self.codes("for i in range(9):\n for j in range(9):\n  for k in range(9):\n   pass\n"))
        self.assertIn("input-loop", self.codes("for i in range(9):\n    x=input()\n"))
        self.assertIn("str-concat", self.codes("s=''\nfor i in range(9):\n    s += 'a'\n"))
        self.assertIn("shadow-builtin", self.codes("sum = 0\nprint(sum)\n"))
        self.assertIn("in-list", self.codes("a=[1,2]\nfor i in range(9):\n    if i in a:\n        pass\n"))
        self.assertIn("mutable-default", self.codes("def f(x=[]):\n    return x\n"))
        self.assertIn("recursion", self.codes("def f(n):\n    return f(n-1)\n"))
        self.assertIn("float-eq", self.codes("x = 0.1\nif x == 0.3:\n    pass\n"))
        self.assertIn("bare-except", self.codes("try:\n    pass\nexcept:\n    pass\n"))
        self.assertIn("unused-var", self.codes("def f():\n    y = 1\n    return 2\n"))
        self.assertIn("syntax", self.codes("def (:\n"))
        self.assertIn("index-in-loop", self.codes("a=[1]\nfor i in range(3):\n    a.index(1)\n"))

    def test_clean_code_has_no_findings_and_setrecursionlimit_silences_the_recursion_hint(self):
        self.assertEqual(lint.lint("import sys\nn = int(sys.stdin.readline())\nprint(n * 2)\n", "py"), [])
        self.assertNotIn("recursion", self.codes("import sys\nsys.setrecursionlimit(10**6)\ndef f(n):\n    return f(n-1) if n else 0\n"))

    def test_cpp_rules(self):
        src = "#include <iostream>\nint main(){int a,b; std::cin>>a>>b; int c = a * b; for(int i=0;i<3;i++){ std::cout<<c<<std::endl; } }\n"
        self.assertTrue({"cin-sync", "endl-loop", "int-overflow"} <= self.codes(src, "cpp"))
        self.assertNotIn("cin-sync", self.codes("int main(){ios::sync_with_stdio(false);cin.tie(nullptr);cin>>a;}", "cpp"))


class HabitTests(unittest.TestCase):
    def test_time_of_day_needs_enough_data(self):
        self.assertIn("不夠", habits.by_time_of_day([])["note"])
        import time as _t
        morning = _t.mktime((2026, 11, 2, 9, 0, 0, 0, 0, -1))
        evening = _t.mktime((2026, 11, 2, 20, 0, 0, 0, 0, -1))
        evs = []
        for i in range(10):
            evs.append({"kind": "test", "problem": f"m{i}", "verdict": "AC", "clean": True, "ts": morning + i * 300})
            evs.append({"kind": "test", "problem": f"n{i}", "verdict": "WA", "ts": evening + i * 300})
        r = habits.by_time_of_day(evs)
        self.assertEqual(r["best"], "上午")
        self.assertIn("一次通過率", r["note"])
        self.assertEqual({x["slot"]: x["rate"] for x in r["slots"]}["晚上"], 0.0)

    def test_fatigue_signals(self):
        now = 1_800_000_000.0
        evs = [{"kind": "test", "problem": "a", "verdict": "WA", "ts": now - 60 * i} for i in range(7)]
        sig = habits.fatigue(evs, now)
        self.assertIn("fail-streak", {s["id"] for s in sig})
        long = [{"kind": "test", "problem": f"q{i}", "verdict": "AC", "ts": now - 3 * 3600 + i * 600} for i in range(19)]
        self.assertIn("long-session", {s["id"] for s in habits.fatigue(long, now)})
        self.assertEqual(habits.fatigue([], now), [])


class IntegrationTests(unittest.TestCase):
    def run_cli(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = cli.main(list(args))
        return rc, buf.getvalue()

    def test_plan_includes_memory_reviews_and_interleaves(self):
        tmp, ws, clock = make_ws()
        with tmp:
            for pid in ("d001", "d002"):
                test_event(ws, clock, pid, "AC")
            clock.t += 15 * DAY
            p = plan_mod.build(ws, 60)
            why = [i["why"] for i in p["items"] if i["kind"] == "review"]
            self.assertTrue(any("記憶排程" in w for w in why), p["items"])

    def test_cli_commands_run_on_a_fresh_and_a_used_workspace(self):
        tmp, ws, clock = make_ws()
        with tmp:
            old = os.getcwd()
            os.chdir(ws.root)
            try:
                for argv, needle in ((["mem"], "納入記憶排程"), (["mem", "forecast"], "負載平準"), (["mem", "fit"], "複習次數"), (["mem", "concepts"], "還沒有"),
                                     (["err"], "空的"), (["insight"], "知識點掌握")):
                    rc, out = self.run_cli(*argv)
                    self.assertEqual(rc, 0, argv)
                    self.assertIn(needle, out, argv)
                ws.log("err", problem="d001", cause="越界", verdict="RE")
                self.assertIn("越界", self.run_cli("err")[1])
                self.assertEqual(self.run_cli("err", "tag", "d001", "除以零")[0], 0)
                self.assertIn("除以零", self.run_cli("err")[1])
                self.assertNotEqual(self.run_cli("err", "tag", "d001", "亂寫")[0], 0)
                self.assertEqual(self.run_cli("new", "d001")[0], 0)
                self.assertEqual(self.run_cli("lint", "d001")[0], 0)
            finally:
                os.chdir(old)

    def test_run_test_logs_cause_and_lint(self):
        from cpe_coach import service
        tmp, ws, clock = make_ws()
        with tmp:
            old = os.getcwd()
            os.chdir(ws.root)
            try:
                self.run_cli("new", "d001")
                sol = service.solution_file(ws, "d001")
                sol.write_text("sum = 0\nprint(undefined_name)\n", encoding="utf-8")
                r = service.run_test(ws, "d001")
                self.assertEqual(r["verdict"], "RE")
                self.assertEqual(r["cause"], "語法或名稱錯誤")
                self.assertIn("shadow-builtin", {x["code"] for x in r["static"]})
                self.assertEqual([e["cause"] for e in ws.events() if e["kind"] == "err"], ["語法或名稱錯誤"])
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main()
