"""階段 0：Python 語法基礎（30 題）。"""
from common import D, lines, rng

# ---- 輸入輸出與運算 ----
D("d001", "打招呼", 0, "輸入輸出",
  "讀入一行名字，輸出 `Hello, 名字!`。",
  "一行，名字（英文字母，長度 ≤ 20）。", "一行問候語。",
  "輸入輸出", "用 input() 讀一行；f-string 或 + 串接字串；注意結尾的驚嘆號。",
  "print(f'Hello, {input().strip()}!')",
  ["Alice\n", "Bob\n", "Python\n"],
  "input() 與 print()、字串格式化。")

D("d002", "多組相加", 0, "輸入輸出／EOF",
  "輸入有很多行，每行兩個整數 a b。對每一行輸出 a+b。",
  "不知道有幾行，讀到檔案結尾（EOF）為止。|a|,|b| ≤ 10^18。", "每行一個答案。",
  "多組輸入讀到 EOF", "用 `for line in sys.stdin:` 一行一行讀，split() 切開再轉 int。",
  "import sys\nfor l in sys.stdin:\n    p=l.split()\n    if p: print(int(p[0])+int(p[1]))",
  ["1 2\n", "100 -250\n3 4\n0 0\n", "123456789012345678 987654321098765432\n-5 -7\n", "0 0\n"],
  "競程最常見的輸入形式：讀到 EOF。Python 的 int 不會溢位。")

D("d003", "長方形", 0, "運算",
  "給長 w 與寬 h，輸出面積與周長，中間用一個空格隔開。",
  "一行兩個正整數 w h（≤ 10^6）。", "一行：面積 周長。",
  "基本運算", "面積 = w*h，周長 = 2*(w+h)；用 map(int, input().split()) 讀兩個數。",
  "w,h=map(int,input().split())\nprint(w*h,2*(w+h))",
  ["3 4\n", "1 1\n", "1000000 999999\n"],
  "map、多變數賦值、print 以空格分隔多個值。")

D("d004", "攝氏轉華氏", 0, "運算／格式化",
  "對每個攝氏溫度 C（整數），輸出華氏溫度 F = C×9/5+32，小數點後 1 位。",
  "每行一個整數 C（-100 ≤ C ≤ 100），讀到 EOF。", "每行一個答案。",
  "浮點數輸出格式", "用 f'{x:.1f}' 控制小數位數；先乘 9 再除 5。",
  "import sys\nfor l in sys.stdin:\n    if l.strip(): print(f'{int(l)*9/5+32:.1f}')",
  ["0\n", "100\n-40\n37\n", "-100\n99\n1\n"],
  "格式化輸出 `:.1f`。")

# ---- 條件 ----
D("d005", "奇偶", 0, "條件判斷",
  "判斷整數 n 是奇數還是偶數，輸出 `odd` 或 `even`。",
  "每行一個整數 n（|n| ≤ 10^9，可能是負數或 0），讀到 EOF。", "每行 odd 或 even。",
  "條件判斷／取餘數", "用 n % 2；Python 對負數取餘數的結果是 0 或 1。",
  "import sys\nfor l in sys.stdin:\n    if l.strip(): print('even' if int(l)%2==0 else 'odd')",
  ["4\n", "7\n-3\n0\n-8\n", "1000000000\n999999999\n"],
  "if / else 與 %。")

D("d006", "三個數的最大值", 0, "條件判斷",
  "輸入三個整數，輸出最大的那個。",
  "每行三個整數 a b c，讀到 EOF。", "每行一個答案。",
  "比較", "可以用 if 連續比較，也可以直接用內建 max（先學前者）。",
  "import sys\nfor l in sys.stdin:\n    p=l.split()\n    if p: print(max(map(int,p)))",
  ["1 2 3\n", "5 5 5\n-1 -2 -3\n9 1 4\n", "0 0 -1\n"],
  "多重條件與比較。")

D("d007", "閏年", 0, "條件判斷",
  "給西元年份，判斷是否為閏年。能被 4 整除且不能被 100 整除，或能被 400 整除，就是閏年。輸出 `yes` 或 `no`。",
  "每行一個正整數年份（≤ 10^5），讀到 EOF。", "每行 yes 或 no。",
  "複合條件", "把規則寫成一個 and / or 的布林式，注意 and 比 or 先算，必要時加括號。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        y=int(l); print('yes' if (y%4==0 and y%100!=0) or y%400==0 else 'no')",
  ["2024\n", "1900\n2000\n2023\n2100\n1600\n4\n", "100000\n99999\n"],
  "and / or / not 的優先順序。")

D("d008", "成績等級", 0, "條件判斷",
  "分數 0–100：90 以上 A、80–89 B、70–79 C、60–69 D、其餘 F。輸出等級。",
  "每行一個整數分數，讀到 EOF。", "每行一個字母。",
  "if / elif / else 鏈", "從高到低依序判斷，用 elif；邊界值 90、80、70、60 要測。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        s=int(l); print('A' if s>=90 else 'B' if s>=80 else 'C' if s>=70 else 'D' if s>=60 else 'F')",
  ["95\n", "90\n89\n80\n79\n70\n69\n60\n59\n0\n100\n", "85\n"],
  "elif 鏈與邊界值測試。")

# ---- 迴圈 ----
D("d009", "1 加到 n", 0, "迴圈",
  "輸入 n，輸出 1+2+…+n。請先用迴圈寫。",
  "每行一個正整數 n（≤ 10^5），讀到 EOF。", "每行一個答案。",
  "for 迴圈累加", "宣告 total=0，用 for i in range(1, n+1) 累加。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l); print(n*(n+1)//2)",
  ["10\n", "1\n100\n", "100000\n99999\n"],
  "range 的右界是『不含』。學會後想想有沒有公式。")

D("d010", "階乘", 0, "迴圈",
  "輸入 n（0 ≤ n ≤ 20），輸出 n!（0! = 1）。",
  "每行一個整數，讀到 EOF。", "每行一個答案。",
  "迴圈連乘", "result 從 1 開始，for i in range(2, n+1) 乘上去。",
  "import sys,math\nfor l in sys.stdin:\n    if l.strip(): print(math.factorial(int(l)))",
  ["5\n", "0\n1\n20\n", "10\n15\n"],
  "累乘；0! 的特例。")

D("d011", "乘法表", 0, "迴圈／格式",
  "輸入 n（1–9），輸出 n 的乘法表，共 9 行，第 i 行格式為 `n*i=結果`。",
  "一行一個整數 n。", "9 行。",
  "迴圈與字串格式", "for i in range(1, 10)；f'{n}*{i}={n*i}'。",
  "n=int(input())\nfor i in range(1,10): print(f'{n}*{i}={n*i}')",
  ["3\n", "1\n", "9\n"],
  "輸出格式要和範例一模一樣（不能多空格）。")

D("d012", "各位數字和", 0, "迴圈／數字",
  "輸入非負整數 n（< 10^18），輸出它各位數字的總和。",
  "每行一個整數，讀到 EOF。", "每行一個答案。",
  "while 迴圈與 % //", "n%10 取最後一位，n//=10 去掉最後一位，直到 n 變成 0。注意 n 本身是 0。",
  "import sys\nfor l in sys.stdin:\n    if l.strip(): print(sum(map(int,l.strip())))",
  ["12345\n", "0\n7\n1000000000\n999999999999999999\n", "1010101\n"],
  "while 迴圈；也可以把數字當字串處理（兩種寫法都要會）。")

# ---- 字串 / list ----
D("d013", "反轉整數", 0, "字串／數字",
  "輸入整數 n，輸出把各位數字反轉後的整數。結果不保留前導 0；負數保留負號。例如 1200 → 21，-120 → -21，0 → 0。",
  "每行一個整數（|n| < 10^18），讀到 EOF。", "每行一個答案。",
  "字串切片", "s[::-1] 反轉字串；先處理負號；轉成 int 再印會自動去掉前導 0。",
  "import sys\nfor l in sys.stdin:\n    s=l.strip()\n    if not s: continue\n    neg=s[0]=='-'\n    r=int(s.lstrip('-')[::-1])\n    print(-r if neg and r else r)",
  ["123\n", "1200\n-120\n0\n7\n-5\n", "100000000000000000\n-999999999999999999\n"],
  "字串切片 [::-1]、int()/str() 轉換。")

D("d014", "母音計數", 0, "字串",
  "對每一行文字，輸出 a e i o u（不分大小寫）共出現幾次。**空行也是一行**，答案是 0。",
  "每行一段文字（可含空格與標點），讀到 EOF。", "每行一個整數。",
  "迴圈走過字串", "用 for ch in line 檢查 ch 是否在 'aeiou' 裡；先 lower()。空行不要跳過。",
  "import sys\nfor l in sys.stdin:\n    print(sum(c in 'aeiou' for c in l.lower()))",
  ["Hello World\n", "\nAEIOU aeiou\nxyz\n\n", "The quick brown fox jumps over the lazy dog.\n"],
  "字串走訪、`in` 運算；注意空行是合法資料。")

D("d015", "迴文", 0, "字串",
  "判斷每一行字串是不是迴文（正著讀反著讀一樣，區分大小寫）。輸出 `YES` 或 `NO`。",
  "每行一個不含空白的字串（長度 1–1000），讀到 EOF。", "每行 YES 或 NO。",
  "字串比較", "s == s[::-1]。",
  "import sys\nfor l in sys.stdin:\n    s=l.strip()\n    if s: print('YES' if s==s[::-1] else 'NO')",
  ["level\n", "abc\nAba\nx\nabba\nabcba\n", "a"*1000+"\n"+"a"*999+"b\n"],
  "字串反轉比較。")

D("d016", "凱薩密碼", 0, "字串",
  "第一行整數 k（0 ≤ k ≤ 1000），第二行一段文字。把每個英文字母往後移 k 位（z 後面接 a，大小寫分開處理），其他字元不變，輸出結果。",
  "兩行：k；文字（長度 ≤ 1000，可含空格）。", "一行加密後的文字。",
  "字元運算 ord/chr", "ord('a') 是 97；(ord(c)-97+k)%26+97。大寫另外一組。",
  "k=int(input())\ns=input()\no=[]\nfor c in s:\n    if 'a'<=c<='z': o.append(chr((ord(c)-97+k)%26+97))\n    elif 'A'<=c<='Z': o.append(chr((ord(c)-65+k)%26+65))\n    else: o.append(c)\nprint(''.join(o))",
  ["3\nHello, World!\n", "0\nabc\n", "26\nXyz\n", "1000\nThe Quick Brown Fox\n", "1\nzZ aA\n"],
  "ord/chr 與取餘數做循環。")

D("d017", "數列統計", 0, "list",
  "第一行 n，第二行 n 個整數。輸出最小值、最大值、平均值（小數點後 2 位），以空格隔開。",
  "n ≤ 1000。", "一行：min max avg。",
  "list 與內建函式", "min()、max()、sum()、len()；平均 = sum/len。",
  "n=int(input())\na=list(map(int,input().split()))\nprint(min(a),max(a),f'{sum(a)/n:.2f}')",
  ["5\n1 2 3 4 5\n", "1\n-7\n", "4\n10 20 30 41\n", "3\n1 1 2\n"],
  "list 基本操作；平均值格式。")

D("d018", "排序", 0, "list／排序",
  "輸入 n 個整數，由小到大排序後輸出（以空格隔開）。",
  "第一行 n（≤ 10^5），第二行 n 個整數。", "一行。",
  "sort", "sorted(a) 或 a.sort()。",
  "n=int(input())\na=sorted(map(int,input().split()))\nprint(*a)",
  ["5\n3 1 4 1 5\n", "1\n9\n", "6\n-1 -5 0 5 3 -2\n"] ,
  "sorted 與 print(*list)。")

D("d019", "去除重複", 0, "list／set",
  "輸入 n 個整數，保留每個數字第一次出現的位置，刪掉後面重複的，依原順序輸出。",
  "第一行 n（≤ 10^5），第二行 n 個整數。", "一行。",
  "用 set 記錄看過的數", "走一遍；沒出現過的才加入結果並記進 set。",
  "n=int(input())\nseen=set();o=[]\nfor x in input().split():\n    x=int(x)\n    if x not in seen: seen.add(x);o.append(x)\nprint(*o)",
  ["7\n1 2 1 3 2 4 4\n", "1\n5\n", "5\n7 7 7 7 7\n", "6\n3 -1 3 -1 0 0\n"],
  "set 的查詢是 O(1)；若用 list 查詢，資料大時會很慢。")

# ---- dict / 函式 ----
D("d020", "詞頻統計", 0, "dict／排序",
  "讀入多行文字，單字以空白分隔（區分大小寫）。輸出每個不同單字及出現次數，依次數由大到小；次數相同時依單字字典序由小到大。每行格式：`單字 次數`。",
  "讀到 EOF。總單字數 ≤ 10^5。", "每個不同單字一行。",
  "dict 計數＋自訂排序", "dict.get(w, 0)+1 計數；sorted(items, key=lambda kv: (-kv[1], kv[0]))。",
  "import sys\nfrom collections import Counter\nc=Counter(sys.stdin.read().split())\nfor w,k in sorted(c.items(),key=lambda kv:(-kv[1],kv[0])): print(w,k)",
  ["a b a\nc b a\n", "hello\n", "x y z\nz y x\nx\n\ny\n", "the cat the dog The end\n"],
  "dict 計數與 key 函式排序，是之後所有題目的基本功。")

D("d021", "質數判斷", 0, "數學／迴圈",
  "判斷整數 n 是否為質數（1 不是質數）。輸出 `YES` 或 `NO`。",
  "每行一個整數 n（1 ≤ n ≤ 10^9），最多 100 行，讀到 EOF。", "每行 YES 或 NO。",
  "試除法到平方根", "只需要試除到 √n：i*i <= n；先排除 n<2。",
  "import sys\nfor l in sys.stdin:\n    if not l.strip(): continue\n    n=int(l)\n    ok=n>1\n    i=2\n    while ok and i*i<=n:\n        if n%i==0: ok=False\n        i+=1\n    print('YES' if ok else 'NO')",
  ["7\n", "1\n2\n4\n9\n97\n100\n", "999999937\n1000000000\n999999929\n"],
  "試除法；n 到 10^9 時，只試除到 31623。", diff=1)

D("d022", "最大公因數與最小公倍數", 0, "數學／函式",
  "對每組正整數 a b 輸出 gcd 與 lcm，以空格隔開。",
  "每行兩個整數（≤ 10^9），讀到 EOF。", "每行：gcd lcm。",
  "輾轉相除法", "gcd(a,b)：while b: a,b=b,a%b。lcm = a*b//gcd。自己寫一次函式。",
  "import sys,math\nfor l in sys.stdin:\n    p=l.split()\n    if p:\n        a,b=int(p[0]),int(p[1]);g=math.gcd(a,b);print(g,a//g*b)",
  ["12 18\n", "1 1\n7 13\n1000000000 999999999\n100 10\n", "36 48\n"],
  "函式 def 與輾轉相除法。")

D("d023", "費氏數列", 0, "迴圈／函式",
  "F(0)=0，F(1)=1，F(n)=F(n-1)+F(n-2)。輸入 n（0 ≤ n ≤ 90），輸出 F(n)。",
  "每行一個整數，讀到 EOF。", "每行一個答案。",
  "迴圈迭代（先別用遞迴）", "用兩個變數 a, b = b, a+b 滾動 n 次。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l);a,b=0,1\n        for _ in range(n): a,b=b,a+b\n        print(a)",
  ["10\n", "0\n1\n2\n50\n90\n", "30\n"],
  "遞迴版對 n=90 會算到天荒地老——這是學複雜度的第一課。")

D("d024", "星星金字塔", 0, "迴圈／格式",
  "輸入 n，輸出 n 層置中金字塔：第 i 層（從 1 開始）有 n-i 個空格開頭，後面接 2i-1 個 `*`。行尾不要有多餘空格。",
  "一行一個整數 n（1 ≤ n ≤ 50）。", "n 行。",
  "巢狀迴圈與字串乘法", "' ' * (n-i) + '*' * (2*i-1)。",
  "n=int(input())\nfor i in range(1,n+1): print(' '*(n-i)+'*'*(2*i-1))",
  ["3\n", "1\n", "5\n", "10\n"],
  "字串可以用 * 重複；輸出的空白也算內容。")

D("d025", "因數個數", 0, "數學／函式",
  "對每個正整數 n 輸出它有幾個正因數。",
  "每行一個整數 n（≤ 10^6），最多 1000 行，讀到 EOF。", "每行一個答案。",
  "只掃到平方根", "i*i<=n；每找到 i 整除，就同時有 n//i 這個因數（i*i==n 時只算一個）。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l);c=0;i=1\n        while i*i<=n:\n            if n%i==0: c+=1 if i*i==n else 2\n            i+=1\n        print(c)",
  ["12\n", "1\n36\n97\n1000000\n", "720720\n999983\n"],
  "成對找因數的技巧，之後的數論都會用。")

D("d026", "矩陣轉置", 0, "二維 list",
  "第一行 r c，接下來 r 行每行 c 個整數。輸出轉置後的矩陣（c 行 r 列），數字以空格隔開。",
  "1 ≤ r, c ≤ 100。", "c 行。",
  "二維 list", "a[i][j] 變成 b[j][i]；zip(*a) 是另一種寫法。",
  "r,c=map(int,input().split())\na=[input().split() for _ in range(r)]\nfor j in range(c): print(*[a[i][j] for i in range(r)])",
  ["2 3\n1 2 3\n4 5 6\n", "1 1\n7\n", "3 1\n1\n2\n3\n", "1 4\n1 2 3 4\n"],
  "二維 list 的索引與建立。")

D("d027", "十進位轉二進位", 0, "進位制",
  "將非負整數轉成二進位表示（不含前綴）。0 的二進位是 `0`。",
  "每行一個整數（≤ 10^18），讀到 EOF。", "每行一個二進位字串。",
  "反覆除以 2", "while n: 取 n%2 再 n//=2，最後反轉；也可用 bin(n)[2:]。先用迴圈寫一次。",
  "import sys\nfor l in sys.stdin:\n    if l.strip(): print(bin(int(l))[2:])",
  ["10\n", "0\n1\n255\n1024\n", "1000000000000000000\n"],
  "進位制是 CPE 常客。")

D("d028", "兩數之和", 0, "set／效能",
  "給 n 個整數與目標 T，是否存在兩個**不同位置**的數，和為 T？輸出 `YES` 或 `NO`。",
  "第一行 n T，第二行 n 個整數。n ≤ 50000。", "YES 或 NO。",
  "set 查詢", "走過每個 x 時，檢查 T-x 是否已在 set 中，再把 x 放進去。O(n)。",
  "n,t=map(int,input().split())\nseen=set()\nok=False\nfor x in map(int,input().split()):\n    if t-x in seen: ok=True;break\n    seen.add(x)\nprint('YES' if ok else 'NO')",
  ["5 9\n2 7 11 15 1\n", "3 6\n3 1 2\n", "2 4\n2 2\n", "1 2\n1\n",
   (lambda r: lines("50000 -1", " ".join(str(2*x) for x in r.sample(range(1,10**6), 50000))))(rng(28))],
  "O(n²) 雙迴圈在 n=50000 時會超時，改用 set 就是 O(n)。這是第一次遇到『效能』。")

D("d029", "異位詞", 0, "字串／dict",
  "輸入兩行字串，若重新排列第一行的字元可以得到第二行（區分大小寫，空白也算字元），輸出 `YES`，否則 `NO`。",
  "兩行，長度 ≤ 1000。", "YES 或 NO。",
  "排序或計數", "sorted(a) == sorted(b)，或用 Counter 比較。",
  "a=input();b=input()\nprint('YES' if sorted(a)==sorted(b) else 'NO')",
  ["listen\nsilent\n", "abc\nabd\n", "a b\nb a\n", "aab\nabb\n", "x\nx\n"],
  "兩種寫法（排序／計數）的取捨。")

D("d030", "簡易銀行", 0, "字串解析／狀態",
  "帳戶初始餘額 0。每行一個指令：`DEPOSIT x` 存入 x；`WITHDRAW x` 提領 x，若餘額不足則輸出 `INSUFFICIENT` 且餘額不變；`BALANCE` 輸出目前餘額。讀到 EOF。",
  "x 為正整數（≤ 10^9）。指令最多 1000 行。", "每個 BALANCE 與每次失敗的 WITHDRAW 輸出一行。",
  "字串解析＋變數狀態", "line.split() 取出指令與參數；用一個 balance 變數維護狀態。",
  "import sys\nb=0\nfor l in sys.stdin:\n    p=l.split()\n    if not p: continue\n    if p[0]=='DEPOSIT': b+=int(p[1])\n    elif p[0]=='WITHDRAW':\n        if int(p[1])>b: print('INSUFFICIENT')\n        else: b-=int(p[1])\n    else: print(b)",
  ["DEPOSIT 100\nBALANCE\nWITHDRAW 30\nBALANCE\nWITHDRAW 100\nBALANCE\n", "BALANCE\n", "DEPOSIT 5\nWITHDRAW 5\nBALANCE\nWITHDRAW 1\n"],
  "模擬題的核心：讀指令、改狀態、輸出。")
