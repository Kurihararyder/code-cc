"""匯出成別的工具看得懂的格式（Anki 卡片、xAPI 學習紀錄），以及隱私：資料清單、加密備份、刪除全部。"""
from __future__ import annotations

import csv
import datetime as dt
import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from . import bank as bank_mod
from . import concepts, lab, notes
from .store import CPE_DIR, Workspace


# ---------- Anki ----------
def anki_tsv(ws, include_quiz: bool = True) -> str:
    """Anki 可以直接匯入的 Tab 分隔文字：欄位 = 正面、背面、標籤。解出過的題目一張卡，概念測驗每題一張。"""
    bank = bank_mod.load_bank(ws)
    st = ws.state()["problems"]
    buf = io.StringIO()
    w0 = csv.writer(buf, delimiter="\t", lineterminator="\n")

    def w_row(cols):                                                  # 欄位裡的換行一律換成 <br>：一張卡一行，Anki 一定讀得進去
        w0.writerow([c.replace("\r", "").replace("\n", "<br>") for c in cols])
    w = type("W", (), {"writerow": staticmethod(w_row)})
    for pid in sorted(p for p, v in st.items() if v.get("first_pass")):
        b = bank.get(pid)
        if not b:
            continue
        cs = concepts.of_problem(b)
        front = f"{pid}　{b.get('title', '')}<br>不看提示，寫出解法的大綱與複雜度。"
        back = "<br>".join(x for x in (b.get("hint_category"), b.get("hint_insight"), (notes.last_outline(ws, pid) or {}).get("text")) if x)
        w.writerow([front, back or "（還沒有內建的提示；寫下你自己的重點）", " ".join(["cpe", *cs])])
    if include_quiz:
        for q in lab.items("quiz"):
            front = q["q"] + (("<pre>" + q["code"] + "</pre>") if q["code"] else "") + "<br>" + "<br>".join(f"{'ABCD'[i]}. {c}" for i, c in enumerate(q["choices"]))
            w.writerow([front, f"{'ABCD'[q['answer']]}。{q['why']}", " ".join(["cpe", "quiz", q["concept"]])])
    return buf.getvalue()


# ---------- xAPI ----------
def xapi(ws, actor_name: str = "learner") -> List[Dict[str, Any]]:
    """每次判題一筆 xAPI statement（actor 用匿名帳號，沒有 email）。可以匯入支援 xAPI 的學習紀錄庫（LRS）。"""
    from .aggregate import anon_id
    actor = {"objectType": "Agent", "name": actor_name, "account": {"homePage": "https://cpe-coach.local", "name": anon_id(ws)}}
    out = []
    for e in ws.events():
        if e.get("kind") != "test" or not e.get("problem") or e.get("verdict") in (None, "SETUP"):
            continue
        ok = e["verdict"] == "AC"
        out.append({"actor": actor, "verb": {"id": "http://adlnet.gov/expapi/verbs/" + ("passed" if ok else "failed"), "display": {"en-US": "passed" if ok else "failed"}},
                    "object": {"objectType": "Activity", "id": f"urn:cpe-coach:problem:{e['problem']}", "definition": {"type": "http://adlnet.gov/expapi/activities/assessment"}},
                    "result": {"success": ok, "response": e["verdict"]}, "timestamp": dt.datetime.fromtimestamp(float(e["ts"]), dt.timezone.utc).isoformat()})
    return out


# ---------- 隱私 ----------
MEANING = {
    "state.json": "每題的進度（次數、第一次通過、複習階段）", "events.jsonl": "每次判題、提示、筆記、錯誤的紀錄（沒有程式碼內容；筆記是你寫的文字）", "config.json": "設定（語言、目標、時限）",
    "vocab.json": "單字本", "custom_problems.json": "你自己加的題目", "past_exams.json": "你匯入的歷屆清單", "reminder.json": "上次提醒的時間", "calibration.json": "難度校準資料",
    "exam.json": "進行中的考試", "chats": "你和 AI 的對話", "backups": "每小時自動留的進度快照", "conflicts": "同步時衝突的另一份檔案", "last_fail": "最近一次失敗的測資"}


def inventory(ws: Workspace) -> Dict[str, Any]:
    rows = []
    for f in sorted(ws.meta.iterdir()):
        size = sum(x.stat().st_size for x in f.rglob("*") if x.is_file()) if f.is_dir() else f.stat().st_size
        rows.append({"name": f.name + ("/" if f.is_dir() else ""), "bytes": size, "meaning": MEANING.get(f.name, "")})
    top = []
    for name in ("solutions", "tests", "statements", "eng", "projects", "exam"):
        d = ws.root / name
        if d.is_dir():
            top.append({"name": name + "/", "bytes": sum(x.stat().st_size for x in d.rglob("*") if x.is_file()), "meaning": "你的解答／測資／題目文字" if name != "eng" else "工程任務"})
    return {"root": str(ws.root), "meta": rows, "other": top,
            "sent_out": "程式不會自己把這些資料送出去。唯一會連網的是：你主動按「問 AI」或提示的 AI 服務（只送你選取的片段與題目）、檢查更新（只問版本號）、匯入 CPE 原題（只下載）。"
                        "金鑰只存在記憶體或你自己的環境變數，不寫進任何檔案。"}


def delete_all(ws: Workspace, confirm: str) -> int:
    """刪除這個工作區的全部學習資料（.cpe、解答、測資、題目文字…）。confirm 必須是工作區資料夾的名稱，避免誤刪。"""
    if confirm != ws.root.name:
        raise ValueError(f"要確認刪除，請把工作區資料夾的名稱 {ws.root.name!r} 當作確認字串。")
    n = 0
    for name in (CPE_DIR, "solutions", "tests", "statements", "eng", "projects", "exam"):
        d = ws.root / name
        if d.is_dir():
            n += sum(1 for x in d.rglob("*") if x.is_file())
            shutil.rmtree(d, ignore_errors=True)
    return n


# ---------- 加密備份（用系統的 openssl；Python 標準函式庫沒有安全的加密） ----------
def _openssl() -> str:
    exe = shutil.which("openssl")
    if not exe:
        raise ValueError("找不到 openssl：加密備份要靠它（macOS 和 Linux 通常有；Windows 可以裝 Git for Windows，它附帶 openssl）。不然就用不加密的備份，自己放在加密的磁碟。")
    return exe


def _openssl_pipe(args, data: bytes, password: str) -> subprocess.CompletedProcess:
    """資料用標準輸入／輸出傳給 openssl，不把檔案路徑交給它：Windows 上 openssl 開不了含中文的檔名（會變成問號），而備份檔名是「CPE進度備份…」。"""
    return subprocess.run([_openssl(), "enc", *args, "-pbkdf2", "-iter", "200000", "-pass", "env:CPE_BACKUP_PW"], input=data, capture_output=True,
                          env=dict(os.environ, CPE_BACKUP_PW=password), timeout=300)


def encrypt_file(src: Path, dest: Path, password: str) -> Path:
    if len(password) < 8:
        raise ValueError("密碼至少 8 個字元")
    p = _openssl_pipe(["-aes-256-cbc", "-salt"], Path(src).read_bytes(), password)
    if p.returncode != 0:
        raise ValueError("加密失敗：" + p.stderr.decode("utf-8", "replace").strip()[:200])
    Path(dest).write_bytes(p.stdout)
    return dest


def decrypt_file(src: Path, dest: Path, password: str) -> Path:
    p = _openssl_pipe(["-d", "-aes-256-cbc"], Path(src).read_bytes(), password)
    if p.returncode != 0:
        raise ValueError("解密失敗：密碼不對，或檔案不是用 cpe export --encrypt 產生的。")
    Path(dest).write_bytes(p.stdout)
    return dest


def encrypted_backup(ws: Workspace, dest: Path, password: str) -> Path:
    from . import backup
    with tempfile.TemporaryDirectory() as d:
        z = backup.export_workspace(ws, Path(d) / "b.zip")
        return encrypt_file(z, dest, password)


def decrypt_to_zip(src: Path, password: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cpe-dec-")) / "b.zip"
    decrypt_file(src, tmp, password)
    return tmp
