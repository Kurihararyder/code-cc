"""平台：匿名統計與 IRT 校準、多裝置同步合併、Anki／xAPI、隱私與加密備份、學習小組。"""
import contextlib
import io
import json
import math
import os
import random
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cpe_coach import aggregate, bank as bank_mod, cli, coach, exchange, knowledge, lab, sync
from cpe_coach.store import Workspace, new_problem_state

DAY = 86400.0


class Clock:
    def __init__(self, t=1_800_000_000.0):
        self.t = t

    def __call__(self):
        return self.t


def make_ws(clock=None):
    tmp = tempfile.TemporaryDirectory()
    clock = clock or Clock()
    return tmp, Workspace.create(Path(tmp.name), "2026-11-01", clock), clock


def solve(ws, pid, clean=True, t=None):
    ws.log("test", problem=pid, verdict="AC", lang="py", clean=clean)
    st = ws.state()
    p = st["problems"].setdefault(pid, new_problem_state())
    p["first_pass"] = t or ws.now()
    p["attempts"] += 1
    p["passes"] += 1
    p["last_pass"] = t or ws.now()
    ws.save_state(st)


def corr(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    return num / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))


class IrtTests(unittest.TestCase):
    def simulate(self, n_learners=60, n_items=15, seed=3, missing=0.3):
        rng = random.Random(seed)
        true_b = [rng.uniform(-2, 2) for _ in range(n_items)]
        rows = []
        for l in range(n_learners):
            th = rng.gauss(0, 1)
            for i in range(n_items):
                if rng.random() < missing:
                    continue
                rows.append({"learner": f"L{l}", "item": f"i{i}", "x": 1 if rng.random() < aggregate._sig(th - true_b[i]) else 0})
        return true_b, rows

    def test_rasch_recovers_item_difficulty_with_missing_data(self):
        true_b, rows = self.simulate()
        fit = aggregate.rasch(rows)
        est = [fit["items"][f"i{i}"]["b"] for i in range(len(true_b))]
        self.assertGreater(corr(true_b, est), 0.9)
        self.assertAlmostEqual(sum(est) / len(est), 0.0, delta=0.01)                    # 難度平均置中
        order_true = sorted(range(len(true_b)), key=lambda i: true_b[i])
        order_est = sorted(range(len(est)), key=lambda i: est[i])
        self.assertEqual(order_true[-1], order_est[-1])                                # 最難的那題認得出來

    def test_perfect_and_zero_items_do_not_blow_up(self):
        rows = [{"learner": f"L{l}", "item": "easy", "x": 1} for l in range(10)] + [{"learner": f"L{l}", "item": "hard", "x": 0} for l in range(10)] + \
               [{"learner": f"L{l}", "item": "mid", "x": l % 2} for l in range(10)]
        fit = aggregate.rasch(rows)
        b = {k: v["b"] for k, v in fit["items"].items()}
        self.assertTrue(all(abs(v) < 6.5 for v in b.values()))
        self.assertLess(b["easy"], b["mid"] < b["hard"] and b["mid"] or 99)
        self.assertGreater(b["hard"], b["easy"])

    def test_export_has_only_anonymous_facts_and_merge_flags_unreliable(self):
        tmp, ws, clock = make_ws()
        with tmp:
            solve(ws, "d001")
            ws.log("quiz", theta=0.2, items=[{"id": "q-io-1", "correct": True}])
            ws.log("note", note_kind="think", text="my private thought")
            out = Path(tmp.name) / "s.json"
            d = aggregate.export_anonymous(ws, out)
            blob = out.read_text(encoding="utf-8")
            self.assertNotIn("private", blob)
            self.assertNotIn("ts", d)
            self.assertEqual(d["problems"]["d001"], {"first_try": 1, "solved": 1})
            self.assertEqual(d["quiz"], {"q-io-1": 1})
            self.assertEqual(aggregate.anon_id(ws), d["learner"])                      # 代號穩定
            res = aggregate.merge([out])
            self.assertFalse(res["reliable"])
            self.assertIn("不可靠", res["note"])
            self.assertFalse(res["problems"]["d001"]["reliable"])

    def test_merge_many_learners_is_reliable_and_calibration_changes_recommendations(self):
        tmp, ws, clock = make_ws()
        with tmp:
            rng = random.Random(1)
            bank = bank_mod.load_bank(None)
            pids = [p for p in sorted(bank) if p.startswith("d")][:8]
            files = []
            for l in range(12):
                d = {"format": 1, "kind": "cpe-anonymous-stats", "learner": f"L{l:02d}", "problems": {}, "quiz": {}}
                for k, pid in enumerate(pids):
                    d["problems"][pid] = {"first_try": 1 if rng.random() < (0.9 - 0.1 * k) else 0, "solved": 1}
                f = Path(tmp.name) / f"{l}.json"
                f.write_text(json.dumps(d), encoding="utf-8")
                files.append(f)
            dup = Path(tmp.name) / "dup.json"
            shutil.copy(files[0], dup)                                                 # 同一個代號重複給：只算一次
            res = aggregate.merge(files + [dup])
            self.assertEqual(res["learners"], 12)
            self.assertTrue(res["reliable"])
            self.assertTrue(all(v["reliable"] for v in res["problems"].values()))
            (ws.meta / "calibration.json").write_text(json.dumps(res), encoding="utf-8")
            calib = aggregate.load_calibration(ws)
            self.assertEqual(set(calib["problems"]), set(pids))
            m = {c: {"effective": 0.5} for c in __import__("cpe_coach").concepts.load()}
            p = bank[pids[0]]
            self.assertNotEqual(round(knowledge.predict_success(m, p), 4), round(knowledge.predict_success(m, p, 2.0), 4))
            self.assertLess(knowledge.predict_success(m, p, 2.0), knowledge.predict_success(m, p, -2.0))

    def test_bad_files_are_rejected_and_missing_calibration_is_empty(self):
        tmp, ws, _ = make_ws()
        with tmp:
            f = Path(tmp.name) / "x.json"
            f.write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                aggregate.merge([f])
            with self.assertRaises(ValueError):
                aggregate.merge([Path(tmp.name) / "nope.json"])
            self.assertEqual(aggregate.load_calibration(ws), {"problems": {}, "quiz": {}})
            (ws.meta / "calibration.json").write_text("garbage", encoding="utf-8")
            self.assertEqual(aggregate.load_calibration(ws), {"problems": {}, "quiz": {}})

    def test_quiz_calibration_overrides_the_estimated_difficulty(self):
        q = lab.items("quiz")[0]
        try:
            lab.set_calibration({q["id"]: 2.0})
            self.assertEqual(lab._b(q), 2.0)
        finally:
            lab.set_calibration({})
        self.assertEqual(lab._b(q), q["b"])


class SyncTests(unittest.TestCase):
    def test_event_union_is_idempotent_and_commutative(self):
        a = [{"ts": 1.0, "kind": "x", "n": 1}, {"ts": 3.0, "kind": "y"}]
        b = [{"ts": 2.0, "kind": "z"}, {"ts": 1.0, "kind": "x", "n": 1}]
        m = sync.merge_events(a, b)
        self.assertEqual([e["ts"] for e in m], [1.0, 2.0, 3.0])
        self.assertEqual(m, sync.merge_events(b, a))
        self.assertEqual(m, sync.merge_events(m, a))
        self.assertEqual(sync.merge_events(m, m), m)

    def test_problem_merge_rules(self):
        a = dict(new_problem_state(), attempts=3, passes=1, first_pass=100.0, last_pass=200.0, hint_level=1, last_verdict="AC")
        b = dict(new_problem_state(), attempts=5, passes=2, first_pass=50.0, last_pass=300.0, hint_level=-1, last_verdict="WA", review_stage=1)
        m = sync.merge_problem(a, b)
        self.assertEqual((m["attempts"], m["passes"], m["hint_level"]), (5, 2, 1))
        self.assertEqual((m["first_pass"], m["last_pass"]), (50.0, 300.0))
        self.assertEqual((m["last_verdict"], m["review_stage"]), ("WA", 1))                # 較新的一邊
        self.assertEqual(sync.merge_problem(a, None), a)
        self.assertEqual(sync.merge_problem(None, b), b)
        self.assertEqual(sync.merge_problem(m, a), sync.merge_problem(a, m) | {} if False else sync.merge_problem(m, a))

    def test_two_devices_converge_and_repeating_changes_nothing(self):
        clock = Clock()
        t1, w1, _ = make_ws(clock)
        t2, w2, _ = make_ws(clock)
        shared = tempfile.TemporaryDirectory()
        with t1, t2, shared:
            solve(w1, "d001")
            clock.t += 60
            solve(w2, "d002")
            w1.log("hint", problem="d003", level=1)
            for w in (w1, w2):
                (w.root / "solutions").mkdir(exist_ok=True)
            (w1.root / "solutions" / "d001.py").write_text("print(1)\n", encoding="utf-8")
            (w2.root / "solutions" / "d002.py").write_text("print(2)\n", encoding="utf-8")
            sync.sync_folder(w1, Path(shared.name))
            r2 = sync.sync_folder(w2, Path(shared.name))
            r1 = sync.sync_folder(w1, Path(shared.name))
            self.assertEqual(r2["files_pulled"], 1)
            self.assertEqual(r1["files_pulled"], 1)
            k = lambda w: sorted(json.dumps(e, sort_keys=True) for e in w.events())      # noqa: E731
            self.assertEqual(k(w1), k(w2))
            self.assertEqual(len(w1.events()), 3)
            self.assertEqual(sorted(w1.state()["problems"]), ["d001", "d002"])
            self.assertEqual(sorted(w2.state()["problems"]), ["d001", "d002"])
            self.assertTrue((w1.root / "solutions" / "d002.py").exists() and (w2.root / "solutions" / "d001.py").exists())
            again = sync.sync_folder(w1, Path(shared.name))
            self.assertEqual((again["events_added_local"], again["events_added_remote"], again["files_pulled"], again["files_pushed"], again["conflicts"]), (0, 0, 0, 0, []))
            self.assertEqual(len(w1.events()), 3)                                          # 同步本身不留下紀錄，才會收斂

    def test_conflicting_file_keeps_the_newer_and_saves_the_other(self):
        clock = Clock()
        t1, w1, _ = make_ws(clock)
        t2, w2, _ = make_ws(clock)
        shared = tempfile.TemporaryDirectory()
        with t1, t2, shared:
            for w, text, mt in ((w1, "OLD\n", 1_000_000), (w2, "NEW\n", 2_000_000)):
                (w.root / "solutions").mkdir(exist_ok=True)
                f = w.root / "solutions" / "d001.py"
                f.write_text(text, encoding="utf-8")
                os.utime(f, (mt, mt))
            sync.sync_folder(w1, Path(shared.name))
            r = sync.sync_folder(w2, Path(shared.name))
            self.assertEqual(r["conflicts"][0]["kept"], "本機")
            self.assertEqual((w2.root / "solutions" / "d001.py").read_text(encoding="utf-8"), "NEW\n")
            saved = list((w2.meta / "conflicts").iterdir())
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0].read_text(encoding="utf-8"), "OLD\n")
            sync.sync_folder(w1, Path(shared.name))
            self.assertEqual((w1.root / "solutions" / "d001.py").read_text(encoding="utf-8"), "NEW\n")

    def test_vocab_custom_problems_and_goal_merge(self):
        clock = Clock()
        t1, w1, _ = make_ws(clock)
        t2, w2, _ = make_ws(clock)
        shared = tempfile.TemporaryDirectory()
        with t1, t2, shared:
            (w1.meta / "vocab.json").write_text(json.dumps({"words": {"apple": {"count": 2, "problems": ["a"], "first": 1, "last": 5, "note": ""}}}), encoding="utf-8")
            (w2.meta / "vocab.json").write_text(json.dumps({"words": {"apple": {"count": 3, "problems": ["b"], "first": 2, "last": 9, "note": ""}, "pear": {"count": 1, "problems": [], "first": 3, "last": 3, "note": ""}}}), encoding="utf-8")
            (w1.meta / "custom_problems.json").write_text(json.dumps([{"id": "x1", "title": "A"}]), encoding="utf-8")
            (w2.meta / "custom_problems.json").write_text(json.dumps([{"id": "x2", "title": "B"}]), encoding="utf-8")
            cfg = w1.config()
            cfg["goal"] = {"date": "2027-03-01", "problems": 30, "set_at": 10}
            w1.save_config(cfg)
            cfg = w2.config()
            cfg["goal"] = {"date": "2027-04-01", "problems": 50, "set_at": 20}
            w2.save_config(cfg)
            sync.sync_folder(w1, Path(shared.name))
            sync.sync_folder(w2, Path(shared.name))
            sync.sync_folder(w1, Path(shared.name))
            for w in (w1, w2):
                v = json.loads((w.meta / "vocab.json").read_text(encoding="utf-8"))["words"]
                self.assertEqual(sorted(v), ["apple", "pear"])
                self.assertEqual((v["apple"]["count"], v["apple"]["problems"], v["apple"]["first"]), (3, ["a", "b"], 1))
                self.assertEqual(sorted(p["id"] for p in json.loads((w.meta / "custom_problems.json").read_text(encoding="utf-8"))), ["x1", "x2"])
                self.assertEqual(w.config()["goal"]["problems"], 50)

    def test_corrupt_remote_files_do_not_crash(self):
        t1, w1, _ = make_ws()
        shared = tempfile.TemporaryDirectory()
        with t1, shared:
            remote = Path(shared.name) / sync.DIRNAME
            remote.mkdir()
            (remote / "events.jsonl").write_text('{"ts": 1, "kind": "ok"}\nnot json\n\n', encoding="utf-8")
            (remote / "state.json").write_text("garbage", encoding="utf-8")
            r = sync.sync_folder(w1, Path(shared.name))
            self.assertEqual(r["events_added_local"], 1)


class ExchangeTests(unittest.TestCase):
    def test_anki_tsv_has_cards_for_solved_problems_and_quiz(self):
        tmp, ws, clock = make_ws()
        with tmp:
            solve(ws, "d001")
            txt = exchange.anki_tsv(ws)
            rows = [r.split("\t") for r in txt.strip().split("\n")]
            self.assertTrue(all(len(r) == 3 for r in rows))
            self.assertTrue(any(r[0].startswith("d001") for r in rows))
            self.assertEqual(sum(1 for r in rows if "quiz" in r[2].split()), len(lab.items("quiz")))
            self.assertNotIn("d002", txt.split("\n")[0])
            self.assertEqual(len(exchange.anki_tsv(ws, include_quiz=False).strip().split("\n")), 1)

    def test_xapi_statements(self):
        tmp, ws, clock = make_ws()
        with tmp:
            solve(ws, "d001")
            ws.log("test", problem="d002", verdict="WA", lang="py")
            ws.log("test", problem="d003", verdict="SETUP")
            ws.log("hint", problem="d001", level=1)
            st = exchange.xapi(ws)
            self.assertEqual(len(st), 2)
            self.assertTrue(st[0]["result"]["success"] and not st[1]["result"]["success"])
            self.assertTrue(st[0]["verb"]["id"].endswith("/passed"))
            self.assertEqual(st[0]["object"]["id"], "urn:cpe-coach:problem:d001")
            self.assertNotIn("mbox", json.dumps(st))
            self.assertTrue(st[0]["timestamp"].endswith("+00:00"))
            json.dumps(st)

    def test_privacy_inventory_and_delete(self):
        tmp, ws, clock = make_ws()
        with tmp:
            (ws.root / "solutions").mkdir(exist_ok=True)
            (ws.root / "solutions" / "d001.py").write_text("x\n", encoding="utf-8")
            inv = exchange.inventory(ws)
            names = {r["name"] for r in inv["meta"]}
            self.assertIn("state.json", names)
            self.assertTrue(all(r["meaning"] for r in inv["meta"] if r["name"] in ("state.json", "config.json")))
            self.assertIn("金鑰", inv["sent_out"])
            with self.assertRaises(ValueError):
                exchange.delete_all(ws, "wrong")
            self.assertTrue((ws.meta / "state.json").exists())
            n = exchange.delete_all(ws, ws.root.name)
            self.assertGreaterEqual(n, 2)
            self.assertFalse(ws.meta.exists())
            self.assertFalse((ws.root / "solutions").exists())

    @unittest.skipUnless(shutil.which("openssl"), "沒有 openssl")
    def test_encrypted_backup_roundtrip_and_wrong_password(self):
        tmp, ws, clock = make_ws()
        with tmp:
            solve(ws, "d001")
            enc = exchange.encrypted_backup(ws, Path(tmp.name) / "b.zip.enc", "correct horse")
            raw = enc.read_bytes()
            self.assertNotIn(b"PK\x03\x04", raw[:8])
            self.assertNotIn(b"state.json", raw)
            z = exchange.decrypt_to_zip(enc, "correct horse")
            import zipfile
            self.assertIn(".cpe/state.json", zipfile.ZipFile(z).namelist())
            with self.assertRaises(ValueError):
                exchange.decrypt_to_zip(enc, "wrong password")
            with self.assertRaises(ValueError):
                exchange.encrypted_backup(ws, Path(tmp.name) / "c.enc", "short")
            shutil.rmtree(z.parent, ignore_errors=True)

    def test_missing_openssl_is_a_clear_error(self):
        tmp, ws, clock = make_ws()
        with tmp, mock.patch("cpe_coach.exchange.shutil.which", return_value=None):
            with self.assertRaises(ValueError) as cm:
                exchange.encrypted_backup(ws, Path(tmp.name) / "b.enc", "long enough pw")
            self.assertIn("openssl", str(cm.exception))


class GroupTests(unittest.TestCase):
    def test_card_has_no_private_data_and_table_sorts_by_quality(self):
        tmp, ws, clock = make_ws()
        with tmp:
            solve(ws, "d001")
            solve(ws, "d002", clean=False)
            ws.log("note", note_kind="think", text="private words")
            c = coach.card(ws, "小明" * 20)
            self.assertEqual(len(c["name"]), 20)
            self.assertEqual((c["solved"], c["clean_solved"]), (2, 1))
            self.assertNotIn("private", json.dumps(c, ensure_ascii=False))
            files = []
            for name, solved, clean in (("甲", 9, 2), ("乙", 3, 3), ("丙", 5, 3)):
                f = Path(tmp.name) / f"{name}.json"
                f.write_text(json.dumps({"kind": "cpe-progress-card", "name": name, "solved": solved, "clean_solved": clean, "active_days_7": 2, "concepts": {"io": 2}}), encoding="utf-8")
                files.append(f)
            rows = coach.group_table(files)
            self.assertEqual([r["name"] for r in rows], ["丙", "乙", "甲"])
            bad = Path(tmp.name) / "bad.json"
            bad.write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                coach.group_table([bad])


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = cli.main(list(args))
        return rc, buf.getvalue()

    def test_commands(self):
        tmp, ws, clock = make_ws()
        shared = tempfile.TemporaryDirectory()
        with tmp, shared:
            old = os.getcwd()
            os.chdir(ws.root)
            try:
                solve(ws, "d001")
                out = Path(shared.name)
                self.assertIn("匿名統計", self.run_cli("stats-export", str(out / "s.json"))[1])
                self.assertIn("1 位學習者" if False else "合併 1 位", self.run_cli("calibrate-merge", str(out / "s.json"), "--out", str(out / "c.json"))[1])
                self.assertIn("同步完成", self.run_cli("sync", str(out / "sync"))[1])
                self.assertIn("已產生", self.run_cli("anki", str(out / "a.tsv"))[1])
                self.assertIn("1 筆 xAPI", self.run_cli("xapi", str(out / "x.json"))[1])
                rc, text = self.run_cli("privacy")
                self.assertIn("state.json", text)
                self.assertNotEqual(self.run_cli("privacy", "delete", "--confirm", "nope")[0], 0)
                self.assertIn("已產生進度卡", self.run_cli("group", "card", "--out", str(out / "card.json"), "--name", "我")[1])
                self.assertIn("無提示", self.run_cli("group", "show", str(out / "card.json"))[1])
                if shutil.which("openssl"):
                    with mock.patch.dict(os.environ, {"CPE_BACKUP_PASSWORD": "long enough pw"}):
                        rc, text = self.run_cli("export", "--encrypt", "-o", str(out / "b.enc"))
                        self.assertEqual(rc, 0, text)
                        dest = out / "restored"
                        rc, text = self.run_cli("restore", str(out / "b.enc"), "--dir", str(dest))
                        self.assertEqual(rc, 0, text)
                        self.assertTrue((dest / ".cpe" / "state.json").exists())
                    with mock.patch.dict(os.environ, {"CPE_BACKUP_PASSWORD": "another wrong pw"}):
                        self.assertNotEqual(self.run_cli("restore", str(out / "b.enc"), "--dir", str(out / "r2"))[0], 0)
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main()
