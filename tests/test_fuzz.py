"""範例變異對拍。"""
import contextlib
import io
import os
import random
import tempfile
import unittest
from pathlib import Path

from cpe_coach import cli, fuzz
from cpe_coach.store import Workspace

# 題目：第一行 n，第二行 n 個整數，輸出有幾種不同的數字。範例 3 / 1 1 2 → 2。
GOOD = "n = int(input())\nprint(len(set(input().split())))\n"
BUGGY = "n = int(input())\na = input().split()\nprint(1 + sum(1 for i in range(1, n) if a[i] != a[i-1]))\n"   # 只算相鄰不同：範例是排序好的所以會過
BRUTE = "n = int(input())\na = input().split()\nr = []\nfor x in a:\n    if x not in r:\n        r.append(x)\nprint(len(r))\n"


def make_ws():
    tmp = tempfile.TemporaryDirectory()
    ws = Workspace.create(Path(tmp.name), "2026-11-01")
    d = ws.tests / "p"
    d.mkdir(parents=True)
    (d / "sample01.in").write_text("3\n1 1 2\n", encoding="utf-8")
    (d / "sample01.out").write_text("2\n", encoding="utf-8")
    (d / "sample02.in").write_text("5\n7 7 7 8 9\n", encoding="utf-8")
    (d / "sample02.out").write_text("3\n", encoding="utf-8")
    for name, code in (("good", GOOD), ("buggy", BUGGY), ("brute", BRUTE)):
        (ws.root / f"{name}.py").write_text(code, encoding="utf-8")
    return tmp, ws


class HelperTests(unittest.TestCase):
    def test_structural_tokens_are_never_mutated(self):
        lines = fuzz.parse("3\n1 5 2\n")
        self.assertEqual(fuzz.structural(lines), {(0, 0)})                   # 3 = 下一行有 3 個數
        graph = fuzz.parse("4 3\n1 2\n2 3\n3 4\n")
        self.assertIn((0, 1), fuzz.structural(graph))                        # m = 後面有 3 行
        rng = random.Random(0)
        fixed, ranges = fuzz.structural(lines), fuzz._groups(lines)
        for _ in range(200):
            out = fuzz.mutate(lines, rng, fixed, ranges)
            self.assertEqual(out[0], ["3"])
            self.assertEqual(len(out[1]), 3)

    def test_mutation_stays_inside_observed_range(self):
        lines = fuzz.parse("3\n10 20 15\n")
        rng = random.Random(1)
        fixed, ranges = fuzz.structural(lines), fuzz._groups(lines)
        for _ in range(300):
            vals = [int(t) for t in fuzz.mutate(lines, rng, fixed, ranges)[1]]
            self.assertTrue(all(10 <= v <= 20 for v in vals), vals)

    def test_edge_columns_use_their_own_ranges(self):
        lines = fuzz.parse("4 3\n1 2 100\n2 3 5\n3 4 7\n")
        ranges = fuzz._groups(lines)
        self.assertEqual(ranges[(1, 0)], (1, 3))                             # u 欄 1..3
        self.assertEqual(ranges[(2, 2)], (5, 100))                           # 權重欄 5..100
        rng = random.Random(2)
        fixed = fuzz.structural(lines)
        for _ in range(300):
            out = fuzz.mutate(lines, rng, fixed, ranges)
            self.assertTrue(all(1 <= int(r[0]) <= 3 for r in out[1:] if r))       # 節點編號不會跑到權重的範圍

    def test_render_roundtrip(self):
        self.assertEqual(fuzz.render(fuzz.parse("3\n1 2  3\n\n\n")), "3\n1 2 3\n")


class FuzzTests(unittest.TestCase):
    def test_finds_bug_that_samples_miss_and_shrinks_it(self):
        tmp, ws = make_ws()
        with tmp:
            r = fuzz.fuzz(ws.root / "buggy.py", ws.root / "brute.py", ws.tests / "p", rounds=300, seed=3)
            self.assertTrue(r["found"], r)
            f = r["found"][0]
            self.assertEqual(f["verdict"], "WA")
            self.assertEqual(f["input"].split("\n")[0], "3" if len(f["input"].split("\n")[1].split()) == 3 else "5")   # 結構沒被破壞
            names = fuzz.save(ws, "p", r["found"])
            self.assertEqual(names[0], "fuzz01")
            self.assertTrue((ws.tests / "p" / "fuzz01.in").exists())
            from cpe_coach.judge import judge
            self.assertEqual(judge(ws.root / "buggy.py", ws.tests / "p").verdict, "WA")      # 存下來的測資會讓壞解答現形
            self.assertEqual(judge(ws.root / "good.py", ws.tests / "p").verdict, "AC")       # 好解答不受影響（預期輸出來自暴力解）

    def test_correct_solution_has_no_findings(self):
        tmp, ws = make_ws()
        with tmp:
            r = fuzz.fuzz(ws.root / "good.py", ws.root / "brute.py", ws.tests / "p", rounds=120, seed=5)
            self.assertEqual(r["found"], [])
            self.assertGreater(r["tried"], 20)

    def test_brute_must_pass_existing_tests_first(self):
        tmp, ws = make_ws()
        with tmp:
            (ws.root / "wrong_brute.py").write_text("print(0)\n", encoding="utf-8")
            with self.assertRaises(fuzz.FuzzError) as cm:
                fuzz.fuzz(ws.root / "good.py", ws.root / "wrong_brute.py", ws.tests / "p")
            self.assertIn("沒有通過現有測資", str(cm.exception))

    def test_no_seed_tests_is_an_error(self):
        tmp, ws = make_ws()
        with tmp:
            with self.assertRaises(fuzz.FuzzError):
                fuzz.fuzz(ws.root / "good.py", ws.root / "brute.py", ws.tests / "nope")

    def test_runtime_error_and_tle_are_reported(self):
        tmp, ws = make_ws()
        with tmp:
            (ws.root / "crash.py").write_text("n = int(input())\na = input().split()\nif len(set(a)) == 1:\n    raise SystemExit(3)\nprint(len(set(a)))\n", encoding="utf-8")
            r = fuzz.fuzz(ws.root / "crash.py", ws.root / "brute.py", ws.tests / "p", rounds=300, seed=2, max_found=1)
            self.assertTrue(r["found"])
            self.assertEqual(r["found"][0]["verdict"], "RE")

    def test_save_numbers_do_not_collide(self):
        tmp, ws = make_ws()
        with tmp:
            f = [{"input": "1\n1\n", "brute_out": "1"}, {"input": "2\n1 2\n", "brute_out": "2\n"}]
            self.assertEqual(fuzz.save(ws, "p", f), ["fuzz01", "fuzz02"])
            self.assertEqual(fuzz.save(ws, "p", f), ["fuzz03", "fuzz04"])
            self.assertEqual((ws.tests / "p" / "fuzz01.out").read_text(encoding="utf-8"), "1\n")


class CliTests(unittest.TestCase):
    def test_fuzz_command(self):
        tmp, ws = make_ws()
        with tmp:
            (ws.solutions).mkdir(exist_ok=True)
            (ws.solutions / "p.py").write_text(BUGGY, encoding="utf-8")
            old = os.getcwd()
            os.chdir(ws.root)
            try:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = cli.main(["fuzz", "p", "--brute", "brute.py", "-n", "300", "--seed", "3", "--save"])
                self.assertEqual(rc, 1)
                self.assertIn("已存成 tests/p/fuzz01", buf.getvalue())
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = cli.main(["test", "p"])
                self.assertNotEqual(rc, 0)                                       # 現在 cpe test 抓得到這個 bug
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main()
