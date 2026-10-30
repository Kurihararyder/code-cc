"""控制台的『開啟』『關閉』：真的啟動 cpe web、用連線探測判斷狀態、真的結束程序。"""
import json
import os
import socket
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
from launcher_helpers import HAVE_GIT, TempDir, bump_version, clean_registry, copy_app_tree, free_port, isolated_env, make_origin, wait_for  # noqa: E402

from cpe_coach import __version__  # noqa: E402
from cpe_coach.launcher import config as cfgmod  # noqa: E402
from cpe_coach.launcher import engine, server  # noqa: E402
from cpe_coach.launcher.engine import InstallOptions, Reporter  # noqa: E402
from cpe_coach.launcher.envcheck import Ctx  # noqa: E402
from cpe_coach.launcher.osinfo import detect  # noqa: E402

WINDOWS = sys.platform == "win32"


class ServerBase(unittest.TestCase):
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
        self.ctx = Ctx(plat=self.plat, net=lambda *a: False)
        tree = copy_app_tree(self.t.path / "tree")
        self.port = free_port()
        opts = InstallOptions(app_dir=self.t.path / "app", workspace=self.t.path / "ws", source="bundle", bundle=tree, python=engine.base_python(),
                              port=self.port, desktop=False, menu=False, add_path=False)
        self.cfg = engine.install(opts, self.plat, self.ctx, Reporter())
        self.procs = []
        self.addCleanup(self.cleanup_procs)

    def cleanup_procs(self):
        try:
            server.stop(self.cfg, self.plat)
        except Exception:
            pass
        for p in self.procs:
            if p.poll() is None:
                server.kill_tree(p.pid, 2)
            try:
                p.wait(10)
            except Exception:
                pass

    def spawn_sleeper(self):
        p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.procs.append(p)
        return p

    def write_run(self, pid, port):
        d = server.run_dir(self.plat)
        d.mkdir(parents=True, exist_ok=True)
        (d / server.RUN_FILE).write_text(json.dumps({"pid": pid, "port": port}), encoding="utf-8")


class StartStop(ServerBase):
    def test_start_serves_the_real_app_and_stop_ends_it(self):
        self.assertEqual(server.status(self.cfg, self.plat).state, "stopped")
        st = server.start(self.cfg, self.plat)
        self.assertTrue(st.running)
        self.assertEqual((st.port, st.url), (self.port, f"http://127.0.0.1:{self.port}/"))
        data = server.probe(self.port)
        self.assertEqual(data["app"], "cpe-coach")
        self.assertEqual(data["version"], __version__)
        self.assertEqual(data["pid"], st.pid)
        self.assertEqual(Path(data["workspace"]).resolve(), (self.t.path / "ws").resolve())
        self.assertFalse(st.external)
        import urllib.request
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(st.url, timeout=10) as r:           # 首頁真的有網頁
            self.assertIn("text/html", r.headers["Content-Type"])
        self.assertTrue(server.log_path(self.plat).read_text(encoding="utf-8").count("CPE 教練網頁介面") >= 1)
        self.assertTrue(server.stop(self.cfg, self.plat))
        self.assertIsNone(server.probe(self.port))
        self.assertFalse(server.pid_alive(st.pid))
        self.assertFalse((server.run_dir(self.plat) / server.RUN_FILE).exists())
        self.assertEqual(server.status(self.cfg, self.plat).state, "stopped")
        self.assertFalse(server.stop(self.cfg, self.plat))                         # 原本就關著：回傳 False、不出錯

    def test_start_is_idempotent(self):
        a = server.start(self.cfg, self.plat)
        b = server.start(self.cfg, self.plat)
        self.assertEqual(a.pid, b.pid)

    def test_status_is_visible_from_another_process(self):
        server.start(self.cfg, self.plat)
        out = subprocess.run([sys.executable, str(self.t.path / "app" / "cpe-panel.pyw"), "status", "--json"], env=self.env, capture_output=True, timeout=60,
                             cwd=str(self.t.path))
        data = json.loads(out.stdout.decode("utf-8"))
        self.assertEqual((out.returncode, data["state"], data["port"]), (0, "running", self.port))
        server.stop(self.cfg, self.plat)
        out = subprocess.run([sys.executable, str(self.t.path / "app" / "cpe-panel.pyw"), "status"], env=self.env, capture_output=True, timeout=60, cwd=str(self.t.path))
        self.assertEqual(out.returncode, 3)

    def test_stop_from_another_process_closes_the_service(self):
        st = server.start(self.cfg, self.plat)
        out = subprocess.run([sys.executable, str(self.t.path / "app" / "cpe-panel.pyw"), "close", "--text"], env=self.env, capture_output=True, timeout=60, cwd=str(self.t.path))
        self.assertEqual(out.returncode, 0, out.stdout.decode("utf-8", "replace"))
        self.assertTrue(wait_for(lambda: server.probe(self.port) is None, 15))
        self.assertTrue(wait_for(lambda: not server.pid_alive(st.pid), 15))

    def test_a_service_started_in_a_terminal_is_recognised_and_can_be_closed(self):
        """使用者自己在終端機執行 cpe web：控制台沒有 PID 檔也要認得它、關得掉。"""
        env = dict(self.env, PYTHONPATH=str(self.t.path / "app"))
        p = subprocess.Popen([self.cfg.python, "-u", "-m", "cpe_coach", "web", "--port", str(self.port), "--no-open"], cwd=str(self.t.path / "ws"), env=env,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.procs.append(p)
        self.assertTrue(wait_for(lambda: server.probe(self.port) is not None, 30))
        st = server.status(self.cfg, self.plat)
        self.assertEqual((st.state, st.external, st.pid), ("running", True, p.pid))
        self.assertTrue(server.stop(self.cfg, self.plat))
        self.assertTrue(wait_for(lambda: p.poll() is not None, 15))

    def test_stale_run_file_is_cleaned_up(self):
        dead = subprocess.Popen([sys.executable, "-c", "pass"])
        dead.wait()
        self.write_run(dead.pid, self.port)
        self.assertEqual(server.status(self.cfg, self.plat).state, "stopped")
        self.assertFalse((server.run_dir(self.plat) / server.RUN_FILE).exists())
        self.assertFalse(server.pid_alive(dead.pid))

    def test_unresponsive_process_is_reported_and_can_be_killed(self):
        p = self.spawn_sleeper()
        self.write_run(p.pid, free_port())
        st = server.status(self.cfg, self.plat)
        self.assertEqual((st.state, st.pid), ("unresponsive", p.pid))
        self.assertTrue(server.stop(self.cfg, self.plat))
        self.assertTrue(wait_for(lambda: p.poll() is not None, 15))

    def test_a_busy_port_makes_the_service_use_another_one(self):
        blocker = socket.socket()
        blocker.bind(("127.0.0.1", self.port))
        blocker.listen(1)
        self.addCleanup(blocker.close)
        logs = []
        st = server.start(self.cfg, self.plat, log=logs.append)
        self.assertNotEqual(st.port, self.port)
        self.assertTrue(any("被別的程式占用" in ln for ln in logs))
        self.assertEqual(self.cfg.port, self.port)                                 # 設定檔裡的偏好不改
        self.assertEqual(server.status(self.cfg, self.plat).port, st.port)
        self.assertEqual(server.probe(st.port)["pid"], st.pid)

    def test_another_program_on_the_port_is_not_mistaken_for_ours(self):
        import http.server
        import threading

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                body = b'{"hello": "world"}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        httpd = http.server.HTTPServer(("127.0.0.1", self.port), H)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        self.assertIsNone(server.probe(self.port))
        self.assertEqual(server.status(self.cfg, self.plat).state, "stopped")
        self.assertFalse(server.stop(self.cfg, self.plat))                          # 不會去結束別人的程式

    def test_missing_workspace_or_python_gives_actionable_errors(self):
        from cpe_coach.launcher.source import rmtree
        rmtree(Path(self.cfg.workspace))
        with self.assertRaises(server.ServerError) as cm:
            server.start(self.cfg, self.plat)
        self.assertIn("修復", str(cm.exception))
        cfg2 = cfgmod.load(self.plat.launcher_home)
        cfg2.python = str(self.t.path / "no-python")
        (self.t.path / "ws").mkdir()
        with self.assertRaises(server.ServerError) as cm:
            server.start(cfg2, self.plat)
        self.assertIn("Python", str(cm.exception))

    def test_a_service_that_dies_immediately_reports_why(self):
        stub = self.t.path / ("fake-python.cmd" if WINDOWS else "fake-python")
        stub.write_text("@echo off\r\necho boom: cannot start 1>&2\r\nexit /b 3\r\n" if WINDOWS else "#!/bin/sh\necho 'boom: cannot start' >&2\nexit 3\n", encoding="utf-8")
        stub.chmod(0o755)
        cfg = cfgmod.load(self.plat.launcher_home)
        cfg.python = str(stub)
        with self.assertRaises(server.ServerError) as cm:
            server.start(cfg, self.plat, wait=20)
        self.assertIn("結束碼 3", str(cm.exception))
        self.assertIn("boom", str(cm.exception))
        self.assertFalse((server.run_dir(self.plat) / server.RUN_FILE).exists())

    def test_service_starts_in_the_workspace_and_uses_the_installed_code(self):
        st = server.start(self.cfg, self.plat)
        out = subprocess.run([sys.executable, "-c", "import json,urllib.request as u; o=u.build_opener(u.ProxyHandler({})); print(o.open('http://127.0.0.1:%d/api/ping').read().decode())" % st.port],
                             capture_output=True, timeout=30)
        self.assertEqual(json.loads(out.stdout.decode("utf-8"))["pid"], st.pid)

    def test_log_does_not_grow_forever(self):
        lp = server.log_path(self.plat)
        lp.parent.mkdir(parents=True, exist_ok=True)
        lp.write_bytes(b"x" * (server.LOG_MAX + 10))
        server.start(self.cfg, self.plat)
        self.assertLess(lp.stat().st_size, server.LOG_MAX)

    def test_open_ui_prefers_an_app_window_when_a_chromium_browser_exists(self):
        calls = []
        fake = self.t.path / ("msedge.exe" if WINDOWS else "chromium")
        fake.write_text("x")
        ctx_browser = mock.patch.object(server, "find_app_browser", return_value=str(fake))
        with ctx_browser, mock.patch.object(server.subprocess, "Popen", side_effect=lambda cmd, **kw: calls.append(cmd)):
            kind = server.open_ui("http://127.0.0.1:1/", self.cfg, self.plat)
        self.assertEqual(kind, "app")
        self.assertEqual(calls[0][0], str(fake))
        self.assertTrue(any(a.startswith("--app=http://127.0.0.1:1/") for a in calls[0]))
        self.cfg.options["app_window"] = False
        opened = []
        with ctx_browser, mock.patch.object(server.webbrowser, "open", side_effect=opened.append):
            self.assertEqual(server.open_ui("http://127.0.0.1:1/", self.cfg, self.plat), "browser")
        self.assertEqual(opened, ["http://127.0.0.1:1/"])

    def test_pick_port_skips_busy_ones_and_gives_up_when_all_are_busy(self):
        self.assertEqual(server.pick_port(9000, lambda p: p == 9003), 9003)
        with self.assertRaises(server.ServerError):
            server.pick_port(9000, lambda p: False, span=3)


@unittest.skipUnless(HAVE_GIT, "需要 git")
class UpdateWhileRunning(unittest.TestCase):
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
        self.ctx = Ctx(plat=self.plat, net=lambda *a: True)
        self.origin = make_origin(self.t.path)
        q = mock.patch.dict(os.environ, {"CPE_REPO_URL": str(self.origin), "CPE_INSTALL_BRANCH": "main"})
        q.start()
        self.addCleanup(q.stop)
        opts = InstallOptions(app_dir=self.t.path / "app", workspace=self.t.path / "ws", branch="main", python=engine.base_python(), port=free_port(),
                              desktop=False, menu=False, add_path=False)
        self.cfg = engine.install(opts, self.plat, self.ctx, Reporter())
        self.addCleanup(lambda: server.stop(self.cfg, self.plat))

    def test_service_is_restarted_on_the_new_code(self):
        old = server.start(self.cfg, self.plat)
        self.assertEqual(server.probe(old.port)["version"], __version__)
        bump_version(self.origin, "9.9.9")
        r = engine.update(self.cfg, self.plat, self.ctx, Reporter())
        self.assertEqual(r["status"], "updated")
        now = server.status(self.cfg, self.plat)
        self.assertTrue(now.running)
        self.assertNotEqual(now.pid, old.pid)
        self.assertEqual(server.probe(now.port)["version"], "9.9.9")
        self.assertFalse(server.pid_alive(old.pid))

    def test_service_stays_up_if_there_is_nothing_to_update(self):
        old = server.start(self.cfg, self.plat)
        self.assertEqual(engine.update(self.cfg, self.plat, self.ctx, Reporter())["status"], "up_to_date")
        self.assertEqual(server.status(self.cfg, self.plat).pid, old.pid)


if __name__ == "__main__":
    unittest.main()
