"""launcher.json：記錄安裝在哪、用哪個 Python、工作區在哪、來源是哪種。"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Optional

from .constants import DEFAULT_PORT, LAUNCHER_FILE

SCHEMA = 1
DEFAULT_OPTIONS = {"open_browser": True, "app_window": True, "autostart_server": False, "stop_on_exit": "ask", "check_update_on_open": True,
                   "desktop_shortcut": True, "menu_shortcut": True, "add_path": True}


@dataclass
class LauncherConfig:
    app_dir: str
    workspace: str
    python: str
    branch: str = ""
    source: Dict[str, Any] = field(default_factory=dict)            # {"type": git|zip|bundle, "commit"/"sha": ..., "url": ...}
    version: str = ""
    port: int = DEFAULT_PORT
    options: Dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_OPTIONS))
    shortcuts: List[str] = field(default_factory=list)              # 建立過的捷徑（解除安裝時移除）
    registered: Dict[str, Any] = field(default_factory=dict)        # {"registry": bool, "path_entry": str}
    installed_at: float = 0.0
    schema: int = SCHEMA

    def opt(self, key: str) -> Any:
        return self.options.get(key, DEFAULT_OPTIONS.get(key))


def path_of(home: Path) -> Path:
    return Path(home) / LAUNCHER_FILE


def load(home: Path) -> Optional[LauncherConfig]:
    p = path_of(home)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict) or not raw.get("app_dir") or not raw.get("workspace"):
        return None
    names = {f.name for f in fields(LauncherConfig)}
    cfg = LauncherConfig(**{k: v for k, v in raw.items() if k in names})
    cfg.options = dict(DEFAULT_OPTIONS, **(cfg.options or {}))
    return cfg


def save(home: Path, cfg: LauncherConfig) -> None:
    p = path_of(home)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(asdict(cfg), ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(str(tmp), str(p))


def touch_installed(cfg: LauncherConfig) -> LauncherConfig:
    cfg.installed_at = cfg.installed_at or time.time()
    return cfg
