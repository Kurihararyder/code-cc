"""安裝精靈測試的共用工具：暫時的 git 倉庫（當作 GitHub）、本機 zip 伺服器、隔離的路徑與環境。
測試絕不碰真正的家目錄、桌面、開始功能表、PATH 與『應用程式與功能』清單。"""
import http.server
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path
from typing import Callable, Dict, Optional

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from cpe_coach.web import LocalServer  # noqa: E402  不做反向 DNS 查詢（macOS 上會卡 30 秒）
GIT_ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
HAVE_GIT = shutil.which("git") is not None
COPY_ROOT_FILES = ["CHANGELOG.md", "cpe-panel.pyw"]


def git(cwd, *args) -> str:
    p = subprocess.run(["git", "-C", str(cwd)] + list(args), capture_output=True, env=GIT_ENV)
    assert p.returncode == 0, (args, p.stderr.decode("utf-8", "replace"))
    return p.stdout.decode("utf-8", "replace").strip()


def copy_app_tree(dest: Path) -> Path:
    """複製目前這份程式（不含 .git 與暫存檔）：當作『GitHub 上的程式』。"""
    shutil.copytree(REPO / "cpe_coach", dest / "cpe_coach", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for f in COPY_ROOT_FILES:
        shutil.copy2(REPO / f, dest / f)
    return dest


def make_origin(parent: Path, branch: str = "main") -> Path:
    origin = Path(parent) / "origin"
    origin.mkdir(parents=True)
    copy_app_tree(origin)
    git(origin, "init", "-q", "-b", branch)
    git(origin, "add", "-A")
    git(origin, "commit", "-q", "-m", "init")
    return origin


def set_version(root: Path, version: str, note: str = "測試用的新版本。", break_launcher: bool = False) -> None:
    """改一份程式資料夾的版本號與更新紀錄（break_launcher：讓安裝精靈本身載入失敗，用來測更新後的退回）。"""
    import re
    init = Path(root) / "cpe_coach" / "__init__.py"
    init.write_text(re.sub(r'__version__ = "[^"]+"', f'__version__ = "{version}"', init.read_text(encoding="utf-8")), encoding="utf-8")
    log = Path(root) / "CHANGELOG.md"
    log.write_text(log.read_text(encoding="utf-8").replace("\n## ", f"\n## {version}（2099-01-01）\n- {note}\n\n## ", 1), encoding="utf-8")
    if break_launcher:
        (Path(root) / "cpe_coach" / "launcher" / "engine.py").write_text("this is not python (\n", encoding="utf-8")


def bump_version(origin: Path, version: str, note: str = "測試用的新版本。", break_launcher: bool = False) -> None:
    set_version(origin, version, note, break_launcher)
    git(origin, "add", "-A")
    git(origin, "commit", "-q", "-m", f"v{version}")


def make_zip(src: Path, dest_zip: Path, top: str = "code-cc-main") -> Path:
    """像 GitHub 的 archive 一樣：外面多包一層資料夾。"""
    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(Path(src).rglob("*")):
            rel = f.relative_to(src)
            if f.is_file() and ".git" not in rel.parts and "__pycache__" not in rel.parts:
                z.write(f, f"{top}/{rel.as_posix()}")
    return dest_zip


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class FileServer:
    """本機 HTTP 伺服器：/archive.zip 與 /sha 兩個固定網址，內容可以隨時換（模擬 GitHub 上有新版本）。"""

    def __init__(self) -> None:
        self.zip_bytes = b""
        self.sha = "0" * 40
        self.fail = False
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                if outer.fail:
                    self.send_response(503)
                    self.end_headers()
                    return
                body = outer.zip_bytes if self.path.endswith(".zip") else outer.sha.encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        self.httpd = LocalServer(("127.0.0.1", 0), H)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    @property
    def archive_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/archive.zip"

    @property
    def sha_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/sha"

    def publish(self, zip_path: Path, sha: str) -> None:
        self.zip_bytes, self.sha = Path(zip_path).read_bytes(), sha

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def isolated_env(tmp: Path) -> Dict[str, str]:
    """家目錄、桌面、開始功能表、控制台資料夾全部導到暫存資料夾；Windows 的登錄改寫到另一個機碼。"""
    home = tmp / "home"
    for d in ("home", "desktop", "menu", "launcher"):
        (tmp / d).mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(HOME=str(home), USERPROFILE=str(home), LOCALAPPDATA=str(home / "AppData" / "Local"), APPDATA=str(home / "AppData" / "Roaming"),
               CPE_LAUNCHER_HOME=str(tmp / "launcher"), CPE_LAUNCHER_DESKTOP=str(tmp / "desktop"), CPE_LAUNCHER_MENU=str(tmp / "menu"),
               CPE_LAUNCHER_REG_SANDBOX=f"Software\\CPE-Coach-Test-{os.getpid()}-{int(time.time() * 1000) % 100000}")
    env.pop("CPE_HOME", None)
    return env


def clean_registry(env: Dict[str, str]) -> None:
    if sys.platform != "win32" or not env.get("CPE_LAUNCHER_REG_SANDBOX"):
        return
    import winreg

    def delete_tree(root, sub):
        try:
            k = winreg.OpenKey(root, sub, 0, winreg.KEY_ALL_ACCESS)
        except OSError:
            return
        with k:
            while True:
                try:
                    child = winreg.EnumKey(k, 0)
                except OSError:
                    break
                delete_tree(root, sub + "\\" + child)
        try:
            winreg.DeleteKey(root, sub)
        except OSError:
            pass
    delete_tree(winreg.HKEY_CURRENT_USER, env["CPE_LAUNCHER_REG_SANDBOX"])


def wait_for(cond: Callable[[], bool], timeout: float = 20.0, step: float = 0.1) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(step)
    return cond()


class TempDir:
    """暫存資料夾。清理時用會去掉唯讀屬性、遇到被防毒短暫鎖住會重試的刪法（Windows 上 git 物件是唯讀的）。"""

    def __init__(self) -> None:
        self.path = Path(tempfile.mkdtemp(prefix="cpe-lt-")).resolve()

    def cleanup(self) -> None:
        from cpe_coach.launcher import source
        source.rmtree(self.path)


def tree_removed(p: Optional[Path]) -> bool:
    return p is None or not Path(p).exists()
