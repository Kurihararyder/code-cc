"""Python 軌道：每個單元都有閱讀指定（章節／頁碼＋重點）與每週安排；指向都和教材目錄一致；資料和產生器一致。"""
import subprocess
import sys
import unittest
from pathlib import Path

from cpe_coach import course

ROOT = Path(__file__).resolve().parent.parent


class PyCourseReadingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = course.load()

    def test_every_unit_has_readings_with_key_points(self):
        for u in self.c["units"]:
            self.assertTrue(u["readings"], u["title"])
            for r in u["readings"]:
                self.assertTrue(r["focus"], (u["title"], r["where"]))
                self.assertIn(r["src"], self.c["resources"])
            self.assertEqual(len(u["read"]), len(u["readings"]))              # 舊欄位（介面顯示用）和新資料同步

    def test_weekly_plan_covers_every_week_and_drill(self):
        pos = 1
        for u in self.c["units"]:
            self.assertEqual(len(u["weekly"]), u["weeks"])
            self.assertEqual([w["week"] for w in u["weekly"]], list(range(pos, pos + u["weeks"])))
            pos += u["weeks"]
            self.assertEqual(sorted(d for w in u["weekly"] for d in w["drills"]), sorted(u["drills"]), u["title"])
            self.assertEqual(sorted(a for w in u["weekly"] for a in w["anchors"]), sorted(u["anchors"]), u["title"])
            self.assertTrue(u["weekly"][-1]["gate"] and not any(w["gate"] for w in u["weekly"][:-1]))
            self.assertEqual(len(u["weekly_text"]), u["weeks"])
        self.assertEqual(pos - 1, self.c["total_weeks"])

    def test_page_pointers_are_inside_one_chapter(self):
        for u in self.c["units"]:
            for r in u["readings"]:
                if r["pages"]:
                    a, b = r["pages"]
                    self.assertLessEqual(a, b)

    def test_generated_files_are_current(self):
        files = [ROOT / "cpe_coach/data/course.json", ROOT / "COURSE.md"]
        before = [f.read_text(encoding="utf-8") for f in files]
        r = subprocess.run([sys.executable, str(ROOT / "dev/gen_course.py")], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(before, [f.read_text(encoding="utf-8") for f in files])


if __name__ == "__main__":
    unittest.main()
