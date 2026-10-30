import random
import tempfile
import unittest
from pathlib import Path

import shutil

from cpe_coach import bank, cli, course, hints, judge, llm, mock, srs, stats
from cpe_coach.store import Workspace, new_problem_state

DAY = 86400.0


class Clock:
    def __init__(self, t=1_800_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


def make_ws():
    tmp = tempfile.TemporaryDirectory()
    clock = Clock()
    ws = Workspace.create(Path(tmp.name), "2026-11-01", clock)
    return tmp, ws, clock


class JudgeTests(unittest.TestCase):
    def test_compare(self):
        self.assertEqual(judge.compare("1\n2\n", "1\n2"), judge.AC)
        self.assertEqual(judge.compare("1 \n2\n\n\n", "1\n2\n"), judge.AC)
        self.assertEqual(judge.compare("1\n\n2\n", "1\n2\n"), judge.PE)
        self.assertEqual(judge.compare("1\n3\n", "1\n2\n"), judge.WA)

    def test_judge_verdicts(self):
        tmp, ws, _ = make_ws()
        with tmp:
            td = ws.tests / "p"
            td.mkdir()
            (td / "a.in").write_text("3\n", encoding="utf-8")
            (td / "a.out").write_text("6\n", encoding="utf-8")
            cases = {
                "ac": ("print(int(input())*2)", judge.AC),
                "wa": ("print(7)", judge.WA),
                "re": ("raise ValueError('x')", judge.RE),
                "ce": ("def (:", judge.CE),
                "tle": ("while True: pass", judge.TLE),
            }
            for name, (code, want) in cases.items():
                f = ws.root / f"{name}.py"
                f.write_text(code, encoding="utf-8")
                self.assertEqual(judge.judge(f, td, timeout=1.0).verdict, want, name)

    def test_missing_tests_is_setup_error(self):
        tmp, ws, _ = make_ws()
        with tmp:
            f = ws.root / "s.py"
            f.write_text("print(1)", encoding="utf-8")
            r = judge.judge(f, ws.tests / "none")
            self.assertTrue(r.setup_error)

    def test_stress_finds_bug(self):
        tmp, ws, _ = make_ws()
        with tmp:
            gen = ws.root / "gen.py"
            gen.write_text("import sys,random\nrandom.seed(int(sys.argv[1]))\nprint(random.randint(1,100))\n", encoding="utf-8")
            brute = ws.root / "brute.py"
            brute.write_text("print(int(input())*2)\n", encoding="utf-8")
            good = ws.root / "good.py"
            good.write_text("n=int(input())\nprint(n*2)\n", encoding="utf-8")
            bad = ws.root / "bad.py"
            bad.write_text("n=int(input())\nprint(n*2 if n < 50 else n*2+1)\n", encoding="utf-8")
            self.assertIsNone(judge.stress(good, brute, gen, 20))
            r = judge.stress(bad, brute, gen, 50)
            self.assertIsNotNone(r)
            self.assertEqual(r[4], judge.WA)


class SrsTests(unittest.TestCase):
    def setUp(self):
        self.p = new_problem_state()
        self.t = 1_800_000_000.0

    def test_clean_first_pass_is_mastered(self):
        info = srs.record_result(self.p, judge.AC, self.t)
        self.assertTrue(info["mastered"])
        self.assertEqual(self.p["review_stage"], srs.MASTERED)

    def test_hint_use_schedules_reviews_1_3_7(self):
        self.p["hint_level"] = 2
        srs.record_result(self.p, judge.AC, self.t)
        self.assertEqual(self.p["review_stage"], 0)
        self.assertAlmostEqual(self.p["review_due"], self.t + 1 * DAY)
        t = self.t + 1 * DAY
        srs.record_result(self.p, judge.AC, t)
        self.assertEqual((self.p["review_stage"], self.p["review_due"]), (1, t + 3 * DAY))
        t += 3 * DAY
        srs.record_result(self.p, judge.AC, t)
        self.assertEqual((self.p["review_stage"], self.p["review_due"]), (2, t + 7 * DAY))
        t += 7 * DAY
        info = srs.record_result(self.p, judge.AC, t)
        self.assertTrue(info["mastered"])
        self.assertEqual(self.p["review_stage"], srs.MASTERED)

    def test_l0_does_not_count_as_hint(self):
        self.p["hint_level"] = 0
        self.assertTrue(srs.record_result(self.p, judge.AC, self.t)["mastered"])

    def test_early_pass_gets_no_credit(self):
        self.p["giveup_at"] = self.t
        srs.record_result(self.p, judge.AC, self.t)
        srs.record_result(self.p, judge.AC, self.t + 100)
        self.assertEqual(self.p["review_stage"], 0)

    def test_hint_during_review_resets_cycle(self):
        self.p["hint_level"] = 1
        srs.record_result(self.p, judge.AC, self.t)
        t = self.t + DAY
        srs.record_result(self.p, judge.AC, t)           # -> stage 1
        t += 3 * DAY
        self.p["hint_level"] = 1                          # 重練時偷看提示
        srs.record_result(self.p, judge.AC, t)
        self.assertEqual(self.p["review_stage"], 0)

    def test_failed_review_restarts(self):
        self.p["hint_level"] = 1
        srs.record_result(self.p, judge.AC, self.t)
        t = self.t + DAY
        srs.record_result(self.p, judge.AC, t)
        t += 3 * DAY
        info = srs.record_result(self.p, judge.WA, t)
        self.assertTrue(info["review_attempt"])
        self.assertEqual((self.p["review_stage"], self.p["review_due"]), (0, t + DAY))


class HintTests(unittest.TestCase):
    def test_gate_rules(self):
        tmp, ws, _ = make_ws()
        with tmp:
            p = new_problem_state()
            hints.check_gate(ws, p, 0)                                   # L0 隨時可用
            with self.assertRaises(hints.HintDenied):                    # 沒試過不能 L1
                hints.check_gate(ws, p, 1)
            p["attempts_since_hint"] = 1
            hints.check_gate(ws, p, 1)
            with self.assertRaises(hints.HintDenied):                    # 不能跳級
                hints.check_gate(ws, p, 3)
            p["hint_level"], p["attempts_since_hint"] = 1, 0
            with self.assertRaises(hints.HintDenied):                    # 升級前要有新嘗試
                hints.check_gate(ws, p, 2)
            hints.check_gate(ws, p, 1)                                   # 重看已解鎖級別免費
            p["hint_level"], p["attempts_since_hint"], p["last_verdict"] = 3, 1, "AC"
            with self.assertRaises(hints.HintDenied):                    # L4 需要失敗紀錄
                hints.check_gate(ws, p, 4)
            p["last_verdict"] = "WA"
            hints.check_gate(ws, p, 4)

    def test_exam_locks_hints(self):
        tmp, ws, _ = make_ws()
        with tmp:
            ws.save_exam({"kind": "mock", "start": 0, "minutes": 1, "problems": [], "files": {}, "results": {}})
            with self.assertRaises(hints.HintDenied):
                hints.check_gate(ws, new_problem_state(), 0)

    def test_request_hint_updates_state_and_uses_static(self):
        tmp, ws, _ = make_ws()
        with tmp:
            b = bank.load_bank()
            st = ws.state()
            ws.problem(st, "uva10041")["attempts_since_hint"] = 1
            ws.save_state(st)
            out = hints.request_hint(ws, "uva10041", 1, b["uva10041"], "", None, None)
            self.assertEqual(out["source"], "static")
            self.assertEqual(ws.state()["problems"]["uva10041"]["hint_level"], 1)
            self.assertEqual(ws.state()["problems"]["uva10041"]["attempts_since_hint"], 0)

    def test_llm_hint_filters_long_code(self):
        tmp, ws, _ = make_ws()
        with tmp:
            long_code = "```python\n" + "\n".join(f"x{i} = {i}" for i in range(30)) + "\n```"
            fake = llm.LLMClient("openai", "k", transport=lambda u, h, b: {
                "choices": [{"message": {"content": "先想想輸入結構。\n" + long_code}}]})
            st = ws.state()
            ws.problem(st, "p")["attempts_since_hint"] = 1
            ws.save_state(st)
            out = hints.request_hint(ws, "p", 0, {"id": "p"}, "", None, fake)
            self.assertEqual(out["source"], "llm")
            self.assertIn("已被系統移除", out["text"])
            self.assertNotIn("x29", out["text"])

    def test_giveup_cooldown(self):
        tmp, ws, clock = make_ws()
        with tmp:
            unlock = hints.giveup(ws, "p")
            self.assertAlmostEqual(unlock, clock.t + 24 * 3600)
            p = ws.state()["problems"]["p"]
            self.assertTrue(srs.is_dirty(p))


class LlmTests(unittest.TestCase):
    def test_strip_long_code_keeps_short(self):
        t = "看這個\n```python\nprint(1)\n```\n結束"
        self.assertEqual(llm.strip_long_code(t, 3), t)

    def test_strip_indented_run(self):
        t = "a\n" + "\n".join("    line%d" % i for i in range(12)) + "\nb"
        out = llm.strip_long_code(t, 5)
        self.assertIn("已被系統移除", out)
        self.assertTrue(out.startswith("a") and out.endswith("b"))

    def test_payloads(self):
        seen = {}

        def t(url, headers, body):
            seen["url"], seen["headers"], seen["body"] = url, headers, body
            return {"content": [{"type": "text", "text": "ok"}]}
        c = llm.LLMClient("anthropic", "KEY", transport=t)
        self.assertEqual(c.complete("sys", "usr"), "ok")
        self.assertEqual(seen["headers"]["x-api-key"], "KEY")
        self.assertEqual(seen["body"]["system"], "sys")

    def test_detect_client(self):
        self.assertIsNone(llm.detect_client({}, env={}))
        self.assertEqual(llm.detect_client({}, env={"ANTHROPIC_API_KEY": "k"}).provider, "anthropic")
        self.assertEqual(llm.detect_client({"provider": "openai"}, env={"OPENAI_API_KEY": "k"}).provider, "openai")
        self.assertIsNone(llm.detect_client({"provider": "openai"}, env={"ANTHROPIC_API_KEY": "k"}))

    def test_gpt_folder_copy_in_sync(self):
        root = Path(__file__).resolve().parent.parent
        self.assertEqual((root / "gpt" / "custom_gpt_instructions.md").read_text(encoding="utf-8"), llm.RULES)


class MockTests(unittest.TestCase):
    def test_composition_and_scoring(self):
        tmp, ws, clock = make_ws()
        with tmp:
            b = bank.load_bank()
            exam = mock.start(ws, b, "mock", random.Random(1))
            self.assertEqual(len(exam["problems"]), 7)
            self.assertEqual(len(set(exam["problems"])), 7)
            diffs = [b[p]["difficulty"] for p in exam["problems"]]
            self.assertEqual(diffs, [1, 1, 1, 2, 2, 3, 4])
            a, c = exam["problems"][0], exam["problems"][1]
            clock.t += 600
            mock.record(ws, exam, a, judge.WA)
            mock.record(ws, exam, a, judge.CE)          # 語法錯誤不罰
            clock.t += 600
            mock.record(ws, exam, a, judge.AC)           # 第 20 分鐘，錯 1 次
            clock.t += 600
            mock.record(ws, exam, c, judge.AC)           # 第 30 分鐘
            s = mock.finish(ws)
            self.assertEqual(s["solved"], 2)
            self.assertEqual(s["penalty"], 20 + 20 + 30)
            self.assertFalse(ws.exam_active())
            self.assertEqual(len(ws.state()["exams"]), 1)

    def test_no_credit_after_time_up(self):
        tmp, ws, clock = make_ws()
        with tmp:
            exam = mock.start(ws, bank.load_bank(), "short", random.Random(2))
            clock.t += 91 * 60
            note = mock.record(ws, exam, exam["problems"][0], judge.AC)
            self.assertIn("不計分", note)
            self.assertEqual(mock.score(ws.exam())["solved"], 0)

    def test_weekly_picks_oldest_solved(self):
        st = {"problems": {
            "a": {**new_problem_state(), "first_pass": 1, "last_pass": 300},
            "b": {**new_problem_state(), "first_pass": 1, "last_pass": 100},
            "c": {**new_problem_state(), "first_pass": 1, "last_pass": 200},
            "d": {**new_problem_state(), "first_pass": 1, "last_pass": 400},
            "e": new_problem_state()}}
        self.assertEqual(mock.pick_weekly(st), ["b", "c", "a"])


class BankTests(unittest.TestCase):
    def test_bank_integrity(self):
        b = bank.load_bank()
        self.assertGreaterEqual(len(b), 200)
        for p in b.values():
            for k in ("id", "title", "stage", "difficulty", "topic", "hint_category"):
                self.assertTrue(p.get(k), (p["id"], k))
            if not p.get("unverified"):
                self.assertTrue(p.get("hint_insight"), p["id"])
            self.assertIn(p["stage"], (1, 2, 3, 4))
            self.assertIn(p["difficulty"], (1, 2, 3, 4))
        self.assertGreaterEqual(sum(1 for p in b.values() if p["difficulty"] == 4), 5)

    def test_custom_overrides(self):
        tmp, ws, _ = make_ws()
        with tmp:
            bank.add_custom(ws, {"id": "uva100", "title": "X", "stage": 1, "difficulty": 1})
            self.assertEqual(bank.load_bank(ws)["uva100"]["title"], "X")


class CourseTests(unittest.TestCase):
    def setUp(self):
        self.c = course.load()
        self.bank = bank.load_bank()

    def test_weeks_contiguous_and_total(self):
        w = 1
        for i, u in enumerate(self.c["units"], 1):
            self.assertEqual((u["n"], u["start"]), (i, w))
            w += u["weeks"]
        self.assertEqual(w - 1, self.c["total_weeks"])
        self.assertEqual(self.c["total_weeks"], 126)

    def test_stages_monotonic(self):
        stages = [u["stage"] for u in self.c["units"]]
        self.assertEqual(stages, sorted(stages))
        self.assertEqual(set(stages), {0, 1, 2, 3, 4, 5})

    def test_all_references_exist_and_every_drill_used(self):
        used = set()
        for u in self.c["units"]:
            ids = list(u["drills"]) + list(u["anchors"])
            if u["gate"] and u["gate"]["type"] == "set":
                ids += u["gate"]["problems"]
                self.assertLessEqual(u["gate"]["need"], len(u["gate"]["problems"]), u["n"])
            for pid in ids:
                self.assertIn(pid, self.bank, (u["n"], pid))
            used |= set(u["drills"])
            if u["gate"] and u["gate"]["type"] == "set":
                used |= set(u["gate"]["problems"])
            for r in u["resources"]:
                self.assertIn(r, self.c["resources"])
            self.assertTrue(u["learn"] and u["goal"] and u["title"], u["n"])
        drills = {p for p, v in self.bank.items() if v.get("drill") and not v.get("reserve")}
        self.assertEqual(drills - used, set())

    def test_cpp_gates_are_cpp_units(self):
        for u in self.c["units"]:
            if u["gate"] and u["gate"]["type"] == "set":
                self.assertEqual(u["gate"]["lang"], u["lang"], u["n"])

    def test_gate_problems_not_all_required_practice_for_first_unit(self):
        # 第一個檢核含沒練過的新題，而不是只重寫
        u = self.c["units"][0]
        self.assertTrue(set(u["gate"]["problems"]) - set(u["drills"]))

    def test_expected_unit(self):
        self.assertEqual(course.expected_unit(self.c, 1)["n"], 1)
        self.assertEqual(course.expected_unit(self.c, 126)["n"], 52)
        self.assertEqual(course.expected_unit(self.c, 9999)["n"], 52)

    def test_drill_files_complete(self):
        for pid, p in self.bank.items():
            if not p.get("drill"):
                continue
            d = bank.DRILLS / pid
            self.assertTrue((d / "statement.md").exists(), pid)
            ins = sorted((d / "tests").glob("*.in"))
            self.assertGreaterEqual(len(ins), 2, pid)
            for f in ins:
                self.assertTrue(f.with_suffix(".out").exists(), (pid, f.name))
            self.assertTrue(ins[0].with_suffix(".out").read_text(encoding="utf-8").strip(), pid)  # 範例輸出不可為空
            # 範例（case01）要出現在題目敘述裡
            self.assertIn(ins[0].read_text(encoding="utf-8").rstrip("\n"), (d / "statement.md").read_text(encoding="utf-8"))

    def test_install_drill_does_not_overwrite_tests(self):
        tmp, ws, _ = make_ws()
        with tmp:
            self.assertTrue(bank.install_drill(ws, "d001"))
            (ws.tests / "d001" / "mine.in").write_text("x\n", encoding="utf-8")
            self.assertFalse(bank.install_drill(ws, "d001"))
            self.assertTrue((ws.tests / "d001" / "mine.in").exists())
            self.assertFalse(bank.install_drill(ws, "uva100"))

    def test_gate_requires_unit_drills_and_advances(self):
        tmp, ws, clock = make_ws()
        with tmp:
            u = self.c["units"][0]
            with self.assertRaises(ValueError):
                course.start_gate(ws, self.bank, self.c, u)          # 還沒練
            for d in u["drills"]:
                ws.log("test", problem=d, verdict="AC", lang="py")
            exam = course.start_gate(ws, self.bank, self.c, u)
            self.assertEqual(exam["problems"], u["gate"]["problems"])
            self.assertTrue((ws.tests / "d004").exists())
            exam = ws.exam()
            for pid in exam["problems"]:
                mock.record(ws, exam, pid, judge.AC)
            s = mock.finish(ws)
            msg = course.evaluate_gate(ws, self.c, s)
            self.assertIn("通過", msg)
            self.assertEqual(ws.state()["course"]["unit"], 2)

    def test_failed_gate_does_not_advance(self):
        tmp, ws, _ = make_ws()
        with tmp:
            u = self.c["units"][0]
            for d in u["drills"]:
                ws.log("test", problem=d, verdict="AC", lang="py")
            exam = course.start_gate(ws, self.bank, self.c, u)
            msg = course.evaluate_gate(ws, self.c, mock.finish(ws))
            self.assertIn("未通過", msg)
            self.assertEqual(ws.state()["course"]["unit"], 1)

    def test_goto_sets_stage(self):
        tmp, ws, _ = make_ws()
        with tmp:
            course.goto(ws, self.c, 30)
            self.assertEqual(ws.config()["stage"], self.c["units"][29]["stage"])
            self.assertEqual(ws.state()["course"]["done"], list(range(1, 30)))


class ImportTests(unittest.TestCase):
    def test_parse_samples_english_and_chinese(self):
        t = "Problem\nSample Input\n3 4\n5 6\n\nSample Output\n7\n11\n"
        self.assertEqual(cli.parse_samples(t), [("3 4\n5 6", "7\n11")])
        t2 = "## 範例輸入 #1\n1\n## 範例輸出 #1\n2\n## 範例輸入 #2\n3\n## 範例輸出 #2\n4\n"
        self.assertEqual(cli.parse_samples(t2), [("1", "2"), ("3", "4")])
        self.assertEqual(cli.parse_samples("沒有範例"), [])


@unittest.skipUnless(shutil.which("g++"), "需要 g++")
class CppTests(unittest.TestCase):
    def test_cpp_verdicts(self):
        tmp, ws, _ = make_ws()
        with tmp:
            td = ws.tests / "p"
            td.mkdir()
            (td / "a.in").write_text("3\n", encoding="utf-8")
            (td / "a.out").write_text("6\n", encoding="utf-8")
            src = {
                "ok": ('#include <iostream>\nint main(){int n;std::cin>>n;std::cout<<n*2<<"\\n";}', judge.AC),
                "wa": ('#include <iostream>\nint main(){std::cout<<7<<"\\n";}', judge.WA),
                "re": ('int main(){return 3;}', judge.RE),
                "ce": ('int main(){ this is not c++ }', judge.CE),
                "tle": ('int main(){while(1){}}', judge.TLE),
            }
            for name, (code, want) in src.items():
                f = ws.root / f"{name}.cpp"
                f.write_text(code, encoding="utf-8")
                self.assertEqual(judge.judge(f, td, timeout=2.0).verdict, want, name)



class CliSmokeTests(unittest.TestCase):
    """從頭走一遍：init → course → new → test → hint 閘門 → import → 重練。"""

    def run_cli(self, *args):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = cli.main(list(args))
        return rc, buf.getvalue()

    def test_learner_flow(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            old = os.getcwd()
            os.chdir(d)
            try:
                self.assertEqual(self.run_cli("init", "ws", "--start", "2026-11-02")[0], 0)
                os.chdir("ws")
                rc, out = self.run_cli("course")
                self.assertEqual(rc, 0)
                self.assertIn("d001", out)
                rc, out = self.run_cli("new", "d001")
                self.assertEqual(rc, 0)
                self.assertTrue((Path("statements") / "d001.md").exists())
                self.assertEqual(len(list(Path("tests/d001").glob("*.in"))), 3)
                # 空白模板應失敗；L1 在還沒嘗試前被擋；試過一次後可以
                self.assertNotEqual(self.run_cli("test", "d001")[0], 0)
                Path("solutions/d001.py").write_text("print(f\"Hello, {input().strip()}!\")\n", encoding="utf-8")
                self.assertEqual(self.run_cli("test", "d001")[0], 0)
                rc, out = self.run_cli("today")
                self.assertEqual(rc, 0)
                self.assertIn("d002", out)
                # 沒做完必做練習不能開檢核
                rc, out = self.run_cli("gate")
                self.assertEqual(rc, 2)
                self.assertIn("d002", out)
                # import 抓範例
                Path("p.txt").write_text("題目\nSample Input\n1 2\nSample Output\n3\n", encoding="utf-8")
                self.assertEqual(self.run_cli("import", "uva99999", "p.txt")[0], 0)
                self.assertTrue(Path("tests/uva99999/sample01.in").exists())
                # 跳關
                self.assertEqual(self.run_cli("course", "goto", "30")[0], 0)
                self.assertIn("單元 30", self.run_cli("course")[1])
                self.assertEqual(self.run_cli("course", "list")[0], 0)
            finally:
                os.chdir(old)


class StatsTests(unittest.TestCase):
    def test_summary(self):
        tmp, ws, clock = make_ws()
        with tmp:
            ws.log("test", problem="a", verdict="AC", review_attempt=True, clean=True)
            ws.log("test", problem="a", verdict="WA", review_attempt=True, clean=True)
            ws.log("hint", problem="a", level=2)
            s = stats.summarize(ws.state(), ws.events(), clock.t)
            self.assertEqual((s["review_attempts"], s["review_clean_passes"]), (2, 1))
            self.assertEqual(s["hints_by_level"], {2: 1})
            self.assertEqual(s["streak"], 1)


if __name__ == "__main__":
    unittest.main()
