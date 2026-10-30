"""課程資料：126 週、52 個單元，從零到 CPE 6 題。"""

RES = {
    "pytut": ("Python 官方教學（繁中）", "https://docs.python.org/zh-tw/3/tutorial/"),
    "pytutor": ("Python Tutor（逐步視覺化執行）", "https://pythontutor.com/"),
    "zj": ("ZeroJudge（繁中題庫）", "https://zerojudge.tw/"),
    "ap325": ("AP325-Python 教材（吳邦一）", "https://hackmd.io/@bangyewu/SJmDbdKSp"),
    "yizhe": ("王一哲教學網站（APCS）", "https://sites.google.com/view/yizhe/%E8%AA%B2%E7%A8%8B/apcs"),
    "cses": ("CSES Problem Set（分類清楚、純標準輸入輸出）", "https://cses.fi/problemset/"),
    "cphb": ("Competitive Programmer's Handbook（免費 PDF）", "https://cses.fi/book/book.pdf"),
    "cpalgo": ("CP-Algorithms（演算法百科）", "https://cp-algorithms.com/"),
    "visualgo": ("VisuAlgo（演算法動畫）", "https://visualgo.net/"),
    "cf": ("Codeforces 題庫（可依 tag / rating 篩選）", "https://codeforces.com/problemset"),
    "atcoder": ("AtCoder（ABC 的 A–D 題）", "https://atcoder.jp/"),
    "cpe": ("CPE 官網（歷屆題目與答對率）", "https://cpe.mcu.edu.tw/"),
    "learncpp": ("learncpp.com（C++ 入門教學）", "https://www.learncpp.com/"),
    "cppref": ("cppreference（C++ 標準庫查詢）", "https://en.cppreference.com/"),
    "progit": ("Pro Git（繁中）", "https://git-scm.com/book/zh-tw/v2"),
}

RHYTHM = [
    ("第 1 天", "新概念", "讀教材 + 在直譯器／Python Tutor 做小實驗；寫下 3 件『我原本以為』與『其實』。"),
    ("第 2 天", "概念練習", "做本單元前半的 drills（`cpe new` → `cpe test`）。卡住才 `cpe hint`。"),
    ("第 3 天", "鞏固", "做本單元後半的 drills；每題通過後想：還有別的寫法嗎？複雜度多少？"),
    ("第 4 天", "真題", "做 anchors（真實 UVA 題，用 `cpe import` 匯入題目）或 pool 的題目；先做 `cpe review` 到期的重練。"),
    ("第 5 天", "重寫日", "把本週用過提示的題目，關掉所有資料，從空白檔重寫。這是留存率最高的一步。"),
    ("第 6 天", "檢核", "每週計時測驗（`cpe mock start --kind weekly`）；單元最後一週改做 `cpe gate`。階段 2 起，這天另撥 1–2 小時做工程任務（`cpe eng`）。"),
    ("第 7 天", "休息", "不寫程式。睡眠是學習的一部分。"),
]

UNITS = []


def U(stage, weeks, title, goal, learn, drills=(), anchors=(), pool=(), res=(), pitfalls=(), check=(), eng=(),
      gate=None, lang="py"):
    UNITS.append(dict(stage=stage, weeks=weeks, title=title, goal=goal, learn=list(learn), drills=list(drills),
                      anchors=list(anchors), pool=list(pool), resources=list(res), pitfalls=list(pitfalls),
                      check=list(check), eng=list(eng), gate=gate, lang=lang, read=[]))


def G(problems, minutes, need, lang="py"):
    return {"type": "set", "problems": list(problems), "minutes": minutes, "need": need, "lang": lang}


def M(kind, need):
    return {"type": "mock", "kind": kind, "need": need}


# ======================= 階段 0：Python 語法基礎（第 1–12 週）=======================
U(0, 2, "環境、輸入輸出與運算", "能安裝並執行 Python，讀入資料、計算、格式化輸出，並讀到檔案結尾（EOF）。",
  ["安裝 Python 3.9 以上（考場是 3.9.6）與一個編輯器（VS Code 或 IDLE）；會在終端機執行 `python 檔名.py`",
   "變數、型別（int / float / str / bool）、算術（+ - * / // % **）、型別轉換 int() str() float()",
   "print() 與 input()；f-string；`map(int, input().split())` 一次讀多個數",
   "讀到 EOF：`for line in sys.stdin:`——CPE 幾乎每一題都這樣讀",
   "怎麼讀錯誤訊息（traceback）：從最後一行往上看，第一個在你檔案裡的行號就是出事的地方"],
  drills=["d001", "d002", "d003"],
  pool=["ZeroJudge 的 a 開頭基礎題：挑解題人數最多的前 15 題，每題都用 `cpe add` 登記或自己記錄"],
  res=["pytut", "pytutor", "zj"],
  pitfalls=["input() 讀進來是字串，直接相加會變成字串串接", "Windows／終端機最後一行沒有換行不影響，但『多印一個空行』會被判錯"],
  check=["`7 / 2`、`7 // 2`、`-7 // 2`、`-7 % 3` 各是多少？為什麼？", "如何一行讀入三個整數 a b c？"],
  gate=G(["d004", "d002"], 45, 2))

U(0, 1, "條件判斷", "能把『如果…就…否則…』的規則寫成 if / elif / else，並系統性地測邊界值。",
  ["比較運算（== != < <= > >=）、布林運算 and / or / not 與優先順序", "if / elif / else 鏈；巢狀 if；三元運算式 `a if cond else b`",
   "邊界值測試：規則裡出現的每個數字，都要測它『剛好』、『少一』、『多一』"],
  drills=["d005", "d006", "d007"], res=["pytut", "pytutor"],
  pitfalls=["`=` 是賦值、`==` 才是比較", "`a < b < c` 在 Python 合法，但別在 C++ 這樣寫（之後會踩）"],
  check=["閏年規則為什麼要用括號？", "elif 與連續多個 if 的差別是什麼？"],
  gate=G(["d008", "d005"], 45, 2))

U(0, 2, "迴圈", "能用 for / while 做累加、連乘、計數、拆解數字與印出圖形。",
  ["for + range(start, stop, step)：右界不含；while 與 break / continue", "累加器模式：先設初值，再在迴圈裡更新",
   "巢狀迴圈與印出圖形；字串乘法 `' ' * n`", "用 `n % 10` 與 `n // 10` 拆數字"],
  drills=["d009", "d010", "d011", "d024"], res=["pytut", "pytutor"],
  pitfalls=["range(1, n) 不含 n", "while 忘了更新條件變成無窮迴圈（Ctrl+C 中止）"],
  check=["`range(10, 0, -3)` 產生什麼？", "階乘的初值為什麼是 1 不是 0？"],
  gate=G(["d012", "d010"], 60, 2))

U(0, 2, "字串與 list", "熟練字串切片、迭代與 list 基本操作，能自己寫迴文、凱薩密碼、統計。",
  ["字串：索引、切片 `s[a:b:c]`、`s[::-1]`、方法（strip split join lower upper find count replace）",
   "字串不可變；ord() / chr()", "list：建立、索引、append / pop / insert、切片、sort / sorted、min / max / sum / len",
   "list comprehension：`[x*x for x in a if x%2==0]`", "迭代：`for i, x in enumerate(a)`、`zip(a, b)`"],
  drills=["d013", "d014", "d015", "d017", "d018"], res=["pytut", "pytutor"],
  pitfalls=["`sort()` 回傳 None（會把 list 本身排好）；`sorted()` 才回傳新 list", "迴圈中邊走邊刪 list 元素會漏掉東西"],
  check=["`'abcde'[1:4]`、`'abcde'[::-2]` 各是什麼？", "split() 與 split(' ') 對 `'a  b'` 的結果有何不同？"],
  gate=G(["d016", "d015"], 60, 2))

U(0, 2, "set、dict 與函式", "會用 set / dict 做快速查詢與計數，會寫函式；第一次感受到『效能』差異。",
  ["set：add、`in`（O(1) 查詢）、集合運算；dict：`d[k]`、`d.get(k, 0)`、items()、`collections.Counter`",
   "排序的 key：`sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))`", "函式：def、參數、return；區域與全域變數",
   "第一次接觸複雜度：list 的 `in` 是 O(n)，set 是 O(1)"],
  drills=["d019", "d020", "d025"], res=["pytut"],
  pitfalls=["用 list 當集合查詢，資料一多就超時", "函式裡改全域變數前要先宣告 global（但更好的做法是用參數與回傳值）"],
  check=["為什麼 d028 用 set 就能從 O(n²) 變 O(n)？", "`Counter('hello')` 長什麼樣？"],
  gate=G(["d028", "d029"], 60, 2))

U(0, 1, "數學基礎與進位制", "能寫質數判斷、gcd、費氏數列、進位轉換等基本數學程式。",
  ["質數試除法到 √n；gcd 輾轉相除法；費氏數列的迭代寫法（遞迴版為什麼慢）", "進位制：用 `%` 與 `//` 反覆取餘數；`bin()`、`int(s, base)`",
   "把重複出現的程式碼抽成函式"],
  drills=["d021", "d022", "d023"], res=["pytut"],
  pitfalls=["1 不是質數", "遞迴費氏 F(40) 就要好幾秒"],
  check=["為什麼只需試除到 √n？", "255 轉二進位是什麼？手算一次。"],
  gate=G(["d027", "d021"], 45, 2))

U(0, 1, "二維 list 與簡單模擬", "能建立與走訪二維陣列，並把一串指令模擬成狀態變化。",
  ["二維 list：`[[0]*C for _ in range(R)]`（不要寫成 `[[0]*C]*R`）", "走訪列與行；轉置；`zip(*a)`",
   "模擬題的標準步驟：讀指令 → 修改狀態 → 輸出"],
  drills=["d026"], res=["pytut", "pytutor"],
  pitfalls=["`[[0]*C]*R` 會讓所有列是同一個 list（在 Python Tutor 畫出來看看）"],
  check=["為什麼 `[[0]*3]*3` 改一格會全變？"],
  gate=G(["d030", "d026"], 45, 2))

U(0, 1, "階段 0 驗收週", "不看資料，90 分鐘內從空白檔重寫 4 題舊題，建立『我真的會』的證據。",
  ["回顧本階段所有被你用過提示的題目（`cpe review`）", "整理一頁筆記：10 個最常用的寫法（讀 EOF、set 計數、排序 key…）",
   "學會 debug：用 print 檢查中間值；縮小問題；寫最小測資"],
  pool=["補完 ZeroJudge 入門題到累計約 60 題（報告的階段 0 目標是 80–120 題）"],
  res=["zj"],
  check=["你最不熟的三個語法是什麼？明天各寫一個小程式練習。"],
  gate=G(["d014", "d020", "d022", "d013"], 120, 3))

# ======================= 階段 1：競程 I/O 與一顆星（第 13–28 週）=======================
U(1, 2, "競程輸入格式", "能處理 CPE 常見的五種輸入格式：EOF、0 0 結束、先給組數、空行分隔、一行多資料。",
  ["`sys.stdin.read().split()` 一次讀完 vs 逐行讀：何時用哪個", "結束標記（`0 0`、單個 `0`）；先給組數 t；空行分隔的群組",
   "輸出格式：Case 標題、組間空行 vs 每組後空行（PE 的最大來源）", "把輸入格式寫在註解裡再開始寫程式的習慣"],
  drills=["d031", "d032", "d033"], anchors=["uva11172", "uva10055", "uva100"],
  pool=["CSES『Introductory Problems』挑解題人數最多的 10 題（練習純標準輸入輸出）"],
  res=["cses", "cpe"],
  pitfalls=["`0 0` 之後還有資料時必須 break", "最後一組之後的空行"],
  check=["什麼情況下不能用 `read().split()`？"],
  gate=G(["d034", "d031"], 60, 2))

U(1, 2, "輸出格式、浮點數與字串映射", "能精準控制輸出格式，並用 dict／查表處理映射類題目。",
  ["`f'{x:.4f}'`、`:>8`、`:02d`；round 的銀行家捨入陷阱", "用 dict 或字串做映射（羅馬數字、摩斯碼、鍵盤位移）", "字串分組掃描（run-length）與『最後一段』的收尾",
   "整數運算優於浮點運算：能用整數比大小就別用除法"],
  drills=["d035", "d039", "d043"], anchors=["uva10082", "uva10420", "uva10226", "uva10282", "uva10062"],
  res=["pytut"],
  pitfalls=["Python 的 round(2.5) 是 2", "分組掃描忘了輸出最後一組"],
  check=["`f'{0.125:.2f}'` 是多少？為什麼？"],
  gate=G(["d045", "d043"], 60, 2))

U(1, 2, "大數與進位制", "善用 Python 大整數，熟練各種進位制轉換。",
  ["Python int 沒有上限（但 3.11 起字串轉換有 4300 位的限制，考場 3.9 沒有）", "任意進位：`int(s, b)` 與手寫轉換", "字串反轉相加類題目（Reverse and Add）",
   "二進位位元計數與 `bin()`"],
  drills=["d036"], anchors=["uva10106", "uva713", "uva10220", "uva10929", "uva10931", "uva10018", "uva10035"],
  res=["pytut"],
  pitfalls=["前導零", "把大數轉成 float 會丟失精度"],
  check=["為什麼 C++ 解大數題要自己實作，而 Python 不用？"],
  gate=G(["d037", "d036"], 60, 2))

U(1, 2, "質數、因數與數學觀察", "能用篩法預處理，並把數學觀察寫成程式（根號、完全平方、數根）。",
  ["埃拉托斯特尼篩法；『先預處理、再 O(1) 查詢』", "因數成對找到 √n；完全平方數的因數個數是奇數", "數根（digital root）、平方數個數 isqrt 公式",
   "遇到數學題先手算小例子找規律"],
  drills=["d038"], anchors=["uva10110", "uva11461", "uva11332", "uva10300", "uva10071", "uva11364", "uva10190"],
  res=["cpalgo"],
  pitfalls=["對每個查詢重算一次篩法"],
  check=["篩法為什麼從 i*i 開始劃掉倍數？"],
  gate=G(["d038", "d025"], 45, 2))

U(1, 2, "網格與座標模擬", "會用方向陣列與邊界檢查模擬二維世界。",
  ["方向陣列 `dirs=[(0,1),(1,0),(0,-1),(-1,0)]` 與轉向（%4）", "邊界檢查 `0<=nx<R and 0<=ny<C`", "鄰居計數（八方向，如踩地雷）",
   "把『題目的規則』逐條翻成程式，不要跳步"],
  drills=["d041", "d042"], anchors=["uva10189", "uva11581", "uva11498", "uva11559", "uva11150", "uva10038"],
  res=["pytutor"],
  pitfalls=["x、y 與列、行的對應（先寫在註解裡）", "斜向鄰居漏掉"],
  check=["螺旋矩陣為什麼用『遇到牆或已填過就轉向』？"],
  gate=G(["d042", "d041"], 60, 2))

U(1, 2, "日期、時間與運算式解析", "會處理日期／時間計算與字串解析（token 化）。",
  ["datetime.date 與 weekday()；也要會用 Zeller 公式自己算", "進位換算（秒→時分秒）、12/24 小時制邊界", "split 後依 token 處理的解析模式"],
  drills=["d040", "d044"], pool=["UVA 上日期／時間類一顆星題：用 `cpe add` 登記後練習"],
  res=["pytut"],
  pitfalls=["0 點與 12 點的邊界"],
  check=["2000 與 1900 為什麼閏年規則不同？"],
  gate=G(["d040", "d044"], 60, 2))

U(1, 2, "一顆星選集 I", "到 CPE 官網取得『一顆星選集』49 題，完成前 25 題。",
  ["用 `cpe import <題號> <題目文字檔>` 把題目與範例匯入（見 README）", "養成習慣：每題先在註解寫輸入格式、輸出格式、範圍；通過後寫下『這題的陷阱』",
   "每週至少 2 題用英文原題（考場題目是英文，有英文字典可用）"],
  pool=["一顆星選集 前 25 題（官網）", "CPE 歷屆 一～二顆星且全體答對率高於 30% 的題目"],
  res=["cpe"],
  check=["用英文複述一題題意給自己聽。"],
  gate=G(["e101", "e102", "e103"], 90, 2))

U(1, 2, "階段 1 驗收：一顆星選集 II 與首次報考", "完成一顆星 49 題；報考第一次 CPE（大專生免費），目標 1–2 題。",
  ["完成選集剩下題目；全部題目能在 30 分鐘內重寫", "考前一週模擬：`cpe mock start --kind short`（3 題 90 分鐘）",
   "考試當天流程：報到、環境測試、題目英文、ICPC 計分（錯一次加 20 分鐘）——先做會的題"],
  pool=["一顆星選集 後 24 題", "報名：查 CPE 官網的最新場次與報名日期"],
  res=["cpe"],
  check=["考場上看到完全沒頭緒的題，你的第一步是什麼？"],
  gate=M("short", 2))

# ======================= 階段 2：資料結構與基礎演算法（第 29–44 週）=======================
U(2, 2, "複雜度估算與排序", "能在寫程式前估算複雜度，並熟練多重條件排序。",
  ["Big-O：O(n)、O(n log n)、O(n²)；『Python 約每秒 10^7 次簡單運算』的粗估法；看範圍倒推演算法",
   "sort 的 key、多重條件、穩定排序；自訂比較（cmp_to_key）", "計數排序（值域小時）", "開始建 Git 習慣：每天的程式碼 commit"],
  drills=["d049"], anchors=["uva10041", "uva11727", "uva11942", "uva11462"],
  pool=["CSES『Sorting and Searching』挑解題人數最多的 8 題"],
  res=["cphb", "cses", "visualgo"],
  eng=[1],
  pitfalls=["字串排序是字典序，'10' < '9'", "忘了先轉成 int 再排序"],
  check=["n=10^5 時 O(n²) 為什麼不行？n=10^3 呢？"],
  gate=G(["d049", "d028"], 60, 2))

U(2, 2, "前綴和與二分搜尋", "會用前綴和處理區間查詢，並正確寫出二分搜尋。",
  ["前綴和：pre[i]；區間和 = pre[r]-pre[l-1]；二維前綴和（選修）", "二分搜尋：lower_bound / upper_bound 語意；迴圈不變量；`bisect` 模組",
   "『對答案二分』的入門概念（最小化最大值）"],
  drills=["d046", "d047"], anchors=["uva10474"],
  pool=["CSES『Sorting and Searching』中標示二分或前綴和的題目", "AP325 對應章節"],
  res=["cphb", "cpalgo", "visualgo"],
  eng=[2],
  pitfalls=["l、r 的開閉區間不一致造成無窮迴圈", "前綴和下標差一"],
  check=["lower_bound 與 upper_bound 的差別？", "二分時 `mid=(l+r)//2` 與 `l=mid` 會有什麼問題？"],
  gate=G(["d046", "d047"], 60, 2))

U(2, 1, "雙指標與滑動視窗", "能用雙指標把 O(n²) 降成 O(n)。",
  ["排序後雙指標（兩端往內）；同向雙指標（滑動視窗）", "證明為什麼指標只需要單向移動"],
  drills=["d048"], anchors=["uva11057", "uva10340"], res=["cpalgo"],
  pitfalls=["指標移動條件寫反造成漏解"],
  check=["d048 為什麼 a[l]+a[r]≤K 時可以一次加 r-l 對？"],
  gate=G(["d048", "d047"], 45, 2))

U(2, 2, "stack、queue 與 deque", "會用資料結構模擬題目，並辨識『後進先出』與『先進先出』場景。",
  ["stack（list）、queue / deque（`collections.deque`）；括號配對、單調 stack／deque", "模擬類題目（Rails、Ferry Loading）", "找規律取代模擬（約瑟夫）"],
  drills=["d050", "d051", "d053"], anchors=["uva673", "uva514", "uva10901", "uva11995", "uva10935", "uva12100"],
  res=["visualgo", "cpalgo"], eng=[3],
  pitfalls=["list.pop(0) 是 O(n)，要用 deque", "空 stack 時 pop"],
  check=["什麼題目看到就該想到 stack？單調 deque 怎麼維持單調？"],
  gate=G(["d050", "d053"], 90, 2))

U(2, 1, "heap 與優先佇列", "會用 heapq 與 dict 做動態維護最小／中位數。",
  ["heapq：heappush / heappop / heapify；max-heap 用負數", "貪心 + heap（合併最小兩個）", "動態中位數（bisect.insort 或雙 heap）"],
  drills=["d052"], anchors=["uva10954", "uva10107", "uva11136"], res=["cpalgo", "visualgo"],
  pitfalls=["heapq 只有最小堆積", "tuple 比較：第一個欄位相同時會比第二個"],
  check=["為什麼 heap 取最小是 O(log n)，而 list 取最小是 O(n)？"],
  gate=G(["d052", "d020"], 60, 2))

U(2, 2, "貪心演算法", "會判斷貪心是否成立，並用交換論證說服自己。",
  ["貪心的典型：區間排程（依結束時間）、區間覆蓋、配對（排序後雙指標）、Huffman（heap）", "怎麼證明：交換論證——假設最優解跟你的選擇不同，換成你的選擇不會變差",
   "反例思維：寫完貪心後，用 5 分鐘找反例"],
  drills=["d054"], anchors=["uva10020", "uva10026", "uva11389", "uva10037"], res=["cphb", "cpalgo"],
  pitfalls=["排序依據選錯", "貪心看似合理但有反例（零錢兌換）"],
  check=["活動選擇為什麼依結束時間排序而不是開始時間？"],
  gate=G(["d055", "d054"], 75, 2))

U(2, 3, "遞迴與回溯", "能寫出遞迴、窮舉與剪枝，並估算搜尋空間。",
  ["遞迴三要素：終止條件、縮小問題、合併結果；呼叫堆疊（用 Python Tutor 看）", "回溯：選擇 → 遞迴 → 還原；全排列、N 皇后、子集合",
   "剪枝：提早放棄不可能的分支；可行性剪枝與最優性剪枝", "`sys.setrecursionlimit` 與遞迴深度的限制"],
  drills=["d056", "d057"], anchors=["uva750", "uva524", "uva10344", "uva624"], res=["pytutor", "cphb"],
  pitfalls=["忘了『還原』狀態", "沒有剪枝造成指數爆炸"],
  check=["N 皇后為什麼用 r-c 與 r+c 判斷斜線？"],
  gate=G(["d056", "d057"], 75, 2))

U(2, 2, "位元運算與子集合枚舉", "會用 bitmask 表示集合並枚舉所有子集合。",
  ["& | ^ ~ << >> 與常用技巧（判斷第 i 位、設定、清除、lowbit）", "n≤20 時 `for mask in range(1<<n)` 枚舉子集合", "XOR 的性質（a^a=0）"],
  drills=["d058", "d059"], anchors=[], pool=["CSES『Introductory Problems』中位元／子集合相關題目"], res=["cphb", "cpalgo"],
  pitfalls=["`1 << i` 的優先順序：要加括號 `(mask >> i) & 1`"],
  check=["`mask & (-mask)` 取出什麼？"],
  gate=G(["d058", "d059"], 60, 2))

U(2, 1, "階段 2 驗收週", "累積 3 題以上的實力：模擬考至少 3 題。這週並報考 APCS 或 CPE。",
  ["整理錯題本：每個錯誤分類（格式／邊界／演算法／超時／粗心）", "完整 3 小時模擬考一次，然後逐題檢討", "報考 CPE：目標 3 題（A- 進階級）"],
  pool=["APCS 實作題（中級～中高級）歷屆題：ZeroJudge 有收錄"], res=["zj", "yizhe"],
  eng=[4],
  check=["上次考試你在哪一題花最多時間？下次怎麼避免？"],
  gate=M("mock", 3))

# ======================= 階段 3：圖論與 DP（第 45–70 週）=======================
U(3, 2, "圖的表示與 BFS / DFS", "會建圖、BFS 求最短步數、DFS 找連通區域，並避免遞迴過深。",
  ["鄰接表 `adj=[[] for _ in range(n+1)]`；鄰接矩陣；有向／無向／加權", "BFS：用 deque、dist 初始 -1、每點只入隊一次；格子 BFS", "DFS：遞迴與迭代（用 stack）；flood fill；二分圖著色",
   "Python 遞迴深度限制：大圖一律寫迭代"],
  drills=["d060"], anchors=["uva572", "uva336", "uva10009", "uva10004", "uva439", "uva10653"],
  pool=["CSES『Graph Algorithms』前幾題（Counting Rooms、Labyrinth）"], res=["cphb", "cpalgo", "visualgo"],
  pitfalls=["入隊時才標記 visited，而不是出隊時", "多組測資忘了清空圖"],
  check=["BFS 為什麼能保證最短？邊有權重時還成立嗎？"],
  gate=G(["d060", "d056"], 60, 2))

U(3, 2, "並查集與連通元件", "能用並查集處理動態連通性。",
  ["Union-Find：路徑壓縮 + 按大小合併；維護集合大小", "離線處理：先排序再合併（Kruskal 的基礎）", "字串節點→編號的 dict"],
  drills=["d061"], anchors=["uva10608", "uva459", "uva11503", "uva11902"], res=["cpalgo", "visualgo"],
  pitfalls=["find 忘了壓縮造成退化成鏈", "把 a、b 本身而不是它們的根拿去比大小"],
  check=["為什麼並查集查詢近似 O(1)？"],
  gate=G(["d061", "d060"], 60, 2))

U(3, 2, "拓撲排序與 DAG", "能判斷有向圖有無環並求合法順序。",
  ["Kahn 演算法（入度）與 DFS 後序；字典序最小要用 heap", "DAG 上的 DP（最長路徑）", "依賴關係題：先建圖再想順序"],
  drills=["d062"], anchors=["uva10305", "uva11060", "uva10926"], res=["cpalgo", "visualgo"],
  pitfalls=["重邊影響入度計算", "有環時的輸出"],
  check=["Kahn 演算法怎麼判斷有環？"],
  gate=G(["d062", "d061"], 60, 2))

U(3, 3, "最短路徑", "會 Dijkstra（堆積版）、Floyd，並能依題目規模選擇。",
  ["Dijkstra：dist + heapq、lazy deletion；為什麼不能有負權", "Floyd–Warshall：k 在最外層；O(n³) 適用 n≤400（C++）／n≤100（Python）", "變形：最小化最大邊（minimax）、多源最短路、路徑還原"],
  drills=["d063", "d065"], anchors=["uva10986", "uva341", "uva10171", "uva567", "uva821", "uva10099", "uva10048"],
  pool=["CSES『Graph Algorithms』最短路徑題"], res=["cpalgo", "visualgo", "cphb"],
  pitfalls=["Floyd 迴圈順序", "把 INF 設太小造成加法後溢位判斷錯"],
  check=["Dijkstra 的 lazy deletion 是什麼意思？"],
  gate=G(["d063", "d065"], 75, 2))

U(3, 2, "最小生成樹", "會 Kruskal，並理解 MST 的應用。",
  ["Kruskal：邊排序 + 並查集；Prim：堆積版", "MST 的性質（切割性質、環性質）", "變形：總長減去 MST、次小生成樹（選修）"],
  drills=["d064"], anchors=["uva10034", "uva11631", "uva10147", "uva11747"], res=["cpalgo", "visualgo"],
  eng=[5],
  pitfalls=["圖不連通時的處理", "歐氏距離不要提前開根號比大小以外的地方"],
  check=["為什麼 Kruskal 選到 n-1 條邊就可以停？"],
  gate=G(["d064", "d063"], 75, 2))

U(3, 2, "DP 入門：一維 DP 與零錢", "能定義 dp 狀態、寫出轉移式，區分『計數』與『最佳化』。",
  ["DP 的四步：定義狀態 → 轉移式 → 初始值 → 答案在哪", "最大子段和（Kadane）、爬樓梯、零錢（最少枚數／組合數）", "迴圈順序決定『組合』或『排列』", "貪心 vs DP：何時貪心會錯"],
  drills=["d071", "d067"], anchors=["uva674", "uva357", "uva10684", "uva507", "uva10465"],
  pool=["CSES『Dynamic Programming』前 6 題"], res=["cphb", "cpalgo"],
  eng=[6],
  pitfalls=["初始值（尤其是 -inf 與 0）", "狀態定義含糊"],
  check=["零錢『組合數』與『排列數』的程式差在哪一行？"],
  gate=G(["d066", "d067"], 75, 2))

U(3, 2, "背包問題", "會 0/1 背包、完全背包與它們的變形。",
  ["0/1 背包（容量逆序）、完全背包（容量順序）、恰好裝滿 vs 不超過", "子集合和、分割等和問題的背包化", "二維→一維滾動陣列"],
  drills=["d068"], anchors=["uva10130", "uva562", "uva11450"], pool=["CSES『Dynamic Programming』背包類題"], res=["cphb", "cpalgo"],
  pitfalls=["0/1 與完全背包的迴圈方向", "狀態維度太大（W 高達 10^9 時不能用）"],
  check=["為什麼 0/1 背包的容量要由大到小？"],
  gate=G(["d068", "d066"], 75, 2))

U(3, 2, "序列 DP：LIS 與 LCS", "會 LIS（含 O(n log n)）、LCS，並能還原路徑。",
  ["LIS O(n²) 與 O(n log n)（tails + bisect）；嚴格 vs 非嚴格", "LCS 二維表；編輯距離；路徑還原（前驅陣列）", "滾動陣列省空間"],
  drills=["d070", "d069"], anchors=["uva10131", "uva10405", "uva10192"], res=["cphb", "cpalgo"],
  pitfalls=["LIS 嚴格遞增用 bisect_left，非嚴格用 bisect_right", "輸出路徑時順序"],
  check=["tails 陣列中的值代表什麼？"],
  gate=G(["d069", "d070"], 75, 2))

U(3, 2, "網格 DP", "能處理網格上的最短／最佳路徑與計數。",
  ["dp[i][j] 由上與左轉移；邊界處理", "字典序最小路徑要由後往前 DP（Unidirectional TSP）", "有障礙、有權重、可繞回（列循環）的變形"],
  drills=["d072"], anchors=["uva116", "uva825", "uva10337"], res=["cphb"],
  pitfalls=["第一列／第一行的初始化", "路徑平手時的規則"],
  check=["為什麼求字典序最小路徑要倒著做 DP？"],
  gate=G(["d072", "d071"], 60, 2))

U(3, 2, "區間 DP", "能辨識並寫出區間 DP。",
  ["狀態 dp[l][r]；依區間長度由小到大計算；枚舉分割點", "矩陣連乘、切木棍、最佳二元搜尋樹、取兩端博弈", "O(n³) 的規模：Python n≈100 內，C++ n≈400 內"],
  drills=["d073"], anchors=["uva10003", "uva10304", "uva10891"], res=["cphb", "cpalgo"],
  pitfalls=["迴圈順序（先枚舉長度）"],
  check=["為什麼切木棍要把切點當端點？"],
  gate=G(["d073", "d072"], 75, 2))

U(3, 2, "位元遮罩 DP", "能用 bitmask 表示『已選集合』並做 DP。",
  ["dp[mask][i]；O(2^n · n²)；n≤20 的訊號", "旅行推銷員、指派問題、完美匹配", "固定最低位未選者來避免重複計數"],
  drills=["d074"], anchors=["uva10911", "uva10032"], res=["cphb", "cpalgo"],
  pitfalls=["Python 在 n=15 就很吃力——這是學 C++ 的動機"],
  check=["為什麼『固定最低位』能避免重複配對？"],
  gate=G(["d074", "d058"], 75, 2))

U(3, 2, "數論：模運算、質因數與組合數", "會模運算、快速冪、模逆元、質因數分解與組合數預處理。",
  ["模運算規則；快速冪 `pow(a,b,m)` 與手寫；費馬小定理求逆元", "質因數分解（試除、篩法最小質因數）；歐拉函數", "組合數取模：階乘 + 逆元階乘預處理；帕斯卡三角形",
   "擴展歐幾里得（選修）"],
  drills=["d075", "d093"], anchors=["uva374", "uva10104", "uva10127", "uva583"], res=["cpalgo", "cphb"],
  pitfalls=["減法取模要 `(a-b)%M` 再保證非負", "乘法前先取模避免大數變慢（Python）／溢位（C++）"],
  check=["為什麼費馬小定理只在模數是質數時可用？"],
  gate=G(["d075", "d038"], 75, 2))

U(3, 1, "階段 3 驗收週", "累積 4 題以上的實力：完整模擬考至少 4 題，並報考 CPE。",
  ["完整 3 小時模擬；逐題檢討：為什麼沒做出來？缺知識／缺技巧／沒時間／粗心", "報考 CPE：目標 4 題（A 專業級）", "完成一個含 pytest 的 CLI 小專案（工程任務）"],
  pool=["Codeforces rating 800–1300，各 tag 各 5 題"], res=["cf", "atcoder"], eng=[7],
  check=["寫下你目前最弱的三個主題。"],
  gate=M("mock", 4))

# ======================= 階段 4：進階演算法與 C++（第 71–100 週）=======================
U(4, 4, "C++ 入門與翻譯舊題", "能用 C++ 通過 Python 解過的題目。",
  ["安裝 g++（Linux/Mac 內建；Windows 用 MinGW/MSYS2）；`g++ -O2 -std=c++17`", "競程模板：`ios::sync_with_stdio(false); cin.tie(nullptr);`；`int` vs `long long`（溢位！）",
   "輸入輸出、vector、string、迴圈、函式、引用；讀到 EOF：`while (cin >> x)`", "對照翻譯：每題先看自己的 Python 解，再逐行翻成 C++",
   "常見落差：整數除法對負數向零取整（Python 是向下取整）、陣列越界不報錯、未初始化變數"],
  drills=["d018", "d021", "d022", "d031", "d049"], anchors=[], res=["learncpp", "cppref"], lang="cpp",
  pitfalls=["int 溢位（乘法前先轉 long long）", "忘了 `\\n` 或 `endl`（endl 很慢）"],
  check=["`-7 / 2` 與 `-7 % 3` 在 C++ 是多少？和 Python 一樣嗎？"],
  gate=G(["d046", "d054"], 90, 2, "cpp"))

U(4, 4, "C++ STL", "能用 STL 容器與演算法寫出標準解。",
  ["vector、sort（含 lambda）、lower_bound / upper_bound、unique", "set / map / unordered_map、priority_queue（預設最大堆積）、deque / stack / queue、pair / tuple、bitset",
   "複雜度：map 是 O(log n)，unordered_map 平均 O(1)", "把 d047、d052、d053、d060、d063、d064 都用 C++ 重寫"],
  drills=["d047", "d052", "d053", "d060", "d063", "d064"], anchors=[], res=["cppref", "learncpp"], lang="cpp",
  pitfalls=["`priority_queue` 預設是最大堆積", "迭代時修改容器造成未定義行為"],
  check=["Python 的 heapq 與 C++ 的 priority_queue 差別是什麼？"],
  gate=G(["d063", "d076"], 90, 2, "cpp"))

U(4, 4, "效能與複雜度", "能在動手前估算是否會超時，並選對語言與演算法。",
  ["10^8 規則：C++ 約 10^8 次簡單運算／秒；Python 約 10^7", "記憶體估算：int 4 byte、long long 8 byte；10^7 個 int = 40MB", "快速 I/O；避免 endl；預先配置陣列",
   "把『Python 超時』的題（d076–d079）全部翻成 C++ 並通過"],
  drills=["d076", "d077", "d078"], anchors=[], res=["cphb", "cppref"], lang="cpp",
  pitfalls=["在迴圈內重複建立大型物件", "多組測資忘了重設陣列"],
  check=["n=2×10^5、q=2×10^5 時哪些演算法可行？"],
  gate=G(["d079", "d077"], 90, 2, "cpp"))

U(4, 4, "計算幾何", "能處理點、線段、多邊形的基本運算且不被邊界情況擊倒。",
  ["向量、叉積（方向）、點積；三點共線；整數幾何優先", "線段相交（含端點、共線）；點在多邊形內（射線法）；多邊形面積（鞋帶公式）", "凸包（Andrew monotone chain）",
   "浮點誤差：eps 的使用；盡量用整數"],
  drills=["d082", "d081", "d080"], anchors=["uva191", "uva378", "uva11437", "uva681", "uva11626", "uva10065"], res=["cpalgo"],
  pitfalls=["共線點是否保留", "退化成點的線段"],
  check=["叉積的符號代表什麼？"],
  gate=G(["d080", "d082"], 90, 2))

U(4, 4, "進階圖論", "會處理負權、強連通分量與（選修）網路流。",
  ["Bellman-Ford 與負環偵測；SPFA 的風險", "強連通分量（Kosaraju / Tarjan）；縮點成 DAG", "最大流入門（Edmonds–Karp）——CPE 少考，建立概念即可", "無向圖的橋與關節點（選修）"],
  drills=["d088", "d089", "d090"], anchors=[], res=["cpalgo", "visualgo"], lang="py",
  pitfalls=["遞迴 DFS 在大圖會爆", "負環『可達』條件"],
  check=["為什麼 Dijkstra 遇到負權會錯？"],
  gate=G(["d089", "d088"], 90, 2))

U(4, 4, "字串演算法與解析", "會 KMP／前綴函數、迴文，以及遞迴下降解析。",
  ["前綴函數（KMP 失敗函數）與週期；Z 函數（選修）", "迴文：中心擴展、Manacher", "字串雜湊（選修）；Trie（選修）", "運算式解析：遞迴下降（expr / term / factor）"],
  drills=["d083", "d084"], anchors=["uva10010", "uva401", "uva11221", "uva10115"], res=["cpalgo"],
  pitfalls=["把字串切片放在迴圈裡造成 O(n²)"],
  check=["前綴函數 pi[i] 的定義？n - pi[n-1] 為什麼是最短週期？"],
  gate=G(["d095", "d083"], 90, 2))

U(4, 4, "進階 DP、樹與博弈", "能做樹 DP、數位 DP 與博弈 DP。",
  ["樹 DP（選／不選）、換根（選修）；用迭代避免遞迴深度問題", "數位 DP：貼上界旗標 tight", "博弈 DP：必勝／必敗狀態、Nim（選修）", "格子路徑計數與取模"],
  drills=["d085", "d091", "d094"], anchors=["uva10404"], res=["cphb", "cpalgo"],
  pitfalls=["數位 DP 的『0 是否計入』", "遞迴狀態沒有記憶化"],
  check=["tight 旗標為什麼只在前面都貼著上界時才為真？"],
  gate=G(["d092", "d085"], 90, 2))

U(4, 1, "進階資料結構", "會稀疏表、BIT、分治計數。",
  ["Sparse Table（RMQ）；樹狀陣列 BIT；線段樹（選修）", "分治：合併排序算逆序對", "座標壓縮"],
  drills=["d086", "d087"], anchors=[], res=["cpalgo", "cphb"], lang="cpp",
  pitfalls=["BIT 的下標從 1 開始", "答案可能超過 int"],
  check=["逆序對為什麼可以在 merge 時順便算？"],
  gate=G(["d086", "d087"], 90, 2, "cpp"))

U(4, 1, "階段 4 驗收週", "累積 5 題的實力：完整模擬考至少 5 題，並報考 CPE。",
  ["完整 3 小時模擬考；用 C++ 解需要效能的題、用 Python 解實作題", "報考 CPE：目標 5 題（A 專業級上緣）"],
  pool=["CPE 歷屆三、四顆星題，按答對率排序，由高到低"], res=["cpe"],
  check=["你在考場上如何決定這題用 Python 還是 C++？"],
  gate=M("mock", 5))

# ======================= 階段 5：衝刺 6 題（第 101–126 週）=======================
U(5, 4, "考試策略與工具箱", "把『會做』變成『考場上做得出來』。",
  ["考場流程：先花 5 分鐘掃過所有題，從最簡單的開始（前三題通常最簡單）", "時間分配：前 3 題 ≤ 60 分鐘；卡住 20 分鐘就換題", "自己的模板：C++ 模板、Python I/O 模板、對拍腳本",
   "除錯清單：邊界、溢位、初始化、多組測資是否清空、輸出格式", "用 `cpe stress` 對拍找反例；用 `cpe mock start` 每週一場"],
  pool=["每週一場完整模擬（3 小時），賽後必檢討每一題"], res=["cpe"],
  check=["你的考場 SOP 是什麼？寫成一張卡片。"],
  gate=M("mock", 4))

U(5, 6, "弱點修補", "用統計找出最弱的三個主題，針對性補強。",
  ["`cpe stats` 看哪類題無提示重寫通過率最低", "每個弱點主題：重讀教材 → 做 10 題 → 重寫 → 考試", "整理『錯題本』：每題寫下最初的錯誤想法與正確想法"],
  pool=["CPE 歷屆全體答對率 5%–20% 的題目", "Codeforces rating 1200–1600，指定弱點 tag"], res=["cpe", "cf"],
  check=["你的弱點主題清單與補強計畫。"],
  gate=M("mock", 5))

U(5, 8, "低答對率題攻堅", "能解全國答對率 5% 以下的題目。",
  ["歷屆題中，答對率低於 5% 的題目通常是進階 DP／圖論／幾何／長模擬", "做法：限時 60 分鐘 → 失敗後走提示階梯 → 24 小時後重寫", "建立題型卡片：看到什麼特徵 → 想到什麼演算法"],
  pool=["CPE 歷屆三、四顆星題全部（約 4 場／年 × 2 題）", "Codeforces rating 1400–1800"], res=["cpe", "cf"],
  check=["這類題的共同點是什麼？你的下一步行動？"],
  gate=M("mock", 5))

U(5, 6, "全真模擬週", "穩定做到 6 題。每週一場完整模擬，連續多場達標。",
  ["每週一場 3 小時全真模擬（ICPC 計分），賽後 2 小時檢討", "模擬環境：關閉 AI 與搜尋、只開字典；用考場同版本 Python 3.9", "目標：連續 3 場至少 2 場達到 6 題"],
  pool=["自己出模擬：`cpe mock start`；也用歷屆題組出整場"], res=["cpe"],
  eng=[8, 9, 10],
  check=["最近三場模擬的題數與罰時趨勢？"],
  gate=M("mock", 6))

U(5, 2, "報考與作品集", "實際報考；完成作品集，把競程能力轉成求職能力。",
  ["考前一週清單：睡眠、環境測試、模板、字典", "整理作品集：3 個專案（含 README、測試、說明）；把這個學習系統本身整理成作品", "規劃下一步：實習、LeetCode／系統設計、專案經驗"],
  pool=[], res=["progit"], eng=[11],
  check=["寫下你報考的日期與目標題數。"],
  gate=None)


# 每個單元『讀哪裡』：章節編號依官方教材／書籍目錄為準，若有出入請以標題搜尋。
CPH = "Competitive Programmer's Handbook"
PYT = "Python 官方教學"
READ = {
    1: [f"{PYT} 第 3 章『非正式介紹』、第 7.1 節『格式化輸出』"],
    2: [f"{PYT} 4.1『if 陳述式』"],
    3: [f"{PYT} 4.2–4.5『for、range()、break／continue』"],
    4: [f"{PYT} 3.1.2『字串』、3.1.3『List』、5.1『List 詳解』"],
    5: [f"{PYT} 5.4『集合』、5.5『字典』、4.x『定義函式』", "標準函式庫 collections.Counter 的說明"],
    6: [f"{PYT} 4.x『定義函式』"],
    7: [f"{PYT} 5.1.3『List Comprehension』（巢狀）"],
    13: ["Python 文件：sys.stdin"], 16: ["CPE 官網『考生使用手冊』（含 Python I/O 範例）"],
    17: [f"{CPH} 第 2 章『Time complexity』、第 3 章『Sorting』"],
    18: [f"{CPH} 第 3 章（Binary search）、第 9 章『Range queries』（Static array queries）"],
    19: [f"{CPH} 第 8 章『Amortized analysis』（Two pointers）"],
    20: [f"{CPH} 第 4 章『Data structures』（Deque、Stack）"],
    21: [f"{CPH} 第 4 章（Priority queues）"],
    22: [f"{CPH} 第 6 章『Greedy algorithms』"],
    23: [f"{CPH} 第 5 章『Complete search』"],
    24: [f"{CPH} 第 10 章『Bit manipulation』"],
    26: [f"{CPH} 第 11 章『Basics of graphs』、第 12 章『Graph traversal』"],
    27: [f"{CPH} 第 15 章『Spanning trees』（Union-find）"],
    28: [f"{CPH} 第 16 章『Directed graphs』（Topological sorting）"],
    29: [f"{CPH} 第 13 章『Shortest paths』"],
    30: [f"{CPH} 第 15 章『Spanning trees』（Kruskal、Prim）"],
    31: [f"{CPH} 第 7 章『Dynamic programming』（Coin problem）"],
    32: [f"{CPH} 第 7 章（Knapsack）"],
    33: [f"{CPH} 第 7 章（Longest increasing subsequence、Edit distance）"],
    34: [f"{CPH} 第 7 章（Paths in a grid）"],
    35: [f"{CPH} 第 7 章；搜尋『interval DP』"],
    36: [f"{CPH} 第 7 章（Counting tilings 之前的 bit 技巧）；搜尋『bitmask DP』"],
    37: [f"{CPH} 第 21 章『Number theory』、第 22 章『Combinatorics』"],
    39: ["learncpp.com 第 0–8 章"], 40: ["cppreference：<vector>、<algorithm>、<set>、<map>、<queue>"],
    42: [f"{CPH} 第 29 章『Geometry』"],
    43: [f"{CPH} 第 17 章『Strong connectivity』、第 20 章『Flows and cuts』"],
    44: [f"{CPH} 第 26 章『String algorithms』"],
    45: [f"{CPH} 第 14 章『Tree algorithms』、第 25 章『Game theory』"],
    46: [f"{CPH} 第 9 章『Range queries』、第 28 章『More segment trees』"],
}
for _i, _u in enumerate(UNITS, 1):
    _u["read"] = READ.get(_i, [])
