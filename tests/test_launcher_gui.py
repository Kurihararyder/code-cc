"""圖形介面的安裝精靈與控制台：真的開視窗（Linux 用 Xvfb 虛擬螢幕），用程式去按按鈕，走完安裝 → 開啟／關閉 → 更新 → 解除安裝。
沒有 tkinter 或開不了視窗時整組略過；在 CI 設 CPE_REQUIRE_GUI=1 就會改成失敗（確保 CI 真的有測到）。"""
import os
import sys
import threading
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
from launcher_helpers import HAVE_GIT, TempDir, bump_version, clean_registry, copy_app_tree, free_port, git, isolated_env, make_origin  # noqa: E402

from cpe_coach import __version__  # noqa: E402
from cpe_coach.launcher import config as cfgmod  # noqa: E402
from cpe_coach.launcher import engine, server, source  # noqa: E402
from cpe_coach.launcher.envcheck import Ctx  # noqa: E402
from cpe_coach.launcher.osinfo import detect  # noqa: E402

try:
    import tkinter as tk
    from cpe_coach.launcher import gui
except ImportError:
    tk = gui = None


def setUpModule():
    why = ""
    if tk is None:
        why = "沒有 tkinter"
    else:
        try:
            r = tk.Tk()
            r.destroy()
        except tk.TclError as e:
            why = f"開不了視窗：{e}"
    if why:
        if os.environ.get("CPE_REQUIRE_GUI"):
            raise RuntimeError("CPE_REQUIRE_GUI 已設定，但圖形介面不能用：" + why)
        raise unittest.SkipTest(why)


def walk(w):
    yield w
    for c in w.winfo_children():
        yield from walk(c)


def texts(root):
    out = []
    for w in walk(root):
        try:
            t = w.cget("text")
        except tk.TclError:
            continue
        if t:
            out.append(str(t))
    return out


def find_btn(root, text):
    for w in walk(root):
        if isinstance(w, gui.Btn) and w.cget("text") == text:
            return w
    raise AssertionError(f"找不到按鈕「{text}」：{[w.cget('text') for w in walk(root) if isinstance(w, gui.Btn)]}")


class GuiBase(unittest.TestCase):
    def setUp(self):
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)
        self.t = TempDir()
        self.addCleanup(self.t.cleanup)
        self.env = isolated_env(self.t.path)
        self.addCleanup(clean_registry, self.env)
        p = mock.patch.dict(os.environ, self.env)
        p.start()
        self.addCleanup(p.stop)
        self.plat = detect(env=self.env, home=Path(self.env["HOME"]))
        self.tree = copy_app_tree(self.t.path / "tree")
        self.ctx = self.make_ctx()
        self.app_dir, self.ws, self.port = self.t.path / "app", self.t.path / "ws", free_port()
        self.boxes = {}
        for name, ret in (("askyesno", True), ("showinfo", None), ("showwarning", None), ("showerror", None), ("askyesnocancel", True)):
            self.patch_box(name, ret)
        b = mock.patch.object(engine, "find_bundle", return_value=self.tree)
        b.start()
        self.addCleanup(b.stop)
        self.gui = None
        self.addCleanup(self.close)

    def make_ctx(self, **over):
        base = dict(plat=self.plat, net=lambda *a: False, bundle=self.tree, which=lambda n: "/usr/bin/" + n, has_tk=lambda: True, port_free=lambda p: True,
                    run=lambda cmd, t=60, env=None: (0, "git version 2.43.0"))
        base.update(over)
        return Ctx(**base)

    def patch_box(self, name, ret):
        calls = []

        def fake(*a, **k):
            calls.append((a, k))
            return ret() if callable(ret) else ret
        m = mock.patch.object(gui.messagebox, name, side_effect=fake)
        m.start()
        self.addCleanup(m.stop)
        self.boxes[name] = calls

    def open(self, **kw) -> "gui.GuiApp":
        self.gui = gui.GuiApp(self.plat, self.ctx)
        self.gui.start(**kw)
        self.gui.root.update()
        return self.gui

    def close(self):
        cfg = cfgmod.load(self.plat.launcher_home)
        if cfg:
            try:
                server.stop(cfg, self.plat)
            except Exception:
                pass
        if self.gui is not None:
            try:
                self.gui.quit()
            except Exception:
                pass
        self.gui = None
        import gc
        gc.collect()                                                                # tkinter 物件要在主執行緒回收

    def install(self, **kw):
        o = engine.InstallOptions(app_dir=self.app_dir, workspace=self.ws, source="bundle", bundle=self.tree, python=engine.base_python(), port=self.port,
                                  desktop=False, menu=False, add_path=False)
        for k, v in kw.items():
            setattr(o, k, v)
        cfg = engine.install(o, self.plat, self.ctx, engine.Reporter())
        cfg.options["check_update_on_open"] = False                                  # 測試預設不在背景連網；要測的測試自己打開
        cfgmod.save(self.plat.launcher_home, cfg)
        return cfg

    def run_wizard_to_options(self, app):
        w = app.view
        w.btn_next.invoke()
        self.assertTrue(app.pump(lambda: bool(w.checks) and not w.busy, 30))
        w.btn_next.invoke()
        self.assertEqual(w.page, 2)
        return self.fill_options(w)

    def fill_options(self, w):
        w.v_app.set(str(self.app_dir))
        w.v_ws.set(str(self.ws))
        w.v_port.set(str(self.port))
        w.v_source.set("bundle")
        w.v_desktop.set(False)
        w.v_menu.set(False)
        w.v_path.set(False)
        return w


class WizardTests(GuiBase):
    def test_walks_every_page_and_installs(self):
        app = self.open()
        w = app.view
        self.assertIsInstance(w, gui.Wizard)
        self.assertEqual(w.page, 0)
        self.assertTrue(any("歡迎使用" in t for t in texts(app.root)))
        self.assertTrue(w.btn_next.enabled and not w.btn_back.enabled)
        w.btn_next.invoke()
        self.assertTrue(app.pump(lambda: bool(w.checks) and not w.busy, 30))
        shown = " ".join(texts(w.check_box))
        for label in ("Python", "git", "磁碟空間", "網頁服務的埠"):
            self.assertIn(label, shown)
        self.assertTrue(w.btn_next.enabled)
        w.btn_next.invoke()
        self.assertEqual(w.page, 2)
        self.assertTrue(w.btn_back.enabled)
        self.fill_options(w)
        w.btn_next.invoke()
        self.assertEqual(w.page, 3)
        self.assertTrue(app.pump(lambda: w.page == 4, 90))
        self.assertIsNotNone(w.cfg, w.error)
        self.assertEqual(w.cfg.version, __version__)
        self.assertTrue(any("安裝完成" in t for t in texts(app.root)))
        self.assertTrue(any(t.startswith("✓  ") for t in texts(app.root)))
        st = engine.installed_state(self.plat)
        self.assertTrue(st.installed and st.healthy, st.problems)
        log = (self.plat.launcher_home / "logs" / "launcher.log").read_text(encoding="utf-8")
        for step in engine.STEPS_INSTALL:
            self.assertIn("== " + step, log)
        w.btn_next.invoke()                                                        # 開啟控制台
        self.assertIsInstance(app.view, gui.Panel)

    def test_blocking_problem_keeps_next_disabled_and_explains(self):
        self.ctx = self.make_ctx(py_version=(3, 7, 0))
        app = self.open()
        w = app.view
        w.btn_next.invoke()
        self.assertTrue(app.pump(lambda: bool(w.checks) and not w.busy, 30))
        self.assertFalse(w.btn_next.enabled)
        self.assertTrue(any("3.7.0" in t for t in texts(w.check_box)))
        self.assertTrue(any("✗" in t for t in texts(w.check_box)))
        self.assertTrue(any("必須先解決" in t for t in texts(app.root)))

    def test_fixable_problems_show_a_checkbox_with_the_right_default(self):
        self.ctx = self.make_ctx(which=lambda n: None if n in ("git", "g++") else "/usr/bin/" + n)
        with mock.patch.object(gui.envcheck, "fix_plan", return_value=engine.envcheck.FixPlan([["true"]], "會跳出授權視窗")):
            app = self.open()
            w = app.view
            w.btn_next.invoke()
            self.assertTrue(app.pump(lambda: bool(w.checks) and not w.busy, 30))
        self.assertEqual(sorted(w.fix_vars), ["install_git", "install_gpp"])
        self.assertTrue(w.fix_vars["install_git"].get())
        self.assertFalse(w.fix_vars["install_gpp"].get())
        self.assertTrue(any("自動安裝 git" in t for t in texts(w.check_box)))
        w.btn_next.invoke()
        self.fill_options(w)
        self.assertTrue(w.collect_options())
        self.assertEqual(w.opts.fixes, ["install_git"])

    def test_option_validation_blocks_bad_input_with_a_clear_message(self):
        app = self.open()
        w = self.run_wizard_to_options(app)
        warn = self.boxes["showwarning"]

        def attempt(**vars_):
            before = len(warn)
            old = {k: getattr(w, k).get() for k in vars_}
            for k, v in vars_.items():
                getattr(w, k).set(v)
            ok = w.collect_options()
            for k, v in old.items():
                getattr(w, k).set(v)
            return ok, (warn[-1][0][1] if len(warn) > before else "")
        ok, msg = attempt(v_app="")
        self.assertFalse(ok)
        ok, msg = attempt(v_app="relative/path")
        self.assertFalse(ok)
        self.assertIn("完整的路徑", msg)
        ok, msg = attempt(v_ws=str(self.app_dir / "inside"))
        self.assertFalse(ok)
        self.assertIn("互相包含", msg)
        busy = self.t.path / "busy"
        busy.mkdir()
        (busy / "x.txt").write_text("x")
        ok, msg = attempt(v_app=str(busy))
        self.assertFalse(ok)
        self.assertIn("不是空的", msg)
        ok, msg = attempt(v_port="80")
        self.assertFalse(ok)
        self.assertIn("1024", msg)
        ok, msg = attempt(v_port="abc")
        self.assertFalse(ok)
        ok, msg = attempt(v_restore=str(self.t.path / "nope.zip"))
        self.assertFalse(ok)
        self.assertIn("找不到備份檔", msg)
        ok, msg = attempt()
        self.assertTrue(ok)
        self.assertEqual(w.opts.port, self.port)

    def test_failed_install_shows_the_reason_and_can_be_retried(self):
        app = self.open()
        w = self.run_wizard_to_options(app)
        with mock.patch.object(engine, "run_cpe", side_effect=engine.EngineError("硬碟壞掉了")):
            w.btn_next.invoke()
            self.assertTrue(app.pump(lambda: w.page == 4, 90))
        self.assertIsNone(w.cfg)
        self.assertTrue(any("安裝沒有完成" in t for t in texts(app.root)))
        self.assertIn("硬碟壞掉了", self.text_widgets(w.body))
        self.assertFalse(self.app_dir.exists() or self.ws.exists())
        self.assertEqual(w.btn_next.cget("text"), "重試")
        w.btn_next.invoke()                                                         # 重試 → 回到環境檢測
        self.assertEqual(w.page, 1)
        self.assertTrue(app.pump(lambda: bool(w.checks) and not w.busy, 30))
        w.btn_next.invoke()
        self.fill_options(w)
        w.btn_next.invoke()
        self.assertTrue(app.pump(lambda: w.page == 4, 90))
        self.assertIsNotNone(w.cfg, w.error)

    def text_widgets(self, root):
        return " ".join(w.get("1.0", "end") for w in walk(root) if isinstance(w, tk.Text))

    def test_cancel_during_install_rolls_everything_back(self):
        app = self.open()
        w = self.run_wizard_to_options(app)
        gate = threading.Event()
        real = source.fetch

        def slow_fetch(*a, **k):
            gate.wait(30)
            return real(*a, **k)
        with mock.patch.object(source, "fetch", side_effect=slow_fetch):
            w.btn_next.invoke()
            self.assertTrue(app.pump(lambda: w.page == 3 and getattr(w, "step_idx", -1) >= 2, 30))
            w.btn_cancel.invoke()                                                   # 取消（確認視窗自動按「是」）
            self.assertTrue(w.cancel.is_set())
            self.assertFalse(w.btn_cancel.enabled)
            gate.set()
            self.assertTrue(app.pump(lambda: w.page == 4, 60))
        self.assertIsNone(w.cfg)
        self.assertIn("已取消", w.error)
        self.assertFalse(self.app_dir.exists() or self.ws.exists())

    def test_already_installed_welcome_offers_open_repair_uninstall(self):
        self.install()
        app = self.open(install_only=True)
        w = app.view
        self.assertIsInstance(w, gui.Wizard)
        self.assertTrue(any("偵測到已經安裝" in t for t in texts(app.root)))
        for name in ("開啟控制台", "修復", "解除安裝"):
            find_btn(app.root, name)
        self.assertEqual(w.btn_next.cget("text"), "重新安裝 ›")
        self.assertEqual((w.v_app.get(), w.v_ws.get()), (str(self.app_dir), str(self.ws)))              # 重新安裝的預設值是上一次的位置
        find_btn(app.root, "開啟控制台").invoke()
        self.assertIsInstance(app.view, gui.Panel)

    def test_default_start_goes_to_the_panel_when_installed_else_the_wizard(self):
        app = self.open()
        self.assertIsInstance(app.view, gui.Wizard)
        app.quit()
        self.install()
        self.gui = None
        app = self.open()
        self.assertIsInstance(app.view, gui.Panel)

    def test_advanced_options_toggle(self):
        app = self.open()
        w = self.run_wizard_to_options(app)
        w.toggle_adv()
        app.root.update()
        self.assertTrue(w.adv.winfo_ismapped())
        self.assertIn("程式來源", " ".join(texts(w.adv)))
        w.toggle_adv()
        app.root.update()
        self.assertFalse(w.adv.winfo_ismapped())

    def test_closing_the_window_mid_install_asks_first(self):
        app = self.open()
        w = self.run_wizard_to_options(app)
        w.busy = True
        w.page = 3
        self.boxes["askyesno"].clear()
        self.assertIs(w.on_close(), False)
        self.assertEqual(len(self.boxes["askyesno"]), 1)
        w.busy = False


class PanelTests(GuiBase):
    def setUp(self):
        super().setUp()
        self.cfg = self.install()
        self.opened = []
        m = mock.patch.object(server, "open_ui", side_effect=lambda url, cfg, plat, log=None: self.opened.append(url) or "browser")
        m.start()
        self.addCleanup(m.stop)

    def test_open_then_close_buttons_start_and_stop_the_real_service(self):
        app = self.open()
        p = app.view
        self.assertIsInstance(p, gui.Panel)
        self.assertEqual(p.btn_main.cget("text"), "▶  開啟")
        self.assertIn("已關閉", texts(p.content))
        self.assertFalse(p.btn_show.winfo_ismapped())
        p.btn_main.invoke()
        self.assertTrue(app.pump(lambda: p.status.running and not p.busy, 40))
        self.assertEqual(p.btn_main.cget("text"), "■  關閉")
        self.assertIn("執行中", texts(p.content))
        self.assertEqual(self.opened, [f"http://127.0.0.1:{self.port}/"])
        self.assertEqual(server.probe(self.port)["pid"], p.status.pid)
        app.root.update()
        self.assertTrue(p.btn_show.winfo_ismapped())
        p.btn_show.invoke()
        self.assertEqual(len(self.opened), 2)
        pid = p.status.pid
        p.btn_main.invoke()
        self.assertTrue(app.pump(lambda: p.status.state == "stopped" and not p.busy, 40))
        self.assertEqual(p.btn_main.cget("text"), "▶  開啟")
        self.assertFalse(server.pid_alive(pid))
        self.assertIsNone(server.probe(self.port))

    def test_status_follows_a_service_started_or_stopped_elsewhere(self):
        app = self.open()
        p = app.view
        server.start(self.cfg, self.plat)                                           # 別的地方（例如指令列）開的
        p.refreshing = False
        p.refresh()
        self.assertTrue(app.pump(lambda: p.status.running, 20))
        server.stop(self.cfg, self.plat)
        p.refreshing = False
        p.refresh()
        self.assertTrue(app.pump(lambda: p.status.state == "stopped", 20))

    def test_open_does_not_launch_the_browser_when_turned_off(self):
        self.cfg.options["open_browser"] = False
        cfgmod.save(self.plat.launcher_home, self.cfg)
        app = self.open()
        p = app.view
        p.btn_main.invoke()
        self.assertTrue(app.pump(lambda: p.status.running and not p.busy, 40))
        self.assertEqual(self.opened, [])

    def test_failed_start_shows_an_error_and_recovers(self):
        app = self.open()
        p = app.view
        with mock.patch.object(server, "start", side_effect=server.ServerError("埠被鎖住")):
            p.btn_main.invoke()
            self.assertTrue(app.pump(lambda: not p.busy, 20))
        self.assertTrue(any("埠被鎖住" in str(c[0][1]) for c in self.boxes["showerror"]))
        self.assertTrue(p.btn_main.enabled)
        self.assertEqual(p.btn_main.cget("text"), "▶  開啟")

    def test_autostart_option_starts_the_service_on_open(self):
        self.cfg.options["autostart_server"] = True
        cfgmod.save(self.plat.launcher_home, self.cfg)
        app = self.open()
        p = app.view
        self.assertTrue(app.pump(lambda: p.status.running and not p.busy, 40))

    def test_settings_are_saved_to_the_launcher_file(self):
        app = self.open()
        p = app.view
        p.show_tab("settings")
        p.vars["open_browser"].set(False)
        p.vars["app_window"].set(False)
        p.vars["autostart_server"].set(True)
        p.vars["stop_on_exit"].set("stop")
        newp = str(free_port())
        p.vars["port"].set(newp)
        saved = cfgmod.load(self.plat.launcher_home)
        self.assertEqual((saved.opt("open_browser"), saved.opt("app_window"), saved.opt("autostart_server"), saved.opt("stop_on_exit"), saved.port),
                         (False, False, True, "stop", int(newp)))
        p.vars["check_update_on_open"].set(True)
        self.assertTrue(cfgmod.load(self.plat.launcher_home).opt("check_update_on_open"))
        p.vars["port"].set("12")                                                    # 不合法的埠不會存
        self.assertEqual(cfgmod.load(self.plat.launcher_home).port, int(newp))

    def test_maintenance_tools(self):
        app = self.open()
        p = app.view
        p.show_tab("tools")
        self.assertEqual(sorted(p.tool_btns), ["backup", "doctor", "log", "repair", "uninstall", "update"])
        p.tool_btns["doctor"].invoke()
        self.assertTrue(app.pump(lambda: not p.busy and "安裝診斷" in self.text_widgets(p.content), 30))
        p.tool_btns["backup"].invoke()
        self.assertTrue(app.pump(lambda: not p.busy and "已備份" in self.text_widgets(p.content), 30))
        zips = list(self.plat.desktop_dir.glob("CPE進度備份-*.zip"))
        self.assertEqual(len(zips), 1)
        self.assertTrue(zipfile.is_zipfile(zips[0]))
        p.tool_btns["log"].invoke()
        self.assertIn("服務紀錄", self.text_widgets(p.content))
        (self.app_dir / "cpe_coach" / "launcher" / "engine.py").unlink()
        p.tool_btns["repair"].invoke()
        self.assertTrue(app.pump(lambda: not p.busy and "修復完成" in self.text_widgets(p.content), 60))
        self.assertEqual(source.verify_import(self.cfg.python, self.app_dir), __version__)

    def text_widgets(self, root):
        return " ".join(w.get("1.0", "end") for w in walk(root) if isinstance(w, tk.Text))

    def test_update_check_reports_honestly_when_offline(self):
        app = self.open()
        p = app.view
        p.show_tab("tools")
        with mock.patch.dict(os.environ, {"CPE_API_COMMIT_URL": f"http://127.0.0.1:{free_port()}/x"}):
            p.tool_btns["update"].invoke()
            self.assertTrue(app.pump(lambda: not p.busy and "連不上" in self.text_widgets(p.content), 30))

    def test_closing_with_a_running_service_asks_what_to_do(self):
        app = self.open()
        p = app.view
        p.btn_main.invoke()
        self.assertTrue(app.pump(lambda: p.status.running and not p.busy, 40))
        pid = p.status.pid
        self.boxes["askyesnocancel"].clear()
        with mock.patch.object(gui.messagebox, "askyesnocancel", return_value=None):
            app.on_close()
        self.assertTrue(app.root.winfo_exists())                                   # 取消 → 留在控制台
        self.assertTrue(server.pid_alive(pid))
        with mock.patch.object(gui.messagebox, "askyesnocancel", return_value=False):
            app.on_close()                                                          # 否 → 服務繼續跑、控制台關閉
        self.assertTrue(server.pid_alive(pid))
        self.gui = None
        self.assertTrue(server.probe(self.port))

    def test_closing_can_stop_the_service_automatically(self):
        self.cfg.options["stop_on_exit"] = "stop"
        cfgmod.save(self.plat.launcher_home, self.cfg)
        app = self.open()
        p = app.view
        p.btn_main.invoke()
        self.assertTrue(app.pump(lambda: p.status.running and not p.busy, 40))
        pid = p.status.pid
        app.on_close()
        self.gui = None
        self.assertTrue(source_wait(lambda: not server.pid_alive(pid)))

    def test_uninstall_button_opens_the_uninstall_view(self):
        app = self.open()
        app.view.show_tab("tools")
        app.view.tool_btns["uninstall"].invoke()
        self.assertIsInstance(app.view, gui.UninstallView)
        find_btn(app.root, "取消").invoke()                                         # 取消 → 回到控制台
        self.assertIsInstance(app.view, gui.Panel)


@unittest.skipUnless(HAVE_GIT, "需要 git")
class PanelUpdate(GuiBase):
    def setUp(self):
        super().setUp()
        self.origin = make_origin(self.t.path)
        m = mock.patch.dict(os.environ, {"CPE_REPO_URL": str(self.origin), "CPE_INSTALL_BRANCH": "main"})
        m.start()
        self.addCleanup(m.stop)
        self.ctx = self.make_ctx(net=lambda *a: True)
        self.cfg = self.install(source="git", branch="main")

    def test_update_button_updates_and_restarts_the_panel(self):
        bump_version(self.origin, "9.9.9", "控制台更新測試")
        restarted = []
        app = self.open()
        p = app.view
        with mock.patch.object(gui.GuiApp, "restart", side_effect=lambda: restarted.append(1)):
            self.boxes["askyesno"].clear()
            p.show_tab("tools")
            p.tool_btns["update"].invoke()
            self.assertTrue(app.pump(lambda: restarted, 90))
        self.assertEqual(cfgmod.load(self.plat.launcher_home).version, "9.9.9")
        self.assertIn("控制台更新測試", " ".join(w.get("1.0", "end") for w in walk(app.root) if isinstance(w, tk.Text)))
        self.assertTrue(self.boxes["showinfo"])

    def test_opening_the_panel_quietly_checks_for_a_new_version_and_shows_a_banner(self):
        self.cfg.options["check_update_on_open"] = True
        cfgmod.save(self.plat.launcher_home, self.cfg)
        bump_version(self.origin, "9.9.9")
        app = self.open()
        p = app.view
        self.assertTrue(app.pump(lambda: p.update_info is not None, 60))
        self.assertEqual(p.update_info["status"], "available")
        app.root.update()
        self.assertTrue(p.upd_card.winfo_ismapped())
        self.assertIn("立即更新", texts(p.upd_card))
        self.assertEqual(self.boxes["showerror"], [])                               # 悄悄的：沒有任何跳出視窗
        self.assertEqual(self.boxes["askyesno"], [])
        self.assertEqual(cfgmod.load(self.plat.launcher_home).version, __version__)   # 只是提示，不會自己更新

    def test_the_quiet_check_shows_nothing_when_up_to_date_or_offline(self):
        self.cfg.options["check_update_on_open"] = True
        cfgmod.save(self.plat.launcher_home, self.cfg)
        app = self.open()
        p = app.view
        self.assertTrue(app.pump(lambda: p.update_info is not None, 60))
        self.assertEqual(p.update_info["status"], "up_to_date")
        app.root.update()
        self.assertFalse(p.upd_card.winfo_ismapped())
        self.close()
        git(self.app_dir, "remote", "set-url", "origin", str(self.t.path / "gone"))     # 連不上
        app = self.open()
        p = app.view
        self.assertTrue(app.pump(lambda: p.update_info is not None, 60))
        self.assertEqual(p.update_info["status"], "unavailable")
        app.root.update()
        self.assertFalse(p.upd_card.winfo_ismapped())
        self.assertEqual(self.boxes["showerror"], [])

    def test_the_quiet_check_can_be_turned_off(self):
        bump_version(self.origin, "9.9.9")
        app = self.open()
        p = app.view
        self.assertIsNone(p.check_id)
        app.pump(lambda: False, 2.5)
        self.assertIsNone(p.update_info)

    def test_declining_the_update_prompt_changes_nothing(self):
        bump_version(self.origin, "9.9.9")
        app = self.open()
        p = app.view
        p.show_tab("tools")
        with mock.patch.object(gui.messagebox, "askyesno", return_value=False):
            p.tool_btns["update"].invoke()
            self.assertTrue(app.pump(lambda: not p.busy and p.update_info is not None, 60))
        self.assertEqual(cfgmod.load(self.plat.launcher_home).version, __version__)
        p.show_tab("home")
        app.root.update()
        self.assertTrue(p.upd_card.winfo_ismapped())                               # 首頁出現「有新版本」的提示
        self.assertIn("立即更新", texts(p.upd_card))


class UninstallTests(GuiBase):
    def setUp(self):
        super().setUp()
        self.cfg = self.install()
        (self.ws / "solutions" / "mine.py").write_text("x = 1\n", encoding="utf-8")

    def test_keep_progress_is_the_default_and_removes_the_program(self):
        app = self.open(uninstall_only=True)
        u = app.view
        self.assertIsInstance(u, gui.UninstallView)
        self.assertFalse(u.v_delete.get())
        self.assertTrue(any("你的學習進度" in t for t in texts(app.root)))
        u.btn_go.invoke()
        self.assertTrue(app.pump(lambda: u.done, 60))
        self.assertTrue(any("已解除安裝" in t for t in texts(app.root)))
        self.assertFalse(self.app_dir.exists())
        self.assertEqual((self.ws / "solutions" / "mine.py").read_text(encoding="utf-8"), "x = 1\n")
        self.assertIsNone(cfgmod.load(self.plat.launcher_home))
        self.assertEqual(u.btn_go.cget("text"), "結束")
        u.btn_go.invoke()
        self.assertFalse(self.gui.runner.alive)

    def test_deleting_progress_requires_the_confirmation_checkbox(self):
        app = self.open(uninstall_only=True)
        u = app.view
        u.v_delete.set(True)
        u.toggle()
        app.root.update()
        self.assertTrue(u.danger.winfo_ismapped())
        u.btn_go.invoke()
        self.assertTrue(self.boxes["showwarning"])
        self.assertTrue(self.app_dir.exists() and self.ws.exists())               # 沒勾確認：什麼都沒動
        u.v_confirm.set(True)
        u.v_backup.set(True)
        u.btn_go.invoke()
        self.assertTrue(app.pump(lambda: u.done, 60))
        self.assertFalse(self.ws.exists())
        zips = list(self.plat.desktop_dir.glob("CPE進度備份-*.zip"))
        self.assertEqual(len(zips), 1)
        with zipfile.ZipFile(zips[0]) as z:
            self.assertIn("solutions/mine.py", z.namelist())

    def test_switching_back_to_keep_hides_the_danger_options(self):
        app = self.open(uninstall_only=True)
        u = app.view
        u.v_delete.set(True)
        u.toggle()
        u.v_confirm.set(True)
        u.v_delete.set(False)
        u.toggle()
        app.root.update()
        self.assertFalse(u.danger.winfo_ismapped())
        self.assertFalse(u.v_confirm.get())

    def test_answering_no_to_the_final_question_changes_nothing(self):
        app = self.open(uninstall_only=True)
        u = app.view
        with mock.patch.object(gui.messagebox, "askyesno", return_value=False):
            u.btn_go.invoke()
        self.assertTrue(self.app_dir.exists())
        self.assertFalse(u.busy)

    def test_cancel_in_standalone_mode_quits(self):
        app = self.open(uninstall_only=True)
        find_btn(app.root, "取消").invoke()
        self.assertFalse(app.runner.alive)
        self.assertTrue(self.app_dir.exists())

    def test_a_failing_uninstall_reports_and_allows_retry(self):
        app = self.open(uninstall_only=True)
        u = app.view
        with mock.patch.object(engine, "uninstall", side_effect=engine.EngineError("有程式正在使用")):
            u.btn_go.invoke()
            self.assertTrue(app.pump(lambda: not u.busy, 30))
        self.assertIn("解除安裝沒有完成", texts(app.root))
        self.assertTrue(u.btn_go.enabled)
        self.assertTrue(self.app_dir.exists())


class WidgetTests(GuiBase):
    def test_button_respects_enabled_state_hover_and_keyboard(self):
        app = self.open()
        calls = []
        b = gui.Btn(app.root, app.th, "測試", lambda: calls.append(1), "primary")
        b.place(x=2, y=2)                                                           # 一定看得到（沒顯示出來的視窗收不到滑鼠事件）
        app.root.update()
        b.invoke()
        b.set_enabled(False)
        b.invoke()
        self.assertEqual(calls, [1])
        b.set_enabled(True)
        self.assertTrue(b.bind("<Return>") and b.bind("<space>"))                    # 鍵盤也能操作（Tab 對焦後按 Enter／空白鍵）
        self.assertEqual(str(b.cget("takefocus")), "1")
        b.event_generate("<Enter>")
        app.root.update()
        self.assertEqual(str(b.cget("bg")), gui.PAL["accent_hover"])
        b.event_generate("<Leave>")
        app.root.update()
        self.assertEqual(str(b.cget("bg")), gui.PAL["accent"])
        b.set_enabled(False)
        b.event_generate("<Enter>")
        app.root.update()
        self.assertEqual(str(b.cget("bg")), gui.PAL["surface3"])                     # 停用的按鈕不會有懸停效果

    def test_scroll_frame_shows_a_scrollbar_only_when_needed(self):
        app = self.open()
        f = gui.ScrollFrame(app.root, "#ffffff")
        f.place(x=0, y=0, width=200, height=100)
        for i in range(3):
            tk.Label(f.inner, text=str(i)).pack()
        app.root.update()
        self.assertFalse(f.bar.winfo_ismapped())
        for i in range(30):
            tk.Label(f.inner, text=str(i)).pack()
        app.root.update()
        app.root.update()
        self.assertTrue(f.bar.winfo_ismapped())

    def test_window_title_and_icon(self):
        app = self.open()
        self.assertIn("安裝精靈", app.root.title())
        self.assertIsNotNone(app.icon_img)
        self.assertEqual(app.icon_img.width(), 256)

    def test_short_text_helper(self):
        self.assertEqual(gui.short("abc", 10), "abc")
        s = gui.short("x" * 100, 20)
        self.assertEqual(len(s), 20)
        self.assertIn("…", s)


def source_wait(cond, timeout=20.0):
    import time
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.1)
    return cond()


if __name__ == "__main__":
    unittest.main()
