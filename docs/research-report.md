# 以 GPT 助教打造「零基礎 → CPE 一次 6 題 → 工程師」自學系統：研究報告（2026 年 10 月版）

**結論先講：CPE 一次 6 題屬於「專家級」（A+），歷年只有約 0.7% 的考生做到；以每天 1–2 小時、從零開始的 Python 學習者來說，合理的預期是 18–30 個月，而且通常會需要在後期補上 C++。AI 助教在「只給提示、不給答案」的設計下有證據支持，但如果沒有護欄，反而可能讓獨立解題能力下降。**

## TL;DR

- **CPE 的實況**：每年 4 次，每次 7 題、3 小時，現場上機，採 ICPC 計分（先比題數，再比罰時，每次錯誤加 20 分鐘）。大專生免費，社會人士 500 元。可用 Python 3.9.6 作答。多數學校的畢業門檻只是「一次 2 題」或「累計 3 題」；6 題（A+ 專家級）是極少數人的成績。2015/03–2024/12 的累計統計中，答對 6 題的有 0.5%、7 題的有 0.2%，近兩年平均答對題數只有 0.65–1.5 題。
- **路線**：Python 基礎與 I/O → 一顆星選集 49 題（目標穩拿 2–3 題）→ 資料結構、排序／二分、前綴和、貪心 → BFS/DFS、DP、數論（4–5 題）→ 進階圖論／DP、效能優化，再加上 C++（6 題）。前 3 題多半能用 Python 寫完；後段題目受執行時間限制，Python 有風險，而且官方並未保證每題都能用 Python 通過。
- **AI 助教**：最強的證據來自 PNAS 2025 的隨機對照試驗。沒有護欄的 GPT-4 讓學生練習時表現提高 48%，但拿掉 AI 後考試成績比控制組低 17%；只給提示的版本則消除了這個傷害，只是並沒有提升考試成績。系統一定要把「提示階梯、禁止給完整解、定期無 AI 測驗」寫進規則裡；另外要記得，Silva 與 Costa（arXiv 2503.14630）評估 4 個 LLM 產生的 190 則提示，發現只有 63% 完全正確、37% 含有錯誤（行數判斷錯誤、解釋有誤或幻覺出不存在的問題），不能把它當成評分依據。

---

## Key Findings（依證據強度分級）

| 結論 | 證據等級 | 主要依據 |
|---|---|---|
| CPE 一場 7 題、3 小時，ICPC 計分，可用 Python 3.9.6 | **明確（官方）** | CPE 官網「環境與教材」、考試規則 |
| 每場至少 1 題出自「一顆星選集」（49 題），每場前三題為一顆星難度 | **明確（官方＋校方公告）** | 元智公告、CPE 官網 |
| 2027 年起，每場會有一題選自「CPE26 選集」 | **明確（官方），但選集內容未查證** | CPE 官網環境頁 |
| 6 題以上約占 0.7%，0 題約占 38.7% | **次級整理（社群彙整官方數據）** | yuihuang.com 彙整 2015–2024 統計 |
| ICPC 類賽事時限以 C++ 校準，Python 可能「解法正確仍超時」 | **共識（多方經驗＋ICPC WF 規則說明）** | Codeforces、ICPC 參賽者說法 |
| 無護欄 AI 會傷害後續獨立表現；有護欄可消除傷害 | **明確（PNAS RCT）** | Bastani et al. 2025\[1\] |
| GPT 程式回饋品質不穩定（約 6 成完全正確） | **明確（多篇研究）** | Phung et al. 2024；arXiv 2503.14630\[2\]\[3\] |
| 達 6 題所需的時間 | **經驗／推測** | 個人心得文、教練教材，無系統性研究 |

---

## 1. CPE（大學程式能力檢定）實況

### 1.1 考試形式與規則（官方資訊，最新查證 2026 年）

- **主辦與場次**：由臺灣程式競賽暨檢定學會主辦，評判系統是銘傳大學謝育平教授維運的「瘋狂程設」。中山大學資工系楊昌彪教授的簡介說明，自\[4\] 2012 年起每年舉辦四次。近年多在\[5\] 3、5、9/10、12 月的星期二晚上，例如 2025/03/25、2025/09/30、2025/12/09、2026/03/24、2026/05/26。
- **時程**：17:30–17:40 報到，17:40–18:30 環境測試，18:40–21:40 正式考試；18:00 之後不得入場。\[6\]\[7\]
- **題數與難度配置**：一場 7 題，配置是「3 題一顆星、2 題二顆星、1 題三顆星、1 題四顆星」，官方\[8\] SOP 也規定「經研判比較簡單的三題，編排為前三題」。官方歷次難易度統計表上，自\[9\] 2011 年起各場都是 3/2/1/1 的配置。\[10\]
- **題目來源**：題目來自 UVA Online Judge（官方文件寫「超過 4500 題」），以英文命題；考場提供線上英文字典。\[11\]\[12\]\[13\]
- **計分**：採 ACM-ICPC 規則，先比答對題數；題數相同時，比「答對題目的耗時總和＋每次錯誤送繳 × 20 分鐘」。\[7\]\[14\]
- **偵錯工具**：系統提供「題目預設測試資料」「自訂測試資料」「人工公開測試資料」，這三種測試都不計入成績。官方提醒，人工公開測資的難度和隱藏測資大致相同，但「無法保證通過『人工公開測試資料』者，必定可以通過『隱藏測試資料』」。\[7\]
- **可用語言**：C/C++（MinGW GCC 6.3.0、MSVC v140）、Java（AdoptOpenJDK 8／11）、**Python（Python 3.9.6）**。因此\[15\] **CPE 確定允許 Python**，但版本是 3.9.6，用不到 3.10 之後的 `match` 等語法。
- **I/O 規定**：只能用標準輸入輸出，不可讀寫檔案。官方考生手冊有 Python 範例，例如用 `while True: try: ... except EOFError: break` 讀到檔案結尾。\[16\]
- **違規處罰**：作弊者當次成績改為 0 題，並取消其後三次考試資格；大專生報名後無故缺考，取消下一次考試資格。\[17\]

### 1.2 報名方式與費用

- 先到 CPE 官網註冊帳號，再報名各場考試；**不接受現場報名**。以 2026-05-26 這場為例，報名期間是 2026-05-12 14:25 到 05-22 18:00，可選的應考地點有 44 處。\[18\]
- **費用**：大專學生免費；高中以下 400 元；社會人士 500 元。成績證明書大專生和高中以下每份 100 元，社會人士每份 200 元。\[18\]
- 不限在自己學校的考場應考，學校沒有協辦也可以報名。\[19\]

### 1.3 「一顆星選集」與 2027 年的新變化

- 官方「一顆星選集」共 49 題，依主題分成：基礎（如 UVA 10041 Vito's family、100 The 3n+1 problem）、字元與字串、數學計算、進位制轉換、質數／因數／倍數、幾何與座標、排序與中位數、模擬、其他。官方規定每場至少考一題。\[13\]\[20\]
- **新規則（需追蹤）**：官網環境頁已公告「2027 年起，CPE 題組將會有一題選自 CPE26 選集中」。我們無法從官方頁面確認\[15\] CPE26 選集的題目清單與公告日期。有一個非官方的模擬考專案標示「CPE26 選集 51／56 題」，由此推測「26」可能指\[21\] 2026 年而不是題數，但這只是推論。**請在 2027 年第一場考試前，用瀏覽器直接查看官網「環境與教材」頁確認。**

### 1.4 通過題數分布與成績等級

**官方等級對照**（中山大學楊昌彪教授〈CPE 簡介〉）：

| 等級 | 名稱 | 答對題數 | 官方能力說明 |
|---|---|---|---|
| A+ | 專家級 Expert | 6 題以上 | 熟悉各種進階演算法、資料結構，並具有優異的程式編寫能力 |
| A | 專業級 Professional | 4–5 題 | 熟悉基礎演算法、資料結構，具良好程式編寫能力 |
| A- | 進階級 Advanced | 3 題 | 熟悉程式設計邏輯，能以程式克服一般常見問題 |
| B | 中級 Intermediate | 2 題 | 具基礎程式編寫能力，能處理簡單問題 |
| C | 初級 Beginner | 1 題 | 具簡單程式編寫能力 |

**歷屆分布**（2015/03–2024/12 累計，社群網站 yuihuang.com 整理）：

| 答對題數 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|---|---|---|---|---|---|---|---|---|
| 人數比例 | 0.2% | 0.5% | 1.3% | 3.8% | 9.3% | 18.2% | 28.0% | 38.7% |

**近兩年平均答對題數**（官方各場頁面）：2025/03/25 是 1.5 題，2025/09/30 是 1.31，2025/12/09 是 1.08，2026/03/24 是 0.65，2026/05/26 是 0.75。\[22\]\[23\]\[24\]2026 年上半年的平均明顯偏低，原因不明，可能和題目難度或考生組成有關，屬於推測。

**這些數字代表什麼**：
- 一次 6 題大約落在前 0.7%，相當於排名前 1%。CPE 是能力檢定，不是競賽，但 6 題實際上已經是競賽選手的水準。
- 第 6、7 題通常是四顆星和三顆星題。以 2020/10/20 這場為例，各題「全體考生答對率」從前到後依序是：Hartals 37.94%、The Decoder 44.95%、Basically Speaking 17.94%、Graphical Editor 3.62%、Is It A Tree? 3.17%、Stamps 0.96%、String Theory 0.09%。\[25\]也就是說，要拿 6 題，必須能解出全國只有約 1% 考生解得出的題目。
- 有一個可以參考的個人歷程：某位考生從 2018/03 的 1 題、2018 年多次 2 題，到 2019 年 4–5 題，最後在 2020/06/09 拿到 7 題，前後約兩年多。\[26\]這是單一個案，不能代表一般情況，但足以說明「從 2 題到 6 題」往往要以年為單位計算。

### 1.5 各校畢業門檻（多數遠低於 6 題）

| 學校／系所 | 門檻 |
|---|---|
| 國立臺北大學資工系 | 一次通過 2 題；一次 5 題以上頒發「程式高手」榮譽獎勵 |
| 元智大學資訊學院英語學士班 | 一次 2 題或累計 3 題；一次 3 題可申請獎學金 |
| 國立雲林科技大學資工系（113/5/22 系務會議決議） | 學士班自第九學期起、碩士班自第五學期起可累計答題數，累計 3 題即符合 |
| 國立中興大學資管系（111 學年起入學） | 一次 2 題，或修過補救教學課程 |
| 臺中教育大學 | 一次 3 題或累計 4 題 |
| 東華大學、大同大學 | 一次 2 題或累計 3 題 |
| 中山大學 | 全校大一新生須通過兩題「中文命題」考試（非資工系通識用途） |
| 陽明交大資工 | 系內另有 GPE 檢定；據學生心得，CPE 抵免需 3 題全對\[27\] |

**解讀**：多數學校的畢業門檻是 2–3 題，大約對應前 30% 的考生。把目標設成 6 題，等於一路從「畢業門檻」拉到「競賽水準」。建議在系統裡把 2 題、3 題、4–5 題設成中間的里程碑。

---

## 2. 從零到 CPE 6 題的學習路線

### 2.1 知識順序與對應 CPE 題數

| 階段 | 核心內容 | 對應 CPE 能力 | 估計時數（每天 1–2 小時） | 練習量建議 |
|---|---|---|---|---|
| 0. 語法基礎 | 變數、型別、if/for/while、函式、list/str/dict 基本操作 | 0 → 1 題 | 120–180 小時（約 3–4 個月，可和大學課程同步） | 80–120 道入門題（ZeroJudge a 字頭、APCS 初級） |
| 1. 競程 I/O 與一顆星 | 多組測資讀到 EOF、`sys.stdin`、格式化輸出、字串處理、進位轉換、質數篩、GCD、模擬 | 1 → 2–3 題 | 100–150 小時（2–3 個月） | 一顆星 49 題全部自己寫完，並且能重寫 |
| 2. 資料結構與基礎演算法 | 排序（含自訂 key）、二分搜尋、前綴和、雙指標、stack/queue/deque、heap（`heapq`）、set/dict 應用、貪心、遞迴與窮舉 | 3 → 4 題 | 150–200 小時（3–4 個月） | 100–150 題（AP325 前半、UVA 二顆星） |
| 3. 圖論與 DP | 樹、圖的表示、BFS/DFS、連通元件、拓撲排序、最短路徑（Dijkstra）、並查集、基礎 DP（背包、LIS、LCS、區間）、數論（模運算、快速冪） | 4 → 5 題 | 200–300 小時（4–6 個月） | 120–200 題（AP325 後半、UVA 三顆星） |
| 4. 進階與效能 | 進階 DP、最小生成樹、回溯剪枝、計算幾何入門、大數、複雜度估算；**C++ STL 入門** | 5 → 6 題 | 250–400 小時（6–9 個月） | 150 題以上，加上每月一場模擬 CPE |

上表的時數是本報告根據教材範圍與個人心得估算的**經驗值**，沒有系統性研究支持。合計約 800–1,200 小時。以每天 1.5 小時、一年 300 個有效學習日來算，大約是 1.8–2.7 年。

### 2.2 不同來源的建議：共識與爭議

**有共識的部分**：
- **先把一顆星選集練熟**。官方保證每場至少一題出自選集，\[28\]各校教學和社群心得也一致建議從這裡下手，這是穩拿前 2–3 題最直接的方法。
- **I/O 處理是初學者最大的門檻**。官方手冊特別用一章講 C/C++/Python 的 I/O 寫法，考生心得也常提到前兩題卡在格式或邊界條件。\[29\]例如有位考生寫道：「前兩題水題竟然就花了我快一個半小時……結果是少寫一個 =」。\[30\]
- **CPE 的程度定位大約是大二「資料結構」**。官方文件寫明：「CPE 適合大二『資料結構』課程以上的程度」。\[31\]
- **以 APCS 級分作為銜接**。吳邦一教授的 AP325 教材（有 Python 版）就是為「已有 APCS 實作三級分、目標五級分」的人設計。教材說三級分大概是會做前兩題，第三、四題才涉及常見的資料結構與演算法。\[32\]這和 CPE 2→4 題的能力跨越很接近。

**有爭議或分歧的部分**：
- **要不要從 Python 開始**：有些教學網站建議 APCS 實作「使用 Python 可能會遇到超時的狀況，建議還是使用 C++」；也有考生在 CPE 中用 Python 內建的 `bin()`、`collections.Counter` 在 6 分鐘和 14 分鐘內解掉前兩題。**本報告的立場**：零基礎階段先用\[33\]\[34\] Python，因為它和你的大學課程一致、語法負擔低；到第 3、4 階段再補 C++。
- **CPE 到底測的是不是「程式能力」**：有工程師的部落格認為 CPE 測的是「解題能力」，而不是「把想法實現成程式」的工程能力。這正好說明，**CPE\[35\] 6 題和成為工程師是兩條需要分開規劃的能力線**（見第 6 節）。
- **刷題量與深度的取捨**：社群裡常見「出現頻率 4–5 次以上的考古題優先」的應試策略（交大 GPE 心得），也有教材強調系統性學習演算法。本報告建議前期以考古題為主，後期以演算法主題為主。\[27\]

---

## 3. 練習平台與資源比較

| 平台 | 難度分級 | 中文介面 | Python 適合度 | 可程式化取得題目資料 | 建議用途 |
|---|---|---|---|---|---|
| **瘋狂程設（CPE 官方）** | 顆星分級（一顆星廣場） | ✅ 中文 | ✅ 與考場環境相同（Python 3.9.6） | ❌ 未見公開 API | **模擬考場的唯一首選** |
| **CPE 官網歷屆考試** | 每題附全體答對率，可當作難度指標 | ✅ | ✅（部分題目附程式碼與題解影片） | ⚠️ 網頁可瀏覽，robots.txt 限制自動擷取 | 考古題，以答對率排序練習 |
| **UVA Online Judge** | 無官方分級（可靠 CPE 星等、社群整理補足） | ❌ 英文 | ⚠️ 支援 Python，但時限以 C/C++ 為準 | ⚠️ 無官方 API（社群工具 uHunt 有非官方 API，未於本研究驗證） | CPE 題目原始來源 |
| **ZeroJudge** | 題號分類＋APCS 標籤 | ✅ 繁中 | ✅ | ❌ 未見公開 API | 零基礎入門、APCS 考古題、UVA 中譯題 |
| **APCS（檢測本身）** | 程式實作分初級／中級／中高級／高級；程式識讀與程式實作各 1–5 級分 | ✅ 中文命題 | ✅ 實作可用 C/C++/Java/Python；識讀題本可選 C 或 Python | — | **適合當作中期檢核點**：每年 1、3、6、7、10、11 月舉辦，免費\[36\]\[37\] |
| **Codeforces** | 題目 rating 800–3500 | ❌ 英文／俄文 | ⚠️ 支援 Python／PyPy，難題容易超時 | ✅ **官方 API** `problemset.problems` 回傳 JSON（含 tags、rating）\[38\]\[39\] | 第 3–4 階段，以 rating 800–1600 題練習 |
| **AtCoder** | ABC 的 A–F 題難度遞增 | ❌ 日／英 | ✅ 初學者友善；Python 使用者多（一般認知，未於本研究驗證） | ⚠️ 社群「AtCoder Problems」提供非官方難度資料（未於本研究驗證） | 第 2–3 階段，ABC 的 A–D 題品質高 |
| **LeetCode** | Easy/Medium/Hard | ⚠️ 有中國站（簡中）；國際站英文 | ✅ 函式介面不需處理 I/O | ⚠️ 無正式公開 API | **面試準備**；但不訓練 CPE 必備的 stdin 處理 |
| **Kattis** | 1.0–10.0 難度分數 | ❌ 英文 | ✅ 支援 Python，社群有大量 Python 題解\[40\]\[41\] | ⚠️ 未見公開題目 API（未驗證） | 大量 ICPC 區域賽題目，第 3–4 階段 |
| **Exercism** | 由易到難的 track | ❌ 英文 | ✅ Python track 和導師回饋（未於本研究驗證細節） | — | 練習 **Pythonic 寫法與測試驅動**，對工程能力有幫助 |

**本報告的建議**：入門用 ZeroJudge 和 APCS，主力練習用 CPE 一顆星選集加瘋狂程設，進階用 AP325 和 Codeforces（API 很方便）。自動化系統的題庫可以優先串接 **Codeforces 官方 API**，它是表中唯一確認有官方公開 JSON API 的平台。CPE 相關題目則建議手動建立題庫，並附上「全體答對率」作為難度標籤。

---

## 4. Python 與競賽程式

### 4.1 優缺點

**優點**：語法簡潔，內建大整數（不會溢位），`collections`、`heapq`、`bisect`、`itertools` 等標準函式庫很強，字串處理方便。在 CPE 前幾題這類「實作／字串／數學」題型中，常常比 C++ 寫得更快。

**缺點**：執行速度慢。ICPC／ECPC 類競賽的時限是用 C++ 參考解校準的，有競程訓練教材實測：在同一台機器上做 10⁸ 次加法迴圈，Python 3.12 要 4.28 秒，大約是 C++ 的 25 倍。\[42\]ICPC 參賽者也指出，世界決賽「主辦方保證每題 C++ 與 Java 可解，但不保證 Python」。\[43\]

### 4.2 CPE 的具體情況

- **CPE 允許使用 Python**（官方環境頁列出 Python 3.9.6）。\[15\]
- **官方沒有公布每題時限，也沒有保證每題都能用 Python 在時限內通過**。官方 SOP 只定義了 TIMELIMIT 判定（「程式執行所花費的時間超過題目限制」）。\[7\]這一點的證據是**缺乏正面聲明**，不是官方明說「不保證」。
- **實務判斷（經驗性）**：

| 題型 | Python 可行性 |
|---|---|
| 一顆星：字串、進位、模擬、簡單數學、排序 | ✅ 幾乎都可行，而且常常寫得比 C++ 快 |
| 大數運算（如 UVA 10929 You can say 11、10220 這類） | ✅ Python 有優勢 |
| 二顆星：BFS/DFS（小圖）、簡單 DP、質數篩（≤10⁶） | ⚠️ 多數可行，需要用 `sys.stdin` 快速讀取，避免遞迴過深（`sys.setrecursionlimit`） |
| 三、四顆星：O(n²) 且 n≈10⁴ 以上、三維 DP、大量回溯、大圖最短路徑 | ❌ 高風險，建議改用 C++ |

**建議**：用 Python 拿下前 3–4 題；目標是 6 題時，最晚在第 4 階段開始學 C++ STL，考場上依照題型選語言。

---

## 5. LLM／GPT 助教對程式學習的影響

### 5.1 主要研究證據（優先列出隨機對照試驗與同儕審查論文）

| 研究 | 設計 | 主要結果 | 對本系統的意義 |
|---|---|---|---|
| **Bastani et al., PNAS 2025**（土耳其高中數學） | RCT，近 1,000 名學生，三組：無 AI／GPT Base（一般 GPT-4）／GPT Tutor（提示用、含教師設計的提示與解答） | 練習時 GPT Base 進步 48%、GPT Tutor 進步 127%；**拿掉 AI 後，GPT Base 組考試比控制組低 17%**；\[44\]\[45\]GPT Tutor 消除了這個負面效果，但考試成績沒有顯著提升\[46\]\[47\] | **「先提示、不直接給答案」能防止傷害，但本身不保證進步**；學生會把無護欄的 AI 當成「拐杖」\[1\] |
| **Nie et al.（Stanford Code in Place, 2024/2025）** | RCT，5,831 名程式入門學生，來自 146 國；含防止直接給解答的提示詞\[48\] | 只有 14.2%（510 人）實際使用；提供 GPT-4 的組別考試參與率 44.1%，對照組 48.5%（**下降 4.3 個百分點**，Bonferroni 校正後 P=.020）；使用者的考試分數估計提高 6.86 個百分點（BCa 90% CI 0.30–14.13，效果量 0.40），但經多重比較校正後不顯著；1–4% 的對話是在試圖騙取作業答案 | 提供 AI 可能**降低投入度**；效益集中在主動使用的人身上 |
| **Pankiewicz & Baker（ITiCSE 2024）** | 大學入門程式課，GPT-4 針對編譯錯誤給提示，控制組沒有提示 | 實驗組專注度較高、「困惑＋挫折」較低；但在 6 種常見錯誤上，**表現結果好壞參半**\[49\] | 情緒支持有效，能力提升不一定 |
| **Prather et al.「The Widening Gap」（ICER 2024）** | 21 場實驗室觀察（含參與式觀察、訪談與眼動追蹤），21 名新手中有 20 人完成題目 | 本來就會的學生用 AI 加速；**卡關的學生原有的後設認知困難沒有消失，還多了新的困難**，而且常有「能力錯覺」，以為自己表現比實際好\[50\] | 系統必須有「無 AI 的客觀檢測」來校正自我評估 |
| **Harvard CS50 Duck（SIGCSE 2024／2025）** | GPT-4／GPT-4o 加 RAG（課程字幕）加護欄，大規模部署\[51\]\[52\] | 學生普遍覺得有幫助；但團隊自己的分析指出，Duck 有**傾向提供過多程式碼範例**的問題，之後持續調整系統提示詞\[52\] | 護欄需要持續評估，不是寫一次提示詞就夠 |

### 5.2 AI 批改／除錯回饋的準確度與常見失誤

- **Phung et al.（LAK 2024）**：引用 Phung et al. ICER 2023 的基準研究指出，GPT-4 對入門 Python 錯誤程式的提示品質**只有約 60%**，人類助教則超過 90%。他們的方法是讓 GPT-4 產生提示，再用較弱的 GPT-3.5 模擬學生去「驗證」提示能不能幫忙修好程式；這樣精確度可以拉高到約 95%，接近人類助教，覆蓋率則在 73.3%–87.5% 之間（BasicAlgo 76.0%、DataRegex 87.5%、DataAnalysis 73.3%），其餘交給人工。有個值得注意的發現：用 GPT-4 當驗證者反而比較差，因為它「即使解釋是錯的，也能把程式修好」。\[2\]
- **arXiv 2503.14630（Silva & Costa，2025）**：評估 GPT-4o、GPT-4o-mini、GPT-4-Turbo、Gemini-1.5-pro 對 5 名學生撰寫的 45 份 Python 解答的回饋。判斷「程式對不對」的準確率分別是 GPT-4o-mini 84.44%、Gemini-1.5-pro 86.67%、GPT-4o 與 GPT-4-Turbo 各 88.89%，但在 190 則提示中**只有 63% 完全正確，37% 含有錯誤**，例如行數判斷錯誤、解釋有誤，或幻覺出不存在的問題（誤報）。
- **常見失誤類型**：(1) 漏掉錯誤；(2) 回饋本身是錯的；(3) 幻覺出不存在的問題；(4)\[53\] 把正確解答判成錯的；(5) 直接洩漏完整解答。

**結論**：AI 只能當「提示者」，**判斷對錯一律交給實際測資**（本地 judge 或瘋狂程設），不能讓 GPT 決定「你的程式對不對」。

### 5.3 「先提示、不直接給答案」有效嗎？

- **有證據支持的部分**：有護欄的提示型 AI **可以避免**無護欄 AI 造成的學習損害（PNAS 2025）；\[45\]\[47\]提示可以降低挫折感（Pankiewicz & Baker）。\[49\]
- **證據還不足的部分**：提示型 AI **能不能讓獨立解題能力明顯超過傳統自學**，目前沒有一致的證據。PNAS 研究中，提示組的考試成績沒有顯著提升；Stanford 的研究結果也不顯著。
- **風險**：學生可能繞過護欄，例如改用公開的 ChatGPT；可能出現能力錯覺；也可能降低投入度。

---

## 6. 從零到工程師：CPE 之外的能力

CPE 只訓練「演算法解題」這條能力線。要成為工程師，還需要另一條「軟體工程」能力線。建議從第 2 階段開始並行，每週撥出約 20–30% 的時間：

| 能力 | 具體目標 | 和本系統結合的方式 |
|---|---|---|
| **Git／GitHub** | commit、branch、PR、`.gitignore` | 每天的解題程式碼都 commit 到 GitHub，自然累積學習紀錄 |
| **測試** | `pytest`、邊界案例、對拍（暴力解 vs 正解） | 「對拍」本身就是競程技巧：用 Python 寫暴力解，隨機產生測資驗證正解 |
| **專案結構** | 模組化、`pyproject.toml`、虛擬環境、型別提示、linter | 把你的「自學系統」本身寫成一個正式專案 |
| **資料庫** | SQL 基礎（SQLite → PostgreSQL）、正規化 | 用 SQLite 存題目、提交紀錄、錯誤類型 |
| **CLI／Web** | `argparse`／`typer` CLI → FastAPI／Flask → 部署 | 先做 CLI 版本的練習系統，再做 Web 介面 |
| **API 與 LLM 應用** | 呼叫 OpenAI API、提示設計、成本控管 | 本系統本身就是作品集 |

**台灣職缺趨勢（概述）**：
- 104《2026 年科技業人才報告書》指出，科技業每月人才缺口約 19.3 萬人，其中「軟體／工程類人員每月徵才 2.5 萬人最多」。不過，104 人才永續長鍾文雄也提到，企業對工程師的需求「正從『量』的擴張轉向『質』的盤整」，軟體／工程類工作機會呈現年減。\[54\]
- 104 的數據顯示，2025 年 11 月 AI 相關工作機會有 9.9 萬個，年增 38%；《104 AI 人才趨勢報告》指出，近 5 年 AI 人才需求成長 97.6%。\[55\]\[56\]
- **解讀**：入門工程師的競爭變得更激烈，企業更看重「能交付的作品」和「會用 AI 工具提升產能」。CPE 成績在部分企業和研究所甄試中有參考價值（官方說法），但**作品集和工程實務能力才是求職的主力**。這一段屬於推論。

---

## 7. 建議學習時程表（每天 1–2 小時）

以 2026 年 11 月開始、每週 6 天計算。

| 期間 | 階段 | 每週內容 | 檢核點（全部要能在**無 AI 協助**下完成） |
|---|---|---|---|
| 第 1–3 個月（2026/11–2027/01） | 0. Python 基礎 | 大學課程＋每天 2–3 題 ZeroJudge 入門題 | ✅ 能獨立寫出讀多組測資到 EOF 的程式；✅ 60 題入門題 |
| 第 4–5 個月（2027/02–03） | 1. 一顆星選集 | 每週 5–6 題一顆星；週末重寫錯題 | ✅ **2027/03 首次報考 CPE，目標 1–2 題**（大專生免費，越早熟悉考場越好）；✅ 一顆星選集完成 25 題 |
| 第 6–7 個月（2027/04–05） | 1→2 | 完成一顆星 49 題；開始排序、二分、前綴和 | ✅ **2027/05 CPE 目標 2 題**（達到多數學校的畢業門檻）；✅ 49 題能在 30 分鐘內重寫任一題 |
| 第 8–11 個月（2027/06–09） | 2. 資料結構 | AP325-Python 前半；stack/queue/heap/貪心；開始建立 Git 習慣 | ✅ 報考 APCS 中級或中高級實作；✅ **2027/09–10 CPE 目標 3 題**（A- 進階級） |
| 第 12–17 個月（2027/10–2028/03） | 3. 圖論與 DP | BFS/DFS、DP、並查集、Dijkstra；Codeforces rating 800–1300；CLI 小專案 | ✅ **CPE 目標 4 題**（A 專業級）；✅ 完成一個含 pytest 的 CLI 專案 |
| 第 18–24 個月（2028/04–10） | 4. 進階＋C++ | C++ STL；進階 DP／圖論；每月一次 3 小時全真模擬 | ✅ **CPE 目標 5 題**；✅ 同一題能用 C++ 改寫並通過時限 |
| 第 25–30 個月（2028/11–2029/04） | 衝刺 6 題 | 專攻三、四顆星題型；檢討歷屆答對率低於 5% 的題目 | ✅ **CPE 6 題（A+）**；✅ Web 專案上線、作品集完成 |

**提醒**：這份時程是以「順利的情況」排出來的。如果卡在 3–4 題的平台期，延長 6–12 個月也屬正常，那位從 1 題進步到 7 題的考生就花了大約兩年多。每一場 CPE 都把它當成正式的進度檢核。

---

## 8. 對學習系統設計的具體建議

### 8.1 每日練習模組

- **間隔重練**：答錯或依賴提示才完成的題目，分別在 1 天、3 天、7 天後要求「無提示重寫」。只有重寫通過，才算真正掌握。
- **難度標籤**：CPE 題目用官方的「全體考生答對率」當作客觀難度；Codeforces 題目用 API 的 rating。
- **判題交給測資，不交給 GPT**：在本地建一個 judge（Python 3.9.6 環境，以 subprocess 執行並設定時限），用範例測資、自訂邊界測資、暴力對拍來判斷對錯。GPT 只負責解釋和提示。研究顯示 LLM 的回饋約有 37% 含錯誤。
- **記錄錯誤類型**：例如 I/O 格式、邊界、超時、演算法選錯，每週由 GPT 產生摘要，但摘要以統計數據為準。

### 8.2 引導式提示（Hint Ladder）

把提示寫成強制分級，每升一級都要先提交新的嘗試：
1. **L0 理解題意**：只用中文重述題目、指出輸入輸出格式，不談解法。
2. **L1 方向**：「這題屬於哪一類？」只給分類，例如「前綴和」。
3. **L2 關鍵觀察**：用一句話說明核心觀念。
4. **L3 虛擬碼骨架**：只給結構，不給完整程式。
5. **L4 指出錯誤所在**：根據失敗的測資指出問題所在的行和原因，**不直接修正**。
6. **完整解答**：只在「放棄」並冷卻 24 小時之後開放，而且之後必須無提示重寫。

**系統提示詞的設計要點**：參考 PNAS 研究中 GPT Tutor 的作法，把**標準解法和教師設計的提示放進提示詞**，以減少幻覺；\[44\]明確禁止輸出完整程式碼；並在輸出端做過濾，例如偵測程式碼區塊超過 N 行就攔截。CS50 的經驗說明，即使有護欄，模型仍然傾向給出過多程式碼，\[52\]所以需要定期抽查對話紀錄。

**驗證機制**：參考 Phung et al. 的作法，GPT 產生提示後，可以用一個較便宜的模型扮演「學生」，看能不能靠這個提示修好程式；修不好就不送出這個提示。\[57\]

### 8.3 模擬 CPE 考試

- **規格要完全模擬**：7 題（3 題一顆星、2 題二顆星、1 題三顆星、1 題四顆星），3 小時，英文題目，**完全禁用 AI**，只允許查字典；採 ICPC 計分（錯一次加 20 分鐘）；提供「人工公開測資」與「隱藏測資」兩層判題。
- **頻率**：第 1 階段每月一次，只出前 3 題、90 分鐘；第 3 階段之後每月一次完整 3 小時。
- **考後檢討**：GPT 只在交卷之後介入，針對沒解出的題目走一次提示階梯。
- **真實考試優先**：每年 4 次 CPE 和 APCS 都是免費（大專生）的客觀檢測，**模擬考不能取代它們**。\[5\]

### 8.4 風險與因應

| 風險 | 證據 | 因應 |
|---|---|---|
| 把 AI 當拐杖，獨立能力下降 | PNAS 2025：無護欄組考試低 17%\[46\] | 提示階梯、禁止給完整程式碼、每週一次無 AI 測驗 |
| 能力錯覺 | Prather et al. 2024\[50\] | 用「無提示重寫通過率」和「模擬考題數」當主要指標，不採信自我感覺 |
| GPT 回饋出錯 | 約 37% 的提示有問題\[58\] | 以測資判定對錯；提示附上「可能有誤」的標示；用雙模型驗證 |
| 繞過護欄，改用公開 ChatGPT | Nie et al. 坦言「沒有花足夠時間測試護欄是否容易被繞過」；問卷中約 2% 學生自述在課外用過 ChatGPT | 靠自律和設計：系統不擋，但會記錄「有沒有使用外部 AI」 |
| 投入度下降 | Stanford RCT：考試參與率 44.1% 對 48.5%，下降 4.3 個百分點 | 把每場真實 CPE 排進行事曆作為外部承諾；設定可見的里程碑 |
| Python 超時 | ICPC 時限以 C++ 校準 | 第 4 階段導入 C++；建立「Python 高風險題型」清單 |
| CPE 規則變動 | 2027 年起加入 CPE26 選集 | 每學期開始前查一次官網；把 CPE26 選集納入題庫 |
| 只練解題，忽略工程能力 | CPE 的定位本身就是解題 | 從第 2 階段起，每週 20–30% 時間投入 Git、測試、專案 |
| API 成本與隱私 | — | 對話紀錄存在本地；用較小的模型做驗證；設定每日 token 上限 |

---

## 9. 官方與主要練習入口

| 資源 | 網址 |
|---|---|
| CPE 官網（銘傳，資料較新） | https://cpe.mcu.edu.tw/ |
| CPE 官網（中山） | https://cpe.cse.nsysu.edu.tw/ |
| CPE 環境與教材（一顆星選集、考試語言版本） | https://cpe.mcu.edu.tw/environment.php |
| CPE 最新考試／報名資訊 | https://cpe.mcu.edu.tw/newest.php |
| CPE 歷屆題目與答對率 | https://cpe.mcu.edu.tw/cpe/test_data/problems |
| CPE 考生使用手冊（含 Python I/O） | https://cpe.cse.nsysu.edu.tw/doc/CPE_manual.pdf |
| CPE 作業流程（SOP） | https://cpe.cse.nsysu.edu.tw/doc/CPE_sop.pdf |
| CPE 成果報告（2024/12） | https://cpe.cse.nsysu.edu.tw/doc/CPE_report_241210.pdf |
| AP325-Python（吳邦一） | https://hackmd.io/@bangyewu/SJmDbdKSp |
| Codeforces API | https://codeforces.com/apiHelp |
| PNAS 2025（Bastani et al.） | https://www.pnas.org/doi/10.1073/pnas.2422633122 |
| Stanford GPT Surprise（Nie et al.） | https://arxiv.org/abs/2407.09975 |
| The Widening Gap（Prather et al.） | https://arxiv.org/abs/2405.17739 |
| GPT-4 編譯錯誤提示研究 | https://arxiv.org/pdf/2403.12737 |
| GPT-4 提示生成與驗證（Phung et al.） | https://arxiv.org/pdf/2310.03780 |
| LLM 回饋品質評估（2025） | https://arxiv.org/html/2503.14630 |

---

## Caveats（資料時效與限制）

- **CPE 官方網站多數頁面禁止自動擷取**。2025–2026 的平均答對題數、報名資訊、CPE26 選集公告，都來自官方頁面的搜尋摘要，以及一個研究子代理的交叉查核；兩個官網的內容也不完全同步，銘傳站較新。**CPE26 選集的題目清單和公告日期沒有查到**，報名前請用瀏覽器確認。
- 「6 題約 0.7%」這個數字來自社群網站整理的 2015–2024 累計資料，不是官方直接公布的統計；最新的成果報告 PDF 沒能讀到。
- 考場的 Python 版本（3.9.6）是 2021/10 安裝包的資訊，之後可能更新。
- 各校畢業門檻是根據各系公告整理，部分公告已有數年歷史，請以所屬系所最新規定為準。
- 第 2 節的時數、第 7 節的時程，都是**經驗性推估**，沒有對照研究支持。
- AI 教育研究多數在數學或入門程式課進行，期間短（數週），使用的是 GPT-4 世代的模型；結果套用到「CPE 競程自學」和 2026 年的新模型時，需要保留空間。PNAS 研究的對象是高中數學，不是程式。
- 平台比較表中標示「未於本研究驗證」的項目，是根據一般認知，請在串接前實際確認。
- 104 人力銀行的數據屬於企業自行發布的調查與新聞稿，定義（例如「AI 相關工作」）由該公司訂定。

## 資料來源

1. [Generative AI without guardrails can harm learning: Evidence from high school mathematics](https://www.pnas.org/doi/10.1073/pnas.2422633122)
2. [\[2310.03780\] Automating Human Tutor-Style Programming Feedback: Leveraging GPT-4 Tutor Model for Hint Generation and GPT-3.5 Student Model for Hint Validation](https://ar5iv.labs.arxiv.org/html/2310.03780)
3. [Assessing Large Language Models for Automated Feedback Generation in Learning Programming Problem Solving](https://arxiv.org/html/2503.14630)
4. [CPE](https://sites.google.com/view/yzuibpi-chi/cpe)
5. [-1- 大學程式能力檢定(CPE)簡介 中山大學資工系 楊昌彪 2020/10/29](https://nur.asia.edu.tw/uploads/asset/data/607f9288905fc3c8cc00002a/CPE_introduction.pdf)
6. [CPE心得 更新於：2016/05/28 - BAHAMUT000的創作 - 巴哈姆特](https://home.gamer.com.tw/creationDetail.php?sn=2192261)
7. [大學程式能力檢定(CPE)作業流程 國立中山大學資訊工程學系 2021/3/23 CPE 整體作業流程 日期 工作項目 主辦學校 (中山大學) 技術團隊](https://cpe.cse.nsysu.edu.tw/doc/CPE_sop.pdf)
8. [【筆記】CPE 大學程式能力檢定](https://andyli.tw/cpe/)
9. [CPE 考試當天流程 一、 考試時程： (一) 工作人員就位：17:00-17:20，登入中山網路大學(JoinNet)，並 取得考官密碼。](https://cpe.cse.nsysu.edu.tw/doc/CPE_examsop.pdf)
10. [大學程式能力檢定(CPE) 2025/09/30 成果報告 謝育平 銘傳大學資訊工程學系](https://cpe.mcu.edu.tw/doc/CPE_report_250930.pdf)
11. [大學先修課程資訊平台](https://cis.ncu.edu.tw/ApcourseSys/search/searchCrs/94)
12. [CPE大學程式能力檢定｜大學程式能力檢定委員會｜104證照中心 - 104學習](https://nabi.104.com.tw/ability/10028328)
13. [大學程式能力檢定, CPE, Collegiate Programming Examination, 國立中山大學, National Sun Yat-sen University](https://cpe.cse.nsysu.edu.tw/environment.php)
14. [CPE大學程式能力檢定 \_ 大學程式能力檢定委員會簡介 \_ 證照中心](https://certify.104.com.tw/cfdocs/edu/certify/certify.cfm?cert_no=4002038019)
15. [大學程式能力檢定, CPE, Collegiate Programming Examination, 銘傳大學, Ming Chuan University](https://cpe.mcu.edu.tw/environment.php)
16. [\- 1- 大學程式能力檢定(CPE) 考生使用手冊 2022 年9 月19 日 這份手冊提供給參加CPE 檢定考試的考生。內容包含考試環境的使](https://cpe.cse.nsysu.edu.tw/doc/CPE_manual.pdf)
17. [大學程式能力檢定(CPE) - 最新消息 - 新聞訊息 - 元智大學資訊學院英語學士班](https://www.in.yzu.edu.tw/tw/modules/news/article.php?storyid=16)
18. [大學程式能力檢定, CPE, Collegiate Programming Examination, 銘傳大學, Ming Chuan University](https://cpe.mcu.edu.tw/newest.php)
19. [5/24大學程式能力檢定(CPE) 大專學生免費報考!! 2016-05-05](https://www.csie.ncu.edu.tw/announcement/560c8c128d352f7e8a719c8d1661001f)
20. [大學程式能力檢定, CPE, Collegiate Programming Examination, 銘傳大學, Ming Chuan University](https://cpe.mcu.edu.tw/)
21. [GitHub - SunnyTee2005/coding-frenzy · GitHub](https://github.com/SunnyTee2005/coding-frenzy)
22. [2026/05/26 CPE (\_平均答對題數：0.75)](https://cpe.mcu.edu.tw/cpe/test_data/2026-05-26)
23. [2025/03/25 CPE (\_平均答對題數：1.5)](https://cpe.mcu.edu.tw/cpe/test_data/2025-03-25)
24. [Collegiate Programming Examination](https://cpe.mcu.edu.tw/cpe/test_data/problems)
25. [2020/10/20 CPE (平均答對題數：1.09)](https://cpe.cse.nsysu.edu.tw/cpe/test_data/2020-10-20)
26. [CPE 解題紀錄 -心路歷程(從1題到7題成長史)](https://louisfghbvc.pixnet.net/blog/posts/17324806590)
27. [\[心得\] 交大GPE 程式檢定考考試心得 - 型號藍の小屋](https://blog.setsal.dev/nctu-gpe/)
28. [【考試】104/05/26(二)舉辦大學程式能力((Collegiate Programming Examination, CPE))檢定活動 - 圖資處資訊服務](https://ccenter2.ncue.edu.tw/files/14-1008-10167,r28-1.php?Lang=zh-tw)
29. [2011年大學程式能力檢定 CPE(Collegiate Programming Examination) 2011 第二次會議紀錄](https://cpe.cse.nsysu.edu.tw/doc/CPE_meeting_111020.pdf)
30. [CPE心得 - Kola (Yan-Hao Wang) - Medium](https://cozy-kola.medium.com/cpe%E5%BF%83%E5%BE%97-%E6%8C%81%E7%BA%8C%E6%9B%B4%E6%96%B0%E4%B8%AD-1f8a07bdcbeb)
31. [大專學生免費報考-大學程式能力檢定 (CPE)](https://competition.npust.edu.tw/2024/04/30/%E5%A4%A7%E5%B0%88%E5%AD%B8%E7%94%9F%E5%85%8D%E8%B2%BB%E5%A0%B1%E8%80%83-%E5%A4%A7%E5%AD%B8%E7%A8%8B%E5%BC%8F%E8%83%BD%E5%8A%9B%E6%AA%A2%E5%AE%9A-cpe-3/)
32. [AP325-Python 第0章 教材說明與預備知識 - HackMD](https://hackmd.io/@bangyewu/SJmDbdKSp)
33. [王一哲的教學網站 - APCS](https://sites.google.com/view/yizhe/%E8%AA%B2%E7%A8%8B/apcs)
34. [20221213 CPE大學程式能力檢定 心得文](https://cbjsprogramdiary.com/2022/12/21/20221213-cpe%E5%A4%A7%E5%AD%B8%E7%A8%8B%E5%BC%8F%E8%83%BD%E5%8A%9B%E6%AA%A2%E5%AE%9A-%E5%BF%83%E5%BE%97%E6%96%87/)
35. [邁向王者的旅途: \[隨筆\] 程式能力該如何檢定?](https://shininglionking.blogspot.com/2015/07/blog-post.html)
36. [想讀資工資管，必懂APCS三重點（2026新版） - 大學考情](https://www.unews.com.tw/News/Info/1874)
37. [APCS 準備攻略：看懂級分的意義，才知道該練什麼（2026）](https://orangeapple.co/articles/apcs-preparation-strategy)
38. [Codeforces API - Codeforces](https://codeforces.com/apiHelp)
39. [Exploring the CodeForces API](https://iq.opengenus.org/exploring-codeforces-api/)
40. [kattis-problems · GitHub Topics · GitHub](https://github.com/topics/kattis-problems)
41. [kattis-solutions · GitHub Topics · GitHub](https://github.com/topics/kattis-solutions)
42. [GitHub - Tayel-Ai-Labs-Courses/Competitive-Programming: ALGORTHIMS WORLD · GitHub](https://github.com/Tayel-Ai-Labs-Courses/Competitive-Programming)
43. [Can Python be used in ACM ICPC? - Quora](https://www.quora.com/Can-Python-be-used-in-ACM-ICPC)
44. [Generative AI Without Guardrails Can Harm Learning](https://hamsabastani.github.io/education_llm.pdf)
45. [(PDF) Generative AI without guardrails can harm learning: Evidence from high school mathematics](https://www.researchgate.net/publication/393011815_Generative_AI_without_guardrails_can_harm_learning_Evidence_from_high_school_mathematics)
46. [Generative AI without guardrails can harm learning: Evidence from high school mathematics.](https://www.semanticscholar.org/paper/Generative-AI-without-guardrails-can-harm-learning:-Bastani-Bastani/60570ad3268871882c65f6ed4ead35db4b220528)
47. [Valerio Capraro on X: "Generative AI can harm learning. A field experiment published in PNAS randomized nearly 1,000 high-school students across three conditions during mathematics classes: - textbooks and notes only - a standard GPT-4 interface - a safeguarded GPT-4 tutor that provided hints rat… / X](https://x.com/ValerioCapraro/status/2080301862524186943)
48. <https://arxiv.org/pdf/2407.09975>
49. [Navigating Compiler Errors with AI Assistance - A Study of GPT Hints in an Introductory Programming Course](https://dl.acm.org/doi/10.1145/3649217.3653608)
50. [\[2405.17739\] The Widening Gap: The Benefits and Harms of Generative AI for Novice Programmers](https://arxiv.org/abs/2405.17739)
51. [Debugging with an AI Tutor: Investigating Novice Help-seeking Behaviors and Perceived Learning](https://dl.acm.org/doi/fullHtml/10.1145/3632620.3671092)
52. [Improving AI in CS50 Leveraging Human Feedback for Better Learning Rongxin Liu](https://cs.harvard.edu/malan/publications/fp0627-liu.pdf)
53. [Improving the Coverage of GPT for Automated Feedback on ...](https://aicet.comp.nus.edu.sg/wp-content/uploads/2024/10/gaied23-gpt.pdf)
54. [104 AI職涯顧問發布《2026年科技業人才報告書》 人才缺口達19.3萬｜104職場力](https://blog.104.com.tw/104data-tech-industry-recruit-2026/)
55. [AI職缺年增4成至9.9萬！3/4企業幫AI人才加薪近10% 104「職涯平台」一站媒合到位](https://news.cnyes.com/news/id/6291157)
56. [近5年AI人才需求成長97.6% 學習AI職涯鍍金起薪溢價69%最高｜壹蘋新聞網](https://news.nextapple.com/finance/20260624/E8F58C18C56CB2428455A75603EF0B7C)
57. [Exploring the Potential and Limitations of Large Language Models for Novice Program Fault Localization](https://arxiv.org/pdf/2512.03421)
58. [Assessing Large Language Models for Automated](https://arxiv.org/pdf/2503.14630)
