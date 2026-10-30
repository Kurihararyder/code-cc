"""自動檢測環境，以及能自動修復的項目（git、C++ 編譯器、tkinter）的安裝計畫。

每個檢查都回傳 Check（ok／warn／fail／info）。所有對外部世界的存取（執行指令、連網、查磁碟、查埠）都透過 Ctx 注入，
所以可以在任何平台用假的環境測試『缺 git』『沒網路』『磁碟不夠』等情況。
"""
from __future__ import annotations

import os
import shutil
import socket
import ssl
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .constants import DEFAULT_PORT, MIN_FREE_MB, MIN_PYTHON, repo_url
from .osinfo import Plat, detect

Runner = Callable[..., Tuple[int, str]]               # (指令, 逾時秒數, 環境變數=None) → (結束碼, 輸出)


def run_cmd(cmd: List[str], timeout: int = 60, env: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
    """執行指令（不跳出黑色視窗），回傳 (結束碼, 輸出)。找不到程式 → 127；逾時 → 124。"""
    kw = {}
    if sys.platform == "win32":
        kw["creationflags"] = 0x08000000                  # CREATE_NO_WINDOW
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout, env=env, **kw)
    except subprocess.TimeoutExpired:
        return 124, f"{cmd[0]} 超過 {timeout} 秒沒有回應"
    except OSError as e:
        return 127, str(e)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace").strip()


def tls_ok(host: str, port: int = 443, timeout: float = 6.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            with ssl.create_default_context().wrap_socket(s, server_hostname=host):
                return True
    except (OSError, ssl.SSLError):
        return False


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if sys.platform != "win32":
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)         # 剛關掉的服務留下的 TIME_WAIT 不算占用（Windows 的這個選項語意不同，不能開）
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def free_mb(path: Path) -> float:
    p = Path(path)
    while not p.exists() and p != p.parent:
        p = p.parent
    return shutil.disk_usage(str(p)).free / 1048576


def tk_importable() -> bool:
    try:
        import tkinter                                # 缺 _tkinter 時這一行就會 ImportError
    except ImportError:
        return False
    if sys.platform == "darwin" and float(getattr(tkinter, "TkVersion", 8.6)) < 8.6:
        return False                                  # 系統內建 Python 附的 Tk 8.5 在新版 macOS 一開視窗就會當掉
    return True


def display_available(plat: Plat) -> bool:
    if plat.system != "linux":
        return True
    return bool(plat.env.get("DISPLAY") or plat.env.get("WAYLAND_DISPLAY"))


@dataclass
class Ctx:
    plat: Plat = field(default_factory=detect)
    run: Runner = run_cmd
    which: Callable[[str], Optional[str]] = shutil.which
    net: Callable[[str, int, float], bool] = tls_ok
    free_mb: Callable[[Path], float] = free_mb
    port_free: Callable[[int], bool] = port_is_free
    has_tk: Callable[[], bool] = tk_importable
    python: str = sys.executable
    py_version: Tuple[int, int, int] = tuple(sys.version_info[:3])           # type: ignore[assignment]
    target: Optional[Path] = None                  # 要安裝到哪（檢查可寫與磁碟空間）
    port: int = DEFAULT_PORT
    bundle: Optional[Path] = None                  # 如果是從原始碼資料夾（zip 解壓）執行：沒有網路時可以從這裡安裝
    is_admin: Callable[[], bool] = lambda: hasattr(os, "geteuid") and os.geteuid() == 0


@dataclass
class Check:
    id: str
    label: str
    status: str                                    # ok | warn | fail | info
    detail: str = ""
    required: bool = True                          # 為 True 且 fail 才會擋住安裝
    fix: Optional[str] = None                      # 可自動修復時的修復代號（install_git／install_gpp／install_tk）
    hint: str = ""                                 # 不能自動修復時的手動做法

    @property
    def blocking(self) -> bool:
        return self.status == "fail" and self.required


# ---------- 找編譯器 ----------
def known_gpp_dirs(plat: Plat) -> List[Path]:
    """Windows 上 MSYS2／MinGW 的固定位置（和判題找 g++ 用同一份清單）。"""
    from ..judge import gpp_candidates
    return gpp_candidates(plat.env, plat.is_windows)


def find_gpp(ctx: Ctx) -> Optional[str]:
    found = ctx.which("g++")
    if found:
        return found
    for d in known_gpp_dirs(ctx.plat):
        f = d / "g++.exe"
        if f.exists():
            return str(f)
    return None


# ---------- 檢查項目 ----------
def check_os(ctx: Ctx) -> Check:
    return Check("os", "作業系統", "info", ctx.plat.label, required=False)


def check_python(ctx: Ctx) -> Check:
    v = ".".join(str(x) for x in ctx.py_version)
    if tuple(ctx.py_version[:2]) < MIN_PYTHON:
        return Check("python", "Python", "fail", f"目前是 {v}，需要 {MIN_PYTHON[0]}.{MIN_PYTHON[1]} 以上",
                     hint="請安裝 Python 3.9～3.12（Windows：勾選 Add python.exe to PATH）。用安裝資料夾裡的『安裝』啟動檔，它會自動幫你裝。")
    return Check("python", "Python", "ok", f"{v}（{ctx.python}）")


def check_tk(ctx: Ctx) -> Check:
    if not ctx.has_tk():
        if ctx.plat.system == "linux":
            return Check("tk", "圖形介面套件（tkinter）", "warn", "沒有安裝，會改用文字模式", required=False, fix="install_tk")
        return Check("tk", "圖形介面套件（tkinter）", "warn", "這個 Python 沒有可用的 tkinter（或版本太舊），會改用文字模式", required=False,
                     hint="從 python.org 安裝的 Python 都有 tkinter；Homebrew 的要另外裝：brew install python-tk")
    if not display_available(ctx.plat):
        return Check("tk", "圖形介面套件（tkinter）", "warn", "有 tkinter 但目前沒有圖形畫面（沒有 DISPLAY），會改用文字模式", required=False)
    return Check("tk", "圖形介面套件（tkinter）", "ok", "可以使用圖形介面")


def check_git(ctx: Ctx) -> Check:
    g = ctx.which("git")
    if g:
        rc, out = ctx.run([g, "--version"], 15)
        return Check("git", "git（下載與更新用）", "ok", out.splitlines()[0] if rc == 0 and out else g, required=False)
    return Check("git", "git（下載與更新用）", "warn", "沒有安裝：仍可安裝（改用下載 zip），但之後 cpe update 要用控制台的 zip 更新",
                 required=False, fix="install_git", hint="https://git-scm.com/downloads")


def repo_host() -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(repo_url()).hostname or "github.com"
    except ValueError:
        return "github.com"


def check_network(ctx: Ctx) -> Check:
    host = repo_host()
    if ctx.net(host, 443, 6.0):
        return Check("net", "網路（連到 GitHub）", "ok", f"{host} 連得上", required=False)
    if ctx.bundle:
        return Check("net", "網路（連到 GitHub）", "warn", f"連不上 {host}；會用這個資料夾裡的程式安裝（之後要更新需要網路）", required=False)
    return Check("net", "網路（連到 GitHub）", "fail", f"連不上 {host}", hint="請確認網路、代理或防火牆；公司或學校網路可能擋掉 github.com")


def check_disk(ctx: Ctx) -> Check:
    path = ctx.target or ctx.plat.launcher_home
    try:
        mb = ctx.free_mb(path)
    except OSError as e:
        return Check("disk", "磁碟空間", "warn", f"查不到：{e}", required=False)
    if mb < MIN_FREE_MB:
        return Check("disk", "磁碟空間", "fail", f"剩 {mb:.0f} MB，至少需要 {MIN_FREE_MB} MB", hint="清出空間或換一個安裝位置")
    return Check("disk", "磁碟空間", "ok", f"剩 {mb / 1024:.1f} GB", required=False)


def check_writable(ctx: Ctx) -> Check:
    path = ctx.target or ctx.plat.launcher_home
    p = Path(path)
    while not p.exists() and p != p.parent:
        p = p.parent
    if os.access(str(p), os.W_OK):
        return Check("write", "安裝位置可寫入", "ok", str(path), required=False)
    return Check("write", "安裝位置可寫入", "fail", f"沒有寫入權限：{p}", hint="換一個你有權限的位置（例如你的使用者資料夾底下）")


def check_port(ctx: Ctx) -> Check:
    if ctx.port_free(ctx.port):
        return Check("port", f"網頁服務的埠 {ctx.port}", "ok", "可以使用", required=False)
    return Check("port", f"網頁服務的埠 {ctx.port}", "warn", "已被占用，會自動改用別的埠（或已經有一個在執行）", required=False)


def check_compiler(ctx: Ctx) -> Check:
    g = find_gpp(ctx)
    if g:
        return Check("gpp", "C++ 編譯器 g++（階段 4 起需要）", "ok", g, required=False)
    return Check("gpp", "C++ 編譯器 g++（階段 4 起需要）", "info", "尚未安裝；Python 題目不需要，之後要練 C++ 再裝即可",
                 required=False, fix="install_gpp",
                 hint="Windows：安裝 MSYS2 後 pacman -S mingw-w64-ucrt-x86_64-gcc；macOS：xcode-select --install；Linux：安裝 g++")


def check_browser(ctx: Ctx) -> Check:
    b = find_app_browser(ctx)
    if b:
        return Check("browser", "瀏覽器（可開成獨立視窗）", "ok", b, required=False)
    return Check("browser", "瀏覽器（可開成獨立視窗）", "info", "找不到 Edge／Chrome，會用預設瀏覽器開啟分頁", required=False)


def find_app_browser(ctx: Ctx) -> Optional[str]:
    """支援 --app= 的瀏覽器（Edge／Chrome／Chromium），用來把網頁開成像桌面程式的獨立視窗。"""
    s = ctx.plat.system
    cands: List[str] = []
    if s == "windows":
        for base in (ctx.plat.env.get("ProgramFiles(x86)"), ctx.plat.env.get("ProgramFiles"), ctx.plat.env.get("LOCALAPPDATA")):
            if base:
                cands += [str(Path(base) / "Microsoft/Edge/Application/msedge.exe"), str(Path(base) / "Google/Chrome/Application/chrome.exe")]
    elif s == "macos":
        cands += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                  "/Applications/Chromium.app/Contents/MacOS/Chromium"]
    for c in cands:
        if Path(c).exists():
            return c
    for name in ("microsoft-edge", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        w = ctx.which(name)
        if w:
            return w
    return None


def check_existing(ctx: Ctx, installed_version: Optional[str]) -> Check:
    if installed_version is not None:
        return Check("existing", "是否已安裝", "info", f"已安裝（版本 {installed_version or '未知'}）：可以修復、更新或解除安裝", required=False)
    return Check("existing", "是否已安裝", "info", "尚未安裝", required=False)


def run_checks(ctx: Ctx, installed_version: Optional[str] = None, network: bool = True) -> List[Check]:
    out = [check_os(ctx), check_python(ctx), check_tk(ctx), check_git(ctx)]
    if network:
        out.append(check_network(ctx))
    out += [check_disk(ctx), check_writable(ctx), check_port(ctx), check_compiler(ctx), check_browser(ctx), check_existing(ctx, installed_version)]
    return out


def summarize(checks: List[Check]) -> Dict[str, object]:
    blocking = [c for c in checks if c.blocking]
    return {"ok": not blocking, "blocking": [c.id for c in blocking], "warnings": [c.id for c in checks if c.status == "warn"]}


# ---------- 自動修復：安裝計畫 ----------
@dataclass
class FixPlan:
    steps: List[List[str]]
    note: str = ""                                 # 給使用者看的說明（例如會跳出系統授權視窗）
    needs_admin: bool = False
    verify: Optional[str] = None                   # 修復後用哪個檢查代號確認


def linux_manager(ctx: Ctx) -> Optional[str]:
    for m in ("apt-get", "dnf", "pacman", "zypper"):
        if ctx.which(m):
            return m
    return None


LINUX_PKGS = {
    "apt-get": {"git": "git", "gpp": "g++", "tk": "python3-tk"},
    "dnf": {"git": "git", "gpp": "gcc-c++", "tk": "python3-tkinter"},
    "pacman": {"git": "git", "gpp": "gcc", "tk": "tk"},
    "zypper": {"git": "git", "gpp": "gcc-c++", "tk": "python3-tk"},
}


def elevate(ctx: Ctx, cmd: List[str], gui: bool) -> List[str]:
    if ctx.is_admin():
        return cmd
    if gui and ctx.which("pkexec"):
        return ["pkexec"] + cmd
    return ["sudo"] + cmd


def fix_plan(ctx: Ctx, fix_id: str, gui: bool = False) -> Optional[FixPlan]:
    what = {"install_git": "git", "install_gpp": "gpp", "install_tk": "tk"}.get(fix_id)
    if what is None:
        return None
    s = ctx.plat.system
    if s == "windows":
        if what == "tk":
            return None
        if not ctx.which("winget"):
            return None
        base = ["winget", "install", "-e", "--silent", "--accept-package-agreements", "--accept-source-agreements", "--id"]
        if what == "git":
            return FixPlan([base + ["Git.Git"]], "會跳出 Windows 的授權視窗（UAC），請按『是』。", True, "git")
        msys = Path(ctx.plat.env.get("MSYS2_ROOT", r"C:\msys64"))
        return FixPlan([base + ["MSYS2.MSYS2"], [str(msys / "usr/bin/bash.exe"), "-lc", "pacman -S --noconfirm --needed mingw-w64-ucrt-x86_64-gcc"]],
                       "要下載約 300 MB、需要幾分鐘，也會跳出授權視窗。", True, "gpp")
    if s == "macos":
        if what == "tk":
            return None
        if what == "git" and ctx.which("brew"):
            return FixPlan([["brew", "install", "git"]], "", False, "git")
        return FixPlan([["xcode-select", "--install"]], "會跳出 Apple 的『命令列開發者工具』安裝視窗，按『安裝』並等它跑完（要幾分鐘）。", False, what)
    m = linux_manager(ctx)
    if not m:
        return None
    pkg = LINUX_PKGS[m][what]
    install = {"apt-get": ["apt-get", "install", "-y", pkg], "dnf": ["dnf", "install", "-y", pkg],
               "pacman": ["pacman", "-S", "--noconfirm", "--needed", pkg], "zypper": ["zypper", "--non-interactive", "install", pkg]}[m]
    steps = []
    if m == "apt-get":
        steps.append(elevate(ctx, ["apt-get", "update"], gui))
    steps.append(elevate(ctx, install, gui))
    return FixPlan(steps, "需要管理員權限，會請你輸入密碼。" if not ctx.is_admin() else "", not ctx.is_admin(), what)


def apply_fix(ctx: Ctx, fix_id: str, log: Callable[[str], None] = lambda s: None, gui: bool = False) -> Tuple[bool, str]:
    plan = fix_plan(ctx, fix_id, gui)
    if plan is None:
        return False, "這個環境沒辦法自動安裝，請照畫面上的手動做法處理。"
    if plan.note:
        log(plan.note)
    for step in plan.steps:
        log("執行：" + " ".join(step))
        rc, out = ctx.run(step, 1800)
        if out:
            log(out[-400:])
        if rc != 0 and not (step[0] == "xcode-select" and "already installed" in out):
            return False, f"指令失敗（結束碼 {rc}）：{' '.join(step)}"
    return True, "完成"
