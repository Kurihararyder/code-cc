"""控制台的「今天」摘要與 2.7 的維護工具：引擎函式與文字模式選單（圖形介面的部分在 test_launcher_panel_gui.py）。"""
import json
import shutil
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
from test_launcher_cli import Base, FakeInput  # noqa: E402

from cpe_coach.launcher import config as cfgmod  # noqa: E402
from cpe_coach.launcher import engine, tui  # noqa: E402
from cpe_coach.store import Workspace  # noqa: E402

DAY = 86400.0
HAS_OPENSSL = shutil.which("openssl") is not None


def old_solved_workspace(ws_path: Path, pids=("d001", "d002"), days_ago=20):
    """在工作區寫進「days_ago 天前解出」的紀錄（直接寫事件檔，這樣現在就會有到期的複習）。"""
    import time
    ws = Workspace(Path(ws_path))
    ws.meta.mkdir(exist_ok=True)
    t = time.time() - days_ago * DAY
    with ws.events_path.open("a", encoding="utf-8") as f:
        for i, pid in enumerate(pids):
            f.write(json.dumps({"ts": t + i, "kind": "test", "problem": pid, "verdict": "AC", "lang": "py", "clean": True}) + "\n")
    st = ws.state()
    for pid in pids:
        st["problems"].setdefault(pid, {})["first_pass"] = t
    from cpe_coach.store import new_problem_state
    for pid in pids:
        d = new_problem_state()
        d["first_pass"] = t
        st["problems"][pid] = d
    ws.save_state(st)


class SummaryText(unittest.TestCase):
    def test_lines_cover_each_situation(self):
        blank = {"due": 0, "due_ids": [], "cards": 0, "goal": None, "goal_status": None, "days_since": None, "solved": 0}
        self.assertIn("還沒有解出過", engine.summary_lines(blank)[0])
        due = dict(blank, due=5, due_ids=["a", "b", "c"], cards=9)
        self.assertIn("5 題的記憶快要退了", engine.summary_lines(due)[0])
        self.assertIn("…", engine.summary_lines(due)[0])
        self.assertIn("沒有到期", engine.summary_lines(dict(blank, cards=3))[0])
        goal = dict(blank, cards=1, goal="目標 30 題（2027-01-01 前）：已 3 題，剩 40 天", goal_status="behind", days_since=5.2)
        lines = engine.summary_lines(goal)
        self.assertIn("趕不上", lines[1])
        self.assertIn("距離上次練習 5 天", lines[2])
        self.assertIn("回來動動手", lines[2])
        self.assertIn("今天已經練習過", engine.summary_lines(dict(blank, cards=1, days_since=0.2))[1])
        self.assertIn("讀不到", engine.summary_lines({"error": "X"})[0])


class EngineTools(Base):
    def setUp(self):
        super().setUp()
        self.assertEqual(self.install_cli()[0], 0)
        self.cfg = cfgmod.load(self.plat.launcher_home)

    def test_summary_on_a_fresh_and_a_used_workspace(self):
        s = engine.learning_summary(self.cfg)
        self.assertNotIn("error", s)
        self.assertEqual((s["due"], s["solved"], s["goal"]), (0, 0, None))
        old_solved_workspace(self.ws)
        s = engine.learning_summary(self.cfg)
        self.assertEqual((s["due"], s["solved"], s["cards"]), (2, 2, 2))
        self.assertGreater(s["days_since"], 19)
        self.assertEqual(sorted(s["due_ids"]), ["d001", "d002"])

    def test_summary_includes_the_goal(self):
        from cpe_coach import planning
        planning.set_goal(Workspace(self.ws), "2099-01-01", 50)
        s = engine.learning_summary(self.cfg)
        self.assertIn("目標 50 題", s["goal"])

    def test_summary_never_raises_even_if_the_workspace_is_broken(self):
        (self.ws / ".cpe" / "state.json").write_text("{not json", encoding="utf-8")
        s = engine.learning_summary(self.cfg)
        self.assertTrue("error" in s or "due" in s)                                   # 壞檔案會被備份並重建，或回報錯誤；兩種都不能丟例外
        bad = cfgmod.LauncherConfig(**{**self.cfg.__dict__, "workspace": str(self.t.path / "nope" / "deeper")}) if hasattr(cfgmod, "LauncherConfig") else self.cfg
        self.assertIsInstance(engine.learning_summary(bad), dict)

    @unittest.skipUnless(HAS_OPENSSL, "沒有 openssl")
    def test_encrypted_backup_roundtrip(self):
        from cpe_coach import exchange
        dest = engine.encrypted_backup_now(self.cfg, self.t.path / "out", "correct horse battery")
        self.assertTrue(dest.name.endswith(".zip.enc"))
        z = exchange.decrypt_to_zip(dest, "correct horse battery")
        import zipfile
        self.assertIn(".cpe/state.json", zipfile.ZipFile(z).namelist())
        with self.assertRaises(ValueError):
            exchange.decrypt_to_zip(dest, "wrong password!!")
        with self.assertRaises(ValueError):
            engine.encrypted_backup_now(self.cfg, self.t.path / "out", "short")

    def test_sync_now_reports_and_converges(self):
        old_solved_workspace(self.ws, ("d001",))
        shared = self.t.path / "shared"
        text = engine.sync_now(self.cfg, shared)
        self.assertIn("同步完成：本機新增 0 筆紀錄、共用資料夾新增 1 筆", text)
        self.assertIn("同步完成：本機新增 0 筆紀錄、共用資料夾新增 0 筆", engine.sync_now(self.cfg, shared))

    def test_reminder_plan_uses_the_installed_python_and_install_reports_failures(self):
        plan = engine.reminder_plan(self.cfg, 8, 15)
        self.assertIn(self.cfg.python, plan["text"])
        self.assertIn(str(self.ws), plan["text"])
        with mock.patch("cpe_coach.reminder.apply_install", return_value=(True, "已安裝")) as ap:
            self.assertIn("每天 08:15", engine.install_reminder(self.cfg, 8, 15))
            self.assertEqual(ap.call_count, 1)
        with mock.patch("cpe_coach.reminder.apply_install", return_value=(False, "沒有 crontab")):
            with self.assertRaises(engine.EngineError):
                engine.install_reminder(self.cfg)

    def test_privacy_text_lists_files_and_says_what_goes_out(self):
        t = engine.privacy_text(self.cfg)
        self.assertIn("state.json", t)
        self.assertIn("金鑰", t)


class TextMenu(Base):
    def make(self, answers):
        fi = FakeInput(answers)
        out = []
        t = tui.TUI(self.plat, self.ctx, inp=fi, out=out.append)
        self.out = out
        return t

    @property
    def text(self):
        return "\n".join(self.out)

    def test_menu_shows_the_today_lines_and_the_new_entries(self):
        self.install_cli()
        old_solved_workspace(self.ws)
        t = self.make(["12", "0"])
        self.assertEqual(t.panel(), 0)
        self.assertIn("今天：有 2 題的記憶快要退了", self.text)
        self.assertIn("加密備份", self.text)
        self.assertIn("資料與隱私", self.text)
        self.assertIn("學習資料位置", self.text)

    def test_sync_entry_asks_for_a_folder(self):
        self.install_cli()
        shared = self.t.path / "shared"
        t = self.make(["10", str(shared), "10", "", "0"])
        t.panel()
        self.assertIn("同步完成", self.text)
        self.assertIn("沒有輸入資料夾", self.text)
        self.assertTrue((shared / "cpe-sync").is_dir())

    @unittest.skipUnless(HAS_OPENSSL, "沒有 openssl")
    def test_encrypted_backup_entry_checks_the_password_length(self):
        self.install_cli()
        t = self.make(["9", "short", "9", "long enough password", "0"])
        t.panel()
        self.assertIn("密碼至少 8 個字元", self.text)
        self.assertIn("已加密備份", self.text)
        self.assertEqual(len(list(self.plat.desktop_dir.glob("CPE進度備份-*.zip.enc"))) + len(list(self.plat.home.glob("CPE進度備份-*.zip.enc"))), 1)

    def test_reminder_entry_only_installs_when_you_say_yes(self):
        self.install_cli()
        with mock.patch("cpe_coach.reminder.apply_install", return_value=(True, "已安裝")) as ap:
            t = self.make(["11", "n", "11", "y", "0"])
            t.panel()
        self.assertEqual(ap.call_count, 1)
        self.assertIn("已安裝每天 19:30", self.text)

    def test_a_failing_tool_shows_the_reason_and_returns_to_the_menu(self):
        self.install_cli()
        with mock.patch("cpe_coach.reminder.apply_install", return_value=(False, "沒有 crontab")):
            t = self.make(["11", "y", "12", "0"])
            self.assertEqual(t.panel(), 0)
        self.assertIn("✗ 沒有 crontab", self.text)
        self.assertIn("學習資料位置", self.text)


if __name__ == "__main__":
    unittest.main()
