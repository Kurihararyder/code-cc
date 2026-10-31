"""圖形介面的安裝精靈與控制台（tkinter，標準函式庫，不需要安裝任何套件）。

所有動作都在背景執行緒做（下載、安裝、啟動服務…），結果用佇列交回主執行緒更新畫面（tkinter 不能在別的執行緒操作）。
真正的工作都在 engine／server，這裡只負責畫面；所以圖形版和文字版行為一致。
"""
from __future__ import annotations

import gc
import queue
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import config as cfgmod
from . import constants as C
from . import engine, envcheck, server, shortcuts
from .config import LauncherConfig
from .engine import Reporter, UninstallOptions
from .envcheck import Ctx
from .osinfo import Plat

PAL = {"bg": "#f4f5fa", "surface": "#ffffff", "surface2": "#eef0f7", "surface3": "#e1e5f1", "border": "#dfe3ee", "text": "#151a2a", "text2": "#465068",
       "text3": "#646d85", "accent": "#4f46e5", "accent_hover": "#4338ca", "accent_soft": "#ecedff", "ok": "#157a3e", "ok_soft": "#e5f5eb",
       "bad": "#bf2a1f", "bad_soft": "#fdeceb", "warn": "#9a5805", "warn_soft": "#fff3dc", "side": "#1b1f3b", "side_text": "#e9ecf4", "side_dim": "#9aa3c7"}
FONTS = {"windows": ["Microsoft JhengHei UI", "Microsoft JhengHei", "微軟正黑體"], "macos": ["PingFang TC", "Heiti TC"],
         "linux": ["Noto Sans CJK TC", "Noto Sans TC", "WenQuanYi Zen Hei", "Droid Sans Fallback", "Noto Sans CJK JP"]}
MONO = ["Consolas", "Menlo", "DejaVu Sans Mono", "Liberation Mono", "Courier New", "Courier"]
STATUS_COLOR = {"ok": "ok", "warn": "warn", "fail": "bad", "info": "text3"}
WIZARD_STEPS = ["歡迎", "環境檢測", "安裝選項", "安裝", "完成"]


class Theme:
    def __init__(self, root: tk.Misc, system: str):
        have = set(tkfont.families(root))
        self.family = next((f for f in FONTS.get(system, []) if f in have), "TkDefaultFont")
        self.mono = next((f for f in MONO if f in have), "TkFixedFont")

    def f(self, size: int = 10, bold: bool = False) -> Tuple:
        if self.family == "TkDefaultFont":
            return ("TkDefaultFont", size, "bold") if bold else ("TkDefaultFont", size)
        return (self.family, size, "bold") if bold else (self.family, size)

    def m(self, size: int = 9) -> Tuple:
        return (self.mono, size)


class Btn(tk.Label):
    """自己畫的按鈕（macOS 的原生按鈕不吃顏色）。invoke() 可以在測試裡呼叫。"""
    KINDS = {"primary": ("accent", "accent_hover", "#ffffff"), "secondary": ("surface2", "surface3", "text"),
             "danger": ("bad", "#9d2118", "#ffffff"), "ghost": ("surface", "surface2", "accent")}

    def __init__(self, master: tk.Misc, th: Theme, text: str, command: Callable[[], None], kind: str = "primary", big: bool = False, bg: Optional[str] = None):
        self.kind, self.command, self.enabled, self.th = kind, command, True, th
        bgk, hov, fgk = self.KINDS[kind]
        self.c_bg, self.c_hov, self.c_fg = PAL.get(bgk, bgk), PAL.get(hov, hov), PAL.get(fgk, fgk)
        ring = bg or str(master.cget("bg"))                      # 對焦的外框平常和背景同色
        super().__init__(master, text=text, bg=self.c_bg, fg=self.c_fg, font=th.f(13 if big else 10, True), padx=26 if big else 14, pady=11 if big else 6,
                         cursor="hand2", takefocus=1, highlightthickness=2, highlightbackground=ring, highlightcolor=PAL["accent"], bd=0)
        self.bind("<Enter>", lambda e: self.enabled and self.configure(bg=self.c_hov))
        self.bind("<Leave>", lambda e: self.enabled and self.configure(bg=self.c_bg))
        self.bind("<Button-1>", lambda e: self.focus_set())
        self.bind("<ButtonRelease-1>", self._click)
        self.bind("<Return>", lambda e: self.invoke())
        self.bind("<space>", lambda e: self.invoke())

    def _click(self, e: tk.Event) -> None:
        if 0 <= e.x < self.winfo_width() and 0 <= e.y < self.winfo_height():
            self.invoke()

    def invoke(self) -> None:
        if self.enabled:
            self.command()

    def set_enabled(self, on: bool) -> None:
        self.enabled = on
        self.configure(bg=self.c_bg if on else PAL["surface3"], fg=self.c_fg if on else PAL["text3"], cursor="hand2" if on else "arrow")

    def set_text(self, text: str) -> None:
        self.configure(text=text)


class Runner:
    """背景執行緒 → 佇列 → 主執行緒。工作函式收到一個 Reporter（進度與紀錄會被送回畫面）。

    背景執行緒只拿到純資料與一個佇列，不會握有任何畫面物件的參照：tkinter 物件如果在別的執行緒被回收，
    會出現 "main thread is not in main loop"，嚴重時整個程序會被 Tcl 中止。回呼函式都留在主執行緒的 handlers 裡，以編號對應。"""

    def __init__(self, root: tk.Misc, plat: Plat):
        self.root, self.plat = root, plat
        self.q: "queue.Queue[Tuple[int, str, tuple]]" = queue.Queue()
        self.handlers: Dict[int, Tuple[Callable[..., None], Optional[Callable[..., None]], Optional[Callable[..., None]]]] = {}
        self.next_id = 0
        self.alive = True
        self.ticks = 0
        self.after_id: Optional[str] = self.root.after(60, self._poll)

    def _poll(self) -> None:
        if not self.alive:
            return
        try:
            while True:
                token, kind, args = self.q.get_nowait()
                handlers = self.handlers.get(token)
                if handlers is None:
                    continue
                on_done, on_step, on_log = handlers
                if kind == "done":
                    del self.handlers[token]
                    on_done(*args)
                elif kind == "step" and on_step:
                    on_step(*args)
                elif kind == "log" and on_log:
                    on_log(*args)
        except queue.Empty:
            pass
        except tk.TclError:
            return
        self.ticks += 1
        if self.ticks % 200 == 0:
            gc.collect()                                                          # 在主執行緒收垃圾
        self.after_id = self.root.after(60, self._poll)

    def submit(self, work: Callable[[Reporter], Any], on_done: Callable[[Any, Optional[BaseException]], None],
               on_step: Optional[Callable[[int, int, str], None]] = None, on_log: Optional[Callable[[str], None]] = None,
               cancel: Optional[threading.Event] = None) -> None:
        self.next_id += 1
        token = self.next_id
        self.handlers[token] = (on_done, on_step, on_log)
        q = self.q
        rep = engine.make_reporter(self.plat, (lambda i, n, s: q.put((token, "step", (i, n, s)))) if on_step else None,
                                   (lambda line: q.put((token, "log", (line,)))) if on_log else None, cancel)

        def body() -> None:
            try:
                res, err = work(rep), None
            except BaseException as e:               # 任何錯誤都要交回畫面，不能讓執行緒默默結束
                res, err = None, e
            q.put((token, "done", (res, err)))
        threading.Thread(target=body, daemon=True).start()

    def stop(self) -> None:
        self.alive = False
        if self.after_id is not None:
            try:
                self.root.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None
        self.handlers.clear()


class ScrollFrame(tk.Frame):
    """內容比視窗高時可以捲動（滑鼠滾輪在框內任何位置都有用）。把東西放進 .inner。
    字體大、螢幕小的時候，頁面內容放不下也不會有按鈕被切掉而點不到。"""
    WHEEL = ("<MouseWheel>", "<Button-4>", "<Button-5>")

    def __init__(self, master: tk.Misc, bg: str):
        super().__init__(master, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0, width=1, height=1)
        self.bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner.bind("<Configure>", self._sync)
        self.canvas.bind("<Configure>", self._resize)
        for seq in self.WHEEL:
            self.bind_all(seq, self._wheel, add="+")

    def _resize(self, e: tk.Event) -> None:
        self.canvas.itemconfigure(self.win, width=e.width)
        self._sync()

    def _sync(self, _e: Optional[tk.Event] = None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        if self.canvas.winfo_height() <= 1:
            return                                                                 # 版面還沒算好：先不要讓捲軸閃一下
        need = self.inner.winfo_reqheight() > self.canvas.winfo_height()
        if need and not self.bar.winfo_ismapped():
            self.bar.pack(side="right", fill="y", before=self.canvas)
        elif not need and self.bar.winfo_ismapped():
            self.bar.pack_forget()

    def _wheel(self, e: tk.Event) -> None:
        if not self.winfo_exists() or not self.bar.winfo_ismapped():
            return
        under = self.winfo_containing(*self.winfo_pointerxy())
        if under is None or not str(under).startswith(str(self)):
            return                                                                 # 滑鼠不在這個框裡
        step = -1 if (getattr(e, "num", 0) == 4 or getattr(e, "delta", 0) > 0) else 1
        self.canvas.yview_scroll(step, "units")

    def destroy(self) -> None:
        for seq in self.WHEEL:
            try:
                self.unbind_all(seq)
            except tk.TclError:
                pass
        super().destroy()


def center(win: tk.Tk, w: int, h: int) -> None:
    win.update_idletasks()
    w, h = min(w, win.winfo_screenwidth() - 40), min(h, win.winfo_screenheight() - 90)        # 小螢幕（例如 1366×768 放大 125%）也放得下
    x, y = max(0, (win.winfo_screenwidth() - w) // 2), max(0, (win.winfo_screenheight() - h) // 3)
    win.geometry(f"{w}x{h}+{x}+{y}")


def short(s: str, n: int = 64) -> str:
    return s if len(s) <= n else s[:n // 2 - 1] + "…" + s[-(n // 2):]


class GuiApp:
    W, H = 820, 580

    def __init__(self, plat: Plat, ctx: Ctx, root: Optional[tk.Tk] = None):
        self.plat, self.ctx = plat, ctx
        self.gc_was_on = gc.isenabled()
        gc.disable()                      # 循環垃圾回收可能在背景執行緒觸發，那時回收 tkinter 物件會讓 Tcl 直接中止程序：改由主執行緒定期收
        self.root = root or tk.Tk()
        self.root.title(C.APP_NAME)
        self.th = Theme(self.root, plat.system)
        self.runner = Runner(self.root, plat)
        self.root.configure(bg=PAL["bg"])
        self.root.minsize(700, 460)
        center(self.root, self.W, self.H)
        self.icon_img: Optional[tk.PhotoImage] = None
        self._style()
        self._icon()
        self.view: Any = None
        self.exit_code = 0
        self.top_id: Optional[str] = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.raise_to_front()

    def raise_to_front(self) -> None:
        """從雙擊的黑色視窗啟動時，新視窗有時會開在別的視窗後面：先短暫設成最上層，確保使用者看得到。"""
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.top_id = self.root.after(500, self.drop_topmost)
        except tk.TclError:
            pass

    def drop_topmost(self) -> None:
        self.top_id = None
        try:
            self.root.attributes("-topmost", False)
        except tk.TclError:
            pass

    # ---------- 外觀 ----------
    def _style(self) -> None:
        st = ttk.Style(self.root)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        th = self.th
        st.configure("TCheckbutton", background=PAL["surface"], foreground=PAL["text"], font=th.f(10), focuscolor=PAL["surface"])
        st.map("TCheckbutton", background=[("active", PAL["surface"])])
        st.configure("Danger.TCheckbutton", background=PAL["bad_soft"], foreground=PAL["text"], font=th.f(10), focuscolor=PAL["bad_soft"])
        st.map("Danger.TCheckbutton", background=[("active", PAL["bad_soft"])])
        st.configure("TRadiobutton", background=PAL["surface"], foreground=PAL["text"], font=th.f(10), focuscolor=PAL["surface"])
        st.map("TRadiobutton", background=[("active", PAL["surface"])])
        st.configure("Accent.Horizontal.TProgressbar", background=PAL["accent"], troughcolor=PAL["surface3"], bordercolor=PAL["surface3"],
                     lightcolor=PAL["accent"], darkcolor=PAL["accent"], thickness=14)
        st.configure("TEntry", fieldbackground="#ffffff", bordercolor=PAL["border"], padding=6)
        st.configure("TCombobox", fieldbackground="#ffffff", padding=4)
        st.configure("TSpinbox", fieldbackground="#ffffff", padding=4)

    def _icon(self) -> None:
        png = shortcuts.assets_dir(self.plat) / "icon.png"
        if not png.exists():
            png = Path(__file__).parent / "assets" / "icon.png"
        try:
            self.icon_img = tk.PhotoImage(file=str(png))
            self.root.iconphoto(True, self.icon_img)
        except tk.TclError:
            self.icon_img = None
        if self.plat.is_windows:
            ico = Path(__file__).parent / "assets" / "icon.ico"
            try:
                self.root.iconbitmap(str(ico))
            except tk.TclError:
                pass

    def clear(self) -> None:
        if self.view is not None and hasattr(self.view, "dispose"):
            self.view.dispose()
        for w in self.root.winfo_children():
            w.destroy()
        self.view = None

    def sidebar(self, parent: tk.Misc, title: str, subtitle: str) -> tk.Frame:
        side = tk.Frame(parent, bg=PAL["side"], width=220)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        if self.icon_img is not None:
            small = self.icon_img.subsample(4, 4)                  # 256 → 64
            lab = tk.Label(side, image=small, bg=PAL["side"])
            lab.image = small                                      # type: ignore[attr-defined]
            lab.pack(pady=(28, 8))
        tk.Label(side, text=title, bg=PAL["side"], fg=PAL["side_text"], font=self.th.f(15, True)).pack()
        tk.Label(side, text=subtitle, bg=PAL["side"], fg=PAL["side_dim"], font=self.th.f(9)).pack(pady=(2, 18))
        return side

    # ---------- 進入點 ----------
    def start(self, install_only: bool = False, uninstall_only: bool = False) -> None:
        st = engine.installed_state(self.plat)
        if uninstall_only and st.cfg is not None:
            self.show_uninstall(st.cfg, standalone=True)
        elif st.installed and st.cfg is not None and not install_only:
            self.show_panel(st.cfg)
        else:
            self.show_wizard()

    def show_wizard(self) -> None:
        self.clear()
        self.root.title(f"{C.APP_NAME} 安裝精靈")
        self.view = Wizard(self)

    def show_panel(self, cfg: LauncherConfig) -> None:
        self.clear()
        self.root.title(f"{C.APP_NAME} 控制台")
        self.view = Panel(self, cfg)

    def show_uninstall(self, cfg: LauncherConfig, standalone: bool = False) -> None:
        self.clear()
        self.root.title(f"解除安裝 {C.APP_NAME}")
        self.view = UninstallView(self, cfg, standalone)

    def restart(self) -> None:
        """程式更新後換新的程序，讓新版的程式碼生效。"""
        from .__main__ import spawn_detached_gui
        spawn_detached_gui([])
        self.quit()

    def on_close(self) -> None:
        if self.view is not None and hasattr(self.view, "on_close"):
            if self.view.on_close() is False:
                return
        self.quit()

    def quit(self, code: int = 0) -> None:
        self.exit_code = code
        if self.view is not None and hasattr(self.view, "dispose"):
            self.view.dispose()
        self.runner.stop()
        if self.top_id is not None:
            try:
                self.root.after_cancel(self.top_id)
            except tk.TclError:
                pass
            self.top_id = None
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        self.view = None
        self.icon_img = None
        gc.collect()
        if self.gc_was_on:
            gc.enable()

    def pump(self, until: Callable[[], bool], timeout: float = 10.0) -> bool:
        """（測試用）一邊處理畫面事件一邊等條件成立。"""
        end = time.time() + timeout
        while time.time() < end:
            self.root.update()
            if until():
                return True
            time.sleep(0.02)
        return until()


# ====================== 安裝精靈 ======================
class Wizard:
    def __init__(self, app: GuiApp):
        self.app, self.th = app, app.th
        self.opts = engine.default_options(app.plat)
        self.state = engine.installed_state(app.plat)
        self.checks: List[envcheck.Check] = []
        self.fix_vars: Dict[str, tk.BooleanVar] = {}
        self.cancel = threading.Event()
        self.page = 0
        self.busy = False
        self.pulse_id: Optional[str] = None
        self.cfg: Optional[LauncherConfig] = None
        self.error = ""
        self.v_app = tk.StringVar(master=app.root, value=str(self.opts.app_dir))
        self.v_ws = tk.StringVar(master=app.root, value=str(self.opts.workspace))
        self.v_desktop = tk.BooleanVar(master=app.root, value=True)
        self.v_menu = tk.BooleanVar(master=app.root, value=True)
        self.v_path = tk.BooleanVar(master=app.root, value=True)
        self.v_open = tk.BooleanVar(master=app.root, value=True)
        self.v_source = tk.StringVar(master=app.root, value="auto")
        self.v_port = tk.StringVar(master=app.root, value=str(C.DEFAULT_PORT))
        self.v_restore = tk.StringVar(master=app.root, value="")
        self.step_labels: List[tk.Label] = []
        self.build_shell()
        self.goto(0)

    # ---- 外框：左邊步驟、右邊內容、底下按鈕 ----
    def build_shell(self) -> None:
        root, th = self.app.root, self.th
        side = self.app.sidebar(root, C.APP_NAME, "安裝精靈")
        self.step_labels = []
        for i, name in enumerate(WIZARD_STEPS):
            lab = tk.Label(side, text="", bg=PAL["side"], fg=PAL["side_dim"], font=th.f(11), anchor="w", padx=34)
            lab.pack(fill="x", pady=3)
            self.step_labels.append(lab)
        tk.Label(side, text=f"版本 {self.opts_version()}", bg=PAL["side"], fg=PAL["side_dim"], font=th.f(9)).pack(side="bottom", pady=14)
        right = tk.Frame(root, bg=PAL["bg"])
        right.pack(side="left", fill="both", expand=True)
        self.head = tk.Label(right, text="", bg=PAL["bg"], fg=PAL["text"], font=th.f(19, True), anchor="w")
        self.head.pack(fill="x", padx=32, pady=(26, 0))
        self.sub = tk.Label(right, text="", bg=PAL["bg"], fg=PAL["text2"], font=th.f(10), anchor="w", justify="left", wraplength=520)
        self.sub.pack(fill="x", padx=32, pady=(4, 12))
        bar = tk.Frame(right, bg=PAL["bg"])
        bar.pack(side="bottom", fill="x", padx=32, pady=18)
        self.btn_cancel = Btn(bar, th, "取消", self.on_cancel_click, "secondary", bg=PAL["bg"])
        self.btn_cancel.pack(side="left")
        self.btn_next = Btn(bar, th, "下一步 ›", self.next, "primary", bg=PAL["bg"])
        self.btn_next.pack(side="right")
        self.btn_back = Btn(bar, th, "‹ 上一步", self.back, "secondary", bg=PAL["bg"])
        self.btn_back.pack(side="right", padx=8)
        self.body = tk.Frame(right, bg=PAL["surface"], highlightthickness=1, highlightbackground=PAL["border"])
        self.body.pack(fill="both", expand=True, padx=32, pady=(0, 4))

    def opts_version(self) -> str:
        from .. import __version__
        return __version__

    def mark_steps(self) -> None:
        for i, lab in enumerate(self.step_labels):
            done, cur = i < self.page, i == self.page
            lab.configure(text=("✓  " if done else "●  " if cur else "○  ") + WIZARD_STEPS[i], fg=PAL["side_text"] if cur else PAL["side_dim"],
                          font=self.th.f(11, cur))

    def set_body(self) -> tk.Frame:
        for w in self.body.winfo_children():
            w.destroy()
        f = tk.Frame(self.body, bg=PAL["surface"])
        f.pack(fill="both", expand=True, padx=20, pady=16)
        return f

    def set_scroll_body(self) -> tk.Frame:
        """放得下就和 set_body 一樣；放不下（字體大、螢幕小）就出現捲軸。"""
        for w in self.body.winfo_children():
            w.destroy()
        sf = ScrollFrame(self.body, PAL["surface"])
        sf.pack(fill="both", expand=True, padx=8, pady=6)
        f = tk.Frame(sf.inner, bg=PAL["surface"])
        f.pack(fill="both", expand=True, padx=12, pady=10)
        return f

    def goto(self, n: int) -> None:
        self.page = n
        self.mark_steps()
        self.btn_back.set_enabled(n in (2,))
        self.btn_next.set_enabled(True)
        self.btn_cancel.set_text("取消")
        [self.page_welcome, self.page_checks, self.page_options, self.page_install, self.page_done][n]()

    def next(self) -> None:
        if self.busy:
            return
        if self.page == 0:
            self.goto(1)
        elif self.page == 1:
            self.goto(2)
        elif self.page == 2:
            if self.collect_options():
                self.goto(3)
        elif self.page == 4:
            self.goto(1) if self.error else self.finish()

    def back(self) -> None:
        if not self.busy and self.page == 2:
            self.goto(1)

    def on_cancel_click(self) -> None:
        if self.page == 3 and self.busy:
            if messagebox.askyesno(C.APP_NAME, "要取消安裝嗎？\n已經做的變更會復原。", parent=self.app.root):
                self.cancel.set()
                self.btn_cancel.set_enabled(False)
        elif self.page == 4:
            self.app.quit()
        elif not self.busy:
            self.app.quit()

    def on_close(self) -> Optional[bool]:
        if self.busy:
            self.on_cancel_click()
            return False
        return None

    # ---- 1 歡迎 ----
    def page_welcome(self) -> None:
        self.head.configure(text=f"歡迎使用 {C.APP_NAME}")
        self.sub.configure(text="這個精靈會檢測你的電腦、自動補齊需要的元件，然後把 CPE 教練安裝好。整個過程大約一到兩分鐘。")
        f = self.set_scroll_body()
        items = [("自動檢測環境", "Python、git、網路、磁碟空間、C++ 編譯器…缺什麼會告訴你，能自動安裝的幫你裝。"),
                 ("安裝後有控制台", "桌面與開始功能表的捷徑會開啟控制台：按「開啟」開始學習、按「關閉」結束，也能更新、備份、修復與解除安裝。"),
                 ("學習進度另外放", "你的解答與紀錄放在獨立的資料夾，更新或解除安裝都不會動到它（除非你自己選要刪除）。")]
        for t, d in items:
            r = tk.Frame(f, bg=PAL["surface"])
            r.pack(fill="x", pady=6)
            tk.Label(r, text="✓", bg=PAL["surface"], fg=PAL["accent"], font=self.th.f(14, True), width=2).pack(side="left", anchor="n")
            col = tk.Frame(r, bg=PAL["surface"])
            col.pack(side="left", fill="x", expand=True)
            tk.Label(col, text=t, bg=PAL["surface"], fg=PAL["text"], font=self.th.f(11, True), anchor="w").pack(fill="x")
            tk.Label(col, text=d, bg=PAL["surface"], fg=PAL["text2"], font=self.th.f(10), anchor="w", justify="left", wraplength=470).pack(fill="x")
        if self.state.installed and self.state.cfg is not None:
            c = self.state.cfg
            box = tk.Frame(f, bg=PAL["accent_soft"], highlightthickness=1, highlightbackground=PAL["border"])
            box.pack(fill="x", pady=(14, 0))
            tk.Label(box, text=f"偵測到已經安裝（版本 {c.version}）" + ("" if self.state.healthy else "，但有問題"), bg=PAL["accent_soft"], fg=PAL["accent"],
                     font=self.th.f(10, True), anchor="w").pack(fill="x", padx=12, pady=(8, 0))
            for p in self.state.problems:
                tk.Label(box, text="! " + p, bg=PAL["accent_soft"], fg=PAL["warn"], font=self.th.f(9), anchor="w", justify="left", wraplength=470).pack(fill="x", padx=12)
            row = tk.Frame(box, bg=PAL["accent_soft"])
            row.pack(fill="x", padx=10, pady=8)
            self.btn_open_panel = Btn(row, self.th, "開啟控制台", lambda: self.app.show_panel(c), "primary", bg=PAL["accent_soft"])
            self.btn_open_panel.pack(side="left", padx=2)
            self.btn_repair = Btn(row, self.th, "修復", self.do_repair, "secondary", bg=PAL["accent_soft"])
            self.btn_repair.pack(side="left", padx=2)
            self.btn_uninstall = Btn(row, self.th, "解除安裝", lambda: self.app.show_uninstall(c), "secondary", bg=PAL["accent_soft"])
            self.btn_uninstall.pack(side="left", padx=2)
            self.btn_next.set_text("重新安裝 ›")
        else:
            self.btn_next.set_text("開始 ›")

    def do_repair(self) -> None:
        c = self.state.cfg
        if c is None or self.busy:
            return
        self.busy = True
        self.sub.configure(text="修復中…")
        plat, ctx = self.app.plat, self.app.ctx
        self.app.runner.submit(lambda rep: engine.repair(c, plat, ctx, rep, engine.find_bundle()), self.repair_done)

    def repair_done(self, res: Any, err: Optional[BaseException]) -> None:
        self.busy = False
        if err is not None:
            messagebox.showerror(C.APP_NAME, f"修復失敗：{err}", parent=self.app.root)
            return
        messagebox.showinfo(C.APP_NAME, "修復完成。", parent=self.app.root)
        self.app.show_panel(res)

    # ---- 2 環境檢測 ----
    def page_checks(self) -> None:
        self.head.configure(text="檢測環境")
        self.sub.configure(text="正在檢查這台電腦…")
        self.btn_next.set_text("下一步 ›")
        self.btn_next.set_enabled(False)
        f = self.set_body()
        self.btn_recheck = Btn(f, self.th, "重新檢測", self.run_checks, "secondary", bg=PAL["surface"])
        self.btn_recheck.pack(anchor="e", side="bottom", pady=(6, 0))
        self.scroll = ScrollFrame(f, PAL["surface"])
        self.scroll.pack(fill="both", expand=True)
        self.check_box = self.scroll.inner
        tk.Label(self.check_box, text="檢測中…", bg=PAL["surface"], fg=PAL["text3"], font=self.th.f(10)).pack(anchor="w")
        self.run_checks()

    def run_checks(self) -> None:
        self.busy = True
        self.btn_next.set_enabled(False)
        ctx, opts = self.app.ctx, self.opts
        ctx.target, ctx.port, ctx.bundle = Path(self.v_app.get() or opts.app_dir), opts.port, opts.bundle
        v = self.state.cfg.version if self.state.cfg else None
        self.app.runner.submit(lambda rep: envcheck.run_checks(ctx, v), self.checks_done)

    def checks_done(self, res: Any, err: Optional[BaseException]) -> None:
        self.busy = False
        if self.page != 1:
            return
        if err is not None:
            self.sub.configure(text=f"檢測時發生錯誤：{err}")
            return
        self.checks = res
        for w in self.check_box.winfo_children():
            w.destroy()
        keep = {k: v.get() for k, v in self.fix_vars.items()}
        self.fix_vars = {}
        for c in self.checks:
            row = tk.Frame(self.check_box, bg=PAL["surface"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=engine.MARK[c.status], bg=PAL["surface"], fg=PAL[STATUS_COLOR[c.status]], font=self.th.f(12, True), width=2).grid(row=0, column=0, sticky="n")
            tk.Label(row, text=c.label, bg=PAL["surface"], fg=PAL["text"], font=self.th.f(10, True), anchor="w", justify="left", wraplength=200).grid(row=0, column=1, sticky="nw")
            tk.Label(row, text=short(c.detail, 80), bg=PAL["surface"], fg=PAL["text2"], font=self.th.f(9), anchor="w", justify="left", wraplength=215).grid(row=0, column=2, sticky="nw", padx=(8, 0))
            row.columnconfigure(1, minsize=205)
            col = tk.Frame(row, bg=PAL["surface"])
            col.grid(row=1, column=1, columnspan=2, sticky="w")
            if c.hint and c.status in ("fail", "warn"):
                tk.Label(col, text="→ " + c.hint, bg=PAL["surface"], fg=PAL["warn"], font=self.th.f(9), anchor="w", justify="left", wraplength=440).pack(fill="x")
            if c.fix and c.status in ("warn", "info") and envcheck.fix_plan(self.app.ctx, c.fix, gui=True) is not None:
                plan = envcheck.fix_plan(self.app.ctx, c.fix, gui=True)
                var = tk.BooleanVar(master=self.app.root, value=keep.get(c.fix, c.fix == "install_git"))
                self.fix_vars[c.fix] = var
                label = {"install_git": "自動安裝 git", "install_gpp": "自動安裝 C++ 編譯器（較大，之後要練 C++ 再裝也可以）", "install_tk": "自動安裝圖形介面套件"}[c.fix]
                ttk.Checkbutton(col, text=label + (f"（{plan.note}）" if plan and plan.note else ""), variable=var).pack(anchor="w", pady=(2, 0))
        s = envcheck.summarize(self.checks)
        if s["ok"]:
            self.sub.configure(text="環境沒有問題，可以繼續。標示「!」的是建議事項，不影響安裝。")
            self.btn_next.set_enabled(True)
        else:
            self.sub.configure(text="有必須先解決的問題（見紅色的 ✗ 與下面的說明）。解決之後按「重新檢測」。")

    # ---- 3 選項 ----
    def page_options(self) -> None:
        self.head.configure(text="安裝選項")
        self.sub.configure(text="預設值就可以直接按「安裝」。")
        self.btn_next.set_text("安裝")
        f = self.set_scroll_body()

        def path_row(label: str, var: tk.StringVar, hint: str, pick) -> None:
            tk.Label(f, text=label, bg=PAL["surface"], fg=PAL["text"], font=self.th.f(10, True), anchor="w").pack(fill="x", pady=(6, 0))
            r = tk.Frame(f, bg=PAL["surface"])
            r.pack(fill="x")
            e = ttk.Entry(r, textvariable=var)
            e.pack(side="left", fill="x", expand=True)
            Btn(r, self.th, "瀏覽…", pick, "secondary", bg=PAL["surface"]).pack(side="left", padx=(6, 0))
            tk.Label(f, text=hint, bg=PAL["surface"], fg=PAL["text3"], font=self.th.f(9), anchor="w").pack(fill="x")
            setattr(self, "entry_" + ("app" if var is self.v_app else "ws"), e)
        path_row("程式安裝位置", self.v_app, "程式本體放這裡（建議用預設）。", lambda: self.pick_dir(self.v_app))
        path_row("學習進度資料夾", self.v_ws, "你的解答、測資與紀錄放這裡；更新與解除安裝預設都不會動它。", lambda: self.pick_dir(self.v_ws))
        tk.Frame(f, bg=PAL["border"], height=1).pack(fill="x", pady=10)
        for var, text in ((self.v_desktop, "建立桌面捷徑"), (self.v_menu, "建立開始功能表／應用程式選單捷徑"), (self.v_path, "讓終端機可以直接輸入 cpe 指令"),
                          (self.v_open, "安裝完成後開啟控制台")):
            ttk.Checkbutton(f, text=text, variable=var).pack(anchor="w", pady=1)
        self.adv_open = False
        self.adv_btn = Btn(f, self.th, "進階選項 ▾", self.toggle_adv, "ghost", bg=PAL["surface"])
        self.adv_btn.pack(anchor="w", pady=(8, 0))
        self.adv = tk.Frame(f, bg=PAL["surface"])

    def toggle_adv(self) -> None:
        self.adv_open = not self.adv_open
        self.adv_btn.set_text("進階選項 ▴" if self.adv_open else "進階選項 ▾")
        if not self.adv_open:
            self.adv.pack_forget()
            return
        for w in self.adv.winfo_children():
            w.destroy()
        self.adv.pack(fill="x")
        r1 = tk.Frame(self.adv, bg=PAL["surface"])
        r1.pack(fill="x", pady=2)
        tk.Label(r1, text="程式來源", bg=PAL["surface"], fg=PAL["text"], font=self.th.f(10), width=10, anchor="w").pack(side="left")
        ttk.Combobox(r1, textvariable=self.v_source, values=["auto", "git", "zip", "bundle"], width=10, state="readonly").pack(side="left")
        tk.Label(r1, text="auto＝自動（git → zip → 本機資料夾）", bg=PAL["surface"], fg=PAL["text3"], font=self.th.f(9)).pack(side="left", padx=8)
        r2 = tk.Frame(self.adv, bg=PAL["surface"])
        r2.pack(fill="x", pady=2)
        tk.Label(r2, text="連接埠", bg=PAL["surface"], fg=PAL["text"], font=self.th.f(10), width=10, anchor="w").pack(side="left")
        ttk.Spinbox(r2, textvariable=self.v_port, from_=1024, to=65535, width=8).pack(side="left")
        r3 = tk.Frame(self.adv, bg=PAL["surface"])
        r3.pack(fill="x", pady=2)
        tk.Label(r3, text="還原備份", bg=PAL["surface"], fg=PAL["text"], font=self.th.f(10), width=10, anchor="w").pack(side="left")
        ttk.Entry(r3, textvariable=self.v_restore).pack(side="left", fill="x", expand=True)
        Btn(r3, self.th, "選擇…", lambda: self.pick_file(self.v_restore), "secondary", bg=PAL["surface"]).pack(side="left", padx=(6, 0))

    def pick_dir(self, var: tk.StringVar) -> None:
        d = filedialog.askdirectory(parent=self.app.root, initialdir=var.get() or str(self.app.plat.home))
        if d:
            var.set(str(Path(d)))

    def pick_file(self, var: tk.StringVar) -> None:
        d = filedialog.askopenfilename(parent=self.app.root, filetypes=[("CPE 備份", "*.zip"), ("全部", "*.*")])
        if d:
            var.set(d)

    def collect_options(self) -> bool:
        o = self.opts
        app_s, ws_s = self.v_app.get().strip(), self.v_ws.get().strip()
        if not app_s or not ws_s:
            messagebox.showwarning(C.APP_NAME, "請填入程式安裝位置與學習進度資料夾。", parent=self.app.root)
            return False
        app_p, ws_p = Path(app_s).expanduser(), Path(ws_s).expanduser()
        if not app_p.is_absolute() or not ws_p.is_absolute():
            messagebox.showwarning(C.APP_NAME, "請填完整的路徑（例如 C:\\Users\\你的名字\\… 或 /home/…）。", parent=self.app.root)
            return False
        if engine.inside(app_p, ws_p) or engine.inside(ws_p, app_p):
            messagebox.showwarning(C.APP_NAME, "程式資料夾與學習進度資料夾不能互相包含，請分開放。", parent=self.app.root)
            return False
        from . import source
        try:
            source.check_target(app_p)
        except source.SourceError as e:
            messagebox.showwarning(C.APP_NAME, str(e), parent=self.app.root)
            return False
        try:
            port = int(self.v_port.get())
            if not 1024 <= port <= 65535:
                raise ValueError
        except ValueError:
            messagebox.showwarning(C.APP_NAME, "連接埠要是 1024–65535 的數字。", parent=self.app.root)
            return False
        restore = self.v_restore.get().strip()
        if restore and not Path(restore).expanduser().is_file():
            messagebox.showwarning(C.APP_NAME, f"找不到備份檔：{restore}", parent=self.app.root)
            return False
        o.app_dir, o.workspace, o.port, o.source = app_p, ws_p, port, self.v_source.get()
        o.desktop, o.menu, o.add_path = self.v_desktop.get(), self.v_menu.get(), self.v_path.get()
        o.restore_from = Path(restore).expanduser() if restore else None
        o.fixes = [k for k, v in self.fix_vars.items() if v.get()]
        return True

    # ---- 4 安裝 ----
    def page_install(self) -> None:
        self.head.configure(text="安裝中")
        self.sub.configure(text="請稍候，不要關閉這個視窗。")
        self.btn_next.set_enabled(False)
        self.btn_back.set_enabled(False)
        f = self.set_body()
        self.cur_step = tk.Label(f, text="準備中…", bg=PAL["surface"], fg=PAL["text"], font=self.th.f(12, True), anchor="w")
        self.cur_step.pack(fill="x")
        self.bar = ttk.Progressbar(f, style="Accent.Horizontal.TProgressbar", mode="determinate", maximum=100)
        self.bar.pack(fill="x", pady=(8, 8))
        self.step_list = tk.Frame(f, bg=PAL["surface"])
        self.step_list.pack(fill="x")
        self.step_marks: List[tk.Label] = []
        for name in engine.STEPS_INSTALL:
            lab = tk.Label(self.step_list, text="○  " + name, bg=PAL["surface"], fg=PAL["text3"], font=self.th.f(10), anchor="w")
            lab.pack(fill="x")
            self.step_marks.append(lab)
        self.log = tk.Text(f, height=7, bg=PAL["surface2"], fg=PAL["text2"], font=self.th.m(9), relief="flat", wrap="word", state="disabled", padx=8, pady=6)
        self.log.pack(fill="both", expand=True, pady=(10, 0))
        self.cancel.clear()
        self.cfg, self.error, self.step_idx = None, "", -1
        self.busy = True
        self.btn_cancel.set_enabled(True)
        o, plat, ctx = self.opts, self.app.plat, self.app.ctx
        self.app.runner.submit(lambda rep: engine.install(o, plat, ctx, rep), self.install_done, self.on_step, self.on_log, self.cancel)
        self.pulse()

    def pulse(self) -> None:
        """步驟之間（例如 git clone 要等一陣子）讓進度條慢慢往前，表示沒有當掉。"""
        if not self.busy or self.page != 3:
            return
        try:
            cur = float(self.bar["value"])
            ceiling = max(4.0, (self.step_idx + 1) / len(engine.STEPS_INSTALL) * 100 - 2)
            if cur < ceiling:
                self.bar["value"] = cur + 0.4
            self.pulse_id = self.app.root.after(120, self.pulse)
        except tk.TclError:
            pass

    def dispose(self) -> None:
        if self.pulse_id is not None:
            try:
                self.app.root.after_cancel(self.pulse_id)
            except tk.TclError:
                pass
            self.pulse_id = None

    def on_step(self, i: int, n: int, name: str) -> None:
        self.step_idx = i
        self.cur_step.configure(text=name + "…")
        self.bar["value"] = max(float(self.bar["value"]), i / n * 100)
        for k, lab in enumerate(self.step_marks):
            lab.configure(text=("✓  " if k < i else "▶  " if k == i else "○  ") + engine.STEPS_INSTALL[k], fg=PAL["ok"] if k < i else PAL["accent"] if k == i else PAL["text3"])

    def on_log(self, line: str) -> None:
        if line.startswith("== "):
            return
        self.log.configure(state="normal")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def install_done(self, res: Any, err: Optional[BaseException]) -> None:
        self.busy = False
        self.cfg, self.error = res, str(err) if err else ""
        if err is None:
            self.bar["value"] = 100
            self.state = engine.installed_state(self.app.plat)
        self.page = 4
        self.mark_steps()
        self.page_done()

    # ---- 5 完成 ----
    def page_done(self) -> None:
        ok = self.cfg is not None and not self.error
        self.btn_cancel.set_text("結束")
        self.btn_cancel.set_enabled(True)
        self.btn_back.set_enabled(False)
        f = self.set_body()
        if ok and self.cfg is not None:
            c = self.cfg
            self.head.configure(text="安裝完成")
            self.sub.configure(text=f"{C.APP_NAME} {c.version} 已經安裝好了。")
            tk.Label(f, text="✓", bg=PAL["surface"], fg=PAL["ok"], font=self.th.f(40, True)).pack(pady=(4, 0))
            lines = [("控制台", "桌面與開始功能表的「" + C.APP_NAME + "」" if c.shortcuts else f"python {Path(c.app_dir) / 'cpe-panel.pyw'}"),
                     ("學習進度資料夾", c.workspace), ("程式位置", c.app_dir)]
            for k, v in lines:
                r = tk.Frame(f, bg=PAL["surface"])
                r.pack(fill="x", pady=2)
                tk.Label(r, text=k, bg=PAL["surface"], fg=PAL["text3"], font=self.th.f(10), width=14, anchor="w").pack(side="left")
                tk.Label(r, text=short(v, 70), bg=PAL["surface"], fg=PAL["text"], font=self.th.f(10), anchor="w").pack(side="left")
            self.btn_next.set_text("開啟控制台 ›" if self.v_open.get() else "完成")
            self.btn_next.set_enabled(True)
            row = tk.Frame(f, bg=PAL["surface"])
            row.pack(fill="x", pady=(14, 0))
            self.btn_play = Btn(row, self.th, "▶ 立即開始學習", self.play_now, "primary", big=True, bg=PAL["surface"])
            self.btn_play.pack(side="left")
        else:
            self.head.configure(text="安裝沒有完成")
            self.sub.configure(text="這一次做的變更都已經復原，你的電腦沒有被改動。")
            tk.Label(f, text="✗", bg=PAL["surface"], fg=PAL["bad"], font=self.th.f(40, True)).pack(pady=(4, 0))
            t = tk.Text(f, height=6, bg=PAL["bad_soft"], fg=PAL["text"], font=self.th.f(10), relief="flat", wrap="word", padx=8, pady=6)
            t.insert("1.0", self.error or "未知的錯誤")
            t.configure(state="disabled")
            t.pack(fill="x")
            row = tk.Frame(f, bg=PAL["surface"])
            row.pack(fill="x", pady=(12, 0))
            Btn(row, self.th, "複製診斷資訊", self.copy_diag, "secondary", bg=PAL["surface"]).pack(side="left")
            self.btn_next.set_text("重試")
            self.btn_next.set_enabled(True)

    def copy_diag(self) -> None:
        text = engine.report_text(self.app.plat, self.app.ctx) + "\n\n--- 安裝紀錄 ---\n" + engine.read_log(self.app.plat, "launcher", 3000) + "\n錯誤：" + self.error
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(text)
        messagebox.showinfo(C.APP_NAME, "已複製。貼給我就能診斷。", parent=self.app.root)

    def play_now(self) -> None:
        c = self.cfg
        if c is None:
            return
        self.btn_play.set_enabled(False)
        self.btn_play.set_text("啟動中…")

        plat = self.app.plat

        def work(rep: Reporter) -> Any:
            st = server.start(c, plat, log=rep.log)
            server.open_ui(st.url, c, plat, rep.log)
            return st
        self.app.runner.submit(work, lambda r, e: self.play_done(e))

    def play_done(self, err: Optional[BaseException]) -> None:
        if err is not None:
            messagebox.showerror(C.APP_NAME, f"無法開啟：{err}", parent=self.app.root)
            self.btn_play.set_enabled(True)
            self.btn_play.set_text("▶ 立即開始學習")
            return
        self.finish()

    def finish(self) -> None:
        if self.cfg is not None and self.v_open.get():
            self.app.show_panel(self.cfg)
        else:
            self.app.quit()


# ====================== 控制台 ======================
class Panel:
    TABS = [("home", "首頁"), ("settings", "設定"), ("tools", "維護")]
    TOOL_HINT = "把滑鼠移到按鈕上會顯示說明；執行的結果顯示在下面。"

    def __init__(self, app: GuiApp, cfg: LauncherConfig):
        self.app, self.th, self.cfg = app, app.th, cfg
        self.status = server.Status("stopped", cfg.port)
        self.busy = False
        self.refreshing = False
        self.alive = True
        self.after_id: Optional[str] = None
        self.check_id: Optional[str] = None
        self.today_id: Optional[str] = None
        self.today_info: Dict[str, Any] = {}
        self.tab = "home"
        self.nav: Dict[str, tk.Label] = {}
        self.update_info: Optional[Dict[str, Any]] = None
        self.build()
        self.show_tab("home")
        self.refresh()
        if cfg.opt("autostart_server"):
            self.app.root.after(300, self.start_server)
        if cfg.opt("check_update_on_open"):
            self.check_id = self.app.root.after(1200, self.auto_check)

    # ---- 版面 ----
    def build(self) -> None:
        root, th = self.app.root, self.th
        side = self.app.sidebar(root, C.APP_NAME, f"控制台　{self.cfg.version}")
        for key, name in self.TABS:
            lab = tk.Label(side, text=name, bg=PAL["side"], fg=PAL["side_dim"], font=th.f(11), anchor="w", padx=34, pady=7, cursor="hand2")
            lab.pack(fill="x")
            lab.bind("<Button-1>", lambda e, k=key: self.show_tab(k))
            self.nav[key] = lab
        self.led = tk.Label(side, text="●", bg=PAL["side"], fg=PAL["side_dim"], font=th.f(11))
        self.side_status = tk.Label(side, text="", bg=PAL["side"], fg=PAL["side_text"], font=th.f(10, True))
        self.side_status.pack(side="bottom", pady=(0, 20))
        self.led.pack(side="bottom")
        right = tk.Frame(root, bg=PAL["bg"])
        right.pack(side="left", fill="both", expand=True)
        self.bar = tk.Label(right, text="就緒", bg=PAL["surface2"], fg=PAL["text2"], font=th.f(9), anchor="w", padx=14, pady=5)
        self.bar.pack(side="bottom", fill="x")
        self.content = tk.Frame(right, bg=PAL["bg"])
        self.content.pack(fill="both", expand=True, padx=30, pady=24)

    def show_tab(self, key: str) -> None:
        self.tab = key
        for k, lab in self.nav.items():
            lab.configure(fg=PAL["side_text"] if k == key else PAL["side_dim"], font=self.th.f(11, k == key), bg="#2a2f55" if k == key else PAL["side"])
        for w in self.content.winfo_children():
            w.destroy()
        {"home": self.tab_home, "settings": self.tab_settings, "tools": self.tab_tools}[key]()
        self.paint_status()

    def card(self, parent: tk.Misc, pady: Tuple[int, int] = (0, 12)) -> tk.Frame:
        c = tk.Frame(parent, bg=PAL["surface"], highlightthickness=1, highlightbackground=PAL["border"])
        c.pack(fill="x", pady=pady)
        return c

    # ---- 首頁 ----
    def tab_home(self) -> None:
        th = self.th
        hero = self.card(self.content)
        inner = tk.Frame(hero, bg=PAL["surface"])
        inner.pack(fill="x", padx=22, pady=20)
        self.hero_title = tk.Label(inner, text="", bg=PAL["surface"], fg=PAL["text"], font=th.f(20, True), anchor="w")
        self.hero_title.pack(fill="x")
        self.hero_sub = tk.Label(inner, text="", bg=PAL["surface"], fg=PAL["text2"], font=th.f(10), anchor="w", justify="left", wraplength=480)
        self.hero_sub.pack(fill="x", pady=(2, 14))
        row = tk.Frame(inner, bg=PAL["surface"])
        row.pack(fill="x")
        self.btn_main = Btn(row, th, "▶  開啟", self.toggle_server, "primary", big=True, bg=PAL["surface"])
        self.btn_main.pack(side="left")
        self.btn_show = Btn(row, th, "開啟學習畫面", self.show_ui, "secondary", bg=PAL["surface"])
        self.btn_show.pack(side="left", padx=10)
        today = self.today_card = self.card(self.content)
        ti = tk.Frame(today, bg=PAL["surface"])
        ti.pack(fill="x", padx=22, pady=14)
        tk.Label(ti, text="今天", bg=PAL["surface"], fg=PAL["text3"], font=th.f(9, True), anchor="w").pack(fill="x")
        self.today_text = tk.Label(ti, text="讀取學習紀錄…", bg=PAL["surface"], fg=PAL["text"], font=th.f(10), anchor="w", justify="left", wraplength=500)
        self.today_text.pack(fill="x", pady=(2, 8))
        trow = tk.Frame(ti, bg=PAL["surface"])
        trow.pack(fill="x")
        self.btn_review = Btn(trow, th, "去複習／看學習洞察", lambda: self.open_page("study/insights"), "secondary", bg=PAL["surface"])
        self.btn_review.pack(side="left")
        self.btn_plan = Btn(trow, th, "今日計畫", lambda: self.open_page("home"), "ghost", bg=PAL["surface"])
        self.btn_plan.pack(side="left", padx=8)
        self.load_today()
        self.upd_card = tk.Frame(self.content, bg=PAL["accent_soft"], highlightthickness=1, highlightbackground=PAL["border"])
        self.upd_label = tk.Label(self.upd_card, text="", bg=PAL["accent_soft"], fg=PAL["accent"], font=th.f(10, True), anchor="w")
        self.upd_label.pack(side="left", padx=12, pady=8)
        self.btn_upd_now = Btn(self.upd_card, th, "立即更新", self.do_update, "primary", bg=PAL["accent_soft"])
        self.btn_upd_now.pack(side="right", padx=10, pady=6)
        info = self.info_card = self.card(self.content)
        for k, v, act in (("版本", f"{self.cfg.version}（{self.cfg.source.get('type', '')}）", None), ("學習進度", self.cfg.workspace, ("開啟資料夾", lambda: engine.open_folder(Path(self.cfg.workspace)))),
                          ("程式位置", self.cfg.app_dir, None), ("Python", self.cfg.python, None)):
            r = tk.Frame(info, bg=PAL["surface"], height=34)
            r.pack(fill="x", padx=18, pady=1)
            r.pack_propagate(False)
            tk.Label(r, text=k, bg=PAL["surface"], fg=PAL["text3"], font=th.f(10), width=9, anchor="w").pack(side="left")
            tk.Label(r, text=short(v, 56), bg=PAL["surface"], fg=PAL["text"], font=th.f(10), anchor="w").pack(side="left")
            if act:
                Btn(r, th, act[0], act[1], "ghost", bg=PAL["surface"]).pack(side="right")
        if self.update_info and self.update_info.get("status") == "available":
            self.show_update_banner()

    def load_today(self) -> None:
        """首頁「今天」卡片：在背景讀學習紀錄（到期複習、目標進度、距離上次練習）。讀不到只是卡片顯示說明，不影響控制台。"""
        if not self.alive or self.tab != "home":
            return
        cfg = self.cfg
        self.app.runner.submit(lambda rep: engine.learning_summary(cfg), self.today_loaded)

    def today_loaded(self, res: Any, err: Optional[BaseException]) -> None:
        if not self.alive or self.tab != "home" or not hasattr(self, "today_text") or not self.today_text.winfo_exists():
            return
        lines = engine.summary_lines(res) if isinstance(res, dict) else [f"（讀不到學習紀錄：{err}）"]
        self.today_text.configure(text="\n".join(lines))
        self.today_info = res if isinstance(res, dict) else {}
        try:
            self.today_id = self.app.root.after(60000, self.load_today)                # 練習完回到控制台時，一分鐘內會更新
        except tk.TclError:
            pass

    def open_page(self, path: str) -> None:
        """直接開啟學習畫面的某一頁（例如 study/insights）。服務還沒開就先啟動再開那一頁。"""
        if self.busy:
            return
        if self.status.running:
            server.open_ui(self.status.url.rstrip("/") + "/#/" + path, self.cfg, self.app.plat, self.say)
        else:
            self.start_server(path)

    def auto_check(self) -> None:
        """像遊戲的啟動器：開啟控制台時在背景悄悄檢查一次有沒有新版本（沒網路或查不到就什麼都不顯示）。"""
        self.check_id = None
        if not self.alive:
            return
        cfg = self.cfg
        self.app.runner.submit(lambda rep: engine.check_update(cfg), self.auto_checked)

    def auto_checked(self, res: Any, err: Optional[BaseException]) -> None:
        if not self.alive or err is not None or not isinstance(res, dict):
            return
        self.update_info = res
        if res.get("status") == "available":
            self.say("有新版本可以更新")
            self.show_update_banner()

    def show_update_banner(self) -> None:
        if self.tab != "home" or not hasattr(self, "upd_card"):
            return
        self.upd_label.configure(text="有新版本可以更新")
        self.upd_card.pack(fill="x", pady=(0, 12), before=self.today_card)

    # ---- 狀態 ----
    def refresh(self) -> None:
        if self.refreshing:
            return
        self.refreshing = True
        cfg, plat = self.cfg, self.app.plat
        self.app.runner.submit(lambda rep: server.status(cfg, plat), self.refresh_done)

    def dispose(self) -> None:
        self.alive = False
        for name in ("after_id", "check_id", "today_id"):
            token = getattr(self, name)
            if token is not None:
                try:
                    self.app.root.after_cancel(token)
                except tk.TclError:
                    pass
                setattr(self, name, None)

    def refresh_done(self, res: Any, err: Optional[BaseException]) -> None:
        self.refreshing = False
        if not self.alive:
            return
        if res is not None:
            self.status = res
            self.paint_status()
        try:
            self.after_id = self.app.root.after(2500, self.refresh)
        except tk.TclError:
            pass

    def paint_status(self) -> None:
        s = self.status
        label = {"running": "執行中", "stopped": "已關閉", "unresponsive": "沒有回應"}[s.state]
        color = {"running": PAL["ok"], "stopped": PAL["side_dim"], "unresponsive": PAL["warn"]}[s.state]
        self.led.configure(fg=color if s.state != "stopped" else PAL["side_dim"])
        self.side_status.configure(text=label)
        if self.tab != "home" or not hasattr(self, "btn_main") or not self.btn_main.winfo_exists():
            return
        if s.state == "running":
            self.hero_title.configure(text="執行中", fg=PAL["ok"])
            self.hero_sub.configure(text=f"{s.url}" + ("　（在控制台以外的地方開啟的）" if s.external else "") + "\n學習畫面開著就可以練習；今天練完按「關閉」。")
            self.btn_main.set_text("■  關閉")
            self.btn_main.c_bg, self.btn_main.c_hov = PAL["bad"], "#9d2118"
            self.btn_show.pack(side="left", padx=10)
        elif s.state == "unresponsive":
            self.hero_title.configure(text="沒有回應", fg=PAL["warn"])
            self.hero_sub.configure(text=f"程序 {s.pid} 還在，但連不上。按「關閉」把它結束，再重新開啟。")
            self.btn_main.set_text("■  關閉")
            self.btn_main.c_bg, self.btn_main.c_hov = PAL["bad"], "#9d2118"
            self.btn_show.pack_forget()
        else:
            self.hero_title.configure(text="已關閉", fg=PAL["text"])
            self.hero_sub.configure(text="按「開啟」會啟動學習服務並開啟畫面。")
            self.btn_main.set_text("▶  開啟")
            self.btn_main.c_bg, self.btn_main.c_hov = PAL["accent"], PAL["accent_hover"]
            self.btn_show.pack_forget()
        self.btn_main.configure(bg=self.btn_main.c_bg if self.btn_main.enabled else PAL["surface3"])

    def say(self, text: str) -> None:
        self.bar.configure(text=text)

    def set_busy(self, on: bool, text: str = "") -> None:
        self.busy = on
        if text:
            self.say(text)
        if hasattr(self, "btn_main") and self.btn_main.winfo_exists():
            self.btn_main.set_enabled(not on)

    # ---- 開啟／關閉 ----
    def toggle_server(self) -> None:
        if self.busy:
            return
        if self.status.state == "stopped":
            self.start_server()
        else:
            self.stop_server()

    def start_server(self, page: str = "") -> None:
        if self.busy:
            return
        self.set_busy(True, "啟動中…")
        open_ui, cfg, plat = bool(self.cfg.opt("open_browser")) or bool(page), self.cfg, self.app.plat

        def work(rep: Reporter) -> Any:
            st = server.start(cfg, plat, log=rep.log)
            if open_ui:
                server.open_ui(st.url.rstrip("/") + "/#/" + page if page else st.url, cfg, plat, rep.log)
            return st
        self.app.runner.submit(work, self.started, on_log=self.say)

    def started(self, res: Any, err: Optional[BaseException]) -> None:
        self.set_busy(False)
        if err is not None:
            self.say("啟動失敗")
            messagebox.showerror(C.APP_NAME, f"無法開啟：\n{err}", parent=self.app.root)
            return
        self.status = res
        self.say(f"已啟動：{res.url}")
        self.paint_status()

    def stop_server(self) -> None:
        self.set_busy(True, "關閉中…")
        cfg, plat = self.cfg, self.app.plat
        self.app.runner.submit(lambda rep: server.stop(cfg, plat, rep.log), self.stopped, on_log=self.say)

    def stopped(self, res: Any, err: Optional[BaseException]) -> None:
        self.set_busy(False)
        if err is not None:
            self.say("關閉失敗")
            messagebox.showerror(C.APP_NAME, f"無法關閉：\n{err}", parent=self.app.root)
            return
        self.status = server.Status("stopped", self.cfg.port)
        self.say("已關閉")
        self.paint_status()

    def show_ui(self) -> None:
        if self.status.running:
            server.open_ui(self.status.url, self.cfg, self.app.plat, self.say)

    # ---- 設定 ----
    def tab_settings(self) -> None:
        th = self.th
        tk.Label(self.content, text="設定", bg=PAL["bg"], fg=PAL["text"], font=th.f(18, True), anchor="w").pack(fill="x", pady=(0, 10))
        c = self.card(self.content)
        inner = tk.Frame(c, bg=PAL["surface"])
        inner.pack(fill="x", padx=20, pady=14)
        self.vars: Dict[str, tk.Variable] = {}

        def check(key: str, text: str) -> None:
            v = tk.BooleanVar(master=self.app.root, value=bool(self.cfg.opt(key)))
            v.trace_add("write", lambda *a, k=key, var=v: self.save_option(k, var.get()))
            self.vars[key] = v
            ttk.Checkbutton(inner, text=text, variable=v).pack(anchor="w", pady=3)
        check("open_browser", "按「開啟」後自動開啟學習畫面")
        check("app_window", "用獨立的應用程式視窗開啟（需要 Edge 或 Chrome）")
        check("autostart_server", "開啟控制台時自動啟動服務")
        check("check_update_on_open", "開啟控制台時自動檢查有沒有新版本（需要網路；沒有就不顯示）")
        r = tk.Frame(inner, bg=PAL["surface"])
        r.pack(fill="x", pady=(8, 0))
        tk.Label(r, text="關閉控制台時：", bg=PAL["surface"], fg=PAL["text"], font=th.f(10)).pack(side="left")
        v = tk.StringVar(master=self.app.root, value=str(self.cfg.opt("stop_on_exit")))
        v.trace_add("write", lambda *a: self.save_option("stop_on_exit", v.get()))
        self.vars["stop_on_exit"] = v
        for val, text in (("ask", "詢問我"), ("stop", "一併關閉服務"), ("keep", "讓服務繼續執行")):
            ttk.Radiobutton(r, text=text, value=val, variable=v).pack(side="left", padx=8)
        r2 = tk.Frame(inner, bg=PAL["surface"])
        r2.pack(fill="x", pady=(10, 0))
        tk.Label(r2, text="服務的連接埠：", bg=PAL["surface"], fg=PAL["text"], font=th.f(10)).pack(side="left")
        pv = tk.StringVar(master=self.app.root, value=str(self.cfg.port))
        ttk.Spinbox(r2, textvariable=pv, from_=1024, to=65535, width=8, command=lambda: self.save_port(pv.get())).pack(side="left", padx=6)
        pv.trace_add("write", lambda *a: self.save_port(pv.get()))
        self.vars["port"] = pv
        tk.Label(r2, text="（下次開啟時生效；被占用會自動改用別的）", bg=PAL["surface"], fg=PAL["text3"], font=th.f(9)).pack(side="left")

    def save_option(self, key: str, value: Any) -> None:
        self.cfg.options[key] = value
        cfgmod.save(self.app.plat.launcher_home, self.cfg)
        self.say("設定已儲存")

    def save_port(self, text: str) -> None:
        if text.isdigit() and 1024 <= int(text) <= 65535 and int(text) != self.cfg.port:
            self.cfg.port = int(text)
            cfgmod.save(self.app.plat.launcher_home, self.cfg)
            self.say("設定已儲存")

    # ---- 維護 ----
    def tab_tools(self) -> None:
        th = self.th
        tk.Label(self.content, text="維護", bg=PAL["bg"], fg=PAL["text"], font=th.f(18, True), anchor="w").pack(fill="x", pady=(0, 10))
        c = self.card(self.content)
        grid = tk.Frame(c, bg=PAL["surface"])
        grid.pack(fill="x", padx=16, pady=(8, 6))
        self.tool_btns: Dict[str, Btn] = {}
        tools = [("update", "檢查更新", "看看有沒有新版本；有的話可以直接更新", self.check_update),
                 ("backup", "備份學習進度", "把解答與紀錄打包成 zip，放到桌面", self.do_backup),
                 ("backup_enc", "加密備份…", "用密碼加密（AES-256，需要系統有 openssl）；忘了密碼就救不回來", self.do_backup_encrypted),
                 ("sync", "同步到共用資料夾…", "兩台電腦用同一個資料夾（Dropbox、隨身碟）合併進度", self.do_sync),
                 ("remind", "每日複習提醒…", "每天固定時間檢查，有到期的複習才跳出通知", self.do_reminder),
                 ("privacy", "資料與隱私", "列出存了哪些資料、哪些會連網", self.do_privacy),
                 ("doctor", "環境檢測", "檢查 Python、git、網路、編譯器…", self.do_doctor),
                 ("repair", "修復安裝", "程式壞了、捷徑不見、Python 換位置時用", self.do_repair),
                 ("log", "查看紀錄", "安裝與服務的紀錄，出問題時貼給我看", self.do_log),
                 ("uninstall", "解除安裝…", "移除程式、捷徑與指令；學習進度預設保留", self.do_uninstall)]
        for col in range(3):
            grid.columnconfigure(col, weight=1, uniform="tools")
        self.tool_hint = tk.Label(c, text=self.TOOL_HINT, bg=PAL["surface"], fg=PAL["text3"], font=th.f(9), anchor="w", justify="left", wraplength=480)
        for i, (key, text, desc, fn) in enumerate(tools):
            b = Btn(grid, th, text, fn, "danger" if key == "uninstall" else "secondary", bg=PAL["surface"])
            b.grid(row=i // 3, column=i % 3, sticky="w", padx=6, pady=3)
            b.bind("<Enter>", lambda e, d=desc: self.tool_hint.configure(text=d), add="+")             # 說明放在按鈕下面一行：10 個按鈕＋說明塞不進視窗，輸出框會被擠掉
            b.bind("<Leave>", lambda e: self.tool_hint.configure(text=self.TOOL_HINT), add="+")
            self.tool_btns[key] = b
        self.tool_hint.pack(fill="x", padx=18, pady=(0, 8))
        self.out = tk.Text(self.content, height=6, bg=PAL["surface"], fg=PAL["text2"], font=th.m(9), relief="flat", wrap="word", state="disabled", padx=10, pady=8,
                           highlightthickness=1, highlightbackground=PAL["border"])
        self.out.pack(fill="both", expand=True)

    def write_out(self, text: str, clear: bool = False) -> None:
        if not hasattr(self, "out") or not self.out.winfo_exists():
            return
        self.out.configure(state="normal")
        if clear:
            self.out.delete("1.0", "end")
        self.out.insert("end", text + "\n")
        self.out.see("end")
        self.out.configure(state="disabled")

    def check_update(self) -> None:
        if self.busy:
            return
        self.set_busy(True, "檢查更新中…")
        self.write_out("檢查更新中…", clear=True)
        cfg = self.cfg
        self.app.runner.submit(lambda rep: engine.check_update(cfg), self.update_checked)

    def update_checked(self, res: Any, err: Optional[BaseException]) -> None:
        self.set_busy(False)
        if err is not None:
            self.write_out(f"檢查失敗：{err}")
            return
        self.update_info = res
        st = res["status"]
        if st == "up_to_date":
            self.write_out("✓ 已經是最新版。")
            self.say("已經是最新版")
        elif st == "unavailable":
            self.write_out("✗ " + str(res.get("reason", "")))
        else:
            n = res.get("behind")
            self.write_out(f"有新版本可以更新{'（新增 %s 個變更）' % n if n else ''}。")
            for sha, subject in (res.get("commits") or [])[:8]:
                self.write_out(f"  {sha}  {subject}")
            if self.app.root.winfo_exists() and messagebox.askyesno(C.APP_NAME, "有新版本，要現在更新嗎？\n（學習進度不會被動到；更新完控制台會重新開啟。）", parent=self.app.root):
                self.do_update()

    def do_update(self) -> None:
        if self.busy:
            return
        self.set_busy(True, "更新中…")
        self.show_tab("tools")
        self.write_out("更新中…", clear=True)
        cfg, plat, ctx = self.cfg, self.app.plat, self.app.ctx
        self.app.runner.submit(lambda rep: engine.update(cfg, plat, ctx, rep), self.update_done, on_log=self.log_line)

    def log_line(self, line: str) -> None:
        if not line.startswith("== "):
            self.write_out(line)

    def update_done(self, res: Any, err: Optional[BaseException]) -> None:
        self.set_busy(False)
        if err is not None:
            self.write_out(f"✗ 更新失敗：{err}")
            return
        st = res["status"]
        if st == "updated":
            self.write_out(f"✓ 已更新：{res['old_version']} → {res['new_version']}")
            if res.get("notes"):
                self.write_out("\n這次更新的內容：\n" + res["notes"])
            messagebox.showinfo(C.APP_NAME, "更新完成，控制台會重新開啟。", parent=self.app.root)
            self.app.restart()
        elif st == "up_to_date":
            self.write_out("✓ 已經是最新版。")
        else:
            self.write_out("✗ " + str(res.get("reason", st)))

    def do_backup(self) -> None:
        if self.busy:
            return
        dest = self.app.plat.desktop_dir if self.app.plat.desktop_dir.is_dir() else self.app.plat.home
        self.set_busy(True, "備份中…")
        cfg = self.cfg
        self.app.runner.submit(lambda rep: engine.backup_now(cfg, dest), self.backup_done)

    def backup_done(self, res: Any, err: Optional[BaseException]) -> None:
        self.set_busy(False)
        self.write_out(f"✗ 備份失敗：{err}" if err else f"✓ 已備份：{res}", clear=True)

    # ---- 2.7 的維護工具 ----
    def ask_password(self) -> Optional[str]:
        """問備份密碼（輸入時不顯示、要輸入兩次）。回傳 None 代表取消。測試時可以替換。"""
        win = tk.Toplevel(self.app.root)
        win.title("備份密碼")
        win.transient(self.app.root)
        win.configure(bg=PAL["bg"], padx=20, pady=16)
        result: Dict[str, Optional[str]] = {"v": None}
        tk.Label(win, text="設定備份密碼（至少 8 個字元）\n忘了密碼，這份備份就打不開。", bg=PAL["bg"], fg=PAL["text"], font=self.th.f(10), justify="left").pack(anchor="w")
        e1, e2 = tk.Entry(win, show="•", width=32), tk.Entry(win, show="•", width=32)
        for lab, e in (("密碼", e1), ("再輸入一次", e2)):
            tk.Label(win, text=lab, bg=PAL["bg"], fg=PAL["text2"], font=self.th.f(9)).pack(anchor="w", pady=(8, 0))
            e.pack(anchor="w")
        msg = tk.Label(win, text="", bg=PAL["bg"], fg=PAL["bad"], font=self.th.f(9))
        msg.pack(anchor="w", pady=(6, 0))

        def ok() -> None:
            if len(e1.get()) < 8:
                msg.configure(text="密碼至少 8 個字元")
            elif e1.get() != e2.get():
                msg.configure(text="兩次輸入的不一樣")
            else:
                result["v"] = e1.get()
                win.destroy()
        row = tk.Frame(win, bg=PAL["bg"])
        row.pack(anchor="e", pady=(10, 0))
        Btn(row, self.th, "取消", win.destroy, "ghost", bg=PAL["bg"]).pack(side="left")
        Btn(row, self.th, "備份", ok, "primary", bg=PAL["bg"]).pack(side="left", padx=(8, 0))
        e1.focus_set()
        win.grab_set()
        self.app.root.wait_window(win)
        return result["v"]

    def do_backup_encrypted(self) -> None:
        if self.busy:
            return
        pw = self.ask_password()
        if not pw:
            return
        dest = self.app.plat.desktop_dir if self.app.plat.desktop_dir.is_dir() else self.app.plat.home
        self.set_busy(True, "加密備份中…")
        cfg = self.cfg
        self.app.runner.submit(lambda rep: engine.encrypted_backup_now(cfg, dest, pw), self.backup_done)

    def do_sync(self) -> None:
        if self.busy:
            return
        folder = filedialog.askdirectory(parent=self.app.root, title="選一個共用資料夾（Dropbox、OneDrive 或隨身碟）")
        if not folder:
            return
        if self.status.running and not messagebox.askyesno(C.APP_NAME, "學習服務還開著。同步前建議先按「關閉」，以免它同時寫入。\n\n還是要現在同步嗎？", parent=self.app.root):
            return
        self.set_busy(True, "同步中…")
        cfg = self.cfg
        self.app.runner.submit(lambda rep: engine.sync_now(cfg, Path(folder)), self.tool_text_done)

    def do_reminder(self) -> None:
        if self.busy:
            return
        try:
            plan = engine.reminder_plan(self.cfg)
        except Exception as e:
            self.write_out(f"✗ 無法產生排程：{e}", clear=True)
            return
        self.write_out(plan["text"], clear=True)
        if not messagebox.askyesno(C.APP_NAME, "要現在安裝每天 19:30 的複習提醒嗎？\n（只有有到期的複習才會通知；之後可以在系統的排程裡移除）", parent=self.app.root):
            return
        self.set_busy(True, "安裝提醒中…")
        cfg = self.cfg
        self.app.runner.submit(lambda rep: engine.install_reminder(cfg), self.tool_text_done)

    def do_privacy(self) -> None:
        if self.busy:
            return
        self.set_busy(True, "讀取中…")
        cfg = self.cfg
        self.app.runner.submit(lambda rep: engine.privacy_text(cfg), self.tool_text_done)

    def tool_text_done(self, res: Any, err: Optional[BaseException]) -> None:
        self.set_busy(False)
        self.write_out(f"✗ {err}" if err else str(res), clear=True)

    def do_doctor(self) -> None:
        if self.busy:
            return
        self.set_busy(True, "檢測中…")
        plat, ctx = self.app.plat, self.app.ctx
        self.app.runner.submit(lambda rep: engine.report_text(plat, ctx), self.doctor_done)

    def doctor_done(self, res: Any, err: Optional[BaseException]) -> None:
        self.set_busy(False)
        self.write_out(str(err) if err else res, clear=True)

    def do_repair(self) -> None:
        if self.busy:
            return
        self.set_busy(True, "修復中…")
        self.write_out("修復中…", clear=True)
        cfg, plat, ctx = self.cfg, self.app.plat, self.app.ctx
        self.app.runner.submit(lambda rep: engine.repair(cfg, plat, ctx, rep, engine.find_bundle()), self.repair_done, on_log=self.log_line)

    def repair_done(self, res: Any, err: Optional[BaseException]) -> None:
        self.set_busy(False)
        if err is not None:
            self.write_out(f"✗ 修復失敗：{err}")
        else:
            self.cfg = res
            self.write_out("✓ 修復完成。")

    def do_log(self) -> None:
        self.write_out("--- 服務紀錄 ---\n" + (engine.read_log(self.app.plat, "server", 2500) or "（沒有）") + "\n--- 安裝紀錄 ---\n" + (engine.read_log(self.app.plat, "launcher", 2500) or "（沒有）"), clear=True)

    def do_uninstall(self) -> None:
        if self.busy:
            return
        self.app.show_uninstall(self.cfg)

    # ---- 離開 ----
    def on_close(self) -> Optional[bool]:
        mode = str(self.cfg.opt("stop_on_exit"))
        if self.busy:
            if not messagebox.askyesno(C.APP_NAME, "還有動作進行中，確定要離開嗎？", parent=self.app.root):
                return False
        if self.status.running and not self.status.external:
            if mode == "ask":
                ans = messagebox.askyesnocancel(C.APP_NAME, "要順便關閉學習服務嗎？\n\n是：關閉服務並離開\n否：讓服務繼續執行（學習畫面可以繼續用）\n取消：留在控制台", parent=self.app.root)
                if ans is None:
                    return False
                mode = "stop" if ans else "keep"
            if mode == "stop":
                try:
                    server.stop(self.cfg, self.app.plat)
                except server.ServerError as e:
                    messagebox.showerror(C.APP_NAME, str(e), parent=self.app.root)
        return None


# ====================== 解除安裝 ======================
class UninstallView:
    def __init__(self, app: GuiApp, cfg: LauncherConfig, standalone: bool):
        self.app, self.th, self.cfg, self.standalone = app, app.th, cfg, standalone
        self.busy = False
        self.done = False
        self.v_delete = tk.BooleanVar(master=app.root, value=False)
        self.v_backup = tk.BooleanVar(master=app.root, value=True)
        self.v_confirm = tk.BooleanVar(master=app.root, value=False)
        self.build()

    def build(self) -> None:
        root, th = self.app.root, self.th
        side = self.app.sidebar(root, C.APP_NAME, "解除安裝")
        tk.Label(side, text="你的學習進度預設會保留", bg=PAL["side"], fg=PAL["side_dim"], font=th.f(9), wraplength=170).pack(side="bottom", pady=18)
        right = tk.Frame(root, bg=PAL["bg"])
        right.pack(side="left", fill="both", expand=True)
        self.head = tk.Label(right, text=f"解除安裝 {C.APP_NAME}", bg=PAL["bg"], fg=PAL["text"], font=th.f(19, True), anchor="w")
        self.head.pack(fill="x", padx=32, pady=(26, 0))
        self.sub = tk.Label(right, text="以下項目會被移除：", bg=PAL["bg"], fg=PAL["text2"], font=th.f(10), anchor="w")
        self.sub.pack(fill="x", padx=32, pady=(4, 12))
        bar = tk.Frame(right, bg=PAL["bg"])
        bar.pack(side="bottom", fill="x", padx=32, pady=18)
        self.btn_cancel = Btn(bar, th, "取消", self.cancel, "secondary", bg=PAL["bg"])
        self.btn_cancel.pack(side="left")
        self.btn_go = Btn(bar, th, "解除安裝", self.go, "danger", bg=PAL["bg"])
        self.btn_go.pack(side="right")
        self.body = tk.Frame(right, bg=PAL["surface"], highlightthickness=1, highlightbackground=PAL["border"])
        self.body.pack(fill="both", expand=True, padx=32, pady=(0, 4))
        sf = ScrollFrame(self.body, PAL["surface"])
        sf.pack(fill="both", expand=True, padx=8, pady=6)
        f = tk.Frame(sf.inner, bg=PAL["surface"])
        f.pack(fill="both", expand=True, padx=12, pady=8)
        self.inner = f
        c = self.cfg
        rows = [("程式", c.app_dir), ("捷徑", f"{len(c.shortcuts)} 個（桌面、開始功能表）"), ("終端機指令 cpe", "移除")]
        if self.app.plat.is_windows:
            rows.append(("「應用程式與功能」裡的項目", "移除"))
        for k, v in rows:
            r = tk.Frame(f, bg=PAL["surface"])
            r.pack(fill="x", pady=2)
            tk.Label(r, text="✓", bg=PAL["surface"], fg=PAL["accent"], font=th.f(10, True), width=2).pack(side="left")
            tk.Label(r, text=f"{k}：", bg=PAL["surface"], fg=PAL["text"], font=th.f(10, True)).pack(side="left")
            tk.Label(r, text=short(v, 52), bg=PAL["surface"], fg=PAL["text2"], font=th.f(10)).pack(side="left")
        tk.Frame(f, bg=PAL["border"], height=1).pack(fill="x", pady=10)
        tk.Label(f, text="你的學習進度", bg=PAL["surface"], fg=PAL["text"], font=th.f(11, True), anchor="w").pack(fill="x")
        tk.Label(f, text=c.workspace, bg=PAL["surface"], fg=PAL["text3"], font=th.f(9), anchor="w").pack(fill="x")
        ttk.Radiobutton(f, text="保留我的學習進度（建議）", value=False, variable=self.v_delete, command=self.toggle).pack(anchor="w", pady=(6, 0))
        ttk.Radiobutton(f, text="同時刪除學習進度（解答與紀錄都會消失，無法復原）", value=True, variable=self.v_delete, command=self.toggle).pack(anchor="w")
        self.danger = tk.Frame(f, bg=PAL["bad_soft"])
        ttk.Checkbutton(self.danger, text="刪除之前，先備份一份到桌面", variable=self.v_backup, style="Danger.TCheckbutton").pack(anchor="w", padx=12, pady=(8, 0))
        ttk.Checkbutton(self.danger, text="我了解刪除後無法復原", variable=self.v_confirm, style="Danger.TCheckbutton").pack(anchor="w", padx=12, pady=(2, 8))
        self.log = tk.Text(f, height=5, bg=PAL["surface2"], fg=PAL["text2"], font=th.m(9), relief="flat", wrap="word", state="disabled", padx=8, pady=6)

    def toggle(self) -> None:
        if self.v_delete.get():
            self.danger.pack(fill="x", pady=(8, 0))
        else:
            self.danger.pack_forget()
            self.v_confirm.set(False)

    def cancel(self) -> None:
        if self.busy:
            return
        if self.done or self.standalone:
            self.app.quit()
        else:
            self.app.show_panel(self.cfg)

    def on_close(self) -> Optional[bool]:
        return False if self.busy else None

    def go(self) -> None:
        if self.busy or self.done:
            if self.done:
                self.app.quit()
            return
        delete = self.v_delete.get()
        if delete and not self.v_confirm.get():
            messagebox.showwarning(C.APP_NAME, "要刪除學習進度，請先勾選「我了解刪除後無法復原」。", parent=self.app.root)
            return
        if not messagebox.askyesno(C.APP_NAME, "確定要解除安裝嗎？" + ("\n學習進度也會被刪除。" if delete else ""), parent=self.app.root, icon="warning"):
            return
        self.busy = True
        self.btn_go.set_enabled(False)
        self.btn_cancel.set_enabled(False)
        self.danger.pack_forget()
        self.log.pack(fill="both", expand=True, pady=(10, 0))
        backup_dir = (self.app.plat.desktop_dir if self.app.plat.desktop_dir.is_dir() else self.app.plat.home) if delete and self.v_backup.get() else None
        opts, cfg, plat = UninstallOptions(delete, backup_dir), self.cfg, self.app.plat
        self.app.runner.submit(lambda rep: engine.uninstall(cfg, plat, opts, rep), self.finished, on_log=self.on_log)

    def on_log(self, line: str) -> None:
        if line.startswith("== "):
            line = line[3:]
        self.log.configure(state="normal")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def finished(self, res: Any, err: Optional[BaseException]) -> None:
        self.busy = False
        self.btn_cancel.set_enabled(True)
        if err is not None:
            self.head.configure(text="解除安裝沒有完成")
            self.sub.configure(text=str(err))
            self.btn_go.set_enabled(True)
            return
        self.done = True
        self.head.configure(text="已解除安裝")
        keep = f"學習進度還在：{res['workspace']}" if not res["workspace_removed"] else "學習進度已刪除。"
        if res.get("backup"):
            keep += f"\n備份：{res['backup']}"
        self.sub.configure(text=keep + ("\n" + "；".join(res["problems"]) if res["problems"] else ""))
        self.btn_go.set_text("結束")
        self.btn_go.c_bg, self.btn_go.c_hov = PAL["accent"], PAL["accent_hover"]
        self.btn_go.set_enabled(True)
        self.btn_go.configure(bg=PAL["accent"])
        self.btn_cancel.pack_forget()


def run(plat: Plat, ctx: Ctx, install_only: bool = False, uninstall_only: bool = False) -> int:
    app = GuiApp(plat, ctx)
    app.start(install_only, uninstall_only)
    app.root.mainloop()
    return app.exit_code
