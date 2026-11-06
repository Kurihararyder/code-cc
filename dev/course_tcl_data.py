"""Tcl 軌道：從零基礎到能寫 EDA 流程腳本與自動化工具的工程師。4 個階段、27 個單元。

為什麼要學 Tcl：商用與開源 EDA 工具（合成、時序分析、擺置繞線）幾乎都用 Tcl 當腳本與設定語言；SDC 時序約束檔本身就是 Tcl；
FPGA 廠商工具（例如 Vivado）也以 Tcl 操作。學校課程常常不教，學生到公司才第一次接觸。
可自動判題（tclsh 比對輸出）的是語言本身與文字處理；商用 EDA 工具的指令（Design Compiler、PrimeTime、Innovus、Vivado）需要授權，只能用開源工具（OpenSTA、OpenROAD、Yosys）練習同樣的寫法，並以人工驗收。
"""
from course_hdl_data import R, U_, PL, PRJ, PLG  # noqa: F401

UNITS = []


def U(*a, **k):
    UNITS.append(U_(*a, **k))


# ============================ T0：Tcl 語言（第 1–11 週）============================
U(0, 1, "環境與第一支腳本", "能執行 Tcl 腳本，並理解『一切皆指令』。",
  ["執行方式：互動式 `tclsh`、執行檔案 `tclsh script.tcl`、在 EDA 工具內（例如 `yosys -c`、OpenSTA、OpenROAD 的 Tcl 殼層）；`source` 載入檔案",
   "語法只有一條規則：指令 = 字（word）的清單，第一個字是指令名稱，其餘是引數；沒有關鍵字、沒有運算子——`if`、`while` 都是指令",
   "`puts`、`set`、`unset`、`incr`；變數沒有宣告與型別，值本質上是字串（『一切皆字串』，內部有型別快取）",
   "註解：`#` 只在『指令開頭』才是註解；行尾註解要寫成 `; #`"],
  planned=[PL("t001", "Hello 與變數", "讀一行輸入，印出問候與字元數"), PL("t002", "行尾註解陷阱", "找出給定腳本中因註解寫法而錯誤的行並修好")],
  build=["在自己的電腦裝好 tclsh（版本 8.6）；寫 5 個小腳本；用 `info patchlevel` 與 `info commands` 看看有多少內建指令"],
  readings=[R.tcltut("0–3", ["Tcl 的基本語法、如何執行腳本、輸出與變數賦值"]),
            R.tclman("puts、set、unset、incr、source、exit", ["逐條查手冊：每個指令的語法列、選項與回傳值"])],
  pitfalls=["把 Tcl 當成有關鍵字的語言", "行尾直接寫 `# 註解` 造成多餘的引數錯誤"],
  check=["`set a 5` 是『陳述式』還是『指令』？差別在哪？", "為什麼 `puts hello world` 會出錯？"],
  gate=PLG(["t001"], 20, 1))

U(0, 1, "求值與替換規則", "理解雙引號、大括號、方括號與反斜線的差別，並能預測求值結果。",
  ["替換（substitution）：變數替換 `$x`、指令替換 `[cmd]`、反斜線替換；『只做一次』是關鍵：一條指令被切成字後，每個字只被替換一次",
   "三種分組：`\"…\"`（允許替換）、`{…}`（不替換，除了行尾反斜線）、`[…]`（指令替換）；巢狀大括號會配對",
   "`expr`：自成一種小語言，**要用大括號包住運算式**（`expr {$a + $b}`）才安全且快（避免二次替換與注入）",
   "數字：整數與浮點、整數除法（`7/2` 是 3，`7/2.0` 是 3.5）、進位制（`0x`、`0b`、`0o`）、精度與溢位（Tcl 整數是任意精度）、`1.0 * 3 == 3.0` 的比較"],
  planned=[PL("t003", "預測輸出", "給 15 段含引號、大括號、方括號的腳本，預測 puts 的結果（對拍 tclsh）"), PL("t004", "expr 注入", "找出不安全的 expr 寫法並改成大括號版本")],
  build=["製作一張『替換規則速查表』：每種引號的行為各 3 個例子；寫一個函式把任意字串安全地放進指令中（提示：`list`、`format`、`subst -nocommands`）"],
  readings=[R.tcltut("4–8", ["三種分組與替換、`expr` 與數字"]),
            R.tclman("expr、subst、format、list、mathop", ["`expr` 的運算子優先序；`subst` 的旗標；`list` 如何正確引用元素"])],
  pitfalls=["沒有用大括號包住 `expr` 的運算式（慢、可被注入）", "以為大括號內的 `$x` 會被替換"],
  check=["`set x 5; puts \"$x\"; puts {$x}; puts [set x]` 各印什麼？", "為什麼 `expr {$a}` 比 `expr $a` 好？"],
  gate=PLG(["t003", "t004"], 30, 2))

U(0, 2, "控制流與 proc", "能寫出有分支、迴圈與函式的腳本，並理解變數範圍與引數傳遞。",
  ["`if`／`elseif`／`else`（條件是 `expr` 運算式，要用大括號）；`switch`（精確比對、`-glob`、`-regexp`、`--` 的用途）；`while`、`for`、`foreach`（多個變數、多個清單）、`break`／`continue`",
   "`proc`：預設引數、可變引數 `args`、回傳值（`return` 或最後一個指令的結果）；引數**傳值**，要修改呼叫端的變數用 `upvar`；`global` 與 `variable`",
   "範圍：每個 proc 有自己的區域變數；`uplevel` 與 `upvar` 的層級（`1`、`#0`）；遞迴與遞迴深度限制（`interp recursionlimit`）",
   "指令的回傳碼（ok／error／return／break／continue）：控制流指令其實就是靠回傳碼運作"],
  planned=[PL("t005", "費氏與質數", "用 proc、迴圈與遞迴各寫一遍"), PL("t006", "swap 與 upvar", "用 upvar 實作交換兩個呼叫端變數的 proc"), PL("t007", "自訂控制結構", "用 uplevel 實作 `repeat N {body}`")],
  build=["實作 `lmax`、`lsum`、`repeat`、`unless`（皆為 proc），附 15 個以上的測試（用 `if` 與 `puts` 的簡單測試框架，之後換 tcltest）"],
  readings=[R.tcltut("9–15", ["if／switch／while／for／proc 與變數範圍"]),
            R.tclman("if、switch、while、for、foreach、break、continue、proc、return、global、variable、upvar、uplevel", ["各指令的語法與回傳碼語意"])],
  pitfalls=["`if {…} else` 的 `else` 與大括號必須在同一行（否則被當成新指令）", "忘了 `foreach` 可以同時迭代多個清單"],
  check=["為什麼 Tcl 的 `if` 條件要寫成 `{$x > 3}`？", "`upvar 1 name local` 做了什麼？"],
  gate=PLG(["t005", "t006", "t007"], 45, 2))

U(0, 2, "清單、陣列與字典", "能熟練選擇並操作 Tcl 三大資料結構。",
  ["清單（list）：`list`、`lindex`、`lrange`、`lappend`、`linsert`、`lreplace`、`lsearch`（`-exact`／`-glob`／`-regexp`／`-all`／`-inline`）、`lsort`（`-integer`／`-dictionary`／`-command`／`-unique`）、`lreverse`、`llength`、`lassign`、`lmap`、`lrepeat`、`join`／`split`、`concat`",
   "清單與字串的關係：清單是『符合引用規則的字串』；用 `list` 與 `lappend` 建立，不要自己拼字串",
   "陣列（array）：關聯陣列，鍵是字串；`array set`／`array get`／`array names`／`array exists`；陣列不是值（不能直接傳遞）；`parray`",
   "字典（dict）：有值語意的關聯容器：`dict create`／`dict get`／`dict set`／`dict exists`／`dict for`／`dict map`／`dict update`／`dict merge`／`dict incr`；巢狀字典；與陣列的取捨"],
  planned=[PL("t008", "詞頻統計", "讀入文字，輸出依頻率排序的詞表"), PL("t009", "矩陣與轉置", "用巢狀清單實作矩陣乘法與轉置"), PL("t010", "字典分組", "把記錄依欄位分組並彙總（用巢狀 dict）"), PL("t011", "清單操作大全", "10 個小題逐一使用 lsearch／lsort／lmap／lassign")],
  build=["實作一個『記錄表』工具：讀入 CSV 風格資料，用 dict 儲存，支援篩選、排序、分組彙總、輸出對齊表格"],
  readings=[R.tcltut("16–18、26–28", ["清單、清單操作、陣列、字典"]),
            R.tclman("list、lindex、lrange、lappend、linsert、lreplace、lsearch、lsort、lreverse、llength、lassign、lmap、lrepeat、join、split、concat、array、dict", ["每個指令的所有子命令與旗標"])],
  pitfalls=["用字串操作取代清單操作，遇到空白或特殊字元就壞掉", "把陣列當成值傳進 proc"],
  check=["`lsort -integer`、`-dictionary`、預設各自如何比較 `10 9 a B`？", "什麼時候用 dict、什麼時候用 array？"],
  gate=PLG(["t008", "t009", "t010", "t011"], 60, 3))

U(0, 2, "字串、模式比對與正規表示式", "能用 string、glob 與正規表示式處理文字，這是 EDA 報告解析的核心技能。",
  ["`string` 子命令：`length`、`index`、`range`、`first`／`last`、`compare`／`equal`、`match`（glob）、`map`、`trim`／`trimleft`／`trimright`、`tolower`／`toupper`、`repeat`、`reverse`、`is`（`integer`、`double`、`alpha` 等）",
   "glob 樣式（`*`、`?`、`[…]`）與 `string match`；`switch -glob`",
   "`regexp`：`-nocase`、`-all`、`-inline`、`-indices`、`-start`；子匹配變數；`regsub`（`-all`、反向參考 `\\1`、`&`）；Tcl 的 ARE 語法（支援 `\\d`、非貪婪 `*?`、`(?i)`）",
   "`format` 與 `scan`：C 風格格式化與解析；對齊輸出表格；格式化浮點數"],
  planned=[PL("t012", "日誌解析", "從日誌行抽出時間戳、等級、訊息，輸出統計"), PL("t013", "regsub 改寫", "把舊格式的設定檔轉成新格式（用 regsub -all 與反向參考）"), PL("t014", "格式化報表", "用 format 輸出對齊的表格，數字右對齊、小數 2 位"), PL("t015", "scan 解析", "用 scan 解析固定格式的行")],
  build=["寫一個通用的 `parse_report` proc：以正規表示式清單與欄位名稱對應，從文字報告中抽出數值，回傳 dict 的清單；用 3 種不同格式的假報告測試"],
  readings=[R.tcltut("19–25", ["glob、string 子命令、`format`、正規表示式 101／102"]),
            R.tclman("string、regexp、regsub、format、scan、switch", ["`regexp` 的所有旗標；`string` 的所有子命令；`format` 與 `scan` 的轉換說明"])],
  pitfalls=["在 Tcl 正規表示式中忘了反斜線在雙引號與大括號內的差別（要把樣式放在大括號內）", "貪婪比對吃掉太多"],
  check=["為什麼正規表示式樣式通常寫在大括號內？", "`regexp -inline -all` 回傳什麼結構？"],
  gate=PLG(["t012", "t013", "t014"], 60, 2))

U(0, 1, "檔案、程序與命令列", "能讀寫檔案、列出檔案、呼叫外部程式並取得輸出。",
  ["`open`／`close`／`gets`／`read`／`puts -nonewline`／`eof`／`flush`；模式 `r`／`w`／`a`／`r+`；`fconfigure`（編碼、緩衝）；用 `try … finally` 確保 `close`",
   "`file`：`exists`、`isdirectory`、`join`、`dirname`、`tail`、`rootname`、`extension`、`normalize`、`mkdir`、`delete`、`copy`、`rename`、`size`、`mtime`；`glob`（`-nocomplain`、`-directory`、`-types`）；`cd`／`pwd`",
   "外部程式：`exec`（回傳標準輸出；非零結束碼會丟例外，要用 `catch`；`2>@1` 合併 stderr）；`open |cmd r` 以管線串流讀取；環境變數 `env(NAME)`；命令列 `argc`／`argv`／`argv0`",
   "跨平台：路徑用 `file join`、不要手拼斜線；換行符號與編碼"],
  planned=[PL("t016", "檔案統計", "遞迴列出目錄下特定副檔名的檔案，統計行數"), PL("t017", "呼叫外部程式", "以 exec 呼叫 iverilog 編譯並擷取警告數量（可用假程式替代）")],
  build=["寫一個命令列工具：`filestat.tcl dir -ext .v -top 10`，以 argv 解析參數，輸出最長的 10 個檔案；錯誤時給出清楚訊息並以非零碼結束"],
  readings=[R.tcltut("29–31、40、43", ["檔案存取、檔案資訊、exec 與 open 管線、cd／pwd、命令列引數與環境變數"]),
            R.tclman("open、close、gets、read、eof、flush、fconfigure、file、glob、cd、pwd、exec", ["`exec` 的行為細節與重導向語法；`glob` 的選項"])],
  pitfalls=["`exec` 在命令列印出到 stderr 就丟例外", "沒關檔案造成資源耗盡"],
  check=["`exec` 什麼時候會丟例外？怎麼取得結束碼？", "為什麼用 `file join` 而不是字串拼接？"],
  gate=PLG(["t016", "t017"], 40, 1))

U(0, 1, "錯誤處理與除錯", "能正確處理例外、讀懂錯誤追蹤並除錯。",
  ["`catch`（回傳碼與結果、`-errorinfo` 變數）；`error`（訊息、info、code）；`return -code`；`try`／`on`／`trap`／`finally`（8.6）與 `throw`",
   "`errorInfo` 與 `errorCode`：讀堆疊追蹤；自訂錯誤碼與用 `trap` 分類處理",
   "除錯：`puts` 偵錯、`info` 內省（`info exists`／`info commands`／`info procs`／`info args`／`info body`／`info level`）、`trace`（變數追蹤與指令追蹤）、`time` 量時間",
   "防禦式寫作：驗證輸入（`string is`）、為 proc 的前置條件寫檢查、錯誤訊息要說明哪個值、期望什麼"],
  planned=[PL("t018", "錯誤分類", "解析給定腳本的錯誤輸出並回報類別與位置"), PL("t019", "安全的資源處理", "確保任何錯誤下檔案都被關閉（用 try／finally）")],
  build=["替前面的工具加上完整的錯誤處理：輸入驗證、自訂錯誤碼、`trap` 分類、統一的錯誤輸出格式與結束碼；寫 10 個故意壞掉的輸入測試"],
  readings=[R.tcltut("41、42、44", ["除錯與錯誤、trace、catch／error／return"]),
            R.tclman("catch、error、try、throw、return、trace、time、info", ["`try` 與 `catch` 的差別；`return` 選項；`trace` 的操作"])],
  pitfalls=["`catch` 後沒檢查回傳碼就當成功", "吞掉例外而不是處理它"],
  check=["`catch` 回傳 1 代表什麼？`return -code error` 呢？", "`try … finally` 為什麼比 `catch` 後手動清理更好？"],
  gate=PLG(["t018", "t019"], 30, 1))

U(0, 1, "階段 T0 驗收週", "獨立完成一個有輸入驗證、錯誤處理與測試的文字處理工具。",
  ["整合：寫一個『日誌分析器』：讀入多個日誌檔，抽出事件、依等級與時間彙總、輸出報表；所有函式有檢查，錯誤時有清楚訊息"],
  build=["完成日誌分析器與 20 個測試案例"],
  readings=[R.tclman("proc、dict、regexp、format、file、try、catch", ["複習：這 7 組指令是 Tcl 日常寫作的主力"])],
  check=["我最常犯的三種 Tcl 錯誤是什麼？怎麼檢查？"],
  gate=PRJ(["日誌分析器：3 種日誌格式都能處理", "20 個測試案例全過（含錯誤輸入）", "所有 proc 有前置條件檢查與一致的錯誤格式", "能逐行解釋一段含 3 層替換的程式"], 5))

# ============================ T1：工程化 Tcl（第 12–22 週）============================
U(1, 1, "模組化：source、namespace 與 package", "能把腳本組織成可重用的模組與套件。",
  ["`source` 載入檔案；`namespace eval`、命名空間內的 proc 與變數、`namespace export`／`import`、`namespace ensemble`（讓 `mymod subcommand` 這種用法成為可能）、`namespace current`／`namespace code`",
   "`package provide`／`package require`／`pkgIndex.tcl`／`auto_path`；版本與相依；`package ifneeded`",
   "專案結構：`lib/`、`tests/`、`bin/`；以 `[info script]` 取得腳本目錄做相對載入",
   "命名與風格：命名空間前綴、不污染全域；避免全域變數"],
  planned=[PL("t020", "寫一個套件", "把字串工具打包成 package，用 `package require` 使用，含版本檢查"), PL("t021", "命名空間 ensemble", "實作 `stack` ensemble：push／pop／peek／size")],
  build=["把前面的日誌分析器拆成 3 個套件（parser、stats、report），用 `package require` 組合；寫 `pkgIndex.tcl`"],
  readings=[R.tcltut("35、36", ["模組化 source、可重用函式庫：package 與 namespace"]),
            R.tclman("namespace、package、source、variable", ["`namespace ensemble`、`package` 子命令"])],
  pitfalls=["把變數寫在全域造成模組之間互相污染", "`pkgIndex.tcl` 的路徑相依"],
  check=["`namespace import` 與 `namespace ensemble` 各解決什麼問題？", "`auto_path` 在哪裡起作用？"],
  gate=PLG(["t020", "t021"], 40, 1))

U(1, 2, "動態程式與指令構造", "能安全地組裝與執行指令，理解 eval、subst、apply 與 uplevel。",
  ["`eval`（會再替換一次，注意注入）、`{*}` 展開運算子（更安全的清單展開）、`apply`（匿名函式）、`uplevel`／`upvar` 進階用法、`tailcall`",
   "動態建立指令：`proc` 在執行時產生、`interp alias`、`rename`（包裝既有指令：加上日誌或計時）",
   "`subst`（`-nocommands`／`-novariables`）；樣板產生：用 `string map` 或 `subst` 產生 Verilog／SDC／腳本",
   "內省：`info commands`／`info args`／`info body`／`info level`，用它實作簡單的除錯與追蹤"],
  planned=[PL("t022", "指令包裝器", "用 rename 包裝一個指令，記錄呼叫次數與耗時"), PL("t023", "樣板展開", "把 `${name}` 形式的樣板與 dict 展開，並正確處理缺值"), PL("t024", "展開運算子", "用 `{*}` 重寫 5 個用 eval 的程式")],
  build=["寫一個『樣板產生器』：從 dict 與樣板檔產生 Verilog 模組骨架（含參數與埠），並用 iverilog 檢查語法"],
  readings=[R.tcltut("32–34、37–39", ["info、eval、指令構造、subst"]),
            R.tclman("eval、apply、subst、rename、interp、tailcall、info", ["各指令的安全用法；`interp alias`"])],
  pitfalls=["用字串拼接指令再 eval（注入與引用問題）", "改了既有指令卻沒保留原行為"],
  check=["為什麼 `{*}$args` 比 `eval $args` 安全？", "`rename` 包裝指令的標準寫法？"],
  gate=PLG(["t022", "t023", "t024"], 45, 2))

U(1, 1, "測試與程式品質", "能用 tcltest 為 Tcl 程式寫自動化測試，並使用靜態檢查。",
  ["`tcltest` 框架：`test` 指令（名稱、描述、約束、設定、本體、清理、預期結果與比對模式）、`configure`、`runAllTests`、`cleanupTests`、`makeFile`／`removeFile`；測試的組織與命名",
   "測試設計：邊界、錯誤輸入、跨平台；以測試先行（TDD）修改舊程式；用測試保護重構",
   "靜態檢查：Nagelfar（找出語法與未定義變數）；程式風格：縮排、命名、註解與函式長度",
   "與 CI 整合：一行指令跑全部測試，失敗就以非零碼結束"],
  planned=[PL("t025", "補測試", "給一份沒有測試的程式與規格，寫出能抓到 4 個隱藏 bug 的測試")],
  build=["替前面所有套件寫 tcltest 測試（至少 60 個），加入 GitHub Actions 執行；用 Nagelfar 檢查並修正警告"],
  readings=[R.tclman("tcltest", ["`test` 指令的各個選項與測試檔結構"]),
            R.doc("nagelfar", "Nagelfar 使用說明", ["如何執行與解讀警告"])],
  pitfalls=["測試依賴執行順序", "預期結果比對模式（exact／glob／regexp）選錯"],
  check=["tcltest 的 `-constraints` 用來做什麼？", "怎麼讓測試失敗時 CI 變紅？"],
  gate=PRJ(["60 個以上 tcltest 測試全部通過", "CI 綠燈", "Nagelfar 無錯誤"], 5))

U(1, 2, "解析結構化與非結構化報告", "能穩定解析 EDA 工具的文字報告與常見資料格式。",
  ["報告解析的通用方法：逐行狀態機（區段開頭、表格標題、資料列、結尾）、用正規表示式抽欄位、處理單位與數字格式（`1,234`、`0.5e-3`、`ns`／`ps`）",
   "常見格式：固定寬度表格、以空白分欄的表格、CSV（用 tcllib 的 `csv` 模組或自己處理引號）、JSON（tcllib 的 `json`）、簡單的 key=value 設定檔",
   "彙總：多份報告合併成一張比較表；計算差異與百分比；輸出文字表格或 CSV 供試算表使用",
   "穩健性：欄位缺失、格式微小改變、工具版本升級後的報告；寫解析器時同步寫測試與樣本"],
  planned=[PL("t026", "表格報告解析", "解析 `report_checks` 風格的時序報告，抽出各級延遲與 slack"), PL("t027", "合成報告彙總", "解析 Yosys `stat` 輸出，彙總多次合成的面積"), PL("t028", "CSV 讀寫", "正確處理含逗號與引號的欄位")],
  build=["寫 Yosys `stat` 與 OpenSTA `report_checks` 兩種報告的解析套件（含樣本檔與測試），輸出 CSV 與 dict"],
  readings=[R.tcltut("22–25", ["字串與正規表示式的複習與實戰"]),
            R.tclman("regexp、scan、format、dict、split、join", ["解析與輸出的主力指令"]),
            R.doc("tcllib", "Tcllib：csv、json 模組", ["不要自己重寫已經有的解析器"])],
  pitfalls=["工具升級後報告格式微調，解析器默默輸出錯誤的數字", "把單位忘了換算"],
  check=["怎麼讓解析器在格式不符時『大聲失敗』而不是默默出錯？", "你的解析器如何處理缺欄位？"],
  gate=PLG(["t026", "t027", "t028"], 60, 2))

U(1, 2, "外部程式、事件與並行", "能管理多個外部程序、處理事件迴圈，並平行跑多個工作。",
  ["管線串流：`open |cmd r+`、非阻塞讀取 `fconfigure -blocking 0`、`fileevent` 搭配事件迴圈；`vwait`、`after`（延遲與排程）、`update`",
   "同時執行多個模擬或合成工作：限制並行數量（工作佇列）、收集結束碼與輸出、逾時處理（`after` ＋ `exec kill` 的包裝）",
   "時間：`clock seconds`／`clock format`／`clock scan`／`clock milliseconds`；時間戳日誌",
   "協程（8.6）：`coroutine`／`yield`／`yieldto`，用同步風格寫非同步流程；與 `after`／`fileevent` 搭配"],
  planned=[PL("t029", "工作佇列", "最多 N 個並行的假工作，輸出完成順序與總耗時"), PL("t030", "逾時包裝", "給一個可能不結束的外部程式，N 秒後終止並回報")],
  build=["實作 `run_parallel`：給一串指令，最多 4 個並行，每個工作有逾時，收集結束碼、輸出與耗時，最後印出摘要表"],
  readings=[R.tcltut("45–47、46", ["通道 I/O、fileevent／vwait、clock、fblocked／fconfigure"]),
            R.tclman("fileevent、vwait、after、update、clock、fconfigure、fblocked、coroutine、yield、yieldto、chan、exec", ["事件驅動 I/O 的各指令與非阻塞模式"])],
  pitfalls=["忘了啟動事件迴圈（`vwait` 或 `update`）導致回呼從不觸發", "阻塞讀取卡住整個腳本"],
  check=["`fileevent` 與 `vwait` 如何配合？", "協程相較於回呼風格有什麼好處？"],
  gate=PLG(["t029", "t030"], 45, 1))

U(1, 2, "物件導向與進階結構", "能用 TclOO 建模複雜工具，並理解解譯器隔離。",
  ["TclOO（8.6 內建）：`oo::class create`、`method`、`constructor`／`destructor`、`variable`、繼承 `superclass`、`next`／`nextto`、`my`／`self`、mixin 與過濾器",
   "何時值得用物件：需要多個實例且有狀態（例如『工作』、『設計』、『報告』物件）；何時 dict＋proc 就夠",
   "子解譯器：`interp create`、`interp eval`、`-safe` 解譯器用來安全執行不可信的設定檔",
   "設計：把『流程步驟』建模成物件，有輸入、輸出與依賴；可序列化的設定"],
  planned=[PL("t031", "TclOO 堆疊與佇列", "用類別實作並含單元測試"), PL("t032", "安全設定檔載入", "在 safe 子解譯器中載入設定檔，只暴露指定指令")],
  build=["用 TclOO 實作 `Step` 與 `Flow` 類別：步驟有名稱、依賴、指令與輸出檔；`Flow` 依依賴順序執行，並跳過輸出已是最新的步驟（類似 make）"],
  readings=[R.tcltut("48", ["子解譯器"]),
            R.tclman("oo::class、oo::define、oo::object、oo::objdefine、oo::copy、my、self、next、nextto、interp", ["TclOO 的類別定義、方法與繼承；interp 的安全模式"])],
  pitfalls=["把全部東西都寫成物件，結果比 dict 更難讀", "在 `-safe` 解譯器中忘了關閉不該暴露的指令"],
  check=["`next` 在方法中做什麼？", "什麼情況下 dict＋proc 比物件更合適？"],
  gate=PLG(["t031", "t032"], 45, 1))

U(1, 1, "階段 T1 驗收週", "完成一個模組化、有測試、有文件的 Tcl 工具套件。",
  ["整合：把前面單元的產出整合成一個『小型建置系統』（Flow／Step、並行、報告解析、測試）"],
  build=["完成小型建置系統：設定檔、依賴、並行、日誌、報告、測試，並寫 README"],
  readings=[R.tclman("namespace、package、tcltest、interp", ["複習：模組化與測試的指令"])],
  check=["我的套件如果交給同事，他需要多久能用起來？README 夠嗎？"],
  gate=PRJ(["小型建置系統可用一行指令執行完整範例流程", "80 個以上測試通過、CI 綠燈", "README 含安裝、使用範例與限制", "TclOO 或 namespace ensemble 的使用有理由說明"], 7))

# ============================ T2：EDA 腳本實務（第 23–33 週）============================
U(2, 2, "SDC 時序約束", "能閱讀與撰寫 SDC 約束，並用 Tcl 腳本產生與檢查它。",
  ["SDC 是 Tcl 的子集加上 EDA 專用指令；核心指令：`create_clock`（週期、波形、埠）、`create_generated_clock`、`set_input_delay`／`set_output_delay`（相對於哪個時脈）、`set_clock_uncertainty`／`set_clock_latency`、`set_false_path`、`set_multicycle_path`、`set_max_delay`／`set_min_delay`、`set_load`／`set_driving_cell`",
   "物件取得：`get_ports`、`get_clocks`、`get_pins`、`get_cells`、`get_nets`（回傳『集合』，不是 Tcl 清單；在商用工具用 `foreach_in_collection` 迭代，開源的 OpenSTA 則可以當清單）",
   "約束的完整性：每個時脈、每個輸入與輸出都要有約束；用工具的未約束檢查（`check_timing` 或對應指令）找漏洞",
   "用 Tcl 產生 SDC：由設計參數（時脈週期、介面清單）以迴圈產生一致的約束；避免複製貼上"],
  planned=[PL("t033", "SDC 產生器", "由 dict 描述的時脈與介面產生 SDC 文字，與標準答案逐行比對"), PL("t034", "SDC 檢查", "解析一份 SDC 並回報缺少的約束（例如輸入沒有延遲）")],
  build=["替一個含 3 個時脈域的小設計寫 SDC（時脈、I/O 延遲、跨域 false path 與 multicycle 各至少一個合理案例），並寫 Tcl 產生器從設計描述自動產生；用 OpenSTA 載入無錯誤"],
  readings=[R.doc("opensta", "OpenSTA 文件：SDC 指令與支援範圍", ["支援哪些指令、與商用工具的差異"]),
            R.book("sta_book", "Bhasker & Chadha, Static Timing Analysis for Nanometer Designs：約束相關章節", ["各約束的意義與常見誤用"]),
            R.tclman("foreach、dict、format", ["用迴圈與 dict 產生約束文字"])],
  pitfalls=["把集合當 Tcl 清單操作（在商用工具會出錯）", "`set_false_path` 濫用，掩蓋真正的時序問題"],
  check=["`set_input_delay` 的數值代表什麼？", "multicycle path 為什麼要同時考慮 setup 與 hold？"],
  gate=PRJ(["含 3 個時脈域的 SDC 與 Tcl 產生器", "OpenSTA 載入無錯誤、無未約束路徑", "每個 false path／multicycle 都附理由說明"], 7))

U(2, 1, "Yosys 與 Tcl 腳本", "能用腳本驅動 Yosys 完成合成流程並擷取結果。",
  ["Yosys 的指令碼：`.ys` 檔與 Tcl（`yosys -c script.tcl`，Tcl 內以 `yosys` 指令呼叫 Yosys 指令）；以 `tee -o` 或 `-q` 擷取輸出；`select` 與 `stat` 的資料擷取",
   "把合成流程參數化：頂層名稱、製程庫、時脈週期、最佳化選項；批次合成多個設計並彙總面積",
   "與前面單元結合：解析 `stat` 報告成 dict、輸出 CSV、做回歸（面積不得惡化超過某個比例）",
   "可重現性：記錄工具版本、參數與輸入雜湊於報告開頭"],
  planned=[PL("t035", "合成報告回歸", "比較兩次合成的 stat，回報面積變化超過門檻的模組")],
  build=["寫 `synth_all.tcl`：掃描目錄下所有設計，依設定合成並輸出面積、單元數與執行時間的 CSV；面積回歸超過 5% 時以非零碼結束"],
  readings=[R.doc("yosys", "Yosys 手冊：Using Yosys／Scripting（Tcl 介面）", ["如何從 Tcl 呼叫 Yosys、擷取結果"]),
            R.tclman("exec、file、glob、dict、format", ["批次與報告的主力指令"])],
  pitfalls=["合成流程沒有固定隨機種子與版本，結果無法重現", "解析輸出而不是使用工具提供的機器可讀介面"],
  check=["為什麼要在報告開頭記錄工具版本？", "怎麼設定面積回歸的門檻才合理？"],
  gate=PRJ(["可批次合成多個設計並輸出 CSV", "面積回歸偵測與非零結束碼", "附可重現資訊（版本、參數）"], 5))

U(2, 2, "OpenSTA／OpenROAD 的 Tcl 介面", "能用 Tcl 驅動時序分析並擷取關鍵數據。",
  ["OpenSTA 流程：`read_liberty`、`read_verilog`、`link_design`、`read_sdc`、`report_checks`（`-path_delay max／min`、`-group_count`、`-format`）、`report_wns`／`report_tns`、`report_clock_skew`；`sta::` 命名空間下的內部 API 可以取得物件與數值",
   "OpenROAD 的 Tcl：各步驟指令（floorplan、place、CTS、route 的 Tcl 指令）；OpenDB 的 Tcl／Python API 可遍歷設計（儘管細節隨版本變動，請以安裝版本的文件為準）",
   "用 Tcl 擷取數值而不是解析文字：能用 API 就用 API；必須解析報告時回到上一單元的解析套件",
   "自動化時序報告：每次合成後自動產生『最差 10 條路徑』摘要與趨勢"],
  planned=[PL("t036", "最差路徑摘要", "讀入網表與 SDC，輸出最差 10 條路徑的起點、終點與 slack 的表格")],
  build=["寫 `sta_summary.tcl`：載入設計，輸出 WNS／TNS、最差 10 條路徑表、各時脈域的路徑數；對 3 個設計執行並產出彙總表"],
  readings=[R.doc("opensta", "OpenSTA 文件：Commands 與 Tcl 命名空間", ["讀入設計與報告的所有指令"]),
            R.doc("openroad", "OpenROAD 文件：各模組的 Tcl 指令與 Database 說明", ["指令與參數；請以你安裝的版本為準"])],
  pitfalls=["不同版本的 API 變動，腳本在升級後壞掉", "忘了先 `link_design` 就查詢"],
  check=["為什麼用 API 擷取數值比解析報告文字穩？", "WNS 與 TNS 有什麼不同？"],
  gate=PRJ(["`sta_summary.tcl` 在 3 個設計上輸出正確的摘要", "與手動執行 `report_checks` 的結果比對一致", "版本與參數記錄"], 7))

U(2, 2, "設計產生器與參數掃描", "能用 Tcl 產生設計與設定，並系統性掃描參數、整理結果。",
  ["產生器：用樣板與 dict 產生 Verilog（參數化模組實例、暫存器檔、位址解碼）、SDC、Makefile 與檔案清單",
   "參數掃描：在時脈週期、管線級數、利用率等維度上做網格掃描；每個組合一個工作目錄；收集結果到一張表",
   "結果整理：輸出 CSV 與簡單的文字圖表（或呼叫 gnuplot／Python 畫圖）；找出 Pareto 前緣（面積 vs 頻率）",
   "效率：快取已完成的組合（輸出檔比輸入新就跳過）、並行執行"],
  planned=[PL("t037", "暫存器檔產生器", "由暫存器描述 dict 產生位址解碼的 Verilog 與標頭檔"), PL("t038", "Pareto 前緣", "給一組（面積, 延遲）結果，輸出非劣解")],
  build=["實作『管線級數 × 時脈週期』的掃描：自動產生不同級數的乘加單元、合成、STA、彙總成表，並標出 Pareto 前緣"],
  readings=[R.tclman("dict、format、file、exec、foreach、lsort", ["產生器與掃描的主力指令"]),
            R.tcltut("37–39", ["指令構造與樣板：format、subst"])],
  pitfalls=["參數組合爆炸卻沒有快取與並行", "把結果表當成事實而不檢查離群值"],
  check=["為什麼要保存每個組合的完整輸入與輸出？", "Pareto 前緣怎麼定義？"],
  gate=PLG(["t037", "t038"], 45, 1))

U(2, 2, "回歸測試與持續整合腳本", "能建立可靠的回歸系統，並與 CI 整合。",
  ["回歸驅動器：測試清單檔、多個隨機種子、平行執行、逾時、保存失敗時的波形與日誌、彙總 PASS／FAIL／TIMEOUT",
   "報告：文字摘要、JUnit XML（讓 CI 顯示每個測試的結果）、失敗重現指令（含種子）",
   "與版本控制整合：只重跑受變更影響的測試（以檔案相依判斷）；夜間完整回歸與提交前快速回歸的分層",
   "穩定性：偵測不穩定（flaky）的測試——同一種子結果不同"],
  planned=[PL("t039", "回歸彙總", "解析多個測試的結果檔，輸出摘要與失敗的重現指令"), PL("t040", "JUnit 輸出", "產生符合 JUnit 格式的 XML")],
  build=["替前面的 Verilog 專案寫 Tcl 回歸驅動器：100 個種子、4 個並行、逾時、JUnit 輸出，並在 GitHub Actions 中執行與上傳報告"],
  readings=[R.tclman("exec、open、fileevent、after、clock、file", ["控制並行工作與計時"]),
            R.doc("verilator", "Verilator：測試與回歸的建議流程", ["Verilator 編譯一次、多種子執行的方式"])],
  pitfalls=["失敗時沒有保存重現所需的種子與波形", "逾時終止後留下殘留的程序"],
  check=["怎麼偵測 flaky 測試？", "為什麼要把快速回歸與完整回歸分層？"],
  gate=PRJ(["回歸驅動器一行指令可執行，輸出摘要與 JUnit", "CI 綠燈並顯示每個測試結果", "失敗可用種子重現"], 7))

U(2, 1, "商用 EDA 的 Tcl 寫法（概念與對照）", "能讀懂商用工具的 Tcl 腳本，並知道它們與開源版本的對應。",
  ["商用工具的 Tcl 慣例（概念層級；需要授權才能實作）：合成工具的讀入、約束、編譯與報告；時序簽核工具的集合物件與 `foreach_in_collection`、`get_*` 與 `all_*` 指令；實體設計工具的流程腳本",
   "FPGA 廠商工具（例如 Vivado）的 Tcl：專案模式與非專案模式；`read_verilog`、`read_xdc`、`synth_design`、`opt_design`、`place_design`、`route_design`、`report_timing_summary`、`write_bitstream`——這是最容易取得（免費版）的商用 Tcl 練習對象之一",
   "對照表：開源與商用流程中每一步的指令對應；哪些寫法可移植、哪些不能",
   "誠實限制：沒有授權就沒有辦法驗證商用工具指令；本單元以閱讀與對照為主，實作用開源工具與（若有）免費 FPGA 工具鏈"],
  planned=[],
  build=["寫一份對照表（開源流程 ↔ 商用流程）；若有 Vivado 或其他免費版工具，用非專案模式寫一支從 RTL 到時序報告的 Tcl 腳本"],
  readings=[R.doc("vivado_tcl", "Vivado Design Suite Tcl 指令參考指南（AMD；需註冊）", ["非專案模式的指令流程"]),
            R.doc("opensta", "OpenSTA 文件", ["與商用時序工具指令的相似與差異"])],
  pitfalls=["把商用工具的集合物件當一般清單", "在不同工具版本之間直接複製貼上腳本"],
  check=["開源與商用流程中，哪三個指令的語意最相近？", "為什麼商用腳本常需要處理『集合』？"],
  gate=PRJ(["對照表（至少 15 條指令）", "若有工具：一支可執行的非專案模式腳本與報告；若沒有：說明哪些步驟因授權無法驗證", "指出 3 個移植時容易出錯的地方"], 5))

U(2, 1, "階段 T2 驗收週", "把腳本整合成一條自動化流程：RTL 到時序與面積報告。",
  ["整合：一條 Tcl 驅動的流程：產生設計→模擬回歸→合成→STA→彙總報告"],
  build=["完成流程並對 3 個設計執行，輸出一頁彙總報告"],
  readings=[R.tclman("exec、file、dict、try、tcltest", ["複習"])],
  check=["如果某一步失敗，我的流程如何處理與回報？"],
  gate=PRJ(["一行指令從 RTL 跑到彙總報告", "3 個設計的結果表", "失敗處理與清楚的錯誤訊息", "測試涵蓋主要模組"], 7))

# ============================ T3：作品與面試（第 34–41 週）============================
U(3, 2, "專題一：流程執行器", "實作一個小型的流程執行器（類似 make 與工作排程的結合）。",
  ["需求：以設定檔描述步驟與依賴、只重跑過期的步驟、並行執行、日誌、失敗處理與重試、可重現紀錄（版本、參數、輸入雜湊）",
   "設計：用 TclOO 或 namespace＋dict；把『解析設定』『排程』『執行』『報告』分開；寫測試先於實作",
   "進階（選做）：快取、遠端執行（ssh）、與工作排程系統（例如 LSF、Slurm）整合的轉接層",
   "文件：README、設定檔格式說明、範例流程"],
  planned=[],
  build=["完成流程執行器與範例（RTL→合成→STA）；測試與文件齊全"],
  readings=[R.tclman("oo::class、namespace、dict、exec、fileevent、clock", ["架構與並行"]),
            R.doc("welch", "Welch 等人，Practical Programming in Tcl and Tk：進階程式設計與事件相關章節", ["把大型 Tcl 程式組織起來的做法"])],
  pitfalls=["沒有明確的『已過期』判斷導致重跑太多或太少", "失敗時留下不一致的狀態"],
  check=["你的流程執行器如何判斷一個步驟需要重跑？"],
  gate=PRJ(["範例流程可重現", "依賴、並行、重試、日誌皆有測試", "README 與設定檔格式說明", "他人可在 10 分鐘內跑起來"], 14))

U(3, 2, "專題二：時序報告分析與儀表板", "實作跨多次執行的時序與面積趨勢分析工具。",
  ["需求：收集多次執行的 STA 與合成結果（來自檔案或資料夾），建立資料表，偵測惡化（回歸），輸出比較報告（文字或 HTML）",
   "設計：資料格式（CSV 或 JSON）、解析層（上一階段的解析套件）、比較與門檻設定、報告產生",
   "輸出：一張總表與每次執行的差異；超過門檻的項目醒目標示；以非零碼結束供 CI 使用",
   "選做：產生簡單的 SVG 圖表（用 Tcl 直接輸出 SVG 文字）"],
  planned=[],
  build=["完成分析工具，用 20 次（可合成的假資料）執行結果測試；含回歸偵測與 HTML 報告"],
  readings=[R.doc("tcllib", "Tcllib：json、csv、html 相關模組", ["不重複造輪子"]),
            R.tclman("dict、format、lsort、regexp、file", ["資料處理的主力指令"])],
  pitfalls=["比較不同工具版本的結果卻當作設計變動", "門檻設太嚴造成每天誤報"],
  check=["怎麼區分『設計變差』與『雜訊』？"],
  gate=PRJ(["分析工具在 20 次資料上正確偵測 3 個預先埋入的回歸", "HTML 或文字報告", "可在 CI 中使用（非零結束碼）", "測試與文件"], 14))

U(3, 2, "專題三：RTL 到版圖的自動化流程", "用 Tcl 把開源流程自動化，並做參數探索。",
  ["範圍：RTL→Yosys 合成→OpenSTA→OpenLane／OpenROAD→簽核；以 Tcl 或流程執行器驅動",
   "參數探索：利用率、時脈週期、佈局密度等；每個組合的 QoR（面積、WNS、功耗、擁塞）收進一張表",
   "報告：Pareto 前緣、最佳設定推薦與理由、失敗組合的分析（例如擁塞過高）",
   "可重現：所有輸入（RTL、約束、工具版本、設定）都記錄，任何一列結果都能重跑"],
  planned=[],
  build=["對一個小設計（例如 UART 或計數器）完成至少 12 個參數組合的探索與報告"],
  readings=[R.doc("openlane", "OpenLane 文件：設定變數與流程控制", ["可以調整哪些參數、各自影響什麼"]),
            R.doc("openroad", "OpenROAD 文件", ["Tcl 介面與報告指令"])],
  pitfalls=["把探索結果當成通用結論（只對這個設計成立）", "忽略失敗組合，只看成功的"],
  check=["你如何確認某個『最佳』設定不是隨機雜訊的結果？"],
  gate=PRJ(["12 個以上組合的完整紀錄與 QoR 表", "Pareto 前緣與推薦設定的說明", "任一列結果可由紀錄重現"], 14))

U(3, 1, "面試與職涯", "能在面試中清楚回答 Tcl 與 EDA 腳本問題，並整理作品集。",
  ["常見題：Tcl 的替換規則與引用、`list` vs 字串、`upvar`／`uplevel`、`dict` vs `array`、`catch`／`try`、正規表示式、`eval` 的風險、命名空間",
   "EDA 腳本題：寫 SDC、解析報告、批次執行與回歸、處理大檔案（逐行串流而非一次讀入）",
   "與 Python 的取捨：何時 Tcl（工具內建、約束與流程）、何時 Python（資料處理、驗證、視覺化）；兩者都要會",
   "作品集：三個專題整理成 README；準備 5 分鐘與 30 分鐘兩種版本的說明"],
  planned=[PL("t041", "Tcl 白板題", "20 題常見題，每題寫程式並用 tclsh 驗證")],
  build=["完成 5 次模擬面試並整理；更新作品集"],
  readings=[R.doc("tclwiki", "Tcler's Wiki：Tcl 的常見陷阱與慣用法", ["常見問題的社群整理"]),
            R.tcltut("4–6、15、37", ["面試最常問的概念：替換、範圍、eval"])],
  pitfalls=["只會語法不會說明為什麼", "作品集沒有可重現的證據"],
  check=["你如何向沒學過 Tcl 的人說明『一切皆指令』？"],
  gate=PRJ(["5 次模擬面試紀錄", "20 題白板題的程式與測試", "作品集（三個專題）"], 7))

U(3, 1, "總驗收：作品集與限時任務", "整合驗收：作品集完整，並在限時內完成腳本任務。",
  ["做一次 3 小時限時任務：給一份工具輸出樣本與需求，寫出解析與彙總腳本，附測試"],
  build=["完成限時任務與作品集整理"],
  readings=[R.tclman("proc、dict、regexp、format、try", ["最常用的 5 組指令"])],
  check=["我能證明自己具備『EDA 腳本工程師』的哪些能力？每項的證據在哪？"],
  gate=PRJ(["3 小時限時任務：解析、彙總、測試全部通過", "作品集三件齊全（流程執行器、報告分析工具、RTL 到版圖自動化）", "每件有 README、測試與可重現指令"], 7))
