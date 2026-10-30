"""依主題診斷弱點：從你的提交紀錄算出每個主題家族的『卡關程度』，並挑出該主題還沒做的題目加練。

分數是可解釋的啟發式，不是統計檢定：
  每題的卡關程度 = 0.2 ×（第一次通過前的失敗次數，最多算 4）＋ 0.25 ×（用了幾次提示，最多算 2）＋ 0.3（放棄過）＋ 0.15 ×（重練失敗次數，最多算 2）；
  還沒通過卻已經試了 2 次以上（或用過提示）的題，至少算 0.8。
  主題分數 = 向全體平均收縮後的平均卡關程度（每個主題加 2 題「平均題」，避免只做一兩題就下定論）。
至少 3 題有紀錄才會下結論；資料不足的主題標示『資料不足』，不會被當成弱點。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from . import bank as bank_mod
from . import course as course_mod
from .store import Workspace

SHRINK_K = 2
MIN_PROBLEMS = 3
WEAK_AT = 0.5
WATCH_AT = 0.35

FAMILIES: List[Tuple[str, str]] = [
    ("basic", "基礎語法與輸入輸出"), ("string", "字串與解析"), ("math", "數學與數論"), ("sim", "模擬與網格"),
    ("sort", "排序、二分與雙指標"), ("ds", "資料結構"), ("greedy", "貪心"), ("search", "遞迴、回溯與位元"),
    ("graph", "圖論"), ("dp", "動態規劃"), ("geo", "計算幾何"), ("cpp", "C++ 與效能"), ("other", "其他"),
]
NAME = dict(FAMILIES)

UNIT_FAMILY = {
    1: "basic", 2: "basic", 3: "basic", 5: "basic", 9: "basic", 10: "basic", 4: "string", 14: "string", 44: "string",
    6: "math", 11: "math", 12: "math", 37: "math", 7: "sim", 13: "sim", 17: "sort", 18: "sort", 19: "sort",
    20: "ds", 21: "ds", 46: "ds", 22: "greedy", 23: "search", 24: "search",
    26: "graph", 27: "graph", 28: "graph", 29: "graph", 30: "graph", 43: "graph",
    31: "dp", 32: "dp", 33: "dp", 34: "dp", 35: "dp", 36: "dp", 45: "dp", 42: "geo", 39: "cpp", 40: "cpp", 41: "cpp",
}
# 不在單元裡的題（UVA 真題、歷屆題、自訂題）靠題目的主題字串判斷；先比對先贏
TOPIC_RULES: List[Tuple[str, str]] = [
    (r"DP|背包|LCS|LIS|Kadane|區間 ?DP|博弈|位元遮罩|子集合和", "dp"),
    (r"BFS|DFS|最短|生成樹|並查集|拓撲|Floyd|歐拉|連通|二分圖|minimax|maximin|flood", "graph"),
    (r"凸包|座標|幾何|多邊形", "geo"),
    (r"大數|進位|質數|因數|數論|模運算|歐幾里得|組合|數學|前綴", "math"),
    (r"字串|解析|正則|取代|回文|映射", "string"),
    (r"堆|stack|queue|deque|優先佇列", "ds"),
    (r"排序|二分|雙指標|中位數", "sort"),
    (r"貪心|區間覆蓋", "greedy"),
    (r"回溯|遞迴|枚舉|位元|子集合", "search"),
    (r"模擬|格子|網格|二維", "sim"),
    (r"輸入輸出|EOF|條件判斷|極值|計數|集合|dict", "basic"),
]


def _unit_index(course: Dict[str, Any]) -> Dict[str, int]:
    idx: Dict[str, int] = {}
    for u in course["units"]:
        for pid in list(u["drills"]) + list(u["anchors"]):
            idx.setdefault(pid, u["n"])
    return idx


def family_of(pid: str, bank: Dict[str, dict], unit_idx: Dict[str, int]) -> str:
    n = unit_idx.get(pid)
    if n in UNIT_FAMILY:
        return UNIT_FAMILY[n]
    topic = bank.get(pid, {}).get("topic") or ""
    for pat, fam in TOPIC_RULES:
        if re.search(pat, topic, re.I):
            return fam
    return "other"


def per_problem(events: List[dict]) -> Dict[str, Dict[str, Any]]:
    """每題：第一次通過前的失敗／提示次數、是否放棄、重練失敗次數、是否已通過。"""
    per: Dict[str, List[dict]] = {}
    for e in events:
        if e.get("problem") and e["kind"] in ("test", "hint", "ask", "giveup"):
            per.setdefault(e["problem"], []).append(e)
    out: Dict[str, Dict[str, Any]] = {}
    for pid, evs in per.items():
        evs.sort(key=lambda e: e["ts"])
        fails = hints = 0
        solved = gave_up = False
        review_fail = 0
        for e in evs:
            k = e["kind"]
            if k == "test":
                if e.get("review_attempt") and e["verdict"] != "AC":
                    review_fail += 1
                if solved:
                    continue
                if e["verdict"] == "AC":
                    solved = True
                else:
                    fails += 1
            elif solved:
                continue
            elif k == "hint" and e.get("level", 0) >= 1:
                hints += 1
            elif k == "ask" and e.get("ask_kind") in ("question", "mismatch"):
                hints += 1
            elif k == "giveup":
                gave_up = True
        attempts = sum(1 for e in evs if e["kind"] == "test")
        if not solved and attempts < 2 and not hints and not gave_up:
            continue                       # 才剛開始的題，還不算卡關
        s = 0.2 * min(fails, 4) + 0.25 * min(hints, 2) + (0.3 if gave_up else 0.0) + 0.15 * min(review_fail, 2)
        if not solved:
            s = max(s, 0.8)
        out[pid] = {"solved": solved, "fails": fails, "hints": hints, "gave_up": gave_up, "review_fail": review_fail,
                    "struggle": round(min(1.0, s), 3), "first_try": solved and fails == 0 and hints == 0 and not gave_up}
    return out


def analyze(ws: Workspace, bank: Optional[Dict[str, dict]] = None, course: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    bank = bank if bank is not None else bank_mod.load_bank(ws)
    course = course or course_mod.load()
    idx = _unit_index(course)
    probs = per_problem(ws.events())
    by: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
    for pid, p in probs.items():
        by.setdefault(family_of(pid, bank, idx), []).append((pid, p))
    all_s = [p["struggle"] for p in probs.values()]
    prior = sum(all_s) / len(all_s) if all_s else 0.3
    rows = []
    for key, name in FAMILIES:
        items = by.get(key, [])
        n = len(items)
        if not n:
            rows.append({"key": key, "name": name, "n": 0, "solved": 0, "first_try_rate": None, "avg_hints": None, "gave_up": 0, "review_fail": 0,
                         "score": None, "level": "none", "problems": []})
            continue
        total = sum(p["struggle"] for _, p in items)
        score = (total + SHRINK_K * prior) / (n + SHRINK_K)
        level = "unknown" if n < MIN_PROBLEMS else "weak" if score >= WEAK_AT else "watch" if score >= WATCH_AT else "ok"
        rows.append({"key": key, "name": name, "n": n, "solved": sum(1 for _, p in items if p["solved"]),
                     "first_try_rate": round(sum(1 for _, p in items if p["first_try"]) / n, 2),
                     "avg_hints": round(sum(p["hints"] for _, p in items) / n, 2), "gave_up": sum(1 for _, p in items if p["gave_up"]),
                     "review_fail": sum(p["review_fail"] for _, p in items), "score": round(score, 2), "level": level,
                     "problems": [{"id": pid, "struggle": p["struggle"], "solved": p["solved"]} for pid, p in sorted(items, key=lambda x: -x[1]["struggle"])[:5]]})
    rows = [r for r in rows if r["n"]] + [r for r in rows if not r["n"]]
    rows.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))
    flagged = [r["key"] for r in rows if r["level"] in ("weak", "watch")]
    return {"families": rows, "weak": [r["key"] for r in rows if r["level"] == "weak"], "watch": [r["key"] for r in rows if r["level"] == "watch"],
            "flagged": flagged, "problems_seen": len(probs), "enough": any(r["level"] in ("weak", "watch", "ok") for r in rows),
            "note": "" if probs else "還沒有紀錄。多做幾題再來看。"}


def candidates(ws: Workspace, bank: Dict[str, dict], course: Dict[str, Any], family: str, limit: int = 3,
               exclude: Optional[set] = None) -> List[Dict[str, Any]]:
    """該主題裡還沒通過、有測資、難度適合你目前階段的題，由易到難。"""
    idx = _unit_index(course)
    st = ws.state()
    stage = int(ws.config()["stage"])
    cur = int(st["course"]["unit"])
    exclude = exclude or set()
    out = []
    for pid, b in bank.items():
        if pid in exclude or b.get("reserve"):
            continue
        sp = st["problems"].get(pid)
        if sp and sp.get("first_pass") is not None:
            continue
        if family_of(pid, bank, idx) != family:
            continue
        if bank_mod.is_drill(pid):
            u = idx.get(pid)
            if u is None or u > cur:             # 還沒學到的單元不出
                continue
        else:
            if not any((ws.tests / pid).glob("*.in")) or int(b.get("stage", 1)) > stage + 1:
                continue
        out.append({"id": pid, "title": b.get("title", pid), "difficulty": int(b.get("difficulty", 2)), "stage": b.get("stage"),
                    "topic": b.get("topic", ""), "drill": bank_mod.is_drill(pid)})
    out.sort(key=lambda p: (p["difficulty"], p["id"]))
    return out[:limit]


def suggestions(ws: Workspace, bank: Dict[str, dict], course: Dict[str, Any], analysis: Optional[Dict[str, Any]] = None,
                per_family: int = 2, families: int = 3) -> List[Dict[str, Any]]:
    """依弱度由高到低，每個弱主題給幾題。"""
    analysis = analysis or analyze(ws, bank, course)
    out, used = [], set()
    for r in analysis["families"]:
        if r["level"] not in ("weak", "watch") or len(set(o["family"] for o in out)) >= families:
            continue
        for c in candidates(ws, bank, course, r["key"], per_family, used):
            used.add(c["id"])
            out.append(dict(c, family=r["key"], family_name=r["name"], score=r["score"], level=r["level"], first_try_rate=r["first_try_rate"]))
    return out
