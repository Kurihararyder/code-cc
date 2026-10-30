import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

from cpe_coach import backup, bank, cli, judge, service
from cpe_coach.store import Workspace, WorkspaceError

POSIX = os.name == "posix"


def mkws(tmp):
    return Workspace.create(Path(tmp), "2026-11-01")


class LimitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_code(self, code, timeout=3.0, mem=256, inp=""):
        f = self.d / "p.py"
        f.write_text(code, encoding="utf-8")
        return judge.run_program(f, inp, timeout, None, mem)

    def test_normal_program(self):
        r = self.run_code("print(int(input())*2)", inp="21\n")
        self.assertEqual((r.rc, r.out.strip(), r.timed_out, r.mle, r.ole), (0, "42", False, False, False))

    def test_memory_limit(self):
        r = self.run_code("x = [0] * (10**9)\nprint(len(x))")
        self.assertTrue(r.mle)

    @unittest.skipUnless(POSIX and shutil.which("ps"), "RSS 輪詢需要 ps")
    def test_rss_probe_and_watchdog_path(self):
        """macOS 沒有 RLIMIT_AS，改用 ps 輪詢常駐記憶體。這裡驗證探測值，並在 Linux 強制走這條路徑確認不會誤殺正常程式。"""
        p = subprocess.Popen([sys.executable, "-c", "import time\nb = bytearray(120 * 1024 * 1024)\nfor i in range(0, len(b), 4096):\n    b[i] = 1\ntime.sleep(5)"])
        try:
            time.sleep(1.0)
            self.assertGreater(judge._rss_mb(p.pid), 100)
            self.assertEqual(judge._rss_mb(2 ** 22 + 12345), 0.0)           # 不存在的 pid
        finally:
            p.kill()
            p.wait()
        old = judge.WATCH_RSS
        judge.WATCH_RSS = True
        try:
            r = self.run_code("print(sum(range(10)))", timeout=5, mem=256)
        finally:
            judge.WATCH_RSS = old
        self.assertEqual((r.rc, r.out.strip(), r.mle), (0, "45", False))

    def test_output_limit_stops_runaway_output(self):
        t = time.time()
        r = self.run_code("while True: print('x' * 1000)", timeout=10)
        self.assertTrue(r.ole)
        self.assertLess(time.time() - t, 8)
        self.assertLessEqual(len(r.out), judge.OUT_LIMIT_MB * 1048576)

    @unittest.skipUnless(POSIX, "行程群組")
    def test_timeout_kills_children_too(self):
        marker = self.d / "alive"
        code = ("import os,time\nif os.fork() == 0:\n    time.sleep(2)\n    open(%r,'w').write('child survived')\nelse:\n    time.sleep(30)\n" % str(marker))
        r = self.run_code(code, timeout=0.5)
        self.assertTrue(r.timed_out)
        time.sleep(2.5)
        self.assertFalse(marker.exists(), "子行程沒有被一起殺掉")

    def test_judge_reports_tle_and_mle(self):
        t = self.d / "t"
        t.mkdir()
        (t / "a.in").write_text("1\n", encoding="utf-8")
        (t / "a.out").write_text("1\n", encoding="utf-8")
        f = self.d / "s.py"
        f.write_text("while True: pass", encoding="utf-8")
        self.assertEqual(judge.judge(f, t, timeout=0.5).verdict, judge.TLE)
        f.write_text("x = bytearray(b'x') * (2 * 1024**3)", encoding="utf-8")
        self.assertEqual(judge.judge(f, t, timeout=3.0, mem_mb=256).verdict, judge.MLE)

    @unittest.skipUnless(shutil.which("g++"), "需要 g++")
    def test_cpp_memory_and_tle(self):
        t = self.d / "t"
        t.mkdir()
        (t / "a.in").write_text("1\n", encoding="utf-8")
        (t / "a.out").write_text("1\n", encoding="utf-8")
        f = self.d / "m.cpp"
        f.write_text("#include <vector>\n#include <cstdio>\nint main(){ std::vector<char> v(2000000000); for (size_t i = 0; i < v.size(); i += 4096) v[i] = 1; printf(\"1\\n\"); }\n", encoding="utf-8")
        self.assertEqual(judge.judge(f, t, timeout=10.0, mem_mb=256).verdict, judge.MLE)
        f.write_text("int main(){ for(;;); }\n", encoding="utf-8")
        self.assertEqual(judge.judge(f, t, timeout=0.7).verdict, judge.TLE)
        f.write_text("#include <cstdio>\nint main(){ int x; scanf(\"%d\", &x); printf(\"%d\\n\", x); }\n", encoding="utf-8")
        self.assertEqual(judge.judge(f, t, timeout=5.0).verdict, judge.AC)


class LockAndRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = mkws(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_lock_is_reentrant_and_released(self):
        with self.ws.lock():
            with self.ws.lock():
                pass
        with self.ws.lock(timeout=0.2):
            pass

    def test_second_process_waits_then_times_out(self):
        code = ("import sys,time\nfrom pathlib import Path\nfrom cpe_coach.store import Workspace\n"
                "ws=Workspace(Path(sys.argv[1]))\nwith ws.lock():\n    print('locked', flush=True)\n    time.sleep(4)\n")
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parent.parent))
        p = subprocess.Popen([sys.executable, "-c", code, str(self.ws.root)], stdout=subprocess.PIPE, text=True, env=env)
        try:
            self.assertEqual(p.stdout.readline().strip(), "locked")
            with self.assertRaises(WorkspaceError) as cm:
                with self.ws.lock(timeout=0.4):
                    pass
            self.assertIn("正在寫入", str(cm.exception))
        finally:
            p.kill()
            p.wait()
        with self.ws.lock(timeout=2):                      # 持有者結束後可以取得
            pass

    def test_corrupt_state_recovers_from_previous_version(self):
        st = self.ws.state()
        self.ws.problem(st, "a")["attempts"] = 7
        self.ws.save_state(st)
        st = self.ws.state()
        self.ws.problem(st, "a")["attempts"] = 8
        self.ws.save_state(st)                             # 此時 .bak 是 7
        self.ws.state_path.write_text("{ 壞掉的 json", encoding="utf-8")
        self.assertEqual(self.ws.state()["problems"]["a"]["attempts"], 7)
        self.assertTrue((self.ws.meta / "recovered.txt").exists())
        self.assertEqual(self.ws.state()["problems"]["a"]["attempts"], 7)    # 修復後檔案有效

    def test_corrupt_without_backup_gives_clear_error(self):
        self.ws.config_path.write_text("not json", encoding="utf-8")
        bak = self.ws.config_path.with_suffix(".json.bak")
        if bak.exists():
            bak.unlink()
        with self.assertRaises(WorkspaceError) as cm:
            self.ws.config()
        self.assertIn("損壞", str(cm.exception))

    def test_partial_last_event_line_is_ignored(self):
        self.ws.log("test", problem="a", verdict="AC")
        with self.ws.events_path.open("a", encoding="utf-8") as f:
            f.write('{"ts": 1, "kind": "te')               # 被中斷的半行
        ev = self.ws.events()
        self.assertEqual(len(ev), 1)

    def test_snapshot_rotation(self):
        for i in range(6):
            (self.ws.meta / "backups").mkdir(exist_ok=True)
            self.ws.clock = lambda i=i: 1_800_000_000.0 + i * 7200
            self.ws.snapshot_state(every=0, keep=3)
        self.assertEqual(len(list((self.ws.meta / "backups").glob("state-*.json"))), 3)


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = mkws(self.tmp.name)
        self.bank = bank.load_bank(self.ws)

    def tearDown(self):
        self.tmp.cleanup()

    def test_roundtrip_and_what_is_included(self):
        service.create_solution(self.ws, self.bank, "d001")          # 內建練習題：測資不備份
        (self.ws.solutions / "d001.py").write_text("print('mine')\n", encoding="utf-8")
        (self.ws.tests / "uva9999").mkdir()
        (self.ws.tests / "uva9999" / "case01.in").write_text("1\n", encoding="utf-8")
        (self.ws.tests / "uva9999" / "case01.out").write_text("2\n", encoding="utf-8")
        st = self.ws.state()
        self.ws.problem(st, "d001")["attempts"] = 3
        self.ws.save_state(st)
        z = backup.export_workspace(self.ws, self.ws.root / "b.zip")
        names = set(zipfile.ZipFile(z).namelist())
        self.assertIn(".cpe/state.json", names)
        self.assertIn("solutions/d001.py", names)
        self.assertIn("tests/uva9999/case01.in", names)
        self.assertFalse([n for n in names if n.startswith("tests/d001")])
        self.assertFalse([n for n in names if "backups/" in n or n.endswith("lock")])
        with tempfile.TemporaryDirectory() as other:
            n = backup.restore_workspace(z, Path(other))
            self.assertGreater(n, 3)
            ws2 = Workspace(Path(other))
            self.assertEqual(ws2.state()["problems"]["d001"]["attempts"], 3)
            self.assertEqual((ws2.solutions / "d001.py").read_text(encoding="utf-8"), "print('mine')\n")
            with self.assertRaises(WorkspaceError):                    # 已有工作區要 --force
                backup.restore_workspace(z, Path(other))
            backup.restore_workspace(z, Path(other), force=True)
            self.assertTrue(list(Path(other).glob(".cpe.before-restore-*")))

    def test_rejects_path_traversal_and_foreign_zip(self):
        evil = self.ws.root / "evil.zip"
        with zipfile.ZipFile(evil, "w") as zf:
            zf.writestr(".cpe/state.json", "{}")
            zf.writestr("../escaped.txt", "x")
        with tempfile.TemporaryDirectory() as other:
            with self.assertRaises(WorkspaceError):
                backup.restore_workspace(evil, Path(other) / "inner")
            self.assertFalse((Path(other) / "escaped.txt").exists())
        foreign = self.ws.root / "foreign.zip"
        with zipfile.ZipFile(foreign, "w") as zf:
            zf.writestr("hello.txt", "x")
        with self.assertRaises(WorkspaceError):
            backup.restore_workspace(foreign, self.ws.root / "x")

    def test_cli_export_and_restore(self):
        import contextlib
        import io
        old = os.getcwd()
        os.chdir(self.ws.root)
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(cli.main(["export", "-o", "out.zip"]), 0)
            self.assertTrue((self.ws.root / "out.zip").exists())
            with tempfile.TemporaryDirectory() as other, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(["restore", "out.zip", "--dir", other]), 0)
                self.assertTrue((Path(other) / ".cpe" / "state.json").exists())
        finally:
            os.chdir(old)


if __name__ == "__main__":
    unittest.main()
