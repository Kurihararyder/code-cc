"""學習指南：資料形狀、答案不外洩、作答記錄與錯題重做、Markdown 與 JSON 與原始碼一致、帶 verify 的題目重跑。"""
import json
import socket
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

from cpe_coach import guides, web
from cpe_coach.store import Workspace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "dev"))
import guide_lib as L  # noqa: E402


class Data(unittest.TestCase):
    def test_every_guide_is_well_formed(self):
        idx = json.loads((guides.DIR / "index.json").read_text(encoding="utf-8"))
        self.assertTrue(idx)
        for g in idx:
            data = json.loads((guides.DIR / f"{g['id']}.json").read_text(encoding="utf-8"))
            n = 0
            for grp in data["groups"]:
                for q in grp["questions"]:
                    n += 1
                    self.assertEqual(len(q["options"]), 4, g["id"])
                    self.assertEqual(len({o.strip() for o in q["options"]}), 4, (g["id"], q["stem"]))
                    self.assertIn(q["answer"], (0, 1, 2, 3))
                    self.assertGreater(len(q["why"]), 10)
            self.assertEqual(n, g["questions"])
            self.assertTrue((ROOT / "docs" / "guides" / f"{g['id']}.md").exists())

    def test_answer_positions_are_balanced(self):
        for f in guides.DIR.glob("*-*.json"):
            data = json.loads(f.read_text(encoding="utf-8"))
            cnt = [0, 0, 0, 0]
            for grp in data["groups"]:
                for q in grp["questions"]:
                    cnt[q["answer"]] += 1
            tot = sum(cnt)
            self.assertTrue(all(c >= tot * 0.12 for c in cnt), (f.name, cnt))

    def test_shuffle_is_deterministic_and_keeps_the_answer(self):
        q = L.Q("題幹", "對", ["錯1", "錯2", "錯3"], "這是一段夠長的解析文字")
        a, b = L.shuffled(q), L.shuffled(q)
        self.assertEqual(a, b)
        self.assertEqual(a["options"][a["answer"]], "對")

    def test_verified_questions_still_pass_with_the_real_tools(self):
        """重新跑所有帶 verify 的題目（有裝工具才跑）。"""
        import gen_guides
        ran = 0
        for g in gen_guides.load_guides():
            for grp in g["groups"]:
                for i, q in enumerate(grp["questions"], 1):
                    v = q.get("verify")
                    if v and L.available(v["lang"]):
                        L.check_question(q, f"{g['id']}/{grp['title']}/{i}")
                        ran += 1
        if ran == 0:
            self.skipTest("沒有安裝驗證工具")


class Api(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Workspace.create(Path(self.tmp.name), "2026-11-01")
        self.gid = json.loads((guides.DIR / "index.json").read_text(encoding="utf-8"))[0]["id"]

    def tearDown(self):
        self.tmp.cleanup()

    def test_set_has_no_answers(self):
        s = guides.get_set(self.ws, self.gid, "0")
        self.assertTrue(s["items"])
        for it in s["items"]:
            self.assertNotIn("answer", it)
            self.assertNotIn("why", it)

    def test_answer_records_and_wrong_set(self):
        s = guides.get_set(self.ws, self.gid, "0")["items"]
        data = json.loads((guides.DIR / f"{self.gid}.json").read_text(encoding="utf-8"))
        right = data["groups"][0]["questions"][0]["answer"]
        r = guides.answer(self.ws, self.gid, 0, 0, right)
        self.assertTrue(r["correct"])
        r = guides.answer(self.ws, self.gid, 0, 1, (data["groups"][0]["questions"][1]["answer"] + 1) % 4)
        self.assertFalse(r["correct"])
        self.assertTrue(r["why"])
        wrong = guides.get_set(self.ws, self.gid, "wrong")["items"]
        self.assertEqual([(x["group"], x["i"]) for x in wrong], [(0, 1)])
        guides.answer(self.ws, self.gid, 0, 1, data["groups"][0]["questions"][1]["answer"])
        self.assertEqual(guides.get_set(self.ws, self.gid, "wrong")["items"], [])
        st = [g for g in guides.index(self.ws) if g["id"] == self.gid][0]
        self.assertEqual((st["answered"], st["correct"], st["wrong"]), (2, 2, 0))
        self.assertTrue(s)

    def test_bad_input(self):
        with self.assertRaises(ValueError):
            guides.get_set(self.ws, "../x", "0")
        with self.assertRaises(ValueError):
            guides.get_set(self.ws, "nope-nope", "0")
        with self.assertRaises(ValueError):
            guides.answer(self.ws, self.gid, 99, 0, 0)
        with self.assertRaises(ValueError):
            guides.answer(self.ws, self.gid, 0, 0, 7)

    def test_web_api(self):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
        app = web.App(Path(self.tmp.name), port)
        httpd = web.LocalServer(("127.0.0.1", port), web.make_handler(app))
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            def call(path, body=None):
                h = {"Host": f"127.0.0.1:{port}", "X-CPE-Token": app.token}
                if body is not None:
                    h["Content-Type"] = "application/json"
                r = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=None if body is None else json.dumps(body).encode(), headers=h,
                                           method="GET" if body is None else "POST")
                return json.load(urllib.request.urlopen(r))
            self.assertTrue(call("/api/guides")["guides"])
            self.assertTrue(call(f"/api/guide?id={self.gid}&group=all")["items"])
            self.assertIn("correct", call("/api/guide/answer", {"id": self.gid, "group": 0, "i": 0, "choice": 0}))
        finally:
            httpd.shutdown()
            httpd.server_close()


if __name__ == "__main__":
    unittest.main()
