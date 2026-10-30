"""安裝精靈的核心流程：用暫存的 git 倉庫／本機 zip 伺服器當成 GitHub，真的安裝、更新、修復、解除安裝。
每個測試都有獨立的家目錄、桌面、開始功能表、控制台資料夾（Windows 的登錄也改寫到另一個機碼），不會動到執行測試的那台電腦。"""
import json
import os
import subprocess
import sys
import threading
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
from launcher_helpers import (HAVE_GIT, REPO, FileServer, TempDir, bump_version, clean_registry, copy_app_tree, free_port, git, isolated_env,  # noqa: E402
                              make_origin, make_zip, set_version, wait_for)

from cpe_coach import __version__  # noqa: E402
from cpe_coach.launcher import config as cfgmod  # noqa: E402
from cpe_coach.launcher import engine, shortcuts, source  # noqa: E402
from cpe_coach.launcher.config import LauncherConfig  # noqa: E402
from cpe_coach.launcher.engine import Cancelled, EngineError, InstallOptions, Reporter, UninstallOptions  # noqa: E402
from cpe_coach.launcher.envcheck import Ctx  # noqa: E402
from cpe_coach.launcher.osinfo import detect  # noqa: E402

WINDOWS = sys.platform == "win32"
MAC = sys.platform == "darwin"


class Base(unittest.TestCase):
    def setUp(self):
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)                                          # 解除安裝會把工作目錄換到家目錄（之後會被刪掉）
        self.t = TempDir()
        self.addCleanup(self.t.cleanup)
        self.env = isolated_env(self.t.path)
        self.addCleanup(clean_registry, self.env)
        p = mock.patch.dict(os.environ, self.env)
        p.start()
        self.addCleanup(p.stop)
        self.plat = detect(env=self.env, home=Path(self.env["HOME"]))
        self.ctx = Ctx(plat=self.plat, net=lambda *a: True)
        self.app, self.ws = self.t.path / "app", self.t.path / "ws"
        self.steps, self.lines = [], []
        self.started = []
        self.addCleanup(self.stop_servers)

    def stop_servers(self):
        from cpe_coach.launcher import server
        for cfg in self.started:
            try:
                server.stop(cfg, self.plat)
            except Exception:
                pass

    def rep(self, **kw) -> Reporter:
        return Reporter(lambda i, n, s: self.steps.append(s), self.lines.append, **kw)

    def opts(self, **kw) -> InstallOptions:
        o = InstallOptions(app_dir=self.app, workspace=self.ws, branch="main", python=engine.base_python(), port=free_port())
        for k, v in kw.items():
            setattr(o, k, v)
        return o

    def use_origin(self, origin: Path):
        p = mock.patch.dict(os.environ, {"CPE_REPO_URL": str(origin), "CPE_INSTALL_BRANCH": "main"})
        p.start()
        self.addCleanup(p.stop)

    def install(self, **kw) -> LauncherConfig:
        cfg = engine.install(self.opts(**kw), self.plat, self.ctx, self.rep())
        self.started.append(cfg)
        return cfg

    def shim(self, name="cpe") -> Path:
        return shortcuts.bin_dir(self.plat) / (name + (".cmd" if WINDOWS else ""))

    def run_shim(self, *args, cwd=None):
        """執行安裝出來的 cpe 指令（工作目錄不在程式碼所在的地方，確保載入的是安裝出來的那一份）。"""
        return subprocess.run([str(self.shim())] + list(args), capture_output=True, text=True, timeout=90, env=dict(self.env), cwd=str(cwd or self.t.path), encoding="utf-8")

    def rm_files(self, paths):
        for s in paths:
            p = Path(s)
            if p.is_file() or p.is_symlink():
                p.unlink()

    def listing(self, d) -> list:
        return sorted(p.name for p in Path(d).iterdir()) if Path(d).exists() else []


def read_lnk(path: Path):
    """用 Windows 的 COM 讀回 .lnk 的目標與參數（確認捷徑真的指到對的地方）。"""
    ps = "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:CPE_LNK); Write-Output $s.TargetPath; Write-Output $s.Arguments; Write-Output $s.WorkingDirectory"
    out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], env=dict(os.environ, CPE_LNK=str(path)), capture_output=True, timeout=60)
    return out.stdout.decode("utf-8", "replace").splitlines()


@unittest.skipUnless(HAVE_GIT, "需要 git")
class InstallFromGit(Base):
    @classmethod
    def setUpClass(cls):
        cls._t = TempDir()
        cls.origin = make_origin(cls._t.path)

    @classmethod
    def tearDownClass(cls):
        cls._t.cleanup()

    def setUp(self):
        super().setUp()
        self.use_origin(self.origin)

    def test_install_creates_a_working_program_workspace_and_launchers(self):
        cfg = self.install()
        self.assertEqual(cfg.version, __version__)
        self.assertEqual(cfg.source["type"], "git")
        self.assertTrue((self.app / ".git").is_dir())
        self.assertTrue((self.ws / ".cpe" / "state.json").is_file())
        st = engine.installed_state(self.plat)
        self.assertTrue(st.installed and st.healthy, st.problems)
        saved = json.loads(cfgmod.path_of(self.plat.launcher_home).read_text(encoding="utf-8"))
        self.assertEqual(saved["app_dir"], str(self.app))
        self.assertEqual(saved["workspace"], str(self.ws))
        self.assertEqual(self.steps, engine.STEPS_INSTALL)
        # cpe 指令真的能跑（用安裝出來的程式，不是測試用的這份）
        self.assertEqual(self.run_shim().returncode, 2)                        # 沒給子指令 → argparse 的用法錯誤
        self.assertIn(f"cpe {__version__}", self.run_shim("--version").stdout)
        out = self.run_shim("today", cwd=self.ws)                              # 在學習進度資料夾裡能用
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_shortcuts_exist_for_this_platform_and_are_recorded(self):
        cfg = self.install()
        recorded = [Path(p) for p in cfg.shortcuts]
        self.assertTrue(recorded and all(p.exists() or p.is_symlink() for p in recorded), recorded)
        if WINDOWS:
            names = sorted(p.name for p in recorded)
            self.assertEqual(len(recorded), 4, names)                          # 桌面 1 + 開始功能表 3
            self.assertTrue(all(n.endswith(".lnk") for n in names), names)
            main = next(p for p in recorded if p.parent == self.plat.desktop_dir)
            target, args, workdir = read_lnk(main)
            self.assertTrue(target.lower().endswith("python.exe") or target.lower().endswith("pythonw.exe"), target)
            self.assertIn("cpe-panel.pyw", args)
            self.assertEqual(Path(workdir), self.app)
            uninstall = next(p for p in recorded if "uninstall" in read_lnk(p)[1])
            self.assertEqual(uninstall.parent, self.plat.menu_dir / "CPE 教練")
            self.assertTrue((self.plat.launcher_home / "assets" / "icon.ico").is_file())
            self.assertTrue(shortcuts.uninstall_entry_exists(self.plat))
        elif MAC:
            app = self.plat.menu_dir / "CPE 教練.app"
            self.assertTrue((app / "Contents" / "MacOS" / "cpe-coach").stat().st_mode & 0o111)
            import plistlib
            info = plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
            self.assertEqual(info["CFBundleExecutable"], "cpe-coach")
            self.assertTrue((app / "Contents" / "Resources" / "AppIcon.icns").is_file())
            desk = self.plat.desktop_dir / "CPE 教練.app"
            self.assertEqual(os.path.realpath(desk), os.path.realpath(app))
        else:
            for d in (self.plat.menu_dir, self.plat.desktop_dir):
                text = (d / "cpe-coach.desktop").read_text(encoding="utf-8")
                self.assertIn("[Desktop Entry]", text)
                self.assertIn(str(shortcuts.bin_dir(self.plat) / "cpe-panel"), text)
                self.assertIn("Icon=" + str(self.plat.launcher_home / "assets" / "icon.png"), text)
                self.assertTrue((d / "cpe-coach.desktop").stat().st_mode & 0o100)
        if not WINDOWS:
            for name in ("cpe", "cpe-panel"):
                link = self.plat.home / ".local" / "bin" / name
                self.assertEqual(os.path.realpath(link), os.path.realpath(self.shim(name)))
            self.assertEqual(sorted(Path(p).name for p in cfg.registered["links"]), ["cpe", "cpe-panel"])

    @unittest.skipUnless(WINDOWS, "Windows 登錄")
    def test_windows_registry_entry_and_user_path(self):
        import winreg
        cfg = self.install()
        root = self.env["CPE_LAUNCHER_REG_SANDBOX"]
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, root + r"\Uninstall\CPE-Coach") as k:
            vals = {winreg.EnumValue(k, i)[0]: winreg.EnumValue(k, i)[1] for i in range(winreg.QueryInfoKey(k)[1])}
        self.assertEqual(vals["DisplayName"], "CPE 教練")
        self.assertEqual(vals["InstallLocation"], str(self.app))
        self.assertIn("cpe-panel.pyw", vals["UninstallString"])
        self.assertTrue(vals["UninstallString"].endswith(" uninstall"))
        self.assertTrue(os.path.isfile(vals["DisplayIcon"]))
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, root + r"\Environment") as k:
            path, _ = winreg.QueryValueEx(k, "Path")
        self.assertIn(str(shortcuts.bin_dir(self.plat)), path.split(";"))
        self.assertEqual(cfg.registered["path_entry"], str(shortcuts.bin_dir(self.plat)))
        engine.uninstall(cfg, self.plat, UninstallOptions(), self.rep())
        self.assertFalse(shortcuts.uninstall_entry_exists(self.plat))
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, root + r"\Environment") as k:
            path, _ = winreg.QueryValueEx(k, "Path")
        self.assertNotIn(str(shortcuts.bin_dir(self.plat)), path.split(";"))

    def test_existing_progress_is_never_touched_by_reinstall(self):
        self.install()
        marker = self.ws / "solutions" / "mine.py"
        marker.write_text("print('我的解答')\n", encoding="utf-8")
        state_before = (self.ws / ".cpe" / "state.json").read_text(encoding="utf-8")
        cfg = self.install()                                                    # 重新安裝
        self.assertEqual(marker.read_text(encoding="utf-8"), "print('我的解答')\n")
        self.assertEqual((self.ws / ".cpe" / "state.json").read_text(encoding="utf-8"), state_before)
        self.assertTrue(engine.installed_state(self.plat).healthy)
        self.assertEqual(len(set(cfg.shortcuts)), len(cfg.shortcuts))           # 捷徑沒有重複記錄

    def test_reinstall_defaults_to_what_was_chosen_last_time(self):
        first = engine.default_options(self.plat)
        self.assertEqual(first.app_dir, self.plat.launcher_home / "app")
        cfg = self.install(desktop=False, menu=True, add_path=False)
        again = engine.default_options(self.plat)
        self.assertEqual((again.app_dir, again.workspace, again.port), (self.app, self.ws, cfg.port))
        self.assertEqual((again.desktop, again.menu, again.add_path), (False, True, False))

    def test_options_choose_which_shortcuts_to_make(self):
        cfg = self.install(desktop=False, menu=False, add_path=False)
        self.assertEqual(cfg.shortcuts, [])
        self.assertEqual(self.listing(self.plat.desktop_dir), [])
        self.assertEqual(self.listing(self.plat.menu_dir), [])
        self.assertFalse(cfg.registered.get("path_entry") or cfg.registered.get("links"))
        self.assertTrue(self.shim().exists())                                   # 指令檔一定會建（控制台要用）

    def test_restore_from_backup_during_install(self):
        self.install()
        (self.ws / "solutions" / "mine.py").write_text("x = 1\n", encoding="utf-8")
        from cpe_coach.store import Workspace
        zip_path = engine.backup_now(cfg := cfgmod.load(self.plat.launcher_home), self.t.path / "bk")
        self.assertTrue(zipfile.is_zipfile(zip_path))
        engine.uninstall(cfg, self.plat, UninstallOptions(remove_workspace=True), self.rep())
        self.assertFalse(self.ws.exists())
        new_ws = self.t.path / "ws-restored"
        self.install(workspace=new_ws, restore_from=zip_path)
        self.assertEqual((new_ws / "solutions" / "mine.py").read_text(encoding="utf-8"), "x = 1\n")
        Workspace(new_ws).state()

    def test_blocking_environment_problem_stops_before_changing_anything(self):
        self.ctx.py_version = (3, 8, 0)
        with self.assertRaises(EngineError) as cm:
            self.install()
        self.assertIn("Python", str(cm.exception))
        self.assertFalse(self.app.exists() or self.ws.exists())
        self.assertIsNone(cfgmod.load(self.plat.launcher_home))

    def test_refuses_a_folder_that_is_not_empty_and_not_ours(self):
        self.app.mkdir()
        (self.app / "我的筆記.txt").write_text("重要", encoding="utf-8")
        with self.assertRaises(EngineError) as cm:
            self.install()
        self.assertIn("不是空的", str(cm.exception))
        self.assertEqual((self.app / "我的筆記.txt").read_text(encoding="utf-8"), "重要")

    def test_program_and_progress_folders_may_not_contain_each_other(self):
        with self.assertRaises(EngineError):
            self.install(workspace=self.app / "進度")
        with self.assertRaises(EngineError):
            self.install(app_dir=self.ws / "程式")

    def test_failure_after_the_program_was_fetched_undoes_everything(self):
        with mock.patch.object(engine, "run_cpe", side_effect=EngineError("boom")):
            with self.assertRaises(EngineError):
                self.install()
        self.assertFalse(self.app.exists())
        self.assertFalse(self.ws.exists())
        self.assertFalse(Path(str(self.app) + ".new").exists())
        self.assertIsNone(cfgmod.load(self.plat.launcher_home))
        self.assertTrue(any("已復原" in ln for ln in self.lines), self.lines)

    def test_failure_late_in_install_undoes_shortcuts_and_config_too(self):
        real = cfgmod.save

        def save_then_fail(home, cfg):
            real(home, cfg)
            raise OSError("disk full")
        with mock.patch.object(cfgmod, "save", side_effect=save_then_fail):
            with self.assertRaises(EngineError):
                self.install()
        self.assertFalse(self.app.exists() or self.ws.exists())
        self.assertEqual(self.listing(self.plat.desktop_dir), [])
        self.assertIsNone(cfgmod.load(self.plat.launcher_home))
        if not WINDOWS:
            self.assertFalse((self.plat.home / ".local" / "bin" / "cpe").exists())

    def test_failed_reinstall_restores_the_previous_working_install(self):
        self.install()
        (self.app / "MARKER").write_text("old", encoding="utf-8")
        (self.ws / "solutions" / "mine.py").write_text("x = 1\n", encoding="utf-8")
        with mock.patch.object(engine, "integrate", side_effect=OSError("nope")):
            with self.assertRaises(EngineError):
                self.install()
        self.assertEqual((self.app / "MARKER").read_text(encoding="utf-8"), "old")
        self.assertTrue(engine.installed_state(self.plat).healthy)
        self.assertEqual((self.ws / "solutions" / "mine.py").read_text(encoding="utf-8"), "x = 1\n")

    def test_cancel_in_the_middle_undoes_what_was_done(self):
        cancel = threading.Event()
        rep = Reporter(lambda i, n, s: cancel.set() if s == "建立學習進度資料夾" else None, self.lines.append, cancel=cancel)
        with self.assertRaises(Cancelled):
            engine.install(self.opts(), self.plat, self.ctx, rep)
        self.assertFalse(self.app.exists() or self.ws.exists())
        self.assertIsNone(cfgmod.load(self.plat.launcher_home))

    def test_log_file_records_the_install(self):
        log = self.plat.launcher_home / "logs" / "launcher.log"
        engine.install(self.opts(), self.plat, self.ctx, engine.make_reporter(self.plat, None, self.lines.append))
        text = log.read_text(encoding="utf-8")
        self.assertIn("已安裝", text)
        self.assertIn("取得程式", text)

    def test_missing_git_falls_back_to_zip_in_auto_mode(self):
        srv = FileServer()
        self.addCleanup(srv.close)
        tree = copy_app_tree(self.t.path / "zip-tree")
        srv.publish(make_zip(tree, self.t.path / "a.zip"), "a" * 40)
        with mock.patch.dict(os.environ, {"CPE_ARCHIVE_URL": srv.archive_url, "CPE_API_COMMIT_URL": srv.sha_url}):
            ctx = Ctx(plat=self.plat, net=lambda *a: True, which=lambda n: None if n == "git" else __import__("shutil").which(n))
            cfg = engine.install(self.opts(), self.plat, ctx, self.rep())
        self.assertEqual(cfg.source["type"], "zip")
        self.assertEqual(cfg.source["sha"], "a" * 40)
        self.assertFalse((self.app / ".git").exists())

    def test_auto_mode_tries_the_next_source_when_one_fails(self):
        srv = FileServer()
        self.addCleanup(srv.close)
        tree = copy_app_tree(self.t.path / "zip-tree")
        srv.publish(make_zip(tree, self.t.path / "a.zip"), "b" * 40)
        with mock.patch.dict(os.environ, {"CPE_REPO_URL": str(self.t.path / "no-such-repo"), "CPE_ARCHIVE_URL": srv.archive_url, "CPE_API_COMMIT_URL": srv.sha_url}):
            cfg = engine.install(self.opts(), self.plat, self.ctx, self.rep())
        self.assertEqual(cfg.source["type"], "zip")
        self.assertTrue(any("git 方式失敗" in ln for ln in self.lines), self.lines)

    def test_explicit_source_does_not_silently_fall_back(self):
        with mock.patch.dict(os.environ, {"CPE_REPO_URL": str(self.t.path / "no-such-repo")}):
            with self.assertRaises(EngineError) as cm:
                self.install(source="git")
        self.assertIn("無法取得程式", str(cm.exception))
        self.assertFalse(self.app.exists())


@unittest.skipUnless(HAVE_GIT, "需要 git")
class UpdateFromGit(Base):
    def setUp(self):
        super().setUp()
        self.origin = make_origin(self.t.path)
        self.use_origin(self.origin)
        self.cfg = self.install()

    def test_update_check_then_update_then_up_to_date(self):
        self.assertEqual(engine.check_update(self.cfg)["status"], "up_to_date")
        bump_version(self.origin, "9.9.9", "新功能 ABC")
        self.assertEqual(engine.check_update(self.cfg)["status"], "available")
        r = engine.update(self.cfg, self.plat, self.ctx, self.rep())
        self.assertEqual(r["status"], "updated")
        self.assertEqual((r["old_version"], r["new_version"]), (__version__, "9.9.9"))
        self.assertIn("新功能 ABC", r["notes"])
        saved = cfgmod.load(self.plat.launcher_home)
        self.assertEqual(saved.version, "9.9.9")
        self.assertEqual(saved.source["version"], "9.9.9")
        self.assertTrue(git(self.origin, "rev-parse", "HEAD").startswith(saved.source["commit"]))
        self.assertIn('"9.9.9"', (self.app / "cpe_coach" / "__init__.py").read_text(encoding="utf-8"))
        self.assertEqual(engine.update(self.cfg, self.plat, self.ctx, self.rep())["status"], "up_to_date")

    def test_progress_is_untouched_by_an_update(self):
        (self.ws / "solutions" / "mine.py").write_text("x = 1\n", encoding="utf-8")
        before = (self.ws / ".cpe" / "state.json").read_text(encoding="utf-8")
        bump_version(self.origin, "9.9.9")
        engine.update(self.cfg, self.plat, self.ctx, self.rep())
        self.assertEqual((self.ws / "solutions" / "mine.py").read_text(encoding="utf-8"), "x = 1\n")
        self.assertEqual((self.ws / ".cpe" / "state.json").read_text(encoding="utf-8"), before)

    def test_locally_modified_program_is_not_overwritten(self):
        target = self.app / "cpe_coach" / "store.py"
        target.write_text(target.read_text(encoding="utf-8") + "\n# 我改的\n", encoding="utf-8")
        bump_version(self.origin, "9.9.9")
        r = engine.update(self.cfg, self.plat, self.ctx, self.rep())
        self.assertEqual(r["status"], "blocked")
        self.assertIn("修改", r["reason"])
        self.assertIn("# 我改的", target.read_text(encoding="utf-8"))
        self.assertEqual(cfgmod.load(self.plat.launcher_home).version, __version__)

    def test_a_new_version_the_wizard_cannot_load_is_rolled_back(self):
        old_commit = git(self.app, "rev-parse", "HEAD")
        bump_version(self.origin, "9.9.9", break_launcher=True)
        r = engine.update(self.cfg, self.plat, self.ctx, self.rep())
        self.assertEqual(r["status"], "rolled_back")
        self.assertEqual(git(self.app, "rev-parse", "HEAD"), old_commit)
        self.assertEqual(source.verify_import(self.cfg.python, self.app), __version__)
        self.assertEqual(cfgmod.load(self.plat.launcher_home).version, __version__)

    def test_unreachable_remote_is_reported_not_crashed(self):
        git(self.app, "remote", "set-url", "origin", str(self.t.path / "gone"))
        r = engine.update(self.cfg, self.plat, self.ctx, self.rep())
        self.assertEqual(r["status"], "unavailable")
        self.assertIn("GitHub", r["reason"])

    def test_repair_reclones_a_broken_program_and_rebuilds_shortcuts(self):
        (self.app / "cpe_coach" / "launcher" / "engine.py").unlink()
        self.rm_files(self.cfg.shortcuts)
        cfg = engine.repair(self.cfg, self.plat, self.ctx, self.rep(), None)
        self.assertEqual(cfg.version, __version__)
        self.assertEqual(source.verify_import(cfg.python, self.app), __version__)
        self.assertTrue(cfg.shortcuts and all(Path(p).exists() or Path(p).is_symlink() for p in cfg.shortcuts))
        self.assertTrue((self.ws / ".cpe").is_dir())

    def test_repair_replaces_a_python_that_disappeared(self):
        cfg = cfgmod.load(self.plat.launcher_home)
        cfg.python = str(self.t.path / "gone" / "python")
        cfgmod.save(self.plat.launcher_home, cfg)
        st = engine.installed_state(self.plat)
        self.assertFalse(st.healthy)
        self.assertTrue(any("Python" in p for p in st.problems))
        fixed = engine.repair(cfg, self.plat, self.ctx, self.rep(), None)
        self.assertTrue(Path(fixed.python).exists())
        self.assertTrue(engine.installed_state(self.plat).healthy)

    def test_repair_recreates_a_deleted_workspace_folder(self):
        from cpe_coach.launcher.source import rmtree
        rmtree(self.ws)
        self.assertFalse(engine.installed_state(self.plat).healthy)
        engine.repair(self.cfg, self.plat, self.ctx, self.rep(), None)
        self.assertTrue((self.ws / ".cpe").is_dir())

    def test_repair_offline_without_a_local_copy_explains_what_to_do(self):
        import shutil
        shutil.rmtree(str(self.app / "cpe_coach" / "launcher"))
        offline = Ctx(plat=self.plat, net=lambda *a: False)
        with self.assertRaises(EngineError) as cm:
            engine.repair(self.cfg, self.plat, offline, self.rep(), None)
        self.assertIn("連不上", str(cm.exception))


class ZipSource(Base):
    def setUp(self):
        super().setUp()
        self.srv = FileServer()
        self.addCleanup(self.srv.close)
        self.tree = copy_app_tree(self.t.path / "tree")
        self.srv.publish(make_zip(self.tree, self.t.path / "v1.zip"), "a" * 40)
        p = mock.patch.dict(os.environ, {"CPE_ARCHIVE_URL": self.srv.archive_url, "CPE_API_COMMIT_URL": self.srv.sha_url})
        p.start()
        self.addCleanup(p.stop)

    def test_install_update_and_up_to_date(self):
        cfg = self.install(source="zip")
        self.assertEqual((cfg.source["type"], cfg.source["sha"]), ("zip", "a" * 40))
        self.assertFalse((self.app / ".git").exists())
        self.assertEqual(engine.check_update(cfg)["status"], "up_to_date")
        set_version(self.tree, "9.9.9", "zip 新功能")
        self.srv.publish(make_zip(self.tree, self.t.path / "v2.zip"), "b" * 40)
        self.assertEqual(engine.check_update(cfg)["status"], "available")
        r = engine.update(cfg, self.plat, self.ctx, self.rep())
        self.assertEqual((r["status"], r["new_version"]), ("updated", "9.9.9"))
        self.assertIn("zip 新功能", r["notes"])
        saved = cfgmod.load(self.plat.launcher_home)
        self.assertEqual((saved.version, saved.source["sha"]), ("9.9.9", "b" * 40))
        self.assertEqual(engine.check_update(saved)["status"], "up_to_date")
        self.assertEqual(self.listing(self.t.path).count("app.new"), 0)
        self.assertEqual([n for n in self.listing(self.t.path) if n.startswith("app.old")], [])

    def test_a_broken_new_version_leaves_the_old_one_in_place(self):
        cfg = self.install(source="zip")
        set_version(self.tree, "9.9.9", break_launcher=True)
        self.srv.publish(make_zip(self.tree, self.t.path / "v2.zip"), "c" * 40)
        r = engine.update(cfg, self.plat, self.ctx, self.rep())
        self.assertEqual(r["status"], "blocked")
        self.assertEqual(source.verify_import(cfg.python, self.app), __version__)
        self.assertEqual([n for n in self.listing(self.t.path) if n.startswith("app.")], [])

    def test_unreachable_server_means_update_unavailable(self):
        cfg = self.install(source="zip")
        self.srv.fail = True
        r = engine.check_update(cfg)
        self.assertEqual(r["status"], "unavailable")

    def test_garbage_download_is_rejected_cleanly(self):
        self.srv.zip_bytes = b"<html>captive portal</html>"
        with self.assertRaises(EngineError) as cm:
            self.install(source="zip")
        self.assertIn("壓縮檔", str(cm.exception))
        self.assertFalse(self.app.exists() or self.ws.exists())

    def test_zip_with_path_traversal_is_rejected(self):
        evil = self.t.path / "evil.zip"
        with zipfile.ZipFile(evil, "w") as z:
            z.writestr("x/cpe_coach/__init__.py", "")
            z.writestr("../../escape.txt", "bad")
        self.srv.zip_bytes = evil.read_bytes()
        with self.assertRaises(EngineError):
            self.install(source="zip")
        self.assertFalse((self.t.path.parent / "escape.txt").exists())
        self.assertFalse(self.app.exists())


class BundleSource(Base):
    def test_offline_install_from_the_folder_the_installer_runs_from(self):
        tree = copy_app_tree(self.t.path / "tree")
        (tree / ".git").mkdir()
        (tree / ".git" / "config").write_text("x")
        (tree / "cpe_coach" / "__pycache__").mkdir()
        (tree / "cpe_coach" / "__pycache__" / "x.pyc").write_text("x")
        ctx = Ctx(plat=self.plat, net=lambda *a: False, bundle=tree)
        with mock.patch.dict(os.environ, {"CPE_API_COMMIT_URL": f"http://127.0.0.1:{free_port()}/none"}):
            cfg = engine.install(self.opts(bundle=tree), self.plat, ctx, self.rep())
            self.started.append(cfg)
            self.assertEqual(cfg.source["type"], "bundle")
            self.assertEqual(cfg.version, __version__)
            self.assertFalse((self.app / ".git").exists())
            self.assertFalse((self.app / "cpe_coach" / "__pycache__" / "x.pyc").exists())
            r = engine.check_update(cfg)
            self.assertEqual(r["status"], "unavailable")                      # 沒網路：誠實說檢查不了

    def test_no_network_and_no_local_copy_is_a_clear_error(self):
        ctx = Ctx(plat=self.plat, net=lambda *a: False)
        with self.assertRaises(EngineError) as cm:
            engine.install(self.opts(), self.plat, ctx, self.rep())
        self.assertIn("GitHub", str(cm.exception))

    def test_source_choice_matrix(self):
        b = Path("/x")
        self.assertEqual(source.choose("auto", True, True, b), "git")
        self.assertEqual(source.choose("auto", False, True, b), "zip")
        self.assertEqual(source.choose("auto", True, False, b), "bundle")
        self.assertEqual(source.choose("auto", False, False, b), "bundle")
        self.assertEqual(source.choose("zip", True, True, None), "zip")
        with self.assertRaises(source.SourceError):
            source.choose("auto", True, False, None)


class Uninstall(Base):
    def setUp(self):
        super().setUp()
        self.tree = copy_app_tree(self.t.path / "tree")
        self.cfg = engine.install(self.opts(source="bundle", bundle=self.tree), self.plat, self.ctx, self.rep())
        (self.ws / "solutions" / "mine.py").write_text("x = 1\n", encoding="utf-8")

    def test_keeps_the_workspace_and_removes_everything_else(self):
        r = engine.uninstall(self.cfg, self.plat, UninstallOptions(), self.rep())
        self.assertEqual(r["problems"], [])
        self.assertFalse(r["workspace_removed"])
        self.assertTrue(wait_for(lambda: not self.app.exists(), 10))
        self.assertFalse(self.plat.launcher_home.exists())
        self.assertEqual(self.listing(self.plat.desktop_dir), [])
        self.assertEqual(self.listing(self.plat.menu_dir), [])
        self.assertEqual((self.ws / "solutions" / "mine.py").read_text(encoding="utf-8"), "x = 1\n")
        self.assertIsNone(cfgmod.load(self.plat.launcher_home))
        if not WINDOWS:
            for name in ("cpe", "cpe-panel"):
                self.assertFalse((self.plat.home / ".local" / "bin" / name).is_symlink())

    def test_can_back_up_then_delete_the_workspace(self):
        bk = self.t.path / "backups"
        r = engine.uninstall(self.cfg, self.plat, UninstallOptions(remove_workspace=True, backup_dir=bk), self.rep())
        self.assertTrue(r["workspace_removed"])
        self.assertFalse(self.ws.exists())
        z = Path(r["backup"])
        self.assertTrue(z.is_file() and z.parent == bk)
        with zipfile.ZipFile(z) as zf:
            names = zf.namelist()
        self.assertIn(".cpe/state.json", names)
        self.assertIn("solutions/mine.py", names)

    def test_refuses_to_delete_dangerous_paths_even_if_the_config_says_so(self):
        home = self.plat.home
        (home / "文件").mkdir()
        (home / "文件" / "重要.txt").write_text("x", encoding="utf-8")
        evil = LauncherConfig(app_dir=str(home), workspace=str(home), python=self.cfg.python, port=free_port())
        r = engine.uninstall(evil, self.plat, UninstallOptions(remove_workspace=True), self.rep())
        self.assertTrue((home / "文件" / "重要.txt").exists())
        self.assertTrue(r["problems"])
        self.assertFalse(r["workspace_removed"])

    def test_removal_problem_rules(self):
        home = self.plat.home
        self.assertTrue(engine.removal_problem(Path(home.anchor), self.plat))
        self.assertTrue(engine.removal_problem(home, self.plat))
        self.assertTrue(engine.removal_problem(home.parent, self.plat))
        self.assertTrue(engine.removal_problem(home / "a", self.plat, keep=home / "a" / "ws"))
        self.assertEqual(engine.removal_problem(home / "a" / "b", self.plat, keep=home / "other"), "")

    def test_a_workspace_inside_the_launcher_folder_survives(self):
        cfg = cfgmod.load(self.plat.launcher_home)
        inner = self.plat.launcher_home / "ws-inside"
        inner.mkdir()
        (inner / ".cpe").mkdir()
        (inner / ".cpe" / "state.json").write_text("{}", encoding="utf-8")
        cfg.workspace = str(inner)
        engine.uninstall(cfg, self.plat, UninstallOptions(), self.rep())
        self.assertTrue((inner / ".cpe" / "state.json").exists())

    def test_uninstall_when_pieces_are_already_gone(self):
        self.rm_files(self.cfg.shortcuts)
        import shutil
        shutil.rmtree(str(shortcuts.bin_dir(self.plat)))
        r = engine.uninstall(self.cfg, self.plat, UninstallOptions(), self.rep())
        self.assertEqual(r["problems"], [])
        self.assertTrue(wait_for(lambda: not self.app.exists(), 10))

    def test_uninstall_from_the_installed_copy_cleans_up_after_it_exits(self):
        """真實情況：控制台跑在它自己的程式資料夾裡，所以要等它結束後由另一個小程序刪。"""
        env = dict(self.env)
        out = subprocess.run([sys.executable, str(self.app / "cpe-panel.pyw"), "uninstall", "--yes", "--text"], env=env, capture_output=True, timeout=90,
                             cwd=str(self.t.path))
        text = out.stdout.decode("utf-8", "replace")
        self.assertEqual(out.returncode, 0, text + out.stderr.decode("utf-8", "replace"))
        self.assertIn("已解除安裝", text)
        self.assertTrue(wait_for(lambda: not self.app.exists() and not self.plat.launcher_home.exists(), 60), self.listing(self.t.path))
        self.assertEqual((self.ws / "solutions" / "mine.py").read_text(encoding="utf-8"), "x = 1\n")

    def test_a_running_service_is_stopped_first(self):
        from cpe_coach.launcher import server
        self.started.append(self.cfg)
        st = server.start(self.cfg, self.plat)
        self.assertTrue(st.running)
        engine.uninstall(self.cfg, self.plat, UninstallOptions(), self.rep())
        self.assertIsNone(server.probe(st.port))


class Misc(unittest.TestCase):
    def test_rmtree_removes_read_only_trees(self):
        t = TempDir()
        self.addCleanup(t.cleanup)
        d = t.path / "ro" / "sub"
        d.mkdir(parents=True)
        f = d / "locked.txt"
        f.write_text("x")
        os.chmod(f, 0o444)
        self.assertTrue(source.rmtree(t.path / "ro"))
        self.assertFalse((t.path / "ro").exists())
        self.assertTrue(source.rmtree(t.path / "never-existed"))

    def test_check_target(self):
        t = TempDir()
        self.addCleanup(t.cleanup)
        source.check_target(t.path / "new")
        (t.path / "empty").mkdir()
        source.check_target(t.path / "empty")
        (t.path / "file").write_text("x")
        with self.assertRaises(source.SourceError):
            source.check_target(t.path / "file")

    def test_verify_import_fails_for_a_broken_tree(self):
        t = TempDir()
        self.addCleanup(t.cleanup)
        (t.path / "cpe_coach").mkdir()
        (t.path / "cpe_coach" / "__init__.py").write_text("raise RuntimeError('x')\n", encoding="utf-8")
        with self.assertRaises(source.SourceError):
            source.verify_import(sys.executable, t.path)

    def test_repository_has_the_launch_files_users_double_click(self):
        for name in ("cpe-panel.pyw", "install-windows.bat", "install-macos.command", "install-linux.sh", "setup/bootstrap.ps1", "setup/bootstrap.sh"):
            self.assertTrue((REPO / name).is_file(), name)
        for name in ("icon.png", "icon.ico", "icon.icns"):
            self.assertGreater((REPO / "cpe_coach" / "launcher" / "assets" / name).stat().st_size, 1000, name)


if __name__ == "__main__":
    unittest.main()
