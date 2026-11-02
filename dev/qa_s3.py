"""階段 3（d060–d075、e301–e303）的品質檢查登記。"""
import heapq
import itertools
import math
import random
from collections import deque

from qa import Q, pt, code, ints, sp, L, word, nums, toks, rows, inrange
from qa_s0 import body, mix

M = 10**9 + 7


def edges_of(ls, k):
    return [tuple(nums(x)) for x in ls[:k]]


def rand_graph(r, n, m, wmax=None, loops=False, connected=False):
    es = []
    if connected:
        for v in range(2, n + 1):
            es.append((r.randint(1, v - 1), v) + ((r.randint(1, wmax),) if wmax else ()))
    while len(es) < m:
        u, v = r.randint(1, n), r.randint(1, n)
        if u == v and not loops:
            continue
        es.append((u, v) + ((r.randint(1, wmax),) if wmax else ()))
    r.shuffle(es)
    return es


def gridtxt(g):
    return f"{len(g)} {len(g[0])}\n" + "\n".join(g) + "\n"


# ---------- d060 迷宮 ----------
def maze_gen(r, R, C, p):
    g = [["#" if r.random() < p else "." for _ in range(C)] for _ in range(R)]
    cells = [(i, j) for i in range(R) for j in range(C)]
    a, b = r.sample(cells, 2) if len(cells) > 1 else (cells[0], cells[0])
    g[a[0]][a[1]] = "S"
    g[b[0]][b[1]] = "E"
    return ["".join(row) for row in g]
def g060(r):
    R, C = r.randint(1, 5), r.randint(2, 5)
    return gridtxt(maze_gen(r, R, C, 0.3))
def b060(t):
    ls = body(t)
    R, C = nums(ls[0])
    g = ls[1:1 + R]
    pos = {(i, j) for i in range(R) for j in range(C) if g[i][j] == "S"}
    E = [(i, j) for i in range(R) for j in range(C) if g[i][j] == "E"][0]
    seen = set(pos)
    step = 0
    while pos:
        if E in pos:
            return f"{step}\n"
        nxt = set()
        for (x, y) in pos:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = x + dx, y + dy
                if 0 <= a < R and 0 <= b < C and g[a][b] != "#" and (a, b) not in seen:
                    seen.add((a, b))
                    nxt.add((a, b))
        pos = nxt
        step += 1
    return "-1\n"
def v060(t):
    ls = body(t)
    R, C = nums(ls[0])
    g = ls[1:]
    return 1 <= R <= 200 and 1 <= C <= 200 and len(g) == R and all(len(x) == C and set(x) <= set("#.SE") for x in g) and "".join(g).count("S") == 1 and "".join(g).count("E") == 1
def big060_open(r):
    g = [["."] * 200 for _ in range(200)]
    g[0][0] = "S"; g[199][199] = "E"
    return gridtxt(["".join(x) for x in g])
def big060_snake(r):
    g = [["."] * 199 for _ in range(199)]
    for i in range(1, 199, 2):
        for j in range(199):
            g[i][j] = "#"
        g[i][198 if (i // 2) % 2 == 0 else 0] = "."
    g[0][0] = "S"; g[198][198] = "E"
    return gridtxt(["".join(x) for x in g])
def big060_rand(r):
    return gridtxt(maze_gen(r, 200, 200, 0.28))
Q("d060", b060, g060, v060,
  wrong=[pt("for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):", "for dx,dy in((1,0),(0,1)):"), pt("d[s[0]][s[1]]=0", "d[s[0]][s[1]]=1"), pt("print(d[e[0]][e[1]])", "print(max(map(max,d)))")],
  slow=[code("import sys\nsys.setrecursionlimit(10**6)\nR,C=map(int,input().split())\ng=[input() for _ in range(R)]\nfor i in range(R):\n    for j in range(C):\n        if g[i][j]=='S': s=(i,j)\n        if g[i][j]=='E': e=(i,j)\nbest=[10**9]\nvis=[[0]*C for _ in range(R)]\ndef go(x,y,d):\n    if d>=best[0]: return\n    if (x,y)==e: best[0]=d;return\n    vis[x][y]=1\n    for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):\n        a,b=x+dx,y+dy\n        if 0<=a<R and 0<=b<C and g[a][b]!='#' and not vis[a][b]: go(a,b,d+1)\n    vis[x][y]=0\ngo(s[0],s[1],0)\nprint(best[0] if best[0]<10**9 else -1)\n", "DFS 窮舉所有路徑")],
  big=[big060_open, big060_snake, big060_rand], nrand=6)

# ---------- d061 並查集 ----------
def g061(r):
    n, m = r.randint(1, 8), r.randint(0, 8)
    return f"{n} {m}\n" + "".join(f"{r.randint(1, n)} {r.randint(1, n)}\n" for _ in range(m))
def b061(t):
    ls = body(t)
    n, m = nums(ls[0])
    comp = list(range(n + 1))
    for l in ls[1:1 + m]:
        a, b = nums(l)
        ca, cb = comp[a], comp[b]
        if ca != cb:
            comp = [ca if c == cb else c for c in comp]
    from collections import Counter
    c = Counter(comp[1:])
    return f"{len(c)} {max(c.values())}\n"
def v061(t):
    ls = body(t)
    n, m = nums(ls[0])
    return 1 <= n <= 50000 and 0 <= m <= 50000 and len(ls) == 1 + m and all(1 <= x <= n for l in ls[1:] for x in nums(l)) and all(len(l.split()) == 2 for l in ls[1:])
Q("d061", b061, g061, v061,
  wrong=[pt("p[b]=a;sz[a]+=sz[b];c-=1", "p[b]=a;sz[a]+=sz[b]"), pt("if sz[a]<sz[b]: a,b=b,a\n        p[b]=a;sz[a]+=sz[b]", "p[b]=a;sz[a]=sz[a]+1"), pt("c=n", "c=n+1")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\ncomp=list(range(n+1))\nfor i in range(m):\n    a,b=int(d[2+2*i]),int(d[3+2*i])\n    ca,cb=comp[a],comp[b]\n    if ca!=cb:\n        for k in range(n+1):\n            if comp[k]==cb: comp[k]=ca\nfrom collections import Counter\nc=Counter(comp[1:])\nprint(len(c),max(c.values()))\n", "合併時整個陣列重貼標籤 O(nm)")],
  big=[lambda r: "30000 30000\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 30000)) + "1 1\n", lambda r: "30000 30000\n" + "".join(f"{r.randint(1, 30000)} {r.randint(1, 30000)}\n" for _ in range(30000))])

# ---------- d062 拓撲排序 ----------
def g062(r):
    n = r.randint(1, 6)
    m = r.randint(0, 8)
    es = []
    perm = list(range(1, n + 1)); r.shuffle(perm)
    for _ in range(m):
        a, b = r.sample(range(n), 2) if n > 1 else (0, 0)
        if n == 1:
            break
        if a > b and r.random() < 0.85:
            a, b = b, a
        es.append((perm[a], perm[b]))
    return f"{n} {len(es)}\n" + "".join(f"{u} {v}\n" for u, v in es)
def b062(t):
    ls = body(t)
    n, m = nums(ls[0])
    es = [tuple(nums(x)) for x in ls[1:1 + m]]
    placed = []
    left = set(range(1, n + 1))
    while left:
        cand = [v for v in sorted(left) if all(u in placed for (u, w) in es if w == v)]
        if not cand:
            return "-1\n"
        placed.append(cand[0])
        left.remove(cand[0])
    return sp(placed) + "\n"
def v062(t):
    ls = body(t)
    n, m = nums(ls[0])
    return 1 <= n <= 20000 and 0 <= m <= 40000 and len(ls) == 1 + m and all(1 <= x <= n for l in ls[1:] for x in nums(l)) and all(nums(l)[0] != nums(l)[1] for l in ls[1:])
def big062(r, cyc=False):
    n, m = 20000, 40000
    perm = list(range(1, n + 1)); r.shuffle(perm)
    es = set()
    while len(es) < m:
        a, b = sorted(r.sample(range(n), 2))
        es.add((perm[a], perm[b]))
    es = list(es)
    r.shuffle(es)
    if cyc:
        es[-1] = (es[-1][1], es[-1][0])
        es.append((perm[-1], perm[0]))
        es.pop(0)
    return f"{n} {len(es)}\n" + "".join(f"{u} {v}\n" for u, v in es)
Q("d062", b062, g062, v062,
  wrong=[pt("h=[i for i in range(1,n+1) if ind[i]==0];heapq.heapify(h)", "h=[i for i in range(1,n+1) if ind[i]==0][::-1]"), pt("print(*(o if len(o)==n else [-1]))", "print(*o)"), code("from collections import deque\nimport sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\nadj=[[] for _ in range(n+1)];ind=[0]*(n+1)\nfor i in range(m):\n    u,v=int(d[2+2*i]),int(d[3+2*i]);adj[u].append(v);ind[v]+=1\nq=deque(i for i in range(1,n+1) if ind[i]==0);o=[]\nwhile q:\n    u=q.popleft();o.append(u)\n    for v in adj[u]:\n        ind[v]-=1\n        if ind[v]==0: q.append(v)\nprint(*(o if len(o)==n else [-1]))\n")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\nadj=[[] for _ in range(n+1)];ind=[0]*(n+1)\nfor i in range(m):\n    u,v=int(d[2+2*i]),int(d[3+2*i]);adj[u].append(v);ind[v]+=1\ndone=[0]*(n+1);o=[]\nfor _ in range(n):\n    for i in range(1,n+1):\n        if not done[i] and ind[i]==0:\n            done[i]=1;o.append(i)\n            for v in adj[i]: ind[v]-=1\n            break\n    else: break\nprint(*(o if len(o)==n else [-1]))\n", "每次線性掃描找最小 O(n²)")],
  big=[big062, lambda r: big062(r, True)])

# ---------- d063 / d064 / d065 ----------
def g063(r):
    n = r.randint(2, 7)
    m = r.randint(0, 10)
    return f"{n} {m}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in rand_graph(r, n, m, 9))
def b063(t):
    ls = body(t)
    n, m = nums(ls[0])
    es = [tuple(nums(x)) for x in ls[1:1 + m]]
    INF = 10**18
    d = [INF] * (n + 1)
    d[1] = 0
    for _ in range(n):
        for u, v, w in es:
            if d[u] + w < d[v]:
                d[v] = d[u] + w
            if d[v] + w < d[u]:
                d[u] = d[v] + w
    return f"{d[n] if d[n] < INF else -1}\n"
def v063(t):
    ls = body(t)
    n, m = nums(ls[0])
    return 1 <= n <= 5000 and 0 <= m <= 20000 and len(ls) == 1 + m and all(1 <= nums(l)[0] <= n and 1 <= nums(l)[1] <= n and 1 <= nums(l)[2] <= 1000 for l in ls[1:])
def big063(r, n=5000, m=20000, conn=True):
    es = rand_graph(r, n, m, 1000, loops=False, connected=conn)
    return f"{n} {len(es)}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in es)
def big063_path(r):
    n = 5000
    es = [(i, i + 1, r.randint(1, 1000)) for i in range(1, n)] + [(1, n, 1000)] * 3
    return f"{n} {len(es)}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in es)
Q("d063", b063, g063, v063,
  wrong=[pt("if du>dist[u]: continue", "if du>dist[u]: break"), pt("adj[u].append((v,w));adj[v].append((u,w))", "adj[u].append((v,w))"), pt("print(dist[n] if dist[n]<INF else -1)", "print(dist[n])"), pt("h=[(0,1)]", "h=[(0,2)]")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\nes=[(int(d[2+3*i]),int(d[3+3*i]),int(d[4+3*i])) for i in range(m)]\nINF=10**18;dist=[INF]*(n+1);dist[1]=0\nfor _ in range(n):\n    for u,v,w in es:\n        if dist[u]+w<dist[v]: dist[v]=dist[u]+w\n        if dist[v]+w<dist[u]: dist[u]=dist[v]+w\nprint(dist[n] if dist[n]<INF else -1)\n", "Bellman-Ford 不提早結束 O(nm)")],
  big=[big063, big063_path, lambda r: big063(r, 5000, 20000, False)])

def g064(r):
    n = r.randint(1, 6)
    m = r.randint(0, 10) if n > 1 else 0
    return f"{n} {m}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in rand_graph(r, n, m, 9)) if n > 1 else f"{n} 0\n"
def b064(t):
    ls = body(t)
    n, m = nums(ls[0])
    es = [tuple(nums(x)) for x in ls[1:1 + m]]
    INF = 10**18
    adj = [[INF] * (n + 1) for _ in range(n + 1)]
    for u, v, w in es:
        adj[u][v] = adj[v][u] = min(adj[u][v], w)
    inT = [False] * (n + 1)
    best = [INF] * (n + 1)
    best[1] = 0
    tot = 0
    for _ in range(n):
        u = min((v for v in range(1, n + 1) if not inT[v]), key=lambda v: best[v])
        if best[u] >= INF:
            return "-1\n"
        inT[u] = True
        tot += best[u]
        for v in range(1, n + 1):
            if not inT[v] and adj[u][v] < best[v]:
                best[v] = adj[u][v]
    return f"{tot}\n"
def v064(t):
    ls = body(t)
    n, m = nums(ls[0])
    return 1 <= n <= 5000 and 0 <= m <= 20000 and len(ls) == 1 + m and all(1 <= nums(l)[0] <= n and 1 <= nums(l)[1] <= n for l in ls[1:]) and all(len(l.split()) == 3 and 1 <= nums(l)[2] <= 10**6 for l in ls[1:])
def big064(r, conn=True, wmax=10**6):
    n, m = 5000, 20000
    es = rand_graph(r, n, m, wmax, connected=conn)
    return f"{n} {len(es)}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in es)
Q("d064", b064, g064, v064,
  wrong=[pt("print(t if c==n-1 else -1)", "print(t)"), pt("E=sorted((int(d[4+3*i]),int(d[2+3*i]),int(d[3+3*i])) for i in range(m))", "E=sorted((int(d[4+3*i]),int(d[2+3*i]),int(d[3+3*i])) for i in range(m))[::-1]"), pt("t=c=0", "t=0;c=1")],
  big=[big064, lambda r: big064(r, False), lambda r: big064(r, True, 3)])

def g065(r):
    n = r.randint(1, 6)
    m = r.randint(0, 8) if n > 1 else 0
    q = r.randint(1, 5)
    es = rand_graph(r, n, m, 9) if n > 1 else []
    return f"{n} {len(es)} {q}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in es) + "".join(f"{r.randint(1, n)} {r.randint(1, n)}\n" for _ in range(q))
def b065(t):
    ls = body(t)
    n, m, q = nums(ls[0])
    es = [tuple(nums(x)) for x in ls[1:1 + m]]
    out = ""
    for l in ls[1 + m:1 + m + q]:
        a, b = nums(l)
        INF = 10**18
        d = [INF] * (n + 1)
        d[a] = 0
        for _ in range(n):
            for u, v, w in es:
                d[v] = min(d[v], d[u] + w)
                d[u] = min(d[u], d[v] + w)
        out += f"{d[b] if d[b] < INF else -1}\n"
    return out
def v065(t):
    ls = body(t)
    n, m, q = nums(ls[0])
    return 1 <= n <= 100 and 0 <= m <= 5000 and 1 <= q <= 10000 and len(ls) == 1 + m + q and all(len(l.split()) == 3 and 1 <= nums(l)[0] <= n and 1 <= nums(l)[1] <= n and 1 <= nums(l)[2] <= 1000 for l in ls[1:1 + m]) and all(len(l.split()) == 2 and 1 <= nums(l)[0] <= n and 1 <= nums(l)[1] <= n for l in ls[1 + m:])
def big065(r):
    n, m, q = 100, 4000, 10000
    es = rand_graph(r, n, m, 1000)
    return f"{n} {m} {q}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in es) + "".join(f"{r.randint(1, n)} {r.randint(1, n)}\n" for _ in range(q))
Q("d065", b065, g065, v065,
  wrong=[pt("for k in range(1,n+1):\n    for a in range(1,n+1):\n        for b in range(1,n+1):", "for a in range(1,n+1):\n    for b in range(1,n+1):\n        for k in range(1,n+1):"), pt("if w<D[u][v]: D[u][v]=D[v][u]=w", "D[u][v]=D[v][u]=w"), pt("print(D[a][b] if D[a][b]<I else -1)", "print(D[a][b])")],
  big=[big065])

# ---------- d066 / d067 / d068 ----------
def g066(r):
    n = r.randint(1, 4)
    cs = r.sample(range(1, 9), n)
    return f"{n} {r.randint(0, 14)}\n{sp(cs)}\n"
def b066(t):
    ls = body(t)
    n, A = nums(ls[0])
    cs = sorted(nums(ls[1]))
    def go(i, rem):
        if rem == 0:
            return 1
        if i == len(cs):
            return 0
        t = 0
        k = 0
        while k * cs[i] <= rem:
            t += go(i + 1, rem - k * cs[i])
            k += 1
        return t
    return f"{go(0, A) % M}\n"
def v066(t):
    ls = body(t)
    n, A = nums(ls[0])
    cs = nums(ls[1])
    return len(ls) == 2 and 1 <= n <= 50 and 0 <= A <= 10**4 and len(cs) == n and len(set(cs)) == n and inrange(cs, 1, 10**4)
Q("d066", b066, g066, v066,
  wrong=[pt("for c in cs:\n    for a in range(c,A+1)", "for a in range(A+1):\n  for c in cs:\n   if c<=a: dp[a]=(dp[a]+dp[a-c])%M\nfor c in []:\n    for a in range(c,A+1)"), pt("dp[0]=1", "dp[0]=0"), pt("%M", "%998244353")],
  big=[lambda r: "50 10000\n" + sp(r.sample(range(1, 200), 50)) + "\n", lambda r: "50 10000\n" + sp(range(1, 51)) + "\n", lambda r: "3 10000\n1 2 3\n", lambda r: "1 10000\n10000\n"], nrand=6)

def g067(r):
    n = r.randint(1, 4)
    cs = r.sample(range(1, 9), n)
    return f"{n} {r.randint(1, 20)}\n{sp(cs)}\n"
def b067(t):
    ls = body(t)
    n, A = nums(ls[0])
    cs = nums(ls[1])
    dist = {0: 0}
    q = deque([0])
    while q:
        x = q.popleft()
        for c in cs:
            y = x + c
            if y <= A and y not in dist:
                dist[y] = dist[x] + 1
                q.append(y)
    return f"{dist.get(A, -1)}\n"
def v067(t):
    ls = body(t)
    n, A = nums(ls[0])
    cs = nums(ls[1])
    return len(ls) == 2 and 1 <= n <= 100 and 0 <= A <= 10**4 and len(cs) == n and len(set(cs)) == n and inrange(cs, 1, 10**4)
Q("d067", b067, g067, v067,
  wrong=[code("n,A=map(int,input().split());cs=sorted(map(int,input().split()),reverse=True)\nc=0\nfor x in cs:\n    c+=A//x;A%=x\nprint(c if A==0 else -1)\n"), pt("print(dp[A] if dp[A]<I else -1)", "print(dp[A])"), pt("dp[0]=0", "dp[0]=1")],
  big=[lambda r: "100 10000\n" + sp(r.sample(range(2, 400), 100)) + "\n", lambda r: "3 9999\n7 13 100\n", lambda r: "2 10000\n4 6\n", lambda r: "4 10000\n1 3 4 7\n"], nrand=6)

def g068(r):
    n = r.randint(1, 6)
    return f"{n} {r.randint(1, 15)}\n" + "".join(f"{r.randint(1, 8)} {r.randint(1, 20)}\n" for _ in range(n))
def b068(t):
    ls = body(t)
    n, W = nums(ls[0])
    it = [tuple(nums(x)) for x in ls[1:1 + n]]
    best = 0
    for m in range(1 << n):
        w = sum(it[i][0] for i in range(n) if m >> i & 1)
        if w <= W:
            best = max(best, sum(it[i][1] for i in range(n) if m >> i & 1))
    return f"{best}\n"
def v068(t):
    ls = body(t)
    n, W = nums(ls[0])
    return len(ls) == 1 + n and 1 <= n <= 100 and 0 <= W <= 10**4 and all(len(l.split()) == 2 and 1 <= nums(l)[0] <= 10**4 and 1 <= nums(l)[1] <= 10**9 for l in ls[1:])
Q("d068", b068, g068, v068,
  wrong=[pt("for j in range(W,w-1,-1):", "for j in range(w,W+1):"), pt("print(dp[W])", "print(max(dp[:-1]))"), pt("range(W,w-1,-1)", "range(W,w,-1)")],
  big=[lambda r: "100 10000\n" + "".join(f"{r.randint(1, 500)} {r.randint(1, 10**9)}\n" for _ in range(100)), lambda r: "100 10000\n" + "".join(f"{r.randint(90, 110)} {r.randint(1, 1000)}\n" for _ in range(100))])

# ---------- d069 LIS / d070 LCS / d071 Kadane / d072 grid ----------
def g069(r):
    n = r.randint(1, 8)
    return f"{n}\n{sp(ints(r, n, -5, 5))}\n"
def b069(t):
    a = nums(body(t)[1])
    dp = [1] * len(a)
    for i in range(len(a)):
        for j in range(i):
            if a[j] < a[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return f"{max(dp)}\n"
Q("d069", b069, g069,
  lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 50000 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), -10**9, 10**9),
  wrong=[pt("bisect.bisect_left(t,x)", "bisect.bisect_right(t,x)"), pt("if i==len(t): t.append(x)\n    else: t[i]=x", "if i==len(t): t.append(x)")],
  slow=[code("n=int(input());a=list(map(int,input().split()))\ndp=[1]*n\nfor i in range(n):\n    for j in range(i):\n        if a[j]<a[i] and dp[j]+1>dp[i]: dp[i]=dp[j]+1\nprint(max(dp))\n", "O(n²) 的 dp")],
  big=[lambda r: "40000\n" + sp(ints(r, 40000, -10**9, 10**9)) + "\n", lambda r: "30000\n" + sp(range(30000)) + "\n", lambda r: "30000\n" + sp([7] * 30000) + "\n"])

def g070(r):
    return word(r, 1, 7, "abc") + "\n" + word(r, 1, 7, "abc") + "\n"
def b070(t):
    a, b = body(t)
    T = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) - 1, -1, -1):
        for j in range(len(b) - 1, -1, -1):
            T[i][j] = 1 + T[i + 1][j + 1] if a[i] == b[j] else max(T[i + 1][j], T[i][j + 1])
    return f"{T[0][0]}\n"
Q("d070", b070, g070,
  lambda t: len(body(t)) == 2 and all(1 <= len(x) <= 1000 and x.islower() and x.isalpha() for x in body(t)),
  wrong=[pt("cur[j]=prev[j-1]+1 if x==b[j-1] else max(prev[j],cur[j-1])", "cur[j]=prev[j-1]+1 if x==b[j-1] else prev[j]"), pt("prev[j-1]+1 if", "prev[j-1]+2 if")],
  slow=[code("import sys\nsys.setrecursionlimit(10000)\na=input();b=input()\ndef f(i,j):\n    if i==len(a) or j==len(b): return 0\n    if a[i]==b[j]: return 1+f(i+1,j+1)\n    return max(f(i+1,j),f(i,j+1))\nprint(f(0,0))\n", "遞迴不記憶")],
  big=[lambda r: "".join(r.choice("abc") for _ in range(1000)) + "\n" + "".join(r.choice("abc") for _ in range(1000)) + "\n", lambda r: "a" * 1000 + "\n" + "a" * 1000 + "\n", lambda r: "".join(r.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(1000)) + "\n" + "".join(r.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(1000)) + "\n"])

def g071(r):
    n = r.randint(1, 8)
    return f"{n}\n{sp(ints(r, n, -9, 9))}\n"
def b071(t):
    a = nums(body(t)[1])
    return f"{max(sum(a[i:j]) for i in range(len(a)) for j in range(i + 1, len(a) + 1))}\n"
Q("d071", b071, g071,
  lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 50000 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), -10**9, 10**9),
  wrong=[pt("cur=best=a[0]", "cur=best=0"), pt("cur=max(x,cur+x)", "cur=max(0,cur+x)"), pt("best=max(best,cur)", "best=cur")],
  slow=[code("n=int(input());a=list(map(int,input().split()))\nbest=a[0]\nfor i in range(n):\n    s=0\n    for j in range(i,n):\n        s+=a[j]\n        if s>best: best=s\nprint(best)\n", "O(n²)")],
  big=[lambda r: "50000\n" + sp(ints(r, 50000, -10**9, 10**9)) + "\n", lambda r: "20000\n" + sp(ints(r, 20000, -10**9, -1)) + "\n"])

def g072(r):
    R, C = r.randint(1, 4), r.randint(1, 4)
    return f"{R} {C}\n" + "".join(sp(ints(r, C, 0, 9)) + "\n" for _ in range(R))
def b072(t):
    ls = body(t)
    R, C = nums(ls[0])
    a = [nums(x) for x in ls[1:1 + R]]
    from functools import lru_cache
    @lru_cache(None)
    def f(i, j):
        if i == R - 1 and j == C - 1:
            return a[i][j]
        o = []
        if i + 1 < R:
            o.append(f(i + 1, j))
        if j + 1 < C:
            o.append(f(i, j + 1))
        return a[i][j] + min(o)
    return f"{f(0, 0)}\n"
Q("d072", b072, g072,
  lambda t: len(body(t)) == 1 + nums(body(t)[0])[0] and 1 <= nums(body(t)[0])[0] <= 300 and 1 <= nums(body(t)[0])[1] <= 300 and all(len(nums(x)) == nums(body(t)[0])[1] and inrange(nums(x), 0, 1000) for x in body(t)[1:]),
  wrong=[pt("a[i][j]+=min(a[i-1][j] if i else 10**18, a[i][j-1] if j else 10**18)", "a[i][j]+=min(a[i-1][j] if i else 0, a[i][j-1] if j else 0)"), pt("print(a[R-1][C-1])", "print(a[R-1][C-1] if R>1 else 0)")],
  big=[lambda r: "300 300\n" + "".join(sp(ints(r, 300, 0, 1000)) + "\n" for _ in range(300)), lambda r: "1 300\n" + sp(ints(r, 300, 0, 1000)) + "\n", lambda r: "300 1\n" + "".join(f"{r.randint(0, 1000)}\n" for _ in range(300))])

# ---------- d073 / d074 / d075 ----------
def g073(r):
    n = r.randint(1, 5)
    return f"{n}\n{sp(ints(r, n + 1, 1, 9))}\n"
def b073(t):
    ls = body(t)
    n = int(ls[0])
    p = nums(ls[1])
    def go(i, j):
        if i == j:
            return 0
        return min(go(i, k) + go(k + 1, j) + p[i - 1] * p[k] * p[j] for k in range(i, j))
    return f"{go(1, n)}\n"
Q("d073", b073, g073,
  lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 100 and len(nums(body(t)[1])) == int(body(t)[0]) + 1 and inrange(nums(body(t)[1]), 1, 100),
  wrong=[pt("p[i-1]*p[k]*p[j]", "p[i]*p[k]*p[j]"), pt("for L in range(2,n+1)", "for L in range(2,n)"), pt("dp[i][k]+dp[k+1][j]+p[i-1]*p[k]*p[j]", "dp[i][k]+dp[k+1][j]+p[i-1]*p[k+1]*p[j]")],
  big=[lambda r: "100\n" + sp(ints(r, 101, 1, 100)) + "\n", lambda r: "100\n" + sp([100] * 101) + "\n"])

def g074(r):
    n = r.randint(1, 6)
    return f"{n}\n" + "".join(sp([0 if i == j else r.randint(0, 20) for j in range(n)]) + "\n" for i in range(n))
def b074(t):
    ls = body(t)
    n = int(ls[0])
    d = [nums(x) for x in ls[1:1 + n]]
    if n == 1:
        return "0\n"
    best = min(sum(d[a][b] for a, b in zip((0,) + p, p + (0,))) for p in itertools.permutations(range(1, n)))
    return f"{best}\n"
Q("d074", b074, g074,
  lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 12 and all(len(nums(x)) == int(body(t)[0]) and inrange(nums(x), 0, 1000) for x in body(t)[1:]) and all(nums(body(t)[1 + i])[i] == 0 for i in range(int(body(t)[0]))),
  wrong=[pt("print(min(dp[(1<<n)-1][i]+d[i][0] for i in range(n)))", "print(min(dp[(1<<n)-1][i] for i in range(n)))"), pt("dp[1][0]=0", "dp[1][0]=1"), pt("v=dp[m][i]+d[i][j]", "v=dp[m][i]+d[j][i]")],
  big=[lambda r: "12\n" + "".join(sp([0 if i == j else r.randint(1, 1000) for j in range(12)]) + "\n" for i in range(12)), lambda r: "11\n" + "".join(sp([0 if i == j else r.randint(0, 1000) for j in range(11)]) + "\n" for i in range(11))])

def g075(r):
    q = r.randint(1, 5)
    return f"{q}\n" + "".join(f"{r.randint(0, 30)} {r.randint(0, 33)}\n" for _ in range(q))
Q("d075", lambda t: "".join(f"{(math.comb(nums(l)[0], nums(l)[1]) if nums(l)[1] <= nums(l)[0] else 0) % M}\n" for l in body(t)[1:]), g075,
  lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 20000 and all(len(l.split()) == 2 and 0 <= nums(l)[0] <= 10**6 and 0 <= nums(l)[1] <= 10**6 for l in body(t)[1:]),
  wrong=[pt("print(0 if r>n or r<0 else f[n]*inv[r]%M*inv[n-r]%M)", "print(f[n]*inv[r]%M*inv[n-r]%M if r<=n else 1)"), pt("M=10**9+7", "M=10**9+9"), pt("inv[N]=pow(f[N],M-2,M)", "inv[N]=pow(f[N],M-3,M)")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nq=int(d[0]);M=10**9+7\nfor i in range(q):\n    n,r=int(d[1+2*i]),int(d[2+2*i])\n    if r>n: print(0);continue\n    r=min(r,n-r)\n    a=1\n    for k in range(r): a=a*(n-k)%M*pow(k+1,M-2,M)%M\n    print(a)\n", "每個查詢重算")],
  big=[lambda r: "20000\n" + "".join(f"{r.randint(0, 10**6)} {r.randint(0, 10**6)}\n" for _ in range(20000)), lambda r: "20000\n" + "".join(f"{(n := r.randint(500000, 10**6))} {n // 2}\n" for _ in range(20000))])

# ---------- e301 / e302 / e303 ----------
def g_e301(r):
    R, C = r.randint(1, 5), r.randint(1, 5)
    g = [["X" if r.random() < 0.15 else "#" if r.random() < 0.25 else "." for _ in range(C)] for _ in range(R)]
    if not any("X" in row for row in g):
        g[r.randrange(R)][r.randrange(C)] = "X"
    return gridtxt(["".join(x) for x in g])
def b_e301(t):
    ls = body(t)
    R, C = nums(ls[0])
    g = ls[1:1 + R]
    s = u = 0
    for i in range(R):
        for j in range(C):
            if g[i][j] != ".":
                continue
            dist = {(i, j): 0}
            q = deque([(i, j)])
            found = None
            while q:
                x, y = q.popleft()
                if g[x][y] == "X":
                    found = dist[(x, y)]
                    break
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = x + dx, y + dy
                    if 0 <= a < R and 0 <= b < C and g[a][b] != "#" and (a, b) not in dist:
                        dist[(a, b)] = dist[(x, y)] + 1
                        q.append((a, b))
            if found is None:
                u += 1
            else:
                s += found
    return f"{s} {u}\n"
def v_e301(t):
    ls = body(t)
    R, C = nums(ls[0])
    return 1 <= R <= 300 and 1 <= C <= 300 and len(ls) == R + 1 and all(len(x) == C and set(x) <= set("#.X") for x in ls[1:]) and "X" in "".join(ls[1:])
def big_e301(r, p=0.2, ex=3):
    g = [["#" if r.random() < p else "." for _ in range(300)] for _ in range(300)]
    for _ in range(ex):
        g[r.randrange(300)][r.randrange(300)] = "X"
    return gridtxt(["".join(x) for x in g])
Q("e301", b_e301, g_e301, v_e301,
  wrong=[pt("if g[i][j]=='X': d[i][j]=0;q.append((i,j))", "if g[i][j]=='X' and not q: d[i][j]=0;q.append((i,j))"), pt("print(s,u)", "print(s+u,u)"), pt("g[a][b]!='#' and d[a][b]<0", "d[a][b]<0")],
  slow=[code("from collections import deque\nR,C=map(int,input().split());g=[input() for _ in range(R)]\ns=u=0\nfor i in range(R):\n    for j in range(C):\n        if g[i][j]!='.': continue\n        dist={(i,j):0};q=deque([(i,j)]);f=None\n        while q:\n            x,y=q.popleft()\n            if g[x][y]=='X': f=dist[(x,y)];break\n            for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):\n                a,b=x+dx,y+dy\n                if 0<=a<R and 0<=b<C and g[a][b]!='#' and (a,b) not in dist: dist[(a,b)]=dist[(x,y)]+1;q.append((a,b))\n        if f is None: u+=1\n        else: s+=f\nprint(s,u)\n", "每個空地各跑一次 BFS")],
  big=[big_e301, lambda r: big_e301(r, 0.35, 2), lambda r: big_e301(r, 0.0, 1)])

def g_e302(r):
    n = r.randint(1, 7)
    perm = list(range(1, n + 1)); r.shuffle(perm)
    es = set()
    for _ in range(r.randint(0, 9)):
        if n < 2:
            break
        a, b = sorted(r.sample(range(n), 2))
        es.add((perm[a], perm[b]))
    es = list(es)
    r.shuffle(es)
    return f"{n} {len(es)}\n" + "".join(f"{u} {v}\n" for u, v in es)
def b_e302(t):
    ls = body(t)
    n, m = nums(ls[0])
    adj = {i: [] for i in range(1, n + 1)}
    for l in ls[1:1 + m]:
        u, v = nums(l)
        adj[u].append(v)
    from functools import lru_cache
    @lru_cache(None)
    def f(u):
        return max([1 + f(v) for v in adj[u]] + [0])
    return f"{max(f(u) for u in adj)}\n"
def v_e302(t):
    ls = body(t)
    n, m = nums(ls[0])
    if not (1 <= n <= 50000 and 0 <= m <= 100000 and len(ls) == 1 + m):
        return False
    adj = {i: [] for i in range(1, n + 1)}
    ind = {i: 0 for i in adj}
    for l in ls[1:]:
        u, v = nums(l)
        if not (1 <= u <= n and 1 <= v <= n and u != v):
            return False
        adj[u].append(v); ind[v] += 1
    q = [i for i in adj if ind[i] == 0]
    seen = 0
    while q:
        u = q.pop(); seen += 1
        for v in adj[u]:
            ind[v] -= 1
            if ind[v] == 0:
                q.append(v)
    return seen == n
def big_e302(r, chain=False):
    n, m = 30000, 60000
    perm = list(range(1, n + 1)); r.shuffle(perm)
    es = set()
    if chain:
        es = {(perm[i], perm[i + 1]) for i in range(n - 1)}
    while len(es) < m:
        a, b = sorted(r.sample(range(n), 2))
        es.add((perm[a], perm[b]))
    es = list(es); r.shuffle(es)
    return f"{n} {m}\n" + "".join(f"{u} {v}\n" for u, v in es)
Q("e302", b_e302, g_e302, v_e302,
  wrong=[pt("dp[v]=max(dp[v],dp[u]+1)", "dp[v]=max(dp[v],1)"), pt("print(max(dp))", "print(dp[n])"), pt("q=deque(i for i in range(1,n+1) if ind[i]==0)", "q=deque([1])")],
  big=[big_e302])

def g_e303(r):
    n = r.randint(1, 7)
    return f"{n}\n{sp(ints(r, n, 1, 12))}\n"
def b_e303(t):
    a = nums(body(t)[1])
    S = sum(a)
    return f"{min(abs(S - 2 * sum(a[i] for i in range(len(a)) if m >> i & 1)) for m in range(1 << len(a)))}\n"
Q("e303", b_e303, g_e303,
  lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 100 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), 1, 100),
  wrong=[pt("best=max(x for x in range(S//2+1) if b>>x&1)", "best=S//2"), pt("print(S-2*best)", "print(S-best)"), pt("b=1", "b=0")],
  big=[lambda r: "100\n" + sp(ints(r, 100, 1, 100)) + "\n", lambda r: "100\n" + sp([100] * 99 + [99]) + "\n"])
