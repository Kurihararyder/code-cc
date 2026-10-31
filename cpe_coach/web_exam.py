"""考試、檢核、歷屆題與單字本的端點。"""
from __future__ import annotations

import re
from typing import Any, Dict

from . import bank as bank_mod
from . import course as course_mod
from . import cpeimport, cpeset, dashboard, mock, pastexams, service, vocab


class ExamMixin:
    """需要 self.ws()、self.llm()、self.ai_info() 等（由 web.App 提供）。"""

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

    def cpe_status(self) -> Dict[str, Any]:
        ws = self.ws()
        return cpeset.status(ws, bank_mod.load_bank(ws))

    def cpe_import(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """從 GitHub 下載 CPE 原題 repo 的 PDF，轉成題目文字與範例測資（只接受『從 GitHub 下載』；本機資料夾請用 cpe past repo）。"""
        ws = self.ws()
        r = cpeimport.import_from(ws, None, force=bool(body.get("force")))
        return {"imported": len(r.imported), "samples": sum(n for _, _, n in r.imported), "skipped": len(r.skipped), "failed": [{"id": a, "why": b} for a, b in r.failed],
                "no_samples": r.no_samples, "missing": r.missing}

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
