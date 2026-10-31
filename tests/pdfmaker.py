"""測試用：自己產生長得像 UVa 題目（XeTeX／xdvipdfmx）的 PDF。
CID 字型（Identity-H＋ToUnicode）、TeX 的簡單字型（沒有 ToUnicode，靠字型名稱的字碼表）、物件串流、多頁、頁尾、等寬字的範例區塊。
（真的題目 PDF 有版權，不能放進這個專案當測試資料，所以測試用自己產生的內容。）"""
import zlib
from typing import Dict, List, Optional, Tuple

PAGE_H = 841.89


class Fnt:
    """一個字型：字元 → 字碼（依第一次出現的順序編號），以及 ToUnicode。"""

    def __init__(self, name: str, kind: str, width: int = 500, mono: bool = False):
        self.name, self.kind, self.width, self.mono = name, kind, width, mono   # kind: cid／tex
        self.codes: Dict[str, int] = {}

    def code(self, ch: str) -> int:
        if self.kind == "tex":
            return ord(ch)
        return self.codes.setdefault(ch, len(self.codes) + 1)

    def encode(self, s: str) -> bytes:
        if self.kind == "tex":
            return s.encode("latin-1")
        return b"".join(self.code(c).to_bytes(2, "big") for c in s)

    def cmap(self) -> bytes:
        rows = "".join(f"<{c:04X}> <{ord(ch):04X}>\n" for ch, c in self.codes.items())
        return (f"/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n1 begincodespacerange\n<0000> <FFFF>\nendcodespacerange\n"
                f"{len(self.codes)} beginbfchar\n{rows}endbfchar\nendcmap\nend end\n").encode("ascii")


def _esc(b: bytes) -> bytes:
    return b.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


class Page:
    def __init__(self):
        self.ops: List[bytes] = []

    def text(self, font_res: str, fnt: Fnt, size: float, x: float, y: float, pieces: List) -> None:
        """pieces：字串與 TJ 的調整數字（正的往左縮，負的往右空開）。"""
        arr = b""
        for p in pieces:
            if isinstance(p, str):
                arr += (b"<" + fnt.encode(p).hex().encode() + b">") if fnt.kind == "cid" else (b"(" + _esc(fnt.encode(p)) + b")")
            else:
                arr += b"%g" % p
        self.ops.append(b"BT /%s %g Tf %g %g Td [%s]TJ ET" % (font_res.encode(), size, x, y, arr))


def line_pieces(fnt: Fnt, s: str) -> List:
    """空白變成 TJ 的間距：等寬字每個空白 = 一格；其他字型 = 0.333 em。"""
    gap = -fnt.width if fnt.mono else -333
    out: List = []
    cur = ""
    for ch in s:
        if ch == " ":
            if cur:
                out.append(cur)
                cur = ""
            if out and isinstance(out[-1], (int, float)):
                out[-1] += gap
            else:
                out.append(gap)
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def wrap(text: str, width: int = 92) -> List[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


def build_pdf(pages: List[Page], fonts: Dict[str, Fnt], objstm: bool = True, creator: str = "XeTeX output 2015.02.05:0031") -> bytes:
    """組成 PDF。objstm=True 時，非串流物件放進物件串流（和 xdvipdfmx 一樣）。"""
    objs: Dict[int, bytes] = {}
    streams: Dict[int, Tuple[bytes, bytes]] = {}
    nxt = [1]

    def new() -> int:
        n = nxt[0]
        nxt[0] += 1
        return n

    catalog, pages_node = new(), new()
    font_objs: Dict[str, int] = {}
    for res, f in fonts.items():
        fo = new()
        font_objs[res] = fo
        if f.kind == "cid":
            tu, desc = new(), new()
            streams[tu] = (b"<< /Filter /FlateDecode >>", zlib.compress(f.cmap()))
            objs[desc] = b"<< /Type /Font /Subtype /CIDFontType0 /BaseFont /AAAAAA+%s /DW %d /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> >>" % (f.name.encode(), f.width)
            objs[fo] = b"<< /Type /Font /Subtype /Type0 /BaseFont /AAAAAA+%s-Identity-H /Encoding /Identity-H /DescendantFonts [%d 0 R] /ToUnicode %d 0 R >>" % (f.name.encode(), desc, tu)
        else:
            widths = b" ".join(b"%d" % f.width for _ in range(95))
            objs[fo] = b"<< /Type /Font /Subtype /Type1 /BaseFont /BBBBBB+%s /FirstChar 32 /LastChar 126 /Widths [%s] >>" % (f.name.encode(), widths)
    res_obj = new()
    objs[res_obj] = b"<< /Font << " + b" ".join(b"/%s %d 0 R" % (k.encode(), v) for k, v in font_objs.items()) + b" >> >>"
    kids = []
    for pg in pages:
        c, pn = new(), new()
        streams[c] = (b"<< /Filter /FlateDecode >>", zlib.compress(b"q 1 0 0 1 72 0 cm\n" + b"\n".join(pg.ops) + b"\nQ"))
        objs[pn] = b"<< /Type /Page /Parent %d 0 R /Resources %d 0 R /Contents [%d 0 R] >>" % (pages_node, res_obj, c)
        kids.append(pn)
    objs[pages_node] = b"<< /Type /Pages /Count %d /Kids [%s] /MediaBox [0 0 595.28 841.89] >>" % (len(kids), b" ".join(b"%d 0 R" % k for k in kids))
    objs[catalog] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages_node
    info = new()
    objs[info] = b"<< /Creator (%s) /Producer (xdvipdfmx \\(20140317\\)) >>" % creator.encode()

    out = bytearray(b"%PDF-1.5\n%\xe4\xf0\xed\xf8\n")
    if objstm:
        packed = sorted(objs)
        body = b"\n".join(objs[n] for n in packed)
        header, off = b"", 0
        for n in packed:
            header += b"%d %d " % (n, off)
            off += len(objs[n]) + 1
        osn = new()
        data = zlib.compress(header + body)
        streams[osn] = (b"<< /Type /ObjStm /N %d /First %d /Filter /FlateDecode >>" % (len(packed), len(header)), data)
        for n in sorted(streams):
            d, raw = streams[n]
            out += b"%d 0 obj\n%s\nstream\n" % (n, d[:-2] + b" /Length %d >>" % len(raw)) + raw + b"\nendstream\nendobj\n"
    else:
        for n in sorted(objs):
            out += b"%d 0 obj\n%s\nendobj\n" % (n, objs[n])
        for n in sorted(streams):
            d, raw = streams[n]
            out += b"%d 0 obj\n%s\nstream\n" % (n, d[:-2] + b" /Length %d >>" % len(raw)) + raw + b"\nendstream\nendobj\n"
    out += b"trailer\n<< /Root %d 0 R /Info %d 0 R >>\n%%%%EOF\n" % (catalog, info)
    return bytes(out)


def make_uva_pdf(number: int, title: str, body: str, input_text: str, output_text: str, sample_in: str, sample_out: str,
                 objstm: bool = True, lines_per_page: Optional[int] = None) -> bytes:
    """像 UVa 的題目：標題、一段描述、Input、Output、Sample Input、Sample Output；lines_per_page 小的時候範例會被換頁切開，每頁有頁尾。"""
    bold = Fnt("LMSans10-Bold", "cid", 600)
    roman = Fnt("LMRoman10-Regular", "cid", 500)
    mono = Fnt("LMMono10-Regular", "cid", 525, mono=True)
    math = Fnt("CMMI10", "tex", 600)
    fonts = {"F1": bold, "F2": roman, "F3": mono, "F4": math}
    rows: List[Tuple[str, str, float, float]] = []                    # (字型資源, 文字, 字級, 這行上方的額外間距)

    def para(s: str) -> None:
        for i, ln in enumerate(wrap(s)):
            rows.append(("F2", ln, 10.909, 0.0))

    def head(s: str) -> None:
        rows.append(("F1", s, 12.0, 14.0))

    rows.append(("F1", f"{number} {title}", 17.215, 0.0))
    para(body)
    head("Input")
    para(input_text)
    head("Output")
    para(output_text)
    head("Sample Input")
    first = True
    for ln in sample_in.split("\n"):
        rows.append(("F3", ln, 9.963, 6.0 if first else 0.0))
        first = False
    head("Sample Output")
    first = True
    for ln in sample_out.split("\n"):
        rows.append(("F3", ln, 9.963, 6.0 if first else 0.0))
        first = False

    per = lines_per_page or 10 ** 6
    chunks = [rows[i:i + per] for i in range(0, len(rows), per)] or [[]]
    pages: List[Page] = []
    for pi, chunk in enumerate(chunks, 1):
        pg = Page()
        y = 750.0
        for res, text, size, extra in chunk:
            f = fonts[res]
            pitch = 10.909 if res == "F3" else (size * 1.25 if res != "F2" else 13.6)
            y -= pitch + extra
            if text.strip():
                pg.text(res, f, size, 0, y, line_pieces(f, text) if res != "F3" else mono_pieces(f, text))
        pg.text("F2", roman, 8, 0, 40, line_pieces(roman, f"Universidad de Valladolid OJ: {number} – {title}   {pi}/{len(chunks)}"))
        pages.append(pg)
    return build_pdf(pages, fonts, objstm=objstm)


def mono_pieces(f: Fnt, s: str) -> List:
    """等寬字：行首的空白寫成縮排由呼叫端處理，這裡只處理中間的空白（連續 n 個空白 = n 格）。"""
    lead = len(s) - len(s.lstrip(" "))
    out = line_pieces(f, s.lstrip(" "))
    return ([-f.width * lead] if lead else []) + out
