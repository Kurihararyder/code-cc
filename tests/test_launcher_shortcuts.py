"""捷徑與指令檔的產生邏輯：用假的『Windows／macOS／Linux』環境在任何平台檢查產生出來的內容（引號、路徑、特殊字元、PowerShell 失敗時的備案）。"""
import base64
import json
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


ICON = str(REPO / "cpe_coach" / "launcher" / "assets" / "icon.ico")


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
    def make(self, run, logs=None):
        p = self.plat("windows")
        cfg = self.cfg(r"C:\Python312\python.exe")
        cfg.app_dir = str(self.t.path / "app dir")
        return p, cfg, shortcuts.create_all(cfg, p, True, True, log=(logs.append if logs is not None else (lambda s: None)), run=run)

    def test_all_lnk_files_are_made_by_one_powershell_run_with_the_values_passed_as_json(self):
        calls = []

        def run(cmd, timeout=60, env=None):
            calls.append((cmd, dict(env or {})))
            out = []
            for i, it in enumerate(json.loads(env["CPE_LNKS"])["items"]):
                Path(it["lnk"]).write_text("fake lnk")
                out.append(f"OK {i}")
            return 0, "\r\n".join(out)
        p, cfg, made = self.make(run)
        self.assertEqual(len(calls), 1)                                             # 四個捷徑只啟動一次 PowerShell（每次要 1 秒左右）
        self.assertEqual(len(made), 4)
        self.assertTrue(all(m.endswith(".lnk") for m in made))
        cmd, env = calls[0]
        self.assertEqual(cmd[0], "powershell")
        self.assertIn("-NoProfile", cmd)
        self.assertIn("CreateShortcut", cmd[-1])
        self.assertNotIn('"', cmd[-1])                                              # 腳本裡沒有雙引號，命令列不會有跳脫問題
        items = json.loads(env["CPE_LNKS"])["items"]
        self.assertEqual([Path(i["lnk"]).name for i in items], ["CPE 教練.lnk", "CPE 教練（控制台）.lnk", "CPE 教練　開始學習.lnk", "解除安裝 CPE 教練.lnk"])
        self.assertEqual(Path(items[0]["lnk"]).parent, self.home / "Desktop")
        for it in items:
            self.assertTrue(it["target"].lower().endswith(".exe"))
            self.assertTrue(it["icon"].endswith("icon.ico"))
            self.assertEqual(it["wd"], cfg.app_dir)
            self.assertTrue(it["args"].startswith(f'"{self.t.path / "app dir" / "cpe-panel.pyw"}"'))      # 路徑有空白要加引號
        self.assertTrue(items[2]["args"].endswith(" open"))
        self.assertTrue(items[3]["args"].endswith(" uninstall"))
        self.assertTrue(all(Path(m).parent in (self.home / "Desktop", p.menu_dir / "CPE 教練") for m in made))

    def test_the_powershell_script_reads_the_json_and_survives_a_single_item(self):
        """Windows PowerShell 5.1 的 ConvertFrom-Json 不展開最上層陣列，所以要包成物件再取 .items（這裡檢查腳本的形狀，真的執行在 Windows 的測試裡）。"""
        self.assertIn("(ConvertFrom-Json $env:CPE_LNKS).items", shortcuts.LNK_SCRIPT)
        self.assertIn("catch", shortcuts.LNK_SCRIPT)

    def test_when_powershell_cannot_make_a_lnk_a_cmd_launcher_is_made_instead_and_the_reason_is_logged(self):
        logs = []
        p, cfg, made = self.make(lambda cmd, timeout=60, env=None: (1, "Constrained language mode"), logs)
        self.assertEqual(len(made), 4)
        self.assertTrue(all(m.endswith(".cmd") for m in made))
        text = Path(made[0]).read_bytes().decode("utf-8")
        self.assertTrue(text.startswith("@echo off\r\nstart \"\" \""))
        self.assertIn("cpe-panel.pyw", text)
        self.assertTrue(any(Path(m).read_bytes().decode("utf-8").rstrip().endswith("uninstall") for m in made))
        joined = "\n".join(logs)
        self.assertIn("Constrained language mode", joined)                          # 沒有原因的失敗訊息沒辦法排查
        self.assertIn("結束碼 1", joined)

    def test_one_failing_item_only_replaces_that_one(self):
        def run(cmd, timeout=60, env=None):
            out = []
            for i, it in enumerate(json.loads(env["CPE_LNKS"])["items"]):
                if i == 2:
                    out.append(f"FAIL {i} : 找不到路徑")
                    continue
                Path(it["lnk"]).write_text("fake lnk")
                out.append(f"OK {i}")
            return 0, "\n".join(out)
        logs = []
        p, cfg, made = self.make(run, logs)
        self.assertEqual([Path(m).suffix for m in made], [".lnk", ".lnk", ".cmd", ".lnk"])
        self.assertIn("找不到路徑", "\n".join(logs))

    def test_a_stale_lnk_from_an_earlier_install_does_not_count_as_success(self):
        (self.home / "Desktop").mkdir(exist_ok=True)
        old = self.home / "Desktop" / "CPE 教練.lnk"
        old.write_text("old")
        p, cfg, made = self.make(lambda cmd, timeout=60, env=None: (1, "boom"))
        self.assertFalse(old.exists())
        self.assertEqual(made[0], str(self.home / "Desktop" / "CPE 教練.cmd"))

    def test_no_desktop_and_no_menu_means_no_powershell_at_all(self):
        calls = []
        p = self.plat("windows")
        made = shortcuts.create_all(self.cfg(r"C:\Python312\python.exe"), p, False, False, run=lambda *a, **k: calls.append(a) or (0, ""))
        self.assertEqual((made, calls), ([], []))

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



@unittest.skipUnless(sys.platform == "win32", "真的用 Windows 的 PowerShell 與 WScript.Shell")
class RealWindowsLnk(Fixture):
    def read_back(self, lnk):
        """用 PowerShell 把 .lnk 讀回來；結果轉成 UTF-8 的 base64 再傳（不靠主控台的編碼）。"""
        script = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:CPE_READ);"
                  "$j=ConvertTo-Json -Compress @{target=$s.TargetPath;args=$s.Arguments;wd=$s.WorkingDirectory;desc=$s.Description};"
                  "[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($j))")
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
                           capture_output=True, env=dict(os.environ, CPE_READ=str(lnk)), timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace"))
        return json.loads(base64.b64decode(r.stdout.strip()).decode("utf-8"))

    def test_lnk_files_are_really_created_with_chinese_and_spaces_and_read_back_correctly(self):
        folder = self.t.path / "開始 功能表 (1)" / "CPE 教練"
        target = Path(sys.executable).with_name("pythonw.exe")
        wd = self.t.path / "app dir"
        wd.mkdir()
        items = [{"lnk": str(folder / "CPE 教練（控制台）.lnk"), "target": str(target), "args": f'"{wd / "cpe-panel.pyw"}"', "wd": str(wd),
                  "icon": ICON, "desc": "控制台：開啟、關閉"},
                 {"lnk": str(folder / "CPE 教練　開始學習.lnk"), "target": str(target), "args": f'"{wd / "cpe-panel.pyw"}" open', "wd": str(wd),
                  "icon": ICON, "desc": "直接開啟學習畫面"}]
        logs = []
        made = shortcuts.make_lnks(items, log=logs.append)
        self.assertEqual(made, [True, True], logs)
        for it in items:
            info = self.read_back(it["lnk"])
            self.assertEqual(info["target"].lower(), it["target"].lower())
            self.assertEqual(info["args"], it["args"])
            self.assertEqual(info["wd"].lower(), it["wd"].lower())
            self.assertEqual(info["desc"], it["desc"])

    def test_a_single_item_works_too_and_overwriting_is_fine(self):
        item = {"lnk": str(self.t.path / "one.lnk"), "target": sys.executable, "args": "-V", "wd": str(self.t.path), "icon": ICON, "desc": "x"}
        self.assertEqual(shortcuts.make_lnks([item]), [True])
        self.assertEqual(shortcuts.make_lnks([item]), [True])
        self.assertEqual(self.read_back(item["lnk"])["args"], "-V")

    def test_a_name_windows_does_not_allow_is_reported_with_the_reason(self):
        logs = []
        made = shortcuts.make_lnks([{"lnk": str(self.t.path / "bad|name.lnk"), "target": sys.executable, "args": "", "wd": str(self.t.path), "icon": ICON, "desc": "x"}], log=logs.append)
        self.assertEqual(made, [False])
        self.assertTrue(logs and "PowerShell" in logs[0], logs)                      # 失敗要留下原因


if __name__ == "__main__":
    unittest.main()
