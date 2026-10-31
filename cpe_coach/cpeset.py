"""CPE 原題清單（一星題 49、二星題 15、歷屆試題 31）與匯入。

清單來自社群整理的 GitHub repo LuckyPigeon/CPE_Previous_Questions（MIT 授權，見 data/cpe_sets.json 的 source）。
內建資料只有題號與標題（事實）；題目敘述是 UVa 各題作者的著作，不內建：匯入時才從 GitHub 把 PDF 下載到「你自己的電腦」，
轉成題目文字（statements/uvaN.txt）與範例測資（tests/uvaN/sample*），原 PDF 也留一份在 statements/uvaN.pdf。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .pastexams import has_statement, has_tests
from .store import Workspace

DATA = Path(__file__).parent / "data" / "cpe_sets.json"
SET_KEYS = ("one", "two", "past")
DIR_TO_KEY = {"一星題": "one", "二星題": "two", "歷屆試題": "past"}


def load() -> Dict[str, Any]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def pid_of(number: int) -> str:
    return f"uva{number}"


def membership() -> Dict[int, List[str]]:
    """UVA 題號 → 屬於哪些集合（one／two／past）。"""
    out: Dict[int, List[str]] = {}
    for key in SET_KEYS:
        for p in load()["sets"][key]["problems"]:
            out.setdefault(int(p["uva"]), []).append(key)
    return out


# ---------- 與題庫的整合 ----------
def _defaults(keys: List[str]) -> Tuple[int, int, str]:
    if "one" in keys:
        return 1, 1, "CPE 一星題"
    if "two" in keys:
        return 2, 2, "CPE 二星題"
    return 2, 2, "CPE 歷屆試題"


def bank_entries() -> Dict[str, Dict[str, Any]]:
    data = load()
    titles: Dict[int, str] = {}
    for key in SET_KEYS:
        for p in data["sets"][key]["problems"]:
            titles.setdefault(int(p["uva"]), p["title"])
    out: Dict[str, Dict[str, Any]] = {}
    for n, keys in membership().items():
        stage, diff, topic = _defaults(keys)
        out[pid_of(n)] = {
            "id": pid_of(n), "title": titles[n], "source": "UVA", "number": n, "stage": stage, "difficulty": diff, "topic": topic,
            "hint_category": "這是 CPE 原題；先讀題、手算範例，再判斷它屬於哪一類。", "hint_insight": None,
            "url": f"https://vjudge.net/problem/UVA-{n}", "official_one_star": "one" in keys, "unverified": True, "cpe_sets": keys}
    return out


def merge_into_bank(bank: Dict[str, dict]) -> None:
    for pid, e in bank_entries().items():
        if pid in bank:
            b = bank[pid]
            b["cpe_sets"] = e["cpe_sets"]
            if "one" in e["cpe_sets"]:
                b["official_one_star"] = True
        else:
            bank[pid] = e


# ---------- 單元的題單 ----------
# 單元 → (集合, 起, 迄, 說明)：集合內依 UVA 題號排序後取 [起:迄]。官網的順序我拿不到，所以明講是依題號排序。
UNIT_SETS = {
    15: ("one", 0, 25, "CPE 一星題選集 前 25 題（依 UVA 題號排序）"),
    16: ("one", 25, None, "CPE 一星題選集 後 24 題（依 UVA 題號排序）"),
    25: ("two", 0, None, "CPE 二星題選集（15 題）"),
    48: ("past", 0, None, "CPE 歷屆試題（31 題；整場模擬的素材）"),
    51: ("past", 0, None, "CPE 歷屆試題（31 題；整場模擬的素材）"),
}


def set_numbers(key: str) -> List[int]:
    return sorted(int(p["uva"]) for p in load()["sets"][key]["problems"])


def unit_pool(ws: Workspace, bank: Dict[str, dict], n: int) -> Optional[Dict[str, Any]]:
    spec = UNIT_SETS.get(n)
    if spec is None:
        return None
    key, lo, hi, label = spec
    st = ws.state()["problems"]
    items = []
    for num in set_numbers(key)[lo:hi]:
        pid = pid_of(num)
        b = bank.get(pid, {})
        items.append({"id": pid, "title": b.get("title", pid), "accuracy": None, "stars": b.get("difficulty"), "has_tests": has_tests(ws, pid),
                      "solved": bool(st.get(pid, {}).get("first_pass")), "url": b.get("url")})
    return {"label": label, "items": items, "ready": sum(1 for p in items if p["has_tests"]), "solved": sum(1 for p in items if p["solved"])}


def status(ws: Workspace, bank: Dict[str, dict]) -> Dict[str, Any]:
    """網頁／命令列要顯示的：三個集合各題的狀態。"""
    data = load()
    st = ws.state()["problems"]
    sets = []
    for key in SET_KEYS:
        rows = []
        for p in sorted(data["sets"][key]["problems"], key=lambda x: x["uva"]):
            pid = pid_of(int(p["uva"]))
            rows.append({"id": pid, "number": int(p["uva"]), "title": bank.get(pid, {}).get("title", p["title"]), "has_statement": has_statement(ws, pid),
                         "has_tests": has_tests(ws, pid), "solved": bool(st.get(pid, {}).get("first_pass")), "no_pdf": bool(p.get("no_pdf"))})
        sets.append({"key": key, "name": data["sets"][key]["name"], "problems": rows, "count": len(rows),
                     "ready": sum(1 for r in rows if r["has_tests"]), "solved": sum(1 for r in rows if r["solved"])})
    ids = {r["id"] for s in sets for r in s["problems"]}
    return {"sets": sets, "total": len(ids), "ready": sum(1 for i in ids if has_tests(ws, i)), "source": data["source"]}
