"""課程：126 週、52 個單元。進度、時程對照與檢核（gate）。"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import bank as bank_mod
from . import mock, pastexams
from .store import Workspace

DATA = Path(__file__).parent / "data" / "course.json"


def load() -> Dict[str, Any]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def get_unit(course: Dict[str, Any], n: int) -> Optional[Dict[str, Any]]:
    return next((u for u in course["units"] if u["n"] == n), None)


def current_unit(ws: Workspace, course: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return get_unit(course, ws.state()["course"]["unit"])


def week_range(u: Dict[str, Any]) -> Tuple[int, int]:
    return u["start"], u["start"] + u["weeks"] - 1


def expected_week(start: dt.date, today: dt.date) -> int:
    return max((today - start).days // 7 + 1, 1)


def expected_unit(course: Dict[str, Any], week: int) -> Dict[str, Any]:
    for u in course["units"]:
        if week <= week_range(u)[1]:
            return u
    return course["units"][-1]


def passed_in_lang(events: List[dict], pid: str, lang: str) -> bool:
    return any(e["kind"] == "test" and e["problem"] == pid and e["verdict"] == "AC" and e.get("lang", "py") == lang
               for e in events)


def unit_progress(ws: Workspace, u: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """回傳（已用該單元語言通過的 drills, 尚未通過的 drills）。"""
    ev = ws.events()
    done = [d for d in u["drills"] if passed_in_lang(ev, d, u["lang"])]
    return done, [d for d in u["drills"] if d not in done]


def start_gate(ws: Workspace, bank: Dict[str, dict], course: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
    g = u["gate"]
    if not g:
        raise ValueError("這個單元沒有檢核（階段最後一個單元是實際報考）。用 cpe course next 直接結束。")
    _, todo = unit_progress(ws, u)
    if todo:
        lang = "C++" if u["lang"] == "cpp" else "Python"
        raise ValueError(f"還有必做練習沒通過（{lang}）：{', '.join(todo)}。先完成再來檢核。")
    gate_info = {"unit": u["n"], "need": g["need"]}
    stage_cap = max(u["stage"], 1)
    if g["type"] == "set":
        for pid in g["problems"]:
            bank_mod.install_drill(ws, pid)
            if not any((ws.tests / pid).glob("*.in")):
                raise ValueError(f"{pid} 沒有測資。先 cpe import {pid} <題目檔> 加入範例")
        exam = mock.start(ws, bank, "gate", ids=g["problems"], minutes=g["minutes"], lang=g["lang"], gate=gate_info)
    else:
        avail = {pid: p for pid, p in bank.items() if bank_mod.is_drill(pid) or any((ws.tests / pid).glob("*.in"))}
        exam = mock.start(ws, avail, g["kind"], gate=gate_info, max_stage=stage_cap,
                          lang="cpp" if u["lang"] == "cpp" else "py")
        for pid in exam["problems"]:
            bank_mod.install_drill(ws, pid)
    return exam


def advance(ws: Workspace, course: Dict[str, Any], n: int) -> Optional[Dict[str, Any]]:
    st = ws.state()
    if n not in st["course"]["done"]:
        st["course"]["done"].append(n)
    nxt = get_unit(course, n + 1)
    if nxt:
        st["course"]["unit"] = nxt["n"]
        cfg = ws.config()
        cfg["stage"] = nxt["stage"]
        ws.save_config(cfg)
    ws.save_state(st)
    ws.log("unit_done", unit=n)
    return nxt


def goto(ws: Workspace, course: Dict[str, Any], n: int) -> Dict[str, Any]:
    u = get_unit(course, n)
    if not u:
        raise ValueError(f"單元只有 1–{len(course['units'])}")
    st = ws.state()
    st["course"]["unit"] = n
    st["course"]["done"] = sorted(set(st["course"]["done"]) | set(range(1, n)))
    ws.save_state(st)
    cfg = ws.config()
    cfg["stage"] = u["stage"]
    ws.save_config(cfg)
    return u


def evaluate_gate(ws: Workspace, course: Dict[str, Any], summary: Dict[str, Any]) -> Optional[str]:
    """交卷後：若是單元檢核，判斷是否通過並推進。回傳要顯示的訊息。"""
    gate = summary.get("gate")
    if not gate:
        return None
    need, n = gate["need"], gate["unit"]
    if summary["solved"] >= need:
        nxt = advance(ws, course, n)
        if nxt:
            a, _ = week_range(nxt)
            return f"✅ 單元 {n} 檢核通過（{summary['solved']}/{summary['total']}，需 {need}）。下一個：單元 {nxt['n']}《{nxt['title']}》（第 {a} 週起）"
        return f"🎓 單元 {n} 檢核通過——整個課程完成！"
    return (f"❌ 單元 {n} 檢核未通過（{summary['solved']}/{summary['total']}，需 {need}）。"
            "建議：用提示階梯檢討沒做出的題目，24 小時後再 cpe gate。")


def _english(ws: Workspace, pid: str) -> bool:
    """這題能不能用英文題目出（內建練習題有英文版就可以；匯入的題目看文字內容）。"""
    from .service import statement_is_english
    if bank_mod.is_drill(pid) and not (ws.root / "statements" / f"{pid}.txt").exists():
        return bank_mod.has_english(pid)
    for x in ("txt", "md"):
        f = ws.root / "statements" / f"{pid}.{x}"
        if f.exists():
            return statement_is_english(f.read_text(encoding="utf-8", errors="replace"))
    return False


def start_mock(ws: Workspace, bank: Dict[str, dict], kind: str, lang: str = "py", every_stage: bool = False, real: bool = False) -> Dict[str, Any]:
    """模擬考／每週測驗。只會出已有測資的題目（內建練習題，或你匯入過的題）。
    real=True：比照考場，只出有英文題目文字的題（內建練習題有英文版，題目一律用英文顯示）。"""
    cap = 9 if every_stage else max(int(ws.config()["stage"]), 1)
    avail = {pid: p for pid, p in bank.items() if bank_mod.is_drill(pid) or any((ws.tests / pid).glob("*.in"))}
    if real:
        avail = {pid: p for pid, p in avail.items() if _english(ws, pid)}
        need = 7 if kind == "mock" else 3
        if kind == "weekly":                                # 每週重寫只出『已通過』的題：要有足夠的已通過英文題
            done = [pid for pid, sp in ws.state()["problems"].items() if sp.get("first_pass") is not None and pid in avail]
            if len(done) < need:
                raise ValueError(f"『比照考場』的每週重寫需要至少 {need} 題「已通過、且有英文題目文字」的題目，目前只有 {len(done)} 題。")
        if len(avail) < need:
            raise ValueError(f"『比照考場』需要至少 {need} 題「有英文題目文字、也有測資」的題目，目前只有 {len(avail)} 題。"
                             "請先匯入歷屆題目（cpe past statements <資料夾>），或取消『比照考場』。")
        cap = 9
    exam = mock.start(ws, avail, kind, lang=lang, max_stage=cap)
    if real:
        exam["real"] = True                             # 先存旗標，再安裝題目，題目才會用英文
        ws.save_exam(exam)
    for pid in exam["problems"]:
        bank_mod.install_drill(ws, pid)
    return exam


def start_past(ws: Workspace, bank: Dict[str, dict], date: str, lang: str = "py", partial: bool = False) -> Dict[str, Any]:
    """歷屆整場：照原本的題序出同一場的題目，180 分鐘，ICPC 計分，AI／提示鎖定。"""
    data = pastexams.load_all(ws)
    e = next((x for x in data["exams"] if x["date"] == date), None)
    if not e or not e["problems"]:
        raise ValueError(f"沒有 {date} 這場的題目資料。用 cpe past import 匯入，或看 cpe past list。")
    view = pastexams.exam_view(ws, bank, e)
    missing = [p for p in view["problems"] if not p["has_tests"]]
    if missing and not partial:
        raise ValueError(f"{date} 有 {len(missing)} 題還沒有測資：" + "、".join(f"第 {p['order']} 題 {p['title']}" for p in missing)
                         + "。先匯入題目（cpe past statements <資料夾>），或選『只出已有測資的題目』。")
    ids = [p["id"] for p in view["problems"] if p["has_tests"]]
    if not ids:
        raise ValueError("這場一題都還沒有測資，無法開始。")
    return mock.start(ws, bank, "past", ids=ids, minutes=180, lang=lang, past=date)
