"""C++ 軌道：每個單元要讀哪裡、讀完要抓到什麼重點。

依據（都是實際查過的目錄，不是憑記憶）：
- learncpp.com：課號（例如 8.10）。gen_course_cpp.py 會驗證每個課號都存在。
- Competitive Programmer's Handbook（Antti Laaksonen，cses.fi/book/book.pdf）：書上印的頁碼。gen 會驗證頁碼落在該章範圍內。
- CP-Algorithms：文章標題（和網站目錄逐字相同）。
- 其他書籍（A Tour of C++、Effective Modern C++、C++ Core Guidelines、CS:APP、CLRS…）：只寫章名或條款號；書的版本不同章號會不同，以你手上那版的目錄為準。

格式：(來源, 範圍, [重點…])。learncpp 的範圍是課號清單；CPH 的範圍用 cph() 產生頁碼。
"""

# learncpp.com 各章的課數（供驗證：1.1…1.N）。F、O 是附錄章。
LEARNCPP = {"0": 13, "1": 11, "2": 13, "3": 10, "4": 12, "5": 9, "6": 8, "O": 4, "7": 14, "8": 15, "9": 6, "10": 9, "11": 10, "F": 4,
            "12": 15, "13": 15, "14": 17, "15": 10, "16": 12, "17": 13, "18": 4, "19": 5, "20": 7, "21": 14, "22": 7, "23": 7,
            "24": 9, "25": 11, "26": 6, "27": 10, "28": 7}

# CPH 各章的起訖頁（書上印的頁碼；章尾到下一章前一頁）。
CPH = {1: (3, 16), 2: (17, 24), 3: (25, 34), 4: (35, 46), 5: (47, 56), 6: (57, 64), 7: (65, 76), 8: (77, 82), 9: (83, 94), 10: (95, 108),
       11: (109, 116), 12: (117, 122), 13: (123, 132), 14: (133, 140), 15: (141, 148), 16: (149, 156), 17: (157, 162), 18: (163, 172),
       19: (173, 180), 20: (181, 196), 21: (197, 206), 22: (207, 216), 23: (217, 224), 24: (225, 234), 25: (235, 242), 26: (243, 250),
       27: (251, 256), 28: (257, 264), 29: (265, 274), 30: (275, 280)}

# CP-Algorithms 的文章標題（與網站目錄相同；供驗證）。
CPALGO = {
    "Binary Exponentiation", "Euclidean algorithm for computing the greatest common divisor", "Extended Euclidean Algorithm", "Sieve of Eratosthenes",
    "Linear Sieve", "Primality tests", "Integer factorization", "Euler's totient function", "Modular Inverse", "Chinese Remainder Theorem",
    "Factorial modulo p", "Bit manipulation", "Enumerating submasks of a bitmask", "Fast Fourier transform", "Minimum Stack / Minimum Queue",
    "Sparse Table", "Disjoint Set Union", "Fenwick Tree", "Sqrt Decomposition", "Segment Tree", "Introduction to Dynamic Programming",
    "Knapsack Problem", "Longest increasing subsequence", "Divide and Conquer DP", "Knuth's Optimization", "String Hashing",
    "Prefix function - Knuth-Morris-Pratt", "Z-function", "Suffix Array", "Aho-Corasick algorithm", "Manacher's Algorithm - Finding all sub-palindromes in O(N)",
    "Binomial Coefficients", "Catalan Numbers", "The Inclusion-Exclusion Principle", "Basic Geometry", "Check if two segments intersect",
    "Area of simple polygon", "Convex hull construction", "Convex hull trick and Li Chao tree", "Finding the nearest pair of points",
    "Half-plane intersection - S&I Algorithm in O(N log N)", "Breadth First Search", "Depth First Search", "Finding Bridges in O(N+M)",
    "Finding Articulation Points in O(N+M)", "Strongly Connected Components and Condensation Graph", "Dijkstra on sparse graphs", "Bellman-Ford - finding shortest paths with negative weights",
    "0-1 BFS", "Floyd-Warshall - finding all shortest paths", "Minimum Spanning Tree - Kruskal with Disjoint Set Union", "Minimum Spanning Tree - Prim's Algorithm",
    "Checking a graph for acyclicity and finding a cycle in O(M)", "Lowest Common Ancestor", "Lowest Common Ancestor - Binary Lifting", "Solve RMQ by finding LCA",
    "Maximum flow - Dinic's algorithm", "Maximum flow - Ford-Fulkerson and Edmonds-Karp", "Minimum-cost flow", "Kuhn's Algorithm - Maximum Bipartite Matching",
    "Topological Sorting", "2-SAT", "Heavy-light decomposition", "Centroid decomposition", "Sprague-Grundy theorem. Nim",
}


def cph(a, b, what, focus):
    return ("cphb", f"{what}（書上印的 pp.{a}–{b}）", focus, (a, b))


def lc(lessons, focus):
    return ("learncpp", lessons, focus, None)


def ca(title, focus):
    return ("cpalgo", title, focus, None)


def bk(src, where, focus):
    return (src, where, focus, None)


R = {}

# ---------------- C0 ----------------
R[1] = [lc("0.4–0.7、0.9、0.11–0.12", ["編譯→連結的流程與 Debug／Release 組態的差別", "把警告開到最高（-Wall -Wextra），並指定語言標準（-std=c++17）"]),
        cph(4, 5, "CPH 1.2 輸入輸出", ["`ios::sync_with_stdio(false); cin.tie(nullptr);` 為什麼讓 cin 變快", "什麼時候不能和 scanf 混用"]),
        cph(8, 9, "CPH 1.4 縮短程式碼", ["typedef／using 取別名；巨集的風險（只當作認識，不要濫用）"])]
R[2] = [lc("4.3–4.6、4.8、4.12", ["各整數型別的大小與範圍；用固定寬度整數（int64_t）", "為什麼要避免無號數；浮點數的精度限制"]),
        lc("10.1–10.6", ["隱式轉換、整數提升、窄化轉換；用 static_cast 明確轉型", "算術轉換的規則：int 乘 int 先溢位再轉 long long"]),
        lc("6.2–6.3、6.7", ["整數除法與取餘對負數的行為", "浮點數比較不要用 =="]),
        cph(6, 7, "CPH 1.3 處理數字", ["整數溢位、模運算的寫法、浮點誤差與 eps"])]
R[3] = [lc("1.5、9.5", ["cin 讀取失敗後的狀態與清除；讀到 EOF 的寫法"]),
        lc("28.1–28.5", ["istream 的 >>／getline／ignore 混用；ostream 的格式化（setw、setprecision、fixed）；串流狀態旗標"]),
        cph(4, 5, "CPH 1.2 輸入輸出", ["大量輸入輸出的加速與 `'\\n'` vs endl"])]
R[4] = [lc("4.10、8.1–8.6", ["if／switch 與 fallthrough；常見 if 錯誤（懸空 else、= 與 ==）"]),
        lc("8.8–8.11", ["while／do-while／for；break／continue；迴圈的邊界（off-by-one）"]),
        lc("6.6、6.8", ["條件運算子；邏輯運算的短路求值"]),
        cph(17, 19, "CPH 2.1 計算規則", ["迴圈次數 → 時間複雜度：兩層迴圈就是 n²"])]
R[5] = [lc("2.1–2.7", ["函式的回傳值、參數與區域範圍；前置宣告"]),
        lc("12.3–12.6", ["傳參考與傳 const 參考：避免複製大物件，並說明何時該修改呼叫端"]),
        lc("11.1–11.3", ["函式多載與多載解析的規則"]),
        lc("20.2–20.3", ["stack 與 heap；遞迴的呼叫堆疊與深度限制"])]
R[6] = [lc("16.1–16.8", ["vector 的建構、傳遞與回傳；無號長度與索引問題；range-for"]),
        lc("16.10–16.12", ["size 與 capacity；push_back 的攤銷成本；vector<bool> 的陷阱"]),
        lc("17.1–17.2、17.7–17.9、17.12", ["array 與 C 陣列；陣列退化成指標；多維陣列"]),
        lc("5.7", ["std::string 基本用法"]),
        cph(35, 36, "CPH 4.1 動態陣列", ["vector 與 string 的常用操作與成本"])]
R[7] = [lc("12.7–12.12", ["指標、空指標、const 與指標、傳位址、回傳參考與位址的風險"]),
        lc("19.1–19.2", ["new／delete 與動態陣列：為什麼容易出錯（下一階段用 RAII 取代）"]),
        lc("1.6、3.10", ["未初始化變數與未定義行為；在問題變成 bug 之前找到它（含 sanitizer 的概念）"])]
R[8] = [lc("3.1–3.5", ["除錯流程與策略；用輸出與斷言縮小範圍"]),
        lc("9.1–9.6", ["測試自己的程式；斷言與 static_assert；輸入驗證"])]

# ---------------- C1 ----------------
R[9] = [lc("13.7–13.12", ["struct 的成員、初始化、傳遞與回傳"]),
        lc("14.2–14.10", ["成員函式、const 成員函式、存取控制、封裝的好處、建構子與初始化列表"]),
        lc("14.16、15.1–15.3", ["explicit；this 指標；類別與標頭檔的分工；巢狀型別"]),
        lc("13.6、21.1、21.4、21.7", ["enum class；運算子多載的基本規則；輸出與比較運算子的寫法"]),
        bk("tour", "A Tour of C++：User-Defined Types、Classes 兩章", ["struct／class／enum 的設計取捨"])]
R[10] = [lc("14.14–14.15、15.4", ["複製建構子；複製省略；解構子"]),
         lc("19.3、21.12–21.13", ["用解構子釋放資源；賦值運算子；淺複製與深複製"]),
         bk("cpp_guide", "Core Guidelines R.1、C.20、C.21", ["RAII：資源綁在物件生命週期上；能不寫特殊成員函式就不寫（Rule of 0）；寫了一個就要考慮全部（Rule of 5）"]),
         bk("tour", "A Tour of C++：Essential Operations 一章", ["複製、移動、解構的預設行為與何時自訂"])]
R[11] = [cph(35, 45, "CPH 第 4 章 資料結構（4.1–4.5）", ["vector／set／map／deque／priority_queue 各自的操作與複雜度", "迭代器與區間；multiset；與排序做法的比較（4.6，pp.44–45）"]),
         lc("16.10–16.12", ["容量與擴容；stack 行為（push_back／pop_back）"]),
         bk("tour", "A Tour of C++：Containers 一章", ["各容器的特性與選擇準則"])]
R[12] = [cph(29, 30, "CPH 3.2 C++ 的排序", ["sort 的比較函式、排序 pair／struct、字串排序"]),
         cph(39, 40, "CPH 4.4 迭代器與區間", ["begin／end 半開區間；lower_bound／upper_bound 的回傳；next_permutation"]),
         lc("18.2–18.3", ["迭代器與標準演算法的基本用法"]),
         bk("tour", "A Tour of C++：Algorithms 一章", ["演算法的前置條件與複雜度"])]
R[13] = [lc("20.6–20.7", ["lambda 語法；捕獲（值／參考）與捕獲的生命週期"]),
         lc("20.1", ["函式指標，與 lambda、std::function 的對照"]),
         bk("emcpp", "Effective Modern C++ 條款 31–34", ["避免預設捕獲模式（懸空參考）；初始化捕獲；泛型 lambda；lambda 優於 std::bind"]),
         cph(29, 30, "CPH 3.2 C++ 的排序", ["用 lambda 寫自訂比較器"])]
R[14] = [lc("11.6–11.10", ["函式樣板、實例化、多個型別參數、非型別參數、跨檔案使用"]),
         lc("13.13–13.15、26.1–26.5", ["類別樣板、CTAD、別名樣板、特化與部分特化"]),
         lc("F.1–F.3", ["constexpr／consteval：把計算移到編譯期"]),
         bk("tour", "A Tour of C++：Templates、Concepts and Generic Programming 兩章", ["樣板設計、concepts 如何限制型別並改善錯誤訊息"])]
R[15] = [lc("22.1、22.5–22.7", ["智慧指標的動機；unique_ptr；shared_ptr；循環參考與 weak_ptr"]),
         bk("emcpp", "Effective Modern C++ 條款 18–21", ["unique_ptr 管獨占資源；shared_ptr 管共享資源；weak_ptr 打破循環；優先用 make_unique／make_shared"]),
         bk("cpp_guide", "Core Guidelines R.20、R.21", ["用 unique_ptr／shared_ptr 表示所有權；除非要共享所有權，優先 unique_ptr"]),
         lc("19.1", ["與裸 new／delete 對照"])]
R[16] = [lc("12.2", ["左值與右值（value category）"]),
         lc("22.2–22.4", ["右值參考；移動建構與移動賦值；std::move 只是轉型"]),
         lc("16.5、27.10", ["回傳 vector 與移動；move_if_noexcept"]),
         bk("emcpp", "Effective Modern C++ 條款 23–30", ["std::move 與 std::forward；萬用參考 vs 右值參考；參考折疊；完美轉發失敗的情況"]),
         bk("cpp_guide", "Core Guidelines F.15–F.20", ["參數傳遞：便宜的值傳值、其他傳 const&、會被接管的用 &&；輸出用回傳值"])]
R[17] = [lc("12.15、5.8–5.9", ["std::optional 表達可能沒有值；string_view 不擁有字串，小心懸空"]),
         lc("9.4–9.6", ["錯誤偵測與處理；assert／static_assert"]),
         lc("27.1–27.3、27.8–27.9", ["例外的基本用法；堆疊展開；例外的危險；noexcept"]),
         bk("tour", "A Tour of C++：Error Handling、Utilities 兩章", ["例外 vs 錯誤碼；variant／optional 等工具型別"]),
         bk("cpp_guide", "Core Guidelines E.2、E.6", ["用例外表示函式無法完成工作；用 RAII 防止例外時洩漏"])]
R[18] = [lc("3.1–3.5、9.1–9.6", ["回顧除錯與測試；把所有通過的題用 sanitizer 再跑一次"])]

# ---------------- C2 ----------------
R[19] = [cph(17, 23, "CPH 第 2 章 時間複雜度", ["計算規則、常見複雜度類別、用輸入規模估算可行性（2.3，p.21）", "最大子陣列和的 O(n³)→O(n²)→O(n) 三種做法（2.4，pp.21–23）"]),
         lc("18.4", ["如何量測自己程式的執行時間"])]
R[20] = [cph(25, 33, "CPH 第 3 章 排序", ["排序理論與下界（3.1）；C++ 的 sort（3.2）", "二分搜尋的三種寫法與對答案二分（3.3，pp.31–33）"]),
         cph(84, 85, "CPH 9.1 靜態陣列查詢", ["一維與二維前綴和"])]
R[21] = [cph(77, 82, "CPH 第 8 章 均攤分析", ["雙指標（8.1）；最近較小元素（8.2）；滑動視窗最小值（8.3）", "為什麼每個元素最多進出一次 → O(n)"]),
         cph(41, 43, "CPH 4.5 其他資料結構", ["deque 與 stack／queue／priority_queue"]),
         ca("Minimum Stack / Minimum Queue", ["以單調結構維護最小值的作法與證明"])]
R[22] = [cph(57, 63, "CPH 第 6 章 貪心演算法", ["找零、排程、任務與期限、最小化總和、資料壓縮（霍夫曼）", "貪心的正確性要靠證明（交換論證），不是靠樣例"]),
         cph(41, 43, "CPH 4.5 其他資料結構", ["priority_queue 的用法與比較器方向"])]
R[23] = [cph(47, 55, "CPH 第 5 章 完全搜尋", ["子集與排列的產生（5.1–5.2）；回溯與剪枝（5.3–5.4，pp.50–53）；折半枚舉（5.5）"]),
         cph(95, 101, "CPH 10.1–10.4 位元運算", ["位元表示與運算；用位元表示集合；位元優化"]),
         ca("Bit manipulation", ["常用技巧與內建函式"]), ca("Enumerating submasks of a bitmask", ["枚舉子遮罩 for (s = m; s; s = (s-1) & m) 及其 3^n 的來由"])]
R[24] = [cph(109, 116, "CPH 第 11 章 圖的基礎", ["圖的術語；鄰接表／鄰接矩陣／邊列表的選擇"]),
         cph(117, 122, "CPH 第 12 章 圖的遍歷", ["DFS、BFS 與應用：連通性、環、二分圖"]),
         cph(145, 146, "CPH 15.2 並查集", ["路徑壓縮與按大小合併"]), cph(149, 150, "CPH 16.1 拓撲排序", ["入度法與 DFS 法"]),
         ca("Disjoint Set Union", ["實作細節與複雜度"]), ca("Topological Sorting", ["偵測環與唯一性"])]
R[25] = [cph(123, 132, "CPH 第 13 章 最短路徑", ["Bellman–Ford（負權）、Dijkstra（priority_queue）、Floyd–Warshall（全點對）"]),
         cph(142, 144, "CPH 15.1 Kruskal", ["排序邊＋並查集"]), cph(147, 148, "CPH 15.3 Prim", ["與 Dijkstra 的相似與差別"]),
         ca("Dijkstra on sparse graphs", ["用 set 或 priority_queue 的實作與過期節點"]), ca("0-1 BFS", ["雙端佇列處理 0／1 權"]),
         ca("Minimum Spanning Tree - Kruskal with Disjoint Set Union", ["完整實作"])]
R[26] = [cph(65, 76, "CPH 第 7 章 動態規劃", ["找零（7.1，pp.65–69）；LIS（7.2）；網格路徑（7.3）；背包（7.4，pp.72–73）；編輯距離（7.5）；方塊鋪排計數（7.6）"]),
         ca("Introduction to Dynamic Programming", ["狀態、轉移、順序的系統化想法"]), ca("Knapsack Problem", ["0-1 與完全背包"]),
         ca("Longest increasing subsequence", ["O(n log n) 做法與還原答案"])]
R[27] = [cph(102, 107, "CPH 10.5 位元 DP", ["子集 DP 與排列 DP（TSP）"]),
         cph(135, 138, "CPH 14.2–14.3 樹的直徑與所有最長路徑", ["樹 DP 與換根"]),
         cph(151, 153, "CPH 16.2 有向圖上的 DP", ["拓撲順序下的 DP"]), cph(75, 76, "CPH 7.6 方塊鋪排計數", ["輪廓線 DP 的入門"])]
R[28] = [cph(15, 16, "CPH 1.6 競賽與資源", ["線上賽與題庫的選擇"]),
         ca("Introduction to Dynamic Programming", ["回顧；挑一個最弱的主題重讀"])]

# ---------------- C3 ----------------
R[29] = [cph(86, 94, "CPH 9.2–9.4", ["BIT（pp.86–88）；線段樹（pp.89–92）；其他技巧（pp.93–94）"]),
         cph(257, 264, "CPH 第 28 章 線段樹再探", ["懶標（28.1，pp.258–260）；動態樹（28.2）；二維（28.4）"]),
         ca("Fenwick Tree", ["區間更新與二維版本"]), ca("Segment Tree", ["遞迴與非遞迴寫法、懶標、持久化的概念"])]
R[30] = [cph(84, 85, "CPH 9.1 靜態陣列查詢", ["稀疏表的做法（冪等運算可 O(1)）"]),
         cph(163, 172, "CPH 第 18 章 樹的查詢", ["祖先（18.1）；子樹與路徑（18.2）；LCA（18.3，pp.167–169）；離線演算法（18.4）"]),
         ca("Sparse Table", ["預處理與查詢"]), ca("Lowest Common Ancestor - Binary Lifting", ["倍增表與查詢"]), ca("Solve RMQ by finding LCA", ["兩者的互相轉換"])]
R[31] = [cph(157, 162, "CPH 第 17 章 強連通", ["Kosaraju（17.1）；2SAT（17.2，pp.160–162）"]),
         ca("Strongly Connected Components and Condensation Graph", ["縮點圖"]), ca("Finding Bridges in O(N+M)", ["low-link 的定義與實作"]),
         ca("Finding Articulation Points in O(N+M)", ["割點的條件"]), ca("2-SAT", ["蘊含圖與構造解"])]
R[32] = [cph(181, 196, "CPH 第 20 章 流與割", ["Ford–Fulkerson（20.1，pp.182–185）；不相交路徑（20.2）；最大匹配（20.3，pp.187–189）；路徑覆蓋（20.4，pp.190–196）"]),
         ca("Maximum flow - Dinic's algorithm", ["分層圖與阻塞流；當前弧優化"]), ca("Kuhn's Algorithm - Maximum Bipartite Matching", ["增廣路徑"]),
         ca("Minimum-cost flow", ["連續最短增廣路"]), bk("clrs", "CLRS：Maximum Flow 一章", ["最大流最小割定理的證明"])]
R[33] = [cph(243, 250, "CPH 第 26 章 字串演算法", ["Trie（26.2）；字串雜湊（26.3，pp.245–246）；Z 演算法（26.4，pp.247–250）"]),
         ca("Prefix function - Knuth-Morris-Pratt", ["字首函數與 KMP"]), ca("String Hashing", ["雙模數、隨機底、衝突機率"]),
         ca("Aho-Corasick algorithm", ["多模式匹配的自動機"]), ca("Suffix Array", ["建構與 LCP"]), ca("Manacher's Algorithm - Finding all sub-palindromes in O(N)", ["O(n) 回文"])]
R[34] = [cph(197, 206, "CPH 第 21 章 數論", ["質數與因數（21.1，pp.197–200）；模運算（21.2，pp.201–203）；解方程式（21.3）；其他結果（21.4）"]),
         cph(207, 216, "CPH 第 22 章 組合數學", ["二項式係數（22.1）；卡特蘭數（22.2）；容斥（22.3）；Burnside（22.4）"]),
         cph(220, 221, "CPH 23.2 線性遞迴", ["矩陣快速冪求第 n 項"]),
         ca("Binary Exponentiation", ["快速冪與應用"]), ca("Extended Euclidean Algorithm", ["求逆元與解線性同餘"]), ca("Chinese Remainder Theorem", ["互質與不互質"]),
         ca("Primality tests", ["Miller-Rabin"]), ca("Integer factorization", ["Pollard rho"]), ca("Fast Fourier transform", ["FFT／NTT"])]
R[35] = [cph(265, 274, "CPH 第 29 章 幾何", ["複數與點線（29.1–29.2）；多邊形面積（29.3）；距離函數（29.4）"]),
         cph(275, 280, "CPH 第 30 章 掃描線演算法", ["交點（30.1）；最近點對（30.2）；凸包（30.3）"]),
         ca("Basic Geometry", ["叉積與點積"]), ca("Check if two segments intersect", ["含共線與端點"]), ca("Convex hull construction", ["Andrew monotone chain"]),
         ca("Finding the nearest pair of points", ["分治"]), ca("Half-plane intersection - S&I Algorithm in O(N log N)", ["排序＋雙端佇列"])]
R[36] = [cph(235, 242, "CPH 第 25 章 博弈論", ["博弈狀態（25.1）；Nim（25.2）；Sprague–Grundy 定理（25.3，pp.238–242）"]),
         cph(220, 221, "CPH 23.2 線性遞迴", ["矩陣快速冪優化 DP"]),
         ca("Divide and Conquer DP", ["適用條件與複雜度"]), ca("Knuth's Optimization", ["四邊形不等式"]),
         ca("Convex hull trick and Li Chao tree", ["斜率優化與 Li Chao 樹"]), ca("Sprague-Grundy theorem. Nim", ["SG 函數的計算"])]
R[37] = [cph(251, 256, "CPH 第 27 章 平方根演算法", ["合併演算法（27.1）；整數分拆（27.2）；莫隊（27.3，pp.255–256）"]),
         cph(170, 172, "CPH 18.4 離線演算法", ["離線處理查詢的想法"]),
         ca("Heavy-light decomposition", ["輕重鏈剖分與路徑查詢"]), ca("Centroid decomposition", ["點分治與路徑統計"]), ca("Sqrt Decomposition", ["分塊與莫隊"])]
R[38] = [cph(15, 16, "CPH 1.6 競賽與資源", ["選擇虛擬競賽的賽事與賽後整理方法"])]

# ---------------- C4 ----------------
R[39] = [bk("csapp", "CS:APP：Optimizing Program Performance 一章", ["編譯器能做與不能做的最佳化；消除迴圈低效率、減少程序呼叫、指令層級平行；剖析與找瓶頸"]),
         bk("godbolt", "Compiler Explorer 練習", ["同一段程式在 -O0 與 -O2 的組語；看迴圈是否被向量化"]),
         lc("0.9、18.4", ["Debug／Release 組態；計時的基本方法"]),
         bk("gbench", "Google Benchmark 使用指南", ["寫微基準；DoNotOptimize；穩定量測"])]
R[40] = [bk("csapp", "CS:APP：The Memory Hierarchy 一章（Locality、Cache Memories、Writing Cache-Friendly Code、The Impact of Caches）", ["時間與空間局部性；快取行與命中率；列優先走訪；分塊提高局部性"]),
         bk("godbolt", "Compiler Explorer／perf 練習", ["以 perf 觀察 cache miss"])]
R[41] = [lc("O.1–O.4", ["bitset、位元運算子、位元遮罩的使用"]),
         lc("F.1–F.3", ["constexpr／consteval 在編譯期產生查表"]),
         cph(100, 101, "CPH 10.4 位元優化", ["用位元平行加速 DP"]),
         ca("Bit manipulation", ["內建函式與技巧"]),
         bk("csapp", "CS:APP：Representing and Manipulating Information 一章", ["整數表示與位元層級運算、溢位"])]
R[42] = [bk("tour", "A Tour of C++：Concurrency 一章", ["thread、mutex、condition_variable、future、atomic 的基本用法"]),
         bk("csapp", "CS:APP：Concurrent Programming 一章", ["競爭、死結、同步；執行緒安全"]),
         bk("cppref", "cppreference：<thread> <mutex> <atomic> <execution>", ["記憶體順序；平行演算法的執行策略"])]
R[43] = [bk("cmake", "CMake 官方教學（Tutorial）", ["target、link、子目錄、測試（CTest）、Release／Debug"]),
         bk("gtest", "GoogleTest Primer", ["TEST、斷言、fixture、參數化測試"]),
         lc("0.9–0.12、9.1–9.6、3.10", ["組態與警告；測試與斷言；找問題的工具"]),
         bk("progit", "Pro Git：Git Basics、Git Branching 兩章", ["提交、分支、合併；工作流程"])]
R[44] = [bk("cpp_guide", "Core Guidelines 的 Per（效能）與 CP（並行）兩節", ["先量測再最佳化；不要在沒有證據時犧牲可讀性"])]

# ---------------- C5 ----------------
R[45] = [bk("cpp_guide", "Core Guidelines I.1–I.4", ["介面明確、避免非 const 全域、避免單例、介面強型別"]),
         bk("cpp_guide", "Core Guidelines 的 T（樣板）一節", ["樣板介面與 concepts 的設計準則"]),
         ca("Disjoint Set Union", ["作為元件實作的參考"]), ca("Segment Tree", ["作為元件實作的參考"])]
R[46] = [bk("ir_book", "Introduction to Information Retrieval：Boolean retrieval、The term vocabulary and postings lists、Index compression、Scoring 各章", ["倒排索引與詞彙；postings 的交集；差分＋變長編碼壓縮；tf-idf 評分"]),
         ca("Aho-Corasick algorithm", ["多模式匹配（選用於補全）"])]
R[47] = [ca("Dijkstra on sparse graphs", ["實作基準"]),
         bk("redblob", "Red Blob Games：Introduction to A*", ["啟發函式、可採納性、與 Dijkstra 的差別"]),
         bk("clrs", "CLRS：Single-Source Shortest Paths 一章", ["鬆弛與最短路徑性質"]),
         bk("ch_paper", "Geisberger 等人，Contraction Hierarchies（WEA 2008）", ["節點排序與捷徑；查詢為什麼快"])]
R[48] = [bk("clrs", "CLRS：Greedy Algorithms 一章（霍夫曼編碼）", ["最優前綴碼與貪心證明"]),
         bk("deflate", "RFC 1951（DEFLATE）", ["LZ77 加霍夫曼的實際格式"]),
         bk("mahoney", "Data Compression Explained（Matt Mahoney）", ["各類壓縮方法的概念與比較"]),
         bk("sa_paper", "Kirkpatrick 等人，Optimization by Simulated Annealing（Science 220，1983）", ["退火的接受準則與降溫排程"])]
R[49] = [bk("ctci", "Cracking the Coding Interview：面試流程與解題框架部分", ["澄清題意、舉例、暴力解、優化、測試的節奏"]),
         bk("ddia", "Designing Data-Intensive Applications：Partitioning 一章", ["雜湊分區與一致性雜湊的取捨"]),
         bk("cpp_guide", "Core Guidelines C（類別）一節", ["虛函式與 vtable 的設計準則；面試常考的 C++ 語言細節"])]
R[50] = [bk("cpe", "CPE 官網歷屆題目", ["做一次完整的限時全真練習"]),
         bk("cf", "Codeforces 虛擬賽", ["賽後整理缺的知識與模板"])]

# 新增的資源（course_cpp_data.RES 沒有的）
EXTRA_RES = {
    "gbench": ("Google Benchmark（微基準框架）", "https://github.com/google/benchmark"),
    "ir_book": ("Introduction to Information Retrieval（免費線上版）", "https://nlp.stanford.edu/IR-book/"),
    "redblob": ("Red Blob Games：Introduction to A*", "https://www.redblobgames.com/pathfinding/a-star/introduction.html"),
    "ch_paper": ("Contraction Hierarchies（Geisberger 等，WEA 2008）", "https://dblp.org/search?q=Contraction%20Hierarchies%20Geisberger"),
    "deflate": ("RFC 1951：DEFLATE 壓縮資料格式", "https://www.rfc-editor.org/rfc/rfc1951"),
    "mahoney": ("Data Compression Explained（Matt Mahoney）", "https://mattmahoney.net/dc/dce.html"),
    "sa_paper": ("Optimization by Simulated Annealing（Kirkpatrick 等，Science 1983）", "https://www.science.org/doi/10.1126/science.220.4598.671"),
    "ctci": ("Cracking the Coding Interview", "https://www.crackingthecodinginterview.com/"),
    "ddia": ("Designing Data-Intensive Applications", "https://dataintensive.net/"),
}
