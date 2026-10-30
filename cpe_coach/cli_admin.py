"""維護用的指令：題庫、備份與還原、網頁介面。"""
from __future__ import annotations

from pathlib import Path

from . import bank as bank_mod
from . import backup
from .llm import RULES
from .store import Workspace


def cmd_add(ws: Workspace, args) -> int:
    p = {"id": args.id, "title": args.title or args.id, "source": "custom", "stage": args.stage,
         "difficulty": args.difficulty, "topic": args.topic or "", "hint_category": args.category,
         "hint_insight": args.insight, "url": args.url, "official_one_star": False}
    if args.accuracy is not None:
        p["official_accuracy"] = args.accuracy
    bank_mod.add_custom(ws, p)
    print(f"已加入／更新題庫：{args.id}")
    return 0


def cmd_bank(ws: Workspace, args) -> int:
    st = ws.state()
    items = [p for p in bank_mod.load_bank(ws).values() if args.stage is None or p["stage"] == args.stage]
    for p in sorted(items, key=lambda p: (p["stage"], p["difficulty"], p["id"])):
        sp = st["problems"].get(p["id"])
        mark = "✓" if sp and sp["first_pass"] is not None else " "
        print(f"{mark} 階段{p['stage']} {'★' * p['difficulty']:<5} {p['id']:<10} {p['title']}　[{p['topic']}]")
    return 0


def cmd_export(ws: Workspace, args) -> int:
    dest = backup.export_workspace(ws, Path(args.out) if args.out else None)
    print(f"已匯出：{dest}（{dest.stat().st_size // 1024} KB）")
    print("包含進度、解答、你匯入的題目與測資；內建練習題的測資不包含（會自動重新安裝）。")
    return 0


def cmd_restore(args) -> int:
    n = backup.restore_workspace(Path(args.file), Path(args.dir), args.force)
    print(f"已還原 {n} 個檔案到 {Path(args.dir).resolve()}。在那個資料夾裡執行 cpe today 繼續。")
    return 0


def cmd_web(ws: Workspace, args) -> int:
    from . import web
    web.serve(ws.root, args.port, not args.no_open)
    return 0


def cmd_gpt_prompt(args) -> int:
    print(RULES)
    return 0


def cmd_update(args) -> int:
    """不需要工作區：更新的是程式本身。"""
    from . import __version__, updater
    root = updater.repo_root()
    print(f"目前版本 {__version__}（{root}）")
    r = updater.apply(root, check_only=args.check)
    st = r["status"]
    if st == "unavailable":
        print("✗ " + r["reason"])
        return 1
    print(f"分支 {r['branch']}（{r['commit']}）　對應遠端 {r['upstream']}")
    if st == "up_to_date":
        print("✓ 已經是最新版。")
        return 0
    if st == "available":
        print(f"有 {r['behind']} 個新的更新：")
        for sha, subject in r["commits"][:15]:
            print(f"  {sha}  {subject}")
        print("\n執行 cpe update 就會更新。（你的學習進度在工作區，不會被動到。）")
        return 0
    if st in ("blocked", "rolled_back"):
        print("✗ " + r["reason"])
        return 1
    print(f"✓ 已更新：{r['old_version']}（{r['old_commit']}）→ {r['new_version']}（{r['new_commit']}）")
    if r.get("notes"):
        print("\n這次更新的內容：\n" + r["notes"])
    print("\n如果網頁介面正開著，請在它的終端機按 Ctrl+C 結束，再重新執行 cpe web。")
    print(f"你的學習進度在工作區，不受影響。萬一更新後有問題，可以退回：git -C \"{root}\" reset --hard {r['old_commit']}")
    return 0
