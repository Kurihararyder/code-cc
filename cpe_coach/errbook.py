"""錯誤本：把每次沒通過的原因分成幾種「錯因」，並彙整成你最常犯的錯。

分類是看判題結果、錯誤訊息與預期／實際輸出的差異做的規則判斷（不是 AI），所以有可能分錯；你可以用 cpe err tag 自己改。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

CAUSES = ["越界", "遞迴過深", "讀入超過輸入", "輸入解析", "除以零", "字典沒有鍵", "語法或名稱錯誤", "記憶體不足", "時間複雜度太高",
          "輸出格式", "大小寫", "差一（邊界）", "浮點精度", "沒有輸出", "輸出不完整", "輸出多餘", "邏輯錯誤", "其他執行錯誤", "編譯錯誤"]

ERROR_RULES = [
    (r"IndexError|index out of range|out_of_range|Segmentation|SIGSEGV", "越界"),
    (r"RecursionError|maximum recursion", "遞迴過深"),
    (r"EOFError|EOF when reading", "讀入超過輸入"),
    (r"ValueError: invalid literal|could not convert|not enough values to unpack|too many values to unpack", "輸入解析"),
    (r"ZeroDivisionError|division by zero|SIGFPE", "除以零"),
    (r"KeyError", "字典沒有鍵"),
    (r"SyntaxError|NameError|IndentationError|TypeError|UnboundLocalError|AttributeError", "語法或名稱錯誤"),
    (r"MemoryError|bad_alloc|Cannot allocate", "記憶體不足"),
]


def _tokens(s: str) -> List[str]:
    return s.split()


def _num(t: str) -> Optional[float]:
    try:
        return float(t)
    except ValueError:
        return None


def classify_wrong_answer(expected: str, actual: str) -> str:
    e, a = _tokens(expected), _tokens(actual)
    if not a:
        return "沒有輸出"
    if e == a:
        return "輸出格式"                                   # 內容一樣，只是空白或換行不同
    if [x.lower() for x in e] == [x.lower() for x in a]:
        return "大小寫"
    if len(e) == len(a):
        diffs = [(_num(x), _num(y)) for x, y in zip(e, a) if x != y]
        if diffs and all(x is not None and y is not None for x, y in diffs):
            if all(abs(x - y) <= max(1e-2, 1e-3 * abs(x)) and abs(x - y) > 0 and abs(x - y) < 1 for x, y in diffs) and any("." in t for t in e):
                return "浮點精度"
            if all(abs(abs(x - y) - 1) < 1e-9 for x, y in diffs):
                return "差一（邊界）"
    if len(a) < len(e) and e[:len(a)] == a:
        return "輸出不完整"
    if len(a) > len(e) and a[:len(e)] == e:
        return "輸出多餘"
    return "邏輯錯誤"


def classify(verdict: str, failing: Optional[Dict[str, Any]]) -> Optional[str]:
    """verdict 是判題結果（WA、RE、TLE、MLE、CE…）；failing 是第一個失敗的測資（input、expected、actual、stderr）。AC 回傳 None。"""
    if verdict == "AC":
        return None
    if verdict == "TLE":
        return "時間複雜度太高"
    if verdict == "MLE":
        return "記憶體不足"
    if verdict == "CE":
        return "編譯錯誤"
    stderr = (failing or {}).get("stderr", "") or ""
    if verdict == "RE" or (verdict not in ("WA", "PE") and stderr):
        for pat, cause in ERROR_RULES:
            if re.search(pat, stderr):
                return cause
        return "其他執行錯誤"
    if failing and failing.get("expected") is not None:
        return classify_wrong_answer(failing["expected"], failing.get("actual", ""))
    return "邏輯錯誤"


def summary(events: List[Dict[str, Any]], bank: Optional[Dict[str, dict]] = None, limit: int = 8) -> Dict[str, Any]:
    """錯誤本：各種錯因出現幾次、最近一次、最常出錯的題；「errtag」事件可以覆蓋自動分類。"""
    relabel: Dict[float, str] = {}
    for ev in events:
        if ev.get("kind") == "errtag" and ev.get("target_ts") is not None:
            relabel[float(ev["target_ts"])] = ev["cause"]
    by: Dict[str, Dict[str, Any]] = {}
    per_problem: Dict[str, int] = {}
    recent: List[Dict[str, Any]] = []
    for ev in events:
        if ev.get("kind") != "err":
            continue
        cause = relabel.get(float(ev["ts"]), ev["cause"])
        row = by.setdefault(cause, {"cause": cause, "count": 0, "last": 0.0, "problems": set()})
        row["count"] += 1
        row["last"] = max(row["last"], float(ev["ts"]))
        row["problems"].add(ev["problem"])
        per_problem[ev["problem"]] = per_problem.get(ev["problem"], 0) + 1
        recent.append({"ts": ev["ts"], "problem": ev["problem"], "cause": cause, "verdict": ev.get("verdict"), "case": ev.get("case"), "input": ev.get("input")})
    causes = sorted(by.values(), key=lambda r: -r["count"])
    total = sum(r["count"] for r in causes)
    for r in causes:
        r["problems"] = sorted(r["problems"])
        r["share"] = round(r["count"] / total, 3) if total else 0.0
    worst = sorted(per_problem.items(), key=lambda kv: -kv[1])[:limit]
    return {"total": total, "causes": causes, "recent": recent[-limit:][::-1],
            "worst_problems": [{"id": k, "errors": v, "title": (bank or {}).get(k, {}).get("title", k)} for k, v in worst],
            "advice": ADVICE.get(causes[0]["cause"]) if causes else None}


ADVICE = {
    "越界": "最常見的是索引超出範圍：先想最小與最大的輸入（n=0、n=1、陣列剛好滿）各會存取哪些位置；迴圈上界要寫成 range(n) 還是 range(n+1)。",
    "遞迴過深": "遞迴深度可能很大：改成迴圈或自己用 stack；Python 要 sys.setrecursionlimit，但太深仍會當掉。",
    "讀入超過輸入": "讀的資料比給的多：確認輸入格式（組數、空行、結尾）；不確定時用 sys.stdin.read().split() 一次讀完再逐個取。",
    "輸入解析": "解析輸入失敗：多半是格式想錯（一行幾個數字、有沒有空行、有沒有非數字字元）；先印出讀到的原始字串確認。",
    "除以零": "分母可能是 0：先找出所有除法與取餘，想想輸入為 0 或 1 時會怎樣。",
    "字典沒有鍵": "用 dict.get(key, 預設值) 或 defaultdict，或先檢查 key 是否存在。",
    "語法或名稱錯誤": "多半是打字或縮排錯誤：從第一個錯誤訊息的行號開始看；變數名稱和型別（字串 vs 整數）要一致。",
    "記憶體不足": "資料量比想像大：不要存不需要的東西，避免建立很大的二維陣列。",
    "時間複雜度太高": "先估計 n 的上限和你的迴圈層數；考慮排序、前綴和、雜湊或雙指標能不能把 O(n²) 降下來。",
    "輸出格式": "答案數值對但格式不對：檢查空白、換行、空行、結尾換行與每組之間要不要空一行。",
    "大小寫": "題目要求的大小寫和你的輸出不同：輸出前再讀一次題目的範例。",
    "差一（邊界）": "答案差 1：檢查迴圈的起訖（含不含端點）、range 的上界、計數從 0 還是 1 開始。",
    "浮點精度": "小數誤差：確認要保留幾位小數、用 round 還是格式化輸出；盡量用整數運算避免浮點。",
    "沒有輸出": "程式沒有輸出任何東西：是不是在某個條件下沒走到 print，或輸出被放在迴圈外。",
    "輸出不完整": "少輸出了：多組輸入時是否提早結束？最後一組有沒有輸出？",
    "輸出多餘": "多輸出了：檢查有沒有留下除錯用的 print，或多印了一組。",
    "邏輯錯誤": "輸出看起來合理但是不對：手算題目範例，再自己造一個最小的反例；`cpe fuzz` 可以幫你找出反例。",
    "其他執行錯誤": "執行時發生錯誤：看錯誤訊息的最後一行與行號。",
    "編譯錯誤": "編譯不過：從第一個 error 開始修。",
}
