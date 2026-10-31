"""CPE 原題匯入：從 GitHub（或你已經下載好的資料夾／zip）把 PDF 轉成題目文字與範例測資。

題目敘述是 UVa 各題作者的著作，不內建在這個專案裡：這裡只負責在「你自己的電腦」上，把你要的 PDF 下載下來轉成學習用的文字。
"""
from __future__ import annotations

import io
import os
import re
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, List, NamedTuple, Optional, Tuple

from . import service, uvastatement
from .cpeset import DIR_TO_KEY, membership, pid_of
from .pastexams import has_statement, has_tests
from .store import Workspace

# 清單與驗證都是對這個提交做的；要換版本用環境變數 CPE_QUESTIONS_REF（分支、標籤或提交），或 CPE_QUESTIONS_URL（整個網址）
DEFAULT_REF = "6304e15d88a8fe46d875ca878a0ca831c08b4a25"
ARCHIVE_URL = "https://github.com/LuckyPigeon/CPE_Previous_Questions/archive/{ref}.zip"
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_PDF = 8 * 1024 * 1024


class CpeImportError(ValueError):
    pass


# ---------- 找出 PDF ----------
class Found(NamedTuple):
    number: int
    key: Optional[str]                     # one／two／past；不在這三個資料夾裡就是 None
    name: str
    read: Callable[[], bytes]


def _classify(rel: str) -> Optional[Tuple[Optional[str], int]]:
    """相對路徑 → (集合, UVA 題號)。檔名要是 <題號>.pdf；路徑上有 一星題／二星題／歷屆試題 就知道屬於哪個集合。"""
    parts = rel.replace("\\", "/").split("/")
    m = re.fullmatch(r"(\d{1,6})\.pdf", parts[-1], re.I)
    if not m:
        return None
    key = next((DIR_TO_KEY[p] for p in parts[:-1] if p in DIR_TO_KEY), None)
    return key, int(m.group(1))


def scan_folder(folder: Path) -> List[Found]:
    out: List[Found] = []
    folder = Path(folder)
    for f in sorted(folder.rglob("*.pdf")):
        if not f.is_file() or f.stat().st_size > MAX_PDF:
            continue
        c = _classify(str(f.relative_to(folder)))
        if c:
            out.append(Found(c[1], c[0], str(f.relative_to(folder)), lambda f=f: f.read_bytes()))
    return out


def scan_zip(blob: bytes) -> List[Found]:
    """只從 zip 讀出符合 <題號>.pdf 的檔案（在記憶體裡處理，不把任何東西解壓到硬碟；路徑穿越之類的檔名一律略過）。"""
    try:
        z = zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile:
        raise CpeImportError("下載到的不是正常的 zip 檔")
    out: List[Found] = []
    total = 0
    for info in z.infolist():
        name = info.filename
        if info.is_dir() or ".." in name.replace("\\", "/").split("/") or name.startswith(("/", "\\")):
            continue
        c = _classify(name)
        if not c or info.file_size > MAX_PDF:
            continue
        total += info.file_size
        if total > MAX_ARCHIVE:
            raise CpeImportError("壓縮檔裡的 PDF 總量超過上限")
        out.append(Found(c[1], c[0], name, lambda info=info: z.read(info)))
    return out


def download(ref: Optional[str] = None, url: Optional[str] = None, timeout: float = 60.0) -> bytes:
    ref = ref or os.environ.get("CPE_QUESTIONS_REF") or DEFAULT_REF
    url = url or os.environ.get("CPE_QUESTIONS_URL") or ARCHIVE_URL.format(ref=ref)
    req = urllib.request.Request(url, headers={"User-Agent": "cpe-coach"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read(MAX_ARCHIVE + 1)
    except (urllib.error.URLError, OSError) as e:
        raise CpeImportError(f"連不上 GitHub（{url}）：{getattr(e, 'reason', e)}。可以先自己下載那個 repo，再用『cpe past repo <資料夾>』匯入。")
    if len(data) > MAX_ARCHIVE:
        raise CpeImportError("下載的檔案太大，已中止")
    return data


# ---------- 匯入 ----------
class Report(NamedTuple):
    imported: List[Tuple[str, str, int]]       # (題號, 標題, 範例組數)
    skipped: List[str]                         # 已經有題目文字，沒有覆蓋
    no_samples: List[str]
    failed: List[Tuple[str, str]]              # (題號, 原因)
    missing: List[str]                         # 清單裡有、但找不到 PDF 的題


def import_found(ws: Workspace, found: List[Found], force: bool = False, keep_pdf: bool = True,
                 progress: Optional[Callable[[str, str], None]] = None) -> Report:
    imported: List[Tuple[str, str, int]] = []
    skipped: List[str] = []
    no_samples: List[str] = []
    failed: List[Tuple[str, str]] = []
    seen: set = set()
    for f in sorted(found, key=lambda x: (x.number, x.name)):
        pid = pid_of(f.number)
        if pid in seen:
            continue
        seen.add(pid)
        if not force and has_statement(ws, pid) and has_tests(ws, pid):
            skipped.append(pid)
            continue
        try:
            raw = f.read()
            st = uvastatement.from_pdf(raw)
            n = service.import_statement(ws, pid, st.text)
        except Exception as e:                                # 一份壞掉的 PDF 不該讓其他題跟著失敗
            failed.append((pid, str(e) or type(e).__name__))
            if progress:
                progress(pid, "失敗")
            continue
        if keep_pdf:
            (ws.root / "statements").mkdir(exist_ok=True)
            (ws.root / "statements" / f"{pid}.pdf").write_bytes(raw)
        if not n:
            no_samples.append(pid)
        imported.append((pid, st.title, n))
        if progress:
            progress(pid, f"{st.title}　範例 {n} 組")
    wanted = {pid_of(n) for n in membership()}
    missing = sorted(wanted - seen, key=lambda p: int(p[3:]))
    return Report(imported, skipped, no_samples, failed, missing)


def import_from(ws: Workspace, source: Optional[str] = None, force: bool = False,
                progress: Optional[Callable[[str, str], None]] = None) -> Report:
    """source：資料夾（例如把 repo clone 下來的位置）、.zip 檔，或不給（從 GitHub 下載）。"""
    if source:
        p = Path(source)
        if p.is_dir():
            found = scan_folder(p)
        elif p.is_file() and p.suffix.lower() == ".zip":
            found = scan_zip(p.read_bytes())
        else:
            raise CpeImportError(f"找不到資料夾或 zip 檔：{source}")
    else:
        found = scan_zip(download())
    if not found:
        raise CpeImportError("裡面沒有找到任何 <題號>.pdf。要給的是 CPE_Previous_Questions 的資料夾（裡面有 一星題／二星題／歷屆試題）。")
    return import_found(ws, found, force=force, progress=progress)
