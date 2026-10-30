"""生字本：讀英文題目時查過的單字。考場題目是英文，累積生字是真的有用的準備。"""
from __future__ import annotations

import csv
import io
import re
from typing import Any, Dict, List, Optional

from .store import Workspace

WORD = re.compile(r"^[A-Za-z][A-Za-z'’-]{1,29}$")
DICT_URL = "https://dictionary.cambridge.org/dictionary/english-chinese-traditional/{}"


def _path(ws: Workspace):
    return ws.meta / "vocab.json"


def load(ws: Workspace) -> Dict[str, Any]:
    return ws._read(_path(ws), {"words": {}})


def add(ws: Workspace, word: str, problem: Optional[str] = None, note: str = "") -> Dict[str, Any]:
    w = word.strip().strip(".,;:!?()\"").lower().replace("’", "'")
    if not WORD.match(w):
        raise ValueError("只能收錄單一英文單字")
    d = load(ws)
    e = d["words"].setdefault(w, {"count": 0, "problems": [], "first": ws.now(), "last": ws.now(), "note": ""})
    e["count"] += 1
    e["last"] = ws.now()
    if problem and problem not in e["problems"]:
        e["problems"].append(problem)
    if note:
        e["note"] = note[:200]
    ws._write(_path(ws), d)
    return {"word": w, **e, "url": DICT_URL.format(w)}


def remove(ws: Workspace, word: str) -> bool:
    d = load(ws)
    ok = d["words"].pop(word.lower(), None) is not None
    ws._write(_path(ws), d)
    return ok


def items(ws: Workspace) -> List[Dict[str, Any]]:
    d = load(ws)["words"]
    return sorted(({"word": w, **e, "url": DICT_URL.format(w)} for w, e in d.items()), key=lambda x: (-x["count"], x["word"]))


def to_csv(ws: Workspace) -> str:
    buf = io.StringIO()
    wr = csv.writer(buf)
    wr.writerow(["word", "count", "problems", "note"])
    for it in items(ws):
        wr.writerow([it["word"], it["count"], " ".join(it["problems"]), it["note"]])
    return buf.getvalue()
