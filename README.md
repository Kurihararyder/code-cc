# CPE 自學教練

零基礎 → CPE 一次 6 題 → 工程師。包含：

- **126 週完整課程**（52 個單元、6 個階段）：[COURSE.md](COURSE.md)
- **107 題原創練習題**，題目敘述與測資都已內建，不用上網找題就能從第一天開始練
- 本地判題、提示階梯、間隔重練、單元檢核、模擬考、對拍、統計

研究依據：[docs/research-report.md](docs/research-report.md)。只需要 Python 3.9+（階段 4 起需要 g++），沒有第三方套件。

## 開始

```bash
pip install -e .          # 之後就有 cpe 指令（或用 python -m cpe_coach）
cpe init my-cpe && cd my-cpe
cpe today                 # 今天該做什麼
cpe course                # 目前單元：要學什麼、必做題、教材、陷阱、檢核
```

## 每天的流程

```bash
cpe new d001              # 安裝題目＋測資，建立 solutions/d001.py
cpe statement d001        # 讀題目
cpe test d001             # 本地判題（AC / WA / PE / TLE / RE / CE）
cpe hint d001             # 卡住才用；先改一版、cpe test 後才能升下一級
cpe giveup d001           # 真的不行：24 小時後 cpe solution 才看得到
cpe review                # 到期的『無提示重寫』；重寫用 cpe new d001 --fresh
```

完成單元的必做練習後：

```bash
cpe gate                  # 單元檢核：限時、空白檔、鎖定提示
# 寫完每題 cpe test，然後：
cpe mock finish           # 交卷。通過就自動進入下一個單元
```

其他：`cpe course list`（全部單元）、`cpe course goto N`（已有基礎可跳關）、`cpe mock start`（7 題 3 小時模擬考）、
`cpe mock start --kind weekly`（每週重寫舊題）、`cpe stats`、`cpe eng`（工程任務）、`cpe stress`（對拍）。

## 課程怎麼運作

| 階段 | 週 | 內容 | 真實 CPE 目標 |
|---|---|---|---|
| 0 | 1–12 | Python 語法基礎 | — |
| 1 | 13–28 | 競程 I/O、一顆星題型 | 2 題（首次報考） |
| 2 | 29–44 | 排序／二分／雙指標／stack／heap／貪心／回溯 | 3 題 |
| 3 | 45–70 | 圖論、DP、數論 | 4 題 |
| 4 | 71–100 | C++、STL、計算幾何、進階圖論／字串／DP | 5 題 |
| 5 | 101–126 | 考試策略、弱點修補、低答對率題、全真模擬 | 6 題 |

每週：新概念 → 練習 → 真題 → **重寫日** → 計時檢核 → 休息。階段 2 起加上每週 20–30% 的工程任務。

**題目從哪來**
- `d001–d095`：階段 0–4 的必做練習，原創。
- `e101–e403`：**驗收專用**題，練習單元不會出現，階段檢核與模擬考才用。
- `uva…`：經典 UVA 真題（選做）。題目敘述請到 vjudge／UVA／瘋狂程設閱讀，把題目文字存成檔案後 `cpe import uva10041 題目.txt`，會自動抓 `Sample Input / Output`（或『範例輸入／輸出』）建成測資。

## 誠實的限制

- **6 題是全國前 1% 的成績。** 課程涵蓋需要的知識並用檢核擋住『以為學會了』，但不能保證你一定達成；**真實 CPE 成績才是最終檢核**。每個階段結尾都安排一次真實報考。卡在平台期延長 6–12 個月很正常。
- 課程內的難度星等、模擬考是我自己估的；官網連不上，沒能核對『官方一顆星選集 49 題』與 CPE26 選集，請自行到 [CPE 官網](https://cpe.mcu.edu.tw/) 取得後用 `cpe import` 加入。
- `uva…` 真題的題號／標題憑記憶整理（約 120 題），部分沒有內建提示（標為 `unverified`）；請以 vjudge 連結上的題目為準，發現錯誤用 `cpe add` 覆蓋。
- 教材不是我寫的：每個單元指向免費教材與章節（Python 官方教學、Competitive Programmer's Handbook、CP-Algorithms…），章節編號以書中目錄為準。
- 內建練習題的期望輸出由參考解產生，並經暴力解交叉驗證；但仍可能有我沒發現的問題，發現請告訴我。
- 「暴力解會超時」的說法我實測過（見各題『這題在練什麼』），但超時與否和你的電腦速度有關；`config.json` 的 `timeout_sec` 可調。

## 提示（選用 AI）

沒有金鑰也能完整使用（L1、L2 是內建提示；L0、L3、L4 退回自助清單）。要 AI 提示：

```bash
export OPENAI_API_KEY=...      # 或 ANTHROPIC_API_KEY
export CPE_MODEL=...           # 可選，預設 gpt-4o / claude-sonnet-5-5
```

用 ChatGPT 網頁的話，看 [gpt/README.md](gpt/README.md)。AI 的回饋可能有誤（研究約 37%），**對錯只看測資**。

## 資料在哪

全部在工作區的 `.cpe/`（`state.json` 進度、`events.jsonl` 每次提交與提示的紀錄、`config.json` 設定），純文字，可以 git 備份。

## 開發

```bash
python -m unittest discover -s tests -v
python dev/gen_drills.py && python dev/gen_course.py   # 重新產生題目與課程（dev/ 內含參考解，學習者請勿閱讀）
```
