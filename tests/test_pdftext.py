"""內建的 PDF 文字擷取器：用 tests/pdfmaker.py 自己產生的 PDF（長得像 UVa 的 XeTeX 輸出）測語法、字型、版面與壞檔。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pdfmaker  # noqa: E402

from cpe_coach import pdftext  # noqa: E402
from cpe_coach.pdftext import Kw, Lexer, Name, PdfTextError, Ref  # noqa: E402


def text_of(data: bytes, **kw) -> str:
    return pdftext.extract_text(data, **kw)


def one_line_pdf(pieces, font=None, kind="cid", size=10.0, objstm=True, extra=None, name="LMRoman10-Regular", width=500):
    f = font or pdfmaker.Fnt(name, kind, width)
    pg = pdfmaker.Page()
    pg.text("F1", f, size, 0, 700, pieces)
    for args in extra or []:
        pg.text(*args)
    return pdfmaker.build_pdf([pg], {"F1": f}, objstm=objstm)


class Syntax(unittest.TestCase):
    def tokens(self, raw: bytes):
        lx = Lexer(raw)
        out = []
        while True:
            t = lx.token()
            if t is None:
                return out
            out.append(t)

    def test_names_numbers_strings_and_delimiters(self):
        t = self.tokens(rb"/Name#20x 12 -3.5 .25 (a\(b\)\\c\101\n) <48 65 6C6c6F> [ ] << >> true % comment" + b"\n" + rb"BT")
        self.assertEqual(t[0], "Name x")
        self.assertIsInstance(t[0], Name)
        self.assertEqual(t[1:4], [12, -3.5, 0.25])
        self.assertEqual(t[4], b"a(b)\\cA\n")
        self.assertEqual(t[5], b"Hello")
        self.assertEqual(t[6:9], ["[", "]", "<<"])
        self.assertEqual(t[9], ">>")
        self.assertIsInstance(t[10], Kw)
        self.assertEqual(t[-1], "BT")

    def test_odd_number_of_hex_digits_and_nested_parentheses(self):
        self.assertEqual(self.tokens(b"<414>"), [b"A@"])
        self.assertEqual(self.tokens(b"(a(b)c)"), [b"a(b)c"])

    def test_unterminated_things_raise_a_clear_error(self):
        for raw in (b"(abc", b"<414"):
            with self.assertRaises(PdfTextError):
                Lexer(raw).token()
        with self.assertRaises(PdfTextError):
            Lexer(b"<< /A 1 ").value()
        with self.assertRaises(PdfTextError):
            Lexer(b"[1 2 ").value()

    def test_values_dicts_arrays_and_references(self):
        v = Lexer(b"<< /A 1 0 R /B [1 2 3 0 R (x)] /C << /D null >> /E 5 6 >>").value()
        self.assertIsInstance(v["A"], Ref)
        self.assertEqual(v["A"].num, 1)
        self.assertEqual(v["B"][:2], [1, 2])
        self.assertEqual(v["B"][2].num, 3)
        self.assertEqual(v["B"][3], b"x")
        self.assertEqual(v["C"], {"D": None})
        self.assertEqual(v["E"], 5)                                   # 「5 6」後面不是 R：只是兩個數字

    def test_cmap_bfchar_and_both_forms_of_bfrange(self):
        cm = (b"1 begincodespacerange <0000> <FFFF> endcodespacerange\n2 beginbfchar <0001> <0041> <0002> <00660069> endbfchar\n"
              b"2 beginbfrange <0010> <0012> <0061> <0020> <0021> [<0078> <0079>] endbfrange")
        m = pdftext.parse_cmap(cm)
        self.assertEqual(m[1], "A")
        self.assertEqual(m[2], "fi")                                  # 連字：一個字碼 = 多個字元
        self.assertEqual([m[0x10], m[0x11], m[0x12]], ["a", "b", "c"])
        self.assertEqual([m[0x20], m[0x21]], ["x", "y"])


class Layout(unittest.TestCase):
    def check_both_structures(self, build):
        for objstm in (True, False):
            with self.subTest(objstm=objstm):
                self.run_check(build(objstm))

    def test_words_lines_and_spaces(self):
        f = pdfmaker.Fnt("LMRoman10-Regular", "cid", 500)

        def build(objstm):
            pg = pdfmaker.Page()
            pg.text("F1", f, 10.909, 0, 700, pdfmaker.line_pieces(f, "Hello big world"))
            pg.text("F1", f, 10.909, 0, 686.4, pdfmaker.line_pieces(f, "second line"))
            return pdfmaker.build_pdf([pg], {"F1": f}, objstm=objstm)
        for objstm in (True, False):
            with self.subTest(objstm=objstm):
                self.assertEqual(text_of(build(objstm)).strip(), "Hello big world\nsecond line")

    def test_small_kerning_is_not_a_space_but_a_word_gap_is(self):
        f = pdfmaker.Fnt("LMRoman10-Regular", "cid", 500)
        data = one_line_pdf(["AV", 80, "ab", -333, "cd"], font=f)
        self.assertEqual(text_of(data).strip(), "AVab cd")

    def test_monospace_columns_and_double_spaces_are_kept(self):
        mono = pdfmaker.Fnt("LMMono10-Regular", "cid", 525, mono=True)
        pg = pdfmaker.Page()
        for i, s in enumerate(["a  b", "1 2 3", "x   y z"]):
            pg.text("F1", mono, 9.963, 0, 700 - 10.909 * i, pdfmaker.mono_pieces(mono, s))
        self.assertEqual(text_of(pdfmaker.build_pdf([pg], {"F1": mono})).strip(), "a  b\n1 2 3\nx   y z")

    def test_blank_lines_and_indentation_inside_monospace_blocks(self):
        mono = pdfmaker.Fnt("LMMono10-Regular", "cid", 525, mono=True)
        pg = pdfmaker.Page()
        ys = {0: 700, 1: 700 - 10.909, 2: 700 - 3 * 10.909, 3: 700 - 4 * 10.909}      # 第 2 行和第 3 行之間隔了一個空行
        for i, s in enumerate(["first", "second", "  indented", "last"]):
            pg.text("F1", mono, 9.963, 0, ys[i], pdfmaker.mono_pieces(mono, s))
        got = text_of(pdfmaker.build_pdf([pg], {"F1": mono})).strip("\n")
        self.assertEqual(got, "first\nsecond\n\n  indented\nlast")

    def test_each_page_is_separate_and_paragraph_gaps_become_blank_lines(self):
        f = pdfmaker.Fnt("LMRoman10-Regular", "cid", 500)
        p1, p2 = pdfmaker.Page(), pdfmaker.Page()
        for i, (y, s) in enumerate([(700, "para one a"), (686.4, "para one b"), (655, "para two")]):
            p1.text("F1", f, 10.909, 0, y, pdfmaker.line_pieces(f, s))
        p2.text("F1", f, 10.909, 0, 700, pdfmaker.line_pieces(f, "next page"))
        pages = pdftext.extract_pages(pdfmaker.build_pdf([p1, p2], {"F1": f}))
        self.assertEqual([[ln.text for ln in pg] for pg in pages], [["para one a", "para one b", "para two"], ["next page"]])
        self.assertEqual([ln.blank_before for ln in pages[0]], [0, 0, 1])

    def test_superscripts_and_subscripts_are_marked(self):
        f = pdfmaker.Fnt("LMRoman10-Regular", "cid", 500)
        small = pdfmaker.Fnt("LMRoman7-Regular", "cid", 500)
        pg = pdfmaker.Page()
        pg.text("F1", f, 10.909, 0, 700, ["N = 10"])
        pg.text("F2", small, 7.97, 5 * 5.45 + 5.0, 703.9, ["9"])                       # 上標：字小、位置高
        pg.text("F1", f, 10.909, 0, 686.4, ["a"])
        pg.text("F2", small, 7.97, 5.45, 685.0, ["i"])                                  # 下標
        got = text_of(pdfmaker.build_pdf([pg], {"F1": f, "F2": small}))
        self.assertIn("10^9", got.replace(" ", ""))
        self.assertIn("a_i", got.replace(" ", ""))
        self.assertNotIn("^", text_of(pdfmaker.build_pdf([pg], {"F1": f, "F2": small}), scripts=False))

    def test_tex_fonts_without_tounicode_use_the_computer_modern_tables(self):
        mi = pdfmaker.Fnt("CMMI10", "tex", 600)                 # 數學斜體：字母就是 ASCII
        sy = pdfmaker.Fnt("CMSY10", "tex", 778)                 # 符號：0x14 ≤、0x15 ≥、0x02 ×
        r = pdfmaker.Fnt("CMR10", "tex", 500)                   # 0x60 ‘、0x27 ’、0x0C fi
        pg = pdfmaker.Page()
        pg.text("F1", mi, 10, 0, 700, ["n"])
        pg.text("F2", sy, 10, 20, 700, [bytes([0x14]).decode("latin-1")])
        pg.text("F3", r, 10, 50, 700, ["1"])
        pg.text("F4", r, 10, 0, 686, [chr(0x60) + "A" + chr(0x27) + " " + chr(0x0C) + "x"])
        pg.text("F2", sy, 10, 0, 672, [bytes([0x02, 0x15]).decode("latin-1")])
        got = text_of(pdfmaker.build_pdf([pg], {"F1": mi, "F2": sy, "F3": r, "F4": r}))
        self.assertIn("n ≤ 1", got)
        self.assertIn("‘A’ fix", got.replace("  ", " "))
        self.assertIn("×≥", got)

    def test_glyph_names_in_differences_are_understood(self):
        # 簡單字型的 /Encoding << /Differences [...] >>：沒有 ToUnicode 時靠字形名稱
        f = pdfmaker.Fnt("LMRoman10-Regular", "tex", 500)
        data = one_line_pdf([bytes([1, 2]).decode("latin-1") + "A"], font=f, objstm=False)
        data = data.replace(b"/FirstChar 32", b"/Encoding << /Differences [1 /bullet /fi] >> /FirstChar 32")
        self.assertEqual(text_of(data).strip(), "•fiA")

    def test_missing_glyph_placeholders_are_dropped_by_the_statement_layer_not_here(self):
        f = pdfmaker.Fnt("LMRoman10-Regular", "cid", 500)
        f.codes["￿"] = 1
        data = one_line_pdf(["a", "￿", "b"], font=f)
        self.assertIn("￿", text_of(data))


class Robustness(unittest.TestCase):
    def good(self):
        return pdfmaker.make_uva_pdf(1, "T", "body text here", "in", "out", "1 2", "3")

    def test_not_a_pdf_and_empty_input(self):
        for raw in (b"", b"hello", b"\x89PNG\r\n\x1a\n" + b"0" * 100):
            with self.assertRaises(PdfTextError):
                pdftext.extract_text(raw)

    def test_encrypted_pdf_is_refused_with_a_reason(self):
        data = self.good().replace(b"trailer\n<<", b"trailer\n<< /Encrypt 99 0 R")
        with self.assertRaises(PdfTextError) as cm:
            pdftext.extract_text(data)
        self.assertIn("加密", str(cm.exception))

    def test_pdf_without_any_text_says_so(self):
        pg = pdfmaker.Page()
        pg.ops.append(b"0 0 100 100 re f")
        with self.assertRaises(PdfTextError) as cm:
            pdftext.extract_text(pdfmaker.build_pdf([pg], {}))
        self.assertIn("沒有文字", str(cm.exception))

    def test_truncated_and_corrupted_files_never_crash_or_hang(self):
        good = self.good()
        for cut in range(0, len(good), max(1, len(good) // 40)):
            try:
                pdftext.extract_text(good[:cut])
            except PdfTextError:
                pass
        bad = bytearray(good)
        for i in range(60, len(bad), 97):
            bad[i] ^= 0x5A
        try:
            pdftext.extract_text(bytes(bad))
        except PdfTextError:
            pass

    def test_deeply_nested_arrays_are_a_clean_error(self):
        data = b"%PDF-1.5\n1 0 obj\n" + b"[" * 5000 + b"\nendobj\n"
        with self.assertRaises(PdfTextError):
            pdftext.extract_text(data)


if __name__ == "__main__":
    unittest.main()
