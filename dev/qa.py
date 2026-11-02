"""出題品質檢查：每題都要通過下面所有檢查才算「審核過」。

  python dev/qa.py              檢查全部題目（約幾分鐘）
  python dev/qa.py d007 d060    只檢查指定的題目
  python dev/qa.py --quick      少跑幾輪隨機對拍（開發時用）

每題在 dev/qa_*.py 裡用 Q(...) 登記：
  brute  另寫的、和參考解不同做法的解（輸入文字 → 輸出文字）。參考解與它在大量隨機小資料上必須完全一致。
  gen    隨機產生「小」輸入的函式 gen(r)（r 是 random.Random）；對拍與額外測資都用它。
  valid  輸入檢查：每一筆測資都要符合題目寫的限制（範圍、格式、保證）。
  wrong  常見的錯誤解（pt(舊, 新) 是把參考解改一小段；code(原始碼) 是整份）。測資必須能抓出每一個。
  slow   正確但太慢的解。必須在時限內跑不完，否則這題的測資分不出快慢。
  big    產生大型輸入的函式 big(r)；放進測資裡專門抓效能。
另外檢查：參考解跑完所有測資的時間要遠低於時限、範例和第一筆測資一致、沒有重複的測資。
"""
from __future__ import annotations

import io
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))
from common import DRILLS  # noqa: E402

QA: Dict[str, dict] = {}
LIMIT = 3.0          # 和 cpe 本機判題的預設時限一致（秒）
MARGIN = bool(__import__("os").environ.get("QA_MARGIN"))      # 設成 1：慢解還要多跑一次，確認它比時限慢很多（本機驗證用，CI 不開）
REF_MAX = float(__import__("os").environ.get("QA_REF_MAX", "1.6"))         # 參考解（Python）在任何一筆測資上不應超過這個秒數，留給學習者的 Python 解答空間


def pt(old: str, new: str) -> dict:
    return {"patch": (old, new)}


def code(src: str, label: str = "") -> dict:
    return {"code": src, "label": label}


def Q(id: str, brute: Optional[Callable[[str], str]], gen: Callable[[random.Random], str], valid: Callable[[str], bool],
      wrong=(), slow=(), big=(), nrand: int = 6, rounds: int = 120, cpp: bool = False, space: int = 1000) -> None:
    assert id not in QA, f"{id} 重複登記"
    QA[id] = dict(brute=brute, gen=gen, valid=valid, wrong=list(wrong), slow=list(slow), big=list(big), nrand=nrand, rounds=rounds, cpp=cpp, space=space)


# ---------- 亂數小工具 ----------
def ints(r, n, lo, hi):
    return [r.randint(lo, hi) for _ in range(n)]


def sp(xs):
    return " ".join(map(str, xs))


def L(*xs):
    return "\n".join(str(x) for x in xs) + "\n"


def word(r, lo=1, hi=8, alpha="abcdefghijklmnopqrstuvwxyz"):
    return "".join(r.choice(alpha) for _ in range(r.randint(lo, hi)))


def toks(t):
    return t.split()


def nums(t):
    return [int(x) for x in t.split()]


def rows(t):
    return t.split("\n")


def inrange(xs, lo, hi):
    return all(lo <= x <= hi for x in xs)


# ---------- 執行 ----------
_REF: Dict[str, dict] = {}
_compiled: Dict[str, object] = {}


def load():
    """載入全部題目與 QA 登記。"""
    import drills_s0, drills_s1, drills_s2, drills_s3, drills_s4, drills_e  # noqa: F401
    try:
        import drills_n  # noqa: F401
    except ImportError:
        pass
    import qa_all  # noqa: F401
    _REF.update({d["id"]: d for d in DRILLS})


def run_inproc(src: str, text: str) -> str:
    """在本程序內跑一份解答（比開子程序快很多）。遇到不適合的寫法就丟例外，呼叫端改用子程序。"""
    c = _compiled.get(src)
    if c is None:
        c = _compiled[src] = compile(src, "<ref>", "exec")
    old_in, old_out = sys.stdin, sys.stdout
    sys.stdin = io.TextIOWrapper(io.BytesIO(text.encode()), encoding="utf-8", newline="")
    sys.stdout = buf = io.StringIO()
    try:
        exec(c, {"__name__": "__main__"})
    except SystemExit:
        pass
    finally:
        sys.stdin, sys.stdout = old_in, old_out
    return buf.getvalue()


def run_sub(src: str, text: str, timeout: float = LIMIT, suffix=".py"):
    """子程序跑，回傳 (輸出, 秒數, 狀態)；狀態 ok／tle／re。"""
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / ("sol" + suffix)
        f.write_text(src, encoding="utf-8")
        t0 = time.perf_counter()
        try:
            p = subprocess.run([sys.executable, "-I", str(f)], input=text.encode(), capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return "", time.perf_counter() - t0, "tle"
        dt = time.perf_counter() - t0
    if p.returncode != 0:
        return p.stdout.decode(errors="replace"), dt, "re"
    return p.stdout.decode(errors="replace"), dt, "ok"


def norm(t: str) -> List[str]:
    ls = [x.rstrip() for x in t.replace("\r\n", "\n").split("\n")]
    while ls and ls[-1] == "":
        ls.pop()
    return ls


class _Budget(Exception):
    pass


def with_budget(fn, seconds: float, *args):
    """在時間內算完才回傳；超過就回傳 None（獨立解通常很慢，遇到大一點的手寫測資就略過那一筆）。"""
    import signal

    def on_alarm(sig, frm):
        raise _Budget()

    old = signal.signal(signal.SIGALRM, on_alarm)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return fn(*args)
    except (_Budget, RecursionError):
        return None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def same(a: str, b: str) -> bool:
    return norm(a) == norm(b)


def fast(src: str, text: str) -> str:
    try:
        return run_inproc(src, text)
    except Exception:
        out, _, st = run_sub(src, text, 30)
        return out


# ---------- 額外測資 ----------
def extra_cases(id: str) -> List[str]:
    """除了手寫的測資之外要加進去的：隨機小測資（固定種子、不和已有的重複）與大測資。"""
    q = QA.get(id)
    if not q:
        return []
    d = _REF[id]
    seen = set(hand_cases(d))
    out = []
    for seed in range(1000, 1400):
        if len(out) >= q["nrand"]:
            break
        t = q["gen"](random.Random(seed))
        if t not in seen:
            seen.add(t)
            out.append(t)
    for i, b in enumerate(q["big"]):
        t = b(random.Random(5000 + i))
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


HAND_BIG = 60000      # 有登記 big 的題目，手寫的超大測資（超過這個字元數）改由 big 取代，避免同一種壓力測資重複出現、套件變得太大


def hand_cases(d) -> List[str]:
    hand = [c[0] if isinstance(c, tuple) else c for c in d["cases"]]
    q = QA.get(d["id"])
    if q and q["big"]:
        hand = [h for i, h in enumerate(hand) if i == 0 or len(h) <= HAND_BIG]
    return hand


def all_inputs(d) -> List[str]:
    return hand_cases(d) + extra_cases(d["id"])


# ---------- 檢查 ----------
def check(id: str, rounds: Optional[int] = None, verbose: bool = False) -> List[str]:
    d = _REF[id]
    q = QA.get(id)
    probs: List[str] = []
    if not q:
        return [f"{id}: 沒有登記 QA"]
    ref = d["ref"]
    inputs = all_inputs(d)
    # 1 測資數量、重複、範例
    if len(inputs) < min(8, q["space"]):
        probs.append(f"測資只有 {len(inputs)} 筆（至少 {min(8, q['space'])} 筆）")
    if len(set(inputs)) != len(inputs):
        probs.append("有重複的測資")
    if len(inputs[0]) > 500:
        probs.append("第一筆測資（會當範例顯示）太長")
    # 2 輸入符合限制
    for i, t in enumerate(inputs):
        try:
            ok = q["valid"](t)
        except Exception as e:
            ok = False
            probs.append(f"case{i+1:02d} 輸入檢查拋出 {type(e).__name__}: {e}")
        if not ok:
            probs.append(f"case{i+1:02d} 不符合題目寫的輸入限制")
    # 3 參考解跑得過、夠快
    expect: List[str] = []
    worst = 0.0
    for i, t in enumerate(inputs):
        out, dt, st = run_sub(ref, t, 120 if q["cpp"] else 20)
        expect.append(out)
        worst = max(worst, dt)
        if st != "ok":
            probs.append(f"參考解在 case{i+1:02d} {st}")
    if not q["cpp"] and worst > REF_MAX:
        probs.append(f"參考解最慢一筆 {worst:.2f}s（> {REF_MAX}s），學習者的 Python 解答可能過不了")
    # 4 對拍
    if q["brute"]:
        n = rounds if rounds is not None else q["rounds"]
        r = random.Random(20240601)
        small = [t for t, e in zip(inputs, expect) if len(t) <= 4000]
        for t in small:
            try:
                b = with_budget(q["brute"], 4.0, t)
            except Exception:                       # 手寫的大／極端測資有時不適合獨立解（例如 eval 的括號層數上限）
                continue
            if b is None:
                continue
            if not same(b, fast(ref, t)):
                probs.append(f"對拍：測資（{t[:60]!r}…）參考解與獨立解不一致")
                break
        for k in range(n):
            t = q["gen"](r)
            try:
                if not q["valid"](t):
                    probs.append(f"gen 產生不合法輸入：{t[:60]!r}")
                    break
            except Exception:
                probs.append(f"gen 產生的輸入檢查失敗：{t[:60]!r}")
                break
            a, b = fast(ref, t), q["brute"](t)
            if not same(a, b):
                probs.append(f"對拍不一致：輸入 {t[:80]!r}\n    參考解 {a[:60]!r}\n    獨立解 {b[:60]!r}")
                break
    else:
        probs.append("沒有獨立解（brute）")
    # 5 錯誤解要被抓到
    for w in q["wrong"]:
        if "patch" in w:
            old, new = w["patch"]
            if old not in ref:
                probs.append(f"pt 找不到要替換的片段：{old!r}")
                continue
            src, label = ref.replace(old, new, 1), f"{old!r}→{new!r}"
        else:
            src, label = w["code"], w.get("label") or w["code"][:30]
        killed = False
        for t, e in zip(inputs, expect):
            out, dt, st = run_sub(src, t, LIMIT)
            if st != "ok" or not same(out, e):
                killed = True
                break
        if not killed:
            hint = ""
            rr = random.Random(777)
            for _ in range(80):                      # 隨機小資料找得到的話，把那筆輸入附上，方便補成固定測資
                t = q["gen"](rr)
                out, dt, st = run_sub(src, t, LIMIT)
                if st != "ok" or not same(out, fast(ref, t)):
                    hint = f"（隨機資料抓得到，建議補這筆：{t[:70]!r}）"
                    break
            probs.append(f"錯誤解沒被測資抓到：{label}{hint}")
    # 6 慢解要超時
    for s in q["slow"]:
        src = s["code"] if "code" in s else ref.replace(*s["patch"], 1)
        killed = False
        for t in sorted(inputs, key=len, reverse=True):          # 從最大的輸入開始：最先超時的就是最重的那一筆
            out, dt, st = run_sub(src, t, LIMIT)
            if st != "ok":                       # 超時，或慢解的做法在大輸入下直接當掉（遞迴過深等）
                killed = True
                if st == "tle" and MARGIN:       # 邊際檢查：慢解不能只是『剛好』超過時限，換一台快一點的機器就過了
                    out2, dt2, st2 = run_sub(src, t, LIMIT * 3)
                    if st2 == "ok" and dt2 < LIMIT * 2:
                        probs.append(f"太慢的解只比時限多一點（{dt2:.1f}s，快一點的機器會過）：" + (s.get("label") or ""))
                break
        if not killed:
            probs.append("太慢的解沒有超時（測資分不出快慢）：" + (s.get("label") or ""))
    return probs


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")        # Windows 的預設編碼印不出 ✓／✗ 與中文
    except Exception:
        pass
    quick = "--quick" in argv
    load()
    ids = [a for a in argv if not a.startswith("--")] or [d["id"] for d in DRILLS]
    bad = 0
    t0 = time.time()
    for id in ids:
        probs = check(id, rounds=25 if quick else None)
        if probs:
            bad += 1
            print(f"✗ {id} {_REF[id]['title']}")
            for p in probs:
                print("   -", p)
        else:
            print(f"✓ {id} {_REF[id]['title']}")
        sys.stdout.flush()
    print(f"\n{len(ids) - bad}/{len(ids)} 題通過（{time.time() - t0:.0f} 秒）")
    return 1 if bad else 0


if __name__ == "__main__":
    import qa as _qa      # 以模組名稱 qa 執行，讓 qa_*.py 的 `from qa import Q` 登記到同一份 QA
    sys.exit(_qa.main(sys.argv[1:]))
