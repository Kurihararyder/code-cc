"""UVa 原題 PDF → 題目文字：去掉每頁的頁尾、把一般段落接成一行（網頁介面才不會被硬換行弄得很醜）、
等寬字的區塊（範例輸入輸出、格式示意）保留原本的換行與空行，最後交給 service.parse_samples 切出範例。

只處理 UVa 的格式（標題 "10010 Where's Waldorf?"、Input／Output／Sample Input／Sample Output 這幾個小標題）。
"""
from __future__ import annotations

import re
from typing import List, NamedTuple, Optional

from . import pdftext

FOOTER_RE = re.compile(r"^\s*Universidad de Valladolid OJ\b.*$")
TITLE_RE = re.compile(r"^\s*(\d{1,6})\s+(\S.*)$")
HEADING_RE = re.compile(r"^(Input|Output|Sample Input(?: ?\d+)?|Sample Output(?: ?\d+)?|Notes?|Explanation|Hints?|Constraints?|Example)\s*:?\s*$", re.I)
BAD_CHARS = {"￿": "–", "�": "–"}


class Statement(NamedTuple):
    number: Optional[int]
    title: str
    text: str
    has_figures: bool


def _lines(pages: List[List[pdftext.Line]]) -> List[tuple]:
    """攤平成 [(文字, 等寬?, 前面的空行數, 是不是頁首, 左邊界 x)]，頁尾已去掉。"""
    out = []
    for pg in pages:
        first = True
        for ln in pg:
            if FOOTER_RE.match(ln.text):
                continue
            for bad, good in BAD_CHARS.items():
                if bad in ln.text:
                    ln.text = ln.text.replace(bad, good)
            out.append((ln.text, ln.mono, 0 if first else ln.blank_before, first, ln.x0, ln.size))
            if ln.text:
                first = False
    return out


def build(pages: List[List[pdftext.Line]]) -> Statement:
    rows = _lines(pages)
    number: Optional[int] = None
    title = ""
    title_idx = -1
    for idx, (text, _mono, _blank, _first, _x, _size) in enumerate(rows):
        if text.strip():
            m = TITLE_RE.match(text)
            if m:
                number, title, title_idx = int(m.group(1)), m.group(2).strip(), idx
            break
    out: List[str] = []
    para: List[str] = []                                     # 目前這一段的各行；遇到空行、小標題或等寬區塊才接成一行

    def flush_para() -> None:
        if not para:
            return
        joined = para[0]
        for nxt in para[1:]:
            if joined.endswith("-") and joined[-2:-1].isalpha() and nxt[:1].islower():
                joined += nxt                                # 單字被連字號切在行尾：直接接上（連字號留著，不猜它是不是複合字）
            else:
                joined += " " + nxt
        out.append(joined)
        para.clear()

    def blank() -> None:
        flush_para()
        if out and out[-1] != "":
            out.append("")

    body = [round(r[4]) for r in rows if r[0].strip() and not r[1] and r[5] < 12.5]
    margin = max(set(body), key=body.count) if body else 0.0                       # 一般文字的左邊界（最常見的起點）；比它縮排進去的行 = 新段落的第一行
    in_mono = False
    for idx, (text, mono, blank_before, first, x0, size) in enumerate(rows):
        s = text.rstrip()
        if not s.strip():
            blank()
        elif idx == title_idx:
            out.append(s.strip())
            blank()
        elif HEADING_RE.match(s.strip()):
            blank()
            out.append(s.strip())
            blank()
            in_mono = False
        elif mono:
            if not in_mono:
                blank()
            in_mono = True
            if blank_before and not first:                   # 範例裡的空行（換頁時不算）
                out.extend([""] * blank_before)
            out.append(s)
        else:
            if in_mono:
                in_mono = False
                blank()
            elif (blank_before and not first) or x0 - margin > 0.8 * size:
                blank()
            para.append(s.strip())
    flush_para()
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip("\n") + "\n"
    return Statement(number, title, text, False)


def from_pdf(data: bytes) -> Statement:
    return build(pdftext.extract_pages(data))
