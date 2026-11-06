"""AI 助教：回答課程單元的問題。用蘇格拉底式引導——講概念、指出該讀的地方、給提示，不直接給整題的完整解答。"""
from __future__ import annotations

from typing import Any, Dict, Optional

from . import course as course_mod
from . import hdl as hdl_mod

SYSTEM = """你是晶片設計學程的助教，用繁體中文回答，語氣簡潔友善。
規則：
1. 先確認學生卡在哪個概念，用一兩個問題引導他自己想到；需要時舉小例子，但**不要直接貼出整題的完整答案程式**。
2. 學生貼了程式與判題輸出時，指出問題發生的位置與原因（例如哪個訊號、哪個週期不符），給下一步要檢查什麼；最多寫出幾行示意，不寫完整解。
3. 回答要對應課程單元的內容；可以指向單元裡列出的閱讀。不確定的事要說不確定，不要編造章節、指令或版本。
4. 回答控制在 300 字以內。
"""


def build_user(track: str, n: int, question: str, pid: Optional[str], code: str, log: str) -> str:
    c = course_mod.load(track)
    u = course_mod.get_unit(c, n)
    if not u:
        raise ValueError(f"單元只有 1–{len(c['units'])}")
    parts = [f"【課程】{track} 軌道，單元 {u['n']}《{u['title']}》\n目標：{u['goal']}\n學習重點：\n- " + "\n- ".join(u["learn"][:6])]
    reads = [r.get("label") or r.get("where") for r in u.get("readings", [])][:5]
    if reads:
        parts.append("單元閱讀：\n- " + "\n- ".join(x for x in reads if x))
    if pid:
        p = hdl_mod.get(pid)
        parts.append(f"【題目 {pid} {p['title']}】\n{p['statement']}")
        if code:
            parts.append("【學生的程式】\n" + code[:8000])
        if log:
            parts.append("【判題輸出】\n" + log[:3000])
    parts.append("【學生的問題】\n" + question)
    return "\n\n".join(parts)


def ask(client: Any, track: str, n: int, question: str, pid: Optional[str] = None, code: str = "", log: str = "") -> Dict[str, Any]:
    question = (question or "").strip()
    if not question:
        raise ValueError("請先輸入問題")
    if len(question) > 2000:
        raise ValueError("問題太長（上限 2000 字）")
    if client is None:
        raise ValueError("AI 助教目前不能使用（沒有金鑰，或管理員尚未開放）。")
    text = client.complete(SYSTEM, build_user(track, n, question, pid, code, log))
    return {"answer": text.strip()}
