"""cpe update：把程式更新到 GitHub 上最新的版本。

只適用於『用 git clone 安裝』的情況（教學裡的標準做法）：更新就是在程式資料夾做一次 fast-forward 的 git pull。
你的學習進度放在『工作區』（cpe init 建立的資料夾），和程式資料夾是分開的，所以更新不會動到它。

安全做法：
- 只做 fast-forward（不產生合併 commit）；本機有改過的檔案、或有沒推送的 commit 時不更新，並說明原因。
- 更新後會用新程式重新 import 一次；如果壞掉，自動退回更新前的版本（這時工作樹是乾淨的，所以 reset 不會弄丟任何東西）。
- 不更新就不連網；`--check` 只查看有沒有新版本，不改任何檔案。
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cpe_coach

GIT_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0", LC_ALL="C")


def repo_root() -> Path:
    return Path(cpe_coach.__file__).resolve().parent.parent


def parse_version(v: str) -> Tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:4])


def read_version(root: Path) -> Optional[str]:
    """不 import、直接從檔案讀版本（更新後新舊程式碼不能混在同一個程序裡）。"""
    try:
        m = re.search(r'__version__\s*=\s*"([^"]+)"', (root / "cpe_coach" / "__init__.py").read_text(encoding="utf-8"))
    except OSError:
        return None
    return m.group(1) if m else None


def _git(root: Path, *args: str, timeout: int = 60) -> Tuple[int, str]:
    try:
        p = subprocess.run(["git", "-C", str(root)] + list(args), capture_output=True, timeout=timeout, env=GIT_ENV)
    except subprocess.TimeoutExpired:
        return 124, f"git {args[0]} 超過 {timeout} 秒沒有回應（網路不通？）"
    except OSError as e:
        return 127, str(e)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace").strip()


def purge_bytecode(root: Path) -> None:
    """刪掉 __pycache__。.pyc 只用『修改時間（秒）加檔案大小』判斷過期：同一秒內改回來、大小又一樣（例如版本號 2.4.1 ↔ 2.4.2）的檔案，舊的 .pyc 會被誤認為有效。"""
    for d in (root / "cpe_coach").rglob("__pycache__"):
        shutil.rmtree(str(d), ignore_errors=True)


def reset_to(root: Path, commit: str) -> Tuple[int, str]:
    """退回到指定的 commit（只在更新後驗證失敗時用；更新前工作樹是乾淨的，所以不會弄丟東西）。"""
    r = _git(root, "reset", "--hard", commit)
    purge_bytecode(root)
    return r


def changelog_since(text: str, old: str, new: str) -> str:
    """CHANGELOG.md 裡版本號 > old 且 <= new 的段落（標題格式：## 2.4.0（日期））。"""
    parts = re.split(r"(?m)^(?=## \d)", text)
    keep = []
    for part in parts:
        m = re.match(r"## (\d+(?:\.\d+)*)", part)
        if m and parse_version(old) < parse_version(m.group(1)) <= parse_version(new):
            keep.append(part.strip())
    return "\n\n".join(keep)


def inspect(root: Path) -> Dict[str, Any]:
    """目前的安裝能不能更新、離遠端差多少。ok=False 時 reason 說明原因。會連網（git fetch）。"""
    info: Dict[str, Any] = {"ok": False, "reason": None, "root": str(root), "version": read_version(root), "commits": []}
    if not (root / ".git").exists():
        info["reason"] = ("這份程式不是用 git 取得的（可能是 zip 解壓、或 pip install . 安裝），所以不能自動更新。"
                          "請照安裝教學（INSTALL.md）用 git clone 重裝一次：你的學習進度在工作區，不受影響。")
        return info
    if shutil.which("git") is None:
        info["reason"] = "找不到 git。請先安裝 git（https://git-scm.com），再執行一次 cpe update。"
        return info
    rc, branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if rc != 0 or branch == "HEAD":
        info["reason"] = "程式資料夾不在任何分支上（detached HEAD），不能自動更新。先 git switch 回你安裝時的分支。"
        return info
    info["branch"] = branch
    rc, up = _git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if rc != 0:
        info["reason"] = f"分支 {branch} 沒有對應的遠端分支。執行：git -C \"{root}\" branch --set-upstream-to=origin/{branch} {branch}"
        return info
    info["upstream"] = up
    rc, out = _git(root, "rev-parse", "--short", "HEAD")
    info["commit"] = out
    rc, out = _git(root, "fetch", "--quiet")
    if rc != 0:
        info["reason"] = "連不上 GitHub（git fetch 失敗）：" + out[-300:]
        return info
    rc, behind = _git(root, "rev-list", "--count", "HEAD..@{u}")
    rc2, ahead = _git(root, "rev-list", "--count", "@{u}..HEAD")
    if rc or rc2:
        info["reason"] = "無法比較本機與遠端的版本：" + (behind if rc else ahead)
        return info
    info["behind"], info["ahead"] = int(behind), int(ahead)
    rc, dirty = _git(root, "status", "--porcelain", "--untracked-files=no")
    info["dirty"] = bool(dirty.strip())
    info["dirty_files"] = [ln[3:] for ln in dirty.splitlines()][:10]
    rc, log = _git(root, "log", "--format=%h%x09%s", "-n", "30", "HEAD..@{u}")
    info["commits"] = [tuple(ln.split("\t", 1)) for ln in log.splitlines() if "\t" in ln]
    info["ok"] = True
    return info


def managed_update(root: Path, check_only: bool) -> Optional[Dict[str, Any]]:
    """用安裝精靈裝的（下載 zip 或複製資料夾）沒有 .git：更新交給精靈的引擎處理。不是這種安裝就回傳 None。"""
    try:
        from .launcher import config as launcher_config
        from .launcher import engine
        from .launcher.envcheck import Ctx
        from .launcher.osinfo import detect
        plat = detect()
        cfg = launcher_config.load(plat.launcher_home)
    except Exception:
        return None
    if cfg is None or Path(cfg.app_dir).resolve() != Path(root).resolve():
        return None
    base: Dict[str, Any] = {"root": str(root), "version": cfg.version, "branch": cfg.branch, "commit": str(cfg.source.get("sha") or "")[:7],
                            "upstream": f"GitHub（{cfg.branch}，下載 zip）", "commits": [], "ahead": 0, "behind": 0}
    r = engine.check_update(cfg) if check_only else engine.update(cfg, plat, Ctx(plat=plat))
    st = r["status"]
    if st == "available":
        return dict(base, status="available", behind=1)
    if st == "updated":
        return dict(base, **{k: r[k] for k in ("old_version", "new_version", "notes")}, status="updated", old_commit=base["commit"],
                    new_commit=str((r.get("source") or {}).get("sha") or "")[:7])
    return dict(base, status=st, reason=r.get("reason", ""))


def apply(root: Path, check_only: bool = False) -> Dict[str, Any]:
    """回傳 {status, ...}。status：unavailable／up_to_date／available（只檢查）／blocked／updated／rolled_back。"""
    if not (root / ".git").exists():
        managed = managed_update(root, check_only)
        if managed is not None:
            return managed
    info = inspect(root)
    if not info["ok"]:
        return dict(info, status="unavailable")
    if info["behind"] == 0:
        return dict(info, status="up_to_date")
    if check_only:
        return dict(info, status="available")
    if info["ahead"]:
        return dict(info, status="blocked", reason=f"本機有 {info['ahead']} 個還沒推送的 commit，和遠端分歧；為了不弄亂你的修改，不自動合併。")
    if info["dirty"]:
        return dict(info, status="blocked",
                    reason="程式檔有被你修改過：" + "、".join(info["dirty_files"]) + "。先 git stash（暫存）或 git checkout .（放棄修改）再更新。")
    old = info["commit"]
    old_version = info["version"] or "0"
    rc, out = _git(root, "merge", "--ff-only", "@{u}")
    if rc != 0:
        return dict(info, status="blocked", reason="無法 fast-forward 更新：" + out[-300:])
    purge_bytecode(root)                                  # 更新跟上一次執行在同一秒內、檔案大小又一樣（版本號）時，舊的 .pyc 會被當成有效
    env = dict(os.environ, PYTHONPATH=str(root))
    chk = subprocess.run([sys.executable, "-B", "-c", "import cpe_coach.cli, cpe_coach; print(cpe_coach.__version__)"], cwd=str(root), env=env,
                         capture_output=True, timeout=60)
    if chk.returncode != 0:
        reset_to(root, old)
        return dict(info, status="rolled_back", reason="新版程式無法載入，已自動退回更新前的版本（" + old + "）：" +
                    chk.stderr.decode("utf-8", "replace").strip()[-300:])
    new_version = chk.stdout.decode("utf-8", "replace").strip() or read_version(root) or old_version
    notes = ""
    try:
        notes = changelog_since((root / "CHANGELOG.md").read_text(encoding="utf-8"), old_version, new_version)
    except OSError:
        pass
    rc, new_commit = _git(root, "rev-parse", "--short", "HEAD")
    return dict(info, status="updated", old_commit=old, new_commit=new_commit, old_version=old_version, new_version=new_version, notes=notes)
