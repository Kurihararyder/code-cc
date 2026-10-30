"""安裝精靈的指令列與文字模式：用腳本化的輸入走完整個流程（安裝 → 開啟 → 關閉 → 更新 → 解除安裝）。"""
import contextlib
import io
import os
import sys
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
from launcher_helpers import TempDir, clean_registry, copy_app_tree, free_port, isolated_env  # noqa: E402

from cpe_coach import __version__  # noqa: E402
from cpe_coach.launcher import __main__ as launcher_main  # noqa: E402
from cpe_coach.launcher import config as cfgmod  # noqa: E402
from cpe_coach.launcher import engine, server, tui  # noqa: E402
from cpe_coach.launcher.envcheck import Ctx  # noqa: E402
from cpe_coach.launcher.osinfo import detect  # noqa: E402


class Base(unittest.TestCase):
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
        b = mock.patch.object(engine, "find_bundle", return_value=self.tree)
        b.start()
        self.addCleanup(b.stop)
        self.app, self.ws, self.port = self.t.path / "app", self.t.path / "ws", free_port()
        self.addCleanup(self.stop_service)

    def make_ctx(self, **over):
        """環境固定：git、g++ 都有、tkinter 可用，所以精靈問的問題與順序不會因為執行測試的那台電腦而不同。"""
        base = dict(plat=self.plat, net=lambda *a: False, bundle=self.tree, which=lambda n: "/usr/bin/" + n, has_tk=lambda: True,
                    run=lambda cmd, t=60, env=None: (0, "git version 2.43.0"))
        base.update(over)
        return Ctx(**base)

    def stop_service(self):
        cfg = cfgmod.load(self.plat.launcher_home)
        if cfg:
            try:
                server.stop(cfg, self.plat)
            except Exception:
                pass

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = launcher_main.run(list(argv), self.plat, self.ctx)
        return rc, out.getvalue() + err.getvalue()

    def install_cli(self):
        return self.cli("install", "--yes", "--text", "--dir", str(self.app), "--workspace", str(self.ws), "--source", "bundle", "--port", str(self.port),
                        "--no-desktop", "--no-menu", "--no-path")


class Cli(Base):
    def test_status_before_install_says_so(self):
        rc, out = self.cli("status")
        self.assertEqual(rc, 1)
        self.assertIn("還沒有安裝", out)
        for cmd in ("open", "close", "update", "repair", "uninstall"):
            self.assertEqual(self.cli(cmd, "--yes", "--text")[0], 1, cmd)

    def test_doctor_prints_checks_without_installing_anything(self):
        rc, out = self.cli("doctor")
        self.assertEqual(rc, 0)
        self.assertIn("尚未安裝", out)
        self.assertIn("Python", out)
        self.assertIsNone(cfgmod.load(self.plat.launcher_home))

    def test_headless_install_open_close_update_uninstall(self):
        rc, out = self.install_cli()
        self.assertEqual(rc, 0, out)
        self.assertIn("安裝完成", out)
        self.assertEqual(cfgmod.load(self.plat.launcher_home).version, __version__)
        self.assertTrue((self.ws / ".cpe").is_dir())
        with mock.patch.object(server, "open_ui", return_value="browser") as opened:
            rc, out = self.cli("open", "--text")
        self.assertEqual(rc, 0, out)
        self.assertEqual(opened.call_count, 1)
        self.assertIn(f"http://127.0.0.1:{self.port}/", out)
        rc, out = self.cli("status")
        self.assertEqual(rc, 0)
        self.assertIn("執行中", out)
        rc, out = self.cli("close")
        self.assertEqual(rc, 0)
        self.assertIn("已關閉", out)
        self.assertEqual(self.cli("status")[0], 3)
        rc, out = self.cli("close")
        self.assertEqual(rc, 0)
        self.assertIn("原本就是關閉", out)
        with mock.patch.dict(os.environ, {"CPE_API_COMMIT_URL": f"http://127.0.0.1:{free_port()}/x"}):
            rc, out = self.cli("update", "--check")
        self.assertEqual(rc, 1)                                                     # 沒有網路：誠實說檢查不了
        rc, out = self.cli("uninstall", "--yes", "--text")
        self.assertEqual(rc, 0, out)
        self.assertIn("已解除安裝", out)
        self.assertIsNone(cfgmod.load(self.plat.launcher_home))
        self.assertTrue((self.ws / ".cpe").is_dir())

    def test_install_options_from_the_command_line(self):
        args = launcher_main.build_parser().parse_args(["install", "--yes", "--dir", "/a", "--workspace", "/b", "--source", "zip", "--port", "9000", "--fix", "git,gpp",
                                                       "--no-path", "--restore", "/r.zip"])
        o = launcher_main.options_from_args(self.plat, args)
        self.assertEqual((o.app_dir, o.workspace, o.source, o.port), (Path("/a"), Path("/b"), "zip", 9000))
        self.assertEqual(o.fixes, ["install_git", "install_gpp"])
        self.assertEqual((o.desktop, o.menu, o.add_path), (True, True, False))
        self.assertEqual(o.restore_from, Path("/r.zip"))

    def test_repair_command(self):
        self.install_cli()
        (self.app / "cpe_coach" / "launcher" / "engine.py").unlink()
        rc, out = self.cli("repair", "--text")
        self.assertEqual(rc, 0, out)
        from cpe_coach.launcher import source
        self.assertEqual(source.verify_import(cfgmod.load(self.plat.launcher_home).python, self.app), __version__)

    def test_uninstall_can_remove_the_workspace_after_a_backup(self):
        self.install_cli()
        bk = self.t.path / "bk"
        rc, out = self.cli("uninstall", "--yes", "--text", "--remove-workspace", "--backup-dir", str(bk))
        self.assertEqual(rc, 0, out)
        self.assertFalse(self.ws.exists())
        zips = list(bk.glob("*.zip"))
        self.assertEqual(len(zips), 1)
        self.assertTrue(zipfile.is_zipfile(zips[0]))

    def test_unexpected_errors_are_written_to_a_crash_log_not_lost(self):
        with mock.patch.object(launcher_main, "dispatch", side_effect=RuntimeError("意外")):
            rc, out = self.cli("doctor", "--text")
        self.assertEqual(rc, 70)
        self.assertIn("意外", out)
        self.assertIn("RuntimeError", (self.plat.launcher_home / "logs" / "crash.log").read_text(encoding="utf-8"))

    def test_ctrl_c_is_a_clean_exit(self):
        with mock.patch.object(launcher_main, "dispatch", side_effect=KeyboardInterrupt):
            self.assertEqual(self.cli("doctor", "--text")[0], 130)

    def test_detached_gui_launch_command(self):
        calls = []
        with mock.patch.object(launcher_main.subprocess, "Popen", side_effect=lambda cmd, **kw: calls.append((cmd, kw))):
            self.assertTrue(launcher_main.spawn_detached_gui(["install", "--detach-gui", "--dir", "x"]))
        cmd, kw = calls[0]
        self.assertTrue(cmd[1].endswith("cpe-panel.pyw"))
        self.assertEqual(cmd[2:], ["install", "--dir", "x"])
        self.assertTrue(kw.get("start_new_session") or kw.get("creationflags"))


class CpeCommand(Base):
    """cpe panel／cpe doctor（主程式的指令）與 zip 安裝的 cpe update。"""

    def run_cpe(self, *argv, stdin=None):
        from cpe_coach import cli
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            if stdin is None:
                rc = cli.main(list(argv))
            else:
                with mock.patch("builtins.input", side_effect=stdin):
                    rc = cli.main(list(argv))
        return rc, out.getvalue() + err.getvalue()

    def test_doctor_command(self):
        rc, out = self.run_cpe("doctor")
        self.assertEqual(rc, 0)
        self.assertIn("安裝診斷", out)

    def test_panel_command_never_installs_anything_without_a_person_answering(self):
        rc, out = self.run_cpe("panel", "--text", stdin=EOFError)
        self.assertEqual(rc, 130)
        self.assertFalse(self.plat.launcher_home.exists() and cfgmod.load(self.plat.launcher_home))
        self.assertFalse((self.plat.default_workspace).exists())

    def test_panel_command_opens_the_menu_when_installed(self):
        self.install_cli()
        rc, out = self.run_cpe("panel", "--text", stdin=["0"])
        self.assertEqual(rc, 0)
        self.assertIn("控制台", out)

    def test_cpe_update_works_for_a_zip_installed_copy(self):
        import subprocess
        from launcher_helpers import FileServer, make_zip, set_version
        srv = FileServer()
        self.addCleanup(srv.close)
        srv.publish(make_zip(self.tree, self.t.path / "v1.zip"), "a" * 40)
        urls = {"CPE_ARCHIVE_URL": srv.archive_url, "CPE_API_COMMIT_URL": srv.sha_url}
        with mock.patch.dict(os.environ, urls):
            rc, out = self.cli("install", "--yes", "--text", "--dir", str(self.app), "--workspace", str(self.ws), "--source", "zip", "--port", str(self.port),
                               "--no-desktop", "--no-menu", "--no-path")
            self.assertEqual(rc, 0, out)

        def installed_cpe(*args):
            env = dict(self.env, PYTHONPATH=str(self.app), **urls)
            p = subprocess.run([sys.executable, "-m", "cpe_coach"] + list(args), env=env, cwd=str(self.t.path), capture_output=True, timeout=120)
            return p.returncode, p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
        rc, out = installed_cpe("update", "--check")
        self.assertEqual(rc, 0, out)
        self.assertIn("已經是最新版", out)
        set_version(self.tree, "9.9.9", "zip 用 cpe update 更新")
        srv.publish(make_zip(self.tree, self.t.path / "v2.zip"), "b" * 40)
        rc, out = installed_cpe("update", "--check")
        self.assertEqual(rc, 0, out)
        self.assertIn("有", out)
        rc, out = installed_cpe("update")
        self.assertEqual(rc, 0, out)
        self.assertIn("9.9.9", out)
        self.assertIn("zip 用 cpe update 更新", out)
        self.assertEqual(cfgmod.load(self.plat.launcher_home).version, "9.9.9")
        rc, out = installed_cpe("update")
        self.assertIn("已經是最新版", out)
        rc, out = installed_cpe("--version")
        self.assertIn("9.9.9", out)


class FakeInput:
    """腳本化的輸入：依序回答，並記下每個問題（用來確認精靈真的有問）。"""

    def __init__(self, answers):
        self.answers, self.prompts = list(answers), []

    def __call__(self, prompt=""):
        self.prompts.append(prompt)
        if not self.answers:
            raise EOFError
        return self.answers.pop(0)


class Tui(Base):
    def make(self, answers, ctx=None):
        self.inp, self.out = FakeInput(answers), []
        return tui.TUI(self.plat, ctx or self.ctx, self.inp, self.out.append)

    @property
    def text(self):
        return "\n".join(self.out)

    def test_wizard_asks_the_questions_and_installs(self):
        t = self.make([str(self.app), str(self.ws), "n", "n", "n", "y", "n"])
        opts = engine.default_options(self.plat)
        opts.source, opts.bundle, opts.port = "bundle", self.tree, self.port
        rc = t.wizard(opts)
        self.assertEqual(rc, 0, self.text)
        self.assertIn("安裝完成", self.text)
        asked = " ".join(self.inp.prompts)
        for q in ("程式安裝位置", "學習進度資料夾", "桌面捷徑", "開始功能表", "cpe 指令", "開始安裝", "現在開啟"):
            self.assertIn(q, asked)
        cfg = cfgmod.load(self.plat.launcher_home)
        self.assertEqual((cfg.app_dir, cfg.workspace), (str(self.app), str(self.ws)))
        self.assertEqual(cfg.shortcuts, [])

    def test_declining_at_the_confirmation_changes_nothing(self):
        t = self.make([str(self.app), str(self.ws), "y", "y", "y", "n"])
        opts = engine.default_options(self.plat)
        opts.source, opts.bundle = "bundle", self.tree
        self.assertEqual(t.wizard(opts), 1)
        self.assertIn("沒有做任何變更", self.text)
        self.assertFalse(self.app.exists() or self.ws.exists())
        self.assertIsNone(cfgmod.load(self.plat.launcher_home))

    def test_wizard_offers_to_install_a_missing_git_and_applies_the_answer(self):
        ctx = self.make_ctx(which=lambda n: None if n in ("git", "winget") else "/usr/bin/" + n)
        fixes = []
        with mock.patch.object(engine.envcheck, "fix_plan", return_value=engine.envcheck.FixPlan([["true"]], "會跳出授權視窗")), \
                mock.patch.object(engine.envcheck, "apply_fix", side_effect=lambda c, f, log=None, gui=False: fixes.append(f) or (True, "完成")):
            t = self.make(["y", str(self.app), str(self.ws), "n", "n", "n", "y", "n"], ctx)
            opts = engine.default_options(self.plat)
            opts.source, opts.bundle, opts.port = "bundle", self.tree, self.port
            self.assertEqual(t.wizard(opts), 0, self.text)
        self.assertEqual(fixes, ["install_git"])
        self.assertIn("要自動安裝", " ".join(self.inp.prompts))
        self.assertIn("會跳出授權視窗", " ".join(self.inp.prompts))

    def test_blocking_problem_stops_the_wizard_with_the_reason(self):
        ctx = self.make_ctx(py_version=(3, 7, 0))
        t = self.make([], ctx)
        self.assertEqual(t.wizard(), 1)
        self.assertIn("必須先解決", self.text)
        self.assertIn("3.7.0", self.text)

    def test_panel_menu_opens_and_closes_the_service_and_shows_state(self):
        self.install_cli()
        t = self.make(["1", "1", "0"])
        with mock.patch.object(server, "open_ui", return_value="browser"):
            rc = t.panel()
        self.assertEqual(rc, 0)
        self.assertIn("○ 已關閉", self.text)
        self.assertIn("● 執行中", self.text)
        self.assertIn("✓ 已開啟", self.text)
        self.assertIn("✓ 已關閉", self.text)
        self.assertEqual(server.status(cfgmod.load(self.plat.launcher_home), self.plat).state, "stopped")

    def test_panel_menu_other_entries(self):
        self.install_cli()
        folder = []
        t = self.make(["6", "5", "4", "3", "0"])
        with mock.patch.object(engine, "open_folder", side_effect=folder.append), mock.patch.object(engine, "backup_now", return_value=Path("/x/b.zip")) as bk, \
                mock.patch.dict(os.environ, {"CPE_API_COMMIT_URL": f"http://127.0.0.1:{free_port()}/x"}):
            self.assertEqual(t.panel(), 0)
        self.assertEqual(folder, [Path(str(self.ws))])
        self.assertEqual(bk.call_count, 1)
        self.assertIn("安裝診斷", self.text)
        self.assertIn("已備份：", self.text)
        self.assertIn("連不上 GitHub", self.text)

    def test_uninstall_flow_keeps_progress_by_default(self):
        self.install_cli()
        cfg = cfgmod.load(self.plat.launcher_home)
        t = self.make(["n", "y"])
        self.assertEqual(t.uninstall_flow(cfg), 0)
        self.assertIn("學習進度保留在", self.text)
        self.assertTrue((self.ws / ".cpe").is_dir())
        self.assertIsNone(cfgmod.load(self.plat.launcher_home))

    def test_deleting_progress_needs_the_word_DELETE(self):
        self.install_cli()
        cfg = cfgmod.load(self.plat.launcher_home)
        t = self.make(["y", "n", "delete"])                                     # 要刪、不備份、確認字樣打錯
        self.assertEqual(t.uninstall_flow(cfg), 1)
        self.assertTrue((self.ws / ".cpe").is_dir())
        self.assertIsNotNone(cfgmod.load(self.plat.launcher_home))              # 什麼都沒動
        t = self.make(["y", "n", "DELETE"])
        self.assertEqual(t.uninstall_flow(cfg), 0)
        self.assertFalse(self.ws.exists())

    def test_cancelling_uninstall_changes_nothing(self):
        self.install_cli()
        cfg = cfgmod.load(self.plat.launcher_home)
        t = self.make(["n", "n"])
        self.assertEqual(t.uninstall_flow(cfg), 1)
        self.assertTrue(self.app.exists())

    def test_menu_ignores_garbage_input(self):
        t = self.make(["abc"])
        self.assertEqual(t.menu("x", ["a", "b"]), 0)
        t = self.make(["9"])
        self.assertEqual(t.menu("x", ["a", "b"]), 0)
        t = self.make([""])
        self.assertEqual(t.menu("x", ["a", "b"], default=2), 2)

    def test_reinstall_from_the_text_menu_proposes_the_existing_locations(self):
        self.install_cli()
        t = self.make(["4", str(self.app), str(self.ws), "n", "n", "n", "n"])           # 重新安裝：每個問題的預設值是現有的位置；最後不確認
        opts = engine.default_options(self.plat)
        opts.source, opts.bundle = "bundle", self.tree
        self.assertEqual(t.wizard(opts), 1)
        shown = [p for p in self.inp.prompts if "程式安裝位置" in p or "學習進度資料夾" in p]
        self.assertTrue(any(f"［{self.app}］" in p for p in shown), shown)
        self.assertTrue(any(f"［{self.ws}］" in p for p in shown), shown)

    def test_existing_install_is_offered_instead_of_reinstalling(self):
        self.install_cli()
        t = self.make(["1", "0"])
        with mock.patch.object(server, "open_ui", return_value="browser"):
            rc = t.wizard()
        self.assertEqual(rc, 0)
        self.assertIn("偵測到已經安裝", self.text)
        self.assertIn("控制台", self.text)


if __name__ == "__main__":
    unittest.main()
