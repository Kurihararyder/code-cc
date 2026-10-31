"""安裝／修復／更新／解除安裝的流程。圖形介面、文字介面與指令列都只呼叫這裡，所以三者行為一致、也都能在沒有畫面的環境測試。

原則：
- 每個流程先宣告步驟（給進度條用），任何一步失敗都會把這一輪已經做的事復原（只復原這一輪新建立的東西）。
- 學習進度資料夾（工作區）預設永遠不碰：安裝只在它不存在時建立，解除安裝只有明確要求才刪，而且刪之前可以先備份。
- 刪東西之前都驗證路徑（不是家目錄、不是磁碟根目錄、真的是我們的資料夾）。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from . import config as cfgmod
from . import constants as C
from . import envcheck, server, shortcuts, source
from .config import LauncherConfig
from .envcheck import Ctx
from .osinfo import Plat

MARK = {"ok": "✓", "warn": "!", "fail": "✗", "info": "·"}
STEPS_INSTALL = ["檢測環境", "安裝缺少的元件", "取得程式", "建立學習進度資料夾", "建立指令與捷徑", "完成"]
STEPS_REPAIR = ["檢查程式", "檢查學習進度", "重建指令與捷徑", "完成"]
STEPS_UPDATE = ["檢查新版本", "更新程式", "重建指令", "完成"]
STEPS_UNINSTALL = ["關閉服務", "備份學習進度", "移除捷徑與登錄", "移除程式", "完成"]


class EngineError(RuntimeError):
    pass


class Cancelled(EngineError):
    pass


class Reporter:
    """進度回報。on_step(索引, 總數, 步驟名稱)、on_log(一行文字)；cancel 事件被設定後，下一步開始前會中止。"""

    def __init__(self, on_step: Optional[Callable[[int, int, str], None]] = None, on_log: Optional[Callable[[str], None]] = None,
                 log_file: Optional[Path] = None, cancel: Optional[threading.Event] = None):
        self.on_step, self.on_log, self.log_file, self.cancel = on_step, on_log, log_file, cancel
        self.steps: List[str] = []
        self.index = -1

    def begin(self, steps: List[str]) -> None:
        self.steps, self.index = list(steps), -1

    def step(self) -> None:
        if self.cancel is not None and self.cancel.is_set():
            raise Cancelled("已取消")
        self.index += 1
        name = self.steps[self.index] if self.index < len(self.steps) else ""
        self.log(f"== {name}")
        if self.on_step:
            self.on_step(self.index, len(self.steps), name)

    def log(self, line: str) -> None:
        if self.on_log:
            self.on_log(line)
        if self.log_file is not None:
            try:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                if self.log_file.exists() and self.log_file.stat().st_size > 512 * 1024:
                    self.log_file.write_text("", encoding="utf-8")
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")
            except OSError:
                pass


class Undo:
    def __init__(self) -> None:
        self.items: List[Any] = []

    def add(self, label: str, fn: Callable[[], None]) -> None:
        self.items.append((label, fn))

    def run(self, log: Callable[[str], None]) -> None:
        for label, fn in reversed(self.items):
            try:
                fn()
                log(f"已復原：{label}")
            except Exception as e:                 # 復原本身失敗不能蓋掉原本的錯誤
                log(f"復原失敗（{label}）：{e}")
        self.items = []


# ---------- 選項與狀態 ----------
@dataclass
class InstallOptions:
    app_dir: Path
    workspace: Path
    source: str = "auto"                           # auto | git | zip | bundle
    branch: str = ""
    desktop: bool = True
    menu: bool = True
    add_path: bool = True
    port: int = C.DEFAULT_PORT
    restore_from: Optional[Path] = None
    bundle: Optional[Path] = None
    python: str = ""
    fixes: List[str] = field(default_factory=list)  # 要先自動安裝的元件（install_git／install_gpp／install_tk）


@dataclass
class UninstallOptions:
    remove_workspace: bool = False
    backup_dir: Optional[Path] = None              # 刪除學習進度之前先備份到這個資料夾


def code_root() -> Path:
    """目前執行中的程式所在的資料夾（安裝完成後就是 app_dir；從 zip 解壓執行時是那個資料夾）。"""
    return Path(__file__).resolve().parents[2]


def find_bundle() -> Optional[Path]:
    r = code_root()
    return r if source.is_app_tree(r) and (r / "cpe_coach" / "launcher").is_dir() else None


def base_python() -> str:
    """記錄用的 Python：真正的直譯器（不是虛擬環境、不是 pythonw）。"""
    exe = getattr(sys, "_base_executable", None) or sys.executable
    exe = shortcuts.console_python(exe)
    return exe if Path(exe).exists() else sys.executable


def default_options(plat: Plat, bundle: Optional[Path] = None) -> InstallOptions:
    """預設的安裝選項。已經裝過的話，預設值就是上一次的選擇（重新安裝或再次執行安裝檔時，位置不會被改回預設）。"""
    o = InstallOptions(app_dir=plat.launcher_home / "app", workspace=plat.default_workspace, branch=C.default_branch(),
                       bundle=bundle if bundle is not None else find_bundle(), port=C.DEFAULT_PORT, python=base_python())
    before = cfgmod.load(plat.launcher_home)
    if before is not None:
        o.app_dir, o.workspace, o.port = Path(before.app_dir), Path(before.workspace), before.port
        o.desktop, o.menu, o.add_path = bool(before.opt("desktop_shortcut")), bool(before.opt("menu_shortcut")), bool(before.opt("add_path"))
    return o


@dataclass
class InstallState:
    installed: bool
    healthy: bool
    cfg: Optional[LauncherConfig] = None
    problems: List[str] = field(default_factory=list)


def installed_state(plat: Plat) -> InstallState:
    cfg = cfgmod.load(plat.launcher_home)
    if cfg is None:
        return InstallState(False, False)
    problems: List[str] = []
    if not source.is_app_tree(Path(cfg.app_dir)):
        problems.append(f"程式資料夾不見了或不完整：{cfg.app_dir}")
    if not Path(cfg.python).exists():
        problems.append(f"記錄的 Python 找不到了：{cfg.python}")
    if not Path(cfg.workspace).is_dir():
        problems.append(f"學習進度資料夾不見了：{cfg.workspace}")
    return InstallState(True, not problems, cfg, problems)


def make_reporter(plat: Plat, on_step=None, on_log=None, cancel=None) -> Reporter:
    return Reporter(on_step, on_log, plat.launcher_home / "logs" / "launcher.log", cancel)


# ---------- 共用：工作區、整合 ----------
def run_cpe(python: str, app_dir: Path, argv: List[str], log: Callable[[str], None]) -> None:
    """用剛裝好的程式執行一個 cpe 指令（init／restore）。這樣同時驗證了安裝出來的程式真的能跑。"""
    code = "import sys; sys.path.insert(0, sys.argv[1]); from cpe_coach.cli import main; raise SystemExit(main(sys.argv[2:]))"
    rc, out = source.run([python, "-I", "-S", "-c", code, str(app_dir)] + argv, 120, cwd=Path(tempfile.gettempdir()))
    if out:
        log(out[-300:])
    if rc != 0:
        raise EngineError(f"cpe {' '.join(argv[:1])} 失敗：{out[-300:]}")


def integrate(cfg: LauncherConfig, plat: Plat, desktop: bool, menu: bool, add_path: bool, rep: Reporter, undo: Optional[Undo] = None,
              run: envcheck.Runner = envcheck.run_cmd) -> None:
    """圖示、cpe 指令、PATH、桌面與開始功能表捷徑、Windows 的解除安裝項目。做了什麼隨時記在 cfg 裡（中途失敗也能完整復原）。"""
    if undo is not None:
        undo.add("捷徑與登錄", lambda: remove_integration(cfg, plat, rep.log))
    shortcuts.copy_assets(cfg.app_dir, plat)
    shortcuts.write_shims(cfg, plat)
    cfg.registered = reg = dict(cfg.registered or {})
    if add_path:
        if plat.is_windows:
            if shortcuts.path_add(plat, str(shortcuts.bin_dir(plat))):
                reg["path_entry"] = str(shortcuts.bin_dir(plat))
        else:
            links = shortcuts.link_on_path(plat)
            if links:
                reg["links"] = [str(p) for p in links]
                if not shortcuts.on_path(plat, shortcuts.local_bin(plat)):
                    rep.log(f"提醒：{shortcuts.local_bin(plat)} 還不在你的 PATH 裡；要在終端機直接輸入 cpe，請把它加進去（例如 ~/.zshrc 或 ~/.bashrc 加一行 export PATH=\"$HOME/.local/bin:$PATH\"）。")
    if plat.is_windows:
        reg["registry"] = True                      # 先記下再寫登錄：寫到一半失敗也會被復原
        shortcuts.register_uninstall(cfg, plat)
    made = shortcuts.create_all(cfg, plat, desktop, menu, rep.log, run)
    cfg.shortcuts = sorted(set(list(cfg.shortcuts or []) + made))
    for m in made:
        rep.log(f"建立捷徑：{m}")


def remove_integration(cfg: LauncherConfig, plat: Plat, log: Callable[[str], None]) -> None:
    failed = shortcuts.remove_created(list(cfg.shortcuts or []), log)
    cfg.shortcuts = failed
    reg = cfg.registered or {}
    if reg.get("path_entry"):
        shortcuts.path_remove(plat, reg["path_entry"])
    for name in list(reg.get("links") or []) + ([reg["link"]] if reg.get("link") else []):       # link：舊版記錄的單一連結
        link = Path(name)
        try:
            if link.is_symlink():
                link.unlink()
        except OSError as e:
            log(f"刪不掉 {link}：{e}")
    if reg.get("registry"):
        shortcuts.unregister_uninstall(plat)
    cfg.registered = {}


# ---------- 安裝 ----------
def install(opts: InstallOptions, plat: Plat, ctx: Ctx, rep: Optional[Reporter] = None) -> LauncherConfig:
    rep = rep or Reporter()
    rep.begin(STEPS_INSTALL)
    undo = Undo()
    python = opts.python or base_python()
    branch = opts.branch or C.default_branch()
    app_dir, ws = Path(opts.app_dir), Path(opts.workspace)
    existing = cfgmod.load(plat.launcher_home)
    try:
        rep.step()
        ctx.target, ctx.port, ctx.bundle, ctx.python = app_dir, opts.port, opts.bundle, python
        checks = envcheck.run_checks(ctx, (existing.version or "") if existing else None)
        for c in checks:
            rep.log(f"{MARK[c.status]} {c.label}：{c.detail}")
        blocking = [c for c in checks if c.blocking]
        if blocking:
            raise EngineError("環境檢測沒有通過：" + "；".join(f"{c.label}（{c.detail}）{c.hint}" for c in blocking))
        try:
            source.check_target(app_dir)
            if ws.exists() and not ws.is_dir():
                raise source.SourceError(f"學習進度位置不是資料夾：{ws}")
        except source.SourceError as e:
            raise EngineError(str(e))
        if app_dir.resolve() == ws.resolve() or app_dir.resolve() in ws.resolve().parents or ws.resolve() in app_dir.resolve().parents:
            raise EngineError("程式資料夾與學習進度資料夾不能互相包含，請分開放。")

        if existing and server.status(existing, plat).running:
            rep.log("先關閉執行中的服務")
            server.stop(existing, plat, rep.log)

        rep.step()
        for fix in opts.fixes:
            ok, msg = envcheck.apply_fix(ctx, fix, rep.log)
            rep.log(("✓ " if ok else "! ") + f"{fix}：{msg}")
        if not opts.fixes:
            rep.log("不需要安裝額外的元件")

        rep.step()
        have_git = bool(ctx.which("git"))
        have_net = any(c.id == "net" and c.status == "ok" for c in checks)
        order = [source.choose(opts.source, have_git, have_net, opts.bundle)]
        if opts.source == "auto":                                          # 自動模式：一種方式失敗就試下一種
            order += [k for k in ("zip", "bundle") if k not in order and (k != "zip" or have_net) and (k != "bundle" or opts.bundle)]
        src: Optional[Dict[str, Any]] = None
        stage = source.staging_dir(app_dir)
        err = ""
        for kind in order:
            try:
                rep.log(f"取得程式：{kind}")
                src = source.fetch(kind, branch, stage, python, opts.bundle, rep.log)
                break
            except source.SourceError as e:
                err = str(e)
                rep.log(f"! {kind} 方式失敗：{err}")
                source.rmtree(stage)
        if src is None:
            raise EngineError("無法取得程式：" + err)
        try:
            old = source.swap_in(stage, app_dir)
        except source.SourceError as e:
            source.rmtree(stage)
            raise EngineError(str(e))

        def undo_swap() -> None:
            source.rmtree(app_dir)
            if old is not None:
                os.replace(str(old), str(app_dir))
        undo.add("程式資料夾", undo_swap)

        rep.step()
        created_ws = not ws.exists()
        if (ws / ".cpe").is_dir():
            rep.log("沿用既有的學習進度資料夾")
        elif opts.restore_from:
            run_cpe(python, app_dir, ["restore", str(opts.restore_from), "--dir", str(ws)], rep.log)
        else:
            run_cpe(python, app_dir, ["init", str(ws)], rep.log)
        if created_ws:
            undo.add("學習進度資料夾", lambda: source.rmtree(ws))

        rep.step()
        cfg = LauncherConfig(app_dir=str(app_dir), workspace=str(ws), python=python, branch=branch, source=src, version=str(src.get("version", "")),
                             port=opts.port, installed_at=time.time())
        if existing:
            cfg.options = dict(existing.options)
        cfg.options.update(desktop_shortcut=opts.desktop, menu_shortcut=opts.menu, add_path=opts.add_path)
        integrate(cfg, plat, opts.desktop, opts.menu, opts.add_path, rep, undo)
        undo.add("設定檔", lambda: cfgmod.path_of(plat.launcher_home).unlink())
        cfgmod.save(plat.launcher_home, cfg)

        rep.step()
        if old is not None:
            source.rmtree(old)
        rep.log(f"已安裝 {C.APP_NAME} {cfg.version}")
        return cfg
    except Cancelled:
        rep.log("已取消，還原中…")
        undo.run(rep.log)
        raise
    except EngineError as e:
        rep.log(f"✗ {e}")
        undo.run(rep.log)
        raise
    except Exception as e:
        rep.log(f"✗ {type(e).__name__}: {e}")
        undo.run(rep.log)
        raise EngineError(f"{type(e).__name__}: {e}")


# ---------- 修復 ----------
def repair(cfg: LauncherConfig, plat: Plat, ctx: Ctx, rep: Optional[Reporter] = None, bundle: Optional[Path] = None) -> LauncherConfig:
    """程式壞掉、Python 換了位置、捷徑被刪掉時：重新取得程式（需要時）並重建指令與捷徑。學習進度不動。"""
    rep = rep or Reporter()
    rep.begin(STEPS_REPAIR)
    app_dir, ws = Path(cfg.app_dir), Path(cfg.workspace)
    try:
        rep.step()
        if not Path(cfg.python).exists():
            rep.log(f"! 記錄的 Python 不見了，改用目前這個：{base_python()}")
            cfg.python = base_python()
        healthy = False
        if source.is_app_tree(app_dir):
            try:
                cfg.version = source.verify_import(cfg.python, app_dir)
                healthy = True
            except source.SourceError as e:
                rep.log(f"! 程式無法載入：{e}")
        if healthy:
            rep.log(f"程式正常（{cfg.version}）")
        else:
            have_net = ctx.net(envcheck.repo_host(), 443, 6.0)
            kind = cfg.source.get("type", "zip")
            if kind == "git" and not ctx.which("git"):
                kind = "zip"
            if not have_net and bundle is None:
                raise EngineError("程式需要重新下載，但現在連不上 GitHub。請確認網路，或從下載的資料夾重新執行安裝。")
            if not have_net:
                kind = "bundle"
            elif kind == "bundle":
                kind = "zip"
            stage = source.staging_dir(app_dir)
            try:
                src = source.fetch(kind, cfg.branch or C.default_branch(), stage, cfg.python, bundle, rep.log)
            except source.SourceError as e:
                source.rmtree(stage)
                raise EngineError(f"重新取得程式失敗：{e}")
            try:
                old = source.swap_in(stage, app_dir)
            except source.SourceError as e:
                source.rmtree(stage)
                raise EngineError(str(e))
            if old is not None:
                source.rmtree(old)
            cfg.source, cfg.version = src, str(src.get("version", ""))

        rep.step()
        if not ws.is_dir():
            rep.log("學習進度資料夾不見了，重新建立空的（要找回進度請用備份還原）")
        if not (ws / ".cpe").is_dir():
            run_cpe(cfg.python, app_dir, ["init", str(ws)], rep.log)

        rep.step()
        integrate(cfg, plat, True, True, bool(cfg.opt("add_path")), rep)
        cfgmod.save(plat.launcher_home, cfg)

        rep.step()
        rep.log("修復完成")
        return cfg
    except EngineError as e:
        rep.log(f"✗ {e}")
        raise
    except Exception as e:
        rep.log(f"✗ {type(e).__name__}: {e}")
        raise EngineError(f"{type(e).__name__}: {e}")


# ---------- 更新 ----------
def check_update(cfg: LauncherConfig) -> Dict[str, Any]:
    """只檢查：回傳 {status: available|up_to_date|unavailable, ...}。git 安裝用 git fetch，zip 安裝比對 GitHub 上最新的 commit。"""
    from .. import updater
    app = Path(cfg.app_dir)
    kind = cfg.source.get("type")
    if kind == "git" and (app / ".git").exists():
        r = updater.apply(app, check_only=True)
        return dict(r, kind="git")
    r = source.zip_check(cfg.source, cfg.branch or C.default_branch())
    if not r["ok"]:
        return {"status": "unavailable", "reason": r["reason"], "kind": kind}
    return {"status": "available" if r["available"] else "up_to_date", "kind": kind, "latest": r["latest"], "version": cfg.version}


def update(cfg: LauncherConfig, plat: Plat, ctx: Ctx, rep: Optional[Reporter] = None) -> Dict[str, Any]:
    """更新程式。服務有開著會先關、更新完再開。回傳 {status, ...}（updated／up_to_date／blocked／unavailable／rolled_back）。"""
    from .. import updater
    rep = rep or Reporter()
    rep.begin(STEPS_UPDATE)
    app = Path(cfg.app_dir)
    was_running = server.status(cfg, plat).running
    try:
        rep.step()
        info = check_update(cfg)
        if info["status"] in ("unavailable", "up_to_date"):
            rep.log(info.get("reason") or "已經是最新版")
            return info

        rep.step()
        if was_running:
            server.stop(cfg, plat, rep.log)
        kind = cfg.source.get("type")
        if kind == "git" and (app / ".git").exists():
            r = updater.apply(app)
            if r["status"] == "updated":
                try:
                    source.verify_import(cfg.python, app)
                except source.SourceError as e:
                    updater.reset_to(app, r["old_commit"])
                    r = dict(r, status="rolled_back", reason=f"新版程式在這個 Python 上無法載入，已退回：{e}")
        else:
            try:
                r = source.zip_update(app, cfg.python, cfg.branch or C.default_branch(), cfg.source, rep.log)
            except source.SourceError as e:
                r = {"status": "blocked", "reason": f"更新失敗，舊版沒有動：{e}"}
        if r["status"] != "updated":
            rep.log(r.get("reason", r["status"]))
            return r

        rep.step()
        cfg.source = r.get("source") or dict(cfg.source, commit=r.get("new_commit", ""), version=r["new_version"])
        cfg.version = r["new_version"]
        shortcuts.copy_assets(cfg.app_dir, plat)
        shortcuts.write_shims(cfg, plat)
        cfgmod.save(plat.launcher_home, cfg)

        rep.step()
        rep.log(f"已更新：{r['old_version']} → {r['new_version']}")
        return r
    finally:
        if was_running:
            try:
                server.start(cfg, plat, log=rep.log)
            except server.ServerError as e:
                rep.log(f"! 更新後重新開啟服務失敗：{e}")


# ---------- 解除安裝 ----------
def inside(path: Path, parent: Path) -> bool:
    try:
        p, q = path.resolve(), parent.resolve()
    except OSError:
        return False
    return p == q or q in p.parents


def removal_problem(path: Path, plat: Plat, keep: Optional[Path] = None) -> str:
    """不能刪的原因（可以刪回傳空字串）。家目錄、磁碟根目錄、會連工作區一起刪掉的路徑一律不刪。"""
    try:
        p = path.resolve()
        home = plat.home.resolve()
    except OSError as e:
        return str(e)
    if len(p.parts) < 3:
        return f"{p} 太接近磁碟根目錄"
    if p == home or p in home.parents:
        return f"{p} 是你的家目錄或它的上層"
    if keep is not None and inside(keep, p):
        return f"{p} 裡面有你要保留的學習進度"
    return ""


CLEANUP_SCRIPT = """
import os, shutil, stat, sys, time
pid, n = int(sys.argv[1]), int(sys.argv[2])
trees, dirs = sys.argv[3:3 + n], sys.argv[3 + n:]
def alive(pid):
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = wintypes.HANDLE
        h = k.OpenProcess(0x1000, False, pid)
        if not h:
            return False
        code = wintypes.DWORD()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True
t = time.time()
while alive(pid) and time.time() - t < 180:
    time.sleep(0.3)
def onerr(f, p, e):
    try:
        os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
        f(p)
    except OSError:
        pass
for p in trees:
    for _ in range(40):
        if os.path.isdir(p) and not os.path.islink(p):
            shutil.rmtree(p, onerror=onerr)
        elif os.path.lexists(p):
            try: os.remove(p)
            except OSError: pass
        if not os.path.lexists(p):
            break
        time.sleep(0.75)
for p in dirs:
    for _ in range(10):
        try:
            os.rmdir(p)
        except OSError:
            if not os.path.exists(p):
                break
            time.sleep(0.5)
"""


def schedule_cleanup(trees: List[Path], empty_dirs: List[Path], python: str, log: Callable[[str], None]) -> None:
    """這個程序還在用要刪的資料夾（程式碼從那裡載入）：另外開一個獨立的小程序，等我們結束後再刪。
    trees 整個刪掉；empty_dirs 只有在空的時候才刪（裡面如果有別的東西就留著）。"""
    py = shortcuts.console_python(python)
    if not Path(py).exists():
        py = sys.executable
    kw: Dict[str, Any] = {}
    if sys.platform == "win32":
        kw["creationflags"] = 0x08000000 | 0x00000200 | 0x00000008                # CREATE_NO_WINDOW | NEW_PROCESS_GROUP | DETACHED_PROCESS
    else:
        kw["start_new_session"] = True
    argv = [py, "-I", "-c", CLEANUP_SCRIPT, str(os.getpid()), str(len(trees))] + [str(p) for p in trees + empty_dirs]
    subprocess.Popen(argv, cwd=tempfile.gettempdir(),
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)
    log("程式資料夾會在這個程式結束後自動刪除")


def uninstall(cfg: LauncherConfig, plat: Plat, opts: UninstallOptions, rep: Optional[Reporter] = None) -> Dict[str, Any]:
    rep = rep or Reporter()
    rep.begin(STEPS_UNINSTALL)
    app_dir, ws, home = Path(cfg.app_dir), Path(cfg.workspace), plat.launcher_home
    result: Dict[str, Any] = {"workspace": str(ws), "workspace_removed": False, "backup": None, "deferred": [], "problems": []}
    keep_ws: Optional[Path] = None if opts.remove_workspace else ws
    try:
        os.chdir(str(plat.home))                                   # 不要讓目前的工作目錄卡住要刪的資料夾（Windows 刪不掉）
    except OSError:
        pass

    rep.step()
    try:
        server.stop(cfg, plat, rep.log)
    except server.ServerError as e:
        raise EngineError(f"無法關閉執行中的服務，先不解除安裝：{e}")

    rep.step()
    if opts.remove_workspace and ws.is_dir() and opts.backup_dir is not None and (ws / ".cpe").is_dir():
        from .. import backup
        from ..store import Workspace
        opts.backup_dir.mkdir(parents=True, exist_ok=True)
        dest = opts.backup_dir / f"CPE進度備份-{time.strftime('%Y%m%d-%H%M%S')}.zip"
        backup.export_workspace(Workspace(ws), dest)
        result["backup"] = str(dest)
        rep.log(f"已備份學習進度：{dest}")
    else:
        rep.log("略過")

    rep.step()
    remove_integration(cfg, plat, rep.log)
    for name in ("cpe.cmd", "cpe-panel.cmd", "cpe", "cpe-panel"):
        try:
            (shortcuts.bin_dir(plat) / name).unlink()
        except OSError:
            pass
    try:
        cfgmod.path_of(home).unlink()                              # 從這一刻起視為『未安裝』
    except OSError:
        pass

    rep.step()
    rep.log_file = None                                            # 紀錄檔也在要刪的資料夾裡，之後不要再寫
    if opts.remove_workspace:
        problem = removal_problem(ws, plat)
        if problem:
            result["problems"].append(f"沒有刪除學習進度：{problem}")
        elif ws.is_dir() and not ((ws / ".cpe").is_dir() or not any(ws.iterdir())):
            result["problems"].append(f"沒有刪除 {ws}：這不是 CPE 教練的學習進度資料夾")
        elif source.rmtree(ws):
            result["workspace_removed"] = True
    trees: List[Path] = []
    if source.is_app_tree(app_dir):
        problem = removal_problem(app_dir, plat, keep_ws)
        if problem:
            result["problems"].append(f"沒有刪除程式資料夾：{problem}")
        else:
            trees.append(app_dir)
    for name in ("bin", "assets", "run", "logs"):
        d = home / name
        if d.exists() and not removal_problem(d, plat, keep_ws):
            trees.append(d)
    leftovers = [home] if not removal_problem(home, plat, keep_ws) else []              # 其他東西都刪完、資料夾空了才會刪掉它
    if inside(Path(__file__), app_dir):
        schedule_cleanup(trees, leftovers, cfg.python, rep.log)
        result["deferred"] = [str(t) for t in trees + leftovers]
    else:
        for t in trees:
            if not source.rmtree(t):
                result["problems"].append(f"刪不掉 {t}（可能有程式正在使用）")
        for d in leftovers:
            try:
                d.rmdir()
            except OSError:
                pass

    rep.step()
    rep.log("已解除安裝" + ("（學習進度已刪除）" if result["workspace_removed"] else f"（學習進度保留在 {ws}）"))
    return result


# ---------- 資訊 ----------
def open_folder(path: Path) -> None:
    p = str(path)
    if sys.platform == "win32":
        os.startfile(p)                                # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", p])
    else:
        subprocess.Popen(["xdg-open", p], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def backup_now(cfg: LauncherConfig, dest_dir: Path) -> Path:
    from .. import backup
    from ..store import Workspace
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"CPE進度備份-{time.strftime('%Y%m%d-%H%M%S')}.zip"
    ws = Workspace(Path(cfg.workspace))
    with ws.lock():
        backup.export_workspace(ws, dest)
    return dest


def read_log(plat: Plat, which: str = "server", n: int = 4000) -> str:
    p = server.log_path(plat) if which == "server" else plat.launcher_home / "logs" / "launcher.log"
    try:
        return p.read_text(encoding="utf-8", errors="replace")[-n:]
    except OSError:
        return ""


def report_text(plat: Plat, ctx: Ctx) -> str:
    """doctor：給人看（也給我診斷）的完整狀態。"""
    from .. import __version__
    st = installed_state(plat)
    lines = [f"{C.APP_NAME} 安裝診斷（執行中的程式版本 {__version__}）", f"位置：{plat.launcher_home}"]
    if st.cfg:
        c = st.cfg
        lines += [f"已安裝：版本 {c.version}　來源 {c.source.get('type')}　分支 {c.branch}", f"程式：{c.app_dir}", f"學習進度：{c.workspace}", f"Python：{c.python}"]
        sv = server.status(c, plat)
        lines.append("服務：" + {"running": "執行中 " + sv.url, "stopped": "已關閉", "unresponsive": f"沒有回應（程序 {sv.pid}）"}[sv.state])
        lines += [f"! {p}" for p in st.problems]
    else:
        lines.append("尚未安裝")
    lines.append("")
    for c in envcheck.run_checks(ctx, st.cfg.version if st.cfg else None):
        lines.append(f"{MARK[c.status]} {c.label}：{c.detail}" + (f"　→ {c.hint}" if c.hint and c.status != "ok" else ""))
    return "\n".join(lines)


# ---------- 控制台：學習摘要與 2.7 的工具（都在背景執行緒呼叫；任何失敗都回傳說明，不丟例外讓畫面當掉） ----------
def learning_summary(cfg: LauncherConfig) -> Dict[str, Any]:
    """首頁「今天」卡片要顯示的：到期複習幾題、目標進度、距離上次練習幾天。唯讀；工作區不存在或壞掉時回傳 {"error": …}。"""
    try:
        from .. import bank as bank_mod
        from .. import memory, planning
        from ..store import Workspace
        ws = Workspace(Path(cfg.workspace))
        now = ws.now()
        bank = bank_mod.load_bank(ws)
        rp, ft = memory.build(ws, bank)
        due = memory.due_now(rp.cards, now, ft.k, due_fn=memory.make_due_fn(ws))
        tests = [e for e in ws.events() if e.get("kind") == "test"]
        days_since = None if not tests else max(0.0, (now - float(tests[-1]["ts"])) / 86400.0)
        g = planning.goal_status(ws)
        goal = None
        if g.get("set"):
            goal = f"目標 {g['target']} 題（{g['date']} 前）：已 {g['solved']} 題，剩 {g['days_left']} 天"
        return {"due": len(due), "due_ids": [d.pid for d in due[:3]], "cards": len(rp.cards), "goal": goal, "goal_status": g.get("status"), "days_since": days_since,
                "solved": sum(1 for p in ws.state()["problems"].values() if p.get("first_pass"))}
    except Exception as e:                                           # 工作區還沒建立、檔案被改壞…都只是「今天卡片」顯示不出來，不能影響控制台本身
        return {"error": f"{type(e).__name__}: {e}"}


def summary_lines(s: Dict[str, Any]) -> List[str]:
    """把 learning_summary 變成幾行好讀的文字（圖形與文字模式共用）。"""
    if s.get("error"):
        return ["（讀不到學習紀錄：" + s["error"] + "）"]
    out = []
    if s["due"]:
        out.append(f"有 {s['due']} 題的記憶快要退了，建議先複習（" + "、".join(s["due_ids"]) + ("…" if s["due"] > 3 else "") + "）")
    elif s["cards"]:
        out.append("目前沒有到期的複習。")
    else:
        out.append("還沒有解出過的題；開始練習後，這裡會顯示該複習什麼。")
    if s["goal"]:
        out.append(s["goal"] + {"behind": "　⚠ 照目前速度趕不上", "ahead": "　✓ 進度超前", "on_track": "　進度正常"}.get(s.get("goal_status"), ""))
    if s["days_since"] is not None:
        d = s["days_since"]
        out.append("今天已經練習過了。" if d < 1 else f"距離上次練習 {int(d)} 天。" + ("　休息夠了，回來動動手吧。" if d >= 3 else ""))
    return out


def encrypted_backup_now(cfg: LauncherConfig, dest_dir: Path, password: str) -> Path:
    from .. import exchange
    from ..store import Workspace
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"CPE進度備份-{time.strftime('%Y%m%d-%H%M%S')}.zip.enc"
    ws = Workspace(Path(cfg.workspace))
    with ws.lock():
        return exchange.encrypted_backup(ws, dest, password)


def sync_now(cfg: LauncherConfig, folder: Path) -> str:
    from .. import sync
    from ..store import Workspace
    r = sync.sync_folder(Workspace(Path(cfg.workspace)), Path(folder))
    lines = [f"同步完成：本機新增 {r['events_added_local']} 筆紀錄、共用資料夾新增 {r['events_added_remote']} 筆；檔案拉下 {r['files_pulled']} 個、推上 {r['files_pushed']} 個。"]
    lines += [f"衝突：{c['file']}（留下{c['kept']}的版本，另一份存在 {c['other_saved_as']}）" for c in r["conflicts"]]
    return "\n".join(lines)


def reminder_plan(cfg: LauncherConfig, hour: int = 19, minute: int = 30) -> Dict[str, Any]:
    from .. import reminder
    from ..store import Workspace
    return reminder.install_plan(Workspace(Path(cfg.workspace)), hour, minute, python=cfg.python)


def install_reminder(cfg: LauncherConfig, hour: int = 19, minute: int = 30) -> str:
    from .. import reminder
    ok, msg = reminder.apply_install(reminder_plan(cfg, hour, minute))
    if not ok:
        raise EngineError(msg)
    return f"已安裝每天 {hour:02d}:{minute:02d} 的複習提醒（有到期的複習才會通知）。"


def privacy_text(cfg: LauncherConfig) -> str:
    from .. import exchange
    from ..store import Workspace
    inv = exchange.inventory(Workspace(Path(cfg.workspace)))
    rows = [f"{r['name']:<24}{r['bytes']:>9} bytes  {r['meaning']}" for r in inv["meta"] + inv["other"]]
    return "學習資料位置：" + inv["root"] + "\n" + "\n".join(rows) + "\n\n" + inv["sent_out"]
