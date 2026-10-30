"""環境自動檢測：用注入的假環境，在任何平台測試『缺 git』『沒網路』『磁碟不夠』『Python 太舊』等情況與自動修復計畫。"""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
from launcher_helpers import TempDir  # noqa: E402

from cpe_coach.launcher import envcheck, osinfo  # noqa: E402
from cpe_coach.launcher.envcheck import Ctx  # noqa: E402
from cpe_coach.launcher.osinfo import Plat  # noqa: E402


def plat(system="linux", home="/home/u", **env):
    return Plat(system, Path(home), "x86_64", dict(env))


def ctx(p=None, **over):
    base = dict(plat=p or plat(), run=lambda cmd, t=60, env=None: (0, "git version 2.43.0"), which=lambda n: f"/usr/bin/{n}", net=lambda h, p, t: True,
                free_mb=lambda p: 50_000.0, port_free=lambda p: True, has_tk=lambda: True, python="/usr/bin/python3", py_version=(3, 12, 1),
                target=None, port=8765, bundle=None, is_admin=lambda: False)
    base.update(over)
    return Ctx(**base)


def by_id(checks):
    return {c.id: c for c in checks}


class Checks(unittest.TestCase):
    def test_healthy_machine_has_no_blocking_problem(self):
        t = TempDir()                                                         # 安裝位置要是真的可寫的資料夾（只有 root 才會讓假的路徑通過 os.access）
        self.addCleanup(t.cleanup)
        c = ctx(plat("linux", str(t.path), DISPLAY=":0"), target=t.path / "app")
        cs = by_id(envcheck.run_checks(c))
        self.assertTrue(envcheck.summarize(list(cs.values()))["ok"])
        self.assertEqual(cs["python"].status, "ok")
        self.assertEqual(cs["git"].status, "ok")
        self.assertEqual(cs["net"].status, "ok")

    def test_old_python_blocks(self):
        cs = by_id(envcheck.run_checks(ctx(py_version=(3, 8, 10))))
        self.assertTrue(cs["python"].blocking)
        self.assertIn("3.8.10", cs["python"].detail)
        self.assertIn("3.9", cs["python"].detail)

    def test_no_network_blocks_unless_a_local_copy_exists(self):
        offline = lambda h, p, t: False  # noqa: E731
        self.assertTrue(by_id(envcheck.run_checks(ctx(net=offline)))["net"].blocking)
        with_bundle = by_id(envcheck.run_checks(ctx(net=offline, bundle=Path("/somewhere"))))["net"]
        self.assertEqual(with_bundle.status, "warn")
        self.assertFalse(with_bundle.blocking)

    def test_network_check_targets_the_repo_host(self):
        seen = []
        with mock.patch.dict(os.environ, {"CPE_REPO_URL": "https://git.example.org/x/y.git"}):
            envcheck.run_checks(ctx(net=lambda h, p, t: seen.append((h, p)) or True))
        self.assertIn(("git.example.org", 443), seen)

    def test_low_disk_blocks(self):
        c = by_id(envcheck.run_checks(ctx(free_mb=lambda p: 120.0)))["disk"]
        self.assertTrue(c.blocking)
        self.assertIn("120", c.detail)

    def test_unwritable_target_blocks(self):
        t = TempDir()
        self.addCleanup(t.cleanup)
        with mock.patch("os.access", return_value=False):
            c = by_id(envcheck.run_checks(ctx(target=t.path / "app")))["write"]
        self.assertTrue(c.blocking)

    def test_missing_git_is_a_fixable_warning_not_a_blocker(self):
        c = ctx(which=lambda n: None if n == "git" else f"/usr/bin/{n}")
        cs = by_id(envcheck.run_checks(c))
        self.assertEqual(cs["git"].status, "warn")
        self.assertEqual(cs["git"].fix, "install_git")
        self.assertFalse(cs["git"].blocking)

    def test_port_in_use_is_only_a_warning(self):
        c = by_id(envcheck.run_checks(ctx(port_free=lambda p: False)))["port"]
        self.assertEqual(c.status, "warn")
        self.assertFalse(c.blocking)

    def test_missing_compiler_is_informational_and_fixable(self):
        c = by_id(envcheck.run_checks(ctx(which=lambda n: None if n == "g++" else f"/usr/bin/{n}")))["gpp"]
        self.assertEqual((c.status, c.fix, c.blocking), ("info", "install_gpp", False))

    def test_windows_compiler_found_in_msys2_even_if_not_on_path(self):
        t = TempDir()
        self.addCleanup(t.cleanup)
        d = t.path / "msys64" / "ucrt64" / "bin"
        d.mkdir(parents=True)
        (d / "g++.exe").write_text("x")
        p = plat("windows", str(t.path), MSYS2_ROOT=str(t.path / "msys64"))
        c = ctx(p, which=lambda n: None)
        self.assertEqual(envcheck.find_gpp(c), str(d / "g++.exe"))
        self.assertEqual(by_id(envcheck.run_checks(c))["gpp"].status, "ok")

    def test_tk_states(self):
        self.assertEqual(by_id(envcheck.run_checks(ctx(plat(DISPLAY=":0"))))["tk"].status, "ok")
        no_display = by_id(envcheck.run_checks(ctx(plat())))["tk"]
        self.assertEqual(no_display.status, "warn")
        self.assertIn("DISPLAY", no_display.detail)
        missing = by_id(envcheck.run_checks(ctx(plat(DISPLAY=":0"), has_tk=lambda: False)))["tk"]
        self.assertEqual((missing.status, missing.fix), ("warn", "install_tk"))
        mac = by_id(envcheck.run_checks(ctx(plat("macos"), has_tk=lambda: False)))["tk"]
        self.assertIsNone(mac.fix)
        self.assertIn("python.org", mac.hint)

    def test_browser_detection_per_platform(self):
        t = TempDir()
        self.addCleanup(t.cleanup)
        edge = t.path / "Microsoft" / "Edge" / "Application" / "msedge.exe"
        edge.parent.mkdir(parents=True)
        edge.write_text("x")
        p = plat("windows", str(t.path), **{"ProgramFiles(x86)": str(t.path)})
        self.assertEqual(envcheck.find_app_browser(ctx(p, which=lambda n: None)), str(edge))
        self.assertIsNone(envcheck.find_app_browser(ctx(plat("linux"), which=lambda n: None)))
        self.assertEqual(envcheck.find_app_browser(ctx(plat("linux"), which=lambda n: "/usr/bin/chromium" if n == "chromium" else None)), "/usr/bin/chromium")

    def test_existing_install_is_reported(self):
        self.assertIn("尚未安裝", by_id(envcheck.run_checks(ctx()))["existing"].detail)
        self.assertIn("2.4.1", by_id(envcheck.run_checks(ctx(), installed_version="2.4.1"))["existing"].detail)

    def test_network_check_can_be_skipped(self):
        self.assertNotIn("net", by_id(envcheck.run_checks(ctx(), network=False)))

    def test_run_cmd_reports_missing_program_and_timeout(self):
        rc, out = envcheck.run_cmd(["definitely-not-a-real-program-xyz"], 5)
        self.assertEqual(rc, 127)
        rc, out = envcheck.run_cmd([sys.executable, "-c", "import time; time.sleep(30)"], 1)
        self.assertEqual(rc, 124)
        rc, out = envcheck.run_cmd([sys.executable, "-c", "print('你好')"], 20, dict(os.environ, PYTHONIOENCODING="utf-8"))          # Windows 的管線預設不是 UTF-8
        self.assertEqual((rc, out), (0, "你好"))

    def test_port_probe_sees_a_real_listener(self):
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        self.addCleanup(s.close)
        self.assertFalse(envcheck.port_is_free(s.getsockname()[1]))


class FixPlans(unittest.TestCase):
    def test_linux_apt_needs_sudo_unless_root(self):
        only = lambda *names: (lambda n: f"/usr/bin/{n}" if n in names else None)  # noqa: E731
        plan = envcheck.fix_plan(ctx(which=only("apt-get")), "install_git")
        self.assertEqual(plan.steps, [["sudo", "apt-get", "update"], ["sudo", "apt-get", "install", "-y", "git"]])
        self.assertTrue(plan.needs_admin)
        root = envcheck.fix_plan(ctx(which=only("apt-get"), is_admin=lambda: True), "install_gpp")
        self.assertEqual(root.steps[-1], ["apt-get", "install", "-y", "g++"])
        self.assertFalse(root.needs_admin)
        gui = envcheck.fix_plan(ctx(which=only("apt-get", "pkexec")), "install_tk", gui=True)
        self.assertEqual(gui.steps[-1][:2], ["pkexec", "apt-get"])
        self.assertEqual(gui.steps[-1][-1], "python3-tk")

    def test_other_linux_package_managers(self):
        for mgr, git_cmd in (("dnf", ["sudo", "dnf", "install", "-y", "git"]), ("pacman", ["sudo", "pacman", "-S", "--noconfirm", "--needed", "git"]),
                             ("zypper", ["sudo", "zypper", "--non-interactive", "install", "git"])):
            plan = envcheck.fix_plan(ctx(which=lambda n, m=mgr: f"/usr/bin/{n}" if n == m else None), "install_git")
            self.assertEqual(plan.steps[-1], git_cmd, mgr)
        self.assertIsNone(envcheck.fix_plan(ctx(which=lambda n: None), "install_git"))

    def test_windows_uses_winget_and_msys2(self):
        p = plat("windows", "C:/Users/u", MSYS2_ROOT="C:/msys64")
        self.assertIsNone(envcheck.fix_plan(ctx(p, which=lambda n: None), "install_git"))              # 沒有 winget：不能自動
        git = envcheck.fix_plan(ctx(p, which=lambda n: "winget"), "install_git")
        self.assertIn("Git.Git", git.steps[0])
        self.assertTrue(git.needs_admin)
        gpp = envcheck.fix_plan(ctx(p, which=lambda n: "winget"), "install_gpp")
        self.assertIn("MSYS2.MSYS2", gpp.steps[0])
        self.assertIn("pacman", gpp.steps[1][-1])
        self.assertIsNone(envcheck.fix_plan(ctx(p, which=lambda n: "winget"), "install_tk"))

    def test_macos_prefers_brew_for_git_and_xcode_select_otherwise(self):
        mac = plat("macos")
        self.assertEqual(envcheck.fix_plan(ctx(mac, which=lambda n: "/opt/homebrew/bin/brew" if n == "brew" else None), "install_git").steps, [["brew", "install", "git"]])
        self.assertEqual(envcheck.fix_plan(ctx(mac, which=lambda n: None), "install_gpp").steps, [["xcode-select", "--install"]])

    def test_unknown_fix_id(self):
        self.assertIsNone(envcheck.fix_plan(ctx(), "install_nothing"))

    def test_apply_fix_runs_steps_and_reports_failure(self):
        calls = []

        def ok(cmd, t=60, env=None):
            calls.append(cmd)
            return 0, "done"
        c = ctx(which=lambda n: "/usr/bin/apt-get" if n == "apt-get" else None, run=ok, is_admin=lambda: True)
        logs = []
        self.assertEqual(envcheck.apply_fix(c, "install_git", logs.append), (True, "完成"))
        self.assertEqual(len(calls), 2)
        bad = ctx(which=lambda n: "/usr/bin/apt-get" if n == "apt-get" else None, run=lambda cmd, t=60, env=None: (100, "E: Unable to locate package"), is_admin=lambda: True)
        okk, msg = envcheck.apply_fix(bad, "install_git")
        self.assertFalse(okk)
        self.assertIn("100", msg)
        okk, msg = envcheck.apply_fix(ctx(which=lambda n: None), "install_git")
        self.assertFalse(okk)
        self.assertIn("手動", msg)

    def test_xcode_select_already_installed_is_not_an_error(self):
        c = ctx(plat("macos"), which=lambda n: None, run=lambda cmd, t=60, env=None: (1, "xcode-select: error: command line tools are already installed"))
        self.assertTrue(envcheck.apply_fix(c, "install_gpp")[0])


class Paths(unittest.TestCase):
    def test_default_locations_per_os(self):
        w = plat("windows", "C:/Users/u", LOCALAPPDATA="C:/Users/u/AppData/Local", APPDATA="C:/Users/u/AppData/Roaming")
        self.assertEqual(w.launcher_home, Path("C:/Users/u/AppData/Local") / "CPE-Coach")
        self.assertEqual(w.menu_dir, Path("C:/Users/u/AppData/Roaming") / "Microsoft" / "Windows" / "Start Menu" / "Programs")
        m = plat("macos", "/Users/u")
        self.assertEqual(m.launcher_home, Path("/Users/u/Library/Application Support/CPE-Coach"))
        self.assertEqual(m.menu_dir, Path("/Users/u/Applications"))
        lx = plat("linux", "/home/u")
        self.assertEqual(lx.launcher_home, Path("/home/u/.local/share/cpe-coach"))
        self.assertEqual(plat("linux", "/home/u", XDG_DATA_HOME="/x").launcher_home, Path("/x/cpe-coach"))
        self.assertEqual(lx.default_workspace, Path("/home/u/CPE學習進度"))

    def test_overrides_for_tests(self):
        p = plat("linux", "/home/u", CPE_LAUNCHER_HOME="/a", CPE_LAUNCHER_DESKTOP="/b", CPE_LAUNCHER_MENU="/c")
        self.assertEqual((p.launcher_home, p.desktop_dir, p.menu_dir), (Path("/a"), Path("/b"), Path("/c")))

    def test_pythonw_is_used_for_gui_on_windows(self):
        t = TempDir()
        self.addCleanup(t.cleanup)
        (t.path / "python.exe").write_text("x")
        self.assertEqual(osinfo.pythonw_for(str(t.path / "python.exe")), str(t.path / "python.exe"))       # 沒有 pythonw.exe 就維持原樣
        (t.path / "pythonw.exe").write_text("x")
        self.assertEqual(osinfo.pythonw_for(str(t.path / "python.exe")), str(t.path / "pythonw.exe"))


if __name__ == "__main__":
    unittest.main()
