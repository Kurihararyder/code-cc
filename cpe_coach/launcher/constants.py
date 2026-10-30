"""名稱、預設值與下載網址。網址與倉庫可用環境變數覆寫（測試與自架鏡像用）。"""
from __future__ import annotations

import os

APP_ID = "cpe-coach"
APP_NAME = "CPE 教練"                    # 顯示名稱（捷徑、視窗標題）
APP_DIR_NAME = "CPE-Coach"               # 資料夾名稱用 ASCII，避免某些工具遇到非 ASCII 路徑出問題
DEFAULT_WORKSPACE_NAME = "CPE學習進度"
DEFAULT_PORT = 8765
MIN_PYTHON = (3, 9)
MIN_FREE_MB = 400
LAUNCHER_FILE = "launcher.json"
DEFAULT_SLUG = "Kurihararyder/code-cc"
DEFAULT_BRANCH = "claude/clever-archimedes-ekcn2m"


def slug() -> str:
    return os.environ.get("CPE_REPO_SLUG", DEFAULT_SLUG)


def repo_url() -> str:
    return os.environ.get("CPE_REPO_URL") or f"https://github.com/{slug()}.git"


def archive_url(branch: str) -> str:
    return (os.environ.get("CPE_ARCHIVE_URL") or f"https://github.com/{slug()}/archive/refs/heads/{{branch}}.zip").replace("{branch}", branch)


def api_commit_url(branch: str) -> str:
    return (os.environ.get("CPE_API_COMMIT_URL") or f"https://api.github.com/repos/{slug()}/commits/{{branch}}").replace("{branch}", branch)


def raw_url(branch: str, path: str) -> str:
    base = os.environ.get("CPE_RAW_URL") or f"https://raw.githubusercontent.com/{slug()}/{{branch}}"
    return base.replace("{branch}", branch).rstrip("/") + "/" + path.lstrip("/")


def default_branch() -> str:
    return os.environ.get("CPE_INSTALL_BRANCH", DEFAULT_BRANCH)
