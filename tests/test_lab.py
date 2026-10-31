"""學習工坊：內容資料用「實際執行」驗證（不信任手寫的答案），以及測驗／診斷／排序題／找錯等邏輯。"""
import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cpe_coach import cli, concepts, lab
from cpe_coach.judge import run_program
from cpe_coach.store import Workspace


def run_code(code, stdin=""):
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "p.py"
        f.write_text(code + "\n", encoding="utf-8")
        r = run_program(f, stdin, 20.0)
        return r._replace(out=r.out.replace("\r\n", "\n"))                    # Windows 的標準輸出換行是 \r\n


class ContentIntegrityTests(unittest.TestCase):
    """資料檔裡每一個答案、輸出、bug 都重新執行一次確認（資料被手改壞了這裡會抓到）。"""

    def test_quiz_answers_match_real_output(self):
        qs = lab.items("quiz")
        self.assertGreaterEqual(len(qs), 40)
        self.assertEqual(len({q["id"] for q in qs}), len(qs))
        self.assertEqual({q["concept"] for q in qs}, set(concepts.load()))                    # 每個知識點都至少有一題
        for q in qs:
            self.assertTrue(0 <= q["answer"] < len(q["choices"]) and len(set(q["choices"])) == len(q["choices"]), q["id"])
            self.assertTrue(q["why"], q["id"])
            self.assertTrue(-2.5 <= q["b"] <= 2.5, q["id"])
            if q["code"]:
                r = run_code(q["code"], q["stdin"] or "")
                self.assertEqual(r.rc, 0, q["id"])
                self.assertEqual(r.out.strip(), q["choices"][q["answer"]].strip(), q["id"])
                self.assertEqual(sum(c.strip() == r.out.strip() for c in q["choices"]), 1, q["id"])

    def test_worked_examples_solve_their_own_tests(self):
        for w in lab.items("worked"):
            self.assertIn(w["concept"], concepts.load())
            code = "\n".join(s["code"] for s in w["steps"])
            self.assertTrue(lab.run_tests(code, w["tests"])["ok"], w["id"])
            self.assertGreaterEqual(len(w["steps"]), 3 if w["id"] != "w-gcd" else 3, w["id"])
            self.assertTrue(all(s["say"] and s["code"] for s in w["steps"]), w["id"])

    def test_every_bug_really_fails_and_the_fix_passes(self):
        bugs = lab.items("bugs")
        self.assertGreaterEqual(len(bugs), 12)
        for b in bugs:
            self.assertTrue(lab.run_tests(b["fixed"], b["tests"])["ok"], b["id"])
            self.assertFalse(lab.run_tests(b["buggy"], b["tests"])["ok"], b["id"])
            bl, fl = b["buggy"].split("\n"), b["fixed"].split("\n")
            changed = {i + 1 for i in range(max(len(bl), len(fl))) if (bl[i] if i < len(bl) else None) != (fl[i] if i < len(fl) else None)}
            self.assertTrue(set(b["bug_lines"]) & changed, b["id"])

    def test_predictions_and_lessons_and_compare(self):
        for p in lab.items("predict"):
            self.assertEqual(run_code(p["code"], p["stdin"]).out.rstrip("\n"), p["output"], p["id"])
        qids = {q["id"] for q in lab.items("quiz")}
        for les in lab.items("lessons"):
            self.assertEqual(run_code(les["code"]).out.rstrip("\n"), les["output"], les["concept"])
            self.assertTrue(set(les["quiz"]) <= qids and les["points"] and les["pitfall"])
        self.assertEqual({x["concept"] for x in lab.items("lessons")}, set(concepts.load()))
        for c in lab.items("compare"):
            self.assertGreaterEqual(len(c["approaches"]), 2)
            for a in c["approaches"]:
                self.assertTrue(lab.run_tests(a["code"], c["tests"])["ok"], (c["id"], a["name"]))

    def test_glossary_has_no_duplicates_and_is_searchable(self):
        g = lab.items("glossary")
        self.assertGreaterEqual(len(g), 80)
        self.assertEqual(len({x["en"] for x in g}), len(g))
        self.assertEqual(lab.search_glossary("subsequence")[0]["zh"], "子序列")
        self.assertTrue(lab.search_glossary("連續"))
        self.assertEqual(lab.search_glossary("zzzzzz"), [])
        self.assertEqual(len(lab.search_glossary("", 5)), 5)


class AdaptiveTests(unittest.TestCase):
    def play(self, correct_if):
        st = lab.cat_new()
        while True:
            q = lab.cat_next(st)
            if q is None:
                break
            full = lab.by_id("quiz", "id", q["id"])
            pick = full["answer"] if correct_if(full) else (full["answer"] + 1) % len(full["choices"])
            lab.cat_answer(st, q["id"], pick)
            if st["done"]:
                break
        return st

    def test_strong_learner_gets_higher_ability_than_weak_one(self):
        strong = self.play(lambda q: True)
        weak = self.play(lambda q: False)
        mid = self.play(lambda q: q["b"] < 0.3)
        self.assertGreater(strong["theta"], mid["theta"])
        self.assertGreater(mid["theta"], weak["theta"])
        self.assertLessEqual(len(strong["asked"]), lab.MAX_Q)
        self.assertGreaterEqual(len(weak["asked"]), lab.MIN_Q)

    def test_questions_get_harder_after_correct_answers(self):
        st = lab.cat_new()
        bs = []
        for _ in range(5):
            q = lab.cat_next(st)
            full = lab.by_id("quiz", "id", q["id"])
            bs.append(full["b"])
            lab.cat_answer(st, q["id"], full["answer"])
        self.assertGreater(bs[-1], bs[0])

    def test_no_question_repeats_and_double_answer_is_rejected(self):
        st = lab.cat_new()
        q = lab.cat_next(st)
        lab.cat_answer(st, q["id"], 0)
        with self.assertRaises(ValueError):
            lab.cat_answer(st, q["id"], 0)
        with self.assertRaises(ValueError):
            lab.cat_answer(st, lab.cat_next(st)["id"], 9)
        seen = {q["id"]}
        for _ in range(11):
            if st["done"]:
                break
            n = lab.cat_next(st)
            self.assertNotIn(n["id"], seen)
            seen.add(n["id"])
            lab.cat_answer(st, n["id"], 0)

    def test_result_recommends_a_start_unit_from_the_first_miss(self):
        st = self.play(lambda q: concepts.load()[q["concept"]]["unit"] < 17)
        res = lab.cat_result(st)
        self.assertTrue(res["weak"])
        self.assertEqual(res["start_unit"], res["weak"][0]["unit"])
        self.assertIn("大略", res["caveat"])
        allright = lab.cat_result(self.play(lambda q: True))
        self.assertEqual(allright["weak"], [])
        self.assertGreaterEqual(allright["start_unit"], 1)
        self.assertEqual(lab.cat_result(lab.cat_new())["start_unit"], 1)

    def test_practice_and_grade(self):
        qs = lab.practice("graph", 5, seed=1)
        self.assertTrue(qs and all(q["concept"] == "graph" for q in qs))
        self.assertNotIn("answer", qs[0])
        q = lab.by_id("quiz", "id", qs[0]["id"])
        self.assertTrue(lab.grade(q["id"], q["answer"])["correct"])
        self.assertFalse(lab.grade(q["id"], (q["answer"] + 1) % 4)["correct"])
        with self.assertRaises(ValueError):
            lab.by_id("quiz", "id", "nope")


class ExerciseTests(unittest.TestCase):
    def test_run_tests_reports_wrong_crash_and_timeout(self):
        t = [{"in": "2\n", "out": "4\n"}]
        self.assertTrue(lab.run_tests("print(int(input()) * 2)", t)["ok"])
        r = lab.run_tests("print(int(input()) + 1)", t)
        self.assertFalse(r["ok"])
        self.assertEqual((r["results"][0]["expected"], r["results"][0]["got"]), ("4", "3"))
        self.assertIn("ValueError", lab.run_tests("int('x')", t)["results"][0]["error"])
        self.assertEqual(lab.run_tests("while True: pass", t, timeout=0.5)["results"][0]["error"], "逾時")
        self.assertTrue(lab.run_tests("print(4)   ", t)["ok"])                       # 行尾空白不影響

    def test_faded_levels_blank_more_steps_and_checking_runs_the_tests(self):
        w = lab.by_id("worked", "id", "w-sum")
        f0, f1, f2 = lab.faded(w, 0), lab.faded(w, 1), lab.faded(w, 2)
        self.assertEqual((len(f0["given"]), len(f1["given"]), len(f2["given"])), (3, 2, 1))
        self.assertEqual(lab.faded(w, 99)["level"], 2)
        self.assertEqual(f1["blank"][0]["say"], w["steps"][-1]["say"])
        good = lab.check_faded(w, 1, "print(sum(a))")
        self.assertTrue(good["ok"] and good["solution"] is None)
        bad = lab.check_faded(w, 1, "print(max(a))")
        self.assertFalse(bad["ok"])
        self.assertIn("print(sum(a))", bad["solution"])

    def test_parsons_shuffles_includes_distractors_and_checks_by_running(self):
        w = lab.by_id("worked", "id", "w-sum")
        p = lab.parsons(w, seed=3)
        real = [ln for s in w["steps"] for ln in s["code"].split("\n") if ln.strip()]
        self.assertEqual(sorted(x["text"] for x in p["lines"]), sorted(real + w["distractors"]))
        self.assertEqual(p, lab.parsons(w, seed=3) | {})                              # 同一個 seed 結果一樣
        text_to_id = {x["text"]: x["id"] for x in p["lines"]}
        order = [text_to_id[t] for t in real]
        r = lab.check_parsons(w, 3, order)
        self.assertTrue(r["ok"] and r["exact"])
        self.assertFalse(lab.check_parsons(w, 3, list(reversed(order)))["ok"])
        with_distractor = lab.check_parsons(w, 3, order + [text_to_id[w["distractors"][0]]])
        self.assertFalse(with_distractor["exact"])
        for bad in ([99], [order[0], order[0]], [-1]):
            with self.assertRaises(ValueError):
                lab.check_parsons(w, 3, bad)

    def test_parsons_keeps_indentation_for_nested_code(self):
        w = lab.by_id("worked", "id", "w-bfs-grid")
        p = lab.parsons(w, seed=1)
        self.assertTrue(any(x["text"].startswith("        ") for x in p["lines"]))     # 縮排是排序題的一部分
        real = [ln for s in w["steps"] for ln in s["code"].split("\n") if ln.strip()]
        ids = {x["text"]: x["id"] for x in p["lines"]}
        self.assertTrue(lab.check_parsons(w, 1, [ids[t] for t in real])["ok"])

    def test_bug_hunt_and_prediction(self):
        b = lab.by_id("bugs", "id", "b-range")
        self.assertTrue(lab.check_bug(b, 3)["found"])
        self.assertFalse(lab.check_bug(b, 1)["found"])
        r = lab.check_bug(b, 3, b["fixed"])
        self.assertTrue(r["fix"]["ok"])
        self.assertFalse(lab.check_bug(b, 3, b["buggy"])["fix"]["ok"])
        p = lab.by_id("predict", "id", "p-float")
        self.assertTrue(lab.check_predict(p, " 0.30000000000000004 \n")["correct"])
        self.assertFalse(lab.check_predict(p, "0.3")["correct"])
        self.assertTrue(lab.check_predict(lab.by_id("predict", "id", "p-slice"), "[]   [2, 3]  [1, 3]")["correct"])


class CliTests(unittest.TestCase):
    def run_cli(self, *args, answers=()):
        buf = io.StringIO()
        it = iter(answers)
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf), mock.patch("builtins.input", lambda prompt="": next(it)):
            rc = cli.main(list(args))
        return rc, buf.getvalue()

    def test_study_commands(self):
        tmp = tempfile.TemporaryDirectory()
        with tmp:
            ws = Workspace.create(Path(tmp.name), "2026-11-01")
            old = os.getcwd()
            os.chdir(ws.root)
            try:
                self.assertIn("w-sum", self.run_cli("study", "list")[1])
                self.assertIn("子序列", self.run_cli("study", "glossary", "subsequence")[1])
                self.assertIn("常見陷阱", self.run_cli("study", "lesson", "graph")[1])
                self.assertNotEqual(self.run_cli("study", "lesson", "nope")[0], 0)
                self.assertIn("步驟 3", self.run_cli("study", "worked", "w-sum")[1])
                ans = Path(tmp.name) / "a.py"
                ans.write_text("print(sum(a))\n", encoding="utf-8")
                rc, out = self.run_cli("study", "faded", "w-sum", "--level", "1", "--answer", str(ans))
                self.assertIn("通過所有測資", out)
                ans.write_text("print(0)\n", encoding="utf-8")
                self.assertIn("還沒通過", self.run_cli("study", "faded", "w-sum", "--answer", str(ans))[1])
                p = lab.parsons(lab.by_id("worked", "id", "w-sum"), 0)
                self.assertIn("[ 0]", self.run_cli("study", "parsons", "w-sum")[1])
                self.assertIn("找到了", self.run_cli("study", "bug", "b-range", "--line", "3")[1])
                self.assertIn("不是這一行", self.run_cli("study", "bug", "b-range", "--line", "1")[1])
                self.assertIn("對了", self.run_cli("study", "predict", "p-float", "--answer", "0.30000000000000004")[1])
                self.assertIn("■", self.run_cli("study", "compare", "c-pairs")[1])
                self.assertEqual(len(p["lines"]), len(lab.parsons(lab.by_id("worked", "id", "w-sum"), 0)["lines"]))
            finally:
                os.chdir(old)

    def test_quiz_practice_and_adaptive_flow(self):
        tmp = tempfile.TemporaryDirectory()
        with tmp:
            ws = Workspace.create(Path(tmp.name), "2026-11-01")
            old = os.getcwd()
            os.chdir(ws.root)
            try:
                rc, out = self.run_cli("quiz", "graph", "-n", "2", answers=["A", "B"])
                self.assertEqual(rc, 0)
                self.assertIn("題答對", out)
                rc, out = self.run_cli("quiz", "graph", answers=["q"])
                self.assertEqual(rc, 0)
                rc, out = self.run_cli("quiz", answers=["A"] * 20)
                self.assertEqual(rc, 0, out)
                self.assertIn("適性診斷", out)
                self.assertIn("程度：", out)
                self.assertTrue([e for e in ws.events() if e["kind"] == "quiz"])
                self.assertNotEqual(self.run_cli("quiz", "nope")[0], 0)
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main()
