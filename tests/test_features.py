"""歷屆題庫、擬真考試、難度校準、每日計畫、工程任務驗收。"""
import tempfile
import unittest
from pathlib import Path

from cpe_coach import bank as bank_mod
from cpe_coach import calibrate, cli, course, eng, mock, pastexams, vocab
from cpe_coach import plan as plan_mod
from cpe_coach.store import Workspace, new_problem_state

DAY = 86400.0
MIN = 60.0


class Clock:
    def __init__(self, t=1_800_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


def make_ws():
    tmp = tempfile.TemporaryDirectory()
    clock = Clock()
    return tmp, Workspace.create(Path(tmp.name), "2026-11-01", clock), clock


def solve(ws, clock, pid, plan):
    """plan: [(分鐘後, 判定)]，依序記錄 test 事件。"""
    for dt_min, verdict in plan:
        clock.t += dt_min * MIN
        ws.log("test", problem=pid, verdict=verdict, lang="py")
        if verdict == "AC":
            st = ws.state()
            p = st["problems"].setdefault(pid, new_problem_state())
            p["attempts"] = p.get("attempts", 0) + len(plan)
            p["first_pass"] = clock.t
            ws.save_state(st)


# ---------- 歷屆題庫 ----------
class PastExamTests(unittest.TestCase):
    def test_bands(self):
        self.assertEqual([pastexams.stars_from_accuracy(a) for a in (44.9, 15.0, 14.9, 3.6, 2.0, 0.96, 0.5, 0.09, 0)], [1, 1, 2, 2, 2, 3, 3, 4, 4])
        self.assertIsNone(pastexams.stars_from_accuracy(None))

    def test_bundled_is_honest(self):
        data = pastexams.load_all(None)
        e = next(x for x in data["exams"] if x["date"] == "2020-10-20")
        self.assertEqual(len(e["problems"]), 7)
        self.assertEqual(sum(1 for p in e["problems"] if p["uva"] is None), 2)       # 報告沒給 UVA 題號的就是沒有
        self.assertAlmostEqual(sum(v for v in data["distribution"].values()), 100.0, delta=0.5)

    def test_problem_ids(self):
        self.assertEqual(pastexams.problem_id({"uva": 458, "order": 2}, "2020-10-20"), "uva458")
        self.assertEqual(pastexams.problem_id({"uva": None, "order": 6}, "2020-10-20"), "cpe20201020q6")

    def test_parse_manifest_formats_and_errors(self):
        text = "date,order,uva,title,accuracy\n2021-03-02,1,100,The 3n+1 problem,41.5%\n2021-03-02\t2\tuva101\tBlocks Problem\t12\n" \
               "2021-03-02 3 - Mystery Box 0.8\n# 2021-03-02 avg=1.7\nnot a line\n2021-13-40,1,1,x,1\n2021-03-02,2,102,Dup,abc\n"
        exams, errors = pastexams.parse_manifest(text)
        self.assertEqual(len(exams), 1)
        e = exams[0]
        self.assertEqual((e["date"], e["avg_solved"]), ("2021-03-02", 1.7))
        self.assertEqual([(p["order"], p["uva"], p["accuracy"]) for p in e["problems"]], [(1, 100, 41.5), (2, 101, 12.0), (3, None, 0.8)])
        self.assertEqual(e["problems"][2]["title"], "Mystery Box")
        self.assertEqual(len(errors), 3)          # 無效行、無效日期、答對率不是數字

    def test_import_merges_and_rejects_empty(self):
        tmp, ws, _ = make_ws()
        with tmp:
            with self.assertRaises(pastexams.ManifestError):
                pastexams.import_manifest(ws, "garbage")
            r = pastexams.import_manifest(ws, "2022-05-01,1,10055,Hashmat the brave warrior,60\n2022-05-01,2,,Odd One,1.5")
            self.assertEqual((r["exams"], r["problems"]), (1, 2))
            pastexams.import_manifest(ws, "2022-05-01,2,10056,Odd One Fixed,1.6\n# 2022-05-01 avg=2.0")
            e = next(x for x in pastexams.load_all(ws)["exams"] if x["date"] == "2022-05-01")
            self.assertEqual(len(e["problems"]), 2)
            self.assertEqual(e["problems"][1]["uva"], 10056)
            self.assertEqual(e["avg_solved"], 2.0)

    def test_merge_into_bank_overrides_stars_with_official(self):
        tmp, ws, _ = make_ws()
        with tmp:
            pastexams.import_manifest(ws, "2022-05-01,1,10004,Bicoloring,0.3")
            b = bank_mod.load_bank(ws)
            self.assertEqual(b["uva10004"]["difficulty"], 4)
            self.assertEqual(b["uva10004"]["difficulty_source"], "official")
            self.assertEqual(b["uva10004"]["official_accuracy"], 0.3)

    def test_percentile(self):
        dist = pastexams.load_all(None)["distribution"]
        p = pastexams.percentile(3, dist)
        self.assertAlmostEqual(p["top"] + p["beats"], 100.0, delta=0.5)
        self.assertEqual(pastexams.percentile(0, dist)["top"], 100.0)
        self.assertLess(pastexams.percentile(6, dist)["top"], 1.0)

    def test_pool(self):
        tmp, ws, _ = make_ws()
        with tmp:
            pastexams.import_manifest(ws, "2022-05-01,1,10055,A,60\n2022-05-01,2,10056,B,2.5\n2022-05-01,3,10057,C,0.2")
            ids = [p["id"] for p in pastexams.pool(ws, bank_mod.load_bank(ws), 1, 100) if p["id"] in ("uva10055", "uva10056", "uva10057")]
            self.assertEqual(ids, ["uva10055", "uva10056"])


class PastStartTests(unittest.TestCase):
    MAN = "\n".join(f"2023-01-10,{i},{20000 + i},Prob {i},{50 / i}" for i in range(1, 8))

    def setUp(self):
        self.tmp, self.ws, self.clock = make_ws()
        pastexams.import_manifest(self.ws, self.MAN)

    def tearDown(self):
        self.tmp.cleanup()

    def add_tests(self, pid, english=True):
        d = self.ws.tests / pid
        d.mkdir(parents=True, exist_ok=True)
        (d / "s1.in").write_text("1\n", encoding="utf-8")
        (d / "s1.out").write_text("2\n", encoding="utf-8")
        (self.ws.root / "statements").mkdir(exist_ok=True)
        (self.ws.root / "statements" / f"{pid}.txt").write_text(("Read an integer from the standard input and print twice the value of that integer on a single line. " * 2) if english else "讀入一個整數並輸出兩倍。" * 10, encoding="utf-8")

    def test_refuses_when_tests_missing_then_partial(self):
        b = bank_mod.load_bank(self.ws)
        with self.assertRaises(ValueError) as cm:
            course.start_past(self.ws, b, "2023-01-10")
        self.assertIn("7 題還沒有測資", str(cm.exception))
        with self.assertRaises(ValueError):
            course.start_past(self.ws, b, "2023-01-10", partial=True)
        self.add_tests("uva20001")
        self.add_tests("uva20003")
        ex = course.start_past(self.ws, b, "2023-01-10", partial=True)
        self.assertEqual(ex["problems"], ["uva20001", "uva20003"])
        self.assertEqual((ex["kind"], ex["minutes"], ex["past"]), ("past", 180, "2023-01-10"))

    def test_full_exam_in_original_order_and_scoreboard(self):
        for i in range(1, 8):
            self.add_tests(f"uva{20000 + i}")
        b = bank_mod.load_bank(self.ws)
        ex = course.start_past(self.ws, b, "2023-01-10")
        self.assertEqual(ex["problems"], [f"uva{20000 + i}" for i in range(1, 8)])
        self.clock.t += 10 * MIN
        mock.record(self.ws, ex, "uva20001", "WA")
        self.clock.t += 5 * MIN
        mock.record(self.ws, ex, "uva20001", "AC")
        self.clock.t += 20 * MIN
        mock.record(self.ws, ex, "uva20002", "AC")
        mock.record(self.ws, ex, "uva20003", "WA")
        ex = self.ws.exam()
        dist = pastexams.load_all(self.ws)["distribution"]
        board = mock.scoreboard(ex, b, dist)
        self.assertEqual((board["solved"], board["total"], board["wrong"]), (2, 7, 2))
        self.assertEqual(board["penalty"], 15 + 20 + 35)                 # 15 分通過 + 一次錯 20 分，加上第二題 35 分
        self.assertEqual([r["status"] for r in board["rows"][:3]], ["ac", "ac", "wrong"])
        self.assertEqual(board["rows"][0]["stars"], 1)                   # 50% → ★1
        self.assertIsNotNone(board["percentile"])
        s = mock.finish(self.ws, dist)
        self.assertEqual(s["solved"], 2)
        self.assertEqual(s["past"], "2023-01-10")
        self.assertAlmostEqual(s["percentile"]["top"] + s["percentile"]["beats"], 100.0, delta=0.5)

    def test_real_mode_needs_english_statements(self):
        b = bank_mod.load_bank(self.ws)
        with self.assertRaises(ValueError) as cm:
            course.start_mock(self.ws, b, "weekly", real=True)
        self.assertIn("已通過", str(cm.exception))
        st = self.ws.state()
        for i in range(1, 4):
            self.add_tests(f"uva{20000 + i}", english=(i != 3))
            st["problems"][f"uva{20000 + i}"] = dict(new_problem_state(), first_pass=self.clock.t - DAY * i, last_pass=self.clock.t - DAY * i)
        self.ws.save_state(st)
        with self.assertRaises(ValueError) as cm:
            course.start_mock(self.ws, b, "weekly", real=True)            # 第 3 題是中文，只有 2 題合格
        self.assertIn("目前只有 2 題", str(cm.exception))
        self.add_tests("uva20003", english=True)
        ex = course.start_mock(self.ws, b, "weekly", real=True)
        self.assertEqual(sorted(ex["problems"]), ["uva20001", "uva20002", "uva20003"])


class UnitPoolTests(unittest.TestCase):
    def test_unit_pool_ranges_and_exclusive_upper_bound(self):
        tmp, ws, _ = make_ws()
        with tmp:
            pastexams.import_manifest(ws, "2022-05-01,1,30001,Easy,45\n2022-05-01,2,30002,Edge,30\n2022-05-01,3,30003,Mid,20\n2022-05-01,4,30004,Hard,0.8")
            b = bank_mod.load_bank(ws)
            ids15 = [p["id"] for p in pastexams.unit_pool(ws, b, 15)["items"] if p["id"].startswith("uva3000")]
            ids16 = [p["id"] for p in pastexams.unit_pool(ws, b, 16)["items"] if p["id"].startswith("uva3000")]
            self.assertEqual(ids15, ["uva30001", "uva30002"])               # 單元 15：≥ 30%
            self.assertEqual(ids16, ["uva30003"])                           # 單元 16：15%–30%，30% 屬於單元 15，不重複
            self.assertEqual([p["id"] for p in pastexams.unit_pool(ws, b, 50)["items"] if p["id"].startswith("uva3000")], ["uva30004"])
            self.assertIsNone(pastexams.unit_pool(ws, b, 3))

    def test_every_imported_problem_is_reachable_from_some_unit(self):
        """『每一題歷屆題都要用進去』：任何答對率都至少落在一個單元的建議範圍內。"""
        for acc in (100, 45, 30, 22, 15, 9, 5, 4.9, 2, 0.5, 0.09, 0):
            hits = [n for n, (lo, hi, _) in pastexams.UNIT_POOLS.items() if lo <= acc <= (hi if hi >= 100 else hi - 1e-9)]
            self.assertTrue(hits, f"答對率 {acc}% 沒有單元會用到")

    def test_plan_offers_past_problem_when_unit_drills_done(self):
        tmp, ws, clock = make_ws()
        with tmp:
            pastexams.import_manifest(ws, "2022-05-01,1,30001,Easy,45")
            d = ws.tests / "uva30001"
            d.mkdir(parents=True)
            (d / "s.in").write_text("1\n", encoding="utf-8")
            (d / "s.out").write_text("1\n", encoding="utf-8")
            c = course.load()
            st = ws.state()
            st["course"]["unit"] = 15
            u = course.get_unit(c, 15)
            for pid in u["drills"]:
                st["problems"][pid] = dict(new_problem_state(), first_pass=clock.t - DAY, last_pass=clock.t - DAY, passes=1, attempts=1)
            ws.save_state(st)
            for pid in u["drills"]:
                ws.log("test", problem=pid, verdict="AC", lang="py")
            items = plan_mod.build(ws, 90)["items"]
            self.assertIn("uva30001", [i["id"] for i in items if i["kind"] == "past"])


class VocabTests(unittest.TestCase):
    def test_add_remove_csv_and_dedupe(self):
        tmp, ws, _ = make_ws()
        with tmp:
            vocab.add(ws, "Hartal", "uva10050", "strike")
            vocab.add(ws, "  hartal ", "uva10050")                  # 同字不同大小寫視為同一個
            vocab.add(ws, "permutation")
            self.assertEqual([w["word"] for w in vocab.items(ws)], sorted(w["word"] for w in vocab.items(ws)))
            self.assertEqual(len(vocab.items(ws)), 2)
            self.assertIn("hartal", vocab.to_csv(ws).lower())
            self.assertTrue(vocab.remove(ws, "permutation"))
            self.assertFalse(vocab.remove(ws, "permutation"))
            with self.assertRaises(ValueError):
                vocab.add(ws, "two words")
            self.assertTrue(vocab.DICT_URL.startswith("https://dictionary.cambridge.org/"))


# ---------- 難度校準 ----------
class CalibrateTests(unittest.TestCase):
    def test_effort_uses_time_attempts_and_hints(self):
        tmp, ws, clock = make_ws()
        with tmp:
            solve(ws, clock, "p1", [(3, "WA"), (3, "AC")])                       # 3 分 + 3 分，2 次嘗試
            clock.t += 3 * DAY                                                   # 隔了很久才回來：中間不算工作時間
            ws.log("hint", problem="p2", level=1)
            solve(ws, clock, "p2", [(10, "AC")])
            ef = calibrate.efforts(ws.events())
            self.assertEqual(ef["p1"]["attempts"], 2)
            self.assertAlmostEqual(ef["p1"]["active_min"], calibrate.BASE_MIN + 3.0, delta=0.1)
            self.assertAlmostEqual(ef["p1"]["effort_min"], ef["p1"]["active_min"] + 4, delta=0.1)
            self.assertEqual(ef["p2"]["hints"], 1)
            self.assertAlmostEqual(ef["p2"]["effort_min"], calibrate.BASE_MIN + 10 + 6, delta=0.1)

    def test_unsolved_problems_have_no_effort(self):
        tmp, ws, clock = make_ws()
        with tmp:
            solve(ws, clock, "p1", [(2, "WA"), (2, "RE")])
            self.assertEqual(calibrate.efforts(ws.events()), {})

    def test_calibrate_needs_three_solves_before_adjusting(self):
        tmp, ws, clock = make_ws()
        with tmp:
            bank = {f"p{i}": {"id": f"p{i}", "title": f"P{i}", "difficulty": 2} for i in range(4)}
            solve(ws, clock, "p0", [(5, "AC")])
            c = calibrate.calibrate(ws, bank)
            self.assertEqual((c["solved"], c["factor"], c["enough"]), (1, 1.0, False))
            for i in (1, 2):
                solve(ws, clock, f"p{i}", [(5, "AC")])
                clock.t += 2 * DAY
            c = calibrate.calibrate(ws, bank)
            self.assertTrue(c["enough"])
            self.assertLess(c["factor"], 1.0)                                    # 10 分 vs 預設 20 分：比預設快
            self.assertEqual(c["rows"][0]["label"], "比標示簡單")
            self.assertGreaterEqual(c["factor"], 0.5)

    def test_est_minutes(self):
        bank = {"a": {"difficulty": 3}}
        self.assertEqual(calibrate.est_minutes(bank, "a", {}, 1.0), 45)
        self.assertEqual(calibrate.est_minutes(bank, "a", {}, 0.5), 22)
        self.assertEqual(calibrate.est_minutes(bank, "a", {"a": {"effort_min": 40}}, 1.0, review=True), 24)
        self.assertEqual(calibrate.est_minutes(bank, "a", {}, 1.0, spent=100), 5)


# ---------- 每日計畫 ----------
class PlanTests(unittest.TestCase):
    def test_fresh_workspace_gets_new_unit_problems_within_budget(self):
        tmp, ws, _ = make_ws()
        with tmp:
            p = plan_mod.build(ws, 30)
            self.assertTrue(p["items"])
            self.assertTrue(all(i["kind"] == "new" for i in p["items"]))
            self.assertLessEqual(sum(i["est"] for i in p["items"] if not i["done"]), 30)
            small = plan_mod.build(ws, 10)
            self.assertLessEqual(len(small["items"]), len(p["items"]))

    def test_due_reviews_come_first(self):
        tmp, ws, clock = make_ws()
        with tmp:
            st = ws.state()
            p = st["problems"].setdefault("d001", new_problem_state())
            p.update(first_pass=clock.t - 3 * DAY, review_stage=0, review_due=clock.t - 1)
            ws.save_state(st)
            p = plan_mod.build(ws, 30)
            self.assertEqual(p["items"][0]["kind"], "review")
            self.assertEqual(p["items"][0]["id"], "d001")

    def test_oversized_first_item_is_still_offered_with_warning(self):
        tmp, ws, clock = make_ws()
        with tmp:
            st = ws.state()
            st["course"]["unit"] = 20
            ws.save_state(st)
            p = plan_mod.build(ws, 10)
            if p["items"]:
                self.assertTrue(p["items"][0]["est"] <= 10 or p["items"][0].get("over"))

    def test_active_exam_replaces_plan(self):
        tmp, ws, clock = make_ws()
        with tmp:
            ws.save_exam({"kind": "weekly", "start": clock.t, "minutes": 60, "problems": ["d001"], "files": {}, "lang": "py", "gate": None, "past": None,
                          "results": {"d001": {"wrong": 0, "ac_min": None}}})
            p = plan_mod.build(ws, 30)
            self.assertEqual([i["kind"] for i in p["items"]], ["exam"])

    def test_solved_today_is_marked_done(self):
        tmp, ws, clock = make_ws()
        with tmp:
            first = plan_mod.build(ws, 30)["items"][0]["id"]
            solve(ws, clock, first, [(3, "AC")])
            items = plan_mod.build(ws, 30)["items"]
            self.assertTrue(next(i for i in items if i["id"] == first)["done"])


# ---------- 工程任務 ----------
SOL = {
    "uva100": "print(int(input()) + 1)\n",
    "uva101": "a, b = map(int, input().split())\nprint(a * b)\n",
    "uva102": "n = int(input())\nprint(n if n >= 0 else -n)\n",
}
GOOD_TESTS = '''from solhelp import run


def test_inc():
    assert run("uva100", "4\\n") == "5\\n"
    assert run("uva100", "-1\\n") == "0\\n"


def test_mul():
    assert run("uva101", "3 4\\n") == "12\\n"
    assert run("uva101", "0 9\\n") == "0\\n"


def test_abs():
    assert run("uva102", "-7\\n") == "7\\n"
    assert run("uva102", "7\\n") == "7\\n"
    assert run("uva102", "0\\n") == "0\\n"
'''


class EngTests(unittest.TestCase):
    def setUp(self):
        self.tmp, self.ws, self.clock = make_ws()
        (self.ws.root / "solutions").mkdir(exist_ok=True)
        for pid, code in SOL.items():
            (self.ws.root / "solutions" / f"{pid}.py").write_text(code, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def labels(self, results):
        return {r["label"]: r["ok"] for r in results}

    def test_tasks_listing_and_next(self):
        ts = eng.tasks(self.ws)
        self.assertEqual([t["n"] for t in ts], list(range(1, 12)))
        self.assertEqual({t["kind"] for t in ts}, {"auto", "semi", "manual"})
        self.assertEqual(eng.next_task(self.ws, 1), None)                       # 工程任務從階段 2 開始
        self.assertEqual(eng.next_task(self.ws, 2)["n"], 1)

    def test_scaffold_is_created_once_and_never_overwrites(self):
        made = eng.start(self.ws, 3)
        self.assertEqual(sorted(made), ["eng/solhelp.py", "eng/test_solutions.py"])
        (self.ws.root / "eng" / "test_solutions.py").write_text("# mine\n", encoding="utf-8")
        self.assertEqual(eng.start(self.ws, 3), [])
        self.assertEqual((self.ws.root / "eng" / "test_solutions.py").read_text(encoding="utf-8"), "# mine\n")
        with self.assertRaises(ValueError):
            eng.start(self.ws, 99)

    def test_pytest_task_fails_on_skeleton_and_passes_on_real_tests(self):
        eng.start(self.ws, 3)
        r = eng.verify(self.ws, 3)
        self.assertFalse(r["ok"])
        self.assertNotIn(3, self.ws.state()["eng_done"])
        (self.ws.root / "eng" / "test_solutions.py").write_text(GOOD_TESTS, encoding="utf-8")
        r = eng.verify(self.ws, 3)
        self.assertTrue(r["ok"], r["results"])
        self.assertIn(3, self.ws.state()["eng_done"])
        self.assertTrue(any("抓得到錯誤" in x["label"] for x in r["results"]))

    def test_mutation_check_catches_tests_that_do_not_really_test(self):
        eng.start(self.ws, 3)
        lazy = "from solhelp import run\n\n\ndef test_a():\n    run('uva100', '1\\n')\n    assert True\n\n\ndef test_b():\n    run('uva101', '1 1\\n')\n    assert 1\n\n\n" \
               "def test_c():\n    run('uva102', '1\\n')\n    assert 2 > 1\n    assert 'uva100'\n    assert 'uva101'\n    assert 'uva102'\n"
        (self.ws.root / "eng" / "test_solutions.py").write_text(lazy, encoding="utf-8")
        r = eng.verify(self.ws, 3)
        lab = self.labels(r["results"])
        self.assertTrue(lab["測試全部通過"])
        self.assertFalse(lab["測試抓得到錯誤（把解答改壞，測試要變紅）"])
        self.assertFalse(r["ok"])
        self.assertEqual(self.ws.state()["eng_done"], [])
        self.assertEqual((self.ws.root / "solutions" / "uva100.py").read_text(encoding="utf-8"), SOL["uva100"])     # 驗收不能弄壞你的解答

    def test_failing_test_is_reported_not_marked_done(self):
        eng.start(self.ws, 3)
        (self.ws.root / "eng" / "test_solutions.py").write_text(GOOD_TESTS.replace('== "5\\n"', '== "6\\n"'), encoding="utf-8")
        r = eng.verify(self.ws, 3)
        self.assertFalse(self.labels(r["results"])["測試全部通過"])
        self.assertFalse(r["ok"])

    def test_manual_tasks_need_evidence_url(self):
        self.assertFalse(eng.verify(self.ws, 2)["ok"])
        self.assertFalse(eng.verify(self.ws, 2, "https://example.com/x")["ok"])
        self.assertFalse(eng.verify(self.ws, 2, "javascript:alert(1)")["ok"])
        self.assertTrue(eng.verify(self.ws, 2, "https://github.com/me/repo/pull/12")["ok"])
        self.assertIn(2, self.ws.state()["eng_done"])
        self.assertFalse(eng.verify(self.ws, 9, "http://insecure.example")["ok"])
        self.assertTrue(eng.verify(self.ws, 9, "https://my-app.fly.dev")["ok"])

    def test_sqlite_task(self):
        eng.start(self.ws, 6)
        self.assertFalse(eng.verify(self.ws, 6)["ok"])
        (self.ws.root / ".cpe" / "events.jsonl").write_text('{"ts":1,"kind":"test","problem":"a","verdict":"AC"}\n{"ts":2,"kind":"test","problem":"a","verdict":"WA"}\n', encoding="utf-8")
        (self.ws.root / "eng" / "progress_db.py").write_text('''import json, sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
db = ROOT / "eng" / "progress.db"
db.unlink(missing_ok=True) if hasattr(db, "unlink") else None
con = sqlite3.connect(db)
con.execute("create table events(ts, kind, problem, verdict)")
con.execute("create table problems(id, title)")
con.execute("insert into problems values ('a', 'A')")
for line in (ROOT / ".cpe" / "events.jsonl").read_text().splitlines():
    e = json.loads(line)
    con.execute("insert into events values (?,?,?,?)", (e["ts"], e["kind"], e["problem"], e["verdict"]))
con.commit()
''', encoding="utf-8")
        (self.ws.root / "eng" / "queries.sql").write_text("select verdict, count(*) from events group by verdict;\nselect p.id from events e join problems p on p.id = e.problem;\n", encoding="utf-8")
        r = eng.verify(self.ws, 6)
        self.assertTrue(r["ok"], r["results"])

    def test_stress_task(self):
        eng.start(self.ws, 4)
        self.assertFalse(eng.verify(self.ws, 4)["ok"])
        d = self.ws.root / "eng" / "stress" / "uva101"
        d.mkdir(parents=True)
        (d / "gen.py").write_text("import random, sys\nrandom.seed(int(sys.argv[1]))\nprint(random.randint(-9, 9), random.randint(-9, 9))\n", encoding="utf-8")
        (d / "brute.py").write_text("a, b = map(int, input().split())\ns = 0\nfor _ in range(abs(b)):\n    s += a\nprint(s if b >= 0 else -s)\n", encoding="utf-8")
        r = eng.verify(self.ws, 4)
        self.assertTrue(r["ok"], r["results"])
        (self.ws.root / "solutions" / "uva101.py").write_text("a, b = map(int, input().split())\nprint(a * b + (1 if a == 5 and b == 5 else 0))\n", encoding="utf-8")
        (d / "gen.py").write_text("import random, sys\nrandom.seed(int(sys.argv[1]))\nprint(random.randint(4, 6), random.randint(4, 6))\n", encoding="utf-8")
        r = eng.verify(self.ws, 4)
        self.assertFalse(r["ok"])                                               # 正解有 bug，對拍要抓到

    def test_verify_logs_events_and_cli(self):
        eng.verify(self.ws, 2)
        eng.verify(self.ws, 2, "https://github.com/a/b/pull/1")
        evs = [e for e in self.ws.events() if e["kind"] == "eng_verify"]
        self.assertEqual([e["ok"] for e in evs], [False, True])
        self.assertTrue(next(t for t in eng.tasks(self.ws) if t["n"] == 2)["done"])


class CliTests(unittest.TestCase):
    def test_plan_calibrate_eng_commands(self):
        tmp, ws, _ = make_ws()
        with tmp:
            import contextlib
            import io
            import os
            old = os.getcwd()
            os.chdir(ws.root)
            try:
                for argv, needle in ((["plan", "-m", "30"], "今天 30 分鐘"), (["calibrate"], "還沒有解出"), (["eng"], "cpe eng start N"),
                                     (["eng", "start", "3"], "eng/solhelp.py"), (["past", "list"], "2020-10-20")):
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf):
                        rc = cli.main(argv)
                    self.assertEqual(rc, 0, argv)
                    self.assertIn(needle, buf.getvalue(), argv)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    self.assertEqual(cli.main(["eng", "verify", "2"]), 1)
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main()
