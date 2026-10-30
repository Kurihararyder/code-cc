"""歷屆 CPE：場次與題目的資料、匯入、整場模擬的素材。

資料來源有兩個：
1. 內建 data/past_exams.json：只收錄研究報告明確列出的資料（誠實標註來源與未核對的欄位）。
2. 工作區 .cpe/past_exams.json：你用 `cpe past import` 或網頁介面匯入的（會覆蓋同場同題號的內建資料）。
題目敘述（有版權）不內建；用 `cpe past statements <資料夾>` 或網頁介面把你自己取得的題目檔匯入。
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .store import Workspace

DATA = Path(__file__).parent / "data" / "past_exams.json"
# 全體答對率 → 星等（依單場 2020/10/20 的資料估計：★1 約 18–45%、★2 約 3%、★3 約 1%、★4 < 0.5%）
BANDS = [(15.0, 1), (2.0, 2), (0.5, 3), (0.0, 4)]
FORMAT_HELP = """每行一題，欄位用逗號（或 Tab）分隔：
date,order,uva,title,accuracy
2020-10-20,1,10050,Hartals,37.94
- date：YYYY-MM-DD；order：該場第幾題（1–7）；uva：UVA 題號（不知道就留空）
- accuracy：全體答對率（%），可留空
另外可以用一行註解記錄該場平均答對題數：
# 2020-10-20 avg=1.09"""


def stars_from_accuracy(acc: Optional[float]) -> Optional[int]:
    if acc is None:
        return None
    return next(s for lo, s in BANDS if acc >= lo)


def stage_from_accuracy(acc: Optional[float]) -> int:
    return {1: 1, 2: 2, 3: 3, 4: 4}[stars_from_accuracy(acc) or 2]


def problem_id(p: Dict[str, Any], date: str) -> str:
    return f"uva{p['uva']}" if p.get("uva") else f"cpe{date.replace('-', '')}q{p['order']}"


# ---------- 載入與合併 ----------
def _bundled() -> Dict[str, Any]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def _user_path(ws: Workspace) -> Path:
    return ws.meta / "past_exams.json"


def load_all(ws: Optional[Workspace] = None) -> Dict[str, Any]:
    base = _bundled()
    exams: Dict[str, Dict[str, Any]] = {e["date"]: json.loads(json.dumps(e)) for e in base["exams"]}
    if ws is not None and _user_path(ws).exists():
        for e in json.loads(_user_path(ws).read_text(encoding="utf-8")).get("exams", []):
            cur = exams.setdefault(e["date"], {"date": e["date"], "avg_solved": None, "problems": [], "source": "你匯入的資料"})
            if e.get("avg_solved") is not None:
                cur["avg_solved"] = e["avg_solved"]
            by_order = {p["order"]: p for p in cur["problems"]}
            for p in e.get("problems", []):
                by_order[p["order"]] = p
            cur["problems"] = [by_order[k] for k in sorted(by_order)]
    dist = {int(k): v for k, v in base["distribution"].items() if not k.startswith("_")}
    return {"exams": [exams[d] for d in sorted(exams)], "distribution": dist}


# ---------- 匯入 ----------
class ManifestError(ValueError):
    pass


def parse_manifest(text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """回傳 (場次清單, 錯誤訊息清單)。有錯誤的行會被略過，其他照常匯入。"""
    exams: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []

    def exam(date: str) -> Dict[str, Any]:
        return exams.setdefault(date, {"date": date, "avg_solved": None, "problems": [], "source": "你匯入的資料"})

    for n, raw in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^#\s*(\d{4}-\d{2}-\d{2})\s+avg\s*=\s*([\d.]+)\s*$", line, re.I)
        if m:
            exam(m.group(1))["avg_solved"] = float(m.group(2))
            continue
        if line.startswith("#") or line.lower().startswith("date"):
            continue
        delim = "\t" if "\t" in line else ("," if "," in line else None)
        cols = next(csv.reader([line], delimiter=delim)) if delim else line.split()
        if not delim and len(cols) > 5:                 # 空白分隔：date order uva title... accuracy
            cols = cols[:3] + [" ".join(cols[3:-1]), cols[-1]]
        cols = [c.strip() for c in cols]
        try:
            if len(cols) < 4:
                raise ManifestError("欄位不足（至少要有 date,order,uva,title）")
            date, order, uva, title = cols[0], cols[1], cols[2], cols[3]
            acc = cols[4] if len(cols) > 4 else ""
            dt.date.fromisoformat(date)
            order = int(order)
            if not 1 <= order <= 9:
                raise ManifestError("order 要在 1–9")
            uva_n = None if uva.lower() in ("", "-", "none", "null", "?") else int(re.sub(r"(?i)^uva", "", uva))
            if not title:
                raise ManifestError("缺少題目名稱")
            acc_f = None if acc.strip().rstrip("%") in ("", "-") else float(acc.strip().rstrip("%"))
            if acc_f is not None and not 0 <= acc_f <= 100:
                raise ManifestError("答對率要在 0–100")
        except (ValueError, ManifestError) as e:
            errors.append(f"第 {n} 行：{e}（{raw.strip()[:60]}）")
            continue
        p = {"order": order, "title": title, "uva": uva_n, "accuracy": acc_f, "uva_verified": True}
        e = exam(date)
        e["problems"] = [x for x in e["problems"] if x["order"] != order] + [p]
        e["problems"].sort(key=lambda x: x["order"])
    return sorted(exams.values(), key=lambda e: e["date"]), errors


def import_manifest(ws: Workspace, text: str) -> Dict[str, Any]:
    exams, errors = parse_manifest(text)
    if not exams:
        raise ManifestError("沒有解析到任何題目。格式：\n" + FORMAT_HELP + ("\n\n" + "\n".join(errors[:5]) if errors else ""))
    cur = json.loads(_user_path(ws).read_text(encoding="utf-8")) if _user_path(ws).exists() else {"exams": []}
    by_date = {e["date"]: e for e in cur["exams"]}
    for e in exams:
        old = by_date.setdefault(e["date"], {"date": e["date"], "avg_solved": None, "problems": [], "source": e["source"]})
        if e["avg_solved"] is not None:
            old["avg_solved"] = e["avg_solved"]
        o = {p["order"]: p for p in old["problems"]}
        o.update({p["order"]: p for p in e["problems"]})
        old["problems"] = [o[k] for k in sorted(o)]
    _user_path(ws).write_text(json.dumps({"exams": [by_date[d] for d in sorted(by_date)]}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"exams": len(exams), "problems": sum(len(e["problems"]) for e in exams), "errors": errors}


# ---------- 與題庫的整合 ----------
def bank_entries(ws: Optional[Workspace]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for e in load_all(ws)["exams"]:
        for p in e["problems"]:
            pid = problem_id(p, e["date"])
            ent = out.setdefault(pid, {
                "id": pid, "title": p["title"], "source": "UVA" if p.get("uva") else "CPE", "number": p.get("uva"),
                "stage": stage_from_accuracy(p.get("accuracy")), "difficulty": stars_from_accuracy(p.get("accuracy")) or 2,
                "topic": "歷屆", "hint_category": "這是歷屆題；先讀題、手算範例，再判斷它屬於哪一類。", "hint_insight": None,
                "url": f"https://vjudge.net/problem/UVA-{p['uva']}" if p.get("uva") else None,
                "official_one_star": False, "unverified": True, "past": [], "official_accuracy": None})
            ent["past"].append({"date": e["date"], "order": p["order"], "accuracy": p.get("accuracy")})
            if p.get("accuracy") is not None:
                ent["official_accuracy"] = p["accuracy"]
                ent["difficulty"] = stars_from_accuracy(p["accuracy"])
                ent["stage"] = stage_from_accuracy(p["accuracy"])
    return out


def merge_into_bank(bank: Dict[str, dict], ws: Optional[Workspace]) -> None:
    for pid, e in bank_entries(ws).items():
        if pid in bank:
            b = bank[pid]
            b["past"] = e["past"]
            if e["official_accuracy"] is not None:
                b["official_accuracy"] = e["official_accuracy"]
                b["difficulty"] = e["difficulty"]
                b["difficulty_source"] = "official"
        else:
            bank[pid] = e


# ---------- 檢視 ----------
def has_tests(ws: Workspace, pid: str) -> bool:
    d = ws.tests / pid
    return d.is_dir() and any(d.glob("*.in"))


def has_statement(ws: Workspace, pid: str) -> bool:
    return any((ws.root / "statements" / f"{pid}.{x}").exists() for x in ("txt", "md"))


def exam_view(ws: Workspace, bank: Dict[str, dict], e: Dict[str, Any]) -> Dict[str, Any]:
    from .service import statement_is_english
    st = ws.state()
    probs = []
    for p in e["problems"]:
        pid = problem_id(p, e["date"])
        sp = st["problems"].get(pid)
        stmt = next(((ws.root / "statements" / f"{pid}.{x}") for x in ("txt", "md") if (ws.root / "statements" / f"{pid}.{x}").exists()), None)
        probs.append({"order": p["order"], "id": pid, "title": p["title"], "uva": p.get("uva"), "uva_verified": p.get("uva_verified", True),
                      "accuracy": p.get("accuracy"), "stars": stars_from_accuracy(p.get("accuracy")),
                      "has_statement": stmt is not None, "english": bool(stmt and statement_is_english(stmt.read_text(encoding="utf-8", errors="replace"))),
                      "has_tests": has_tests(ws, pid), "solved": bool(sp and sp["first_pass"] is not None),
                      "url": bank.get(pid, {}).get("url")})
    ready = [p for p in probs if p["has_tests"]]
    return {"date": e["date"], "avg_solved": e.get("avg_solved"), "source": e.get("source"), "problems": probs,
            "count": len(probs), "ready": len(ready), "complete": len(probs) >= 7 and len(ready) == len(probs),
            "solved": sum(1 for p in probs if p["solved"])}


def list_exams(ws: Workspace, bank: Dict[str, dict]) -> Dict[str, Any]:
    data = load_all(ws)
    return {"exams": [exam_view(ws, bank, e) for e in reversed(data["exams"])], "distribution": data["distribution"],
            "trend": [{"date": e["date"], "avg": e["avg_solved"]} for e in data["exams"] if e.get("avg_solved") is not None]}


def pool(ws: Workspace, bank: Dict[str, dict], lo: float = 0, hi: float = 100) -> List[Dict[str, Any]]:
    """依全體答對率範圍列出已匯入的歷屆題（答對率由高到低）。"""
    out = []
    for pid, b in bank.items():
        acc = b.get("official_accuracy")
        if b.get("past") and acc is not None and lo <= acc <= hi:
            out.append({"id": pid, "title": b["title"], "accuracy": acc, "stars": stars_from_accuracy(acc),
                        "dates": [x["date"] for x in b["past"]], "has_tests": has_tests(ws, pid), "url": b.get("url")})
    out.sort(key=lambda x: -x["accuracy"])
    return out


# 單元 → 要從匯入的歷屆題裡挑哪個答對率範圍（%）。階段 5 的單元用歷屆題當主要練習材料。
UNIT_POOLS = {
    15: (30.0, 100.0, "歷屆全體答對率 30% 以上（一～二顆星）"),
    16: (15.0, 30.0, "歷屆全體答對率 15%–30%"),
    25: (5.0, 15.0, "歷屆全體答對率 5%–15%（階段 2 驗收的延伸）"),
    47: (0.5, 5.0, "歷屆全體答對率 0.5%–5%（三～四顆星入門）"),
    48: (5.0, 100.0, "歷屆全體答對率 5% 以上（先把容易拿的分數練熟）"),
    49: (5.0, 20.0, "歷屆全體答對率 5%–20%（弱點修補）"),
    50: (0.0, 5.0, "歷屆全體答對率 5% 以下（攻堅）"),
    51: (0.0, 100.0, "所有歷屆題（也可以直接整場模擬）"),
}


def unit_pool(ws: Workspace, bank: Dict[str, dict], n: int) -> Optional[Dict[str, Any]]:
    """這個單元建議用的歷屆題（只列已經匯入、有答對率資料的）。"""
    spec = UNIT_POOLS.get(n)
    if spec is None:
        return None
    lo, hi, label = spec
    st = ws.state()["problems"]
    items = [dict(p, solved=bool(st.get(p["id"], {}).get("first_pass"))) for p in pool(ws, bank, lo, hi if hi >= 100 else hi - 1e-9)]
    return {"lo": lo, "hi": hi, "label": label, "items": items, "ready": sum(1 for p in items if p["has_tests"]),
            "solved": sum(1 for p in items if p["solved"])}


def percentile(solved: int, dist: Dict[int, float]) -> Dict[str, float]:
    """歷年考生中，答對題數 ≥ solved 的比例（前 X%）與 < solved 的比例（超過 X% 的人）。"""
    top = sum(v for k, v in dist.items() if k >= solved)
    beats = sum(v for k, v in dist.items() if k < solved)
    return {"top": round(top, 1), "beats": round(beats, 1)}
