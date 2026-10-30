"""開啟／關閉本機網頁服務（cpe web）。

狀態不只看 PID 檔：用『連到 /api/ping』確認那個埠上跑的真的是 CPE 教練、而且是哪個程序。
所以不管服務是控制台開的、還是你自己在終端機執行 cpe web 開的，控制台都認得、也都能關。
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .config import LauncherConfig
from .envcheck import Ctx, find_app_browser, port_is_free
from .osinfo import Plat

RUN_FILE = "server.json"
LOG_MAX = 1 << 20
_children: Dict[int, subprocess.Popen] = {}               # 這個程序自己開的服務：結束後要 poll() 才不會留下殭屍程序


class ServerError(RuntimeError):
    pass


@dataclass
class Status:
    state: str                                            # running | stopped | unresponsive
    port: int
    pid: Optional[int] = None
    url: str = ""
    workspace: str = ""
    version: str = ""
    external: bool = False                                # 不是控制台開的（例如在終端機執行的 cpe web）

    @property
    def running(self) -> bool:
        return self.state == "running"


def run_dir(plat: Plat) -> Path:
    return plat.launcher_home / "run"


def log_path(plat: Plat) -> Path:
    return plat.launcher_home / "logs" / "server.log"


def _read_run(plat: Plat) -> Optional[Dict[str, Any]]:
    try:
        d = json.loads((run_dir(plat) / RUN_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) and isinstance(d.get("pid"), int) and isinstance(d.get("port"), int) else None


def _write_run(plat: Plat, data: Dict[str, Any]) -> None:
    d = run_dir(plat)
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / (RUN_FILE + ".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    os.replace(str(tmp), str(d / RUN_FILE))


def _clear_run(plat: Plat) -> None:
    try:
        (run_dir(plat) / RUN_FILE).unlink()
    except OSError:
        pass


# ---------- 程序存活 ----------
def pid_alive(pid: int) -> bool:
    child = _children.get(pid)
    if child is not None:
        return child.poll() is None
    if sys.platform == "win32":
        return _win_alive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return not _is_zombie(pid)


def _is_zombie(pid: int) -> bool:
    """已經結束、但父程序（例如另一個開著的控制台）還沒回收的程序：os.kill(pid, 0) 仍然成功，實際上已經死了。"""
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8", errors="replace") as f:
            return f.read().rsplit(")", 1)[1].split()[0] == "Z"
    except (OSError, IndexError):
        pass
    try:
        out = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, timeout=5).stdout.decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError):
        return False
    return out.startswith("Z")


def _win_alive(pid: int) -> bool:
    """Windows 的 os.kill(pid, 0) 會真的送出 Ctrl 事件、不能拿來探測；改用 OpenProcess + GetExitCodeProcess。"""
    import ctypes
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.restype = wintypes.HANDLE
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    h = k.OpenProcess(0x1000, False, pid)                  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return ctypes.get_last_error() == 5                # 存取被拒：程序存在但不是我們的
    try:
        code = wintypes.DWORD()
        return bool(k.GetExitCodeProcess(h, ctypes.byref(code))) and code.value == 259     # STILL_ACTIVE
    finally:
        k.CloseHandle(h)


def probe(port: int, timeout: float = 1.5) -> Optional[Dict[str, Any]]:
    """連到 /api/ping。是 CPE 教練的服務回傳 {app, version, pid, port, workspace}，其他情況回傳 None。不走代理。"""
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with op.open(f"http://127.0.0.1:{port}/api/ping", timeout=timeout) as r:
            data = json.loads(r.read(8192).decode("utf-8", "replace"))
    except (urllib.error.URLError, OSError, ValueError):
        return None
    return data if isinstance(data, dict) and data.get("app") == "cpe-coach" and isinstance(data.get("pid"), int) else None


def _status_from(data: Dict[str, Any], port: int, external: bool) -> Status:
    return Status("running", port, data["pid"], f"http://127.0.0.1:{port}/", str(data.get("workspace", "")), str(data.get("version", "")), external)


def status(cfg: LauncherConfig, plat: Plat) -> Status:
    rec = _read_run(plat)
    if rec:
        data = probe(rec["port"])
        if data:
            return _status_from(data, rec["port"], False)
    data = probe(cfg.port)
    if data:
        return _status_from(data, cfg.port, True)
    if rec and pid_alive(rec["pid"]):
        return Status("unresponsive", rec["port"], rec["pid"], f"http://127.0.0.1:{rec['port']}/")
    if rec:
        _clear_run(plat)
    return Status("stopped", cfg.port)


# ---------- 開啟 ----------
def pick_port(preferred: int, is_free: Callable[[int], bool] = port_is_free, span: int = 50) -> int:
    for p in range(preferred, preferred + span):
        if is_free(p):
            return p
    raise ServerError(f"{preferred}–{preferred + span - 1} 的埠都被占用了")


def server_command(cfg: LauncherConfig, port: int) -> List[str]:
    return [cfg.python, "-u", "-m", "cpe_coach", "web", "--port", str(port), "--no-open"]


def server_env(cfg: LauncherConfig) -> Dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = cfg.app_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _same_dir(a: Any, b: Path) -> bool:
    try:
        return bool(a) and Path(str(a)).resolve() == Path(b).resolve()
    except OSError:
        return False


def _log_tail(path: Path, n: int = 600) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-n:].strip()
    except OSError:
        return ""


def start(cfg: LauncherConfig, plat: Plat, wait: float = 45.0, log: Callable[[str], None] = lambda s: None,
          is_free: Callable[[int], bool] = port_is_free) -> Status:
    """啟動服務並等到真的連得上；已經在跑就直接回傳。失敗丟 ServerError（附上紀錄檔的結尾）。"""
    st = status(cfg, plat)
    if st.running:
        return st
    if st.state == "unresponsive":
        stop(cfg, plat, log)
    ws = Path(cfg.workspace)
    if not ws.is_dir():
        raise ServerError(f"學習進度資料夾不見了：{ws}。到控制台的『維護』按『修復』可以重建。")
    if not Path(cfg.python).exists():
        raise ServerError(f"記錄的 Python 找不到了：{cfg.python}。到控制台的『維護』按『修復』。")
    port = pick_port(cfg.port, is_free)
    if port != cfg.port:
        log(f"埠 {cfg.port} 被別的程式占用，改用 {port}")
    lp = log_path(plat)
    lp.parent.mkdir(parents=True, exist_ok=True)
    if lp.exists() and lp.stat().st_size > LOG_MAX:
        lp.write_text("", encoding="utf-8")
    out = open(lp, "ab")
    kw: Dict[str, Any] = {}
    if sys.platform == "win32":
        kw["creationflags"] = 0x08000000 | 0x00000200      # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    out.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} 啟動 {' '.join(server_command(cfg, port))}\n".encode("utf-8"))
    out.flush()
    try:
        p = subprocess.Popen(server_command(cfg, port), cwd=str(ws), env=server_env(cfg), stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT, **kw)
    except OSError as e:
        out.close()
        raise ServerError(f"無法啟動：{e}")
    out.close()
    _children[p.pid] = p
    _write_run(plat, {"pid": p.pid, "port": port, "started": time.time()})
    deadline = time.time() + wait
    while time.time() < deadline:
        data = probe(port, 1.0)
        if data and (data["pid"] == p.pid or (p.poll() is None and _same_dir(data.get("workspace"), ws))):
            if data["pid"] != p.pid:                      # 啟動器（例如虛擬環境的 python.exe）另外開了真正的服務程序：以服務自己回報的為準
                _write_run(plat, {"pid": data["pid"], "port": port, "started": time.time()})
            log(f"服務已啟動：http://127.0.0.1:{port}/")
            return _status_from(data, port, False)
        if p.poll() is not None:
            _clear_run(plat)
            raise ServerError(f"服務一啟動就結束了（結束碼 {p.returncode}）：\n{_log_tail(lp)}")
        time.sleep(0.15)
    kill_tree(p.pid)
    _clear_run(plat)
    raise ServerError(f"{wait:.0f} 秒內沒有啟動完成：\n{_log_tail(lp)}")


# ---------- 關閉 ----------
def kill_tree(pid: int, grace: float = 6.0) -> bool:
    """結束服務與它開出的子程序（判題用的）。先請它收尾，逾時才強制結束。回傳是否已經結束。"""
    if not pid_alive(pid):
        return True
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, creationflags=0x08000000)
    else:
        group = False
        try:
            group = os.getpgid(pid) == pid                  # 是自己的程序群組領頭才能整組結束，否則只結束它本身
        except OSError:
            pass
        _signal(pid, signal.SIGTERM, group)
        end = time.time() + grace
        while time.time() < end and pid_alive(pid):
            time.sleep(0.1)
        if pid_alive(pid):
            _signal(pid, signal.SIGKILL, group)
    end = time.time() + 5
    while time.time() < end and pid_alive(pid):
        time.sleep(0.1)
    return not pid_alive(pid)


def _signal(pid: int, sig: int, group: bool) -> None:
    try:
        if group:
            os.killpg(pid, sig)
        else:
            os.kill(pid, sig)
    except (ProcessLookupError, PermissionError):
        pass


def stop(cfg: LauncherConfig, plat: Plat, log: Callable[[str], None] = lambda s: None) -> bool:
    """關閉服務。原本就沒開回傳 False；成功關掉回傳 True；關不掉丟 ServerError。"""
    st = status(cfg, plat)
    if st.state == "stopped" or st.pid is None:
        _clear_run(plat)
        return False
    log(f"關閉服務（程序 {st.pid}）")
    if not kill_tree(st.pid):
        raise ServerError(f"無法結束程序 {st.pid}，請用工作管理員結束它")
    _children.pop(st.pid, None)
    _clear_run(plat)
    return True


# ---------- 開畫面 ----------
def open_ui(url: str, cfg: LauncherConfig, plat: Plat, log: Callable[[str], None] = lambda s: None) -> str:
    """開啟學習畫面：有 Edge／Chrome 就用獨立應用視窗（像桌面程式），否則用預設瀏覽器。回傳 app 或 browser。"""
    if cfg.opt("app_window"):
        b = find_app_browser(Ctx(plat=plat))
        if b:
            try:
                kw: Dict[str, Any] = {}
                if sys.platform == "win32":
                    kw["creationflags"] = 0x08000000
                subprocess.Popen([b, f"--app={url}", "--window-size=1320,880"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)
                return "app"
            except OSError as e:
                log(f"無法開啟獨立視窗（{e}），改用預設瀏覽器")
    try:
        webbrowser.open(url)
    except Exception as e:
        log(f"無法開啟瀏覽器（{e}）；請手動開啟 {url}")
    return "browser"
