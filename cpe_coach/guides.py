"""學習指南測驗：每門課每階段一份的單選題（資料在 data/guides/*.json，由 dev/gen_guides.py 產生）。
題目送到瀏覽器時不含答案與解析；作答後由這裡判對錯、回傳解析並記錄（錯題可以單獨重做）。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .store import Workspace

DIR = Path(__file__).parent / "data" / "guides"


def _index() -> List[Dict[str, Any]]:
    f = DIR / "index.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def _load(gid: str) -> Dict[str, Any]:
    if not gid.replace("-", "").isalnum():
        raise ValueError("指南編號不正確")
    f = DIR / f"{gid}.json"
    if not f.exists():
        raise ValueError(f"沒有 {gid} 這份指南")
    return json.loads(f.read_text(encoding="utf-8"))


def _last(ws: Workspace) -> Dict[str, bool]:
    """每題最近一次作答是否答對：key = 'gid|group|i'。"""
    out: Dict[str, bool] = {}
    for e in ws.events():
        if e["kind"] == "gquiz":
            out[f"{e['guide']}|{e['group']}|{e['q']}"] = bool(e["ok"])
    return out


def index(ws: Workspace) -> List[Dict[str, Any]]:
    last = _last(ws)
    res = []
    for g in _index():
        keys = [k for k in last if k.startswith(g["id"] + "|")]
        res.append({**g, "answered": len(keys), "correct": sum(1 for k in keys if last[k]), "wrong": sum(1 for k in keys if not last[k])})
    return res


def get_set(ws: Workspace, gid: str, group: str) -> Dict[str, Any]:
    g = _load(gid)
    last = _last(ws)
    items = []
    for gi, grp in enumerate(g["groups"]):
        if group == "wrong" or group == "all" or str(gi) == group:
            for qi, q in enumerate(grp["questions"]):
                if group == "wrong" and last.get(f"{gid}|{gi}|{qi}") is not False:
                    continue
                items.append({"group": gi, "i": qi, "stem": q["stem"], "code": q["code"], "lang": q["lang"], "options": q["options"], "section": grp["title"]})
    if not items and group != "wrong" and not any(str(i) == group for i in range(len(g["groups"]))) and group != "all":
        raise ValueError("沒有這組題目")
    return {"id": gid, "title": g["title"], "items": items}


def answer(ws: Workspace, gid: str, group: int, i: int, choice: int) -> Dict[str, Any]:
    g = _load(gid)
    try:
        q = g["groups"][group]["questions"][i]
    except (IndexError, TypeError):
        raise ValueError("沒有這一題")
    if choice not in (0, 1, 2, 3):
        raise ValueError("選項只有 0–3")
    ok = choice == q["answer"]
    ws.log("gquiz", guide=gid, group=group, q=i, ok=ok, choice=choice)
    return {"correct": ok, "answer": q["answer"], "why": q["why"]}
