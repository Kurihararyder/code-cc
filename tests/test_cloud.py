"""學程雲端（Supabase）：登入、授權（含離線寬限）、閘門、進度同步、AI 代理，全部用假的伺服器測，不連網。"""
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from cpe_coach import cloud, web
from cpe_coach.store import Workspace

CFG = {"url": "https://x.supabase.co", "key": "sb_publishable_test", "domain": "t.example.com"}


class FakeServer:
    """只實作用到的端點。access：check_access 回傳的內容；可隨時改。"""

    def __init__(self):
        self.access = {"ok": True, "reason": "ok", "role": "student", "student_id": "s1", "name": "甲", "cohort": "114", "ai_allowed": False,
                       "must_change_pw": False, "valid_until": None, "ip": "1.2.3.4"}
        self.app = {"grace_hours": 72, "min_version": "2.9.0", "latest_version": "2.9.0", "announcement": "", "ai_enabled": False}
        self.down = False
        self.progress = None
        self.calls = []
        self.good = ("s1@t.example.com", "pw123456")

    def __call__(self, method, url, headers, body, timeout):
        if self.down:
            raise cloud.CloudError("連不上學程伺服器：test", 0, "network")
        path = url.split("supabase.co", 1)[1]
        data = json.loads(body.decode()) if body else {}
        self.calls.append((method, path))
        if path.startswith("/auth/v1/token?grant_type=password"):
            if (data["email"], data["password"]) != self.good:
                return 400, {"error": "invalid_grant"}
            return 200, {"access_token": "AT", "refresh_token": "RT", "expires_in": 3600}
        if path.startswith("/auth/v1/token?grant_type=refresh_token"):
            return (200, {"access_token": "AT2", "refresh_token": "RT2", "expires_in": 3600}) if data.get("refresh_token") == "RT" else (400, {})
        if path == "/rest/v1/rpc/check_access":
            return 200, dict(self.access, app=self.app)
        if path == "/rest/v1/rpc/app_info":
            return 200, self.app
        if path == "/rest/v1/rpc/load_progress":
            return 200, {"ok": True, "data": self.progress}
        if path == "/rest/v1/rpc/save_progress":
            self.progress = data["p_data"]
            self.summary = data["p_summary"]
            return 200, {"ok": True}
        if path == "/auth/v1/user" and method == "PUT":
            return 200, {}
        if path == "/rest/v1/rpc/pw_changed":
            self.access["must_change_pw"] = False
            return 200, None
        return 404, {"message": "no " + path}


class CloudTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.srv = FakeServer()
        self.now = [1_000_000.0]
        self.c = cloud.Cloud(CFG, self.root, http=self.srv, clock=lambda: self.now[0])

    def test_login_ok_and_bad_password(self):
        with self.assertRaises(cloud.CloudError) as cm:
            self.c.login("s1", "wrong")
        self.assertEqual(cm.exception.reason, "bad_credentials")
        r = self.c.login("S1 ", "pw123456")            # 學號不分大小寫、忽略前後空白
        self.assertTrue(r["ok"])
        st = self.c.status("2.9.0")
        self.assertTrue(st["allowed"] and st["logged_in"] and not st["is_admin"])

    def test_session_file_is_private_and_survives_restart(self):
        self.c.login("s1", "pw123456")
        f = self.root / ".cpe" / "cloud.json"
        self.assertTrue(f.exists())
        if hasattr(f, "stat") and __import__("os").name != "nt":
            self.assertEqual(f.stat().st_mode & 0o077, 0)
        c2 = cloud.Cloud(CFG, self.root, http=self.srv, clock=lambda: self.now[0])
        self.assertTrue(c2.status("2.9.0")["logged_in"])

    def test_denied_reasons_block(self):
        self.c.login("s1", "pw123456")
        for reason in ("inactive", "expired", "not_started", "ip_denied"):
            self.srv.access = dict(self.srv.access, ok=False, reason=reason)
            self.now[0] += cloud.CHECK_EVERY + 1
            st = self.c.status("2.9.0")
            self.assertFalse(st["allowed"], reason)
            self.assertEqual(st["reason"], reason)
            self.assertTrue(st["message"])

    def test_must_change_password_blocks_until_changed(self):
        self.srv.access["must_change_pw"] = True
        self.c.login("s1", "pw123456")
        self.assertFalse(self.c.status("2.9.0")["allowed"])
        with self.assertRaises(cloud.CloudError):
            self.c.change_password("short")
        self.c.change_password("longenough1")
        self.assertTrue(self.c.status("2.9.0")["allowed"])

    def test_forced_update_when_below_min_version(self):
        self.srv.app["min_version"] = "3.0.0"
        self.c.login("s1", "pw123456")
        st = self.c.status("2.9.0")
        self.assertTrue(st["need_update"] and not st["allowed"])
        self.assertTrue(self.c.status("3.0.0")["allowed"])

    def test_offline_grace(self):
        self.c.login("s1", "pw123456")
        self.srv.down = True
        self.now[0] += cloud.CHECK_EVERY + 1
        self.assertTrue(self.c.status("2.9.0")["allowed"])            # 離線但在寬限內
        self.assertTrue(self.c.status("2.9.0")["offline"])
        self.now[0] += 73 * 3600
        st = self.c.status("2.9.0")
        self.assertFalse(st["allowed"])
        self.assertEqual(st["reason"], "offline_expired")

    def test_offline_never_extends_past_expiry_and_rejects_clock_rollback(self):
        self.srv.access["valid_until"] = "1970-01-12T14:00:00+00:00"   # = 1_000_800 秒（比現在多 800 秒）
        self.c.login("s1", "pw123456")
        self.srv.down = True
        self.now[0] += cloud.CHECK_EVERY + 1
        self.assertTrue(self.c.status("2.9.0")["allowed"])
        self.now[0] += 3600
        self.assertEqual(self.c.status("2.9.0")["reason"], "expired")
        # 時鐘往回調：不能因此延長
        c2 = cloud.Cloud(CFG, self.root, http=self.srv, clock=lambda: 10.0)
        self.assertFalse(c2.status("2.9.0")["allowed"])

    def test_offline_without_previous_success_is_denied(self):
        self.srv.down = True
        c = cloud.Cloud(CFG, self.root, http=self.srv, clock=lambda: 5.0)
        self.assertFalse(c.status("2.9.0")["allowed"])
        with self.assertRaises(cloud.CloudError):
            c.login("s1", "pw123456")

    def test_expired_token_is_refreshed_and_dead_refresh_logs_out(self):
        self.c.login("s1", "pw123456")
        self.now[0] += 4000
        self.c.rpc("app_info")
        self.assertEqual(self.c.sess["access"], "AT2")
        self.now[0] += 4000
        self.c.sess["refresh"] = "dead"
        with self.assertRaises(cloud.CloudError):
            self.c.rpc("app_info")
        self.assertFalse(self.c.status("2.9.0")["logged_in"])

    def test_ai_available_needs_global_and_personal_grant(self):
        self.c.login("s1", "pw123456")
        self.assertFalse(self.c.ai_available()[0])
        self.srv.app["ai_enabled"] = True
        self.srv.access["ai_allowed"] = False
        self.c.access(force=True)
        self.assertIn("授權", self.c.ai_available()[1])
        self.srv.access["ai_allowed"] = True
        self.c.access(force=True)
        self.assertTrue(self.c.ai_available()[0])
        client = self.c.ai_client()
        self.assertFalse(client.send_auth)                              # 本機沒有任何 OpenAI 金鑰
        self.assertTrue(client.base_url.endswith("/functions/v1/ai-proxy"))

    def test_sync_roundtrip_between_two_machines(self):
        self.c.login("s1", "pw123456")
        ws1 = Workspace.create(self.root / "w1", "2026-11-01")
        ws1.log("note", x=1)
        self.c.sync(ws1)
        self.assertIn("events.jsonl", self.srv.progress["files"])
        self.assertEqual(self.srv.summary["events"], 1)
        ws2 = Workspace.create(self.root / "w2", "2026-11-01")
        ws2.log("note", x=2)
        c2 = cloud.Cloud(CFG, self.root / "other", http=self.srv, clock=lambda: self.now[0])
        c2.login("s1", "pw123456")
        c2.sync(ws2)
        self.assertEqual(len(ws2.events()), 2)                          # 兩台的紀錄合併
        self.c.sync(ws1)
        self.assertEqual(len(ws1.events()), 2)

    def test_unpack_rejects_path_traversal(self):
        d = self.root / "r"
        cloud._unpack({"files": {"../evil.txt": "x", "ok/a.txt": "y"}}, d)
        self.assertTrue((d / "ok" / "a.txt").exists())
        self.assertFalse((self.root / "evil.txt").exists())

    def test_config_off_switch(self):
        self.assertIsNone(cloud.load_config({"CPE_CLOUD": "off"}))
        cfg = cloud.load_config({})
        self.assertTrue(cfg and cfg["url"].startswith("https://") and "service_role" not in json.dumps(cfg))


class GateTest(unittest.TestCase):
    """本機伺服器：沒登入時所有學習 API 都回 401；通過授權才放行；管理 API 只給管理員。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        Workspace.create(root, "2026-11-01")
        cls.srv = FakeServer()
        cls.cloud = cloud.Cloud(CFG, root, http=cls.srv)
        cls.app = web.App(root, 0, cls.cloud)
        cls.httpd = web.LocalServer(("127.0.0.1", 0), web.make_handler(cls.app))
        cls.port = cls.httpd.server_address[1]
        cls.app.port = cls.port
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.tmp.cleanup()

    def req(self, path, body=None):
        r = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=None if body is None else json.dumps(body).encode(),
                                   headers={"X-CPE-Token": self.app.token, "Content-Type": "application/json"}, method="GET" if body is None else "POST")
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_flow(self):
        code, j = self.req("/api/state")
        self.assertEqual(code, 401)
        self.assertTrue(j["login_required"])
        code, j = self.req("/api/cloud/status")
        self.assertEqual(code, 200)
        self.assertTrue(j["enabled"] and not j["logged_in"])
        for p in ("/api/dashboard", "/api/backup", "/api/problem?id=d001"):
            self.assertEqual(self.req(p)[0], 401, p)
        self.assertEqual(self.req("/api/new", {"id": "d001"})[0], 401)
        code, j = self.req("/api/cloud/login", {"sid": "s1", "password": "bad"})
        self.assertEqual(code, 400)
        code, j = self.req("/api/cloud/login", {"sid": "s1", "password": "pw123456"})
        self.assertEqual(code, 200)
        self.assertTrue(j["allowed"])
        self.assertEqual(self.req("/api/state")[0], 200)
        # 學生不能用管理 API
        code, j = self.req("/api/admin/rpc", {"name": "admin_list_users"})
        self.assertEqual(code, 400)
        self.assertIn("管理員", j["error"])
        # 授權被收回 → 下一次檢查就被擋
        self.srv.access = dict(self.srv.access, ok=False, reason="expired")
        self.cloud.access(force=True)
        code, j = self.req("/api/state")
        self.assertEqual(code, 401)
        self.assertEqual(j["cloud"]["reason"], "expired")
        self.srv.access = dict(self.srv.access, ok=True, reason="ok")
        self.cloud.access(force=True)
        self.assertEqual(self.req("/api/state")[0], 200)
        # 管理員
        self.srv.access = dict(self.srv.access, role="admin")
        self.cloud.access(force=True)
        self.assertEqual(self.req("/api/admin/rpc", {"name": "drop_everything"})[0], 400)    # 不在白名單
        code, j = self.req("/api/admin/fn", {"action": "evil"})
        self.assertEqual(code, 400)
        # 登出
        self.assertEqual(self.req("/api/cloud/logout", {})[0], 200)
        self.assertEqual(self.req("/api/state")[0], 401)


if __name__ == "__main__":
    unittest.main()


class BackupExcludesCredentialsTest(unittest.TestCase):
    def test_cloud_session_never_in_backup(self):
        from cpe_coach import backup
        with tempfile.TemporaryDirectory() as d:
            ws = Workspace.create(Path(d) / "w", "2026-11-01")
            (ws.meta / "cloud.json").write_text('{"refresh": "SECRET"}', encoding="utf-8")
            names = [f.name for f in backup._files(ws)]
            self.assertNotIn("cloud.json", names)
