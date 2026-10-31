"""選用：拿真的 CPE_Previous_Questions（釘住的提交）驗證擷取結果。
設定環境變數 CPE_QUESTIONS_DIR=<clone 的資料夾> 才會跑；沒設就整個略過（真的題目 PDF 有版權，不放進本專案）。
只比對雜湊（tests/fixtures/cpe_repo_digests.json）以及（有裝 poppler 的話）和 pdftotext 的範例逐字比對；絕不執行 repo 裡別人的解答。"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cpe_coach import cpeimport, cpeset, service, uvastatement  # noqa: E402

FOLDER = os.environ.get("CPE_QUESTIONS_DIR")
FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "cpe_repo_digests.json").read_text(encoding="utf-8"))


def norm(t: str) -> str:
    return " ".join(t.split())


@unittest.skipUnless(FOLDER and Path(FOLDER).is_dir(), "未設定 CPE_QUESTIONS_DIR")
class RealRepoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.found = {f.number: f for f in cpeimport.scan_folder(Path(FOLDER))}

    def test_every_listed_problem_has_a_pdf_except_the_known_gaps(self):
        listed = set(cpeset.membership())
        self.assertEqual(sorted(listed - set(self.found)), [1034, 11332])
        self.assertEqual(len(self.found), 89)

    def test_sample_digests_match_the_pinned_commit(self):
        bad = []
        for n, f in sorted(self.found.items()):
            st = uvastatement.from_pdf(f.read())
            got = [hashlib.sha256((norm(a) + "\n---\n" + norm(b)).encode("utf-8")).hexdigest() for a, b in service.parse_samples(st.text)]
            if got != FIXTURE["digests"][str(n)]:
                bad.append(n)
        self.assertEqual(bad, [])

    @unittest.skipUnless(shutil.which("pdftotext"), "沒有 pdftotext")
    def test_samples_agree_with_pdftotext_token_by_token(self):
        """對照組：pdftotext -layout 的 Sample Input／Output 區塊（去掉頁尾），逐個詞比對。"""
        bad = []
        for n, f in sorted(self.found.items()):
            raw = f.read()
            ref = subprocess.run(["pdftotext", "-layout", "-", "-"], input=raw, capture_output=True).stdout.decode("utf-8", "replace")
            lines = [ln for ln in ref.replace("\f", "\n").split("\n") if "Universidad de Valladolid OJ" not in ln and not re.fullmatch(r"\s*\d+/\d+\s*", ln)]
            marks = [(i, "in" if re.match(r"^\s*Sample Input", ln) else "out") for i, ln in enumerate(lines) if re.match(r"^\s*Sample (Input|Output)", ln)]
            blocks = [(kind, lines[i + 1:(marks[k + 1][0] if k + 1 < len(marks) else len(lines))]) for k, (i, kind) in enumerate(marks)]
            pairs, pend = [], None
            for kind, body in blocks:
                if kind == "in":
                    pend = body
                elif pend is not None:
                    pairs.append((pend, body))
                    pend = None
            mine = service.parse_samples(uvastatement.from_pdf(raw).text)
            if [(a.split(), b.split()) for a, b in mine] != [(" ".join(x).split(), " ".join(y).split()) for x, y in pairs]:
                bad.append(n)
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
