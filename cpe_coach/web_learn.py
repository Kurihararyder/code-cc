"""每日計畫、難度校準、弱點診斷與工程任務的端點。"""
from __future__ import annotations

from typing import Any, Dict

from . import bank as bank_mod
from . import course as course_mod
from . import calibrate, eng, weakness
from . import plan as plan_mod


class LearnMixin:
    """需要 self.ws()、self.llm()、self.ai_info() 等（由 web.App 提供）。"""

    # ---- 每日計畫、校準、工程任務 ----
    def plan(self, minutes: int) -> Dict[str, Any]:
        return plan_mod.build(self.ws(), max(10, min(480, minutes)))

    def calibration(self) -> Dict[str, Any]:
        ws = self.ws()
        return calibrate.calibrate(ws, bank_mod.load_bank(ws))

    def weakness(self) -> Dict[str, Any]:
        ws = self.ws()
        bank, c = bank_mod.load_bank(ws), course_mod.load()
        a = weakness.analyze(ws, bank, c)
        return dict(a, suggestions=weakness.suggestions(ws, bank, c, a, per_family=3))

    def eng_list(self) -> Dict[str, Any]:
        return {"tasks": eng.tasks(self.ws())}

    def eng_start(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return {"created": eng.start(self.ws(), int(body["n"]))}

    def eng_verify(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return eng.verify(self.ws(), int(body["n"]), (body.get("evidence") or "").strip() or None)
