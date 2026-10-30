"""本機網頁介面：cpe web。只綁 127.0.0.1，POST 需要 token，並檢查 Host／Origin（防 CSRF 與 DNS rebinding）。
前端是同源的靜態檔（無 inline script／style），搭配嚴格的 CSP。沒有第三方套件。
API 金鑰只存在這個程序的記憶體，不寫入工作區。
"""
from __future__ import annotations

import datetime as dt
import json
import re
import secrets
import shutil
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from . import ask as ask_mod
from . import bank as bank_mod
from . import course as course_mod
from . import backup, calibrate, dashboard, eng, hints, mock, pastexams, service, srs, vocab
from . import plan as plan_mod
from .llm import detect_client
from .store import Workspace, WorkspaceError

STATIC = Path(__file__).parent / "static"
MAX_BODY = 512 * 1024
CTYPES = {".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml",
          ".png": "image/png", ".ico": "image/x-icon", ".json": "application/json", ".webmanifest": "application/manifest+json"}
STATIC_RE = re.compile(r"^/static/[A-Za-z0-9_\-./]+$")
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; "
       "connect-src 'self'; manifest-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


class App:
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
        return {"timeout_sec": cfg["timeout_sec"], "start_date": cfg["start_date"], "stage": cfg["stage"],
                "model": cfg.get("model"), "ai": self.ai_info(ws), "g++": bool(shutil.which("g++")),
                "workspace": str(ws.root)}

    # ---------- 寫入 ----------
    def new(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        bank = bank_mod.load_bank(ws)
        pid = body["id"]
        if service.solution_file(ws, pid, body.get("lang")).exists() and not body.get("fresh"):
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
        r["lint"] = []
        if r["failing"] and r["lang"] == "py":
            r["lint"] = service.lint(service.solution_file(ws, body["id"], body.get("lang")).read_text(encoding="utf-8"))
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

    def hint(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        bank = bank_mod.load_bank(ws)
        pid, level = body["id"], int(body["level"])
        sol = service.solution_file(ws, pid)
        code = sol.read_text(encoding="utf-8") if sol.exists() else ""
        out = hints.request_hint(ws, pid, level, bank_mod.resolve(bank, pid), code, service.load_failure(ws, pid), self.llm(ws))
        return {**out, "level": level, "name": hints.LEVEL_NAMES[level]}

    def giveup(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return {"unlock_at": hints.giveup(self.ws(), body["id"])}

    def solution(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        bank = bank_mod.load_bank(ws)
        pid = body["id"]
        sol = service.solution_file(ws, pid)
        return hints.solution_text(ws, pid, bank_mod.resolve(bank, pid), sol.read_text(encoding="utf-8") if sol.exists() else "", self.llm(ws))

    def gate_start(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        c = course_mod.load()
        u = course_mod.current_unit(ws, c)
        if not u:
            raise ValueError("課程已經全部完成")
        course_mod.start_gate(ws, bank_mod.load_bank(ws), c, u)
        return {"exam": dashboard.exam_view(ws, ws.exam())}

    def mock_start(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        kind = body.get("kind", "mock")
        if kind not in ("mock", "short", "weekly"):
            raise ValueError("kind 只能是 mock／short／weekly")
        course_mod.start_mock(ws, bank_mod.load_bank(ws), kind, body.get("lang") or "py", bool(body.get("all")), bool(body.get("real")))
        return {"exam": dashboard.exam_view(ws, ws.exam())}

    def exam_finish(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        s = mock.finish(ws, pastexams.load_all(ws)["distribution"])
        return {"summary": s, "message": course_mod.evaluate_gate(ws, course_mod.load(), s)}

    # ---- 歷屆與考試擬真 ----
    def past_list(self) -> Dict[str, Any]:
        ws = self.ws()
        return pastexams.list_exams(ws, bank_mod.load_bank(ws))

    def past_import(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        try:
            return pastexams.import_manifest(ws, body.get("text", ""))
        except pastexams.ManifestError as e:
            raise ValueError(str(e))

    def past_statement(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """貼上單一題的題目文字：存下並把範例建成測資。"""
        ws = self.ws()
        pid = body["id"]
        if not re.match(r"^[A-Za-z0-9_\-]{1,40}$", pid):
            raise ValueError("題號格式不正確")
        n = service.import_statement(ws, pid, body.get("text", ""))
        return {"id": pid, "samples": n, "english": service.statement_is_english(body.get("text", ""))}

    def past_start(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        course_mod.start_past(ws, bank_mod.load_bank(ws), body["date"], body.get("lang") or "py", bool(body.get("partial")))
        return {"exam": dashboard.exam_view(ws, ws.exam())}

    def vocab_list(self) -> Dict[str, Any]:
        return {"words": vocab.items(self.ws())}

    def vocab_add(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return vocab.add(self.ws(), body["word"], body.get("problem"), body.get("note", ""))

    def vocab_remove(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return {"removed": vocab.remove(self.ws(), body["word"])}

    # ---- 每日計畫、校準、工程任務 ----
    def plan(self, minutes: int) -> Dict[str, Any]:
        return plan_mod.build(self.ws(), max(10, min(480, minutes)))

    def calibration(self) -> Dict[str, Any]:
        ws = self.ws()
        return calibrate.calibrate(ws, bank_mod.load_bank(ws))

    def eng_list(self) -> Dict[str, Any]:
        return {"tasks": eng.tasks(self.ws())}

    def eng_start(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return {"created": eng.start(self.ws(), int(body["n"]))}

    def eng_verify(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return eng.verify(self.ws(), int(body["n"]), (body.get("evidence") or "").strip() or None)

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
           "/api/past": lambda q: app.past_list(), "/api/vocab": lambda q: app.vocab_list(),
           "/api/plan": lambda q: app.plan(int(q.get("minutes", "30"))), "/api/calibration": lambda q: app.calibration(),
           "/api/eng": lambda q: app.eng_list()}
    POST = {"/api/new": app.new, "/api/save": app.save, "/api/test": app.test, "/api/trace": app.trace, "/api/ask": app.ask,
            "/api/hint": app.hint, "/api/giveup": app.giveup, "/api/solution": app.solution, "/api/gate": app.gate_start,
            "/api/mock": app.mock_start, "/api/exam/finish": app.exam_finish, "/api/course/goto": app.course_goto,
            "/api/course/next": app.course_next, "/api/settings": app.set_settings, "/api/past/import": app.past_import,
            "/api/past/statement": app.past_statement, "/api/past/start": app.past_start, "/api/vocab/add": app.vocab_add,
            "/api/vocab/remove": app.vocab_remove, "/api/eng/start": app.eng_start, "/api/eng/verify": app.eng_verify, "/api/key": app.set_key, "/api/ai/test": app.ai_test}

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
