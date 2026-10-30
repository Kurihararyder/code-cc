"""本地判題：跑解答、比對輸出、對拍。判對錯只看測資，不看任何 AI 的意見。"""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, NamedTuple, Optional

AC, WA, PE, TLE, RE, CE, MLE = "AC", "WA", "PE", "TLE", "RE", "CE", "MLE"
VERDICT_ZH = {
    AC: "通過", WA: "答案錯誤", PE: "格式錯誤（內容對但空白／換行不同）",
    TLE: "超過時間", RE: "執行時錯誤", CE: "語法錯誤", MLE: "記憶體超過上限",
}
FAILS = (WA, PE, TLE, RE, CE, MLE)
DEFAULT_MEM_MB = 1024
OUT_LIMIT_MB = 32


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


class RunResult(NamedTuple):
    rc: Optional[int]
    out: str
    err: str
    elapsed: float
    timed_out: bool
    mle: bool = False
    ole: bool = False


# POSIX：在 exec 之前設定資源上限（不用 preexec_fn：多執行緒的網頁伺服器下不安全）。
_LAUNCH = (
    "import os,sys,resource\n"
    "m=int(sys.argv[1])*1048576; f=int(sys.argv[2])*1048576\n"
    "for k,v in ((resource.RLIMIT_AS,m),(resource.RLIMIT_FSIZE,f)):\n"
    "    try: resource.setrlimit(k,(v,v))\n"
    "    except Exception: pass\n"
    "os.execvp(sys.argv[3], sys.argv[3:])\n"
)


def _win_limit(proc, mem_mb: int) -> None:
    """Windows：用 Job Object 限制單一行程的記憶體（盡力而為；失敗就不限制）。尚未在真實 Windows 上驗證，見 CI。"""
    try:
        import ctypes
        from ctypes import wintypes as w

        class BASIC(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", w.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t),
                        ("ActiveProcessLimit", w.DWORD), ("Affinity", ctypes.c_size_t), ("PriorityClass", w.DWORD), ("SchedulingClass", w.DWORD)]

        class IOC(ctypes.Structure):
            _fields_ = [(n, ctypes.c_uint64) for n in ("ReadOps", "WriteOps", "OtherOps", "ReadBytes", "WriteBytes", "OtherBytes")]

        class EXT(ctypes.Structure):
            _fields_ = [("Basic", BASIC), ("Io", IOC), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]
        k32 = ctypes.windll.kernel32
        job = k32.CreateJobObjectW(None, None)
        info = EXT()
        info.Basic.LimitFlags = 0x100 | 0x2000          # PROCESS_MEMORY | KILL_ON_JOB_CLOSE
        info.ProcessMemoryLimit = mem_mb * 1048576
        k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
        k32.AssignProcessToJobObject(job, int(proc._handle))
        proc._cpe_job = job                              # 保持參照，行程結束後才關閉
    except Exception:
        pass


def _kill(proc) -> None:
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except (ProcessLookupError, PermissionError, OSError):
        pass


WATCH_RSS = sys.platform == "darwin"                  # macOS 不會執行 RLIMIT_AS：改用輪詢常駐記憶體


def _rss_mb(pid: int) -> float:
    """行程目前的常駐記憶體（MB）。macOS 沒有可用的 RLIMIT_AS，改用 ps 輪詢；失敗就當作 0。"""
    try:
        out = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], capture_output=True, text=True, timeout=2).stdout.strip()
        return int(out) / 1024.0 if out else 0.0
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0.0


def run_program(path: Path, stdin_text: str, timeout: float, cmd=None, mem_mb: int = DEFAULT_MEM_MB) -> RunResult:
    """在資源上限下執行：時間、記憶體（POSIX 用 RLIMIT_AS、Windows 用 Job Object）、輸出大小。
    輸出走暫存檔而不是管線，所以無窮輸出不會撐爆記憶體；超過上限就強制結束。"""
    cmd = list(cmd or [sys.executable, str(path)])
    cap = OUT_LIMIT_MB * 1048576
    with tempfile.TemporaryDirectory(prefix="cpe-run-") as d:
        fin, fout, ferr = Path(d) / "in", Path(d) / "out", Path(d) / "err"
        fin.write_bytes(stdin_text.encode("utf-8"))
        kw = {}
        if os.name == "posix":
            cmd = [sys.executable, "-c", _LAUNCH, str(mem_mb), str(OUT_LIMIT_MB)] + cmd
            kw["start_new_session"] = True
        else:
            kw["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        timed_out = ole = rss_kill = False
        watch_rss = WATCH_RSS
        next_rss = 0.0
        with open(fin, "rb") as si, open(fout, "wb") as so, open(ferr, "wb") as se:
            start = time.perf_counter()
            proc = subprocess.Popen(cmd, stdin=si, stdout=so, stderr=se, **kw)
            if os.name != "posix":
                _win_limit(proc, mem_mb)
            while True:
                try:
                    proc.wait(timeout=0.02)
                    break
                except subprocess.TimeoutExpired:
                    pass
                if time.perf_counter() - start > timeout:
                    timed_out = True
                    _kill(proc)
                    proc.wait()
                    break
                if fout.stat().st_size > cap:
                    ole = True
                    _kill(proc)
                    proc.wait()
                    break
                if watch_rss and time.perf_counter() >= next_rss:
                    next_rss = time.perf_counter() + 0.1
                    if _rss_mb(proc.pid) > mem_mb:
                        rss_kill = True
                        _kill(proc)
                        proc.wait()
                        break
            elapsed = time.perf_counter() - start
        rc = proc.returncode
        if fout.stat().st_size >= cap:                    # 寫到上限就被作業系統擋下（Python 會得到 OSError）
            ole = True
        with open(fout, "rb") as f:
            out = f.read(cap).decode("utf-8", "replace")
        with open(ferr, "rb") as f:
            err = f.read(65536).decode("utf-8", "replace")
    if os.name == "posix" and rc == -signal.SIGXFSZ:
        ole = True
    mle = rss_kill or (not timed_out) and rc not in (0, None) and ("MemoryError" in err or "bad_alloc" in err or "std::bad_alloc" in err)
    if ole:
        err = (err + "\n輸出超過 %d MB，已強制結束。" % OUT_LIMIT_MB).strip()
    return RunResult(None if timed_out else rc, out, err, timeout if timed_out else elapsed, timed_out, mle, ole)


def find_cases(tests_dir: Path):
    """tests/<id>/ 底下成對的 *.in / *.out。"""
    if not tests_dir.is_dir():
        return []
    return [(f, f.with_suffix(".out")) for f in sorted(tests_dir.glob("*.in")) if f.with_suffix(".out").exists()]


def judge(solution: Path, tests_dir: Path, timeout: float = 3.0, mem_mb: int = DEFAULT_MEM_MB) -> JudgeResult:
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
            r = run_program(solution, inp, timeout, cmd, mem_mb)
            if r.timed_out:
                v = TLE
            elif r.mle:
                v = MLE
            elif r.rc != 0:
                v = RE
            else:
                v = compare(r.out, exp)
            results.append(CaseResult(fin.stem, v, r.elapsed, inp, exp, r.out, r.err))
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
            rb = run_program(brute, inp, timeout, cmd_b)
            if rb.timed_out or rb.rc != 0:
                raise RuntimeError("暴力解本身執行失敗或超時，請先修好暴力解")
            rs = run_program(solution, inp, timeout, cmd_s)
            if rs.timed_out:
                return seed, inp, rb.out, rs.out, TLE
            if rs.mle:
                return seed, inp, rb.out, rs.out, MLE
            if rs.rc != 0:
                return seed, inp, rb.out, rs.out, RE
            if rs.out.split() != rb.out.split():
                return seed, inp, rb.out, rs.out, WA
        return None
    finally:
        for t in (tmp_s, tmp_b):
            if t:
                shutil.rmtree(t, ignore_errors=True)
