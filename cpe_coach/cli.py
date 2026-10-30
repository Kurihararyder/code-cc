"""cpe 指令列介面：解析參數並分派到 cli_learn／cli_exam／cli_admin 裡的指令。"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import __version__

from . import bank as bank_mod
from . import hints
from .store import Workspace, WorkspaceError
from .cli_learn import cmd_addtest, cmd_course, cmd_external, cmd_fuzz, cmd_gate, cmd_giveup, cmd_hint, cmd_import, cmd_init, cmd_lang, cmd_new, cmd_next, cmd_review, cmd_roadmap, cmd_solution, cmd_stage, cmd_statement, cmd_stress, cmd_test, cmd_today
from .cli_exam import cmd_ai_eval, cmd_calibrate, cmd_eng, cmd_mock, cmd_past, cmd_plan, cmd_stats, cmd_vocab, cmd_weak
from .cli_admin import cmd_add, cmd_bank, cmd_export, cmd_gpt_prompt, cmd_panel, cmd_restore, cmd_update, cmd_web


# ---------- 解析 ----------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="cpe", description="CPE 自學教練：本地判題、提示階梯、間隔重練、模擬考")
    ap.add_argument("--version", action="version", version=f"cpe {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="建立工作區")
    s.add_argument("dir", nargs="?", default="cpe-workspace")
    s.add_argument("--start", help="開始日期 YYYY-MM-DD（預設今天）")

    s = sub.add_parser("course", help="課程：目前單元、全部單元、跳關")
    s.add_argument("action", nargs="?", default="show", choices=["show", "list", "next", "goto"])
    s.add_argument("n", nargs="?", type=int, help="單元編號（show／goto）")
    sub.add_parser("gate", help="開始目前單元的檢核")
    sub.add_parser("roadmap", help="顯示學習路線與各階段目標日期")
    s = sub.add_parser("stage", help="設定目前階段 0–5")
    s.add_argument("n", type=int)
    sub.add_parser("today", help="今天該做什麼")
    s = sub.add_parser("next", help="推薦下一題")
    s.add_argument("-n", type=int, default=3)

    s = sub.add_parser("new", help="建立解答檔（空白模板）；內建練習題會自動安裝題目與測資")
    s.add_argument("id")
    s.add_argument("--fresh", action="store_true", help="舊檔備份後從空白重寫")
    s.add_argument("--lang", choices=["py", "cpp"], help="語言（預設 py）")
    s = sub.add_parser("statement", help="顯示題目敘述（內建題可用 --lang 切換中文／中英對照／英文）")
    s.add_argument("id")
    s.add_argument("--lang", choices=["zh", "bi", "en"], help="只這次用這個語言顯示")
    s = sub.add_parser("lang", help="內建題的題目語言：auto（階段 0 中文、階段 1 中英對照、之後英文）／zh／bi／en")
    s.add_argument("mode", nargs="?", choices=list(bank_mod.LANG_MODES))
    s = sub.add_parser("import", help="從題目文字檔匯入敘述與範例測資（Sample Input/Output、範例輸入/輸出）")
    s.add_argument("id")
    s.add_argument("file")
    s = sub.add_parser("addtest", help="加入一組範例測資")
    s.add_argument("id")
    s.add_argument("--in", dest="infile")
    s.add_argument("--out", dest="outfile")
    s = sub.add_parser("test", help="本地判題")
    s.add_argument("id")
    s.add_argument("--lang", choices=["py", "cpp"], help="同時有 .py 與 .cpp 時指定")
    s = sub.add_parser("stress", help="對拍：暴力解 vs 你的解")
    s.add_argument("id")
    s.add_argument("--gen", required=True, help="產生器（以 seed 為 argv[1]）")
    s.add_argument("--brute", required=True, help="暴力解")
    s.add_argument("-n", type=int, default=200)

    s = sub.add_parser("fuzz", help="範例變異對拍：用你的暴力解當標準答案，自動找出你的解答的錯並存成測資（不需要寫產生器）")
    s.add_argument("id")
    s.add_argument("--brute", required=True, help="暴力解檔案（要先通過所有現有測資）")
    s.add_argument("-n", type=int, default=300, help="嘗試次數")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--max", type=int, default=3, help="最多收集幾組差異")
    s.add_argument("--save", action="store_true", help="把差異存成 tests/<id>/fuzzNN")
    s = sub.add_parser("ai-eval", help="用你的 API 金鑰評測詢問系統：JSON 遵守率、引用驗證率、規則遵守、用量與費用")
    s.add_argument("-n", type=int, default=24, help="詢問次數（預設 24）")
    s.add_argument("--kinds", default="explain,question,mismatch")
    s.add_argument("--no-reply", action="store_true", help="不測追問回覆")
    s.add_argument("--price-in", type=float, help="每百萬輸入 token 的美元單價（用來估算費用）")
    s.add_argument("--price-out", type=float, help="每百萬輸出 token 的美元單價")
    s.add_argument("--out", help="報告輸出路徑")
    s.add_argument("--yes", action="store_true", help="確認會花費 API 額度")
    s = sub.add_parser("hint", help="提示階梯 L0–L4")
    s.add_argument("id")
    s.add_argument("-l", "--level", type=int, choices=range(5), metavar="0-4")
    s = sub.add_parser("giveup", help="放棄這題（24 小時後才能看解法）")
    s.add_argument("id")
    s = sub.add_parser("solution", help="冷卻結束後看解法講解")
    s.add_argument("id")
    sub.add_parser("review", help="到期與排程中的重練")

    s = sub.add_parser("mock", help="模擬考／每週無 AI 測驗")
    s.add_argument("action", choices=["start", "status", "finish"])
    s.add_argument("--kind", choices=["mock", "short", "weekly"], default="mock",
                   help="mock=7 題 3 小時；short=3 題 90 分；weekly=重寫 3 題舊題 60 分")
    s.add_argument("--lang", choices=["py", "cpp"], help="考試檔語言")
    s.add_argument("--all", action="store_true", help="不限制階段（預設只出你學過階段的題目）")
    s.add_argument("--real", action="store_true", help="比照考場：只出有英文題目文字的題（需先匯入歷屆題目）")
    s = sub.add_parser("past", help="歷屆題庫：list／show 日期／import 檔案／statements 資料夾／start 日期／template")
    s.add_argument("action", choices=["list", "show", "import", "statements", "start", "template"])
    s.add_argument("arg", nargs="?", help="日期、檔案或資料夾")
    s.add_argument("--partial", action="store_true", help="start：只出已有測資的題目")
    s.add_argument("--lang", choices=["py", "cpp"])
    s = sub.add_parser("vocab", help="生字本")
    s.add_argument("action", nargs="?", default="list", choices=["list", "export", "add"])
    s.add_argument("word", nargs="?")
    sub.add_parser("stats", help="學習統計")

    s = sub.add_parser("add", help="加入／更新自訂題目")
    s.add_argument("id")
    s.add_argument("--title")
    s.add_argument("--stage", type=int, default=1)
    s.add_argument("--difficulty", type=int, default=1, choices=range(1, 5))
    s.add_argument("--topic")
    s.add_argument("--category", help="L1 方向提示")
    s.add_argument("--insight", help="L2 關鍵觀察")
    s.add_argument("--url")
    s.add_argument("--accuracy", type=float, help="官方全體答對率（%%），當難度標籤")
    s = sub.add_parser("bank", help="列出題庫")
    s.add_argument("--stage", type=int)
    s = sub.add_parser("eng", help="工程能力任務（有自動驗收）")
    s.add_argument("action", nargs="?", choices=["list", "start", "verify"], default="list")
    s.add_argument("n", nargs="?", type=int)
    s.add_argument("--evidence", help="需要證據的任務：提供網址")
    s = sub.add_parser("plan", help="今天 N 分鐘的自動排程")
    s.add_argument("-m", "--minutes", type=int, default=30)
    sub.add_parser("calibrate", help="用你的實際解題紀錄看題目對你多難")
    sub.add_parser("weak", help="依主題診斷弱點，並建議加練的題")
    s = sub.add_parser("external", help="記錄你用了外部 AI（如 ChatGPT 網頁）")
    s.add_argument("id")
    s = sub.add_parser("export", help="匯出備份（zip）")
    s.add_argument("-o", "--out", help="輸出檔名（預設在工作區內 cpe-backup-時間.zip）")
    s = sub.add_parser("restore", help="從備份還原")
    s.add_argument("file")
    s.add_argument("--dir", default=".", help="還原到哪個資料夾（預設目前資料夾）")
    s.add_argument("--force", action="store_true", help="目標已有工作區時覆蓋（舊的 .cpe 會先改名保留）")
    s = sub.add_parser("web", help="啟動本機網頁介面（選取文字 → 問 AI）")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--no-open", action="store_true", help="不要自動開瀏覽器")
    s = sub.add_parser("update", help="更新程式到 GitHub 上最新的版本（git clone 或安裝精靈裝的都可以）；不會動到你的學習進度")
    s.add_argument("--check", action="store_true", help="只檢查有沒有新版本，不更新")
    s = sub.add_parser("panel", help="開啟控制台：開啟／關閉學習服務、更新、備份、修復、解除安裝（沒裝過就開安裝精靈）")
    s.add_argument("--text", action="store_true", help="用文字模式（不開圖形視窗）")
    sub.add_parser("doctor", help="環境檢測與安裝診斷（Python、git、網路、編譯器、服務狀態…）")
    sub.add_parser("gpt-prompt", help="印出可貼進 ChatGPT 自訂 GPT 的助教規則")
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "init":
            return cmd_init(args)
        if args.cmd == "gpt-prompt":
            return cmd_gpt_prompt(args)
        if args.cmd == "restore":
            return cmd_restore(args)
        if args.cmd == "update":
            return cmd_update(args)
        if args.cmd in ("panel", "doctor"):
            return cmd_panel(args)
        ws = Workspace.find()
        handler = {
            "course": cmd_course, "gate": cmd_gate, "statement": cmd_statement, "import": cmd_import,
            "roadmap": cmd_roadmap, "stage": cmd_stage, "today": cmd_today, "next": cmd_next, "new": cmd_new,
            "addtest": cmd_addtest, "test": cmd_test, "stress": cmd_stress, "hint": cmd_hint,
            "giveup": cmd_giveup, "solution": cmd_solution, "review": cmd_review, "mock": cmd_mock,
            "stats": cmd_stats, "add": cmd_add, "bank": cmd_bank, "eng": cmd_eng, "external": cmd_external, "web": cmd_web, "export": cmd_export, "past": cmd_past, "vocab": cmd_vocab, "plan": cmd_plan, "calibrate": cmd_calibrate, "lang": cmd_lang, "fuzz": cmd_fuzz, "ai-eval": cmd_ai_eval, "weak": cmd_weak,
        }[args.cmd]
        if args.cmd == "web":                       # 長時間執行：不要整個程序持有鎖，由每個請求自己加鎖
            return handler(ws, args)
        with ws.lock():
            return handler(ws, args)
    except (WorkspaceError, hints.HintDenied, ValueError, RuntimeError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
