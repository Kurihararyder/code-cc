"""cpe 指令共用的小工具。"""
from __future__ import annotations

import datetime as dt
import time
from typing import Dict, List

from . import course as course_mod
from .llm import detect_client
from .store import Workspace


# ---------- 小工具 ----------
def fmt_ts(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


def fmt_dur(sec: float) -> str:
    sec = int(max(sec, 0))
    h, m = divmod(sec // 60, 60)
    return f"{h} 小時 {m} 分" if h else f"{m} 分"


def start_date(ws: Workspace) -> dt.date:
    s = ws.config().get("start_date")
    return dt.date.fromisoformat(s) if s else dt.date.today()


def today_date(ws: Workspace) -> dt.date:
    return dt.date.fromtimestamp(ws.now())


def effective_stage(ws: Workspace) -> int:
    return max(int(ws.config()["stage"]), 1)


def suggestions(ws: Workspace, bank: Dict[str, dict], limit: int = 3) -> List[dict]:
    """目前單元的下一批練習題（先 drills，再真題）；單元沒有時退回依階段挑題。"""
    c = course_mod.load()
    u = course_mod.current_unit(ws, c)
    st = ws.state()

    def unsolved(pid: str) -> bool:
        sp = st["problems"].get(pid)
        return not (sp and sp["first_pass"] is not None)

    if u:
        _, todo = course_mod.unit_progress(ws, u)
        ids = todo + [a for a in u["anchors"] if unsolved(a)]
        out = [bank[i] for i in ids if i in bank]
        if out:
            return out[:limit]
    eff = effective_stage(ws)
    out = [p for p in bank.values() if p["stage"] <= eff and unsolved(p["id"]) and not p.get("drill")]
    out.sort(key=lambda p: (0 if p["stage"] == eff else 1, p["stage"], p["difficulty"], p.get("number", 0)))
    return out[:limit]


def show_problem(p: dict, hint_new: bool = True) -> None:
    star = "★" * int(p.get("difficulty", 1))
    print(f"  {p['id']:<10} {star:<5} {p['title']}　[{p.get('topic', '')}]")
    if p.get("drill") and hint_new:
        print(f"             cpe new {p['id']}　→ 題目與測資自動安裝")
    elif p.get("url"):
        print(f"             題目：{p['url']}（也可到瘋狂程設／UVA 找）")


def get_llm(ws: Workspace):
    return detect_client(ws.config())


def _read_block(prompt: str) -> str:
    print(prompt + "（貼完後單獨一行輸入 END）")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def print_board(b) -> None:
    print(f"\n計分板：{b['solved']}/{b['total']} 題　罰時 {b['penalty']} 分鐘（錯誤共 {b['wrong']} 次）")
    for r in b["rows"]:
        mark = {"ac": f"✓ 第 {r['ac_min']} 分鐘" + (f"（錯 {r['wrong']}）" if r["wrong"] else ""), "wrong": f"✗ 錯 {r['wrong']} 次", "open": "—"}[r["status"]]
        acc = f"　全國 {r['accuracy']}%" if r["accuracy"] is not None else ""
        print(f"  {r['order']}. {r['id']:<18} {r['title'][:28]:<28} {mark}{acc}")
    if b.get("percentile"):
        print(f"  以目前題數對照歷年分布：前 {b['percentile']['top']}%")
