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
    """一律用 UTF-8 位元組進出（Windows 的文字模式會用系統碼頁，中文會變樣）。"""
    try:
        r = subprocess.run(cmd, cwd=cwd, input=stdin.encode("utf-8"), capture_output=True, timeout=timeout)
        return r.returncode, r.stdout.decode("utf-8", "replace")[:OUT_CAP], r.stderr.decode("utf-8", "replace")[:OUT_CAP], False
    except subprocess.TimeoutExpired as e:
        return -1, (e.stdout or b"").decode("utf-8", "replace")[:OUT_CAP], "", True


# tclsh 的標準輸入輸出預設用系統碼頁（Windows 不是 UTF-8）；放在同一行最前面，不改變程式的行號
TCL_PRELUDE = "fconfigure stdin -encoding utf-8; fconfigure stdout -encoding utf-8; fconfigure stderr -encoding utf-8; "


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
            Path(d, "sol.tcl").write_text(TCL_PRELUDE + code + "\n" + (p.get("harness") or ""), encoding="utf-8")
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


def parse_vcd(text: str, scope: str = "tb", max_points: int = 64) -> Dict[str, Any]:
    """只取指定 scope 的訊號；回傳 {signals:[{name,width}], times:[ps], values:{name:[每個時間點的值]}}（最多 max_points 個有變化的時間點）。"""
    ids: Dict[str, str] = {}
    widths: Dict[str, int] = {}
    stack: List[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        t = lines[i].split()
        if t[:1] == ["$scope"]:
            stack.append(t[2])
        elif t[:1] == ["$upscope"]:
            stack.pop()
        elif t[:1] == ["$var"] and stack == [scope] and t[1] in ("wire", "reg"):
            width, code, name = int(t[2]), t[3], t[4]
            if code not in ids:
                ids[code] = name
                widths[name] = width
        elif t[:1] == ["$enddefinitions"]:
            i += 1
            break
        i += 1
    names = list(dict.fromkeys(ids.values()))
    cur = {n: "x" for n in names}
    times: List[int] = []
    values: Dict[str, List[str]] = {n: [] for n in names}
    now: Optional[int] = None
    dirty = False

    def flush() -> None:
        if now is not None and dirty:
            times.append(now)
            for n in names:
                values[n].append(cur[n])

    for ln in lines[i:]:
        ln = ln.strip()
        if not ln or ln.startswith("$"):
            continue
        if ln[0] == "#":
            flush()
            if len(times) >= max_points:
                now = None
                break
            now, dirty = int(ln[1:]), False
        elif ln[0] in "bB":
            val, code = ln[1:].split()
            if code in ids:
                w = widths[ids[code]]
                cur[ids[code]] = (val if len(val) >= w else (val[0] if val[0] in "xz" else "0") * (w - len(val)) + val)
                dirty = True
        elif ln[0] in "01xzXZ" and ln[1:] in ids:
            cur[ids[ln[1:]]] = ln[0].lower()
            dirty = True
    if now is not None:
        flush()
    return {"signals": [{"name": n, "width": widths[n]} for n in names], "times": times, "values": values}


def wave(pid: str, code: str) -> Dict[str, Any]:
    p = get(pid)
    if p["track"] != "verilog":
        raise ValueError("只有 Verilog 題有波形")
    if not tools()["verilog"]:
        raise ValueError("找不到 iverilog／vvp")
    tb = p["testbench"].replace("module tb;", 'module tb;\n  initial begin $dumpfile("w.vcd"); $dumpvars(0, tb); end', 1)
    with tempfile.TemporaryDirectory() as d:
        Path(d, "user.v").write_text(code, encoding="utf-8")
        Path(d, "tb.v").write_text(tb, encoding="utf-8")
        rc, out, err, to = _run(["iverilog", "-g2012", "-o", "sim", "tb.v", "user.v"], d)
        if rc != 0:
            return {"ok": False, "message": "編譯失敗", "log": (err or out).strip()}
        rc, out, err, to = _run(["vvp", "-n", "sim"], d)
        f = Path(d, "w.vcd")
        if not f.exists():
            return {"ok": False, "message": "沒有產生波形", "log": out}
        return {"ok": True, **parse_vcd(f.read_text(encoding="utf-8", errors="replace"))}
