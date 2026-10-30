"""題庫：內建題庫 + 工作區自訂題目（自訂的同 id 會覆蓋內建）。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from .store import Workspace

DATA = Path(__file__).parent / "data"


def load_bank(ws: Optional[Workspace] = None) -> Dict[str, dict]:
    bank = {p["id"]: p for p in json.loads((DATA / "problems.json").read_text(encoding="utf-8"))}
    if ws is not None and ws.custom_bank_path.exists():
        for p in json.loads(ws.custom_bank_path.read_text(encoding="utf-8")):
            bank[p["id"]] = p
    return bank


def add_custom(ws: Workspace, problem: dict) -> None:
    items = []
    if ws.custom_bank_path.exists():
        items = json.loads(ws.custom_bank_path.read_text(encoding="utf-8"))
    items = [p for p in items if p["id"] != problem["id"]] + [problem]
    ws.custom_bank_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve(bank: Dict[str, dict], pid: str) -> dict:
    """題目不在題庫也能練（例如自己練的題），只是沒有內建提示。"""
    if pid in bank:
        return bank[pid]
    return {"id": pid, "title": pid, "stage": 1, "difficulty": 1, "topic": "自訂",
            "hint_category": None, "hint_insight": None, "url": None}
