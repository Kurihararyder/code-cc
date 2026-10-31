"""考試、歷屆題、計畫、統計與評測相關的指令。"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from . import bank as bank_mod
from . import course as course_mod
from . import aieval, calibrate, cpeimport, cpeset, eng, mock, pastexams, service, stats, vocab, weakness
from . import plan as plan_mod
from .llm import detect_client
from .store import Workspace
from .cli_common import fmt_dur, print_board, show_problem


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


def cmd_past(ws: Workspace, args) -> int:
    bank = bank_mod.load_bank(ws)
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
            m = re.match(r"^(?:uva)?[-_ ]?(\d+)\b.*\.(txt|md|html?|pdf)$", f.name, re.I)
            if not m:
                continue
            pid = f"uva{int(m.group(1))}"
            k = service.import_statement(ws, pid, service.read_statement_file(f))
            n_files += 1
            n_samples += k
            print(f"  {pid:<10} {f.name}　範例 {k} 組" + ("" if k else "　⚠ 找不到 Sample Input／Output，請用 cpe addtest 補"))
        print(f"\n處理 {n_files} 個檔案，共建立 {n_samples} 組範例測資。檔名格式：10050.txt、uva10050.html …")
    elif args.action == "repo":
        _past_repo(ws, args)
    elif args.action == "sets":
        _past_sets(ws, bank)
    elif args.action == "start":
        exam = course_mod.start_past(ws, bank, args.arg, args.lang or "py", args.partial)
        print(f"歷屆整場開始：{args.arg}，{exam['minutes']} 分鐘，{len(exam['problems'])} 題。AI 與提示已鎖定。")
        for pid in exam["problems"]:
            show_problem(bank_mod.resolve(bank, pid), hint_new=False)
            print(f"             檔案：{exam['files'][pid]}　題目：cpe statement {pid}")
        print("寫完用 cpe test <題號>；cpe mock status 看計分板；cpe mock finish 交卷。")
    return 0


def _past_repo(ws: Workspace, args) -> None:
    """把 CPE 原題（社群整理的 GitHub repo：一星題 49、二星題 15、歷屆試題 31）的 PDF 匯入成題目文字與範例測資。"""
    where = f"讀取 {args.arg}" if args.arg else "從 GitHub 下載（約 6 MB）"
    print(f"匯入 CPE 原題：{where}…")
    r = cpeimport.import_from(ws, args.arg, force=args.force, progress=lambda pid, msg: print(f"  {pid:<10} {msg}"))
    samples = sum(n for _, _, n in r.imported)
    print(f"\n完成：匯入 {len(r.imported)} 題（範例測資 {samples} 組）；略過已匯入的 {len(r.skipped)} 題；失敗 {len(r.failed)} 題。")
    for pid, why in r.failed:
        print(f"  ✗ {pid}：{why}")
    if r.no_samples:
        print("  找不到 Sample Input／Output：" + "、".join(r.no_samples) + "（請用 cpe addtest 補）")
    if r.missing:
        print("清單裡有、但這份資料沒有 PDF 的題：" + "、".join(r.missing) + "（要練的話自己貼上題目：cpe import <題號> <檔案>）")
    print("題目文字在 statements/uvaN.txt，原 PDF 也留在 statements/uvaN.pdf（算式、表格、圖擷取不好的地方請對照 PDF）。")
    print("下一步：cpe past sets 看三個題單；cpe new uva10008 開始練。" + ("　(已匯入的沒有覆蓋；要重做加 --force)" if r.skipped else ""))


def _past_sets(ws: Workspace, bank) -> None:
    s = cpeset.status(ws, bank)
    for g in s["sets"]:
        print(f"\n{g['name']}（{g['count']} 題；可練 {g['ready']}、已通過 {g['solved']}）")
        for r in g["problems"]:
            flag = ("✓" if r["solved"] else " ") + ("T" if r["has_tests"] else "-") + ("S" if r["has_statement"] else "-")
            print(f"  [{flag}] {r['id']:<9} {r['title']}" + ("　（該 repo 沒有 PDF）" if r["no_pdf"] and not r["has_statement"] else ""))
    print(f"\n[已通過/有測資(T)/有題目文字(S)]　共 {s['total']} 題，已可練 {s['ready']} 題。匯入：cpe past repo")


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


def cmd_weak(ws: Workspace, args) -> int:
    bank = bank_mod.load_bank(ws)
    a = weakness.analyze(ws, bank)
    if not a["problems_seen"]:
        print(a["note"])
        return 0
    LV = {"weak": "弱點", "watch": "留意", "ok": "穩", "unknown": "資料不足", "none": ""}
    print("主題弱點（分數越高越卡；至少 3 題有紀錄才下結論）")
    for r in a["families"]:
        if not r["n"]:
            continue
        print(f"  {r['name']:<12} {LV[r['level']]:<4} 分數 {r['score']:.2f}　{r['n']} 題有紀錄、首次通過率 {round(100 * r['first_try_rate'])}%、平均提示 {r['avg_hints']}、放棄 {r['gave_up']}")
    sug = weakness.suggestions(ws, bank, course_mod.load(), a, per_family=3)
    if sug:
        print("\n建議加練：")
        for w in sug:
            print(f"  {w['id']:<10} {w['title']}　（{w['family_name']}，★{w['difficulty']}）")
    elif a["flagged"]:
        print("\n弱主題目前沒有可練的未完成題。可以匯入更多題（cpe past / cpe import）。")
    else:
        print("\n目前沒有明顯的弱主題。")
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


def cmd_ai_eval(ws: Workspace, args) -> int:
    llm = detect_client(ws.config())
    if llm is None:
        raise ValueError("沒有設定 API 金鑰（環境變數 OPENAI_API_KEY，或 ANTHROPIC_API_KEY）。若金鑰由雲端環境的『網路密鑰』代理注入，請加上環境變數 CPE_PROXY_AUTH=1。")
    kinds = tuple(k for k in args.kinds.split(",") if k)
    if not set(kinds) <= set(aieval.KINDS):
        raise ValueError("--kinds 只能是 explain,question,mismatch")
    print(f"將對 {llm.provider} 的模型 {llm.model} 做約 {args.n}～{int(args.n * 2.2)} 次 API 呼叫（每次約一兩千 token，會產生費用）。")
    if not args.yes:
        print("確認要執行請加 --yes。（用的是暫存工作區，不會動到你的進度。）")
        return 0
    rep = aieval.run_eval(llm, args.n, kinds, not args.no_reply, args.price_in, args.price_out, progress=lambda m: print("  " + m, flush=True))
    print("\n" + aieval.format_report(rep))
    out = Path(args.out) if args.out else ws.meta / "eval" / time.strftime("ai-eval-%Y%m%d-%H%M%S.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n完整報告（含每一則回答，不含金鑰）：{out}")
    return 0
