"""由 dev/hdl_problems_data.py 產生 cpe_coach/data/hdl_problems.json，並逐題自我驗證：
參考解必須 AC、故意寫錯的版本必須判失敗；Tcl 手寫的範例期望輸出必須等於參考解的輸出。"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dev"))
from cpe_coach import hdl  # noqa: E402
import hdl_problems_data as D  # noqa: E402

OUT = ROOT / "cpe_coach" / "data" / "hdl_problems.json"


def run_tcl(code: str, stdin: str) -> str:
    with tempfile.TemporaryDirectory() as d:
        Path(d, "s.tcl").write_text(hdl.TCL_PRELUDE + code, encoding="utf-8")
        r = subprocess.run(["tclsh", "s.tcl"], cwd=d, input=stdin.encode("utf-8"), capture_output=True, timeout=30)
        if r.returncode != 0:
            raise SystemExit("參考解執行錯誤：" + r.stderr.decode("utf-8", "replace"))
        return r.stdout.decode("utf-8")


def main() -> int:
    if not hdl.tools()["verilog"] or not hdl.tools()["tcl"]:
        raise SystemExit("需要 iverilog／vvp 與 tclsh 才能產生並驗證題庫")
    out = {}
    for pid, p in sorted(D.V.items()):
        data = {k: p[k] for k in ("track", "unit", "title", "statement", "template", "testbench", "require", "ref")}
        r = hdl.judge_verilog(data, p["ref"])
        if r["verdict"] != "AC":
            raise SystemExit(f"{pid} 參考解沒有通過：{r['verdict']}\n{r['log']}")
        r = hdl.judge_verilog(data, p["bad"])
        if r["verdict"] == "AC":
            raise SystemExit(f"{pid} 故意寫錯的版本竟然通過了——測試台太弱")
        out[pid] = data
    for pid, p in sorted(D.T.items()):
        tests = []
        sin, sexp = p["sample"]
        full = lambda code: code + "\n" + p["harness"]  # noqa: E731
        got = run_tcl(full(p["ref"]), sin)
        if hdl._tcl_norm(got) != hdl._tcl_norm(sexp):
            raise SystemExit(f"{pid} 手寫範例期望與參考解不同：\n期望：{sexp!r}\n參考解：{got!r}")
        tests.append({"in": sin, "out": sexp})
        for s in p["inputs"]:
            tests.append({"in": s, "out": run_tcl(full(p["ref"]), s)})
        data = {"track": "tcl", "unit": p["unit"], "title": p["title"], "statement": p["statement"], "template": p["template"],
                "harness": p["harness"], "tests": tests, "ref": p["ref"]}
        r = hdl.judge_tcl(data, p["ref"])
        if r["verdict"] != "AC":
            raise SystemExit(f"{pid} 參考解沒有通過：{r}")
        r = hdl.judge_tcl(data, p["bad"])
        if r["verdict"] == "AC":
            raise SystemExit(f"{pid} 故意寫錯的版本竟然通過了——測資太弱")
        out[pid] = data
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"hdl 題庫：Verilog {len(D.V)} 題、Tcl {len(D.T)} 題（參考解皆 AC、錯誤版本皆被擋下）")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
