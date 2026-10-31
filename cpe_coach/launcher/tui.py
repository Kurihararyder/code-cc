"""文字模式的安裝精靈與控制台（沒有圖形畫面、沒有 tkinter 時使用；功能和圖形版一樣，因為都呼叫 engine）。

輸入輸出都可以注入，所以能用腳本化的輸入完整測試。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, List, Optional

from . import constants as C
from . import engine, envcheck, server
from .config import LauncherConfig
from .engine import EngineError, InstallOptions, Reporter, UninstallOptions
from .envcheck import Ctx
from .osinfo import Plat

BAR = "─" * 54


class TUI:
    def __init__(self, plat: Plat, ctx: Ctx, inp: Optional[Callable[[str], str]] = None, out: Callable[[str], None] = print, assume_yes: bool = False):
        self.plat, self.ctx, self.out, self.assume_yes = plat, ctx, out, assume_yes
        self.custom_input = inp is not None
        self.inp = inp if inp is not None else (lambda prompt="": input(prompt))         # 呼叫當下才取 input（預設參數會在定義時就綁死，測試無法替換）

    # ---------- 輸入輸出 ----------
    def say(self, text: str = "") -> None:
        self.out(text)

    def ask(self, prompt: str, default: str = "") -> str:
        if self.assume_yes:
            return default
        try:
            v = self.inp(f"{prompt}" + (f"［{default}］" if default else "") + "：").strip()
        except EOFError:
            raise KeyboardInterrupt                      # 沒有輸入可讀（例如被導向、Ctrl-D）：視為中斷，絕不能當成『全部用預設值』去安裝
        return v or default

    def yes(self, prompt: str, default: bool = True) -> bool:
        if self.assume_yes:
            return default
        try:
            v = self.inp(f"{prompt} [{'Y/n' if default else 'y/N'}] ").strip().lower()
        except EOFError:
            raise KeyboardInterrupt
        return default if not v else v in ("y", "yes", "是", "好", "1")

    def reporter(self, cancel=None) -> Reporter:
        rep_index = [0]

        def on_step(i: int, n: int, name: str) -> None:
            rep_index[0] = i
            self.say(f"\n[{i + 1}/{n}] {name}")

        def on_log(line: str) -> None:
            if line.startswith("== ") or (rep_index[0] == 0 and line[:2] in ("✓ ", "! ", "✗ ", "· ")):
                return                                      # 步驟標題另外顯示；環境檢測的結果前面已經列過了
            for ln in line.splitlines():
                self.say("   " + ln)

        return engine.make_reporter(self.plat, on_step, on_log, cancel)

    def show_checks(self, checks: List[envcheck.Check]) -> None:
        for c in checks:
            self.say(f" {engine.MARK[c.status]} {c.label}：{c.detail}")
            if c.hint and c.status in ("fail", "warn"):
                self.say(f"     → {c.hint}")

    # ---------- 安裝精靈 ----------
    def wizard(self, opts: Optional[InstallOptions] = None) -> int:
        self.say(f"\n{BAR}\n  {C.APP_NAME} 安裝精靈（文字模式）\n{BAR}")
        st = engine.installed_state(self.plat)
        if st.installed and st.cfg is not None and not self.assume_yes:
            self.say(f"\n偵測到已經安裝：版本 {st.cfg.version}，位置 {st.cfg.app_dir}")
            for p in st.problems:
                self.say(f" ! {p}")
            pick = self.menu("要做什麼？", ["開啟控制台", "修復", "更新", "重新安裝", "解除安裝"], default=2 if st.problems else 1)
            if pick == 0:
                return 0
            if pick == 1:
                return self.panel()
            if pick == 2:
                return self.run_repair(st.cfg)
            if pick == 3:
                return self.run_update(st.cfg)
            if pick == 5:
                return self.uninstall_flow(st.cfg)
        opts = opts or engine.default_options(self.plat)
        self.say("\n正在檢測環境…")
        self.ctx.target, self.ctx.port, self.ctx.bundle = opts.app_dir, opts.port, opts.bundle
        checks = envcheck.run_checks(self.ctx, st.cfg.version if st.cfg else None)
        self.show_checks(checks)
        blocking = [c for c in checks if c.blocking]
        if blocking:
            self.say("\n✗ 有必須先解決的問題（見上面的『→』說明）。解決後再執行一次安裝。")
            return 1
        for c in checks:
            if c.fix and c.status in ("warn", "info") and c.fix not in opts.fixes:
                plan = envcheck.fix_plan(self.ctx, c.fix)
                if plan is None:
                    continue
                want_default = c.fix == "install_git"
                if self.yes(f"\n要自動安裝「{c.label}」嗎？{'（' + plan.note + '）' if plan.note else ''}", want_default and not self.assume_yes):
                    opts.fixes.append(c.fix)
        if not self.assume_yes:
            opts.app_dir = Path(self.ask("\n程式安裝位置", str(opts.app_dir)))
            opts.workspace = Path(self.ask("學習進度資料夾（你的解答與紀錄放這裡，建議放在文件資料夾）", str(opts.workspace)))
            opts.desktop = self.yes("建立桌面捷徑？", opts.desktop)
            opts.menu = self.yes("建立開始功能表／應用程式選單捷徑？", opts.menu)
            opts.add_path = self.yes("讓終端機可以直接輸入 cpe 指令？", opts.add_path)
            self.say(f"\n即將安裝：\n  程式：{opts.app_dir}\n  學習進度：{opts.workspace}\n  來源：{opts.source}（分支 {opts.branch}）")
            if not self.yes("開始安裝？", True):
                self.say("已取消，沒有做任何變更。")
                return 1
        try:
            cfg = engine.install(opts, self.plat, self.ctx, self.reporter())
        except EngineError as e:
            self.say(f"\n✗ 安裝失敗：{e}\n（已把這一次做的變更復原；詳細紀錄在 {self.plat.launcher_home / 'logs' / 'launcher.log'}）")
            return 1
        self.say(f"\n{BAR}\n  ✓ 安裝完成：{C.APP_NAME} {cfg.version}\n{BAR}")
        self.say(f"  控制台：{'桌面或開始功能表的「' + C.APP_NAME + '」' if cfg.shortcuts else 'python ' + str(Path(cfg.app_dir) / 'cpe-panel.pyw')}")
        self.say(f"  學習進度：{cfg.workspace}")
        if not self.assume_yes and self.yes("\n現在開啟學習畫面嗎？", True):
            return self.do_open(cfg)
        return 0

    def menu(self, title: str, items: List[str], default: int = 1) -> int:
        self.say(f"\n{title}")
        for i, it in enumerate(items, 1):
            self.say(f"  {i}) {it}")
        self.say("  0) 離開")
        v = self.ask("請輸入數字", str(default))
        return int(v) if v.isdigit() and 0 <= int(v) <= len(items) else 0

    # ---------- 操作 ----------
    def do_open(self, cfg: LauncherConfig, open_ui: bool = True) -> int:
        try:
            st = server.start(cfg, self.plat, log=lambda s: self.say("   " + s))
        except server.ServerError as e:
            self.say(f"✗ {e}")
            return 1
        if open_ui:
            server.open_ui(st.url, cfg, self.plat, lambda s: self.say("   " + s))
        self.say(f"✓ 已開啟：{st.url}")
        return 0

    def do_close(self, cfg: LauncherConfig) -> int:
        try:
            closed = server.stop(cfg, self.plat, lambda s: self.say("   " + s))
        except server.ServerError as e:
            self.say(f"✗ {e}")
            return 1
        self.say("✓ 已關閉" if closed else "服務原本就是關閉的")
        return 0

    def run_repair(self, cfg: LauncherConfig) -> int:
        try:
            engine.repair(cfg, self.plat, self.ctx, self.reporter(), engine.find_bundle())
        except EngineError as e:
            self.say(f"✗ 修復失敗：{e}")
            return 1
        self.say("✓ 修復完成")
        return 0

    def run_update(self, cfg: LauncherConfig, check_only: bool = False) -> int:
        if check_only:
            info = engine.check_update(cfg)
            self.say({"available": "✓ 有新版本可以更新", "up_to_date": "✓ 已經是最新版", "unavailable": "✗ " + str(info.get("reason", ""))}.get(info["status"], str(info)))
            return 0 if info["status"] != "unavailable" else 1
        r = engine.update(cfg, self.plat, self.ctx, self.reporter())
        st = r["status"]
        if st == "updated":
            self.say(f"\n✓ 已更新：{r['old_version']} → {r['new_version']}")
            if r.get("notes"):
                self.say("\n這次更新的內容：\n" + r["notes"])
            self.say("\n請重新開啟控制台，新版才會生效。")
            return 0
        if st == "up_to_date":
            self.say("✓ 已經是最新版")
            return 0
        self.say("✗ " + str(r.get("reason", st)))
        return 1

    def uninstall_flow(self, cfg: LauncherConfig, remove_workspace: Optional[bool] = None, backup_dir: Optional[Path] = None) -> int:
        self.say(f"\n{BAR}\n  解除安裝 {C.APP_NAME}\n{BAR}")
        self.say(f"會移除：程式（{cfg.app_dir}）、捷徑、指令{'、「應用程式與功能」裡的項目' if self.plat.is_windows else ''}。")
        self.say(f"你的學習進度（{cfg.workspace}）預設會保留。")
        if remove_workspace is None:
            remove_workspace = (not self.assume_yes) and self.yes("要連學習進度一起刪除嗎？（刪除後無法復原）", False)
        if remove_workspace:
            if backup_dir is None and not self.assume_yes and self.yes("刪除前先備份一份到桌面？", True):
                backup_dir = self.plat.desktop_dir if self.plat.desktop_dir.is_dir() else self.plat.home
            if not self.assume_yes and self.ask("請輸入 DELETE 確認刪除學習進度", "") != "DELETE":
                self.say("沒有輸入 DELETE，已取消。")
                return 1
        elif not self.assume_yes and not self.yes("確定要解除安裝嗎？", False):
            self.say("已取消。")
            return 1
        try:
            r = engine.uninstall(cfg, self.plat, UninstallOptions(remove_workspace, backup_dir), self.reporter())
        except EngineError as e:
            self.say(f"✗ {e}")
            return 1
        for p in r["problems"]:
            self.say(f" ! {p}")
        if r["backup"]:
            self.say(f"學習進度備份：{r['backup']}")
        self.say(f"✓ 已解除安裝。{'學習進度已刪除。' if r['workspace_removed'] else '學習進度保留在 ' + r['workspace']}")
        return 0

    def guarded(self, fn: Callable[[], None]) -> None:
        """控制台的工具失敗時只顯示原因，回到選單，不要整個程式崩潰。"""
        try:
            fn()
        except (EngineError, ValueError, OSError) as e:
            self.say(f"✗ {e}")

    def encrypted_backup(self, cfg) -> None:
        import getpass
        prompt = "備份密碼（至少 8 個字元；忘了就救不回來）"
        pw = self.ask(prompt, "") if (self.custom_input or self.assume_yes) else getpass.getpass(prompt + "：")      # 真人在終端機輸入時不顯示密碼
        if len(pw) < 8:
            self.say("✗ 密碼至少 8 個字元，沒有備份。")
            return
        dest = self.plat.desktop_dir if self.plat.desktop_dir.is_dir() else self.plat.home
        self.guarded(lambda: self.say(f"✓ 已加密備份：{engine.encrypted_backup_now(cfg, dest, pw)}"))

    # ---------- 控制台 ----------
    def panel(self) -> int:
        while True:
            st = engine.installed_state(self.plat)
            if not st.installed or st.cfg is None:
                self.say("尚未安裝。")
                return self.wizard()
            cfg = st.cfg
            sv = server.status(cfg, self.plat)
            state = {"running": f"● 執行中  {sv.url}", "stopped": "○ 已關閉", "unresponsive": "! 沒有回應"}[sv.state]
            self.say(f"\n{BAR}\n  {C.APP_NAME} 控制台　版本 {cfg.version}\n  狀態：{state}\n{BAR}")
            for line in engine.summary_lines(engine.learning_summary(cfg)):
                self.say("  今天：" + line)
            for p in st.problems:
                self.say(f" ! {p}")
            items = ["關閉服務" if sv.running else "開啟（啟動並開啟學習畫面）", "重新開啟學習畫面", "檢查並套用更新", "備份學習進度", "開啟學習進度資料夾", "環境檢測", "修復", "解除安裝",
                     "加密備份", "同步到共用資料夾", "安裝每日複習提醒", "資料與隱私（存了什麼、什麼會連網）"]
            n = self.menu("要做什麼？", items, default=1)
            if n == 0:
                return 0
            if n == 1:
                (self.do_close if sv.running else self.do_open)(cfg)
            elif n == 2:
                self.do_open(cfg)
            elif n == 3:
                self.run_update(cfg)
            elif n == 4:
                dest = engine.backup_now(cfg, self.plat.desktop_dir if self.plat.desktop_dir.is_dir() else self.plat.home)
                self.say(f"✓ 已備份：{dest}")
            elif n == 5:
                engine.open_folder(Path(cfg.workspace))
            elif n == 6:
                self.say(engine.report_text(self.plat, self.ctx))
            elif n == 7:
                self.run_repair(cfg)
            elif n == 8:
                if self.uninstall_flow(cfg) == 0:
                    return 0
            elif n == 9:
                self.encrypted_backup(cfg)
            elif n == 10:
                folder = self.ask("共用資料夾的路徑（Dropbox、隨身碟…）", "")
                self.guarded(lambda: self.say(engine.sync_now(cfg, Path(folder)))) if folder else self.say("沒有輸入資料夾。")
            elif n == 11:
                self.say(engine.reminder_plan(cfg)["text"])
                if self.yes("要現在安裝每天 19:30 的複習提醒嗎？", False):
                    self.guarded(lambda: self.say("✓ " + engine.install_reminder(cfg)))
            elif n == 12:
                self.say(engine.privacy_text(cfg))


def stdout_is_tty() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False
