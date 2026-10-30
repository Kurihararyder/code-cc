"""本機網頁介面：cpe web。只綁 127.0.0.1，POST 需要 token，並檢查 Host／Origin（防 CSRF 與 DNS rebinding）。

沒有第三方套件。API 金鑰只存在這個程序的記憶體，不寫入工作區。
"""
from __future__ import annotations

import json
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from . import ask as ask_mod
from . import bank as bank_mod
from . import course as course_mod
from . import mock, service, srs
from .llm import detect_client
from .store import Workspace, WorkspaceError

INDEX = Path(__file__).parent / "static" / "index.html"
MAX_BODY = 512 * 1024


class App:
    def __init__(self, root: Path, port: int):
        self.root, self.port = Path(root), port
        self.token = secrets.token_urlsafe(24)
        self.key: Optional[str] = None
        self.lock = threading.Lock()

    def ws(self) -> Workspace:
        return Workspace(self.root)

    def llm(self, ws: Workspace):
        cfg = ws.config()
        return detect_client(cfg, key=self.key)

    # ---------- 各 API ----------
    def state(self) -> Dict[str, Any]:
        ws = self.ws()
        bank = bank_mod.load_bank(ws)
        course = course_mod.load()
        st = ws.state()
        u = course_mod.current_unit(ws, course)
        probs = []
        unit_info = None
        if u:
            done, _ = course_mod.unit_progress(ws, u)
            ids = list(u["drills"])
            if u["gate"] and u["gate"]["type"] == "set":
                ids += [p for p in u["gate"]["problems"] if p not in ids]
            for pid in ids + [a for a in u["anchors"] if a not in ids]:
                p = bank_mod.resolve(bank, pid)
                sp = st["problems"].get(pid)
                role = "必做" if pid in u["drills"] else ("檢核" if pid in ids else "真題")
                probs.append({"id": pid, "title": p["title"], "role": role, "solved": bool(sp and sp["first_pass"] is not None),
                              "last": sp["last_verdict"] if sp else None, "done_in_lang": pid in done})
            a, b = course_mod.week_range(u)
            unit_info = {"n": u["n"], "total": len(course["units"]), "title": u["title"], "goal": u["goal"], "stage": u["stage"],
                         "weeks": [a, b], "learn": u["learn"], "pitfalls": u["pitfalls"], "check": u["check"],
                         "gate": u["gate"], "lang": u["lang"], "read": u.get("read", [])}
        due = [{"id": pid, "title": bank_mod.resolve(bank, pid)["title"]} for pid, _ in srs.due_list(st, ws.now())]
        exam = ws.exam()
        llm = self.llm(ws)
        return {"unit": unit_info, "problems": probs, "due": due,
                "exam": ({"kind": exam["kind"], "problems": exam["problems"],
                          "left": int(mock.remaining_seconds(exam, ws.now()))} if exam else None),
                "ai": {"available": llm is not None, "model": llm.model if llm else ws.config().get("model") or "gpt-4o"}}

    def problem(self, pid: str) -> Dict[str, Any]:
        ws = self.ws()
        return service.problem_view(ws, bank_mod.load_bank(ws), pid)

    def new(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        bank = bank_mod.load_bank(ws)
        pid = body["id"]
        if (service.solution_file(ws, pid, body.get("lang")).exists()) and not body.get("fresh"):
            return {"created": False, **service.problem_view(ws, bank, pid)}
        service.create_solution(ws, bank, pid, body.get("lang") or "py", bool(body.get("fresh")))
        return {"created": True, **service.problem_view(ws, bank, pid)}

    def save(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        f = service.solution_file(ws, body["id"], body.get("lang"))
        if not f.parent.exists():
            raise ValueError("還沒有解答檔")
        f.write_text(body["code"], encoding="utf-8")
        return {"saved": True, "file": str(f.relative_to(ws.root))}

    def test(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        if "code" in body:
            self.save(body)
        r = service.run_test(ws, body["id"], body.get("lang"), body.get("predicted"))
        if r["failing"]:
            code = service.solution_file(ws, body["id"], body.get("lang")).read_text(encoding="utf-8")
            r["lint"] = service.lint(code) if r["lang"] == "py" else []
        else:
            r["lint"] = []
        return r

    def trace(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        if "code" in body:
            self.save(body)
        return service.trace_program(ws, body["id"])

    def ask(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        bank = bank_mod.load_bank(ws)
        pid = body["id"]
        stmt = service.problem_view(ws, bank, pid)["statement"]
        if "code" in body:
            self.save(body)
        return ask_mod.ask(ws, bank, pid, self.llm(ws), kind=body.get("kind", "question"), source=body.get("source", "code"),
                           selection=body.get("selection", ""), line_start=body.get("line_start"), line_end=body.get("line_end"),
                           note=body.get("note", ""), trace_text=body.get("trace_text", ""), thread=body.get("thread"),
                           reply=body.get("reply", ""), statement=stmt)

    def chat(self, pid: str) -> Dict[str, Any]:
        return ask_mod.load_chat(self.ws(), pid)

    def set_key(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        if "key" in body:
            self.key = (body["key"] or "").strip() or None
        if body.get("model"):
            cfg = ws.config()
            cfg["model"] = body["model"].strip()
            ws.save_config(cfg)
        llm = self.llm(ws)
        return {"available": llm is not None, "model": llm.model if llm else None}


def make_handler(app: App):
    class H(BaseHTTPRequestHandler):
        server_version = "cpe"

        def log_message(self, *a):          # 安靜
            pass

        # ---- 安全檢查 ----
        def _host_ok(self) -> bool:
            allowed = {f"127.0.0.1:{app.port}", f"localhost:{app.port}"}
            if self.headers.get("Host", "") not in allowed:
                return False
            origin = self.headers.get("Origin")
            return origin is None or origin in {f"http://127.0.0.1:{app.port}", f"http://localhost:{app.port}"}

        def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8") -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj: Any) -> None:
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

        def _fail(self, code: int, msg: str) -> None:
            self._json(code, {"error": msg})

        # ---- GET ----
        def do_GET(self):
            if not self._host_ok():
                return self._fail(403, "bad host")
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                if u.path == "/":
                    html = INDEX.read_text(encoding="utf-8").replace("__TOKEN__", app.token)
                    return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
                if not self.headers.get("X-CPE-Token") == app.token:
                    return self._fail(403, "bad token")
                if u.path == "/api/state":
                    return self._json(200, app.state())
                if u.path == "/api/problem":
                    return self._json(200, app.problem(q["id"]))
                if u.path == "/api/chat":
                    return self._json(200, app.chat(q["id"]))
                return self._fail(404, "not found")
            except (KeyError, ValueError, WorkspaceError) as e:
                return self._fail(400, str(e))

        # ---- POST ----
        def do_POST(self):
            if not self._host_ok():
                return self._fail(403, "bad host")
            if self.headers.get("X-CPE-Token") != app.token:
                return self._fail(403, "bad token")
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                return self._fail(415, "json only")
            n = int(self.headers.get("Content-Length", "0"))
            if n > MAX_BODY:
                return self._fail(413, "too large")
            try:
                body = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            except json.JSONDecodeError:
                return self._fail(400, "bad json")
            route = {"/api/new": app.new, "/api/save": app.save, "/api/test": app.test, "/api/trace": app.trace,
                     "/api/ask": app.ask, "/api/key": app.set_key}.get(urlparse(self.path).path)
            if route is None:
                return self._fail(404, "not found")
            try:
                with app.lock:
                    return self._json(200, route(body))
            except ask_mod.AskDenied as e:
                return self._fail(409, str(e))
            except (KeyError, ValueError, WorkspaceError) as e:
                return self._fail(400, str(e))
            except Exception as e:          # 不讓伺服器因單一請求崩潰
                return self._fail(500, f"{type(e).__name__}: {e}")

    return H


def serve(root: Path, port: int = 8765, open_browser: bool = True, announce=print) -> None:
    app = App(root, port)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(app))
    url = f"http://127.0.0.1:{port}/"
    announce(f"CPE 教練網頁介面：{url}　（Ctrl+C 結束）")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
