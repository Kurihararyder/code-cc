"""階段 1：競程 I/O 與一顆星題型（15 題）。"""
from common import D, lines, rng

D("d031", "直到 0 0 為止", 1, "輸入格式",
  "每行兩個整數 a b，輸出 |a-b|。遇到 `0 0` 就結束（這一行不要處理）。結束標記之後的內容要忽略。",
  "|a|,|b| ≤ 10^9。", "每行一個答案。",
  "以特殊值結束的輸入", "讀一行、split、轉 int；如果 a==0 and b==0 就 break。",
  "import sys\nfor l in sys.stdin:\n    p=l.split()\n    if not p: continue\n    a,b=int(p[0]),int(p[1])\n    if a==0 and b==0: break\n    print(abs(a-b))",
  ["3 5\n0 0\n", "10 2\n-4 4\n0 5\n5 0\n0 0\n99 99\n", "0 0\n", "1000000000 -1000000000\n0 0\n"],
  "UVA 很多題用 `0 0` 或單個 `0` 結束；結束行之後可能還有資料。")

D("d032", "先給組數", 1, "輸入格式",
  "第一行 t 代表測資組數。每組兩行：第一行 n，第二行 n 個整數。對每組輸出總和。",
  "t ≤ 100，n ≤ 1000；n 可能是 0（此時第二行是空行）。", "每組一行。",
  "先給組數、再給資料", "讀完整份輸入 data=sys.stdin.read().split() 再用指標取最穩；注意 n=0 時沒有任何數字可讀。",
  "import sys\nd=sys.stdin.read().split()\nt=int(d[0]);i=1\nfor _ in range(t):\n    n=int(d[i]);i+=1\n    print(sum(map(int,d[i:i+n])));i+=n",
  ["2\n3\n1 2 3\n2\n10 -10\n", "1\n0\n\n", "3\n1\n5\n0\n\n4\n1 1 1 1\n"],
  "『全部讀進來再切』不怕空行與換行位置問題；但每行有意義的題目不能這樣。")

D("d033", "空行分隔的資料", 1, "輸入格式",
  "輸入由數個群組組成，群組之間以**一個空行**分隔，每個群組有若干行，每行一個整數。對每個群組輸出整數總和。",
  "群組數 ≤ 100，每組 ≤ 100 行。輸入最後沒有多餘空行。", "每個群組一行。",
  "以空行分隔的群組", "逐行讀；遇到空行就結算並重設累計值；EOF 時別忘了結算最後一組。",
  "import sys\ns=0;has=False\nfor l in sys.stdin:\n    l=l.strip()\n    if l=='':\n        print(s);s=0;has=False\n    else:\n        s+=int(l);has=True\nif has: print(s)",
  ["1\n2\n3\n\n10\n20\n", "5\n", "1\n\n2\n\n3\n", "-1\n-2\n\n100\n"],
  "UVA 10226、10282 這類題都是這種格式。EOF 之後的『最後一組』是經典漏洞。")

D("d034", "Case 格式與空行", 1, "輸出格式",
  "第一行 t，之後 t 行每行一個整數 n。對第 k 組輸出 `Case #k:`，下一行輸出 1+2+…+n。**組與組之間輸出一個空行，最後一組後面不要空行。**",
  "t ≤ 100，n ≤ 10^6。", "見範例。",
  "輸出格式（標題行、空行）", "第 k 組輸出前，若 k>1 先印一個空行；或收集成 list 再 '\\n\\n'.join。",
  "t=int(input())\nfor k in range(1,t+1):\n    n=int(input())\n    if k>1: print()\n    print(f'Case #{k}:')\n    print(n*(n+1)//2)",
  ["2\n3\n4\n", "1\n1\n", "3\n10\n0\n1000000\n"],
  "UVA 常見：『組與組之間』與『每組之後』的空行要區分清楚。這是 PE（格式錯誤）的最大來源。")

D("d035", "除法與小數位", 1, "浮點數格式",
  "每行兩個正整數 a b，輸出 a/b，**四捨五入到小數點後 4 位**。",
  "a, b ≤ 10^6，讀到 EOF。測資保證不會剛好落在 5 的進位邊界。", "每行一個答案。",
  "浮點數輸出", "f'{a/b:.4f}'；用整數除法 // 會丟掉小數。",
  "import sys\nfor l in sys.stdin:\n    p=l.split()\n    if p: print(f'{int(p[0])/int(p[1]):.4f}')",
  ["1 3\n", "10 4\n7 7\n2 3\n1 1000000\n999999 1000000\n", "22 7\n355 113\n"],
  "浮點格式。若題目要求精確小數，改用整數運算或 decimal 更保險。")

D("d036", "大數加與乘", 1, "大整數",
  "每行兩個非負整數 a b（最多 500 位），輸出 a+b 與 a*b，各佔一行。",
  "讀到 EOF，最多 20 行。", "每組輸出 2 行。",
  "Python 大整數", "int() 直接轉；Python 的 int 不會溢位——這是用 Python 解大數題的優勢。",
  "import sys\nfor l in sys.stdin:\n    p=l.split()\n    if p:\n        a,b=int(p[0]),int(p[1]);print(a+b);print(a*b)",
  ["1 2\n", "0 0\n99999999999999999999 1\n", "9"*500+" "+"9"*500+"\n", "123456789 987654321\n"],
  "C++ 做不到的事，Python 一行搞定。")

D("d037", "進位制轉換", 1, "進位制",
  "每行三個值 `s a b`：s 是 a 進位（2 ≤ a ≤ 16）的數字（大寫英文字母代表 10–15），請轉成 b 進位（2 ≤ b ≤ 16），輸出大寫。",
  "s 轉成十進位後 ≤ 10^18；輸出沒有前導 0（0 輸出 0）。讀到 EOF。", "每行一個答案。",
  "任意進位制", "int(s, a) 轉十進位；再自己寫迴圈用 '0123456789ABCDEF' 取餘數轉 b 進位。",
  "import sys\nD='0123456789ABCDEF'\nfor l in sys.stdin:\n    p=l.split()\n    if not p: continue\n    n=int(p[0],int(p[1]));b=int(p[2])\n    o=''\n    while n: o=D[n%b]+o;n//=b\n    print(o or '0')",
  ["FF 16 2\n", "0 10 2\n1010 2 10\n7B 16 8\nZZ 10 2\n".replace("ZZ 10 2\n", "255 10 16\n"), "FFFFFFFFFFFF 16 10\n100 10 2\n"],
  "進位制轉換在 CPE 歷屆很常見。")

D("d038", "質數個數查詢", 1, "質數篩",
  "第一行 q，之後 q 行每行一個 n，輸出 1..n 之間有幾個質數。",
  "q ≤ 30000，n ≤ 10^6。", "每個查詢一行。",
  "埃拉托斯特尼篩法＋前綴和", "先篩一次到 10^6，再累計成 pi[n]；每個查詢直接查表。逐一試除會超時。",
  "import sys\nN=10**6\nsv=bytearray([1])*(N+1);sv[0]=sv[1]=0\nfor i in range(2,int(N**.5)+1):\n    if sv[i]: sv[i*i::i]=bytearray(len(range(i*i,N+1,i)))\npi=[0]*(N+1)\nfor i in range(1,N+1): pi[i]=pi[i-1]+sv[i]\nd=sys.stdin.read().split()\nfor x in d[1:1+int(d[0])]: print(pi[int(x)])",
  ["5\n1\n2\n10\n100\n1000000\n", "1\n1\n", (lambda r: lines(30000, *[r.randint(1,10**6) for _ in range(30000)]))(rng(38))],
  "『先預處理、再 O(1) 查詢』是競程最重要的思維之一。")

D("d039", "羅馬數字", 1, "字串／映射",
  "將 1–3999 的整數轉成羅馬數字（I V X L C D M；4=IV、9=IX、40=XL、90=XC、400=CD、900=CM）。",
  "每行一個整數，讀到 EOF。", "每行一個羅馬數字。",
  "貪心映射表", "準備 (值, 符號) 由大到小的表（含 900、400、90、40、9、4），反覆減掉最大可減的值。",
  "import sys\nT=[(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l);o=''\n        for v,s in T:\n            while n>=v: o+=s;n-=v\n        print(o)",
  ["4\n", "1\n9\n14\n40\n90\n400\n1994\n2024\n3999\n", "58\n3888\n"],
  "查表＋貪心。")

D("d040", "星期幾", 1, "日期",
  "給日期 `y m d`（1900–2100，保證合法），輸出那天是星期幾：Monday、Tuesday、Wednesday、Thursday、Friday、Saturday、Sunday。",
  "讀到 EOF。", "每行一個英文星期名稱。",
  "日期計算", "可以用 datetime.date(y,m,d).weekday()（0=Monday），或用 Zeller 公式自己算（建議兩種都練）。",
  "import sys,datetime\nN=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']\nfor l in sys.stdin:\n    p=l.split()\n    if p: print(N[datetime.date(int(p[0]),int(p[1]),int(p[2])).weekday()])",
  ["2024 1 1\n", "2000 2 29\n1900 1 1\n2100 12 31\n1999 12 31\n2026 10 30\n", "2024 2 29\n"],
  "CPE 考場是 Python 3.9.6，datetime 可用。")

D("d041", "機器人走格子", 1, "模擬／二維座標",
  "機器人在 N×N 格子（座標 0..N-1）左下角 (0,0)。第一行 N，第二行是指令字串，由 `U`(y+1) `D`(y-1) `L`(x-1) `R`(x+1) 組成。如果某個移動會走出格子就**忽略該指令**。輸出最後座標 `x y`。",
  "N ≤ 100，指令長度 ≤ 10^5。", "一行：x y。",
  "座標模擬與邊界", "每步先算新座標，檢查 0<=nx<N and 0<=ny<N 才更新。",
  "n=int(input());s=input().strip();x=y=0\nfor c in s:\n    dx,dy={'U':(0,1),'D':(0,-1),'L':(-1,0),'R':(1,0)}[c]\n    if 0<=x+dx<n and 0<=y+dy<n: x+=dx;y+=dy\nprint(x,y)",
  ["3\nUURR\n", "1\nUDLR\n", "5\nLLLLDDDD\n", "4\nURURURURUR\n", (lambda r: lines(100, "".join(r.choice("UDLR") for _ in range(100000))))(rng(41))],
  "模擬題的標準套路：方向表＋邊界檢查。")

D("d042", "螺旋矩陣", 1, "二維模擬",
  "輸入 n，輸出 n×n 的螺旋矩陣：從左上角 1 開始順時針往內填入 1..n²。每行的數字以空格分隔。",
  "n ≤ 30。", "n 行。",
  "方向切換模擬", "用方向陣列 (0,1)(1,0)(0,-1)(-1,0)；下一格出界或已填過就轉向。",
  "n=int(input())\na=[[0]*n for _ in range(n)]\nx=y=d=0\nD=[(0,1),(1,0),(0,-1),(-1,0)]\nfor k in range(1,n*n+1):\n    a[x][y]=k\n    nx,ny=x+D[d][0],y+D[d][1]\n    if not(0<=nx<n and 0<=ny<n and a[nx][ny]==0):\n        d=(d+1)%4;nx,ny=x+D[d][0],y+D[d][1]\n    x,y=nx,ny\nfor r in a: print(*r)",
  ["3\n", "1\n", "4\n", "7\n", "30\n"],
  "『轉向』類模擬的標準寫法。")

D("d043", "連續字元壓縮", 1, "字串",
  "對每行字串（不含空白）做壓縮：連續相同字元用 `字元+次數` 表示，例如 `aaabcc` → `a3b1c2`。",
  "每行長度 ≤ 10^5，讀到 EOF。", "每行一個壓縮結果。",
  "分組掃描", "維護目前字元與計數；字元改變時輸出。結尾別忘了輸出最後一段。",
  "import sys\nfor l in sys.stdin:\n    s=l.strip()\n    if not s: continue\n    o=[];c=s[0];k=0\n    for ch in s:\n        if ch==c: k+=1\n        else: o.append(f'{c}{k}');c=ch;k=1\n    o.append(f'{c}{k}');print(''.join(o))",
  ["aaabcc\n", "a\nab\naaaa\nzzzzzzzzzzzz\nabcabc\n", "x"*100000+"\n"],
  "迴圈結束後『還有一段沒輸出』是最常見的 off-by-one。")

D("d044", "由左到右的算式", 1, "字串解析",
  "每行是以空格分隔的算式：整數與 + - * 交替，例如 `3 + 4 * 2`。**不看優先順序，一律由左到右**計算（所以 3+4*2 = 14）。輸出結果。",
  "整數 0–1000，每行最多 20 個數字。讀到 EOF。", "每行一個整數。",
  "token 解析", "split() 後第一個數當初值，之後每次取（運算子, 數字）成對處理。",
  "import sys\nfor l in sys.stdin:\n    t=l.split()\n    if not t: continue\n    r=int(t[0])\n    for i in range(1,len(t),2):\n        o,v=t[i],int(t[i+1])\n        r=r+v if o=='+' else r-v if o=='-' else r*v\n    print(r)",
  ["3 + 4 * 2\n", "5\n1 - 2 - 3\n10 * 10 * 10 * 10\n0 + 0\n", "1000 * 1000 - 999999\n"],
  "之後 d095 會挑戰有優先順序與括號。")

D("d045", "24 小時轉 12 小時", 1, "字串格式",
  "輸入 `hh:mm:ss`（24 小時制），轉成 12 小時制 `hh:mm:ss AM` 或 `hh:mm:ss PM`。00:xx:xx 是 `12:xx:xx AM`，12:xx:xx 是 `12:xx:xx PM`。hh 保持兩位數。",
  "讀到 EOF。", "每行一個結果。",
  "字串格式化與邊界", "h%12，若為 0 則顯示 12；用 f'{h:02d}' 補零。0 與 12 是邊界。",
  "import sys\nfor l in sys.stdin:\n    s=l.strip()\n    if not s: continue\n    h,m,sec=s.split(':');h=int(h)\n    print(f\"{(h%12) or 12:02d}:{m}:{sec} {'AM' if h<12 else 'PM'}\")",
  ["13:05:09\n", "00:00:00\n12:00:00\n12:59:59\n23:59:59\n01:02:03\n11:11:11\n", "00:30:00\n"],
  "邊界時間（0 點與 12 點）是這題的重點。")
