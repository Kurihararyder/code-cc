"""內建練習題的英文版與語言漸進（中文 → 中英對照 → 英文）。"""
import contextlib
import io
import os
import re
import tempfile
import unittest
from pathlib import Path

from cpe_coach import bank as bank_mod
from cpe_coach import cli, course, service
from cpe_coach.store import Workspace

BANK = bank_mod.load_bank(None)
DRILL_IDS = sorted(p for p, b in BANK.items() if b.get("drill"))
CJK = re.compile(r"[぀-ヿ㐀-鿿가-힯＀-￯]")


def make_ws():
    tmp = tempfile.TemporaryDirectory()
    return tmp, Workspace.create(Path(tmp.name), "2026-11-01")


class EnglishContentTests(unittest.TestCase):
    def test_every_drill_has_an_english_version(self):
        self.assertEqual(len(DRILL_IDS), 107)
        for pid in DRILL_IDS:
            self.assertTrue(bank_mod.has_english(pid), pid)
            self.assertTrue(BANK[pid].get("title_en"), pid)

    def test_english_text_is_english_and_has_exam_style_sections(self):
        for pid in DRILL_IDS:
            text = (bank_mod.DRILLS / pid / "statement.en.md").read_text(encoding="utf-8")
            self.assertFalse(CJK.findall(text), f"{pid} 的英文版含有中日韓字元：{CJK.findall(text)[:3]}")
            self.assertTrue(service.statement_is_english(text), pid)
            for h in ("## Input", "## Output", "## Sample Input", "## Sample Output"):
                self.assertIn(h, text, pid)

    def test_english_sample_equals_first_test_case(self):
        for pid in DRILL_IDS:
            text = (bank_mod.DRILLS / pid / "statement.en.md").read_text(encoding="utf-8")
            (sin, sout), = service.parse_samples(text)
            tdir = bank_mod.DRILLS / pid / "tests"
            self.assertEqual(sin.strip(), (tdir / "case01.in").read_text(encoding="utf-8").strip(), pid)
            self.assertEqual(sout.strip(), (tdir / "case01.out").read_text(encoding="utf-8").strip(), pid)

    def test_english_and_chinese_agree_on_numbers(self):
        """粗略的一致性檢查：中文版出現的數字限制（≤ 10^5 之類）英文版也要有。"""
        for pid in DRILL_IDS:
            zh = (bank_mod.DRILLS / pid / "statement.md").read_text(encoding="utf-8")
            en = (bank_mod.DRILLS / pid / "statement.en.md").read_text(encoding="utf-8")
            body_zh = zh.split("## 範例")[0]
            body_en = en.split("## Sample Input")[0]
            nums_zh = set(re.findall(r"10\^\d+|\d{3,}", body_zh))
            missing = {n for n in nums_zh if n not in body_en}
            self.assertFalse(missing, f"{pid} 英文版少了數字 {missing}")


class ModeTests(unittest.TestCase):
    def test_auto_follows_course_stage(self):
        tmp, ws = make_ws()
        with tmp:
            self.assertEqual(bank_mod.resolve_lang(ws, "d001"), "zh")          # 階段 0
            self.assertEqual(bank_mod.resolve_lang(ws, "d031"), "bi")          # 階段 1
            self.assertEqual(bank_mod.resolve_lang(ws, "d046"), "en")          # 階段 2
            self.assertEqual(bank_mod.resolve_lang(ws, "uva100"), "zh")        # 沒有英文版的題目不受影響

    def test_setting_overrides_and_exam_real_forces_english(self):
        tmp, ws = make_ws()
        with tmp:
            cfg = ws.config()
            cfg["statement_lang"] = "en"
            ws.save_config(cfg)
            self.assertEqual(bank_mod.resolve_lang(ws, "d001"), "en")
            cfg["statement_lang"] = "zh"
            ws.save_config(cfg)
            self.assertEqual(bank_mod.resolve_lang(ws, "d060"), "zh")
            ws.save_exam({"kind": "mock", "start": ws.now(), "minutes": 180, "problems": [], "files": {}, "results": {}, "real": True})
            self.assertEqual(bank_mod.resolve_lang(ws, "d001"), "en")

    def test_bilingual_has_both_and_statement_for_follows_setting(self):
        tmp, ws = make_ws()
        with tmp:
            bi = bank_mod.drill_statement("d031", "bi")
            self.assertIn("## Input", bi)
            self.assertIn("## 輸入", bi)
            self.assertLess(bi.index("## Input"), bi.index("## 輸入"))         # 英文在前
            cfg = ws.config()
            cfg["statement_lang"] = "zh"
            ws.save_config(cfg)
            self.assertNotIn("## Input", service.statement_for(ws, "d031"))
            cfg["statement_lang"] = "en"
            ws.save_config(cfg)
            self.assertNotIn("## 輸入", service.statement_for(ws, "d031"))      # 切換立即生效，不用重新安裝

    def test_user_imported_override_wins_and_foreign_problems_untouched(self):
        tmp, ws = make_ws()
        with tmp:
            service.import_statement(ws, "d001", "My own text. Sample Input\n1\nSample Output\n2\n")
            self.assertTrue(service.statement_for(ws, "d001").startswith("My own text"))
            service.import_statement(ws, "uva9", "Foreign statement.\nSample Input\n1\nSample Output\n1\n")
            self.assertIn("Foreign statement", service.statement_for(ws, "uva9"))
            self.assertEqual(service.statement_for(ws, "nope"), "")

    def test_problem_view_reports_language(self):
        tmp, ws = make_ws()
        with tmp:
            v = service.problem_view(ws, bank_mod.load_bank(ws), "d031")
            self.assertEqual((v["lang_mode"], v["has_english"], v["lang_setting"]), ("bi", True, "auto"))
            self.assertEqual(v["title_en"], "Until 0 0")
            self.assertIn("Input", v["statement"])


class RealModeTests(unittest.TestCase):
    def test_real_mock_uses_builtin_drills_in_english(self):
        tmp, ws = make_ws()
        with tmp:
            bank = bank_mod.load_bank(ws)
            ex = course.start_mock(ws, bank, "mock", real=True)
            self.assertTrue(ex["real"])
            self.assertEqual(len(ex["problems"]), 7)
            for pid in ex["problems"]:
                text = service.statement_for(ws, pid)
                self.assertTrue(service.statement_is_english(text), pid)
                self.assertFalse(CJK.findall(text), pid)
                self.assertTrue(service.statement_is_english((ws.root / "statements" / f"{pid}.md").read_text(encoding="utf-8")), pid)
            self.assertTrue(ws.exam()["real"])

    def test_non_real_mock_keeps_normal_language(self):
        tmp, ws = make_ws()
        with tmp:
            ex = course.start_mock(ws, bank_mod.load_bank(ws), "short", every_stage=False)
            self.assertFalse(ex.get("real"))


class CliTests(unittest.TestCase):
    def run_cli(self, ws, *argv):
        old = os.getcwd()
        os.chdir(ws.root)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = cli.main(list(argv))
        finally:
            os.chdir(old)
        return rc, buf.getvalue()

    def test_lang_and_statement_commands(self):
        tmp, ws = make_ws()
        with tmp:
            rc, out = self.run_cli(ws, "lang")
            self.assertIn("auto", out)
            rc, out = self.run_cli(ws, "lang", "en")
            self.assertIn("全部英文", out)
            rc, out = self.run_cli(ws, "statement", "d001")
            self.assertIn("## Input", out)
            rc, out = self.run_cli(ws, "statement", "d001", "--lang", "zh")
            self.assertIn("## 輸入", out)
            rc, out = self.run_cli(ws, "statement", "d001", "--lang", "bi")
            self.assertIn("中文對照", out)


if __name__ == "__main__":
    unittest.main()
