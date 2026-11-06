"""產生 C++ 軌道：cpe_coach/data/course_cpp.json 與 COURSE_CPP.md，並驗證資料（題目存在、檢核有效、週數連續）。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
import course_cpp_data as C  # noqa: E402

DATA = ROOT / "cpe_coach" / "data"


def validate(units, bank_ids, reserve):
    errs = []
    seen_drill, seen_planned = {}, {}
    for i, u in enumerate(units, 1):
        where = f"單元 {i}《{u['title']}》"
        if not u["learn"] or not u["goal"]:
            errs.append(f"{where}: 缺 goal 或 learn")
        for r in u["resources"]:
            if r not in C.RES:
                errs.append(f"{where}: 沒有資源 {r}")
        for d in u["drills"]:
            if d not in bank_ids:
                errs.append(f"{where}: 題庫沒有 {d}")
            if d in reserve:
                errs.append(f"{where}: {d} 是保留題（只能放在檢核）")
            if d in seen_drill:
                errs.append(f"{where}: {d} 已在單元 {seen_drill[d]} 使用")
            seen_drill[d] = i
        for p in u["planned"]:
            if p["id"] in seen_planned:
                errs.append(f"{where}: 規劃題號 {p['id']} 重複")
            seen_planned[p["id"]] = i
        g = u["gate"]
        if g is None:
            errs.append(f"{where}: 沒有檢核")
            continue
        if g["type"] == "set":
            bad = [x for x in g["problems"] if x not in bank_ids]
            if bad:
                errs.append(f"{where}: 檢核題不存在 {bad}")
            if not any(x not in u["drills"] for x in g["problems"]):
                errs.append(f"{where}: 檢核至少要有一題沒在練習時出現過")
            if not 1 <= g["need"] <= len(g["problems"]):
                errs.append(f"{where}: need 不合理")
        elif g["type"] == "project":
            if len(g["criteria"]) < 2:
                errs.append(f"{where}: 作品驗收至少 2 條標準")
        else:
            errs.append(f"{where}: 未知的檢核類型")
        if u["stage"] < 0 or u["stage"] >= len(C.STAGES):
            errs.append(f"{where}: stage 超出範圍")
    stages = [u["stage"] for u in units]
    if stages != sorted(stages):
        errs.append("階段順序不是遞增")
    return errs, seen_drill, seen_planned


def main():
    bank = json.loads((DATA / "drills" / "index.json").read_text(encoding="utf-8"))
    ids = {d["id"] for d in bank}
    reserve = {d["id"] for d in bank if d.get("reserve")}
    units = [dict(u) for u in C.UNITS]
    start = 1
    for n, u in enumerate(units, 1):
        u["n"], u["start"] = n, start
        start += u["weeks"]
    errs, used, planned = validate(units, ids, reserve)
    if errs:
        print("\n".join(errs))
        sys.exit(1)
    out = {"track": "cpp", "rhythm": [list(r) for r in C.RHYTHM], "resources": {k: list(v) for k, v in C.RES.items()},
           "stages": [{"id": a, "title": b, "goal": c} for a, b, c in C.STAGES], "total_weeks": start - 1, "units": units}
    (DATA / "course_cpp.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (ROOT / "COURSE_CPP.md").write_text(render(out, used, planned), encoding="utf-8")
    print(f"C++ 軌道：{len(units)} 個單元、{start - 1} 週、{len(used)} 題現有題庫、{len(planned)} 題待新增")


def render(c, used, planned):
    L = [f"# C++ 軌道：從零基礎到演算法工程師（{c['total_weeks']} 週，{len(c['units'])} 個單元）", "",
         "> 由 `dev/gen_course_cpp.py` 產生，不要手改；修改請編輯 `dev/course_cpp_data.py`。",
         "",
         f"這條軌道和 Python 軌道（[COURSE.md](COURSE.md)）獨立：Python 軌道的終點是 CPE 一次 6 題；這條的終點是**能在工作上寫出正確、快、可維護的 C++ 演算法程式碼**。"
         f"每週約 10–12 小時；{c['total_weeks']} 週約 {round(c['total_weeks'] / 4.345)} 個月。週數是估計，請依自己的進度調整。", "",
         "## 狀態（誠實版）", "",
         f"- 題庫：本軌道用到現有題庫的 **{len(used)}** 題（C++ 由 g++ 判題）；另有 **{len(planned)}** 題標為 *待新增*（進階演算法與面試題），還沒有題目與測資。",
         "- build 作業與作品驗收（type=project）是**人工對照驗收標準**，不能自動判；這是刻意的：效能、設計與測試品質沒辦法只靠輸入輸出判斷。",
         "- 介面還沒有『切換軌道』：目前這是課綱與驗證過的資料，下一步是新增題目、並讓 `cpe course` 與網頁介面能選軌道、各自保存進度。", "",
         "## 階段總覽", "", "| 階段 | 週 | 名稱 | 目標 |", "|---|---|---|---|"]
    for i, s in enumerate(c["stages"]):
        us = [u for u in c["units"] if u["stage"] == i]
        a, b = us[0]["start"], us[-1]["start"] + us[-1]["weeks"] - 1
        L.append(f"| {s['id']} | {a}–{b} | {s['title']} | {s['goal']} |")
    L += ["", "## 每週節奏", ""] + [f"- **{a}（{b}）**：{d}" for a, b, d in c["rhythm"]]
    L += ["", "## 能力標準（各階段結束時）", "",
          "| 階段 | 你應該能 |", "|---|---|",
          "| C0 | 編譯、除錯一支幾百行的程式；用 sanitizer 抓出 UB；不再被溢位與越界嚇到 |",
          "| C1 | 用 RAII 與智慧指標管理資源；選對 STL 容器並說出複雜度；寫簡單的樣板與 lambda；懂移動語意 |",
          "| C2 | 用 C++ 做完 CPE 等級題目（含四顆星），在時限內，穩定一次 6 題 |",
          "| C3 | 實作線段樹、LCA、SCC、Dinic、Aho-Corasick、NTT、凸包等；Codeforces Div2 C–E／AtCoder ABC E–G 等級 |",
          "| C4 | 量測、剖析並改善效能；懂快取與資料佈局；寫無資料競爭的平行程式；用 CMake＋測試＋CI 維持品質 |",
          "| C5 | 有測試、基準、文件的演算法函式庫與三個專題；通過面試等級的設計與溝通 |", ""]
    L += ["## 單元", ""]
    for i, s in enumerate(c["stages"]):
        L += [f"### 階段 {s['id']}：{s['title']}", "", s["goal"], ""]
        for u in [x for x in c["units"] if x["stage"] == i]:
            a, b = u["start"], u["start"] + u["weeks"] - 1
            L += [f"#### 單元 {u['n']}：{u['title']}（第 {a}{'–' + str(b) if b > a else ''} 週）", "", f"**目標**：{u['goal']}", "", "**學什麼**"]
            L += [f"- {x}" for x in u["learn"]]
            if u["drills"]:
                L += ["", "**題庫題目（用 C++）**：" + "、".join(f"`{d}`" for d in u["drills"])]
            if u["planned"]:
                L += ["", "**待新增題目**："] + [f"- `{p['id']}` {p['title']}：{p['topic']}" for p in u["planned"]]
            if u["build"]:
                L += ["", "**實作作業**："] + [f"- {x}" for x in u["build"]]
            if u["pitfalls"]:
                L += ["", "**常見陷阱**："] + [f"- {x}" for x in u["pitfalls"]]
            if u["check"]:
                L += ["", "**自我檢查**："] + [f"- {x}" for x in u["check"]]
            if u["read"]:
                L += ["", "**閱讀**：" + "；".join(u["read"])]
            L += ["", "**資源**：" + "、".join(f"[{c['resources'][r][0]}]({c['resources'][r][1]})" for r in u["resources"]) if u["resources"] else ""]
            g = u["gate"]
            if g["type"] == "set":
                L += ["", f"**檢核**：{g['minutes']} 分鐘內用 C++ 通過 " + "、".join(f"`{p}`" for p in g["problems"]) + f" 其中 {g['need']} 題"]
            else:
                L += ["", f"**作品驗收**（{g['days']} 天內，逐條對照）："] + [f"- [ ] {x}" for x in g["criteria"]]
            L.append("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
