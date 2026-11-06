"""Verilog／Tcl 題庫：資料形狀、判題（需要 iverilog／tclsh）、與軌道進度的連動、網頁 API。"""
import json
import shutil
import socket
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

from cpe_coach import hdl, tracks, web
from cpe_coach.store import Workspace

HAVE_V = bool(shutil.which("iverilog") and shutil.which("vvp"))
HAVE_T = bool(shutil.which("tclsh"))
PROBLEMS = json.loads(hdl.DATA.read_text(encoding="utf-8"))


class Shape(unittest.TestCase):
    def test_every_problem_is_planned_in_a_course(self):
        from cpe_coach import course
        planned = {}
        for t in ("verilog", "tcl"):
            for u in course.load(t)["units"]:
                for p in u["planned"]:
                    planned[p["id"]] = (t, u["n"])
        for pid, p in PROBLEMS.items():
            self.assertEqual(planned.get(pid), (p["track"], p["unit"]), pid)

    def test_fields(self):
        for pid, p in PROBLEMS.items():
            self.assertTrue(p["statement"] and p["template"] and p["ref"], pid)
            if p["track"] == "verilog":
                self.assertIn("ALL PASS", p["testbench"])
            else:
                self.assertTrue(len(p["tests"]) >= 3, pid)


@unittest.skipUnless(HAVE_V, "需要 iverilog")
class VerilogJudge(unittest.TestCase):
    def test_reference_passes_and_template_fails(self):
        for pid, p in PROBLEMS.items():
            if p["track"] != "verilog":
                continue
            self.assertEqual(hdl.judge(pid, p["ref"])["verdict"], "AC", pid)
            self.assertEqual(hdl.judge(pid, p["template"])["verdict"], "WA", pid)

    def test_compile_error_and_timeout_shape(self):
        self.assertEqual(hdl.judge("v007", "module top_module(")["verdict"], "CE")

    def test_require_helper_module(self):
        self.assertEqual(hdl.judge("v005", "module top_module(input [7:0] a, input [7:0] b, input cin, output [7:0] sum, output cout);\n"
                                   "assign {cout,sum} = a + b + cin;\nendmodule")["verdict"], "WA")


@unittest.skipUnless(HAVE_T, "需要 tclsh")
class TclJudge(unittest.TestCase):
    def test_reference_passes_and_empty_fails(self):
        for pid, p in PROBLEMS.items():
            if p["track"] != "tcl":
                continue
            self.assertEqual(hdl.judge(pid, p["ref"])["verdict"], "AC", pid)
            self.assertNotEqual(hdl.judge(pid, "# nothing\n")["verdict"], "AC", pid)

    def test_runtime_error_reported(self):
        r = hdl.judge("t001", "error boom")
        self.assertEqual(r["verdict"], "RE")
        self.assertIn("boom", r["log"])


@unittest.skipUnless(HAVE_V and HAVE_T, "需要 iverilog 與 tclsh")
class Integration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Workspace.create(Path(self.tmp.name), "2026-11-01")

    def tearDown(self):
        self.tmp.cleanup()

    def test_unit_needs_available_problems_passed(self):
        with self.assertRaises(ValueError):
            tracks.mark_done(self.ws, "verilog", 6)             # v012 已開放，還沒通過
        hdl.judge_and_record(self.ws, "v012", PROBLEMS["v012"]["ref"])
        tracks.mark_done(self.ws, "verilog", 6)
        self.assertIn(6, self.ws.state()["tracks"]["verilog"]["done"])

    def test_failed_attempt_does_not_count(self):
        hdl.judge_and_record(self.ws, "t001", "puts nope")
        d = tracks.unit_detail(self.ws, {}, "tcl", 1)
        self.assertFalse(d["planned"][0]["done"])
        self.assertTrue(d["planned"][0]["available"])
        self.assertTrue((self.ws.root / "hdl" / "t001.tcl").exists())

    def test_web_api(self):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
        app = web.App(Path(self.tmp.name), port)
        httpd = web.LocalServer(("127.0.0.1", port), web.make_handler(app))
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            def call(path, body=None):
                h = {"Host": f"127.0.0.1:{port}", "X-CPE-Token": app.token}
                if body is not None:
                    h["Content-Type"] = "application/json"
                r = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=None if body is None else json.dumps(body).encode(),
                                           headers=h, method="GET" if body is None else "POST")
                return json.load(urllib.request.urlopen(r))
            self.assertEqual(len(call("/api/hdl")["problems"]), len(PROBLEMS))
            P = call("/api/hdl/problem?id=t001")
            self.assertNotIn("ref", P)
            self.assertNotIn("tests", P)
            self.assertEqual(call("/api/hdl/run", {"id": "t001", "code": PROBLEMS["t001"]["ref"]})["verdict"], "AC")
        finally:
            httpd.shutdown()
            httpd.server_close()


if __name__ == "__main__":
    unittest.main()


class Vcd(unittest.TestCase):
    SAMPLE = """$timescale 1ps $end
$scope module tb $end
$var wire 1 ! clk $end
$var reg 4 " q [3:0] $end
$var integer 32 # i $end
$scope module dut $end
$var wire 1 $ inner $end
$upscope $end
$upscope $end
$enddefinitions $end
#0
0!
b101 "
b0 #
0$
#5
1!
#10
b11 "
#10
"""

    def test_parse_keeps_only_top_scope_signals_and_pads_bus_values(self):
        r = hdl.parse_vcd(self.SAMPLE)
        self.assertEqual([s["name"] for s in r["signals"]], ["clk", "q"])
        self.assertEqual(r["times"], [0, 5, 10])
        self.assertEqual(r["values"]["clk"], ["0", "1", "1"])
        self.assertEqual(r["values"]["q"], ["0101", "0101", "0011"])

    def test_max_points(self):
        body = "".join(f"#{i}\n{i % 2}!\n" for i in range(200))
        r = hdl.parse_vcd("$scope module tb $end\n$var wire 1 ! clk $end\n$upscope $end\n$enddefinitions $end\n" + body, max_points=10)
        self.assertEqual(len(r["times"]), 10)

    @unittest.skipUnless(HAVE_V, "需要 iverilog")
    def test_wave_of_a_real_problem(self):
        r = hdl.wave("v007", PROBLEMS["v007"]["ref"])
        self.assertTrue(r["ok"])
        names = {s["name"] for s in r["signals"]}
        self.assertTrue({"req", "idx_d", "idx_r", "valid_d", "valid_r"} <= names)
        self.assertFalse(hdl.wave("v007", "module top_module(")["ok"])
        with self.assertRaises(ValueError):
            hdl.wave("t001", "")
