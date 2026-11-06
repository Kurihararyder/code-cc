from guide_lib import Q

HDR = "#include <bits/stdc++.h>\nusing namespace std;\n"


def prog(body, pre=""):
    return HDR + (pre.strip("\n") + "\n" if pre else "") + "int main() {\n" + "".join("    " + ln + "\n" for ln in body.strip("\n").split("\n")) + "}\n"


def cq(stem, right, wrong, why, body, expect, pre="", free=False):
    """預測 C++ 輸出的題：整支程式用 g++ -std=c++17 實際編譯執行，輸出必須含 expect。"""
    code = prog(body, pre)
    return Q(stem, right, wrong, why, verify={"lang": "cpp", "code": code, "expect": expect, "free": free}, code=code, lang="cpp")


GUIDE = dict(
    id="cpp-c0", track="cpp", stage=0,
    title="C++ 基礎總整理與模擬測驗（階段 C0）",
    subtitle="對應課程：C++ 軌道階段 C0（單元 1–8）。每一題「預測輸出」的程式都用 g++ -std=c++17 實際編譯、執行驗證過（64 位元 Linux；`sizeof` 等與平台有關的數字以此為準）。",
    howto="""每組重點後面接一組單選模擬題（四選一），最後附解答與解析。

1. 先讀重點，**每個例子自己編譯執行一遍**：`g++ -std=c++17 -O2 -Wall -Wextra main.cpp -o main && ./main`。
2. 預測輸出的題先自己推演（尤其是整數除法、型別提升、傳值與傳參考），再看選項。
3. 對照 Python 的差別特別留意：`/` 與 `%` 對負數、整數會溢位、陣列不檢查邊界。
4. 網頁的「指南」頁可以作答、計分、單獨重做錯題。

出題風格：四選一；誘答多是典型錯誤——整數除法當成浮點、傳值以為會修改、`size_t` 減法回繞、`cin >>` 後直接 `getline`、`substr` 的第二參數是長度。題目中的 `#include <bits/stdc++.h>` 是 GCC 才有的方便標頭，競程常用。""",
    sections=[
        dict(title="單元 1–2：工具鏈、型別與運算", body=r"""### 從原始碼到可執行檔
| 階段 | 做什麼 | 典型錯誤 |
| --- | --- | --- |
| 前處理 | 展開 `#include`、`#define` | 找不到標頭 |
| 編譯 | `.cpp` → 目的檔（語法、型別檢查） | `error: expected ';'`、型別不符 |
| 連結 | 把目的檔與函式庫合成可執行檔 | `undefined reference to …`（宣告了但沒定義） |
| 執行 | 執行程式 | 段錯誤、未定義行為、答案錯誤 |

常用指令：`g++ -std=c++17 -O2 -Wall -Wextra main.cpp -o main`（`-Wall -Wextra` 開警告，`-fsanitize=address,undefined` 抓越界與未定義行為）。

### 型別與大小（64 位元 Linux／g++）
| 型別 | 大小 | 範圍／備註 |
| --- | --- | --- |
| `char` | 1 | −128…127（是否有號與平台有關） |
| `int` | 4 | ≈ ±2.1×10⁹ |
| `long long` | 8 | ≈ ±9.2×10¹⁸ |
| `double` | 8 | 約 15–16 位有效數字 |
| 指標 | 8 | |

### 與 Python 最不同的運算規則
- 整數除法**向 0 截斷**：`7/2 = 3`、`-7/2 = -3`（Python 是 −4）；`%` 的符號跟**被除數**：`-7 % 3 = -1`（Python 是 2）。
- 整數**會溢位**：有號溢位是未定義行為；無號是回繞（`unsigned char c = 255; c++` → 0）。需要大數時用 `long long`，字面值寫 `100000LL * 100000`。
- 運算先依運算元型別進行：`5/2*2.0` = `(5/2)*2.0` = 4（先做整數除法）；要浮點就讓其中一個是 double：`5/2.0`。
- 型別提升：`char c='A'; c+1` 是 `int` 66，不是字元。`int x = 3.9;` 截斷成 3。
- `0.1 + 0.2 == 0.3` 為假（同 Python）。
- `const`／`constexpr` 宣告常數；`auto` 讓編譯器推導型別。"""),
        dict(title="單元 3：輸入輸出", body=r"""| 工作 | 寫法 |
| --- | --- |
| 加速 | `ios::sync_with_stdio(false); cin.tie(nullptr);`（之後不要混用 `scanf`／`printf`） |
| 讀到 EOF | `while (cin >> x) {…}` |
| 讀整行 | `getline(cin, s)` |
| 小數位數 | `cout << fixed << setprecision(2) << x;` |
| 對齊 | `setw(5)`（靠右）、`left` |
| C 風格 | `printf("%d %5.1f\n", n, x)` |

- `cin >> n` 之後**換行字元還留在緩衝區**，緊接著 `getline` 會讀到空字串；要先 `cin.ignore()` 或改用 `getline` 一路讀。
- `'\n'` 比 `endl` 快（`endl` 每次都 flush）。
- `cout << 'a' + 1` 印 `98`（`int`）；要印字元要轉型 `(char)('a' + 1)`。
- `cout << 1e6` 預設會印成 `1e+06`；要整數格式就轉成 `long long`，或用 `fixed`。"""),
        dict(title="單元 4：條件與迴圈", body=r"""- `switch` 的 `case` 若沒有 `break` 會**直通（fall through）**到下一個 case。
- `if` 的 `else` 一律接到**最近**的未配對 `if`（dangling else）；一律加大括號。
- `&&`、`||` **短路求值**：`i != 0 && 10 / i > 1` 不會除以 0。
- `do { … } while (cond);` 至少執行一次。
- 無號數陷阱：`for (size_t i = n; i >= 0; --i)` 是無窮迴圈（無號數永遠 ≥ 0）；`unsigned u = 0; u--;` 得 4294967295。
- `while (n--)` 以舊值判斷再遞減：n = 3 時迴圈內 n 依序是 2、1、0。
- `break` 只跳出最內層迴圈。三元運算子 `a > b ? a : b`。
- 邊界：用半開區間 `[l, r)`，迴圈寫 `i < n`。"""),
        dict(title="單元 5：函式、傳值與傳參考", body=r"""| 傳遞方式 | 寫法 | 效果 |
| --- | --- | --- |
| 傳值 | `void f(int x)` | 複製一份，函式內修改**不影響**呼叫端 |
| 傳參考 | `void f(int& x)` | 別名，修改**影響**呼叫端 |
| 傳常數參考 | `void f(const string& s)` | 不複製、不能改；大型物件的預設選擇 |
| 傳指標 | `void f(int* p)` | 可修改指到的物件；可為 `nullptr` |

- 陣列當參數會**退化成指標**：函式內 `sizeof(a)` 是指標大小 8，不是陣列大小。
- `static` 區域變數只初始化一次，值在多次呼叫間保留。
- 預設引數、函式多載（同名不同參數）；函式必須**先宣告再使用**。
- 絕不要回傳區域變數的參考或指標（懸空）。
- 遞迴要有終止條件；深度太深會爆堆疊（約數萬到數十萬層，視每層大小）。"""),
        dict(title="單元 6：陣列、vector 與 string", body=r"""### 陣列
- `int a[5] = {1, 2};` 其餘元素補 0；**區域**陣列不初始化就是隨機值，**全域**陣列自動為 0。
- 陣列**不檢查邊界**：越界讀寫是未定義行為（可能默默出錯）。大陣列放全域（區域陣列在堆疊上，約 8 MB 上限）。

### vector
| 寫法 | 說明 |
| --- | --- |
| `vector<int> v(3, 7)` | 3 個 7 |
| `v.push_back(x)`、`v.pop_back()`、`v.size()`、`v.empty()` | |
| `v[i]` 不檢查邊界；`v.at(i)` 越界丟 `out_of_range` | |
| `vector<vector<int>> g(R, vector<int>(C, 0))` | 二維 |
| `sort(v.begin(), v.end())`、`reverse(…)`、`greater<int>()` 遞減 | |

- **`v.size()` 回傳無號數**：空 vector 的 `v.size() - 1` 是 18446744073709551615；比較請轉型 `(int)v.size()`。

### string
- `s.substr(pos, len)` 第二參數是**長度**（不是結束索引）：`"hello".substr(1, 3)` = `"ell"`。
- `s += 'd'`、`s.size()`、`s.find(x)` 找不到回 `string::npos`。
- 轉換：`to_string(12)`、`stoi("12")`。字串可用 `==`、`<` 比較（字典序）。"""),
        dict(title="單元 7：指標、參考與記憶體模型", body=r"""| 項目 | 說明 |
| --- | --- |
| `int* p = &x;` | `p` 存 x 的位址；`*p` 是 x 本身 |
| `int& r = x;` | `r` 是 x 的別名，必須初始化、不能重新綁定 |
| 指標運算 | `p + 1` 前進 **`sizeof(int)`** 位元組；`a[i]` 等於 `*(a + i)` |
| `nullptr` | 空指標；解參考是未定義行為（通常段錯誤） |
| `const int* p` | 不能透過 p 修改指到的值 |
| `int* const p` | p 本身不能改指向別處 |

- `int *a, b;` 只有 `a` 是指標，`b` 是 `int`。
- `new` 配置堆積記憶體，要用 `delete` 釋放；`new[]` 配 `delete[]`，不匹配是未定義行為。忘了釋放 = 記憶體洩漏。
- 懸空指標：指向已釋放或已離開作用域的物件，使用是未定義行為。
- 堆疊（區域變數，自動釋放，容量小）與堆積（`new`，手動釋放，容量大）。
- 現代 C++ 優先用 `vector`、`string` 與智慧指標，少用原始 `new`／`delete`（單元 15）。"""),
    ],
    confusions=r"""### 最容易混淆的幾組
| 容易搞錯 | 正確觀念 |
| --- | --- |
| `-7/2`、`-7%3` | `-3`、`-1`（Python 是 `-4`、`2`） |
| `5/2*2.0` | 4：先整數除法 |
| `v.size() - 1`（空） | 回繞成巨大正數 |
| `void swap(int a, int b)` | 傳值，無效；要用 `int&` |
| `cin >> n; getline(…)` | 會讀到空行；先 `cin.ignore()` |
| `substr(1, 3)` | 從 1 起取 **3 個字元**（不是到 3） |
| `sizeof(陣列參數)` | 指標大小 8 |
| `int *a, b;` | b 不是指標 |
| `switch` 沒 `break` | 直通下一個 case |
| `endl` 與 `'\n'` | `endl` 會 flush，較慢 |
| 區域陣列 | 不初始化是垃圾值；大陣列放全域 |
| `cout << 1e6` | `1e+06` |

### 必背速查
- `int` 4、`long long` 8、指標 8、`char` 1（64 位元）。
- 二維 vector：`vector<vector<int>> g(R, vector<int>(C))`。
- 競程開頭：`ios::sync_with_stdio(false); cin.tie(nullptr);`。
- 偵錯：`-fsanitize=address,undefined -g`。""",
    groups=[
        dict(title="單元 1–2 模擬測驗：工具鏈、型別與運算", unit=2, questions=[
            Q("編譯時出現 `undefined reference to 'foo()'`，這是哪一階段的錯誤、通常原因是？", "連結階段；`foo()` 只有宣告、沒有（或沒連結到）定義", ["編譯階段；少了分號", "執行階段；記憶體不足", "前處理階段；`#include` 路徑錯誤"], "編譯器只檢查宣告就放行；連結器找不到實際定義才報 undefined reference。常見原因：忘了寫定義、沒把 .cpp 一起編譯。"),
            Q("下列哪一組編譯選項最適合開發時抓出越界與未定義行為？", "`-g -fsanitize=address,undefined -Wall -Wextra`", ["`-O3 -ffast-math`", "`-s -w`", "`-E`"], "Sanitizer 在執行時偵測越界、懸空與整數溢位等問題；`-Wall -Wextra` 開啟編譯期警告。`-O3` 只是最佳化，`-E` 只做前處理。"),
            cq("執行後輸出什麼？", "`-3 -1`", ["`-4 2`", "`-3 2`", "`-4 -1`"], "C++ 的整數除法向 0 截斷（−3.5 → −3），`%` 的符號與被除數相同（−7 % 3 = −1）。與 Python 的 `-4`、`2` 不同——從 Python 轉過來最常錯在這裡。", "cout << -7 / 2 << \" \" << -7 % 3 << endl;", "-3 -1"),
            cq("執行後輸出什麼？", "`3.5`", ["`3`", "`4`", "`3.0`"], "`(double)7` 先轉成 double，再除以 2，整個運算是浮點除法；`cout` 印 3.5。", "cout << (double)7 / 2 << endl;", "3.5"),
            cq("執行後輸出什麼？", "`4`", ["`5`", "`4.5`", "`5.0`"], "`5/2*2.0` 先做 `5/2`（整數除法 = 2），再 `2*2.0 = 4.0`，`cout` 印成 4。想要 5 就要寫 `5/2.0*2`。", "cout << 5 / 2 * 2.0 << endl;", "4"),
            cq("執行後輸出什麼？", "`0`", ["`256`", "`-1`", "`255`"], "`unsigned char` 的最大值是 255，再加 1 回繞到 0（無號整數的溢位是有定義的）。有號整數溢位則是未定義行為。", "unsigned char c = 255;\nc++;\ncout << (int)c << endl;", "0"),
            cq("在 64 位元 g++ 下，`sizeof(int)`、`sizeof(long long)`、`sizeof(char)` 依序是？", "`4 8 1`", ["`4 4 1`", "`2 4 1`", "`8 8 2`"], "常見平台上 int 是 4 位元組、long long 是 8、char 恆為 1（`sizeof(char)` 由標準定義為 1）。", "cout << sizeof(int) << \" \" << sizeof(long long) << \" \" << sizeof(char) << endl;", "4 8 1"),
            cq("執行後輸出什麼？", "`66`", ["`B`", "`A1`", "`65`"], "`'A'` 在運算時被提升成 `int`（65），加 1 得到整數 66，`cout` 以整數印出；要印 `B` 必須轉回 `char`。", "char c = 'A';\ncout << c + 1 << endl;", "66"),
            cq("執行後輸出什麼？", "`3`", ["`3.9`", "`4`", "發生錯誤"], "把 double 指派給 int 會截斷小數（不是四捨五入）。使用大括號初始化 `int x{3.9}` 則會被編譯器擋下（縮窄轉換）。", "int x = 3.9;\ncout << x << endl;", "3"),
            cq("要正確計算 `100000 * 100000` 並印出 `10000000000`，應該怎麼寫？", "`long long y = 100000LL * 100000;`", ["`long long y = 100000 * 100000;`", "`int y = 100000 * 100000;`", "`double y = 100000 * 100000;`"], "右邊如果兩個字面值都是 `int`，乘法在 `int` 上做，已經溢位（有號溢位是未定義行為，通常得到回繞值）才被轉成 long long。必須讓其中一個運算元是 long long。", "long long y = 100000LL * 100000;\ncout << y << endl;", "10000000000", free=True),
            cq("執行後輸出什麼？", "`false`", ["`true`", "`1`", "`0.3`"], "和 Python 一樣，0.1 + 0.2 在二進位浮點數中不精確，不等於 0.3。比較浮點數要用誤差。", "cout << boolalpha << (0.1 + 0.2 == 0.3) << endl;", "false"),
            cq("`int a = 5; int b = a++;` 之後依序印出 `a`、`b`（連在一起），輸出是？", "`65`（a 變成 6，b 拿到遞增前的 5）", ["`56`（a 還是 5，b 變成 6）", "`66`", "`55`"], "後置遞增 `a++` 的值是**遞增前**的 a，然後 a 才加 1。前置 `++a` 則是先加再取值。", "int a = 5;\nint b = a++;\ncout << a << b << endl;", "65"),
        ]),
        dict(title="單元 3 模擬測驗：輸入輸出", unit=3, questions=[
            cq("先 `in >> n`（讀到 5），再 `getline(in, s)`，`s` 的內容是？（輸入為 `5\\nhello world\\n`）", "`[]`（`s` 是空字串，讀到的是 `5` 後面剩下的換行）", ["`[hello world]`", "`[5]`", "`[hello]`"], "`>>` 不會吃掉數字後面的換行；`getline` 一讀就遇到這個換行，回傳空字串。解法：`getline(cin >> ws, s)` 或 `cin.ignore()`。", "istringstream in(\"5\\nhello world\\n\");\nint n;\nin >> n;\nstring s;\ngetline(in, s);\ncout << \"[\" << s << \"]\" << endl;", "[]"),
            cq("執行後輸出什麼？", "`3.14`", ["`3.1`", "`3.142`", "`3.14159`"], "`fixed` 固定用小數表示，`setprecision(2)` 在 fixed 下表示『小數點後 2 位』，並四捨五入。", "cout << fixed << setprecision(2) << 3.14159 << endl;", "3.14"),
            cq("執行 `printf(\"%5.1f|\", 3.14159)` 輸出什麼？", "`  3.1|`", ["`3.1|`", "`3.14159|`", "`3.1   |`"], "`%5.1f` 表示總寬度 5、小數 1 位，不足寬度時在左邊補空白。", "printf(\"%5.1f|\\n\", 3.14159);", "  3.1|"),
            cq("執行後輸出什麼？", "`98`", ["`b`", "`a1`", "`97`"], "`'a' + 1` 的型別是 `int`，值為 98。若要輸出字元 `b`，需寫 `(char)('a' + 1)`。", "cout << 'a' + 1 << endl;", "98"),
            cq("以 `while (in >> x) sum += x;` 讀入 `1 2 3`，`sum` 最後是？", "`6`", ["`3`", "`0`", "`123`"], "`in >> x` 讀取成功時條件為真；讀到結尾失敗後條件為假而結束。這是處理『不知道有幾筆』的標準寫法。", "istringstream in(\"1 2 3\");\nint x, sum = 0;\nwhile (in >> x) sum += x;\ncout << sum << endl;", "6"),
            cq("執行後輸出什麼？（`|` 只是標記邊界）", "`|   42|`", ["`|42   |`", "`|42|`", "`|00042|`"], "`setw(5)` 設定下一個輸出的寬度為 5，預設靠右對齊，左邊補空白。", "cout << \"|\" << setw(5) << 42 << \"|\" << endl;", "|   42|"),
            cq("執行後輸出什麼？", "`1e+06`", ["`1000000`", "`1000000.0`", "`1e6`"], "double 預設以最短的科學記號或一般記號輸出（6 位有效數字）。需要整數格式：`(long long)1e6` 或 `fixed`。", "cout << 1000000.0 << endl;", "1e+06"),
            Q("競賽程式中加上 `ios::sync_with_stdio(false); cin.tie(nullptr);` 的主要目的與副作用是？", "加速 `cin`／`cout`；之後不能再混用 `scanf`／`printf`", ["讓程式自動處理 EOF；沒有副作用", "讓輸出自動排序；沒有副作用", "關閉所有緩衝區以便除錯"], "預設 C++ 串流與 C 的 stdio 同步，速度慢；關掉同步後速度大增，但兩套 I/O 的順序就不再保證一致。"),
        ]),
        dict(title="單元 4 模擬測驗：條件與迴圈", unit=4, questions=[
            cq("執行後輸出什麼？", "`AB`", ["`A`", "`B`", "`C`"], "x = 1 進入 `case 1` 印 A；沒有 `break`，繼續直通 `case 2` 印 B，遇到 `break` 才離開。", "int x = 1;\nswitch (x) {\n    case 1: cout << \"A\";\n    case 2: cout << \"B\"; break;\n    default: cout << \"C\";\n}\ncout << endl;", "AB"),
            cq("執行後輸出什麼？", "`4294967295`", ["`-1`", "`0`", "`65535`"], "無號整數 0 減 1 回繞成最大值 2³²−1。這就是 `for (size_t i = n; i >= 0; --i)` 變成無窮迴圈的原因。", "unsigned u = 0;\nu--;\ncout << u << endl;", "4294967295"),
            cq("`int n = 3; while (n--) cout << n << ' ';` 輸出什麼？", "`2 1 0 `", ["`3 2 1 `", "`2 1 `", "`3 2 1 0 `"], "`n--` 的值是舊值：判斷時 n = 3（真），然後 n 變 2 才進入迴圈主體，最後 n = 1 判斷為真、n 變 0 進入，下次判斷 0 為假而結束。", "int n = 3;\nwhile (n--) cout << n << ' ';\ncout << endl;", "2 1 0 "),
            cq("執行後輸出什麼？", "`10`", ["什麼都不印", "`1`", "`0`"], "`do-while` 先執行主體再判斷條件，所以即使條件一開始就為假，主體也會執行一次。", "int i = 10;\ndo {\n    cout << i;\n} while (i < 5);\ncout << endl;", "10"),
            cq("巢狀迴圈中，內層的 `break` 之後，外層迴圈會？", "照常繼續下一輪；總共印出 3 次", ["整個迴圈全部結束", "程式立即結束", "外層也跳過一輪"], "`break` 只跳出『最內層』的迴圈。要一次跳出多層，用旗標、`return`，或把迴圈包進函式。", "int cnt = 0;\nfor (int i = 0; i < 3; i++)\n    for (int j = 0; j < 5; j++) {\n        if (j == 1) break;\n        cnt++;\n    }\ncout << cnt << endl;", "3"),
            cq("下列 dangling else 的程式輸出什麼？", "`B`（`else` 屬於內層 `if`；b 為 0，所以內層的 else 執行）", ["什麼都不印（以為 `else` 屬於外層 `if`）", "`A`", "`AB`"], "`else` 一律接最近的未配對 `if`：這裡屬於 `if (b)`，b 為 0 所以印 B。縮排只是視覺提示，編譯器不看；加大括號才能明確表達意圖。", "int a = 1, b = 0;\nif (a)\n    if (b) cout << \"A\";\n    else cout << \"B\";\ncout << endl;", "B"),
            cq("執行後輸出什麼？", "`not-called`", ["`called`", "發生除以零而當掉", "什麼都不印"], "`&&` 短路求值：左邊 `i != 0` 為假，整個運算式已確定為假，右邊的 `10 / i` 不會被計算，所以不會除以零。", "int i = 0;\nif (i != 0 && 10 / i > 1) cout << \"called\";\nelse cout << \"not-called\";\ncout << endl;", "not-called"),
            cq("計算 1 到 n 的總和（n = 100），下列哪個迴圈邊界是正確的，輸出？", "`for (int i = 1; i <= n; i++)` → `5050`", ["`for (int i = 1; i < n; i++)` → `5050`", "`for (int i = 0; i < n; i++)` → `5050`", "`for (int i = 1; i <= n; i++)` → `5051`"], "要包含 n 就用 `<=`；`i < n` 少加最後一個（得 4950），`i = 0` 起算也只多加 0 但少加 n。邊界錯是最常見的 WA 來源。", "int n = 100, s = 0;\nfor (int i = 1; i <= n; i++) s += i;\ncout << s << endl;", "5050"),
        ]),
        dict(title="單元 5 模擬測驗：函式、傳值與傳參考", unit=5, questions=[
            cq("執行後輸出什麼？", "`1 2`（傳值，沒有交換）", ["`2 1`", "`1 1`", "`2 2`"], "傳值是複製一份參數，函式內交換的是複本，呼叫端的變數不變。", "int a = 1, b = 2;\nswap_by_value(a, b);\ncout << a << \" \" << b << endl;", "1 2", pre="void swap_by_value(int x, int y) { int t = x; x = y; y = t; }"),
            cq("執行後輸出什麼？", "`2 1`", ["`1 2`", "`1 1`", "`2 2`"], "參數是 `int&`，x、y 是呼叫端 a、b 的別名，交換直接作用在原變數。", "int a = 1, b = 2;\nswap_by_ref(a, b);\ncout << a << \" \" << b << endl;", "2 1", pre="void swap_by_ref(int& x, int& y) { int t = x; x = y; y = t; }"),
            cq("三次呼叫 `next()` 之後，最後一次的回傳值是？", "`3`", ["`1`", "`0`", "`6`"], "`static` 區域變數只初始化一次，值在多次呼叫之間保留，所以依序回傳 1、2、3。", "next(); next();\ncout << next() << endl;", "3", pre="int next() { static int c = 0; return ++c; }"),
            cq("在 main 與函式 `f(int a[10])` 中，各自印出 `sizeof(a)`（main 中是 `int a[10]`），結果是？", "`40 8`", ["`40 40`", "`10 10`", "`8 8`"], "陣列當參數時退化成指標，函式內 `sizeof(a)` 是指標大小 8；在宣告它的作用域內 `sizeof` 才是整個陣列 40 位元組。", "int a[10];\ncout << sizeof(a) << \" \";\nf(a);\ncout << endl;", "40 8", pre="void f(int a[10]) { cout << sizeof(a); }"),
            Q("參數是大型物件（如 `vector<int>`），且函式不需要修改它，最合適的宣告是？", "`void f(const vector<int>& v)`", ["`void f(vector<int> v)`", "`void f(vector<int>* v)`", "`void f(vector<int>&& v)`"], "`const&` 不複製（O(1)）也不允許修改；傳值會複製整個容器，在迴圈或遞迴中常造成 TLE。"),
            cq("函式 `int fact(int n)` 以遞迴計算 5!，輸出？", "`120`", ["`24`", "`5`", "`720`"], "5! = 5×4×3×2×1 = 120；`n <= 1` 是終止條件，缺少它會無限遞迴直到堆疊爆掉。", "cout << fact(5) << endl;", "120", pre="int fact(int n) { return n <= 1 ? 1 : n * fact(n - 1); }"),
            Q("為什麼不應該回傳區域變數的參考，例如 `int& f() { int x = 1; return x; }`？", "函式結束後 x 就被銷毀，回傳的參考指向無效記憶體（懸空），使用是未定義行為", ["x 會自動被轉成全域變數", "編譯器一定會報錯，所以不可能發生", "只是效率較差，結果仍然正確"], "區域變數的生命週期只到函式結束；編譯器通常只給警告。這類錯誤會在特定情況下才爆發，很難除錯。"),
            Q("函式 `g()` 在 `main` 之後才定義，而 `main` 裡呼叫了 `g()`，會發生什麼？", "編譯錯誤：`g` 在使用時尚未宣告；需在 main 前加函式原型 `void g();`", ["自動找到 g，沒有問題", "連結時才會報錯", "執行時才會報錯"], "C++ 由上而下編譯，使用前必須先看到宣告。原型宣告讓你把定義放在後面。"),
        ]),
        dict(title="單元 6 模擬測驗：陣列、vector 與 string", unit=6, questions=[
            cq("`int a[5] = {1, 2};` 之後 `a[4]` 是多少？", "`0`", ["隨機值", "`2`", "編譯錯誤"], "大括號初始化時，沒有列出的元素會被值初始化為 0（即使是區域陣列）。完全不寫 `= {…}` 的區域陣列才是隨機值。", "int a[5] = {1, 2};\ncout << a[4] << endl;", "0"),
            cq("`vector<int> v(3, 7)` 之後印 `v.size()` 與 `v[2]`，輸出？", "`37`", ["`73`", "`27`", "`3`"], "`vector<int> v(3, 7)` 建立 3 個值為 7 的元素：size = 3，v[2] = 7，連著印成 37。", "vector<int> v(3, 7);\ncout << v.size() << v[2] << endl;", "37"),
            cq("空的 `vector<int> v`，`v.size() - 1` 的結果是？", "`18446744073709551615`", ["`-1`", "`0`", "執行時錯誤"], "`size()` 回傳無號的 `size_t`，0 − 1 回繞成 2⁶⁴ − 1。寫 `i < (int)v.size() - 1` 或 `i + 1 < v.size()` 避免。", "vector<int> v;\ncout << v.size() - 1 << endl;", "18446744073709551615"),
            cq("對 `vector<int> v(3)` 呼叫 `v.at(5)` 會？", "丟出 `out_of_range` 例外（被 catch 後印出）", ["回傳 0", "回傳隨機值", "靜默忽略"], "`v[5]` 不檢查邊界（未定義行為）；`v.at(5)` 會檢查並丟例外，偵錯時很有用。", "vector<int> v(3);\ntry {\n    v.at(5);\n} catch (const out_of_range&) {\n    cout << \"out_of_range\" << endl;\n}", "out_of_range"),
            cq("`string(\"hello\").substr(1, 3)` 的結果是？", "`ell`", ["`el`", "`ello`", "`hell`"], "`substr(pos, len)` 的第二個參數是**長度**：從索引 1 起取 3 個字元 = ell。Python 切片 `[1:3]` 才是到結束索引。", "cout << string(\"hello\").substr(1, 3) << endl;", "ell"),
            cq("執行後輸出什麼？", "`123`", ["`15`", "`12 3`", "發生錯誤"], "`to_string(12)` 得到字串 `\"12\"`，再串接 `\"3\"`。要做加法要用 `stoi`。", "cout << to_string(12) + \"3\" << endl;", "123"),
            cq("`vector<int> v = {3, 1, 2}`，依遞減排序後印出？", "`3 2 1`", ["`1 2 3`", "`2 1 3`", "`3 1 2`"], "`sort(v.begin(), v.end(), greater<int>())` 使用比較函式 `greater` 由大到小排序。", "vector<int> v = {3, 1, 2};\nsort(v.begin(), v.end(), greater<int>());\nfor (int x : v) cout << x << ' ';\ncout << endl;", "3 2 1"),
            cq("二維 `vector<vector<int>> g(2, vector<int>(3, 0));` 的 `g.size()` 與 `g[0].size()` 是？", "`2 3`", ["`3 2`", "`2 2`", "`6 6`"], "外層有 2 個元素（列），每個內層有 3 個元素（欄）。第一個參數是列數。", "vector<vector<int>> g(2, vector<int>(3, 0));\ncout << g.size() << \" \" << g[0].size() << endl;", "2 3"),
            Q("為什麼 CPE／競賽中常把大陣列（如 `int a[10000000]`）宣告成全域變數？", "區域陣列放在堆疊（通常約 8 MB 上限），太大會爆堆疊；全域陣列放在靜態區並自動初始化為 0", ["全域變數存取速度比區域變數快 100 倍", "區域陣列不能超過 100 個元素", "全域變數不需要 `#include`"], "40 MB 的區域陣列幾乎一定在進入函式時就 segmentation fault；全域或 `static` 或 `vector` 都沒這個問題。"),
            cq("執行後輸出什麼？", "`3 1`", ["`1 3`", "`4 1`", "`3 3`"], "`s.find` 回傳第一次出現的索引；找不到回傳 `string::npos`（一個很大的無號數，常用 `== string::npos` 判斷）。", "string s = \"abcabc\";\nint i = s.find(\"abc\", 1);\ncout << i << \" \" << s.find('b') << endl;", "3 1"),
        ]),
        dict(title="單元 7–8 模擬測驗：指標、參考與綜合", unit=8, questions=[
            cq("執行後輸出什麼？", "`7`", ["`5`", "指標的位址", "編譯錯誤"], "`p` 指向 x，`*p = 7` 透過指標改了 x 本身。", "int x = 5;\nint* p = &x;\n*p = 7;\ncout << x << endl;", "7"),
            cq("執行後輸出什麼？", "`9`", ["`5`", "`r` 的位址", "編譯錯誤"], "`int& r = x` 讓 r 成為 x 的別名，對 r 賦值就是對 x 賦值。", "int x = 5;\nint& r = x;\nr = 9;\ncout << x << endl;", "9"),
            cq("`int a[3] = {10, 20, 30}; int* p = a;` 之後輸出 `*(p + 2)` 與 `p[1]`？", "`30 20`", ["`20 10`", "`30 30`", "`12 21`"], "`p + 2` 前進兩個 int，指到 a[2] = 30；`p[1]` 等於 `*(p + 1)` = a[1] = 20。", "int a[3] = {10, 20, 30};\nint* p = a;\ncout << *(p + 2) << \" \" << p[1] << endl;", "30 20"),
            cq("`int a[2] = {1, 2}; int* p = a; p++;` 之後 `*p` 與 `p` 比 `a` 多的位元組數是？", "`2 4`", ["`1 1`", "`2 1`", "`1 4`"], "指標加 1 是前進『一個元素』= `sizeof(int)` = 4 位元組，所以指到 a[1]（值 2）。", "int a[2] = {1, 2};\nint* p = a;\np++;\ncout << *p << \" \" << (char*)p - (char*)a << endl;", "2 4"),
            cq("`int *a, b;` 之後 `sizeof(a)` 與 `sizeof(b)` 是？", "`84`（a 是指標 8 位元組，b 是 int 4 位元組）", ["`88`", "`44`", "`48`"], "`*` 只綁定在緊接著的變數上，所以只有 a 是指標，b 是普通 int。要兩個都是指標必須寫 `int *a, *b;`。", "int *a, b;\ncout << sizeof(a) << sizeof(b) << endl;", "84"),
            Q("`const int* p` 與 `int* const p` 的差別？", "前者不能透過 p 修改指到的值；後者 p 本身不能改指向別處", ["兩者完全相同", "前者 p 不能被改指向；後者不能修改指到的值", "兩者都表示 p 永遠是 nullptr"], "從右往左讀：`const int* p` 是『p 是指向 const int 的指標』；`int* const p` 是『p 是 const 的、指向 int 的指標』。"),
            Q("下列關於 `new` 與 `delete` 的敘述，何者正確？", "`new[]` 配置的要用 `delete[]` 釋放；忘了釋放會造成記憶體洩漏，重複釋放或配對錯誤是未定義行為", ["`delete` 可以釋放任何指標，包括區域變數的位址", "`new` 配置的記憶體離開作用域會自動釋放", "`delete` 之後指標會自動變成 `nullptr`"], "堆積上的物件不會隨作用域結束而釋放；現代 C++ 用 `vector`、`string`、智慧指標管理，避免手動 new/delete。"),
            Q("哪一種情況最可能造成『懸空指標』？", "指標指向已經離開作用域的區域變數，或指向已被 `delete` 的物件", ["指標被初始化成 `nullptr`", "指標指向全域變數", "指標指向 `static` 區域變數"], "被指的物件生命週期已結束，指標卻還在，使用它是未定義行為。解參考 `nullptr` 同樣危險，但它是『空』而不是『懸空』。"),
            cq("下列程式的輸出是？（綜合：傳參考、陣列、迴圈）", "`6`", ["`0`", "`3`", "`123`"], "`addAll` 以參考接收 `sum`，在迴圈中累加陣列元素 1+2+3 = 6，並修改呼叫端的 `sum`。", "int a[3] = {1, 2, 3};\nint sum = 0;\naddAll(a, 3, sum);\ncout << sum << endl;", "6", pre="void addAll(int* a, int n, int& s) { for (int i = 0; i < n; i++) s += a[i]; }"),
            Q("階段 C0 驗收題在 40 分鐘內做出兩題。下列哪個習慣最能避免時間浪費？", "先用題目範例與自己出的邊界資料測試，開 `-fsanitize=address,undefined` 抓執行期錯誤，再提交", ["寫完就直接提交，讓評測系統告訴你對不對", "只測題目範例", "先把程式最佳化到最快再測試"], "範例通常很弱；邊界（n=1、最大值、全相同）與 sanitizer 能在本機抓出多數 WA／RE，節省提交次數。"),
        ]),
    ],
)
