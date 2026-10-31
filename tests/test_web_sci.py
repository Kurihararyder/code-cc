"""學習洞察與學習工坊的網頁 API：端點行為、不洩漏答案、壞輸入。"""
import datetime as dt
import json
import socket
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from cpe_coach import lab, web
from cpe_coach.store import Workspace


class ApiBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        Workspace.create(Path(cls.tmp.name), "2026-11-01")
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        cls.port = s.getsockname()[1]
        s.close()
        cls.app = web.App(Path(cls.tmp.name), cls.port)
        cls.httpd = web.LocalServer(("127.0.0.1", cls.port), web.make_handler(cls.app))
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.tmp.cleanup()

    def req(self, path, body=None, raw=False):
        h = {"Host": f"127.0.0.1:{self.port}", "X-CPE-Token": self.app.token}
        if body is not None:
            h["Content-Type"] = "application/json"
        r = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=None if body is None else json.dumps(body).encode(), headers=h, method="POST" if body is not None else "GET")
        try:
            with urllib.request.urlopen(r) as resp:
                data = resp.read()
                return resp.status, (data if raw else json.loads(data)), resp.headers
        except urllib.error.HTTPError as e:
            data = e.read()
            return e.code, (data if raw else json.loads(data or b"{}")), e.headers


class InsightsApiTests(ApiBase):
    def test_insights_has_everything_on_a_fresh_workspace(self):
        code, d, _ = self.req("/api/insights")
        self.assertEqual(code, 200)
        for k in ("mastery", "recommend", "memory", "errors", "habits", "fatigue", "goal", "achievements", "week", "month", "prediction", "strategy", "final", "experiment", "reminder", "calibrated"):
            self.assertIn(k, d, k)
        self.assertEqual(len(d["mastery"]), 26)
        self.assertEqual(len(d["memory"]["forecast"]), 14)
        self.assertFalse(d["memory"]["personalized"])
        self.assertTrue(d["recommend"])
        self.assertIn("set", d["goal"])
        json.dumps(d)

    def test_goal_flow_and_validation(self):
        code, d, _ = self.req("/api/goal/set", {"date": "nonsense", "problems": 5})
        self.assertEqual(code, 400)
        date = (dt.date.today() + dt.timedelta(days=45)).isoformat()
        code, d, _ = self.req("/api/goal/set", {"date": date, "problems": 30})
        self.assertEqual((code, d["target"], d["set"]), (200, 30, True))
        self.assertEqual(self.req("/api/insights")[1]["goal"]["target"], 30)

    def test_experiment_toggle(self):
        code, d, _ = self.req("/api/exp", {"on": True})
        self.assertTrue(d["enabled"])
        self.assertFalse(self.req("/api/exp", {"on": False})[1]["enabled"])


class NotesApiTests(ApiBase):
    def test_notes_add_list_and_recall_compares_with_the_insight(self):
        self.assertEqual(self.req("/api/notes/add", {"kind": "bogus", "text": "x"})[0], 400)
        self.assertEqual(self.req("/api/notes/add", {"kind": "think", "text": "x", "problem": "../etc"})[0], 400)
        code, d, _ = self.req("/api/notes/add", {"kind": "reflect", "text": "今天很累"})
        self.assertEqual(code, 200)
        code, d, _ = self.req("/api/notes/add", {"kind": "recall", "text": "用 BFS 從起點一層一層擴張，第一次到終點就是最短路", "problem": "uva10009"})
        self.assertIn("compare", d)
        self.assertIn("insight", d["compare"])
        code, d, _ = self.req("/api/notes?kind=reflect")
        self.assertEqual([n["text"] for n in d["notes"]], ["今天很累"])

    def test_explain_scores_offline_when_there_is_no_key(self):
        code, d, _ = self.req("/api/explain", {"problem": "uva10009", "text": "用 BFS 找最短路徑，並記錄每個城市的上一個城市，最後倒著回溯輸出路徑。", "offline": True})
        self.assertEqual(code, 200)
        self.assertEqual(d["mode"], "offline")
        self.assertEqual(self.req("/api/explain", {"problem": "nosuchproblem", "text": "x" * 40, "offline": True})[0], 400)


class LabApiTests(ApiBase):
    def test_index_and_read_endpoints_do_not_leak_answers(self):
        code, idx, _ = self.req("/api/lab/index")
        self.assertEqual((code, len(idx["concepts"])), (200, 26))
        b = self.req("/api/lab/bug?id=b-range")[1]
        self.assertNotIn("bug_lines", b)
        self.assertNotIn("fixed", b)
        self.assertNotIn("why", b)
        self.assertIn("range(1, n)", b["code"])
        p = self.req("/api/lab/predict?id=p-float")[1]
        self.assertNotIn("output", p)
        w = self.req("/api/lab/worked?id=w-sum&level=1")[1]
        self.assertEqual(len(w["faded"]["given"]), 2)
        ps = self.req("/api/lab/parsons?id=w-sum&seed=2")[1]
        self.assertNotIn("_answer_ids", ps)
        self.assertNotIn("_text", ps)
        self.assertTrue(self.req("/api/lab/lesson?concept=graph")[1]["points"])
        self.assertEqual(self.req("/api/lab/lesson?concept=nope")[0], 400)
        self.assertTrue(self.req("/api/lab/compare?id=c-pairs")[1]["approaches"])
        self.assertEqual(self.req("/api/lab/glossary?q=subsequence")[1]["items"][0]["zh"], "子序列")

    def test_quiz_flow_through_the_api(self):
        code, d, _ = self.req("/api/lab/quiz/start", {})
        state, q = d["state"], d["question"]
        self.assertNotIn("answer", q)
        for _ in range(lab.MAX_Q):
            full = lab.by_id("quiz", "id", q["id"])
            code, r, _ = self.req("/api/lab/quiz/answer", {"state": state, "id": q["id"], "choice": full["answer"]})
            self.assertEqual(code, 200)
            self.assertTrue(r["correct"])
            state = r["state"]
            if r["result"]:
                break
            q = r["question"]
        self.assertTrue(r["result"])
        self.assertGreater(r["result"]["theta"], 0)
        ws = Workspace(Path(self.tmp.name))
        self.assertTrue([e for e in ws.events() if e["kind"] == "quiz" and e.get("items")])
        # 竄改用戶端狀態：能力值會被重算，不存在的題號會被拒絕
        bad = dict(state, theta=99, asked=[{"id": "nope", "concept": "io", "correct": True, "choice": 0}])
        self.assertEqual(self.req("/api/lab/quiz/answer", {"state": bad, "id": "q-io-1", "choice": 0})[0], 400)
        self.assertEqual(self.req("/api/lab/quiz/answer", {"state": "x", "id": "q-io-1", "choice": 0})[0], 400)

    def test_practice_and_grade(self):
        code, d, _ = self.req("/api/lab/quiz/practice", {"concept": "graph", "n": 3})
        self.assertEqual((code, len(d["questions"])), (200, 2))
        self.assertEqual(self.req("/api/lab/quiz/practice", {"concept": "nope"})[0], 400)
        q = lab.by_id("quiz", "id", d["questions"][0]["id"])
        self.assertTrue(self.req("/api/lab/grade", {"id": q["id"], "choice": q["answer"]})[1]["correct"])

    def test_exercise_checks(self):
        w = lab.by_id("worked", "id", "w-sum")
        self.assertTrue(self.req("/api/lab/faded/check", {"id": "w-sum", "level": 1, "answer": "print(sum(a))"})[1]["ok"])
        self.assertFalse(self.req("/api/lab/faded/check", {"id": "w-sum", "level": 1, "answer": "print(0)"})[1]["ok"])
        ps = self.req("/api/lab/parsons?id=w-sum&seed=2")[1]
        ids = {x["text"]: x["id"] for x in ps["lines"]}
        real = [ln for s in w["steps"] for ln in s["code"].split("\n") if ln.strip()]
        self.assertTrue(self.req("/api/lab/parsons/check", {"id": "w-sum", "seed": 2, "order": [ids[t] for t in real]})[1]["ok"])
        self.assertEqual(self.req("/api/lab/parsons/check", {"id": "w-sum", "seed": 2, "order": [999]})[0], 400)
        self.assertEqual(self.req("/api/lab/parsons/check", {"id": "w-sum", "seed": 2, "order": "x"})[0], 400)
        r = self.req("/api/lab/bug/check", {"id": "b-range", "line": 3})[1]
        self.assertTrue(r["found"])
        self.assertFalse(self.req("/api/lab/bug/check", {"id": "b-range", "line": 1})[1]["found"])
        fixed = lab.by_id("bugs", "id", "b-range")["fixed"]
        self.assertTrue(self.req("/api/lab/bug/check", {"id": "b-range", "line": 3, "fixed": fixed})[1]["fix"]["ok"])
        self.assertTrue(self.req("/api/lab/predict/check", {"id": "p-float", "answer": "0.30000000000000004"})[1]["correct"])
        self.assertEqual(self.req("/api/lab/predict/check", {"id": "nope", "answer": "x"})[0], 400)


class ExportApiTests(ApiBase):
    def test_downloads_and_coach_import(self):
        for kind, ctype, needle in (("anki", "text/tab-separated-values", b"cpe"), ("xapi", "application/json", b"["), ("report", "text/html", "學習報告".encode())):
            code, body, h = self.req(f"/api/export/{kind}", raw=True)
            self.assertEqual(code, 200, kind)
            self.assertTrue(h["Content-Type"].startswith(ctype), kind)
            self.assertIn(needle, body, kind)
        self.assertEqual(self.req("/api/export/zzz", raw=True)[0], 400)
        code, d, _ = self.req("/api/coach/import", {"from": "老師", "comments": [{"text": "加油"}, {"text": ""}]})
        self.assertEqual((code, d["imported"]), (200, 1))
        self.assertEqual(self.req("/api/insights")[1]["coach_comments"][0]["text"], "加油")

    def test_exam_focus_without_an_exam_is_harmless(self):
        code, d, _ = self.req("/api/exam/focus", {"seconds": 5})
        self.assertEqual((code, d["active"], d["count"]), (200, False, 0))

    def test_requires_token(self):
        r = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/insights", headers={"Host": f"127.0.0.1:{self.port}"})
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(r)
        self.assertEqual(cm.exception.code, 403)


if __name__ == "__main__":
    unittest.main()
