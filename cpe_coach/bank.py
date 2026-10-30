"""題庫：內建經典題 + 內建原創練習題（drills）+ 工作區自訂題目（自訂的同 id 會覆蓋內建）。"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, Optional

from . import pastexams
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
    pastexams.merge_into_bank(bank, ws)
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


# ---------- 題目語言：階段 0 中文 → 階段 1 中英對照 → 之後純英文（考場是英文） ----------
LANG_MODES = ("auto", "zh", "bi", "en")
LANG_ZH = {"zh": "中文", "bi": "中英對照", "en": "English"}
_stage_cache: Dict[str, int] = {}


def has_english(pid: str) -> bool:
    return (DRILLS / pid / "statement.en.md").exists()


def _course_stage(pid: str) -> int:
    if not _stage_cache:
        for p in _load(DRILLS / "index.json"):
            _stage_cache[p["id"]] = int(p.get("course_stage", 1))
    return _stage_cache.get(pid, 1)


def auto_mode(pid: str) -> str:
    st = _course_stage(pid)
    return "zh" if st <= 0 else "bi" if st == 1 else "en"


def resolve_lang(ws: Workspace, pid: str) -> str:
    """這一題現在該用哪種語言顯示：真實考場一律英文；否則依設定，auto 時依階段逐步過渡。"""
    if not has_english(pid):
        return "zh"
    ex = ws.exam()
    if ex and ex.get("real"):
        return "en"
    mode = ws.config().get("statement_lang", "auto")
    return auto_mode(pid) if mode not in ("zh", "bi", "en") else mode


def drill_statement(pid: str, mode: str) -> str:
    zh = (DRILLS / pid / "statement.md").read_text(encoding="utf-8")
    if mode == "zh" or not has_english(pid):
        return zh
    en = (DRILLS / pid / "statement.en.md").read_text(encoding="utf-8")
    return en if mode == "en" else en.rstrip() + "\n\n---\n\n### 中文對照\n\n" + zh


def install_drill(ws: Workspace, pid: str) -> bool:
    """把內建練習題的題目敘述與測資複製到工作區。已存在的測資不會被覆蓋。回傳是否新安裝。"""
    src = DRILLS / pid
    if not (src / "statement.md").exists():
        return False
    (ws.root / "statements").mkdir(exist_ok=True)
    dst_stmt = ws.root / "statements" / f"{pid}.md"
    dst_tests = ws.tests / pid
    fresh = not dst_tests.exists() or not any(dst_tests.glob("*.in"))
    dst_stmt.write_text(drill_statement(pid, resolve_lang(ws, pid)), encoding="utf-8")
    if fresh:
        dst_tests.mkdir(parents=True, exist_ok=True)
        for f in (src / "tests").iterdir():
            shutil.copyfile(f, dst_tests / f.name)
    return fresh
