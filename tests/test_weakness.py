"""主題弱點診斷：分數、收縮、建議加練、計畫整合。"""
import tempfile
import unittest
from pathlib import Path

from cpe_coach import bank as bank_mod
from cpe_coach import course, dashboard, weakness
from cpe_coach import plan as plan_mod
from cpe_coach.store import Workspace, new_problem_state

MIN = 60.0
C = course.load()


class Clock:
    def __init__(self, t=1_800_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


def make_ws():
    tmp = tempfile.TemporaryDirectory()
    clock = Clock()
    return tmp, Workspace.create(Path(tmp.name), "2026-11-01", clock), clock


def play(ws, clock, pid, verdicts, hints=0, giveup=False, review=False):
    for _ in range(hints):
        clock.t += MIN
        ws.log("hint", problem=pid, level=2, source="builtin")
    if giveup:
        clock.t += MIN
        ws.log("giveup", problem=pid)
    for v in verdicts:
        clock.t += 2 * MIN
        ws.log("test", problem=pid, verdict=v, lang="py", review_attempt=review, clean=True, advanced=False, mastered=False)
    if verdicts and verdicts[-1] == "AC":
        st = ws.state()
        st["problems"].setdefault(pid, new_problem_state())["first_pass"] = clock.t
        ws.save_state(st)


def drills(n):
    return C["units"][n - 1]["drills"]


class WeaknessTests(unittest.TestCase):
    def test_per_problem_struggle_rules(self):
        tmp, ws, clock = make_ws()
        with tmp:
            play(ws, clock, "a", ["AC"])                              # 一次過
            play(ws, clock, "b", ["WA", "WA", "AC"], hints=1)         # 失敗 2 次＋提示 1 次
            play(ws, clock, "c", ["WA"])                              # 才剛開始：不算
            play(ws, clock, "d", ["WA", "RE"])                        # 還沒過但試了 2 次：至少 0.8
            play(ws, clock, "e", ["AC"], giveup=True)
            play(ws, clock, "f", ["AC"])
            play(ws, clock, "f", ["WA"], review=True)                 # 已通過後，重練失敗
            pp = weakness.per_problem(ws.events())
            self.assertEqual(pp["a"]["struggle"], 0.0)
            self.assertTrue(pp["a"]["first_try"])
            self.assertAlmostEqual(pp["b"]["struggle"], 0.4 + 0.25)
            self.assertNotIn("c", pp)
            self.assertEqual(pp["d"]["struggle"], 0.8)
            self.assertFalse(pp["d"]["solved"])
            self.assertAlmostEqual(pp["e"]["struggle"], 0.3)
            self.assertEqual(pp["f"]["review_fail"], 1)

    def test_hints_after_first_pass_do_not_count(self):
        tmp, ws, clock = make_ws()
        with tmp:
            play(ws, clock, "a", ["AC"])
            play(ws, clock, "a", [], hints=2)
            self.assertEqual(weakness.per_problem(ws.events())["a"]["hints"], 0)

    def test_family_mapping(self):
        bank = {"uva1": {"topic": "區間 DP"}, "uva2": {"topic": "最短路徑"}, "uva3": {"topic": "字串取代模擬"}, "uva4": {"topic": "大數／字串"}, "uva5": {"topic": "？？"}}
        idx = weakness._unit_index(C)
        self.assertEqual([weakness.family_of(p, bank, idx) for p in ("uva1", "uva2", "uva3", "uva4", "uva5")], ["dp", "graph", "string", "math", "other"])
        self.assertEqual(weakness.family_of(drills(31)[0], {}, idx), "dp")        # 單元內的題以單元為準
        self.assertEqual(weakness.family_of(drills(26)[0], {}, idx), "graph")

    def test_every_drill_has_a_known_family(self):
        bank = bank_mod.load_bank(None)
        idx = weakness._unit_index(C)
        for pid, b in bank.items():
            if b.get("drill") and not b.get("reserve"):
                self.assertIn(weakness.family_of(pid, bank, idx), weakness.NAME, pid)
        fams = {weakness.family_of(pid, bank, idx) for pid in bank if bank[pid].get("drill") and not bank[pid].get("reserve")}
        self.assertGreaterEqual(len(fams), 8)

    def test_levels_shrinkage_and_flags(self):
        tmp, ws, clock = make_ws()
        with tmp:
            for pid in drills(31)[:2] + drills(32)[:1] + drills(33)[:2]:           # DP：5 題都很掙扎
                play(ws, clock, pid, ["WA", "WA", "WA", "AC"], hints=2)
            for pid in drills(1) + drills(2):                                     # 基礎：6 題一次過
                play(ws, clock, pid, ["AC"])
            play(ws, clock, drills(26)[0], ["WA", "WA"])                          # 圖論：只有 1 題 → 資料不足
            a = weakness.analyze(ws)
            lv = {r["key"]: r["level"] for r in a["families"]}
            self.assertEqual(lv["dp"], "weak")
            self.assertEqual(lv["basic"], "ok")
            self.assertEqual(lv["graph"], "unknown")                              # 不下結論
            self.assertEqual(a["weak"], ["dp"])
            self.assertEqual(a["families"][0]["key"], "dp")                       # 最弱的排最前面
            dp = a["families"][0]
            self.assertEqual((dp["n"], dp["first_try_rate"]), (5, 0.0))
            self.assertLess(dp["score"], 1.0)

    def test_no_data_is_not_a_weakness(self):
        tmp, ws, _ = make_ws()
        with tmp:
            a = weakness.analyze(ws)
            self.assertEqual((a["flagged"], a["problems_seen"], a["enough"]), ([], 0, False))
            self.assertTrue(a["note"])

    def test_candidates_only_from_reached_units_unsolved_and_not_reserved(self):
        tmp, ws, clock = make_ws()
        with tmp:
            bank = bank_mod.load_bank(ws)
            st = ws.state()
            st["course"]["unit"] = 32
            ws.save_state(st)
            c = weakness.candidates(ws, bank, C, "dp", 10)
            ids = {x["id"] for x in c}
            self.assertTrue(set(drills(31)) <= ids and set(drills(32)) <= ids)
            self.assertFalse(set(drills(33)) & ids)                              # 還沒學到的單元不出
            self.assertTrue(all(not bank[i].get("reserve") for i in ids))
            st = ws.state()
            st["problems"][drills(31)[0]] = dict(new_problem_state(), first_pass=clock.t)
            ws.save_state(st)
            self.assertNotIn(drills(31)[0], {x["id"] for x in weakness.candidates(ws, bank, C, "dp", 10)})
            self.assertEqual([x["difficulty"] for x in c], sorted(x["difficulty"] for x in c))


class PlanIntegrationTests(unittest.TestCase):
    def setup_weak_dp(self, ws, clock, unit=35):
        st = ws.state()
        st["course"]["unit"] = unit
        ws.save_state(st)
        for pid in drills(31) + drills(32):
            play(ws, clock, pid, ["WA", "WA", "WA", "AC"], hints=2)
        for pid in drills(1) + drills(2) + drills(3):
            play(ws, clock, pid, ["AC"])

    def test_plan_adds_weak_practice_and_labels_why(self):
        tmp, ws, clock = make_ws()
        with tmp:
            self.setup_weak_dp(ws, clock)
            p = plan_mod.build(ws, 90)
            weak = [i for i in p["items"] if i["kind"] == "weak"]
            self.assertTrue(weak)
            self.assertIn("動態規劃", weak[0]["why"])
            ids = [i["id"] for i in p["items"] if i["id"]]
            self.assertEqual(len(ids), len(set(ids)))                            # 同一題不會重複出現

    def test_no_weak_items_without_enough_data(self):
        tmp, ws, clock = make_ws()
        with tmp:
            play(ws, clock, drills(31)[0], ["WA", "WA", "AC"], hints=2)
            self.assertFalse([i for i in plan_mod.build(ws, 90)["items"] if i["kind"] == "weak"])

    def test_unit_49_detail_carries_weakness_and_suggestions(self):
        tmp, ws, clock = make_ws()
        with tmp:
            self.setup_weak_dp(ws, clock, unit=49)
            d = dashboard.unit_detail(ws, bank_mod.load_bank(ws), C, 49)
            self.assertEqual(d["weak"]["weak"], ["dp"])
            self.assertTrue(d["weak"]["suggestions"])
            self.assertIsNone(dashboard.unit_detail(ws, bank_mod.load_bank(ws), C, 48)["weak"])
            p = plan_mod.build(ws, 120)
            self.assertGreaterEqual(len([i for i in p["items"] if i["kind"] == "weak"]), 2)


if __name__ == "__main__":
    unittest.main()
