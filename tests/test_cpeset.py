"""CPE 原題：題目文字整理（uvastatement）、清單與題庫整合（cpeset）、匯入（cpeimport）、命令列與網頁。
用 tests/pdfmaker.py 自己產生的 PDF 當資料；真的題目 PDF 有版權，不放進專案。可選的真實資料驗證在 test_cpe_real.py。"""
import contextlib
import io
import json
import os
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
import pdfmaker  # noqa: E402

from cpe_coach import bank as bank_mod
from cpe_coach import cli, cpeimport, cpeset, dashboard, pastexams, pdftext, service, uvastatement, web
from cpe_coach import course as course_mod
from cpe_coach import plan as plan_mod
from cpe_coach.store import Workspace

BODY = ("Given a list of words and a grid of letters, find every word in the grid in all eight directions. "
        "The search is case-insensitive, and a word that is split across two lines with a hyphen must be joined back correctly.")


def uva_pdf(n, title="Test Title", **kw):
    return pdfmaker.make_uva_pdf(n, title, BODY, "The first line has the number of cases T (1 <= T <= 20).", "Print one line for each case.",
                                 "2\n1 2\n3 4", "3\n7", **kw)


def make_repo(folder: Path, layout):
    """layout: {"一星題": [10008, ...], ...} → folder/一星題/10008/10008.pdf（和真的 repo 一樣的結構）。"""
    for d, nums in layout.items():
        for n in nums:
            p = folder / d / str(n)
            p.mkdir(parents=True, exist_ok=True)
            (p / f"{n}.pdf").write_bytes(uva_pdf(n, f"Title {n}"))
            (p / "solution.py").write_text("raise SystemExit('never run')\n")        # 別人的解答：匯入絕不能去碰


def make_zip(layout, extra=None) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for d, nums in layout.items():
            for n in nums:
                z.writestr(f"CPE_Previous_Questions-abc/{d}/{n}/{n}.pdf", uva_pdf(n, f"Title {n}"))
        for name, data in (extra or {}).items():
            z.writestr(name, data)
    return buf.getvalue()


class StatementTests(unittest.TestCase):
    def test_title_footer_headings_and_samples(self):
        st = uvastatement.from_pdf(uva_pdf(10010, "Where's Waldorf?"))
        self.assertEqual((st.number, st.title), (10010, "Where's Waldorf?"))
        self.assertNotIn("Universidad", st.text)
        for h in ("Input", "Output", "Sample Input", "Sample Output"):
            self.assertIn(f"\n{h}\n", st.text)
        self.assertEqual(service.parse_samples(st.text), [("2\n1 2\n3 4", "3\n7")])

    def test_prose_is_reflowed_into_one_line_per_paragraph(self):
        st = uvastatement.from_pdf(uva_pdf(1))
        self.assertIn(BODY, st.text.replace("  ", " "))

    def test_sample_split_across_a_page_break_stays_one_block(self):
        for per in (7, 9, 11):
            with self.subTest(lines_per_page=per):
                st = uvastatement.from_pdf(uva_pdf(5, lines_per_page=per))
                self.assertNotIn("Universidad", st.text)
                self.assertEqual(service.parse_samples(st.text), [("2\n1 2\n3 4", "3\n7")])

    def test_objstm_and_plain_structure_give_the_same_text(self):
        self.assertEqual(uvastatement.from_pdf(uva_pdf(7, objstm=True)).text, uvastatement.from_pdf(uva_pdf(7, objstm=False)).text)

    def test_missing_glyph_placeholder_becomes_a_dash(self):
        pages = pdftext.extract_pages(uva_pdf(3))
        pages[0][3].text = "range 1￿5"
        self.assertIn("range 1–5", uvastatement.build(pages).text)

    def test_hyphenated_word_at_line_end_is_joined_without_a_space(self):
        mk = pdftext.Line
        pages = [[mk("7 Hyphens", False, 700, 0, 17), mk("some compo-", False, 680, 0, 10.9), mk("sition here", False, 666, 0, 10.9)]]
        self.assertIn("some compo-sition here", uvastatement.build(pages).text)


class SetDataTests(unittest.TestCase):
    def test_set_sizes_and_overlaps(self):
        sizes = {k: len(cpeset.set_numbers(k)) for k in cpeset.SET_KEYS}
        self.assertEqual(sizes, {"one": 49, "two": 15, "past": 31})
        m = cpeset.membership()
        self.assertEqual(len(m), 91)
        self.assertEqual(sorted(n for n, k in m.items() if len(k) > 1), [10189, 10268, 11349, 11417])

    def test_data_has_titles_and_no_statement_text(self):
        data = cpeset.load()
        for key in cpeset.SET_KEYS:
            for p in data["sets"][key]["problems"]:
                self.assertTrue(p["title"])
                self.assertLessEqual(set(p), {"uva", "title", "no_pdf", "title_unknown", "sha256"})
        self.assertLess(len(cpeset.DATA.read_bytes()), 40_000)                       # 只有題號與標題

    def test_bank_merge_keeps_existing_entries_and_adds_the_rest(self):
        with tempfile.TemporaryDirectory() as d:
            ws = Workspace.create(Path(d), "2026-11-01")
            bank = bank_mod.load_bank(ws)
            self.assertTrue(all(f"uva{n}" in bank for n in cpeset.membership()))
            e = bank["uva10008"]
            self.assertIn("one", e["cpe_sets"])
            self.assertTrue(e["official_one_star"])
            self.assertEqual(e["source"], "UVA")
            plain = bank_mod.load_bank(Workspace.create(Path(d) / "x", "2026-11-01"))
            self.assertEqual(len(plain), len(bank))

    def test_unit_pools(self):
        with tempfile.TemporaryDirectory() as d:
            ws = Workspace.create(Path(d), "2026-11-01")
            bank = bank_mod.load_bank(ws)
            sizes = {n: len(cpeset.unit_pool(ws, bank, n)["items"]) for n in cpeset.UNIT_SETS}
            self.assertEqual(sizes, {15: 25, 16: 24, 25: 15, 48: 31, 51: 31})
            self.assertIsNone(cpeset.unit_pool(ws, bank, 3))
            a, b = ({i["id"] for i in cpeset.unit_pool(ws, bank, n)["items"]} for n in (15, 16))
            self.assertFalse(a & b)
            detail = dashboard.unit_detail(ws, bank, course_mod.load(), 15)
            self.assertEqual(len(detail["cpe_pool"]["items"]), 25)


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ws = Workspace.create(Path(self.tmp.name) / "ws", "2026-11-01")
        self.layout = {"一星題": [10008, 10010], "二星題": [10004], "歷屆試題": [10189, 255]}

    def test_import_from_folder_writes_statement_tests_and_pdf(self):
        repo = Path(self.tmp.name) / "repo"
        make_repo(repo, self.layout)
        msgs = []
        r = cpeimport.import_from(self.ws, str(repo), progress=lambda pid, m: msgs.append(pid))
        self.assertEqual(sorted(p for p, _, _ in r.imported), ["uva10004", "uva10008", "uva10010", "uva10189", "uva255"])
        self.assertEqual(len(msgs), 5)
        self.assertEqual(r.failed, [])
        self.assertIn("uva11332", r.missing)
        self.assertTrue((self.ws.root / "statements" / "uva10008.txt").exists())
        self.assertTrue((self.ws.root / "statements" / "uva10008.pdf").read_bytes().startswith(b"%PDF"))
        self.assertTrue(pastexams.has_tests(self.ws, "uva10008"))
        self.assertEqual((self.ws.root / "tests" / "uva10008" / "sample01.out").read_text().split(), ["3", "7"])

    def test_second_run_skips_and_force_redoes(self):
        repo = Path(self.tmp.name) / "repo"
        make_repo(repo, self.layout)
        cpeimport.import_from(self.ws, str(repo))
        again = cpeimport.import_from(self.ws, str(repo))
        self.assertEqual((len(again.imported), len(again.skipped)), (0, 5))
        (self.ws.root / "statements" / "uva10008.txt").write_text("edited")
        forced = cpeimport.import_from(self.ws, str(repo), force=True)
        self.assertEqual(len(forced.imported), 5)
        self.assertNotEqual((self.ws.root / "statements" / "uva10008.txt").read_text(), "edited")

    def test_import_from_zip_file_and_unrelated_entries_ignored(self):
        blob = make_zip(self.layout, {"x/../../evil.pdf": b"%PDF", "/abs/10008.pdf": b"%PDF", "x/readme.md": b"hi", "x/notes.pdf": b"%PDF", "x/一星題/1/1.txt": b"t"})
        found = cpeimport.scan_zip(blob)
        self.assertEqual(sorted(f.number for f in found), [255, 10004, 10008, 10010, 10189])
        zp = Path(self.tmp.name) / "q.zip"
        zp.write_bytes(blob)
        r = cpeimport.import_from(self.ws, str(zp))
        self.assertEqual(len(r.imported), 5)
        self.assertFalse((Path(self.tmp.name) / "evil.pdf").exists())

    def test_corrupt_pdf_is_reported_and_the_rest_continue(self):
        blob = make_zip({"一星題": [10008]}, {"R/一星題/10010/10010.pdf": b"%PDF-1.5 garbage"})
        r = cpeimport.import_found(self.ws, cpeimport.scan_zip(blob))
        self.assertEqual([p for p, _, _ in r.imported], ["uva10008"])
        self.assertEqual([p for p, _ in r.failed], ["uva10010"])
        self.assertFalse((self.ws.root / "statements" / "uva10010.txt").exists())

    def test_bad_sources_have_clear_errors(self):
        for src, word in ((str(Path(self.tmp.name) / "missing"), "找不到"), ):
            with self.assertRaises(cpeimport.CpeImportError) as cm:
                cpeimport.import_from(self.ws, src)
            self.assertIn(word, str(cm.exception))
        empty = Path(self.tmp.name) / "empty"
        empty.mkdir()
        with self.assertRaises(cpeimport.CpeImportError) as cm:
            cpeimport.import_from(self.ws, str(empty))
        self.assertIn("沒有找到", str(cm.exception))
        with self.assertRaises(cpeimport.CpeImportError):
            cpeimport.scan_zip(b"not a zip")

    def test_oversize_files_are_ignored(self):
        old = cpeimport.MAX_PDF
        cpeimport.MAX_PDF = 100
        try:
            self.assertEqual(cpeimport.scan_zip(make_zip({"一星題": [10008]})), [])
        finally:
            cpeimport.MAX_PDF = old

    def test_download_from_local_server_and_unreachable_message(self):
        blob = make_zip(self.layout)
        from http.server import BaseHTTPRequestHandler

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Length", str(len(blob)))
                self.end_headers()
                self.wfile.write(blob)

            def log_message(self, *a):
                pass
        httpd = web.LocalServer(("127.0.0.1", 0), H)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        old = os.environ.get("CPE_QUESTIONS_URL")
        os.environ["CPE_QUESTIONS_URL"] = f"http://127.0.0.1:{httpd.server_address[1]}/a.zip"
        try:
            r = cpeimport.import_from(self.ws)
            self.assertEqual(len(r.imported), 5)
            s = socket.socket()
            s.bind(("127.0.0.1", 0))
            dead = s.getsockname()[1]
            s.close()
            os.environ["CPE_QUESTIONS_URL"] = f"http://127.0.0.1:{dead}/a.zip"
            with self.assertRaises(cpeimport.CpeImportError) as cm:
                cpeimport.download(timeout=3, retries=0)
            self.assertIn("連不上 GitHub", str(cm.exception))
        finally:
            if old is None:
                os.environ.pop("CPE_QUESTIONS_URL", None)
            else:
                os.environ["CPE_QUESTIONS_URL"] = old

    def test_imported_problem_is_practicable_and_enters_the_plan(self):
        repo = Path(self.tmp.name) / "repo"
        make_repo(repo, self.layout)
        cpeimport.import_from(self.ws, str(repo))
        bank = bank_mod.load_bank(self.ws)
        self.assertTrue(cpeset.status(self.ws, bank)["ready"] >= 5)
        pool = cpeset.unit_pool(self.ws, bank, 15)
        self.assertGreaterEqual(pool["ready"], 2)
        p = plan_mod.build(self.ws, 120)
        self.assertTrue(p["items"])


class CliWebTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "ws"
        self.ws = Workspace.create(self.root, "2026-11-01")
        self.repo = Path(self.tmp.name) / "repo"
        make_repo(self.repo, {"一星題": [10008], "歷屆試題": [255]})
        self.old = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.old)

    def run_cli(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rc = cli.main(list(args))
        return rc, buf.getvalue()

    def test_past_repo_sets_and_statement(self):
        rc, out = self.run_cli("past", "repo", str(self.repo))
        self.assertEqual(rc, 0, out)
        self.assertIn("匯入 2 題", out)
        self.assertIn("清單裡有、但這份資料沒有 PDF", out)
        rc, out = self.run_cli("past", "sets")
        self.assertEqual(rc, 0)
        self.assertIn("一星題（49 題", out)
        self.assertIn("[ TS] uva10008", out)
        rc, out = self.run_cli("past", "repo", str(self.repo))
        self.assertIn("略過已匯入的 2 題", out)
        rc, out = self.run_cli("past", "repo", str(self.repo), "--force")
        self.assertIn("匯入 2 題", out)
        rc, out = self.run_cli("statement", "uva10008")
        self.assertEqual(rc, 0)
        self.assertIn("Title 10008", out)
        rc, out = self.run_cli("past", "repo", str(self.root / "nope"))
        self.assertNotEqual(rc, 0)
        self.assertIn("找不到", out)

    def test_sets_shows_tags_and_tip_after_a_sample_only_pass(self):
        self.run_cli("past", "repo", str(self.repo))
        rc, out = self.run_cli("past", "sets")
        self.assertIn("What's Cryptanalysis?　字串・計數・排序", out)
        self.assertEqual(self.run_cli("new", "uva10008")[0], 0)
        sol = next((self.root / "solutions").glob("uva10008.*")) if (self.root / "solutions").exists() else next(self.root.glob("uva10008.py"))
        sol.write_text("n = int(input())\nfor _ in range(n):\n    print(sum(map(int, input().split())))\n", encoding="utf-8")
        rc, out = self.run_cli("test", "uva10008")
        self.assertEqual(rc, 0, out)
        self.assertIn("通過範例不代表答案正確", out)
        self.assertIn("cpe fuzz uva10008 --brute brute.py --save", out)

    def test_statements_command_accepts_pdf_files(self):
        folder = Path(self.tmp.name) / "pdfs"
        folder.mkdir()
        (folder / "uva10010.pdf").write_bytes(uva_pdf(10010, "Where"))
        rc, out = self.run_cli("past", "statements", str(folder))
        self.assertEqual(rc, 0, out)
        self.assertTrue((self.root / "tests" / "uva10010" / "sample01.in").exists())

    def test_web_endpoints(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        app = web.App(self.root, port)
        httpd = web.LocalServer(("127.0.0.1", port), web.make_handler(app))
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)

        def req(path, body=None):
            r = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=None if body is None else json.dumps(body).encode(), method="POST" if body is not None else "GET",
                                       headers={"Host": f"127.0.0.1:{port}", "X-CPE-Token": app.token, "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(r) as resp:
                    return resp.status, json.loads(resp.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read() or b"{}")
        code, st = req("/api/cpe")
        self.assertEqual((code, st["total"], st["ready"]), (200, 91, 0))
        self.assertEqual([g["count"] for g in st["sets"]], [49, 15, 31])
        old = os.environ.get("CPE_QUESTIONS_URL")
        os.environ["CPE_QUESTIONS_URL"] = f"http://127.0.0.1:{port + 1}/none.zip"
        old_wait = cpeimport.download.__defaults__
        cpeimport.download.__defaults__ = (None, None, 3.0, 0, 0.0)               # 不重試，測試才不用等
        try:
            code, j = req("/api/cpe/import", {})
            self.assertEqual(code, 200)
            for _ in range(100):
                code, j = req("/api/cpe/progress")
                if j["state"] not in ("download", "convert"):
                    break
                time.sleep(0.1)
            self.assertEqual(j["state"], "error")
            self.assertIn("連不上", j["error"])
            # 成功的一次：假的 GitHub
            blob = make_zip({"一星題": [10008, 100], "歷屆試題": [255]})
            from http.server import BaseHTTPRequestHandler

            class H(BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(blob)))
                    self.end_headers()
                    self.wfile.write(blob)

                def log_message(self, *a):
                    pass
            gh = web.LocalServer(("127.0.0.1", 0), H)
            threading.Thread(target=gh.serve_forever, daemon=True).start()
            self.addCleanup(gh.server_close)
            self.addCleanup(gh.shutdown)
            os.environ["CPE_QUESTIONS_URL"] = f"http://127.0.0.1:{gh.server_address[1]}/a.zip"
            req("/api/cpe/import", {})
            for _ in range(200):
                code, j = req("/api/cpe/progress")
                if j["state"] not in ("download", "convert"):
                    break
                time.sleep(0.1)
            self.assertEqual(j["state"], "done", j)
            self.assertEqual((j["report"]["imported"], j["report"]["failed"]), (3, []))
            self.assertEqual(j["done"], j["total"])
            code, st = req("/api/cpe")
            self.assertEqual(st["ready"], 3)
            self.assertTrue(any(p["has_pdf"] for g in st["sets"] for p in g["problems"]))
            # 原 PDF 與題目頁的旗標
            r = urllib.request.Request(f"http://127.0.0.1:{port}/api/statement.pdf?id=uva10008", headers={"Host": f"127.0.0.1:{port}", "X-CPE-Token": app.token})
            with urllib.request.urlopen(r) as resp:
                self.assertEqual(resp.headers["Content-Type"], "application/pdf")
                self.assertTrue(resp.read().startswith(b"%PDF"))
            for bad in ("uva999", "..%2Fx", ""):
                r = urllib.request.Request(f"http://127.0.0.1:{port}/api/statement.pdf?id={bad}", headers={"Host": f"127.0.0.1:{port}", "X-CPE-Token": app.token})
                with self.assertRaises(urllib.error.HTTPError) as cm:
                    urllib.request.urlopen(r)
                self.assertEqual(cm.exception.code, 400)
            self.assertTrue(req("/api/problem?id=uva10008")[1]["has_pdf"])
        finally:
            cpeimport.download.__defaults__ = old_wait
            if old is None:
                os.environ.pop("CPE_QUESTIONS_URL", None)
            else:
                os.environ["CPE_QUESTIONS_URL"] = old


class ExtraTests(unittest.TestCase):
    def test_every_problem_has_meta_and_the_hints_reach_the_bank(self):
        mt = cpeset.meta()
        self.assertEqual(sorted(mt), sorted(cpeset.membership()))
        for n, m in mt.items():
            self.assertTrue(m["t"] and m["c"] and m["i"], n)
            self.assertIn(m["s"], (1, 2, 3, 4))
            self.assertTrue(1 <= m["u"] <= 52, n)
        with tempfile.TemporaryDirectory() as d:
            bank = bank_mod.load_bank(Workspace.create(Path(d), "2026-11-01"))
            for n in cpeset.membership():
                e = bank[f"uva{n}"]
                self.assertTrue(e.get("hint_insight"), n)
                self.assertTrue(e["cpe_tags"], n)
            self.assertIn("Horner", bank["uva10268"]["hint_insight"])
            self.assertNotIn("Horner", bank["uva100"]["hint_insight"])               # 原本就有的提示不被覆蓋

    def test_related_problems_share_tags(self):
        rel = cpeset.related(10010)
        self.assertTrue(rel and 10010 not in rel)
        mine = set(cpeset.meta()[10010]["t"])
        self.assertTrue(all(mine & set(cpeset.meta()[n]["t"]) for n in rel))
        self.assertEqual(cpeset.related(999999), [])

    def test_official_order_override_file(self):
        with tempfile.TemporaryDirectory() as d:
            ws = Workspace.create(Path(d), "2026-11-01")
            default = cpeset.set_numbers("one", ws)
            self.assertEqual(default, sorted(default))
            (ws.meta / "cpe_order.json").write_text(json.dumps({"one": [12019, 100, 999, 12019]}), encoding="utf-8")
            got = cpeset.set_numbers("one", ws)
            self.assertEqual(got[:2], [12019, 100])
            self.assertEqual(sorted(got), sorted(default))
            bank = bank_mod.load_bank(ws)
            self.assertEqual(cpeset.unit_pool(ws, bank, 15)["items"][0]["id"], "uva12019")
            (ws.meta / "cpe_order.json").write_text("not json", encoding="utf-8")
            self.assertEqual(cpeset.set_numbers("one", ws), default)

    def test_pool_items_carry_tags_prereq_and_related(self):
        with tempfile.TemporaryDirectory() as d:
            ws = Workspace.create(Path(d), "2026-11-01")
            it = cpeset.unit_pool(ws, bank_mod.load_bank(ws), 15)["items"][0]
            self.assertTrue(it["tags"] and it["prereq_unit"] and it["related"])

    def test_pdf_hashes_cover_every_pdf_and_a_changed_pdf_is_flagged(self):
        h = cpeset.pdf_hashes()
        self.assertEqual(len(h), 89)
        with tempfile.TemporaryDirectory() as d:
            ws = Workspace.create(Path(d), "2026-11-01")
            f = cpeimport.Found(10008, "one", "x.pdf", lambda: uva_pdf(10008))
            r = cpeimport.import_found(ws, [f])
            self.assertEqual(r.changed, ("uva10008",))                           # 合成的 PDF 當然和真的雜湊不同
            self.assertEqual(cpeimport.import_found(ws, [cpeimport.Found(999999, None, "y.pdf", lambda: uva_pdf(1))]).changed, ())

    def test_download_retries_server_errors_but_not_404(self):
        from http.server import BaseHTTPRequestHandler
        hits = []
        blob = make_zip({"一星題": [10008]})

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append(self.path)
                code = 404 if self.path == "/gone" else (503 if len([x for x in hits if x == self.path]) < 3 else 200)
                self.send_response(code)
                self.send_header("Content-Length", str(len(blob) if code == 200 else 0))
                self.end_headers()
                if code == 200:
                    self.wfile.write(blob)

            def log_message(self, *a):
                pass
        httpd = web.LocalServer(("127.0.0.1", 0), H)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        base = f"http://127.0.0.1:{httpd.server_address[1]}"
        self.assertEqual(cpeimport.download(url=base + "/flaky", wait=0.01), blob)         # 503, 503, 200
        self.assertEqual(hits.count("/flaky"), 3)
        with self.assertRaises(cpeimport.CpeImportError) as cm:
            cpeimport.download(url=base + "/gone", wait=0.01)
        self.assertIn("404", str(cm.exception))
        self.assertEqual(hits.count("/gone"), 1)                                             # 404 不重試

    def test_hyphen_is_dropped_only_with_evidence(self):
        mk = pdftext.Line

        def run(a, b):
            return uvastatement.build([[mk("1 T", False, 700, 0, 17), mk(a, False, 680, 0, 10.9), mk(b, False, 666, 0, 10.9)]]).text.strip().split("\n")[-1]
        self.assertEqual(run("find a single-", "source path"), "find a single-source path")          # 沒佐證：保留
        self.assertEqual(run("each in-", "teger is read"), "each integer is read")                    # 內建題目裡有 integer
        self.assertEqual(run("a rectan-", "gular grid, rectangular"), "a rectangular grid, rectangular")   # 本題其他地方有


if __name__ == "__main__":
    unittest.main()
