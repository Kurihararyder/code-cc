"""CPE 原題清單（一星題 49、二星題 15、歷屆試題 31）與匯入。

清單來自社群整理的 GitHub repo LuckyPigeon/CPE_Previous_Questions（MIT 授權，見 data/cpe_sets.json 的 source）。
內建資料只有題號與標題（事實）；題目敘述是 UVa 各題作者的著作，不內建：匯入時才從 GitHub 把 PDF 下載到「你自己的電腦」，
轉成題目文字（statements/uvaN.txt）與範例測資（tests/uvaN/sample*），原 PDF 也留一份在 statements/uvaN.pdf。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .pastexams import has_statement, has_tests
from .store import Workspace

DATA = Path(__file__).parent / "data" / "cpe_sets.json"
META = Path(__file__).parent / "data" / "cpe_meta.json"          # 每題的標籤、先修單元、難度、提示（我寫的，沒有官方核對）
SET_KEYS = ("one", "two", "past")
DIR_TO_KEY = {"一星題": "one", "二星題": "two", "歷屆試題": "past"}


def load() -> Dict[str, Any]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def meta() -> Dict[int, Dict[str, Any]]:
    """UVA 題號 → {t 標籤, u 先修單元, s 難度, c 這是哪一類, i 關鍵洞察}。"""
    if not META.exists():
        return {}
    return {int(k): v for k, v in json.loads(META.read_text(encoding="utf-8"))["problems"].items()}


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
    mt = meta()
    titles: Dict[int, str] = {}
    for key in SET_KEYS:
        for p in data["sets"][key]["problems"]:
            titles.setdefault(int(p["uva"]), p["title"])
    out: Dict[str, Dict[str, Any]] = {}
    for n, keys in membership().items():
        stage, diff, topic = _defaults(keys)
        m = mt.get(n)
        if m:
            diff, topic = m["s"], "／".join(m["t"][:3])
        out[pid_of(n)] = {
            "id": pid_of(n), "title": titles[n], "source": "UVA", "number": n, "stage": stage, "difficulty": diff, "topic": topic,
            "hint_category": m["c"] if m else "這是 CPE 原題；先讀題、手算範例，再判斷它屬於哪一類。", "hint_insight": m["i"] if m else None,
            "url": f"https://vjudge.net/problem/UVA-{n}", "official_one_star": "one" in keys, "unverified": True, "cpe_sets": keys,
            "cpe_tags": m["t"] if m else [], "prereq_unit": m["u"] if m else None}
    return out


def merge_into_bank(bank: Dict[str, dict]) -> None:
    for pid, e in bank_entries().items():
        if pid in bank:
            b = bank[pid]
            b["cpe_sets"] = e["cpe_sets"]
            b["cpe_tags"], b["prereq_unit"] = e["cpe_tags"], e["prereq_unit"]
            if not b.get("hint_insight") and e["hint_insight"]:                    # 原本沒有提示的，補上我寫的；原本就有的不動
                b["hint_insight"] = e["hint_insight"]
                if "hint_category" not in b or not b["hint_category"]:
                    b["hint_category"] = e["hint_category"]
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


def set_numbers(key: str, ws: Optional[Workspace] = None) -> List[int]:
    """集合內的題號：預設依 UVA 題號排序；工作區的 .cpe/cpe_order.json（{"one": [100, 118, ...]}）可以改成官網的順序，沒列到的排在後面。"""
    nums = sorted(int(p["uva"]) for p in load()["sets"][key]["problems"])
    if ws is not None:
        f = ws.meta / "cpe_order.json"
        try:
            custom = [int(x) for x in json.loads(f.read_text(encoding="utf-8")).get(key, []) if int(x) in nums]
        except (OSError, ValueError, TypeError, AttributeError):
            custom = []
        if custom:
            seen = set(custom)
            nums = list(dict.fromkeys(custom)) + [n for n in nums if n not in seen]
    return nums


def related(number: int, limit: int = 3) -> List[int]:
    """同標籤重疊最多的其他題（相似題）；同分時題號小的在前。"""
    mt = meta()
    me = set(mt.get(number, {}).get("t", []))
    if not me:
        return []
    scored = sorted(((len(me & set(m["t"])), -n) for n, m in mt.items() if n != number and me & set(m["t"])), reverse=True)
    return [-k for _, k in scored[:limit]]


def unit_pool(ws: Workspace, bank: Dict[str, dict], n: int) -> Optional[Dict[str, Any]]:
    spec = UNIT_SETS.get(n)
    if spec is None:
        return None
    key, lo, hi, label = spec
    st = ws.state()["problems"]
    items = []
    for num in set_numbers(key, ws)[lo:hi]:
        pid = pid_of(num)
        b = bank.get(pid, {})
        items.append({"id": pid, "title": b.get("title", pid), "accuracy": None, "stars": b.get("difficulty"), "has_tests": has_tests(ws, pid),
                      "solved": bool(st.get(pid, {}).get("first_pass")), "url": b.get("url"), "tags": b.get("cpe_tags", []),
                      "prereq_unit": b.get("prereq_unit"), "related": [pid_of(r) for r in related(num)]})
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
                         "has_tests": has_tests(ws, pid), "solved": bool(st.get(pid, {}).get("first_pass")), "no_pdf": bool(p.get("no_pdf")),
                         "tags": bank.get(pid, {}).get("cpe_tags", []), "prereq_unit": bank.get(pid, {}).get("prereq_unit"),
                         "has_pdf": (ws.root / "statements" / f"{pid}.pdf").exists()})
        sets.append({"key": key, "name": data["sets"][key]["name"], "problems": rows, "count": len(rows),
                     "ready": sum(1 for r in rows if r["has_tests"]), "solved": sum(1 for r in rows if r["solved"])})
    ids = {r["id"] for s in sets for r in s["problems"]}
    return {"sets": sets, "total": len(ids), "ready": sum(1 for i in ids if has_tests(ws, i)), "source": data["source"]}


def pdf_hashes() -> Dict[int, Set[str]]:
    """UVA 題號 → 驗證時那份 PDF 的 SHA-256（只有指紋，不含內容）。同一題在兩個題單裡的檔案可能不同，所以是集合。"""
    out: Dict[int, Set[str]] = {}
    for key in SET_KEYS:
        for p in load()["sets"][key]["problems"]:
            if p.get("sha256"):
                out.setdefault(int(p["uva"]), set()).add(p["sha256"])
    return out
