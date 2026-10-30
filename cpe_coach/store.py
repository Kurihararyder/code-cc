"""工作區：狀態、事件紀錄、設定。全部存成純文字 JSON，方便備份與 git。"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

CPE_DIR = ".cpe"
DEFAULT_CONFIG: Dict[str, Any] = {
    "start_date": None,   # YYYY-MM-DD，init 時填入
    "stage": 0,           # 目前所在階段 0–5
    "timeout_sec": 3.0,   # 本地判題每筆測資時限
    "provider": None,     # openai / anthropic；None 代表依環境變數自動偵測
    "model": None,
}


class WorkspaceError(Exception):
    pass


class Workspace:
    def __init__(self, root: Path, clock: Callable[[], float] = time.time):
        self.root = Path(root)
        self.clock = clock

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
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    @staticmethod
    def _read(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

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
        if not self.events_path.exists():
            return []
        out = []
        for line in self.events_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out

    def problem(self, st: Dict[str, Any], pid: str) -> Dict[str, Any]:
        return st["problems"].setdefault(pid, new_problem_state())


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
