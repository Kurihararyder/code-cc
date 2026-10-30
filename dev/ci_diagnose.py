"""CI 診斷：印出幾項跟平台有關、容易出問題的量測，出事時日誌裡就有線索。不會讓 CI 失敗（只印資訊）。
  - 名稱解析要多久（macOS 的虛擬機上曾經讓網頁服務卡 30 秒）
  - 網頁服務從啟動到能連線要多久
  - Windows：用幾種方式建立 .lnk，哪一種可以、PowerShell 的版本與原則
用法：python dev/ci_diagnose.py
"""
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def timed(label, fn):
    t = time.time()
    try:
        res = fn()
        note = repr(res)[:120]
    except Exception as e:                                   # 診斷：什麼例外都只記錄
        note = f"{type(e).__name__}: {e}"
    print(f"  {label:<46} {time.time() - t:6.2f}s  {note}", flush=True)


def sh(cmd, timeout=60, **kw):
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout, **kw)
        return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace").strip()
    except Exception as e:
        return 127, f"{type(e).__name__}: {e}"


def names():
    print("== 名稱解析與本機連線", flush=True)
    timed("socket.gethostname()", socket.gethostname)
    timed("socket.getfqdn('127.0.0.1')  ← HTTPServer 啟動時會做", lambda: socket.getfqdn("127.0.0.1"))
    timed("socket.gethostbyaddr('127.0.0.1')", lambda: socket.gethostbyaddr("127.0.0.1"))
    timed("socket.getaddrinfo('localhost', 80)", lambda: socket.getaddrinfo("localhost", 80)[:1])
    timed("socket.getfqdn()", socket.getfqdn)
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    from cpe_coach.web import LocalServer

    def bind(cls):
        s = cls(("127.0.0.1", 0), BaseHTTPRequestHandler)
        s.server_close()
        return cls.__name__
    timed("標準 ThreadingHTTPServer 綁定", lambda: bind(ThreadingHTTPServer))
    timed("LocalServer 綁定（我們用的）", lambda: bind(LocalServer))
    if sys.platform == "darwin":
        for cmd in (["sw_vers"], ["scutil", "--dns"], ["cat", "/etc/hosts"]):
            rc, out = sh(cmd)
            print(f"  $ {' '.join(cmd)} → {rc}\n    " + "\n    ".join(out.splitlines()[:14]), flush=True)


def web_start():
    print("== 網頁服務啟動時間", flush=True)
    tmp = Path(tempfile.mkdtemp(prefix="cpe-diag-"))
    ws = tmp / "ws"
    env = dict(os.environ, PYTHONPATH=str(REPO), PYTHONUTF8="1", PYTHONFAULTHANDLER="1")
    rc, out = sh([sys.executable, "-m", "cpe_coach", "init", str(ws)], env=env, cwd=str(tmp))
    print(f"  cpe init → {rc} {out.splitlines()[0] if out else ''}", flush=True)
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    log = tmp / "web.log"
    t0 = time.time()
    with open(log, "wb") as f:
        p = subprocess.Popen([sys.executable, "-u", "-X", "faulthandler", "-m", "cpe_coach", "web", "--port", str(port), "--no-open"],
                             cwd=str(ws), env=env, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    up = None
    import urllib.request
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while time.time() - t0 < 60:
        try:
            with opener.open(f"http://127.0.0.1:{port}/api/ping", timeout=1) as r:
                up = (time.time() - t0, r.read()[:100])
                break
        except Exception:
            time.sleep(0.2)
    print(f"  {'連得上：%.2f 秒' % up[0] if up else '60 秒內連不上'}  {up[1] if up else ''}", flush=True)
    if not up:
        try:                                                 # 看它卡在哪（Windows 沒有 SIGABRT 的行為，所以只在 POSIX 做）
            if sys.platform != "win32":
                import signal
                p.send_signal(signal.SIGABRT)
                time.sleep(1)
        except OSError:
            pass
    p.terminate()
    try:
        p.wait(10)
    except subprocess.TimeoutExpired:
        p.kill()
    print("  伺服器輸出：" + log.read_text(encoding="utf-8", errors="replace")[-1500:].replace("\n", "\n    "), flush=True)


def lnk():
    print("== Windows 建立 .lnk", flush=True)
    import ctypes
    from cpe_coach.launcher import shortcuts
    print(f"  系統 ANSI 字碼頁 GetACP() = {ctypes.windll.kernel32.GetACP()}（英文版 1252：WScript.Shell 處理不了中文路徑）", flush=True)
    rc, out = sh(["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString(); $ExecutionContext.SessionState.LanguageMode"])
    print(f"  PowerShell → {rc} {out.replace(chr(10), ' | ')[:200]}", flush=True)
    tmp = Path(tempfile.mkdtemp(prefix="cpe-lnk-"))
    icon = str(REPO / "cpe_coach" / "launcher" / "assets" / "icon.ico")
    base = {"target": sys.executable, "args": '"C:\\a b\\x.pyw" open', "wd": str(tmp), "icon": icon, "desc": "診斷"}
    for label, name in (("A 正式使用的方式（IShellLinkW，Unicode），中文檔名", "測試 捷徑.lnk"), ("A 同上，英文檔名", "plain.lnk")):
        logs = []
        t0 = time.time()
        res = shortcuts.make_lnks([dict(base, lnk=str(tmp / name))], sys.executable, log=logs.append)
        print(f"  {label}：{res}  {time.time() - t0:.2f}s  {logs}", flush=True)
    for label, name in (("W 對照：WScript.Shell，英文檔名", "w-plain.lnk"), ("W 對照：WScript.Shell，中文檔名", "w-測試.lnk")):
        ps = "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:CPE_L);$s.TargetPath=$env:CPE_T;$s.Save()"
        rc, out = sh(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], env=dict(os.environ, CPE_L=str(tmp / name), CPE_T=sys.executable))
        print(f"  {label}：rc={rc} 檔案存在={(tmp / name).exists()} 輸出={out[:160]!r}", flush=True)
    desk = Path(os.path.expanduser("~")) / "Desktop"
    print(f"  桌面資料夾 {desk} 存在={desk.is_dir()}；APPDATA={os.environ.get('APPDATA')}", flush=True)


if __name__ == "__main__":
    print(f"Python {sys.version.split()[0]}  {sys.platform}  {os.name}", flush=True)
    names()
    web_start()
    if sys.platform == "win32":
        lnk()
