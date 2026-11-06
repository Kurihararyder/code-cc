"""C++ 軌道課綱：題目都存在、檢核有效、週數連續、資料和產生器一致。"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from cpe_coach import bank, course

ROOT = Path(__file__).resolve().parent.parent


class CppCourseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = course.load("cpp")
        cls.ids = {d["id"] for d in json.loads((ROOT / "cpe_coach/data/drills/index.json").read_text(encoding="utf-8"))}

    def test_shape(self):
        c = self.c
        self.assertEqual(c["track"], "cpp")
        self.assertEqual(len(c["stages"]), 6)
        self.assertEqual([u["n"] for u in c["units"]], list(range(1, len(c["units"]) + 1)))
        self.assertEqual(c["total_weeks"], sum(u["weeks"] for u in c["units"]))
        pos = 1
        for u in c["units"]:
            self.assertEqual(u["start"], pos)
            pos += u["weeks"]
            self.assertEqual(u["lang"], "cpp")
            self.assertTrue(u["goal"] and u["learn"] and u["check"], u["title"])
        stages = [u["stage"] for u in c["units"]]
        self.assertEqual(stages, sorted(stages))
        self.assertEqual(set(stages), set(range(6)))

    def test_every_referenced_problem_exists_and_none_is_reused_as_practice(self):
        seen = set()
        for u in self.c["units"]:
            for d in u["drills"]:
                self.assertIn(d, self.ids, d)
                self.assertFalse(bank.is_reserve(d) if hasattr(bank, "is_reserve") else d.startswith("e"), d)
                self.assertNotIn(d, seen, f"{d} 重複")
                seen.add(d)
            g = u["gate"]
            if g["type"] == "set":
                for p in g["problems"]:
                    self.assertIn(p, self.ids, p)
                self.assertTrue(any(p not in u["drills"] for p in g["problems"]), u["title"])
                self.assertTrue(1 <= g["need"] <= len(g["problems"]))
            else:
                self.assertEqual(g["type"], "project")
                self.assertGreaterEqual(len(g["criteria"]), 2, u["title"])

    def test_planned_problem_ids_unique(self):
        ids = [p["id"] for u in self.c["units"] for p in u["planned"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(i not in self.ids for i in ids))                 # 待新增的題號不能和現有題庫衝突

    def test_resources_resolve(self):
        for u in self.c["units"]:
            for r in u["resources"]:
                self.assertIn(r, self.c["resources"], r)

    def test_python_track_is_unchanged_by_default(self):
        self.assertEqual(len(course.load()["units"]), 52)

    def test_generated_files_are_current(self):
        before = ((ROOT / "cpe_coach/data/course_cpp.json").read_text(encoding="utf-8"), (ROOT / "COURSE_CPP.md").read_text(encoding="utf-8"))
        r = subprocess.run([sys.executable, str(ROOT / "dev/gen_course_cpp.py")], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        after = ((ROOT / "cpe_coach/data/course_cpp.json").read_text(encoding="utf-8"), (ROOT / "COURSE_CPP.md").read_text(encoding="utf-8"))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
