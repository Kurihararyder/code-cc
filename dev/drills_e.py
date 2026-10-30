"""驗收用的考場風格題（reserve）：練習單元不會出現，階段驗收才用到。"""
from common import D, lines, rng

# ---------------- 階段 1 ----------------
D("e101", "成績排名", 1, "排序／輸出格式",
  "第一行 t。每組先給 n，接著 n 行 `姓名 分數`。依分數由高到低、同分依姓名字典序由小到大排序，輸出名次：同分者名次相同，下一個名次要跳號（例如 1,1,3）。\n每組先輸出一行 `Case #k:`，再輸出每人一行 `名次 姓名 分數`。**組與組之間輸出一個空行，最後一組後面沒有空行。**",
  "t ≤ 50，n ≤ 100，姓名為不含空白的英文字母，分數為 0–100 的整數。", "見題目。",
  "排序＋名次＋輸出格式", "sorted(key=(-分數, 姓名))；名次 = 前面比他分數高的人數 + 1；注意空行的位置。",
  "t=int(input())\nfor k in range(1,t+1):\n    n=int(input());rows=[]\n    for _ in range(n):\n        a,b=input().split();rows.append((a,int(b)))\n    rows.sort(key=lambda r:(-r[1],r[0]))\n    if k>1: print()\n    print(f'Case #{k}:')\n    for a,b in rows: print(sum(1 for x in rows if x[1]>b)+1,a,b)",
  ["2\n3\nbob 90\nalice 90\ncarol 80\n2\nz 0\ny 100\n", "1\n1\nsolo 50\n", "1\n4\na 5\nb 5\nc 5\nd 5\n",
   (lambda r: lines(30, *sum([[ (n := r.randint(1, 40)) ] + [f"{''.join(r.choice('abcde') for _ in range(3))}{i} {r.randint(0,100)}" for i in range(n)] for _ in range(30)], [])))(rng(101))],
  "把前面學的 I/O 格式、排序、計數組合起來。", diff=2, reserve=True)

D("e102", "密碼強度", 1, "字串",
  "對每一行密碼（不含空白，長度 1–50）評分，滿足幾項就得幾分：①長度 ≥ 8 ②含小寫字母 ③含大寫字母 ④含數字 ⑤含 `!@#$%^&*` 其中之一。輸出 `分數 等級`：5 分 STRONG；3 或 4 分 MEDIUM；其餘 WEAK。",
  "讀到 EOF。", "每行一個結果。",
  "字串判斷", "用 any(c.islower() for c in s) 之類的寫法逐項檢查。",
  "import sys\nfor l in sys.stdin:\n    s=l.strip()\n    if not s: continue\n    sc=(len(s)>=8)+any(c.islower() for c in s)+any(c.isupper() for c in s)+any(c.isdigit() for c in s)+any(c in '!@#$%^&*' for c in s)\n    print(sc,'STRONG' if sc==5 else 'MEDIUM' if sc>=3 else 'WEAK')",
  ["Passw0rd!\n", "abc\nABCDEFGH\n12345678\nabcDEF12\n!!!!!!!!\nA1\nx\n", "aB3$\nlongpasswordnodigits\nSHORT1!\n"],
  "每個條件都要有一筆測資覆蓋。", diff=1, reserve=True)

D("e103", "停車費", 1, "時間計算",
  "每行兩個時間 `HH:MM HH:MM`（進場、出場，同一天，出場不早於進場）。前 30 分鐘免費；之後每『不足或滿』30 分鐘收 20 元；單次最高 200 元。輸出費用。",
  "讀到 EOF。", "每行一個整數。",
  "時間換算與邊界", "先換成分鐘；d≤30 為 0；否則區塊數 = ceil((d-30)/30)；用 (x+29)//30 做無條件進位；最後取 min(200, …)。",
  "import sys\nfor l in sys.stdin:\n    p=l.split()\n    if len(p)<2: continue\n    f=lambda t:int(t[:2])*60+int(t[3:])\n    d=f(p[1])-f(p[0])\n    print(0 if d<=30 else min(200,((d-30+29)//30)*20))",
  ["08:00 09:00\n", "10:00 10:00\n10:00 10:30\n10:00 10:31\n10:00 11:00\n10:00 11:01\n00:00 23:59\n12:15 14:45\n", "09:05 09:36\n"],
  "30、31、60、61 分鐘是邊界。", diff=2, reserve=True)

# ---------------- 階段 2 ----------------
D("e201", "最小間距", 2, "排序",
  "給 n 個整數（可重複），排序後看相鄰兩數的差。輸出最小的差，以及有幾組相鄰數對的差等於這個最小值。",
  "第一行 n（2 ≤ n ≤ 30000），第二行 n 個整數。", "一行：最小差 組數。",
  "排序後掃描相鄰元素", "排序後算 b[i+1]-b[i]，取最小並計數。重複的數字差為 0。",
  "n=int(input());a=sorted(map(int,input().split()))\nd=[a[i+1]-a[i] for i in range(n-1)]\nm=min(d);print(m,d.count(m))",
  ["5\n1 5 3 9 11\n", "2\n7 7\n", "4\n1 1 1 1\n", "3\n-5 0 5\n",
   (lambda r: lines(30000, " ".join(str(r.randint(-10**9,10**9)) for _ in range(30000))))(rng(201))],
  "『先排序』讓很多問題變簡單。", diff=2, reserve=True)

D("e202", "工作排程", 2, "貪心＋堆積",
  "有 n 份工作，每份需要 1 單位時間，必須在第 d 個單位時間結束前完成（時間從 1 開始，第 t 個單位時間做一份工作，t ≤ d），完成可得報酬 p。一個單位時間只能做一份。求最大總報酬。",
  "第一行 n（≤ 30000），接著 n 行 `d p`（1 ≤ d ≤ 10^9，1 ≤ p ≤ 10^9）。", "一個整數。",
  "按期限排序＋最小堆積", "依期限由小到大處理；把報酬放進最小堆積；若堆積大小超過目前期限，就彈出最小的報酬。堆積剩下的總和就是答案。",
  "import heapq,sys\nd=sys.stdin.read().split()\nn=int(d[0]);J=sorted((int(d[1+2*i]),int(d[2+2*i])) for i in range(n))\nh=[]\nfor dl,p in J:\n    heapq.heappush(h,p)\n    if len(h)>dl: heapq.heappop(h)\nprint(sum(h))",
  ["4\n2 100\n1 19\n2 27\n1 25\n", "1\n1 5\n", "3\n1 1\n1 2\n1 3\n", "3\n3 1\n3 2\n3 3\n",
   (lambda r: lines(30000, *[f"{r.randint(1,20000)} {r.randint(1,10**9)}" for _ in range(30000)]))(rng(202))],
  "這是『貪心＋可反悔』的經典。", diff=3, reserve=True)

D("e203", "括號生成", 2, "回溯",
  "輸入 n（1 ≤ n ≤ 8），依字典序（`(` 小於 `)`）輸出所有由 n 對括號組成的合法括號字串，每個一行。",
  "一個整數。", "每個合法字串一行。",
  "回溯＋可行性剪枝", "遞迴時記錄已放的左括號數與右括號數：左 < n 才可放左；右 < 左 才可放右。先放左再放右自然就是字典序。",
  "n=int(input())\ndef go(s,l,r):\n    if l==n and r==n: print(s);return\n    if l<n: go(s+'(',l+1,r)\n    if r<l: go(s+')',l,r+1)\ngo('',0,0)",
  ["2\n", "1\n", "3\n", "8\n"],
  "不必先生成所有 2^(2n) 個字串再過濾，在生成途中剪枝。", diff=2, reserve=True)

# ---------------- 階段 3 ----------------
D("e301", "最近出口", 3, "多源 BFS",
  "R×C 的格子：`#` 牆、`.` 空地、`X` 出口。空地每步可往上下左右走（不能穿牆）。對每個空地，求到最近出口的步數。輸出：所有『能到達出口的空地』的步數總和，以及『到不了任何出口的空地』個數。",
  "第一行 R C（≤ 300），接著 R 行。至少有一個出口。", "一行：總和 不可達個數。",
  "多源 BFS", "把所有出口同時放進 queue 當起點（距離 0）一次 BFS 即可，不要對每個空地各跑一次。",
  "from collections import deque\nR,C=map(int,input().split());g=[input() for _ in range(R)]\nd=[[-1]*C for _ in range(R)];q=deque()\nfor i in range(R):\n    for j in range(C):\n        if g[i][j]=='X': d[i][j]=0;q.append((i,j))\nwhile q:\n    x,y=q.popleft()\n    for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):\n        a,b=x+dx,y+dy\n        if 0<=a<R and 0<=b<C and g[a][b]!='#' and d[a][b]<0: d[a][b]=d[x][y]+1;q.append((a,b))\ns=u=0\nfor i in range(R):\n    for j in range(C):\n        if g[i][j]=='.':\n            if d[i][j]<0: u+=1\n            else: s+=d[i][j]\nprint(s,u)",
  ["3 3\nX..\n.#.\n...\n", "1 3\nX#.\n", "2 2\nXX\nXX\n",
   (lambda r: (lambda g: lines("300 300", *["".join(row) for row in g]))((lambda g: (g[0].__setitem__(0, "X"), g[150].__setitem__(150, "X"), g)[2])([[r.choice("..#") for _ in range(300)] for _ in range(300)])))(rng(301))],
  "對每個起點各跑一次是 O(N²·E)；多源 BFS 只要 O(N)。", diff=2, reserve=True)

D("e302", "DAG 最長路徑", 3, "拓撲排序＋DP",
  "有向無環圖（保證沒有環）n 點 m 邊，求一條邊數最多的路徑有幾條邊。",
  "第一行 n m（n ≤ 50000, m ≤ 100000），接著 m 行 `u v`。", "一個整數。",
  "DAG 上的 DP", "依拓撲順序處理：dp[v] = max(dp[u]+1)。用 Kahn 演算法同時更新。",
  "from collections import deque\nimport sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\nadj=[[] for _ in range(n+1)];ind=[0]*(n+1)\nfor i in range(m):\n    u,v=int(d[2+2*i]),int(d[3+2*i]);adj[u].append(v);ind[v]+=1\nq=deque(i for i in range(1,n+1) if ind[i]==0);dp=[0]*(n+1)\nwhile q:\n    u=q.popleft()\n    for v in adj[u]:\n        dp[v]=max(dp[v],dp[u]+1);ind[v]-=1\n        if ind[v]==0: q.append(v)\nprint(max(dp))",
  ["4 3\n1 2\n2 3\n1 4\n", "1 0\n", "3 3\n1 2\n2 3\n1 3\n", "5 0\n",
   (lambda r: (lambda E: lines(f"20000 {len(E)}", *[f"{a} {b}" for a, b in E]))([(min(x, y), max(x, y)) for x, y in ((r.randint(1, 20000), r.randint(1, 20000)) for _ in range(40000)) if x != y]))(rng(302))],
  "最長路徑在一般圖是難題，在 DAG 卻是 O(n+m)。", diff=3, reserve=True)

D("e303", "分成兩堆", 3, "背包",
  "把 n 個正整數分成兩堆（每個數屬於其中一堆），使兩堆總和之差的絕對值最小。輸出最小差。",
  "第一行 n（≤ 100），第二行 n 個整數（每個 ≤ 100）。", "一個整數。",
  "子集合和（背包）", "總和 S；找出能湊到的子集合和 x ≤ S/2 中最大的，答案 = S - 2x。可用 bool 陣列或 Python 大整數位元集。",
  "n=int(input());a=list(map(int,input().split()));S=sum(a);b=1\nfor x in a: b|=b<<x\nbest=max(x for x in range(S//2+1) if b>>x&1)\nprint(S-2*best)",
  ["4\n1 6 11 5\n", "1\n7\n", "2\n3 3\n", "3\n1 2 4\n",
   (lambda r: lines(100, " ".join(str(r.randint(1,100)) for _ in range(100))))(rng(303))],
  "和 d068 同一類，只是要先想到轉化。", diff=3, reserve=True)

# ---------------- 階段 4 ----------------
D("e401", "和為 K 的子陣列", 4, "前綴和＋dict",
  "給 n 個整數（可為負）與 K，數有幾個連續子陣列的和恰為 K。",
  "第一行 n K（n ≤ 20000）；第二行 n 個整數（|a| ≤ 1000）。", "一個整數。",
  "前綴和 + 雜湊表", "pre[j]-pre[i]=K ⟺ pre[i]=pre[j]-K。掃描時用 dict 記錄各前綴和出現次數。O(n)。",
  "n,k=map(int,input().split());c={0:1};s=t=0\nfor x in map(int,input().split()):\n    s+=x;t+=c.get(s-k,0);c[s]=c.get(s,0)+1\nprint(t)",
  ["5 5\n1 2 3 -1 4\n", "3 0\n0 0 0\n", "1 7\n7\n", "2 100\n1 2\n",
   (lambda r: lines("20000 0", " ".join(str(r.randint(-3,3)) for _ in range(20000))))(rng(401))],
  "負數讓雙指標失效，要改用前綴和＋雜湊。", diff=2, reserve=True)

D("e402", "直方圖最大矩形", 4, "單調 stack",
  "直方圖有 n 根寬度為 1 的柱子，高度為 h[i]。求最大的矩形面積（矩形必須由連續的柱子組成，高度取其中最低者）。",
  "第一行 n（≤ 20000），第二行 n 個整數（0 ≤ h ≤ 10^9）。", "一個整數。",
  "單調 stack", "維持高度遞增的 stack；遇到較矮的柱子就彈出並以被彈出者為最低高度計算面積，寬度由新的 stack 頂到目前位置決定。",
  "n=int(input());h=list(map(int,input().split()))+[0];st=[];best=0\nfor i,x in enumerate(h):\n    while st and h[st[-1]]>=x:\n        H=h[st.pop()];W=i-st[-1]-1 if st else i\n        best=max(best,H*W)\n    st.append(i)\nprint(best)",
  ["6\n2 1 5 6 2 3\n", "1\n5\n", "3\n0 0 0\n", "4\n4 4 4 4\n", "5\n1 2 3 4 5\n",
   (lambda r: lines(20000, " ".join(str(r.randint(0,10**9)) for _ in range(20000))))(rng(402))],
  "每根柱子最多進出 stack 一次，所以是 O(n)。", diff=3, reserve=True)

D("e403", "可免費通過的路", 4, "分層最短路",
  "無向加權圖 n 點 m 邊。你可以讓最多 K 條邊的成本變成 0（選擇哪些邊由你決定）。求點 1 到點 n 的最小總成本；不連通輸出 -1。",
  "第一行 n m K（n ≤ 1000, m ≤ 5000, K ≤ 5），接著 m 行 `u v w`（1 ≤ w ≤ 10^6）。", "一個整數。",
  "擴充狀態的 Dijkstra", "狀態 (點, 已用免費次數)：dist[v][j]。走一條邊有兩種轉移：付費（j 不變）或免費（j+1，需 j<K）。答案取 min over j。",
  "import heapq,sys\nd=sys.stdin.read().split()\nn,m,K=int(d[0]),int(d[1]),int(d[2])\nadj=[[] for _ in range(n+1)]\nfor i in range(m):\n    u,v,w=int(d[3+3*i]),int(d[4+3*i]),int(d[5+3*i]);adj[u].append((v,w));adj[v].append((u,w))\nI=float('inf');D=[[I]*(K+1) for _ in range(n+1)];D[1][0]=0;h=[(0,1,0)]\nwhile h:\n    c,u,j=heapq.heappop(h)\n    if c>D[u][j]: continue\n    for v,w in adj[u]:\n        if c+w<D[v][j]: D[v][j]=c+w;heapq.heappush(h,(c+w,v,j))\n        if j<K and c<D[v][j+1]: D[v][j+1]=c;heapq.heappush(h,(c,v,j+1))\nr=min(D[n]);print(r if r<I else -1)",
  ["3 3 1\n1 2 5\n2 3 7\n1 3 20\n", "2 1 0\n1 2 9\n", "2 1 3\n1 2 9\n", "3 1 2\n1 2 4\n", "1 0 2\n",
   (lambda r: (lambda E: lines(f"1000 {len(E)} 3", *[f"{a} {b} {w}" for a, b, w in E]))([(r.randint(1,999), r.randint(2,1000), r.randint(1,10**6)) for _ in range(5000)]))(rng(403))],
  "同一個點用了不同次數的免費機會，是不同的狀態。", diff=4, reserve=True)
