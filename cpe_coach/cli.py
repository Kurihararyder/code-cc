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
from . import backup, calibrate, eng, hints, mock, pastexams, roadmap, service, srs, stats, vocab
from . import plan as plan_mod
from .service import add_test, fail_path, parse_samples, solution_file, trunc
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
    r = service.create_solution(ws, bank, args.id, args.lang or "py", args.fresh)
    if r["drill"]:
        print(f"題目：statements/{args.id}.md　（cpe statement {args.id} 可直接顯示）")
    if r["note"]:
        print(f"（{r['note']}）")
    print(f"已建立 {r['path'].relative_to(ws.root)}（{r['tests']} 組測資）")
    if not r["tests"]:
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


def cmd_import(ws: Workspace, args) -> int:
    text = service.read_statement_file(Path(args.file))
    n = service.import_statement(ws, args.id, text)
    if not n:
        print(f"已存入 statements/{args.id}.txt，但找不到『Sample Input / 範例輸入』區塊。請改用 cpe addtest {args.id}")
        return 1
    print(f"已存入 statements/{args.id}.txt，並建立 {n} 組範例測資（tests/{args.id}/sample*）。")
    print("請對照原題確認輸出沒有被多切或少切；範例通常只是『最基本』的測資，通過後還要自己補邊界測資。")
    return 0


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
    r = service.run_test(ws, pid, args.lang)
    if r["setup_error"]:
        print(f"✗ {r['message']}")
        return 1
    for c in r["cases"]:
        mark = "✓" if c["verdict"] == AC else "✗"
        print(f"  {mark} {c['name']:<12} {c['verdict']:<4} {c['seconds']:.2f}s")
    print(f"\n結果：{r['verdict']} {r['verdict_zh']}" + (f"（{r['message']}）" if r["message"] else ""))
    f = r["failing"]
    if f:
        print(f"\n— 第一個失敗的測資 {f['name']} —")
        print("輸入：\n" + trunc(f["input"]) + "\n預期輸出：\n" + trunc(f["expected"]) + "\n你的輸出：\n" + (trunc(f["actual"]) or "（空）"))
        if f["stderr"].strip():
            print("錯誤訊息：\n" + trunc(f["stderr"].strip().splitlines()[-1] if f["verdict"] == "RE" else f["stderr"], 300))
    if r["exam_note"]:
        print("\n" + r["exam_note"])
    info, rev = r["info"], r["review"]
    if r["verdict"] == AC:
        if info["mastered"]:
            print("\n🎉 精熟！這題已完成（無提示通過）。")
        elif info["advanced"]:
            print(f"\n🔁 重練通過！下次重練：{fmt_ts(rev['due'])}")
        elif rev["stage"] is not None and rev["stage"] < srs.MASTERED:
            print(f"\n✔ 通過，但這題用了提示／看了解法，需要無提示重寫：{fmt_ts(rev['due'])} 起")
    elif info["review_attempt"]:
        print("\n↩ 到期重寫沒通過，重練週期重新從 1 天後開始。")
    return 0 if r["verdict"] == AC else 1


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
    bank = bank_mod.load_bank(ws)
    sol = solution_file(ws, args.id)
    code = sol.read_text(encoding="utf-8") if sol.exists() else ""
    r = hints.solution_text(ws, args.id, bank_mod.resolve(bank, args.id), code, get_llm(ws))
    print(r["text"])
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
        exam = course_mod.start_mock(ws, bank, args.kind, args.lang or "py", args.all, args.real)
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
        print_board(mock.scoreboard(exam, bank, pastexams.load_all(ws)["distribution"]))
    else:
        s = mock.finish(ws, pastexams.load_all(ws)["distribution"])
        print(f"交卷：{s['kind']} 答對 {s['solved']}/{s['total']} 題，總罰時 {s['penalty']} 分鐘")
        if s.get("percentile"):
            pc = s["percentile"]
            print(f"參考：歷年（2015–2024）考生中，答對 ≥ {s['solved']} 題的約 {pc['top']}%，你超過約 {pc['beats']}% 的考生。")
            print("（這只是粗略對照：資料是社群彙整的累計分布，你的條件與真實考場不同。）")
        msg = course_mod.evaluate_gate(ws, course_mod.load(), s)
        if msg:
            print(msg)
        print("考後檢討：沒解出的題目現在可以走提示階梯（cpe hint）。")
    return 0


def print_board(b) -> None:
    print(f"\n計分板：{b['solved']}/{b['total']} 題　罰時 {b['penalty']} 分鐘（錯誤共 {b['wrong']} 次）")
    for r in b["rows"]:
        mark = {"ac": f"✓ 第 {r['ac_min']} 分鐘" + (f"（錯 {r['wrong']}）" if r["wrong"] else ""), "wrong": f"✗ 錯 {r['wrong']} 次", "open": "—"}[r["status"]]
        acc = f"　全國 {r['accuracy']}%" if r["accuracy"] is not None else ""
        print(f"  {r['order']}. {r['id']:<18} {r['title'][:28]:<28} {mark}{acc}")
    if b.get("percentile"):
        print(f"  以目前題數對照歷年分布：前 {b['percentile']['top']}%")


def cmd_past(ws: Workspace, args) -> int:
    bank = bank_mod.load_bank(ws)
    data = pastexams.load_all(ws)
    if args.action == "list":
        for e in reversed(pastexams.list_exams(ws, bank)["exams"]):
            avg = f"　平均答對 {e['avg_solved']}" if e["avg_solved"] is not None else ""
            print(f"{e['date']}　{e['count']} 題（有測資 {e['ready']}／已通過 {e['solved']}）{avg}" + ("　✔可出整場" if e["complete"] else ""))
        print("\n匯入格式：cpe past template；匯入題目：cpe past statements <資料夾>")
    elif args.action == "template":
        print(pastexams.FORMAT_HELP)
    elif args.action == "import":
        r = pastexams.import_manifest(ws, Path(args.arg).read_text(encoding="utf-8"))
        print(f"已匯入 {r['exams']} 場、{r['problems']} 題。")
        for e in r["errors"]:
            print("  略過：" + e)
    elif args.action == "show":
        e = next((x for x in pastexams.list_exams(ws, bank)["exams"] if x["date"] == args.arg), None)
        if not e:
            raise ValueError(f"沒有 {args.arg} 這場。cpe past list 看全部。")
        for p in e["problems"]:
            flag = ("✓" if p["solved"] else " ") + ("T" if p["has_tests"] else "-") + ("S" if p["has_statement"] else "-")
            print(f"{p['order']}. [{flag}] {p['id']:<18} {p['title']:<30} {'★' * (p['stars'] or 0):<5} {p['accuracy'] if p['accuracy'] is not None else '?'}%")
        print("\n[已通過/有測資(T)/有題目文字(S)]；整場模擬：cpe past start " + e["date"])
    elif args.action == "statements":
        folder = Path(args.arg)
        n_files = n_samples = 0
        for f in sorted(folder.iterdir()):
            m = re.match(r"^(?:uva)?[-_ ]?(\d+)\b.*\.(txt|md|html?)$", f.name, re.I)
            if not m:
                continue
            pid = f"uva{int(m.group(1))}"
            k = service.import_statement(ws, pid, service.read_statement_file(f))
            n_files += 1
            n_samples += k
            print(f"  {pid:<10} {f.name}　範例 {k} 組" + ("" if k else "　⚠ 找不到 Sample Input／Output，請用 cpe addtest 補"))
        print(f"\n處理 {n_files} 個檔案，共建立 {n_samples} 組範例測資。檔名格式：10050.txt、uva10050.html …")
    elif args.action == "start":
        exam = course_mod.start_past(ws, bank, args.arg, args.lang or "py", args.partial)
        print(f"歷屆整場開始：{args.arg}，{exam['minutes']} 分鐘，{len(exam['problems'])} 題。AI 與提示已鎖定。")
        for pid in exam["problems"]:
            show_problem(bank_mod.resolve(bank, pid), hint_new=False)
            print(f"             檔案：{exam['files'][pid]}　題目：cpe statement {pid}")
        print("寫完用 cpe test <題號>；cpe mock status 看計分板；cpe mock finish 交卷。")
    return 0


def cmd_vocab(ws: Workspace, args) -> int:
    if args.action == "export":
        print(vocab.to_csv(ws), end="")
        return 0
    if args.action == "add":
        r = vocab.add(ws, args.word)
        print(f"已加入：{r['word']}（第 {r['count']} 次查）　{r['url']}")
        return 0
    its = vocab.items(ws)
    if not its:
        print("生字本是空的。在網頁介面讀英文題目時選一個單字 → 查字典，就會自動記下來。")
    for it in its:
        print(f"{it['word']:<18} ×{it['count']}  {' '.join(it['problems'])}")
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
    if s["predict_total"]:
        print(f"提交前預測準確度：{s['predict_correct']}/{s['predict_total']}（{100 * s['predict_correct'] // s['predict_total']}%）← 越準，代表你越懂自己的程式")
    if s["asks"]:
        print(f"網頁 AI 詢問：{s['asks']} 次（引用全數通過驗證 {s['asks_verified']} 次）")
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
    action = args.action
    if action in ("start", "verify") and args.n is None:
        raise ValueError(f"請指定任務編號：cpe eng {action} N")
    if action == "start":
        made = eng.start(ws, args.n)
        t = next(x for x in eng.tasks(ws) if x["n"] == args.n)
        print(f"#{t['n']} {t['title']}　[{t['kind_zh']}]")
        for rel in made:
            print(f"  建立 {rel}")
        if not made and t["has_scaffold"]:
            print("  範本檔已存在，沒有覆蓋。")
        print(f"\n做完後驗收：cpe eng verify {t['n']}" + ("  --evidence <網址>" if t["kind"] == "manual" else ""))
        return 0
    if action == "verify":
        r = eng.verify(ws, args.n, args.evidence)
        for x in r["results"]:
            print(f"  {'✓' if x['ok'] else '✗'} {x['label']}" + (f"\n      {x['msg']}" if x["msg"] and not x["ok"] else ""))
        print("\n" + (f"✅ 任務 #{args.n} 通過驗收" if r["ok"] else f"還沒過。修好後再 cpe eng verify {args.n}"))
        return 0 if r["ok"] else 1
    stage = int(ws.config()["stage"])
    for t in eng.tasks(ws):
        mark = "✓" if t["done"] else ("·" if t["min_stage"] <= stage else " ")
        print(f"{mark} #{t['n']:<2} （階段 {t['min_stage']}+）{t['title']}　[{t['kind_zh']}]")
    print("\n開始：cpe eng start N　　驗收：cpe eng verify N（通過才會標記完成）")
    return 0


def cmd_plan(ws: Workspace, args) -> int:
    p = plan_mod.build(ws, args.minutes)
    print(f"📋 {p['date']} 今天 {p['minutes']} 分鐘" + ("" if p.get("calibrated", True) else "（預估時間用預設值；解完 3 題後會依你的速度調整）"))
    if not p["items"]:
        print("  今天沒有必做的事。可以自由挑一題，或複習已解過的題。")
    for i, it in enumerate(p["items"], 1):
        ref = f" {it['id']}" if it["id"] else ""
        print(f"  {'✓' if it['done'] else str(i) + '.'} [{plan_mod.KIND_ZH[it['kind']]}]{ref} {it['title']}　~{it['est']} 分　{it['why']}")
    print(f"\n合計約 {p['total_est']} 分鐘。")
    for it in p["later"]:
        print(f"  另外安排：{it['title']}（{it['est']} 分）— {it['why']}")
    return 0


def cmd_calibrate(ws: Workspace, args) -> int:
    c = calibrate.calibrate(ws, bank_mod.load_bank(ws))
    if not c["rows"]:
        print("還沒有解出的題目。每解出一題，我會記下你花的時間、嘗試次數與提示次數。")
        return 0
    print(f"已解 {c['solved']} 題；你的速度係數 ×{c['factor']}（1.0 = 和預設時間一樣快；小於 1 表示比預設快）。{c['note']}")
    for s, v in c["by_star"].items():
        print(f"  標示 ★{s}：{v['n']} 題，中位數 {v['median']} 分鐘（預設 {v['prior']}）")
    print("\n和標示差最多的題：")
    for r in c["rows"][:10]:
        print(f"  {r['id']:<18} 標示 ★{r['listed']}（{r['source']}） → 對你 ★{r['mine']}　{r['label']}　{r['effort_min']} 分／{r['attempts']} 次／{r['hints']} 提示　{r['title']}")
    return 0


def cmd_external(ws: Workspace, args) -> int:
    ws.log("external_ai", problem=args.id)
    print("已記錄你用了外部 AI（誠實記錄比不用更重要）。這題建議之後無提示重寫。")
    return 0


def cmd_export(ws: Workspace, args) -> int:
    dest = backup.export_workspace(ws, Path(args.out) if args.out else None)
    print(f"已匯出：{dest}（{dest.stat().st_size // 1024} KB）")
    print("包含進度、解答、你匯入的題目與測資；內建練習題的測資不包含（會自動重新安裝）。")
    return 0


def cmd_restore(args) -> int:
    n = backup.restore_workspace(Path(args.file), Path(args.dir), args.force)
    print(f"已還原 {n} 個檔案到 {Path(args.dir).resolve()}。在那個資料夾裡執行 cpe today 繼續。")
    return 0


def cmd_web(ws: Workspace, args) -> int:
    from . import web
    web.serve(ws.root, args.port, not args.no_open)
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
    s.add_argument("--real", action="store_true", help="比照考場：只出有英文題目文字的題（需先匯入歷屆題目）")
    s = sub.add_parser("past", help="歷屆題庫：list／show 日期／import 檔案／statements 資料夾／start 日期／template")
    s.add_argument("action", choices=["list", "show", "import", "statements", "start", "template"])
    s.add_argument("arg", nargs="?", help="日期、檔案或資料夾")
    s.add_argument("--partial", action="store_true", help="start：只出已有測資的題目")
    s.add_argument("--lang", choices=["py", "cpp"])
    s = sub.add_parser("vocab", help="生字本")
    s.add_argument("action", nargs="?", default="list", choices=["list", "export", "add"])
    s.add_argument("word", nargs="?")
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
    s = sub.add_parser("eng", help="工程能力任務（有自動驗收）")
    s.add_argument("action", nargs="?", choices=["list", "start", "verify"], default="list")
    s.add_argument("n", nargs="?", type=int)
    s.add_argument("--evidence", help="需要證據的任務：提供網址")
    s = sub.add_parser("plan", help="今天 N 分鐘的自動排程")
    s.add_argument("-m", "--minutes", type=int, default=30)
    sub.add_parser("calibrate", help="用你的實際解題紀錄看題目對你多難")
    s = sub.add_parser("external", help="記錄你用了外部 AI（如 ChatGPT 網頁）")
    s.add_argument("id")
    s = sub.add_parser("export", help="匯出備份（zip）")
    s.add_argument("-o", "--out", help="輸出檔名（預設在工作區內 cpe-backup-時間.zip）")
    s = sub.add_parser("restore", help="從備份還原")
    s.add_argument("file")
    s.add_argument("--dir", default=".", help="還原到哪個資料夾（預設目前資料夾）")
    s.add_argument("--force", action="store_true", help="目標已有工作區時覆蓋（舊的 .cpe 會先改名保留）")
    s = sub.add_parser("web", help="啟動本機網頁介面（選取文字 → 問 AI）")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--no-open", action="store_true", help="不要自動開瀏覽器")
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
        if args.cmd == "restore":
            return cmd_restore(args)
        ws = Workspace.find()
        handler = {
            "course": cmd_course, "gate": cmd_gate, "statement": cmd_statement, "import": cmd_import,
            "roadmap": cmd_roadmap, "stage": cmd_stage, "today": cmd_today, "next": cmd_next, "new": cmd_new,
            "addtest": cmd_addtest, "test": cmd_test, "stress": cmd_stress, "hint": cmd_hint,
            "giveup": cmd_giveup, "solution": cmd_solution, "review": cmd_review, "mock": cmd_mock,
            "stats": cmd_stats, "add": cmd_add, "bank": cmd_bank, "eng": cmd_eng, "external": cmd_external, "web": cmd_web, "export": cmd_export, "past": cmd_past, "vocab": cmd_vocab, "plan": cmd_plan, "calibrate": cmd_calibrate,
        }[args.cmd]
        if args.cmd == "web":                       # 長時間執行：不要整個程序持有鎖，由每個請求自己加鎖
            return handler(ws, args)
        with ws.lock():
            return handler(ws, args)
    except (WorkspaceError, hints.HintDenied, ValueError, RuntimeError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
