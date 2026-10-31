"""只用標準函式庫從 PDF 取出文字（匯入 UVa 的原題 PDF 用）。

支援範圍（夠用就好，不是通用的 PDF 閱讀器）：
- 物件串流（ObjStm）、FlateDecode／ASCIIHex／ASCII85 壓縮；不需要 xref 表（直接掃描物件）。
- 字型：Type0／CID（Identity-H，用 ToUnicode 還原文字）、簡單字型（ToUnicode，或 TeX 的 Computer Modern：CMR／CMMI／CMSY…
  依字型名稱用固定的字碼表）。
- 內容串流：BT／ET、Tf、Td／TD／Tm／T*、Tj／TJ／'／"、Tc／Tw／Tz／TL／Ts、q／Q／cm。
- 版面：同一行的字依位置接起來，字距夠大才補空白（等寬字型補到對得上欄位，所以範例輸入的空格數正確），行距大的地方補空行，
  上標／下標寫成 ^ 與 _。

不支援：加密、掃描圖片（沒有文字層）、直書。遇到就丟 PdfTextError，讓呼叫端說明原因。
"""
from __future__ import annotations

import base64
import math
import re
import zlib
from typing import Any, Dict, List, Optional, Tuple


class PdfTextError(Exception):
    pass


# ---------- PDF 語法 ----------
class Name(str):
    pass


class Ref:
    __slots__ = ("num",)

    def __init__(self, num: int):
        self.num = num

    def __repr__(self) -> str:
        return f"Ref({self.num})"


class Kw(str):
    """關鍵字／運算子（obj、stream、true、BT、Tj…）。"""


WS = b"\x00\t\n\x0c\r "
DELIM = b"()<>[]{}/%"
NUM_RE = re.compile(rb"[+-]?(?:\d+\.?\d*|\.\d+)")
_ESC = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12, ord("("): 40, ord(")"): 41, ord("\\"): 92}


class Lexer:
    def __init__(self, data: bytes, pos: int = 0):
        self.d = data
        self.i = pos

    def skip_ws(self) -> None:
        d, n = self.d, len(self.d)
        while self.i < n:
            c = d[self.i]
            if c in WS:
                self.i += 1
            elif c == 0x25:                                   # % 註解到行尾
                while self.i < n and d[self.i] not in b"\r\n":
                    self.i += 1
            else:
                break

    def token(self) -> Any:
        """下一個記號：數字、Name、bytes（字串）、Kw、或 '[' ']' '<<' '>>'；結尾回傳 None。"""
        self.skip_ws()
        d, n = self.d, len(self.d)
        if self.i >= n:
            return None
        c = d[self.i]
        if c == 0x2F:                                         # /Name
            j = self.i + 1
            while j < n and d[j] not in WS and d[j] not in DELIM:
                j += 1
            raw = d[self.i + 1:j]
            self.i = j
            return Name(re.sub(rb"#([0-9A-Fa-f]{2})", lambda m: bytes([int(m.group(1), 16)]), raw).decode("latin-1"))
        if c == 0x28:                                         # (字串)
            return self._literal()
        if c == 0x3C:
            if d[self.i + 1:self.i + 2] == b"<":
                self.i += 2
                return "<<"
            j = d.find(b">", self.i)
            if j < 0:
                raise PdfTextError("十六進位字串沒有結尾")
            hx = re.sub(rb"[^0-9A-Fa-f]", b"", d[self.i + 1:j])
            if len(hx) % 2:
                hx += b"0"
            self.i = j + 1
            return bytes.fromhex(hx.decode("ascii"))
        if c == 0x3E:
            if d[self.i + 1:self.i + 2] == b">":
                self.i += 2
                return ">>"
            self.i += 1
            return Kw(">")
        if c in b"[]":
            self.i += 1
            return chr(c)
        if c in b"{}":
            self.i += 1
            return Kw(chr(c))
        if c == 0x29:
            self.i += 1
            return Kw(")")
        m = NUM_RE.match(d, self.i)
        if m and (m.end() >= n or d[m.end()] in WS or d[m.end()] in DELIM):
            self.i = m.end()
            s = m.group(0)
            return float(s) if b"." in s else int(s)
        j = self.i
        while j < n and d[j] not in WS and d[j] not in DELIM:
            j += 1
        if j == self.i:
            j += 1
        w = d[self.i:j].decode("latin-1")
        self.i = j
        return Kw(w)

    def _literal(self) -> bytes:
        d, n = self.d, len(self.d)
        i = self.i + 1
        depth, out = 1, bytearray()
        while i < n:
            c = d[i]
            if c == 0x5C:                                     # 跳脫
                i += 1
                if i >= n:
                    break
                e = d[i]
                if e in _ESC:
                    out.append(_ESC[e])
                elif 0x30 <= e <= 0x37:
                    j = i
                    while j < n and j < i + 3 and 0x30 <= d[j] <= 0x37:
                        j += 1
                    out.append(int(d[i:j], 8) & 0xFF)
                    i = j - 1
                elif e == 0x0D:
                    if d[i + 1:i + 2] == b"\n":
                        i += 1
                elif e == 0x0A:
                    pass
                else:
                    out.append(e)
            elif c == 0x28:
                depth += 1
                out.append(c)
            elif c == 0x29:
                depth -= 1
                if depth == 0:
                    self.i = i + 1
                    return bytes(out)
                out.append(c)
            else:
                out.append(c)
            i += 1
        raise PdfTextError("字串沒有結尾")

    def value(self, tok: Any = None) -> Any:
        """解析一個物件（字典、陣列、數字、間接參照 N G R…）。tok：已經讀出的第一個記號。"""
        if tok is None:
            tok = self.token()
        if tok == "<<" and not isinstance(tok, (bytes, Name)):
            out: Dict[str, Any] = {}
            while True:
                k = self.token()
                if k == ">>" and not isinstance(k, (bytes, Name)):
                    return out
                if k is None:
                    raise PdfTextError("字典沒有結尾")
                if not isinstance(k, Name):
                    continue
                out[str(k)] = self.value()
        if tok == "[" and not isinstance(tok, (bytes, Name)):
            arr: List[Any] = []
            while True:
                t = self.token()
                if t == "]" and not isinstance(t, (bytes, Name)):
                    return arr
                if t is None:
                    raise PdfTextError("陣列沒有結尾")
                arr.append(self.value(t))
        if isinstance(tok, int) and not isinstance(tok, bool):
            save = self.i
            t2 = self.token()
            if isinstance(t2, int) and not isinstance(t2, bool):
                t3 = self.token()
                if isinstance(t3, Kw) and t3 == "R":
                    return Ref(tok)
            self.i = save
            return tok
        if isinstance(tok, Kw):
            return {"true": True, "false": False, "null": None}.get(str(tok), tok)
        return tok


# ---------- 串流解碼 ----------
def _flate(data: bytes) -> bytes:
    try:
        return zlib.decompress(data)
    except zlib.error:
        d = zlib.decompressobj()
        try:
            return d.decompress(data)
        except zlib.error:
            return b""


def decode_stream(dic: Dict[str, Any], raw: bytes, pdf: "Pdf") -> bytes:
    filters = pdf.resolve(dic.get("Filter"))
    if filters is None:
        return raw
    if not isinstance(filters, list):
        filters = [filters]
    params = pdf.resolve(dic.get("DecodeParms"))
    if not isinstance(params, list):
        params = [params] * len(filters)
    data = raw
    for f, p in zip(filters, params):
        f = str(pdf.resolve(f))
        if f in ("FlateDecode", "Fl"):
            data = _flate(data)
            p = pdf.resolve(p)
            if isinstance(p, dict) and pdf.resolve(p.get("Predictor", 1)) not in (1, None):
                raise PdfTextError("不支援帶預測器的壓縮串流")
        elif f in ("ASCIIHexDecode", "AHx"):
            hx = re.sub(rb"[^0-9A-Fa-f]", b"", data.split(b">")[0])
            data = bytes.fromhex((hx + (b"0" if len(hx) % 2 else b"")).decode("ascii"))
        elif f in ("ASCII85Decode", "A85"):
            body = data.strip()
            if body.startswith(b"<~"):
                body = body[2:]
            data = base64.a85decode(body.split(b"~>")[0], adobe=False)
        else:
            raise PdfTextError(f"不支援的壓縮方式：{f}")
    return data


# ---------- 文件 ----------
OBJ_RE = re.compile(rb"(?<![0-9])(\d+)\s+(\d+)\s+obj\b")


class Pdf:
    def __init__(self, data: bytes):
        if not data.lstrip().startswith(b"%PDF"):
            raise PdfTextError("這不是 PDF 檔")
        self.data = data
        self.objs: Dict[int, Any] = {}
        self.streams: Dict[int, Tuple[Dict[str, Any], bytes]] = {}
        try:
            self._scan()
            self._objstms()
        except RecursionError:
            raise PdfTextError("這個 PDF 的結構太複雜，讀不了")
        if re.search(rb"/Encrypt\s", data[-4096:]) or any(isinstance(v, dict) and "Encrypt" in v for v in self.objs.values()):
            raise PdfTextError("這個 PDF 有加密，沒辦法讀")

    def resolve(self, v: Any, depth: int = 0) -> Any:
        while isinstance(v, Ref) and depth < 30:
            v = self.objs.get(v.num)
            depth += 1
        return v

    def _scan(self) -> None:
        d = self.data
        pos = 0
        while True:
            m = OBJ_RE.search(d, pos)
            if not m:
                return
            num = int(m.group(1))
            lx = Lexer(d, m.end())
            try:
                val = lx.value()
            except PdfTextError:
                pos = m.end()
                continue
            pos = lx.i
            lx.skip_ws()
            if isinstance(val, dict) and d.startswith(b"stream", lx.i):
                start = lx.i + 6
                if d[start:start + 2] == b"\r\n":
                    start += 2
                elif d[start:start + 1] in (b"\n", b"\r"):
                    start += 1
                length = self.resolve(val.get("Length")) if not isinstance(val.get("Length"), Ref) else None
                end = None
                if isinstance(length, int) and d[start + length:start + length + 20].lstrip(b"\r\n ").startswith(b"endstream"):
                    end = start + length
                if end is None:
                    end = d.find(b"endstream", start)
                    if end < 0:
                        end = len(d)
                    while end > start and d[end - 1:end] in (b"\n", b"\r"):
                        end -= 1
                self.streams[num] = (val, d[start:end])
                pos = end
            self.objs[num] = val

    def _objstms(self) -> None:
        for num, (dic, raw) in list(self.streams.items()):
            if str(dic.get("Type")) != "ObjStm":
                continue
            try:
                body = decode_stream(dic, raw, self)
                n, first = int(self.resolve(dic["N"])), int(self.resolve(dic["First"]))
            except (PdfTextError, KeyError, TypeError, ValueError):
                continue
            lx = Lexer(body)
            pairs = []
            for _ in range(n):
                a, b = lx.token(), lx.token()
                if isinstance(a, int) and isinstance(b, int):
                    pairs.append((a, b))
            for onum, off in pairs:
                try:
                    self.objs.setdefault(onum, Lexer(body, first + off).value())
                except PdfTextError:
                    continue

    def stream(self, v: Any) -> Optional[bytes]:
        if isinstance(v, Ref):
            item = self.streams.get(v.num)
            if item is None:
                return None
            return decode_stream(item[0], item[1], self)
        return None

    def pages(self) -> List[Dict[str, Any]]:
        """依頁面樹的順序回傳每一頁的字典（Resources 從上層繼承）。"""
        root = None
        for v in self.objs.values():
            if isinstance(v, dict) and str(v.get("Type")) == "Catalog":
                root = v
                break
        out: List[Dict[str, Any]] = []

        def walk(node: Any, inherited: Dict[str, Any], seen: set) -> None:
            n = self.resolve(node)
            if not isinstance(n, dict) or id(n) in seen:
                return
            seen.add(id(n))
            inh = dict(inherited)
            if "Resources" in n:
                inh["Resources"] = n["Resources"]
            if str(n.get("Type")) == "Pages" or "Kids" in n:
                for k in self.resolve(n.get("Kids")) or []:
                    walk(k, inh, seen)
            else:
                page = dict(n)
                page.setdefault("Resources", inh.get("Resources"))
                out.append(page)
        if root is not None:
            walk(root.get("Pages"), {}, set())
        if not out:                                           # 頁面樹壞了：照物件編號找 /Type /Page
            for num in sorted(self.objs):
                v = self.objs[num]
                if isinstance(v, dict) and str(v.get("Type")) == "Page":
                    out.append(v)
        return out


# ---------- 字型 ----------
def _utf16(b: bytes) -> str:
    try:
        return b.decode("utf-16-be")
    except UnicodeDecodeError:
        return ""


def parse_cmap(text: bytes) -> Dict[int, str]:
    """ToUnicode CMap → {字碼: 文字}。"""
    out: Dict[int, str] = {}
    for blk in re.findall(rb"beginbfchar(.*?)endbfchar", text, re.S):
        for a, b in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]*)>", blk):
            out[int(a, 16)] = _utf16(bytes.fromhex(b.decode()))
    for blk in re.findall(rb"beginbfrange(.*?)endbfrange", text, re.S):
        lx = Lexer(blk)
        while True:
            lo = lx.token()
            if lo is None:
                break
            hi = lx.token()
            dst = lx.token()
            if not (isinstance(lo, bytes) and isinstance(hi, bytes)):
                break
            a, b = int.from_bytes(lo, "big"), int.from_bytes(hi, "big")
            if dst == "[":
                items = []
                while True:
                    t = lx.token()
                    if t == "]" or t is None:
                        break
                    items.append(t)
                for k, it in enumerate(items):
                    if a + k <= b and isinstance(it, bytes):
                        out[a + k] = _utf16(it)
            elif isinstance(dst, bytes) and dst:
                base = _utf16(dst)
                for k in range(0, min(b - a, 0xFFFF) + 1):
                    out[a + k] = base[:-1] + chr(ord(base[-1]) + k) if base else ""
    return out


def _tex_tables() -> Dict[str, Dict[int, str]]:
    """TeX 的 Computer Modern 字型（沒有 ToUnicode）的字碼表：只列出和 ASCII 不同、或常出現在題目裡的字元。"""
    greek_up = dict(enumerate("ΓΔΘΛΞΠΣΥΦΨΩ"))
    ot1 = dict(greek_up)
    ot1.update({0x0B: "ff", 0x0C: "fi", 0x0D: "fl", 0x0E: "ffi", 0x0F: "ffl", 0x10: "ı", 0x11: "ȷ", 0x19: "ß", 0x1A: "æ", 0x1B: "œ", 0x1C: "ø",
                0x1D: "Æ", 0x1E: "Œ", 0x1F: "Ø", 0x22: "”", 0x27: "’", 0x3C: "¡", 0x3E: "¿", 0x5C: "“", 0x60: "‘", 0x7B: "–", 0x7C: "—"})
    tt = dict(greek_up)
    tt.update({0x0B: "ff", 0x0C: "fi", 0x0D: "fl", 0x0E: "ffi", 0x0F: "ffl"})
    mi = dict(greek_up)
    mi.update(dict(zip(range(0x0B, 0x28), "αβγδεζηθικλμνξπρστυφχψωεϑϖϱςφ")))
    mi.update({0x3A: ".", 0x3B: ",", 0x3C: "<", 0x3D: "/", 0x3E: ">", 0x3F: "⋆", 0x40: "∂", 0x60: "ℓ", 0x7D: "℘"})
    sy_syms = "−·×∗÷◇±∓⊕⊖⊗⊘⊙○∘•≍≡⊆⊇≤≥⪯⪰∼≈⊂⊃≪≫≺≻←→↑↓↔↗↙≃⇐⇒⇑⇓⇔↖↘∝′∞∈∋△▽/¬∅ℜℑ⊤⊥ℵ"
    sy = dict(enumerate(sy_syms[:0x40]))
    sy[0x36] = "/"
    sy[0x37] = "/"
    sy[0x38], sy[0x39] = "∀", "∃"
    sy.update({0x3A: "¬", 0x3B: "∅", 0x3C: "ℜ", 0x3D: "ℑ", 0x3E: "⊤", 0x3F: "⊥", 0x40: "ℵ"})
    sy.update({0x5B: "∪", 0x5C: "∩", 0x5D: "⊎", 0x5E: "∧", 0x5F: "∨", 0x60: "⊢", 0x61: "⊣", 0x62: "⌊", 0x63: "⌋", 0x64: "⌈", 0x65: "⌉", 0x66: "{", 0x67: "}",
               0x68: "⟨", 0x69: "⟩", 0x6A: "|", 0x6B: "‖", 0x6C: "↕", 0x6D: "⇕", 0x6E: "\\", 0x6F: "≀", 0x70: "√", 0x71: "⨿", 0x72: "∇", 0x73: "∫",
               0x74: "⊔", 0x75: "⊓", 0x76: "⊑", 0x77: "⊒", 0x78: "§", 0x79: "†", 0x7A: "‡", 0x7B: "¶", 0x7C: "♣", 0x7D: "♦", 0x7E: "♥", 0x7F: "♠"})
    sy.update({0x30: "′", 0x31: "∞", 0x32: "∈", 0x33: "∋", 0x34: "△", 0x35: "▽"})
    ex = {0x50: "∑", 0x51: "∏", 0x52: "∫", 0x58: "∑", 0x59: "∏", 0x5A: "∫", 0x70: "√", 0x71: "√", 0x72: "√", 0x73: "√", 0x00: "(", 0x01: ")", 0x02: "[", 0x03: "]"}
    return {"ot1": ot1, "tt": tt, "mi": mi, "sy": sy, "ex": ex}


_TEX = _tex_tables()


def tex_family(base_font: str) -> Optional[str]:
    name = re.sub(r"^[A-Z]{6}\+", "", base_font or "")
    m = re.match(r"^(CM[A-Z]+?)(\d*)$", name)
    if not m:
        return None
    fam = m.group(1)
    if fam == "CMMI":
        return "mi"
    if fam == "CMSY":
        return "sy"
    if fam == "CMEX":
        return "ex"
    if fam == "CMTT":
        return "tt"
    return "ot1"                                              # CMR／CMBX／CMTI／CMSSBX／CMSL／CMSS…


_AGL = {
    "space": " ", "exclam": "!", "quotedbl": '"', "numbersign": "#", "dollar": "$", "percent": "%", "ampersand": "&", "quotesingle": "'",
    "parenleft": "(", "parenright": ")", "asterisk": "*", "plus": "+", "comma": ",", "hyphen": "-", "minus": "−", "period": ".", "slash": "/",
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "colon": ":", "semicolon": ";", "less": "<", "equal": "=", "greater": ">", "question": "?", "at": "@",
    "bracketleft": "[", "backslash": "\\", "bracketright": "]", "asciicircum": "^", "underscore": "_", "grave": "`",
    "braceleft": "{", "bar": "|", "braceright": "}", "asciitilde": "~", "bullet": "•", "endash": "–", "emdash": "—",
    "quoteleft": "‘", "quoteright": "’", "quotedblleft": "“", "quotedblright": "”", "quotesinglbase": "‚", "quotedblbase": "„",
    "fi": "fi", "fl": "fl", "ff": "ff", "ffi": "ffi", "ffl": "ffl", "ellipsis": "…", "degree": "°", "multiply": "×", "divide": "÷",
    "plusminus": "±", "lessequal": "≤", "greaterequal": "≥", "notequal": "≠", "infinity": "∞", "summation": "∑", "product": "∏",
    "radical": "√", "periodcentered": "·", "section": "§", "dagger": "†", "daggerdbl": "‡", "paragraph": "¶", "copyright": "©",
    "registered": "®", "guillemotleft": "«", "guillemotright": "»", "exclamdown": "¡", "questiondown": "¿", "germandbls": "ß",
    "dotlessi": "ı", "nbspace": "\u00a0", "uni00A0": "\u00a0", "arrowright": "→", "arrowleft": "←", "element": "∈", "logicalnot": "¬",
}


def glyph_unicode(name: str) -> str:
    if name in _AGL:
        return _AGL[name]
    if len(name) == 1:
        return name
    m = re.fullmatch(r"uni([0-9A-Fa-f]{4})+", name)
    if m:
        return "".join(chr(int(name[i:i + 4], 16)) for i in range(3, len(name), 4))
    m = re.fullmatch(r"u([0-9A-Fa-f]{4,6})", name)
    if m:
        return chr(int(m.group(1), 16))
    return ""


class Font:
    def __init__(self, pdf: Pdf, fd: Dict[str, Any]):
        self.pdf = pdf
        sub = str(pdf.resolve(fd.get("Subtype")))
        self.base = str(pdf.resolve(fd.get("BaseFont")) or "")
        self.two_byte = sub == "Type0"
        self.uni: Dict[int, str] = {}
        tu = pdf.stream(fd.get("ToUnicode"))
        if tu:
            self.uni = parse_cmap(tu)
        self.dw = 1000.0
        self.w: Dict[int, float] = {}
        self.first = 0
        self.widths: List[float] = []
        self.missing = 0.0
        self.table: Optional[Dict[int, str]] = None
        self.enc: Dict[int, str] = {}
        if self.two_byte:
            desc = pdf.resolve(fd.get("DescendantFonts"))
            df = pdf.resolve(desc[0]) if isinstance(desc, list) and desc else {}
            self.dw = float(pdf.resolve(df.get("DW", 1000)))
            self._read_w(pdf.resolve(df.get("W")) or [])
            if not self.base:
                self.base = str(pdf.resolve(df.get("BaseFont")) or "")
        else:
            self.first = int(pdf.resolve(fd.get("FirstChar", 0)) or 0)
            self.widths = [float(pdf.resolve(x)) for x in (pdf.resolve(fd.get("Widths")) or [])]
            fdesc = pdf.resolve(fd.get("FontDescriptor"))
            if isinstance(fdesc, dict):
                self.missing = float(pdf.resolve(fdesc.get("MissingWidth", 0)) or 0)
            fam = tex_family(self.base)
            if fam:
                self.table = _TEX[fam]
            enc = pdf.resolve(fd.get("Encoding"))
            if isinstance(enc, dict):
                code = 0
                for it in pdf.resolve(enc.get("Differences")) or []:
                    it = pdf.resolve(it)
                    if isinstance(it, int):
                        code = it
                    elif isinstance(it, Name):
                        txt = glyph_unicode(str(it))
                        if txt:
                            self.enc[code] = txt
                        code += 1
        n = self.base.lower()
        self.mono = any(k in n for k in ("mono", "courier", "cmtt", "consolas", "typewriter"))

    def _read_w(self, arr: List[Any]) -> None:
        pdf, i = self.pdf, 0
        while i < len(arr):
            a = pdf.resolve(arr[i])
            b = pdf.resolve(arr[i + 1]) if i + 1 < len(arr) else None
            if isinstance(b, list):
                for k, w in enumerate(b):
                    self.w[int(a) + k] = float(pdf.resolve(w))
                i += 2
            elif i + 2 < len(arr):
                for c in range(int(a), int(b) + 1):
                    self.w[c] = float(pdf.resolve(arr[i + 2]))
                i += 3
            else:
                break

    def decode(self, s: bytes) -> List[Tuple[str, float]]:
        """字串 → [(文字, 寬度（千分之一個字級）)]。"""
        out: List[Tuple[str, float]] = []
        if self.two_byte:
            for k in range(0, len(s) - 1, 2):
                code = (s[k] << 8) | s[k + 1]
                out.append((self.uni.get(code, "�"), self.w.get(code, self.dw)))
            return out
        for code in s:
            if code in self.uni:
                ch = self.uni[code]
            elif code in self.enc:
                ch = self.enc[code]
            elif self.table is not None:
                ch = self.table.get(code) or (chr(code) if 0x20 <= code < 0x7F else "")
            else:
                ch = chr(code) if 0x20 <= code < 0x7F else (" " if code == 0xA0 else "")
            idx = code - self.first
            w = self.widths[idx] if 0 <= idx < len(self.widths) else self.missing
            out.append((ch, w))
        return out


# ---------- 內容串流 ----------
class Glyph:
    __slots__ = ("x", "y", "w", "size", "text", "mono")

    def __init__(self, x: float, y: float, w: float, size: float, text: str, mono: bool):
        self.x, self.y, self.w, self.size, self.text, self.mono = x, y, w, size, text, mono


def _mul(a: List[float], b: List[float]) -> List[float]:
    """矩陣乘法（列向量慣例：a 先、b 後）。矩陣是 [a b c d e f]。"""
    return [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3],
            a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
            a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]]


def interpret(pdf: Pdf, page: Dict[str, Any], fonts_cache: Dict[int, Font]) -> List[Glyph]:
    res = pdf.resolve(page.get("Resources")) or {}
    fdict = pdf.resolve(res.get("Font")) or {}
    contents = pdf.resolve(page.get("Contents"))
    parts = contents if isinstance(contents, list) else [page.get("Contents")]
    blobs = []
    for c in parts:
        b = pdf.stream(c)
        if b:
            blobs.append(b)
    data = b"\n".join(blobs)

    def font_for(name: str) -> Optional[Font]:
        ref = fdict.get(name)
        if ref is None:
            return None
        key = ref.num if isinstance(ref, Ref) else id(ref)
        if key not in fonts_cache:
            fd = pdf.resolve(ref)
            if not isinstance(fd, dict):
                return None
            fonts_cache[key] = Font(pdf, fd)
        return fonts_cache[key]

    glyphs: List[Glyph] = []
    ctm = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    stack: List[List[float]] = []
    tm = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    tlm = list(tm)
    font: Optional[Font] = None
    fsize = 0.0
    tc = tw = 0.0
    th = 1.0
    tl = 0.0
    rise = 0.0

    def show(s: bytes) -> None:
        nonlocal tm
        if font is None:
            return
        for ch, w1000 in font.decode(s):
            trm = _mul(_mul([fsize * th, 0.0, 0.0, fsize, 0.0, rise], tm), ctm)
            adv = (w1000 / 1000.0 * fsize + tc + (tw if ch == " " else 0.0)) * th
            if ch:
                glyphs.append(Glyph(trm[4], trm[5], w1000 / 1000.0 * math.hypot(trm[0], trm[1]), math.hypot(trm[2], trm[3]), ch, font.mono))
            tm = _mul([1.0, 0.0, 0.0, 1.0, adv, 0.0], tm)

    lx = Lexer(data)
    ops: List[Any] = []
    while True:
        try:
            tok = lx.token()
        except PdfTextError:
            break
        if tok is None:
            break
        if isinstance(tok, Kw) and tok not in (")", ">", "{", "}") and str(tok) not in ("true", "false", "null"):
            op = str(tok)
            a = ops
            ops = []
            try:
                if op == "q":
                    stack.append(list(ctm))
                elif op == "Q":
                    if stack:
                        ctm = stack.pop()
                elif op == "cm" and len(a) >= 6:
                    ctm = _mul([float(x) for x in a[-6:]], ctm)
                elif op == "BT":
                    tm = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
                    tlm = list(tm)
                elif op == "Tf" and len(a) >= 2:
                    font = font_for(str(a[-2]))
                    fsize = float(a[-1])
                elif op == "Tc" and a:
                    tc = float(a[-1])
                elif op == "Tw" and a:
                    tw = float(a[-1])
                elif op == "Tz" and a:
                    th = float(a[-1]) / 100.0
                elif op == "TL" and a:
                    tl = float(a[-1])
                elif op == "Ts" and a:
                    rise = float(a[-1])
                elif op in ("Td", "TD") and len(a) >= 2:
                    if op == "TD":
                        tl = -float(a[-1])
                    tlm = _mul([1.0, 0.0, 0.0, 1.0, float(a[-2]), float(a[-1])], tlm)
                    tm = list(tlm)
                elif op == "Tm" and len(a) >= 6:
                    tm = [float(x) for x in a[-6:]]
                    tlm = list(tm)
                elif op == "T*":
                    tlm = _mul([1.0, 0.0, 0.0, 1.0, 0.0, -tl], tlm)
                    tm = list(tlm)
                elif op in ("Tj", "'", '"') and a:
                    if op in ("'", '"'):
                        tlm = _mul([1.0, 0.0, 0.0, 1.0, 0.0, -tl], tlm)
                        tm = list(tlm)
                    if isinstance(a[-1], bytes):
                        show(a[-1])
                elif op == "TJ" and a and isinstance(a[-1], list):
                    for it in a[-1]:
                        if isinstance(it, bytes):
                            show(it)
                        elif isinstance(it, (int, float)):
                            tm = _mul([1.0, 0.0, 0.0, 1.0, -float(it) / 1000.0 * fsize * th, 0.0], tm)
                elif op == "BI":                              # 行內圖片：跳過
                    j = lx.d.find(b"ID", lx.i)
                    k = lx.d.find(b"EI", j + 2) if j >= 0 else -1
                    lx.i = (k + 2) if k >= 0 else len(lx.d)
            except (ValueError, TypeError, IndexError):
                pass
            continue
        if tok == "[" and not isinstance(tok, (bytes, Name)):
            ops.append(lx.value(tok))
        elif tok == "<<" and not isinstance(tok, (bytes, Name)):
            ops.append(lx.value(tok))
        else:
            ops.append(tok)
        if len(ops) > 64:
            ops = ops[-32:]
    return glyphs


# ---------- 版面：字 → 行 → 文字 ----------
class Line:
    __slots__ = ("text", "mono", "y", "x0", "size", "blank_before")

    def __init__(self, text: str, mono: bool, y: float, x0: float, size: float):
        self.text, self.mono, self.y, self.x0, self.size = text, mono, y, x0, size
        self.blank_before = 0

    def __repr__(self) -> str:
        return f"Line({self.text!r}, mono={self.mono}, blank_before={self.blank_before})"


def build_lines(glyphs: List[Glyph], scripts: bool = True) -> List[Line]:
    """依內容串流的順序把字組成行：y 差超過字級的 45% 就換行；同一行裡字距夠大才補空白。（空行與縮排見 apply_spacing）"""
    if not glyphs:
        return []
    rows: List[List[Glyph]] = []
    base_y = None
    base_size = 0.0
    for g in glyphs:
        if base_y is None or abs(g.y - base_y) > 0.45 * max(base_size, g.size):
            rows.append([g])
            base_y, base_size = g.y, g.size
        else:
            rows[-1].append(g)
            if g.size > base_size * 1.05:
                base_size = g.size
    lines: List[Line] = []
    for row in rows:
        size = max(g.size for g in row)
        main = [g for g in row if g.size >= 0.85 * size] or row
        base = sorted(g.y for g in main)[len(main) // 2]
        mono_w = sum(g.w for g in row if g.mono)
        mono = mono_w > 0.8 * (sum(g.w for g in row) or 1.0)
        cell = max((g.w for g in main if g.mono), default=0.0)
        out: List[str] = []
        prev: Optional[Glyph] = None
        script = ""                                           # 目前在上標("^")或下標("_")
        script_buf: List[str] = []

        def flush_script() -> None:
            nonlocal script, script_buf
            if script_buf:
                body = "".join(script_buf)
                out.append(script + (body if len(body) == 1 else "(" + body + ")"))
            script, script_buf = "", []

        for g in row:
            small = scripts and g.size < 0.85 * size
            kind = ""
            if small and g.y > base + 0.2 * size:
                kind = "^"
            elif small and g.y < base - 0.1 * size:
                kind = "_"
            if kind != script:
                flush_script()
            if prev is not None:
                gap = g.x - (prev.x + prev.w)
                unit = cell if (g.mono and prev.mono and cell > 0) else 0.0
                if unit:
                    n = int(gap / unit + 0.5)
                    if n >= 1:
                        (script_buf if kind else out).append(" " * n)
                elif gap > 0.14 * max(g.size, prev.size):
                    (script_buf if kind else out).append(" ")
            if kind:
                script = kind
                script_buf.append(g.text)
            else:
                out.append(g.text)
            prev = g
        flush_script()
        text = "".join(out).rstrip()
        lines.append(Line(text, mono, base, row[0].x, size))
    return lines


def apply_spacing(pages: List[List[Line]]) -> None:
    """行距 → 空行；等寬字行的縮排。行距用「整份文件」量（有的頁只有幾行，量不準）。
    等寬字（範例輸入輸出）：相鄰等寬行的最小行距就是一行，整數倍的間隔就是空行；一般文字：行距明顯變大才算段落間的空行。"""
    mono_gaps: List[float] = []
    prose_gaps: List[float] = []
    for lines in pages:
        for i in range(1, len(lines)):
            gap = lines[i - 1].y - lines[i].y
            if gap <= 0:
                continue
            if lines[i].mono and lines[i - 1].mono and gap > 0.5 * lines[i].size:
                mono_gaps.append(gap)
            elif not lines[i].mono and not lines[i - 1].mono and gap < 2.5 * lines[i].size:
                prose_gaps.append(gap)
    mono_pitch = min(mono_gaps) if mono_gaps else 0.0
    prose_gaps.sort()
    prose_pitch = prose_gaps[len(prose_gaps) // 2] if prose_gaps else 0.0
    for lines in pages:
        for i in range(1, len(lines)):
            gap = lines[i - 1].y - lines[i].y
            if gap <= 0:
                continue
            if lines[i].mono and lines[i - 1].mono and mono_pitch > 0:
                lines[i].blank_before = max(0, min(int(gap / mono_pitch + 0.5) - 1, 3))
            elif prose_pitch > 0 and gap > 1.35 * prose_pitch:
                lines[i].blank_before = 1
        mono_x = [ln.x0 for ln in lines if ln.mono and ln.text]
        if mono_x:
            left = min(mono_x)
            for ln in lines:
                if ln.mono and ln.text and ln.size:
                    k = int((ln.x0 - left) / (ln.size * 0.525) + 0.5)
                    if k > 0:
                        ln.text = " " * k + ln.text


def extract_pages(data: bytes, scripts: bool = True) -> List[List[Line]]:
    """PDF 的每一頁 → 行的清單。"""
    pdf = Pdf(data)
    pages = pdf.pages()
    if not pages:
        raise PdfTextError("找不到任何頁面")
    cache: Dict[int, Font] = {}
    out = [build_lines(interpret(pdf, p, cache), scripts) for p in pages]
    apply_spacing(out)
    if not any(ln.text for pg in out for ln in pg):
        raise PdfTextError("這個 PDF 裡沒有文字（可能是掃描的圖片）")
    return out


def extract_text(data: bytes, scripts: bool = True) -> str:
    """整份 PDF 的純文字（頁與頁之間直接接起來）。"""
    chunks: List[str] = []
    for pg in extract_pages(data, scripts):
        for ln in pg:
            chunks.extend([""] * ln.blank_before)
            chunks.append(ln.text)
        chunks.append("")
    return "\n".join(chunks)
