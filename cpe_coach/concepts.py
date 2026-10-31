"""知識點（概念）：把每一題對到幾個知識點，並提供先修關係。記憶、掌握度推測、推薦下一題都以知識點為單位。"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

DATA = Path(__file__).parent / "data" / "concepts.json"
_cache: Optional[Dict[str, Any]] = None


def load() -> Dict[str, Dict[str, Any]]:
    global _cache
    if _cache is None:
        _cache = json.loads(DATA.read_text(encoding="utf-8"))["concepts"]
    return _cache


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s.lower())


def of_problem(p: Dict[str, Any]) -> List[str]:
    """一題屬於哪些知識點：用 topic、標籤、標題比對關鍵字；全都比不到就歸到 loop（一般模擬題）。
    比對時用「長關鍵字優先」，一個關鍵字只算一次。"""
    hay = _norm(" ".join([str(p.get("topic", "")), " ".join(p.get("cpe_tags", []) or []), str(p.get("title", ""))]))
    found: List[str] = []
    for cid, c in load().items():
        if any(_norm(k) in hay for k in c["kw"]):
            found.append(cid)
    return found[:3] or ["loop"]


def prereq_closure(cid: str) -> Set[str]:
    out: Set[str] = set()
    todo = list(load().get(cid, {}).get("pre", []))
    while todo:
        x = todo.pop()
        if x not in out:
            out.add(x)
            todo.extend(load().get(x, {}).get("pre", []))
    return out


def topo_order() -> List[str]:
    """先修在前的順序（同層依課程單元）。"""
    cs = load()
    done: List[str] = []
    seen: Set[str] = set()

    def visit(c: str) -> None:
        if c in seen:
            return
        seen.add(c)
        for p in cs[c]["pre"]:
            visit(p)
        done.append(c)
    for c in sorted(cs, key=lambda k: (cs[k]["unit"], k)):
        visit(c)
    return done


def validate() -> List[str]:
    """資料自我檢查：先修要存在、不能有環。回傳問題清單（空 = 正常）。"""
    cs = load()
    bad = [f"{c} 的先修 {p} 不存在" for c, v in cs.items() for p in v["pre"] if p not in cs]
    state: Dict[str, int] = {}

    def dfs(c: str) -> bool:
        if state.get(c) == 1:
            return True
        if state.get(c) == 2:
            return False
        state[c] = 1
        cyc = any(dfs(p) for p in cs[c]["pre"] if p in cs)
        state[c] = 2
        return cyc
    if any(dfs(c) for c in cs):
        bad.append("先修關係有環")
    return bad
