"""編輯行為：網頁編輯器只記「次數與時間」，不記你打了什麼字（隱私）。從這些數字判斷你可能卡在哪裡。

記錄的欄位（每次按「執行」時一併送出）：edits（輸入事件次數）、deletes（其中刪除的次數）、pastes（貼上次數）、
active_s（有輸入的秒數）、max_pause_s（最長一次停頓）、since_open_s（從開啟這題到現在）、runs（這次開啟後執行幾次）。
判斷規則很粗糙：只是提醒「你也許該換個方法」，不是診斷。
"""
from __future__ import annotations

from typing import Any, Dict, List

FIELDS = ("edits", "deletes", "pastes", "active_s", "max_pause_s", "since_open_s", "runs")


def clean(raw: Any) -> Dict[str, float]:
    """只收數字、限制範圍；其他欄位一律丟掉。"""
    out: Dict[str, float] = {}
    if not isinstance(raw, dict):
        return out
    for k in FIELDS:
        v = raw.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 1e7:
            out[k] = float(v)
    return out


def patterns(b: Dict[str, float], failed_runs: int = 0) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    edits, deletes = b.get("edits", 0), b.get("deletes", 0)
    runs = b.get("runs", 0)
    if edits >= 40 and deletes / max(edits, 1) > 0.45 and failed_runs >= 2:
        out.append({"id": "thrash", "msg": "你一直在改了又刪，而且還沒通過：先停下來，用紙筆手算範例、寫下每一步的規則，再回來寫程式。"})
    if b.get("max_pause_s", 0) >= 300 and edits < 30:
        out.append({"id": "stuck-reading", "msg": "中間停了很久而且打的字很少，可能卡在理解題意或不知道怎麼開始：看範例逐步推演，或用 L0 提示只釐清題意。"})
    if runs >= 5 and edits / max(runs, 1) < 8 and failed_runs >= 4:
        out.append({"id": "guess-and-run", "msg": "每次只改一點就執行、連續失敗：這種試誤很耗時間。先預測「這個輸入應該得到什麼」再執行，預測錯的地方就是你理解有落差的地方。"})
    if b.get("pastes", 0) >= 1 and edits < 15 and b.get("since_open_s", 1e9) < 120:
        out.append({"id": "pasted", "msg": "這題的程式幾乎是整段貼上的：如果是自己的舊解，OK；如果是別人的，之後的『無提示重寫』會很吃力，建議自己重打一次。"})
    if b.get("since_open_s", 0) > 3600 and b.get("active_s", 0) < 300:
        out.append({"id": "idle-open", "msg": "這題開了很久但幾乎沒動手：有時只是離開了，但如果是在發呆，先做 5 分鐘能做的最小一步（寫輸入、印出範例答案）。"})
    return out


def summary(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    n = 0
    for ev in events:
        if ev.get("kind") != "beh":
            continue
        n += 1
        for p in patterns({k: ev.get(k, 0) for k in FIELDS}, int(ev.get("failed_runs", 0))):
            counts[p["id"]] = counts.get(p["id"], 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])
    return {"samples": n, "patterns": [{"id": k, "count": v} for k, v in top]}
