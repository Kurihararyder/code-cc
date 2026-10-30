"""取得程式本體：git clone（優先）、下載 GitHub 的 zip、或複製這個資料夾（沒有網路時）。

做法：先放到旁邊的暫存資料夾，通過驗證（真的能 import）才換成正式位置；任何一步失敗都不會留下半成品，
舊版本（修復／更新時）會先改名保留，換成功才刪。
"""
from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from urllib.parse import urlparse
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import constants as C
from ..updater import changelog_since, read_version

Log = Callable[[str], None]
UA = "cpe-coach-installer"
SKIP_COPY = (".git", "__pycache__", "*.pyc", "*.zip", "*.pid", "node_modules", ".pytest_cache", "*.egg-info", "cpe-workspace")


class SourceError(RuntimeError):
    pass


def _noop(_: str) -> None:
    pass


def run(cmd: List[str], timeout: int = 900, cwd: Optional[Path] = None, env: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
    kw: Dict[str, Any] = {}
    if sys.platform == "win32":
        kw["creationflags"] = 0x08000000                              # CREATE_NO_WINDOW
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout, cwd=str(cwd) if cwd else None, env=env, **kw)
    except subprocess.TimeoutExpired:
        return 124, f"{cmd[0]} 超過 {timeout} 秒沒有回應"
    except OSError as e:
        return 127, str(e)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace").strip()


def git_env() -> Dict[str, str]:
    return dict(os.environ, GIT_TERMINAL_PROMPT="0", LC_ALL="C")


# ---------- 檔案處理 ----------
def rmtree(path: Path, tries: int = 6) -> bool:
    """刪資料夾。Windows 上 git 物件是唯讀、防毒軟體可能暫時鎖住檔案：去掉唯讀、重試幾次。"""
    path = Path(path)
    if not path.exists() and not path.is_symlink():
        return True

    def onerror(func, p, _exc):
        try:
            os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
            func(p)
        except OSError:
            pass

    for i in range(tries):
        if path.is_symlink() or path.is_file():
            try:
                path.unlink()
            except OSError:
                pass
        else:
            shutil.rmtree(str(path), onerror=onerror)
        if not path.exists():
            return True
        time.sleep(0.4 * (i + 1))
    return not path.exists()


def is_app_tree(p: Path) -> bool:
    return (Path(p) / "cpe_coach" / "__init__.py").is_file()


def check_target(app_dir: Path) -> None:
    """安裝位置必須是不存在、空的、或是先前裝過的（避免誤把使用者的其他資料夾當成安裝位置，之後解除安裝時被刪掉）。"""
    p = Path(app_dir)
    if not p.exists():
        return
    if not p.is_dir():
        raise SourceError(f"安裝位置不是資料夾：{p}")
    if any(p.iterdir()) and not is_app_tree(p):
        raise SourceError(f"安裝位置 {p} 不是空的，而且看起來不是 CPE 教練的資料夾。請選一個空資料夾，或選一個還不存在的名稱。")


def swap_in(new_dir: Path, app_dir: Path) -> Optional[Path]:
    """new_dir 換成 app_dir。舊的先改名保留（回傳舊路徑，成功後由呼叫端刪除）；換失敗就改回去。"""
    new_dir, app_dir = Path(new_dir), Path(app_dir)
    app_dir.parent.mkdir(parents=True, exist_ok=True)
    old: Optional[Path] = None
    if app_dir.exists():
        old = app_dir.with_name(f"{app_dir.name}.old-{int(time.time())}")
        for i in range(5):
            try:
                os.replace(str(app_dir), str(old))
                break
            except OSError as e:
                if i == 4:
                    raise SourceError(f"無法替換舊版程式資料夾（可能有程式正在使用它）：{e}")
                time.sleep(0.6)
    try:
        os.replace(str(new_dir), str(app_dir))
    except OSError as e:
        if old is not None:
            try:
                os.replace(str(old), str(app_dir))
            except OSError:
                pass
        raise SourceError(f"無法放到安裝位置 {app_dir}：{e}")
    return old


def staging_dir(app_dir: Path) -> Path:
    p = Path(app_dir).with_name(Path(app_dir).name + ".new")
    rmtree(p)
    return p


def verify_import(python: str, app_dir: Path) -> str:
    """用記錄的 Python 真的載入一次，回傳版本。-I 不受使用者環境變數影響；-S 不載入 site-packages（不會被別處裝的同名套件，例如開發用的 pip install -e 蓋過去）；
    -B 不寫 .pyc（驗證失敗要退回時，不會留下對應新版原始碼、但原始碼已被退回的過期 .pyc）。"""
    code = "import sys; sys.path.insert(0, sys.argv[1]); import cpe_coach, cpe_coach.cli, cpe_coach.web, cpe_coach.launcher.engine; print(cpe_coach.__version__)"
    rc, out = run([python, "-I", "-S", "-B", "-c", code, str(app_dir)], 90, cwd=Path(tempfile.gettempdir()))
    if rc != 0:
        raise SourceError("新放進去的程式無法載入：" + out[-400:])
    return out.splitlines()[-1].strip()


# ---------- git ----------
def git_clone(url: str, branch: str, dest: Path, log: Log = _noop, git: Optional[str] = None) -> Dict[str, Any]:
    git = git or shutil.which("git")
    if not git:
        raise SourceError("找不到 git")
    log(f"git clone {url}（分支 {branch}）")
    rc, out = run([git, "clone", "--quiet", "-c", "core.autocrlf=false", "--branch", branch, "--single-branch", url, str(dest)], 900, env=git_env())
    if rc != 0:
        raise SourceError("git clone 失敗：" + out[-400:])
    _, sha = run([git, "-C", str(dest), "rev-parse", "--short", "HEAD"], 30)
    return {"type": "git", "commit": sha, "url": url, "branch": branch}


# ---------- zip ----------
def opener(url: str = "") -> urllib.request.OpenerDirector:
    """一般用系統的代理設定；連到本機（測試用的伺服器）時不走代理。"""
    host = (urlparse(url).hostname or "") if url else ""
    if host in ("127.0.0.1", "localhost", "::1"):
        return urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return urllib.request.build_opener()


def download(url: str, dest: Path, log: Log = _noop, timeout: int = 60, progress: Optional[Callable[[int, int], None]] = None) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    log(f"下載 {url}")
    try:
        with opener(url).open(req, timeout=timeout) as r, open(dest, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            got = 0
            while True:
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if progress:
                    progress(got, total)
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise SourceError(f"下載失敗：{e}")
    if total and got < total:
        raise SourceError(f"下載不完整（{got}／{total} 位元組）")
    return got


def remote_sha(branch: str, timeout: int = 15) -> Optional[str]:
    """GitHub 上這個分支最新 commit 的 sha（只用來判斷 zip 安裝有沒有新版本）。查不到回傳 None。"""
    req = urllib.request.Request(C.api_commit_url(branch), headers={"User-Agent": UA, "Accept": "application/vnd.github.sha"})
    try:
        with opener(C.api_commit_url(branch)).open(req, timeout=timeout) as r:
            body = r.read(65536).decode("utf-8", "replace")
    except (urllib.error.URLError, OSError, ValueError):
        return None
    m = re.search(r"\b[0-9a-f]{40}\b", body)
    return m.group(0) if m else None


def extract_zip(zip_path: Path, dest: Path) -> Path:
    """解到 dest，回傳程式根目錄（GitHub 的 zip 外面多包一層資料夾）。"""
    try:
        with zipfile.ZipFile(zip_path) as z:
            bad = z.testzip()
            if bad:
                raise SourceError(f"下載的壓縮檔損毀（{bad}）")
            base = Path(dest).resolve()
            for m in z.infolist():
                t = (base / m.filename).resolve()
                if t != base and base not in t.parents:
                    raise SourceError("壓縮檔含有不安全的路徑，已中止")
            z.extractall(str(dest))
    except zipfile.BadZipFile:
        raise SourceError("下載到的不是有效的壓縮檔（可能被網路設備擋掉或改寫）")
    if is_app_tree(dest):
        return Path(dest)
    subs = [d for d in Path(dest).iterdir() if d.is_dir()]
    for d in subs:
        if is_app_tree(d):
            return d
    raise SourceError("壓縮檔裡找不到 cpe_coach 程式資料夾")


def fetch_zip(url: str, branch: str, dest: Path, log: Log = _noop, progress: Optional[Callable[[int, int], None]] = None) -> Dict[str, Any]:
    tmp = Path(tempfile.mkdtemp(prefix="cpe-zip-"))
    try:
        z = tmp / "src.zip"
        download(url, z, log, progress=progress)
        root = extract_zip(z, tmp / "x")
        shutil.move(str(root), str(dest))
    finally:
        rmtree(tmp)
    return {"type": "zip", "sha": remote_sha(branch) or "", "url": url, "branch": branch}


# ---------- bundle ----------
def copy_bundle(src: Path, dest: Path, log: Log = _noop) -> Dict[str, Any]:
    src = Path(src)
    if not is_app_tree(src):
        raise SourceError(f"{src} 不是 CPE 教練的程式資料夾")
    log(f"複製 {src}")
    shutil.copytree(str(src), str(dest), ignore=shutil.ignore_patterns(*SKIP_COPY))
    return {"type": "bundle", "from": str(src)}


# ---------- 組合 ----------
def choose(kind: str, have_git: bool, have_net: bool, bundle: Optional[Path]) -> str:
    """auto：有 git 且有網路 → git；有網路 → zip；否則用這個資料夾裡的程式。"""
    if kind in ("git", "zip", "bundle"):
        return kind
    if have_net and have_git:
        return "git"
    if have_net:
        return "zip"
    if bundle is not None:
        return "bundle"
    raise SourceError("連不上 GitHub，而且沒有可以直接安裝的本機程式。請確認網路後再試。")


def fetch(kind: str, branch: str, dest: Path, python: str, bundle: Optional[Path] = None, log: Log = _noop,
          progress: Optional[Callable[[int, int], None]] = None) -> Dict[str, Any]:
    """把程式放到 dest（尚未存在的資料夾），驗證可以載入，回傳 source 紀錄（含 version）。"""
    if kind == "git":
        src = git_clone(C.repo_url(), branch, dest, log)
    elif kind == "zip":
        src = fetch_zip(C.archive_url(branch), branch, dest, log, progress)
    elif kind == "bundle":
        if bundle is None:
            raise SourceError("沒有指定本機程式資料夾")
        src = copy_bundle(bundle, dest, log)
    else:
        raise SourceError(f"不認得的來源：{kind}")
    src["version"] = verify_import(python, dest)
    log(f"程式版本 {src['version']}")
    return src


# ---------- zip 安裝的更新（沒有 .git 時） ----------
def zip_check(source: Dict[str, Any], branch: str) -> Dict[str, Any]:
    latest = remote_sha(branch)
    if latest is None:
        return {"ok": False, "reason": "連不上 GitHub，無法檢查更新。"}
    cur = source.get("sha") or ""
    return {"ok": True, "latest": latest, "current": cur, "available": cur != latest}


def zip_update(app_dir: Path, python: str, branch: str, old_source: Dict[str, Any], log: Log = _noop) -> Dict[str, Any]:
    """重新下載、驗證後整個換掉；驗證失敗保留舊版。回傳 {status, old_version, new_version, notes, source}。"""
    old_version = read_version(app_dir) or "0"
    stage = staging_dir(app_dir)
    try:
        src = fetch_zip(C.archive_url(branch), branch, stage, log)
        new_version = verify_import(python, stage)
    except SourceError:
        rmtree(stage)
        raise
    src["version"] = new_version
    old = swap_in(stage, app_dir)
    if old is not None:
        rmtree(old)
    notes = ""
    try:
        notes = changelog_since((Path(app_dir) / "CHANGELOG.md").read_text(encoding="utf-8"), old_version, new_version)
    except OSError:
        pass
    return {"status": "updated", "old_version": old_version, "new_version": new_version, "notes": notes, "source": src}
