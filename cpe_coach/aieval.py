"""AI 詢問系統評測：用真實的模型跑一組情境，量化『它到底守不守規矩』。

我沒有拿真的 API 金鑰測過詢問系統，所以把測法做成工具：你用自己的金鑰跑一次（約 20～40 次呼叫），
把報告貼回來，就能知道真實模型的 JSON 遵守率、引用驗證率、費用，並據此調整提示詞。

做法：在暫存工作區裡裝內建練習題、寫入一份『有 bug 的學生程式』、真的跑判題拿到失敗輸出，再依序問
explain／question／mismatch，question 與 mismatch 之後再用一個故意不完整的回答測試『回饋』。
不會動到你的進度。
"""
from __future__ import annotations

import re
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import ask as ask_mod
from . import bank as bank_mod
from . import service
from .llm import REMOVED, LLMClient, LLMError
from .store import Workspace

# (題號, 有 bug 的程式, 錯誤那一行裡的關鍵字, 學生對追問的回答（故意只對一半）)
SCENARIOS: List[Tuple[str, str, str, str]] = [
    ("d001", 'print("Hello " + input() + "!")\n', 'print("Hello', "我猜是少了逗號？"),
    ("d003", "w, h = map(int, input().split())\nprint(w * h, w + h)\n", "w + h", "我覺得周長算錯了。"),
    ("d005", "n = int(input())\nprint('odd' if n % 2 == 1 else 'even')\n", "n = int(input())", "好像只讀了一行？"),
    ("d009", "import sys\nfor line in sys.stdin:\n    n = int(line)\n    print(sum(range(1, n)))\n", "range(1, n)", "range 的右界我不太確定。"),
    ("d010", "import sys\nfor line in sys.stdin:\n    n = int(line)\n    r = 1\n    for i in range(1, n):\n        r *= i\n    print(r)\n", "range(1, n)", "應該是少乘了 n。"),
    ("d013", "import sys\nfor line in sys.stdin:\n    print(int(line.strip()[::-1]))\n", "[::-1]", "負號會跑到後面吧。"),
    ("d014", "import sys\nfor line in sys.stdin:\n    print(sum(1 for c in line if c in 'aeiou'))\n", "'aeiou'", "大小寫的問題嗎？"),
    ("d018", "n = int(input())\na = input().split()\nprint(' '.join(sorted(a)))\n", "sorted(a)", "sorted 是照字串排的？"),
    ("d052", "n = int(input())\na = sorted(map(int, input().split()))\nprint(sum(a[:2]))\n", "sum(a[:2])", "只合併了一次。"),
    ("d047", "import bisect\nn, q = map(int, input().split())\na = list(map(int, input().split()))\nprint(*[bisect.bisect_right(a, x) + 1 for x in map(int, input().split())])\n", "bisect_right", "是不是該用 bisect_left？"),
]
KINDS = ("explain", "question", "mismatch")
EXPLAIN_WORDS = ("EOF", "stdin", "gcd", "字典序", "迴文", "前綴", "取餘數", "range", "split", "遞增", "子序列")


def _sentences(text: str) -> int:
    return len([s for s in re.split(r"[。！？!?\n]+", text) if s.strip()])


def _cjk_ratio(text: str) -> float:
    cjk = len(re.findall(r"[㐀-鿿]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return cjk / max(1, cjk + latin)


_VERDICT_CLAIM = re.compile(r"(你的|這份|這段)?(程式|程式碼|解答)[^。！？\n]{0,8}(是對的|沒有問題|沒問題|有問題|是錯的|寫錯了|正確|不正確)")


def message_checks(kind: str, msg: str) -> Dict[str, bool]:
    """依 INQUIRY_RULES 逐條檢查（只檢查機器能判斷的部分）。"""
    return {
        "ends_with_question": True if kind == "explain" else msg.strip().endswith(("?", "？")),
        "at_most_4_sentences": _sentences(msg) <= 4,
        "no_long_code": REMOVED not in msg,
        "no_correctness_claim": not _VERDICT_CLAIM.search(msg),
        "traditional_chinese": _cjk_ratio(msg) >= 0.3,
    }


def build_scenarios(ws: Workspace, bank: Dict[str, dict], limit: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    """裝題、寫入有 bug 的程式、真的跑判題。沒有失敗的情境會被略過（並回報）。"""
    out, skipped = [], []
    for pid, code, key, answer in SCENARIOS:
        if len(out) >= limit:
            break
        if not bank_mod.is_drill(pid):
            skipped.append(f"{pid}：不是內建題")
            continue
        bank_mod.install_drill(ws, pid)
        ws.solutions.mkdir(exist_ok=True)
        f = service.solution_file(ws, pid)
        f.write_text(code, encoding="utf-8")
        res = service.run_test(ws, pid)
        if res["verdict"] == "AC" or res.get("setup_error"):
            skipped.append(f"{pid}：這份有 bug 的程式竟然通過（{res['verdict']}），略過")
            continue
        out.append({"pid": pid, "code": code, "key": key, "answer": answer, "verdict": res["verdict"]})
    return out, skipped


def pick_selection(kind: str, ws: Workspace, sc: Dict[str, Any], statement: str) -> Dict[str, Any]:
    pid, code = sc["pid"], sc["code"]
    if kind == "explain":
        body = [ln for ln in statement.splitlines() if ln.strip() and not ln.startswith(("#", "**"))]
        word = next((w for w in EXPLAIN_WORDS if w in statement), None) or (body[0][:14] if body else "輸入")
        return {"source": "statement", "selection": word, "line_start": None, "line_end": None}
    if kind == "mismatch":
        f = ask_mod.load_failure(ws, pid) or {}
        actual = (f.get("actual") or "").strip().splitlines()
        return {"source": "output", "selection": (actual[0] if actual else (f.get("expected") or "x").strip().splitlines()[0])[:80], "line_start": None, "line_end": None}
    for i, ln in enumerate(code.splitlines(), 1):
        if sc["key"] in ln:
            return {"source": "code", "selection": ln.strip(), "line_start": i, "line_end": i}
    first = code.splitlines()[0]
    return {"source": "code", "selection": first, "line_start": 1, "line_end": 1}


def run_eval(llm: LLMClient, n: int = 24, kinds: Tuple[str, ...] = KINDS, replies: bool = True,
             price_in: Optional[float] = None, price_out: Optional[float] = None,
             progress: Optional[Callable[[str], None]] = None, workdir: Optional[Path] = None) -> Dict[str, Any]:
    say = progress or (lambda s: None)
    turns: List[Dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="cpe-eval-") as td:
        ws = Workspace.create(Path(workdir or td), "2026-01-05")
        bank = bank_mod.load_bank(ws)
        scenarios, skipped = build_scenarios(ws, bank, max(1, (n + len(kinds) - 1) // len(kinds)))
        plan = [(sc, k) for sc in scenarios for k in kinds][:n]
        for idx, (sc, kind) in enumerate(plan, 1):
            pid = sc["pid"]
            # 每題每種問法都從乾淨狀態開始（避免閘門互相擋住）：重設這題的提示紀錄與對話
            st = ws.state()
            p = ws.problem(st, pid)
            p["hint_level"], p["attempts_since_hint"] = -1, 1
            ws.save_state(st)
            ask_mod.save_chat(ws, pid, {"threads": []})
            sel = pick_selection(kind, ws, sc, service.statement_for(ws, pid))
            say(f"[{idx}/{len(plan)}] {pid} {kind}")
            t = {"pid": pid, "kind": kind, "selection": sel["selection"], "source": sel["source"]}
            try:
                r = ask_mod.ask(ws, bank, pid, llm, kind=kind, statement=service.statement_for(ws, pid), **sel)
                rep = r["reply"]
                t.update(ok=True, parsed=rep.get("parsed", True), verified=rep["verified"], type=rep["type"], message=rep["message"],
                         evidence=[{k: e[k] for k in ("source", "quote", "ok") if k in e} | ({"relabeled": True} if e.get("relabeled") else {}) for e in rep["evidence"]],
                         usage=rep.get("usage", {}), checks=message_checks(kind, rep["message"]))
                if replies and kind != "explain":
                    r2 = ask_mod.ask(ws, bank, pid, llm, thread=r["thread"], reply=sc["answer"], statement=service.statement_for(ws, pid))
                    rep2 = r2["reply"]
                    t["reply_turn"] = {"verified": rep2["verified"], "type": rep2["type"], "message": rep2["message"], "usage": rep2.get("usage", {}),
                                       "checks": message_checks("feedback", rep2["message"])}
            except (ask_mod.AskDenied, LLMError) as e:
                t.update(ok=False, error=str(e)[:300])
            turns.append(t)
    return summarize(llm, turns, skipped, price_in, price_out)


def _rate(xs: List[bool]) -> Optional[float]:
    return round(sum(xs) / len(xs), 3) if xs else None


def summarize(llm: LLMClient, turns: List[Dict[str, Any]], skipped: List[str], price_in: Optional[float], price_out: Optional[float]) -> Dict[str, Any]:
    first = [t for t in turns if t.get("ok")]
    replies = [t["reply_turn"] for t in first if t.get("reply_turn")]
    allv = first + replies
    use = [t["usage"] for t in allv if t.get("usage")]
    tin = sum(u.get("tokens_in", 0) for u in use)
    tout = sum(u.get("tokens_out", 0) for u in use)
    secs = [u.get("seconds", 0.0) for u in use if u.get("calls")]
    checks: Dict[str, List[bool]] = {}
    for t in allv:
        for k, v in t["checks"].items():
            checks.setdefault(k, []).append(v)
    ev = [e for t in first for e in t["evidence"]]
    cost = None
    if price_in is not None and price_out is not None:
        cost = round(tin / 1e6 * price_in + tout / 1e6 * price_out, 4)
    s = {
        "model": llm.model, "provider": llm.provider, "asks": len(turns), "failed_calls": len(turns) - len(first), "replies": len(replies),
        "json_parsed_rate": _rate([bool(t["parsed"]) for t in first]),
        "all_quotes_verified_rate": _rate([bool(t["verified"]) for t in first]),
        "feedback_verified_rate": _rate([bool(r["verified"]) for r in replies]),
        "quote_ok_rate": _rate([bool(e["ok"]) for e in ev]),
        "relabeled_quotes": sum(1 for e in ev if e.get("relabeled")),
        "retry_rate": _rate([u.get("calls", 1) > 1 for u in use]),
        "rule_checks": {k: _rate(v) for k, v in checks.items()},
        "tokens_in": tin, "tokens_out": tout, "tokens_per_ask": round((tin + tout) / max(1, len(use))),
        "seconds_mean": round(statistics.mean(secs), 2) if secs else None,
        "seconds_p95": round(sorted(secs)[int(0.95 * (len(secs) - 1))], 2) if secs else None,
        "cost_usd_estimate": cost, "skipped_scenarios": skipped,
        "errors": sorted({t["error"] for t in turns if not t.get("ok")})[:3],
    }
    s["advice"] = advise(s)
    return {"summary": s, "turns": turns, "created": time.strftime("%Y-%m-%d %H:%M:%S")}


def advise(s: Dict[str, Any]) -> List[str]:
    out = []
    if s["asks"] == 0 or s["asks"] == s["failed_calls"]:
        return ["沒有任何一次成功的呼叫：先用『設定 → 測試連線』確認金鑰、模型名稱與網路。"]
    if (s["json_parsed_rate"] or 0) < 0.95:
        out.append("JSON 遵守率偏低：這個模型常不照格式輸出。可以換用支援 JSON 模式的模型，或在 tutor_rules.md 加強格式說明。")
    if (s["all_quotes_verified_rate"] or 0) < 0.8:
        out.append("引用驗證率偏低：模型常引用不存在的文字。檢查 quote_ok_rate；若 relabeled_quotes 很多，是模型常把來源標錯（系統會自動更正，不影響可信度）。")
    for k, label in (("ends_with_question", "沒有以問題結尾"), ("at_most_4_sentences", "超過 4 句"), ("no_long_code", "貼出過長的程式碼"),
                     ("no_correctness_claim", "直接評論程式對錯"), ("traditional_chinese", "沒有用繁體中文")):
        v = s["rule_checks"].get(k)
        if v is not None and v < 0.9:
            out.append(f"規則遵守不佳：{label}的比例偏高（遵守率 {v:.0%}）。")
    if s["retry_rate"] and s["retry_rate"] > 0.3:
        out.append(f"{s['retry_rate']:.0%} 的詢問需要重答（引用無法驗證）：會讓費用與等待時間增加。")
    if not out:
        out.append("各項指標都在合理範圍。仍請自己讀幾則回答（報告的 turns），確認它真的『從細節問起』而不是在洩漏答案。")
    return out


def format_report(rep: Dict[str, Any]) -> str:
    s = rep["summary"]
    pct = lambda v: "—" if v is None else f"{v:.0%}"
    lines = [f"模型：{s['model']}（{s['provider']}）　詢問 {s['asks']} 次（失敗 {s['failed_calls']}）＋追問回覆 {s['replies']} 次",
             f"JSON 解析成功率：{pct(s['json_parsed_rate'])}",
             f"所有引用都驗證通過的詢問：{pct(s['all_quotes_verified_rate'])}　（追問回覆：{pct(s['feedback_verified_rate'])}）　單筆引用正確率：{pct(s['quote_ok_rate'])}　來源標錯被自動更正：{s['relabeled_quotes']} 筆",
             f"需要重答的比例：{pct(s['retry_rate'])}",
             "規則遵守率：" + "、".join(f"{k} {pct(v)}" for k, v in s["rule_checks"].items()),
             f"用量：輸入 {s['tokens_in']} + 輸出 {s['tokens_out']} tokens（平均每次 {s['tokens_per_ask']}）；耗時平均 {s['seconds_mean']} 秒、p95 {s['seconds_p95']} 秒"]
    if s["cost_usd_estimate"] is not None:
        lines.append(f"費用估算：約 US$ {s['cost_usd_estimate']}（依你給的單價）")
    else:
        lines.append("費用：用 --price-in／--price-out（每百萬 token 的美元單價，以你帳號的實際價格為準）可估算。")
    if s["errors"]:
        lines.append("錯誤訊息：" + "；".join(s["errors"]))
    if s["skipped_scenarios"]:
        lines.append("略過的情境：" + "；".join(s["skipped_scenarios"]))
    lines += ["", "建議："] + ["  • " + a for a in s["advice"]]
    return "\n".join(lines)
