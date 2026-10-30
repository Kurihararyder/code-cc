"""更新程式之後，舊版建立的工作區（既有的學習進度）要能照常讀寫，而且不會被弄壞。
範本是舊版程式實際產生的（見 tests/fixtures/README.md）。"""
import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from cpe_coach import cli, web
from cpe_coach.store import Workspace

FIX = Path(__file__).parent / "fixtures"
FIXTURES = ["ws_v1_0_0", "ws_v2_1_0"]
READ_ONLY = [["today"], ["plan", "-m", "45"], ["weak"], ["calibrate"], ["stats"], ["review"], ["bank"], ["course"], ["course", "list"],
             ["roadmap"], ["eng"], ["past", "list"], ["vocab"], ["lang"], ["next"], ["mock", "status"]]


def run(root, *argv):
    old = os.getcwd()
    os.chdir(root)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = cli.main(list(argv))
    finally:
        os.chdir(old)
    return rc, buf.getvalue()


class UpgradeBase(unittest.TestCase):
    name = ""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "ws"
        shutil.copytree(FIX / self.name, self.root)
        self.before_state = json.loads((self.root / ".cpe" / "state.json").read_text(encoding="utf-8"))
        self.before_events = (self.root / ".cpe" / "events.jsonl").read_text(encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_read_only_commands_work_and_change_nothing(self):
        for argv in READ_ONLY:
            rc, out = run(self.root, *argv)
            self.assertEqual(rc, 0, f"cpe {' '.join(argv)} 失敗：{out[-300:]}")
        after = json.loads((self.root / ".cpe" / "state.json").read_text(encoding="utf-8"))
        for pid, p in self.before_state["problems"].items():
            for k, v in p.items():
                self.assertEqual(after["problems"][pid].get(k), v, f"{pid}.{k} 被改到了")
        self.assertEqual((self.root / ".cpe" / "events.jsonl").read_text(encoding="utf-8"), self.before_events)

    def test_old_state_gets_defaults_for_new_fields(self):
        ws = Workspace(self.root)
        st = ws.state()
        for key in ("problems", "eng_done", "exams", "course"):
            self.assertIn(key, st)
        cfg = ws.config()
        for key in ("memory_mb", "statement_lang", "timeout_sec", "stage"):
            self.assertIn(key, cfg)
        self.assertEqual(cfg["statement_lang"], "auto")

    def test_web_api_reads_old_workspace(self):
        app = web.App(self.root, 0)
        pid = sorted(self.before_state["problems"])[0]
        for fn in (app.state, app.dashboard, app.course_map, lambda: app.unit(None), app.stats, lambda: app.plan(30), app.calibration, app.weakness,
                   app.eng_list, app.past_list, app.vocab_list, app.settings, lambda: app.search("d0"), lambda: app.problem(pid), lambda: app.chat(pid)):
            fn()
        self.assertTrue(app.dashboard()["stats"]["solved"] >= 1)

    def test_progress_is_visible_and_judging_still_works(self):
        pid = next(p for p, v in self.before_state["problems"].items() if v.get("first_pass"))
        rc, out = run(self.root, "test", pid)
        self.assertEqual(rc, 0, out)
        self.assertIn("AC", out)
        st = json.loads((self.root / ".cpe" / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(st["problems"][pid]["first_pass"], self.before_state["problems"][pid]["first_pass"])      # 第一次通過的時間不會被覆蓋
        self.assertGreaterEqual(st["problems"][pid]["passes"], self.before_state["problems"][pid]["passes"] + 1)

    def test_due_review_is_still_due_and_advances(self):
        ws = Workspace(self.root)
        due = [pid for pid, p in ws.state()["problems"].items() if p.get("review_due") is not None and p["review_due"] < ws.now()]
        self.assertTrue(due, "範本裡應該有一題已到期的重練")
        rc, out = run(self.root, "plan", "-m", "30")
        self.assertIn(due[0], out)
        rc, out = run(self.root, "test", due[0])
        self.assertEqual(rc, 0)
        self.assertGreaterEqual(Workspace(self.root).state()["problems"][due[0]]["review_stage"], 1)

    def test_export_and_restore_roundtrip(self):
        z = Path(self.tmp.name) / "b.zip"
        rc, out = run(self.root, "export", "-o", str(z))
        self.assertEqual(rc, 0, out)
        other = Path(self.tmp.name) / "restored"
        rc, out = run(Path(self.tmp.name), "restore", str(z), "--dir", str(other))
        self.assertEqual(rc, 0, out)
        got = json.loads((other / ".cpe" / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(got["problems"], self.before_state["problems"])

    def test_new_features_work_on_old_workspace(self):
        rc, out = run(self.root, "new", "d003" if self.name == "ws_v2_1_0" else "uva458")
        self.assertIn(rc, (0, 2))                         # 已存在（2）或新建（0）都可以，不能崩潰
        rc, out = run(self.root, "past", "show", "2020-10-20")
        self.assertEqual(rc, 0, out)
        rc, out = run(self.root, "lang", "en")
        self.assertEqual(rc, 0, out)


class UpgradeFromV1(UpgradeBase):
    name = "ws_v1_0_0"


class UpgradeFromV21(UpgradeBase):
    name = "ws_v2_1_0"

    def test_drill_statements_and_language(self):
        rc, out = run(self.root, "statement", "d001")
        self.assertEqual(rc, 0, out)
        rc, out = run(self.root, "statement", "d001", "--lang", "en")
        self.assertIn("## Input", out)

    def test_course_position_is_defaulted_not_lost(self):
        st = Workspace(self.root).state()
        self.assertEqual(st["course"]["unit"], self.before_state["course"]["unit"])


del UpgradeBase                                   # 基底類別本身不要被當成測試執行

if __name__ == "__main__":
    unittest.main()
