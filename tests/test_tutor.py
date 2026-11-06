"""AI 助教：提示詞內容、輸入檢查、沒有 AI 時的錯誤（用假的 AI，不連線）。"""
import unittest

from cpe_coach import tutor


class Fake:
    def __init__(self):
        self.calls = []

    def complete(self, system, user):
        self.calls.append((system, user))
        return "  先想想重置時狀態該是什麼。  "


class TutorTests(unittest.TestCase):
    def test_prompt_has_unit_problem_code_and_log_but_no_reference(self):
        c = Fake()
        r = tutor.ask(c, "verilog", 6, "為什麼我的 z 一直是 0？", pid="v012", code="module top_module; endmodule", log="MISMATCH 週期 4")
        self.assertEqual(r["answer"], "先想想重置時狀態該是什麼。")
        system, user = c.calls[0]
        self.assertIn("不要直接貼出整題的完整答案", system)
        for needle in ("有限狀態機", "v012", "module top_module", "MISMATCH 週期 4", "為什麼我的 z 一直是 0？"):
            self.assertIn(needle, user)
        self.assertNotIn("localparam S0", user)                 # 參考解不會送出去

    def test_input_checks(self):
        with self.assertRaises(ValueError):
            tutor.ask(Fake(), "tcl", 1, "   ")
        with self.assertRaises(ValueError):
            tutor.ask(Fake(), "tcl", 1, "x" * 2001)
        with self.assertRaises(ValueError):
            tutor.ask(None, "tcl", 1, "hi")
        with self.assertRaises(ValueError):
            tutor.ask(Fake(), "tcl", 999, "hi")


if __name__ == "__main__":
    unittest.main()
