"""匯出與還原工作區（進度、解答、你匯入的題目與測資）。內建練習題的測資不備份，可由程式重新安裝。"""
from __future__ import annotations

import json
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import bank as bank_mod
from .store import CPE_DIR, Workspace, WorkspaceError

VERSION = 1
SKIP_META = {"backups", "last_fail", "lock", "trace_input.txt"}


def _files(ws: Workspace) -> List[Path]:
    out: List[Path] = []
    for f in sorted((ws.meta).rglob("*")):
        rel = f.relative_to(ws.meta)
        if f.is_file() and not (set(rel.parts) & SKIP_META) and f.suffix not in (".tmp",) and ".corrupt-" not in f.name:
            out.append(f)
    for top in ("solutions", "eng", "projects", "exam"):
        d = ws.root / top
        if d.is_dir():
            out += [f for f in sorted(d.rglob("*")) if f.is_file() and "__pycache__" not in f.parts]
    for top in ("tests", "statements"):
        d = ws.root / top
        if not d.is_dir():
            continue
        for item in sorted(d.iterdir()):
            pid = item.stem if top == "statements" else item.name
            if bank_mod.is_drill(pid):
                continue                      # 內建練習題：可重新安裝
            out += [f for f in sorted(item.rglob("*")) if f.is_file()] if item.is_dir() else [item]
    return out


def export_workspace(ws: Workspace, dest: Optional[Path] = None) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(ws.now()))
    dest = Path(dest) if dest else ws.root / f"cpe-backup-{stamp}.zip"
    files = _files(ws)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            if f.resolve() == dest.resolve():
                continue
            z.write(f, f.relative_to(ws.root).as_posix())
        z.writestr("backup.json", json.dumps({"version": VERSION, "created": stamp, "files": len(files)}, ensure_ascii=False))
    return dest


def export_bytes(ws: Workspace) -> bytes:
    import io
    buf = io.BytesIO()
    files = _files(ws)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.relative_to(ws.root).as_posix())
        z.writestr("backup.json", json.dumps({"version": VERSION, "files": len(files)}, ensure_ascii=False))
    return buf.getvalue()


def restore_workspace(zip_path: Path, dest: Path, force: bool = False) -> int:
    """還原到 dest。已有工作區時需要 force。拒絕任何會跑出 dest 的路徑。"""
    dest = Path(dest).resolve()
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise WorkspaceError(f"找不到備份檔 {zip_path}")
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        if f"{CPE_DIR}/state.json" not in names:
            raise WorkspaceError("這不是 cpe 的備份檔（缺少 .cpe/state.json）")
        if (dest / CPE_DIR).exists() and not force:
            raise WorkspaceError(f"{dest} 已經有工作區。要覆蓋請加 --force（舊的 .cpe 會先改名備份）。")
        for n in names:
            target = (dest / n).resolve()
            if dest != target and dest not in target.parents:
                raise WorkspaceError(f"備份檔包含不安全的路徑：{n}")
        if (dest / CPE_DIR).exists():
            (dest / CPE_DIR).rename(dest / f"{CPE_DIR}.before-restore-{int(time.time())}")
        dest.mkdir(parents=True, exist_ok=True)
        n_ok = 0
        for n in names:
            if n == "backup.json" or n.endswith("/"):
                continue
            t = dest / n
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_bytes(z.read(n))
            n_ok += 1
    return n_ok
