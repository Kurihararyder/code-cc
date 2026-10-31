"""產生 cpe_coach/data/lab/*.json：把 dev/lab_*_src.py 的來源資料「實際執行」過，確認答案與輸出，再寫成學習內容。
任何一題的輸出對不上都會中止，所以內容裡的答案不是我手寫的。  用法：python dev/gen_lab.py"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from cpe_coach import concepts  # noqa: E402
from cpe_coach.judge import run_program  # noqa: E402
import lab_quiz_src  # noqa: E402
import lab_text_src  # noqa: E402
import lab_worked_src  # noqa: E402

OUT = ROOT / "cpe_coach" / "data" / "lab"
TMP = ROOT / ".lab_tmp"


def run(code: str, stdin: str = "", timeout: float = 20.0):
    TMP.mkdir(exist_ok=True)
    f = TMP / "p.py"
    f.write_text(code + "\n", encoding="utf-8")
    r = run_program(f, stdin, timeout)
    return r


def out_of(code: str, stdin: str = "") -> str:
    r = run(code, stdin)
    if r.rc != 0 or r.timed_out:
        raise SystemExit(f"執行失敗：\n{code}\n{r.err}")
    return r.out.rstrip("\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cs = concepts.load()
    # 概念測驗
    quiz = []
    for (qid, cid, b, q, code, stdin, choices, ans, why) in lab_quiz_src.Q:
        assert cid in cs and 0 <= ans < len(choices) and len(set(choices)) == len(choices), qid
        if code:
            got = out_of(code, stdin or "")
            if got.strip() != choices[ans].strip():
                raise SystemExit(f"{qid}: 實際輸出 {got!r} ≠ 標示的答案 {choices[ans]!r}")
            wrong = [c for i, c in enumerate(choices) if i != ans and c.strip() == got.strip()]
            assert not wrong, qid
        quiz.append({"id": qid, "concept": cid, "b": b, "q": q, "code": code, "stdin": stdin, "choices": choices, "answer": ans, "why": why})
    (OUT / "quiz.json").write_text(json.dumps({"items": quiz}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    qids = {x["id"] for x in quiz}

    # 示範題
    worked = []
    for (wid, cid, title, problem, steps, tests, distractors) in lab_worked_src.WORKED:
        assert cid in cs, wid
        sol = "\n".join(code for _, code in steps)
        tl = [{"in": t, "out": out_of(sol, t)} for t in tests]
        worked.append({"id": wid, "concept": cid, "title": title, "problem": problem, "steps": [{"say": s, "code": c} for s, c in steps], "tests": tl, "distractors": distractors})
    (OUT / "worked.json").write_text(json.dumps({"items": worked}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # 找錯題
    bugs = []
    for (bid, cid, title, stmt, tests, buggy, fixed, lines, why) in lab_worked_src.BUGS:
        assert cid in cs, bid
        tl = [{"in": t, "out": out_of(fixed, t)} for t in tests]
        failing = 0
        for t in tl:
            r = run(buggy, t["in"])
            if r.rc != 0 or r.timed_out or r.out.rstrip("\n") != t["out"]:
                failing += 1
        if not failing:
            raise SystemExit(f"{bid}: 有 bug 的程式在所有測資都答對了，不是好題目")
        bl, fl = buggy.split("\n"), fixed.split("\n")
        changed = {i + 1 for i in range(max(len(bl), len(fl))) if (bl[i] if i < len(bl) else None) != (fl[i] if i < len(fl) else None)}
        if not (set(lines) & changed):
            raise SystemExit(f"{bid}: 標的 bug 行 {lines} 不在有改動的行 {sorted(changed)}")
        assert all(1 <= n <= len(bl) for n in lines), bid
        bugs.append({"id": bid, "concept": cid, "title": title, "statement": stmt, "buggy": buggy, "fixed": fixed, "bug_lines": lines, "why": why, "tests": tl})
    (OUT / "bugs.json").write_text(json.dumps({"items": bugs}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # 預測輸出
    pred = []
    for (pid, cid, code, stdin) in lab_worked_src.PREDICT:
        assert cid in cs, pid
        pred.append({"id": pid, "concept": cid, "code": code, "stdin": stdin, "output": out_of(code, stdin)})
    (OUT / "predict.json").write_text(json.dumps({"items": pred}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # 微課
    lessons = []
    for (cid, title, mins, points, code, pitfall, qs) in lab_text_src.LESSONS:
        assert cid in cs and all(q in qids for q in qs), cid
        lessons.append({"concept": cid, "title": title, "minutes": mins, "points": points, "code": code, "output": out_of(code), "pitfall": pitfall, "quiz": qs})
    (OUT / "lessons.json").write_text(json.dumps({"items": lessons}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # 術語表
    (OUT / "glossary.json").write_text(json.dumps({"items": [{"en": e, "zh": z, "note": n} for e, z, n in lab_text_src.GLOSSARY]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # 解法比較
    comp = []
    for (cid_, title, problem, tests, approaches) in lab_worked_src.COMPARE:
        tl = []
        for t in tests:
            outs = [out_of(code, t) for _, _, code, _ in approaches]
            if len(set(outs)) != 1:
                raise SystemExit(f"{cid_}: 各種解法在輸入 {t!r} 的輸出不一致：{outs}")
            tl.append({"in": t, "out": outs[0]})
        comp.append({"id": cid_, "title": title, "problem": problem, "tests": tl, "approaches": [{"name": n, "complexity": c, "code": code, "note": note} for n, c, code, note in approaches]})
    (OUT / "compare.json").write_text(json.dumps({"items": comp}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    import shutil
    shutil.rmtree(TMP, ignore_errors=True)
    print({"quiz": len(quiz), "worked": len(worked), "bugs": len(bugs), "predict": len(pred), "lessons": len(lessons), "glossary": len(lab_text_src.GLOSSARY), "compare": len(comp)})


if __name__ == "__main__":
    main()
