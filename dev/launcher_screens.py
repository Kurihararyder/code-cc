"""把安裝精靈與控制台的每一個畫面都開出來並截圖（需要 Xvfb 與 ImageMagick 的 import）。
用法：xvfb-run -a -s "-screen 0 1280x800x24" python dev/launcher_screens.py 輸出資料夾
用暫存的家目錄、桌面與開始功能表，不會動到這台電腦；程式來源用這個資料夾（bundle），所以不需要網路。
CI 會把截圖存成 artifact，也用來更新 docs/screens/launcher-*.png。"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))

from launcher_helpers import copy_app_tree, free_port, isolated_env  # noqa: E402

from cpe_coach.launcher import config as cfgmod  # noqa: E402
from cpe_coach.launcher import engine, gui, server  # noqa: E402
from cpe_coach.launcher.envcheck import Ctx  # noqa: E402
from cpe_coach.launcher.osinfo import detect  # noqa: E402


def seed_learning(ws_dir: Path) -> None:
    import json
    from cpe_coach.store import Workspace, new_problem_state
    ws = Workspace(ws_dir)
    t = time.time() - 20 * 86400
    with ws.events_path.open("a", encoding="utf-8") as f:
        for i, pid in enumerate(("d001", "d002", "d003")):
            f.write(json.dumps({"ts": t + i, "kind": "test", "problem": pid, "verdict": "AC", "lang": "py", "clean": True}) + "\n")
    st = ws.state()
    for pid in ("d001", "d002", "d003"):
        d = new_problem_state()
        d["first_pass"] = t
        st["problems"][pid] = d
    ws.save_state(st)


def main(out_dir: str) -> int:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="cpe-shots-"))
    env = isolated_env(tmp)
    os.environ.update(env)
    plat = detect(env=env, home=Path(env["HOME"]))
    tree = copy_app_tree(tmp / "tree")
    ctx = Ctx(plat=plat, net=lambda *a: True, bundle=tree, which=lambda n: None if n == "g++" else shutil.which(n) or "/usr/bin/" + n, has_tk=lambda: True)
    for name in ("showinfo", "showwarning", "showerror"):
        setattr(gui.messagebox, name, lambda *a, **k: None)
    gui.messagebox.askyesno = lambda *a, **k: True
    gui.messagebox.askyesnocancel = lambda *a, **k: True
    port = free_port()
    shots = []

    def snap(app, name):
        app.root.update()
        time.sleep(0.3)
        app.root.update()
        f = out / f"{name}.png"
        subprocess.run(["import", "-window", hex(app.root.winfo_id()), str(f)], check=True)
        shots.append(f.name)

    app = gui.GuiApp(plat, ctx)
    app.start()
    w = app.view
    snap(app, "01-welcome")
    w.btn_next.invoke()
    app.pump(lambda: bool(w.checks) and not w.busy, 30)
    snap(app, "02-checks")
    w.btn_next.invoke()
    w.v_app.set(str(tmp / "CPE-Coach" / "app"))
    w.v_ws.set(str(tmp / "CPE學習進度"))
    w.v_port.set(str(port))
    w.v_source.set("bundle")
    snap(app, "03-options")
    w.btn_next.invoke()
    app.pump(lambda: w.page == 3 and getattr(w, "step_idx", -1) >= 2, 30)
    snap(app, "04-installing")
    app.pump(lambda: w.page == 4, 120)
    snap(app, "05-done")
    w.btn_next.invoke()
    p = app.view
    seed_learning(tmp / "CPE學習進度")                      # 讓首頁「今天」卡片有東西可以顯示（20 天前解出兩題 → 現在該複習）
    p.load_today()
    app.pump(lambda: bool(p.today_info), 30)
    snap(app, "06-panel-stopped")
    with mock.patch.object(server, "open_ui", return_value="browser"):
        p.btn_main.invoke()
        app.pump(lambda: p.status.running and not p.busy, 40)
    snap(app, "07-panel-running")
    p.show_tab("settings")
    snap(app, "08-settings")
    p.show_tab("tools")
    p.tool_btns["doctor"].invoke()
    app.pump(lambda: not p.busy, 30)
    snap(app, "09-tools")
    p.show_tab("home")
    p.btn_main.invoke()
    app.pump(lambda: p.status.state == "stopped" and not p.busy, 30)
    p.show_tab("tools")
    p.tool_btns["uninstall"].invoke()
    u = app.view
    snap(app, "10-uninstall")
    u.v_delete.set(True)
    u.toggle()
    snap(app, "11-uninstall-delete")
    u.v_delete.set(False)
    u.toggle()
    u.btn_go.invoke()
    app.pump(lambda: u.done, 60)
    snap(app, "12-uninstalled")
    cfg = cfgmod.load(plat.launcher_home)
    if cfg:
        server.stop(cfg, plat)
    app.quit()
    engine.os.chdir(str(REPO))
    shutil.rmtree(tmp, ignore_errors=True)
    print("已輸出", len(shots), "張：", ", ".join(shots))
    return 0 if len(shots) == 12 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "launcher-screens"))
