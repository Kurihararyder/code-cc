"""本機伺服器的攻擊探測（對假 Supabase，不連網）。用法：python dev/security_probe.py
啟動假雲端（8794）與真的 cpe web（8795），逐項嘗試：沒登入、錯 token、錯 Host／Origin、路徑變形、目錄穿越、學生越權。
任何一項『拿到資料』都算失敗，結束碼非 0。"""
import http.client
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT_FAKE, PORT_WEB = 8794, 8795


def call(method, path, body=None, headers=None, host=None):
    c = http.client.HTTPConnection("127.0.0.1", PORT_WEB, timeout=15)
    h = {"Host": host or f"127.0.0.1:{PORT_WEB}"}
    h.update(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h.setdefault("Content-Type", "application/json")
    c.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
    for k, v in h.items():
        c.putheader(k, v)
    if data is not None:
        c.putheader("Content-Length", str(len(data)))
    c.endheaders(data)
    r = c.getresponse()
    out = (r.status, r.read())
    c.close()
    return out


def main():
    tmp = tempfile.mkdtemp()
    env = dict(os.environ, PYTHONPATH=str(ROOT), CPE_CLOUD_URL=f"http://127.0.0.1:{PORT_FAKE}", CPE_CLOUD_KEY="fake")
    fake = subprocess.Popen([sys.executable, str(ROOT / "dev/ui_e2e/fake_supabase.py"), str(PORT_FAKE)], env=env)
    subprocess.run([sys.executable, "-m", "cpe_coach", "init"], cwd=tmp, env=env, capture_output=True)
    web = subprocess.Popen([sys.executable, "-m", "cpe_coach", "web", "--no-open", "--port", str(PORT_WEB)], cwd=os.path.join(tmp, "cpe-workspace"), env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fails = []

    def check(name, ok, detail=""):
        print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if not ok else ""))
        if not ok:
            fails.append(name)

    try:
        for _ in range(40):
            try:
                call("GET", "/api/ping")
                break
            except OSError:
                time.sleep(0.25)
        st, html = call("GET", "/")
        token = html.decode().split('cpe-token" content="')[1].split('"')[0]
        T = {"X-CPE-Token": token}
        denied = (401, 403, 404, 405, 400)

        # 1. 沒登入：所有學習資料 API 都要 401
        paths = ["/api/state", "/api/dashboard", "/api/course", "/api/stats", "/api/settings", "/api/backup", "/api/export/anki", "/api/notes",
                 "/api/problem?id=d001", "/api/statement.pdf?id=d001", "/api/vocab", "/api/plan", "/api/weakness", "/api/insights", "/api/lab/index"]
        for p in paths:
            s, b = call("GET", p, headers=T)
            check(f"未登入 GET {p} 被擋", s == 401, f"{s} {b[:60]}")
        for p in ["/api/new", "/api/save", "/api/test", "/api/ask", "/api/hint", "/api/solution", "/api/mock", "/api/settings", "/api/key", "/api/past/import", "/api/cpe/import"]:
            s, b = call("POST", p, {"id": "d001"}, T)
            check(f"未登入 POST {p} 被擋", s == 401, f"{s} {b[:60]}")
        for p in ["/api/admin/rpc", "/api/admin/fn", "/api/admin/ai_test", "/api/cloud/sync", "/api/cloud/report"]:
            s, b = call("POST", p, {"name": "admin_list_users", "action": "create_users"}, T)
            check(f"未登入 POST {p} 被擋", s == 401, f"{s} {b[:60]}")

        # 2. 路徑變形不能繞過閘門
        for p in ["//api/state", "/api/state/", "/API/state", "/api/state%2f", "/api/./state", "/api//state", "/api/state;x", "/api/state%00", "/%61pi/state", "/api/state#x", "/api/state?x=1"]:
            s, b = call("GET", p, headers=T)
            check(f"路徑變形 {p} 沒洩漏", s in denied and b"unit" not in b and b"course" not in b[:80], f"{s} {b[:60]}")

        # 3. token 與 Host／Origin
        s, b = call("GET", "/api/state")
        check("沒帶 token 被擋", s == 403, s)
        s, b = call("GET", "/api/state", headers={"X-CPE-Token": "wrong"})
        check("錯誤 token 被擋", s == 403, s)
        s, b = call("GET", "/api/state", headers=T, host="evil.example.com")
        check("錯誤 Host（DNS rebinding）被擋", s == 403, s)
        s, b = call("GET", "/", host="evil.example.com")
        check("錯誤 Host 拿不到首頁（token 不外流）", s == 403 and b"cpe-token" not in b, s)
        s, b = call("POST", "/api/cloud/logout", {}, dict(T, Origin="http://evil.example.com"))
        check("錯誤 Origin（CSRF）被擋", s == 403, s)
        s, b = call("POST", "/api/cloud/logout", "x", dict(T, **{"Content-Type": "text/plain"}))
        check("非 JSON 的 POST 被擋", s in (415, 400, 403), s)
        s, b = call("POST", "/api/cloud/login", None, dict(T, **{"Content-Length": "99999999", "Content-Type": "application/json"}))
        check("超大 Content-Length 被擋", s in (413, 400, 403), s)

        # 4. 靜態檔與目錄穿越
        for p in ["/static/../store.py", "/static/%2e%2e/store.py", "/static/js/../../web.py", "/static/..%2fweb.py", "/static/js/%2e%2e/%2e%2e/cloud.py", "/static/\\..\\web.py",
                  "/static/index.html.bak", "/static/img/../../data/cloud.json"]:
            s, b = call("GET", p, headers=T)
            check(f"目錄穿越 {p} 拿不到原始碼", s in denied and b"import" not in b[:300] and b"sb_publishable" not in b, f"{s} {b[:50]}")
        s, b = call("GET", "/static/js/main.js")
        check("正常靜態檔可讀", s == 200)
        s, b = call("GET", "/static/js/gate.js")
        check("靜態檔不含任何金鑰（只有網頁程式碼）", b"service_role" not in b and b"sb_secret" not in b)

        # 5. 登入學生後：管理 API 要擋、危險操作要擋
        s, b = call("POST", "/api/cloud/login", {"sid": "s001", "password": "init1234"}, T)
        check("學生登入成功", s == 200 and json.loads(b).get("allowed"), f"{s} {b[:80]}")
        s, b = call("GET", "/api/state", headers=T)
        check("登入後可讀資料", s == 200, s)
        for name in ["admin_list_users", "admin_export", "admin_set_secret", "not_in_whitelist", "access_for"]:
            s, b = call("POST", "/api/admin/rpc", {"name": name, "args": {}}, T)
            check(f"學生呼叫管理 RPC {name} 被擋", s == 400 and "result" not in json.loads(b), f"{s} {b[:60]}")
        for act in ["create_users", "reset_password", "delete_user", "evil"]:
            s, b = call("POST", "/api/admin/fn", {"action": act, "users": [{"student_id": "x1"}]}, T)
            check(f"學生呼叫管理函式 {act} 被擋", s == 400, f"{s} {b[:60]}")
        s, b = call("GET", "/api/cloud/status", headers=T)
        j = json.loads(b)
        check("狀態回應不含憑證", "access" in j and b"tok-s001" not in b and b"refresh" not in b.lower(), b[:80])
        s, b = call("GET", "/api/backup", headers=T)
        check("備份下載不含登入憑證", b"cloud.json" not in b and b"tok-s001" not in b)
        sess = Path(tmp, "cpe-workspace", ".cpe", "cloud.json")
        mode = sess.stat().st_mode & 0o777 if sess.exists() else None
        check("登入憑證檔權限 600（非 Windows）", os.name == "nt" or mode == 0o600, oct(mode) if mode else "no file")
        # 6. 登出後又被擋
        call("POST", "/api/cloud/logout", {}, T)
        s, b = call("GET", "/api/state", headers=T)
        check("登出後再次被擋", s == 401, s)
    finally:
        web.terminate()
        fake.terminate()
    print(f"\n{'全部通過' if not fails else '失敗 %d 項：' % len(fails) + '、'.join(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
