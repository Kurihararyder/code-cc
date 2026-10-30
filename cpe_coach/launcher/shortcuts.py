"""指令捷徑（cpe）、桌面／開始功能表捷徑、Windows 的『應用程式與功能』解除安裝項目、終端機 PATH。

所有建立出來的東西都會回傳路徑，由設定檔記下來；解除安裝時只刪這些，不會誤刪別的檔案。
"""
from __future__ import annotations

import json
import os
import plistlib
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from . import constants as C
from .config import LauncherConfig
from .envcheck import run_cmd
from .osinfo import Plat, pythonw_for

Runner = Callable[..., Tuple[int, str]]
Log = Callable[[str], None]
# ---------- 路徑 ----------
def bin_dir(plat: Plat) -> Path:
    return plat.launcher_home / "bin"


def assets_dir(plat: Plat) -> Path:
    return plat.launcher_home / "assets"


def panel_script(app_dir: str) -> Path:
    return Path(app_dir) / "cpe-panel.pyw"


def console_python(python: str) -> str:
    """pythonw.exe（沒有黑色視窗）換成 python.exe（指令列用）；其他原樣。"""
    name = re.split(r"[\\/]", python)[-1]
    return python[:-len(name)] + "python.exe" if name.lower() == "pythonw.exe" else python


def shq(s: str) -> str:
    return "'" + str(s).replace("'", "'\\''") + "'"


def copy_assets(app_dir: str, plat: Plat) -> Dict[str, Path]:
    """圖示複製到固定位置：之後換掉程式資料夾（更新）時捷徑的圖示不會不見。"""
    src = Path(app_dir) / "cpe_coach" / "launcher" / "assets"
    dst = assets_dir(plat)
    dst.mkdir(parents=True, exist_ok=True)
    out: Dict[str, Path] = {}
    if src.is_dir():
        for f in src.iterdir():
            if f.is_file():
                shutil.copy2(str(f), str(dst / f.name))
                out[f.name] = dst / f.name
    return out


def batch_bytes(text: str, encoding: Optional[str] = None) -> bytes:
    """批次檔（.cmd）的編碼：cmd.exe 用系統的字碼頁讀它（繁體中文 Windows 是 950），不是 UTF-8。
    使用者資料夾常常有中文（例如 C:\\Users\\王小明），所以要用系統字碼頁寫，路徑才不會變亂碼；寫不進去（字碼頁沒有那個字）才退回 UTF-8。"""
    enc = encoding or ("mbcs" if sys.platform == "win32" else "utf-8")
    try:
        return text.encode(enc)
    except (UnicodeEncodeError, LookupError):
        return text.encode("utf-8")


# ---------- cpe／cpe-panel 指令 ----------
def write_shims(cfg: LauncherConfig, plat: Plat, encoding: Optional[str] = None) -> List[Path]:
    d = bin_dir(plat)
    d.mkdir(parents=True, exist_ok=True)
    py, app = console_python(cfg.python), cfg.app_dir
    out: List[Path] = []
    if plat.is_windows:
        def esc(s: str) -> str:
            return s.replace("%", "%%")
        files = {
            "cpe.cmd": f'@echo off\r\nsetlocal\r\nset "PYTHONPATH={esc(app)}"\r\nset "PYTHONUTF8=1"\r\n"{esc(py)}" -m cpe_coach %*\r\nexit /b %ERRORLEVEL%\r\n',
            "cpe-panel.cmd": f'@echo off\r\n"{esc(pythonw_for(py))}" "{esc(str(panel_script(app)))}" %*\r\n',
        }
        for name, body in files.items():
            (d / name).write_bytes(batch_bytes(body, encoding))
            out.append(d / name)
        return out
    files = {
        "cpe": f"#!/bin/sh\nPYTHONPATH={shq(app)} PYTHONUTF8=1 exec {shq(py)} -m cpe_coach \"$@\"\n",
        "cpe-panel": f"#!/bin/sh\nexec {shq(py)} {shq(str(panel_script(app)))} \"$@\"\n",
    }
    for name, body in files.items():
        f = d / name
        f.write_text(body, encoding="utf-8")
        f.chmod(f.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        out.append(f)
    return out


def local_bin(plat: Plat) -> Path:
    return plat.home / ".local" / "bin"


def link_on_path(plat: Plat) -> List[Path]:
    """macOS／Linux：在 ~/.local/bin 放 cpe 與 cpe-panel 的連結（多數 Linux 的終端機預設就找得到）。回傳連結好（或原本就是我們的）的那些。"""
    if plat.is_windows:
        return []
    out: List[Path] = []
    for name in ("cpe", "cpe-panel"):
        src = bin_dir(plat) / name
        dst = local_bin(plat) / name
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_symlink() or dst.exists():
                if dst.is_symlink() and os.path.realpath(str(dst)) == os.path.realpath(str(src)):
                    out.append(dst)
                continue                                         # 那裡已經有別的同名指令（例如 pip 裝的 cpe），不去蓋掉
            dst.symlink_to(src)
            out.append(dst)
        except OSError:
            continue
    return out


def on_path(plat: Plat, directory: Path) -> bool:
    return any(os.path.normcase(os.path.normpath(p)) == os.path.normcase(os.path.normpath(str(directory)))
               for p in (plat.env.get("PATH") or "").split(os.pathsep) if p)


# ---------- Windows：登錄（PATH 與解除安裝項目） ----------
def reg_root(plat: Plat) -> str:
    """測試時用 CPE_LAUNCHER_REG_SANDBOX 改到另一個機碼，不會動到真正的 PATH 與『應用程式與功能』清單。"""
    return plat.env.get("CPE_LAUNCHER_REG_SANDBOX", "")


def _env_key(plat: Plat) -> str:
    r = reg_root(plat)
    return (r + r"\Environment") if r else "Environment"


def _uninstall_key(plat: Plat) -> str:
    r = reg_root(plat)
    return (r + r"\Uninstall\CPE-Coach") if r else r"Software\Microsoft\Windows\CurrentVersion\Uninstall\CPE-Coach"


def _norm(p: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.expandvars(p)))


def _broadcast_env_change() -> None:
    import ctypes
    result = ctypes.c_ulong()
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x1A, 0, "Environment", 2, 5000, ctypes.byref(result))      # WM_SETTINGCHANGE


def path_add(plat: Plat, directory: str) -> bool:
    """把資料夾加進『使用者』的 PATH（不需要系統管理員）。做完之後它在 PATH 裡就回傳 True（原本就在也是）；不是 Windows 回傳 False。"""
    if sys.platform != "win32" or not plat.is_windows:
        return False
    import winreg
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, _env_key(plat), 0, winreg.KEY_READ | winreg.KEY_WRITE) as k:
        try:
            cur, typ = winreg.QueryValueEx(k, "Path")
        except FileNotFoundError:
            cur, typ = "", winreg.REG_EXPAND_SZ
        parts = [p for p in str(cur).split(";") if p]
        if any(_norm(p) == _norm(directory) for p in parts):
            return True
        winreg.SetValueEx(k, "Path", 0, typ, ";".join(parts + [directory]))
    if not reg_root(plat):
        _broadcast_env_change()
    return True


def path_remove(plat: Plat, directory: str) -> bool:
    if sys.platform != "win32" or not plat.is_windows:
        return False
    import winreg
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _env_key(plat), 0, winreg.KEY_READ | winreg.KEY_WRITE)
    except OSError:
        return False
    with k:
        try:
            cur, typ = winreg.QueryValueEx(k, "Path")
        except FileNotFoundError:
            return False
        parts = [p for p in str(cur).split(";") if p]
        keep = [p for p in parts if _norm(p) != _norm(directory)]
        if len(keep) == len(parts):
            return False
        winreg.SetValueEx(k, "Path", 0, typ, ";".join(keep))
    if not reg_root(plat):
        _broadcast_env_change()
    return True


def dir_size_kb(p: str) -> int:
    total = 0
    for root, _dirs, files in os.walk(p):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total // 1024


def register_uninstall(cfg: LauncherConfig, plat: Plat) -> bool:
    """Windows 設定 → 應用程式 → 已安裝的應用程式 裡出現『CPE 教練』，可以從那裡解除安裝。"""
    if sys.platform != "win32" or not plat.is_windows:
        return False
    import winreg
    py = console_python(cfg.python)
    gui = pythonw_for(py)
    icon = assets_dir(plat) / "icon.ico"
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, _uninstall_key(plat), 0, winreg.KEY_WRITE) as k:
        def sv(name: str, val, typ=winreg.REG_SZ) -> None:
            winreg.SetValueEx(k, name, 0, typ, val)
        sv("DisplayName", C.APP_NAME)
        sv("DisplayVersion", cfg.version or "")
        sv("Publisher", "CPE Coach")
        sv("InstallLocation", cfg.app_dir)
        sv("InstallDate", time.strftime("%Y%m%d"))
        if icon.exists():
            sv("DisplayIcon", str(icon))
        sv("UninstallString", f'"{gui}" "{panel_script(cfg.app_dir)}" uninstall')
        sv("NoModify", 1, winreg.REG_DWORD)
        sv("NoRepair", 1, winreg.REG_DWORD)
        sv("EstimatedSize", dir_size_kb(cfg.app_dir), winreg.REG_DWORD)
    return True


def unregister_uninstall(plat: Plat) -> bool:
    if sys.platform != "win32" or not plat.is_windows:
        return False
    import winreg
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, _uninstall_key(plat))
    except OSError:
        return False
    return True


def uninstall_entry_exists(plat: Plat) -> bool:
    if sys.platform != "win32" or not plat.is_windows:
        return False
    import winreg
    try:
        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CURRENT_USER, _uninstall_key(plat)))
    except OSError:
        return False
    return True


# ---------- 捷徑檔 ----------
def lnk_helper() -> Path:
    return Path(__file__).with_name("winlnk.py")


def make_lnks(items: List[Dict[str, str]], python: str, run: Runner = run_cmd, log: Log = lambda s: None) -> List[bool]:
    """Windows 的 .lnk，一次建立全部。每一項是 {lnk, target, args, wd, icon, desc}；回傳每一項是否真的建立出來。
    用另一個行程執行 winlnk.py（IShellLinkW，Unicode；路徑有中文也行，WScript.Shell 在英文版 Windows 上不行），
    失敗時把它的輸出寫進紀錄（不然只知道失敗、不知道為什麼）。"""
    if not items:
        return []
    for it in items:
        lnk = Path(it["lnk"])
        lnk.parent.mkdir(parents=True, exist_ok=True)
        try:
            if lnk.is_file():
                lnk.unlink()                            # 重新安裝：先刪掉舊的，之後才分得出這次有沒有建立成功
        except OSError:
            pass
    env = dict(os.environ, CPE_LNKS=json.dumps({"items": items}), PYTHONIOENCODING="utf-8")
    rc, out = run([console_python(python), "-I", str(lnk_helper())], 90, env)
    out = out.replace("\r", "")
    failed = {int(m.group(1)): m.group(2) for m in re.finditer(r"^FAIL (\d+) : (.*)$", out, re.M)}
    made = [Path(it["lnk"]).is_file() and i not in failed for i, it in enumerate(items)]
    if not all(made):
        why = "; ".join(sorted(set(failed.values())))[:300] if failed else out.strip()[-300:]
        log(f"沒能建立 .lnk 捷徑（結束碼 {rc}）：{why or '沒有任何輸出'}")
    return made


def make_cmd_launcher(path: Path, gui_python: str, script: str, arg: str = "", encoding: Optional[str] = None) -> None:
    """沒辦法建立 .lnk（例如 PowerShell 被限制）時的替代：一個雙擊就能開的 .cmd。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = f'@echo off\r\nstart "" "{gui_python}" "{script}" {arg}\r\n'.replace("%", "%%")
    path.write_bytes(batch_bytes(body, encoding))


def desktop_quote(s: str) -> str:
    """.desktop 的 Exec 欄位引號規則。"""
    esc = s.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$")
    return f'"{esc}"'


def make_desktop_entry(path: Path, name: str, exec_line: str, icon: str, actions: List[Tuple[str, str, str]]) -> None:
    lines = ["[Desktop Entry]", "Version=1.0", "Type=Application", f"Name={name}", f"Comment={C.APP_NAME}控制台：開啟、關閉、更新、解除安裝",
             f"Exec={exec_line}", f"Icon={icon}", "Terminal=false", "Categories=Education;Development;", "StartupNotify=true"]
    if actions:
        lines.append("Actions=" + ";".join(a[0] for a in actions) + ";")
        for key, label, cmd in actions:
            lines += ["", f"[Desktop Action {key}]", f"Name={label}", f"Exec={cmd}"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def make_app_bundle(dest: Path, name: str, shim: Path, icns: Optional[Path], version: str) -> None:
    contents = dest / "Contents"
    (contents / "MacOS").mkdir(parents=True, exist_ok=True)
    (contents / "Resources").mkdir(parents=True, exist_ok=True)
    plist = {"CFBundleName": name, "CFBundleDisplayName": name, "CFBundleIdentifier": "io.github.cpe-coach.launcher", "CFBundleExecutable": "cpe-coach",
             "CFBundlePackageType": "APPL", "CFBundleShortVersionString": version or "1", "CFBundleVersion": version or "1",
             "NSHighResolutionCapable": True, "LSMinimumSystemVersion": "10.13"}
    if icns is not None and icns.exists():
        shutil.copy2(str(icns), str(contents / "Resources" / "AppIcon.icns"))
        plist["CFBundleIconFile"] = "AppIcon"
    (contents / "Info.plist").write_bytes(plistlib.dumps(plist))
    exe = contents / "MacOS" / "cpe-coach"
    exe.write_text(f"#!/bin/sh\nexec {shq(str(shim))} \"$@\"\n", encoding="utf-8")
    exe.chmod(0o755)


def create_all(cfg: LauncherConfig, plat: Plat, desktop: bool = True, menu: bool = True, log: Log = lambda s: None, run: Runner = run_cmd) -> List[str]:
    """建立桌面與開始功能表（應用程式選單）的捷徑，回傳建立出來的路徑。個別失敗只記錄、不中止安裝。"""
    created: List[str] = []
    assets = assets_dir(plat)
    py = console_python(cfg.python)
    gui = pythonw_for(py)
    script = str(panel_script(cfg.app_dir))
    name = C.APP_NAME

    def attempt(label: str, fn: Callable[[], Optional[Path]]) -> None:
        try:
            p = fn()
            if p is not None:
                created.append(str(p))
        except (OSError, subprocess.SubprocessError) as e:
            log(f"{label}沒有建立成功：{e}")

    if plat.is_windows:
        icon = str(assets / "icon.ico")
        specs: List[Tuple[Path, str, str, str]] = []                                  # (資料夾, 名稱, 啟動參數, 說明)
        if desktop:
            specs.append((plat.desktop_dir, name, "", f"{name}控制台"))
        if menu:
            folder = plat.menu_dir / name
            specs += [(folder, f"{name}（控制台）", "", f"{name}控制台：開啟、關閉、更新、解除安裝"),
                      (folder, f"{name}　開始學習", "open", "直接開啟學習畫面"),
                      (folder, f"解除安裝 {name}", "uninstall", f"解除安裝 {name}")]
        items = [{"lnk": str(f / f"{t}.lnk"), "target": gui, "args": (f'"{script}" ' + a).strip(), "wd": cfg.app_dir, "icon": icon, "desc": d} for f, t, a, d in specs]
        try:
            made_lnk = make_lnks(items, cfg.python, run, log)
        except (OSError, subprocess.SubprocessError) as e:
            log(f"捷徑沒有建立成功：{e}")
            made_lnk = [False] * len(items)
        for (folder, title, arg, _desc), it, ok in zip(specs, items, made_lnk):
            if ok:
                created.append(it["lnk"])
                continue

            def cmd_fallback(folder=folder, title=title, arg=arg) -> Optional[Path]:
                fb = folder / f"{title}.cmd"
                make_cmd_launcher(fb, gui, script, arg)
                log(f"{title} 改用 .cmd 捷徑（沒辦法建立 .lnk）")
                return fb
            attempt(title, cmd_fallback)
        return created

    shim = bin_dir(plat) / "cpe-panel"
    if plat.is_macos:
        if menu:
            app = plat.menu_dir / f"{name}.app"

            def mk() -> Optional[Path]:
                if app.exists():
                    shutil.rmtree(str(app))
                make_app_bundle(app, name, shim, assets / "icon.icns", cfg.version)
                return app
            attempt("應用程式", mk)
        if desktop and menu and (plat.menu_dir / f"{name}.app").exists():
            def ln() -> Optional[Path]:
                d = plat.desktop_dir / f"{name}.app"
                if not plat.desktop_dir.is_dir():
                    return None
                if d.is_symlink() or d.exists():
                    d.unlink()
                d.symlink_to(plat.menu_dir / f"{name}.app")
                return d
            attempt("桌面捷徑", ln)
        return created

    icon = str(assets / "icon.png")
    actions = [("Open", "開始學習", f"{desktop_quote(str(shim))} open"), ("Uninstall", f"解除安裝 {name}", f"{desktop_quote(str(shim))} uninstall")]

    def desk(folder: Path) -> Optional[Path]:
        f = folder / "cpe-coach.desktop"
        make_desktop_entry(f, name, desktop_quote(str(shim)), icon, actions)
        return f
    if menu:
        attempt("應用程式選單", lambda: desk(plat.menu_dir))
    if desktop and plat.desktop_dir.is_dir():
        def desk_copy() -> Optional[Path]:
            f = desk(plat.desktop_dir)
            if shutil.which("gio"):
                run(["gio", "set", str(f), "metadata::trusted", "true"], 15)          # GNOME 要標記為信任才能雙擊
            return f
        attempt("桌面捷徑", desk_copy)
    return created


def remove_created(paths: List[str], log: Log = lambda s: None) -> List[str]:
    """刪掉安裝時建立的捷徑。回傳刪不掉的。開始功能表資料夾空了就一起刪。"""
    failed: List[str] = []
    for s in paths:
        p = Path(s)
        try:
            if p.is_symlink() or p.is_file():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(str(p))
            parent = p.parent
            if parent.name == C.APP_NAME and parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError as e:
            log(f"刪不掉 {p}：{e}")
            failed.append(s)
    return failed
