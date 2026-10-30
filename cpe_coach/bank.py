"""題庫：內建經典題 + 內建原創練習題（drills）+ 工作區自訂題目（自訂的同 id 會覆蓋內建）。"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, Optional

from .store import Workspace

DATA = Path(__file__).parent / "data"
DRILLS = DATA / "drills"


def _load(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def load_bank(ws: Optional[Workspace] = None) -> Dict[str, dict]:
    bank: Dict[str, dict] = {}
    for f in (DATA / "problems.json", DATA / "problems_extra.json", DRILLS / "index.json"):
        for p in _load(f):
            bank[p["id"]] = p
    if ws is not None:
        for p in _load(ws.custom_bank_path):
            bank[p["id"]] = p
    return bank


def add_custom(ws: Workspace, problem: dict) -> None:
    items = [p for p in _load(ws.custom_bank_path) if p["id"] != problem["id"]] + [problem]
    ws.custom_bank_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve(bank: Dict[str, dict], pid: str) -> dict:
    """題目不在題庫也能練（例如自己練的題），只是沒有內建提示。"""
    if pid in bank:
        return bank[pid]
    return {"id": pid, "title": pid, "stage": 1, "difficulty": 1, "topic": "自訂",
            "hint_category": None, "hint_insight": None, "url": None}


def is_drill(pid: str) -> bool:
    return (DRILLS / pid / "statement.md").exists()


def install_drill(ws: Workspace, pid: str) -> bool:
    """把內建練習題的題目敘述與測資複製到工作區。已存在的測資不會被覆蓋。回傳是否新安裝。"""
    src = DRILLS / pid
    if not (src / "statement.md").exists():
        return False
    (ws.root / "statements").mkdir(exist_ok=True)
    dst_stmt = ws.root / "statements" / f"{pid}.md"
    dst_tests = ws.tests / pid
    fresh = not dst_tests.exists() or not any(dst_tests.glob("*.in"))
    shutil.copyfile(src / "statement.md", dst_stmt)
    if fresh:
        dst_tests.mkdir(parents=True, exist_ok=True)
        for f in (src / "tests").iterdir():
            shutil.copyfile(f, dst_tests / f.name)
    return fresh
