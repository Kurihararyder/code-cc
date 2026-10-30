"""雙擊用的啟動檔（Windows .bat＋PowerShell、macOS .command、Linux .sh）：格式正確、能在這個平台上執行『只檢查』模式。
真的裝 Python 的步驟（winget、python.org 的安裝程式、Homebrew、apt）只有在真的缺 Python 的電腦上才會跑，這裡驗證不到。"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from launcher_helpers import REPO, TempDir  # noqa: E402

WINDOWS = sys.platform == "win32"
SH = shutil.which("sh")


class Formats(unittest.TestCase):
    def test_bat_is_ascii_with_windows_line_endings(self):
        raw = (REPO / "install-windows.bat").read_bytes()
        raw.decode("ascii")                                                         # cmd 讀取非 ASCII 的批次檔容易亂碼：訊息都放在 PowerShell 裡
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))

    def test_bat_has_no_parenthesised_blocks_because_a_folder_like_Downloads_1_would_break_them(self):
        lines = (REPO / "install-windows.bat").read_bytes().decode("ascii").splitlines()
        code = [ln for ln in lines if ln.strip() and not ln.lower().startswith("rem ")]
        self.assertFalse([ln for ln in code if ln.strip() == ")" or ln.rstrip().endswith("(")], code)
        self.assertTrue(any(ln.startswith(":local") for ln in code))

    def test_powershell_script_has_a_bom_so_windows_powershell_reads_the_chinese_text(self):
        raw = (REPO / "setup" / "bootstrap.ps1").read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        text = raw.decode("utf-8-sig")
        self.assertIn("找不到 Python", text)
        for needle in ("-CheckOnly", "Get-FileHash", "python-3.12.10-amd64.exe", "WindowsApps"):
            self.assertIn(needle, text)

    def test_pinned_python_installer_hashes_are_in_both_scripts(self):
        ps = (REPO / "setup" / "bootstrap.ps1").read_text(encoding="utf-8-sig")
        sh = (REPO / "setup" / "bootstrap.sh").read_text(encoding="utf-8")
        import re
        for h in re.findall(r"Sha256 = \"([0-9a-f]+)\"", ps):
            self.assertEqual(len(h), 64)
        self.assertEqual(len(re.findall(r"Sha256 = ", ps)), 3)
        self.assertRegex(sh, r"PKG_SHA256=[0-9a-f]{64}")

    @unittest.skipIf(WINDOWS, "POSIX 檔案權限")
    def test_shell_launchers_are_executable_and_parse(self):
        for name in ("install-macos.command", "install-linux.sh", "setup/bootstrap.sh", "cpe-panel.pyw"):
            p = REPO / name
            self.assertTrue(os.access(p, os.X_OK), f"{name} 沒有執行權限")
        for name in ("install-macos.command", "install-linux.sh", "setup/bootstrap.sh"):
            r = subprocess.run([SH, "-n", str(REPO / name)], capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))

    def test_shell_variables_are_never_glued_to_non_ascii_text(self):
        """macOS 的 sh（bash 3.2）在非 UTF-8 語系下，會把 $OS）的全形括號當成變數名稱的一部分（unbound variable）：訊息裡的變數都要用 ${名稱}。"""
        import re
        for name in ("setup/bootstrap.sh", "install-macos.command", "install-linux.sh"):
            text = (REPO / name).read_text(encoding="utf-8")
            bad = re.findall(r"\$[A-Za-z_][A-Za-z0-9_]*(?=[^\x00-\x7f])", text)
            self.assertEqual(bad, [], f"{name}: 變數後面直接接中文／全形符號，請改成 ${{名稱}}")

    @unittest.skipIf(WINDOWS, "POSIX 啟動檔")
    def test_bootstrap_survives_a_non_utf8_locale_under_strict_mode(self):
        """用 C 語系跑（macOS CI 的情況）：不能因為訊息裡的非 ASCII 字元而失敗。"""
        env = dict(os.environ, LC_ALL="C", LANG="C", HOME=tempfile.gettempdir())
        r = subprocess.run([SH, str(REPO / "setup" / "bootstrap.sh"), "--check"], capture_output=True, timeout=120, env=env, cwd=tempfile.gettempdir())
        out = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
        self.assertEqual(r.returncode, 0, out)
        self.assertNotIn("unbound variable", out)

    def test_launch_files_point_at_the_same_repository_and_branch(self):
        from cpe_coach.launcher import constants
        for name in ("install-windows.bat", "setup/bootstrap.ps1", "setup/bootstrap.sh"):
            text = (REPO / name).read_bytes().decode("utf-8", "replace")
            self.assertIn(constants.DEFAULT_BRANCH, text, name)
        self.assertIn(constants.DEFAULT_SLUG, (REPO / "setup" / "bootstrap.ps1").read_text(encoding="utf-8-sig"))


@unittest.skipIf(WINDOWS, "POSIX 啟動檔")
class PosixCheckMode(unittest.TestCase):
    def run_sh(self, script, *args, path=None):
        env = dict(os.environ, HOME=tempfile.gettempdir(), CPE_NO_FIXED_PYTHON="1")          # 只靠 PATH 找 Python（macOS 的 CI 機器在固定位置裝了 Python）
        if path is not None:
            env["PATH"] = path
        return subprocess.run([SH, str(REPO / script)] + list(args), capture_output=True, timeout=120, env=env, cwd=tempfile.gettempdir())

    def test_check_mode_reports_python_and_the_install_diagnosis_without_installing(self):
        name = "install-macos.command" if sys.platform == "darwin" else "install-linux.sh"
        home = TempDir()
        self.addCleanup(home.cleanup)
        env = dict(os.environ, HOME=str(home.path), CPE_LAUNCHER_HOME=str(home.path / "launcher"), CPE_LAUNCHER_DESKTOP=str(home.path / "d"),
                   CPE_LAUNCHER_MENU=str(home.path / "m"))
        r = subprocess.run([SH, str(REPO / name), "--check"], capture_output=True, timeout=120, env=env, cwd=tempfile.gettempdir())
        out = r.stdout.decode("utf-8", "replace")
        self.assertEqual(r.returncode, 0, out + r.stderr.decode("utf-8", "replace"))
        self.assertIn("Python", out)
        self.assertIn("安裝診斷", out)
        self.assertIn("尚未安裝", out)
        self.assertFalse((home.path / "launcher").exists())                          # 只檢查：什麼都沒建立

    def test_check_mode_explains_what_it_would_do_when_python_is_missing(self):
        tools = TempDir()
        self.addCleanup(tools.cleanup)
        for t in ("dirname", "uname", "id", "cat", "mktemp"):
            real = shutil.which(t)
            if real:
                os.symlink(real, tools.path / t)
        r = self.run_sh("setup/bootstrap.sh", "--check", path=str(tools.path))
        out = r.stdout.decode("utf-8", "replace")
        self.assertEqual(r.returncode, 0, out + r.stderr.decode("utf-8", "replace"))
        self.assertIn("找不到 Python 3.9 以上", out)
        self.assertIn("檢查模式", out)

    def test_without_python_and_without_permission_it_stops_with_instructions(self):
        tools = TempDir()
        self.addCleanup(tools.cleanup)
        for t in ("dirname", "uname", "id", "cat", "mktemp"):
            real = shutil.which(t)
            if real:
                os.symlink(real, tools.path / t)
        r = subprocess.run([SH, str(REPO / "setup" / "bootstrap.sh")], capture_output=True, timeout=60, env=dict(os.environ, PATH=str(tools.path), CPE_NO_FIXED_PYTHON="1"),
                           stdin=subprocess.DEVNULL, cwd=tempfile.gettempdir())
        out = r.stdout.decode("utf-8", "replace")
        self.assertEqual(r.returncode, 1, out)
        self.assertIn("https://www.python.org/downloads/", out)


@unittest.skipUnless(WINDOWS, "Windows PowerShell")
class WindowsCheckMode(unittest.TestCase):
    def ps(self, *args):
        return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass"] + list(args), capture_output=True, timeout=180)

    def test_script_parses(self):
        r = self.ps("-Command", "$e=$null;$t=$null;[void][System.Management.Automation.Language.Parser]::ParseFile('%s',[ref]$t,[ref]$e);"
                    "if($e.Count){$e|ForEach-Object{Write-Output $_.Message};exit 1}" % (REPO / "setup" / "bootstrap.ps1"))
        self.assertEqual(r.returncode, 0, r.stdout.decode("utf-8", "replace"))

    def test_check_only_from_a_folder_with_spaces_parentheses_and_chinese_in_its_name(self):
        """使用者把壓縮檔下載兩次，資料夾就會叫「code-cc (1)」；中文資料夾也很常見。"""
        import shutil
        t = TempDir()
        self.addCleanup(t.cleanup)
        folder = t.path / "下載 (1) & 備份"
        (folder / "setup").mkdir(parents=True)
        shutil.copy2(REPO / "install-windows.bat", folder / "install-windows.bat")
        shutil.copy2(REPO / "setup" / "bootstrap.ps1", folder / "setup" / "bootstrap.ps1")
        bat = folder / "install-windows.bat"
        # 檔案總管雙擊 .bat 時執行的是  cmd.exe /c ""路徑" "；路徑裡有 & ( ) 時 cmd 的引號規則要靠 /s 才會剝掉最外面那一對
        r = subprocess.run('cmd /s /c ""%s" -CheckOnly"' % bat, capture_output=True, timeout=180, stdin=subprocess.DEVNULL, cwd=str(t.path))
        out = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
        self.assertEqual(r.returncode, 0, out)
        self.assertIn("Python", out)

    def test_check_only_through_the_bat_file(self):
        r = subprocess.run(["cmd", "/c", str(REPO / "install-windows.bat"), "-CheckOnly"], capture_output=True, timeout=180, stdin=subprocess.DEVNULL)
        out = r.stdout.decode("utf-8", "replace")
        self.assertEqual(r.returncode, 0, out + r.stderr.decode("utf-8", "replace"))
        self.assertIn("Python", out)
        self.assertIn("安裝診斷", out)


if __name__ == "__main__":
    unittest.main()
