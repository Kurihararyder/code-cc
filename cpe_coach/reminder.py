"""複習提醒：到期的複習題累積了，就跳出桌面通知。

做法：`cpe remind check` 檢查一次（沒有到期的、剛提醒過、或在安靜時段都不會打擾你）；`cpe remind install` 印出（或 --apply 時執行）
讓作業系統每天固定時間呼叫它的指令（Linux crontab、macOS launchd、Windows 工作排程器）。程式本身不會常駐背景。

誠實的限制：通知與排程的安裝指令我只在 Linux 的測試環境驗證過指令的產生與檢查邏輯；真正的桌面通知（notify-send／osascript／PowerShell）
和 launchd／工作排程器的安裝，我沒有在真的 macOS／Windows 桌面上跑過。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from . import bank as bank_mod
from . import memory

QUIET = (22, 7)                      # 晚上 10 點到早上 7 點不通知
MIN_GAP_H = 8


def _state_path(ws) -> Path:
    return ws.meta / "reminder.json"


def summary(ws) -> Dict[str, Any]:
    bank = bank_mod.load_bank(ws)
    rp, ft = memory.build(ws, bank)
    due = memory.due_now(rp.cards, ws.now(), ft.k, due_fn=memory.make_due_fn(ws))
    return {"due": len(due), "items": [{"id": d.pid, "retention": round(d.r_now, 2), "title": bank.get(d.pid, {}).get("title", d.pid)} for d in due[:5]]}


def in_quiet_hours(ts: float) -> bool:
    h = time.localtime(ts).tm_hour
    return h >= QUIET[0] or h < QUIET[1]


def should_notify(ws, due: int) -> Tuple[bool, str]:
    now = ws.now()
    if due <= 0:
        return False, "沒有到期的複習"
    if in_quiet_hours(now):
        return False, "安靜時段"
    try:
        last = json.loads(_state_path(ws).read_text(encoding="utf-8")).get("last", 0)
    except (OSError, ValueError):
        last = 0
    if now - last < MIN_GAP_H * 3600:
        return False, "剛提醒過"
    return True, ""


def notify(title: str, message: str) -> Tuple[bool, str]:
    """送出桌面通知；失敗只回傳 (False, 原因)，不丟例外。"""
    try:
        if sys.platform.startswith("linux") and shutil.which("notify-send"):
            subprocess.run(["notify-send", title, message], timeout=10, check=True)
            return True, "notify-send"
        if sys.platform == "darwin" and shutil.which("osascript"):
            esc = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')      # noqa: E731
            subprocess.run(["osascript", "-e", f'display notification "{esc(message)}" with title "{esc(title)}"'], timeout=10, check=True)
            return True, "osascript"
        if os.name == "nt" and shutil.which("powershell"):
            ps = ("Add-Type -AssemblyName System.Windows.Forms;$n=New-Object System.Windows.Forms.NotifyIcon;$n.Icon=[System.Drawing.SystemIcons]::Information;"
                  "$n.Visible=$true;$n.ShowBalloonTip(8000,$env:CPE_T,$env:CPE_M,'Info');Start-Sleep -Seconds 9;$n.Dispose()")
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], timeout=30, check=True, env=dict(os.environ, CPE_T=title, CPE_M=message))
            return True, "powershell"
    except (OSError, subprocess.SubprocessError) as e:
        return False, str(e)
    return False, "這台機器沒有可用的通知方式"


def check(ws, notifier: Callable[[str, str], Tuple[bool, str]] = notify, force: bool = False) -> Dict[str, Any]:
    s = summary(ws)
    ok, why = (True, "") if (force and s["due"] > 0) else should_notify(ws, s["due"])
    res = {"due": s["due"], "notified": False, "reason": why, "items": s["items"]}
    if not ok:
        return res
    names = "、".join(i["id"] for i in s["items"][:3])
    sent, how = notifier("CPE 教練：該複習了", f"有 {s['due']} 題的記憶快要退了（{names}）。花 10 分鐘複習效果最好。")
    res.update(notified=sent, reason="" if sent else how, method=how)
    if sent:
        _state_path(ws).write_text(json.dumps({"last": ws.now()}), encoding="utf-8")
    return res


def install_plan(ws, hour: int = 19, minute: int = 30, platform: Optional[str] = None, python: Optional[str] = None) -> Dict[str, Any]:
    """產生安裝每日提醒的指令（不執行）。"""
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError("時間不正確")
    platform = platform or ("windows" if os.name == "nt" else "macos" if sys.platform == "darwin" else "linux")
    py = python or sys.executable
    root = str(ws.root)
    if platform == "linux":
        line = f'{minute} {hour} * * * cd "{root}" && "{py}" -m cpe_coach remind check'
        return {"platform": platform, "kind": "crontab", "line": line, "apply": ["crontab"], "uninstall": "crontab -e（刪掉含有 cpe_coach remind 的那一行）",
                "text": "加入 crontab（crontab -e）這一行：\n" + line + "\n（桌面通知要有 notify-send；cron 環境下可能需要設定 DISPLAY／DBUS_SESSION_BUS_ADDRESS。）"}
    if platform == "macos":
        label = "com.cpe-coach.remind"
        path = str(Path.home() / "Library" / "LaunchAgents" / f"{label}.plist")
        plist = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0"><dict>\n'
                 f'<key>Label</key><string>{label}</string>\n<key>ProgramArguments</key><array><string>{py}</string><string>-m</string><string>cpe_coach</string><string>remind</string><string>check</string></array>\n'
                 f'<key>WorkingDirectory</key><string>{root}</string>\n<key>StartCalendarInterval</key><dict><key>Hour</key><integer>{hour}</integer><key>Minute</key><integer>{minute}</integer></dict>\n</dict></plist>\n')
        return {"platform": platform, "kind": "launchd", "path": path, "content": plist, "apply": ["launchctl", "load", path], "uninstall": f"launchctl unload {path} && rm {path}",
                "text": f"把下面的內容存成 {path}，再執行 launchctl load {path}：\n" + plist}
    cmd = ["schtasks", "/Create", "/SC", "DAILY", "/TN", "CPE Coach Reminder", "/TR", f'cmd /c cd /d "{root}" && "{py}" -m cpe_coach remind check', "/ST", f"{hour:02d}:{minute:02d}", "/F"]
    return {"platform": "windows", "kind": "schtasks", "command": cmd, "apply": cmd, "uninstall": 'schtasks /Delete /TN "CPE Coach Reminder" /F', "text": "在命令提示字元執行：\n" + subprocess.list2cmdline(cmd)}


def apply_install(plan: Dict[str, Any]) -> Tuple[bool, str]:
    """真的安裝（只在使用者明確加 --apply 時才會呼叫）。"""
    try:
        if plan["kind"] == "crontab":
            cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            lines = [ln for ln in (cur.stdout if cur.returncode == 0 else "").splitlines() if "cpe_coach remind check" not in ln]
            subprocess.run(["crontab", "-"], input="\n".join(lines + [plan["line"]]) + "\n", text=True, check=True, timeout=20)
        elif plan["kind"] == "launchd":
            Path(plan["path"]).parent.mkdir(parents=True, exist_ok=True)
            Path(plan["path"]).write_text(plan["content"], encoding="utf-8")
            subprocess.run(plan["apply"], check=True, timeout=20)
        else:
            subprocess.run(plan["apply"], check=True, timeout=30)
        return True, "已安裝"
    except (OSError, subprocess.SubprocessError) as e:
        return False, f"安裝失敗：{e}"
