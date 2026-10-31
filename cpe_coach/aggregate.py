"""匿名統計與難度校準（IRT）。

單機版沒有「很多人的資料」可用，所以走「自願、用檔案交換」：每個人用 `cpe stats-export` 匯出一個只含「每題一次通過與否」的匿名檔
（沒有時間戳、沒有程式碼、沒有題目文字、沒有名字；只有隨機代號），把檔案集中給一個人，用 `cpe calibrate-merge 檔案…` 合併、
用 Rasch（1PL）模型估出每題的難度，產生 calibration.json，放進工作區的 .cpe/ 後，推薦下一題與適性診斷就會改用校準過的難度。

誠實的限制：少於 5 個學習者、或單題少於 8 筆作答時，估計不可靠，會明確標出來而且不套用；Rasch 假設每題鑑別度相同，是簡化。
"""
from __future__ import annotations

import json
import math
import secrets
from pathlib import Path
from typing import Any, Dict, List

from . import bank as bank_mod
from . import knowledge

MIN_LEARNERS = 5
MIN_RESPONSES = 8


def anon_id(ws) -> str:
    cfg = ws.config()
    if not cfg.get("anon_id"):
        cfg["anon_id"] = secrets.token_hex(6)
        ws.save_config(cfg)
    return cfg["anon_id"]


def export_anonymous(ws, dest: Path) -> Dict[str, Any]:
    """只含：隨機代號、內建題庫裡每題「第一次作答是否一次通過」與是否用提示、概念測驗每題對錯。"""
    base = bank_mod.load_bank(None)
    first: Dict[str, Dict[str, Any]] = {}
    for a in knowledge.attempts(ws.events()):
        if a["problem"] in base and a["problem"] not in first:
            first[a["problem"]] = {"first_try": 1 if a["correct"] else 0, "solved": 1 if a["solved"] else 0}
    quiz: Dict[str, int] = {}
    for e in ws.events():
        if e.get("kind") == "quiz":
            for it in e.get("items", []):
                quiz.setdefault(it["id"], 1 if it["correct"] else 0)
    data = {"format": 1, "kind": "cpe-anonymous-stats", "learner": anon_id(ws), "problems": first, "quiz": quiz}
    Path(dest).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


def _sig(x: float) -> float:
    return 1 / (1 + math.exp(-max(-30, min(30, x))))


def rasch(responses: List[Dict[str, Any]], iters: int = 60) -> Dict[str, Any]:
    """responses：[{learner, item, x(0/1)}]。聯合最大概似（JMLE），能力與難度都加一點先驗避免全對／全錯發散，難度平均置中為 0。"""
    learners = sorted({r["learner"] for r in responses})
    items = sorted({r["item"] for r in responses})
    li, ii = {l: k for k, l in enumerate(learners)}, {i: k for k, i in enumerate(items)}
    theta = [0.0] * len(learners)
    b = [0.0] * len(items)
    by_l: Dict[int, List] = {}
    by_i: Dict[int, List] = {}
    for r in responses:
        by_l.setdefault(li[r["learner"]], []).append((ii[r["item"]], r["x"]))
        by_i.setdefault(ii[r["item"]], []).append((li[r["learner"]], r["x"]))
    for _ in range(iters):
        for l, rows in by_l.items():
            g = sum(x - _sig(theta[l] - b[i]) for i, x in rows) - theta[l] / 4.0
            h = sum(_sig(theta[l] - b[i]) * (1 - _sig(theta[l] - b[i])) for i, _ in rows) + 0.25
            theta[l] = max(-6, min(6, theta[l] + max(-1, min(1, g / h))))
        for i, rows in by_i.items():
            g = sum(_sig(theta[l] - b[i]) - x for l, x in rows) - b[i] / 4.0
            h = sum(_sig(theta[l] - b[i]) * (1 - _sig(theta[l] - b[i])) for l, _ in rows) + 0.25
            b[i] = max(-6, min(6, b[i] + max(-1, min(1, g / h))))
        mean = sum(b) / len(b)
        b = [v - mean for v in b]
    out = {}
    for i, it in enumerate(items):
        info = sum(_sig(theta[l] - b[i]) * (1 - _sig(theta[l] - b[i])) for l, _ in by_i[i]) + 0.25
        out[it] = {"b": round(b[i], 3), "se": round(1 / math.sqrt(info), 3), "n": len(by_i[i]), "p_correct": round(sum(x for _, x in by_i[i]) / len(by_i[i]), 3)}
    return {"items": out, "learners": len(learners), "theta": {l: round(theta[k], 3) for l, k in li.items()}}


def merge(paths: List[Path]) -> Dict[str, Any]:
    seen: Dict[str, Dict[str, Any]] = {}
    for p in paths:
        try:
            d = json.loads(Path(p).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ValueError(f"讀不了 {p}")
        if not isinstance(d, dict) or d.get("kind") != "cpe-anonymous-stats" or not isinstance(d.get("learner"), str):
            raise ValueError(f"{p} 不是 cpe stats-export 產生的檔案")
        seen[d["learner"]] = d                              # 同一個代號重複出現只算一次（保留最後一份）
    rows_p, rows_q = [], []
    for l, d in seen.items():
        for pid, v in d.get("problems", {}).items():
            if isinstance(v, dict) and v.get("first_try") in (0, 1):
                rows_p.append({"learner": l, "item": pid, "x": v["first_try"]})
        for qid, x in d.get("quiz", {}).items():
            if x in (0, 1):
                rows_q.append({"learner": l, "item": qid, "x": x})
    res: Dict[str, Any] = {"learners": len(seen), "reliable": len(seen) >= MIN_LEARNERS, "problems": {}, "quiz": {}}
    for key, rows in (("problems", rows_p), ("quiz", rows_q)):
        if rows:
            fit = rasch(rows)
            res[key] = {k: v for k, v in fit["items"].items()}
    for key in ("problems", "quiz"):
        for k, v in res[key].items():
            v["reliable"] = res["reliable"] and v["n"] >= MIN_RESPONSES
    res["note"] = ("學習者不足 %d 人，估計不可靠，不會被套用。" % MIN_LEARNERS) if not res["reliable"] else "只有標為 reliable 的題目會被套用。"
    return res


def load_calibration(ws) -> Dict[str, Dict[str, float]]:
    """工作區 .cpe/calibration.json 裡可靠的難度（Rasch 的 b，平均置中）。沒有檔案或損壞就是空的。"""
    try:
        d = json.loads((ws.meta / "calibration.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"problems": {}, "quiz": {}}
    return {k: {i: float(v["b"]) for i, v in d.get(k, {}).items() if isinstance(v, dict) and v.get("reliable") and "b" in v} for k in ("problems", "quiz")}
