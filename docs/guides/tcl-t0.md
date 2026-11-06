# Tcl 語言總整理與模擬測驗（階段 T0）

對應課程：Tcl 軌道階段 T0（單元 1–8）。所有「預測輸出」題的答案都用 tclsh 實際執行驗證過。

## 一、這份指南怎麼用

每組重點後面接一組單選模擬題（四選一），最後附解答與解析。建議做法：

1. 先讀重點整理，**自己用 tclsh 把每個例子跑一遍**，不要只看。
2. 做題時遮住解析，答完再對。錯的題目回頭找對應的重點，並把「為什麼」寫成自己的話。
3. 預測輸出的題目，先在紙上寫出每一步的替換結果，再看選項。
4. 網頁的「學習指南測驗」可以作答、計分並記錄錯題。

出題風格（與階段驗收一致）：四選一；誘答多是典型錯誤——忘了替換只做一次、大括號與雙引號混用、把 Tcl 當成有關鍵字的語言、整數除法當成浮點除法。

## 二、學習地圖

| 單元 | 週次 | 名稱 | 目標 |
| --- | --- | --- | --- |
| 1 | 1 | 環境與第一支腳本 | 能執行 Tcl 腳本，並理解『一切皆指令』。 |
| 2 | 2 | 求值與替換規則 | 理解雙引號、大括號、方括號與反斜線的差別，並能預測求值結果。 |
| 3 | 3–4 | 控制流與 proc | 能寫出有分支、迴圈與函式的腳本，並理解變數範圍與引數傳遞。 |
| 4 | 5–6 | 清單、陣列與字典 | 能熟練選擇並操作 Tcl 三大資料結構。 |
| 5 | 7–8 | 字串、模式比對與正規表示式 | 能用 string、glob 與正規表示式處理文字，這是 EDA 報告解析的核心技能。 |
| 6 | 9 | 檔案、程序與命令列 | 能讀寫檔案、列出檔案、呼叫外部程式並取得輸出。 |
| 7 | 10 | 錯誤處理與除錯 | 能正確處理例外、讀懂錯誤追蹤並除錯。 |
| 8 | 11 | 階段 T0 驗收週 | 獨立完成一個有輸入驗證、錯誤處理與測試的文字處理工具。 |

## 三、單元 1–2：Tcl 的核心——一切都是指令、字串與替換

Tcl 的語法只有一條主規則：**一行是一個指令，第一個字是指令名稱，其餘的字是引數**。`if`、`while`、`proc` 都只是普通指令，沒有「關鍵字」。所有值在概念上都是字串（內部會快取數字或清單表示，但行為上等同字串）。

### 十二條規則（dodekalogue）的實用版

| 符號 | 作用 | 例 | 結果 |
| --- | --- | --- | --- |
| `空白／換行／;` | 分隔字與指令 | `set a 1; set b 2` | 兩個指令 |
| `"..."` | 分組，**內部仍做替換** | `"sum=[expr {1+2}]"` | `sum=3` |
| `{...}` | 分組，**內部完全不替換** | `{sum=[expr {1+2}]}` | 原樣字串 |
| `$name` | 變數替換 | `$a` | 變數的值 |
| `[cmd]` | 指令替換（先執行，把結果放回） | `[string length abc]` | `3` |
| `\` | 反斜線替換／續行 | `\t` `\n` `\$` | Tab、換行、字面 `$` |
| `#` | 註解——**只在指令開頭才算** | `# 註解`、`puts hi ;# 註解` | |

- **替換只做一次**，由左到右；替換的結果不會再被當成程式碼重新解析（除非你用 `eval`／`subst`）。
- 大括號可以巢狀，常用來傳遞「程式碼」給 `if`、`while`、`proc`、`expr`，讓那些指令自己決定何時、如何求值。
- **永遠寫 `expr {...}`**：大括號讓 `expr` 自己解析運算式，比較快，也避免二次替換造成的錯誤與注入。

### 常用基本指令

| 指令 | 用途 | 例 |
| --- | --- | --- |
| `set x 5` | 設定／讀取變數 | `set x`→ 5 |
| `puts ?-nonewline? str` | 輸出 | `puts -nonewline hi` |
| `expr {…}` | 數學／邏輯運算 | `expr {3 + 4}`→ 7 |
| `incr x ?n?` | 整數加法（變數不存在時視為 0） | `incr cnt` |
| `append s a b` | 字串附加 | |
| `unset x`、`info exists x` | 刪除、檢查變數 | |

### expr 必背
- 整數除法**向下取整**：`7/2 = 3`，`-7/2 = -4`；要小數就讓其中一個是浮點：`7/2.0 = 3.5`。
- `**` 是次方且**右結合**：`2**3**2 = 2**9 = 512`。
- 比較用 `==`、`!=`、`<`；字串相等可用 `eq`、`ne`（不會把 `1.0` 與 `1` 當成相等）。
- 註解陷阱：`puts hi # 註解` 會把 `#`、`註解` 當成多餘的引數而出錯；要寫成 `puts hi ;# 註解`。

## 四、單元 3：控制流與 proc

### 控制流（都是指令，所以大括號的位置有規定）

```tcl
if {$x > 3} {
    puts big
} elseif {$x > 1} {
    puts mid
} else {
    puts small
}
```

- `else`／`elseif` 必須和前一個 `}` **在同一行**，否則換行會結束指令，`else` 會被當成新指令。
- 條件和主體用大括號：條件才會在每次判斷時重新求值（`while`、`for` 尤其重要）。
- `for {init} {test} {next} {body}`、`while {test} {body}`、`foreach var list {body}`；`break`／`continue` 與一般語言相同。
- `foreach {k v} $list {...}`：一次取多個變數；多個清單可以並行走訪。
- `switch ?-exact|-glob|-regexp? $v {pattern body ...  default body}`：預設是 `-exact`。

### proc

| 寫法 | 說明 |
| --- | --- |
| `proc name {a b} {body}` | 基本定義 |
| `proc greet {n {g Hello}} {...}` | 有預設值的引數 |
| `proc f {first args} {...}` | `args` 收剩餘引數成清單 |
| `return value` | 回傳；沒有 `return` 時回傳**最後一個指令的結果** |
| `global x` | 在 proc 內使用全域變數 |

- **proc 有自己的區域作用域**：看不到全域變數，除非 `global` 或 `$::x`。
- 引數傳遞是「傳值」；想改呼叫端的變數，傳**變數名稱**，再用 `upvar`（單元 9 會細講）。
- 遞迴沒有特別語法，proc 直接呼叫自己即可。

## 五、單元 4：清單、陣列與字典

### 清單（list）——有序，以空白分隔的字串

| 指令 | 結果（以 `L = {a b c d}`） |
| --- | --- |
| `llength $L` | 4 |
| `lindex $L 1`、`lindex $L end`、`lindex $L end-1` | `b`、`d`、`c` |
| `lrange $L 1 2` | `b c` |
| `lappend L e` | 就地加在尾端（會改變變數） |
| `linsert $L 1 x` | `a x b c d`（回傳新清單） |
| `lreplace $L 1 2 X` | `a X d` |
| `lsearch $L c` | 2（找不到回 -1） |
| `lsort`、`lsort -integer`、`lsort -decreasing` | 預設是**字典序（字串）**，所以 `10` 排在 `9` 前面 |
| `lmap x $L {expr}` | 對每個元素求值並收集 |
| `lassign {1 2 3} x y` | 把前兩個指派給 x、y，**回傳剩下的** `3` |
| `split "a,b" ,`／`join $L -` | 字串 ⇄ 清單 |

- 含空白的元素要用 `list` 或大括號保護：`list a {b c}` → `a {b c}`，長度 2。
- 多個連續空白在清單裡視為一個分隔（`llength "a   b"` = 2），但 `split` 對每個分隔字元都切：`split "a,,b" ,` 得到 3 個元素（中間是空字串）。

### 陣列（array）與字典（dict）

| 比較 | array | dict |
| --- | --- | --- |
| 本質 | 變數的集合（不是值） | 一個值（鍵值清單） |
| 能不能整個傳給 proc／回傳 | 不能（要 `array get`／`upvar`） | 能 |
| 巢狀 | 不直接支援 | `dict set d a b 1` 可巢狀 |
| 讀取 | `$a(key)`；`array names a` | `dict get $d key`；`dict keys` |
| 不存在的鍵 | 讀取出錯 | `dict get` 出錯 `key "k" not known in dictionary`；用 `dict exists` 先查 |

- `puts $a`（a 是陣列）會出錯：`can't read "a": variable is array`。
- `dict for {k v} $d {...}` 走訪；`dict incr d k` 計數很方便；`dict get` 的順序是**插入順序**。

## 六、單元 5：字串、模式比對與正規表示式

### string 子指令速查

| 指令 | 例 | 結果 |
| --- | --- | --- |
| `string length` | `string length hello` | 5 |
| `string range s i j` | `string range hello 1 3` | `ell` |
| `string index`、`first`、`last` | `string first b abcb`／`last` | 1／3 |
| `string match glob s` | `string match h*o hello` | 1 |
| `string map {舊 新 …} s` | `string map {a 1 b 2} abcab` | `12c12` |
| `string trim`／`tolower`／`toupper`／`repeat` | `string repeat ab 3` | `ababab` |
| `string is integer -strict s` | `string is integer -strict abc` | 0 |
| `string compare a b` | | -1／0／1 |

### 三種「比對」不要混
1. **glob**（`string match`、`glob`、`switch -glob`）：`*` 任意長度、`?` 一個字元、`[abc]` 集合。
2. **regexp**（`regexp`、`regsub`）：完整正規表示式，大括號包住避免反斜線被先替換。
3. **精確**（`string equal`、`eq`）。

### regexp／regsub
- `regexp {(\d+)-(\d+)} $s all a b`：比對成功回傳 1，`all` 是整段，`a`、`b` 是括號擷取。
- `regexp -all -inline {\d+} "a1b22c333"` → `1 22 333`。
- 預設**貪婪**：`a.*b` 對 `aXbYb` 得 `aXbYb`；非貪婪 `a.*?b` 得 `aXb`。
- `regsub -all {\s+} $s " "` 把連續空白縮成一個；用 `\1` 引用括號、`&` 代表整段比對。

### format／scan
- `format "%5.2f|%-4d|%04d" 3.14159 7 42` → ` 3.14|7   |0042`（`-` 靠左、`0` 補零、`5.2f` 總寬 5 小數 2 位）。
- `scan "12 ab" "%d %s" n s` 回傳**成功轉換的個數**（這裡是 2），並把值放進 `n`、`s`。

## 七、單元 6–7：檔案、程序、命令列與錯誤處理

### 檔案與路徑

| 指令 | 說明 |
| --- | --- |
| `file join a b c.txt` | 組路徑（永遠用 `/`） → `a/b/c.txt` |
| `file tail`／`dirname`／`extension`／`rootname` | `/a/b/c.tar.gz` → `c.tar.gz`、`/a/b`、`.gz`、`/a/b/c.tar` |
| `file exists`、`file isdirectory`、`glob *.v` | 檢查、列出 |
| `set f [open path r\|w\|a]`、`gets $f line`、`puts $f str`、`read $f`、`close $f` | 讀寫；**`gets` 在檔尾回傳 -1** |

標準讀檔迴圈：`while {[gets $f line] >= 0} {...}`。`close` 之前寫入的資料可能還在緩衝區；沒關閉會漏資料並佔用檔案描述符。

### 外部程式與命令列
- `exec cmd args…` 回傳**標準輸出（去掉最後一個換行）**；若程式以非 0 結束，`exec` 會丟出錯誤 `child process exited abnormally`。
- `tclsh script.tcl a b`：`$argc` = 2、`$argv` = `{a b}`、`$argv0` = `script.tcl`。
- `exit n` 設定結束碼——用在回歸腳本讓 CI 能判斷成敗。

### 錯誤處理

| 工具 | 說明 |
| --- | --- |
| `catch {script} var` | 回傳 0（成功）或 1（錯誤）等代碼；結果或錯誤訊息放進 `var` |
| `error msg` | 丟出錯誤 |
| `try {…} on error {m} {…} finally {…}` | 8.6 起；`finally` 一定執行 |
| `throw {CLASS detail} msg` + `try … trap {CLASS detail}` | 依錯誤代碼分類處理 |
| `$::errorInfo` | 看出錯當下的呼叫堆疊 |

除錯小技巧：`puts stderr`、`info exists var`、`info commands`、`info body proc`、把可疑運算式拆開逐步印出。

## 八、易混淆重點與必背速查表

### 最容易混淆的幾組

| 容易搞錯 | 正確觀念 |
| --- | --- |
| `"..."` 與 `{...}` | 雙引號**仍替換**，大括號**完全不替換** |
| `expr $a+$b` 與 `expr {$a+$b}` | 後者才安全、快；前者會被 Tcl 先替換一次，`expr` 再解析一次 |
| `#` 註解 | 只在指令開頭有效；行尾註解要先寫 `;` |
| `else` 換行 | 會變成新指令 → `invalid command name "else"` |
| `7/2` 與 `7/2.0` | 3 與 3.5；負數向下取整（`-7/2 = -4`） |
| `lsort` 預設 | 字串字典序，數字要加 `-integer` |
| `array` 與 `dict` | array 不是值；dict 是值，可傳遞與巢狀 |
| `lassign` 的回傳 | 回傳**沒被指派的剩餘元素** |
| `exec` 非 0 結束 | 丟錯誤，要用 `catch` 或 `try` |
| proc 看不到全域變數 | 要 `global` 或 `$::x` |

### 必背速查
- 替換只做一次；要二次求值才用 `eval`／`subst`。
- 清單索引：`end`、`end-1`；範圍是**含兩端**（`lrange $L 1 2` 取第 1、2 個）。
- 檔案讀取迴圈 `gets` 回 -1 結束；`catch` 回 0 成功、1 錯誤。
- `format` 與 C 的 `printf` 幾乎一樣；`scan` 回傳轉換個數。

## 九、單元 1–2 模擬測驗：指令、替換、expr（共 12 題）

**1.** 下列關於 Tcl 語法的敘述，何者正確？

- A. 每個指令一定要用分號結尾，否則無法執行
- B. `if`、`while`、`proc` 都只是普通指令，第一個字是指令名稱，其餘是引數
- C. 引數的型別在呼叫前必須先宣告為整數或字串
- D. `if`、`while` 是語言保留的關鍵字，不能被覆寫或重新定義

**2.** 執行後輸出什麼？

```tcl
puts [expr {3 + 4}]
```

- A. 發生錯誤
- B. `3 + 4`
- C. `{3 + 4}`
- D. `7`

**3.** 執行後輸出什麼？

```tcl
set a 10
puts {a=$a}
```

- A. 發生錯誤：can't read "a"
- B. `a=`
- C. `a=$a`
- D. `a=10`

**4.** 執行後輸出什麼？

```tcl
set n [string length hello]
puts $n
```

- A. `hello`
- B. 發生錯誤
- C. `string length hello`
- D. `5`

**5.** 為什麼建議一律寫 `expr {$a + $b}`，而不是 `expr $a + $b`？

- A. 不加大括號 `expr` 就無法執行加法
- B. 大括號讓 `expr` 自己解析運算式：不會被先替換一次、執行較快，也避免含特殊字元的值造成錯誤或程式碼注入
- C. 大括號讓運算結果自動轉成整數，不寫就會得到字串
- D. 大括號是 Tcl 規定運算子一定要被括住

**6.** 執行後輸出什麼？

```tcl
puts "Total: [expr {2*3}] items"
```

- A. `Total:  items`
- B. `Total: [expr {2*3}] items`
- C. `Total: 2*3 items`
- D. `Total: 6 items`

**7.** 執行後輸出什麼？

```tcl
puts {a\tb}
```

- A. `a    b`（中間是 Tab）
- B. 發生錯誤
- C. `a\tb`（反斜線、t 兩個字元原樣印出）
- D. `atb`

**8.** `puts hi # 註解` 會怎樣？

```tcl
catch {puts hi # comment} err
puts $err
```

- A. 印出 `hi # 註解`
- B. 正常印出 `hi`，`#` 後面的內容被忽略
- C. 印出 `hi` 並在 stderr 顯示警告
- D. 出錯：`puts` 收到太多引數（wrong # args），因為 `#` 只有在指令開頭才算註解

**9.** 執行後輸出什麼？

```tcl
set s "x"
append s y z
puts $s
```

- A. `x`
- B. `xy`
- C. `xyz`
- D. `x y z`

**10.** 變數 `cnt` 尚未設定，執行 `incr cnt` 後 `puts $cnt` 會印出？

```tcl
unset -nocomplain cnt
incr cnt
puts $cnt
```

- A. 空字串
- B. `0`
- C. `1`
- D. 發生錯誤：can't read "cnt"

**11.** `puts [expr {-7/2}]` 輸出？

```tcl
puts [expr {-7/2}]
```

- A. `-3`
- B. `-4.0`
- C. `-3.5`
- D. `-4`

**12.** `puts [expr {2**3**2}]` 輸出？

```tcl
puts [expr {2**3**2}]
```

- A. `36`
- B. `64`
- C. `512`
- D. `8`

### 單元 1–2 模擬測驗：指令、替換、expr解答與解析

- **1. B**　Tcl 的語法只有『指令＋引數』這一條規則，控制結構也是指令，所以大括號的位置才會影響語意。換行或分號才是指令分隔，型別在 Tcl 中概念上都是字串。
- **2. D**　`[expr {3 + 4}]` 先被執行並以結果 7 取代，再交給 `puts`。
- **3. C**　大括號內完全不做替換，所以 `$a` 保持原樣。若改成雙引號才會得到 `a=10`。
- **4. D**　方括號內的 `string length hello` 先執行得到 5，再把 5 存進 n，最後 `puts $n` 印出 5。
- **5. B**　沒有大括號時，Tcl 會先對整個字串做一次替換，`expr` 再解析一次（二次求值）。值裡若含有 `[`、`$` 等字元，就可能被當成指令執行。
- **6. D**　雙引號內仍會做指令替換，所以 `[expr {2*3}]` 變成 6。
- **7. C**　大括號內不做反斜線替換，所以 `\t` 保持兩個字元。若寫成 `"a\tb"`（雙引號）才會得到 Tab。
- **8. D**　Tcl 的註解是一個『指令』，必須出現在指令開頭。行尾要加註解請先用分號結束指令：`puts hi ;# 註解`。
- **9. C**　`append` 可一次附加多個字串到變數尾端，不加分隔。
- **10. C**　自 Tcl 8.5 起，`incr` 對不存在的變數會當作 0 再加 1，並建立變數。
- **11. D**　兩個整數相除是整數除法，而且 Tcl 向下取整（往負無限大），所以 -3.5 變成 -4，不是 C 語言的 -3。要小數請寫 `-7/2.0`。
- **12. C**　`**` 是右結合：先算 3**2 = 9，再算 2**9 = 512。

## 十、單元 3 模擬測驗：控制流與 proc（共 11 題）

**1.** 下面的程式為什麼會出錯？

```tcl
if {1} {puts a}
else {puts b}
```

- A. `puts` 不能放在大括號裡
- B. 換行使 `if` 指令在第一行結束，下一行的 `else` 被當成新指令：`invalid command name "else"`
- C. `if` 的條件一定要用雙引號
- D. Tcl 沒有 `else`，只有 `elseif`

**2.** 執行後輸出什麼？

```tcl
for {set i 0} {$i < 3} {incr i} {puts -nonewline $i}
```

- A. `123`
- B. `3`
- C. `0 1 2`
- D. `012`

**3.** 執行後的輸出是？

```tcl
foreach {k v} {a 1 b 2} {puts "$k=$v"}
```

- A. 發生錯誤，`foreach` 一次只能取一個變數
- B. `a 1 b 2` 在同一行
- C. `a=1` 與 `b=2` 各一行
- D. 只印出第一組鍵值就結束

**4.** 執行後輸出什麼？

```tcl
proc add {a b} {return [expr {$a+$b}]}
puts [add 2 3]
```

- A. `2 3`
- B. 發生錯誤
- C. `23`
- D. `5`

**5.** 執行 `f` 的結果是？

```tcl
set x 10
proc f {} {puts $x}
f
```

- A. 出錯：`can't read "x": no such variable`
- B. 印出 `10`
- C. 印出 `x`
- D. 印出空字串

**6.** 執行後輸出什麼？

```tcl
proc greet {name {greeting Hello}} {puts "$greeting, $name"}
greet Ann
```

- A. 發生錯誤：wrong # args
- B. `, Ann`
- C. `Ann`
- D. `Hello, Ann`

**7.** `proc cnt args {llength $args}` 呼叫 `cnt a b c` 回傳？

```tcl
proc cnt args {llength $args}
puts [cnt a b c]
```

- A. `0`
- B. `1`
- C. `a b c`
- D. `3`

**8.** `proc f {} {set x 5}` 沒有寫 `return`，`puts [f]` 印出？

```tcl
proc f {} {set x 5}
puts [f]
```

- A. `0`
- B. `5`
- C. 發生錯誤
- D. 空字串

**9.** 執行後輸出什麼？

```tcl
foreach i {1 2 3 4} {
    if {$i == 3} break
    puts -nonewline "$i "
}
```

- A. `1 2 3 `
- B. `3 4 `
- C. `1 2 3 4 `
- D. `1 2 `（印出 1、2 後在 3 時 `break` 結束）

**10.** 執行後輸出什麼？

```tcl
proc fact n {
    if {$n <= 1} {return 1}
    expr {$n * [fact [expr {$n - 1}]]}
}
puts [fact 5]
```

- A. `5`
- B. `720`
- C. `120`
- D. `24`

**11.** 執行後輸出什麼？

```tcl
switch -glob foo.txt {
    *.tcl {puts tcl}
    *.txt {puts text}
    default {puts other}
}
```

- A. `tcl`
- B. `other`
- C. `text`
- D. `tcl` 與 `text` 兩者都印

### 單元 3 模擬測驗：控制流與 proc解答與解析

- **1. B**　`else` 必須和前一個 `}` 在同一行；否則 Tcl 以換行分隔指令，`else` 就成了不存在的指令。
- **2. D**　迴圈變數 i 從 0 跑到 2，`puts -nonewline` 不換行也不加空格，所以連成 012。
- **3. C**　`foreach {k v} list` 一次從清單取兩個元素，分別指派給 k 與 v。
- **4. D**　`add` 回傳 `expr {$a+$b}` 的結果 5。
- **5. A**　proc 有自己的區域作用域，看不到全域的 x。要用 `global x` 或 `$::x`。
- **6. D**　第二個引數 greeting 有預設值 Hello，只傳一個引數時就用預設值。
- **7. D**　名為 `args` 的最後一個參數會收集所有剩餘引數成清單；沒有 `return` 時 proc 回傳最後一個指令的結果。
- **8. B**　proc 的回傳值預設是最後一個執行的指令的結果，`set x 5` 的結果是 5。
- **9. D**　當 i 等於 3 時執行 `break`，立刻離開迴圈，所以 3 沒有被印出。
- **10. C**　5! = 5 × 4 × 3 × 2 × 1 = 120；proc 可以直接遞迴呼叫自己，`n<=1` 是終止條件。
- **11. C**　`-glob` 讓模式用萬用字元比對；`foo.txt` 符合 `*.txt`，第一個符合的分支執行後就結束（不會 fall through）。

## 十一、單元 4 模擬測驗：清單、陣列、字典（共 12 題）

**1.** `llength {a b {c d}}` 的結果？

```tcl
puts [llength {a b {c d}}]
```

- A. `4`
- B. `3`
- C. `2`
- D. `5`

**2.** `lindex {a b c} end-1` 的結果？

```tcl
puts [lindex {a b c} end-1]
```

- A. `b`
- B. `a`
- C. 發生錯誤
- D. `c`

**3.** `lrange {a b c d} 1 2` 的結果？

```tcl
puts [lrange {a b c d} 1 2]
```

- A. `a b c`
- B. `c`
- C. `b c d`
- D. `b c`

**4.** `lsort {10 9 100 1}`（不加選項）的結果？

```tcl
puts [lsort {10 9 100 1}]
```

- A. `1 9 10 100`
- B. `100 10 9 1`
- C. `9 10 100 1`
- D. `1 10 100 9`

**5.** `lsearch {a b c} z` 的結果？

```tcl
puts [lsearch {a b c} z]
```

- A. 空字串
- B. 發生錯誤
- C. `0`
- D. `-1`

**6.** `array set a {x 1}` 之後執行 `puts $a` 會？

```tcl
array set a {x 1}
puts $a
```

- A. 印出 `x 1`
- B. 印出 `1`
- C. 印出 `a`
- D. 出錯：`can't read "a": variable is array`

**7.** `dict get {a 1} z` 會？

```tcl
dict get {a 1} z
```

- A. 回傳 `0`
- B. 回傳空字串
- C. 回傳 `z`
- D. 出錯：`key "z" not known in dictionary`

**8.** 執行後輸出什麼？

```tcl
puts [lmap x {1 2 3} {expr {$x*$x}}]
```

- A. `1 2 3`
- B. `{1 4 9}`
- C. `14 9`
- D. `1 4 9`

**9.** `puts [linsert {a c} 1 b]` 的結果？

```tcl
puts [linsert {a c} 1 b]
```

- A. `b a c`
- B. `a b c`
- C. `a c b`
- D. `a b c` 且原清單被修改

**10.** `llength [split "a,b,,c" ,]` 的結果？

```tcl
puts [llength [split "a,b,,c" ,]]
```

- A. `3`
- B. `2`
- C. `4`
- D. `5`

**11.** `puts [lassign {1 2 3} x y]` 輸出？

```tcl
puts [lassign {1 2 3} x y]
```

- A. 空字串
- B. `2`
- C. `3`
- D. `1 2`

**12.** `llength "a   b"`（三個空白）的結果？

```tcl
puts [llength "a   b"]
```

- A. `1`
- B. `2`
- C. `3`
- D. `4`

### 單元 4 模擬測驗：清單、陣列、字典解答與解析

- **1. B**　大括號把 `c d` 包成同一個元素，所以元素是 `a`、`b`、`{c d}` 共 3 個。
- **2. A**　`end` 是最後一個，`end-1` 是倒數第二個。
- **3. D**　`lrange` 的範圍含兩端，索引 1 到 2 就是 `b c`。
- **4. D**　預設是字串字典序，`10` 的第一個字元 `1` 小於 `9`，所以 `9` 排最後。要數值排序請加 `-integer`。
- **5. D**　找不到時 `lsearch` 回傳 -1。
- **6. D**　陣列不是值，不能整個用 `$a` 讀取；要用 `array get a`、`$a(x)` 或 `array names a`。
- **7. D**　字典取不存在的鍵會丟錯誤；先用 `dict exists` 檢查，或用 `catch`。
- **8. D**　`lmap` 對每個元素求值並把結果收集成新清單。
- **9. B**　`linsert` 在索引 1 之前插入並**回傳新清單**，不會改變原變數。
- **10. C**　`split` 對每個分隔字元都切一刀，連續兩個逗號之間是一個空字串元素：a、b、空、c 共 4 個。
- **11. C**　`lassign` 把前面的元素指派給變數，**回傳沒被指派的剩餘元素**。
- **12. B**　把字串當清單時，連續空白視為一個分隔。對照 `split` 則是每個分隔字元都切。

## 十二、單元 5 模擬測驗：字串與正規表示式（共 12 題）

**1.** `string range hello 1 3` 的結果？

```tcl
puts [string range hello 1 3]
```

- A. `hel`
- B. `el`
- C. `ell`
- D. `ello`

**2.** `string match {h*o} hello` 的結果？

```tcl
puts [string match {h*o} hello]
```

- A. `hello`
- B. `0`
- C. `5`
- D. `1`

**3.** `string map {a 1 b 2} abcab` 的結果？

```tcl
puts [string map {a 1 b 2} abcab]
```

- A. `1b2c`
- B. `12c12`
- C. `abcab`
- D. `12c`

**4.** 執行後輸出什麼？

```tcl
regexp {(\d+)-(\d+)} "tel 12-345" all a b
puts "$a,$b"
```

- A. `tel 12-345,12`
- B. `12-345`
- C. `1,3`
- D. `12,345`

**5.** `puts [regsub -all {\s+} "a   b  c" " "]` 輸出？

```tcl
puts [regsub -all {\s+} "a   b  c" " "]
```

- A. `a   b  c`
- B. `a b c`
- C. `abc`
- D. `a b  c`

**6.** `puts [format "%5.2f|%-4d|%04d" 3.14159 7 42]` 輸出？

```tcl
puts [format "%5.2f|%-4d|%04d" 3.14159 7 42]
```

- A. ` 3.14|7   |0042`
- B. `3.14| 7  |0042`
- C. `3.14159|7|42`
- D. ` 3.14|   7|42`

**7.** `puts [string last b abcb]` 的結果？

```tcl
puts [string last b abcb]
```

- A. `3`
- B. `1`
- C. `2`
- D. `-1`

**8.** `puts [regexp -all -inline {\d+} "a1b22c333"]` 輸出？

```tcl
puts [regexp -all -inline {\d+} "a1b22c333"]
```

- A. `1 22 333`
- B. `122333`
- C. `1`
- D. `a1b22c333`

**9.** `puts [scan "12 ab" "%d %s" n s]` 輸出？

```tcl
puts [scan "12 ab" "%d %s" n s]
```

- A. `1`
- B. `0`
- C. `12 ab`
- D. `2`

**10.** `puts [string is integer -strict abc]` 輸出？

```tcl
puts [string is integer -strict abc]
```

- A. `false`
- B. `1`
- C. `0`
- D. 發生錯誤

**11.** `regexp {a.*?b} "aXbYb" m; puts $m` 輸出？

```tcl
regexp {a.*?b} "aXbYb" m
puts $m
```

- A. `ab`
- B. `a`
- C. `aXbYb`
- D. `aXb`

**12.** 為什麼正規表示式通常寫在大括號裡，例如 `regexp {\d+} $s`？

- A. 大括號讓反斜線保持原樣交給 `regexp`；若用雙引號，Tcl 會先處理反斜線替換
- B. 大括號可以讓正規表示式比對更快
- C. 大括號會讓比對變成不分大小寫
- D. `regexp` 規定模式一定要放在大括號內

### 單元 5 模擬測驗：字串與正規表示式解答與解析

- **1. C**　索引從 0 開始、含兩端：1 到 3 是 e、l、l。
- **2. D**　`string match` 用 glob 比對，`*` 代表任意長度，符合回傳 1。
- **3. B**　`string map` 把每個舊字串換成對應的新字串，一次掃描完成。
- **4. D**　兩組括號分別擷取 12 與 345，放進變數 a 與 b。
- **5. B**　`-all` 取代所有符合的連續空白為單一空格。
- **6. A**　`%5.2f` 總寬 5、小數 2 位（前面補一個空白）；`%-4d` 靠左寬 4；`%04d` 靠右寬 4 補零。
- **7. A**　`last` 找最後一次出現的位置，索引從 0 開始：a=0, b=1, c=2, b=3。
- **8. A**　`-all -inline` 回傳所有符合的子字串成清單。
- **9. D**　`scan` 回傳成功轉換的欄位數；值本身放在變數 n 與 s。
- **10. C**　`abc` 不是整數，所以回傳 0（布林值以 0／1 表示）。
- **11. D**　`*?` 是非貪婪量詞，取最短符合；貪婪的 `a.*b` 才會得到 `aXbYb`。
- **12. A**　雙引號中 `\d` 會先被 Tcl 當成反斜線序列處理，字元就變了；大括號把原始字元交給正規表示式引擎。

## 十三、單元 6–7 模擬測驗：檔案、程序與錯誤處理（共 12 題）

**1.** `file join a b c.txt` 的結果？

```tcl
puts [file join a b c.txt]
```

- A. `a\b\c.txt`（Windows 上）
- B. `a/b/c.txt`
- C. `abc.txt`
- D. `a b c.txt`

**2.** 寫入兩行再用 `while {[gets $f line] >= 0}` 計數，結果是？

```tcl
set f [open t.txt w]
puts $f line1
puts $f line2
close $f
set f [open t.txt r]
set n 0
while {[gets $f line] >= 0} {incr n}
close $f
puts $n
```

- A. `1`
- B. `3`
- C. `0`
- D. `2`

**3.** `file extension a.tar.gz` 與 `file rootname a.tar.gz` 分別是？

```tcl
puts "[file extension a.tar.gz] [file rootname a.tar.gz]"
```

- A. `.tar.gz` 與 `a`
- B. `.gz` 與 `a`
- C. `.gz` 與 `a.tar`
- D. `gz` 與 `a.tar`

**4.** `puts [string length [exec echo hi]]` 輸出？

```tcl
puts [string length [exec echo hi]]
```

- A. `0`
- B. `2`
- C. `4`
- D. `3`

**5.** `exec` 執行的程式以非 0 結束碼結束時會？

```tcl
puts [catch {exec false} e]
puts $e
```

- A. 丟出錯誤（如 `child process exited abnormally`），要用 `catch` 或 `try` 處理
- B. 靜默忽略，回傳空字串
- C. 直接結束整個 Tcl 程式
- D. 回傳結束碼數字

**6.** `puts [catch {error boom} e]; puts $e` 依序輸出？

```tcl
puts [catch {error boom} e]
puts $e
```

- A. `1` 與 `boom`
- B. `1` 與空字串
- C. `boom` 與 `1`
- D. `0` 與 `boom`

**7.** `catch {expr {1/0}} e` 之後 `puts $e` 輸出？

```tcl
catch {expr {1/0}} e
puts $e
```

- A. `0`
- B. 空字串
- C. `inf`
- D. `divide by zero`

**8.** 執行後輸出什麼？

```tcl
try {error x} on error {m} {puts caught:$m} finally {puts done}
```

- A. 只有 `done`
- B. `caught:x` 然後 `done`
- C. `done` 然後 `caught:x`
- D. 只有 `caught:x`

**9.** 執行後輸出什麼？

```tcl
try {throw {MY ERR} oops} trap {MY ERR} {m} {puts "trapped $m"}
```

- A. 沒有輸出，錯誤被丟出
- B. `MY ERR oops`
- C. `oops`
- D. `trapped oops`

**10.** 執行 `tclsh run.tcl a b` 時，腳本內的 `$argc` 與 `$argv` 是？

- A. `2` 與 `{run.tcl a}`
- B. `2` 與 `{a b}`（不含腳本名稱）
- C. `3` 與 `{run.tcl a b}`
- D. `1` 與 `a`

**11.** 為什麼寫檔後一定要 `close`？

- A. 因為 Tcl 的檔案只能開啟一次
- B. 沒有 `close` 檔案就無法被其他程式刪除
- C. `close` 會自動幫檔案加上換行
- D. 關閉時才保證緩衝區的資料寫入檔案，並釋放檔案描述符

**12.** `puts [info exists nosuch]` 輸出？

```tcl
puts [info exists nosuch]
```

- A. 空字串
- B. 發生錯誤
- C. `1`
- D. `0`

### 單元 6–7 模擬測驗：檔案、程序與錯誤處理解答與解析

- **1. B**　`file join` 一律使用正斜線 `/` 組路徑，Tcl 在各平台都接受。
- **2. D**　`gets` 讀到檔尾回傳 -1 結束迴圈；兩行各讀一次，計數 2。
- **3. C**　副檔名只算最後一個點之後；rootname 是去掉副檔名後的部分。
- **4. B**　`exec` 回傳標準輸出並**去掉最後的換行**，所以 `hi` 長度是 2。
- **5. A**　這個設計讓回歸腳本不會漏看失敗；要容忍失敗就包 `catch`。
- **6. A**　`error` 丟出錯誤，`catch` 回傳 1，訊息放進 `e`。
- **7. D**　整數除以零在 Tcl 是錯誤，訊息為 `divide by zero`。
- **8. B**　`on error` 處理錯誤，`finally` 無論成敗都在最後執行。
- **9. D**　`throw` 丟出帶錯誤代碼 `{MY ERR}` 的錯誤，`trap {MY ERR}` 依代碼前綴比對並處理。
- **10. B**　腳本名稱放在 `$argv0`，`$argv` 只含後面的參數。
- **11. D**　未關閉的檔案可能漏資料，開太多還會耗盡檔案描述符；用 `try … finally { close $f }` 確保一定關閉。
- **12. D**　`info exists` 檢查變數是否存在，不存在回 0，且不會出錯。

## 十四、綜合模擬測驗（階段 T0 驗收風格）（共 10 題）

**1.** `puts [list a {b c}]` 輸出？

```tcl
puts [list a {b c}]
```

- A. `a b c`
- B. `a {b c}`
- C. `a {{b c}}`
- D. `{a} {b c}`

**2.** `puts [expr {1 + 2 * 3 ** 2}]` 輸出？

```tcl
puts [expr {1 + 2 * 3 ** 2}]
```

- A. `27`
- B. `15`
- C. `19`
- D. `81`

**3.** `set x(1) 5; puts $x(1)` 輸出？

```tcl
set x(1) 5
puts $x(1)
```

- A. 發生錯誤
- B. 空字串
- C. `x(1)`
- D. `5`

**4.** `puts [expr {"abc" < "abd"}]` 輸出？

```tcl
puts [expr {"abc" < "abd"}]
```

- A. `abc`
- B. `0`
- C. 發生錯誤
- D. `1`

**5.** 執行後輸出什麼？

```tcl
set cmd {puts hi}
eval $cmd
```

- A. `hi`
- B. `$cmd`
- C. 發生錯誤
- D. `puts hi`

**6.** 要在 proc 內修改呼叫端的某個變數，最合適的做法是？

- A. 傳入變數名稱，在 proc 內用 `upvar` 連結到呼叫端的變數
- B. 在 proc 內 `set` 同名變數，它會自動影響呼叫端
- C. 把變數寫成 `$x` 傳進去，proc 直接修改參數
- D. Tcl 無法做到這件事

**7.** 以下哪一個不是 Tcl 的「值」而是「變數的集合」？

- A. 字串
- B. `dict`
- C. `array`
- D. `list`

**8.** 寫 `while {$i < 10} {...}` 時條件為什麼要放在大括號裡？

- A. 讓條件在每次迴圈判斷時重新求值；若用 `"$i < 10"` 或不加大括號，替換只在進入時做一次，條件永遠不變
- B. 大括號讓迴圈執行得比較快但語意相同
- C. 雙引號會使迴圈執行兩次
- D. 這只是慣例，不加也一樣

**9.** 下列哪一段最能讓 CI 偵測到回歸腳本失敗？

- A. 腳本偵測到失敗時 `exit 1`（非 0），讓呼叫它的 shell 看到失敗
- B. 用 `catch` 吞掉所有錯誤
- C. 只把錯誤訊息 `puts` 出來
- D. 把結果寫進檔案，不改變結束碼

**10.** `lsort -integer {10 9 100 1}` 與預設 `lsort` 的差別是？

```tcl
puts [lsort -integer {10 9 100 1}]
```

- A. 前者按數值排序得 `1 9 10 100`，後者按字串字典序得 `1 10 100 9`
- B. 兩者結果相同
- C. 前者回傳降冪排序
- D. 前者較慢，但結果相同

### 綜合模擬測驗（階段 T0 驗收風格）解答與解析

- **1. B**　`list` 會替含空白的元素加上大括號保護，輸出能再被當成兩個元素的清單。
- **2. C**　次方最先：3**2=9；再乘：2×9=18；最後加 1 得 19。
- **3. D**　`x(1)` 是陣列 x 的元素；`$x(1)` 取它的值。
- **4. D**　`expr` 的比較運算子遇到非數字字串時按字典序比較，abc 小於 abd。
- **5. A**　`eval` 把字串當成程式碼再求值一次；這是少數會「二次求值」的場合，使用者輸入絕不要直接 `eval`。
- **6. A**　引數是傳值，修改參數不影響呼叫端。傳名稱＋`upvar` 是 Tcl 的傳參考做法（`upvar 1 $name local`）。
- **7. C**　array 不能整個傳遞或回傳；list、dict 都是值。
- **8. A**　`while` 是指令，條件字串在呼叫前會被替換一次；大括號阻止替換，讓 `while` 自己每次重新求值。
- **9. A**　CI 靠程序的結束碼判斷成敗；只印訊息不會被 CI 視為失敗。
- **10. A**　資料是數字時務必指定 `-integer`（或 `-real`），否則會得到字典序。
