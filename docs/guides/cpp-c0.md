# C++ 基礎總整理與模擬測驗（階段 C0）

對應課程：C++ 軌道階段 C0（單元 1–8）。每一題「預測輸出」的程式都用 g++ -std=c++17 實際編譯、執行驗證過（64 位元 Linux；`sizeof` 等與平台有關的數字以此為準）。

## 一、這份指南怎麼用

每組重點後面接一組單選模擬題（四選一），最後附解答與解析。

1. 先讀重點，**每個例子自己編譯執行一遍**：`g++ -std=c++17 -O2 -Wall -Wextra main.cpp -o main && ./main`。
2. 預測輸出的題先自己推演（尤其是整數除法、型別提升、傳值與傳參考），再看選項。
3. 對照 Python 的差別特別留意：`/` 與 `%` 對負數、整數會溢位、陣列不檢查邊界。
4. 網頁的「指南」頁可以作答、計分、單獨重做錯題。

出題風格：四選一；誘答多是典型錯誤——整數除法當成浮點、傳值以為會修改、`size_t` 減法回繞、`cin >>` 後直接 `getline`、`substr` 的第二參數是長度。題目中的 `#include <bits/stdc++.h>` 是 GCC 才有的方便標頭，競程常用。

## 二、學習地圖

| 單元 | 週次 | 名稱 | 目標 |
| --- | --- | --- | --- |
| 1 | 1 | 工具鏈與第一個程式 | 能安裝編譯器，編譯並執行程式，看懂編譯錯誤與警告。 |
| 2 | 2 | 型別、變數與運算 | 懂整數大小與溢位、整數除法、浮點誤差、型別轉換。 |
| 3 | 3 | 輸入輸出與格式 | 穩定處理各種輸入格式（多組、EOF、含空白的整行），並精確控制輸出格式。 |
| 4 | 4–5 | 條件與迴圈 | 熟練 if／switch／for／while／do-while，能把需求翻成迴圈與條件。 |
| 5 | 6 | 函式、傳值與傳參考 | 會設計函式介面，懂傳值、傳參考、傳 const 參考的差別。 |
| 6 | 7–8 | 陣列、vector 與 string | 熟練一維與二維資料，知道越界的後果。 |
| 7 | 9 | 指標、參考與記憶體模型 | 懂 stack 與 heap、指標與參考、未定義行為，並會用工具抓錯。 |
| 8 | 10 | 階段 C0 驗收週 | 用 C++ 在時限內解出 Python 軌道階段 0–1 等級的題目，並通過 sanitizer。 |

## 三、單元 1–2：工具鏈、型別與運算

### 從原始碼到可執行檔
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
- `const`／`constexpr` 宣告常數；`auto` 讓編譯器推導型別。

## 四、單元 3：輸入輸出

| 工作 | 寫法 |
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
- `cout << 1e6` 預設會印成 `1e+06`；要整數格式就轉成 `long long`，或用 `fixed`。

## 五、單元 4：條件與迴圈

- `switch` 的 `case` 若沒有 `break` 會**直通（fall through）**到下一個 case。
- `if` 的 `else` 一律接到**最近**的未配對 `if`（dangling else）；一律加大括號。
- `&&`、`||` **短路求值**：`i != 0 && 10 / i > 1` 不會除以 0。
- `do { … } while (cond);` 至少執行一次。
- 無號數陷阱：`for (size_t i = n; i >= 0; --i)` 是無窮迴圈（無號數永遠 ≥ 0）；`unsigned u = 0; u--;` 得 4294967295。
- `while (n--)` 以舊值判斷再遞減：n = 3 時迴圈內 n 依序是 2、1、0。
- `break` 只跳出最內層迴圈。三元運算子 `a > b ? a : b`。
- 邊界：用半開區間 `[l, r)`，迴圈寫 `i < n`。

## 六、單元 5：函式、傳值與傳參考

| 傳遞方式 | 寫法 | 效果 |
| --- | --- | --- |
| 傳值 | `void f(int x)` | 複製一份，函式內修改**不影響**呼叫端 |
| 傳參考 | `void f(int& x)` | 別名，修改**影響**呼叫端 |
| 傳常數參考 | `void f(const string& s)` | 不複製、不能改；大型物件的預設選擇 |
| 傳指標 | `void f(int* p)` | 可修改指到的物件；可為 `nullptr` |

- 陣列當參數會**退化成指標**：函式內 `sizeof(a)` 是指標大小 8，不是陣列大小。
- `static` 區域變數只初始化一次，值在多次呼叫間保留。
- 預設引數、函式多載（同名不同參數）；函式必須**先宣告再使用**。
- 絕不要回傳區域變數的參考或指標（懸空）。
- 遞迴要有終止條件；深度太深會爆堆疊（約數萬到數十萬層，視每層大小）。

## 七、單元 6：陣列、vector 與 string

### 陣列
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
- 轉換：`to_string(12)`、`stoi("12")`。字串可用 `==`、`<` 比較（字典序）。

## 八、單元 7：指標、參考與記憶體模型

| 項目 | 說明 |
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
- 現代 C++ 優先用 `vector`、`string` 與智慧指標，少用原始 `new`／`delete`（單元 15）。

## 九、易混淆重點與必背速查表

### 最容易混淆的幾組
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
- 偵錯：`-fsanitize=address,undefined -g`。

## 十、單元 1–2 模擬測驗：工具鏈、型別與運算（共 12 題）

**1.** 編譯時出現 `undefined reference to 'foo()'`，這是哪一階段的錯誤、通常原因是？

- A. 前處理階段；`#include` 路徑錯誤
- B. 編譯階段；少了分號
- C. 連結階段；`foo()` 只有宣告、沒有（或沒連結到）定義
- D. 執行階段；記憶體不足

**2.** 下列哪一組編譯選項最適合開發時抓出越界與未定義行為？

- A. `-g -fsanitize=address,undefined -Wall -Wextra`
- B. `-s -w`
- C. `-O3 -ffast-math`
- D. `-E`

**3.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    cout << -7 / 2 << " " << -7 % 3 << endl;
}
```

- A. `-3 -1`
- B. `-4 -1`
- C. `-4 2`
- D. `-3 2`

**4.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    cout << (double)7 / 2 << endl;
}
```

- A. `3.0`
- B. `3.5`
- C. `4`
- D. `3`

**5.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    cout << 5 / 2 * 2.0 << endl;
}
```

- A. `4`
- B. `5`
- C. `5.0`
- D. `4.5`

**6.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    unsigned char c = 255;
    c++;
    cout << (int)c << endl;
}
```

- A. `0`
- B. `255`
- C. `256`
- D. `-1`

**7.** 在 64 位元 g++ 下，`sizeof(int)`、`sizeof(long long)`、`sizeof(char)` 依序是？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    cout << sizeof(int) << " " << sizeof(long long) << " " << sizeof(char) << endl;
}
```

- A. `8 8 2`
- B. `4 8 1`
- C. `2 4 1`
- D. `4 4 1`

**8.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    char c = 'A';
    cout << c + 1 << endl;
}
```

- A. `A1`
- B. `66`
- C. `B`
- D. `65`

**9.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int x = 3.9;
    cout << x << endl;
}
```

- A. `3.9`
- B. `3`
- C. 發生錯誤
- D. `4`

**10.** 要正確計算 `100000 * 100000` 並印出 `10000000000`，應該怎麼寫？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    long long y = 100000LL * 100000;
    cout << y << endl;
}
```

- A. `int y = 100000 * 100000;`
- B. `long long y = 100000 * 100000;`
- C. `long long y = 100000LL * 100000;`
- D. `double y = 100000 * 100000;`

**11.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    cout << boolalpha << (0.1 + 0.2 == 0.3) << endl;
}
```

- A. `0.3`
- B. `false`
- C. `1`
- D. `true`

**12.** `int a = 5; int b = a++;` 之後依序印出 `a`、`b`（連在一起），輸出是？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int a = 5;
    int b = a++;
    cout << a << b << endl;
}
```

- A. `65`（a 變成 6，b 拿到遞增前的 5）
- B. `66`
- C. `55`
- D. `56`（a 還是 5，b 變成 6）

### 單元 1–2 模擬測驗：工具鏈、型別與運算解答與解析

- **1. C**　編譯器只檢查宣告就放行；連結器找不到實際定義才報 undefined reference。常見原因：忘了寫定義、沒把 .cpp 一起編譯。
- **2. A**　Sanitizer 在執行時偵測越界、懸空與整數溢位等問題；`-Wall -Wextra` 開啟編譯期警告。`-O3` 只是最佳化，`-E` 只做前處理。
- **3. A**　C++ 的整數除法向 0 截斷（−3.5 → −3），`%` 的符號與被除數相同（−7 % 3 = −1）。與 Python 的 `-4`、`2` 不同——從 Python 轉過來最常錯在這裡。
- **4. B**　`(double)7` 先轉成 double，再除以 2，整個運算是浮點除法；`cout` 印 3.5。
- **5. A**　`5/2*2.0` 先做 `5/2`（整數除法 = 2），再 `2*2.0 = 4.0`，`cout` 印成 4。想要 5 就要寫 `5/2.0*2`。
- **6. A**　`unsigned char` 的最大值是 255，再加 1 回繞到 0（無號整數的溢位是有定義的）。有號整數溢位則是未定義行為。
- **7. B**　常見平台上 int 是 4 位元組、long long 是 8、char 恆為 1（`sizeof(char)` 由標準定義為 1）。
- **8. B**　`'A'` 在運算時被提升成 `int`（65），加 1 得到整數 66，`cout` 以整數印出；要印 `B` 必須轉回 `char`。
- **9. B**　把 double 指派給 int 會截斷小數（不是四捨五入）。使用大括號初始化 `int x{3.9}` 則會被編譯器擋下（縮窄轉換）。
- **10. C**　右邊如果兩個字面值都是 `int`，乘法在 `int` 上做，已經溢位（有號溢位是未定義行為，通常得到回繞值）才被轉成 long long。必須讓其中一個運算元是 long long。
- **11. B**　和 Python 一樣，0.1 + 0.2 在二進位浮點數中不精確，不等於 0.3。比較浮點數要用誤差。
- **12. A**　後置遞增 `a++` 的值是**遞增前**的 a，然後 a 才加 1。前置 `++a` 則是先加再取值。

## 十一、單元 3 模擬測驗：輸入輸出（共 8 題）

**1.** 先 `in >> n`（讀到 5），再 `getline(in, s)`，`s` 的內容是？（輸入為 `5\nhello world\n`）

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    istringstream in("5\nhello world\n");
    int n;
    in >> n;
    string s;
    getline(in, s);
    cout << "[" << s << "]" << endl;
}
```

- A. `[hello world]`
- B. `[5]`
- C. `[]`（`s` 是空字串，讀到的是 `5` 後面剩下的換行）
- D. `[hello]`

**2.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    cout << fixed << setprecision(2) << 3.14159 << endl;
}
```

- A. `3.1`
- B. `3.142`
- C. `3.14`
- D. `3.14159`

**3.** 執行 `printf("%5.1f|", 3.14159)` 輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    printf("%5.1f|\n", 3.14159);
}
```

- A. `3.1|`
- B. `  3.1|`
- C. `3.14159|`
- D. `3.1   |`

**4.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    cout << 'a' + 1 << endl;
}
```

- A. `b`
- B. `97`
- C. `98`
- D. `a1`

**5.** 以 `while (in >> x) sum += x;` 讀入 `1 2 3`，`sum` 最後是？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    istringstream in("1 2 3");
    int x, sum = 0;
    while (in >> x) sum += x;
    cout << sum << endl;
}
```

- A. `3`
- B. `6`
- C. `0`
- D. `123`

**6.** 執行後輸出什麼？（`|` 只是標記邊界）

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    cout << "|" << setw(5) << 42 << "|" << endl;
}
```

- A. `|00042|`
- B. `|42|`
- C. `|42   |`
- D. `|   42|`

**7.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    cout << 1000000.0 << endl;
}
```

- A. `1000000`
- B. `1e+06`
- C. `1000000.0`
- D. `1e6`

**8.** 競賽程式中加上 `ios::sync_with_stdio(false); cin.tie(nullptr);` 的主要目的與副作用是？

- A. 關閉所有緩衝區以便除錯
- B. 讓輸出自動排序；沒有副作用
- C. 讓程式自動處理 EOF；沒有副作用
- D. 加速 `cin`／`cout`；之後不能再混用 `scanf`／`printf`

### 單元 3 模擬測驗：輸入輸出解答與解析

- **1. C**　`>>` 不會吃掉數字後面的換行；`getline` 一讀就遇到這個換行，回傳空字串。解法：`getline(cin >> ws, s)` 或 `cin.ignore()`。
- **2. C**　`fixed` 固定用小數表示，`setprecision(2)` 在 fixed 下表示『小數點後 2 位』，並四捨五入。
- **3. B**　`%5.1f` 表示總寬度 5、小數 1 位，不足寬度時在左邊補空白。
- **4. C**　`'a' + 1` 的型別是 `int`，值為 98。若要輸出字元 `b`，需寫 `(char)('a' + 1)`。
- **5. B**　`in >> x` 讀取成功時條件為真；讀到結尾失敗後條件為假而結束。這是處理『不知道有幾筆』的標準寫法。
- **6. D**　`setw(5)` 設定下一個輸出的寬度為 5，預設靠右對齊，左邊補空白。
- **7. B**　double 預設以最短的科學記號或一般記號輸出（6 位有效數字）。需要整數格式：`(long long)1e6` 或 `fixed`。
- **8. D**　預設 C++ 串流與 C 的 stdio 同步，速度慢；關掉同步後速度大增，但兩套 I/O 的順序就不再保證一致。

## 十二、單元 4 模擬測驗：條件與迴圈（共 8 題）

**1.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int x = 1;
    switch (x) {
        case 1: cout << "A";
        case 2: cout << "B"; break;
        default: cout << "C";
    }
    cout << endl;
}
```

- A. `A`
- B. `B`
- C. `AB`
- D. `C`

**2.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    unsigned u = 0;
    u--;
    cout << u << endl;
}
```

- A. `65535`
- B. `0`
- C. `4294967295`
- D. `-1`

**3.** `int n = 3; while (n--) cout << n << ' ';` 輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n = 3;
    while (n--) cout << n << ' ';
    cout << endl;
}
```

- A. `2 1 `
- B. `3 2 1 `
- C. `2 1 0 `
- D. `3 2 1 0 `

**4.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int i = 10;
    do {
        cout << i;
    } while (i < 5);
    cout << endl;
}
```

- A. `1`
- B. `0`
- C. 什麼都不印
- D. `10`

**5.** 巢狀迴圈中，內層的 `break` 之後，外層迴圈會？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int cnt = 0;
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 5; j++) {
            if (j == 1) break;
            cnt++;
        }
    cout << cnt << endl;
}
```

- A. 程式立即結束
- B. 整個迴圈全部結束
- C. 照常繼續下一輪；總共印出 3 次
- D. 外層也跳過一輪

**6.** 下列 dangling else 的程式輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int a = 1, b = 0;
    if (a)
        if (b) cout << "A";
        else cout << "B";
    cout << endl;
}
```

- A. 什麼都不印（以為 `else` 屬於外層 `if`）
- B. `AB`
- C. `A`
- D. `B`（`else` 屬於內層 `if`；b 為 0，所以內層的 else 執行）

**7.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int i = 0;
    if (i != 0 && 10 / i > 1) cout << "called";
    else cout << "not-called";
    cout << endl;
}
```

- A. `not-called`
- B. 什麼都不印
- C. 發生除以零而當掉
- D. `called`

**8.** 計算 1 到 n 的總和（n = 100），下列哪個迴圈邊界是正確的，輸出？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n = 100, s = 0;
    for (int i = 1; i <= n; i++) s += i;
    cout << s << endl;
}
```

- A. `for (int i = 1; i <= n; i++)` → `5051`
- B. `for (int i = 1; i < n; i++)` → `5050`
- C. `for (int i = 0; i < n; i++)` → `5050`
- D. `for (int i = 1; i <= n; i++)` → `5050`

### 單元 4 模擬測驗：條件與迴圈解答與解析

- **1. C**　x = 1 進入 `case 1` 印 A；沒有 `break`，繼續直通 `case 2` 印 B，遇到 `break` 才離開。
- **2. C**　無號整數 0 減 1 回繞成最大值 2³²−1。這就是 `for (size_t i = n; i >= 0; --i)` 變成無窮迴圈的原因。
- **3. C**　`n--` 的值是舊值：判斷時 n = 3（真），然後 n 變 2 才進入迴圈主體，最後 n = 1 判斷為真、n 變 0 進入，下次判斷 0 為假而結束。
- **4. D**　`do-while` 先執行主體再判斷條件，所以即使條件一開始就為假，主體也會執行一次。
- **5. C**　`break` 只跳出『最內層』的迴圈。要一次跳出多層，用旗標、`return`，或把迴圈包進函式。
- **6. D**　`else` 一律接最近的未配對 `if`：這裡屬於 `if (b)`，b 為 0 所以印 B。縮排只是視覺提示，編譯器不看；加大括號才能明確表達意圖。
- **7. A**　`&&` 短路求值：左邊 `i != 0` 為假，整個運算式已確定為假，右邊的 `10 / i` 不會被計算，所以不會除以零。
- **8. D**　要包含 n 就用 `<=`；`i < n` 少加最後一個（得 4950），`i = 0` 起算也只多加 0 但少加 n。邊界錯是最常見的 WA 來源。

## 十三、單元 5 模擬測驗：函式、傳值與傳參考（共 8 題）

**1.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
void swap_by_value(int x, int y) { int t = x; x = y; y = t; }
int main() {
    int a = 1, b = 2;
    swap_by_value(a, b);
    cout << a << " " << b << endl;
}
```

- A. `1 1`
- B. `1 2`（傳值，沒有交換）
- C. `2 1`
- D. `2 2`

**2.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
void swap_by_ref(int& x, int& y) { int t = x; x = y; y = t; }
int main() {
    int a = 1, b = 2;
    swap_by_ref(a, b);
    cout << a << " " << b << endl;
}
```

- A. `2 2`
- B. `2 1`
- C. `1 1`
- D. `1 2`

**3.** 三次呼叫 `next()` 之後，最後一次的回傳值是？

```cpp
#include <bits/stdc++.h>
using namespace std;
int next() { static int c = 0; return ++c; }
int main() {
    next(); next();
    cout << next() << endl;
}
```

- A. `6`
- B. `1`
- C. `3`
- D. `0`

**4.** 在 main 與函式 `f(int a[10])` 中，各自印出 `sizeof(a)`（main 中是 `int a[10]`），結果是？

```cpp
#include <bits/stdc++.h>
using namespace std;
void f(int a[10]) { cout << sizeof(a); }
int main() {
    int a[10];
    cout << sizeof(a) << " ";
    f(a);
    cout << endl;
}
```

- A. `40 8`
- B. `40 40`
- C. `10 10`
- D. `8 8`

**5.** 參數是大型物件（如 `vector<int>`），且函式不需要修改它，最合適的宣告是？

- A. `void f(const vector<int>& v)`
- B. `void f(vector<int> v)`
- C. `void f(vector<int>* v)`
- D. `void f(vector<int>&& v)`

**6.** 函式 `int fact(int n)` 以遞迴計算 5!，輸出？

```cpp
#include <bits/stdc++.h>
using namespace std;
int fact(int n) { return n <= 1 ? 1 : n * fact(n - 1); }
int main() {
    cout << fact(5) << endl;
}
```

- A. `720`
- B. `5`
- C. `24`
- D. `120`

**7.** 為什麼不應該回傳區域變數的參考，例如 `int& f() { int x = 1; return x; }`？

- A. x 會自動被轉成全域變數
- B. 編譯器一定會報錯，所以不可能發生
- C. 只是效率較差，結果仍然正確
- D. 函式結束後 x 就被銷毀，回傳的參考指向無效記憶體（懸空），使用是未定義行為

**8.** 函式 `g()` 在 `main` 之後才定義，而 `main` 裡呼叫了 `g()`，會發生什麼？

- A. 執行時才會報錯
- B. 自動找到 g，沒有問題
- C. 連結時才會報錯
- D. 編譯錯誤：`g` 在使用時尚未宣告；需在 main 前加函式原型 `void g();`

### 單元 5 模擬測驗：函式、傳值與傳參考解答與解析

- **1. B**　傳值是複製一份參數，函式內交換的是複本，呼叫端的變數不變。
- **2. B**　參數是 `int&`，x、y 是呼叫端 a、b 的別名，交換直接作用在原變數。
- **3. C**　`static` 區域變數只初始化一次，值在多次呼叫之間保留，所以依序回傳 1、2、3。
- **4. A**　陣列當參數時退化成指標，函式內 `sizeof(a)` 是指標大小 8；在宣告它的作用域內 `sizeof` 才是整個陣列 40 位元組。
- **5. A**　`const&` 不複製（O(1)）也不允許修改；傳值會複製整個容器，在迴圈或遞迴中常造成 TLE。
- **6. D**　5! = 5×4×3×2×1 = 120；`n <= 1` 是終止條件，缺少它會無限遞迴直到堆疊爆掉。
- **7. D**　區域變數的生命週期只到函式結束；編譯器通常只給警告。這類錯誤會在特定情況下才爆發，很難除錯。
- **8. D**　C++ 由上而下編譯，使用前必須先看到宣告。原型宣告讓你把定義放在後面。

## 十四、單元 6 模擬測驗：陣列、vector 與 string（共 10 題）

**1.** `int a[5] = {1, 2};` 之後 `a[4]` 是多少？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int a[5] = {1, 2};
    cout << a[4] << endl;
}
```

- A. `2`
- B. `0`
- C. 編譯錯誤
- D. 隨機值

**2.** `vector<int> v(3, 7)` 之後印 `v.size()` 與 `v[2]`，輸出？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    vector<int> v(3, 7);
    cout << v.size() << v[2] << endl;
}
```

- A. `37`
- B. `27`
- C. `3`
- D. `73`

**3.** 空的 `vector<int> v`，`v.size() - 1` 的結果是？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    vector<int> v;
    cout << v.size() - 1 << endl;
}
```

- A. 執行時錯誤
- B. `0`
- C. `-1`
- D. `18446744073709551615`

**4.** 對 `vector<int> v(3)` 呼叫 `v.at(5)` 會？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    vector<int> v(3);
    try {
        v.at(5);
    } catch (const out_of_range&) {
        cout << "out_of_range" << endl;
    }
}
```

- A. 回傳隨機值
- B. 回傳 0
- C. 丟出 `out_of_range` 例外（被 catch 後印出）
- D. 靜默忽略

**5.** `string("hello").substr(1, 3)` 的結果是？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    cout << string("hello").substr(1, 3) << endl;
}
```

- A. `el`
- B. `ello`
- C. `ell`
- D. `hell`

**6.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    cout << to_string(12) + "3" << endl;
}
```

- A. `12 3`
- B. 發生錯誤
- C. `123`
- D. `15`

**7.** `vector<int> v = {3, 1, 2}`，依遞減排序後印出？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    vector<int> v = {3, 1, 2};
    sort(v.begin(), v.end(), greater<int>());
    for (int x : v) cout << x << ' ';
    cout << endl;
}
```

- A. `3 1 2`
- B. `3 2 1`
- C. `2 1 3`
- D. `1 2 3`

**8.** 二維 `vector<vector<int>> g(2, vector<int>(3, 0));` 的 `g.size()` 與 `g[0].size()` 是？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    vector<vector<int>> g(2, vector<int>(3, 0));
    cout << g.size() << " " << g[0].size() << endl;
}
```

- A. `3 2`
- B. `2 3`
- C. `6 6`
- D. `2 2`

**9.** 為什麼 CPE／競賽中常把大陣列（如 `int a[10000000]`）宣告成全域變數？

- A. 全域變數不需要 `#include`
- B. 區域陣列不能超過 100 個元素
- C. 全域變數存取速度比區域變數快 100 倍
- D. 區域陣列放在堆疊（通常約 8 MB 上限），太大會爆堆疊；全域陣列放在靜態區並自動初始化為 0

**10.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    string s = "abcabc";
    int i = s.find("abc", 1);
    cout << i << " " << s.find('b') << endl;
}
```

- A. `4 1`
- B. `3 3`
- C. `1 3`
- D. `3 1`

### 單元 6 模擬測驗：陣列、vector 與 string解答與解析

- **1. B**　大括號初始化時，沒有列出的元素會被值初始化為 0（即使是區域陣列）。完全不寫 `= {…}` 的區域陣列才是隨機值。
- **2. A**　`vector<int> v(3, 7)` 建立 3 個值為 7 的元素：size = 3，v[2] = 7，連著印成 37。
- **3. D**　`size()` 回傳無號的 `size_t`，0 − 1 回繞成 2⁶⁴ − 1。寫 `i < (int)v.size() - 1` 或 `i + 1 < v.size()` 避免。
- **4. C**　`v[5]` 不檢查邊界（未定義行為）；`v.at(5)` 會檢查並丟例外，偵錯時很有用。
- **5. C**　`substr(pos, len)` 的第二個參數是**長度**：從索引 1 起取 3 個字元 = ell。Python 切片 `[1:3]` 才是到結束索引。
- **6. C**　`to_string(12)` 得到字串 `"12"`，再串接 `"3"`。要做加法要用 `stoi`。
- **7. B**　`sort(v.begin(), v.end(), greater<int>())` 使用比較函式 `greater` 由大到小排序。
- **8. B**　外層有 2 個元素（列），每個內層有 3 個元素（欄）。第一個參數是列數。
- **9. D**　40 MB 的區域陣列幾乎一定在進入函式時就 segmentation fault；全域或 `static` 或 `vector` 都沒這個問題。
- **10. D**　`s.find` 回傳第一次出現的索引；找不到回傳 `string::npos`（一個很大的無號數，常用 `== string::npos` 判斷）。

## 十五、單元 7–8 模擬測驗：指標、參考與綜合（共 10 題）

**1.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int x = 5;
    int* p = &x;
    *p = 7;
    cout << x << endl;
}
```

- A. 編譯錯誤
- B. `7`
- C. 指標的位址
- D. `5`

**2.** 執行後輸出什麼？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int x = 5;
    int& r = x;
    r = 9;
    cout << x << endl;
}
```

- A. `9`
- B. `r` 的位址
- C. `5`
- D. 編譯錯誤

**3.** `int a[3] = {10, 20, 30}; int* p = a;` 之後輸出 `*(p + 2)` 與 `p[1]`？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int a[3] = {10, 20, 30};
    int* p = a;
    cout << *(p + 2) << " " << p[1] << endl;
}
```

- A. `30 30`
- B. `12 21`
- C. `20 10`
- D. `30 20`

**4.** `int a[2] = {1, 2}; int* p = a; p++;` 之後 `*p` 與 `p` 比 `a` 多的位元組數是？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int a[2] = {1, 2};
    int* p = a;
    p++;
    cout << *p << " " << (char*)p - (char*)a << endl;
}
```

- A. `2 1`
- B. `2 4`
- C. `1 1`
- D. `1 4`

**5.** `int *a, b;` 之後 `sizeof(a)` 與 `sizeof(b)` 是？

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    int *a, b;
    cout << sizeof(a) << sizeof(b) << endl;
}
```

- A. `48`
- B. `84`（a 是指標 8 位元組，b 是 int 4 位元組）
- C. `44`
- D. `88`

**6.** `const int* p` 與 `int* const p` 的差別？

- A. 兩者完全相同
- B. 前者 p 不能被改指向；後者不能修改指到的值
- C. 前者不能透過 p 修改指到的值；後者 p 本身不能改指向別處
- D. 兩者都表示 p 永遠是 nullptr

**7.** 下列關於 `new` 與 `delete` 的敘述，何者正確？

- A. `delete` 之後指標會自動變成 `nullptr`
- B. `new` 配置的記憶體離開作用域會自動釋放
- C. `delete` 可以釋放任何指標，包括區域變數的位址
- D. `new[]` 配置的要用 `delete[]` 釋放；忘了釋放會造成記憶體洩漏，重複釋放或配對錯誤是未定義行為

**8.** 哪一種情況最可能造成『懸空指標』？

- A. 指標指向已經離開作用域的區域變數，或指向已被 `delete` 的物件
- B. 指標被初始化成 `nullptr`
- C. 指標指向全域變數
- D. 指標指向 `static` 區域變數

**9.** 下列程式的輸出是？（綜合：傳參考、陣列、迴圈）

```cpp
#include <bits/stdc++.h>
using namespace std;
void addAll(int* a, int n, int& s) { for (int i = 0; i < n; i++) s += a[i]; }
int main() {
    int a[3] = {1, 2, 3};
    int sum = 0;
    addAll(a, 3, sum);
    cout << sum << endl;
}
```

- A. `6`
- B. `0`
- C. `123`
- D. `3`

**10.** 階段 C0 驗收題在 40 分鐘內做出兩題。下列哪個習慣最能避免時間浪費？

- A. 只測題目範例
- B. 寫完就直接提交，讓評測系統告訴你對不對
- C. 先把程式最佳化到最快再測試
- D. 先用題目範例與自己出的邊界資料測試，開 `-fsanitize=address,undefined` 抓執行期錯誤，再提交

### 單元 7–8 模擬測驗：指標、參考與綜合解答與解析

- **1. B**　`p` 指向 x，`*p = 7` 透過指標改了 x 本身。
- **2. A**　`int& r = x` 讓 r 成為 x 的別名，對 r 賦值就是對 x 賦值。
- **3. D**　`p + 2` 前進兩個 int，指到 a[2] = 30；`p[1]` 等於 `*(p + 1)` = a[1] = 20。
- **4. B**　指標加 1 是前進『一個元素』= `sizeof(int)` = 4 位元組，所以指到 a[1]（值 2）。
- **5. B**　`*` 只綁定在緊接著的變數上，所以只有 a 是指標，b 是普通 int。要兩個都是指標必須寫 `int *a, *b;`。
- **6. C**　從右往左讀：`const int* p` 是『p 是指向 const int 的指標』；`int* const p` 是『p 是 const 的、指向 int 的指標』。
- **7. D**　堆積上的物件不會隨作用域結束而釋放；現代 C++ 用 `vector`、`string`、智慧指標管理，避免手動 new/delete。
- **8. A**　被指的物件生命週期已結束，指標卻還在，使用它是未定義行為。解參考 `nullptr` 同樣危險，但它是『空』而不是『懸空』。
- **9. A**　`addAll` 以參考接收 `sum`，在迴圈中累加陣列元素 1+2+3 = 6，並修改呼叫端的 `sum`。
- **10. D**　範例通常很弱；邊界（n=1、最大值、全相同）與 sanitizer 能在本機抓出多數 WA／RE，節省提交次數。
