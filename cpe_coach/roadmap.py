"""學習路線與工程能力清單（來源：docs/research-report.md 第 2、6、7 節）。

時數與月份是報告的「經驗估計」，不是研究結論；進度停滯時延長是正常的。
"""
from __future__ import annotations

import datetime as dt
from typing import Dict, List

STAGES: List[Dict] = [
    {"n": 0, "name": "Python 語法基礎", "end_month": 3, "hours": "120–180",
     "content": "變數、型別、if/for/while、函式、list/str/dict；多組輸入讀到 EOF",
     "practice": "80–120 題入門題（ZeroJudge a 字頭、APCS 初級）",
     "checkpoint": "能獨立寫出讀多組測資到 EOF 的程式；完成 60 題入門題", "cpe_goal": "0 → 1 題"},
    {"n": 1, "name": "競程 I/O 與一顆星選集", "end_month": 7, "hours": "100–150",
     "content": "sys.stdin、格式化輸出、字串、進位轉換、質數篩、GCD、模擬",
     "practice": "一顆星選集 49 題全部自己寫完並能重寫",
     "checkpoint": "49 題能在 30 分鐘內重寫任一題；CPE 達 2 題（多數學校畢業門檻）", "cpe_goal": "2–3 題"},
    {"n": 2, "name": "資料結構與基礎演算法", "end_month": 11, "hours": "150–200",
     "content": "排序（自訂 key）、二分、前綴和、雙指標、stack/queue/heap、set/dict、貪心、遞迴與窮舉",
     "practice": "100–150 題（AP325 前半、UVA 二顆星）；開始建立 Git 習慣",
     "checkpoint": "報考 APCS 中級或中高級實作；CPE 達 3 題（A-）", "cpe_goal": "3–4 題"},
    {"n": 3, "name": "圖論與 DP", "end_month": 17, "hours": "200–300",
     "content": "BFS/DFS、連通元件、拓撲排序、Dijkstra、並查集、背包／LIS／LCS／區間 DP、模運算與快速冪",
     "practice": "120–200 題（AP325 後半、UVA 三顆星、Codeforces 800–1300）",
     "checkpoint": "CPE 達 4 題（A）；完成一個含 pytest 的 CLI 專案", "cpe_goal": "4 題"},
    {"n": 4, "name": "進階演算法與 C++", "end_month": 24, "hours": "250–400",
     "content": "進階 DP／圖論、最小生成樹、回溯剪枝、計算幾何入門、複雜度估算、C++ STL",
     "practice": "150 題以上；每月一場 3 小時全真模擬",
     "checkpoint": "CPE 達 5 題；同一題能用 C++ 改寫並通過時限", "cpe_goal": "5 題"},
    {"n": 5, "name": "衝刺 6 題", "end_month": 30, "hours": "—",
     "content": "專攻三、四顆星題型；檢討歷屆答對率低於 5% 的題目",
     "practice": "歷屆低答對率題目 + 每月全真模擬",
     "checkpoint": "CPE 6 題（A+）；Web 專案上線、作品集完成", "cpe_goal": "6 題"},
]

# 工程能力線：報告建議從階段 2 起每週撥 20–30% 時間
ENGINEERING: List[Dict] = [
    {"n": 1, "min_stage": 2, "task": "把每天的解題程式碼 commit 到 GitHub（git init、commit、branch、.gitignore）"},
    {"n": 2, "min_stage": 2, "task": "學會開 PR：在自己的 repo 開一個 branch、發 PR、自己 review 後 merge"},
    {"n": 3, "min_stage": 2, "task": "用 pytest 為 3 個舊題目寫測試，包含邊界案例"},
    {"n": 4, "min_stage": 2, "task": "寫一個『暴力解 vs 正解』的對拍腳本（也可用 cpe stress）"},
    {"n": 5, "min_stage": 3, "task": "建立虛擬環境與 pyproject.toml，加上型別提示與 ruff／flake8"},
    {"n": 6, "min_stage": 3, "task": "SQL 基礎：用 SQLite 存題目與提交紀錄，練習 JOIN 與 GROUP BY"},
    {"n": 7, "min_stage": 3, "task": "用 argparse／typer 做一個 CLI 小專案並附 pytest"},
    {"n": 8, "min_stage": 4, "task": "用 FastAPI 或 Flask 做一個 Web API，加上基本測試"},
    {"n": 9, "min_stage": 4, "task": "把 Web 服務部署上線（任一雲端平台），並寫 README"},
    {"n": 10, "min_stage": 4, "task": "呼叫 LLM API 做一個小應用，加上成本上限與錯誤處理"},
    {"n": 11, "min_stage": 5, "task": "整理作品集：3 個專案各附 README、測試、說明文件"},
]


def add_months(d: dt.date, months: int) -> dt.date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28, 31, 30, 31, 30,
                      31, 31, 30, 31, 30, 31][m - 1])
    return dt.date(y, m, day)


def target_date(start: dt.date, stage: Dict) -> dt.date:
    return add_months(start, stage["end_month"])


def expected_stage(start: dt.date, today: dt.date) -> int:
    """依時程表，今天『應該』在哪個階段。"""
    for s in STAGES:
        if today <= target_date(start, s):
            return s["n"]
    return STAGES[-1]["n"]
