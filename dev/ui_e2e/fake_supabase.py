"""最小的假 Supabase（HTTP）：給管理後台的瀏覽器測試用，不連網。用法：python fake_supabase.py PORT
帳號：admin / admin1234（管理員）、s001 / init1234（學生）。狀態都在記憶體。"""
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

USERS = {}
LOG = []
REPORTS = []
SETTINGS = {"ip_policy": {"enabled": False, "cidrs": []}, "ai": {"enabled": False, "model": "gpt-4o", "daily_calls": 60, "max_tokens": 1500},
            "app": {"latest_version": "2.9.0", "min_version": "2.9.0", "announcement": "", "update_note": ""}, "offline": {"grace_hours": 72}, "notices": {"items": []}}


def add(sid, name, role="student", pw="init1234", active=True, cohort="114"):
    USERS[sid] = {"id": "id-" + sid, "student_id": sid, "name": name, "role": role, "cohort": cohort, "active": active, "archived": False, "valid_from": None, "valid_until": None,
                  "ai_allowed": False, "ip_mode": "inherit", "allowed_ips": [], "must_change_pw": False, "note": "", "last_login_at": None, "last_ip": None,
                  "login_count": 0, "created_at": "2026-11-01T00:00:00Z", "pw": pw, "summary": {"solved": 3, "unit": 2, "last_active": time.time() - 86400, "stuck": [{"id": "d019", "attempts": 6}]}}


add("admin", "管理員", "admin", "admin1234")
add("s001", "王小明")


def status(u):
    return "ok" if u["active"] else "inactive"


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def out(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def me(self):
        tok = (self.headers.get("Authorization") or "").replace("Bearer ", "")
        return next((u for u in USERS.values() if tok == "tok-" + u["student_id"]), None)

    def do_PUT(self):
        self.out(200, {})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        d = json.loads(self.rfile.read(n) or b"{}")
        p = self.path
        if p.startswith("/auth/v1/token"):
            if "refresh" in p:
                return self.out(400, {})
            sid = d["email"].split("@")[0]
            u = USERS.get(sid)
            if not u or u["pw"] != d["password"]:
                return self.out(400, {"error": "invalid_grant"})
            return self.out(200, {"access_token": "tok-" + sid, "refresh_token": "r", "expires_in": 3600})
        if p == "/rest/v1/rpc/app_info":
            return self.out(200, dict(SETTINGS["app"], grace_hours=72, ai_enabled=False))
        u = self.me()
        if not u:
            return self.out(401, {})
        name = p.rsplit("/", 1)[-1]
        if p.startswith("/functions/v1/admin"):
            res = []
            for r in d.get("users", []):
                if r["student_id"] in USERS:
                    res.append({"student_id": r["student_id"], "ok": False, "error": "學號已存在"})
                    continue
                add(r["student_id"], r.get("name", ""), cohort=d.get("cohort", ""), active=d.get("active") is True, pw="pw-" + r["student_id"])
                res.append({"student_id": r["student_id"], "name": r.get("name", ""), "ok": True, "password": "pw-" + r["student_id"], "id": "id-" + r["student_id"]})
            return self.out(200, {"results": res})
        if name == "check_access":
            LOG.append({"at": "2026-11-02T00:00:00Z", "student_id": u["student_id"], "action": "login", "ip": "1.2.3.4", "ok": True, "detail": None})
            return self.out(200, {"ok": u["active"], "reason": "ok" if u["active"] else "inactive", "role": u["role"], "student_id": u["student_id"], "name": u["name"], "cohort": u["cohort"],
                                  "ai_allowed": False, "must_change_pw": u["must_change_pw"], "valid_until": None, "ip": "1.2.3.4", "app": dict(SETTINGS["app"], grace_hours=72)})
        if name == "report_problem":
            REPORTS.append({"id": len(REPORTS) + 1, "at": "2026-11-02T00:00:00Z", "student_id": u["student_id"], "problem_id": d["p_pid"], "body": d["p_body"], "resolved": False})
            return self.out(200, {"ok": True, "reason": "ok"})
        if name in ("my_notices", "load_progress", "save_progress", "pw_changed"):
            return self.out(200, [] if name == "my_notices" else {"ok": True, "data": None})
        if u["role"] != "admin":
            return self.out(403, {"message": "admin only"})
        students = [x for x in USERS.values()]
        if name == "admin_list_users":
            return self.out(200, [dict({k: v for k, v in x.items() if k != "pw"}, status=status(x), progress_at=None, ai_calls_24h=0) for x in students])
        if name == "admin_overview":
            return self.out(200, {"students": len(students) - 1, "active": sum(1 for x in students if x["active"]) - 1, "pending": sum(1 for x in students if not x["active"]), "expired": 0, "ai_allowed": 0,
                                  "logins_24h": len(LOG), "denied_24h": 0, "ai_calls_24h": 0, "ai_tokens_7d": 0, "expiring_7d": 0, "cohorts": [{"cohort": "114", "n": 1}]})
        if name in ("admin_update_user", "admin_bulk_update", "admin_set_archived"):
            ids = d.get("p_ids") or [d.get("p_id")]
            patch = d.get("p") if isinstance(d.get("p"), dict) else {"archived": d.get("p")}
            for x in students:
                if x["id"] in ids:
                    x.update(patch)
            return self.out(200, len(ids) if name != "admin_update_user" else None)
        if name == "admin_get_settings":
            return self.out(200, SETTINGS)
        if name in ("admin_set_setting", "admin_set_notices"):
            if name == "admin_set_notices":
                SETTINGS["notices"] = d["p"]
            else:
                SETTINGS[d["p_key"]] = d["p_value"]
            return self.out(200, None)
        if name == "admin_secret_status":
            return self.out(200, {"set": False})
        if name == "admin_audit":
            return self.out(200, LOG[-50:])
        if name == "admin_anomalies":
            return self.out(200, {"multi_ip": [{"student_id": "s001", "ips": 3, "list": ["1.1.1.1", "2.2.2.2", "3.3.3.3"]}], "denied": [], "open_reports": sum(1 for r in REPORTS if not r["resolved"])})
        if name == "admin_reports":
            return self.out(200, [r for r in REPORTS if r["resolved"] == d["p_resolved"]])
        if name == "admin_resolve_report":
            for r in REPORTS:
                if r["id"] == d["p_id"]:
                    r["resolved"] = d["p"]
            return self.out(200, None)
        if name == "admin_auto_archive":
            return self.out(200, 0)
        if name in ("admin_ai_usage", "admin_expiring"):
            return self.out(200, [])
        if name == "admin_insights":
            return self.out(200, {"stuck": [{"id": "d019", "students": 1, "attempts": 6}], "inactive": [], "units": [{"unit": 2, "n": 1}], "weekly": [{"week_ago": w, "active": 1} for w in (3, 2, 1, 0)], "solved_avg": 3})
        if name == "admin_export":
            return self.out(200, {"profiles": [], "settings": SETTINGS})
        return self.out(404, {"message": "no " + name})


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
