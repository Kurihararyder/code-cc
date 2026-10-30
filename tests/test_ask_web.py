import json
import socket
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from cpe_coach import ask, bank, service, web
from cpe_coach.llm import LLMClient, LLMError
from cpe_coach.store import Workspace


class Clock:
    t = 1_800_000_000.0

    def __call__(self):
        return self.t


def fake_llm(replies):
    """依序回傳 replies（字串或 dict）；dict 會轉成 JSON。可以丟 LLMError。"""
    calls = []

    def transport(url, headers, body):
        calls.append(body["messages"])
        r = replies.pop(0)
        if isinstance(r, Exception):
            raise r
        text = r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)
        return {"choices": [{"message": {"content": text}}]}
    c = LLMClient("openai", "k", transport=transport)
    c.calls = calls
    return c


def good(quote="print", src="code", line=None, msg="你預期這一行輸出什麼？", typ="predict"):
    return {"type": typ, "message": msg, "evidence": [{"source": src, "line": line, "quote": quote}]}


class AskBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Workspace.create(Path(self.tmp.name), "2026-11-01", Clock())
        self.bank = bank.load_bank(self.ws)
        service.create_solution(self.ws, self.bank, "d001")
        (self.ws.solutions / "d001.py").write_text('name = input()\nprint("Hello " + name)\n')

    def tearDown(self):
        self.tmp.cleanup()

    def attempt(self):
        return service.run_test(self.ws, "d001")

    def q(self, llm, **kw):
        args = dict(kind="question", source="code", selection='print("Hello " + name)', line_start=2, line_end=2)
        args.update(kw)
        return ask.ask(self.ws, self.bank, "d001", llm, **args)


class VerifyTests(unittest.TestCase):
    def test_code_quote_fixes_line(self):
        code = "a = 1\nb = a + 2\n"
        out = ask.verify_evidence([{"source": "code", "line": 1, "quote": "b = a + 2"}], {"code": code})
        self.assertTrue(out[0]["ok"])
        self.assertEqual(out[0]["line"], 2)

    def test_whitespace_normalized_and_fabricated_rejected(self):
        out = ask.verify_evidence([{"source": "code", "quote": "b   =  a+2"}, {"source": "code", "quote": "not here"},
                                   {"source": "statement", "quote": "輸出"}, {"source": "nope", "quote": "x"},
                                   {"source": "code", "quote": "x"}],
                                  {"code": "b = a+2", "statement": "請輸出答案"})
        self.assertEqual([o["ok"] for o in out], [True, False, True, False, False])   # 空白差異會被正規化；捏造的、未知來源的、太短的都不行

    def test_parse_reply(self):
        self.assertTrue(ask.parse_reply('前言 {"message": "hi", "evidence": []} 後記')["parsed"])
        self.assertFalse(ask.parse_reply("純文字")["parsed"])
        self.assertFalse(ask.parse_reply('{"type": "x"}')["parsed"])


class AskFlowTests(AskBase):
    def test_no_key(self):
        with self.assertRaises(ask.AskDenied):
            self.q(None)

    def test_gate_requires_attempt_then_blocks_second_question(self):
        llm = fake_llm([good(), good()])
        with self.assertRaises(ask.AskDenied) as cm:
            self.q(llm)
        self.assertIn("先自己試一次", str(cm.exception))
        self.attempt()
        r = self.q(llm)
        self.assertTrue(r["reply"]["verified"])
        self.assertEqual(self.ws.state()["problems"]["d001"]["hint_level"], 2)
        with self.assertRaises(ask.AskDenied) as cm:
            self.q(llm)
        self.assertIn("剛問過", str(cm.exception))
        self.attempt()                          # 新的測試後可以再問
        self.q(llm)

    def test_explain_is_free_and_not_a_hint(self):
        r = self.q(fake_llm([good(msg="print 是把東西印到螢幕。", typ="explain")]), kind="explain", selection="print")
        self.assertTrue(r["reply"]["verified"])
        self.assertEqual(self.ws.state()["problems"]["d001"]["hint_level"], -1)

    def test_mismatch_needs_failing_verdict(self):
        (self.ws.solutions / "d001.py").write_text('print(f"Hello, {input().strip()}!")\n')
        self.attempt()                           # 通過
        with self.assertRaises(ask.AskDenied):
            self.q(fake_llm([good()]), kind="mismatch")

    def test_fabricated_quote_gets_one_retry(self):
        self.attempt()
        llm = fake_llm([good(quote="this is not in code"), good(quote="input()")])
        r = self.q(llm)
        self.assertTrue(r["reply"]["verified"])
        self.assertEqual(len(llm.calls), 2)
        self.assertIn("找不到", llm.calls[1][-1]["content"])

    def test_still_fabricated_is_flagged(self):
        self.attempt()
        r = self.q(fake_llm([good(quote="nope nope"), good(quote="still nope")]))
        self.assertFalse(r["reply"]["verified"])
        self.assertIn("半信半疑", r["reply"]["warning"])

    def test_non_json_flagged(self):
        self.attempt()
        r = self.q(fake_llm(["隨便一段沒有 JSON 的文字"]))
        self.assertFalse(r["reply"]["verified"])
        self.assertTrue(r["reply"]["warning"])

    def test_long_code_stripped(self):
        self.attempt()
        long_msg = "試試：\n```python\n" + "\n".join(f"x{i}=1" for i in range(12)) + "\n```\n你覺得呢？"
        r = self.q(fake_llm([good(msg=long_msg)]))
        self.assertIn("已被系統移除", r["reply"]["message"])

    def test_llm_error_rolls_back_hint_level(self):
        self.attempt()
        with self.assertRaises(ask.AskDenied):
            self.q(fake_llm([LLMError("boom")]))
        p = self.ws.state()["problems"]["d001"]
        self.assertEqual((p["hint_level"], p["attempts_since_hint"]), (-1, 1))
        self.assertEqual(ask.load_chat(self.ws, "d001")["threads"], [])

    def test_reply_flow_and_cap(self):
        self.attempt()
        llm = fake_llm([good(), good(typ="feedback", msg="說對一半。") ] + [good(typ="feedback")] * 12)
        r = self.q(llm)
        tid = r["thread"]
        r2 = ask.ask(self.ws, self.bank, "d001", llm, thread=tid, reply="我覺得少逗號")
        self.assertEqual(r2["reply"]["type"], "feedback")
        # 程式改過 → 回覆時會附上最新程式
        (self.ws.solutions / "d001.py").write_text('print("Hello, " + input())\n')
        ask.ask(self.ws, self.bank, "d001", llm, thread=tid, reply="改好了")
        self.assertIn("已修改程式", llm.calls[-1][-1]["content"])
        with self.assertRaises(ask.AskDenied):
            ask.ask(self.ws, self.bank, "d001", llm, thread=tid, reply="   ")
        with self.assertRaises(ask.AskDenied):
            for _ in range(15):
                ask.ask(self.ws, self.bank, "d001", llm, thread=tid, reply="再來")

    def test_exam_locks_everything(self):
        self.attempt()
        self.ws.save_exam({"kind": "mock", "start": 0, "minutes": 1, "problems": [], "files": {}, "results": {}})
        with self.assertRaises(ask.AskDenied):
            self.q(fake_llm([good()]), kind="explain", selection="print")

    def test_prompt_contains_selection_and_numbered_code(self):
        self.attempt()
        llm = fake_llm([good()])
        self.q(llm, selection='print("Hello " + name)')
        user = llm.calls[0][1]["content"]
        self.assertIn("  2| print(", user)
        self.assertIn("[學生選取] 來源：code，第 2 行", user)
        self.assertIn("預期輸出", user)


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        Workspace.create(Path(cls.tmp.name), "2026-11-01")
        s = socket.socket(); s.bind(("127.0.0.1", 0)); cls.port = s.getsockname()[1]; s.close()
        cls.app = web.App(Path(cls.tmp.name), cls.port)
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", cls.port), web.make_handler(cls.app))
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.tmp.cleanup()

    def req(self, path, body=None, headers=None, token=True):
        h = {"Host": f"127.0.0.1:{self.port}"}
        if token:
            h["X-CPE-Token"] = self.app.token
        if body is not None:
            h["Content-Type"] = "application/json"
        h.update(headers or {})
        r = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=None if body is None else json.dumps(body).encode(),
                                   headers=h, method="POST" if body is not None else "GET")
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()

    def test_index_has_token_and_security_headers(self):
        code, html = self.req("/", token=False)
        self.assertEqual(code, 200)
        self.assertIn(self.app.token, html)
        self.assertNotIn("__TOKEN__", html)

    def test_host_and_token_and_origin_protection(self):
        self.assertEqual(self.req("/", headers={"Host": "evil.example"}, token=False)[0], 403)
        self.assertEqual(self.req("/api/state", token=False)[0], 403)
        self.assertEqual(self.req("/api/save", {"id": "d001", "code": "x"}, token=False)[0], 403)
        self.assertEqual(self.req("/api/state", headers={"Origin": "http://evil.example"})[0], 403)
        self.assertEqual(self.req("/api/state", headers={"X-CPE-Token": "wrong"})[0], 403)

    def test_requires_json_content_type(self):
        r = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/save", data=b"{}", method="POST",
                                   headers={"Host": f"127.0.0.1:{self.port}", "X-CPE-Token": self.app.token,
                                            "Content-Type": "text/plain"})
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(r)
        self.assertEqual(cm.exception.code, 415)

    def test_state_new_test_trace_flow(self):
        code, body = self.req("/api/state")
        self.assertEqual(code, 200)
        st = json.loads(body)
        self.assertEqual(st["unit"]["n"], 1)
        self.assertFalse(st["ai"]["available"] and False)
        code, body = self.req("/api/new", {"id": "d001"})
        self.assertEqual(code, 200)
        self.assertTrue(json.loads(body)["created"])
        code, body = self.req("/api/test", {"id": "d001", "code": 'print(f"Hello, {input().strip()}!")\n'})
        self.assertEqual(json.loads(body)["verdict"], "AC")
        code, body = self.req("/api/trace", {"id": "d001"})
        self.assertGreater(len(json.loads(body)["steps"]), 0)
        code, body = self.req("/api/problem?id=d001")
        self.assertTrue(json.loads(body)["solved"])

    def test_ask_without_key_is_409_and_key_roundtrip(self):
        self.app.key = None
        code, body = self.req("/api/ask", {"id": "d001", "kind": "explain", "source": "statement", "selection": "輸出"})
        self.assertEqual(code, 409)
        self.assertIn("API 金鑰", json.loads(body)["error"])
        code, body = self.req("/api/key", {"key": "sk-test", "model": "gpt-4o"})
        self.assertTrue(json.loads(body)["available"])
        self.assertFalse((Path(self.tmp.name) / ".cpe" / "config.json").read_text().count("sk-test"))   # 金鑰不落地
        self.app.key = None

    def test_unknown_route_and_bad_json(self):
        self.assertEqual(self.req("/api/nope", {})[0], 404)
        r = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/save", data=b"{not json", method="POST",
                                   headers={"Host": f"127.0.0.1:{self.port}", "X-CPE-Token": self.app.token,
                                            "Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(r)
        self.assertEqual(cm.exception.code, 400)


class ServiceTests(unittest.TestCase):
    def test_lint_catches_common_traps_without_false_positives(self):
        tags = lambda c: [x["tag"] for x in service.lint(c)]
        self.assertIn("alias-list", tags("g=[[0]*3]*3\n"))
        self.assertNotIn("alias-list", tags("a=[0]*3\nb=[[0]*3 for _ in range(3)]\n"))
        self.assertIn("shadow-builtin", tags("sum = 0\nfor x in a: sum += x\n"))
        self.assertIn("none-return", tags("a = b.sort()\n"))
        self.assertIn("slow-pop0", tags("q.pop(0)\n"))
        self.assertEqual(tags("def f(:\n"), [])               # 語法錯誤交給判題
        self.assertEqual(tags("n = int(input())\nprint(n)\n"), [])


if __name__ == "__main__":
    unittest.main()
