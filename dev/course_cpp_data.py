"""C++ 軌道：從零基礎到演算法工程師。6 個階段、50 個單元。

和 Python 軌道（course_data.py）獨立：Python 軌道的終點是 CPE 一次 6 題；這條軌道的終點是『能在工作上寫出正確、快、可維護的 C++ 演算法程式碼』。
- drills：現有題庫（用 C++ 解，由 g++ 判題）。planned：還沒有的題目（要新增，標明主題），build：不能自動判的實作作業（有驗收標準）。
- gate：type=set 用題庫題目計時檢核；type=project 是作品驗收（criteria 逐條檢查）。
"""

RES = {
    "learncpp": ("learncpp.com（C++ 入門教學，有繁中社群翻譯）", "https://www.learncpp.com/"),
    "cppref": ("cppreference（標準庫查詢）", "https://en.cppreference.com/"),
    "cpp_guide": ("C++ Core Guidelines（Stroustrup、Sutter）", "https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines"),
    "tour": ("A Tour of C++（Bjarne Stroustrup）", "https://www.stroustrup.com/tour3.html"),
    "emcpp": ("Effective Modern C++（Scott Meyers）", "https://www.oreilly.com/library/view/effective-modern-c/9781491908419/"),
    "cphb": ("Competitive Programmer's Handbook（免費 PDF）", "https://cses.fi/book/book.pdf"),
    "cpalgo": ("CP-Algorithms（演算法百科）", "https://cp-algorithms.com/"),
    "cses": ("CSES Problem Set（分類清楚、標準輸入輸出）", "https://cses.fi/problemset/"),
    "cf": ("Codeforces 題庫（可依 tag／rating 篩選）", "https://codeforces.com/problemset"),
    "atcoder": ("AtCoder（ABC／ARC）", "https://atcoder.jp/"),
    "visualgo": ("VisuAlgo（演算法動畫）", "https://visualgo.net/"),
    "clrs": ("Introduction to Algorithms（CLRS）", "https://mitpress.mit.edu/9780262046305/introduction-to-algorithms/"),
    "csapp": ("Computer Systems: A Programmer's Perspective（記憶體階層、連結）", "https://csapp.cs.cmu.edu/"),
    "godbolt": ("Compiler Explorer（看編譯器產生的組語）", "https://godbolt.org/"),
    "gtest": ("GoogleTest／Catch2（單元測試框架）", "https://google.github.io/googletest/"),
    "cmake": ("Modern CMake 入門（官方教學）", "https://cmake.org/cmake/help/latest/guide/tutorial/index.html"),
    "cpe": ("CPE 官網（歷屆題目與答對率）", "https://cpe.mcu.edu.tw/"),
    "progit": ("Pro Git（繁中）", "https://git-scm.com/book/zh-tw/v2"),
}

STAGES = [
    ("C0", "零基礎與工具鏈", "能獨立編譯、執行、除錯一支幾百行的 C++ 程式，讀寫輸入輸出，不被未定義行為嚇到。"),
    ("C1", "現代 C++ 核心", "懂物件生命週期（RAII）、STL、樣板、移動語意；寫出不漏記憶體、不複製多餘資料的程式。"),
    ("C2", "競程與基礎演算法", "用 C++ 做完 CPE 等級（含四顆星）的題目：排序、圖、DP、貪心、位元。"),
    ("C3", "進階資料結構與演算法", "線段樹、LCA、強連通、網路流、字串演算法、數論、幾何、DP 優化、樹分治。"),
    ("C4", "效能工程與系統能力", "會量測、剖析、改資料佈局、用平行與位元技巧；用 CMake、單元測試、sanitizer 與 CI 維持品質。"),
    ("C5", "演算法工程師作品與面試", "做出有測試、有基準、有文件的演算法函式庫與三個專題；能做系統設計與面試。"),
]

RHYTHM = [
    ("第 1 天", "新概念", "讀教材，在 Compiler Explorer 或本機做小實驗；每個概念都寫一個『會出錯的最小範例』並預測結果。"),
    ("第 2 天", "概念練習", "做本單元前半的 drills（用 C++：`cpe new <題號> --lang cpp`）。卡住才 `cpe hint`。"),
    ("第 3 天", "鞏固", "做後半的 drills；每題通過後問：複雜度？有沒有 UB？用 `-fsanitize=address,undefined` 再跑一次。"),
    ("第 4 天", "實作", "做本單元的 build 作業（不能自動判的實作），照驗收標準自己逐條檢查。"),
    ("第 5 天", "重寫日", "把本週用過提示的題目關掉資料從空白檔重寫；C++ 加做『改用另一種容器或寫法再通過一次』。"),
    ("第 6 天", "檢核", "計時檢核；單元最後一週做 `cpe gate`（作品單元是逐條驗收）。"),
    ("第 7 天", "休息", "不寫程式。"),
]

UNITS = []


def U(stage, weeks, title, goal, learn, drills=(), planned=(), build=(), res=(), pitfalls=(), check=(), gate=None, read=()):
    UNITS.append(dict(stage=stage, weeks=weeks, title=title, goal=goal, learn=list(learn), drills=list(drills),
                      planned=[dict(id=p[0], title=p[1], topic=p[2]) for p in planned], build=list(build),
                      resources=list(res), pitfalls=list(pitfalls), check=list(check), gate=gate, lang="cpp", read=list(read)))


def G(problems, minutes, need):
    return {"type": "set", "problems": list(problems), "minutes": minutes, "need": need, "lang": "cpp"}


def P(criteria, days=7):
    return {"type": "project", "criteria": list(criteria), "days": days}


# ============================ C0：零基礎與工具鏈（第 1–10 週）============================
U(0, 1, "工具鏈與第一個程式", "能安裝編譯器，編譯並執行程式，看懂編譯錯誤與警告。",
  ["安裝 g++（Linux／macOS 內建或用套件管理員；Windows 用 MSYS2 或 WSL）；`g++ -std=c++17 -O2 -Wall -Wextra a.cpp -o a`",
   "編譯的四步：前處理、編譯、組譯、連結；`#include` 只是把檔案貼進來；`main` 的回傳值",
   "讀錯誤訊息：從第一個 error 開始修（後面常是連鎖反應）；warning 也要處理",
   "用 Compiler Explorer 看同一段程式在 -O0 與 -O2 的差別（只要知道『編譯器會大幅改寫程式』）",
   "競程模板：`ios::sync_with_stdio(false); cin.tie(nullptr);` 為什麼能加速、什麼時候不能和 scanf 混用"],
  drills=["d001", "d003"],
  build=["寫 hello.cpp，故意製造 5 種錯誤（少分號、型別不符、未宣告、少 include、連結不到函式）並記下各自的錯誤訊息長什麼樣"],
  res=["learncpp", "cppref", "godbolt"],
  pitfalls=["沒開 -Wall 就看不到很多真正的 bug", "Windows 的 `a.exe` 與 Linux 的 `./a` 路徑寫法不同"],
  check=["`#include <bits/stdc++.h>` 是標準嗎？在哪些編譯器不能用？", "-O2 會不會改變程式的『正確結果』？（在沒有 UB 的前提下）"],
  gate=G(["d002"], 20, 1), read=["learncpp 第 0 章"])

U(0, 1, "型別、變數與運算", "懂整數大小與溢位、整數除法、浮點誤差、型別轉換。",
  ["int／long long／unsigned／char／bool／double 的範圍；`<cstdint>` 的 int32_t、int64_t；`sizeof`",
   "有號整數溢位是未定義行為（UB），不是『繞回去』；無號才是模運算",
   "整數除法與取餘對負數向零取整：`-7 / 2 == -3`、`-7 % 3 == -1`（Python 不同）",
   "隱式轉換陷阱：int 乘 int 先溢位再轉 long long；`1LL * a * b`；有號與無號比較",
   "const、constexpr、auto；浮點數不要用 == 比較"],
  drills=["d004", "d096", "d097", "d027", "d037"],
  build=["寫一個程式印出各型別的 sizeof 與極值（numeric_limits），再用 -fsanitize=undefined 跑一個整數溢位範例，看它怎麼報告"],
  res=["learncpp", "cppref"],
  pitfalls=["`int` 乘法前沒轉 long long", "`abs` 在 <cstdlib> 與 <cmath> 有不同多載（int 與 double）"],
  check=["`INT_MAX + 1` 的結果是什麼？為什麼這個問題不能用『繞回去』回答？", "`(unsigned)-1 > 0` 是 true 還是 false？"],
  gate=G(["d098"], 20, 1), read=["learncpp 第 4 章"])

U(0, 1, "輸入輸出與格式", "穩定處理各種輸入格式（多組、EOF、含空白的整行），並精確控制輸出格式。",
  ["`cin >> x` 的回傳值與 EOF：`while (cin >> x)`；`getline` 與 `cin >>` 混用要吃掉換行（`cin.ignore()`）",
   "`cout << fixed << setprecision(2)`；`<iomanip>` 的 setw／setfill；`printf` 的格式字串",
   "大量輸出用 `'\\n'` 不用 `endl`（endl 會 flush）",
   "scanf／printf 與 cin／cout 的速度與混用規則"],
  drills=["d002", "d031", "d032", "d033", "d034", "d035"],
  res=["learncpp", "cppref"],
  pitfalls=["`cin >> n` 之後直接 `getline` 讀到空字串", "浮點輸出四捨五入與 `-0.00`"],
  check=["讀到 EOF 的三種寫法各有什麼差別？", "`cout << 0.1 + 0.2` 與 `printf(\"%.17g\")` 各印什麼？"],
  gate=G(["d111"], 25, 1), read=["learncpp 第 28 章（輸入輸出）"])

U(0, 2, "條件與迴圈", "熟練 if／switch／for／while／do-while，能把需求翻成迴圈與條件。",
  ["if／else if／switch（要寫 break）；三元運算子；邏輯運算的短路求值",
   "for／range-for／while；`break`／`continue`；巢狀迴圈與複雜度（兩層就是 n²）",
   "off-by-one：半開區間 [l, r) 的好處；迴圈變數型別（`size_t` 倒數迴圈會無窮）",
   "把需求拆成『狀態＋轉移』再寫迴圈；先手算小例子"],
  drills=["d005", "d006", "d007", "d008", "d009", "d010", "d012", "d040", "d099", "d100", "d101", "d107", "d122", "d123"],
  res=["learncpp"],
  pitfalls=["`for (size_t i = n - 1; i >= 0; --i)` 永遠成立", "switch 忘了 break 的 fall-through"],
  check=["`for (int i = 0; i < n; i++) for (int j = i; j < n; j++)` 執行幾次內層？", "短路求值能避免哪種錯誤？"],
  gate=G(["d011", "d024"], 40, 2), read=["learncpp 第 5–8 章"])

U(0, 1, "函式、傳值與傳參考", "會設計函式介面，懂傳值、傳參考、傳 const 參考的差別。",
  ["函式宣告與定義、前置宣告；多載；預設引數",
   "傳值會複製；`T&` 可修改呼叫端；`const T&` 避免複製又不修改（大物件用這個）",
   "回傳值：區域變數不要回傳參考或指標；現代編譯器會省略複製",
   "遞迴：基底條件、遞迴深度與 stack 溢位（約幾萬層就可能炸）"],
  drills=["d021", "d022", "d023", "d025", "d106", "d117"],
  res=["learncpp", "cppref"],
  pitfalls=["回傳區域變數的參考（懸空參考）", "遞迴沒有基底條件或深度太大"],
  check=["`void f(vector<int> v)` 與 `void f(const vector<int>& v)` 的成本差多少？", "什麼情況下遞迴會 stack overflow？怎麼改成迭代？"],
  gate=G(["d118"], 30, 1), read=["learncpp 第 10–11 章"])

U(0, 2, "陣列、vector 與 string", "熟練一維與二維資料，知道越界的後果。",
  ["C 陣列（大小固定、不檢查越界、傳進函式會退化成指標）；`std::array`；`vector` 的 push_back／resize／reserve",
   "`vector<vector<int>>` 與一維壓平；`string` 的 substr／find／拼接與效能（`+=` 才是攤銷 O(1)）",
   "越界存取是 UB：可能剛好沒事、可能當掉、可能默默改到別的變數；用 `.at()` 或 `-D_GLIBCXX_DEBUG` 抓",
   "大陣列放全域或 vector，不要放區域（stack 只有幾 MB）"],
  drills=["d013", "d014", "d015", "d016", "d017", "d026", "d108", "d109", "d110", "d115", "d043", "d036", "d113", "d114"],
  build=["寫一個故意越界的程式，用 -fsanitize=address 看報告；再改用 vector.at() 看例外；說明三種行為的差別"],
  res=["learncpp", "cppref"],
  pitfalls=["`int a[1000000]` 放在 main 裡 → stack 溢位", "`vector<bool>` 不是真正的 bool 容器"],
  check=["`v.size() - 1` 在 v 為空時是多少？", "`string s; s = s + 'a'` 與 `s += 'a'` 效能一樣嗎？"],
  gate=G(["d103"], 30, 1), read=["learncpp 第 16–17 章"])

U(0, 1, "指標、參考與記憶體模型", "懂 stack 與 heap、指標與參考、未定義行為，並會用工具抓錯。",
  ["stack（自動變數）、heap（new／malloc）、靜態區；位址與 `&`、`*`；指標算術與陣列的關係",
   "參考是別名、不可為空、不可重新綁定；指標可為空（`nullptr`）、可重新指向",
   "常見 UB：越界、懸空指標、未初始化變數、有號溢位、重複釋放；sanitizer：ASan、UBSan",
   "為什麼現代 C++ 少用裸 new／delete（下一階段用 RAII 取代）",
   "二維陣列與邊界：網格模擬題是最常見的越界（UB）來源，本單元的題目都用它來練『索引一定要先檢查』"],
  drills=["d041", "d042", "d119", "d120", "d121"],
  build=["寫 4 個各含一種 UB 的程式（越界、use-after-free、未初始化、有號溢位），各用對應 sanitizer 抓出，並記錄報告怎麼看"],
  res=["learncpp", "cpp_guide"],
  pitfalls=["回傳指向區域變數的指標", "`delete` 與 `delete[]` 混用"],
  check=["指標與參考的三個差別？", "為什麼『程式沒當掉』不代表『程式正確』？"],
  gate=G(["d122"], 30, 1), read=["learncpp 第 12 章"])

U(0, 1, "階段 C0 驗收週", "用 C++ 在時限內解出 Python 軌道階段 0–1 等級的題目，並通過 sanitizer。",
  ["複習本階段薄弱單元；把所有通過的題用 `-O2 -Wall -Wextra -fsanitize=address,undefined` 再跑一次，修掉所有警告"],
  res=["learncpp"], check=["我最常犯的三種 C++ 錯誤是什麼？有什麼檢查清單避免？"],
  gate=G(["e101", "e102", "d039"], 90, 2))

# ============================ C1：現代 C++ 核心（第 11–23 週）============================
U(1, 1, "struct、class 與封裝", "會用類別建模，區分資料與行為，控制存取。",
  ["struct 與 class（預設存取不同）；成員函式、`const` 成員函式；建構子與初始化列表",
   "封裝：不變量（invariant）由類別維護；`private` 資料＋公開介面",
   "運算子多載（`operator<`、`operator==`、`operator<<`）；`friend` 的用途與濫用",
   "`enum class`；`using` 型別別名；命名空間；標頭檔與 include guard／`#pragma once`"],
  drills=["d030", "d044", "d045"],
  build=["把 d044 的『運算式解析』寫成 Token、Lexer、Parser 三個類別，每個類別至少 3 個單元測試（先用 assert，之後換框架）"],
  res=["learncpp", "tour", "cpp_guide"],
  pitfalls=["在標頭檔裡 `using namespace std;`", "沒有初始化的成員變數"],
  check=["struct 與 class 在 C++ 差在哪？", "什麼是類別的不變量？舉一個例子。"],
  gate=G(["d029"], 40, 1), read=["learncpp 第 13–14 章"])

U(1, 2, "RAII、生命週期與 Rule of 0／3／5", "不用裸 new／delete 管理資源；懂物件何時建構、複製、銷毀。",
  ["建構與解構的順序；區域物件離開作用域就銷毀——這就是 RAII：資源綁在物件生命週期上（記憶體、檔案、鎖）",
   "複製建構、複製賦值、解構：預設行為與自己寫的時機；Rule of 3；有移動語意後是 Rule of 5；能不寫就不寫是 Rule of 0",
   "淺複製與深複製；雙重釋放的成因",
   "例外安全：建構失敗會發生什麼；`noexcept`",
   "練習方式：本單元的 stack 類題目（d124、d135）請先自己寫一個 RAII 的 Stack 類別（內含 vector 或自管陣列），再用它解題"],
  drills=["d124", "d135"],
  build=["實作 `class IntBuffer`（自己管理一塊 new[] 記憶體）：完整 Rule of 5，用 ASan 與 valgrind 驗證無洩漏、無重複釋放；再改成 `std::vector<int>` 版本（Rule of 0）比較程式碼量"],
  res=["learncpp", "tour", "cpp_guide"],
  pitfalls=["自己寫了解構子卻沒處理複製（Rule of 3 違反）", "解構子丟例外"],
  check=["什麼時候編譯器會自動產生複製建構子？什麼時候不會？", "RAII 怎麼讓『提早 return 或丟例外時也不漏資源』？"],
  gate=P(["IntBuffer 通過 ASan、UBSan、valgrind 無任何報告", "含 10 個以上測試：複製、賦值、自我賦值、空緩衝、大緩衝", "能口頭說明每個特殊成員函式在哪些情況被呼叫"], 5),
  read=["learncpp 第 15、21–22 章"])

U(1, 2, "STL 容器全覽與複雜度", "能依需求選容器，並說出每個操作的複雜度。",
  ["序列容器：vector（連續、攤銷 O(1) 尾端新增）、deque、list、array；關聯容器：set／map（常見實作是紅黑樹，O(log n)）、unordered_set／map（雜湊，平均 O(1)、最差 O(n)）",
   "multiset／multimap；`priority_queue`（預設最大堆）；`stack`／`queue` 是配接器",
   "迭代器失效規則：vector 擴容後舊迭代器全失效；在迴圈中 erase 的正確寫法",
   "自訂雜湊與比較函式；unordered_map 被惡意資料打爆（競賽中用自訂 hash）",
   "選擇準則：預設用 vector；要排序且動態用 set／map；要最小／最大用 priority_queue"],
  drills=["d018", "d019", "d020", "d028", "d103", "d104", "d105", "d029", "d102", "d112", "d039"],
  planned=[("c101", "迭代器失效偵測", "寫出會讓迭代器失效的操作序列，判斷輸出（要求用 vector／list／map 各一）")],
  build=["對 vector／list／set／unordered_set 各測 10^6 次插入、查詢、刪除，畫出耗時表，解釋為什麼 list 常常輸給 vector"],
  res=["cppref", "learncpp", "tour"],
  pitfalls=["在 range-for 中修改正在迭代的容器", "unordered_map 用 `operator[]` 查詢會偷偷插入"],
  check=["set 與 unordered_set 什麼時候選哪個？", "`map<string,int> m; m[\"a\"]` 查詢不存在的鍵會發生什麼？"],
  gate=G(["d127"], 45, 1), read=["cppreference：<vector> <map> <set> <unordered_map> <queue>"])

U(1, 1, "迭代器與 <algorithm>", "用標準演算法取代手寫迴圈，懂迭代器類別與前置條件。",
  ["迭代器類別：input／forward／bidirectional／random access／contiguous；`begin`／`end` 半開區間",
   "常用演算法：sort、stable_sort、nth_element、lower_bound／upper_bound、binary_search、unique、reverse、rotate、accumulate、iota、partial_sum、min_element、next_permutation",
   "排序需要『嚴格弱序』：比較函式 `<=` 會造成未定義行為甚至當掉",
   "erase–remove 慣用法與 C++20 的 `std::erase`"],
  drills=["d049", "d125", "d126", "d047"],
  build=["不寫任何 for／while，只用 <algorithm> 與 <numeric> 解 d125（排序統計），並說明每個演算法的複雜度"],
  res=["cppref", "tour"],
  pitfalls=["比較函式不滿足嚴格弱序（`<=`）→ 可能 crash", "`lower_bound` 對沒排序的區間使用"],
  check=["`std::sort` 的比較函式必須滿足什麼性質？", "`unique` 為什麼要搭配 `erase`？"],
  gate=G(["d048"], 30, 1), read=["cppreference：<algorithm> <numeric>"])

U(1, 1, "Lambda 與函式物件", "會用 lambda 寫自訂比較、轉換與回呼，懂捕獲的生命週期風險。",
  ["lambda 語法 `[捕獲](參數){...}`；值捕獲 vs 參考捕獲；`mutable`；泛型 lambda（`auto` 參數）",
   "`std::function` 的成本（型別擦除、可能配置記憶體）與樣板參數傳入 lambda 的零成本",
   "自訂比較器：傳給 sort／priority_queue／set；`greater<>` 與 lambda 的寫法差別",
   "懸空捕獲：把參考捕獲的 lambda 存起來、離開作用域後再用"],
  drills=["d055", "d140"],
  build=["用 lambda 寫 5 種排序（多鍵、降序、依自訂函式值、穩定、依字串長度再字典序），並各說明比較函式為何是嚴格弱序"],
  res=["cppref", "learncpp", "tour"],
  pitfalls=["參考捕獲區域變數後把 lambda 回傳", "priority_queue 的比較器方向與 sort 相反"],
  check=["`priority_queue<int, vector<int>, greater<int>>` 是最小堆還是最大堆？", "什麼時候該用 std::function、什麼時候用 template 參數？"],
  gate=G(["d138"], 30, 1), read=["learncpp 第 20 章"])

U(1, 2, "樣板與泛型程式設計", "寫得出泛型容器與演算法，會讀樣板錯誤，用 concepts 限制型別。",
  ["函式樣板與類別樣板；型別推導；非型別樣板參數（`template<int N>`）",
   "樣板只在使用時才實例化，所以錯誤訊息很長——從第一個 `required from` 讀起",
   "特化與 `if constexpr`；變參樣板（`...`）入門",
   "C++20 concepts：`template<std::integral T>`、`requires`，讓錯誤訊息變短、介面更清楚",
   "標頭檔：樣板要放在標頭（定義可見）"],
  planned=[("c102", "泛型 ModInt", "template<int MOD> 的模整數類別，支援 + - * / 與快速冪，對 5 個模數通過同一組測試"),
           ("c103", "泛型 Matrix", "template<class T, size_t N> 的方陣乘法與快速冪（用於遞迴式與圖的路徑計數）")],
  build=["實作 `template<class T> class Fenwick`（支援任意可加型別），並用 concepts 限制 T 必須有 `operator+`；再實作 ModInt，把 d177 用它重寫"],
  res=["cppref", "tour", "learncpp"],
  pitfalls=["在 .cpp 裡放樣板定義導致連結錯誤", "樣板推導失敗卻被錯誤訊息淹沒"],
  check=["為什麼樣板函式通常放在標頭檔？", "concepts 解決了 SFINAE 的哪些問題？"],
  gate=P(["ModInt：支援 + - * /（逆元）、pow、輸入輸出運算子；對模數 998244353 與 1e9+7 通過同一組測試", "Fenwick<T>：用 concepts 限制型別，含 20 個以上測試與複雜度說明", "錯誤使用型別時，編譯錯誤訊息停在 requires 那一行（附截圖或文字）"], 7),
  read=["learncpp 第 11、26 章；A Tour of C++ 第 7 章"])

U(1, 1, "智慧指標與所有權", "以 unique_ptr／shared_ptr 表達所有權，避免洩漏與循環參考。",
  ["`unique_ptr`（獨占、零成本）、`shared_ptr`（計數、有成本）、`weak_ptr`（打破循環）；`make_unique`／`make_shared`",
   "所有權語意：函式參數用裸指標／參考表示『借用』，用 unique_ptr 表示『接管』",
   "什麼時候不需要指標：多數情況直接用值或 vector",
   "用智慧指標實作鏈結串列、二元樹，並比較與 vector 版本的快取表現"],
  planned=[("c104", "樹的節點釋放", "用 unique_ptr 建 10^6 個節點的樹，確認解構不會遞迴爆 stack（需自行改成迭代釋放）")],
  build=["用 unique_ptr 實作二元搜尋樹（插入、查詢、刪除、中序走訪）；用 ASan 確認無洩漏；再說明為什麼 10^6 節點的退化樹在解構時會 stack overflow、怎麼解"],
  res=["learncpp", "cpp_guide", "tour"],
  pitfalls=["兩個 shared_ptr 互相持有造成洩漏", "用同一個裸指標建立兩個 shared_ptr"],
  check=["什麼時候用 unique_ptr、什麼時候用 shared_ptr？", "為什麼 `make_shared` 比 `shared_ptr<T>(new T)` 好？"],
  gate=G(["d149"], 30, 1), read=["learncpp 第 22 章"])

U(1, 1, "移動語意與完美轉發", "懂左值／右值、移動與複製的差別，會寫移動建構。",
  ["左值與右值；右值參考 `T&&`；`std::move` 只是轉型（不搬任何東西）；被移動後物件處於『有效但未指定』狀態",
   "移動建構／移動賦值與 noexcept：vector 擴容時用 `std::move_if_noexcept`——移動建構子不是 noexcept 而且型別可以複製時，會改用複製（為了保持強例外保證）",
   "回傳值最佳化（RVO）與強制省略複製（C++17）：多數時候不要 `return std::move(x)`",
   "轉發參考與 `std::forward`；`emplace_back` 與 `push_back` 的差別"],
  planned=[("c105", "計數複製與移動", "用帶計數器的類別，預測各種操作（push_back、emplace_back、sort、swap）會觸發幾次複製與移動")],
  build=["對 IntBuffer 加上移動操作，量測 vector<IntBuffer> 擴容時複製與移動各發生幾次，解釋 noexcept 的影響"],
  res=["emcpp", "cppref", "learncpp"],
  pitfalls=["對 const 物件 std::move 實際上還是複製", "使用被移動後的物件"],
  check=["`std::move(x)` 之後 x 還能用嗎？能做什麼？", "為什麼移動建構子要標 noexcept？"],
  gate=G(["d136"], 30, 1), read=["learncpp 第 22 章；Effective Modern C++ 條款 23–30"])

U(1, 1, "現代語法與錯誤處理", "善用 optional、variant、string_view、結構化綁定與例外。",
  ["`std::optional`（可能沒有值）、`std::variant`＋`std::visit`（和型別）、`std::string_view`（不擁有的字串視圖，小心懸空）",
   "結構化綁定 `auto [a, b] = ...`；`if` 初始化；`std::span`；C++20 ranges 入門",
   "例外 vs 錯誤碼 vs optional：何時用哪個；例外安全三級保證",
   "斷言（assert）、前置條件與契約式設計"],
  build=["（選做，題庫 d095）用 variant 為 d095 的運算式建 AST（數字、二元運算、括號），用 visit 求值；解析錯誤用 optional 或例外回報，二選一並說明理由"],
  res=["tour", "cppref", "cpp_guide"],
  pitfalls=["string_view 指向已銷毀的暫時字串", "catch 例外用傳值造成切片"],
  check=["`optional<int>` 與回傳 -1 表示失敗相比的好處？", "string_view 可以安全地存進成員變數嗎？"],
  gate=G(["d092"], 45, 1), read=["A Tour of C++ 第 3、8、9 章"])

U(1, 1, "階段 C1 驗收週", "用現代 C++ 風格解題與實作小型函式庫，零 sanitizer 報告。",
  ["複習；回顧本階段所有 build 作業，補上缺的測試與註解"],
  res=["cpp_guide"], check=["列出你寫 C++ 時固定遵守的 10 條規則（用 Core Guidelines 編號對照）"],
  gate=G(["e201", "e202"], 90, 2))

# ============================ C2：競程與基礎演算法（第 24–41 週）============================
U(2, 1, "複雜度分析與常數優化", "能在寫程式前估算是否會超時，並知道哪些常數最值得優化。",
  ["大 O 與輸入規模：1 秒約 10^8 次簡單運算；n≤10^5 要 O(n log n)、n≤20 可指數、n≤500 可 O(n³)",
   "均攤分析（vector 擴容、雙指標）；遞迴式與主定理的直覺",
   "常數：快取友善（連續記憶體）、少用 `endl` 與 `map`、避免在迴圈裡配置記憶體",
   "用 `<chrono>` 量測，用 `-O2` 與不同輸入規模看斜率"],
  drills=["d038", "d116", "d118"],
  build=["對一個 O(n²) 與一個 O(n log n) 解，量測 n = 10^3…10^6 的耗時，畫出斜率並對照理論"],
  res=["cphb", "cpalgo", "cppref"],
  pitfalls=["只看漸進複雜度忽略常數（如 unordered_map 對小資料不一定比排序快）", "沒考慮遞迴深度與記憶體限制"],
  check=["n = 2×10^5 時 O(n²) 為什麼一定超時？", "均攤 O(1) 是什麼意思？"],
  gate=G(["d075"], 30, 1), read=["CPH 第 2 章"])

U(2, 2, "排序、二分搜尋、前綴和與差分", "把『可以排序／二分／累積』的觀察用在題目上。",
  ["排序後解題：配對、區間、掃描；自訂比較；穩定排序的用途",
   "二分搜尋的三種：找值、找邊界（lower／upper_bound）、對『答案』二分（可行性單調）",
   "一維與二維前綴和、差分陣列（區間加）；離散化（排序＋unique＋lower_bound）",
   "寫二分的不變量：[lo, hi) 半開區間，每一步都縮小，不會無窮迴圈"],
  drills=["d046", "d128", "d129", "d130"],
  planned=[("c201", "離散化計數", "座標大到 10^9 的點，離散化後用差分統計重疊（對拍暴力）")],
  res=["cphb", "cpalgo", "cses"],
  pitfalls=["二分的 mid 溢位（`(l + r) / 2`）與邊界死循環", "差分陣列還原時漏掉最後一格"],
  check=["答案二分需要什麼性質？舉兩個例子。", "二維前綴和的包含排除公式？"],
  gate=G(["d047", "d131"], 40, 1), read=["CPH 第 3、9 章"])

U(2, 2, "雙指標、滑動視窗與單調結構", "用 O(n) 取代 O(n²) 的區間問題。",
  ["雙指標：同向（滑動視窗）與對向（有序陣列兩數和）；視窗內維護計數或和",
   "單調 stack：下一個更大元素、直方圖最大矩形；單調 deque：滑動視窗最大值",
   "證明為什麼是 O(n)：每個元素最多進出一次"],
  drills=["d131", "d132", "d053", "d133", "d139", "d050", "d051"],
  res=["cphb", "cpalgo", "cses"],
  pitfalls=["視窗收縮的條件寫錯導致漏解", "單調 stack 存索引還是值"],
  check=["滑動視窗最大值為什麼 deque 內要維持遞減？", "雙指標法適用的『單調性』是什麼？"],
  gate=G(["e402"], 40, 1), read=["CPH 第 8 章"])

U(2, 1, "堆與貪心", "辨認貪心可行的題型並證明（交換論證）。",
  ["priority_queue 的典型用途：合併、Top-K、模擬事件、Dijkstra；雙堆維護中位數",
   "貪心的證明：交換論證、反證、歸納；常見題型：區間排程、區間覆蓋、霍夫曼、背包的部分版本",
   "反例思維：寫貪心前先找一個能打倒它的反例"],
  drills=["d052", "d054", "d136", "d137", "d138", "d127"],
  res=["cphb", "cpalgo"],
  pitfalls=["貪心沒有證明，只靠樣例通過", "排序鍵選錯（依結束時間還是開始時間）"],
  check=["區間排程為什麼依結束時間排序？", "貪心與 DP 的分界怎麼判斷？"],
  gate=G(["e202"], 40, 1), read=["CPH 第 6 章"])

U(2, 2, "遞迴、回溯與位元運算", "寫出正確的搜尋，會剪枝，用位元表示集合。",
  ["遞迴三要素：狀態、轉移、終止；搜尋樹與剪枝；全排列與組合的兩種寫法",
   "位元運算：`& | ^ ~ << >>`、`1<<k`、lowbit `x & -x`、`__builtin_popcount`、枚舉子集 `for (s = m; s; s = (s-1) & m)`",
   "有號數右移與 `1 << 31` 是 UB 的邊界；用 `1LL <<`",
   "meet in the middle（折半枚舉）入門"],
  drills=["d056", "d057", "d058", "d059", "d141", "d142", "d143", "d144", "d145"],
  res=["cphb", "cpalgo", "cses"],
  pitfalls=["遞迴搜尋沒有還原狀態（backtrack）", "`1 << 40` 用 int 計算"],
  check=["枚舉 n 個元素所有子集的兩種方法？", "`x & (x - 1)` 做了什麼？"],
  gate=G(["e203"], 40, 1), read=["CPH 第 5 章"])

U(2, 2, "圖：BFS、DFS、並查集與拓撲排序", "會表示圖、遍歷圖，並辨認連通性、環、層次與依賴。",
  ["鄰接表（`vector<vector<int>>`）vs 鄰接矩陣；有向／無向；加權",
   "BFS（最短步數、多源）、DFS（連通分量、遞迴深度與改迭代）；二分圖著色",
   "並查集：路徑壓縮＋按大小合併，近似 O(α(n))；維護群組大小；偵測環",
   "拓撲排序：Kahn（入度）與 DFS；唯一性；分層；在 DAG 上做 DP"],
  drills=["d060", "d061", "d062", "d146", "d147", "d148", "d149", "d150", "d151", "d152", "d153"],
  res=["cphb", "cpalgo", "cses", "visualgo"],
  pitfalls=["無向圖忘了加反向邊", "DFS 遞迴在 10^5~10^6 層會 stack overflow（需要迭代版或加大 stack）"],
  check=["BFS 為什麼能求無權圖最短路？", "並查集不做路徑壓縮會退化成多少？"],
  gate=G(["e301", "e302"], 60, 1), read=["CPH 第 11–12、15–16 章"])

U(2, 2, "最短路徑與最小生成樹", "選對最短路演算法，會建 MST 並處理變形。",
  ["Dijkstra（priority_queue，負權不能用）、Bellman-Ford（負權與偵測負環）、Floyd-Warshall（n≤400 全點對）、0-1 BFS",
   "最短路徑計數與還原路徑；分層圖（多一維狀態）",
   "MST：Kruskal（排序＋並查集）、Prim；唯一性；瓶頸路徑",
   "選擇準則：看邊權、點數、是否要全點對"],
  drills=["d063", "d064", "d065", "d154", "d156", "d157", "d158", "d088"],
  planned=[("c202", "0-1 BFS 與雙端佇列", "邊權只有 0 或 1 的最短路，要求 O(V+E)，對拍 Dijkstra")],
  res=["cphb", "cpalgo", "cses", "visualgo"],
  pitfalls=["INF 設太小導致相加溢位", "Dijkstra 的過期節點沒略過"],
  check=["為什麼 Dijkstra 不能處理負權邊？", "Kruskal 與 Prim 各適合什麼密度的圖？"],
  gate=G(["e403"], 60, 1), read=["CPH 第 13–15 章"])

U(2, 3, "DP 基礎、背包與序列 DP", "能定義狀態、寫轉移、決定順序與初始化，並優化空間。",
  ["DP 三步：狀態定義、轉移方程、邊界；自頂向下（記憶化）vs 自底向上",
   "一維：爬階梯、選或不選；背包：0-1、完全、恰好裝滿；二維：LCS、編輯距離、網格路徑與正方形",
   "滾動陣列與背包倒序更新的原因；最佳化 vs 計數（模運算）",
   "LIS 的 O(n log n)；Kadane；計數 DP 的取模"],
  drills=["d066", "d067", "d068", "d069", "d070", "d071", "d072", "d159", "d160", "d161", "d163", "d164", "d166", "d167", "d169", "d170", "d171", "d091"],
  res=["cphb", "cpalgo", "cses"],
  pitfalls=["0-1 背包正向更新導致一個物品被選多次", "初始化 INF 與 0 搞混"],
  check=["為什麼 0-1 背包的一維解要倒序？", "什麼時候記憶化比自底向上方便？"],
  gate=G(["e303"], 50, 1), read=["CPH 第 7 章"])

U(2, 2, "區間 DP、位元遮罩 DP 與樹 DP", "處理狀態是『區間』『集合』『子樹』的 DP。",
  ["區間 DP：`dp[l][r]` 枚舉分割點，O(n³)；回文與合併成本",
   "位元遮罩 DP：`dp[mask][i]`，n≤20；TSP 與指派問題；子集枚舉 3^n",
   "樹 DP：後序合併子樹；直徑與最大路徑和；換根 DP 入門",
   "DP 的順序：依區間長度、依 mask 大小、依 DFS 後序"],
  drills=["d073", "d074", "d085", "d172", "d173", "d174", "d175", "d176", "d168", "d194"],
  res=["cphb", "cpalgo", "cses"],
  pitfalls=["區間 DP 迴圈順序（要依長度）", "樹 DP 用遞迴在鏈狀樹爆 stack"],
  check=["TSP 位元遮罩 DP 的狀態與複雜度？", "樹的直徑為什麼可以用兩次 BFS 也可以用樹 DP？"],
  gate=G(["d091"], 50, 1), read=["CPH 第 10 章"])

U(2, 1, "階段 C2 驗收週：CPE 全真", "用 C++ 在時限內完成 CPE 等級題目，達到穩定一次 6 題的程度。",
  ["全真模擬：`cpe mock start --kind full`（語言選 C++）；賽後檢討：每題的錯誤類型與時間分配"],
  res=["cphb", "cf"], check=["我的 C++ 模板（IO、容器別名、常用函式）有哪些？"],
  gate=G(["e301", "e302", "e303"], 120, 2))

# ============================ C3：進階資料結構與演算法（第 42–60 週）============================
U(3, 2, "樹狀陣列與線段樹", "做到單點／區間更新與查詢，會用 lazy propagation。",
  ["Fenwick（BIT）：前綴和、逆序對、區間更新單點查詢；二維 BIT",
   "線段樹：遞迴與非遞迴寫法；區間和／最大值／gcd；lazy propagation（區間加、區間賦值）",
   "離線處理：把查詢排序後掃描；座標壓縮",
   "什麼時候選 BIT（簡單、常數小）、什麼時候選線段樹（可處理非可逆運算）"],
  drills=["d086", "d195", "d196"],
  planned=[("c301", "區間加區間和", "懶標線段樹，n、q ≤ 2×10^5，對拍暴力"), ("c302", "二維 BIT", "矩形加、矩形和"), ("c303", "區間賦值與最大連續段", "維護前綴／後綴／最大段合併")],
  res=["cpalgo", "cphb", "cses"],
  pitfalls=["懶標下推順序", "線段樹大小開 4n"],
  check=["為什麼 BIT 只能處理『可逆』運算？", "懶標什麼時候需要下推？"],
  gate=G(["d087"], 60, 1), read=["CP-Algorithms：Fenwick Tree、Segment Tree"])

U(3, 2, "稀疏表、RMQ、LCA 與樹上查詢", "O(1) 區間最值，樹上祖先與路徑查詢。",
  ["稀疏表（sparse table）：預處理 O(n log n)、查詢 O(1)（冪等運算）",
   "LCA 三種：倍增（binary lifting）、Euler tour＋RMQ、Tarjan 離線",
   "子樹用 DFS 序變成區間；路徑查詢的組合；樹的直徑與重心",
   "樹上差分"],
  drills=["d087", "d186", "d187"],
  planned=[("c304", "第 k 祖先", "倍增求第 k 祖先與 LCA，n、q ≤ 2×10^5"), ("c305", "子樹查詢", "DFS 序＋BIT，子樹加值與單點查詢"), ("c306", "樹上路徑差分", "每條路徑加 1，求每條邊被覆蓋次數")],
  res=["cpalgo", "cphb"],
  pitfalls=["稀疏表只能用於冪等運算（min、max、gcd），不能用於和", "倍增陣列大小 log 的計算"],
  check=["為什麼 LCA 可以化成 RMQ？", "倍增法預處理與查詢各是多少複雜度？"],
  gate=G(["d194"], 60, 1), read=["CP-Algorithms：LCA"])

U(3, 2, "強連通、橋與割點、2-SAT", "處理有向圖縮點與無向圖雙連通。",
  ["SCC：Tarjan 與 Kosaraju；縮點成 DAG 後做 DP",
   "橋與割點（low-link）；邊雙連通與點雙連通",
   "2-SAT：蘊含圖＋SCC，構造解",
   "迭代版 DFS 以避免遞迴爆 stack"],
  drills=["d089"],
  planned=[("c307", "找橋", "輸出所有橋，n、m ≤ 2×10^5"), ("c308", "割點與雙連通分量", "輸出割點與點雙連通分量數"), ("c309", "2-SAT 構造", "輸出一組可行解或 IMPOSSIBLE"), ("c310", "縮點 DP", "SCC 縮點後求最長路徑")],
  res=["cpalgo", "cphb"],
  pitfalls=["Tarjan 的 low 值更新用 dfn 還是 low", "重邊與自環"],
  check=["Tarjan 與 Kosaraju 各需要幾次 DFS？", "2-SAT 為什麼用 SCC 能判斷無解？"],
  gate=G(["d062"], 60, 1), read=["CP-Algorithms：Strongly connected components、Bridges"])

U(3, 2, "網路流與匹配", "建模成最大流／最小割／匹配，並用 Dinic 實作。",
  ["最大流最小割定理；Edmonds-Karp 與 Dinic（BFS 分層＋DFS 阻塞流）；複雜度直覺",
   "二分圖匹配：匈牙利演算法與 Hopcroft-Karp；最小點覆蓋與最大獨立集（König）",
   "最小費用流（SPFA／Dijkstra＋勢能）；常見建模：拆點、超級源匯點、最大權閉合子圖",
   "寫流量程式的除錯法：先用小圖手算、檢查流量守恆"],
  drills=["d090"],
  planned=[("c311", "Dinic 最大流", "n≤10^3、m≤10^4"), ("c312", "二分圖最大匹配", "Hopcroft-Karp，n、m ≤ 10^5"), ("c313", "最小費用最大流", "輸出流量與費用"), ("c314", "最大權閉合子圖", "專案與依賴，建模成最小割"), ("c315", "拆點建模", "點容量限制的最大流")],
  res=["cpalgo", "clrs", "cphb"],
  pitfalls=["反向邊容量為 0 的建立", "當前弧優化漏掉導致 TLE"],
  check=["最大流最小割定理的內容？", "為什麼 Dinic 在單位容量網路特別快？"],
  gate=G(["d089"], 60, 1), read=["CP-Algorithms：Maximum flow；CLRS 第 26 章"])

U(3, 2, "字串演算法", "O(n) 字串比對、多模式、後綴結構與雜湊。",
  ["KMP 失敗函數、Z 函數、字首函數的關係；週期與邊界",
   "字串雜湊（多項式雜湊、雙模數、抗被打爆的隨機底）；Manacher 回文",
   "Trie 與 Aho-Corasick（多模式匹配）；後綴陣列與 LCP（SA-IS 或倍增）",
   "後綴自動機的概念與用途（選修）"],
  drills=["d083", "d084", "d189", "d190", "d191"],
  planned=[("c316", "雜湊比較子字串", "q 次詢問 s[l1..r1] 與 s[l2..r2] 是否相等，對拍 KMP"), ("c317", "Aho-Corasick", "文字中多模式出現次數"), ("c318", "Manacher", "最長回文子字串"), ("c319", "後綴陣列＋LCP", "不同子字串個數")],
  res=["cpalgo", "cphb"],
  pitfalls=["單一模數雜湊被構造資料打爆", "後綴陣列的哨兵字元"],
  check=["KMP 的失敗函數表示什麼？", "雜湊衝突機率怎麼估？雙模數夠嗎？"],
  gate=G(["d095"], 60, 1), read=["CP-Algorithms：String Processing"])

U(3, 2, "數論與組合", "模運算、質數、組合計數與卷積。",
  ["快速冪、擴展歐幾里得與模逆元、費馬小定理；線性篩與歐拉函數；中國剩餘定理（CRT）",
   "Miller-Rabin 質數判定與 Pollard rho 分解（64 位元）；整除分塊",
   "組合：nCr mod p（階乘預處理、Lucas）；卡特蘭數、容斥原理、Burnside 入門",
   "FFT／NTT 多項式乘法；矩陣快速冪求線性遞迴"],
  drills=["d093", "d075", "d177", "d178", "d179"],
  planned=[("c320", "CRT 合併", "多組同餘式，不互質版本"), ("c321", "Miller-Rabin", "判定 10^18 以內的質數"), ("c322", "Pollard rho", "分解 10^18 以內的整數"), ("c323", "nCr mod p 與 Lucas", "p 為小質數"), ("c324", "NTT 卷積", "兩個長 2×10^5 的多項式相乘 mod 998244353"), ("c325", "矩陣快速冪", "線性遞迴第 n 項")],
  res=["cpalgo", "cphb", "cses"],
  pitfalls=["`a * b % m` 在 m 約 10^18 時要用 `__int128`", "模逆元需要 gcd = 1"],
  check=["為什麼費馬小定理能求逆元？什麼時候不能用？", "NTT 為什麼常用 998244353？"],
  gate=G(["d038"], 60, 1), read=["CPH 第 21–25 章"])

U(3, 2, "計算幾何", "用整數與叉積做精準的幾何判斷，會凸包與掃描線。",
  ["向量、叉積與點積；線段相交與點在多邊形內；面積（鞋帶公式）",
   "凸包：Andrew monotone chain；旋轉卡尺（直徑、最小外接矩形）",
   "最近點對（分治或掃描線）；半平面交（選修）",
   "浮點誤差：能用整數就不要用浮點；`eps` 的用法與陷阱"],
  drills=["d080", "d081", "d082", "d181", "d182", "d183", "d184"],
  planned=[("c326", "凸包", "輸出凸包頂點（含共線處理規則）"), ("c327", "旋轉卡尺", "凸包直徑"), ("c328", "最近點對", "n ≤ 2×10^5"), ("c329", "半平面交", "判斷是否有交與面積")],
  res=["cpalgo", "cphb"],
  pitfalls=["共線點與重複點處理", "叉積乘法溢位 int"],
  check=["為什麼幾何題盡量用整數？", "Andrew 演算法如何處理共線點？"],
  gate=G(["d078"], 60, 1), read=["CPH 第 29 章"])

U(3, 2, "進階 DP 與優化", "辨認並套用 DP 優化，處理大狀態。",
  ["斜率優化（CHT）與 Li Chao 樹；分治優化（D&C optimization）；Knuth 優化",
   "SOS DP（子集和）；數位 DP 進階；博弈 DP 與 SG 函數",
   "單調佇列優化 DP；矩陣快速冪優化線性遞迴 DP",
   "判斷是否適用：先寫暴力 DP，觀察轉移的單調性／凸性"],
  drills=["d092", "d094", "d193"],
  planned=[("c330", "斜率優化 DP", "n ≤ 10^6 的分段成本最小化"), ("c331", "分治優化", "k 段分割最小成本"), ("c332", "SOS DP", "n ≤ 20 的子集和與超集和"), ("c333", "SG 函數", "多堆組合博弈")],
  res=["cpalgo", "cphb"],
  pitfalls=["優化條件（四邊形不等式、斜率單調）沒驗證就套用", "CHT 的斜率與查詢順序"],
  check=["什麼是 DP 的四邊形不等式？它保證什麼？", "SOS DP 的複雜度為什麼是 n·2^n？"],
  gate=G(["d076"], 60, 1), read=["CP-Algorithms：Divide and Conquer DP、Convex Hull Trick"])

U(3, 2, "樹分治、HLD 與離線演算法", "處理大規模樹上路徑查詢與離線查詢。",
  ["重輕鏈剖分（HLD）：把樹路徑變成 O(log n) 段序列區間，配合線段樹",
   "點分治（centroid decomposition）：路徑計數與統計",
   "啟發式合併（small to large）與 DSU on tree",
   "莫隊（Mo's algorithm）與帶修改莫隊；離線排序技巧"],
  planned=[("c334", "HLD 路徑查詢", "路徑加值與路徑最大值，n、q ≤ 10^5"), ("c335", "點分治路徑計數", "統計長度恰為 k 的路徑數"), ("c336", "DSU on tree", "子樹內不同顏色數"), ("c337", "莫隊", "區間內不同數字個數"), ("c338", "樹上啟發式合併", "各子樹眾數")],
  res=["cpalgo", "cphb"],
  pitfalls=["HLD 的線段樹位置映射", "莫隊的奇偶排序優化與指針移動順序"],
  check=["HLD 為什麼任一路徑只經過 O(log n) 條輕邊？", "莫隊的複雜度怎麼推導？"],
  gate=G(["d086"], 60, 1), read=["CP-Algorithms：Heavy-light decomposition、Centroid decomposition"])

U(3, 1, "階段 C3 驗收週", "用 C++ 在 4–5 小時內完成演算法比賽等級（Codeforces Div2 C–E／ABC E–G）題目。",
  ["以 Codeforces 或 AtCoder 的歷史賽事做虛擬競賽；賽後把每個沒做出來的題整理成『缺的知識＋模板』"],
  res=["cf", "atcoder", "cpalgo"], check=["我的模板庫有哪些？每個都有測試嗎？"],
  gate=G(["e403", "d079", "d182"], 150, 2))

# ============================ C4：效能工程與系統能力（第 61–70 週）============================
U(4, 2, "效能量測與剖析", "用數據找瓶頸，而不是用猜的。",
  ["量測：`<chrono>`、重複多次取中位數、避免被編譯器消掉（`benchmark::DoNotOptimize`）；用 Google Benchmark",
   "剖析器：`perf stat／perf record`、gprof、valgrind --tool=callgrind、火焰圖；看 cache miss 與 branch miss",
   "編譯旗標：-O2／-O3／-march=native／-flto；看 Compiler Explorer 的組語",
   "TLE 獵人：對 d076–d079 這類題，先量測再優化"],
  drills=["d076", "d077", "d078", "d079"],
  build=["對一個 10^7 規模的程式做完整剖析：perf 找出前 3 個熱點、說明各自成因、提出並驗證修正，附前後數據（至少 20% 改進）"],
  res=["godbolt", "cppref", "csapp"],
  pitfalls=["在 -O0 下量測", "只跑一次就下結論", "微基準被編譯器整段刪掉"],
  check=["perf stat 的 IPC 代表什麼？", "為什麼要用中位數而不是平均？"],
  gate=P(["剖析報告：熱點、原因、修正、前後數據", "benchmark 程式碼可重現（含編譯與執行指令）", "改進不改變輸出（以對拍驗證）"], 7), read=["CS:APP 第 5、6 章"])

U(4, 2, "記憶體階層與資料佈局", "懂快取與記憶體頻寬，會改資料佈局讓程式變快。",
  ["快取行（64 B）、空間／時間局部性；行優先與列優先走訪；快取未命中的代價",
   "AoS vs SoA；`vector<vector<T>>` vs 一維壓平；小物件配置（記憶體池、arena）",
   "對齊與 padding、false sharing；虛擬記憶體與 page fault 入門",
   "分塊（tiling）：矩陣乘法的 cache blocking"],
  planned=[("c401", "矩陣乘法分塊", "n = 1024 的矩陣乘法，目標比樸素版快 5 倍以上")],
  build=["實作矩陣乘法 ijk、ikj、分塊三版，量測並解釋差距；把 AoS 改 SoA 並量測一個粒子更新迴圈"],
  res=["csapp", "godbolt", "cppref"],
  pitfalls=["只看理論複雜度忽略記憶體存取模式", "二維陣列走訪順序錯了慢數倍"],
  check=["為什麼 ikj 比 ijk 快？", "什麼是 false sharing？"],
  gate=P(["三種矩陣乘法的量測表與解釋", "SoA 版本在粒子更新上有可重現的加速", "用 perf 或 cachegrind 的 cache miss 數據佐證"], 7), read=["CS:APP 第 6 章"])

U(4, 1, "位元技巧、SIMD 與編譯期計算", "用 bitset、內建函式、constexpr 與自動向量化加速。",
  ["`std::bitset` 與用位元平行加速 DP（LCS、背包）；`__builtin_popcountll／clzll／ctzll`；C++20 `<bit>`",
   "自動向量化：寫成編譯器能向量化的迴圈（無相依、連續記憶體）；`-fopt-info-vec`；SIMD intrinsics 概念（AVX2）",
   "constexpr／consteval：在編譯期產生查表；`static_assert`",
   "`-march=native` 的風險（部署到別台機器不能跑）"],
  planned=[("c402", "bitset 加速", "n = 10^5 的 0-1 背包可達性，用 bitset 達到 O(n·W/64)"), ("c403", "編譯期查表", "constexpr 產生質數表與階乘表")],
  build=["讓一個簡單迴圈被自動向量化（附 -fopt-info-vec 輸出），再破壞它（加入相依）看輸出怎麼變"],
  res=["godbolt", "cppref", "csapp"],
  pitfalls=["對未對齊或有別名的指標期待向量化", "constexpr 運算量太大拖慢編譯"],
  check=["bitset 為什麼能把某些 DP 加速 64 倍？", "什麼情況會阻止自動向量化？"],
  gate=P(["bitset 版 0-1 背包通過 10^5 規模且比 vector<bool> 快 10 倍以上", "constexpr 查表有 static_assert 驗證", "附自動向量化報告與說明"], 5), read=["cppreference：<bitset> <bit>"])

U(4, 2, "並行與平行", "寫出沒有資料競爭的多執行緒程式，並理解何時值得平行。",
  ["`std::thread`、`mutex`、`lock_guard`／`scoped_lock`、`condition_variable`；死結的四個條件與避免",
   "`std::atomic` 與記憶體順序（relaxed／acquire／release／seq_cst）入門；資料競爭是 UB",
   "`std::async`／`future`；平行演算法 `std::execution::par`；OpenMP 入門",
   "Amdahl 定律；用 ThreadSanitizer 抓競爭；平行的負擔（執行緒建立、同步、false sharing）"],
  planned=[("c404", "平行前綴和", "把一個 10^8 的前綴和分段平行化，量測加速比"), ("c405", "平行合併排序", "遞迴到門檻後改循序，量測加速比")],
  build=["寫一個故意有資料競爭的程式，用 -fsanitize=thread 抓出，再用 mutex 與 atomic 各修一次並量測差異"],
  res=["cppref", "tour", "csapp"],
  pitfalls=["把 `int counter` 在多執行緒下直接 ++", "鎖的粒度太大導致沒加速", "忘了 join"],
  check=["Amdahl 定律說了什麼？", "`atomic<int>` 與 `mutex` 保護的 int 各有什麼成本？"],
  gate=P(["平行前綴和與平行合併排序在 4 核以上有 2 倍以上加速並附量測", "TSan 零報告", "對拍驗證結果與循序版相同"], 7), read=["A Tour of C++ 第 18 章"])

U(4, 2, "建置、測試與品質", "用 CMake 管專案，用測試與工具維持品質。",
  ["CMake：目標（target）、`target_link_libraries`、`add_subdirectory`、`FetchContent`／套件管理；Release 與 Debug 設定",
   "單元測試：GoogleTest 或 Catch2；參數化測試；隨機測試與對拍；模糊測試（libFuzzer／AFL++ 概念）",
   "靜態分析：clang-tidy、cppcheck；格式化：clang-format；警告視為錯誤的策略",
   "CI：在 GitHub Actions 跑編譯＋測試＋sanitizer；git 工作流程與程式碼審查"],
  build=["把前面某個作業（如 ModInt 或 Fenwick）整理成 CMake 專案：src／include／tests／bench，CI 跑 Debug＋ASan＋UBSan＋Release 測試"],
  res=["cmake", "gtest", "progit", "cpp_guide"],
  pitfalls=["測試只在 Release 跑，錯過 assert", "CI 沒有 sanitizer"],
  check=["為什麼要同時跑 Debug 與 Release 測試？", "模糊測試與隨機對拍的差別？"],
  gate=P(["CMake 專案可一行指令建置與測試", "至少 30 個測試，含邊界與隨機對拍", "CI 綠燈且包含 ASan／UBSan", "clang-tidy 無新警告"], 7), read=["Modern CMake 教學"])

U(4, 1, "階段 C4 驗收週", "把效能與品質流程套用到一個完整小專案。",
  ["回顧前四個單元的作品，選一個加上基準、測試與文件，整理成作品集第一份"],
  res=["cmake", "gtest"], check=["我的專案能讓別人一行指令重現結果嗎？"],
  gate=P(["作品集第一份：README（問題、方法、複雜度、基準結果）", "任何人 clone 後 `cmake --build` 與測試都能過", "有效能數據與剖析結論"], 5))

# ============================ C5：演算法工程師作品與面試（第 71–82 週）============================
U(5, 3, "演算法函式庫（header-only）", "把整條軌道的演算法整理成可測試、可文件化的函式庫。",
  ["API 設計：泛型、命名、複雜度寫在文件、錯誤處理；header-only 的取捨",
   "函式庫內容（至少 15 個）：DSU、Fenwick、線段樹（含 lazy）、稀疏表、LCA、SCC、Dinic、匹配、KMP／Z／雜湊、Aho-Corasick、後綴陣列、ModInt、NTT、Miller-Rabin、凸包",
   "每個元件：單元測試、隨機對拍、基準；文件與使用範例",
   "版本與相容：C++17 與 C++20 的差異處理"],
  build=["完成 header-only 函式庫 `algolib`：每個元件有測試、對拍與基準；README 有複雜度表與使用範例；發佈 v1.0 tag"],
  res=["cpalgo", "cpp_guide", "gtest", "cmake"],
  pitfalls=["沒有對拍就相信自己的實作", "API 為了競賽方便而不通用"],
  check=["你的哪個元件最容易寫錯？測試怎麼保證？"],
  gate=P(["15 個以上元件，各有測試與基準", "全部通過 ASan／UBSan／TSan（適用者）", "README 含複雜度表與範例；CI 綠燈", "隨機抽 3 個元件，能現場說明演算法、複雜度與邊界"], 14))

U(5, 2, "專題一：搜尋與索引", "實作一個小型全文檢索：倒排索引、前綴查詢與 Top-K。",
  ["資料結構：倒排索引、Trie 或 FST 概念、Top-K 堆；字詞切分與正規化",
   "效能：記憶體佈局、壓縮（差分＋變長編碼）、批次查詢、快取",
   "正確性：與暴力版對拍；邊界（空查詢、重複詞、超長文件）",
   "基準：1 GB 文字或 10^6 文件規模的建索引時間與查詢延遲分位數（p50／p99）"],
  build=["實作 `mini-search`：建索引、AND／OR 查詢、前綴補全、Top-K（BM25 或簡單 TF-IDF）；與暴力版對拍；提交基準報告"],
  res=["cpalgo", "tour"],
  pitfalls=["只量平均延遲不看 p99", "索引壓縮後忘了測解壓正確性"],
  check=["為什麼倒排索引用差分編碼？"],
  gate=P(["功能：AND／OR、前綴、Top-K", "對拍通過且有 20 個以上邊界測試", "基準：建索引吞吐量與 p50／p99 查詢延遲，附圖", "README 說明設計取捨"], 10))

U(5, 2, "專題二：路徑規劃引擎", "在大圖上做最短路與 A*，並做加速。",
  ["Dijkstra、A*（啟發函式可採納性）、雙向搜尋；圖的壓縮表示（CSR）",
   "加速技術：ALT（地標）、Contraction Hierarchies 概念；多次查詢的預處理與取捨",
   "資料：自行產生網格圖與道路網格；或使用公開道路網資料集",
   "正確性與效能：與 Dijkstra 對拍；查詢延遲與預處理時間的取捨"],
  build=["實作 `mini-router`：CSR 圖、Dijkstra、A*、雙向 Dijkstra；對 10^6 節點圖比較三者的查詢時間與擴展節點數"],
  res=["cpalgo", "clrs", "csapp"],
  pitfalls=["啟發函式不可採納導致結果不是最短", "CSR 建構時邊排序錯誤"],
  check=["A* 的啟發函式必須滿足什麼才保證最優？"],
  gate=P(["三種演算法對拍一致（10^4 組隨機查詢）", "附擴展節點數與時間比較圖", "CSR 圖的記憶體使用量低於鄰接表版本並有數據"], 10))

U(5, 2, "專題三：壓縮或最佳化求解器", "二選一：實作資料壓縮器，或實作啟發式最佳化求解器。",
  ["選項 A：壓縮：Huffman、LZ77／LZSS、BWT＋MTF、算術編碼概念；位元層級 I/O；與 gzip 比較壓縮率與速度",
   "選項 B：求解器：排班／裝箱／TSP 的啟發式（貪心、局部搜尋、模擬退火、禁忌搜尋）；與精確解（小規模）比較品質差距",
   "兩者共通：可重現的隨機種子、基準資料集、品質與時間的取捨曲線",
   "選項 A 要驗證無損還原；選項 B 要驗證解的可行性"],
  build=["完成 A 或 B：附基準資料集、可重現腳本、結果圖與一頁報告"],
  res=["clrs", "cpalgo"],
  pitfalls=["壓縮器沒做損壞資料輸入的處理", "啟發式沒有固定隨機種子導致無法重現"],
  check=["你的方法在哪類輸入上最差？為什麼？"],
  gate=P(["A：任意檔案壓縮後可無損還原（含空檔與 1 GB 檔）；B：所有輸出解皆可行（以檢查器驗證）", "與參考方法（gzip 或精確解）的比較表", "一頁報告：設計、取捨、局限"], 10))

U(5, 2, "面試與系統設計", "能在 45 分鐘內講清楚解法、寫出可用程式，並做小型系統設計。",
  ["演算法面試流程：澄清題意→舉例→暴力解→優化→複雜度→寫碼→測試；說話節奏與溝通",
   "經典設計題：LRU／LFU 快取、限流器、任務排程器、一致性雜湊、Top-K 熱門項目、簡易鍵值儲存",
   "C++ 面試：RAII、移動語意、虛函式與 vtable、智慧指標、UB 辨認、STL 實作細節",
   "行為面試：描述專案取捨與失敗經驗；作品集講解"],
  planned=[("c501", "LRU 快取", "O(1) 的 get／put，用雜湊＋雙向鏈結串列，要求通過隨機對拍"), ("c502", "限流器", "滑動視窗與令牌桶兩種實作"), ("c503", "一致性雜湊", "含虛擬節點與節點增減的搬移量統計")],
  build=["完成 6 次模擬面試（互相或請人當面試官），每次錄音或寫回饋；整理自己的常見失誤清單"],
  res=["cf", "clrs", "tour"],
  pitfalls=["一開始就寫碼不先澄清題意", "只講複雜度不講取捨"],
  check=["你如何向非技術人員說明你的專題？"],
  gate=P(["6 次模擬面試紀錄與回饋", "LRU、限流器、一致性雜湊三個實作通過測試", "能在 10 分鐘內說清楚每個專題的設計取捨"], 10))

U(5, 1, "總驗收：作品集與全真模擬", "整合驗收：作品集完整，且在時限內通過全真題組。",
  ["整理作品集：algolib、三個專題、效能報告、學習紀錄；錄一段 10 分鐘的專案講解"],
  res=["cf", "cpe"], check=["我能證明自己具備『演算法工程師』的哪些能力？每項的證據在哪？"],
  gate=P(["全真模擬：CPE 等級 6 題中穩定做出 5 題以上（C++）", "Codeforces／AtCoder 虛擬賽：達到 Div2 C–D 穩定", "作品集四件齊全：algolib v1.0、三個專題，各有 README、測試、基準", "10 分鐘專案講解影片"], 10))
