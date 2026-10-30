# CPE 6 題完整課程（126 週）

從零基礎到 CPE 一次 6 題。總長 **126 週（約 29 個月）**，每週約 9 小時（每天 1.5 小時、一週 6 天）。

> **這份課程保證什麼、不保證什麼**
> - 保證：涵蓋 CPE 一～四顆星題目需要的知識，每個單元有可驗證的檢核點（`cpe gate`），不會讓你『以為學會了』。
> - 不保證：6 題是全國前 1% 的成績（約 0.7%）。課程內的模擬考難度是我自己估的，**真實 CPE 的成績才是最終檢核**；
>   卡在平台期延長 6–12 個月很正常。每個階段結尾都安排一次真實 CPE 報考。

## 一週怎麼過

| 天 | 做什麼 | 內容 |
|---|---|---|
| 第 1 天 | 新概念 | 讀教材 + 在直譯器／Python Tutor 做小實驗；寫下 3 件『我原本以為』與『其實』。 |
| 第 2 天 | 概念練習 | 做本單元前半的 drills（`cpe new` → `cpe test`）。卡住才 `cpe hint`。 |
| 第 3 天 | 鞏固 | 做本單元後半的 drills；每題通過後想：還有別的寫法嗎？複雜度多少？ |
| 第 4 天 | 真題 | 做 anchors（真實 UVA 題，用 `cpe import` 匯入題目）或 pool 的題目；先做 `cpe review` 到期的重練。 |
| 第 5 天 | 重寫日 | 把本週用過提示的題目，關掉所有資料，從空白檔重寫。這是留存率最高的一步。 |
| 第 6 天 | 檢核 | 每週計時測驗（`cpe mock start --kind weekly`）；單元最後一週改做 `cpe gate`。階段 2 起，這天另撥 1–2 小時做工程任務（`cpe eng`）。 |
| 第 7 天 | 休息 | 不寫程式。睡眠是學習的一部分。 |

## 全覽

| 週 | # | 單元 | 檢核 |
|---|---|---|---|
| 1–2 | 1 | 環境、輸入輸出與運算 | 2 題限時 45 分，答對 ≥ 2 |
| 3 | 2 | 條件判斷 | 2 題限時 45 分，答對 ≥ 2 |
| 4–5 | 3 | 迴圈 | 2 題限時 60 分，答對 ≥ 2 |
| 6–7 | 4 | 字串與 list | 2 題限時 60 分，答對 ≥ 2 |
| 8–9 | 5 | set、dict 與函式 | 2 題限時 60 分，答對 ≥ 2 |
| 10 | 6 | 數學基礎與進位制 | 2 題限時 45 分，答對 ≥ 2 |
| 11 | 7 | 二維 list 與簡單模擬 | 2 題限時 45 分，答對 ≥ 2 |
| 12 | 8 | 階段 0 驗收週 | 4 題限時 120 分，答對 ≥ 3 |
| 13–14 | 9 | 競程輸入格式 | 2 題限時 60 分，答對 ≥ 2 |
| 15–16 | 10 | 輸出格式、浮點數與字串映射 | 2 題限時 60 分，答對 ≥ 2 |
| 17–18 | 11 | 大數與進位制 | 2 題限時 60 分，答對 ≥ 2 |
| 19–20 | 12 | 質數、因數與數學觀察 | 2 題限時 45 分，答對 ≥ 2 |
| 21–22 | 13 | 網格與座標模擬 | 2 題限時 60 分，答對 ≥ 2 |
| 23–24 | 14 | 日期、時間與運算式解析 | 2 題限時 60 分，答對 ≥ 2 |
| 25–26 | 15 | 一顆星選集 I | 3 題限時 90 分，答對 ≥ 2 |
| 27–28 | 16 | 階段 1 驗收：一顆星選集 II 與首次報考 | 模擬考 short 答對 ≥ 2 |
| 29–30 | 17 | 複雜度估算與排序 | 2 題限時 60 分，答對 ≥ 2 |
| 31–32 | 18 | 前綴和與二分搜尋 | 2 題限時 60 分，答對 ≥ 2 |
| 33 | 19 | 雙指標與滑動視窗 | 2 題限時 45 分，答對 ≥ 2 |
| 34–35 | 20 | stack、queue 與 deque | 2 題限時 90 分，答對 ≥ 2 |
| 36 | 21 | heap 與優先佇列 | 2 題限時 60 分，答對 ≥ 2 |
| 37–38 | 22 | 貪心演算法 | 2 題限時 75 分，答對 ≥ 2 |
| 39–41 | 23 | 遞迴與回溯 | 2 題限時 75 分，答對 ≥ 2 |
| 42–43 | 24 | 位元運算與子集合枚舉 | 2 題限時 60 分，答對 ≥ 2 |
| 44 | 25 | 階段 2 驗收週 | 模擬考 mock 答對 ≥ 3 |
| 45–46 | 26 | 圖的表示與 BFS / DFS | 2 題限時 60 分，答對 ≥ 2 |
| 47–48 | 27 | 並查集與連通元件 | 2 題限時 60 分，答對 ≥ 2 |
| 49–50 | 28 | 拓撲排序與 DAG | 2 題限時 60 分，答對 ≥ 2 |
| 51–53 | 29 | 最短路徑 | 2 題限時 75 分，答對 ≥ 2 |
| 54–55 | 30 | 最小生成樹 | 2 題限時 75 分，答對 ≥ 2 |
| 56–57 | 31 | DP 入門：一維 DP 與零錢 | 2 題限時 75 分，答對 ≥ 2 |
| 58–59 | 32 | 背包問題 | 2 題限時 75 分，答對 ≥ 2 |
| 60–61 | 33 | 序列 DP：LIS 與 LCS | 2 題限時 75 分，答對 ≥ 2 |
| 62–63 | 34 | 網格 DP | 2 題限時 60 分，答對 ≥ 2 |
| 64–65 | 35 | 區間 DP | 2 題限時 75 分，答對 ≥ 2 |
| 66–67 | 36 | 位元遮罩 DP | 2 題限時 75 分，答對 ≥ 2 |
| 68–69 | 37 | 數論：模運算、質因數與組合數 | 2 題限時 75 分，答對 ≥ 2 |
| 70 | 38 | 階段 3 驗收週 | 模擬考 mock 答對 ≥ 4 |
| 71–74 | 39 | C++ 入門與翻譯舊題 | 2 題限時 90 分，答對 ≥ 2 |
| 75–78 | 40 | C++ STL | 2 題限時 90 分，答對 ≥ 2 |
| 79–82 | 41 | 效能與複雜度 | 2 題限時 90 分，答對 ≥ 2 |
| 83–86 | 42 | 計算幾何 | 2 題限時 90 分，答對 ≥ 2 |
| 87–90 | 43 | 進階圖論 | 2 題限時 90 分，答對 ≥ 2 |
| 91–94 | 44 | 字串演算法與解析 | 2 題限時 90 分，答對 ≥ 2 |
| 95–98 | 45 | 進階 DP、樹與博弈 | 2 題限時 90 分，答對 ≥ 2 |
| 99 | 46 | 進階資料結構 | 2 題限時 90 分，答對 ≥ 2 |
| 100 | 47 | 階段 4 驗收週 | 模擬考 mock 答對 ≥ 5 |
| 101–104 | 48 | 考試策略與工具箱 | 模擬考 mock 答對 ≥ 4 |
| 105–110 | 49 | 弱點修補 | 模擬考 mock 答對 ≥ 5 |
| 111–118 | 50 | 低答對率題攻堅 | 模擬考 mock 答對 ≥ 5 |
| 119–124 | 51 | 全真模擬週 | 模擬考 mock 答對 ≥ 6 |
| 125–126 | 52 | 報考與作品集 | — |

---

## 階段 0 · Python 語法基礎　（目標：CPE 0→1 題）

### 單元 1　環境、輸入輸出與運算　（第 1–2 週）

**學完你能：**能安裝並執行 Python，讀入資料、計算、格式化輸出，並讀到檔案結尾（EOF）。

**要學的：**
- 安裝 Python 3.9 以上（考場是 3.9.6）與一個編輯器（VS Code 或 IDLE）；會在終端機執行 `python 檔名.py`
- 變數、型別（int / float / str / bool）、算術（+ - * / // % **）、型別轉換 int() str() float()
- print() 與 input()；f-string；`map(int, input().split())` 一次讀多個數
- 讀到 EOF：`for line in sys.stdin:`——CPE 幾乎每一題都這樣讀
- 怎麼讀錯誤訊息（traceback）：從最後一行往上看，第一個在你檔案裡的行號就是出事的地方

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d001` 打招呼
- `d002` 多組相加
- `d003` 長方形

**延伸題庫：**
- ZeroJudge 的 a 開頭基礎題：挑解題人數最多的前 15 題，每題都用 `cpe add` 登記或自己記錄

**要讀的章節：**
- Python 官方教學 第 3 章『非正式介紹』、第 7.1 節『格式化輸出』

**教材：**[Python 官方教學（繁中）](https://docs.python.org/zh-tw/3/tutorial/)、[Python Tutor（逐步視覺化執行）](https://pythontutor.com/)、[ZeroJudge（繁中題庫）](https://zerojudge.tw/)

**常見陷阱：**
- input() 讀進來是字串，直接相加會變成字串串接
- Windows／終端機最後一行沒有換行不影響，但『多印一個空行』會被判錯

**自我檢查（不看資料回答）：**
- `7 / 2`、`7 // 2`、`-7 // 2`、`-7 % 3` 各是多少？為什麼？
- 如何一行讀入三個整數 a b c？

**檢核（`cpe gate`）：**從空白檔、不看提示，45 分鐘內完成 `d004` 攝氏轉華氏、`d002` 多組相加，至少答對 2 題。

### 單元 2　條件判斷　（第 3 週）

**學完你能：**能把『如果…就…否則…』的規則寫成 if / elif / else，並系統性地測邊界值。

**要學的：**
- 比較運算（== != < <= > >=）、布林運算 and / or / not 與優先順序
- if / elif / else 鏈；巢狀 if；三元運算式 `a if cond else b`
- 邊界值測試：規則裡出現的每個數字，都要測它『剛好』、『少一』、『多一』

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d005` 奇偶
- `d006` 三個數的最大值
- `d007` 閏年

**要讀的章節：**
- Python 官方教學 4.1『if 陳述式』

**教材：**[Python 官方教學（繁中）](https://docs.python.org/zh-tw/3/tutorial/)、[Python Tutor（逐步視覺化執行）](https://pythontutor.com/)

**常見陷阱：**
- `=` 是賦值、`==` 才是比較
- `a < b < c` 在 Python 合法，但別在 C++ 這樣寫（之後會踩）

**自我檢查（不看資料回答）：**
- 閏年規則為什麼要用括號？
- elif 與連續多個 if 的差別是什麼？

**檢核（`cpe gate`）：**從空白檔、不看提示，45 分鐘內完成 `d008` 成績等級、`d005` 奇偶，至少答對 2 題。

### 單元 3　迴圈　（第 4–5 週）

**學完你能：**能用 for / while 做累加、連乘、計數、拆解數字與印出圖形。

**要學的：**
- for + range(start, stop, step)：右界不含；while 與 break / continue
- 累加器模式：先設初值，再在迴圈裡更新
- 巢狀迴圈與印出圖形；字串乘法 `' ' * n`
- 用 `n % 10` 與 `n // 10` 拆數字

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d009` 1 加到 n
- `d010` 階乘
- `d011` 乘法表
- `d024` 星星金字塔

**要讀的章節：**
- Python 官方教學 4.2–4.5『for、range()、break／continue』

**教材：**[Python 官方教學（繁中）](https://docs.python.org/zh-tw/3/tutorial/)、[Python Tutor（逐步視覺化執行）](https://pythontutor.com/)

**常見陷阱：**
- range(1, n) 不含 n
- while 忘了更新條件變成無窮迴圈（Ctrl+C 中止）

**自我檢查（不看資料回答）：**
- `range(10, 0, -3)` 產生什麼？
- 階乘的初值為什麼是 1 不是 0？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d012` 各位數字和、`d010` 階乘，至少答對 2 題。

### 單元 4　字串與 list　（第 6–7 週）

**學完你能：**熟練字串切片、迭代與 list 基本操作，能自己寫迴文、凱薩密碼、統計。

**要學的：**
- 字串：索引、切片 `s[a:b:c]`、`s[::-1]`、方法（strip split join lower upper find count replace）
- 字串不可變；ord() / chr()
- list：建立、索引、append / pop / insert、切片、sort / sorted、min / max / sum / len
- list comprehension：`[x*x for x in a if x%2==0]`
- 迭代：`for i, x in enumerate(a)`、`zip(a, b)`

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d013` 反轉整數
- `d014` 母音計數
- `d015` 迴文
- `d017` 數列統計
- `d018` 排序

**要讀的章節：**
- Python 官方教學 3.1.2『字串』、3.1.3『List』、5.1『List 詳解』

**教材：**[Python 官方教學（繁中）](https://docs.python.org/zh-tw/3/tutorial/)、[Python Tutor（逐步視覺化執行）](https://pythontutor.com/)

**常見陷阱：**
- `sort()` 回傳 None（會把 list 本身排好）；`sorted()` 才回傳新 list
- 迴圈中邊走邊刪 list 元素會漏掉東西

**自我檢查（不看資料回答）：**
- `'abcde'[1:4]`、`'abcde'[::-2]` 各是什麼？
- split() 與 split(' ') 對 `'a  b'` 的結果有何不同？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d016` 凱薩密碼、`d015` 迴文，至少答對 2 題。

### 單元 5　set、dict 與函式　（第 8–9 週）

**學完你能：**會用 set / dict 做快速查詢與計數，會寫函式；第一次感受到『效能』差異。

**要學的：**
- set：add、`in`（O(1) 查詢）、集合運算；dict：`d[k]`、`d.get(k, 0)`、items()、`collections.Counter`
- 排序的 key：`sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))`
- 函式：def、參數、return；區域與全域變數
- 第一次接觸複雜度：list 的 `in` 是 O(n)，set 是 O(1)

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d019` 去除重複
- `d020` 詞頻統計
- `d025` 因數個數

**要讀的章節：**
- Python 官方教學 5.4『集合』、5.5『字典』、4.x『定義函式』
- 標準函式庫 collections.Counter 的說明

**教材：**[Python 官方教學（繁中）](https://docs.python.org/zh-tw/3/tutorial/)

**常見陷阱：**
- 用 list 當集合查詢，資料一多就超時
- 函式裡改全域變數前要先宣告 global（但更好的做法是用參數與回傳值）

**自我檢查（不看資料回答）：**
- 為什麼 d028 用 set 就能從 O(n²) 變 O(n)？
- `Counter('hello')` 長什麼樣？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d028` 兩數之和、`d029` 異位詞，至少答對 2 題。

### 單元 6　數學基礎與進位制　（第 10 週）

**學完你能：**能寫質數判斷、gcd、費氏數列、進位轉換等基本數學程式。

**要學的：**
- 質數試除法到 √n；gcd 輾轉相除法；費氏數列的迭代寫法（遞迴版為什麼慢）
- 進位制：用 `%` 與 `//` 反覆取餘數；`bin()`、`int(s, base)`
- 把重複出現的程式碼抽成函式

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d021` 質數判斷
- `d022` 最大公因數與最小公倍數
- `d023` 費氏數列

**要讀的章節：**
- Python 官方教學 4.x『定義函式』

**教材：**[Python 官方教學（繁中）](https://docs.python.org/zh-tw/3/tutorial/)

**常見陷阱：**
- 1 不是質數
- 遞迴費氏 F(40) 就要好幾秒

**自我檢查（不看資料回答）：**
- 為什麼只需試除到 √n？
- 255 轉二進位是什麼？手算一次。

**檢核（`cpe gate`）：**從空白檔、不看提示，45 分鐘內完成 `d027` 十進位轉二進位、`d021` 質數判斷，至少答對 2 題。

### 單元 7　二維 list 與簡單模擬　（第 11 週）

**學完你能：**能建立與走訪二維陣列，並把一串指令模擬成狀態變化。

**要學的：**
- 二維 list：`[[0]*C for _ in range(R)]`（不要寫成 `[[0]*C]*R`）
- 走訪列與行；轉置；`zip(*a)`
- 模擬題的標準步驟：讀指令 → 修改狀態 → 輸出

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d026` 矩陣轉置

**要讀的章節：**
- Python 官方教學 5.1.3『List Comprehension』（巢狀）

**教材：**[Python 官方教學（繁中）](https://docs.python.org/zh-tw/3/tutorial/)、[Python Tutor（逐步視覺化執行）](https://pythontutor.com/)

**常見陷阱：**
- `[[0]*C]*R` 會讓所有列是同一個 list（在 Python Tutor 畫出來看看）

**自我檢查（不看資料回答）：**
- 為什麼 `[[0]*3]*3` 改一格會全變？

**檢核（`cpe gate`）：**從空白檔、不看提示，45 分鐘內完成 `d030` 簡易銀行、`d026` 矩陣轉置，至少答對 2 題。

### 單元 8　階段 0 驗收週　（第 12 週）

**學完你能：**不看資料，90 分鐘內從空白檔重寫 4 題舊題，建立『我真的會』的證據。

**要學的：**
- 回顧本階段所有被你用過提示的題目（`cpe review`）
- 整理一頁筆記：10 個最常用的寫法（讀 EOF、set 計數、排序 key…）
- 學會 debug：用 print 檢查中間值；縮小問題；寫最小測資

**延伸題庫：**
- 補完 ZeroJudge 入門題到累計約 60 題（報告的階段 0 目標是 80–120 題）

**教材：**[ZeroJudge（繁中題庫）](https://zerojudge.tw/)

**自我檢查（不看資料回答）：**
- 你最不熟的三個語法是什麼？明天各寫一個小程式練習。

**檢核（`cpe gate`）：**從空白檔、不看提示，120 分鐘內完成 `d014` 母音計數、`d020` 詞頻統計、`d022` 最大公因數與最小公倍數、`d013` 反轉整數，至少答對 3 題。


---

## 階段 1 · 競程 I/O 與一顆星　（目標：CPE 2 題（首次報考））

### 單元 9　競程輸入格式　（第 13–14 週）

**學完你能：**能處理 CPE 常見的五種輸入格式：EOF、0 0 結束、先給組數、空行分隔、一行多資料。

**要學的：**
- `sys.stdin.read().split()` 一次讀完 vs 逐行讀：何時用哪個
- 結束標記（`0 0`、單個 `0`）；先給組數 t；空行分隔的群組
- 輸出格式：Case 標題、組間空行 vs 每組後空行（PE 的最大來源）
- 把輸入格式寫在註解裡再開始寫程式的習慣

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d031` 直到 0 0 為止
- `d032` 先給組數
- `d033` 空行分隔的資料

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva11172` Relational Operators、`uva10055` Hashmat the Brave Warrior、`uva100` The 3n+1 problem

**延伸題庫：**
- CSES『Introductory Problems』挑解題人數最多的 10 題（練習純標準輸入輸出）

**教材：**[CSES Problem Set（分類清楚、純標準輸入輸出）](https://cses.fi/problemset/)、[CPE 官網（歷屆題目與答對率）](https://cpe.mcu.edu.tw/)

**常見陷阱：**
- `0 0` 之後還有資料時必須 break
- 最後一組之後的空行

**自我檢查（不看資料回答）：**
- 什麼情況下不能用 `read().split()`？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d034` Case 格式與空行、`d031` 直到 0 0 為止，至少答對 2 題。

### 單元 10　輸出格式、浮點數與字串映射　（第 15–16 週）

**學完你能：**能精準控制輸出格式，並用 dict／查表處理映射類題目。

**要學的：**
- `f'{x:.4f}'`、`:>8`、`:02d`；round 的銀行家捨入陷阱
- 用 dict 或字串做映射（羅馬數字、摩斯碼、鍵盤位移）
- 字串分組掃描（run-length）與『最後一段』的收尾
- 整數運算優於浮點運算：能用整數比大小就別用除法

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d035` 除法與小數位
- `d039` 羅馬數字
- `d043` 連續字元壓縮

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10082` WERTYU、`uva10420` List of Conquests、`uva10226` Hardwood Species、`uva10282` Babelfish、`uva10062` Tell me the frequencies!

**教材：**[Python 官方教學（繁中）](https://docs.python.org/zh-tw/3/tutorial/)

**常見陷阱：**
- Python 的 round(2.5) 是 2
- 分組掃描忘了輸出最後一組

**自我檢查（不看資料回答）：**
- `f'{0.125:.2f}'` 是多少？為什麼？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d045` 24 小時轉 12 小時、`d043` 連續字元壓縮，至少答對 2 題。

### 單元 11　大數與進位制　（第 17–18 週）

**學完你能：**善用 Python 大整數，熟練各種進位制轉換。

**要學的：**
- Python int 沒有上限（但 3.11 起字串轉換有 4300 位的限制，考場 3.9 沒有）
- 任意進位：`int(s, b)` 與手寫轉換
- 字串反轉相加類題目（Reverse and Add）
- 二進位位元計數與 `bin()`

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d036` 大數加與乘

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10106` Product、`uva713` Adding Reversed Numbers、`uva10220` I Love Big Numbers !、`uva10929` You can say 11、`uva10931` Parity、`uva10018` Reverse and Add、`uva10035` Primary Arithmetic

**教材：**[Python 官方教學（繁中）](https://docs.python.org/zh-tw/3/tutorial/)

**常見陷阱：**
- 前導零
- 把大數轉成 float 會丟失精度

**自我檢查（不看資料回答）：**
- 為什麼 C++ 解大數題要自己實作，而 Python 不用？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d037` 進位制轉換、`d036` 大數加與乘，至少答對 2 題。

### 單元 12　質數、因數與數學觀察　（第 19–20 週）

**學完你能：**能用篩法預處理，並把數學觀察寫成程式（根號、完全平方、數根）。

**要學的：**
- 埃拉托斯特尼篩法；『先預處理、再 O(1) 查詢』
- 因數成對找到 √n；完全平方數的因數個數是奇數
- 數根（digital root）、平方數個數 isqrt 公式
- 遇到數學題先手算小例子找規律

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d038` 質數個數查詢

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10110` Light, more light、`uva11461` Square Numbers、`uva11332` Summing Digits、`uva10300` Ecological Premium、`uva10071` Back to High School Physics、`uva11364` Parking、`uva10190` Divide, But Not Quite Conquer!

**教材：**[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)

**常見陷阱：**
- 對每個查詢重算一次篩法

**自我檢查（不看資料回答）：**
- 篩法為什麼從 i*i 開始劃掉倍數？

**檢核（`cpe gate`）：**從空白檔、不看提示，45 分鐘內完成 `d038` 質數個數查詢、`d025` 因數個數，至少答對 2 題。

### 單元 13　網格與座標模擬　（第 21–22 週）

**學完你能：**會用方向陣列與邊界檢查模擬二維世界。

**要學的：**
- 方向陣列 `dirs=[(0,1),(1,0),(0,-1),(-1,0)]` 與轉向（%4）
- 邊界檢查 `0<=nx<R and 0<=ny<C`
- 鄰居計數（八方向，如踩地雷）
- 把『題目的規則』逐條翻成程式，不要跳步

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d041` 機器人走格子
- `d042` 螺旋矩陣

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10189` Minesweeper、`uva11581` Grid Successors、`uva11498` Division of Nlogonia、`uva11559` Event Planning、`uva11150` Cola、`uva10038` Jolly Jumpers

**要讀的章節：**
- Python 文件：sys.stdin

**教材：**[Python Tutor（逐步視覺化執行）](https://pythontutor.com/)

**常見陷阱：**
- x、y 與列、行的對應（先寫在註解裡）
- 斜向鄰居漏掉

**自我檢查（不看資料回答）：**
- 螺旋矩陣為什麼用『遇到牆或已填過就轉向』？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d042` 螺旋矩陣、`d041` 機器人走格子，至少答對 2 題。

### 單元 14　日期、時間與運算式解析　（第 23–24 週）

**學完你能：**會處理日期／時間計算與字串解析（token 化）。

**要學的：**
- datetime.date 與 weekday()；也要會用 Zeller 公式自己算
- 進位換算（秒→時分秒）、12/24 小時制邊界
- split 後依 token 處理的解析模式

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d040` 星期幾
- `d044` 由左到右的算式

**延伸題庫：**
- UVA 上日期／時間類一顆星題：用 `cpe add` 登記後練習

**教材：**[Python 官方教學（繁中）](https://docs.python.org/zh-tw/3/tutorial/)

**常見陷阱：**
- 0 點與 12 點的邊界

**自我檢查（不看資料回答）：**
- 2000 與 1900 為什麼閏年規則不同？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d040` 星期幾、`d044` 由左到右的算式，至少答對 2 題。

### 單元 15　一顆星選集 I　（第 25–26 週）

**學完你能：**到 CPE 官網取得『一顆星選集』49 題，完成前 25 題。

**要學的：**
- 用 `cpe import <題號> <題目文字檔>` 把題目與範例匯入（見 README）
- 養成習慣：每題先在註解寫輸入格式、輸出格式、範圍；通過後寫下『這題的陷阱』
- 每週至少 2 題用英文原題（考場題目是英文，有英文字典可用）

**延伸題庫：**
- 一顆星選集 前 25 題（官網）
- CPE 歷屆 一～二顆星且全體答對率高於 30% 的題目

**教材：**[CPE 官網（歷屆題目與答對率）](https://cpe.mcu.edu.tw/)

**自我檢查（不看資料回答）：**
- 用英文複述一題題意給自己聽。

**檢核（`cpe gate`）：**從空白檔、不看提示，90 分鐘內完成 `e101` 成績排名、`e102` 密碼強度、`e103` 停車費，至少答對 2 題。

### 單元 16　階段 1 驗收：一顆星選集 II 與首次報考　（第 27–28 週）

**學完你能：**完成一顆星 49 題；報考第一次 CPE（大專生免費），目標 1–2 題。

**要學的：**
- 完成選集剩下題目；全部題目能在 30 分鐘內重寫
- 考前一週模擬：`cpe mock start --kind short`（3 題 90 分鐘）
- 考試當天流程：報到、環境測試、題目英文、ICPC 計分（錯一次加 20 分鐘）——先做會的題

**延伸題庫：**
- 一顆星選集 後 24 題
- 報名：查 CPE 官網的最新場次與報名日期

**要讀的章節：**
- CPE 官網『考生使用手冊』（含 Python I/O 範例）

**教材：**[CPE 官網（歷屆題目與答對率）](https://cpe.mcu.edu.tw/)

**自我檢查（不看資料回答）：**
- 考場上看到完全沒頭緒的題，你的第一步是什麼？

**檢核（`cpe gate`）：**模擬考（short），至少答對 2 題。


---

## 階段 2 · 資料結構與基礎演算法　（目標：CPE 3 題（A-））

### 單元 17　複雜度估算與排序　（第 29–30 週）

**學完你能：**能在寫程式前估算複雜度，並熟練多重條件排序。

**要學的：**
- Big-O：O(n)、O(n log n)、O(n²)；『Python 約每秒 10^7 次簡單運算』的粗估法；看範圍倒推演算法
- sort 的 key、多重條件、穩定排序；自訂比較（cmp_to_key）
- 計數排序（值域小時）
- 開始建 Git 習慣：每天的程式碼 commit

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d049` 學生排名

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10041` Vito's Family、`uva11727` Cost Cutting、`uva11942` Lumberjack Sequencing、`uva11462` Age Sort

**延伸題庫：**
- CSES『Sorting and Searching』挑解題人數最多的 8 題

**要讀的章節：**
- Competitive Programmer's Handbook 第 2 章『Time complexity』、第 3 章『Sorting』

**教材：**[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)、[CSES Problem Set（分類清楚、純標準輸入輸出）](https://cses.fi/problemset/)、[VisuAlgo（演算法動畫）](https://visualgo.net/)

**常見陷阱：**
- 字串排序是字典序，'10' < '9'
- 忘了先轉成 int 再排序

**自我檢查（不看資料回答）：**
- n=10^5 時 O(n²) 為什麼不行？n=10^3 呢？

**工程任務：**#1（`cpe eng` 查看）

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d049` 學生排名、`d028` 兩數之和，至少答對 2 題。

### 單元 18　前綴和與二分搜尋　（第 31–32 週）

**學完你能：**會用前綴和處理區間查詢，並正確寫出二分搜尋。

**要學的：**
- 前綴和：pre[i]；區間和 = pre[r]-pre[l-1]；二維前綴和（選修）
- 二分搜尋：lower_bound / upper_bound 語意；迴圈不變量；`bisect` 模組
- 『對答案二分』的入門概念（最小化最大值）

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d046` 區間和查詢
- `d047` 第一個不小於 x 的位置

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10474` Where is the Marble?

**延伸題庫：**
- CSES『Sorting and Searching』中標示二分或前綴和的題目
- AP325 對應章節

**要讀的章節：**
- Competitive Programmer's Handbook 第 3 章（Binary search）、第 9 章『Range queries』（Static array queries）

**教材：**[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)、[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)、[VisuAlgo（演算法動畫）](https://visualgo.net/)

**常見陷阱：**
- l、r 的開閉區間不一致造成無窮迴圈
- 前綴和下標差一

**自我檢查（不看資料回答）：**
- lower_bound 與 upper_bound 的差別？
- 二分時 `mid=(l+r)//2` 與 `l=mid` 會有什麼問題？

**工程任務：**#2（`cpe eng` 查看）

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d046` 區間和查詢、`d047` 第一個不小於 x 的位置，至少答對 2 題。

### 單元 19　雙指標與滑動視窗　（第 33 週）

**學完你能：**能用雙指標把 O(n²) 降成 O(n)。

**要學的：**
- 排序後雙指標（兩端往內）；同向雙指標（滑動視窗）
- 證明為什麼指標只需要單向移動

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d048` 和不超過 K 的配對數

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva11057` Exact Sum、`uva10340` All in All

**要讀的章節：**
- Competitive Programmer's Handbook 第 8 章『Amortized analysis』（Two pointers）

**教材：**[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)

**常見陷阱：**
- 指標移動條件寫反造成漏解

**自我檢查（不看資料回答）：**
- d048 為什麼 a[l]+a[r]≤K 時可以一次加 r-l 對？

**檢核（`cpe gate`）：**從空白檔、不看提示，45 分鐘內完成 `d048` 和不超過 K 的配對數、`d047` 第一個不小於 x 的位置，至少答對 2 題。

### 單元 20　stack、queue 與 deque　（第 34–35 週）

**學完你能：**會用資料結構模擬題目，並辨識『後進先出』與『先進先出』場景。

**要學的：**
- stack（list）、queue / deque（`collections.deque`）；括號配對、單調 stack／deque
- 模擬類題目（Rails、Ferry Loading）
- 找規律取代模擬（約瑟夫）

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d050` 括號配對
- `d051` 約瑟夫問題
- `d053` 滑動視窗最大值

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva673` Parentheses Balance、`uva514` Rails、`uva10901` Ferry Loading III、`uva11995` I Can Guess the Data Structure!、`uva10935` Throwing cards away I、`uva12100` Printer Queue

**要讀的章節：**
- Competitive Programmer's Handbook 第 4 章『Data structures』（Deque、Stack）

**教材：**[VisuAlgo（演算法動畫）](https://visualgo.net/)、[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)

**常見陷阱：**
- list.pop(0) 是 O(n)，要用 deque
- 空 stack 時 pop

**自我檢查（不看資料回答）：**
- 什麼題目看到就該想到 stack？單調 deque 怎麼維持單調？

**工程任務：**#3（`cpe eng` 查看）

**檢核（`cpe gate`）：**從空白檔、不看提示，90 分鐘內完成 `d050` 括號配對、`d053` 滑動視窗最大值，至少答對 2 題。

### 單元 21　heap 與優先佇列　（第 36 週）

**學完你能：**會用 heapq 與 dict 做動態維護最小／中位數。

**要學的：**
- heapq：heappush / heappop / heapify；max-heap 用負數
- 貪心 + heap（合併最小兩個）
- 動態中位數（bisect.insort 或雙 heap）

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d052` 合併成本

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10954` Add All、`uva10107` What is the Median?、`uva11136` Hoax or what

**要讀的章節：**
- Competitive Programmer's Handbook 第 4 章（Priority queues）

**教材：**[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)、[VisuAlgo（演算法動畫）](https://visualgo.net/)

**常見陷阱：**
- heapq 只有最小堆積
- tuple 比較：第一個欄位相同時會比第二個

**自我檢查（不看資料回答）：**
- 為什麼 heap 取最小是 O(log n)，而 list 取最小是 O(n)？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d052` 合併成本、`d020` 詞頻統計，至少答對 2 題。

### 單元 22　貪心演算法　（第 37–38 週）

**學完你能：**會判斷貪心是否成立，並用交換論證說服自己。

**要學的：**
- 貪心的典型：區間排程（依結束時間）、區間覆蓋、配對（排序後雙指標）、Huffman（heap）
- 怎麼證明：交換論證——假設最優解跟你的選擇不同，換成你的選擇不會變差
- 反例思維：寫完貪心後，用 5 分鐘找反例

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d054` 活動選擇

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10020` Minimal coverage、`uva10026` Shoemaker's Problem、`uva11389` The Bus Driver Problem、`uva10037` Bridge

**要讀的章節：**
- Competitive Programmer's Handbook 第 6 章『Greedy algorithms』

**教材：**[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)、[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)

**常見陷阱：**
- 排序依據選錯
- 貪心看似合理但有反例（零錢兌換）

**自我檢查（不看資料回答）：**
- 活動選擇為什麼依結束時間排序而不是開始時間？

**檢核（`cpe gate`）：**從空白檔、不看提示，75 分鐘內完成 `d055` 分餅乾、`d054` 活動選擇，至少答對 2 題。

### 單元 23　遞迴與回溯　（第 39–41 週）

**學完你能：**能寫出遞迴、窮舉與剪枝，並估算搜尋空間。

**要學的：**
- 遞迴三要素：終止條件、縮小問題、合併結果；呼叫堆疊（用 Python Tutor 看）
- 回溯：選擇 → 遞迴 → 還原；全排列、N 皇后、子集合
- 剪枝：提早放棄不可能的分支；可行性剪枝與最優性剪枝
- `sys.setrecursionlimit` 與遞迴深度的限制

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d056` 全排列
- `d057` N 皇后方案數

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva750` 8 Queens Chess Problem、`uva524` Prime Ring Problem、`uva10344` 23 out of 5、`uva624` CD

**要讀的章節：**
- Competitive Programmer's Handbook 第 5 章『Complete search』

**教材：**[Python Tutor（逐步視覺化執行）](https://pythontutor.com/)、[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)

**常見陷阱：**
- 忘了『還原』狀態
- 沒有剪枝造成指數爆炸

**自我檢查（不看資料回答）：**
- N 皇后為什麼用 r-c 與 r+c 判斷斜線？

**檢核（`cpe gate`）：**從空白檔、不看提示，75 分鐘內完成 `d056` 全排列、`d057` N 皇后方案數，至少答對 2 題。

### 單元 24　位元運算與子集合枚舉　（第 42–43 週）

**學完你能：**會用 bitmask 表示集合並枚舉所有子集合。

**要學的：**
- & | ^ ~ << >> 與常用技巧（判斷第 i 位、設定、清除、lowbit）
- n≤20 時 `for mask in range(1<<n)` 枚舉子集合
- XOR 的性質（a^a=0）

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d058` 子集合和
- `d059` 落單的數

**延伸題庫：**
- CSES『Introductory Problems』中位元／子集合相關題目

**要讀的章節：**
- Competitive Programmer's Handbook 第 10 章『Bit manipulation』

**教材：**[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)、[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)

**常見陷阱：**
- `1 << i` 的優先順序：要加括號 `(mask >> i) & 1`

**自我檢查（不看資料回答）：**
- `mask & (-mask)` 取出什麼？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d058` 子集合和、`d059` 落單的數，至少答對 2 題。

### 單元 25　階段 2 驗收週　（第 44 週）

**學完你能：**累積 3 題以上的實力：模擬考至少 3 題。這週並報考 APCS 或 CPE。

**要學的：**
- 整理錯題本：每個錯誤分類（格式／邊界／演算法／超時／粗心）
- 完整 3 小時模擬考一次，然後逐題檢討
- 報考 CPE：目標 3 題（A- 進階級）

**延伸題庫：**
- APCS 實作題（中級～中高級）歷屆題：ZeroJudge 有收錄

**教材：**[ZeroJudge（繁中題庫）](https://zerojudge.tw/)、[王一哲教學網站（APCS）](https://sites.google.com/view/yizhe/%E8%AA%B2%E7%A8%8B/apcs)

**自我檢查（不看資料回答）：**
- 上次考試你在哪一題花最多時間？下次怎麼避免？

**工程任務：**#4（`cpe eng` 查看）

**檢核（`cpe gate`）：**模擬考（mock），至少答對 3 題。


---

## 階段 3 · 圖論與 DP　（目標：CPE 4 題（A））

### 單元 26　圖的表示與 BFS / DFS　（第 45–46 週）

**學完你能：**會建圖、BFS 求最短步數、DFS 找連通區域，並避免遞迴過深。

**要學的：**
- 鄰接表 `adj=[[] for _ in range(n+1)]`；鄰接矩陣；有向／無向／加權
- BFS：用 deque、dist 初始 -1、每點只入隊一次；格子 BFS
- DFS：遞迴與迭代（用 stack）；flood fill；二分圖著色
- Python 遞迴深度限制：大圖一律寫迭代

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d060` 迷宮最短路

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva572` Oil Deposits、`uva336` A Node Too Far、`uva10009` All Roads Lead Where?、`uva10004` Bicoloring、`uva439` Knight Moves、`uva10653` Bombs! NO they are Mines!!

**延伸題庫：**
- CSES『Graph Algorithms』前幾題（Counting Rooms、Labyrinth）

**要讀的章節：**
- Competitive Programmer's Handbook 第 11 章『Basics of graphs』、第 12 章『Graph traversal』

**教材：**[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)、[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)、[VisuAlgo（演算法動畫）](https://visualgo.net/)

**常見陷阱：**
- 入隊時才標記 visited，而不是出隊時
- 多組測資忘了清空圖

**自我檢查（不看資料回答）：**
- BFS 為什麼能保證最短？邊有權重時還成立嗎？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d060` 迷宮最短路、`d056` 全排列，至少答對 2 題。

### 單元 27　並查集與連通元件　（第 47–48 週）

**學完你能：**能用並查集處理動態連通性。

**要學的：**
- Union-Find：路徑壓縮 + 按大小合併；維護集合大小
- 離線處理：先排序再合併（Kruskal 的基礎）
- 字串節點→編號的 dict

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d061` 並查集：連通分量

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10608` Friends、`uva459` Graph Connectivity、`uva11503` Virtual Friends、`uva11902` Dominator

**要讀的章節：**
- Competitive Programmer's Handbook 第 15 章『Spanning trees』（Union-find）

**教材：**[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)、[VisuAlgo（演算法動畫）](https://visualgo.net/)

**常見陷阱：**
- find 忘了壓縮造成退化成鏈
- 把 a、b 本身而不是它們的根拿去比大小

**自我檢查（不看資料回答）：**
- 為什麼並查集查詢近似 O(1)？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d061` 並查集：連通分量、`d060` 迷宮最短路，至少答對 2 題。

### 單元 28　拓撲排序與 DAG　（第 49–50 週）

**學完你能：**能判斷有向圖有無環並求合法順序。

**要學的：**
- Kahn 演算法（入度）與 DFS 後序；字典序最小要用 heap
- DAG 上的 DP（最長路徑）
- 依賴關係題：先建圖再想順序

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d062` 字典序最小的拓撲排序

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10305` Ordering Tasks、`uva11060` Beverages、`uva10926` How Many Dependencies?

**要讀的章節：**
- Competitive Programmer's Handbook 第 16 章『Directed graphs』（Topological sorting）

**教材：**[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)、[VisuAlgo（演算法動畫）](https://visualgo.net/)

**常見陷阱：**
- 重邊影響入度計算
- 有環時的輸出

**自我檢查（不看資料回答）：**
- Kahn 演算法怎麼判斷有環？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d062` 字典序最小的拓撲排序、`d061` 並查集：連通分量，至少答對 2 題。

### 單元 29　最短路徑　（第 51–53 週）

**學完你能：**會 Dijkstra（堆積版）、Floyd，並能依題目規模選擇。

**要學的：**
- Dijkstra：dist + heapq、lazy deletion；為什麼不能有負權
- Floyd–Warshall：k 在最外層；O(n³) 適用 n≤400（C++）／n≤100（Python）
- 變形：最小化最大邊（minimax）、多源最短路、路徑還原

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d063` Dijkstra 最短路徑
- `d065` Floyd–Warshall 全點對最短路

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10986` Sending email、`uva341` Non-Stop Travel、`uva10171` Meeting Prof. Miguel、`uva567` Risk、`uva821` Page Hopping、`uva10099` The Tourist Guide、`uva10048` Audiophobia

**延伸題庫：**
- CSES『Graph Algorithms』最短路徑題

**要讀的章節：**
- Competitive Programmer's Handbook 第 13 章『Shortest paths』

**教材：**[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)、[VisuAlgo（演算法動畫）](https://visualgo.net/)、[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)

**常見陷阱：**
- Floyd 迴圈順序
- 把 INF 設太小造成加法後溢位判斷錯

**自我檢查（不看資料回答）：**
- Dijkstra 的 lazy deletion 是什麼意思？

**檢核（`cpe gate`）：**從空白檔、不看提示，75 分鐘內完成 `d063` Dijkstra 最短路徑、`d065` Floyd–Warshall 全點對最短路，至少答對 2 題。

### 單元 30　最小生成樹　（第 54–55 週）

**學完你能：**會 Kruskal，並理解 MST 的應用。

**要學的：**
- Kruskal：邊排序 + 並查集；Prim：堆積版
- MST 的性質（切割性質、環性質）
- 變形：總長減去 MST、次小生成樹（選修）

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d064` 最小生成樹

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10034` Freckles、`uva11631` Dark roads、`uva10147` Highways、`uva11747` Heavy Cycle Edges

**要讀的章節：**
- Competitive Programmer's Handbook 第 15 章『Spanning trees』（Kruskal、Prim）

**教材：**[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)、[VisuAlgo（演算法動畫）](https://visualgo.net/)

**常見陷阱：**
- 圖不連通時的處理
- 歐氏距離不要提前開根號比大小以外的地方

**自我檢查（不看資料回答）：**
- 為什麼 Kruskal 選到 n-1 條邊就可以停？

**工程任務：**#5（`cpe eng` 查看）

**檢核（`cpe gate`）：**從空白檔、不看提示，75 分鐘內完成 `d064` 最小生成樹、`d063` Dijkstra 最短路徑，至少答對 2 題。

### 單元 31　DP 入門：一維 DP 與零錢　（第 56–57 週）

**學完你能：**能定義 dp 狀態、寫出轉移式，區分『計數』與『最佳化』。

**要學的：**
- DP 的四步：定義狀態 → 轉移式 → 初始值 → 答案在哪
- 最大子段和（Kadane）、爬樓梯、零錢（最少枚數／組合數）
- 迴圈順序決定『組合』或『排列』
- 貪心 vs DP：何時貪心會錯

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d071` 最大連續子陣列和
- `d067` 最少硬幣數

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva674` Coin Change、`uva357` Let Me Count The Ways、`uva10684` The jackpot、`uva507` Jill Rides Again、`uva10465` Homer Simpson

**延伸題庫：**
- CSES『Dynamic Programming』前 6 題

**要讀的章節：**
- Competitive Programmer's Handbook 第 7 章『Dynamic programming』（Coin problem）

**教材：**[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)、[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)

**常見陷阱：**
- 初始值（尤其是 -inf 與 0）
- 狀態定義含糊

**自我檢查（不看資料回答）：**
- 零錢『組合數』與『排列數』的程式差在哪一行？

**工程任務：**#6（`cpe eng` 查看）

**檢核（`cpe gate`）：**從空白檔、不看提示，75 分鐘內完成 `d066` 硬幣組合數、`d067` 最少硬幣數，至少答對 2 題。

### 單元 32　背包問題　（第 58–59 週）

**學完你能：**會 0/1 背包、完全背包與它們的變形。

**要學的：**
- 0/1 背包（容量逆序）、完全背包（容量順序）、恰好裝滿 vs 不超過
- 子集合和、分割等和問題的背包化
- 二維→一維滾動陣列

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d068` 0/1 背包

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10130` SuperSale、`uva562` Dividing coins、`uva11450` Wedding Shopping

**延伸題庫：**
- CSES『Dynamic Programming』背包類題

**要讀的章節：**
- Competitive Programmer's Handbook 第 7 章（Knapsack）

**教材：**[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)、[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)

**常見陷阱：**
- 0/1 與完全背包的迴圈方向
- 狀態維度太大（W 高達 10^9 時不能用）

**自我檢查（不看資料回答）：**
- 為什麼 0/1 背包的容量要由大到小？

**檢核（`cpe gate`）：**從空白檔、不看提示，75 分鐘內完成 `d068` 0/1 背包、`d066` 硬幣組合數，至少答對 2 題。

### 單元 33　序列 DP：LIS 與 LCS　（第 60–61 週）

**學完你能：**會 LIS（含 O(n log n)）、LCS，並能還原路徑。

**要學的：**
- LIS O(n²) 與 O(n log n)（tails + bisect）；嚴格 vs 非嚴格
- LCS 二維表；編輯距離；路徑還原（前驅陣列）
- 滾動陣列省空間

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d070` 最長共同子序列
- `d069` 最長遞增子序列

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10131` Is Bigger Smarter?、`uva10405` Longest Common Subsequence、`uva10192` Vacation

**要讀的章節：**
- Competitive Programmer's Handbook 第 7 章（Longest increasing subsequence、Edit distance）

**教材：**[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)、[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)

**常見陷阱：**
- LIS 嚴格遞增用 bisect_left，非嚴格用 bisect_right
- 輸出路徑時順序

**自我檢查（不看資料回答）：**
- tails 陣列中的值代表什麼？

**檢核（`cpe gate`）：**從空白檔、不看提示，75 分鐘內完成 `d069` 最長遞增子序列、`d070` 最長共同子序列，至少答對 2 題。

### 單元 34　網格 DP　（第 62–63 週）

**學完你能：**能處理網格上的最短／最佳路徑與計數。

**要學的：**
- dp[i][j] 由上與左轉移；邊界處理
- 字典序最小路徑要由後往前 DP（Unidirectional TSP）
- 有障礙、有權重、可繞回（列循環）的變形

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d072` 網格最小路徑和

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva116` Unidirectional TSP、`uva825` Walking on the Safe Side、`uva10337` Flight Planner

**要讀的章節：**
- Competitive Programmer's Handbook 第 7 章（Paths in a grid）

**教材：**[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)

**常見陷阱：**
- 第一列／第一行的初始化
- 路徑平手時的規則

**自我檢查（不看資料回答）：**
- 為什麼求字典序最小路徑要倒著做 DP？

**檢核（`cpe gate`）：**從空白檔、不看提示，60 分鐘內完成 `d072` 網格最小路徑和、`d071` 最大連續子陣列和，至少答對 2 題。

### 單元 35　區間 DP　（第 64–65 週）

**學完你能：**能辨識並寫出區間 DP。

**要學的：**
- 狀態 dp[l][r]；依區間長度由小到大計算；枚舉分割點
- 矩陣連乘、切木棍、最佳二元搜尋樹、取兩端博弈
- O(n³) 的規模：Python n≈100 內，C++ n≈400 內

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d073` 矩陣連乘

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10003` Cutting Sticks、`uva10304` Optimal Binary Search Tree、`uva10891` Game of Sum

**要讀的章節：**
- Competitive Programmer's Handbook 第 7 章；搜尋『interval DP』

**教材：**[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)、[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)

**常見陷阱：**
- 迴圈順序（先枚舉長度）

**自我檢查（不看資料回答）：**
- 為什麼切木棍要把切點當端點？

**檢核（`cpe gate`）：**從空白檔、不看提示，75 分鐘內完成 `d073` 矩陣連乘、`d072` 網格最小路徑和，至少答對 2 題。

### 單元 36　位元遮罩 DP　（第 66–67 週）

**學完你能：**能用 bitmask 表示『已選集合』並做 DP。

**要學的：**
- dp[mask][i]；O(2^n · n²)；n≤20 的訊號
- 旅行推銷員、指派問題、完美匹配
- 固定最低位未選者來避免重複計數

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d074` 旅行推銷員（小規模）

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10911` Forming Quiz Teams、`uva10032` Tug of War

**要讀的章節：**
- Competitive Programmer's Handbook 第 7 章（Counting tilings 之前的 bit 技巧）；搜尋『bitmask DP』

**教材：**[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)、[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)

**常見陷阱：**
- Python 在 n=15 就很吃力——這是學 C++ 的動機

**自我檢查（不看資料回答）：**
- 為什麼『固定最低位』能避免重複配對？

**檢核（`cpe gate`）：**從空白檔、不看提示，75 分鐘內完成 `d074` 旅行推銷員（小規模）、`d058` 子集合和，至少答對 2 題。

### 單元 37　數論：模運算、質因數與組合數　（第 68–69 週）

**學完你能：**會模運算、快速冪、模逆元、質因數分解與組合數預處理。

**要學的：**
- 模運算規則；快速冪 `pow(a,b,m)` 與手寫；費馬小定理求逆元
- 質因數分解（試除、篩法最小質因數）；歐拉函數
- 組合數取模：階乘 + 逆元階乘預處理；帕斯卡三角形
- 擴展歐幾里得（選修）

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d075` 組合數取模
- `d093` 歐拉函數

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva374` Big Mod、`uva10104` Euclid Problem、`uva10127` Ones、`uva583` Prime Factors

**要讀的章節：**
- Competitive Programmer's Handbook 第 21 章『Number theory』、第 22 章『Combinatorics』

**教材：**[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)、[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)

**常見陷阱：**
- 減法取模要 `(a-b)%M` 再保證非負
- 乘法前先取模避免大數變慢（Python）／溢位（C++）

**自我檢查（不看資料回答）：**
- 為什麼費馬小定理只在模數是質數時可用？

**檢核（`cpe gate`）：**從空白檔、不看提示，75 分鐘內完成 `d075` 組合數取模、`d038` 質數個數查詢，至少答對 2 題。

### 單元 38　階段 3 驗收週　（第 70 週）

**學完你能：**累積 4 題以上的實力：完整模擬考至少 4 題，並報考 CPE。

**要學的：**
- 完整 3 小時模擬；逐題檢討：為什麼沒做出來？缺知識／缺技巧／沒時間／粗心
- 報考 CPE：目標 4 題（A 專業級）
- 完成一個含 pytest 的 CLI 小專案（工程任務）

**延伸題庫：**
- Codeforces rating 800–1300，各 tag 各 5 題

**教材：**[Codeforces 題庫（可依 tag / rating 篩選）](https://codeforces.com/problemset)、[AtCoder（ABC 的 A–D 題）](https://atcoder.jp/)

**自我檢查（不看資料回答）：**
- 寫下你目前最弱的三個主題。

**工程任務：**#7（`cpe eng` 查看）

**檢核（`cpe gate`）：**模擬考（mock），至少答對 4 題。


---

## 階段 4 · 進階演算法與 C++　（目標：CPE 5 題）

### 單元 39　C++ 入門與翻譯舊題　（第 71–74 週）

**學完你能：**能用 C++ 通過 Python 解過的題目。

**語言：C++**（`cpe new <題號> --lang cpp`）

**要學的：**
- 安裝 g++（Linux/Mac 內建；Windows 用 MinGW/MSYS2）；`g++ -O2 -std=c++17`
- 競程模板：`ios::sync_with_stdio(false); cin.tie(nullptr);`；`int` vs `long long`（溢位！）
- 輸入輸出、vector、string、迴圈、函式、引用；讀到 EOF：`while (cin >> x)`
- 對照翻譯：每題先看自己的 Python 解，再逐行翻成 C++
- 常見落差：整數除法對負數向零取整（Python 是向下取整）、陣列越界不報錯、未初始化變數

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d018` 排序
- `d021` 質數判斷
- `d022` 最大公因數與最小公倍數
- `d031` 直到 0 0 為止
- `d049` 學生排名

**要讀的章節：**
- learncpp.com 第 0–8 章

**教材：**[learncpp.com（C++ 入門教學）](https://www.learncpp.com/)、[cppreference（C++ 標準庫查詢）](https://en.cppreference.com/)

**常見陷阱：**
- int 溢位（乘法前先轉 long long）
- 忘了 `\n` 或 `endl`（endl 很慢）

**自我檢查（不看資料回答）：**
- `-7 / 2` 與 `-7 % 3` 在 C++ 是多少？和 Python 一樣嗎？

**檢核（`cpe gate`）：**從空白檔、不看提示，90 分鐘內完成 `d046` 區間和查詢、`d054` 活動選擇，至少答對 2 題，用 C++。

### 單元 40　C++ STL　（第 75–78 週）

**學完你能：**能用 STL 容器與演算法寫出標準解。

**語言：C++**（`cpe new <題號> --lang cpp`）

**要學的：**
- vector、sort（含 lambda）、lower_bound / upper_bound、unique
- set / map / unordered_map、priority_queue（預設最大堆積）、deque / stack / queue、pair / tuple、bitset
- 複雜度：map 是 O(log n)，unordered_map 平均 O(1)
- 把 d047、d052、d053、d060、d063、d064 都用 C++ 重寫

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d047` 第一個不小於 x 的位置
- `d052` 合併成本
- `d053` 滑動視窗最大值
- `d060` 迷宮最短路
- `d063` Dijkstra 最短路徑
- `d064` 最小生成樹

**要讀的章節：**
- cppreference：<vector>、<algorithm>、<set>、<map>、<queue>

**教材：**[cppreference（C++ 標準庫查詢）](https://en.cppreference.com/)、[learncpp.com（C++ 入門教學）](https://www.learncpp.com/)

**常見陷阱：**
- `priority_queue` 預設是最大堆積
- 迭代時修改容器造成未定義行為

**自我檢查（不看資料回答）：**
- Python 的 heapq 與 C++ 的 priority_queue 差別是什麼？

**檢核（`cpe gate`）：**從空白檔、不看提示，90 分鐘內完成 `d063` Dijkstra 最短路徑、`d076` 最長共同子序列（大），至少答對 2 題，用 C++。

### 單元 41　效能與複雜度　（第 79–82 週）

**學完你能：**能在動手前估算是否會超時，並選對語言與演算法。

**語言：C++**（`cpe new <題號> --lang cpp`）

**要學的：**
- 10^8 規則：C++ 約 10^8 次簡單運算／秒；Python 約 10^7
- 記憶體估算：int 4 byte、long long 8 byte；10^7 個 int = 40MB
- 快速 I/O；避免 endl；預先配置陣列
- 把『Python 超時』的題（d076–d079）全部翻成 C++ 並通過

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d076` 最長共同子序列（大）
- `d077` 質數個數（大）
- `d078` 背包（大）

**教材：**[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)、[cppreference（C++ 標準庫查詢）](https://en.cppreference.com/)

**常見陷阱：**
- 在迴圈內重複建立大型物件
- 多組測資忘了重設陣列

**自我檢查（不看資料回答）：**
- n=2×10^5、q=2×10^5 時哪些演算法可行？

**檢核（`cpe gate`）：**從空白檔、不看提示，90 分鐘內完成 `d079` Floyd（大）、`d077` 質數個數（大），至少答對 2 題，用 C++。

### 單元 42　計算幾何　（第 83–86 週）

**學完你能：**能處理點、線段、多邊形的基本運算且不被邊界情況擊倒。

**要學的：**
- 向量、叉積（方向）、點積；三點共線；整數幾何優先
- 線段相交（含端點、共線）；點在多邊形內（射線法）；多邊形面積（鞋帶公式）
- 凸包（Andrew monotone chain）
- 浮點誤差：eps 的使用；盡量用整數

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d082` 多邊形面積
- `d081` 線段相交
- `d080` 凸包

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva191` Intersection、`uva378` Intersecting Lines、`uva11437` Triangle Fun、`uva681` Convex Hull Finding、`uva11626` Convex Hull、`uva10065` Useless Tile Packers

**要讀的章節：**
- Competitive Programmer's Handbook 第 29 章『Geometry』

**教材：**[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)

**常見陷阱：**
- 共線點是否保留
- 退化成點的線段

**自我檢查（不看資料回答）：**
- 叉積的符號代表什麼？

**檢核（`cpe gate`）：**從空白檔、不看提示，90 分鐘內完成 `d080` 凸包、`d082` 多邊形面積，至少答對 2 題。

### 單元 43　進階圖論　（第 87–90 週）

**學完你能：**會處理負權、強連通分量與（選修）網路流。

**要學的：**
- Bellman-Ford 與負環偵測；SPFA 的風險
- 強連通分量（Kosaraju / Tarjan）；縮點成 DAG
- 最大流入門（Edmonds–Karp）——CPE 少考，建立概念即可
- 無向圖的橋與關節點（選修）

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d088` 負權邊與負環
- `d089` 強連通分量
- `d090` 最大流（選修）

**要讀的章節：**
- Competitive Programmer's Handbook 第 17 章『Strong connectivity』、第 20 章『Flows and cuts』

**教材：**[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)、[VisuAlgo（演算法動畫）](https://visualgo.net/)

**常見陷阱：**
- 遞迴 DFS 在大圖會爆
- 負環『可達』條件

**自我檢查（不看資料回答）：**
- 為什麼 Dijkstra 遇到負權會錯？

**檢核（`cpe gate`）：**從空白檔、不看提示，90 分鐘內完成 `d089` 強連通分量、`d088` 負權邊與負環，至少答對 2 題。

### 單元 44　字串演算法與解析　（第 91–94 週）

**學完你能：**會 KMP／前綴函數、迴文，以及遞迴下降解析。

**要學的：**
- 前綴函數（KMP 失敗函數）與週期；Z 函數（選修）
- 迴文：中心擴展、Manacher
- 字串雜湊（選修）；Trie（選修）
- 運算式解析：遞迴下降（expr / term / factor）

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d083` 最短週期
- `d084` 最長迴文子字串

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10010` Where's Waldorf?、`uva401` Palindromes、`uva11221` Magic Square Palindromes、`uva10115` Automatic Editing

**要讀的章節：**
- Competitive Programmer's Handbook 第 26 章『String algorithms』

**教材：**[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)

**常見陷阱：**
- 把字串切片放在迴圈裡造成 O(n²)

**自我檢查（不看資料回答）：**
- 前綴函數 pi[i] 的定義？n - pi[n-1] 為什麼是最短週期？

**檢核（`cpe gate`）：**從空白檔、不看提示，90 分鐘內完成 `d095` 運算式求值、`d083` 最短週期，至少答對 2 題。

### 單元 45　進階 DP、樹與博弈　（第 95–98 週）

**學完你能：**能做樹 DP、數位 DP 與博弈 DP。

**要學的：**
- 樹 DP（選／不選）、換根（選修）；用迭代避免遞迴深度問題
- 數位 DP：貼上界旗標 tight
- 博弈 DP：必勝／必敗狀態、Nim（選修）
- 格子路徑計數與取模

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d085` 樹上最大獨立集
- `d091` 有障礙的格子路徑數
- `d094` 數位 DP

**真題（選做；題目到 vjudge／UVA／瘋狂程設閱讀，範例用 `cpe import` 匯入）：**
- `uva10404` Bachet's Game

**要讀的章節：**
- Competitive Programmer's Handbook 第 14 章『Tree algorithms』、第 25 章『Game theory』

**教材：**[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)、[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)

**常見陷阱：**
- 數位 DP 的『0 是否計入』
- 遞迴狀態沒有記憶化

**自我檢查（不看資料回答）：**
- tight 旗標為什麼只在前面都貼著上界時才為真？

**檢核（`cpe gate`）：**從空白檔、不看提示，90 分鐘內完成 `d092` 取石子遊戲、`d085` 樹上最大獨立集，至少答對 2 題。

### 單元 46　進階資料結構　（第 99 週）

**學完你能：**會稀疏表、BIT、分治計數。

**語言：C++**（`cpe new <題號> --lang cpp`）

**要學的：**
- Sparse Table（RMQ）；樹狀陣列 BIT；線段樹（選修）
- 分治：合併排序算逆序對
- 座標壓縮

**必做練習（本地判題，`cpe new <題號>` 自動安裝題目與測資）：**
- `d086` 逆序數對
- `d087` 區間最小值

**要讀的章節：**
- Competitive Programmer's Handbook 第 9 章『Range queries』、第 28 章『More segment trees』

**教材：**[CP-Algorithms（演算法百科）](https://cp-algorithms.com/)、[Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)

**常見陷阱：**
- BIT 的下標從 1 開始
- 答案可能超過 int

**自我檢查（不看資料回答）：**
- 逆序對為什麼可以在 merge 時順便算？

**檢核（`cpe gate`）：**從空白檔、不看提示，90 分鐘內完成 `d086` 逆序數對、`d087` 區間最小值，至少答對 2 題，用 C++。

### 單元 47　階段 4 驗收週　（第 100 週）

**學完你能：**累積 5 題的實力：完整模擬考至少 5 題，並報考 CPE。

**要學的：**
- 完整 3 小時模擬考；用 C++ 解需要效能的題、用 Python 解實作題
- 報考 CPE：目標 5 題（A 專業級上緣）

**延伸題庫：**
- CPE 歷屆三、四顆星題，按答對率排序，由高到低

**教材：**[CPE 官網（歷屆題目與答對率）](https://cpe.mcu.edu.tw/)

**自我檢查（不看資料回答）：**
- 你在考場上如何決定這題用 Python 還是 C++？

**檢核（`cpe gate`）：**模擬考（mock），至少答對 5 題。


---

## 階段 5 · 衝刺 6 題　（目標：CPE 6 題（A+））

### 單元 48　考試策略與工具箱　（第 101–104 週）

**學完你能：**把『會做』變成『考場上做得出來』。

**要學的：**
- 考場流程：先花 5 分鐘掃過所有題，從最簡單的開始（前三題通常最簡單）
- 時間分配：前 3 題 ≤ 60 分鐘；卡住 20 分鐘就換題
- 自己的模板：C++ 模板、Python I/O 模板、對拍腳本
- 除錯清單：邊界、溢位、初始化、多組測資是否清空、輸出格式
- 用 `cpe stress` 對拍找反例；用 `cpe mock start` 每週一場

**延伸題庫：**
- 每週一場完整模擬（3 小時），賽後必檢討每一題

**教材：**[CPE 官網（歷屆題目與答對率）](https://cpe.mcu.edu.tw/)

**自我檢查（不看資料回答）：**
- 你的考場 SOP 是什麼？寫成一張卡片。

**檢核（`cpe gate`）：**模擬考（mock），至少答對 4 題。

### 單元 49　弱點修補　（第 105–110 週）

**學完你能：**用統計找出最弱的三個主題，針對性補強。

**要學的：**
- `cpe weak`（或統計頁的『主題弱點』）依你的失敗次數、提示與重練失敗，列出最卡的主題；今日計畫會自動多排這些主題的題
- 每個弱點主題：重讀教材 → 做 10 題 → 重寫 → 考試
- 整理『錯題本』：每題寫下最初的錯誤想法與正確想法

**延伸題庫：**
- CPE 歷屆全體答對率 5%–20% 的題目
- Codeforces rating 1200–1600，指定弱點 tag

**教材：**[CPE 官網（歷屆題目與答對率）](https://cpe.mcu.edu.tw/)、[Codeforces 題庫（可依 tag / rating 篩選）](https://codeforces.com/problemset)

**自我檢查（不看資料回答）：**
- 你的弱點主題清單與補強計畫。

**檢核（`cpe gate`）：**模擬考（mock），至少答對 5 題。

### 單元 50　低答對率題攻堅　（第 111–118 週）

**學完你能：**能解全國答對率 5% 以下的題目。

**要學的：**
- 歷屆題中，答對率低於 5% 的題目通常是進階 DP／圖論／幾何／長模擬
- 做法：限時 60 分鐘 → 失敗後走提示階梯 → 24 小時後重寫
- 建立題型卡片：看到什麼特徵 → 想到什麼演算法

**延伸題庫：**
- CPE 歷屆三、四顆星題全部（約 4 場／年 × 2 題）
- Codeforces rating 1400–1800

**教材：**[CPE 官網（歷屆題目與答對率）](https://cpe.mcu.edu.tw/)、[Codeforces 題庫（可依 tag / rating 篩選）](https://codeforces.com/problemset)

**自我檢查（不看資料回答）：**
- 這類題的共同點是什麼？你的下一步行動？

**檢核（`cpe gate`）：**模擬考（mock），至少答對 5 題。

### 單元 51　全真模擬週　（第 119–124 週）

**學完你能：**穩定做到 6 題。每週一場完整模擬，連續多場達標。

**要學的：**
- 每週一場 3 小時全真模擬（ICPC 計分），賽後 2 小時檢討
- 模擬環境：關閉 AI 與搜尋、只開字典；用考場同版本 Python 3.9
- 目標：連續 3 場至少 2 場達到 6 題

**延伸題庫：**
- 自己出模擬：`cpe mock start`；也用歷屆題組出整場

**教材：**[CPE 官網（歷屆題目與答對率）](https://cpe.mcu.edu.tw/)

**自我檢查（不看資料回答）：**
- 最近三場模擬的題數與罰時趨勢？

**工程任務：**#8；#9；#10（`cpe eng` 查看）

**檢核（`cpe gate`）：**模擬考（mock），至少答對 6 題。

### 單元 52　報考與作品集　（第 125–126 週）

**學完你能：**實際報考；完成作品集，把競程能力轉成求職能力。

**要學的：**
- 考前一週清單：睡眠、環境測試、模板、字典
- 整理作品集：3 個專案（含 README、測試、說明）；把這個學習系統本身整理成作品
- 規劃下一步：實習、LeetCode／系統設計、專案經驗

**教材：**[Pro Git（繁中）](https://git-scm.com/book/zh-tw/v2)

**自我檢查（不看資料回答）：**
- 寫下你報考的日期與目標題數。

**工程任務：**#11（`cpe eng` 查看）

**檢核：**實際報考並記錄成績。

---

## 教材總表

- [Python 官方教學（繁中）](https://docs.python.org/zh-tw/3/tutorial/)
- [Python Tutor（逐步視覺化執行）](https://pythontutor.com/)
- [ZeroJudge（繁中題庫）](https://zerojudge.tw/)
- [AP325-Python 教材（吳邦一）](https://hackmd.io/@bangyewu/SJmDbdKSp)
- [王一哲教學網站（APCS）](https://sites.google.com/view/yizhe/%E8%AA%B2%E7%A8%8B/apcs)
- [CSES Problem Set（分類清楚、純標準輸入輸出）](https://cses.fi/problemset/)
- [Competitive Programmer's Handbook（免費 PDF）](https://cses.fi/book/book.pdf)
- [CP-Algorithms（演算法百科）](https://cp-algorithms.com/)
- [VisuAlgo（演算法動畫）](https://visualgo.net/)
- [Codeforces 題庫（可依 tag / rating 篩選）](https://codeforces.com/problemset)
- [AtCoder（ABC 的 A–D 題）](https://atcoder.jp/)
- [CPE 官網（歷屆題目與答對率）](https://cpe.mcu.edu.tw/)
- [learncpp.com（C++ 入門教學）](https://www.learncpp.com/)
- [cppreference（C++ 標準庫查詢）](https://en.cppreference.com/)
- [Pro Git（繁中）](https://git-scm.com/book/zh-tw/v2)

_網址可能變動，失效請自行搜尋名稱；章節編號以教材目錄為準。_
