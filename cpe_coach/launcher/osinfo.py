"""各作業系統的路徑與慣例。所有路徑計算都是純函式（可用假的 system／env 在任何平台測試）。"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Mapping, Optional

from .constants import APP_DIR_NAME, DEFAULT_WORKSPACE_NAME


@dataclass(frozen=True)
class Plat:
    system: str                                   # windows | macos | linux
    home: Path
    machine: str = ""
    env: Mapping[str, str] = field(default_factory=dict)

    @property
    def is_windows(self) -> bool:
        return self.system == "windows"

    @property
    def is_macos(self) -> bool:
        return self.system == "macos"

    @property
    def label(self) -> str:
        return {"windows": "Windows", "macos": "macOS", "linux": "Linux"}[self.system] + (f"（{self.machine}）" if self.machine else "")

    # ---- 程式與設定放哪裡 ----
    @property
    def launcher_home(self) -> Path:
        """launcher.json、紀錄、執行狀態、cpe 指令捷徑放這裡。CPE_LAUNCHER_HOME 可覆寫（測試用）。"""
        if self.env.get("CPE_LAUNCHER_HOME"):
            return Path(self.env["CPE_LAUNCHER_HOME"])
        if self.is_windows:
            return Path(self.env.get("LOCALAPPDATA") or self.home / "AppData" / "Local") / APP_DIR_NAME
        if self.is_macos:
            return self.home / "Library" / "Application Support" / APP_DIR_NAME
        return Path(self.env.get("XDG_DATA_HOME") or self.home / ".local" / "share") / "cpe-coach"

    @property
    def default_workspace(self) -> Path:
        return self.home / DEFAULT_WORKSPACE_NAME

    @property
    def desktop_dir(self) -> Path:
        if self.env.get("CPE_LAUNCHER_DESKTOP"):
            return Path(self.env["CPE_LAUNCHER_DESKTOP"])
        if self.is_windows:
            return known_folder_windows(0x10, self.home / "Desktop")           # CSIDL_DESKTOPDIRECTORY（OneDrive 轉向也算得到）
        return self.home / "Desktop"

    @property
    def menu_dir(self) -> Path:
        """開始功能表（Windows）／應用程式（macOS）／應用程式選單（Linux）。"""
        if self.env.get("CPE_LAUNCHER_MENU"):
            return Path(self.env["CPE_LAUNCHER_MENU"])
        if self.is_windows:
            return Path(self.env.get("APPDATA") or self.home / "AppData" / "Roaming") / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        if self.is_macos:
            return self.home / "Applications"
        return Path(self.env.get("XDG_DATA_HOME") or self.home / ".local" / "share") / "applications"

    @property
    def exe_suffix(self) -> str:
        return ".exe" if self.is_windows else ""


def known_folder_windows(csidl: int, fallback: Path) -> Path:
    if sys.platform != "win32":
        return fallback
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(260)
        if ctypes.windll.shell32.SHGetFolderPathW(0, csidl, 0, 0, buf) == 0 and buf.value:
            return Path(buf.value)
    except Exception:
        pass
    return fallback


def detect(env: Optional[Mapping[str, str]] = None, system: Optional[str] = None, home: Optional[Path] = None) -> Plat:
    env = dict(os.environ if env is None else env)
    if system is None:
        system = "windows" if sys.platform == "win32" else "macos" if sys.platform == "darwin" else "linux"
    import platform as _pf
    return Plat(system, Path(home) if home else Path(os.path.expanduser("~")), _pf.machine(), env)


def pythonw_for(python: str) -> str:
    """Windows 上 GUI 要用 pythonw.exe（不會跳出黑色視窗）；找不到就用原本的。"""
    p = Path(python)
    if p.name.lower() == "python.exe":
        w = p.with_name("pythonw.exe")
        if w.exists():
            return str(w)
    return python


def env_as_dict(plat: Plat) -> Dict[str, str]:
    return dict(plat.env)
