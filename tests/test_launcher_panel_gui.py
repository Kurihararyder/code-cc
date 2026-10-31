"""控制台（圖形介面）的「今天」摘要卡與新的維護工具：真的開視窗、用程式按按鈕、操作對話框。沒有 tkinter 或開不了視窗時略過（CI 設 CPE_REQUIRE_GUI=1 會改成失敗）。"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import test_launcher_gui as _g  # noqa: E402
from test_launcher_gui import GuiBase, texts, walk  # noqa: E402
from test_launcher_panel_tools import HAS_OPENSSL, old_solved_workspace  # noqa: E402

from cpe_coach.launcher import server  # noqa: E402

try:
    import tkinter as tk
    from cpe_coach.launcher import gui
except ImportError:                                                                    # 沒有 tkinter：setUpModule 會整組略過
    tk = gui = None

setUpModule = _g.setUpModule                                                          # 沒有 tkinter／開不了視窗時整組略過（和 test_launcher_gui 一樣的規則）


class PanelBase(GuiBase):
    def setUp(self):
        super().setUp()
        self.cfg = self.install()
        self.opened = []
        m = mock.patch.object(server, "open_ui", side_effect=lambda url, cfg, plat, log=None: self.opened.append(url) or "browser")
        m.start()
        self.addCleanup(m.stop)

    def text_widgets(self, root):
        return " ".join(w.get("1.0", "end") for w in walk(root) if isinstance(w, tk.Text))


class TodayCard(PanelBase):
    def test_card_shows_due_reviews_and_updates_when_data_arrives(self):
        old_solved_workspace(self.ws)
        app = self.open()
        p = app.view
        self.assertTrue(app.pump(lambda: "記憶快要退了" in " ".join(texts(p.content)), 30), texts(p.content))
        self.assertIn("2 題", " ".join(texts(p.content)))
        self.assertEqual(p.today_info["due"], 2)

    def test_card_for_a_brand_new_learner_is_encouraging_not_an_error(self):
        app = self.open()
        p = app.view
        self.assertTrue(app.pump(lambda: "還沒有解出過" in " ".join(texts(p.content)), 30), texts(p.content))
        self.assertNotIn("讀不到", " ".join(texts(p.content)))

    def test_review_button_opens_the_study_page_when_the_service_is_running(self):
        app = self.open()
        p = app.view
        p.btn_main.invoke()
        self.assertTrue(app.pump(lambda: p.status.running and not p.busy, 40))
        self.opened.clear()
        p.btn_review.invoke()
        self.assertEqual(self.opened, [f"http://127.0.0.1:{self.port}/#/study/insights"])
        p.btn_plan.invoke()
        self.assertEqual(self.opened[-1], f"http://127.0.0.1:{self.port}/#/home")

    def test_review_button_starts_the_service_first_when_it_is_closed(self):
        app = self.open()
        p = app.view
        self.assertEqual(p.status.state, "stopped")
        p.btn_review.invoke()
        self.assertTrue(app.pump(lambda: p.status.running and not p.busy, 40))
        self.assertEqual(self.opened, [f"http://127.0.0.1:{self.port}/#/study/insights"])

    def test_starting_normally_still_opens_the_plain_address(self):
        app = self.open()
        p = app.view
        p.btn_main.invoke()
        self.assertTrue(app.pump(lambda: p.status.running and not p.busy, 40))
        self.assertEqual(self.opened, [f"http://127.0.0.1:{self.port}/"])

    def test_leaving_the_home_tab_and_closing_do_not_leave_timers_or_errors(self):
        app = self.open()
        p = app.view
        self.assertTrue(app.pump(lambda: bool(p.today_info), 30))
        p.show_tab("tools")
        p.show_tab("home")
        app.root.update()
        app.quit()
        self.gui = None


class ToolsLayout(PanelBase):
    def test_all_buttons_and_the_output_box_fit_in_the_window(self):
        app = self.open()
        p = app.view
        p.show_tab("tools")
        app.root.update()
        h = app.root.winfo_height()
        for key, b in p.tool_btns.items():
            self.assertTrue(b.winfo_ismapped(), key)
            self.assertLessEqual(b.winfo_rooty() + b.winfo_height(), app.root.winfo_rooty() + h, key)
        self.assertGreaterEqual(p.out.winfo_height(), 60)                              # 輸出框不能被按鈕擠沒了
        self.assertLessEqual(p.out.winfo_rooty() + p.out.winfo_height(), app.root.winfo_rooty() + h + 2)

    def test_pointing_at_a_button_shows_what_it_does(self):
        app = self.open()
        p = app.view
        p.show_tab("tools")
        app.root.update()                                                              # 沒顯示出來的視窗收不到滑鼠事件
        self.assertEqual(p.tool_hint.cget("text"), p.TOOL_HINT)
        p.tool_btns["sync"].event_generate("<Enter>", x=4, y=4, when="now")
        app.root.update()
        self.assertIn("同一個資料夾", p.tool_hint.cget("text"))
        p.tool_btns["sync"].event_generate("<Leave>", x=4, y=4, when="now")
        app.root.update()
        self.assertEqual(p.tool_hint.cget("text"), p.TOOL_HINT)


class NewTools(PanelBase):
    def test_privacy_button_lists_the_data(self):
        app = self.open()
        p = app.view
        p.show_tab("tools")
        p.tool_btns["privacy"].invoke()
        self.assertTrue(app.pump(lambda: not p.busy and "學習資料位置" in self.text_widgets(p.content), 30))

    def test_sync_button_asks_for_a_folder_and_reports(self):
        app = self.open()
        p = app.view
        p.show_tab("tools")
        shared = self.t.path / "shared"
        with mock.patch.object(gui.filedialog, "askdirectory", return_value=str(shared)):
            p.tool_btns["sync"].invoke()
            self.assertTrue(app.pump(lambda: not p.busy and "同步完成" in self.text_widgets(p.content), 30))
        self.assertTrue((shared / "cpe-sync").is_dir())

    def test_sync_button_does_nothing_when_you_cancel_the_folder_dialog(self):
        app = self.open()
        p = app.view
        p.show_tab("tools")
        with mock.patch.object(gui.filedialog, "askdirectory", return_value=""):
            p.tool_btns["sync"].invoke()
        self.assertFalse(p.busy)
        self.assertNotIn("同步完成", self.text_widgets(p.content))

    def test_sync_warns_when_the_service_is_running_and_respects_no(self):
        app = self.open()
        p = app.view
        p.btn_main.invoke()
        self.assertTrue(app.pump(lambda: p.status.running and not p.busy, 40))
        p.show_tab("tools")
        self.boxes["askyesno"].clear()
        self.patch_box("askyesno", False)
        with mock.patch.object(gui.filedialog, "askdirectory", return_value=str(self.t.path / "shared2")):
            p.tool_btns["sync"].invoke()
        self.assertFalse((self.t.path / "shared2").exists())
        self.assertTrue(self.boxes["askyesno"])

    def test_reminder_button_shows_the_plan_and_installs_only_after_yes(self):
        app = self.open()
        p = app.view
        p.show_tab("tools")
        with mock.patch("cpe_coach.reminder.apply_install", return_value=(True, "已安裝")) as ap:
            self.patch_box("askyesno", False)
            p.tool_btns["remind"].invoke()
            self.assertEqual(ap.call_count, 0)
            self.assertIn("remind check", self.text_widgets(p.content))
            self.patch_box("askyesno", True)
            p.tool_btns["remind"].invoke()
            self.assertTrue(app.pump(lambda: not p.busy and "已安裝每天 19:30" in self.text_widgets(p.content), 30))
            self.assertEqual(ap.call_count, 1)

    def test_reminder_failure_is_reported_in_the_output_box(self):
        app = self.open()
        p = app.view
        p.show_tab("tools")
        with mock.patch("cpe_coach.reminder.apply_install", return_value=(False, "沒有 crontab")):
            p.tool_btns["remind"].invoke()
            self.assertTrue(app.pump(lambda: not p.busy and "✗" in self.text_widgets(p.content) and "沒有 crontab" in self.text_widgets(p.content), 30))

    @unittest.skipUnless(HAS_OPENSSL, "沒有 openssl")
    def test_encrypted_backup_button_uses_the_password_dialog(self):
        app = self.open()
        p = app.view
        p.show_tab("tools")
        with mock.patch.object(gui.Panel, "ask_password", return_value=None):
            p.tool_btns["backup_enc"].invoke()
        self.assertFalse(p.busy)                                                       # 取消 = 什麼都不做
        with mock.patch.object(gui.Panel, "ask_password", return_value="correct horse battery"):
            p.tool_btns["backup_enc"].invoke()
            self.assertTrue(app.pump(lambda: not p.busy and "已備份" in self.text_widgets(p.content), 30))
        self.assertEqual(len(list(self.plat.desktop_dir.glob("CPE進度備份-*.zip.enc"))), 1)

    def test_password_dialog_validates_length_and_match_then_returns_the_password(self):
        app = self.open()
        p = app.view
        steps = []

        def drive():
            top = [w for w in app.root.winfo_children() if isinstance(w, tk.Toplevel)][0]
            entries = [w for w in walk(top) if isinstance(w, tk.Entry)]
            btn = [w for w in walk(top) if isinstance(w, gui.Btn) and w.cget("text") == "備份"][0]
            msg = [w for w in walk(top) if isinstance(w, tk.Label) and w.cget("fg") == gui.PAL["bad"]][0]
            for e, v in ((entries[0], "short"), (entries[1], "short")):
                e.delete(0, "end")
                e.insert(0, v)
            btn.invoke()
            steps.append(msg.cget("text"))
            entries[0].delete(0, "end")
            entries[0].insert(0, "long enough pw")
            entries[1].delete(0, "end")
            entries[1].insert(0, "different one!")
            btn.invoke()
            steps.append(msg.cget("text"))
            entries[1].delete(0, "end")
            entries[1].insert(0, "long enough pw")
            btn.invoke()
        app.root.after(150, drive)
        pw = p.ask_password()
        self.assertEqual(pw, "long enough pw")
        self.assertIn("至少 8", steps[0])
        self.assertIn("不一樣", steps[1])

    def test_password_dialog_cancel_returns_none(self):
        app = self.open()
        p = app.view

        def drive():
            top = [w for w in app.root.winfo_children() if isinstance(w, tk.Toplevel)][0]
            [w for w in walk(top) if isinstance(w, gui.Btn) and w.cget("text") == "取消"][0].invoke()
        app.root.after(150, drive)
        self.assertIsNone(p.ask_password())


if __name__ == "__main__":
    unittest.main()
