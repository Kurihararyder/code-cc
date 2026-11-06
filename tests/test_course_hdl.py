"""Verilog 與 Tcl 軌道課綱：教材指向都存在、檢核有效、週數連續、資料和產生器一致；並實測判題方式的可行性（有工具才跑）。"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cpe_coach import course

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "dev"))
import course_hdl_refs as REF  # noqa: E402


class HdlCourseTests(unittest.TestCase):
    def tracks(self):
        return {t: course.load(t) for t in ("verilog", "tcl")}

    def test_shape(self):
        for t, c in self.tracks().items():
            self.assertEqual(c["track"], t)
            self.assertEqual(c["total_weeks"], sum(u["weeks"] for u in c["units"]), t)
            pos = 1
            for i, u in enumerate(c["units"], 1):
                self.assertEqual(u["n"], i)
                self.assertEqual(u["start"], pos)
                pos += u["weeks"]
                self.assertTrue(u["goal"] and u["learn"] and u["readings"] and u["check"], (t, u["title"]))
                self.assertEqual(len(u["weekly"]), u["weeks"])
                self.assertTrue(u["weekly"][-1]["gate"] and not any(w["gate"] for w in u["weekly"][:-1]))
            stages = [u["stage"] for u in c["units"]]
            self.assertEqual(stages, sorted(stages))
            self.assertEqual(set(stages), set(range(len(c["stages"]))))

    def test_every_pointer_matches_its_source(self):
        for t, c in self.tracks().items():
            for u in c["units"]:
                for r in u["readings"]:
                    self.assertIn(r["src"], c["resources"])
                    self.assertTrue(r["focus"])
                    if r["src"] == "hdlbits":
                        sec, _, names = r["where"].partition("｜")
                        for nm in [x.strip() for x in names.split("、") if x.strip()]:
                            self.assertIn(nm, REF.HDLBITS[sec], (t, sec, nm))
                    if r["src"] == "tclman":
                        for cmd in r["where"].split("、"):
                            self.assertIn(cmd, REF.TCL_CMDS, cmd)

    def test_gates_are_valid(self):
        for t, c in self.tracks().items():
            planned = set()
            for u in c["units"]:
                planned |= {p["id"] for p in u["planned"]}
                g = u["gate"]
                if g["type"] == "hdlbits":
                    for item in g["problems"]:
                        sec, _, nm = item.partition("｜")
                        self.assertIn(nm, REF.HDLBITS[sec])
                elif g["type"] == "planned":
                    self.assertTrue(set(g["problems"]) <= planned, (t, u["title"]))
                else:
                    self.assertEqual(g["type"], "project")
                    self.assertGreaterEqual(len(g["criteria"]), 2)

    def test_planned_ids_unique_per_track(self):
        for t, c in self.tracks().items():
            ids = [p["id"] for u in c["units"] for p in u["planned"]]
            self.assertEqual(len(ids), len(set(ids)), t)

    def test_generated_files_are_current(self):
        files = [ROOT / "cpe_coach/data/course_verilog.json", ROOT / "cpe_coach/data/course_tcl.json", ROOT / "COURSE_VERILOG.md", ROOT / "COURSE_TCL.md"]
        before = [f.read_text(encoding="utf-8") for f in files]
        r = subprocess.run([sys.executable, str(ROOT / "dev/gen_course_hdl.py")], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(before, [f.read_text(encoding="utf-8") for f in files])


@unittest.skipUnless(shutil.which("iverilog") and shutil.which("vvp"), "沒有安裝 iverilog")
class VerilogJudgingFeasibilityTests(unittest.TestCase):
    """課綱規劃的判題方式：iverilog 編譯＋vvp 執行 testbench，看輸出是 PASS 或 FAIL。這裡證明這個方式能分辨對與錯的設計。"""
    TB = """module tb; reg [3:0] a,b; wire [4:0] s; integer i, errs=0; adder u(.a(a),.b(b),.s(s));
      initial begin for (i=0;i<256;i=i+1) begin {a,b}=i[7:0]; #1; if (s !== a+b) errs=errs+1; end
      if (errs==0) $display("PASS"); else $display("FAIL %0d", errs); $finish; end endmodule"""

    def run_design(self, body):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "dut.v").write_text(f"module adder(input [3:0] a, b, output [4:0] s); {body} endmodule", encoding="utf-8")
            (Path(d) / "tb.v").write_text(self.TB, encoding="utf-8")
            c = subprocess.run(["iverilog", "-g2012", "-o", str(Path(d) / "sim"), str(Path(d) / "tb.v"), str(Path(d) / "dut.v")], capture_output=True, text=True)
            self.assertEqual(c.returncode, 0, c.stderr)
            return subprocess.run(["vvp", str(Path(d) / "sim")], capture_output=True, text=True, timeout=30).stdout

    def test_correct_and_wrong_designs_are_told_apart(self):
        self.assertIn("PASS", self.run_design("assign s = a + b;"))
        self.assertIn("FAIL", self.run_design("assign s = a ^ b;"))
        self.assertIn("FAIL", self.run_design("assign s = {1'b0, a} + {1'b0, b} - 1;"))


@unittest.skipUnless(shutil.which("tclsh"), "沒有安裝 tclsh")
class TclJudgingFeasibilityTests(unittest.TestCase):
    def run_script(self, text):
        with tempfile.TemporaryDirectory() as d:                      # 判題用檔案執行（從標準輸入餵入時 tclsh 把錯誤印出後仍以 0 結束）
            f = Path(d) / "s.tcl"
            f.write_text(text, encoding="utf-8")
            return subprocess.run(["tclsh", str(f)], capture_output=True, text=True, timeout=30)

    def test_tclsh_runs_scripts_and_exposes_errors(self):
        ok = self.run_script("proc f {n} {expr {$n<2 ? $n : [f [expr {$n-1}]]+[f [expr {$n-2}]]}}\nputs [f 10]\n")
        self.assertEqual((ok.returncode, ok.stdout.strip()), (0, "55"))
        bad = self.run_script("puts [nosuchcommand]\n")
        self.assertNotEqual(bad.returncode, 0)


if __name__ == "__main__":
    unittest.main()
