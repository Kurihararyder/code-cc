"""診斷工具：反例縮小、複雜度實測、演算法簽名、編輯行為、筆記與自我解釋評分。"""
import contextlib
import io
import math
import os
import random
import tempfile
import unittest
from pathlib import Path

from cpe_coach import behavior, cli, notes, service, tools
from cpe_coach.store import Workspace


def make_ws():
    tmp = tempfile.TemporaryDirectory()
    return tmp, Workspace.create(Path(tmp.name), "2026-11-01")


class DdminTests(unittest.TestCase):
    def test_finds_a_single_culprit_and_a_pair(self):
        calls = []

        def one(xs):
            calls.append(1)
            return 7 in xs
        self.assertEqual(tools.ddmin(list(range(50)), one), [7])
        self.assertEqual(sorted(tools.ddmin(list(range(30)), lambda xs: 3 in xs and 20 in xs)), [3, 20])
        self.assertEqual(tools.ddmin([1, 2, 3], lambda xs: True), [1])           # 什麼都會失敗：縮到最小
        self.assertEqual(tools.ddmin([5], lambda xs: True), [5])

    def test_budget_is_respected(self):
        n = []

        def f(xs):
            n.append(1)
            return len(xs) > 1
        tools.ddmin(list(range(200)), f, budget=15)
        self.assertLessEqual(len(n), 15)

    def test_minimize_input_removes_lines_tokens_and_shrinks_numbers(self):
        text = "5\n1 2 3 4 5\n99 98\n13 7 8\nhello\n"
        small = tools.minimize_input(text, lambda t: "13" in t.split())
        self.assertIn("13", small.split())
        self.assertLess(len(small), len(text))
        self.assertEqual(tools.minimize_input("1 2\n", lambda t: False), "1 2\n")          # 本來就不失敗：原樣回傳
        big = tools.minimize_input("1000000 5\n", lambda t: int(t.split()[0]) >= 1)
        self.assertEqual(big.split()[0], "1")


class ShrinkTests(unittest.TestCase):
    def test_runtime_error_is_shrunk_with_the_same_error_class(self):
        tmp, ws = make_ws()
        with tmp:
            sol = Path(tmp.name) / "s.py"
            sol.write_text("a = list(map(int, input().split()))\nprint(a[2])\n", encoding="utf-8")
            r = tools.shrink_failure(sol, "9 9\n1 2\n3 4\n", None, timeout=5)
            self.assertEqual((r["kind"], r["error"]), ("RE", "IndexError"))
            self.assertLess(r["minimal_size"], r["original_size"])
            self.assertLessEqual(len(r["minimal"].split()), 2)

    def test_wrong_answer_needs_a_brute_force_reference(self):
        tmp, ws = make_ws()
        with tmp:
            sol = Path(tmp.name) / "s.py"
            brute = Path(tmp.name) / "b.py"
            sol.write_text("import sys\nxs = [int(t) for t in sys.stdin.read().split()]\nprint(sum(x for x in xs if x != 13))\n", encoding="utf-8")
            brute.write_text("import sys\nprint(sum(int(t) for t in sys.stdin.read().split()))\n", encoding="utf-8")
            text = "4 5\n13 8\n9\n"
            with self.assertRaises(ValueError):
                tools.shrink_failure(sol, text, None, timeout=5)
            r = tools.shrink_failure(sol, text, brute, timeout=5)
            self.assertEqual(r["kind"], "WA")
            self.assertEqual(r["minimal"].split(), ["13"])
            with self.assertRaises(ValueError):
                tools.shrink_failure(sol, "1 2\n", brute, timeout=5)                    # 這個輸入沒有出錯

    def test_timeout_is_shrunk_too(self):
        tmp, ws = make_ws()
        with tmp:
            sol = Path(tmp.name) / "s.py"
            sol.write_text("n = int(input())\nwhile n > 5:\n    pass\n", encoding="utf-8")
            r = tools.shrink_failure(sol, "100\nextra\n", None, timeout=0.6, budget=30)
            self.assertEqual(r["kind"], "TLE")
            self.assertLess(r["minimal_size"], r["original_size"])


class ComplexityTests(unittest.TestCase):
    def synth(self, f, noise=0.03, seed=1):
        rng = random.Random(seed)
        return [(n, 0.0004 * f(n) * (1 + rng.uniform(-noise, noise))) for n in (500, 1000, 2000, 4000, 8000)]

    def test_fit_picks_the_generating_model(self):
        for name, f in tools.MODELS:
            if name in ("O(1)", "O(log n)"):
                continue
            r = tools.fit_complexity(self.synth(f))
            self.assertEqual(r["best"], name, (name, r))
        lin = tools.fit_complexity(self.synth(lambda n: n))
        quad = tools.fit_complexity(self.synth(lambda n: n * n))
        self.assertAlmostEqual(lin["slope"], 1.0, delta=0.15)
        self.assertAlmostEqual(quad["slope"], 2.0, delta=0.15)
        self.assertTrue(quad["confident"])

    def test_constant_time(self):
        r = tools.fit_complexity([(n, 0.05) for n in (500, 1000, 2000, 4000)], baseline=0.0)
        self.assertEqual(r["best"], "O(1)")

    def test_auto_input_understands_common_shapes_and_refuses_the_rest(self):
        rng = random.Random(1)
        one_line = tools.auto_input("3\n5 1 9\n", 7, rng)
        self.assertEqual(one_line.split("\n")[0], "7")
        self.assertEqual(len(one_line.split("\n")[1].split()), 7)
        rows = tools.auto_input("2\n1 2\n3 4\n", 5, rng)
        self.assertEqual(len(rows.strip().split("\n")), 6)
        self.assertIsNone(tools.auto_input("hello world\n", 5, rng))
        self.assertIsNone(tools.auto_input("3\n1 2\n", 5, rng))                        # n 和資料筆數對不上
        self.assertIsNone(tools.auto_input("", 5, rng))

    def test_estimate_for_n_max(self):
        self.assertIn("逾時", tools.estimate_for_n_max("O(n²)", 10 ** 6))
        self.assertIn("來得及", tools.estimate_for_n_max("O(n)", 10 ** 5))
        self.assertIsNone(tools.estimate_for_n_max("O(??)", 10))

    def test_measurement_separates_linear_from_quadratic(self):
        tmp, ws = make_ws()
        with tmp:
            lin = Path(tmp.name) / "lin.py"
            quad = Path(tmp.name) / "quad.py"
            lin.write_text("n = int(input())\na = list(map(int, input().split()))\nprint(sum(a))\n", encoding="utf-8")
            quad.write_text("n = int(input())\na = list(map(int, input().split()))\nc = 0\nfor i in a:\n    for j in a:\n        c += 1\nprint(c)\n", encoding="utf-8")
            rng = random.Random(1)

            def make(n):
                return tools.auto_input("3\n5 1 9\n", n, rng)
            rl = tools.measure_complexity(lin, make, [20000, 40000, 80000, 160000], repeat=2)
            rq = tools.measure_complexity(quad, make, [300, 600, 1200, 2400], repeat=2)
            self.assertGreater(rq["slope"], rl["slope"] + 0.4, (rl, rq))
            self.assertIn(rq["best"], ("O(n²)", "O(n³)"))
        self.assertTrue(rl["points"])
        self.assertTrue(math.isfinite(rq["slope"]))

    def test_unreadable_input_shape_is_a_clear_error(self):
        tmp, ws = make_ws()
        with tmp:
            sol = Path(tmp.name) / "s.py"
            sol.write_text("print(1)\n", encoding="utf-8")
            with self.assertRaises(ValueError) as cm:
                tools.measure_complexity(sol, lambda n: None, [10, 20])
            self.assertIn("--gen", str(cm.exception))


class SignatureTests(unittest.TestCase):
    def test_labels(self):
        self.assertIn("排序", tools.signature("a=sorted(map(int,input().split()))\nprint(a[0])")["labels"])
        self.assertIn("堆", tools.signature("import heapq\nh=[]\nheapq.heappush(h,1)\n")["labels"])
        self.assertIn("遞迴", tools.signature("def f(n):\n    return f(n-1) if n else 0\nf(3)\n")["labels"])
        self.assertIn("二分", tools.signature("import bisect\nbisect.bisect_left([1],1)\n")["labels"])
        self.assertIn("動態規劃", tools.signature("dp=[0]*10\nfor i in range(1,10):\n    dp[i]=max(dp[i-1],1)\n")["labels"])
        self.assertIn("位元運算", tools.signature("x=1<<3\n")["labels"])
        self.assertIn("佇列／stack", tools.signature("from collections import deque\nq=deque()\nq.popleft\n")["labels"])
        self.assertIn("雜湊", tools.signature("from collections import Counter\nc=Counter()\n")["labels"])

    def test_brute_force_detection_and_comparison(self):
        s = tools.signature("from itertools import permutations\nfor p in permutations(range(5)):\n    pass\n")
        self.assertTrue(s["brute_force"])
        deep = tools.signature("for i in range(3):\n for j in range(3):\n  for k in range(3):\n   pass\n")
        self.assertTrue(deep["brute_force"] and deep["depth"] == 3)
        cmp_ = tools.compare_with_expected(deep, ["dp"])
        self.assertIn("暴力", cmp_["verdict"])
        ok = tools.compare_with_expected(tools.signature("import heapq\nheapq.heappush([],1)\n"), ["shortest"])
        self.assertIn("相符", ok["verdict"])
        self.assertEqual(tools.signature("def (:")["notes"], ["語法錯誤，無法分析"])
        self.assertIn("沒有可對照", tools.compare_with_expected(deep, ["io"])["verdict"])


class BehaviorTests(unittest.TestCase):
    def test_clean_keeps_only_bounded_numbers(self):
        c = behavior.clean({"edits": 5, "deletes": "x", "pastes": True, "secret_code": "print(1)", "active_s": -3, "runs": 2})
        self.assertEqual(c, {"edits": 5.0, "runs": 2.0})
        self.assertEqual(behavior.clean("nope"), {})
        self.assertEqual(behavior.clean({"edits": 1e12}), {})

    def test_patterns(self):
        ids = lambda b, f: {p["id"] for p in behavior.patterns(b, f)}      # noqa: E731
        self.assertIn("thrash", ids({"edits": 100, "deletes": 60}, 3))
        self.assertNotIn("thrash", ids({"edits": 100, "deletes": 60}, 0))
        self.assertIn("stuck-reading", ids({"max_pause_s": 400, "edits": 5}, 0))
        self.assertIn("guess-and-run", ids({"runs": 8, "edits": 30}, 6))
        self.assertIn("pasted", ids({"pastes": 1, "edits": 3, "since_open_s": 30}, 0))
        self.assertIn("idle-open", ids({"since_open_s": 7200, "active_s": 20}, 0))
        self.assertEqual(ids({"edits": 20, "deletes": 2, "runs": 1, "since_open_s": 600, "active_s": 400}, 0), set())

    def test_summary_counts_patterns_from_events(self):
        evs = [{"kind": "beh", "edits": 100, "deletes": 60, "failed_runs": 3}, {"kind": "beh", "edits": 100, "deletes": 60, "failed_runs": 3}, {"kind": "test"}]
        s = behavior.summary(evs)
        self.assertEqual((s["samples"], s["patterns"][0]), (2, {"id": "thrash", "count": 2}))


class NotesTests(unittest.TestCase):
    def test_add_list_and_last_outline(self):
        tmp, ws = make_ws()
        with tmp:
            with self.assertRaises(ValueError):
                notes.add(ws, "bogus", "x")
            with self.assertRaises(ValueError):
                notes.add(ws, "think", "   ")
            notes.add(ws, "think", "先排序再雙指標", "d001")
            notes.add(ws, "recall", "用 BFS", "d001")
            notes.add(ws, "reflect", "今天太累")
            self.assertEqual(len(notes.listing(ws)), 3)
            self.assertEqual(len(notes.listing(ws, "reflect")), 1)
            self.assertEqual(notes.last_outline(ws, "d001")["text"], "用 BFS")
            self.assertIsNone(notes.last_outline(ws, "d999"))
            self.assertEqual(len(notes.add(ws, "think", "x" * 9000)["text"]), notes.MAX_LEN)

    def test_offline_score_rewards_coverage_and_punishes_short_answers(self):
        insight = "用 BFS 從起點出發，第一次到達終點的距離就是最短路；要用 visited 避免重複走。"
        good = notes.score_offline("我用 BFS 從起點開始一層一層擴張，第一次碰到終點時的距離就是最短路，並用 visited 記錄走過的點避免重複。", insight)
        weak = notes.score_offline("暴力枚舉所有排列然後取最小值，因為資料不大所以可以。", insight)
        short = notes.score_offline("BFS", insight)
        self.assertGreater(good["score"], weak["score"])
        self.assertGreater(good["score"], 0.5)
        self.assertLess(short["score"], good["score"])
        self.assertIn("太短", short["message"])
        self.assertIn("bfs", good["hit"])

    def test_ai_score_parses_json_and_rejects_garbage(self):
        class Fake:
            def __init__(self, reply):
                self.reply = reply

            def complete(self, system, user):
                self.system, self.user = system, user
                return self.reply
        ok = notes.score_with_ai(Fake('好的 {"score": 0.8, "good": ["BFS"], "missing": ["visited"], "message": "不錯"}'), "我用 BFS", "BFS 最短路 visited", "題目")
        self.assertEqual((ok["mode"], ok["score"], ok["missed"]), ("ai", 0.8, ["visited"]))
        for bad in ("沒有 json", '{"score": 5}', '{"score": "x"}'):
            with self.assertRaises((ValueError, KeyError)):
                notes.score_with_ai(Fake(bad), "a", "b")
        f = Fake('{"score": 0.5, "good": [], "missing": [], "message": ""}')
        notes.score_with_ai(f, "答案", "洞察", "題目文字")
        self.assertIn("不要給完整解答", f.system)
        self.assertIn("洞察", f.user)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = cli.main(list(args))
        return rc, buf.getvalue()

    def test_commands_end_to_end(self):
        tmp, ws = make_ws()
        with tmp:
            old = os.getcwd()
            os.chdir(ws.root)
            try:
                self.assertEqual(self.run_cli("new", "d001")[0], 0)
                sol = service.solution_file(ws, "d001")
                sol.write_text("x = input().split()[5]\nprint(x)\n", encoding="utf-8")
                self.assertNotEqual(self.run_cli("test", "d001")[0], 0)
                rc, out = self.run_cli("shrink", "d001")
                self.assertEqual(rc, 0, out)
                self.assertIn("IndexError", out)
                self.assertIn("最小的失敗輸入", out)
                rc, out = self.run_cli("shrink", "d001", "--save")
                self.assertTrue(list((ws.tests / "d001").glob("shrink*.in")))
                rc, out = self.run_cli("algo", "d001")
                self.assertEqual(rc, 0)
                self.assertIn("你的解法看起來", out)
                rc, out = self.run_cli("note", "add", "reflect", "今天的想法", "--problem", "d001")
                self.assertIn("已記下", out)
                self.assertIn("今天的想法", self.run_cli("note")[1])
                rc, out = self.run_cli("recall", "d001")
                self.assertIn("先不要看程式碼", out)
                rc, out = self.run_cli("recall", "d001", "輸入一個名字然後印出打招呼的字串，用 input 與 f-string")
                self.assertIn("已記下", out)
                rc, out = self.run_cli("recall", "d001", "第二次的大綱")
                self.assertIn("上次", out)
                self.assertNotEqual(self.run_cli("explain", "nosuchproblem", "文字")[0], 0)
                rc, out = self.run_cli("explain", "d001", "先讀入名字，再用格式化字串把名字放進打招呼的句子裡輸出。", "--offline")
                self.assertIn("離線", out)
                self.assertTrue(notes.listing(ws, "explain", "d001"))
                self.assertNotEqual(self.run_cli("complexity", "d001")[0], 0)               # d001 的輸入不是可放大的結構：要求 --gen
            finally:
                os.chdir(old)

    def test_api_test_logs_behavior_and_returns_patterns(self):
        import socket
        import threading
        import json
        import urllib.request
        from cpe_coach import web
        tmp, ws = make_ws()
        with tmp:
            s = socket.socket()
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
            s.close()
            app = web.App(Path(tmp.name), port)
            httpd = web.LocalServer(("127.0.0.1", port), web.make_handler(app))
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            try:
                def post(path, body):
                    r = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=json.dumps(body).encode(), method="POST",
                                               headers={"Host": f"127.0.0.1:{port}", "X-CPE-Token": app.token, "Content-Type": "application/json"})
                    with urllib.request.urlopen(r) as resp:
                        return json.loads(resp.read())
                post("/api/new", {"id": "d001"})
                beh = {"edits": 120, "deletes": 70, "pastes": 0, "active_s": 100, "max_pause_s": 20, "since_open_s": 600, "runs": 3, "evil": "x"}
                for _ in range(2):
                    r = post("/api/test", {"id": "d001", "code": "print(1)\n", "beh": beh})
                self.assertEqual(r["verdict"], "WA")
                self.assertIn("thrash", {b["id"] for b in r["behavior"]})
                self.assertTrue(r["cause"])
                logged = [e for e in ws.events() if e["kind"] == "beh"]
                self.assertEqual(len(logged), 2)
                self.assertNotIn("evil", logged[0])
                r = post("/api/test", {"id": "d001", "code": "print(1)\n"})                # 沒送行為資料：沒有提示也不出錯
                self.assertEqual(r["behavior"], [])
            finally:
                httpd.shutdown()
                httpd.server_close()


if __name__ == "__main__":
    unittest.main()
