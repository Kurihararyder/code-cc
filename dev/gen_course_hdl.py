"""產生 Verilog 與 Tcl 軌道：cpe_coach/data/course_verilog.json、course_tcl.json 與 COURSE_VERILOG.md、COURSE_TCL.md，並驗證資料。

驗證：HDLBits 題目名稱存在、Tcl 教學課號在 0–48、Tcl 指令名稱在 8.6 手冊、Harris 章號在 1–9、資源都有定義、檢核有效、規劃題號唯一。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
import course_hdl_data as D  # noqa: E402
import course_hdl_refs as REF  # noqa: E402
import course_tcl_data as T  # noqa: E402
import course_verilog_data as V  # noqa: E402

DATA = ROOT / "cpe_coach" / "data"

RHYTHM_V = [
    ("第 1 天", "新概念", "讀教材；每個概念先在紙上畫出電路，再寫 Verilog；用模擬器跑一個最小範例。"),
    ("第 2 天", "概念練習", "做本單元前半的 HDLBits 題目；卡住先看波形，不要先看答案。"),
    ("第 3 天", "鞏固", "做後半的題目；每題通過後用 Verilator lint 與 Yosys 再檢查一次可合成性。"),
    ("第 4 天", "實作", "做本單元的 build 作業；先寫 testbench 再寫設計。"),
    ("第 5 天", "重寫日", "把用過提示的題目關掉資料，從空白檔重寫；試著換一種寫法再通過。"),
    ("第 6 天", "檢核", "單元最後一週做檢核（作品單元逐條驗收）。"),
    ("第 7 天", "休息", "不寫程式。"),
]
RHYTHM_T = [
    ("第 1 天", "新概念", "讀教材與手冊；在 tclsh 裡逐行實驗，每個替換規則寫一個『預測再驗證』的例子。"),
    ("第 2 天", "概念練習", "做本單元前半的練習題（用 tclsh 判題）。"),
    ("第 3 天", "鞏固", "做後半的題目；每題通過後用 `info`／`puts` 檢查中間值。"),
    ("第 4 天", "實作", "做本單元的 build 作業；先寫測試再寫程式。"),
    ("第 5 天", "重寫日", "把用過提示的題目關掉資料，從空白檔重寫。"),
    ("第 6 天", "檢核", "單元最後一週做檢核（作品單元逐條驗收）。"),
    ("第 7 天", "休息", "不寫程式。"),
]

TRACKS = {
    "verilog": dict(
        title="Verilog／SystemVerilog 軌道：從數位邏輯到 RTL、驗證與實體流程", lang="verilog", units=V.UNITS, rhythm=RHYTHM_V,
        stages=[("V0", "數位邏輯與第一個電路", "能獨立寫出、模擬並除錯一個小型數位設計，並知道它能不能合成。"),
                ("V1", "RTL 設計", "能設計資料路徑與控制、FIFO、算術電路、跨時脈域與一顆 RISC-V 處理器，寫出模擬與合成一致的程式。"),
                ("V2", "驗證", "能做驗證計畫、自我檢查環境、cocotb 與 SystemVerilog 驗證、斷言與形式驗證、覆蓋率與回歸。"),
                ("V3", "合成、時序與實體流程", "能合成、讀寫 SDC、做時序分析與收斂、低功耗與 DFT 概念，並用開源流程做到版圖或 FPGA。"),
                ("V4", "SoC、專題與職涯", "能整合 SoC、完成處理器、加速器與下線流程三個專題，並通過面試等級的說明。")],
        file="course_verilog.json", md="COURSE_VERILOG.md",
        intro="這條軌道的終點是**能在公司擔任數位 IC 的設計或驗證工程師**：寫得出可合成的 RTL、做得出有覆蓋與形式證明的驗證、看得懂時序與實體報告、做過一次從 RTL 到版圖（或 FPGA）的完整流程。",
        ability=[("V0", "寫出並模擬組合與序列電路、狀態機與自我檢查的 testbench；知道什麼寫法不能合成"),
                 ("V1", "設計資料路徑與控制、FIFO、算術電路、CDC 與 RISC-V 單週期與管線處理器；通過 lint 與合成"),
                 ("V2", "替設計建立驗證計畫與環境（SV 或 cocotb）、斷言與形式驗證、覆蓋率與回歸；能讀懂 UVM 環境"),
                 ("V3", "用 Yosys 合成、寫 SDC、讀時序報告並收斂、低功耗與 DFT 的概念；用 OpenLane 走完到 GDS 或實作到 FPGA"),
                 ("V4", "整合 SoC 與韌體、完成核心與加速器專題、走完下線流程、面試與作品集")],
        status=["練習題：本軌道用 HDLBits（外部、免費、線上判題）；{n_hdl} 題以名稱引用（名稱已逐一核對）。另有 **{n_pl}** 題標為 *待新增*（用 iverilog 編譯＋vvp 執行測試台、比對輸出；判題器尚未實作）。",
                "判題的可行性：我在開發環境實測過 iverilog 能編譯、vvp 能執行測試台，並分辨出正確與錯誤的設計；Yosys 也能執行。學員需要自己安裝這些工具。",
                "作品驗收（type=project）是**人工對照驗收標準**：效能、設計品質與驗證完整度沒辦法只靠輸入輸出判斷。",
                "商用 EDA（Design Compiler、PrimeTime、Innovus、Questa、VCS、Xcelium）需要授權，無法在這裡驗證；本課綱改用開源工具（Yosys、OpenSTA、OpenROAD、OpenLane、Verilator、iverilog、cocotb、SymbiYosys），概念可遷移，指令不同。完整的 UVM 需要支援它的模擬器（多為商用），UVM 單元以閱讀與對照為主。",
                "介面還沒有『切換軌道』，也還沒有各自的進度；目前是課綱與驗證過的資料。"]),
    "tcl": dict(
        title="Tcl 軌道：從零基礎到 EDA 流程腳本工程師", lang="tcl", units=T.UNITS, rhythm=RHYTHM_T,
        stages=[("T0", "Tcl 語言", "能寫出有分支、迴圈、函式、資料結構、文字處理與錯誤處理的 Tcl 腳本，並理解替換規則。"),
                ("T1", "工程化 Tcl", "能把腳本組織成套件、寫測試、解析報告、控制外部程式與並行、用 TclOO 建模。"),
                ("T2", "EDA 腳本實務", "能寫 SDC、驅動 Yosys／OpenSTA／OpenROAD、做設計產生器與參數掃描、建立回歸與 CI。"),
                ("T3", "作品與面試", "完成流程執行器、報告分析工具與 RTL 到版圖自動化三個專題，並通過面試等級的說明。")],
        file="course_tcl.json", md="COURSE_TCL.md",
        intro="這條軌道的終點是**能替 IC 設計團隊寫與維護流程腳本**：寫約束、跑工具、解析報告、做回歸與參數探索，而且寫得出有測試、可重現的工具。Tcl 之所以重要：EDA 工具幾乎都用它當腳本與設定語言，SDC 本身就是 Tcl。",
        ability=[("T0", "寫出正確的 Tcl：替換規則、控制流、proc、list／dict、字串與正規表示式、檔案與外部程式、錯誤處理"),
                 ("T1", "模組化（namespace／package）、tcltest 測試、報告解析、並行與事件、TclOO"),
                 ("T2", "SDC 約束、Yosys／OpenSTA／OpenROAD 的 Tcl 介面、設計產生器、參數掃描、回歸與 CI；能讀懂商用工具腳本"),
                 ("T3", "流程執行器、報告分析與回歸偵測、RTL 到版圖自動化；面試與作品集")],
        status=["練習題：**{n_pl}** 題標為 *待新增*（用 tclsh 執行、比對輸出，判題器尚未實作）；我在開發環境實測過 tclsh 能執行腳本並輸出結果。",
                "教材：Tcl 官方教學（8.5 版 0–48 課，課號已逐一核對）與 Tcl 8.6 指令手冊（指令名稱已逐一核對）。",
                "作品驗收（type=project）是**人工對照驗收標準**。",
                "商用 EDA 的 Tcl 指令（Design Compiler、PrimeTime、Innovus、Vivado 等）需要授權，無法在這裡驗證；SDC 與 OpenSTA／OpenROAD／Yosys 的 Tcl 介面是開源可練習的對應。",
                "介面還沒有『切換軌道』，也還沒有各自的進度；目前是課綱與驗證過的資料。"]),
}


def split(lst, k):
    q, r = divmod(len(lst), k)
    out, i = [], 0
    for j in range(k):
        n = q + (1 if j < r else 0)
        out.append(lst[i:i + n])
        i += n
    return out


def label(src, where, ch):
    if src == "hdlbits":
        return "HDLBits：" + where
    if src == "harris":
        return f"Harris & Harris《{REF.HARRIS[ch]}》（{where}）"
    if src == "tcltut":
        return "Tcl 教學第 " + where + " 課"
    if src == "tclman":
        return "Tcl 手冊：" + where
    return where


def lesson_errors(spec):
    for tok in [t.strip() for t in spec.split("、") if t.strip()]:
        m = re.match(r"^(\d+)(?:–(\d+))?$", tok)
        if not m:
            return f"看不懂的課號 {tok}"
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        if not (0 <= a <= b <= REF.TCL_LESSONS):
            return f"課號 {tok} 超出 0–{REF.TCL_LESSONS}"
    return None


def validate(track, units):
    errs = []
    planned_seen = {}
    for n, u in enumerate(units, 1):
        w = f"[{track}] 單元 {n}《{u['title']}》"
        if not (u["goal"] and u["learn"] and u["readings"]):
            errs.append(f"{w}: 缺 goal／learn／readings")
        if not 0 <= u["stage"] < len(TRACKS[track]["stages"]):
            errs.append(f"{w}: stage 超出範圍")
        for p in u["planned"]:
            if p["id"] in planned_seen:
                errs.append(f"{w}: 規劃題號 {p['id']} 重複")
            planned_seen[p["id"]] = n
        for src, where, focus, extra in u["readings"]:
            if src not in D.RES:
                errs.append(f"{w}: 不認得的來源 {src}")
            if not focus:
                errs.append(f"{w}: {src} 沒有重點")
            if src == "hdlbits":
                sec, _, names = where.partition("｜")
                if sec not in REF.HDLBITS:
                    errs.append(f"{w}: HDLBits 沒有章節 {sec}")
                else:
                    for nm in [x.strip() for x in names.split("、") if x.strip()]:
                        if nm not in REF.HDLBITS[sec]:
                            errs.append(f"{w}: HDLBits『{sec}』沒有題目 {nm}")
            elif src == "harris":
                if extra not in REF.HARRIS:
                    errs.append(f"{w}: Harris 沒有第 {extra} 章")
            elif src == "tcltut":
                e = lesson_errors(where)
                if e:
                    errs.append(f"{w}: Tcl 教學 {e}")
            elif src == "tclman":
                for c in [x.strip() for x in where.split("、") if x.strip()]:
                    if c not in REF.TCL_CMDS:
                        errs.append(f"{w}: Tcl 8.6 手冊沒有指令 {c}")
        g = u["gate"]
        if not g:
            errs.append(f"{w}: 沒有檢核")
            continue
        if g["type"] == "hdlbits":
            for item in g["problems"]:
                sec, _, nm = item.partition("｜")
                if nm not in REF.HDLBITS.get(sec, []):
                    errs.append(f"{w}: 檢核題 {item} 不存在")
            if not 1 <= g["need"] <= len(g["problems"]):
                errs.append(f"{w}: need 不合理")
        elif g["type"] == "planned":
            for pid in g["problems"]:
                if pid not in planned_seen:
                    errs.append(f"{w}: 檢核用的規劃題 {pid} 還沒定義（要在這個單元或更早的單元）")
            if not 1 <= g["need"] <= len(g["problems"]):
                errs.append(f"{w}: need 不合理")
        elif g["type"] == "project":
            if len(g["criteria"]) < 2:
                errs.append(f"{w}: 作品驗收至少 2 條標準")
        else:
            errs.append(f"{w}: 未知的檢核類型 {g['type']}")
    return errs


def weekly(u):
    w = u["weeks"]
    rs, ls, pl = split(u["readings"], w), split(u["learn"], w), split(u["planned"], w)
    out = []
    for i in range(w):
        last = i == w - 1
        out.append({"week": u["start"] + i, "readings": [r["label"] for r in rs[i]], "learn": ls[i], "planned": [p["id"] for p in pl[i]],
                    "build": u["build"] if last else [], "gate": last})
    return out


def build(track):
    spec = TRACKS[track]
    units = []
    start = 1
    for n, u in enumerate(spec["units"], 1):
        u = dict(u)
        u["n"], u["start"], u["lang"] = n, start, spec["lang"]
        start += u["weeks"]
        units.append(u)
    errs = validate(track, units)
    if errs:
        print("\n".join(errs))
        sys.exit(1)
    for u in units:
        u["readings"] = [{"src": s, "where": wh, "focus": f, "chapter": ex if s == "harris" else None, "label": label(s, wh, ex)} for s, wh, f, ex in u["readings"]]
        u["weekly"] = weekly(u)
    out = {"track": track, "title": spec["title"], "rhythm": [list(r) for r in spec["rhythm"]], "resources": {k: list(v) for k, v in D.RES.items()},
           "stages": [{"id": a, "title": b, "goal": c} for a, b, c in spec["stages"]], "total_weeks": start - 1, "units": units}
    (DATA / spec["file"]).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (ROOT / spec["md"]).write_text(render(spec, out), encoding="utf-8")
    n_pl = sum(len(u["planned"]) for u in units)
    n_hdl = len({(r["where"]) for u in units for r in u["readings"] if r["src"] == "hdlbits"})
    print(f"{track}：{len(units)} 個單元、{start - 1} 週、{n_pl} 題待新增、{sum(len(u['readings']) for u in units)} 個閱讀項目、{n_hdl} 組 HDLBits 指向")


def gate_text(g):
    if g["type"] == "hdlbits":
        return [f"**檢核**：完成這些 HDLBits 題目（{g['need']}／{len(g['problems'])} 題以上）：" + "、".join(f"`{p.split('｜')[1]}`" for p in g["problems"])]
    if g["type"] == "planned":
        return [f"**檢核**：{g['minutes']} 分鐘內完成新增題目 " + "、".join(f"`{p}`" for p in g["problems"]) + f" 其中 {g['need']} 題（題目尚待新增）"]
    return [f"**作品驗收**（{g['days']} 天內，逐條對照）："] + [f"- [ ] {x}" for x in g["criteria"]]


def render(spec, c):
    tw = c["total_weeks"]
    n_pl = sum(len(u["planned"]) for u in c["units"])
    n_hdl = len({r["where"] for u in c["units"] for r in u["readings"] if r["src"] == "hdlbits"})
    L = [f"# {spec['title']}（{tw} 週，{len(c['units'])} 個單元）", "", f"> 由 `dev/gen_course_hdl.py` 產生，不要手改；修改請編輯 `dev/course_{spec['lang']}_data.py`。", "",
         spec["intro"] + f" 每週約 10–12 小時；{tw} 週約 {round(tw / 4.345)} 個月。週數是估計，請依自己的進度調整。", "", "## 狀態（誠實版）", ""]
    L += ["- " + s.format(n_pl=n_pl, n_hdl=n_hdl) for s in spec["status"]]
    L += ["", "## 階段總覽", "", "| 階段 | 週 | 名稱 | 目標 |", "|---|---|---|---|"]
    for i, s in enumerate(c["stages"]):
        us = [u for u in c["units"] if u["stage"] == i]
        L.append(f"| {s['id']} | {us[0]['start']}–{us[-1]['start'] + us[-1]['weeks'] - 1} | {s['title']} | {s['goal']} |")
    L += ["", "## 每週節奏", ""] + [f"- **{a}（{b}）**：{d}" for a, b, d in c["rhythm"]]
    L += ["", "## 能力標準（各階段結束時）", "", "| 階段 | 你應該能 |", "|---|---|"] + [f"| {a} | {b} |" for a, b in spec["ability"]] + [""]
    L += ["## 單元", ""]
    for i, s in enumerate(c["stages"]):
        L += [f"### 階段 {s['id']}：{s['title']}", "", s["goal"], ""]
        for u in [x for x in c["units"] if x["stage"] == i]:
            a, b = u["start"], u["start"] + u["weeks"] - 1
            L += [f"#### 單元 {u['n']}：{u['title']}（第 {a}{'–' + str(b) if b > a else ''} 週）", "", f"**目標**：{u['goal']}", "", "**學什麼**"] + [f"- {x}" for x in u["learn"]]
            if u["planned"]:
                L += ["", "**待新增題目**："] + [f"- `{p['id']}` {p['title']}：{p['topic']}" for p in u["planned"]]
            if u["build"]:
                L += ["", "**實作作業**："] + [f"- {x}" for x in u["build"]]
            if u["pitfalls"]:
                L += ["", "**常見陷阱**："] + [f"- {x}" for x in u["pitfalls"]]
            if u["check"]:
                L += ["", "**自我檢查**："] + [f"- {x}" for x in u["check"]]
            L += ["", "**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）"]
            for r in u["readings"]:
                L.append(f"- **{r['label']}**")
                L += [f"  - {f}" for f in r["focus"]]
            L += ["", "**每週安排**", "", "| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |", "|---|---|---|---|---|"]
            for wk in u["weekly"]:
                todo = list(wk["build"]) + (["**單元檢核**"] if wk["gate"] else [])
                L.append("| {w} | {r} | {l} | {p} | {t} |".format(w=wk["week"], r="<br>".join(wk["readings"]) or "—", l="<br>".join(wk["learn"]) or "—",
                                                                    p="、".join(f"`{x}`" for x in wk["planned"]) or "—", t="<br>".join(todo) or "—"))
            L += [""] + gate_text(u["gate"]) + [""]
    L += ["## 教材總表", ""] + [f"- [{v[0]}]({v[1]})" if v[1] else f"- {v[0]}" for v in c["resources"].values()]
    L += ["", "_網址可能變動，失效請自行搜尋名稱。_", ""]
    return "\n".join(L) + "\n"


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    for t in TRACKS:
        build(t)


if __name__ == "__main__":
    main()
