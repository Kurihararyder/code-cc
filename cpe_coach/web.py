"""本機網頁介面：cpe web。只綁 127.0.0.1，POST 需要 token，並檢查 Host／Origin（防 CSRF 與 DNS rebinding）。
前端是同源的靜態檔（無 inline script／style），搭配嚴格的 CSP。沒有第三方套件。
API 金鑰只存在這個程序的記憶體，不寫入工作區。
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import secrets
import signal
import socketserver
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from . import ask as ask_mod
from . import bank as bank_mod
from . import course as course_mod
from . import __version__, backup, dashboard, hints, judge, service, srs, updater
from .llm import detect_client
from .web_exam import ExamMixin
from .web_learn import LearnMixin
from .web_practice import PracticeMixin
from .store import Workspace, WorkspaceError

STATIC = Path(__file__).parent / "static"
MAX_BODY = 512 * 1024
CTYPES = {".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml",
          ".png": "image/png", ".ico": "image/x-icon", ".json": "application/json", ".webmanifest": "application/manifest+json"}
STATIC_RE = re.compile(r"^/static/[A-Za-z0-9_\-./]+$")
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; "
       "connect-src 'self'; manifest-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


class App(PracticeMixin, ExamMixin, LearnMixin):
    def __init__(self, root: Path, port: int):
        self.root, self.port = Path(root), port
        self.token = secrets.token_urlsafe(24)
        self.key: Optional[str] = None
        self.lock = threading.Lock()

    def ws(self) -> Workspace:
        return Workspace(self.root)

    def llm(self, ws: Workspace):
        return detect_client(ws.config(), key=self.key)

    def ai_info(self, ws: Workspace) -> Dict[str, Any]:
        llm = self.llm(ws)
        return {"available": llm is not None, "model": llm.model if llm else (ws.config().get("model") or "gpt-4o")}

    def start_date(self, ws: Workspace) -> dt.date:
        s = ws.config().get("start_date")
        return dt.date.fromisoformat(s) if s else dt.date.today()

    # ---------- 讀取 ----------
    def state(self) -> Dict[str, Any]:
        ws = self.ws()
        course = course_mod.load()
        u = course_mod.current_unit(ws, course)
        st = ws.state()
        return {"unit": ({"n": u["n"], "title": u["title"], "stage": u["stage"], "total": len(course["units"]),
                          "weeks": list(course_mod.week_range(u)), "lang": u["lang"]} if u else None),
                "exam": dashboard.exam_view(ws, ws.exam()), "ai": self.ai_info(ws),
                "due": len(srs.due_list(st, ws.now()))}

    def dashboard(self) -> Dict[str, Any]:
        ws = self.ws()
        return dashboard.dashboard(ws, bank_mod.load_bank(ws), course_mod.load(), self.ai_info(ws), self.start_date(ws))

    def course_map(self) -> Dict[str, Any]:
        ws = self.ws()
        return dashboard.course_map(ws, course_mod.load(), self.start_date(ws))

    def unit(self, n: Optional[int]) -> Dict[str, Any]:
        ws = self.ws()
        c = course_mod.load()
        return dashboard.unit_detail(ws, bank_mod.load_bank(ws), c, n or ws.state()["course"]["unit"])

    def stats(self) -> Dict[str, Any]:
        return dashboard.stats_view(self.ws())

    def problem(self, pid: str) -> Dict[str, Any]:
        ws = self.ws()
        return service.problem_view(ws, bank_mod.load_bank(ws), pid)

    def chat(self, pid: str) -> Dict[str, Any]:
        return ask_mod.load_chat(self.ws(), pid)

    def search(self, q: str) -> Dict[str, Any]:
        ws = self.ws()
        q = q.strip().lower()
        out = []
        for p in bank_mod.load_bank(ws).values():
            hay = f"{p['id']} {p['title']} {p.get('topic', '')}".lower()
            if not q or q in hay:
                out.append({"id": p["id"], "title": p["title"], "topic": p.get("topic", ""), "difficulty": p.get("difficulty", 1),
                            "drill": bool(p.get("drill"))})
        out.sort(key=lambda p: (not p["id"].lower().startswith(q), not p["drill"], p["id"]))
        return {"results": out[:30]}

    def settings(self) -> Dict[str, Any]:
        ws = self.ws()
        cfg = ws.config()
        return {"timeout_sec": cfg["timeout_sec"], "start_date": cfg["start_date"], "stage": cfg["stage"], "statement_lang": cfg.get("statement_lang", "auto"),
                "model": cfg.get("model"), "ai": self.ai_info(ws), "g++": bool(judge.find_gpp()),
                "workspace": str(ws.root), "version": __version__}


    def update_check(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """只檢查有沒有新版本（git fetch），不更新。真正的更新請在終端機執行 cpe update。"""
        r = updater.apply(updater.repo_root(), check_only=True)
        return {"status": r["status"], "version": __version__, "reason": r.get("reason"), "branch": r.get("branch"), "commit": r.get("commit"),
                "behind": r.get("behind", 0), "commits": [{"sha": a, "subject": b} for a, b in r.get("commits", [])][:15]}

    def course_goto(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        u = course_mod.goto(ws, course_mod.load(), int(body["n"]))
        return {"unit": u["n"], "title": u["title"]}

    def course_next(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        c = course_mod.load()
        u = course_mod.current_unit(ws, c)
        if not u or u["gate"]:
            raise ValueError("這個單元要通過檢核才能前進")
        nxt = course_mod.advance(ws, c, u["n"])
        return {"unit": nxt["n"] if nxt else None}

    def ai_test(self, body: Dict[str, Any]) -> Dict[str, Any]:
        import time as _t
        from .llm import LLMError
        llm = self.llm(self.ws())
        if llm is None:
            return {"ok": False, "error": "還沒有設定 API 金鑰"}
        t0 = _t.time()
        try:
            llm.complete("只回覆一個字：OK", "ping")
        except LLMError as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "model": llm.model, "ms": int((_t.time() - t0) * 1000)}

    def set_key(self, body: Dict[str, Any]) -> Dict[str, Any]:
        self.set_settings({k: body[k] for k in ("key", "model") if k in body})
        return self.ai_info(self.ws())

    def set_settings(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        cfg = ws.config()
        if "timeout_sec" in body:
            t = float(body["timeout_sec"])
            if not 0.5 <= t <= 120:
                raise ValueError("時限需介於 0.5–120 秒")
            cfg["timeout_sec"] = t
        if body.get("start_date"):
            dt.date.fromisoformat(body["start_date"])
            cfg["start_date"] = body["start_date"]
        if "model" in body:
            cfg["model"] = (body["model"] or "").strip() or None
        if "statement_lang" in body:
            if body["statement_lang"] not in bank_mod.LANG_MODES:
                raise ValueError("題目語言只能是 auto／zh／bi／en")
            cfg["statement_lang"] = body["statement_lang"]
        ws.save_config(cfg)
        if "key" in body:
            self.key = (body["key"] or "").strip() or None
        return self.settings()


def make_handler(app: App):
    GET = {"/api/state": lambda q: app.state(), "/api/dashboard": lambda q: app.dashboard(),
           "/api/course": lambda q: app.course_map(), "/api/stats": lambda q: app.stats(),
           "/api/unit": lambda q: app.unit(int(q["n"]) if "n" in q else None),
           "/api/problem": lambda q: app.problem(q["id"]), "/api/chat": lambda q: app.chat(q["id"]),
           "/api/search": lambda q: app.search(q.get("q", "")), "/api/settings": lambda q: app.settings(),
           "/api/past": lambda q: app.past_list(), "/api/cpe": lambda q: app.cpe_status(), "/api/vocab": lambda q: app.vocab_list(),
           "/api/plan": lambda q: app.plan(int(q.get("minutes", "30"))), "/api/calibration": lambda q: app.calibration(), "/api/weakness": lambda q: app.weakness(),
           "/api/eng": lambda q: app.eng_list()}
    POST = {"/api/new": app.new, "/api/save": app.save, "/api/test": app.test, "/api/trace": app.trace, "/api/fuzz": app.fuzz, "/api/ask": app.ask,
            "/api/hint": app.hint, "/api/giveup": app.giveup, "/api/solution": app.solution, "/api/gate": app.gate_start,
            "/api/mock": app.mock_start, "/api/exam/finish": app.exam_finish, "/api/course/goto": app.course_goto,
            "/api/course/next": app.course_next, "/api/settings": app.set_settings, "/api/past/import": app.past_import, "/api/cpe/import": app.cpe_import,
            "/api/past/statement": app.past_statement, "/api/past/start": app.past_start, "/api/vocab/add": app.vocab_add,
            "/api/vocab/remove": app.vocab_remove, "/api/eng/start": app.eng_start, "/api/eng/verify": app.eng_verify, "/api/key": app.set_key, "/api/ai/test": app.ai_test, "/api/update/check": app.update_check}

    class H(BaseHTTPRequestHandler):
        server_version = "cpe"

        def log_message(self, *a):
            pass

        def _host_ok(self) -> bool:
            if self.headers.get("Host", "") not in {f"127.0.0.1:{app.port}", f"localhost:{app.port}"}:
                return False
            origin = self.headers.get("Origin")
            return origin is None or origin in {f"http://127.0.0.1:{app.port}", f"http://localhost:{app.port}"}

        def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8", cache: str = "no-store") -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", cache)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", CSP)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj: Any) -> None:
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

        def _fail(self, code: int, msg: str) -> None:
            self._json(code, {"error": msg})

        def _static(self, path: str) -> None:
            if not STATIC_RE.match(path) or ".." in path:
                return self._fail(404, "not found")
            f = (STATIC / path[len("/static/"):]).resolve()
            if STATIC.resolve() not in f.parents or not f.is_file() or f.suffix not in CTYPES:
                return self._fail(404, "not found")
            self._send(200, f.read_bytes(), CTYPES[f.suffix], "no-cache")

        def do_GET(self):
            if not self._host_ok():
                return self._fail(403, "bad host")
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                if u.path == "/":
                    html = (STATIC / "index.html").read_text(encoding="utf-8").replace("__TOKEN__", app.token)
                    return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
                if u.path.startswith("/static/"):
                    return self._static(u.path)
                if u.path == "/api/ping":                # 給安裝控制台判斷『這個埠上跑的是不是 CPE 教練、是哪個程序』；不含任何學習資料
                    return self._json(200, {"app": "cpe-coach", "version": __version__, "pid": os.getpid(), "port": app.port, "workspace": str(app.root)})
                if self.headers.get("X-CPE-Token") != app.token:
                    return self._fail(403, "bad token")
                if u.path == "/api/backup":
                    with app.ws().lock():
                        data = backup.export_bytes(app.ws())
                    return self._send(200, data, "application/zip")
                fn = GET.get(u.path)
                if fn is None:
                    return self._fail(404, "not found")
                return self._json(200, fn(q))
            except (KeyError, ValueError, WorkspaceError) as e:
                return self._fail(400, str(e))
            except Exception as e:
                return self._fail(500, f"{type(e).__name__}: {e}")

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
            fn = POST.get(urlparse(self.path).path)
            if fn is None:
                return self._fail(404, "not found")
            try:
                with app.lock, app.ws().lock():
                    return self._json(200, fn(body))
            except (ask_mod.AskDenied, hints.HintDenied) as e:
                return self._fail(409, str(e))
            except (KeyError, ValueError, WorkspaceError) as e:
                return self._fail(400, str(e))
            except Exception as e:
                return self._fail(500, f"{type(e).__name__}: {e}")

    return H


class LocalServer(ThreadingHTTPServer):
    """HTTPServer.server_bind 會對位址做反向 DNS 查詢（socket.getfqdn）只為了記下主機名稱；我們只聽 127.0.0.1，用不到，
    而某些 macOS（包含 GitHub 的 macOS 虛擬機）這個查詢會卡 30 秒，網頁服務就遲遲起不來。直接略過。"""

    def server_bind(self) -> None:
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = str(host)
        self.server_port = port


def _stop_on_sigterm(signum, frame) -> None:
    raise KeyboardInterrupt


def serve(root: Path, port: int = 8765, open_browser: bool = True, announce=print) -> None:
    app = App(root, port)
    httpd = LocalServer(("127.0.0.1", port), make_handler(app))
    url = f"http://127.0.0.1:{port}/"
    announce(f"CPE 教練網頁介面：{url}　（Ctrl+C 結束）")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        signal.signal(signal.SIGTERM, _stop_on_sigterm)       # 控制台按『關閉』時能正常收尾
    except (ValueError, OSError):
        pass                                                  # 不在主執行緒（測試）時略過
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
