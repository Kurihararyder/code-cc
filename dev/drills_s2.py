"""階段 2：資料結構與基礎演算法（14 題）。"""
from common import D, lines, rng


def big_arr(seed, n, lo, hi):
    r = rng(seed)
    return [r.randint(lo, hi) for _ in range(n)]


D("d046", "區間和查詢", 2, "前綴和",
  "給長度 n 的陣列與 q 個查詢，每個查詢 l r（1 起算），輸出 a[l]+…+a[r]。",
  "第一行 n q；第二行 n 個整數；接著 q 行 l r。n, q ≤ 20000，|a| ≤ 10^6。", "每個查詢一行。",
  "前綴和", "先算 pre[i]=pre[i-1]+a[i]，答案 = pre[r]-pre[l-1]。每個查詢 O(1)。",
  "import sys\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1])\npre=[0]\nfor x in d[2:2+n]: pre.append(pre[-1]+int(x))\ni=2+n\nfor _ in range(q):\n    l,r=int(d[i]),int(d[i+1]);i+=2;print(pre[r]-pre[l-1])",
  ["5 3\n1 2 3 4 5\n1 5\n2 3\n5 5\n", "1 1\n-7\n1 1\n",
   (lambda r: lines("20000 20000", " ".join(str(r.randint(-10**6, 10**6)) for _ in range(20000)),
                    *[f"{min(a,b)} {max(a,b)}" for a, b in ((r.randint(1,20000), r.randint(1,20000)) for _ in range(20000))]))(rng(46))],
  "每次查詢都手寫迴圈加總是 O(nq)，在這裡會超時（用內建 sum(a[l-1:r]) 在這個規模勉強過，但 n、q 放大 5 倍就不行——考題通常會放大）。", diff=2)

D("d047", "第一個不小於 x 的位置", 2, "二分搜尋",
  "給遞增（可重複）排序好的陣列，對每個查詢 x，輸出最小的位置 i（1 起算）使得 a[i] ≥ x；若不存在輸出 n+1。",
  "第一行 n q；第二行 n 個遞增整數；第三行 q 個查詢。n, q ≤ 20000。", "q 個數字，以空格隔開，一行。",
  "二分搜尋（lower_bound）", "bisect.bisect_left(a, x)+1；也要會自己寫：lo, hi 夾擠，循環不變量要想清楚。",
  "import bisect\nn,q=map(int,input().split())\na=list(map(int,input().split()))\nprint(*[bisect.bisect_left(a,int(x))+1 for x in input().split()])",
  ["5 4\n1 3 3 5 8\n3 4 9 0\n", "1 2\n5\n5 6\n",
   (lambda r: lines("20000 20000", " ".join(map(str, sorted(r.randint(1,10**6) for _ in range(20000)))),
                    " ".join(str(r.randint(0,10**6+1)) for _ in range(20000))))(rng(47))],
  "線性掃描 O(nq) 會超時；二分是 O(q log n)。", diff=2)

D("d048", "和不超過 K 的配對數", 2, "排序＋雙指標",
  "給 n 個整數與 K，數有幾對 i<j 滿足 a[i]+a[j] ≤ K。",
  "第一行 n K；第二行 n 個整數。n ≤ 40000，|a|,|K| ≤ 10^9。", "一個整數。",
  "排序後雙指標", "排序後，左指標 l、右指標 r：若 a[l]+a[r] ≤ K，則 l 與 (l+1..r) 都成立，加上 r-l 對，l++；否則 r--。",
  "n,k=map(int,input().split())\na=sorted(map(int,input().split()))\nl,r,c=0,n-1,0\nwhile l<r:\n    if a[l]+a[r]<=k: c+=r-l;l+=1\n    else: r-=1\nprint(c)",
  ["5 6\n1 2 3 4 5\n", "2 0\n5 -5\n", "1 10\n3\n", "4 -1\n1 2 3 4\n",
   (lambda r: lines("40000 0", " ".join(str(r.randint(-10**9,10**9)) for _ in range(40000))))(rng(48))],
  "O(n²) 全部配對在 40000 時要 8×10^8 次運算，Python 必超時。", diff=2)

D("d049", "學生排名", 2, "自訂排序",
  "n 位學生，每行 `姓名 分數`。依分數由高到低排序；分數相同依姓名字典序由小到大。輸出 `姓名 分數`。",
  "第一行 n（≤ 10^5），之後 n 行，姓名為不含空白的英文字母。", "n 行。",
  "sort 的 key 與多重排序條件", "sorted(rows, key=lambda r: (-r[1], r[0]))。分數要先轉成 int 再排。",
  "import sys\nd=sys.stdin.read().split()\nn=int(d[0])\nrows=[(d[1+2*i],int(d[2+2*i])) for i in range(n)]\nrows.sort(key=lambda r:(-r[1],r[0]))\nfor a,b in rows: print(a,b)",
  ["3\nbob 90\nalice 90\ncarol 100\n", "1\nz 0\n", "4\nb 5\na 5\nc 5\nd 6\n",
   (lambda r: lines(20000, *[f"{''.join(r.choice('abc') for _ in range(5))} {r.randint(0,100)}" for _ in range(20000)]))(rng(49))],
  "排序的 key 函式；字串比較用的是字典序。")

D("d050", "括號配對", 2, "stack",
  "每行一個只含 `()[]{}` 的字串，判斷括號是否合法配對。輸出 `YES` 或 `NO`。空行視為合法（YES）。",
  "每行長度 ≤ 10^5，讀到 EOF。", "每行 YES 或 NO。",
  "stack（後進先出）", "遇到左括號 push，遇到右括號檢查 stack 頂是否為對應的左括號並 pop；最後 stack 必須為空。",
  "import sys\nP={')':'(',']':'[','}':'{'}\nfor l in sys.stdin:\n    s=l.strip();st=[];ok=True\n    for c in s:\n        if c in '([{': st.append(c)\n        elif not st or st.pop()!=P[c]: ok=False;break\n    print('YES' if ok and not st else 'NO')",
  ["([]{})\n", "(\n)\n\n([)]\n((()))\n{[}\n]\n", "("*50000+")"*50000+"\n"],
  "stack 的第一堂課：遇到右括號時 stack 可能是空的。")

D("d051", "約瑟夫問題", 2, "queue／找規律",
  "n 個人編號 1..n 圍成一圈，從 1 號開始報數，數到 k 的人出列，下一個人重新從 1 報數，直到剩一人。輸出最後留下的人的編號。",
  "每行 `n k`（1 ≤ n ≤ 10^6，1 ≤ k ≤ 10^9），讀到 EOF，最多 10 行。", "每行一個編號。",
  "模擬太慢時找遞迴關係", "小 n 可以用 deque 模擬（rotate）。大 n 時，令 f(i) 為 i 個人時倖存者的 0 起算位置：f(1)=0，f(i)=(f(i-1)+k)%i。答案是 f(n)+1。",
  "import sys\nfor l in sys.stdin:\n    p=l.split()\n    if p:\n        n,k=int(p[0]),int(p[1]);f=0\n        for i in range(2,n+1): f=(f+k)%i\n        print(f+1)",
  ["5 2\n", "1 5\n7 3\n10 1\n6 6\n", "1000000 1000000000\n999999 7\n"],
  "直接模擬是 O(nk)，會超時；找到遞推式後 O(n)。", diff=2)

D("d052", "合併成本", 2, "heap／貪心",
  "有 n 個正整數，每次選兩個數合併成它們的和，成本為這個和。重複到只剩一個數，求最小總成本。",
  "第一行 n（≤ 50000），第二行 n 個正整數（≤ 10^9）。n=1 時成本為 0。", "一個整數。",
  "優先佇列（heapq）＋貪心", "每次取最小的兩個合併，再放回；heapq.heappop/heappush，O(n log n)。",
  "import heapq\nn=int(input());a=list(map(int,input().split()))\nheapq.heapify(a);t=0\nwhile len(a)>1:\n    x=heapq.heappop(a)+heapq.heappop(a);t+=x;heapq.heappush(a,x)\nprint(t)",
  ["4\n1 2 3 4\n", "1\n5\n", "2\n7 8\n", "5\n5 5 5 5 5\n",
   (lambda r: lines(50000, " ".join(str(r.randint(1,10**9)) for _ in range(50000))))(rng(52))],
  "每次都 sort 再取最小的做法是 O(n² log n)。UVA 10954 是同一題。", diff=2)

D("d053", "滑動視窗最大值", 2, "deque 單調佇列",
  "給長度 n 的陣列與視窗大小 k，輸出每個長度為 k 的連續區間的最大值（共 n-k+1 個），以空格隔開。",
  "第一行 n k；第二行 n 個整數。n ≤ 40000。", "一行。",
  "單調 deque", "deque 裡存索引，維持對應的值遞減；新元素進來時從尾端彈掉比它小的；頭端若已滑出視窗也彈掉。",
  "from collections import deque\nn,k=map(int,input().split())\na=list(map(int,input().split()))\nq=deque();o=[]\nfor i,x in enumerate(a):\n    while q and a[q[-1]]<=x: q.pop()\n    q.append(i)\n    if q[0]<=i-k: q.popleft()\n    if i>=k-1: o.append(a[q[0]])\nprint(*o)",
  ["8 3\n1 3 -1 -3 5 3 6 7\n", "1 1\n5\n", "5 5\n1 2 3 2 1\n", "4 1\n4 3 2 1\n",
   (lambda r: lines("40000 20000", " ".join(str(r.randint(-10**9,10**9)) for _ in range(40000))))(rng(53))],
  "O(nk) 暴力在 k 很大時超時。每個元素最多進出 deque 一次 → O(n)。", diff=3)

D("d054", "活動選擇", 2, "貪心",
  "有 n 個活動，每個活動 [s, e) 為開始與結束時間（結束時間那一刻已空出，所以 e 等於下一個的 s 是允許的）。同一時間只能參加一個，最多能參加幾個？",
  "第一行 n（≤ 30000），之後 n 行 `s e`（0 ≤ s < e ≤ 10^9）。", "一個整數。",
  "貪心：依結束時間排序", "依 e 由小到大排序，能接就接（s ≥ 上一個選擇的 e）。證明是『交換論證』。",
  "import sys\nd=sys.stdin.read().split()\nn=int(d[0])\niv=sorted(((int(d[2+2*i]),int(d[1+2*i])) for i in range(n)))\nc=0;t=-1\nfor e,s in iv:\n    if s>=t: c+=1;t=e\nprint(c)",
  ["4\n1 3\n2 4\n3 5\n0 1\n", "1\n0 1\n", "3\n0 10\n1 2\n2 3\n", "3\n1 5\n1 5\n1 5\n",
   (lambda r: lines(30000, *[f"{s} {s+r.randint(1,10**4)}" for s in (r.randint(0,10**8) for _ in range(30000))]))(rng(54))],
  "貪心的關鍵是『選什麼當排序依據』。選錯（例如依開始時間）會得到錯誤答案。", diff=2)

D("d055", "分餅乾", 2, "貪心＋排序",
  "n 個小孩，第 i 個要求餅乾大小至少 g[i]；m 塊餅乾，第 j 塊大小 s[j]。每塊餅乾最多給一個小孩，每個小孩最多拿一塊。最多能滿足幾個小孩？",
  "第一行 n m；第二行 n 個 g；第三行 m 個 s。n, m ≤ 30000。", "一個整數。",
  "貪心配對", "兩邊都排序；對最小需求的小孩，用最小夠用的餅乾；雙指標推進。",
  "n,m=map(int,input().split())\ng=sorted(map(int,input().split()));s=sorted(map(int,input().split()))\ni=0\nfor x in s:\n    if i<n and x>=g[i]: i+=1\nprint(i)",
  ["3 2\n1 2 3\n1 1\n", "2 3\n1 2\n1 2 3\n", "3 3\n5 5 5\n4 4 4\n", "1 1\n7\n7\n",
   (lambda r: lines("30000 30000", " ".join(str(r.randint(1,10**6)) for _ in range(30000)), " ".join(str(r.randint(1,10**6)) for _ in range(30000))))(rng(55))],
  "排序後雙指標，是最常見的貪心組合。")

D("d056", "全排列", 2, "遞迴",
  "輸入 n（1 ≤ n ≤ 7），依字典序輸出 1..n 的所有排列，每個排列一行，數字以空格隔開。",
  "一個整數。", "n! 行。",
  "遞迴枚舉", "用 used[] 陣列標記，依 1..n 順序嘗試，遞迴深度 n；到達 n 時輸出。這樣自然就是字典序。",
  "import itertools\nn=int(input())\nfor p in itertools.permutations(range(1,n+1)): print(*p)",
  ["3\n", "1\n", "2\n", "5\n", "7\n"],
  "請自己寫遞迴，不要用 itertools——這是回溯法的熱身。")

D("d057", "N 皇后方案數", 2, "回溯",
  "在 n×n 棋盤放 n 個皇后，使任兩個皇后不在同一列、同一行、同一斜線。輸入 n（1 ≤ n ≤ 9），輸出方案數。",
  "每行一個 n，讀到 EOF，最多 9 行。", "每行一個整數。",
  "回溯＋剪枝", "逐列放，用三個集合記錄已佔用的行、主對角線（r-c）、副對角線（r+c），放不下就回退。",
  "import sys\ndef solve(n):\n    cols=set();d1=set();d2=set()\n    def go(r):\n        if r==n: return 1\n        t=0\n        for c in range(n):\n            if c in cols or r-c in d1 or r+c in d2: continue\n            cols.add(c);d1.add(r-c);d2.add(r+c)\n            t+=go(r+1)\n            cols.remove(c);d1.remove(r-c);d2.remove(r+c)\n        return t\n    return go(0)\nfor l in sys.stdin:\n    if l.strip(): print(solve(int(l)))",
  ["4\n", "1\n2\n3\n5\n6\n", "8\n9\n7\n"],
  "回溯法的標準範例。想想為什麼要『還原』狀態。", diff=3)

D("d058", "子集合和", 2, "枚舉／位元運算",
  "給 n 個正整數（可重複）與目標 T，數有幾個『索引子集合』的總和恰為 T（空集合的和是 0）。",
  "第一行 n T；第二行 n 個整數。n ≤ 18，每個數 ≤ 1000。", "一個整數。",
  "枚舉所有子集合（bitmask）", "for mask in range(1<<n)：檢查哪些位元是 1 就加上那一項。2^18 = 262144 次，可行。",
  "n,t=map(int,input().split())\na=list(map(int,input().split()))\ndp={0:1}\nfor x in a:\n    nd=dict(dp)\n    for s,c in dp.items(): nd[s+x]=nd.get(s+x,0)+c\n    dp=nd\nprint(dp.get(t,0))",
  ["3 3\n1 2 3\n", "1 5\n5\n", "4 0\n1 2 3 4\n", "5 4\n2 2 2 2 2\n",
   (lambda r: lines("18 5000", " ".join(str(r.randint(1,1000)) for _ in range(18))))(rng(58))],
  "n ≤ 20 就該想到『枚舉所有子集合』。", diff=2)

D("d059", "落單的數", 2, "位元運算",
  "給 n（奇數）個整數，其中恰有一個出現一次，其他都恰好出現兩次。找出落單的那個。",
  "第一行 n（≤ 30001），第二行 n 個整數（絕對值 ≤ 10^9）。", "一個整數。",
  "XOR 的性質", "a^a=0，a^0=a。把全部 XOR 起來，成對的會互相抵消。",
  "n=int(input())\nx=0\nfor v in map(int,input().split()): x^=v\nprint(x)",
  ["5\n1 2 3 2 1\n", "1\n7\n", "3\n-5 3 -5\n",
   (lambda r: (lambda xs: lines(len(xs), " ".join(map(str, xs))))((lambda a: (r.shuffle(a), a)[1])((lambda v: v + v + [777777777])(list(range(-14999, 15000))))))(rng(59))],
  "負數的 XOR 在 Python 也成立。")
