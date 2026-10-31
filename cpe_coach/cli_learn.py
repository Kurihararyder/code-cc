"""每天練習用的指令：今天要做什麼、課程、出題、判題、提示、重練。"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from . import bank as bank_mod
from . import course as course_mod
from . import fuzz as fuzz_mod, hints, mock, roadmap, service, srs
from .service import add_test, fail_path, solution_file, trunc
from .judge import AC, stress
from .store import Workspace
from .cli_common import _read_block, fmt_dur, fmt_ts, get_llm, show_problem, start_date, suggestions, today_date


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
    print("\n只有一點時間？cpe plan -m 30 會依你的進度排出今天 30 分鐘要做的事。")
    print("開始：cpe new <題號> → 寫程式 → cpe test <題號>。卡住再 cpe hint <題號>。")
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
    if bank_mod.is_drill(args.id):
        bank_mod.install_drill(ws, args.id)
    text = service.statement_for(ws, args.id)
    if not text:
        raise ValueError(f"沒有 {args.id} 的題目敘述。外部題目請用 cpe import {args.id} <檔案> 存入")
    if args.lang:
        if not bank_mod.is_drill(args.id):
            raise ValueError("只有內建練習題有多種語言版本")
        text = bank_mod.drill_statement(args.id, args.lang)
    print(text)
    return 0


def cmd_lang(ws: Workspace, args) -> int:
    cfg = ws.config()
    if args.mode:
        cfg["statement_lang"] = args.mode
        ws.save_config(cfg)
    mode = cfg.get("statement_lang", "auto")
    print(f"內建題目語言：{mode}" + {"auto": "（階段 0 中文 → 階段 1 中英對照 → 階段 2 起英文）", "zh": "（全部中文）", "bi": "（全部中英對照）", "en": "（全部英文）"}[mode])
    print("真實考場模式（cpe mock start --real）一律英文。")
    return 0


def cmd_import(ws: Workspace, args) -> int:
    text = service.read_statement_file(Path(args.file))
    n = service.import_statement(ws, args.id, text)
    if not n:
        print(f"已存入 statements/{args.id}.txt，但找不到『Sample Input / 範例輸入』區塊。請改用 cpe addtest {args.id}")
        return 1
    print(f"已存入 statements/{args.id}.txt，並建立 {n} 組範例測資（tests/{args.id}/sample*）。")
    print("請對照原題確認輸出沒有被多切或少切；範例通常只是『最基本』的測資，通過後還要自己補邊界測資。")
    return 0


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
    if r["verdict"] == AC and args.id.startswith("uva") and not r["exam_note"] and len(r["cases"]) <= 3 and all(c["name"].startswith("sample") for c in r["cases"]):
        print(f"\n提醒：原題只附了範例，通過範例不代表答案正確。想自己找出沒被涵蓋的錯：寫一個很慢但一定對的暴力解 brute.py，執行\n  cpe fuzz {args.id} --brute brute.py --save")
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


def cmd_fuzz(ws: Workspace, args) -> int:
    sol = solution_file(ws, args.id)
    try:
        r = fuzz_mod.fuzz(sol, Path(args.brute), ws.tests / args.id, args.n, args.seed, args.max, float(ws.config()["timeout_sec"]),
                          int(ws.config().get("memory_mb", 1024)))
    except fuzz_mod.FuzzError as e:
        raise ValueError(str(e))
    print(f"變異 {r['tried']} 組（暴力解自己跑不動而略過 {r['skipped']} 組），種子輸入 {r['seeds']} 組。")
    if not r["found"]:
        print("✓ 沒有發現你的解和暴力解不一致。這只代表『範例附近的變化』沒問題，不代表一定正確；還是要自己想邊界。")
        return 0
    print(f"✗ 找到 {len(r['found'])} 組不一致（已盡量縮小）。請先確認輸入符合題目限制：")
    for k, f in enumerate(r["found"], 1):
        print(f"\n[{k}] {f['verdict']}\n輸入：\n{trunc(f['input'], 300)}暴力解：\n{trunc(f['brute_out'], 200)}\n你的解：\n{trunc(f['sol_out'], 200)}")
    if args.save:
        names = fuzz_mod.save(ws, args.id, r["found"])
        print(f"\n已存成 tests/{args.id}/{'、'.join(names)}。之後 cpe test 會一起跑；若某組輸入其實不合法，直接刪掉那兩個檔案。")
    else:
        print("\n加 --save 可以把這些存成測資。")
    return 1


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


def cmd_external(ws: Workspace, args) -> int:
    ws.log("external_ai", problem=args.id)
    print("已記錄你用了外部 AI（誠實記錄比不用更重要）。這題建議之後無提示重寫。")
    return 0
