"""提示階梯：L0 理解題意 → L1 方向 → L2 關鍵觀察 → L3 骨架 → L4 錯誤定位，並用規則擋住『一路按到底』。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from . import srs
from .judge import AC, FAILS, VERDICT_ZH
from .llm import RULES, LLMClient, LLMError, strip_long_code
from .store import Workspace

LEVEL_NAMES = {0: "L0 理解題意", 1: "L1 方向", 2: "L2 關鍵觀察", 3: "L3 虛擬碼骨架", 4: "L4 錯誤定位"}
CODE_LINE_LIMIT = {0: 0, 1: 0, 2: 0, 3: 10, 4: 4}
DISCLAIMER = "（提示可能有誤，請以測資結果為準。）"
GIVEUP_COOLDOWN = 24 * 3600.0


class HintDenied(Exception):
    pass


def check_gate(ws: Workspace, p: Dict[str, Any], level: int) -> None:
    if level not in LEVEL_NAMES:
        raise HintDenied("提示級別只有 0–4")
    if ws.exam_active():
        raise HintDenied("考試進行中，禁止使用提示。交卷後再用：cpe mock finish")
    cur = p["hint_level"]
    if level <= cur:
        return                                  # 回頭重看已解鎖的級別，免費
    if level > max(cur, 0) + 1:
        where = "還沒用過提示，請從 L0 或 L1 開始" if cur < 0 else f"你現在在 {LEVEL_NAMES[cur]}，下一步是 L{cur + 1}"
        raise HintDenied(f"要一級一級來：{where}")
    if level == 0:
        return
    if p["attempts_since_hint"] < 1:
        raise HintDenied("先自己試一次：改好你的想法後執行 cpe test，再回來要下一級提示")
    if level == 4 and (p["last_verdict"] is None or p["last_verdict"] == AC):
        raise HintDenied("L4 是用來定位錯誤的：你的最近一次提交要是失敗的才有東西可以看")


def _statement(ws: Workspace, pid: str) -> str:
    for ext in ("md", "txt"):
        f = ws.root / "statements" / f"{pid}.{ext}"
        if f.exists():
            return f.read_text(encoding="utf-8")
    return ""


def static_hint(problem: Dict[str, Any], level: int, last_failure: Optional[Dict[str, Any]]) -> Optional[str]:
    if level == 0:
        return ("題意檢查清單（請用自己的話回答，寫在註解裡）：\n"
                "  1. 輸入長什麼樣？有幾組？怎麼知道結束（EOF／特殊結尾／第一行是組數）？\n"
                "  2. 輸出長什麼樣？有沒有固定的標題、空行、小數位數？\n"
                "  3. 數值範圍多大？會不會超過 10^5？需要擔心超時嗎？\n"
                "  4. 最小的輸入是什麼？有沒有『空』或『只有一個元素』的情況？")
    if level == 1:
        return problem.get("hint_category")
    if level == 2:
        if problem.get("hint_insight"):
            return problem["hint_insight"]
        if problem.get("unverified"):
            return ("這題沒有內建的關鍵觀察。回頭看 L1 的分類，想想這一類題的標準模板；"
                    "把題目的限制範圍寫下來，反推可行的複雜度。")
        return None
    if level == 3:
        return ("（沒有設定 AI 金鑰，改用自助骨架法）請在檔案開頭用註解寫出三段：\n"
                "  # 1. 讀入：每組資料如何讀？\n  # 2. 處理：L2 那句關鍵觀察要變成哪幾個步驟？用哪個資料結構？\n"
                "  # 3. 輸出：格式細節（空行、小數位）\n再把每一段翻成程式。")
    if level == 4 and last_failure:
        v = last_failure["verdict"]
        tips = {
            "WA": "用範例測資手算，並找出第一個和預期不同的輸出行；常見原因：邊界值、初始值、off-by-one。",
            "PE": "內容對了但空白／換行不同：檢查行尾空白、組與組之間的空行、小數位數。",
            "TLE": "估算複雜度：n 多大？有沒有巢狀迴圈可用前綴和／排序／dict 取代？輸入有用 sys.stdin 嗎？",
            "RE": "看 traceback 的最後一行：IndexError → 邊界；ValueError → 輸入格式；RecursionError → 改迴圈或調高遞迴上限。",
            "CE": "語法錯誤：看錯誤訊息所指的那一行（以及它的上一行）。",
        }
        return tips.get(v)
    return None


def build_user_prompt(problem: Dict[str, Any], level: int, statement: str, code: str,
                      failure: Optional[Dict[str, Any]]) -> str:
    parts = [f"題目：{problem['id']} {problem.get('title', '')}（主題：{problem.get('topic', '')}）",
             f"學生現在要求：{LEVEL_NAMES[level]}。只能給這一級的內容。"]
    if statement:
        parts.append("題目敘述：\n" + statement)
    if problem.get("hint_insight"):
        parts.append("教師參考（不要直接照抄給學生，用來避免你自己出錯）：" + problem["hint_insight"])
    if code.strip():
        parts.append("學生目前的程式：\n```python\n" + code.rstrip() + "\n```")
    if failure:
        f = failure
        parts.append(f"最近一次失敗：{VERDICT_ZH.get(f['verdict'], f['verdict'])}\n"
                     f"輸入：\n{f['input'][:600]}\n預期輸出：\n{f['expected'][:600]}\n實際輸出：\n{f['actual'][:600]}\n"
                     f"錯誤訊息：{f.get('stderr', '')[-300:]}")
    return "\n\n".join(parts)


def request_hint(ws: Workspace, pid: str, level: int, problem: Dict[str, Any], code: str,
                 failure: Optional[Dict[str, Any]], llm: Optional[LLMClient]) -> Dict[str, Any]:
    """通過閘門後取得提示並記錄。回傳 {text, source}。"""
    st = ws.state()
    p = ws.problem(st, pid)
    check_gate(ws, p, level)

    text, source = None, "static"
    needs_ai = level in (3, 4)
    if llm is not None and (needs_ai or level == 0):
        try:
            raw = llm.complete(RULES, build_user_prompt(problem, level, _statement(ws, pid), code, failure))
            text, source = strip_long_code(raw, CODE_LINE_LIMIT[level]), "llm"
        except LLMError as e:
            text = None
            ws.log("hint_llm_error", problem=pid, level=level, error=str(e))
    if text is None:
        text = static_hint(problem, level, failure)
    if not text:
        raise HintDenied("這題沒有內建的這一級提示。你可以用 cpe add 補上，或設定 AI 金鑰取得 AI 提示")
    if source == "llm":
        text += "\n" + DISCLAIMER

    if level > p["hint_level"]:
        p["hint_level"] = level
        p["attempts_since_hint"] = 0
    ws.save_state(st)
    ws.log("hint", problem=pid, level=level, source=source)
    return {"text": text, "source": source}


def giveup(ws: Workspace, pid: str) -> float:
    if ws.exam_active():
        raise HintDenied("考試進行中不能放棄看解法")
    st = ws.state()
    p = ws.problem(st, pid)
    if p["giveup_at"] is None:
        p["giveup_at"] = ws.now()
    ws.save_state(st)
    ws.log("giveup", problem=pid)
    return p["giveup_at"] + GIVEUP_COOLDOWN


def solution_unlocked_at(p: Dict[str, Any]) -> Optional[float]:
    return None if p["giveup_at"] is None else p["giveup_at"] + GIVEUP_COOLDOWN


def explain_solution(problem: Dict[str, Any], code: str, statement: str, llm: LLMClient) -> str:
    system = (RULES + "\n\n# 現在是特例\n學生已放棄並完成 24 小時冷卻。請完整講解解法的思路與複雜度，"
              "可附關鍵片段（≤ 15 行）。講解完提醒他：之後必須關掉講解、從空白檔無提示重寫一次。")
    user = f"題目：{problem['id']} {problem.get('title', '')}（主題：{problem.get('topic', '')}）\n"
    if statement:
        user += "題目敘述：\n" + statement + "\n"
    if problem.get("hint_insight"):
        user += "教師參考：" + problem["hint_insight"] + "\n"
    if code.strip():
        user += "學生目前的程式：\n```python\n" + code.rstrip() + "\n```\n"
    user += "請完整講解這題的解法。"
    return strip_long_code(llm.complete(system, user), 15)


def solution_text(ws: Workspace, pid: str, problem: Dict[str, Any], code: str, llm: Optional[LLMClient]) -> Dict[str, Any]:
    """放棄並冷卻 24 小時後才能看解法講解。回傳 {text, source}。"""
    st = ws.state()
    p = ws.problem(st, pid)
    unlock = solution_unlocked_at(p)
    if ws.exam_active():
        raise HintDenied("考試進行中不能看解法")
    if unlock is None:
        raise HintDenied("還沒放棄。真的卡住請先按『放棄這題』（冷卻 24 小時）")
    if ws.now() < unlock:
        left = int((unlock - ws.now()) // 60)
        raise HintDenied(f"冷卻中，還要等 {left // 60} 小時 {left % 60} 分")
    if llm is None:
        text = ("沒有設定 AI 金鑰。可以看這題的關鍵觀察，再去查社群題解：\n"
                + (problem.get("hint_insight") or "（此題沒有內建解說）"))
        source = "static"
    else:
        try:
            text = explain_solution(problem, code, _statement(ws, pid), llm)
            source = "llm"
        except LLMError as e:
            raise HintDenied(f"AI 講解失敗：{e}")
    ws.log("solution_viewed", problem=pid)
    return {"text": text, "source": source}
