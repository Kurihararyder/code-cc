# CPE 自學教練

零基礎 → CPE 一次 6 題 → 工程師。把研究報告（[docs/research-report.md](docs/research-report.md)）的結論做成可以直接用的工具：

| 報告的建議 | 這個工具怎麼做 |
|---|---|
| 判題交給測資，不交給 GPT | `cpe test`：本地判題（AC / WA / PE / TLE / RE / CE），每題可有多組測資 |
| 提示階梯，禁止給完整解 | `cpe hint`：L0 題意 → L1 方向 → L2 觀察 → L3 骨架 → L4 錯誤定位；要先有新嘗試才能升級；AI 輸出會過濾長程式碼 |
| 間隔重練 1／3／7 天 | 靠提示或放棄才通過的題目，必須到期後「從空白檔無提示重寫」；沒用提示的一次通過即精熟 |
| 放棄後冷卻 | `cpe giveup` → 24 小時後才能 `cpe solution` |
| 模擬 CPE | `cpe mock start`：7 題（3×★1、2×★2、★3、★4）、3 小時、ICPC 罰時 20 分、提示鎖定 |
| 每週無 AI 測驗 | `cpe mock start --kind weekly`：從空白檔重寫 3 題舊題 |
| 對拍 | `cpe stress`：暴力解 vs 你的解，找到的反例自動存成測資 |
| 客觀指標防止能力錯覺 | `cpe stats`：無提示重寫通過率、提示用量、模擬考題數 |
| 時程與工程能力線 | `cpe roadmap`、`cpe eng` |

只需要 Python 3.9+，沒有任何第三方套件。

## 安裝與開始

```bash
pip install -e .          # 之後就有 cpe 指令（或用 python -m cpe_coach）
cpe init my-cpe && cd my-cpe
cpe today
```

## 每天的流程

```bash
cpe today                 # 今天要做什麼（到期重練、新題、工程任務）
cpe new uva10041          # 建立 solutions/uva10041.py（含讀到 EOF 的模板）
cpe addtest uva10041      # 貼上題目的範例輸入／輸出（或 --in a.in --out a.out）
cpe test uva10041         # 本地判題
cpe hint uva10041         # 卡住才用；先改一版、cpe test 後才能升下一級
cpe giveup uva10041       # 真的不行：24 小時後 cpe solution 才看得到
cpe review                # 重練清單；重寫用 cpe new <題號> --fresh
```

題目敘述不隨附（版權），`cpe today` / `cpe bank` 會給連結與題號，範例測資自己貼進 `cpe addtest`。
想讓 AI 提示看到題目，把敘述存成 `statements/<題號>.txt`。

## AI 提示（選用）

沒有金鑰也能完整使用（L1、L2 是內建提示；L0、L3、L4 退回自助清單）。要 AI 提示：

```bash
export OPENAI_API_KEY=...      # 或 ANTHROPIC_API_KEY
export CPE_MODEL=...           # 可選，預設 gpt-4o / claude-sonnet-5-5
```

用 ChatGPT 網頁的話，看 [gpt/README.md](gpt/README.md)。

## 題庫

內建 70 題經典 UVA 題（階段 1–4，難度 ★–★★★★），每題附 L1、L2 提示。**請注意**：
- 只有 `uva100`、`uva10041` 是研究報告明確點名的官方一顆星選集題；其餘是我依主題與難度挑的練習題，**不代表是官方選集**。
- 階段與星數是粗估。官方一顆星選集 49 題請到 [CPE 官網「環境與教材」](https://cpe.mcu.edu.tw/environment.php) 取得，再用 `cpe add` 補進來；歷屆題目的「全體答對率」才是客觀難度（`cpe add --accuracy`）。
- 提示是我寫的，未逐題上線驗證；如果發現錯誤，請用 `cpe add <id> --insight ...` 覆蓋。
- 2027 年起每場會有一題出自 CPE26 選集，內容我沒查到，請在報考前確認。

## 資料在哪

全部在工作區的 `.cpe/`（`state.json` 進度、`events.jsonl` 每次提交與提示的紀錄、`config.json` 設定），純文字，可以 git 備份。

## 開發

```bash
python -m unittest discover -s tests -v
```
