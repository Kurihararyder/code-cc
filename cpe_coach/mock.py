"""模擬考：完全比照 CPE（7 題／3 小時／ICPC 計分／禁用提示）。每週無 AI 測驗共用同一套引擎。"""
from __future__ import annotations

import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .judge import AC, CE, FAILS
from .store import Workspace

PENALTY_MIN = 20
# 每場 7 題：3 題一顆星、2 題二顆星、1 題三顆星、1 題四顆星
FULL = {"difficulties": [1, 1, 1, 2, 2, 3, 4], "minutes": 180}
SHORT = {"difficulties": [1, 1, 1], "minutes": 90}
WEEKLY_COUNT, WEEKLY_MINUTES = 3, 60

TEMPLATE = '''import sys


def main():
    for line in sys.stdin:  # 多組測資：讀到 EOF
        line = line.rstrip("\\n")  # 空行也可能是一筆資料；題目沒說就不要跳過
        # TODO


if __name__ == "__main__":
    main()
'''


CPP_TEMPLATE = '''#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    // TODO
    return 0;
}
'''


def template(lang: str) -> str:
    return CPP_TEMPLATE if lang == "cpp" else TEMPLATE


def pick_by_difficulty(bank: Dict[str, dict], difficulties: List[int], st: Dict[str, Any],
                       rng: random.Random, max_stage: int = 9) -> List[str]:
    """每個難度挑一題（盡量挑沒通過的）。該難度沒題目時，退而取最接近的難度。
    max_stage 限制題目階段，避免出到你還沒學過的主題。"""
    chosen: List[str] = []
    for d in difficulties:
        pool = [p for p in bank.values() if p["id"] not in chosen and p.get("stage", 1) <= max_stage]
        if not pool:
            break
        # 優先順序：難度最接近 → 沒做過（其中優先驗收專用題 reserve）→ 隨機
        def key(p):
            solved = st["problems"].get(p["id"], {}).get("first_pass") is not None
            return (abs(p["difficulty"] - d), solved, (not p.get("reserve")) if not solved else False, rng.random())
        pool.sort(key=key)
        chosen.append(pool[0]["id"])
    return chosen


def pick_weekly(st: Dict[str, Any], n: int = WEEKLY_COUNT) -> List[str]:
    """挑最久沒碰的已通過題目，從空白檔重寫。"""
    solved = [(p["last_pass"] or 0, pid) for pid, p in st["problems"].items() if p["first_pass"] is not None]
    solved.sort()
    return [pid for _, pid in solved[:n]]


def _stamp(ts: float) -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime(ts))


def start(ws: Workspace, bank: Dict[str, dict], kind: str, rng: Optional[random.Random] = None, *,
          ids: Optional[List[str]] = None, minutes: Optional[int] = None, lang: str = "py",
          gate: Optional[Dict[str, Any]] = None, max_stage: int = 9) -> Dict[str, Any]:
    """kind: mock（7 題 3 小時）／short（3 題 90 分）／weekly（重寫 3 題舊題）／gate（指定題目）。"""
    if ws.exam_active():
        raise ValueError("已有進行中的考試，先 cpe mock finish")
    st = ws.state()
    rng = rng or random.Random()
    if kind == "gate":
        if not ids:
            raise ValueError("gate 需要指定題目")
    elif kind == "weekly":
        ids, minutes = pick_weekly(st), WEEKLY_MINUTES
        if not ids:
            raise ValueError("還沒有通過的題目，無法出每週測驗。先解幾題吧")
    else:
        spec = FULL if kind == "mock" else SHORT
        ids, minutes = pick_by_difficulty(bank, spec["difficulties"], st, rng, max_stage), spec["minutes"]
    ext = "cpp" if lang == "cpp" else "py"
    folder = ws.exam_dir / f"{kind}-{_stamp(ws.now())}"
    folder.mkdir(parents=True, exist_ok=True)
    files = {}
    for pid in ids:
        f = folder / f"{pid}.{ext}"
        f.write_text(template(lang), encoding="utf-8")
        files[pid] = str(f.relative_to(ws.root))
    exam = {"kind": kind, "start": ws.now(), "minutes": minutes, "problems": ids, "files": files, "lang": lang,
            "gate": gate, "results": {pid: {"wrong": 0, "ac_min": None} for pid in ids}}
    ws.save_exam(exam)
    ws.log("exam_start", exam_kind=kind, problems=ids, minutes=minutes)
    return exam


def remaining_seconds(exam: Dict[str, Any], now: float) -> float:
    return exam["start"] + exam["minutes"] * 60 - now


def solution_path(ws: Workspace, exam: Dict[str, Any], pid: str) -> Optional[Path]:
    f = exam["files"].get(pid)
    return ws.root / f if f else None


def record(ws: Workspace, exam: Dict[str, Any], pid: str, verdict: str) -> str:
    """記錄一次提交。逾時不計分；語法錯誤不計罰時（比照 ICPC 慣例）。"""
    if pid not in exam["results"]:
        return ""
    r = exam["results"][pid]
    now = ws.now()
    if remaining_seconds(exam, now) < 0:
        return "已超過考試時間，這次提交不計分。"
    if r["ac_min"] is not None:
        return ""
    if verdict == AC:
        r["ac_min"] = int((now - exam["start"]) // 60)
        ws.save_exam(exam)
        return f"計分：第 {r['ac_min']} 分鐘通過，累計錯誤 {r['wrong']} 次。"
    if verdict in FAILS and verdict != CE:
        r["wrong"] += 1
        ws.save_exam(exam)
        return f"計分：這題已錯 {r['wrong']} 次（每次 +{PENALTY_MIN} 分鐘罰時）。"
    return ""


def score(exam: Dict[str, Any]) -> Dict[str, Any]:
    solved = [(pid, r) for pid, r in exam["results"].items() if r["ac_min"] is not None]
    penalty = sum(r["ac_min"] + PENALTY_MIN * r["wrong"] for _, r in solved)
    return {"kind": exam["kind"], "solved": len(solved), "total": len(exam["problems"]),
            "penalty": penalty, "problems": exam["problems"], "gate": exam.get("gate"),
            "detail": {pid: dict(r) for pid, r in exam["results"].items()}}


def finish(ws: Workspace) -> Dict[str, Any]:
    exam = ws.exam()
    if exam is None:
        raise ValueError("目前沒有進行中的考試")
    summary = score(exam)
    summary["date"] = _stamp(exam["start"])
    st = ws.state()
    st["exams"].append(summary)
    ws.save_state(st)
    ws.save_exam(None)
    ws.log("exam_finish", exam_kind=summary["kind"], solved=summary["solved"],
           total=summary["total"], penalty=summary["penalty"])
    return summary
