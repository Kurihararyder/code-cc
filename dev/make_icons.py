"""產生安裝精靈與捷徑用的圖示（icon.png／icon.ico／icon.icns），只用標準函式庫。
和網頁介面的圖示（cpe_coach/static/icon.svg）同一個設計：靛藍圓角方塊、白色的 <  / > 符號。
用法：python dev/make_icons.py     輸出到 cpe_coach/launcher/assets/
"""
import math
import struct
import sys
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "cpe_coach" / "launcher" / "assets"
TOP, BOTTOM = (99, 102, 241), (67, 56, 202)                 # #6366f1 → #4338ca
STROKES = [[(24, 22), (14, 32), (24, 42)], [(40, 22), (50, 32), (40, 42)], [(35, 17), (29, 47)]]
STROKE_W = 5.0
RADIUS = 14.0


def seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def rrect_sd(px, py, size, r):
    cx = cy = size / 2
    qx, qy = abs(px - cx) - (size / 2 - r), abs(py - cy) - (size / 2 - r)
    return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - r


def render(px_size):
    k = px_size / 64.0
    rows = []
    for y in range(px_size):
        row = bytearray()
        for x in range(px_size):
            ux, uy = (x + 0.5) / k, (y + 0.5) / k                   # 轉成 64×64 的座標
            cov = min(1.0, max(0.0, 0.5 - rrect_sd(ux, uy, 64, RADIUS) * k))
            if cov <= 0:
                row += b"\x00\x00\x00\x00"
                continue
            t = (ux + uy) / 128.0
            base = [TOP[i] + (BOTTOM[i] - TOP[i]) * t for i in range(3)]
            d = min(seg_dist(ux, uy, s[i], s[i + 1]) for s in STROKES for i in range(len(s) - 1))
            w = min(1.0, max(0.0, 0.5 - (d - STROKE_W / 2) * k))
            rgb = [base[i] + (255 - base[i]) * w for i in range(3)]
            row += bytes([round(rgb[0]), round(rgb[1]), round(rgb[2]), round(255 * cov)])
        rows.append(bytes(row))
    return rows


def png_bytes(px_size):
    rows = render(px_size)
    raw = b"".join(b"\x00" + r for r in rows)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", px_size, px_size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def ico_bytes(pngs):
    n = len(pngs)
    head = struct.pack("<HHH", 0, 1, n)
    entries, data, offset = b"", b"", 6 + 16 * n
    for size, png in pngs:
        entries += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(png), offset)
        data += png
        offset += len(png)
    return head + entries + data


def icns_bytes(items):
    body = b"".join(tag + struct.pack(">I", 8 + len(png)) + png for tag, png in items)
    return b"icns" + struct.pack(">I", 8 + len(body)) + body


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cache = {}

    def get(n):
        if n not in cache:
            cache[n] = png_bytes(n)
        return cache[n]
    (OUT / "icon.png").write_bytes(get(256))
    (OUT / "icon.ico").write_bytes(ico_bytes([(n, get(n)) for n in (16, 24, 32, 48, 64, 128, 256)]))
    (OUT / "icon.icns").write_bytes(icns_bytes([(b"ic07", get(128)), (b"ic08", get(256)), (b"ic09", get(512))]))
    print("已輸出：", ", ".join(f"{p.name} {p.stat().st_size // 1024} KB" for p in sorted(OUT.iterdir())))


if __name__ == "__main__":
    sys.exit(main())
