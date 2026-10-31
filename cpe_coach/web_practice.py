"""練習頁用的端點：建檔、存檔、判題、追蹤、對拍、AI 詢問與提示。"""
from __future__ import annotations

from typing import Any, Dict

from . import ask as ask_mod
from . import bank as bank_mod
from . import behavior
from . import fuzz as fuzz_mod, hints, service


class PracticeMixin:
    """需要 self.ws()、self.llm()、self.ai_info() 等（由 web.App 提供）。"""

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
        beh = behavior.clean(body.get("beh"))
        r["behavior"] = []
        if beh:                                                                       # 編輯行為（只有次數與時間）：記錄並回傳可能卡住的提示
            recent = [e for e in ws.events()[-30:] if e.get("kind") == "test" and e.get("problem") == body["id"]]
            failed = sum(1 for e in recent if e.get("verdict") != "AC")
            ws.log("beh", problem=body["id"], failed_runs=failed, **beh)
            r["behavior"] = behavior.patterns(beh, failed) if r["verdict"] != "AC" else []
        if r["failing"] and r["lang"] == "py":
            r["lint"] = service.lint(service.solution_file(ws, body["id"], body.get("lang")).read_text(encoding="utf-8"))
        return r

    def trace(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ws = self.ws()
        if "code" in body:
            self.save(body)
        return service.trace_program(ws, body["id"])

    def fuzz(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """範例變異對拍：用你寫的暴力解當標準答案，找出你的解答的錯，可選擇存成測資。"""
        ws = self.ws()
        pid = body["id"]
        if ws.exam():
            raise ValueError("考試中不能對拍。")
        if "code" in body:
            self.save(body)
        brute = (body.get("brute") or "").strip()
        if not brute:
            raise ValueError("請貼上你的暴力解程式碼")
        d = ws.meta / "fuzz"
        d.mkdir(exist_ok=True)
        bf = d / f"{pid}_brute.py"
        bf.write_text(brute + "\n", encoding="utf-8")
        sol = service.solution_file(ws, pid)
        if not sol.exists():
            raise ValueError("還沒有你的解答檔")
        rounds = max(20, min(2000, int(body.get("rounds") or 300)))
        cfg = ws.config()
        try:
            r = fuzz_mod.fuzz(sol, bf, ws.tests / pid, rounds, int(body.get("seed") or 1), 3, float(cfg["timeout_sec"]), int(cfg.get("memory_mb", 1024)))
        except fuzz_mod.FuzzError as e:
            raise ValueError(str(e))
        saved = fuzz_mod.save(ws, pid, r["found"]) if r["found"] and body.get("save") else []
        return dict(r, saved=saved, tests=len(service.find_cases(ws.tests / pid)))

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
