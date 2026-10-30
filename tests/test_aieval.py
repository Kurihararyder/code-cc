"""真實模型常見的『不守規矩』行為：詢問系統是否撐得住，以及評測工具本身。"""
import json
import re
import unittest

from cpe_coach import aieval, ask
from cpe_coach.llm import LLMClient, LLMError


def selection_of(body):
    user = [m for m in body["messages"] if m["role"] == "user"][0]["content"]
    m = re.search(r'\[學生選取\][^\n]*\n"""\n(.*?)\n"""', user, re.S)
    return (m.group(1).strip().splitlines() or ["x"])[0] if m else "x"


def make_transport(mode, log=None):
    state = {"n": 0}

    def reply(body, text, usage=(120, 40)):
        return {"choices": [{"message": {"content": text}}], "usage": {"prompt_tokens": usage[0], "completion_tokens": usage[1]}}

    def transport(url, headers, body):
        state["n"] += 1
        if log is not None:
            log.append(json.loads(json.dumps(body)))
        last = body["messages"][-1]["content"]
        sel = selection_of(body)
        src = "statement" if "[學生選取] 來源：statement" in "".join(m["content"] for m in body["messages"] if m["role"] == "user") else \
              "output" if "[學生選取] 來源：output" in "".join(m["content"] for m in body["messages"] if m["role"] == "user") else "code"
        feedback = last.startswith("[學生回答]")
        q = "你預期這一行執行完之後，變數會是多少？"
        obj = {"type": "feedback" if feedback else "predict", "message": ("你說對了一半。" if feedback else "") + q,
               "evidence": [{"source": src, "line": None, "quote": sel}]}
        if mode == "good":
            return reply(body, json.dumps(obj, ensure_ascii=False))
        if mode == "fenced":
            return reply(body, "好的，這是我的回答：\n```json\n" + json.dumps(obj, ensure_ascii=False) + "\n```\n希望有幫助 {not json}")
        if mode == "lineno":
            obj["evidence"][0]["quote"] = "  3| " + sel
            return reply(body, json.dumps(obj, ensure_ascii=False))
        if mode == "mislabel":
            obj["evidence"][0]["source"] = "trace" if src != "trace" else "code"
            return reply(body, json.dumps(obj, ensure_ascii=False))
        if mode == "truncated":
            txt = json.dumps(obj, ensure_ascii=False)
            return reply(body, txt[: txt.index('"evidence"') - 2])
        if mode == "empty":
            return reply(body, "")
        if mode == "english":
            obj["message"] = "What do you expect the variable to be after this line runs? Please think carefully."
            return reply(body, json.dumps(obj, ensure_ascii=False))
        if mode == "claims":
            obj["message"] = "你的程式是錯的，因為這一行有問題。"
            return reply(body, json.dumps(obj, ensure_ascii=False))
        if mode == "fabricate":
            obj["evidence"][0]["quote"] = "這段文字根本不存在於任何來源"
            return reply(body, json.dumps(obj, ensure_ascii=False))
        if mode == "flaky429":
            if state["n"] <= 2:
                raise LLMError("API 回應 429：rate limit", 429, 0.0)
            return reply(body, json.dumps(obj, ensure_ascii=False))
        if mode == "json400":
            if "response_format" in body:
                raise LLMError("API 回應 400：Unsupported parameter: 'response_format'", 400)
            return reply(body, json.dumps(obj, ensure_ascii=False))
        if mode == "down":
            raise LLMError("API 回應 500：boom", 500)
        raise AssertionError(mode)

    return transport


def client(mode, log=None, **kw):
    return LLMClient("openai", "k", transport=make_transport(mode, log), sleep=lambda s: None, **kw)


def run(mode, n=3, **kw):
    return aieval.run_eval(client(mode, **kw), n=n, replies=True)


class ParseTests(unittest.TestCase):
    def test_json_in_prose_with_braces_and_fences(self):
        raw = '前言 {這不是 JSON} 然後：\n```json\n{"type":"predict","message":"哈囉？","evidence":[{"source":"code","line":"3","quote":"x = 1"}]}\n```\n後記 {"a":1}'
        d = ask.parse_reply(raw)
        self.assertTrue(d["parsed"])
        self.assertEqual((d["type"], d["message"], d["evidence"][0]["line"]), ("predict", "哈囉？", 3))      # 行號字串會轉成數字

    def test_first_dict_with_message_wins_and_bad_evidence_dropped(self):
        d = ask.parse_reply('{"x":1} {"message":"第二個","evidence":["bad",{"source":"CODE","quote":5},{"source":"Code","quote":"ok"}]}')
        self.assertEqual(d["message"], "第二個")
        self.assertEqual(d["evidence"], [{"source": "code", "line": None, "quote": "ok"}])

    def test_truncated_json_salvages_message_only(self):
        d = ask.parse_reply('{"type": "predict", "message": "你預期 \\"x\\" 是多少？", "evid')
        self.assertFalse(d["parsed"])
        self.assertEqual(d["message"], '你預期 "x" 是多少？')
        self.assertEqual(d["evidence"], [])

    def test_plain_text_and_none(self):
        self.assertEqual(ask.parse_reply("純文字回答")["message"], "純文字回答")
        self.assertEqual(ask.parse_reply("")["message"], "")

    def test_quote_cleaning_strips_line_number_prefix_and_backticks(self):
        src = {"code": "a = 1\nfor i in range(3):\n    print(i)\n", "statement": "", "output": "", "trace": ""}
        ev = ask.verify_evidence([{"source": "code", "line": 1, "quote": "  2| for i in range(3):"}, {"source": "code", "line": None, "quote": "`print(i)`"}], src)
        self.assertEqual([e["ok"] for e in ev], [True, True])
        self.assertEqual(ev[0]["line"], 2)                                  # 行號以實際位置為準


class ClientTests(unittest.TestCase):
    def test_retries_429_with_retry_after_then_succeeds_and_counts_usage(self):
        sleeps = []
        c = LLMClient("openai", "k", transport=make_transport("flaky429"), sleep=sleeps.append)
        out = c.chat("sys", [{"role": "user", "content": '[學生選取] 來源：code\n"""\nx\n"""'}])
        self.assertIn("message", out)
        self.assertEqual(len(sleeps), 2)
        u = c.usage()
        self.assertEqual((u["calls"], u["tokens_in"], u["tokens_out"], u["retries"]), (1, 120, 40, 2))

    def test_gives_up_after_retries(self):
        c = LLMClient("openai", "k", transport=make_transport("down"), sleep=lambda s: None, retries=2)
        with self.assertRaises(LLMError):
            c.chat("s", [{"role": "user", "content": "x"}])

    def test_non_retryable_error_is_not_retried(self):
        n = []

        def t(u, h, b):
            n.append(1)
            raise LLMError("API 回應 401：bad key", 401)
        with self.assertRaises(LLMError):
            LLMClient("openai", "k", transport=t, sleep=lambda s: None).chat("s", [{"role": "user", "content": "x"}])
        self.assertEqual(len(n), 1)

    def test_json_mode_is_requested_and_dropped_when_unsupported(self):
        log = []
        c = client("json400", log)
        c.chat("s", [{"role": "user", "content": '[學生選取] 來源：code\n"""\nx\n"""'}])
        self.assertTrue(log[0].get("response_format"))
        self.assertNotIn("response_format", log[1])
        self.assertFalse(c.json_mode)
        c.chat("s", [{"role": "user", "content": '[學生選取] 來源：code\n"""\nx\n"""'}])
        self.assertNotIn("response_format", log[2])                         # 之後不再送

    def test_anthropic_has_no_json_mode(self):
        log = []
        c = LLMClient("anthropic", "k", transport=lambda u, h, b: (log.append(b), {"content": [{"type": "text", "text": "hi"}], "usage": {"input_tokens": 3, "output_tokens": 2}})[1])
        self.assertEqual(c.chat("s", [{"role": "user", "content": "x"}]), "hi")
        self.assertNotIn("response_format", log[0])
        self.assertEqual((c.usage()["tokens_in"], c.usage()["tokens_out"]), (3, 2))


class EvalTests(unittest.TestCase):
    def test_well_behaved_model_scores_clean(self):
        rep = run("good", n=6)
        s = rep["summary"]
        self.assertEqual((s["asks"], s["failed_calls"]), (6, 0))
        self.assertEqual((s["json_parsed_rate"], s["all_quotes_verified_rate"], s["retry_rate"]), (1.0, 1.0, 0.0))
        self.assertEqual(s["rule_checks"]["ends_with_question"], 1.0)
        self.assertGreater(s["replies"], 0)
        self.assertEqual(s["feedback_verified_rate"], 1.0)
        self.assertGreater(s["tokens_in"], 0)
        self.assertIsNone(s["cost_usd_estimate"])
        self.assertIn("各項指標都在合理範圍", "".join(s["advice"]))
        self.assertTrue(aieval.format_report(rep))

    def test_cost_estimate_from_prices(self):
        rep = aieval.run_eval(client("good"), n=3, replies=False, price_in=2.0, price_out=10.0)
        s = rep["summary"]
        self.assertAlmostEqual(s["cost_usd_estimate"], s["tokens_in"] / 1e6 * 2 + s["tokens_out"] / 1e6 * 10, places=4)

    def test_fenced_and_prose_wrapped_json_still_verifies(self):
        s = run("fenced")["summary"]
        self.assertEqual((s["json_parsed_rate"], s["all_quotes_verified_rate"]), (1.0, 1.0))

    def test_line_number_prefix_in_quotes_is_tolerated(self):
        s = run("lineno")["summary"]
        self.assertEqual(s["all_quotes_verified_rate"], 1.0)

    def test_mislabelled_source_is_corrected_and_counted(self):
        s = run("mislabel", n=3)["summary"]
        self.assertGreaterEqual(s["relabeled_quotes"], 1)
        self.assertEqual(s["all_quotes_verified_rate"], 1.0)

    def test_truncated_json_is_unverified_and_flagged(self):
        rep = run("truncated", n=3)
        s = rep["summary"]
        self.assertEqual(s["json_parsed_rate"], 0.0)
        self.assertEqual(s["all_quotes_verified_rate"], 0.0)
        self.assertTrue(any("JSON" in a for a in s["advice"]))
        self.assertTrue(all(t["message"] for t in rep["turns"] if t.get("ok")))   # 至少把訊息撈出來給學生看

    def test_fabricated_quotes_trigger_one_retry_then_warning(self):
        rep = run("fabricate", n=3)
        s = rep["summary"]
        self.assertEqual(s["all_quotes_verified_rate"], 0.0)
        self.assertEqual(s["retry_rate"], 1.0)
        first = [t for t in rep["turns"] if t.get("ok")][0]
        self.assertEqual(first["usage"]["calls"], 2)                           # 原本一次＋要求重答一次，不會無限重試

    def test_empty_replies_are_failures_not_blank_messages(self):
        rep = run("empty", n=3)
        self.assertEqual(rep["summary"]["failed_calls"], 3)
        self.assertTrue(all(not t["ok"] for t in rep["turns"]))
        self.assertIn("沒有任何一次成功", rep["summary"]["advice"][0])

    def test_rule_violations_are_measured(self):
        s = run("english", n=3)["summary"]
        self.assertEqual(s["rule_checks"]["traditional_chinese"], 0.0)
        self.assertTrue(any("繁體中文" in a for a in s["advice"]))
        s = run("claims", n=3)["summary"]
        self.assertEqual(s["rule_checks"]["no_correctness_claim"], 0.0)

    def test_provider_down_is_reported_and_user_state_untouched(self):
        rep = run("down", n=3)
        self.assertEqual(rep["summary"]["failed_calls"], 3)

    def test_scenarios_really_fail_before_asking(self):
        from pathlib import Path
        import tempfile
        from cpe_coach import bank as bank_mod
        from cpe_coach.store import Workspace
        with tempfile.TemporaryDirectory() as td:
            ws = Workspace.create(Path(td), "2026-01-05")
            sc, skipped = aieval.build_scenarios(ws, bank_mod.load_bank(ws), 20)
            self.assertEqual(len(sc), len(aieval.SCENARIOS), skipped)           # 每份有 bug 的程式都真的判為失敗
            self.assertTrue(all(s["verdict"] != "AC" for s in sc))


class ChatLogTests(unittest.TestCase):
    def test_ask_event_records_tokens(self):
        import tempfile
        from pathlib import Path
        from cpe_coach import bank as bank_mod, service
        from cpe_coach.store import Workspace
        with tempfile.TemporaryDirectory() as td:
            ws = Workspace.create(Path(td), "2026-01-05")
            bank = bank_mod.load_bank(ws)
            bank_mod.install_drill(ws, "d001")
            ws.solutions.mkdir(exist_ok=True)
            service.solution_file(ws, "d001").write_text('print("Hello " + input() + "!")\n', encoding="utf-8")
            service.run_test(ws, "d001")
            r = ask.ask(ws, bank, "d001", client("good"), kind="question", source="code", selection='print("Hello " + input() + "!")', line_start=1, line_end=1,
                        statement=service.statement_for(ws, "d001"))
            self.assertTrue(r["reply"]["verified"])
            ev = [e for e in ws.events() if e["kind"] == "ask"][-1]
            self.assertEqual((ev["tokens_in"], ev["tokens_out"], ev["calls"]), (120, 40, 1))


if __name__ == "__main__":
    unittest.main()
