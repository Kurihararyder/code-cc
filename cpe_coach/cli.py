"""cpe 指令列介面。"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import bank as bank_mod
from . import course as course_mod
from . import hints, mock, roadmap, srs, stats
from .judge import AC, VERDICT_ZH, find_cases, judge, stress
from .llm import RULES, LLMError, detect_client
from .store import Workspace, WorkspaceError



# ---------- 小工具 ----------
def fmt_ts(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


def fmt_dur(sec: float) -> str:
    sec = int(max(sec, 0))
    h, m = divmod(sec // 60, 60)
    return f"{h} 小時 {m} 分" if h else f"{m} 分"


def start_date(ws: Workspace) -> dt.date:
    s = ws.config().get("start_date")
    return dt.date.fromisoformat(s) if s else dt.date.today()


def today_date(ws: Workspace) -> dt.date:
    return dt.date.fromtimestamp(ws.now())


def solution_file(ws: Workspace, pid: str, lang: Optional[str] = None) -> Path:
    """考試中的題目用考試檔；否則依 --lang 或最近修改的 .py/.cpp。"""
    exam = ws.exam()
    if exam and not lang:
        p = mock.solution_path(ws, exam, pid)
        if p:
            return p
    py, cpp = ws.solutions / f"{pid}.py", ws.solutions / f"{pid}.cpp"
    if lang:
        return cpp if lang == "cpp" else py
    existing = [f for f in (py, cpp) if f.exists()]
    return max(existing, key=lambda f: f.stat().st_mtime) if existing else py


def fail_path(ws: Workspace, pid: str) -> Path:
    return ws.meta / "last_fail" / f"{pid}.json"


def trunc(text: str, n: int = 400) -> str:
    text = text.rstrip()
    return text if len(text) <= n else text[:n] + f"\n…（共 {len(text)} 字元，已截斷）"


def effective_stage(ws: Workspace) -> int:
    return max(int(ws.config()["stage"]), 1)


# ---------- 指令 ----------
def cmd_init(args) -> int:
    root = Path(args.dir).resolve()
    d = args.start or dt.date.today().isoformat()
    dt.date.fromisoformat(d)
    ws = Workspace.create(root, d)
    print(f"已建立工作區：{ws.root}")
    print(f"  開始日期 {d}；解答放在 solutions/，測資放在 tests/<題號>/")
    print("  下一步：cd 進去，執行 cpe today")
    return 0


def cmd_roadmap(ws: Workspace, args) -> int:
    cfg, sd = ws.config(), start_date(ws)
    cur, exp = int(cfg["stage"]), roadmap.expected_stage(sd, today_date(ws))
    print(f"開始日期 {sd}　目前階段 {cur}　依時程表今天應在階段 {exp}")
    for s in roadmap.STAGES:
        mark = "▶" if s["n"] == cur else " "
        print(f"\n{mark} 階段 {s['n']}：{s['name']}（約 {s['hours']} 小時，目標 {roadmap.target_date(sd, s)} 前完成，CPE {s['cpe_goal']}）")
        print(f"    內容：{s['content']}")
        print(f"    練習：{s['practice']}")
        print(f"    檢核：{s['checkpoint']}")
    if cur < exp:
        print(f"\n⚠ 比時程落後 {exp - cur} 個階段。報告的提醒：卡在平台期延長 6–12 個月屬正常，重點是別斷掉。")
    print("\n（時數與月份為報告的經驗估計。每一場真實 CPE 都當作進度檢核。）")
    return 0


def cmd_stage(ws: Workspace, args) -> int:
    if not 0 <= args.n < len(roadmap.STAGES):
        raise ValueError("階段是 0–5")
    cfg = ws.config()
    cfg["stage"] = args.n
    ws.save_config(cfg)
    s = roadmap.STAGES[args.n]
    print(f"已設定目前階段：{args.n} {s['name']}\n本階段檢核點：{s['checkpoint']}")
    return 0


def suggestions(ws: Workspace, bank: Dict[str, dict], limit: int = 3) -> List[dict]:
    """目前單元的下一批練習題（先 drills，再真題）；單元沒有時退回依階段挑題。"""
    c = course_mod.load()
    u = course_mod.current_unit(ws, c)
    st = ws.state()

    def unsolved(pid: str) -> bool:
        sp = st["problems"].get(pid)
        return not (sp and sp["first_pass"] is not None)

    if u:
        _, todo = course_mod.unit_progress(ws, u)
        ids = todo + [a for a in u["anchors"] if unsolved(a)]
        out = [bank[i] for i in ids if i in bank]
        if out:
            return out[:limit]
    eff = effective_stage(ws)
    out = [p for p in bank.values() if p["stage"] <= eff and unsolved(p["id"]) and not p.get("drill")]
    out.sort(key=lambda p: (0 if p["stage"] == eff else 1, p["stage"], p["difficulty"], p.get("number", 0)))
    return out[:limit]


def show_problem(p: dict, hint_new: bool = True) -> None:
    star = "★" * int(p.get("difficulty", 1))
    print(f"  {p['id']:<10} {star:<5} {p['title']}　[{p.get('topic', '')}]")
    if p.get("drill") and hint_new:
        print(f"             cpe new {p['id']}　→ 題目與測資自動安裝")
    elif p.get("url"):
        print(f"             題目：{p['url']}（也可到瘋狂程設／UVA 找）")


def cmd_today(ws: Workspace, args) -> int:
    bank = bank_mod.load_bank(ws)
    st, now = ws.state(), ws.now()
    c = course_mod.load()
    u = course_mod.current_unit(ws, c)
    exam = ws.exam()
    if u:
        a, b = course_mod.week_range(u)
        wk = course_mod.expected_week(start_date(ws), today_date(ws))
        eu = course_mod.expected_unit(c, wk)
        print(f"📅 {today_date(ws)}　第 {wk} 週　你在：單元 {u['n']}《{u['title']}》（課表第 {a}{'' if a == b else '–' + str(b)} 週）")
        if eu["n"] > u["n"]:
            print(f"   ⚠ 依課表你現在應該在單元 {eu['n']}。落後不用慌，但別連續兩週沒練（卡住用 cpe hint，不要卡著不動）。")
        elif eu["n"] < u["n"]:
            print(f"   👍 你比課表快 {u['n'] - eu['n']} 個單元。")
    if exam:
        left = mock.remaining_seconds(exam, now)
        print(f"\n⏱ 考試進行中（{exam['kind']}），{'剩 ' + fmt_dur(left) if left > 0 else '時間到'}。題目：{', '.join(exam['problems'])}")
        print("  考試期間提示已鎖定。交卷：cpe mock finish")
        return 0
    due = srs.due_list(st, now)
    if due:
        print(f"\n🔁 到期重練 {len(due)} 題（從空白檔、不看提示重寫）：")
        for pid, _ in due:
            show_problem(bank_mod.resolve(bank, pid))
        print("  做法：cpe new <題號> --fresh，寫完 cpe test <題號>")
    if u:
        done, todo = course_mod.unit_progress(ws, u)
        print(f"\n📘 本單元必做 {len(done)}/{len(u['drills'])} 完成：")
        shown = 0
        for pid in todo[:3]:
            show_problem(bank_mod.resolve(bank, pid))
            shown += 1
        if not todo:
            print("  必做練習都完成了。")
            if u["anchors"]:
                print("  真題（選做）：" + "、".join(u["anchors"][:6]))
            if u["gate"]:
                print("  👉 準備好了就檢核：cpe gate")
            else:
                print("  這個單元的檢核是實際報考。完成後：cpe course next")
        print("  詳細內容：cpe course")
    solved = srs.counts(st)["solved"]
    if solved >= mock.WEEKLY_COUNT:
        ex = [e for e in ws.events() if e["kind"] == "exam_start" and e.get("exam_kind") == "weekly"]
        if not ex or now - ex[-1]["ts"] > 7 * 86400:
            print("\n📝 這週還沒做無 AI 測驗：cpe mock start --kind weekly")
    stage = int(ws.config()["stage"])
    open_eng = [t for t in roadmap.ENGINEERING if t["min_stage"] <= stage and t["n"] not in st["eng_done"]]
    if open_eng:
        print(f"\n🛠 工程能力（每週撥 20–30% 時間）：#{open_eng[0]['n']} {open_eng[0]['task']}")
    print("\n開始：cpe new <題號> → 寫程式 → cpe test <題號>。卡住再 cpe hint <題號>。")
    return 0


def cmd_next(ws: Workspace, args) -> int:
    bank = bank_mod.load_bank(ws)
    sug = suggestions(ws, bank, args.n)
    if not sug:
        print("沒有符合目前單元的未完成題目。")
    for p in sug:
        show_problem(p)
    return 0


def cmd_course(ws: Workspace, args) -> int:
    c = course_mod.load()
    bank = bank_mod.load_bank(ws)
    st = ws.state()
    if args.action == "list":
        cur = st["course"]["unit"]
        wk = course_mod.expected_week(start_date(ws), today_date(ws))
        print(f"今天是第 {wk} 週（依開始日期 {start_date(ws)}）")
        for u in c["units"]:
            a, b = course_mod.week_range(u)
            mark = "✓" if u["n"] in st["course"]["done"] else ("▶" if u["n"] == cur else " ")
            print(f"{mark} 單元{u['n']:>2}　第{a:>3}{'' if a == b else '–' + str(b):<4}週　階段{u['stage']}　{u['title']}")
        return 0
    if args.action == "goto":
        u = course_mod.goto(ws, c, args.n)
        print(f"已跳到單元 {u['n']}《{u['title']}》，之前的單元視為完成（階段 {u['stage']}）。")
        return 0
    if args.action == "next":
        u = course_mod.current_unit(ws, c)
        if not u:
            print("課程已經全部完成 🎓")
            return 0
        if u["gate"]:
            raise ValueError("這個單元要通過檢核才能前進：cpe gate。（已有把握可用 cpe course goto N 跳過）")
        nxt = course_mod.advance(ws, c, u["n"])
        print(f"完成單元 {u['n']}。" + (f"下一個：單元 {nxt['n']}《{nxt['title']}》" if nxt else "課程結束！"))
        return 0
    u = course_mod.get_unit(c, args.n) if args.n else course_mod.current_unit(ws, c)
    if not u:
        print("課程已經全部完成 🎓（cpe course list 查看全部單元）")
        return 0
    a, b = course_mod.week_range(u)
    print(f"單元 {u['n']}／{len(c['units'])}　《{u['title']}》　階段 {u['stage']}　第 {a}{'' if a == b else '–' + str(b)} 週" + ("　【C++】" if u["lang"] == "cpp" else ""))
    print(f"\n學完你能：{u['goal']}\n\n要學的：")
    for x in u["learn"]:
        print(f"  • {x}")
    if u["drills"]:
        done, todo = course_mod.unit_progress(ws, u)
        print(f"\n必做練習（{len(done)}/{len(u['drills'])}）：")
        for d in u["drills"]:
            p = bank_mod.resolve(bank, d)
            print(f"  {'✓' if d in done else ' '} {d}  {p['title']}　[{p.get('topic', '')}]")
    if u["anchors"]:
        print("\n真題（選做）：" + "、".join(u["anchors"]))
    for x in u["pool"]:
        print(f"延伸題庫：{x}")
    if u.get("read"):
        print("\n要讀的章節：")
        for x in u["read"]:
            print(f"  📖 {x}")
    if u["resources"]:
        print("\n教材：" + "；".join(f"{c['resources'][r]['name']} {c['resources'][r]['url']}" for r in u["resources"]))
    if u["pitfalls"]:
        print("\n常見陷阱：")
        for x in u["pitfalls"]:
            print(f"  ! {x}")
    if u["check"]:
        print("\n自我檢查（不看資料回答）：")
        for x in u["check"]:
            print(f"  ? {x}")
    g = u["gate"]
    if g:
        if g["type"] == "mock":
            print(f"\n檢核（cpe gate）：模擬考 {g['kind']}，至少答對 {g['need']} 題")
        else:
            print(f"\n檢核（cpe gate）：{g['minutes']} 分鐘、不看提示，{', '.join(g['problems'])} 至少答對 {g['need']} 題" + ("（C++）" if g["lang"] == "cpp" else ""))
    else:
        print("\n檢核：實際報考。完成後 cpe course next")
    return 0


def cmd_gate(ws: Workspace, args) -> int:
    c = course_mod.load()
    bank = bank_mod.load_bank(ws)
    u = course_mod.current_unit(ws, c)
    if not u:
        raise ValueError("課程已經全部完成")
    exam = course_mod.start_gate(ws, bank, c, u)
    print(f"單元 {u['n']} 檢核開始：{exam['minutes']} 分鐘，{len(exam['problems'])} 題，需答對 {exam['gate']['need']} 題。提示已鎖定。")
    for pid in exam["problems"]:
        show_problem(bank_mod.resolve(bank, pid), hint_new=False)
        print(f"             檔案：{exam['files'][pid]}　題目：cpe statement {pid}")
    print("寫完用 cpe test <題號>；交卷用 cpe mock finish。")
    return 0


def cmd_new(ws: Workspace, args) -> int:
    bank = bank_mod.load_bank(ws)
    f = solution_file(ws, args.id, args.lang or "py")
    if bank_mod.is_drill(args.id):
        bank_mod.install_drill(ws, args.id)
        print(f"題目：statements/{args.id}.md　（cpe statement {args.id} 可直接顯示）")
    elif args.id not in bank:
        print(f"（{args.id} 不在題庫，當作自訂題目。範例測資請用 cpe import 或 cpe addtest 加入）")
    ws.solutions.mkdir(exist_ok=True)
    if f.exists():
        if not args.fresh:
            raise ValueError(f"{f.name} 已存在。要從空白重寫請加 --fresh（舊檔會備份到 solutions/archive/）")
        arc = ws.solutions / "archive"
        arc.mkdir(exist_ok=True)
        shutil.move(str(f), str(arc / f"{f.stem}-{time.strftime('%Y%m%d%H%M%S', time.localtime(ws.now()))}{f.suffix}"))
    f.write_text(mock.template(args.lang or "py"), encoding="utf-8")
    (ws.tests / args.id).mkdir(parents=True, exist_ok=True)
    n = len(find_cases(ws.tests / args.id))
    print(f"已建立 {f.relative_to(ws.root)}（{n} 組測資）")
    if not n:
        print(f"請先加入題目的範例測資：cpe import {args.id} <題目文字檔>　或　cpe addtest {args.id}")
    return 0


def cmd_statement(ws: Workspace, args) -> int:
    f = ws.root / "statements" / f"{args.id}.md"
    if not f.exists() and bank_mod.is_drill(args.id):
        bank_mod.install_drill(ws, args.id)
    for ext in ("md", "txt"):
        f = ws.root / "statements" / f"{args.id}.{ext}"
        if f.exists():
            print(f.read_text(encoding="utf-8"))
            return 0
    raise ValueError(f"沒有 {args.id} 的題目敘述。外部題目請用 cpe import {args.id} <檔案> 存入")


SAMPLE_IN = re.compile(r"^\s*(?:#+\s*)?(?:sample\s+input|範例\s*輸入|輸入\s*範例|測試\s*輸入)\b.*$", re.I)
SAMPLE_OUT = re.compile(r"^\s*(?:#+\s*)?(?:sample\s+output|範例\s*輸出|輸出\s*範例|測試\s*輸出)\b.*$", re.I)


def parse_samples(text: str) -> List[tuple]:
    """從題目文字找出 (範例輸入, 範例輸出) 配對。支援 Sample Input/Output、範例輸入/輸出。"""
    marks = []
    lines_ = text.replace("\r\n", "\n").split("\n")
    for i, ln in enumerate(lines_):
        if SAMPLE_IN.match(ln):
            marks.append((i, "in"))
        elif SAMPLE_OUT.match(ln):
            marks.append((i, "out"))
    blocks = []
    for k, (i, kind) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines_)
        body = lines_[i + 1:end]
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        blocks.append((kind, "\n".join(body)))
    out, pending = [], None
    for kind, body in blocks:
        if kind == "in":
            pending = body
        elif pending is not None:
            out.append((pending, body))
            pending = None
    return out


def cmd_import(ws: Workspace, args) -> int:
    text = Path(args.file).read_text(encoding="utf-8")
    (ws.root / "statements").mkdir(exist_ok=True)
    (ws.root / "statements" / f"{args.id}.txt").write_text(text, encoding="utf-8")
    samples = parse_samples(text)
    if not samples:
        print(f"已存入 statements/{args.id}.txt，但找不到『Sample Input / 範例輸入』區塊。請改用 cpe addtest {args.id}")
        return 1
    for inp, out in samples:
        name = add_test(ws, args.id, inp, out)
        print(f"  加入 tests/{args.id}/{name}（輸入 {len(inp.splitlines())} 行／輸出 {len(out.splitlines())} 行）")
    print("請對照原題確認輸出沒有被多切或少切；範例通常只是『最基本』的測資，通過後還要自己補邊界測資。")
    return 0


def add_test(ws: Workspace, pid: str, inp: str, out: str) -> str:
    d = ws.tests / pid
    d.mkdir(parents=True, exist_ok=True)
    n = len(list(d.glob("*.in"))) + 1
    while (d / f"case{n:02d}.in").exists():
        n += 1
    name = f"case{n:02d}"
    (d / f"{name}.in").write_text(inp if inp.endswith("\n") else inp + "\n", encoding="utf-8")
    (d / f"{name}.out").write_text(out if out.endswith("\n") else out + "\n", encoding="utf-8")
    return name


def _read_block(prompt: str) -> str:
    print(prompt + "（貼完後單獨一行輸入 END）")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def cmd_addtest(ws: Workspace, args) -> int:
    if args.infile or args.outfile:
        if not (args.infile and args.outfile):
            raise ValueError("--in 和 --out 要一起給")
        inp = Path(args.infile).read_text(encoding="utf-8")
        out = Path(args.outfile).read_text(encoding="utf-8")
    else:
        inp, out = _read_block("貼上【輸入】"), _read_block("貼上【預期輸出】")
    name = add_test(ws, args.id, inp, out)
    print(f"已加入 tests/{args.id}/{name}")
    return 0


def cmd_test(ws: Workspace, args) -> int:
    pid = args.id
    sol = solution_file(ws, pid, args.lang)
    cfg = ws.config()
    res = judge(sol, ws.tests / pid, float(cfg["timeout_sec"]))
    if res.setup_error:
        print(f"✗ {res.message}")
        return 1

    for c in res.cases:
        mark = "✓" if c.verdict == AC else "✗"
        print(f"  {mark} {c.name:<12} {c.verdict:<4} {c.seconds:.2f}s")
    print(f"\n結果：{res.verdict} {VERDICT_ZH[res.verdict]}" + (f"（{res.message}）" if res.message else ""))
    f = res.failing
    if f:
        print(f"\n— 第一個失敗的測資 {f.name} —")
        print("輸入：\n" + trunc(f.input_text) + "\n預期輸出：\n" + trunc(f.expected) + "\n你的輸出：\n" + (trunc(f.actual) or "（空）"))
        if f.stderr.strip():
            print("錯誤訊息：\n" + trunc(f.stderr.strip().splitlines()[-1] if f.verdict == "RE" else f.stderr, 300))
        fp = fail_path(ws, pid)
        fp.parent.mkdir(exist_ok=True)
        fp.write_text(json.dumps({"verdict": f.verdict, "input": f.input_text, "expected": f.expected,
                                  "actual": f.actual, "stderr": f.stderr}, ensure_ascii=False), encoding="utf-8")
    elif fail_path(ws, pid).exists():
        fail_path(ws, pid).unlink()

    st = ws.state()
    p = ws.problem(st, pid)
    info = srs.record_result(p, res.verdict, ws.now())
    ws.save_state(st)
    ws.log("test", problem=pid, verdict=res.verdict, lang="cpp" if sol.suffix == ".cpp" else "py", **info)

    exam = ws.exam()
    if exam:
        note = mock.record(ws, exam, pid, res.verdict)
        if note:
            print("\n" + note)
    if res.verdict == AC:
        if info["mastered"]:
            print("\n🎉 精熟！這題已完成（無提示通過）。")
        elif info["advanced"]:
            print(f"\n🔁 重練通過！下次重練：{fmt_ts(p['review_due'])}")
        elif p["review_stage"] is not None and p["review_stage"] < srs.MASTERED:
            print(f"\n✔ 通過，但這題用了提示／看了解法，需要無提示重寫：{fmt_ts(p['review_due'])} 起")
    elif info["review_attempt"]:
        print("\n↩ 到期重寫沒通過，重練週期重新從 1 天後開始。")
    return 0 if res.verdict == AC else 1


def cmd_stress(ws: Workspace, args) -> int:
    sol = solution_file(ws, args.id)
    r = stress(sol, Path(args.brute), Path(args.gen), args.n)
    if r is None:
        print(f"✓ 對拍 {args.n} 組都一致。")
        return 0
    seed, inp, out_b, out_s, v = r
    name = add_test(ws, args.id, inp, out_b)
    print(f"✗ seed={seed} 不一致（{v}）。已存成 tests/{args.id}/{name}，之後 cpe test 會一起跑。")
    print("輸入：\n" + trunc(inp, 300) + "\n暴力解：\n" + trunc(out_b, 200) + "\n你的解：\n" + trunc(out_s, 200))
    return 1


def get_llm(ws: Workspace):
    return detect_client(ws.config())


def cmd_hint(ws: Workspace, args) -> int:
    bank = bank_mod.load_bank(ws)
    st = ws.state()
    p = ws.problem(st, args.id)
    level = args.level
    if level is None:
        level = 1 if p["hint_level"] < 0 else min(p["hint_level"] + 1, 4)
    sol = solution_file(ws, args.id)
    code = sol.read_text(encoding="utf-8") if sol.exists() else ""
    fp = fail_path(ws, args.id)
    failure = json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else None
    out = hints.request_hint(ws, args.id, level, bank_mod.resolve(bank, args.id), code, failure, get_llm(ws))
    print(f"【{hints.LEVEL_NAMES[level]}】{'（AI）' if out['source'] == 'llm' else ''}\n{out['text']}")
    if level >= 1:
        print("\n（這題之後通過會被列入『無提示重寫』名單。）")
    if level < 4:
        print(f"想要下一級？先改一版、cpe test 一次，再 cpe hint {args.id}")
    return 0


def cmd_giveup(ws: Workspace, args) -> int:
    unlock = hints.giveup(ws, args.id)
    print(f"已記錄放棄。解法在 {fmt_ts(unlock)} 之後才能用 cpe solution 看。")
    print("冷卻期間請做別的題，睡一覺再回來；看完解法後必須從空白檔無提示重寫。")
    return 0


def cmd_solution(ws: Workspace, args) -> int:
    st = ws.state()
    p = ws.problem(st, args.id)
    unlock = hints.solution_unlocked_at(p)
    if ws.exam_active():
        raise hints.HintDenied("考試進行中不能看解法")
    if unlock is None:
        raise hints.HintDenied(f"還沒放棄。真的卡住請先 cpe giveup {args.id}（冷卻 24 小時）")
    if ws.now() < unlock:
        raise hints.HintDenied(f"冷卻中，還要等 {fmt_dur(unlock - ws.now())}（{fmt_ts(unlock)} 解鎖）")
    bank = bank_mod.load_bank(ws)
    problem = bank_mod.resolve(bank, args.id)
    llm = get_llm(ws)
    sol = solution_file(ws, args.id)
    code = sol.read_text(encoding="utf-8") if sol.exists() else ""
    if llm is None:
        print("沒有設定 AI 金鑰。可以看這題的關鍵觀察，再去查社群題解：")
        print(f"  {problem.get('hint_insight') or '（此題沒有內建解說）'}")
    else:
        try:
            print(hints.explain_solution(problem, code, hints._statement(ws, args.id), llm))
        except LLMError as e:
            raise ValueError(f"AI 講解失敗：{e}")
    ws.log("solution_viewed", problem=args.id)
    print(f"\n接著：cpe new {args.id} --fresh，關掉解法，從空白檔重寫並通過 cpe test。")
    return 0


def cmd_review(ws: Workspace, args) -> int:
    bank = bank_mod.load_bank(ws)
    st, now = ws.state(), ws.now()
    due = srs.due_list(st, now)
    pending = [(pid, p) for pid, p in st["problems"].items() if srs.review_pending(p) and not srs.review_due(p, now)]
    if not due and not pending:
        print("沒有需要重練的題目 👍")
        return 0
    if due:
        print("到期：")
        for pid, p in due:
            show_problem(bank_mod.resolve(bank, pid))
    if pending:
        print("排程中：")
        for pid, p in sorted(pending, key=lambda kv: kv[1]["review_due"]):
            print(f"  {pid:<10} {fmt_ts(p['review_due'])}（第 {p['review_stage'] + 1}/3 次）")
    return 0


def cmd_mock(ws: Workspace, args) -> int:
    bank = bank_mod.load_bank(ws)
    now = ws.now()
    if args.action == "start":
        cap = max(int(ws.config()["stage"]), 1) if not args.all else 9
        avail = {pid: p for pid, p in bank.items() if bank_mod.is_drill(pid) or any((ws.tests / pid).glob("*.in"))}
        exam = mock.start(ws, avail, args.kind, lang=args.lang or "py", max_stage=cap)
        for pid in exam["problems"]:
            bank_mod.install_drill(ws, pid)
        print(f"考試開始：{args.kind}，{exam['minutes']} 分鐘，{len(exam['problems'])} 題。提示與看解法已鎖定。")
        for pid in exam["problems"]:
            show_problem(bank_mod.resolve(bank, pid), hint_new=False)
            print(f"             檔案：{exam['files'][pid]}　題目：cpe statement {pid}")
        print("寫完用 cpe test <題號>；交卷用 cpe mock finish。（只會出已有測資的題目：內建練習題，或你用 cpe import 加過的題）")
    elif args.action == "status":
        exam = ws.exam()
        if not exam:
            print("目前沒有進行中的考試。")
            return 0
        left = mock.remaining_seconds(exam, now)
        print(("剩餘 " + fmt_dur(left)) if left > 0 else "⏰ 時間到（之後的提交不計分）")
        for pid, r in exam["results"].items():
            state = f"✓ 第 {r['ac_min']} 分鐘" if r["ac_min"] is not None else "—"
            print(f"  {pid:<10} 錯 {r['wrong']} 次　{state}")
    else:
        s = mock.finish(ws)
        print(f"交卷：{s['kind']} 答對 {s['solved']}/{s['total']} 題，總罰時 {s['penalty']} 分鐘")
        msg = course_mod.evaluate_gate(ws, course_mod.load(), s)
        if msg:
            print(msg)
        print("考後檢討：沒解出的題目現在可以走提示階梯（cpe hint）。")
    return 0


def cmd_stats(ws: Workspace, args) -> int:
    s = stats.summarize(ws.state(), ws.events(), ws.now())
    c = s["counts"]
    print(f"已通過 {c['solved']} 題　精熟 {c['mastered']}　重練中 {c['reviewing']}")
    print(f"練習天數 {s['practice_days']}　連續 {s['streak']} 天")
    print(f"提交：本週 {s['attempts_week']} 次 / 累計 {s['attempts_total']} 次")
    print(f"  本週結果 {s['verdicts_week'] or '—'}")
    print(f"  累計結果 {s['verdicts_total'] or '—'}")
    ra = s["review_attempts"]
    rate = f"{s['review_clean_passes']}/{ra}（{100 * s['review_clean_passes'] // ra}%）" if ra else "—"
    print(f"無提示重寫通過率：{rate}　← 最重要的指標，比自我感覺可靠")
    print(f"提示使用：{s['hints_by_level'] or '—'}　放棄 {s['giveups']} 次　用外部 AI {s['external_ai']} 次")
    if s["exams"]:
        print("考試紀錄：")
        for e in s["exams"][-5:]:
            print(f"  {e['date']}  {e['kind']:<6} {e['solved']}/{e['total']} 題　罰時 {e['penalty']}")
    return 0


def cmd_add(ws: Workspace, args) -> int:
    p = {"id": args.id, "title": args.title or args.id, "source": "custom", "stage": args.stage,
         "difficulty": args.difficulty, "topic": args.topic or "", "hint_category": args.category,
         "hint_insight": args.insight, "url": args.url, "official_one_star": False}
    if args.accuracy is not None:
        p["official_accuracy"] = args.accuracy
    bank_mod.add_custom(ws, p)
    print(f"已加入／更新題庫：{args.id}")
    return 0


def cmd_bank(ws: Workspace, args) -> int:
    st = ws.state()
    items = [p for p in bank_mod.load_bank(ws).values() if args.stage is None or p["stage"] == args.stage]
    for p in sorted(items, key=lambda p: (p["stage"], p["difficulty"], p["id"])):
        sp = st["problems"].get(p["id"])
        mark = "✓" if sp and sp["first_pass"] is not None else " "
        print(f"{mark} 階段{p['stage']} {'★' * p['difficulty']:<5} {p['id']:<10} {p['title']}　[{p['topic']}]")
    return 0


def cmd_eng(ws: Workspace, args) -> int:
    st = ws.state()
    if args.done is not None:
        if args.done not in {t["n"] for t in roadmap.ENGINEERING}:
            raise ValueError("沒有這個編號")
        if args.done not in st["eng_done"]:
            st["eng_done"].append(args.done)
            ws.save_state(st)
        print(f"已標記完成 #{args.done}")
        return 0
    stage = int(ws.config()["stage"])
    for t in roadmap.ENGINEERING:
        mark = "✓" if t["n"] in st["eng_done"] else ("·" if t["min_stage"] <= stage else " ")
        print(f"{mark} #{t['n']:<2} （階段 {t['min_stage']}+）{t['task']}")
    print("\n完成後：cpe eng --done N")
    return 0


def cmd_external(ws: Workspace, args) -> int:
    ws.log("external_ai", problem=args.id)
    print("已記錄你用了外部 AI（誠實記錄比不用更重要）。這題建議之後無提示重寫。")
    return 0


def cmd_gpt_prompt(args) -> int:
    print(RULES)
    return 0


# ---------- 解析 ----------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="cpe", description="CPE 自學教練：本地判題、提示階梯、間隔重練、模擬考")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="建立工作區")
    s.add_argument("dir", nargs="?", default="cpe-workspace")
    s.add_argument("--start", help="開始日期 YYYY-MM-DD（預設今天）")

    s = sub.add_parser("course", help="課程：目前單元、全部單元、跳關")
    s.add_argument("action", nargs="?", default="show", choices=["show", "list", "next", "goto"])
    s.add_argument("n", nargs="?", type=int, help="單元編號（show／goto）")
    sub.add_parser("gate", help="開始目前單元的檢核")
    sub.add_parser("roadmap", help="顯示學習路線與各階段目標日期")
    s = sub.add_parser("stage", help="設定目前階段 0–5")
    s.add_argument("n", type=int)
    sub.add_parser("today", help="今天該做什麼")
    s = sub.add_parser("next", help="推薦下一題")
    s.add_argument("-n", type=int, default=3)

    s = sub.add_parser("new", help="建立解答檔（空白模板）；內建練習題會自動安裝題目與測資")
    s.add_argument("id")
    s.add_argument("--fresh", action="store_true", help="舊檔備份後從空白重寫")
    s.add_argument("--lang", choices=["py", "cpp"], help="語言（預設 py）")
    s = sub.add_parser("statement", help="顯示題目敘述")
    s.add_argument("id")
    s = sub.add_parser("import", help="從題目文字檔匯入敘述與範例測資（Sample Input/Output、範例輸入/輸出）")
    s.add_argument("id")
    s.add_argument("file")
    s = sub.add_parser("addtest", help="加入一組範例測資")
    s.add_argument("id")
    s.add_argument("--in", dest="infile")
    s.add_argument("--out", dest="outfile")
    s = sub.add_parser("test", help="本地判題")
    s.add_argument("id")
    s.add_argument("--lang", choices=["py", "cpp"], help="同時有 .py 與 .cpp 時指定")
    s = sub.add_parser("stress", help="對拍：暴力解 vs 你的解")
    s.add_argument("id")
    s.add_argument("--gen", required=True, help="產生器（以 seed 為 argv[1]）")
    s.add_argument("--brute", required=True, help="暴力解")
    s.add_argument("-n", type=int, default=200)

    s = sub.add_parser("hint", help="提示階梯 L0–L4")
    s.add_argument("id")
    s.add_argument("-l", "--level", type=int, choices=range(5), metavar="0-4")
    s = sub.add_parser("giveup", help="放棄這題（24 小時後才能看解法）")
    s.add_argument("id")
    s = sub.add_parser("solution", help="冷卻結束後看解法講解")
    s.add_argument("id")
    sub.add_parser("review", help="到期與排程中的重練")

    s = sub.add_parser("mock", help="模擬考／每週無 AI 測驗")
    s.add_argument("action", choices=["start", "status", "finish"])
    s.add_argument("--kind", choices=["mock", "short", "weekly"], default="mock",
                   help="mock=7 題 3 小時；short=3 題 90 分；weekly=重寫 3 題舊題 60 分")
    s.add_argument("--lang", choices=["py", "cpp"], help="考試檔語言")
    s.add_argument("--all", action="store_true", help="不限制階段（預設只出你學過階段的題目）")
    sub.add_parser("stats", help="學習統計")

    s = sub.add_parser("add", help="加入／更新自訂題目")
    s.add_argument("id")
    s.add_argument("--title")
    s.add_argument("--stage", type=int, default=1)
    s.add_argument("--difficulty", type=int, default=1, choices=range(1, 5))
    s.add_argument("--topic")
    s.add_argument("--category", help="L1 方向提示")
    s.add_argument("--insight", help="L2 關鍵觀察")
    s.add_argument("--url")
    s.add_argument("--accuracy", type=float, help="官方全體答對率（%%），當難度標籤")
    s = sub.add_parser("bank", help="列出題庫")
    s.add_argument("--stage", type=int)
    s = sub.add_parser("eng", help="工程能力清單")
    s.add_argument("--done", type=int)
    s = sub.add_parser("external", help="記錄你用了外部 AI（如 ChatGPT 網頁）")
    s.add_argument("id")
    sub.add_parser("gpt-prompt", help="印出可貼進 ChatGPT 自訂 GPT 的助教規則")
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "init":
            return cmd_init(args)
        if args.cmd == "gpt-prompt":
            return cmd_gpt_prompt(args)
        ws = Workspace.find()
        handler = {
            "course": cmd_course, "gate": cmd_gate, "statement": cmd_statement, "import": cmd_import,
            "roadmap": cmd_roadmap, "stage": cmd_stage, "today": cmd_today, "next": cmd_next, "new": cmd_new,
            "addtest": cmd_addtest, "test": cmd_test, "stress": cmd_stress, "hint": cmd_hint,
            "giveup": cmd_giveup, "solution": cmd_solution, "review": cmd_review, "mock": cmd_mock,
            "stats": cmd_stats, "add": cmd_add, "bank": cmd_bank, "eng": cmd_eng, "external": cmd_external,
        }[args.cmd]
        return handler(ws, args)
    except (WorkspaceError, hints.HintDenied, ValueError, RuntimeError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
