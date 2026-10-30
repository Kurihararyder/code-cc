"""CPE 教練的安裝精靈與控制台。

  python -m cpe_coach.launcher            已安裝 → 控制台；還沒安裝 → 安裝精靈（有圖形畫面用圖形，否則文字模式）
  python -m cpe_coach.launcher install    安裝精靈（--yes 不詢問、全用預設值；--text 強制文字模式）
  python -m cpe_coach.launcher open       開啟（啟動服務並開啟學習畫面），不顯示控制台
  python -m cpe_coach.launcher close      關閉服務
  python -m cpe_coach.launcher status     顯示狀態
  python -m cpe_coach.launcher update     更新（--check 只檢查）
  python -m cpe_coach.launcher repair     修復
  python -m cpe_coach.launcher uninstall  解除安裝（--remove-workspace 連學習進度一起刪）
  python -m cpe_coach.launcher doctor     環境檢測與安裝診斷
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import traceback
from pathlib import Path
from typing import List, Optional

from . import config as cfgmod
from . import constants as C
from . import engine, envcheck, server, shortcuts
from .envcheck import Ctx
from .osinfo import Plat, detect, pythonw_for


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="cpe-panel", description=f"{C.APP_NAME} 安裝精靈與控制台")
    ap.add_argument("command", nargs="?", default="panel",
                    choices=["panel", "install", "open", "close", "status", "update", "repair", "uninstall", "doctor"])
    ap.add_argument("--text", action="store_true", help="強制使用文字模式（不開圖形視窗）")
    ap.add_argument("--yes", "-y", action="store_true", help="不詢問，全部用預設值（或你指定的選項）")
    ap.add_argument("--dir", help="install：程式安裝位置")
    ap.add_argument("--workspace", help="install：學習進度資料夾")
    ap.add_argument("--source", choices=["auto", "git", "zip", "bundle"], default="auto", help="install：程式來源（預設自動選）")
    ap.add_argument("--branch", help="install：分支")
    ap.add_argument("--port", type=int, help="install：網頁服務的埠")
    ap.add_argument("--restore", help="install：從備份檔還原學習進度")
    ap.add_argument("--fix", default="", help="install：先自動安裝的元件，逗號分隔：git,gpp,tk")
    ap.add_argument("--no-desktop", action="store_true")
    ap.add_argument("--no-menu", action="store_true")
    ap.add_argument("--no-path", action="store_true")
    ap.add_argument("--check", action="store_true", help="update：只檢查有沒有新版本")
    ap.add_argument("--remove-workspace", action="store_true", help="uninstall：連學習進度一起刪（不可復原）")
    ap.add_argument("--backup-dir", help="uninstall：刪除學習進度前先備份到這個資料夾")
    ap.add_argument("--json", action="store_true", help="status：輸出 JSON")
    ap.add_argument("--no-browser", action="store_true", help="open：只啟動服務，不開啟學習畫面")
    ap.add_argument("--detach-gui", action="store_true", help="可以開圖形視窗時，另開不帶黑色視窗的程序後立刻返回（給雙擊啟動檔用）")
    return ap


def gui_usable(ctx: Ctx) -> bool:
    return ctx.has_tk() and envcheck.display_available(ctx.plat)


def spawn_detached_gui(argv: List[str]) -> bool:
    """用 pythonw（Windows）重新啟動自己並立刻返回，讓雙擊啟動檔的黑色視窗可以關掉。"""
    exe = pythonw_for(shortcuts.console_python(sys.executable)) if sys.platform == "win32" else sys.executable
    script = Path(__file__).resolve().parents[2] / "cpe-panel.pyw"
    cmd = [exe, str(script)] + [a for a in argv if a != "--detach-gui"]
    kw = {}
    if sys.platform == "win32":
        kw["creationflags"] = 0x08000000 | 0x00000200 | 0x00000008
    else:
        kw["start_new_session"] = True
    try:
        subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)
    except OSError:
        return False
    return True


def options_from_args(plat: Plat, args: argparse.Namespace) -> engine.InstallOptions:
    o = engine.default_options(plat)
    if args.dir:
        o.app_dir = Path(args.dir).expanduser()
    if args.workspace:
        o.workspace = Path(args.workspace).expanduser()
    o.source = args.source
    if args.branch:
        o.branch = args.branch
    if args.port:
        o.port = args.port
    if args.restore:
        o.restore_from = Path(args.restore).expanduser()
    o.fixes = [f"install_{x.strip()}" for x in args.fix.split(",") if x.strip()]
    o.desktop, o.menu, o.add_path = not args.no_desktop, not args.no_menu, not args.no_path
    return o


def require_install(plat: Plat) -> Optional[cfgmod.LauncherConfig]:
    cfg = cfgmod.load(plat.launcher_home)
    if cfg is None:
        print(f"還沒有安裝 {C.APP_NAME}。先執行：python -m cpe_coach.launcher install")
    return cfg


def run(argv: Optional[List[str]] = None, plat: Optional[Plat] = None, ctx: Optional[Ctx] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    plat = plat or detect()
    ctx = ctx or Ctx(plat=plat)
    try:
        return dispatch(args, argv, plat, ctx)
    except KeyboardInterrupt:
        print("\n已中斷。")
        return 130
    except Exception as e:                                         # 不讓雙擊的使用者看到一閃而過的視窗：寫進紀錄檔
        crash(plat, e, args.text)
        return 70


def crash(plat: Plat, e: BaseException, text_mode: bool) -> None:
    msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    try:
        d = plat.launcher_home / "logs"
        d.mkdir(parents=True, exist_ok=True)
        (d / "crash.log").write_text(msg, encoding="utf-8")
        where = f"詳細內容已寫在 {d / 'crash.log'}"
    except OSError:
        where = ""
    short = f"{C.APP_NAME} 發生非預期的錯誤：{type(e).__name__}: {e}\n{where}"
    if sys.stderr is not None:
        print(short, file=sys.stderr)
    if not text_mode:
        try:
            import tkinter
            from tkinter import messagebox
            r = tkinter.Tk()
            r.withdraw()
            messagebox.showerror(C.APP_NAME, short)
            r.destroy()
        except Exception:
            pass


def dispatch(args: argparse.Namespace, argv: List[str], plat: Plat, ctx: Ctx) -> int:
    cmd = args.command
    if cmd == "doctor":
        print(engine.report_text(plat, ctx))
        return 0
    if cmd == "install" and args.yes:
        return headless_install(args, plat, ctx)
    if cmd in ("panel", "install"):
        use_gui = gui_usable(ctx) and not args.text and not args.yes
        if use_gui and args.detach_gui and spawn_detached_gui(argv):
            return 0
        if use_gui:
            try:
                from . import gui
                return gui.run(plat, ctx, install_only=(cmd == "install"))
            except Exception as e:                                 # tkinter 在這台機器上開不起來：改用文字模式
                print(f"（圖形介面無法啟動：{type(e).__name__}: {e}；改用文字模式）")
        from .tui import TUI
        t = TUI(plat, ctx)
        if cmd == "install":
            return t.wizard(options_from_args(plat, args))
        return t.panel()
    if cmd == "status":
        cfg = require_install(plat)
        if cfg is None:
            return 1
        sv = server.status(cfg, plat)
        if args.json:
            print(json.dumps({"state": sv.state, "url": sv.url, "pid": sv.pid, "port": sv.port, "version": cfg.version, "workspace": cfg.workspace}, ensure_ascii=False))
        else:
            print({"running": f"● 執行中 {sv.url}", "stopped": "○ 已關閉", "unresponsive": f"! 沒有回應（程序 {sv.pid}）"}[sv.state] + f"　版本 {cfg.version}")
        return 0 if sv.running else 3
    cfg = require_install(plat)
    if cfg is None:
        return 1
    from .tui import TUI
    t = TUI(plat, ctx, assume_yes=args.yes)
    if cmd == "open":
        rc = t.do_open(cfg, open_ui=not args.no_browser)
        if rc and gui_usable(ctx) and not args.text:
            _error_box(f"無法開啟 {C.APP_NAME}。詳細原因見：{server.log_path(plat)}")
        return rc
    if cmd == "close":
        return t.do_close(cfg)
    if cmd == "update":
        return t.run_update(cfg, check_only=args.check)
    if cmd == "repair":
        return t.run_repair(cfg)
    if cmd == "uninstall":
        if gui_usable(ctx) and not args.text and not args.yes:
            from . import gui
            return gui.run(plat, ctx, uninstall_only=True)
        return t.uninstall_flow(cfg, args.remove_workspace if args.yes else None, Path(args.backup_dir) if args.backup_dir else None)
    return 2


def headless_install(args: argparse.Namespace, plat: Plat, ctx: Ctx) -> int:
    from .tui import TUI
    return TUI(plat, ctx, assume_yes=True).wizard(options_from_args(plat, args))


def _error_box(msg: str) -> None:
    try:
        import tkinter
        from tkinter import messagebox
        r = tkinter.Tk()
        r.withdraw()
        messagebox.showerror(C.APP_NAME, msg)
        r.destroy()
    except Exception:
        pass


def main(argv: Optional[List[str]] = None) -> int:
    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
