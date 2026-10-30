"""捷徑與指令檔的產生邏輯：用假的『Windows／macOS／Linux』環境在任何平台檢查產生出來的內容（引號、路徑、特殊字元、PowerShell 失敗時的備案）。"""
import os
import plistlib
import shlex
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from launcher_helpers import REPO, TempDir  # noqa: E402

from cpe_coach.launcher import shortcuts  # noqa: E402
from cpe_coach.launcher.config import LauncherConfig  # noqa: E402
from cpe_coach.launcher.osinfo import Plat  # noqa: E402


class Fixture(unittest.TestCase):
    def setUp(self):
        self.t = TempDir()
        self.addCleanup(self.t.cleanup)
        self.home = self.t.path / "home dir"            # 路徑裡有空白
        self.home.mkdir()
        (self.home / "Desktop").mkdir()

    def plat(self, system):
        env = {"CPE_LAUNCHER_HOME": str(self.t.path / "Launcher Home"), "CPE_LAUNCHER_MENU": str(self.t.path / "Menu")}
        if system != "windows":
            return Plat(system, self.home, "x", env)
        env["CPE_LAUNCHER_DESKTOP"] = str(self.home / "Desktop")
        return Plat(system, self.home, "x", env)

    def cfg(self, py="/opt/py thon/bin/python3"):
        return LauncherConfig(app_dir=str(self.t.path / "app dir"), workspace=str(self.t.path / "ws"), python=py, version="2.5.0")


class Shims(Fixture):
    def test_posix_shims_quote_paths_with_spaces_and_quotes(self):
        p = self.plat("linux")
        cfg = self.cfg("/opt/it's/py thon/python3")
        cfg.app_dir = str(self.t.path / "it's app")
        files = shortcuts.write_shims(cfg, p)
        by_name = {f.name: f for f in files}
        self.assertEqual(sorted(by_name), ["cpe", "cpe-panel"])
        for f in files:
            self.assertTrue(os.access(f, os.X_OK))
            first, rest = f.read_text(encoding="utf-8").split("\n", 1)
            self.assertEqual(first, "#!/bin/sh")
        # 用真的 shell 解析，確認引號沒有被特殊字元弄壞
        words = shlex.split(by_name["cpe"].read_text(encoding="utf-8").splitlines()[1])
        self.assertEqual(words[0], f"PYTHONPATH={cfg.app_dir}")
        self.assertEqual(words[1], "PYTHONUTF8=1")
        self.assertEqual(words[2:5], ["exec", "/opt/it's/py thon/python3", "-m"])
        self.assertEqual(words[5:], ["cpe_coach", "$@"])
        panel = shlex.split(by_name["cpe-panel"].read_text(encoding="utf-8").splitlines()[1])
        self.assertEqual(panel[:3], ["exec", "/opt/it's/py thon/python3", str(Path(cfg.app_dir) / "cpe-panel.pyw")])

    def test_windows_shims_use_crlf_isolate_the_environment_and_escape_percent(self):
        p = self.plat("windows")
        cfg = self.cfg(r"C:\Program Files\Python312\pythonw.exe")
        cfg.app_dir = r"C:\Users\50%\app"
        files = {f.name: f for f in shortcuts.write_shims(cfg, p)}
        self.assertEqual(sorted(files), ["cpe-panel.cmd", "cpe.cmd"])
        cpe = files["cpe.cmd"].read_bytes().decode("utf-8")
        self.assertIn("\r\n", cpe)
        self.assertNotIn("\n", cpe.replace("\r\n", ""))
        self.assertIn("setlocal", cpe)                                        # 設定的環境變數不會殘留在使用者的命令列
        self.assertIn(r'set "PYTHONPATH=C:\Users\50%%\app"', cpe)             # % 要寫成 %% 才不會被批次檔展開
        self.assertIn(r'"C:\Program Files\Python312\python.exe" -m cpe_coach %*', cpe)          # 指令列版用 python.exe，不是 pythonw
        self.assertIn("exit /b %ERRORLEVEL%", cpe)
        panel = files["cpe-panel.cmd"].read_bytes().decode("utf-8")
        self.assertIn("cpe-panel.pyw", panel)

    def test_batch_files_use_the_system_code_page_so_chinese_user_names_survive(self):
        """cmd.exe 讀批次檔用系統字碼頁（繁體中文 Windows 是 cp950）：UTF-8 寫的中文路徑會變亂碼、找不到 python。"""
        p = self.plat("windows")
        cfg = self.cfg(r"C:\Users\王小明\AppData\Local\Programs\Python\Python312\python.exe")
        cfg.app_dir = r"C:\Users\王小明\AppData\Local\CPE-Coach\app"
        files = {f.name: f for f in shortcuts.write_shims(cfg, p, encoding="cp950")}
        raw = files["cpe.cmd"].read_bytes()
        self.assertEqual(raw.decode("cp950").count("王小明"), 2)
        with self.assertRaises(UnicodeDecodeError):
            raw.decode("utf-8")
        self.assertEqual(shortcuts.batch_bytes("路徑", "cp950"), "路徑".encode("cp950"))
        self.assertEqual(shortcuts.batch_bytes("ŝ路徑", "cp1252"), "ŝ路徑".encode("utf-8"))                       # 字碼頁寫不進去：退回 UTF-8
        self.assertEqual(shortcuts.batch_bytes("abc", "no-such-codec"), b"abc")

    def test_shell_quote(self):
        self.assertEqual(shortcuts.shq("a b"), "'a b'")
        self.assertEqual(shlex.split(shortcuts.shq("it's $HOME `x`")), ["it's $HOME `x`"])
        self.assertEqual(shortcuts.console_python(r"C:\Python\pythonw.exe"), r"C:\Python\python.exe")
        self.assertEqual(shortcuts.console_python("/usr/bin/python3"), "/usr/bin/python3")


class Links(Fixture):
    def test_links_are_made_once_and_never_overwrite_someone_elses_command(self):
        p = self.plat("linux")
        cfg = self.cfg()
        shortcuts.write_shims(cfg, p)
        first = shortcuts.link_on_path(p)
        self.assertEqual(sorted(x.name for x in first), ["cpe", "cpe-panel"])
        self.assertEqual(sorted(x.name for x in shortcuts.link_on_path(p)), ["cpe", "cpe-panel"])         # 再做一次：認得是自己的
        (self.home / ".local" / "bin" / "cpe").unlink()
        (self.home / ".local" / "bin" / "cpe").write_text("#!/bin/sh\necho pip's cpe\n")                    # 換成別人的 cpe（例如 pip 裝的）
        again = shortcuts.link_on_path(p)
        self.assertEqual([x.name for x in again], ["cpe-panel"])
        self.assertIn("pip's cpe", (self.home / ".local" / "bin" / "cpe").read_text())
        self.assertEqual(shortcuts.link_on_path(self.plat("windows")), [])

    def test_on_path(self):
        p = Plat("linux", self.home, "x", {"PATH": os.pathsep.join(["/usr/bin", str(self.home / ".local" / "bin")])})
        self.assertTrue(shortcuts.on_path(p, self.home / ".local" / "bin"))
        self.assertFalse(shortcuts.on_path(p, self.home / "elsewhere"))


class Windows(Fixture):
    def make(self, run):
        p = self.plat("windows")
        cfg = self.cfg(r"C:\Python312\python.exe")
        cfg.app_dir = str(self.t.path / "app dir")
        return p, cfg, shortcuts.create_all(cfg, p, True, True, run=run)

    def test_lnk_is_created_through_powershell_with_values_passed_in_the_environment(self):
        calls = []

        def run(cmd, timeout=60, env=None):
            calls.append((cmd, dict(env or {})))
            Path(env["CPE_LNK"]).write_text("fake lnk")
            return 0, ""
        p, cfg, made = self.make(run)
        self.assertEqual(len(made), 4)
        self.assertTrue(all(m.endswith(".lnk") for m in made))
        cmd, env = calls[0]
        self.assertEqual(cmd[0], "powershell")
        self.assertIn("-NoProfile", cmd)
        self.assertIn("CreateShortcut", cmd[-1])
        self.assertEqual(Path(env["CPE_LNK"]).parent, self.home / "Desktop")
        self.assertEqual(Path(env["CPE_LNK"]).name, "CPE 教練.lnk")
        self.assertTrue(env["CPE_TARGET"].lower().endswith(".exe"))
        self.assertEqual(env["CPE_ARGS"], f'"{self.t.path / "app dir" / "cpe-panel.pyw"}"')               # 路徑有空白要加引號
        self.assertEqual(env["CPE_WD"], cfg.app_dir)
        self.assertTrue(env["CPE_ICON"].endswith("icon.ico"))
        names = {Path(e["CPE_LNK"]).name for _, e in calls}
        self.assertEqual(names, {"CPE 教練.lnk", "CPE 教練（控制台）.lnk", "CPE 教練　開始學習.lnk", "解除安裝 CPE 教練.lnk"})
        args = {Path(e["CPE_LNK"]).name: e["CPE_ARGS"] for _, e in calls}
        self.assertTrue(args["CPE 教練　開始學習.lnk"].endswith(" open"))
        self.assertTrue(args["解除安裝 CPE 教練.lnk"].endswith(" uninstall"))
        self.assertTrue(all(Path(m).parent in (self.home / "Desktop", p.menu_dir / "CPE 教練") for m in made))

    def test_when_powershell_cannot_make_a_lnk_a_cmd_launcher_is_made_instead(self):
        p, cfg, made = self.make(lambda cmd, timeout=60, env=None: (1, "Constrained language mode"))
        self.assertEqual(len(made), 4)
        self.assertTrue(all(m.endswith(".cmd") for m in made))
        text = Path(made[0]).read_bytes().decode("utf-8")
        self.assertTrue(text.startswith("@echo off\r\nstart \"\" \""))
        self.assertIn("cpe-panel.pyw", text)
        self.assertTrue(any(Path(m).read_bytes().decode("utf-8").rstrip().endswith("uninstall") for m in made))

    def test_remove_created_deletes_files_and_the_empty_menu_folder(self):
        p, cfg, made = self.make(lambda cmd, timeout=60, env=None: (1, ""))
        failed = shortcuts.remove_created(made)
        self.assertEqual(failed, [])
        self.assertFalse(any(Path(m).exists() for m in made))
        self.assertFalse((p.menu_dir / "CPE 教練").exists())
        self.assertEqual(shortcuts.remove_created(made), [])                    # 再刪一次也不出錯

    def test_registry_and_path_helpers_do_nothing_on_other_systems(self):
        p = self.plat("windows")
        if sys.platform != "win32":
            self.assertFalse(shortcuts.path_add(p, r"C:\x"))
            self.assertFalse(shortcuts.path_remove(p, r"C:\x"))
            self.assertFalse(shortcuts.register_uninstall(self.cfg(), p))
            self.assertFalse(shortcuts.unregister_uninstall(p))
            self.assertFalse(shortcuts.uninstall_entry_exists(p))


class MacOS(Fixture):
    def test_app_bundle_is_built_with_icon_plist_and_launcher(self):
        p = self.plat("macos")
        cfg = self.cfg()
        shortcuts.write_shims(cfg, p)
        shortcuts.assets_dir(p).mkdir(parents=True)
        (shortcuts.assets_dir(p) / "icon.icns").write_bytes(b"icns-bytes")
        made = shortcuts.create_all(cfg, p, True, True)
        app = p.menu_dir / "CPE 教練.app"
        self.assertEqual(sorted(made), sorted([str(app), str(self.home / "Desktop" / "CPE 教練.app")]))
        info = plistlib.loads((app / "Contents" / "Info.plist").read_bytes())
        self.assertEqual((info["CFBundleName"], info["CFBundleExecutable"], info["CFBundleIconFile"], info["CFBundleVersion"]), ("CPE 教練", "cpe-coach", "AppIcon", "2.5.0"))
        self.assertEqual((app / "Contents" / "Resources" / "AppIcon.icns").read_bytes(), b"icns-bytes")
        exe = app / "Contents" / "MacOS" / "cpe-coach"
        self.assertTrue(os.access(exe, os.X_OK))
        self.assertEqual(shlex.split(exe.read_text(encoding="utf-8").splitlines()[1]), ["exec", str(shortcuts.bin_dir(p) / "cpe-panel"), "$@"])
        desk = self.home / "Desktop" / "CPE 教練.app"
        self.assertTrue(desk.is_symlink())
        made2 = shortcuts.create_all(cfg, p, True, True)                        # 重做不出錯（先刪掉舊的）
        self.assertEqual(sorted(made2), sorted(made))
        self.assertEqual(shortcuts.remove_created(made), [])
        self.assertFalse(app.exists() or desk.is_symlink())


class Linux(Fixture):
    def test_desktop_entry_has_quoted_exec_icon_and_actions(self):
        p = self.plat("linux")
        cfg = self.cfg()
        shortcuts.write_shims(cfg, p)
        made = shortcuts.create_all(cfg, p, True, True)
        entry = (p.menu_dir / "cpe-coach.desktop").read_text(encoding="utf-8")
        self.assertEqual(sorted(made), sorted([str(p.menu_dir / "cpe-coach.desktop"), str(self.home / "Desktop" / "cpe-coach.desktop")]))
        main = entry.split("[Desktop Action", 1)[0]                              # 只看主要區段（動作區段也有 Name、Exec）
        lines = dict(ln.split("=", 1) for ln in main.splitlines() if "=" in ln)
        self.assertEqual(lines["Name"], "CPE 教練")
        self.assertEqual(lines["Terminal"], "false")
        self.assertTrue(lines["Exec"].startswith('"') and lines["Exec"].endswith('"'))
        self.assertIn("Launcher Home", lines["Exec"])                          # 有空白的路徑要加引號
        self.assertTrue(lines["Icon"].endswith("icon.png"))
        self.assertIn("[Desktop Action Open]", entry)
        self.assertIn("[Desktop Action Uninstall]", entry)
        self.assertIn("Actions=Open;Uninstall;", entry)
        self.assertTrue(os.access(p.menu_dir / "cpe-coach.desktop", os.X_OK))

    def test_desktop_quote_escapes_what_the_spec_requires(self):
        self.assertEqual(shortcuts.desktop_quote('a"b$c`d\\e'), '"a\\"b\\$c\\`d\\\\e"')

    def test_no_desktop_folder_means_no_desktop_shortcut_and_no_error(self):
        p = Plat("linux", self.t.path / "nohome", "x", {"CPE_LAUNCHER_HOME": str(self.t.path / "lh"), "CPE_LAUNCHER_MENU": str(self.t.path / "menu")})
        shortcuts.write_shims(self.cfg(), p)
        made = shortcuts.create_all(self.cfg(), p, True, True)
        self.assertEqual([Path(m).parent for m in made], [self.t.path / "menu"])

    def test_generated_shims_really_run_python_with_the_right_path(self):
        """用真的 sh 執行產生出來的 cpe：它會用記錄的 Python、PYTHONPATH 指到程式資料夾。"""
        p = self.plat("linux")
        fake = self.t.path / "fake python"
        fake.write_text('#!/bin/sh\necho "PYTHONPATH=$PYTHONPATH"\necho "UTF8=$PYTHONUTF8"\necho "ARGS=$@"\n', encoding="utf-8")
        fake.chmod(0o755)
        cfg = self.cfg(str(fake))
        shortcuts.write_shims(cfg, p)
        out = subprocess.run([str(shortcuts.bin_dir(p) / "cpe"), "today", "a b"], capture_output=True, text=True, env=dict(os.environ, PYTHONPATH="/other"))
        self.assertIn(f"PYTHONPATH={cfg.app_dir}\n", out.stdout)                # 不會把別處的 PYTHONPATH 帶進來
        self.assertIn("UTF8=1", out.stdout)
        self.assertIn("ARGS=-m cpe_coach today a b", out.stdout)


class Assets(unittest.TestCase):
    def test_icons_are_valid_files(self):
        d = REPO / "cpe_coach" / "launcher" / "assets"
        png = (d / "icon.png").read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        ico = (d / "icon.ico").read_bytes()
        self.assertEqual(ico[:4], b"\x00\x00\x01\x00")
        self.assertEqual(int.from_bytes(ico[4:6], "little"), 7)
        icns = (d / "icon.icns").read_bytes()
        self.assertEqual(icns[:4], b"icns")
        self.assertEqual(int.from_bytes(icns[4:8], "big"), len(icns))

    def test_copy_assets_puts_icons_in_a_stable_place(self):
        t = TempDir()
        self.addCleanup(t.cleanup)
        p = Plat("linux", t.path, "x", {"CPE_LAUNCHER_HOME": str(t.path / "lh")})
        out = shortcuts.copy_assets(str(REPO), p)
        self.assertEqual(sorted(out), ["icon.icns", "icon.ico", "icon.png"])
        self.assertTrue(all(f.is_file() for f in out.values()))


if __name__ == "__main__":
    unittest.main()
