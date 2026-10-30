"""階段 4：C++ 與進階演算法（20 題）。這些題 Python 容易超時，是練習改用 C++ 的素材。"""
from common import D, lines, rng


def rs(seed, n, alpha):
    r = rng(seed)
    return "".join(r.choice(alpha) for _ in range(n))


D("d076", "最長共同子序列（大）", 4, "DP／效能",
  "同 d070，但兩個字串長度各最多 3000。",
  "兩行字串（小寫英文字母）。", "一個整數。",
  "LCS（用 C++ 改寫）", "演算法與 d070 相同：9×10^6 個格子。Python 約 5 秒以上，C++ 不到 0.1 秒。這題的目的是『把 Python 解法翻成 C++ 並通過』。",
  "a=input();b=input()\nm=len(b);prev=[0]*(m+1)\nfor x in a:\n    cur=[0]*(m+1)\n    for j in range(1,m+1):\n        cur[j]=prev[j-1]+1 if x==b[j-1] else (prev[j] if prev[j]>cur[j-1] else cur[j-1])\n    prev=cur\nprint(prev[m])",
  ["abcde\nace\n", "a\nb\n", lines(rs(76, 2000, "abc"), rs(77, 2000, "abc")), lines(rs(78, 3000, "ab"), rs(79, 3000, "ab"))],
  "第一次感受到『同樣的演算法，語言不同差 50 倍』。", diff=3, timeout=90)

D("d077", "質數個數（大）", 4, "篩法／效能",
  "輸入 N，輸出 1..N 之間質數的個數。",
  "每行一個 N（≤ 3×10^7），最多 3 行，讀到 EOF。", "每行一個整數。",
  "篩法（C++ 練習）", "線性篩或埃氏篩；C++ 用 vector<bool> 或 vector<char>。Python 用 bytearray 切片賦值可以勉強過。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        N=int(l)\n        sv=bytearray([1])*(N+1);sv[0:2]=b'\\0\\0'[:min(2,N+1)]\n        for i in range(2,int(N**.5)+1):\n            if sv[i]: sv[i*i::i]=bytearray(len(range(i*i,N+1,i)))\n        print(sum(sv))",
  ["10\n", "1\n2\n100\n1000000\n", "30000000\n", "29999999\n"],
  "記憶體也要估：3×10^7 個 bool 約 30MB（char）或 4MB（bitset）。", diff=2, timeout=60)

D("d078", "背包（大）", 4, "DP／效能",
  "同 d068 的 0/1 背包，但 n ≤ 1000、W ≤ 50000。",
  "第一行 n W；接著 n 行 `w v`。", "一個整數。",
  "背包（C++ 練習）", "5×10^7 次轉移。Python 迴圈會超時，C++ 幾十毫秒。",
  "n,W=map(int,input().split());dp=[0]*(W+1)\nfor _ in range(n):\n    w,v=map(int,input().split())\n    if w<=W: dp[w:]=[a if a>b+v else b+v for a,b in zip(dp[w:],dp)]\nprint(dp[W])",
  ["3 50\n10 60\n20 100\n30 120\n", "1 5\n6 100\n",
   (lambda r: lines("1000 50000", *[f"{r.randint(1,2000)} {r.randint(1,10**6)}" for _ in range(1000)]))(rng(78))],
  "狀態數 × 轉移數 = 運算量。10^8 以內 C++ 安全，Python 約 10^7 就危險。", diff=3, timeout=90)

D("d079", "Floyd（大）", 4, "最短路徑／效能",
  "無向加權圖 n ≤ 400 個點，m 條邊，q 個查詢 `a b`，輸出最短距離，不連通輸出 -1。",
  "第一行 n m q；接著 m 行 `u v w`（1 ≤ w ≤ 1000）；接著 q 行查詢。", "q 行。",
  "Floyd（C++ 練習）", "6.4×10^7 次三重迴圈。Python 超時，C++ 約 0.1 秒。",
  "import sys\nd=sys.stdin.read().split()\nn,m,q=int(d[0]),int(d[1]),int(d[2])\nI=10**9;D=[[I]*(n+1) for _ in range(n+1)]\nfor i in range(n+1): D[i][i]=0\ni=3\nfor _ in range(m):\n    u,v,w=int(d[i]),int(d[i+1]),int(d[i+2]);i+=3\n    if w<D[u][v]: D[u][v]=D[v][u]=w\nfor k in range(1,n+1):\n    rk=D[k]\n    for a in range(1,n+1):\n        dak=D[a][k]\n        if dak<I:\n            ra=D[a]\n            D[a]=[x if x<dak+y else dak+y for x,y in zip(ra,rk)]\nfor _ in range(q):\n    a,b=int(d[i]),int(d[i+1]);i+=2;print(D[a][b] if D[a][b]<I else -1)",
  ["3 2 2\n1 2 4\n2 3 5\n1 3\n3 1\n",
   (lambda r: (lambda E: lines("400 3000 1000", *[f"{a} {b} {w}" for a, b, w in E], *[f"{r.randint(1,400)} {r.randint(1,400)}" for _ in range(1000)]))([(r.randint(1,399), r.randint(2,400), r.randint(1,1000)) for _ in range(3000)]))(rng(79))],
  "", diff=3, timeout=120)

D("d080", "凸包", 4, "計算幾何",
  "平面上 n 個整數座標點（可能重複、共線）。輸出凸包的頂點數（共線的點不算頂點），以及凸包面積的兩倍（整數）。若所有點共線，頂點數輸出 2（只有兩端點）、面積 0；只有一個相異點則頂點數 1、面積 0。",
  "第一行 n（≤ 20000），接著 n 行 `x y`（|x|,|y| ≤ 10^6）。", "一行：頂點數 面積兩倍。",
  "凸包（Andrew monotone chain）", "點排序後做上下兩段；用叉積 cross(o,a,b) <= 0 時彈出（去掉共線點）。面積用 shoelace 公式。",
  "import sys\nd=sys.stdin.read().split()\nn=int(d[0])\nP=sorted(set((int(d[1+2*i]),int(d[2+2*i])) for i in range(n)))\nif len(P)<=2:\n    print(len(P),0)\nelse:\n    def cr(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])\n    lo=[]\n    for p in P:\n        while len(lo)>=2 and cr(lo[-2],lo[-1],p)<=0: lo.pop()\n        lo.append(p)\n    up=[]\n    for p in reversed(P):\n        while len(up)>=2 and cr(up[-2],up[-1],p)<=0: up.pop()\n        up.append(p)\n    H=lo[:-1]+up[:-1]\n    a=sum(H[i][0]*H[(i+1)%len(H)][1]-H[(i+1)%len(H)][0]*H[i][1] for i in range(len(H)))\n    print(len(H),abs(a))",
  ["4\n0 0\n1 0\n1 1\n0 1\n", "1\n5 5\n", "3\n0 0\n1 1\n2 2\n", "5\n0 0\n2 0\n1 0\n2 2\n0 2\n", "2\n3 3\n3 3\n",
   (lambda r: lines(20000, *[f"{r.randint(-10**6,10**6)} {r.randint(-10**6,10**6)}" for _ in range(20000)]))(rng(80))],
  "叉積符號與『共線要不要保留』是幾何題最常見的細節。", diff=4)

D("d081", "線段相交", 4, "計算幾何",
  "每行 8 個整數 `x1 y1 x2 y2 x3 y3 x4 y4`，代表線段 AB 與 CD（端點可重合，線段可能退化成點）。若兩線段有任何共同點（包含端點接觸、共線重疊），輸出 `YES`，否則 `NO`。",
  "座標絕對值 ≤ 10^9，最多 1000 行，讀到 EOF。", "每行 YES 或 NO。",
  "叉積＋共線時的範圍檢查", "用 orientation 判斷兩端點在對方線段的兩側；共線時檢查投影範圍（bounding box）是否重疊。四個特例：端點接觸、共線不重疊、共線重疊、退化成點。",
  "import sys\ndef cr(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])\ndef sg(x): return (x>0)-(x<0)\ndef on(p,q,r): return min(p[0],q[0])<=r[0]<=max(p[0],q[0]) and min(p[1],q[1])<=r[1]<=max(p[1],q[1])\ndef inter(a,b,c,d):\n    d1,d2,d3,d4=sg(cr(a,b,c)),sg(cr(a,b,d)),sg(cr(c,d,a)),sg(cr(c,d,b))\n    if d1*d2<0 and d3*d4<0: return True\n    if d1==0 and on(a,b,c): return True\n    if d2==0 and on(a,b,d): return True\n    if d3==0 and on(c,d,a): return True\n    if d4==0 and on(c,d,b): return True\n    return False\nfor l in sys.stdin:\n    v=list(map(int,l.split()))\n    if len(v)==8: print('YES' if inter(tuple(v[0:2]),tuple(v[2:4]),tuple(v[4:6]),tuple(v[6:8])) else 'NO')",
  ["0 0 2 2 0 2 2 0\n", "0 0 1 1 2 2 3 3\n0 0 2 2 1 1 3 3\n0 0 1 0 1 0 2 5\n0 0 0 0 0 0 0 0\n0 0 4 0 2 0 2 3\n0 0 1 1 1 2 2 3\n5 5 5 5 1 1 9 9\n",
   (lambda r: lines(*[" ".join(str(r.randint(-5,5)) for _ in range(8)) for _ in range(1000)]))(rng(81))],
  "邊界情況很多：建議自己造 10 組測資再提交。", diff=4)

D("d082", "多邊形面積", 4, "計算幾何",
  "給一個簡單多邊形（頂點依順時針或逆時針順序），輸出面積的兩倍（整數）。",
  "第一行 n（3 ≤ n ≤ 10^5），接著 n 行 `x y`（|x|,|y| ≤ 10^6）。", "一個整數。",
  "鞋帶公式（shoelace）", "sum(x_i*y_{i+1} - x_{i+1}*y_i) 的絕對值。用整數就不會有浮點誤差，所以題目才問『兩倍』。",
  "import sys\nd=sys.stdin.read().split()\nn=int(d[0])\nP=[(int(d[1+2*i]),int(d[2+2*i])) for i in range(n)]\nprint(abs(sum(P[i][0]*P[(i+1)%n][1]-P[(i+1)%n][0]*P[i][1] for i in range(n))))",
  ["4\n0 0\n2 0\n2 2\n0 2\n", "3\n0 0\n4 0\n0 3\n", "3\n0 0\n0 3\n4 0\n", "4\n-1 -1\n1 -1\n1 1\n-1 1\n"],
  "遇到幾何題，能用整數就不要用浮點。")

D("d083", "最短週期", 4, "字串（KMP 失敗函數）",
  "給字串 s，求最小的 p（1 ≤ p ≤ |s|）使得 s 是由 s[0:p] 重複（最後一次可以不完整）得到的字串。",
  "每行一個小寫字串（長度 ≤ 2×10^5），讀到 EOF，最多 5 行。", "每行一個整數。",
  "KMP 前綴函數", "pi[i] 是 s[0..i] 的最長相等真前後綴長度。答案是 n - pi[n-1]。O(n)。",
  "import sys\nfor l in sys.stdin:\n    s=l.strip()\n    if not s: continue\n    n=len(s);pi=[0]*n;k=0\n    for i in range(1,n):\n        while k and s[i]!=s[k]: k=pi[k-1]\n        if s[i]==s[k]: k+=1\n        pi[i]=k\n    print(n-pi[-1])",
  ["abcabcab\n", "aaaa\nabcd\nabab\nabcabcabc\na\nabaab\n", "ab"*100000+"a\n", ("a"*199999)+"b\n"],
  "暴力試每個 p 是 O(n²)。這是 KMP 的經典應用。", diff=3)

D("d084", "最長迴文子字串", 4, "字串／效能",
  "輸出字串中最長迴文子字串的長度。",
  "每行一個小寫字串（長度 ≤ 5000），讀到 EOF，最多 5 行。", "每行一個整數。",
  "中心擴展 / Manacher", "枚舉每個中心向兩邊擴展是 O(n²)。n=5000 時 Python 偏慢、C++ 輕鬆。進階：Manacher O(n)。",
  "import sys\ndef lp(s):\n    t='^#'+'#'.join(s)+'#$';n=len(t);P=[0]*n;C=R=0\n    for i in range(1,n-1):\n        if i<R: P[i]=min(R-i,P[2*C-i])\n        while t[i+1+P[i]]==t[i-1-P[i]]: P[i]+=1\n        if i+P[i]>R: C,R=i,i+P[i]\n    return max(P)\nfor l in sys.stdin:\n    s=l.strip()\n    if s: print(lp(s))",
  ["babad\n", "a\naa\nabc\nabacdfgdcaba\nforgeeksskeegfor\n", "a"*5000+"\n", rs(84, 5000, "ab") + "\n"],
  "『全部相同的字元』是中心擴展法最壞的輸入。", diff=3)

D("d085", "樹上最大獨立集", 4, "樹 DP",
  "n 個點的樹，選出最多的點，使得任兩個被選的點之間沒有邊。輸出最多能選幾個。",
  "第一行 n（≤ 25000），接著 n-1 行 `u v`。", "一個整數。",
  "樹 DP（含遞迴深度）", "dp[v][0/1]：v 不選／選的最大值；dp[v][1]=1+Σdp[c][0]，dp[v][0]=Σmax(dp[c]). 鏈狀的樹深度 10^5，Python 要改成迭代或調高 recursionlimit。",
  "import sys\nd=sys.stdin.read().split()\nn=int(d[0])\nadj=[[] for _ in range(n+1)]\nfor i in range(n-1):\n    u,v=int(d[1+2*i]),int(d[2+2*i]);adj[u].append(v);adj[v].append(u)\npar=[0]*(n+1);order=[];st=[1];par[1]=-1\nwhile st:\n    u=st.pop();order.append(u)\n    for v in adj[u]:\n        if v!=par[u]: par[v]=u;st.append(v)\na=[0]*(n+1);b=[1]*(n+1)\nfor u in reversed(order):\n    p=par[u]\n    if p>0: a[p]+=max(a[u],b[u]);b[p]+=a[u]\nprint(max(a[1],b[1]))",
  ["5\n1 2\n1 3\n3 4\n3 5\n", "1\n", "2\n1 2\n",
   lines(25000, *[f"{i} {i+1}" for i in range(1, 25000)]),
   (lambda r: lines(20000, *[f"{r.randint(1,i-1)} {i}" for i in range(2, 20001)]))(rng(85))],
  "鏈狀測資會讓遞迴爆掉，這是 Python 的限制。", diff=4)

D("d086", "逆序數對", 4, "分治／BIT",
  "給 n 個整數，求有幾對 i<j 滿足 a[i] > a[j]。",
  "第一行 n（≤ 30000），第二行 n 個整數。", "一個整數（可能很大）。",
  "合併排序計數 / 樹狀陣列", "在 merge sort 合併時，左邊剩下 m 個比右邊目前元素大的，就貢獻 m 個逆序對。或用 BIT 做座標壓縮後計數。",
  "import sys\nfrom bisect import bisect_right\ndef cnt(a):\n    if len(a)<2: return a,0\n    m=len(a)//2;l,x=cnt(a[:m]);r,y=cnt(a[m:]);c=x+y;o=[];i=j=0\n    while i<len(l) and j<len(r):\n        if l[i]<=r[j]: o.append(l[i]);i+=1\n        else: o.append(r[j]);j+=1;c+=len(l)-i\n    o+=l[i:]+r[j:];return o,c\nn=int(input());print(cnt(list(map(int,input().split())))[1])",
  ["5\n2 4 1 3 5\n", "1\n5\n", "5\n5 4 3 2 1\n", "4\n1 1 1 1\n",
   (lambda r: lines(30000, " ".join(str(r.randint(1,10**9)) for _ in range(30000))))(rng(86)),
   lines(30000, " ".join(str(30000-i) for i in range(30000)))],
  "答案可達 n²/2，C++ 要用 long long。", diff=4)

D("d087", "區間最小值", 4, "稀疏表／線段樹",
  "給長度 n 的陣列，q 個查詢 `l r`（1 起算），輸出 min(a[l..r])。",
  "第一行 n q（≤ 15000）；第二行 n 個整數；接著 q 行。", "每個查詢一行。",
  "RMQ（Sparse Table）", "預處理 st[k][i]=min(a[i..i+2^k-1])；查詢取兩個覆蓋的區塊：k=floor(log2(len))。預處理 O(n log n)，查詢 O(1)。",
  "import sys\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1]);a=list(map(int,d[2:2+n]))\nst=[a]\nk=1\nwhile 2*k<=n:\n    p=st[-1];st.append([min(p[i],p[i+k]) for i in range(n-2*k+1)]);k*=2\ni=2+n\nfor _ in range(q):\n    l,r=int(d[i])-1,int(d[i+1])-1;i+=2;j=(r-l+1).bit_length()-1;print(min(st[j][l],st[j][r-(1<<j)+1]))",
  ["5 3\n5 2 4 7 1\n1 3\n2 5\n4 4\n", "1 1\n9\n1 1\n",
   (lambda r: lines("15000 15000", " ".join(str(r.randint(-10**9,10**9)) for _ in range(15000)), *[f"{min(a,b)} {max(a,b)}" for a, b in ((r.randint(1,15000), r.randint(1,15000)) for _ in range(15000))]))(rng(87))],
  "這裡的 n 很小，暴力 min(a[l-1:r]) 也能過；真實考題會把 n、q 放大到 10^5 以上，所以要練會 O(1) 查詢的做法。", diff=3)

D("d088", "負權邊與負環", 4, "Bellman-Ford",
  "有向圖 n 點 m 邊，邊權可為負。若從點 1 出發能到達某個負環，輸出 `NEGATIVE CYCLE`；否則輸出點 1 到點 n 的最短距離，到不了輸出 `UNREACHABLE`。",
  "第一行 n m（n ≤ 500, m ≤ 3000），接著 m 行 `u v w`（|w| ≤ 1000）。", "一行。",
  "Bellman-Ford", "relax 所有邊 n-1 輪；第 n 輪還能更新，代表從 1 可達的負環存在。只有『已知有距離』的點才能 relax。",
  "import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\nE=[(int(d[2+3*i]),int(d[3+3*i]),int(d[4+3*i])) for i in range(m)]\nI=float('inf');D=[I]*(n+1);D[1]=0;neg=False\nfor it in range(n):\n    ch=False\n    for u,v,w in E:\n        if D[u]<I and D[u]+w<D[v]: D[v]=D[u]+w;ch=True\n    if not ch: break\n    if it==n-1: neg=True\nprint('NEGATIVE CYCLE' if neg else (D[n] if D[n]<I else 'UNREACHABLE'))",
  ["3 3\n1 2 4\n2 3 -2\n1 3 5\n", "2 2\n1 2 1\n2 1 -3\n", "3 1\n1 2 5\n", "1 0\n", "3 3\n2 3 1\n3 2 -5\n1 2 1\n", "4 3\n2 3 -1\n3 2 -1\n1 4 7\n",
   (lambda r: lines("500 3000", *[f"{r.randint(1,500)} {r.randint(1,500)} {r.randint(-5,1000)}" for _ in range(3000)]))(rng(88)),
   (lambda r: lines("500 3000", *[f"{u} {u+1} {r.randint(-3,10)}" for u in range(1, 500)], *[f"{r.randint(1,400)} {r.randint(401,500)} {r.randint(0,1000)}" for _ in range(3000-499)]))(rng(89))],
  "『從 1 可達』這個條件容易漏掉：不可達的負環不算。", diff=4)

D("d089", "強連通分量", 4, "SCC",
  "有向圖 n 點 m 邊。輸出強連通分量的個數與最大分量的大小。",
  "第一行 n m（n ≤ 10000, m ≤ 30000），接著 m 行 `u v`。", "一行：個數 最大大小。",
  "Kosaraju / Tarjan（迭代版）", "Kosaraju：第一次 DFS 記完成順序，轉置圖上依反序再 DFS。遞迴深度會到 n，Python 請寫成迭代。",
  "import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\ng=[[] for _ in range(n+1)];h=[[] for _ in range(n+1)]\nfor i in range(m):\n    u,v=int(d[2+2*i]),int(d[3+2*i]);g[u].append(v);h[v].append(u)\nseen=[0]*(n+1);order=[]\nfor s in range(1,n+1):\n    if seen[s]: continue\n    seen[s]=1;st=[(s,0)]\n    while st:\n        u,i=st.pop()\n        if i<len(g[u]):\n            st.append((u,i+1));v=g[u][i]\n            if not seen[v]: seen[v]=1;st.append((v,0))\n        else: order.append(u)\ncomp=[0]*(n+1);c=0;sizes=[]\nfor s in reversed(order):\n    if comp[s]: continue\n    c+=1;comp[s]=c;st=[s];k=0\n    while st:\n        u=st.pop();k+=1\n        for v in h[u]:\n            if not comp[v]: comp[v]=c;st.append(v)\n    sizes.append(k)\nprint(c,max(sizes))",
  ["5 5\n1 2\n2 3\n3 1\n3 4\n4 5\n", "1 0\n", "3 3\n1 2\n2 3\n3 1\n", "4 0\n",
   (lambda r: lines("10000 30000", *[f"{r.randint(1,10000)} {r.randint(1,10000)}" for _ in range(30000)]))(rng(90)),
   lines("10000 10000", *[f"{i} {i%10000+1}" for i in range(1, 10001)])],
  "環狀大圖會讓遞迴 DFS 在 Python 爆掉。", diff=4)

D("d090", "最大流（選修）", 4, "網路流",
  "有向圖 n 點 m 條邊，每條邊有容量。求從點 1（源）到點 n（匯）的最大流量。",
  "第一行 n m（n ≤ 50, m ≤ 300），接著 m 行 `u v c`（c ≤ 1000）。可能有重邊。", "一個整數。",
  "Edmonds–Karp（選修）", "反覆用 BFS 找增廣路，沿路徑扣掉瓶頸容量，並建立反向邊。CPE 少考，但打好基礎能理解『匹配』『最小割』。",
  "from collections import deque\nn,m=map(int,input().split())\ncap=[[0]*(n+1) for _ in range(n+1)]\nfor _ in range(m):\n    u,v,c=map(int,input().split());cap[u][v]+=c\nf=0\nwhile True:\n    par=[0]*(n+1);par[1]=-1;q=deque([1])\n    while q and not par[n]:\n        u=q.popleft()\n        for v in range(1,n+1):\n            if not par[v] and cap[u][v]>0: par[v]=u;q.append(v)\n    if not par[n]: break\n    b=10**18;v=n\n    while v!=1: b=min(b,cap[par[v]][v]);v=par[v]\n    v=n\n    while v!=1: cap[par[v]][v]-=b;cap[v][par[v]]+=b;v=par[v]\n    f+=b\nprint(f)",
  ["4 5\n1 2 3\n1 3 2\n2 3 1\n2 4 2\n3 4 3\n", "2 1\n1 2 5\n", "3 1\n1 2 5\n", "2 2\n1 2 3\n1 2 4\n",
   (lambda r: lines("50 300", *[f"{r.randint(1,49)} {r.randint(2,50)} {r.randint(1,1000)}" for _ in range(300)]))(rng(91))],
  "選修題。", diff=4)

D("d091", "有障礙的格子路徑數", 4, "DP（計數）",
  "R×C 的格子，`#` 是障礙，`.` 可走。只能往右或往下，從左上角走到右下角有幾種走法？對 1000000007 取餘數。（起點或終點是障礙則為 0）",
  "第一行 R C（≤ 400），接著 R 行字串。", "一個整數。",
  "網格 DP 計數", "dp[i][j] = dp[i-1][j] + dp[i][j-1]（該格非障礙）；起點 dp=1。邊界。",
  "R,C=map(int,input().split());g=[input() for _ in range(R)];M=10**9+7\ndp=[[0]*C for _ in range(R)]\nfor i in range(R):\n    for j in range(C):\n        if g[i][j]=='#': continue\n        if i==0 and j==0: dp[i][j]=1;continue\n        dp[i][j]=((dp[i-1][j] if i else 0)+(dp[i][j-1] if j else 0))%M\nprint(dp[R-1][C-1])",
  ["3 3\n...\n.#.\n...\n", "1 1\n.\n", "1 1\n#\n", "2 2\n.#\n#.\n", "3 3\n...\n...\n...\n",
   (lambda r: lines("400 400", *["".join("#" if r.random() < .05 and (i, j) not in ((0, 0), (399, 399)) else "." for j in range(400)) for i in range(400)]))(rng(92)),
   lines("400 400", *["." * 400 for _ in range(400)])],
  "答案很大，每一步都要取餘數。", diff=3)

D("d092", "取石子遊戲", 4, "博弈 DP",
  "一堆 n 顆石頭，兩人輪流取，每次可取的數量必須是給定集合 S 中的某個數（取不夠的數量不能選），不能取的人輸。先手必勝輸出 `WIN`，否則 `LOSE`。",
  "第一行 k q（k ≤ 10, q ≤ 1000）；第二行 k 個正整數 S；接著 q 行每行一個 n（0 ≤ n ≤ 10^6）。", "每個查詢一行。",
  "必勝／必敗狀態", "win[n] = 存在 s∈S 使 win[n-s] 為 False。只算到查詢中最大的 n 即可。10^7 次轉移在 Python 偏慢。",
  "import sys\nd=sys.stdin.read().split()\nk,q=int(d[0]),int(d[1]);S=sorted(map(int,d[2:2+k]));Q=[int(x) for x in d[2+k:2+k+q]]\nN=max(Q);w=bytearray(N+1)\nfor n in range(1,N+1):\n    for s in S:\n        if s>n: break\n        if not w[n-s]: w[n]=1;break\nfor n in Q: print('WIN' if w[n] else 'LOSE')",
  ["3 5\n1 3 4\n0 1 2 3 7\n", "1 3\n2\n0 1 2\n", "2 4\n3 5\n1 3 8 9\n",
   (lambda r: lines("5 1000", "2 3 7 11 13", *[r.randint(0,10**6) for _ in range(999)], 10**6))(rng(93))],
  "觀察週期也是一種解法。", diff=3, timeout=60)

D("d093", "歐拉函數", 4, "數論",
  "φ(n) 是 1..n 中與 n 互質的數的個數。對每個查詢 n 輸出 φ(n)。",
  "第一行 q（≤ 20000）；接著 q 行，n ≤ 10^6。", "每個查詢一行。",
  "篩法求 φ", "φ(n) = n·Π(1-1/p)。篩一次到 10^6：phi[i]=i；對每個質數 p，所有倍數 phi[m] -= phi[m]//p。",
  "import sys\nd=sys.stdin.read().split()\nq=int(d[0]);Q=[int(x) for x in d[1:1+q]];N=max(Q+[1])\nphi=list(range(N+1))\nfor p in range(2,N+1):\n    if phi[p]==p:\n        for m in range(p,N+1,p): phi[m]-=phi[m]//p\nfor n in Q: print(phi[n])",
  ["5\n1\n2\n6\n10\n12\n", "1\n1000000\n", "1\n999983\n",
   (lambda r: lines(20000, *[r.randint(1,10**6) for _ in range(20000)]))(rng(94))],
  "", diff=3, timeout=60)

D("d094", "數位 DP", 4, "數位 DP",
  "每行 `N S`：數 1..N 中有幾個數字的各位數字和恰為 S。",
  "N ≤ 10^18，S ≤ 162，最多 100 行，讀到 EOF。", "每行一個整數。",
  "Digit DP", "逐位決定：狀態（位置, 目前和, 是否貼著上界）。f(pos, sum, tight)。上界前綴相同時才受限。要小心 0 不計入 1..N。",
  "import sys\nfrom functools import lru_cache\ndef cnt(N,S):\n    ds=list(map(int,str(N)))\n    @lru_cache(None)\n    def f(i,s,t):\n        if s>S: return 0\n        if i==len(ds): return 1 if s==S else 0\n        top=ds[i] if t else 9\n        return sum(f(i+1,s+x,t and x==top) for x in range(top+1))\n    r=f(0,0,True)\n    return r-(1 if S==0 else 0)\nfor l in sys.stdin:\n    p=l.split()\n    if p: print(cnt(int(p[0]),int(p[1])))",
  ["100 1\n", "10 1\n99 9\n1000 27\n1 1\n1 0\n999999999999999999 81\n1000000000000000000 1\n", "123456789 45\n"],
  "暴力枚舉在 N=10^18 不可能。這題和 CPE 的距離比較遠，屬於進階選修。", diff=4)

D("d095", "運算式求值", 4, "解析／遞迴下降",
  "每行一個運算式，由非負整數、`+` `-` `*`、括號與空白組成（沒有一元負號）。依一般優先順序（括號 > 乘 > 加減，同級由左到右）計算並輸出結果（可能很大）。",
  "每行長度 ≤ 1000，讀到 EOF，最多 100 行。", "每行一個整數。",
  "遞迴下降解析", "expr = term (('+'|'-') term)*；term = factor ('*' factor)*；factor = number | '(' expr ')'。每個函式負責一個優先順序層級。",
  "import sys\nsys.setrecursionlimit(10000)\ndef ev(s):\n    t=s.replace(' ','');i=[0]\n    def e():\n        v=tm()\n        while i[0]<len(t) and t[i[0]] in '+-':\n            o=t[i[0]];i[0]+=1;x=tm();v=v+x if o=='+' else v-x\n        return v\n    def tm():\n        v=fc()\n        while i[0]<len(t) and t[i[0]]=='*': i[0]+=1;v*=fc()\n        return v\n    def fc():\n        if t[i[0]]=='(':\n            i[0]+=1;v=e();i[0]+=1;return v\n        j=i[0]\n        while j<len(t) and t[j].isdigit(): j+=1\n        v=int(t[i[0]:j]);i[0]=j;return v\n    return e()\nfor l in sys.stdin:\n    if l.strip(): print(ev(l))",
  ["1+2*3\n", "(1+2)*3\n10 - 2 - 3\n2*(3+(4*5))\n7\n((((1))))\n100*100*100*100\n0*5+3\n", "1 + 2 * (3 + 4 * (5 + 6)) - 7\n"],
  "做完這題，你就懂得『編譯器』在做什麼了。", diff=4)
