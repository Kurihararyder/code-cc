"""本地判題：跑解答、比對輸出、對拍。判對錯只看測資，不看任何 AI 的意見。"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

AC, WA, PE, TLE, RE, CE = "AC", "WA", "PE", "TLE", "RE", "CE"
VERDICT_ZH = {
    AC: "通過", WA: "答案錯誤", PE: "格式錯誤（內容對但空白／換行不同）",
    TLE: "超過時間", RE: "執行時錯誤", CE: "語法錯誤",
}
FAILS = (WA, PE, TLE, RE, CE)


@dataclass
class CaseResult:
    name: str
    verdict: str
    seconds: float = 0.0
    input_text: str = ""
    expected: str = ""
    actual: str = ""
    stderr: str = ""


@dataclass
class JudgeResult:
    verdict: str
    cases: List[CaseResult] = field(default_factory=list)
    message: str = ""
    setup_error: bool = False   # 缺解答檔／缺測資：不算一次提交

    @property
    def failing(self) -> Optional[CaseResult]:
        for c in self.cases:
            if c.verdict != AC:
                return c
        return None


def normalize(text: str) -> List[str]:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def compare(actual: str, expected: str) -> str:
    if normalize(actual) == normalize(expected):
        return AC
    if actual.split() == expected.split():
        return PE
    return WA


def syntax_error(path: Path) -> Optional[str]:
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as e:
        return f"第 {e.lineno} 行：{e.msg}"
    return None


def prepare(path: Path):
    """回傳 (指令列, 暫存目錄或 None, 錯誤訊息)。.cpp 會先編譯。"""
    if path.suffix != ".cpp":
        return [sys.executable, str(path)], None, None
    gxx = shutil.which("g++")
    if not gxx:
        return None, None, "找不到 g++。請先安裝（Linux/Mac 通常內建；Windows 可裝 MSYS2/MinGW），或改用 Python"
    tmp = Path(tempfile.mkdtemp(prefix="cpe-build-"))
    exe = tmp / "prog"
    p = subprocess.run([gxx, "-O2", "-std=c++17", "-o", str(exe), str(path)], capture_output=True, timeout=120)
    if p.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        err = p.stderr.decode("utf-8", "replace").strip().splitlines()
        return None, None, "編譯失敗：" + "\n".join(err[:6])
    return [str(exe)], tmp, None


def run_program(path: Path, stdin_text: str, timeout: float, cmd=None):
    start = time.perf_counter()
    try:
        proc = subprocess.run(cmd or [sys.executable, str(path)], input=stdin_text.encode("utf-8"),
                              capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        return None, (e.stdout or b"").decode("utf-8", "replace"), "", timeout, True
    elapsed = time.perf_counter() - start
    return (proc.returncode, proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"), elapsed, False)


def find_cases(tests_dir: Path):
    """tests/<id>/ 底下成對的 *.in / *.out。"""
    if not tests_dir.is_dir():
        return []
    return [(f, f.with_suffix(".out")) for f in sorted(tests_dir.glob("*.in")) if f.with_suffix(".out").exists()]


def judge(solution: Path, tests_dir: Path, timeout: float = 3.0) -> JudgeResult:
    if not solution.exists():
        return JudgeResult(CE, message=f"找不到解答檔 {solution}", setup_error=True)
    cases = find_cases(tests_dir)
    if solution.suffix == ".py":
        err = syntax_error(solution)
        if err:
            return JudgeResult(CE, message=err)
    if not cases:
        return JudgeResult(CE, message=f"{tests_dir} 沒有測資。先用 cpe addtest 或 cpe import 加入題目範例", setup_error=True)
    cmd, tmp, err = prepare(solution)
    if err:
        # 缺 g++ 是環境問題；編譯失敗才是一次提交
        return JudgeResult(CE, message=err, setup_error=err.startswith("找不到"))
    try:
        results: List[CaseResult] = []
        for fin, fout in cases:
            inp = fin.read_text(encoding="utf-8")
            exp = fout.read_text(encoding="utf-8")
            rc, out, err_text, secs, timed_out = run_program(solution, inp, timeout, cmd)
            if timed_out:
                v = TLE
            elif rc != 0:
                v = RE
            else:
                v = compare(out, exp)
            results.append(CaseResult(fin.stem, v, secs, inp, exp, out, err_text))
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    overall = next((c.verdict for c in results if c.verdict != AC), AC)
    return JudgeResult(overall, results)


def stress(solution: Path, brute: Path, gen: Path, rounds: int, timeout: float = 5.0, first_seed: int = 1):
    """對拍：gen 以 seed 為 argv[1] 產生輸入，比對正解與暴力解。回傳 (seed, input, brute_out, sol_out, verdict) 或 None。"""
    cmd_s, tmp_s, err_s = prepare(solution)
    cmd_b, tmp_b, err_b = prepare(brute)
    try:
        if err_s or err_b:
            raise RuntimeError(err_s or err_b)
        for seed in range(first_seed, first_seed + rounds):
            g = subprocess.run([sys.executable, str(gen), str(seed)], capture_output=True, timeout=timeout)
            if g.returncode != 0:
                raise RuntimeError(f"產生器失敗：{g.stderr.decode('utf-8', 'replace')[-300:]}")
            inp = g.stdout.decode("utf-8")
            rc_b, out_b, _, _, to_b = run_program(brute, inp, timeout, cmd_b)
            if to_b or rc_b != 0:
                raise RuntimeError("暴力解本身執行失敗或超時，請先修好暴力解")
            rc_s, out_s, _, _, to_s = run_program(solution, inp, timeout, cmd_s)
            if to_s:
                return seed, inp, out_b, out_s, TLE
            if rc_s != 0:
                return seed, inp, out_b, out_s, RE
            if out_s.split() != out_b.split():
                return seed, inp, out_b, out_s, WA
        return None
    finally:
        for t in (tmp_s, tmp_b):
            if t:
                shutil.rmtree(t, ignore_errors=True)
