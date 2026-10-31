"""解題筆記：思路紀錄、回想解法大綱（提取練習）、反思日誌，以及自我解釋的評分。

自我解釋評分有兩種：有設定 AI 金鑰時請 AI 依「題目的關鍵洞察」評分；沒有時用離線規則（關鍵詞涵蓋率），
離線規則只能看你有沒有提到重點，看不懂你說得對不對，所以只當參考。
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

KINDS = ("think", "recall", "reflect", "explain")
MAX_LEN = 4000


def add(ws, kind: str, text: str, problem: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
    if kind not in KINDS:
        raise ValueError("筆記種類要是：" + "、".join(KINDS))
    text = (text or "").strip()
    if not text:
        raise ValueError("內容是空的")
    return ws.log("note", note_kind=kind, problem=problem, text=text[:MAX_LEN], **extra)


def listing(ws, kind: Optional[str] = None, problem: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    rows = [e for e in ws.events() if e.get("kind") == "note" and (kind is None or e.get("note_kind") == kind) and (problem is None or e.get("problem") == problem)]
    return rows[-limit:][::-1]


def last_outline(ws, problem: str) -> Optional[Dict[str, Any]]:
    """這題最近一次寫下的解法大綱（回想練習用：複習前先自己寫，再和上次比對）。"""
    rows = listing(ws, "recall", problem, 1) or listing(ws, "think", problem, 1)
    return rows[0] if rows else None


_STOP = set("的了是在有和與或也都就而及要可以我你他它這那一個如果因為所以但是然後先再用把被從到對於")


def keywords(text: str) -> List[str]:
    """離線用：英文單字（≥3 字母）與中文的 2 字詞（滑動視窗），去掉常見虛詞。"""
    words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", text)]
    for seg in re.findall(r"[一-鿿]+", text):
        for i in range(len(seg) - 1):
            bi = seg[i:i + 2]
            if not (set(bi) & _STOP):
                words.append(bi)
    return list(dict.fromkeys(words))


def score_offline(answer: str, insight: str, category: str = "") -> Dict[str, Any]:
    ref = keywords(insight + " " + category)
    got = set(keywords(answer))
    hit = [w for w in ref if w in got]
    cover = len(hit) / len(ref) if ref else 0.0
    length_ok = len(answer.strip()) >= 30
    score = round(min(1.0, cover * 1.6) * (1.0 if length_ok else 0.6), 2)
    if not length_ok:
        msg = "太短了：用自己的話至少寫幾句，說明『為什麼這樣做』而不只是『做了什麼』。"
    elif score >= 0.6:
        msg = "你提到了關鍵觀念的大部分。"
    elif score >= 0.3:
        msg = "你提到了一部分重點，但還漏了一些；對照下面的關鍵洞察再補充。"
    else:
        msg = "重點好像沒提到；先看關鍵洞察，再試著用自己的話重講一次。"
    return {"mode": "offline", "score": score, "hit": hit[:12], "missed": [w for w in ref if w not in got][:12], "message": msg,
            "note": "離線評分只比對關鍵詞，不理解內容對不對。"}


def score_with_ai(client, answer: str, insight: str, statement: str = "") -> Dict[str, Any]:
    """請 AI 評分。要求只回傳 JSON；解析失敗就丟例外，由呼叫端改用離線評分。"""
    system = ("你是競賽程式的助教。學生用自己的話解釋一題的解法。依『標準的關鍵洞察』評分，只回傳 JSON："
              '{"score": 0到1的小數, "good": ["說對的重點"], "missing": ["漏掉或說錯的重點"], "message": "一句鼓勵加具體建議"}。不要給完整解答。')
    user = f"題目：\n{statement[:1500]}\n\n標準的關鍵洞察：\n{insight}\n\n學生的解釋：\n{answer[:3000]}"
    raw = client.complete(system, user) if hasattr(client, "complete") else client(system, user)
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError("AI 沒有回傳 JSON")
    d = json.loads(m.group(0))
    score = float(d["score"])
    if not 0 <= score <= 1:
        raise ValueError("分數不在 0–1")
    return {"mode": "ai", "score": round(score, 2), "hit": list(d.get("good", []))[:8], "missed": list(d.get("missing", []))[:8], "message": str(d.get("message", ""))[:300],
            "note": "AI 評分，仍可能出錯。"}
