"""記憶模型：用 FSRS-4.5 的公式（穩定度 S、難度 D、可提取度 R）排程複習。

和原本 srs.py 的差別：srs.py 只管「靠提示才完成」的題（1／3／7 天無提示重寫）；這裡管**所有解出過的題**（包含一次就過的），
也以「知識點」為單位追蹤記憶。所有狀態都從事件紀錄（events.jsonl）重播算出，不另外存檔，所以備份、還原、多裝置合併都不會不一致。

誠實的限制：預設參數是 FSRS-4.5 公開的預設值（用大量 Anki 資料訓練），不是用「寫程式題」訓練的；
個人化只做一個參數 k（你比預設記得好或差），而且資料少於 10 次複習時不啟用（避免過度擬合）。
"""
from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Tuple

from . import concepts

W = [0.4872, 1.4003, 3.7145, 13.8206, 5.1618, 1.2298, 0.8975, 0.031, 1.6474, 0.1367, 1.0461, 2.1072, 0.0793, 0.3246, 1.587, 0.2272, 2.8755]
DECAY, FACTOR = -0.5, 19 / 81
DAY = 86400.0
MIN_GAP = 6 * 3600.0                 # 同一題 6 小時內的重複提交算同一次複習
AGAIN, HARD, GOOD, EASY = 1, 2, 3, 4
TARGET = 0.9                         # 目標保留率
MIN_REVIEWS_FOR_FIT = 10


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def retrievability(t_days: float, s: float) -> float:
    return (1 + FACTOR * max(t_days, 0.0) / s) ** DECAY


def interval_days(s: float, r: float = TARGET) -> float:
    return s / FACTOR * (r ** (1 / DECAY) - 1)


def init_stability(g: int) -> float:
    return max(W[g - 1], 0.1)


def init_difficulty(g: int) -> float:
    return _clamp(W[4] - W[5] * (g - 3), 1.0, 10.0)


def next_difficulty(d: float, g: int) -> float:
    nd = d - W[6] * (g - 3)
    return _clamp(W[7] * init_difficulty(3) + (1 - W[7]) * nd, 1.0, 10.0)


def stability_after_success(d: float, s: float, r: float, g: int) -> float:
    hard = W[15] if g == HARD else 1.0
    easy = W[16] if g == EASY else 1.0
    return s * (1 + math.exp(W[8]) * (11 - d) * s ** (-W[9]) * (math.exp(W[10] * (1 - r)) - 1) * hard * easy)


def stability_after_lapse(d: float, s: float, r: float) -> float:
    return min(s, W[11] * d ** (-W[12]) * ((s + 1) ** W[13] - 1) * math.exp(W[14] * (1 - r)))


class Card:
    __slots__ = ("s", "d", "last", "reps", "lapses", "log")

    def __init__(self) -> None:
        self.s = 0.0
        self.d = 0.0
        self.last = 0.0
        self.reps = 0
        self.lapses = 0
        self.log: List[Tuple[float, int, float]] = []          # (時間, 評分, 複習當下預測的 R)；第一次學習的 R 記 -1

    def r_at(self, now: float, k: float = 1.0) -> float:
        if self.reps == 0:
            return 0.0
        return _clamp(retrievability((now - self.last) / DAY, self.s), 0.0, 1.0) ** k

    def review(self, ts: float, g: int) -> float:
        """記錄一次複習，回傳複習當下的預測 R（第一次學習回傳 -1）。"""
        if self.reps == 0:
            self.s, self.d = init_stability(g), init_difficulty(g)
            r = -1.0
        else:
            r = retrievability((ts - self.last) / DAY, self.s)
            if g == AGAIN:
                self.s = max(0.1, stability_after_lapse(self.d, self.s, r))
                self.lapses += 1
            else:
                self.s = stability_after_success(self.d, self.s, r, g)
            self.d = next_difficulty(self.d, g)
        self.last = ts
        self.reps += 1
        self.log.append((ts, g, r))
        return r

    def due(self, k: float = 1.0, target: float = TARGET) -> float:
        """下次複習時間：預測保留率降到 target 的時候（k 是個人化修正，k<1 表示你比預設記得好）。"""
        return self.last + max(interval_days(self.s, target ** (1.0 / k)), 0.5) * DAY


def _grade(ev: Dict[str, Any], fails_before: int, first: bool) -> int:
    ok = ev.get("verdict") == "AC"
    if not ok:
        return AGAIN
    if not ev.get("clean", True):
        return HARD
    if first and fails_before == 0:
        return EASY
    return GOOD


class Replay(NamedTuple):
    cards: Dict[str, Card]
    concept_cards: Dict[str, Card]
    pairs: List[Tuple[float, int]]                      # (預測 R, 實際記得=1／忘了=0)，只含「複習」（不含第一次學習）


def replay(events: Iterable[Dict[str, Any]], bank: Optional[Dict[str, dict]] = None, concept_map: Optional[Dict[str, List[str]]] = None) -> Replay:
    cards: Dict[str, Card] = {}
    ccards: Dict[str, Card] = {}
    pairs: List[Tuple[float, int]] = []
    fails: Dict[str, int] = {}
    cmap = concept_map or {}
    for ev in events:
        if ev.get("kind") != "test" or not ev.get("problem") or ev.get("verdict") in (None, "SETUP"):
            continue
        pid, ts, ok = ev["problem"], float(ev["ts"]), ev["verdict"] == "AC"
        card = cards.get(pid)
        if card is None or card.reps == 0:
            if not ok:
                fails[pid] = fails.get(pid, 0) + 1                     # 還沒解出來之前的失敗：不是複習
                continue
            card = cards.setdefault(pid, Card())
            g = _grade(ev, fails.get(pid, 0), True)
            card.review(ts, g)
            fails[pid] = 0
            for c in _concepts(pid, bank, cmap):
                ccards.setdefault(c, Card()).review(ts, g)
            continue
        if ts - card.last < MIN_GAP:
            continue                                                   # 同一次練習的重複提交
        g = _grade(ev, 0, False)
        r = card.review(ts, g)
        pairs.append((r, 1 if g != AGAIN else 0))
        for c in _concepts(pid, bank, cmap):
            cc = ccards.setdefault(c, Card())
            if ts - cc.last >= MIN_GAP or cc.reps == 0:
                cc.review(ts, g)
    return Replay(cards, ccards, pairs)


def _concepts(pid: str, bank: Optional[Dict[str, dict]], cmap: Dict[str, List[str]]) -> List[str]:
    if pid in cmap:
        return cmap[pid]
    cs = concepts.of_problem(bank[pid]) if bank and pid in bank else ["loop"]
    cmap[pid] = cs
    return cs


# ---------- 個人化 ----------
class Fit(NamedTuple):
    k: float
    n: int
    enabled: bool
    loss_default: float
    loss_fit: float


def _logloss(pairs: List[Tuple[float, int]], k: float) -> float:
    tot = 0.0
    for r, y in pairs:
        p = _clamp(r ** k, 0.01, 0.99)
        tot -= math.log(p) if y else math.log(1 - p)
    return tot / max(len(pairs), 1)


def fit(pairs: List[Tuple[float, int]]) -> Fit:
    """只調一個參數 k（R' = R^k）：用「懲罰偏離 1」的最大概似，資料少時自然被拉回 1。複習次數太少（< 10）就不啟用。"""
    n = len(pairs)
    base = _logloss(pairs, 1.0) if n else 0.0
    if n < MIN_REVIEWS_FOR_FIT:
        return Fit(1.0, n, False, base, base)
    best_k, best = 1.0, float("inf")
    for i in range(-30, 31):
        k = math.exp(i * 0.04)                                          # k 從 0.30 到 3.3
        loss = _logloss(pairs, k) + (math.log(k) ** 2) * (6.0 / n)      # 資料越少，越不敢離開 1
        if loss < best:
            best_k, best = k, loss
    return Fit(best_k, n, True, base, _logloss(pairs, best_k))


# ---------- 對外 ----------
def build(ws, bank: Optional[Dict[str, dict]] = None) -> Tuple[Replay, Fit]:
    rp = replay(ws.events(), bank)
    return rp, fit(rp.pairs)


class DueItem(NamedTuple):
    pid: str
    r_now: float
    due_ts: float
    day: int                    # 平準後排在第幾天（0 = 今天）
    overdue_days: float


def schedule(cards: Dict[str, Card], now: float, k: float = 1.0, cap: int = 8, spread: int = 2) -> List[DueItem]:
    """所有題目的到期時間；平準：一天最多排 cap 題，超過的往後移最多 spread 天（越快忘的越先排）。"""
    raw = sorted(((c.due(k), pid, c) for pid, c in cards.items() if c.reps), key=lambda x: x[0])
    load: Dict[int, int] = {}
    out: List[DueItem] = []
    for due, pid, c in raw:
        day0 = max(0, int(math.floor((due - now) / DAY)))
        day = day0
        while load.get(day, 0) >= cap and day < day0 + spread:
            day += 1
        load[day] = load.get(day, 0) + 1
        out.append(DueItem(pid, c.r_at(now, k), due, day, max(0.0, (now - due) / DAY)))
    return out


def due_now(cards: Dict[str, Card], now: float, k: float = 1.0, cap: int = 8) -> List[DueItem]:
    return sorted([x for x in schedule(cards, now, k, cap) if x.day == 0 and x.due_ts <= now + 1], key=lambda x: x.r_now)


def forecast(cards: Dict[str, Card], now: float, days: int = 14, k: float = 1.0, cap: int = 8) -> List[int]:
    out = [0] * days
    for it in schedule(cards, now, k, cap):
        if it.day < days:
            out[it.day] += 1
    return out


def concept_report(ccards: Dict[str, Card], now: float, k: float = 1.0) -> List[Dict[str, Any]]:
    cs = concepts.load()
    rows = []
    for cid, c in ccards.items():
        if cid in cs:
            rows.append({"id": cid, "name": cs[cid]["name"], "retention": round(c.r_at(now, k), 3), "stability_days": round(c.s, 1), "reviews": c.reps, "lapses": c.lapses})
    return sorted(rows, key=lambda r: r["retention"])
