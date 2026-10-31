"""多裝置同步與合併：兩台電腦（或電腦與隨身碟）透過「一個共用資料夾」（Dropbox、OneDrive、隨身碟都行）合併學習資料，沒有伺服器、沒有帳號。

做法是離線優先的雙向合併，每台各自完整可用，同步時才把兩邊對起來：
- 事件紀錄（events.jsonl，所有記憶、掌握度、錯誤本、報告都是從它重播算出來的）：兩邊的聯集，依時間排序，內容完全相同的只留一筆。
  所以同步多少次、順序怎麼樣，結果都一樣（可交換、可重複）。
- 進度（state.json）：每一題逐欄位合併（次數取大、第一次通過取最早、最近的紀錄取比較新的那邊）。
- 單字本、你匯入的題目、歷屆清單：以鍵值合併（兩邊都有就保留較新的那筆）。
- 解答、測資、題目文字：只有一邊有就複製過去；兩邊都有而且不同，修改時間較新的留下，另一份存到 .cpe/conflicts/ 讓你自己看，不會悄悄覆蓋。

誠實的限制：合併規則是啟發式的（尤其是進度的逐欄位合併）；兩台機器「同時」改同一題時，結果可能不是你預期的那一邊，所以衝突的檔案才會另存。
不能同時在兩台機器上同步到同一個資料夾（沒有鎖）；同步前先關閉網頁服務，以免它同時寫入。
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import bank as bank_mod
from .store import Workspace

DIRNAME = "cpe-sync"
FILE_DIRS = ("solutions", "tests", "statements")
JSON_FILES = ("vocab.json", "custom_problems.json", "past_exams.json")


def _key(ev: Dict[str, Any]) -> str:
    return json.dumps(ev, sort_keys=True, ensure_ascii=False)


def merge_events(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Dict[str, Dict[str, Any]] = {}
    for ev in list(a) + list(b):
        seen.setdefault(_key(ev), ev)
    return sorted(seen.values(), key=lambda e: (float(e.get("ts", 0)), _key(e)))


def _newness(p: Dict[str, Any]) -> Tuple[float, int]:
    vals = [float(p[k]) for k in ("last_pass", "giveup_at", "first_pass") if p.get(k)]
    return (max(vals) if vals else 0.0, int(p.get("attempts", 0)))


def merge_problem(a: Optional[Dict[str, Any]], b: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if a is None or b is None:
        return json.loads(json.dumps(a or b))
    newer, older = (a, b) if _newness(a) >= _newness(b) else (b, a)
    out = json.loads(json.dumps(newer))
    for k in ("attempts", "passes", "hint_level"):
        if k in a or k in b:
            out[k] = max(a.get(k, 0) or 0, b.get(k, 0) or 0)
    fp = [x for x in (a.get("first_pass"), b.get("first_pass")) if x]
    out["first_pass"] = min(fp) if fp else None
    lp = [x for x in (a.get("last_pass"), b.get("last_pass")) if x]
    out["last_pass"] = max(lp) if lp else None
    return out


def merge_state(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = json.loads(json.dumps(a))
    pa, pb = a.get("problems", {}), b.get("problems", {})
    out["problems"] = {pid: merge_problem(pa.get(pid), pb.get(pid)) for pid in sorted(set(pa) | set(pb))}
    out["eng_done"] = sorted(set(a.get("eng_done", [])) | set(b.get("eng_done", [])), key=str)
    seen = {}
    for e in list(a.get("exams", [])) + list(b.get("exams", [])):
        seen.setdefault(_key(e), e)
    out["exams"] = sorted(seen.values(), key=lambda e: str(e.get("date", "")))
    ca, cb = a.get("course", {"unit": 1, "done": []}), b.get("course", {"unit": 1, "done": []})
    out["course"] = {"unit": max(ca.get("unit", 1), cb.get("unit", 1)), "done": sorted(set(ca.get("done", [])) | set(cb.get("done", [])))}
    return out


def _merge_named(a: Any, b: Any, name: str) -> Any:
    """單字本、自訂題目、歷屆清單：依各自的鍵合併，兩邊都有就保留「較新」的那筆（單字本看 last；其餘以 b（遠端）和 a（本機）相同時沒差、不同時本機優先）。"""
    if name == "vocab.json":
        out = {"words": {}}
        for src in (a or {}, b or {}):
            for w, e in src.get("words", {}).items():
                cur = out["words"].get(w)
                if cur is None:
                    out["words"][w] = e
                else:
                    keep = e if e.get("last", 0) > cur.get("last", 0) else cur
                    merged = dict(keep)
                    merged["count"] = max(cur.get("count", 0), e.get("count", 0))
                    merged["problems"] = sorted(set(cur.get("problems", [])) | set(e.get("problems", [])))
                    merged["first"] = min(cur.get("first", e.get("first", 0)), e.get("first", cur.get("first", 0)))
                    out["words"][w] = merged
        return out
    if name == "custom_problems.json":
        by = {p["id"]: p for p in (b or [])}
        by.update({p["id"]: p for p in (a or [])})
        return [by[k] for k in sorted(by)]
    by = {e["date"]: e for e in (b or {}).get("exams", [])}
    by.update({e["date"]: e for e in (a or {}).get("exams", [])})
    return {"exams": [by[d] for d in sorted(by)]}


def _read_json(p: Path, default: Any) -> Any:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _write_atomic(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, p)


def _events_text(evs: List[Dict[str, Any]]) -> str:
    return "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in evs)


def _read_events(p: Path) -> List[Dict[str, Any]]:
    out = []
    try:
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                try:
                    out.append(json.loads(ln))
                except ValueError:
                    continue
    except OSError:
        pass
    return out


def _local_files(ws: Workspace) -> Dict[str, Path]:
    out: Dict[str, Path] = {}
    for top in FILE_DIRS:
        d = ws.root / top
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*")):
            if not f.is_file() or "__pycache__" in f.parts or f.suffix in (".tmp", ".pyc"):
                continue
            rel = f.relative_to(ws.root).as_posix()
            pid = rel.split("/")[1].split(".")[0] if "/" in rel else ""
            if top in ("tests", "statements") and bank_mod.is_drill(pid):
                continue                                          # 內建練習題可以重新安裝，不用同步
            out[rel] = f
    return out


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sync_folder(ws: Workspace, folder: Path) -> Dict[str, Any]:
    remote = Path(folder) / DIRNAME
    remote.mkdir(parents=True, exist_ok=True)
    report: Dict[str, Any] = {"events_added_local": 0, "events_added_remote": 0, "files_pulled": 0, "files_pushed": 0, "conflicts": []}
    with ws.lock():
        # 事件
        le, re_ = ws.events(), _read_events(remote / "events.jsonl")
        merged = merge_events(le, re_)
        lk, rk = {_key(e) for e in le}, {_key(e) for e in re_}
        report["events_added_local"] = len({_key(e) for e in merged} - lk)
        report["events_added_remote"] = len({_key(e) for e in merged} - rk)
        if report["events_added_local"]:
            _write_atomic(ws.events_path, _events_text(merged))
        _write_atomic(remote / "events.jsonl", _events_text(merged))
        # 進度
        ms = merge_state(ws.state(), _read_json(remote / "state.json", {"problems": {}}))
        ws._write(ws.state_path, ms)
        _write_atomic(remote / "state.json", json.dumps(ms, ensure_ascii=False, indent=1))
        # 設定裡要共用的：目標（取設定時間較晚的）
        lg, rg = ws.config().get("goal"), _read_json(remote / "config.json", {}).get("goal")
        pick = max([g for g in (lg, rg) if g], key=lambda g: g.get("set_at", 0), default=None)
        if pick:
            cfg = ws.config()
            cfg["goal"] = pick
            ws.save_config(cfg)
            _write_atomic(remote / "config.json", json.dumps({"goal": pick}, ensure_ascii=False))
        # 單字本、自訂題目、歷屆清單
        for name in JSON_FILES:
            a = _read_json(ws.meta / name, None)
            b = _read_json(remote / name, None)
            if a is None and b is None:
                continue
            m = _merge_named(a, b, name)
            _write_atomic(ws.meta / name, json.dumps(m, ensure_ascii=False, indent=1))
            _write_atomic(remote / name, json.dumps(m, ensure_ascii=False, indent=1))
        # 檔案
        local = _local_files(ws)
        rdir = remote / "files"
        remote_files = {f.relative_to(rdir).as_posix(): f for f in sorted(rdir.rglob("*")) if f.is_file()} if rdir.is_dir() else {}
        for rel in sorted(set(local) | set(remote_files)):
            lf, rf = local.get(rel), remote_files.get(rel)
            if lf and not rf:
                (rdir / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(lf, rdir / rel)
                report["files_pushed"] += 1
            elif rf and not lf:
                (ws.root / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(rf, ws.root / rel)
                report["files_pulled"] += 1
            elif lf and rf and _sha(lf) != _sha(rf):
                keep_local = lf.stat().st_mtime >= rf.stat().st_mtime
                loser = rf if keep_local else lf
                cdir = ws.meta / "conflicts"
                cdir.mkdir(exist_ok=True)
                saved = cdir / (rel.replace("/", "__") + f".{_sha(loser)[:8]}")
                shutil.copy2(loser, saved)
                winner = lf if keep_local else rf
                shutil.copy2(winner, rf if keep_local else lf)
                report["conflicts"].append({"file": rel, "kept": "本機" if keep_local else "共用資料夾", "other_saved_as": str(saved.relative_to(ws.root))})
        _write_atomic(remote / "manifest.json", json.dumps({"format": 1, "updated": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ws.now())), "events": len(merged)}))
    return report
