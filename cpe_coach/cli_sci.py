"""學習科學相關的指令：記憶排程、知識點掌握、錯誤本、習慣與疲勞、靜態分析、工具與內容（陸續加入）。"""
from __future__ import annotations

import time

import json
import random
from pathlib import Path

from . import bank as bank_mod
from . import aggregate, coach, concepts, errbook, exchange, experiment, sync as sync_mod, habits, judge, knowledge, lab, lint, memory, notes, planning, reminder, tools
from .llm import detect_client
from .service import fail_path, solution_file, statement_for
from .store import Workspace


def _d(ts: float) -> str:
    return time.strftime("%m-%d %H:%M", time.localtime(ts))


def cmd_mem(ws: Workspace, args) -> int:
    bank = bank_mod.load_bank(ws)
    rp, ft = memory.build(ws, bank)
    now = ws.now()
    if args.action == "status":
        print(f"已解出且納入記憶排程的題：{len(rp.cards)} 題；複習紀錄 {len(rp.pairs)} 次。")
        due = memory.due_now(rp.cards, now, ft.k, due_fn=memory.make_due_fn(ws))
        print(f"現在該複習：{len(due)} 題（預測保留率由低到高）")
        for d in due[:10]:
            print(f"  {d.pid:<12} 預測保留率 {round(100 * d.r_now):>3}%　已逾期 {d.overdue_days:.1f} 天　{bank.get(d.pid, {}).get('title', '')}")
        print(("個人化：k=%.2f（用你的 %d 次複習擬合；k<1 表示你比預設模型記得好）" % (ft.k, ft.n)) if ft.enabled else f"個人化：還沒啟用（需要至少 {memory.MIN_REVIEWS_FOR_FIT} 次複習，目前 {ft.n} 次）；先用 FSRS-4.5 預設參數。")
    elif args.action == "due":
        for d in memory.schedule(rp.cards, now, ft.k, due_fn=memory.make_due_fn(ws)):
            when = "今天" if d.day == 0 else f"{d.day} 天後"
            print(f"{d.pid:<12} {when:<6} 預測保留率 {round(100 * d.r_now):>3}%　下次 {_d(d.due_ts)}")
    elif args.action == "forecast":
        f = memory.forecast(rp.cards, now, 14, ft.k, due_fn=memory.make_due_fn(ws))
        for i, n in enumerate(f):
            print(f"{time.strftime('%m-%d', time.localtime(now + i * 86400))}　{'█' * n} {n}")
        print("每天最多排 8 題，超過的會往後挪最多 2 天（負載平準）。")
    elif args.action == "fit":
        print(f"複習次數 {ft.n}；k={ft.k:.3f}；預設參數的對數損失 {ft.loss_default:.3f} → 個人化 {ft.loss_fit:.3f}；{'已啟用' if ft.enabled else '未啟用（資料不足）'}")
    elif args.action == "concepts":
        for r in memory.concept_report(rp.concept_cards, now, ft.k):
            print(f"{r['name']:<16} 預測保留率 {round(100 * r['retention']):>3}%　穩定度 {r['stability_days']:>6} 天　複習 {r['reviews']} 次　遺忘 {r['lapses']} 次")
        if not rp.concept_cards:
            print("還沒有解出過的題。")
    return 0


def cmd_err(ws: Workspace, args) -> int:
    bank = bank_mod.load_bank(ws)
    if args.action == "tag":
        if not args.id or not args.cause:
            raise ValueError("用法：cpe err tag <題號> <錯因>；錯因：" + "、".join(errbook.CAUSES))
        if args.cause not in errbook.CAUSES:
            raise ValueError("錯因要是這些之一：" + "、".join(errbook.CAUSES))
        last = [e for e in ws.events() if e.get("kind") == "err" and e["problem"] == args.id]
        if not last:
            raise ValueError(f"{args.id} 沒有錯誤紀錄")
        ws.log("errtag", target_ts=last[-1]["ts"], problem=args.id, cause=args.cause)
        print(f"已把 {args.id} 最近一次的錯因改成「{args.cause}」。")
        return 0
    s = errbook.summary(ws.events(), bank)
    if not s["total"]:
        print("錯誤本是空的（還沒有沒通過的紀錄）。")
        return 0
    print(f"共 {s['total']} 次沒通過；最常見的錯因：")
    for r in s["causes"]:
        print(f"  {r['cause']:<10} {r['count']:>3} 次（{round(100 * r['share'])}%）　涉及 {len(r['problems'])} 題　最近 {_d(r['last'])}")
    if s["advice"]:
        print("\n建議：" + s["advice"])
    print("\n最常出錯的題：" + "、".join(f"{w['id']}（{w['errors']}）" for w in s["worst_problems"][:5]))
    print("分類是規則判斷，可能分錯；用 cpe err tag <題號> <錯因> 修正。")
    return 0


def cmd_insight(ws: Workspace, args) -> int:
    bank = bank_mod.load_bank(ws)
    m = knowledge.mastery(ws, bank)
    print("知識點掌握（P(會)：貝氏知識追蹤；保留率：記憶模型）")
    for cid in concepts.topo_order():
        r = m[cid]
        if not r["touched"] and r["level"] == 0:
            continue
        ret = "—" if r["retention"] is None else f"{round(100 * r['retention'])}%"
        print(f"  {r['name']:<14} P(會) {round(100 * r['p_know']):>3}%　保留率 {ret:>4}　層級 {r['label']}" + ("　⚠ 該複習" if r["needs_review"] else ""))
    print("\n下一題推薦（推測成功率最接近 70%）：")
    for r in knowledge.recommend(ws, bank, 3):
        print(f"  {r['id']:<12} {r['title']}　{r['why']}")
    ev = ws.events()
    hb = habits.by_time_of_day(ev)
    if hb["note"]:
        print("\n時段：" + hb["note"])
    for sgn in habits.fatigue(ev, ws.now()):
        print(("⚠ " if sgn["level"] == "warn" else "· ") + sgn["msg"])
    return 0


def cmd_lint(ws: Workspace, args) -> int:
    sol = solution_file(ws, args.id)
    if not sol.exists():
        raise ValueError(f"找不到 {args.id} 的解答檔")
    found = lint.lint(sol.read_text(encoding="utf-8"), "cpp" if sol.suffix == ".cpp" else "py")
    if not found:
        print("沒有發現明顯的問題（靜態分析只抓常見的慢寫法與新手錯誤，不保證沒有 bug）。")
    for f in found:
        print(f"  第 {f['line']} 行 [{f['level']}] {f['msg']}")
    return 0


def cmd_shrink(ws: Workspace, args) -> int:
    sol = solution_file(ws, args.id)
    if args.input:
        text = Path(args.input).read_text(encoding="utf-8")
    elif fail_path(ws, args.id).exists():
        text = json.loads(fail_path(ws, args.id).read_text(encoding="utf-8"))["input"]
    else:
        raise ValueError("沒有可縮小的輸入：先 cpe test 讓它失敗一次，或用 --input 檔案 指定。")
    r = tools.shrink_failure(sol, text, Path(args.brute) if args.brute else None, float(ws.config()["timeout_sec"]), int(ws.config().get("memory_mb", 1024)), args.budget)
    print(f"失敗種類：{r['kind']}{'（' + r['error'] + '）' if r['error'] else ''}；輸入由 {r['original_size']} 個字元縮到 {r['minimal_size']} 個。")
    print("最小的失敗輸入：\n" + r["minimal"])
    print("提醒：縮小後的輸入不一定符合題目的限制，請自己確認它是合法的輸入。")
    if args.save:
        d = ws.tests / args.id
        n = len(list(d.glob("shrink*.in"))) + 1
        (d / f"shrink{n:02d}.in").write_text(r["minimal"], encoding="utf-8")
        print(f"輸入已存成 tests/{args.id}/shrink{n:02d}.in；預期輸出要你自己確認後存成同名的 .out（沒有標準答案就不能自動產生）。")
    return 0


def cmd_complexity(ws: Workspace, args) -> int:
    sol = solution_file(ws, args.id)
    cases = judge.find_cases(ws.tests / args.id)
    rng = random.Random(1)
    if args.gen:
        import subprocess
        import sys

        def make(n: int):
            p = subprocess.run([sys.executable, args.gen, str(n)], capture_output=True, text=True, timeout=60)
            return p.stdout if p.returncode == 0 else None
    elif cases:
        sample = cases[0][0].read_text(encoding="utf-8")

        def make(n: int):
            return tools.auto_input(sample, n, rng)
    else:
        raise ValueError("沒有測資可以放大，請用 --gen 產生器.py")
    sizes = [int(x) for x in args.sizes.split(",")] if args.sizes else [250, 500, 1000, 2000, 4000]
    r = tools.measure_complexity(sol, make, sizes, timeout=float(args.timeout), budget_s=float(args.budget))
    for n, t in r.get("points", []):
        print(f"  n={n:<8} {t * 1000:9.1f} ms")
    if "best" not in r:
        print(r.get("error", "資料不足"))
        return 1
    print(f"估計的時間複雜度：{r['best']}（次佳 {r['runner_up']}；對數斜率 {r['slope']}；{'信心尚可' if r['confident'] else '兩個候選很接近，信心低'}）")
    if r.get("error"):
        print("注意：" + r["error"])
    if args.nmax:
        print(tools.estimate_for_n_max(r["best"], args.nmax) or "")
    print("這是用隨機輸入實測再擬合的估計，不是證明；Python 啟動時間與機器雜訊會影響結果。")
    return 0


def cmd_algo(ws: Workspace, args) -> int:
    sol = solution_file(ws, args.id)
    bank = bank_mod.load_bank(ws)
    sig = tools.signature(sol.read_text(encoding="utf-8"))
    cmp_ = tools.compare_with_expected(sig, concepts.of_problem(bank_mod.resolve(bank, args.id)))
    print("你的解法看起來用到：" + ("、".join(sig["labels"]) or "（看不出特別的技巧）") + f"；迴圈最深 {sig['depth']} 層")
    for n in sig["notes"]:
        print("· " + n)
    print(cmp_["verdict"])
    print("（這是看語法特徵的啟發式判斷，不是理解你的程式。）")
    return 0


def cmd_note(ws: Workspace, args) -> int:
    if args.action == "add":
        if not args.text:
            raise ValueError("用法：cpe note add <種類 think|recall|reflect> <文字> [--problem 題號]")
        notes.add(ws, args.kind, args.text, args.problem)
        print("已記下。")
        return 0
    for e in notes.listing(ws, args.kind, args.problem, 20):
        print(f"[{_d(e['ts'])}] {e['note_kind']:<7} {e.get('problem') or '-':<10} {e['text'][:100]}")
    return 0


def cmd_recall(ws: Workspace, args) -> int:
    """回想練習：複習一題之前，先不看程式，自己寫下解法大綱，再和上次比對。"""
    bank = bank_mod.load_bank(ws)
    p = bank_mod.resolve(bank, args.id)
    if not args.text:
        prev = notes.last_outline(ws, args.id)
        print(f"{args.id} {p.get('title', '')}\n先不要看程式碼：用幾句話寫下你記得的解法（用什麼做法、為什麼、複雜度），然後：\n  cpe recall {args.id} \"你的大綱\"")
        if prev:
            print("\n（你上次寫的大綱存著，交出新的之後會一起顯示對照。）")
        return 0
    prev = notes.last_outline(ws, args.id)
    notes.add(ws, "recall", args.text, args.id)
    print("已記下。")
    if prev:
        print(f"\n上次（{_d(prev['ts'])}）你寫的：\n  {prev['text']}")
    if p.get("hint_insight"):
        sc = notes.score_offline(args.text, p["hint_insight"], p.get("hint_category", ""))
        print(f"\n對照關鍵洞察：{p['hint_insight']}\n離線比對：{sc['message']}（{sc['note']}）")
    return 0


def cmd_explain(ws: Workspace, args) -> int:
    bank = bank_mod.load_bank(ws)
    p = bank_mod.resolve(bank, args.id)
    insight = p.get("hint_insight") or ""
    if not insight:
        raise ValueError("這題沒有內建的關鍵洞察可以對照；用 cpe note add reflect 當筆記就好。")
    res = None
    if not args.offline:
        client = detect_client(ws.config())
        if client is not None:
            try:
                res = notes.score_with_ai(client, args.text, insight, statement_for(ws, args.id))
            except Exception as e:                                   # AI 失敗、金鑰錯、回傳格式不對：退回離線評分，不中斷
                print(f"（AI 評分失敗：{e}；改用離線評分）")
    res = res or notes.score_offline(args.text, insight, p.get("hint_category", ""))
    notes.add(ws, "explain", args.text, args.id, score=res["score"], mode=res["mode"])
    print(f"自我解釋評分（{res['mode']}）：{res['score']}　{res['message']}")
    if res["missed"]:
        print("可能漏掉：" + "、".join(res["missed"]))
    print(res["note"])
    return 0


def _ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def _show_q(q: dict) -> None:
    print("\n" + q["q"])
    if q.get("code"):
        print("```\n" + q["code"] + "\n```")
    if q.get("stdin"):
        print("（輸入：" + q["stdin"].strip().replace("\n", " ⏎ ") + "）")
    for i, c in enumerate(q["choices"]):
        print(f"  {'ABCD'[i]}. " + c.replace("\n", "\n     "))


def _pick(n: int) -> int:
    while True:
        a = _ask("你的答案（A–%s，q 離開）：" % "ABCD"[n - 1]).upper()
        if a == "Q" or a == "":
            return -1
        if a in "ABCD"[:n] and len(a) == 1:
            return "ABCD".index(a)


def cmd_quiz(ws: Workspace, args) -> int:
    if args.concept:
        if args.concept not in concepts.load():
            raise ValueError("知識點：" + "、".join(concepts.load()))
        right = 0
        qs = lab.practice(args.concept, args.n)
        for q in qs:
            _show_q(q)
            c = _pick(len(q["choices"]))
            if c < 0:
                return 0
            g = lab.grade(q["id"], c)
            right += g["correct"]
            print(("✔ 答對了。" if g["correct"] else f"✘ 答案是 {'ABCD'[g['answer']]}。") + g["why"])
        print(f"\n{right}/{len(qs)} 題答對。")
        return 0
    from . import aggregate
    lab.set_calibration(aggregate.load_calibration(ws)["quiz"])
    state = lab.cat_new()
    print("適性診斷：最多 %d 題，會依你的答對情況調整難度（q 可離開）。" % lab.MAX_Q)
    while True:
        q = lab.cat_next(state)
        if q is None:
            break
        _show_q(q)
        c = _pick(len(q["choices"]))
        if c < 0:
            return 0
        r = lab.cat_answer(state, q["id"], c)
        print(("✔ " if r["correct"] else "✘ 答案是 %s。" % "ABCD"[r["answer"]]) + r["why"])
        if state["done"]:
            break
    res = lab.cat_result(state)
    print(f"\n程度：{res['level']}（能力估計 {res['theta']}，答對 {res['correct']}/{res['answered']}）")
    if res["weak"]:
        print("建議先補：" + "、".join(f"{w['name']}（單元 {w['unit']}）" for w in res["weak"]))
    print(res["why"] + "\n" + res["caveat"])
    ws.log("quiz", theta=res["theta"], answered=res["answered"], correct=res["correct"], start_unit=res["start_unit"], items=[{"id": a["id"], "correct": a["correct"]} for a in state["asked"]])
    return 0


def cmd_study(ws: Workspace, args) -> int:
    kind, key = args.kind, args.id
    if kind == "list":
        for name, label in (("worked", "示範題"), ("bugs", "找 bug"), ("predict", "預測輸出"), ("lessons", "微課"), ("compare", "解法比較")):
            ids = [it.get("id") or it.get("concept") for it in lab.items(name)]
            print(f"{label}：" + "、".join(ids))
        return 0
    if kind == "glossary":
        for r in lab.search_glossary(key or "", 30):
            print(f"{r['en']:<22} {r['zh']}" + (f"　{r['note']}" if r["note"] else ""))
        return 0
    if kind == "lesson":
        if not key or key not in concepts.load():
            raise ValueError("用法：cpe study lesson <知識點>；知識點：" + "、".join(concepts.load()))
        les = lab.lesson(key)
        print(f"{les['title']}（約 {les['minutes']} 分鐘）\n")
        for p in les["points"]:
            print("・" + p)
        print("\n```\n" + les["code"] + "\n```\n輸出：\n" + les["output"] + "\n\n常見陷阱：" + les["pitfall"] + "\n練習：cpe quiz " + key)
        return 0
    if kind in ("worked", "faded", "parsons"):
        if not key:
            raise ValueError("用法：cpe study %s <示範題編號>（cpe study list 看全部）" % kind)
        w = lab.by_id("worked", "id", key)
        if kind == "worked":
            print(f"{w['title']}\n{w['problem']}\n")
            for i, s in enumerate(w["steps"], 1):
                print(f"步驟 {i}：{s['say']}\n```\n{s['code']}\n```")
            return 0
        if kind == "faded":
            f = lab.faded(w, args.level)
            print(f"{w['title']}（留白 {f['level']}/{f['max_level']} 步）\n{w['problem']}\n")
            for s in f["given"]:
                print(f"```\n{s['code']}\n```")
            for s in f["blank"]:
                print("（請你寫）" + s["say"])
            if args.answer:
                r = lab.check_faded(w, args.level, Path(args.answer).read_text(encoding="utf-8"))
                print("✔ 通過所有測資。" if r["ok"] else "✘ 還沒通過：\n" + "\n".join(f"  輸入 {x['input']!r} 預期 {x['expected']!r} 得到 {x['got']!r} {x['error']}" for x in r["results"] if not x["ok"]))
            else:
                print("\n把你寫的接在上面程式後面的部分存成檔案，再用 --answer 檔案 檢查。")
            return 0
        p = lab.parsons(w, args.seed)
        print(f"{w['title']}\n{w['problem']}\n把下面的行排成正確的程式（有些行是多餘的，要排除）：")
        for ln in p["lines"]:
            print(f"  [{ln['id']:>2}] {ln['text']}")
        if args.order:
            r = lab.check_parsons(w, args.seed, [int(x) for x in args.order.split(",")])
            print("✔ 通過所有測資。" if r["ok"] else "✘ 還沒通過。")
        else:
            print("\n用 --order 3,0,5,… 提交你排好的行編號（以逗號分隔）。")
        return 0
    if kind == "bug":
        if not key:
            raise ValueError("用法：cpe study bug <編號>（cpe study list 看全部）")
        b = lab.by_id("bugs", "id", key)
        print(f"{b['title']}：{b['statement']}\n")
        for i, ln in enumerate(b["buggy"].split("\n"), 1):
            print(f"{i:>3}  {ln}")
        if args.line:
            r = lab.check_bug(b, args.line)
            print(("✔ 找到了！" if r["found"] else "✘ 不是這一行。") + (r["why"] if r["found"] else ""))
        else:
            print("\n這個程式在某些輸入會答錯或當掉。用 --line N 回答你覺得有問題的是第幾行。")
        return 0
    if kind == "predict":
        if not key:
            raise ValueError("用法：cpe study predict <編號>（cpe study list 看全部）")
        p = lab.by_id("predict", "id", key)
        print("下面的程式會輸出什麼？先在心裡（或紙上）寫出來：\n```\n" + p["code"] + "\n```")
        if p["stdin"]:
            print("輸入：" + p["stdin"].strip())
        if args.answer is not None:
            r = lab.check_predict(p, args.answer)
            print(("✔ 對了。" if r["correct"] else "✘ 不一樣。") + "\n實際輸出：\n" + r["output"])
        else:
            print("用 --answer \"你的預測\" 檢查。")
        return 0
    if kind == "compare":
        if not key:
            raise ValueError("用法：cpe study compare <編號>（cpe study list 看全部）")
        c = lab.by_id("compare", "id", key)
        print(f"{c['title']}\n{c['problem']}\n")
        for a in c["approaches"]:
            print(f"■ {a['name']}（{a['complexity']}）\n{a['note']}\n```\n{a['code']}\n```\n")
        return 0
    return 0


def cmd_goal(ws: Workspace, args) -> int:
    if args.action == "set":
        if not args.date or not args.problems:
            raise ValueError("用法：cpe goal set --date 2027-03-20 --problems 60")
        g = planning.set_goal(ws, args.date, args.problems)
        print(f"目標已設定：{g['date']} 之前累積解出 {g['problems']} 題。")
    s = planning.goal_status(ws)
    if not s["set"]:
        print("還沒有設定目標。cpe goal set --date YYYY-MM-DD --problems N")
        return 0
    print(f"目標：{s['date']} 前解出 {s['target']} 題；目前 {s['solved']} 題，還差 {s['remaining']} 題，剩 {s['days_left']} 天。")
    print(f"需要的速度：每週 {s['need_per_week']:.1f} 題；你最近的速度：每週 {s['pace_per_week']} 題。" if s["need_per_week"] is not None else "已經到期。")
    if s["forecast_days"] and s["forecast_days"]["possible"]:
        f = s["forecast_days"]
        print(f"預測還要幾天（10%／50%／90%）：{f['p10']}／{f['p50']}／{f['p90']} 天（用你最近每天的解題數做 1000 次模擬）。")
    if s["daily_minutes"]:
        print(f"平均每題約 {s['minutes_per_problem']} 分鐘 → 為了趕上，平均每天約 {s['daily_minutes']} 分鐘。")
    print(s["message"])
    return 0


def cmd_report(ws: Workspace, args) -> int:
    r = planning.report(ws, args.days, bank_mod.load_bank(ws))
    print(f"{r['range'][0]} ～ {r['range'][1]}（最近 {r['days']} 天）")
    print(f"練習 {r['active_days']} 天、約 {r['minutes']} 分鐘；提交 {r['submissions']} 次；新解出 {r['new_solved']} 題；一次就對 {r['first_try_correct']}/{r['attempts']}")
    print(f"複習 {r['reviews_passed']}/{r['reviews']} 通過；用了 {r['hints']} 次提示；寫了 {r['notes']} 則筆記")
    if r["top_errors"]:
        print("最常見的錯因：" + "、".join(f"{e['cause']}（{e['count']}）" for e in r["top_errors"]))
    if r["time_of_day"]:
        print("時段：" + r["time_of_day"])
    if args.days >= 7 and not r["notes"]:
        print("\n花一分鐘想想：這段時間最卡的是什麼？有什麼下次想改的做法？  cpe note add reflect \"…\"")
    if args.out:
        out = coach.export(ws, Path(args.out), args.notes)
        print(f"已產生給老師的報告：{out['html']}（只含統計數字，不含程式碼與題目文字）")
    return 0


def cmd_achievements(ws: Workspace, args) -> int:
    for a in planning.achievements(ws, bank_mod.load_bank(ws)):
        print(("✔ " if a["unlocked"] else "· ") + f"{a['name']}：{a['desc']}" + (f"（{_d(a['ts'])}）" if a["unlocked"] else ""))
    print("成就看的是做法的品質（無提示、回想、複習），不是刷題量；沒有「斷了就歸零」的連續紀錄。")
    return 0


def cmd_strategy(ws: Workspace, args) -> int:
    t = planning.time_strategy(ws)
    for a in t["advice"]:
        print("・" + a)
    return 0


def cmd_predict(ws: Workspace, args) -> int:
    p = planning.score_prediction(ws, bank_mod.load_bank(ws))
    print(f"預期答對 {p['expected']} 題；至少 4 題的機率約 {round(100 * p['p_at_least_4'])}%、至少 6 題約 {round(100 * p['p_at_least_6'])}%；壓力係數 {p['pressure_factor']}")
    for k, v in enumerate(p["distribution"]):
        print(f"  答對 {k} 題：{round(100 * v):>3}%  {'█' * round(40 * v)}")
    print("各難度的推測一次通過率：" + "、".join(f"★{s} {round(100 * x)}%（樣本 {p['samples'][s]}）" for s, x in p["per_star"].items()))
    print(p["caveat"])
    pr = planning.pressure(ws, bank_mod.load_bank(ws))
    print(pr.get("note", ""))
    return 0


def cmd_final(ws: Workspace, args) -> int:
    for it in planning.final_checklist(ws, bank_mod.load_bank(ws), args.days)["items"]:
        print("□ " + it["text"])
    return 0


def cmd_remind(ws: Workspace, args) -> int:
    if args.action == "check":
        r = reminder.check(ws, force=args.force)
        print(f"到期的複習：{r['due']} 題" + ("；已通知" if r["notified"] else f"；沒有通知（{r['reason']}）"))
        return 0
    plan = reminder.install_plan(ws, args.hour, args.minute)
    print(plan["text"])
    if args.apply:
        ok, msg = reminder.apply_install(plan)
        print(msg)
        return 0 if ok else 1
    print("\n以上只是列出指令；加 --apply 才會真的安裝。取消：" + plan["uninstall"])
    return 0


def cmd_coach(ws: Workspace, args) -> int:
    if args.action == "import":
        if not args.file:
            raise ValueError("用法：cpe coach import 留言檔.json")
        print(f"已匯入 {coach.import_comments(ws, Path(args.file))} 則留言。")
    elif args.action == "export":
        out = coach.export(ws, Path(args.file or "."), args.notes)
        print("已產生：" + out["html"] + "\n（只含統計數字與知識點狀態，不含程式碼、題目文字、金鑰與 AI 對話。）")
    else:
        for c in coach.comments(ws):
            print(f"[{_d(c['ts'])}] {c['from'] or '老師'}：{c['text']}" + (f"（{c['problem']}）" if c["problem"] else ""))
    return 0


def cmd_exp(ws: Workspace, args) -> int:
    if args.action in ("start", "stop"):
        experiment.set_enabled(ws, args.action == "start")
        print("實驗已" + ("開啟：約一半的題會改用固定間隔（1/3/7/14/30/60 天）複習，另一半用 FSRS。" if args.action == "start" else "關閉：全部回到 FSRS。"))
    rp, _ = memory.build(ws, bank_mod.load_bank(ws))
    r = experiment.analyze(ws, rp.cards)
    print("實驗：" + ("進行中" if r["enabled"] else "沒有開啟"))
    for a, d in r["arms"].items():
        print(f"  {a:<6} 複習 {d['reviews']:>3} 次　記得比例 {d['recall_rate']}　95% 區間 {d['ci']}　間隔中位數 {d['median_gap_days']} 天")
    print(r["conclusion"])
    return 0


def cmd_stats_export(ws: Workspace, args) -> int:
    d = aggregate.export_anonymous(ws, Path(args.out))
    print(f"已匯出匿名統計：{args.out}（代號 {d['learner']}；{len(d['problems'])} 題的一次通過與否、{len(d['quiz'])} 題概念測驗）。")
    print("檔案裡沒有時間、程式碼、題目文字或名字；你可以放心看過內容再決定要不要給別人。")
    return 0


def cmd_calibrate_merge(ws: Workspace, args) -> int:
    res = aggregate.merge([Path(f) for f in args.files])
    rel = sum(1 for k in ("problems", "quiz") for v in res[k].values() if v["reliable"])
    print(f"合併 {res['learners']} 位學習者；可靠的題目 {rel} 題。{res['note']}")
    for k, label in (("problems", "題目"), ("quiz", "測驗題")):
        top = sorted(res[k].items(), key=lambda kv: -kv[1]["b"])[:3]
        if top:
            print(f"最難的{label}：" + "、".join(f"{i}（b={v['b']}，一次通過率 {round(100 * v['p_correct'])}%，n={v['n']}）" for i, v in top))
    if args.out:
        Path(args.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"已寫入 {args.out}。放進工作區的 .cpe/calibration.json，推薦下一題與適性診斷就會改用校準過的難度。")
    return 0


def cmd_sync(ws: Workspace, args) -> int:
    r = sync_mod.sync_folder(ws, Path(args.folder))
    print(f"同步完成：本機新增 {r['events_added_local']} 筆紀錄、共用資料夾新增 {r['events_added_remote']} 筆；檔案拉下 {r['files_pulled']} 個、推上 {r['files_pushed']} 個。")
    for c in r["conflicts"]:
        print(f"  衝突：{c['file']}　留下{c['kept']}的版本，另一份存在 {c['other_saved_as']}")
    return 0


def cmd_anki(ws: Workspace, args) -> int:
    Path(args.out).write_text(exchange.anki_tsv(ws, not args.no_quiz), encoding="utf-8")
    print(f"已產生 {args.out}：在 Anki 選「檔案 → 匯入」，欄位對應 正面／背面／標籤（Tab 分隔，允許 HTML）。")
    return 0


def cmd_xapi(ws: Workspace, args) -> int:
    st = exchange.xapi(ws)
    Path(args.out).write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已產生 {len(st)} 筆 xAPI statements：{args.out}（actor 是匿名帳號，沒有 email）。")
    return 0


def cmd_privacy(ws: Workspace, args) -> int:
    if args.action == "delete":
        n = exchange.delete_all(ws, args.confirm or "")
        print(f"已刪除 {n} 個檔案。")
        return 0
    inv = exchange.inventory(ws)
    print(f"工作區：{inv['root']}\n\n.cpe/ 裡的資料：")
    for r in inv["meta"]:
        print(f"  {r['name']:<24} {r['bytes']:>9} bytes  {r['meaning']}")
    for r in inv["other"]:
        print(f"  {r['name']:<24} {r['bytes']:>9} bytes  {r['meaning']}")
    print("\n" + inv["sent_out"] + "\n刪除全部：cpe privacy delete --confirm <工作區資料夾名稱>（先用 cpe export 備份）。")
    return 0


def cmd_group(ws: Workspace, args) -> int:
    if args.action == "card":
        Path(args.out).write_text(json.dumps(coach.card(ws, args.name or "me"), ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"已產生進度卡：{args.out}（只有暱稱與統計數字）。傳給同學，大家用 cpe group show 卡片… 看對照表。")
        return 0
    rows = coach.group_table([Path(f) for f in args.files])
    print(f"{'暱稱':<12}{'解出':>6}{'無提示':>8}{'近7天練習':>10}{'知識點':>8}")
    for r in rows:
        print(f"{r['name']:<12}{r['solved']:>6}{r['clean_solved']:>8}{r['active_days_7']:>10}{r['concepts']:>8}")
    print("排序依「無提示通過的題數」（看品質）；這只是互相打氣的參考，不是比賽。")
    return 0


def register(sub) -> None:
    s = sub.add_parser("stats-export", help="匯出匿名統計檔（只有每題一次通過與否；自願給別人合併校準難度）")
    s.add_argument("out")
    s = sub.add_parser("calibrate-merge", help="合併多個匿名統計檔，用 IRT 估每題的難度")
    s.add_argument("files", nargs="+")
    s.add_argument("--out", help="寫出 calibration.json")
    s = sub.add_parser("sync", help="多裝置同步：和一個共用資料夾（Dropbox／隨身碟）雙向合併進度與紀錄")
    s.add_argument("folder")
    s = sub.add_parser("anki", help="匯出 Anki 卡片（Tab 分隔文字）")
    s.add_argument("out")
    s.add_argument("--no-quiz", action="store_true")
    s = sub.add_parser("xapi", help="匯出 xAPI 學習紀錄（JSON）")
    s.add_argument("out")
    s = sub.add_parser("privacy", help="列出存了什麼資料、資料會不會送出去；delete 刪除全部")
    s.add_argument("action", nargs="?", default="show", choices=["show", "delete"])
    s.add_argument("--confirm")
    s = sub.add_parser("group", help="學習小組：card 產生進度卡、show 看多張卡的對照表（用檔案交換）")
    s.add_argument("action", choices=["card", "show"])
    s.add_argument("files", nargs="*")
    s.add_argument("--out", default="cpe-card.json")
    s.add_argument("--name")
    s = sub.add_parser("goal", help="目標倒推：設定日期與題數，看進度、預測完成日、需要的速度")
    s.add_argument("action", nargs="?", default="show", choices=["show", "set"])
    s.add_argument("--date")
    s.add_argument("--problems", type=int)
    s = sub.add_parser("report", help="週報／月報（--out 資料夾 產生可以給老師的 HTML）")
    s.add_argument("--days", type=int, default=7)
    s.add_argument("--out")
    s.add_argument("--notes", action="store_true", help="報告附上你的近期筆記")
    sub.add_parser("achievements", help="成就（看品質不看刷題量）")
    sub.add_parser("strategy", help="考試時間策略：從你的模擬考歷史分析")
    sub.add_parser("predict", help="落點預測：推測真實考試答對題數的分布（粗估）")
    s = sub.add_parser("final", help="考前清單")
    s.add_argument("--days", type=int, help="距離考試還有幾天")
    s = sub.add_parser("remind", help="複習提醒：check 檢查一次並通知；install 列出（或 --apply 安裝）每天自動檢查的排程")
    s.add_argument("action", nargs="?", default="check", choices=["check", "install"])
    s.add_argument("--force", action="store_true", help="check：忽略『剛提醒過』與安靜時段")
    s.add_argument("--hour", type=int, default=19)
    s.add_argument("--minute", type=int, default=30)
    s.add_argument("--apply", action="store_true", help="install：真的安裝排程")
    s = sub.add_parser("coach", help="教練模式：export 產生給老師的報告、import 匯入老師的留言、list 看留言")
    s.add_argument("action", nargs="?", default="list", choices=["list", "export", "import"])
    s.add_argument("file", nargs="?")
    s.add_argument("--notes", action="store_true")
    s = sub.add_parser("exp", help="自我實驗：FSRS 對固定間隔（start／stop／結果）")
    s.add_argument("action", nargs="?", default="show", choices=["show", "start", "stop"])
    s = sub.add_parser("quiz", help="概念測驗：不給知識點就做適性診斷（最多 12 題），給知識點就練那個知識點")
    s.add_argument("concept", nargs="?")
    s.add_argument("-n", type=int, default=5)
    s = sub.add_parser("study", help="學習工坊：list／lesson／worked／faded／parsons／bug／predict／compare／glossary")
    s.add_argument("kind", choices=["list", "lesson", "worked", "faded", "parsons", "bug", "predict", "compare", "glossary"])
    s.add_argument("id", nargs="?")
    s.add_argument("--level", type=int, default=1, help="faded：留白幾步")
    s.add_argument("--answer", help="faded：你寫的程式檔；predict：你的預測")
    s.add_argument("--order", help="parsons：排好的行編號，逗號分隔")
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--line", type=int, help="bug：你覺得有問題的行號")
    s = sub.add_parser("shrink", help="把會讓你的程式出錯的輸入縮到最小（需要暴力解，或失敗是執行錯誤／逾時）")
    s.add_argument("id")
    s.add_argument("--brute", help="暴力解（標準答案）")
    s.add_argument("--input", help="指定要縮小的輸入檔（預設用最近一次失敗的測資）")
    s.add_argument("--budget", type=int, default=150, help="最多試幾次")
    s.add_argument("--save", action="store_true", help="把縮小後的輸入存進 tests/<題號>/shrinkNN.in")
    s = sub.add_parser("complexity", help="實測你的解答的時間複雜度（放大輸入、擬合曲線）")
    s.add_argument("id")
    s.add_argument("--gen", help="輸入產生器（收到參數 n，印出大小為 n 的輸入）；沒給就從範例自動放大")
    s.add_argument("--sizes", help="逗號分隔的輸入大小，例如 500,1000,2000,4000")
    s.add_argument("--nmax", type=int, help="題目的 n 上限：估計在那個大小要多久")
    s.add_argument("--timeout", default="10")
    s.add_argument("--budget", default="40", help="最多花幾秒")
    s = sub.add_parser("algo", help="你的解法看起來是哪一類演算法，和這題預期的是否相符")
    s.add_argument("id")
    s = sub.add_parser("note", help="思路、回想、反思筆記：add／list")
    s.add_argument("action", nargs="?", default="list", choices=["add", "list"])
    s.add_argument("kind", nargs="?", choices=list(notes.KINDS))
    s.add_argument("text", nargs="?")
    s.add_argument("--problem")
    s = sub.add_parser("recall", help="回想練習：複習前先不看程式，自己寫下解法大綱")
    s.add_argument("id")
    s.add_argument("text", nargs="?")
    s = sub.add_parser("explain", help="用自己的話解釋解法，並評分（有 AI 金鑰用 AI，否則離線關鍵詞比對）")
    s.add_argument("id")
    s.add_argument("text")
    s.add_argument("--offline", action="store_true")
    s = sub.add_parser("mem", help="記憶排程（FSRS）：status／due／forecast／fit／concepts")
    s.add_argument("action", nargs="?", default="status", choices=["status", "due", "forecast", "fit", "concepts"])
    s = sub.add_parser("err", help="錯誤本：看最常犯的錯因；tag <題號> <錯因> 修正自動分類")
    s.add_argument("action", nargs="?", default="show", choices=["show", "tag"])
    s.add_argument("id", nargs="?")
    s.add_argument("cause", nargs="?")
    sub.add_parser("insight", help="知識點掌握、下一題推薦、時段與疲勞提醒")
    s = sub.add_parser("lint", help="靜態分析：找常見的慢寫法與新手錯誤")
    s.add_argument("id")


HANDLERS = {"mem": cmd_mem, "err": cmd_err, "insight": cmd_insight, "lint": cmd_lint, "shrink": cmd_shrink, "complexity": cmd_complexity, "algo": cmd_algo,
            "note": cmd_note, "recall": cmd_recall, "explain": cmd_explain, "quiz": cmd_quiz, "study": cmd_study, "goal": cmd_goal, "report": cmd_report, "achievements": cmd_achievements,
            "strategy": cmd_strategy, "predict": cmd_predict, "final": cmd_final, "remind": cmd_remind, "coach": cmd_coach, "exp": cmd_exp, "stats-export": cmd_stats_export,
            "calibrate-merge": cmd_calibrate_merge, "sync": cmd_sync, "anki": cmd_anki, "xapi": cmd_xapi, "privacy": cmd_privacy, "group": cmd_group}
