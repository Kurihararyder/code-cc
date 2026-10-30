"""CI 用：安裝精靈真的在這個作業系統上裝完／解除安裝之後，檢查該有的東西都在、該消失的都消失了（用預設位置，在一次性的虛擬機上跑）。
用法：python dev/ci_installer_check.py installed      安裝後：程式、學習進度、指令、捷徑、登錄（Windows）、服務開關
      python dev/ci_installer_check.py removed        解除安裝後：全部清乾淨，只有學習進度還在
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

for _stream in (sys.stdout, sys.stderr):                    # Windows 的 CI 預設 cp1252，印不出 ✓ 與中文
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from cpe_coach.launcher import config, server, shortcuts  # noqa: E402
from cpe_coach.launcher.osinfo import detect  # noqa: E402

plat = detect()
problems = []


def check(ok, msg):
    print(("✓ " if ok else "✗ ") + msg)
    if not ok:
        problems.append(msg)


def wait(cond, timeout=90):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(1)
    return cond()


def launcher(*args):
    script = Path(__file__).resolve().parent.parent / "cpe-panel.pyw"
    return subprocess.run([sys.executable, str(script)] + list(args), capture_output=True, timeout=180)


def installed():
    cfg = config.load(plat.launcher_home)
    check(cfg is not None, f"launcher.json 存在（{plat.launcher_home}）")
    if cfg is None:
        return
    app, ws = Path(cfg.app_dir), Path(cfg.workspace)
    check((app / "cpe_coach" / "__init__.py").is_file(), f"程式資料夾 {app}")
    check((ws / ".cpe" / "state.json").is_file(), f"學習進度資料夾 {ws}")
    check(bool(cfg.shortcuts) and all(Path(p).exists() or Path(p).is_symlink() for p in cfg.shortcuts), f"捷徑 {len(cfg.shortcuts)} 個都存在：{cfg.shortcuts}")
    if plat.is_windows:
        check(all(p.lower().endswith(".lnk") for p in cfg.shortcuts), "Windows 的捷徑都是真正的 .lnk（不是建立失敗時的 .cmd 備案）")
    shim = shortcuts.bin_dir(plat) / ("cpe.cmd" if plat.is_windows else "cpe")
    r = subprocess.run([str(shim), "--version"], capture_output=True, timeout=60, cwd=str(ws))
    check(r.returncode == 0 and b"cpe " in r.stdout, f"cpe 指令可用：{r.stdout.decode('utf-8', 'replace').strip()}")
    if plat.is_windows:
        check(shortcuts.uninstall_entry_exists(plat), "『應用程式與功能』有 CPE 教練的項目")
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            path, _ = winreg.QueryValueEx(k, "Path")
        check(str(shortcuts.bin_dir(plat)) in path.split(";"), "使用者 PATH 有 cpe 指令的資料夾")
    r = launcher("open", "--text", "--no-browser")
    check(r.returncode == 0, "open（啟動服務）：" + r.stdout.decode("utf-8", "replace").strip().splitlines()[-1])
    st = server.status(cfg, plat)
    check(st.running and server.probe(st.port) is not None, f"服務執行中：{st.url}")
    r = launcher("status", "--json")
    check(r.returncode == 0 and json.loads(r.stdout.decode("utf-8"))["state"] == "running", "status 回報執行中")
    r = launcher("close", "--text")
    check(r.returncode == 0, "close（關閉服務）")
    check(wait(lambda: server.probe(st.port) is None, 20), "服務已經關閉（連線被拒絕）")
    r = launcher("status")
    check(r.returncode == 3, "status 回報已關閉")
    r = launcher("doctor")
    check(r.returncode == 0 and "已安裝" in r.stdout.decode("utf-8", "replace"), "doctor 能跑")


def removed(ws_path):
    check(config.load(plat.launcher_home) is None, "launcher.json 已移除")
    check(wait(lambda: not plat.launcher_home.exists(), 90), f"控制台資料夾已刪除：{plat.launcher_home}")
    check(not any(p.exists() for p in plat.menu_dir.glob("*CPE*")), f"開始功能表／應用程式選單沒有殘留（{plat.menu_dir}）")
    check(not any(p.exists() for p in plat.desktop_dir.glob("*CPE*")) and not any(p.exists() for p in plat.desktop_dir.glob("cpe-coach*")), "桌面沒有殘留")
    if plat.is_windows:
        check(not shortcuts.uninstall_entry_exists(plat), "『應用程式與功能』的項目已移除")
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            path, _ = winreg.QueryValueEx(k, "Path")
        check(str(shortcuts.bin_dir(plat)) not in path.split(";"), "使用者 PATH 已清掉")
    else:
        check(not any((plat.home / ".local" / "bin" / n).is_symlink() for n in ("cpe", "cpe-panel")), "~/.local/bin 裡的 cpe 與 cpe-panel 連結已移除")
    check((Path(ws_path) / ".cpe" / "state.json").is_file(), f"學習進度還在：{ws_path}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "installed":
        installed()
    elif mode == "removed":
        removed(sys.argv[2])
    else:
        sys.exit(__doc__)
    sys.exit(1 if problems else 0)
