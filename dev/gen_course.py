"""產生 course.json、problems_extra.json 與 COURSE.md。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
import course_data as C  # noqa: E402

DATA = ROOT / "cpe_coach" / "data"

EXTRA = [  # (編號, 標題, 階段, 難度, 主題)
    (10004, "Bicoloring", 3, 2, "二分圖著色／BFS"), (10009, "All Roads Lead Where?", 3, 2, "BFS"),
    (10010, "Where's Waldorf?", 4, 2, "字串／網格搜尋"), (10037, "Bridge", 2, 3, "貪心"),
    (10048, "Audiophobia", 3, 3, "minimax 路徑／Floyd"), (10065, "Useless Tile Packers", 4, 3, "凸包"),
    (10099, "The Tourist Guide", 3, 3, "maximin 路徑"), (10104, "Euclid Problem", 3, 3, "擴展歐幾里得"),
    (10115, "Automatic Editing", 4, 2, "字串取代模擬"), (10127, "Ones", 3, 2, "數論／模運算"),
    (10147, "Highways", 3, 3, "MST"), (10192, "Vacation", 3, 2, "LCS"),
    (10344, "23 out of 5", 2, 2, "回溯"), (10465, "Homer Simpson", 3, 2, "DP（完全背包）"),
    (10653, "Bombs! NO they are Mines!!", 3, 2, "BFS（網格）"), (10901, "Ferry Loading III", 2, 2, "queue 模擬"),
    (10926, "How Many Dependencies?", 3, 2, "DFS／DAG"), (10935, "Throwing cards away I", 2, 1, "queue 模擬"),
    (11060, "Beverages", 3, 2, "拓撲排序"), (11136, "Hoax or what", 2, 2, "heap／multiset"),
    (11221, "Magic Square Palindromes", 4, 2, "字串／迴文"), (11389, "The Bus Driver Problem", 2, 2, "貪心／排序"),
    (11437, "Triangle Fun", 4, 3, "計算幾何"), (11626, "Convex Hull", 4, 3, "凸包"),
    (11747, "Heavy Cycle Edges", 3, 3, "MST"), (11902, "Dominator", 3, 2, "DFS 可達性"),
    (11995, "I Can Guess the Data Structure!", 2, 2, "stack／queue／priority queue"), (12100, "Printer Queue", 2, 2, "queue 模擬"),
    (191, "Intersection", 4, 3, "計算幾何（線段與矩形）"), (341, "Non-Stop Travel", 3, 2, "Dijkstra 與路徑"),
    (357, "Let Me Count The Ways", 3, 2, "DP（零錢）"), (374, "Big Mod", 3, 2, "快速冪"),
    (378, "Intersecting Lines", 4, 3, "計算幾何"), (401, "Palindromes", 4, 2, "字串／迴文與鏡像"),
    (439, "Knight Moves", 3, 2, "BFS"), (507, "Jill Rides Again", 3, 2, "最大子段和"),
    (514, "Rails", 2, 2, "stack"), (524, "Prime Ring Problem", 2, 3, "回溯"),
    (562, "Dividing coins", 3, 2, "背包"), (567, "Risk", 3, 2, "Floyd"),
    (583, "Prime Factors", 3, 2, "質因數分解"), (673, "Parentheses Balance", 2, 1, "stack"),
    (674, "Coin Change", 3, 2, "DP（零錢）"), (681, "Convex Hull Finding", 4, 3, "凸包"),
    (750, "8 Queens Chess Problem", 2, 3, "回溯"), (821, "Page Hopping", 3, 2, "Floyd／BFS"),
    (825, "Walking on the Safe Side", 3, 2, "格子 DP"),
]


def main():
    extra = [{"id": f"uva{n}", "title": t, "source": "UVA", "number": n, "stage": s, "difficulty": d, "topic": top,
              "hint_category": f"這題的主題：{top}。", "hint_insight": None,
              "url": f"https://vjudge.net/problem/UVA-{n}", "official_one_star": False, "unverified": True}
             for n, t, s, d, top in EXTRA]
    (DATA / "problems_extra.json").write_text(json.dumps(extra, ensure_ascii=False, indent=1), encoding="utf-8")

    w = 1
    for i, u in enumerate(C.UNITS, 1):
        u["n"], u["start"] = i, w
        w += u["weeks"]
    course = {"rhythm": [{"day": a, "name": b, "what": c} for a, b, c in C.RHYTHM],
              "resources": {k: {"name": v[0], "url": v[1]} for k, v in C.RES.items()},
              "total_weeks": w - 1, "units": C.UNITS}
    (DATA / "course.json").write_text(json.dumps(course, ensure_ascii=False, indent=1), encoding="utf-8")
    write_md(course)
    print("units", len(C.UNITS), "weeks", w - 1, "extra anchors", len(extra))


STAGE_NAMES = {0: "階段 0 · Python 語法基礎", 1: "階段 1 · 競程 I/O 與一顆星", 2: "階段 2 · 資料結構與基礎演算法",
               3: "階段 3 · 圖論與 DP", 4: "階段 4 · 進階演算法與 C++", 5: "階段 5 · 衝刺 6 題"}
STAGE_TARGET = {0: "CPE 0→1 題", 1: "CPE 2 題（首次報考）", 2: "CPE 3 題（A-）", 3: "CPE 4 題（A）", 4: "CPE 5 題", 5: "CPE 6 題（A+）"}


def write_md(course):
    drills = {d["id"]: d for d in json.loads((DATA / "drills" / "index.json").read_text(encoding="utf-8"))}
    bank = {p["id"]: p for p in json.loads((DATA / "problems.json").read_text(encoding="utf-8"))}
    bank.update({p["id"]: p for p in json.loads((DATA / "problems_extra.json").read_text(encoding="utf-8"))})
    res = course["resources"]

    def name(pid):
        p = drills.get(pid) or bank.get(pid)
        return f"`{pid}` {p['title']}" if p else f"`{pid}`"

    o = ["# CPE 6 題完整課程（126 週）", "",
         "從零基礎到 CPE 一次 6 題。總長 **126 週（約 29 個月）**，每週約 9 小時（每天 1.5 小時、一週 6 天）。",
         "", "> **這份課程保證什麼、不保證什麼**",
         "> - 保證：涵蓋 CPE 一～四顆星題目需要的知識，每個單元有可驗證的檢核點（`cpe gate`），不會讓你『以為學會了』。",
         "> - 不保證：6 題是全國前 1% 的成績（約 0.7%）。課程內的模擬考難度是我自己估的，**真實 CPE 的成績才是最終檢核**；",
         ">   卡在平台期延長 6–12 個月很正常。每個階段結尾都安排一次真實 CPE 報考。", "",
         "## 一週怎麼過", "", "| 天 | 做什麼 | 內容 |", "|---|---|---|"]
    for r in course["rhythm"]:
        o.append(f"| {r['day']} | {r['name']} | {r['what']} |")
    o += ["", "## 全覽", "", "| 週 | # | 單元 | 檢核 |", "|---|---|---|---|"]
    for u in course["units"]:
        a, b = u["start"], u["start"] + u["weeks"] - 1
        wk = f"{a}" if a == b else f"{a}–{b}"
        g = u["gate"]
        gate = "—" if not g else (f"模擬考 {g['kind']} 答對 ≥ {g['need']}" if g["type"] == "mock"
                                  else f"{len(g['problems'])} 題限時 {g['minutes']} 分，答對 ≥ {g['need']}")
        o.append(f"| {wk} | {u['n']} | {u['title']} | {gate} |")
    cur = None
    for u in course["units"]:
        if u["stage"] != cur:
            cur = u["stage"]
            o += ["", f"---", "", f"## {STAGE_NAMES[cur]}　（目標：{STAGE_TARGET[cur]}）", ""]
        a, b = u["start"], u["start"] + u["weeks"] - 1
        o += [f"### 單元 {u['n']}　{u['title']}　（第 {a}{'' if a == b else '–' + str(b)} 週）", "", f"**學完你能：**{u['goal']}", ""]
        if u["lang"] == "cpp":
            o += ["**語言：C++**（`cpe new <題號> --lang cpp`）", ""]
        o += ["**要學的：**"] + [f"- {x}" for x in u["learn"]] + [""]
        if u["drills"]:
            o += ["**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**"] + [f"- {name(d)}" for d in u["drills"]] + [""]
        if u["anchors"]:
            o += ["**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**", "- " + "、".join(name(a) for a in u["anchors"]), ""]
        if u["pool"]:
            o += ["**延伸題庫：**"] + [f"- {x}" for x in u["pool"]] + [""]
        if u.get("read"):
            o += ["**要讀的章節：**"] + [f"- {x}" for x in u["read"]] + [""]
        if u["resources"]:
            o += ["**教材：**" + "、".join(f"[{res[r]['name']}]({res[r]['url']})" for r in u["resources"]), ""]
        if u["pitfalls"]:
            o += ["**常見陷阱：**"] + [f"- {x}" for x in u["pitfalls"]] + [""]
        if u["check"]:
            o += ["**自我檢查（不看資料回答）：**"] + [f"- {x}" for x in u["check"]] + [""]
        if u["eng"]:
            o += ["**工程任務：**" + "；".join(f"#{n}" for n in u["eng"]) + "（`cpe eng` 查看）", ""]
        g = u["gate"]
        if g:
            if g["type"] == "mock":
                o += [f"**檢核（`cpe gate`）：**模擬考（{g['kind']}），至少答對 {g['need']} 題。", ""]
            else:
                lang = "，用 C++" if g["lang"] == "cpp" else ""
                o += [f"**檢核（`cpe gate`）：**從空白檔、不看提示，{g['minutes']} 分鐘內完成 " + "、".join(name(p) for p in g["problems"]) + f"，至少答對 {g['need']} 題{lang}。", ""]
        else:
            o += ["**檢核：**實際報考並記錄成績。", ""]
    o += ["---", "", "## 教材總表", ""] + [f"- [{v['name']}]({v['url']})" for v in res.values()]
    o += ["", "_網址可能變動，失效請自行搜尋名稱；章節編號以教材目錄為準。_", ""]
    (ROOT / "COURSE.md").write_text("\n".join(o), encoding="utf-8")


if __name__ == "__main__":
    main()
