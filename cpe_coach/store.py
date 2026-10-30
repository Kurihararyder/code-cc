"""工作區：狀態、事件紀錄、設定。全部存成純文字 JSON，方便備份與 git。"""
from __future__ import annotations

import contextlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, Optional

CPE_DIR = ".cpe"
DEFAULT_CONFIG: Dict[str, Any] = {
    "start_date": None,   # YYYY-MM-DD，init 時填入
    "stage": 0,           # 目前所在階段 0–5
    "timeout_sec": 3.0,   # 本地判題每筆測資時限
    "memory_mb": 1024,    # 單一程式的記憶體上限（POSIX 用 RLIMIT_AS；macOS 不一定強制）
    "statement_lang": "auto",  # 內建練習題的題目語言：auto（階段 0 中文、階段 1 中英對照、之後英文）／zh／bi／en
    "provider": None,     # openai / anthropic；None 代表依環境變數自動偵測
    "model": None,
}


class WorkspaceError(Exception):
    pass


class _FileLock:
    """跨程序鎖（CLI 與網頁介面同時寫同一個工作區時，序列化讀改寫）。
    POSIX 用 flock；Windows 用 msvcrt.locking（兩者都在 CI 的 Linux／macOS／Windows 上跑過測試）。"""

    def __init__(self, path: Path, timeout: float = 30.0):
        self.path, self.timeout, self.fd = path, timeout, None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = open(self.path, "a+")
        deadline = time.time() + self.timeout
        while True:
            try:
                if os.name == "posix":
                    import fcntl
                    fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                else:
                    import msvcrt
                    self.fd.seek(0)
                    msvcrt.locking(self.fd.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                if time.time() > deadline:
                    self.fd.close()
                    self.fd = None
                    raise WorkspaceError("另一個 cpe 程序（例如網頁介面）正在寫入這個工作區，等了 %d 秒仍未釋放。請稍後再試。" % self.timeout)
                time.sleep(0.05)

    def release(self) -> None:
        if self.fd is None:
            return
        try:
            if os.name == "posix":
                import fcntl
                fcntl.flock(self.fd, fcntl.LOCK_UN)
            else:
                import msvcrt
                self.fd.seek(0)
                msvcrt.locking(self.fd.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            self.fd.close()
            self.fd = None


class Workspace:
    def __init__(self, root: Path, clock: Callable[[], float] = time.time):
        self.root = Path(root)
        self.clock = clock

    # ---- 鎖 ----
    @contextlib.contextmanager
    def lock(self, timeout: float = 30.0) -> Iterator[None]:
        """可重入（同一執行緒巢狀不會死鎖）。"""
        tl = self.__dict__.setdefault("_tl", threading.local())
        depth = getattr(tl, "depth", 0)
        if depth == 0:
            tl.flock = _FileLock(self.meta / "lock", timeout)
            tl.flock.acquire()
        tl.depth = depth + 1
        try:
            yield
        finally:
            tl.depth -= 1
            if tl.depth == 0:
                tl.flock.release()

    # ---- 位置 ----
    @property
    def meta(self) -> Path:
        return self.root / CPE_DIR

    @property
    def solutions(self) -> Path:
        return self.root / "solutions"

    @property
    def tests(self) -> Path:
        return self.root / "tests"

    @property
    def exam_dir(self) -> Path:
        return self.root / "exam"

    @classmethod
    def find(cls, start: Optional[Path] = None, clock: Callable[[], float] = time.time) -> "Workspace":
        env = os.environ.get("CPE_HOME")
        if env:
            p = Path(env)
            if (p / CPE_DIR).is_dir():
                return cls(p, clock)
            raise WorkspaceError(f"CPE_HOME={env} 不是有效的工作區（缺少 {CPE_DIR}/），請先 cpe init")
        cur = Path(start or Path.cwd()).resolve()
        for d in [cur, *cur.parents]:
            if (d / CPE_DIR).is_dir():
                return cls(d, clock)
        raise WorkspaceError("找不到工作區。請先執行：cpe init")

    @classmethod
    def create(cls, root: Path, start_date: str, clock: Callable[[], float] = time.time) -> "Workspace":
        ws = cls(root, clock)
        ws.meta.mkdir(parents=True, exist_ok=True)
        ws.solutions.mkdir(exist_ok=True)
        ws.tests.mkdir(exist_ok=True)
        if not ws.config_path.exists():
            cfg = dict(DEFAULT_CONFIG)
            cfg["start_date"] = start_date
            ws._write(ws.config_path, cfg)
        if not ws.state_path.exists():
            ws._write(ws.state_path, {"problems": {}, "eng_done": [], "exams": [], "course": {"unit": 1, "done": []}})
        return ws

    # ---- 檔案 ----
    @property
    def config_path(self) -> Path:
        return self.meta / "config.json"

    @property
    def state_path(self) -> Path:
        return self.meta / "state.json"

    @property
    def events_path(self) -> Path:
        return self.meta / "events.jsonl"

    @property
    def exam_path(self) -> Path:
        return self.meta / "exam.json"

    @property
    def custom_bank_path(self) -> Path:
        return self.meta / "custom_problems.json"

    @staticmethod
    def _write(path: Path, data: Any) -> None:
        """原子寫入；覆蓋前把舊檔留成 .bak，之後若檔案壞掉可以救回。"""
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        if path.exists():
            try:
                bak = path.with_suffix(path.suffix + ".bak")
                bak.write_bytes(path.read_bytes())
            except OSError:
                pass
        tmp.replace(path)

    @staticmethod
    def _read(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            bak = path.with_suffix(path.suffix + ".bak")
            if bak.exists():
                try:
                    data = json.loads(bak.read_text(encoding="utf-8"))
                    path.replace(path.with_suffix(path.suffix + ".corrupt-%d" % int(time.time())))
                    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    note = path.parent / "recovered.txt"
                    with note.open("a", encoding="utf-8") as f:
                        f.write("%s：%s 損壞，已用上一個版本（.bak）還原\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), path.name))
                    return data
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            raise WorkspaceError("%s 損壞而且沒有可用的備份。可以用 cpe restore 還原備份檔，或把它改名後重新開始。" % path)

    def snapshot_state(self, every: float = 3600.0, keep: int = 24) -> None:
        """每小時最多一份、保留最近 24 份的 state.json 快照。"""
        d = self.meta / "backups"
        d.mkdir(exist_ok=True)
        snaps = sorted(d.glob("state-*.json"))
        if snaps and time.time() - snaps[-1].stat().st_mtime < every:
            return
        if self.state_path.exists():
            (d / ("state-%s.json" % time.strftime("%Y%m%d-%H%M%S", time.localtime(self.now())))).write_bytes(self.state_path.read_bytes())
        for old in sorted(d.glob("state-*.json"))[:-keep]:
            old.unlink()

    # ---- 設定 / 狀態 ----
    def now(self) -> float:
        return self.clock()

    def config(self) -> Dict[str, Any]:
        cfg = dict(DEFAULT_CONFIG)
        cfg.update(self._read(self.config_path, {}))
        return cfg

    def save_config(self, cfg: Dict[str, Any]) -> None:
        self._write(self.config_path, cfg)

    def state(self) -> Dict[str, Any]:
        st = self._read(self.state_path, {})
        st.setdefault("problems", {})
        st.setdefault("eng_done", [])
        st.setdefault("exams", [])
        st.setdefault("course", {"unit": 1, "done": []})
        return st

    def save_state(self, st: Dict[str, Any]) -> None:
        self._write(self.state_path, st)
        try:
            self.snapshot_state()
        except OSError:
            pass

    # ---- 考試 ----
    def exam(self) -> Optional[Dict[str, Any]]:
        return self._read(self.exam_path, None)

    def save_exam(self, exam: Optional[Dict[str, Any]]) -> None:
        if exam is None:
            if self.exam_path.exists():
                self.exam_path.unlink()
        else:
            self._write(self.exam_path, exam)

    def exam_active(self) -> bool:
        return self.exam() is not None

    # ---- 事件 ----
    def log(self, kind: str, **fields: Any) -> Dict[str, Any]:
        ev = {"ts": self.now(), "kind": kind, **fields}
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        return ev

    def events(self) -> list:
        """讀取事件紀錄。用『已讀到哪個位元組』做增量快取：紀錄只會往後附加，所以每次只讀新增的部分。
        檔案被換掉、縮短或前後內容對不上（例如被還原／手動改過）就整份重讀。回傳的是新串列（事件字典本身共用，請勿修改）。"""
        p = self.events_path
        try:
            f = p.open("rb")
        except FileNotFoundError:
            return []
        with f:
            st = os.fstat(f.fileno())
            key = str(p)
            with _EVENT_LOCK:
                c = _EVENT_CACHE.get(key)
                if c is not None:
                    ok = c["id"] == (st.st_dev, st.st_ino) and st.st_size >= c["off"]
                    if ok and c["off"] > 0:
                        f.seek(0)
                        head = f.read(64)
                        f.seek(max(0, c["off"] - 64))
                        ok = head == c["head"] and f.read(min(64, c["off"])) == c["tail"]
                    if not ok:
                        c = None
                if c is None:
                    c = {"id": (st.st_dev, st.st_ino), "off": 0, "events": [], "head": b"", "tail": b""}
                f.seek(c["off"])
                data = f.read()
                end = data.rfind(b"\n")
                if end >= 0:
                    _parse_events(data[: end + 1], c["events"])
                    c["off"] += end + 1
                    f.seek(0)
                    c["head"] = f.read(64)
                    f.seek(max(0, c["off"] - 64))
                    c["tail"] = f.read(min(64, c["off"]))
                _EVENT_CACHE[key] = c
                out = list(c["events"])
                _parse_events(data[end + 1:], out)          # 還沒有換行結尾的最後一行：能解析就算，但不放進快取
                return out

    def problem(self, st: Dict[str, Any], pid: str) -> Dict[str, Any]:
        return st["problems"].setdefault(pid, new_problem_state())


_EVENT_CACHE: Dict[str, Dict[str, Any]] = {}
_EVENT_LOCK = threading.Lock()


def _parse_events(data: bytes, out: list) -> None:
    for line in data.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue                       # 寫到一半被中斷的行，略過即可
        if isinstance(obj, dict):
            out.append(obj)


def new_problem_state() -> Dict[str, Any]:
    return {
        "attempts": 0,
        "passes": 0,
        "first_pass": None,
        "last_pass": None,
        "last_verdict": None,
        "hint_level": -1,           # 這一輪用到的最高提示級別；-1 表示沒用過
        "attempts_since_hint": 0,   # 上次提示之後的提交次數
        "giveup_at": None,
        "dirty": False,             # 這一輪是否靠提示／放棄才完成
        "review_stage": None,       # None=尚未完成；0..2 重練進行中；3=已精熟
        "review_due": None,
    }
