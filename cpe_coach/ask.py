"""詢問引擎：學生在題目／程式／測試結果上選一段文字 → 針對那一段發問。

設計重點（從細節來）
1. 每個問題都錨定在選取的那一段，AI 必須『逐字引用』程式或題目，系統驗證引用真的存在，不存在的丟掉並要求重答。
2. 三種模式、各有閘門：explain（解釋詞彙，不算提示）／question（考我這一段，算 L2）／mismatch（預期和實際不同，算 L4）。
3. 新問題要先有嘗試、且上一個問題之後要有新的測試；回覆 AI 的追問不受限。
4. 對錯只由測資決定；AI 只評論『推理』。
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from .judge import AC
from .llm import RULES, LLMClient, LLMError, strip_long_code
from .service import load_failure, solution_file, trunc
from .store import Workspace

KINDS = {
    "explain": {"label": "這是什麼意思？", "level": 0},
    "question": {"label": "考我這一段", "level": 2},
    "mismatch": {"label": "預期和實際不同", "level": 4},
}
SOURCES = ("statement", "code", "output", "trace")
MAX_REPLIES = 10

INQUIRY_RULES = """
# 詢問模式（從細節來）
學生在畫面上選取了一段文字，你只能針對『那一段』說話，並且必須引用證據。

只輸出一個 JSON 物件（不要 markdown 圍欄、不要多餘文字）：
{"type": "predict|locate|counterexample|complexity|explain|feedback",
 "message": "給學生的話，繁體中文，最多 4 句。除了 explain 與 feedback，最後一句必須是一個問題。",
 "evidence": [{"source": "code|statement|output|trace", "line": 行號或null, "quote": "從該來源逐字複製的一小段"}]}

規則：
1. quote 必須是提供內容裡逐字存在的片段（可以只是一個變數名稱或一行）。系統會自動驗證，找不到的引用會被丟棄並要求你重答。至少引用一處。
2. 一次只問一個問題。不要透露修正方式，不要給超過 4 行的程式碼。
3. 模式 explain：只解釋選取的詞或語法的『一般意義』，用與本題無關的小例子（type=explain）。不要把它套到本題的解法上。
4. 模式 question：針對選取的那一段，請學生做以下其中一件事（type 對應）：
   predict=預測某個變數在某一步的值或某個輸出；locate=指出是哪一行造成某個現象；
   counterexample=構造一個會讓這一行出錯的最小輸入；complexity=估算在最大輸入下這段大約執行幾次。
5. 模式 mismatch：根據『預期輸出』與『實際輸出』的第一個差異，問學生那一個差異是哪一行產生的、或要他先手算那一筆。不要直接說答案。
6. 學生回覆你的問題時（type=feedback）：只評論他的『推理』，具體指出他說對的細節與他推錯的細節（要引用他的原話或程式），再用一個更小的問題帶他往前一步。
   絕對不要說「你的程式是對的／錯的」——對錯由測資決定。
7. 若題目有『教師參考』，那是給你自己防止出錯用的，不要直接抄給學生。
""".strip()


class AskDenied(Exception):
    pass


# ---------- 對話紀錄 ----------
def _chat_path(ws: Workspace, pid: str):
    return ws.meta / "chats" / f"{pid}.json"


def load_chat(ws: Workspace, pid: str) -> Dict[str, Any]:
    p = _chat_path(ws, pid)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"threads": []}


def save_chat(ws: Workspace, pid: str, chat: Dict[str, Any]) -> None:
    p = _chat_path(ws, pid)
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(chat, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------- 閘門 ----------
def check_gate(ws: Workspace, p: Dict[str, Any], kind: str, source: str) -> None:
    if kind not in KINDS:
        raise AskDenied("未知的詢問模式")
    if source not in SOURCES:
        raise AskDenied("未知的來源")
    if ws.exam_active():
        raise AskDenied("考試進行中，AI 詢問已鎖定。交卷後再用。")
    if kind == "explain":
        return
    if p["attempts"] < 1:
        raise AskDenied("先自己試一次：寫一版、按『執行測試』之後再來問。")
    if kind == "mismatch" and (p["last_verdict"] is None or p["last_verdict"] == AC):
        raise AskDenied("『預期和實際不同』要在最近一次測試失敗時才能用。")
    cur = p["hint_level"]
    if cur >= KINDS[kind]["level"] - 1 and cur >= 2 and p["attempts_since_hint"] < 1:
        raise AskDenied("你剛問過一個問題。先照它的提示改一版、再按『執行測試』，才能問下一個。（回覆 AI 的追問不受限制。）")


# ---------- 組提示 ----------
def number_lines(code: str) -> str:
    return "\n".join(f"{i:>3}| {ln}" for i, ln in enumerate(code.splitlines(), 1))


def failure_text(f: Optional[Dict[str, Any]]) -> str:
    if not f:
        return ""
    return (f"判題結果：{f['verdict']}\n輸入：\n{trunc(f['input'], 500)}\n預期輸出：\n{trunc(f['expected'], 500)}\n"
            f"實際輸出：\n{trunc(f['actual'], 500) or '（空）'}\n錯誤訊息：{f.get('stderr', '').strip()[-300:]}")


def build_context(ws: Workspace, bank: Dict[str, dict], pid: str, code: str, statement: str) -> Dict[str, str]:
    p = bank.get(pid, {"id": pid, "title": pid, "topic": ""})
    return {"statement": statement, "code": code, "output": failure_text(load_failure(ws, pid)),
            "title": f"{pid} {p.get('title', '')}（主題：{p.get('topic', '')}）",
            "insight": p.get("hint_insight") or ""}


def build_user_message(ctx: Dict[str, str], kind: str, source: str, selection: str, lines: Tuple[Optional[int], Optional[int]],
                       note: str, trace_text: str) -> str:
    parts = [f"[題目] {ctx['title']}"]
    if ctx["statement"]:
        parts.append("[題目敘述]\n" + trunc(ctx["statement"], 3000))
    if ctx["code"].strip():
        parts.append("[學生程式（含行號）]\n" + number_lines(ctx["code"]))
    if ctx["output"]:
        parts.append("[最近一次判題]\n" + ctx["output"])
    if trace_text:
        parts.append("[逐行追蹤（學生剛看過）]\n" + trunc(trace_text, 2500))
    if ctx["insight"]:
        parts.append("[教師參考（不要直接透露）] " + ctx["insight"])
    loc = ""
    if source == "code" and lines[0]:
        loc = f"，第 {lines[0]}" + (f"–{lines[1]}" if lines[1] and lines[1] != lines[0] else "") + " 行"
    parts.append(f"[學生選取] 來源：{source}{loc}\n\"\"\"\n{selection}\n\"\"\"")
    if note:
        parts.append("[學生補充] " + note)
    parts.append(f"[模式] {kind}（{KINDS[kind]['label']}）")
    return "\n\n".join(parts)


# ---------- 解析與驗證 ----------
def parse_reply(raw: str) -> Dict[str, Any]:
    m = re.search(r"\{.*\}", raw, re.S)
    if m:
        try:
            d = json.loads(m.group(0))
            if isinstance(d, dict) and isinstance(d.get("message"), str):
                ev = d.get("evidence") if isinstance(d.get("evidence"), list) else []
                return {"type": str(d.get("type", "")), "message": d["message"].strip(),
                        "evidence": [e for e in ev if isinstance(e, dict)], "parsed": True}
        except json.JSONDecodeError:
            pass
    return {"type": "", "message": raw.strip(), "evidence": [], "parsed": False}


def _norm(s: str) -> str:
    return " ".join(s.split())


def _find(src: str, quote: str, sources: Dict[str, str]):
    """在指定來源找引用；回傳 (ok, 行號或 None)。"""
    text, q = sources.get(src, ""), _norm(quote)
    if len(q) < 2 or not text:
        return False, None
    if src == "code":
        hits = [i for i, ln in enumerate(text.splitlines(), 1) if q in _norm(ln)]
        if hits:
            return True, hits
        return (q in _norm(text)), None            # 跨行引用
    return (q in _norm(text)), None


def verify_evidence(evidence: List[Dict[str, Any]], sources: Dict[str, str]) -> List[Dict[str, Any]]:
    """每筆引用都要逐字出現在提供的內容裡。
    - 程式碼的行號會修正成實際所在行。
    - 模型常把來源標錯（例如把題目文字標成 code）：若在別的來源唯一找到，就更正來源而不是丟掉。"""
    out = []
    for e in evidence:
        src, quote = str(e.get("source", "")), str(e.get("quote", ""))
        item = {"source": src, "quote": quote[:200], "line": e.get("line"), "ok": False}
        ok, hits = _find(src, quote, sources)
        if not ok:
            alts = [(k, _find(k, quote, sources)) for k in sources if k != src]
            alts = [(k, r) for k, r in alts if r[0]]
            if len(alts) == 1:
                src, (ok, hits) = alts[0]
                item["source"], item["relabeled"] = src, True
        if ok:
            item["ok"] = True
            if src == "code" and hits:
                item["line"] = e.get("line") if e.get("line") in hits else hits[0]
            elif src != "code":
                item["line"] = None
        out.append(item)
    return out


# ---------- 主流程 ----------
def ask(ws: Workspace, bank: Dict[str, dict], pid: str, llm: Optional[LLMClient], *, kind: str = "question",
        source: str = "code", selection: str = "", line_start: Optional[int] = None, line_end: Optional[int] = None,
        note: str = "", trace_text: str = "", thread: Optional[str] = None, reply: str = "",
        statement: str = "") -> Dict[str, Any]:
    if llm is None:
        raise AskDenied("沒有設定 API 金鑰。在畫面右上角貼上 OpenAI 金鑰，或設定環境變數 OPENAI_API_KEY。")
    sol = solution_file(ws, pid)
    code = sol.read_text(encoding="utf-8") if sol.exists() else ""
    ctx = build_context(ws, bank, pid, code, statement)
    sources = {"statement": statement, "code": code, "output": ctx["output"], "trace": trace_text}
    chat = load_chat(ws, pid)
    prev_state = None            # 新問題失敗時用來還原提示級別
    code_hash = hashlib.sha1(code.encode("utf-8")).hexdigest()[:10]

    if thread:                                            # 回覆追問
        th = next((t for t in chat["threads"] if t["id"] == thread), None)
        if th is None:
            raise AskDenied("找不到這個對話")
        if ws.exam_active():
            raise AskDenied("考試進行中，AI 詢問已鎖定。")
        if sum(1 for m in th["messages"] if m["role"] == "user") > MAX_REPLIES:
            raise AskDenied(f"這個對話已經來回 {MAX_REPLIES} 次了。去改程式、跑測試，再開新的問題。")
        if not reply.strip():
            raise AskDenied("請輸入你的回答")
        content = "[學生回答]\n" + reply.strip()
        if th["code_hash"] != code_hash:
            content += "\n\n[學生已修改程式，最新版本（含行號）]\n" + number_lines(code)
            th["code_hash"] = code_hash
        if ctx["output"]:
            content += "\n\n[最近一次判題]\n" + ctx["output"]
        th["messages"].append({"role": "user", "content": content, "display": reply.strip()})
    else:                                                 # 新問題
        if not selection.strip():
            raise AskDenied("請先在畫面上選取一段文字")
        st = ws.state()
        p = ws.problem(st, pid)
        check_gate(ws, p, kind, source)
        user = build_user_message(ctx, kind, source, selection[:1500], (line_start, line_end), note, trace_text)
        th = {"id": uuid.uuid4().hex[:8], "kind": kind, "source": source, "selection": selection[:1500],
              "line_start": line_start, "line_end": line_end, "code_hash": code_hash, "created": ws.now(),
              "messages": [{"role": "user", "content": user, "display": selection[:300]}]}
        chat["threads"].append(th)
        prev_state = (p["hint_level"], p["attempts_since_hint"])
        lvl = KINDS[kind]["level"]
        if lvl >= 1 and lvl > p["hint_level"]:      # explain（L0）不算提示，也不重設嘗試計數
            p["hint_level"] = lvl
            p["attempts_since_hint"] = 0
        ws.save_state(st)

    system = RULES + "\n\n" + INQUIRY_RULES
    history = [{"role": m["role"], "content": m["content"]} for m in th["messages"]][-9:]
    try:
        raw = llm.chat(system, history)
        parsed = parse_reply(raw)
        checked = verify_evidence(parsed["evidence"], sources)
        bad = [c for c in checked if not c["ok"]]
        if (bad or not checked) and parsed["parsed"]:     # 要求重答一次
            why = ("你引用的這些在原文中找不到：" + "；".join(f"[{c['source']}] {c['quote']}" for c in bad)) if bad else "你沒有提供任何引用"
            raw2 = llm.chat(system, history + [{"role": "assistant", "content": raw},
                                                {"role": "user", "content": why + "。請只引用逐字存在的內容，重新輸出 JSON。"}])
            parsed2 = parse_reply(raw2)
            checked2 = verify_evidence(parsed2["evidence"], sources)
            if parsed2["parsed"] and checked2 and sum(c["ok"] for c in checked2) >= sum(c["ok"] for c in checked):
                raw, parsed, checked = raw2, parsed2, checked2
    except LLMError as e:
        if not thread:                                    # 呼叫失敗：不留下半成品，也不算提示
            chat["threads"].remove(th)
            st = ws.state()
            q = ws.problem(st, pid)
            q["hint_level"], q["attempts_since_hint"] = prev_state
            ws.save_state(st)
        else:
            th["messages"].pop()
        save_chat(ws, pid, chat)
        raise AskDenied(f"AI 呼叫失敗：{e}")

    message = strip_long_code(parsed["message"], 4)
    good = [c for c in checked if c["ok"]]
    verified = bool(good) and len(good) == len(checked)
    result = {"type": parsed["type"], "message": message, "evidence": checked, "verified": verified,
              "warning": None if (verified or kind == "explain" and good) else "⚠ 這次回答沒有完整可驗證的引用，請半信半疑，並以測試結果為準。"}
    th["messages"].append({"role": "assistant", "content": raw, "display": message, "evidence": checked,
                           "verified": verified, "warning": result["warning"], "type": parsed["type"]})
    save_chat(ws, pid, chat)
    ws.log("ask", problem=pid, ask_kind=th["kind"], source=th["source"], thread=th["id"], reply=bool(thread),
           verified=verified, model=llm.model)
    return {"thread": th["id"], "reply": result, "kind": th["kind"]}
