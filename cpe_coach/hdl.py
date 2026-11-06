"""Verilog／Tcl 題庫與判題。Verilog 用 iverilog＋vvp 跑自我檢查測試台；Tcl 用 tclsh 對拍標準輸出。

題目資料在 data/hdl_problems.json（由 dev/gen_hdl.py 產生並逐題自我驗證：參考解必須 AC、故意寫錯的版本必須失敗）。
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .store import Workspace

DATA = Path(__file__).parent / "data" / "hdl_problems.json"
TIMEOUT = 30
OUT_CAP = 20000
_cache: Optional[Dict[str, Any]] = None


def load() -> Dict[str, Any]:
    global _cache
    if _cache is None:
        _cache = json.loads(DATA.read_text(encoding="utf-8"))
    return _cache


def get(pid: str) -> Dict[str, Any]:
    p = load().get(pid)
    if not p:
        raise ValueError(f"沒有 {pid} 這題。用 cpe hdl list 看全部。")
    return p


def tools() -> Dict[str, bool]:
    return {"verilog": bool(shutil.which("iverilog") and shutil.which("vvp")), "tcl": bool(shutil.which("tclsh"))}


def listing(ws: Optional[Workspace] = None) -> List[Dict[str, Any]]:
    done = set()
    if ws is not None:
        done = {e["problem"] for e in ws.events() if e["kind"] == "test" and e.get("verdict") == "AC" and e.get("lang") in ("verilog", "tcl")}
    return [{"id": pid, "track": p["track"], "unit": p["unit"], "title": p["title"], "done": pid in done} for pid, p in sorted(load().items())]


def _run(cmd: List[str], cwd: str, stdin: str = "", timeout: int = TIMEOUT):
    try:
        r = subprocess.run(cmd, cwd=cwd, input=stdin, capture_output=True, text=True, timeout=timeout, errors="replace")
        return r.returncode, r.stdout[:OUT_CAP], r.stderr[:OUT_CAP], False
    except subprocess.TimeoutExpired as e:
        return -1, (e.stdout or "")[:OUT_CAP] if isinstance(e.stdout, str) else "", "", True


def judge_verilog(p: Dict[str, Any], code: str) -> Dict[str, Any]:
    if not tools()["verilog"]:
        return {"verdict": "RE", "message": "找不到 iverilog／vvp。請先安裝 Icarus Verilog（見課程單元 1）。", "log": ""}
    for pat, msg in p.get("require", []):
        if len(re.findall(pat, code)) < 2:
            return {"verdict": "WA", "message": msg, "log": ""}
    with tempfile.TemporaryDirectory() as d:
        Path(d, "user.v").write_text(code, encoding="utf-8")
        Path(d, "tb.v").write_text(p["testbench"], encoding="utf-8")
        rc, out, err, to = _run(["iverilog", "-g2012", "-o", "sim", "tb.v", "user.v"], d)
        if rc != 0:
            return {"verdict": "CE", "message": "編譯失敗", "log": (err or out).strip()}
        rc, out, err, to = _run(["vvp", "-n", "sim"], d)
        if to:
            return {"verdict": "TLE", "message": f"模擬超過 {TIMEOUT} 秒（是否有組合迴路或無窮迴圈？）", "log": out}
        out = "\n".join(x for x in out.splitlines() if "$finish called" not in x).strip()
        if "ALL PASS" in out and "MISMATCH" not in out:
            return {"verdict": "AC", "message": "全部通過", "log": out}
        return {"verdict": "WA", "message": "輸出與參考設計不同", "log": out}


def _tcl_norm(s: str) -> str:
    return "\n".join(x.rstrip() for x in s.strip().splitlines())


def judge_tcl(p: Dict[str, Any], code: str) -> Dict[str, Any]:
    if not tools()["tcl"]:
        return {"verdict": "RE", "message": "找不到 tclsh。請先安裝 Tcl。", "log": ""}
    fails: List[str] = []
    with tempfile.TemporaryDirectory() as d:
        for i, t in enumerate(p["tests"], 1):
            Path(d, "sol.tcl").write_text(code + "\n" + (p.get("harness") or ""), encoding="utf-8")
            rc, out, err, to = _run(["tclsh", "sol.tcl"], d, t["in"])
            if to:
                return {"verdict": "TLE", "message": f"第 {i} 筆超過 {TIMEOUT} 秒", "log": ""}
            if rc != 0:
                return {"verdict": "RE", "message": f"第 {i} 筆執行錯誤", "log": err.strip()}
            if _tcl_norm(out) != _tcl_norm(t["out"]):
                fails.append(f"第 {i} 筆\n輸入：\n{t['in'].strip()}\n期望：\n{t['out'].strip()}\n你的輸出：\n{out.strip()}")
                if len(fails) >= 2:
                    break
    if fails:
        return {"verdict": "WA", "message": "輸出與期望不同", "log": "\n\n".join(fails)}
    return {"verdict": "AC", "message": f"{len(p['tests'])} 筆全部通過", "log": ""}


def judge(pid: str, code: str) -> Dict[str, Any]:
    p = get(pid)
    r = judge_verilog(p, code) if p["track"] == "verilog" else judge_tcl(p, code)
    return {"id": pid, **r}


def judge_and_record(ws: Workspace, pid: str, code: str) -> Dict[str, Any]:
    r = judge(pid, code)
    d = ws.root / "hdl"
    d.mkdir(exist_ok=True)
    ext = "v" if get(pid)["track"] == "verilog" else "tcl"
    (d / f"{pid}.{ext}").write_text(code, encoding="utf-8")
    ws.log("test", problem=pid, verdict=r["verdict"], lang=get(pid)["track"])
    return r
