"""階段 3：圖論與 DP（16 題）。"""
from common import D, lines, rng


def grid_case(seed, R, C, p, block=False):
    r = rng(seed)
    g = [["#" if r.random() < p else "." for _ in range(C)] for _ in range(R)]
    g[0][0] = "S"; g[R-1][C-1] = "E"
    if block:
        g[R-2][C-1] = "#"; g[R-1][C-2] = "#"
    return lines(f"{R} {C}", *["".join(row) for row in g])


def graph_case(seed, n, m, wmax=1000, extra_tree=True):
    r = rng(seed)
    edges = []
    if extra_tree:
        for v in range(2, n+1): edges.append((r.randint(1, v-1), v, r.randint(1, wmax)))
    while len(edges) < m:
        a, b = r.randint(1, n), r.randint(1, n)
        if a != b: edges.append((a, b, r.randint(1, wmax)))
    r.shuffle(edges)
    return lines(f"{n} {len(edges)}", *[f"{a} {b} {w}" for a, b, w in edges])


D("d060", "迷宮最短路", 3, "BFS",
  "R×C 的迷宮，`#` 是牆，`.` 是路，`S` 起點、`E` 終點。每步可往上下左右走一格，求 S 到 E 的最少步數；到不了輸出 -1。",
  "第一行 R C（≤ 200），接著 R 行字串。恰有一個 S 與一個 E。", "一個整數。",
  "BFS（最短路徑，邊權相同）", "用 deque；dist 陣列初始 -1；每個格子只入隊一次；第一次到達 E 的距離就是最短。",
  "from collections import deque\nR,C=map(int,input().split())\ng=[input() for _ in range(R)]\nfor i in range(R):\n    for j in range(C):\n        if g[i][j]=='S': s=(i,j)\n        if g[i][j]=='E': e=(i,j)\nd=[[-1]*C for _ in range(R)];d[s[0]][s[1]]=0;q=deque([s])\nwhile q:\n    x,y=q.popleft()\n    for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):\n        a,b=x+dx,y+dy\n        if 0<=a<R and 0<=b<C and g[a][b]!='#' and d[a][b]<0: d[a][b]=d[x][y]+1;q.append((a,b))\nprint(d[e[0]][e[1]])",
  ["3 3\nS..\n.#.\n..E\n", "1 2\nSE\n", "3 3\nS#.\n###\n..E\n", "2 5\nS.#.E\n..#..\n",
   grid_case(60, 200, 200, 0.2), grid_case(61, 150, 150, 0.1, True)],
  "BFS 保證『第一次到達』就是最短距離。DFS 做不到。", diff=2)

D("d061", "並查集：連通分量", 3, "並查集",
  "n 個點，m 次操作 `a b` 表示把 a 與 b 所在的群組合併。全部做完後，輸出群組數與最大群組的大小。",
  "第一行 n m（n, m ≤ 50000），接著 m 行。", "一行：群組數 最大群組大小。",
  "Disjoint Set Union", "parent[] 加上路徑壓縮（find 時把路徑上的點直接指向根）、按大小合併；維護 size[]。",
  "import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\np=list(range(n+1));sz=[1]*(n+1)\ndef f(x):\n    while p[x]!=x: p[x]=p[p[x]];x=p[x]\n    return x\nc=n\nfor i in range(m):\n    a,b=f(int(d[2+2*i])),f(int(d[3+2*i]))\n    if a!=b:\n        if sz[a]<sz[b]: a,b=b,a\n        p[b]=a;sz[a]+=sz[b];c-=1\nprint(c,max(sz[f(i)] for i in range(1,n+1)))",
  ["5 3\n1 2\n2 3\n4 5\n", "1 0\n", "4 2\n1 2\n1 2\n", "3 3\n1 1\n2 3\n3 2\n",
   (lambda r: lines("50000 35000", *[f"{r.randint(1,50000)} {r.randint(1,50000)}" for _ in range(35000)]))(rng(61))],
  "要同時會『路徑壓縮』與『依大小合併』，單獨用其一也夠快，但兩個都用最穩。", diff=2)

D("d062", "字典序最小的拓撲排序", 3, "拓撲排序",
  "有向圖 n 個點 m 條邊 `u v` 表示 u 必須在 v 之前。輸出字典序最小的合法順序；若有環輸出 -1。",
  "第一行 n m（n ≤ 20000, m ≤ 40000），接著 m 行。可能有重邊。", "一行 n 個數字，或 -1。",
  "Kahn 演算法＋最小堆積", "入度為 0 的點放進 min-heap；每次取最小的，拿掉它的出邊並更新入度。最後數量不足 n 就是有環。",
  "import heapq,sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\nadj=[[] for _ in range(n+1)];ind=[0]*(n+1)\nfor i in range(m):\n    u,v=int(d[2+2*i]),int(d[3+2*i]);adj[u].append(v);ind[v]+=1\nh=[i for i in range(1,n+1) if ind[i]==0];heapq.heapify(h);o=[]\nwhile h:\n    u=heapq.heappop(h);o.append(u)\n    for v in adj[u]:\n        ind[v]-=1\n        if ind[v]==0: heapq.heappush(h,v)\nprint(*(o if len(o)==n else [-1]))",
  ["4 3\n1 2\n1 3\n3 4\n", "3 3\n1 2\n2 3\n3 1\n", "3 0\n", "4 4\n4 3\n3 2\n2 1\n4 1\n", "2 2\n1 2\n1 2\n",
   (lambda r: (lambda E: lines(f"20000 {len(E)}", *[f"{a} {b}" for a, b in E]))([(min(x, y), max(x, y)) for x, y in ((r.randint(1, 20000), r.randint(1, 20000)) for _ in range(40000)) if x != y]))(rng(62))],
  "輸入若有 u==v 的邊會變成環；本測資已避免。", diff=3)

D("d063", "Dijkstra 最短路徑", 3, "最短路徑",
  "無向加權圖 n 點 m 邊，求點 1 到點 n 的最短距離；不連通輸出 -1。",
  "第一行 n m（n ≤ 5000, m ≤ 2×10^4），接著 m 行 `u v w`（1 ≤ w ≤ 1000）。", "一個整數。",
  "Dijkstra＋優先佇列", "heapq 存 (dist, node)；取出時若 dist 比紀錄的大就跳過（lazy deletion）。O((n+m) log n)。",
  "import heapq,sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\nadj=[[] for _ in range(n+1)]\nfor i in range(m):\n    u,v,w=int(d[2+3*i]),int(d[3+3*i]),int(d[4+3*i]);adj[u].append((v,w));adj[v].append((u,w))\nINF=float('inf');dist=[INF]*(n+1);dist[1]=0;h=[(0,1)]\nwhile h:\n    du,u=heapq.heappop(h)\n    if du>dist[u]: continue\n    for v,w in adj[u]:\n        if du+w<dist[v]: dist[v]=du+w;heapq.heappush(h,(dist[v],v))\nprint(dist[n] if dist[n]<INF else -1)",
  ["3 3\n1 2 5\n2 3 5\n1 3 20\n", "2 0\n", "1 0\n", "4 2\n1 2 1\n3 4 1\n", graph_case(63, 5000, 20000), graph_case(64, 4000, 15000, 50)],
  "O(n²) 的 Dijkstra 在 n=5000 時要 2.5×10^7 次，Python 會很吃力；堆積版快很多。", diff=3)

D("d064", "最小生成樹", 3, "MST",
  "無向加權連通圖，求最小生成樹的總權重；若圖不連通輸出 -1。",
  "第一行 n m（n ≤ 5000, m ≤ 2×10^4），接著 m 行 `u v w`。", "一個整數。",
  "Kruskal＋並查集", "邊依權重排序，依序嘗試合併，兩端已連通就跳過；選到 n-1 條邊即完成。",
  "import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\nE=sorted((int(d[4+3*i]),int(d[2+3*i]),int(d[3+3*i])) for i in range(m))\np=list(range(n+1))\ndef f(x):\n    while p[x]!=x: p[x]=p[p[x]];x=p[x]\n    return x\nt=c=0\nfor w,u,v in E:\n    a,b=f(u),f(v)\n    if a!=b: p[a]=b;t+=w;c+=1\nprint(t if c==n-1 else -1)",
  ["3 3\n1 2 1\n2 3 2\n1 3 3\n", "1 0\n", "4 2\n1 2 1\n3 4 1\n", "2 2\n1 2 9\n1 2 3\n", graph_case(65, 5000, 20000), graph_case(66, 2500, 10000, 30)],
  "Kruskal 與 Prim 都要會；先學 Kruskal，因為它只用到排序＋並查集。", diff=3)

D("d065", "Floyd–Warshall 全點對最短路", 3, "最短路徑",
  "無向加權圖 n ≤ 100 個點，m 條邊，q 個查詢 `a b`，輸出 a 到 b 的最短距離；不連通輸出 -1。",
  "第一行 n m q；接著 m 行 `u v w`；接著 q 行查詢。", "q 行。",
  "Floyd–Warshall", "dist[i][j] = min(dist[i][j], dist[i][k]+dist[k][j])，k 必須是最外層迴圈。",
  "import sys\nd=sys.stdin.read().split()\nn,m,q=int(d[0]),int(d[1]),int(d[2])\nI=10**18;D=[[I]*(n+1) for _ in range(n+1)]\nfor i in range(n+1): D[i][i]=0\ni=3\nfor _ in range(m):\n    u,v,w=int(d[i]),int(d[i+1]),int(d[i+2]);i+=3\n    if w<D[u][v]: D[u][v]=D[v][u]=w\nfor k in range(1,n+1):\n    for a in range(1,n+1):\n        for b in range(1,n+1):\n            if D[a][k]+D[k][b]<D[a][b]: D[a][b]=D[a][k]+D[k][b]\nfor _ in range(q):\n    a,b=int(d[i]),int(d[i+1]);i+=2;print(D[a][b] if D[a][b]<I else -1)",
  ["3 2 3\n1 2 4\n2 3 5\n1 3\n3 1\n1 1\n", "2 0 1\n1 2\n", "4 5 2\n1 2 1\n2 3 1\n3 4 1\n1 4 10\n1 3 5\n1 4\n2 4\n",
   (lambda r: (lambda e: lines("100 400 200", *[f"{a} {b} {w}" for a, b, w in e], *[f"{r.randint(1,100)} {r.randint(1,100)}" for _ in range(200)]))([(r.randint(1,99), 100 if i == 0 else r.randint(1,100), r.randint(1,50)) for i in range(400)]))(rng(65))],
  "迴圈順序寫錯（k 不在最外層）是 Floyd 最經典的錯誤。", diff=3)

D("d066", "硬幣組合數", 3, "DP（計數）",
  "有 n 種面額（各不相同，每種無限多個），湊出金額 A 有幾種組合（不計順序）？答案對 1000000007 取餘數。",
  "第一行 n A（n ≤ 50, A ≤ 10^4）；第二行 n 個面額（≤ 10^4）。", "一個整數。",
  "背包型 DP（無限背包計數）", "dp[0]=1；外層迴圈跑面額、內層跑金額 a=c..A：dp[a]+=dp[a-c]。外層是面額才不會把順序算成不同。",
  "n,A=map(int,input().split());cs=list(map(int,input().split()))\nM=10**9+7;dp=[0]*(A+1);dp[0]=1\nfor c in cs:\n    for a in range(c,A+1): dp[a]=(dp[a]+dp[a-c])%M\nprint(dp[A])",
  ["3 4\n1 2 3\n", "1 5\n5\n", "1 3\n2\n", "2 0\n1 2\n", "5 10000\n1 5 10 50 100\n", "20 10000\n" + " ".join(str(x) for x in (1,2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67)) + "\n"],
  "迴圈順序決定『組合』還是『排列』，這是 DP 最重要的觀察之一。", diff=3)

D("d067", "最少硬幣數", 3, "DP（最佳化）",
  "有 n 種面額（各不相同、每種無限多個），湊出金額 A 最少要幾枚硬幣？湊不出來輸出 -1。",
  "第一行 n A（n ≤ 100, A ≤ 10^4）；第二行 n 個面額。", "一個整數。",
  "DP 狀態轉移", "dp[a] = min(dp[a-c]+1)；dp[0]=0，其餘初始為無限大。貪心（先拿大面額）在一般面額下是錯的。",
  "n,A=map(int,input().split());cs=list(map(int,input().split()))\nI=10**9;dp=[I]*(A+1);dp[0]=0\nfor a in range(1,A+1):\n    for c in cs:\n        if c<=a and dp[a-c]+1<dp[a]: dp[a]=dp[a-c]+1\nprint(dp[A] if dp[A]<I else -1)",
  ["3 11\n1 2 5\n", "1 3\n2\n", "3 6\n1 3 4\n", "2 0\n5 7\n", "4 10000\n1 7 13 29\n", "5 9999\n10 20 50 100 200\n"],
  "測資包含貪心會錯的例子（6 = 3+3，不是 4+1+1）。", diff=3)

D("d068", "0/1 背包", 3, "DP（背包）",
  "n 個物品，第 i 個重量 w 價值 v，背包容量 W。每個物品最多選一次，求最大總價值。",
  "第一行 n W（n ≤ 100, W ≤ 10^4）；接著 n 行 `w v`。", "一個整數。",
  "0/1 背包", "dp[j] 為容量 j 時的最大價值；對每個物品，j 要『由大到小』更新，避免同一物品被選兩次。",
  "n,W=map(int,input().split());dp=[0]*(W+1)\nfor _ in range(n):\n    w,v=map(int,input().split())\n    for j in range(W,w-1,-1):\n        if dp[j-w]+v>dp[j]: dp[j]=dp[j-w]+v\nprint(dp[W])",
  ["3 50\n10 60\n20 100\n30 120\n", "1 5\n6 100\n", "2 10\n5 5\n5 5\n", "3 0\n1 1\n2 2\n3 3\n",
   (lambda r: lines("100 10000", *[f"{r.randint(1,500)} {r.randint(1,1000)}" for _ in range(100)]))(rng(68))],
  "內層迴圈由大到小，是 0/1 與無限背包唯一的差別。", diff=3)

D("d069", "最長遞增子序列", 3, "DP＋二分",
  "給長度 n 的整數序列，求最長嚴格遞增子序列（可以不連續）的長度。",
  "第一行 n（≤ 50000），第二行 n 個整數。", "一個整數。",
  "LIS 的 O(n log n) 解法", "O(n²) 的 dp[i] 在 n=5×10^4 會超時。維護 tails[]：tails[k] 是長度 k+1 的遞增子序列最小結尾；每個數用 bisect_left 找位置取代。",
  "import bisect\nn=int(input());t=[]\nfor x in map(int,input().split()):\n    i=bisect.bisect_left(t,x)\n    if i==len(t): t.append(x)\n    else: t[i]=x\nprint(len(t))",
  ["8\n10 9 2 5 3 7 101 18\n", "1\n5\n", "5\n5 4 3 2 1\n", "5\n2 2 2 2 2\n", "6\n1 2 3 4 5 6\n",
   (lambda r: lines(50000, " ".join(str(r.randint(1,10**9)) for _ in range(50000))))(rng(69))],
  "先寫 O(n²) 版本理解 dp，再升級成 O(n log n)。", diff=3)

D("d070", "最長共同子序列", 3, "DP（二維）",
  "給兩個字串（只含小寫英文字母，長度 ≤ 1000），求最長共同子序列的長度。",
  "兩行，各一個字串。", "一個整數。",
  "LCS 二維 DP", "dp[i][j] 為 a 前 i 個與 b 前 j 個的 LCS；字元相等取 dp[i-1][j-1]+1，否則取 max(dp[i-1][j], dp[i][j-1])。",
  "a=input();b=input()\nm=len(b);prev=[0]*(m+1)\nfor x in a:\n    cur=[0]*(m+1)\n    for j in range(1,m+1):\n        cur[j]=prev[j-1]+1 if x==b[j-1] else max(prev[j],cur[j-1])\n    prev=cur\nprint(prev[m])",
  ["abcde\nace\n", "abc\nabc\n", "abc\ndef\n", "a\na\n",
   (lambda r: lines("".join(r.choice("abcd") for _ in range(1000)), "".join(r.choice("abcd") for _ in range(1000))))(rng(70))],
  "二維 DP 可以用滾動陣列把空間降成一維。", diff=3)

D("d071", "最大連續子陣列和", 3, "DP（Kadane）",
  "給 n 個整數（可能為負），求非空連續子陣列的最大總和。",
  "第一行 n（≤ 50000），第二行 n 個整數。", "一個整數。",
  "Kadane 演算法", "cur = max(x, cur+x)；ans = max(ans, cur)。ans 不能從 0 開始（全負數時答案是最大的那個負數）。",
  "n=int(input());a=list(map(int,input().split()))\ncur=best=a[0]\nfor x in a[1:]:\n    cur=max(x,cur+x);best=max(best,cur)\nprint(best)",
  ["9\n-2 1 -3 4 -1 2 1 -5 4\n", "1\n-5\n", "3\n-3 -1 -2\n", "4\n1 2 3 4\n",
   (lambda r: lines(50000, " ".join(str(r.randint(-1000,1000)) for _ in range(50000))))(rng(71))],
  "初始值與『全負數』是這題的考點。", diff=2)

D("d072", "網格最小路徑和", 3, "DP（網格）",
  "R×C 的格子，每格有非負整數。從左上角走到右下角，每步只能往右或往下，求經過的數字總和最小是多少。",
  "第一行 R C（≤ 300）；接著 R 行各 C 個整數（≤ 1000）。", "一個整數。",
  "網格 DP", "dp[i][j] = a[i][j] + min(dp[i-1][j], dp[i][j-1])；第一列與第一行單獨處理。",
  "R,C=map(int,input().split())\na=[list(map(int,input().split())) for _ in range(R)]\nfor i in range(R):\n    for j in range(C):\n        if i==0 and j==0: continue\n        a[i][j]+=min(a[i-1][j] if i else 10**18, a[i][j-1] if j else 10**18)\nprint(a[R-1][C-1])",
  ["3 3\n1 3 1\n1 5 1\n4 2 1\n", "1 1\n5\n", "1 4\n1 2 3 4\n", "3 1\n1\n2\n3\n",
   (lambda r: lines("300 300", *[" ".join(str(r.randint(0,1000)) for _ in range(300)) for _ in range(300)]))(rng(72))],
  "邊界處理是這題的重點。", diff=2)

D("d073", "矩陣連乘", 3, "區間 DP",
  "n 個矩陣相乘，第 i 個矩陣大小為 p[i-1]×p[i]。找出加括號方式使純量乘法次數最少，輸出最少次數。",
  "第一行 n（≤ 100）；第二行 n+1 個整數 p[0..n]（≤ 100）。", "一個整數。",
  "區間 DP", "dp[i][j]：第 i 到 j 個矩陣相乘的最小成本；枚舉分割點 k：dp[i][k]+dp[k+1][j]+p[i-1]*p[k]*p[j]。依區間長度由小到大計算。",
  "n=int(input());p=list(map(int,input().split()))\ndp=[[0]*(n+1) for _ in range(n+1)]\nfor L in range(2,n+1):\n    for i in range(1,n-L+2):\n        j=i+L-1;dp[i][j]=min(dp[i][k]+dp[k+1][j]+p[i-1]*p[k]*p[j] for k in range(i,j))\nprint(dp[1][n])",
  ["3\n10 30 5 60\n", "1\n5 6\n", "2\n3 4 5\n", "4\n40 20 30 10 30\n",
   (lambda r: lines(100, " ".join(str(r.randint(1,100)) for _ in range(101))))(rng(73))],
  "區間 DP 的迴圈順序：先枚舉『長度』。", diff=3)

D("d074", "旅行推銷員（小規模）", 3, "位元遮罩 DP",
  "n 個城市（n ≤ 12），給距離矩陣 d[i][j]（可能不對稱）。從城市 0 出發，每個城市恰好拜訪一次，最後回到 0，求最短總距離。n=1 時答案為 0。",
  "第一行 n；接著 n 行各 n 個整數（0 ≤ d ≤ 1000）。", "一個整數。",
  "bitmask DP", "dp[mask][i]：已訪問集合為 mask、目前在 i 的最短距離；轉移到未訪問的 j。時間 O(2^n · n²)。",
  "n=int(input());d=[list(map(int,input().split())) for _ in range(n)]\nI=10**18;dp=[[I]*n for _ in range(1<<n)];dp[1][0]=0\nfor m in range(1<<n):\n    for i in range(n):\n        if dp[m][i]>=I or not m>>i&1: continue\n        for j in range(n):\n            if not m>>j&1:\n                v=dp[m][i]+d[i][j]\n                if v<dp[m|1<<j][j]: dp[m|1<<j][j]=v\nprint(min(dp[(1<<n)-1][i]+d[i][0] for i in range(n)))",
  ["3\n0 10 15\n10 0 20\n15 20 0\n", "1\n0\n", "2\n0 5\n7 0\n",
   (lambda r: lines(10, *[" ".join("0" if i == j else str(r.randint(1,1000)) for j in range(10)) for i in range(10)]))(rng(74)),
   (lambda r: lines(12, *[" ".join("0" if i == j else str(r.randint(1,1000)) for j in range(12)) for i in range(12)]))(rng(75))],
  "n ≤ 12~20 通常暗示 bitmask。n=12 在 Python 約 10^7 次運算，要注意常數。", diff=4, timeout=60)

D("d075", "組合數取模", 3, "數論／預處理",
  "q 個查詢，每個查詢 `n r`，輸出 C(n, r) 對 1000000007 取餘數（r > n 時為 0）。",
  "第一行 q（≤ 20000）；接著 q 行；n ≤ 10^6。", "每個查詢一行。",
  "階乘預處理＋模逆元", "預先算 fact[0..N]；用費馬小定理 inv_fact[N]=pow(fact[N], p-2, p)，再往下遞推 inv_fact[i-1]=inv_fact[i]*i。",
  "import sys\nd=sys.stdin.read().split()\nq=int(d[0]);M=10**9+7\nN=max([int(d[1+2*i]) for i in range(q)]+[1])\nf=[1]*(N+1)\nfor i in range(1,N+1): f[i]=f[i-1]*i%M\ninv=[1]*(N+1);inv[N]=pow(f[N],M-2,M)\nfor i in range(N,0,-1): inv[i-1]=inv[i]*i%M\nfor i in range(q):\n    n,r=int(d[1+2*i]),int(d[2+2*i])\n    print(0 if r>n or r<0 else f[n]*inv[r]%M*inv[n-r]%M)",
  ["3\n5 2\n10 0\n4 5\n", "1\n1000000 500000\n", "2\n0 0\n1 1\n",
   (lambda r: lines(20000, *[f"{n} {r.randint(0,n)}" for n in (r.randint(0,10**6) for _ in range(20000))]))(rng(76))],
  "模數運算：不能直接除，要乘『模逆元』。", diff=3)
