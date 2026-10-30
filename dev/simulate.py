"""模擬一位完美學員走完 Python 單元，驗證課程、題目安裝、判題、檢核、推進全部串得起來。"""
import io, json, os, sys, tempfile, contextlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).parent.parent))
import drills_s0, drills_s1, drills_s2, drills_s3, drills_s4, drills_e
from common import DRILLS
from cpe_coach import cli, course as course_mod
from cpe_coach.store import Workspace

REF = {d["id"]: d["ref"] for d in DRILLS}
tmp = tempfile.mkdtemp()
os.chdir(tmp)

def run(*args, quiet=True):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = cli.main(list(args))
    if not quiet: print(buf.getvalue())
    return rc, buf.getvalue()

run("init", "ws", "--start", "2026-11-02")
os.chdir("ws")
ws = Workspace.find()
cfg = ws.config(); cfg["timeout_sec"] = 60; ws.save_config(cfg)
c = course_mod.load()
SKIP_CPP = True
fails = []
for u in c["units"]:
    cur = course_mod.current_unit(ws, c)
    if cur["n"] != u["n"]: fails.append(("不同步", u["n"], cur["n"])); break
    if u["lang"] == "cpp":
        print(f"單元 {u['n']} 是 C++ 單元 → goto 下一個"); course_mod.goto(ws, c, u["n"] + 1); continue
    for d in u["drills"]:
        rc, out = run("new", d)
        assert rc == 0, out
        Path(f"solutions/{d}.py").write_text(REF[d], encoding="utf-8")
        rc, out = run("test", d)
        if rc != 0: fails.append(("drill 失敗", d, out[-300:]))
    if not u["gate"]:
        run("course", "next"); continue
    rc, out = run("gate")
    if rc != 0: fails.append(("gate 開不起來", u["n"], out)); break
    exam = ws.exam()
    for pid in exam["problems"]:
        Path(ws.root, exam["files"][pid]).write_text(REF[pid], encoding="utf-8")
        run("test", pid)
    rc, out = run("mock", "finish")
    ok = "檢核通過" in out
    print(f"單元 {u['n']:>2} {u['title'][:14]:<14} gate {'通過' if ok else '未過'} {exam['problems']}")
    if not ok:
        fails.append(("gate 未過", u["n"], out)); course_mod.goto(ws, c, u["n"] + 1)
print("失敗:", fails if fails else "無")
print("最終單元:", ws.state()["course"]["unit"], "stage", ws.config()["stage"])
