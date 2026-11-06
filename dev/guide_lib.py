"""課程學習指南（像《資料結構期中考總整理》那樣：重點、表格、算例、易混淆、速查、每組單選模擬題與解析）的資料工具。

寫題目只要寫「正確答案」和三個「誘答」，選項順序由產生器依題目文字決定性地洗牌。
可驗證的題目（預測輸出、計算）帶 verify：產生器會實際執行 tclsh／python／iverilog／g++，輸出必須出現在正確選項裡。
"""
from __future__ import annotations

import hashlib
import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

LETTERS = "ABCD"


def cn(n: int) -> str:
    d = "零一二三四五六七八九"
    if n < 10:
        return d[n]
    return ("十" if n < 20 else d[n // 10] + "十") + (d[n % 10] if n % 10 else "")


def Q(stem: str, right: str, wrong: List[str], why: str, verify: Optional[Dict[str, str]] = None, code: str = "", lang: str = "") -> Dict[str, Any]:
    """stem：題幹；right：正確選項；wrong：3 個誘答；why：解析（要講『為什麼』與誘答錯在哪）；
    verify：{"lang": "tcl|py|verilog|cpp", "code": 可執行的程式, "expect": 輸出中必須包含的字串（也必須出現在 right 裡）}；code/lang：題幹附的程式碼區塊。"""
    return dict(stem=stem, right=right, wrong=list(wrong), why=why, verify=verify, code=code, lang=lang)


def shuffled(q: Dict[str, Any]) -> Dict[str, Any]:
    opts = [q["right"]] + q["wrong"]
    rnd = random.Random(int(hashlib.sha256((q["stem"] + q["code"]).encode("utf-8")).hexdigest()[:12], 16))
    order = list(range(4))
    rnd.shuffle(order)
    return {"stem": q["stem"], "code": q["code"], "lang": q["lang"], "options": [opts[i] for i in order], "answer": order.index(0), "why": q["why"]}


def _run(cmd: List[str], cwd: str, timeout: int = 30) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=timeout)
    out = r.stdout.decode("utf-8", "replace")
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} 失敗：{r.stderr.decode('utf-8', 'replace')[-400:]}")
    return out


def run_verify(v: Dict[str, str]) -> str:
    lang, code = v["lang"], v["code"]
    with tempfile.TemporaryDirectory() as d:
        if lang == "tcl":
            Path(d, "t.tcl").write_text(code, encoding="utf-8")
            return _run(["tclsh", "t.tcl"], d)
        if lang == "py":
            Path(d, "t.py").write_text(code, encoding="utf-8")
            return _run([sys.executable, "-I", "t.py"], d)
        if lang == "verilog":
            Path(d, "t.v").write_text(code, encoding="utf-8")
            _run(["iverilog", "-g2012", "-o", "sim", "t.v"], d)
            return _run(["vvp", "-n", "sim"], d)
        if lang == "cpp":
            Path(d, "t.cpp").write_text(code, encoding="utf-8")
            exe = "t.exe" if os.name == "nt" else "t"
            _run(["g++", "-std=c++17", "-O0", "-o", exe, "t.cpp"], d, 120)
            return _run([str(Path(d, exe))], d)
    raise ValueError("verify.lang 只能是 tcl／py／verilog／cpp")


_cpp_ok: Optional[bool] = None


def available(lang: str) -> bool:
    global _cpp_ok
    if lang == "py":
        return True
    if lang == "cpp":                                   # 題目用 <bits/stdc++.h>（GCC 專有）：macOS 的 g++ 是 clang，沒有這個標頭
        if _cpp_ok is None:
            _cpp_ok = False
            if shutil.which("g++"):
                with tempfile.TemporaryDirectory() as d:
                    Path(d, "a.cpp").write_text("#include <bits/stdc++.h>\nint main(){}\n", encoding="utf-8")
                    _cpp_ok = subprocess.run(["g++", "-std=c++17", "-o", os.path.join(d, "a"), os.path.join(d, "a.cpp")], capture_output=True).returncode == 0
        return _cpp_ok
    need = {"tcl": ["tclsh"], "verilog": ["iverilog", "vvp"]}[lang]
    return all(shutil.which(x) for x in need)


def check_question(q: Dict[str, Any], where: str, strict_verify: bool = True) -> int:
    """回傳實際執行驗證的次數；有問題就丟 SystemExit。"""
    opts = [q["right"]] + q["wrong"]
    if len(q["wrong"]) != 3 or len({o.strip() for o in opts}) != 4 or any(not o.strip() for o in opts):
        raise SystemExit(f"{where}：要有 1 個正確 + 3 個不同的誘答")
    if len(q["why"]) < 12:
        raise SystemExit(f"{where}：解析太短")
    if q["stem"].count("\n") > 12:
        raise SystemExit(f"{where}：題幹太長")
    v = q.get("verify")
    if not v:
        return 0
    if not available(v["lang"]):
        if strict_verify:
            raise SystemExit(f"{where}：缺少 {v['lang']} 工具，無法驗證")
        return 0
    out = run_verify(v)
    exp = v["expect"] if isinstance(v["expect"], list) else [v["expect"]]
    norm = lambda t: t.replace("`", "")  # noqa: E731
    for e in exp:
        if e not in out:
            raise SystemExit(f"{where}：實際輸出沒有 {e!r}：\n{out[-300:]}")
        if not v.get("free") and e not in q["right"]:
            raise SystemExit(f"{where}：驗證用的期望值 {e!r} 沒出現在正確選項裡")
    if len(exp) == 1 and not v.get("free"):
        for w in q["wrong"]:
            if norm(w) == norm(exp[0]):
                raise SystemExit(f"{where}：誘答與正確答案相同 {exp[0]!r}")
    return 1


def render_markdown(g: Dict[str, Any]) -> str:
    out: List[str] = [f"# {g['title']}", "", g["subtitle"], ""]
    out += ["## 一、這份指南怎麼用", "", g["howto"], ""]
    out += ["## 二、學習地圖", "", g["map"], ""]
    n = 3
    for sec in g["sections"]:
        out += [f"## {cn(n)}、{sec['title']}", "", sec["body"], ""]
        n += 1
    out += [f"## {cn(n)}、易混淆重點與必背速查表", "", g["confusions"], ""]
    n += 1
    qn = 0
    for grp in g["groups"]:
        out += [f"## {cn(n)}、{grp['title']}（共 {len(grp['questions'])} 題）", ""]
        n += 1
        sh = [shuffled(q) for q in grp["questions"]]
        for i, q in enumerate(sh, 1):
            out += [f"**{i}.** {q['stem']}", ""]
            if q["code"]:
                out += [f"```{q['lang']}", q["code"].rstrip("\n"), "```", ""]
            out += [f"- {LETTERS[k]}. {o}" for k, o in enumerate(q["options"])] + [""]
        out += [f"### {grp['title']}解答與解析", ""]
        out += [f"- **{i}. {LETTERS[q['answer']]}**　{q['why']}" for i, q in enumerate(sh, 1)] + [""]
        qn += len(sh)
    return "\n".join(out).rstrip() + "\n"


def to_quiz_json(g: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": g["id"], "track": g["track"], "title": g["title"],
            "groups": [{"title": grp["title"], "unit": grp.get("unit"), "questions": [shuffled(q) for q in grp["questions"]]} for grp in g["groups"]]}
