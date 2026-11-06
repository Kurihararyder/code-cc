"""課程軌道：各自記進度、不影響 py 主線、非法軌道被擋。"""
import tempfile
import unittest
from pathlib import Path

from cpe_coach import bank as bank_mod
from cpe_coach import tracks
from cpe_coach.store import Workspace


class TrackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Workspace.create(Path(self.tmp.name), "2026-11-01")
        self.bank = bank_mod.load_bank(self.ws)

    def tearDown(self):
        self.tmp.cleanup()

    def test_overview_has_four_tracks(self):
        self.assertEqual([o["track"] for o in tracks.overview(self.ws)], ["py", "cpp", "verilog", "tcl"])

    def test_progress_is_per_track(self):
        tracks.mark_done(self.ws, "tcl", 1)
        ov = {o["track"]: o for o in tracks.overview(self.ws)}
        self.assertEqual((ov["tcl"]["done"], ov["tcl"]["current"]), (1, 2))
        self.assertEqual((ov["verilog"]["done"], ov["py"]["done"]), (0, 0))
        self.assertEqual(self.ws.state()["course"]["done"], [])

    def test_goto_marks_earlier_done(self):
        tracks.goto(self.ws, "verilog", 5)
        m = tracks.course_map(self.ws, "verilog", __import__("datetime").date(2026, 11, 1))
        self.assertEqual(m["done"], 4)
        self.assertEqual(m["current"], 5)

    def test_unit_detail_every_unit(self):
        for t in ("cpp", "verilog", "tcl"):
            from cpe_coach import course
            for u in course.load(t)["units"]:
                d = tracks.unit_detail(self.ws, self.bank, t, u["n"])
                self.assertTrue(d["resources"] or not d["readings"], (t, u["n"]))

    def test_bad_track_and_unit(self):
        with self.assertRaises(ValueError):
            tracks.course_map(self.ws, "rust", __import__("datetime").date.today())
        with self.assertRaises(ValueError):
            tracks.goto(self.ws, "tcl", 999)

    def test_cpp_unit_with_drills_needs_them_passed(self):
        with self.assertRaises(ValueError):
            tracks.mark_done(self.ws, "cpp", 1)


if __name__ == "__main__":
    unittest.main()
