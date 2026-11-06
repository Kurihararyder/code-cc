"""Python 軌道（52 個單元）：每個單元要讀哪裡、讀完要抓什麼重點。

依據（實際查過的目錄）：
- Python 官方教學（docs.python.org/zh-tw/3/tutorial）：章節號（例如 5.1.3）。gen_course.py 會驗證每個章節號都存在。
- Competitive Programmer's Handbook：書上印的頁碼；CP-Algorithms：文章標題；learncpp.com：課號（C++ 單元）。這些共用 course_cpp_readings.py 的驗證表。
- 其他（CSES 題單分類、CPE 官網、ZeroJudge 等）：只寫名稱，不寫頁碼。

格式與 C++ 軌道相同：(來源, 範圍, [重點…], 頁碼或 None)。
"""
from course_cpp_readings import cph, ca, lc, bk  # noqa: F401

# Python 官方教學的章節號（繁中版目錄；供驗證）。
PYTUT = set()


def _add(ch, subs):
    PYTUT.add(str(ch))
    for s in subs:
        PYTUT.add(f"{ch}.{s}" if not isinstance(s, tuple) else f"{ch}.{s[0]}")
        if isinstance(s, tuple):
            for t in s[1]:
                PYTUT.add(f"{ch}.{s[0]}.{t}")


for _c in (1, 13):
    PYTUT.add(str(_c))
_add(2, [(1, [1, 2]), (2, [1])])
_add(3, [(1, [1, 2, 3]), 2])
_add(4, [1, 2, 3, 4, 5, 6, 7, 8, (9, [1, 2, 3, 4, 5, 6, 7, 8]), 10])
_add(5, [(1, [1, 2, 3, 4, 5]), 2, 3, 4, 5, 6, 7, 8])
_add(6, [(1, [1, 2, 3]), 2, 3, (4, [1, 2])])
_add(7, [(1, [1, 2, 3, 4]), (2, [1, 2])])
_add(8, list(range(1, 11)))
_add(9, [1, (2, [1]), (3, [1, 2, 3, 4, 5]), 4, (5, [1]), 6, 7, 8, 9, 10])
_add(10, list(range(1, 13)))
_add(11, list(range(1, 9)))
_add(12, [1, 2, 3])
_add(14, [1, 2])
_add(15, [1])
_add(16, [(1, [1, 2, 3, 4])])
for _x in ("4.9.3.1", "4.9.3.2", "4.9.3.3", "4.9.3.4", "4.9.3.5"):
    PYTUT.add(_x)


def py(where, focus):
    return ("pytut", where, focus, None)


R = {}

# ---------------- 階段 0 ----------------
R[1] = [py("2.1、3.1.1–3.1.2", ["在直譯器互動模式做小實驗；數字運算與字串的基本操作；`/`、`//`、`%`、`**` 的差別"]),
        py("7.1.1", ["f-string：把變數放進輸出、控制小數位數與對齊"]),
        bk("pytutor", "Python Tutor 視覺化", ["用逐步執行看變數如何改變，找出自己『以為』和『其實』的差距"]),
        bk("cses", "CSES Introductory Problems 的前幾題", ["熟悉標準輸入輸出的判題方式（選做）"])]
R[2] = [py("4.1", ["if／elif／else 的結構與縮排"]), py("5.7", ["條件的更多細節：and／or 的短路求值、鏈式比較 `a < b < c`、真假值（空容器為假）"]),
        bk("pytutor", "Python Tutor 視覺化", ["逐步看條件走哪條分支"])]
R[3] = [py("4.2–4.5", ["for／range()／break／continue／迴圈的 else；range 的半開區間"]), py("5.6", ["迴圈技巧：enumerate、zip、reversed、sorted"]),
        cph(17, 19, "CPH 2.1 計算規則", ["迴圈次數怎麼換算成時間複雜度（兩層迴圈就是 n²）"])]
R[4] = [py("3.1.2", ["字串的索引、切片、不可變"]), py("3.1.3", ["list 的索引、切片、可變"]), py("5.1", ["list 的常用方法與 comprehension 的入門"]),
        py("5.3", ["tuple 與序列的解包"])]
R[5] = [py("5.4–5.5", ["set 的集合運算與去重；dict 的增查刪與迭代；鍵必須可雜湊"]),
        py("4.8、4.9.1–4.9.2", ["定義函式、回傳值、預設引數、關鍵字引數；預設引數用可變物件的陷阱"]),
        py("9.2", ["作用域與命名空間：區域與全域變數、global／nonlocal"])]
R[6] = [py("3.1.1、4.8", ["整數沒有溢位（任意精度）；divmod；函式拆分重複計算"]), py("15.1", ["浮點數的表示誤差：為什麼 0.1 + 0.2 != 0.3"]),
        cph(10, 14, "CPH 1.5 數學預備知識", ["和公式、集合論、邏輯、函數等會在題目裡用到的基本觀念"])]
R[7] = [py("5.1.3–5.1.4", ["list comprehension 與巢狀的寫法；用它建立二維陣列（小心 `[[0]*m]*n` 的共用參考）"]),
        bk("pytutor", "Python Tutor 視覺化", ["看二維 list 的別名（aliasing）如何造成『一改全改』"])]
R[8] = [py("8.1–8.3", ["讀懂 traceback；例外的基本處理"]), bk("zj", "ZeroJudge 基礎題", ["限時完成驗收題組的練習來源"])]

# ---------------- 階段 1 ----------------
R[9] = [py("7.1.1", ["格式化輸出複習"]),
        bk("cpe", "CPE 官網『考生使用手冊』", ["考場的輸入輸出方式與 Python 版本（3.9.6）"]),
        bk("cses", "CSES Introductory Problems", ["多組輸入與讀到 EOF 的練習"])]
R[10] = [py("7.1.1–7.1.3", ["f-string 與 str.format 的格式規格：寬度、對齊、小數位數"]), py("15.1", ["浮點誤差；輸出小數時四捨五入的處理"]),
         py("5.5", ["用 dict 做字元／字串映射"])]
R[11] = [py("3.1.1", ["Python 的大整數：直接運算即可，不必自己實作"]),
         cph(6, 7, "CPH 1.3 處理數字", ["整數溢位（Python 沒有，但 C++ 有）、模運算、浮點誤差——為什麼同一題換語言要小心"])]
R[12] = [ca("Sieve of Eratosthenes", ["篩法的做法與 O(n log log n)"]), cph(197, 200, "CPH 21.1 質數與因數", ["質因數分解、約數個數與和、質數判定"]),
         ca("Euclidean algorithm for computing the greatest common divisor", ["gcd 與 lcm"])]
R[13] = [bk("pytutor", "Python Tutor 視覺化", ["二維陣列與座標的對應"]), bk("py_docs", "Python 文件：sys.stdin", ["一次讀完所有輸入：`sys.stdin.read().split()`"]),
         py("5.1.3–5.1.4", ["用 comprehension 處理格子"])]
R[14] = [py("10.8", ["datetime 模組（考場可用，但很多題要自己算日期會更可靠）"]), py("5.1.1", ["用 list 當 stack：解析運算式的基本工具"]),
         bk("py_docs", "Python 文件：str 的方法", ["split、strip、isdigit 等字串解析常用方法"])]
R[15] = [bk("cpe", "CPE 官網歷屆題目與答對率", ["挑一顆星的題目做；先看答對率判斷難度"]), bk("cses", "CSES Introductory Problems", ["補充練習"])]
R[16] = [bk("cpe", "CPE 官網『考生使用手冊』", ["報名、考場規則與 Python I/O 範例"]), cph(15, 16, "CPH 1.6 競賽與資源", ["賽後怎麼檢討、怎麼找題"])]

# ---------------- 階段 2 ----------------
R[17] = [cph(17, 23, "CPH 第 2 章 時間複雜度", ["計算規則與複雜度類別；用輸入規模估算可行性（p.21）；最大子陣列和的三種做法（pp.21–23）"]),
         cph(25, 30, "CPH 3.1–3.2 排序", ["排序理論與下界；C++ 的 sort（概念同 Python 的 sorted／key）"]),
         bk("visualgo", "VisuAlgo：Sorting", ["動畫看各排序的運作與複雜度"])]
R[18] = [cph(31, 33, "CPH 3.3 二分搜尋", ["三種寫法：找值、找邊界、對答案二分"]), cph(84, 85, "CPH 9.1 靜態陣列查詢", ["一維與二維前綴和"]),
         py("11.7", ["bisect 的 bisect_left／bisect_right（用在二分，比手寫穩定）"])]
R[19] = [cph(77, 80, "CPH 8.1–8.2", ["雙指標、最近較小元素：為什麼是 O(n)"]), cph(81, 82, "CPH 8.3 滑動視窗最小值", ["單調 deque 的維護"]),
         ca("Minimum Stack / Minimum Queue", ["以單調結構維護最小值"])]
R[20] = [cph(41, 43, "CPH 4.5 其他資料結構", ["deque、stack、queue、priority_queue 的用途"]), py("5.1.1–5.1.2", ["用 list 當 stack、用 collections.deque 當 queue（list.pop(0) 是 O(n)）"]),
         ca("Minimum Stack / Minimum Queue", ["單調 stack 的典型題型"])]
R[21] = [cph(41, 43, "CPH 4.5 其他資料結構", ["priority_queue 的用途"]), py("11.7", ["heapq：只有最小堆；最大堆用取負數"]),
         bk("visualgo", "VisuAlgo：Heap", ["動畫看 sift-up／sift-down"])]
R[22] = [cph(57, 63, "CPH 第 6 章 貪心演算法", ["找零、排程、任務與期限、最小化總和、霍夫曼；貪心的正確性靠交換論證證明"]),
         cph(58, 59, "CPH 6.2 排程", ["依結束時間排序的區間排程為什麼最優"])]
R[23] = [cph(47, 53, "CPH 5.1–5.4", ["子集與排列的產生、回溯、剪枝"]), cph(54, 55, "CPH 5.5 折半枚舉", ["把 2^n 降成 2^(n/2)"]),
         py("4.8", ["遞迴函式的寫法；預設遞迴深度限制約 1000，要用 `sys.setrecursionlimit` 並注意風險"]),
         bk("pytutor", "Python Tutor 視覺化", ["看遞迴的呼叫堆疊"])]
R[24] = [cph(95, 101, "CPH 10.1–10.4", ["位元表示與運算；用位元表示集合；位元優化"]), ca("Bit manipulation", ["常用技巧"]),
         ca("Enumerating submasks of a bitmask", ["枚舉子遮罩 3^n 的來由"])]
R[25] = [bk("zj", "ZeroJudge 題庫", ["限時練習階段 2 的題型"]), bk("yizhe", "王一哲 APCS 教學網站", ["APCS 題目的解析與寫法對照"])]

# ---------------- 階段 3 ----------------
R[26] = [cph(109, 116, "CPH 第 11 章 圖的基礎", ["圖的術語；鄰接表／鄰接矩陣／邊列表的選擇"]), cph(117, 122, "CPH 第 12 章 圖的遍歷", ["DFS、BFS；連通性、環、二分圖"]),
         ca("Breadth First Search", ["最短步數、多源 BFS"]), ca("Depth First Search", ["遞迴與改成迭代避免爆 stack"]), bk("visualgo", "VisuAlgo：Graph Traversal", ["動畫看 BFS／DFS"])]
R[27] = [cph(145, 146, "CPH 15.2 並查集", ["路徑壓縮與按大小合併；近似 O(α(n))"]), ca("Disjoint Set Union", ["實作與應用（連通元件、環偵測）"])]
R[28] = [cph(149, 150, "CPH 16.1 拓撲排序", ["入度法（Kahn）與 DFS 法"]), cph(151, 153, "CPH 16.2 有向圖上的 DP", ["在 DAG 上依拓撲順序做 DP"]),
         ca("Topological Sorting", ["偵測環與唯一性"])]
R[29] = [cph(123, 132, "CPH 第 13 章 最短路徑", ["Bellman–Ford（負權）、Dijkstra（priority_queue）、Floyd–Warshall（全點對）"]),
         ca("Dijkstra on sparse graphs", ["用 heapq 的實作；過期節點要略過"]), ca("0-1 BFS", ["雙端佇列處理 0／1 權"]),
         ca("Bellman-Ford - finding shortest paths with negative weights", ["負環偵測"])]
R[30] = [cph(142, 144, "CPH 15.1 Kruskal", ["排序邊＋並查集"]), cph(147, 148, "CPH 15.3 Prim", ["與 Dijkstra 的相似與差別"]),
         ca("Minimum Spanning Tree - Kruskal with Disjoint Set Union", ["完整實作"]), ca("Minimum Spanning Tree - Prim's Algorithm", ["稠密圖的選擇"])]
R[31] = [cph(65, 69, "CPH 7.1 找零問題", ["最佳化版與計數版；由遞迴改成 DP 的過程"]), ca("Introduction to Dynamic Programming", ["狀態、轉移、順序的系統化想法"]),
         bk("py_docs", "Python 文件：functools.lru_cache", ["做記憶化時參數必須可雜湊；遞迴深度仍受限制"])]
R[32] = [cph(72, 73, "CPH 7.4 背包問題", ["0-1 背包與一維滾動陣列倒序更新的原因"]), ca("Knapsack Problem", ["0-1、完全背包與恰好裝滿"])]
R[33] = [cph(70, 70, "CPH 7.2 最長上升子序列", ["O(n²) 與 O(n log n) 做法"]), cph(74, 74, "CPH 7.5 編輯距離", ["二維 DP 的狀態與轉移"]),
         ca("Longest increasing subsequence", ["還原答案的做法"])]
R[34] = [cph(71, 71, "CPH 7.3 網格路徑", ["格子上的路徑最佳化與計數"]), cph(75, 76, "CPH 7.6 方塊鋪排計數", ["網格 DP 的進階入門"])]
R[35] = [cph(65, 76, "CPH 第 7 章（區間 DP 的概念沿用 DP 的狀態設計）", ["區間 DP 的轉移是『枚舉分割點』；依區間長度由短到長計算"]),
         ca("Introduction to Dynamic Programming", ["回顧；挑區間型的例題對照"])]
R[36] = [cph(98, 99, "CPH 10.3 用位元表示集合", ["集合與遮罩互相轉換"]), cph(102, 107, "CPH 10.5 位元 DP", ["子集 DP 與排列 DP"]),
         ca("Enumerating submasks of a bitmask", ["子集枚舉的複雜度"])]
R[37] = [cph(197, 206, "CPH 第 21 章 數論", ["質數與因數、模運算、解方程式"]), cph(207, 216, "CPH 第 22 章 組合數學", ["二項式係數、卡特蘭數、容斥原理"]),
         ca("Binary Exponentiation", ["快速冪（Python 內建 `pow(a, b, m)` 可直接用）"]), ca("Modular Inverse", ["模逆元與用法"]), ca("Binomial Coefficients", ["預處理階乘求組合數"])]
R[38] = [bk("cf", "Codeforces 題庫", ["做階段 3 範圍（依 tag：graphs、dp、math）的題"]), bk("atcoder", "AtCoder ABC", ["A–D 題的虛擬賽練習"])]

# ---------------- 階段 4 ----------------
R[39] = [lc("0.4–0.7、0.9、0.11–0.12", ["編譯、連結與組態；打開警告；指定標準 -std=c++17"]),
         lc("1.5、4.3–4.6、4.12", ["cin／cout；整數型別與溢位；固定寬度整數；static_cast"]),
         lc("6.2–6.3、8.8–8.11", ["整數除法對負數的行為（和 Python 不同）；while 與 for 的寫法"]),
         lc("16.1–16.8、5.7", ["vector 與 string 的基本用法（對應 Python 的 list 與 str）"]),
         bk("cppref", "cppreference 的 C++ 語言參考", ["查語法與標準庫用法"])]
R[40] = [cph(35, 45, "CPH 第 4 章 資料結構（4.1–4.5）", ["vector／set／map／deque／priority_queue 與 Python 的對照與複雜度"]), cph(29, 30, "CPH 3.2 C++ 的排序", ["sort 與自訂比較器"]),
         lc("18.2–18.3", ["迭代器與標準演算法"]), bk("cppref", "cppreference：<vector> <algorithm> <set> <map> <queue>", ["查成員函式與複雜度保證"])]
R[41] = [cph(17, 23, "CPH 第 2 章 時間複雜度", ["回顧：C++ 約每秒 10^8 次簡單運算，Python 約 10^7"]), lc("18.4", ["量測自己程式的執行時間"]),
         bk("cppref", "cppreference：<chrono>", ["用 chrono 量測"])]
R[42] = [cph(265, 274, "CPH 第 29 章 幾何", ["複數與點線、多邊形面積、距離函數"]), cph(275, 280, "CPH 第 30 章 掃描線演算法", ["交點、最近點對、凸包"]),
         ca("Basic Geometry", ["叉積與點積；能用整數就不用浮點"]), ca("Check if two segments intersect", ["含共線與端點"]), ca("Convex hull construction", ["Andrew monotone chain"])]
R[43] = [cph(157, 162, "CPH 第 17 章 強連通", ["Kosaraju；2SAT"]), cph(181, 196, "CPH 第 20 章 流與割", ["Ford–Fulkerson；不相交路徑；最大匹配；路徑覆蓋"]),
         ca("Strongly Connected Components and Condensation Graph", ["縮點圖"]), ca("Maximum flow - Dinic's algorithm", ["分層圖與阻塞流"]),
         ca("Kuhn's Algorithm - Maximum Bipartite Matching", ["增廣路徑"])]
R[44] = [cph(243, 250, "CPH 第 26 章 字串演算法", ["Trie；字串雜湊；Z 演算法"]), ca("Prefix function - Knuth-Morris-Pratt", ["字首函數與 KMP"]),
         ca("Z-function", ["與字首函數的關係"]), ca("String Hashing", ["雙模數與衝突機率"]), ca("Aho-Corasick algorithm", ["多模式匹配（選讀）"])]
R[45] = [cph(133, 140, "CPH 第 14 章 樹演算法", ["樹的遍歷、直徑、所有最長路徑、二元樹"]), cph(235, 242, "CPH 第 25 章 博弈論", ["博弈狀態、Nim、Sprague–Grundy"]),
         ca("Sprague-Grundy theorem. Nim", ["SG 函數的計算"])]
R[46] = [cph(86, 94, "CPH 9.2–9.4", ["BIT、線段樹與其他技巧"]), cph(257, 264, "CPH 第 28 章 線段樹再探", ["懶標、動態樹、二維"]),
         ca("Fenwick Tree", ["區間更新與二維版本"]), ca("Segment Tree", ["遞迴與非遞迴寫法、懶標"]), ca("Sparse Table", ["O(1) 區間最值"])]
R[47] = [bk("cpe", "CPE 官網", ["實際報考：把階段 4 的成績記下來"]), cph(15, 16, "CPH 1.6 競賽與資源", ["賽後檢討"])]

# ---------------- 階段 5 ----------------
R[48] = [bk("cpe", "CPE 官網『考生使用手冊』與歷屆題目", ["考場環境、題目語言與計分規則；ICPC 計分（罰時 20 分鐘）"]), cph(15, 16, "CPH 1.6 競賽與資源", ["比賽策略與資源"]),
         bk("cpe", "歷屆整場模擬（本系統『考試』頁）", ["練習讀題順序：先看全部題目、先做最有把握的"])]
R[49] = [bk("cphb", "依自己的弱點回到對應章節（見統計頁或 `cpe weak`）", ["用統計頁的弱點排序決定重讀哪一章；重讀時只做『我之前錯過的類型』"]),
         bk("cpe", "CPE 官網歷屆題目", ["挑弱點對應主題的歷屆題補強"])]
R[50] = [bk("cpe", "CPE 官網答對率低的歷屆題", ["挑答對率最低的題：先分析為什麼低（題意陷阱、複雜實作、冷門演算法）"]),
         bk("cf", "Codeforces 依 tag 與 rating 篩選", ["rating 1600–2000 的題是低答對率題的練習來源"])]
R[51] = [bk("cpe", "CPE 官網歷屆整場", ["每週一次 180 分鐘全真模擬，賽後逐題檢討：錯在讀題、演算法、還是實作"]), cph(15, 16, "CPH 1.6 競賽與資源", ["賽後整理方法"])]
R[52] = [bk("cpe", "CPE 官網報名與考生使用手冊", ["報名時程與考場規則"]), bk("progit", "Pro Git：Git Basics 一章", ["把學習紀錄與作品整理成版本控制的專案"])]

# Python 軌道額外用到的資源（course_data.RES 沒有的）
EXTRA_RES = {"py_docs": ("Python 標準函式庫文件（繁中）", "https://docs.python.org/zh-tw/3/library/index.html")}
