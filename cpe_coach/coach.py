"""教練模式：把進度整理成一份可以傳給老師的報告（HTML＋JSON），並匯入老師寫回來的留言。全部是檔案交換，沒有伺服器、沒有帳號。

報告裡只有統計數字與知識點狀態（以及你同意的話，近期的筆記）。**不含你的程式碼、題目文字、金鑰、AI 對話。**
"""
from __future__ import annotations

import html
import json
import time
from pathlib import Path
from typing import Any, Dict, List

from . import bank as bank_mod
from . import errbook, knowledge, planning

MAX_COMMENTS = 50
MAX_LEN = 1000


def build(ws, with_notes: bool = False) -> Dict[str, Any]:
    bank = bank_mod.load_bank(ws)
    m = knowledge.mastery(ws, bank)
    err = errbook.summary(ws.events(), bank)
    data: Dict[str, Any] = {
        "generated": time.strftime("%Y-%m-%d %H:%M", time.localtime(ws.now())), "format": 1,
        "goal": planning.goal_status(ws), "week": planning.report(ws, 7, bank), "month": planning.report(ws, 30, bank),
        "concepts": [{"name": v["name"], "level": v["label"], "p_know": v["p_know"], "retention": v["retention"]} for v in m.values() if v["touched"]],
        "errors": [{"cause": c["cause"], "count": c["count"]} for c in err["causes"][:6]],
        "achievements": [{"name": a["name"]} for a in planning.achievements(ws, bank) if a["unlocked"]],
        "exams": [{"kind": e["kind"], "solved": e["solved"], "total": e["total"], "penalty": e["penalty"], "date": e.get("date")} for e in ws.state()["exams"][-10:]],
        "prediction": planning.score_prediction(ws, bank),
        "comments": comments(ws),
    }
    if with_notes:
        data["notes"] = [{"kind": e["note_kind"], "problem": e.get("problem"), "text": e["text"][:500]} for e in ws.events() if e.get("kind") == "note"][-20:]
    return data


def to_html(d: Dict[str, Any]) -> str:
    esc = html.escape
    rows = lambda items, cols: "".join("<tr>" + "".join(f"<td>{esc(str(x.get(c, '')))}</td>" for c in cols) + "</tr>" for x in items)      # noqa: E731
    w, mth, g = d["week"], d["month"], d["goal"]
    goal = (f"<p>目標：{esc(str(g['target']))} 題，截止 {esc(g['date'])}；已完成 {g['solved']}；{esc(g['message'])}</p>" if g.get("set") else "<p>還沒有設定目標。</p>")
    notes = ""
    if d.get("notes"):
        notes = "<h2>筆記（學生同意附上）</h2><ul>" + "".join(f"<li>[{esc(n['kind'])}] {esc(n['text'])}</li>" for n in d["notes"]) + "</ul>"
    pred = d["prediction"]
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CPE 教練 學習報告</title>
<style>body{{font:15px/1.6 system-ui,"Noto Sans TC",sans-serif;max-width:860px;margin:24px auto;padding:0 16px;color:#1b1f2a}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #d6d9e0;padding:4px 8px;text-align:left}}h2{{margin-top:28px}}.muted{{color:#69708a;font-size:13px}}</style></head>
<body><h1>CPE 教練 學習報告</h1><p class="muted">產生時間 {esc(d['generated'])}。報告只含統計數字與知識點狀態，不含程式碼、題目文字或 AI 對話。</p>
{goal}
<h2>最近 7 天／30 天</h2><table><tr><th></th><th>7 天</th><th>30 天</th></tr>
<tr><td>練習的天數</td><td>{w['active_days']}</td><td>{mth['active_days']}</td></tr><tr><td>新解出的題</td><td>{w['new_solved']}</td><td>{mth['new_solved']}</td></tr>
<tr><td>複習（通過／次數）</td><td>{w['reviews_passed']}/{w['reviews']}</td><td>{mth['reviews_passed']}/{mth['reviews']}</td></tr><tr><td>用了提示</td><td>{w['hints']}</td><td>{mth['hints']}</td></tr></table>
<h2>知識點</h2><table><tr><th>知識點</th><th>層級</th><th>P(會)</th><th>保留率</th></tr>{rows(d['concepts'], ['name', 'level', 'p_know', 'retention'])}</table>
<h2>最常見的錯因</h2><table><tr><th>錯因</th><th>次數</th></tr>{rows(d['errors'], ['cause', 'count'])}</table>
<h2>模擬考</h2><table><tr><th>種類</th><th>答對</th><th>總題數</th><th>罰時</th><th>日期</th></tr>{rows(d['exams'], ['kind', 'solved', 'total', 'penalty', 'date'])}</table>
<h2>落點預測（粗估）</h2><p>預期答對 {pred['expected']} 題；至少 4 題的機率約 {round(100 * pred['p_at_least_4'])}%。<span class="muted">{esc(pred['caveat'])}</span></p>
{notes}<h2>老師的留言</h2><ul>{''.join(f"<li>{esc(c['text'])}（{esc(c.get('from', ''))}）</li>" for c in d['comments']) or '<li class="muted">（還沒有）</li>'}</ul></body></html>"""


def export(ws, out: Path, with_notes: bool = False) -> Dict[str, str]:
    d = build(ws, with_notes)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "cpe-report.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "cpe-report.html").write_text(to_html(d), encoding="utf-8")
    return {"html": str(out / "cpe-report.html"), "json": str(out / "cpe-report.json")}


def import_comments(ws, path: Path) -> int:
    """老師的留言檔：{"from": "王老師", "comments": [{"text": "...", "problem": "d003"（可省略）}]}。只收文字，長度與筆數都有上限。"""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"讀不了留言檔：{e}")
    if not isinstance(data, dict) or not isinstance(data.get("comments"), list):
        raise ValueError('留言檔格式：{"from": "老師", "comments": [{"text": "..."}]}')
    who = str(data.get("from", ""))[:40]
    n = 0
    for c in data["comments"][:MAX_COMMENTS]:
        if isinstance(c, dict) and isinstance(c.get("text"), str) and c["text"].strip():
            prob = c.get("problem") if isinstance(c.get("problem"), str) and len(c["problem"]) <= 40 else None
            ws.log("coach", text=c["text"].strip()[:MAX_LEN], problem=prob, **{"from": who})
            n += 1
    return n


def comments(ws, limit: int = 20) -> List[Dict[str, Any]]:
    return [{"ts": e["ts"], "text": e["text"], "problem": e.get("problem"), "from": e.get("from", "")} for e in ws.events() if e.get("kind") == "coach"][-limit:][::-1]


# ---------- 學習小組：用檔案交換「進度卡」（沒有伺服器、完全自願） ----------
def card(ws, name: str) -> Dict[str, Any]:
    """一張可以傳給同學的進度卡：暱稱、解出幾題、無提示通過幾題、最近 7 天練習幾天、各知識點層級。不含任何題目或程式。"""
    bank = bank_mod.load_bank(ws)
    m = knowledge.mastery(ws, bank)
    st = ws.state()["problems"]
    wk = planning.report(ws, 7, bank)
    return {"format": 1, "kind": "cpe-progress-card", "name": str(name)[:20], "solved": sum(1 for p in st.values() if p.get("first_pass")),
            "clean_solved": len({a["problem"] for a in knowledge.attempts(ws.events()) if a["solved"] and a["clean"]}), "active_days_7": wk["active_days"],
            "concepts": {cid: v["level"] for cid, v in m.items() if v["touched"]}}


def group_table(paths: List[Path]) -> List[Dict[str, Any]]:
    cards = []
    for p in paths:
        try:
            d = json.loads(Path(p).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ValueError(f"讀不了 {p}")
        if not isinstance(d, dict) or d.get("kind") != "cpe-progress-card":
            raise ValueError(f"{p} 不是進度卡")
        cards.append({"name": str(d.get("name", ""))[:20], "solved": int(d.get("solved", 0)), "clean_solved": int(d.get("clean_solved", 0)),
                      "active_days_7": int(d.get("active_days_7", 0)), "concepts": len(d.get("concepts", {}))})
    return sorted(cards, key=lambda c: (-c["clean_solved"], -c["active_days_7"], c["name"]))
