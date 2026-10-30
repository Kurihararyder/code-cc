"""參考解的交叉驗證（暴力解 vs 參考解）。"""
import itertools, random, subprocess, sys, heapq
sys.path.insert(0, '.')
import drills_s0, drills_s1, drills_s2, drills_s3, drills_s4
try:
    import drills_s3, drills_s4
except Exception:
    pass
from common import DRILLS
REF = {d['id']: d['ref'] for d in DRILLS}

def run(id, text):
    return subprocess.run([sys.executable, '-c', REF[id]], input=text.encode(), capture_output=True, timeout=20).stdout.decode().split()

R = random.Random(1)
def check(id, gen, brute, n=150):
    for _ in range(n):
        t = gen()
        got, want = run(id, t), [str(x) for x in brute(t)]
        assert got == want, (id, t, got, want)
    print('ok', id)

def L(t): return t.split('\n')

# d048
def g():
    n = R.randint(1, 8); k = R.randint(-10, 10)
    return f"{n} {k}\n{' '.join(str(R.randint(-6,6)) for _ in range(n))}\n"
def b(t):
    l = L(t); n, k = map(int, l[0].split()); a = list(map(int, l[1].split()))
    return [sum(1 for i in range(n) for j in range(i+1, n) if a[i]+a[j] <= k)]
check('d048', g, b)
# d052
def g():
    n = R.randint(1, 7); return f"{n}\n{' '.join(str(R.randint(1,9)) for _ in range(n))}\n"
def b(t):
    a = list(map(int, L(t)[1].split())); tot = 0
    while len(a) > 1:
        a.sort(); x = a[0]+a[1]; tot += x; a = a[2:]+[x]
    return [tot]
check('d052', g, b)
# d053
def g():
    n = R.randint(1, 9); k = R.randint(1, n); return f"{n} {k}\n{' '.join(str(R.randint(-5,5)) for _ in range(n))}\n"
def b(t):
    l = L(t); n, k = map(int, l[0].split()); a = list(map(int, l[1].split()))
    return [max(a[i:i+k]) for i in range(n-k+1)]
check('d053', g, b)
# d054
def g():
    n = R.randint(1, 7); iv = []
    for _ in range(n):
        s = R.randint(0, 8); iv.append((s, s+R.randint(1, 4)))
    return f"{n}\n" + "\n".join(f"{s} {e}" for s, e in iv) + "\n"
def b(t):
    iv = [tuple(map(int, x.split())) for x in L(t)[1:] if x]
    best = 0
    for m in range(1 << len(iv)):
        ch = sorted(iv[i] for i in range(len(iv)) if m >> i & 1)
        if all(ch[i][1] <= ch[i+1][0] for i in range(len(ch)-1)): best = max(best, len(ch))
    return [best]
check('d054', g, b)
# d055
def g():
    n, m = R.randint(1, 5), R.randint(1, 5)
    return f"{n} {m}\n{' '.join(str(R.randint(1,6)) for _ in range(n))}\n{' '.join(str(R.randint(1,6)) for _ in range(m))}\n"
def b(t):
    l = L(t); n, m = map(int, l[0].split()); g_ = list(map(int, l[1].split())); s = list(map(int, l[2].split()))
    best = 0
    for perm in itertools.permutations(range(m), min(n, m)):
        c = 0
        for i, j in enumerate(perm):
            if i < n and s[j] >= g_[i]: c += 1
        best = max(best, c)
    # 也允許小孩多於餅乾：枚舉小孩子集
    for r in range(1, min(n, m)+1):
        for kids in itertools.permutations(range(n), r):
            for cs in itertools.permutations(range(m), r):
                best = max(best, sum(1 for a, c in zip(kids, cs) if s[c] >= g_[a]))
    return [best]
check('d055', g, b, 60)
# d058
def g():
    n = R.randint(1, 8); return f"{n} {R.randint(0,15)}\n{' '.join(str(R.randint(1,6)) for _ in range(n))}\n"
def b(t):
    l = L(t); n, T = map(int, l[0].split()); a = list(map(int, l[1].split()))
    return [sum(1 for m in range(1 << n) if sum(a[i] for i in range(n) if m >> i & 1) == T)]
check('d058', g, b)
# d051
def g(): return f"{R.randint(1,12)} {R.randint(1,15)}\n"
def b(t):
    n, k = map(int, t.split()); p = list(range(1, n+1)); i = 0
    while len(p) > 1: i = (i+k-1) % len(p); p.pop(i)
    return p
check('d051', g, b)
# d057 已知值
assert run('d057', "1\n2\n3\n4\n5\n6\n7\n8\n9\n") == "1 0 0 2 10 4 40 92 352".split(); print('ok d057')
# d037 往返

# ---------------- 階段 3 ----------------
import math
M = 10**9+7
def rl(n, lo, hi): return [R.randint(lo, hi) for _ in range(n)]
# d066 / d067
def g():
    n = R.randint(1, 3); cs = R.sample(range(1, 8), n); A = R.randint(0, 15)
    return f"{n} {A}\n{' '.join(map(str, cs))}\n"
def b66(t):
    l = L(t); n, A = map(int, l[0].split()); cs = list(map(int, l[1].split()))
    def go(i, rem):
        if rem == 0: return 1
        if i == len(cs) or rem < 0: return 0
        return go(i, rem-cs[i]) + go(i+1, rem)
    return [go(0, A) % M]
check('d066', g, b66)
def b67(t):
    l = L(t); n, A = map(int, l[0].split()); cs = list(map(int, l[1].split()))
    best = [None]
    def go(rem, used):
        if rem == 0:
            best[0] = used if best[0] is None else min(best[0], used); return
        for c in cs:
            if c <= rem and used < 20: go(rem-c, used+1)
    go(A, 0)
    return [best[0] if best[0] is not None else -1]
check('d067', g, b67, 80)
# d068
def g():
    n = R.randint(1, 6); W = R.randint(0, 12)
    return f"{n} {W}\n" + "\n".join(f"{R.randint(1,8)} {R.randint(1,9)}" for _ in range(n)) + "\n"
def b(t):
    l = L(t); n, W = map(int, l[0].split()); it = [tuple(map(int, x.split())) for x in l[1:1+n]]
    return [max(sum(v for i, (w, v) in enumerate(it) if m >> i & 1) for m in range(1 << n) if sum(w for i, (w, v) in enumerate(it) if m >> i & 1) <= W)]
check('d068', g, b)
# d069
def g():
    n = R.randint(1, 9); return f"{n}\n{' '.join(map(str, rl(n, 1, 6)))}\n"
def b(t):
    a = list(map(int, L(t)[1].split())); dp = [1]*len(a)
    for i in range(len(a)):
        for j in range(i):
            if a[j] < a[i]: dp[i] = max(dp[i], dp[j]+1)
    return [max(dp)]
check('d069', g, b)
# d070
def g(): return "".join(R.choice("abc") for _ in range(R.randint(1, 7))) + "\n" + "".join(R.choice("abc") for _ in range(R.randint(1, 7))) + "\n"
def b(t):
    a, bb = L(t)[:2]
    best = 0
    for m in range(1 << len(a)):
        s = "".join(a[i] for i in range(len(a)) if m >> i & 1)
        it = iter(bb)
        if all(c in it for c in s): best = max(best, len(s))
    return [best]
check('d070', g, b)
# d071
def g():
    n = R.randint(1, 8); return f"{n}\n{' '.join(map(str, rl(n, -6, 6)))}\n"
def b(t):
    a = list(map(int, L(t)[1].split()))
    return [max(sum(a[i:j]) for i in range(len(a)) for j in range(i+1, len(a)+1))]
check('d071', g, b)
# d072
def g():
    r, c = R.randint(1, 4), R.randint(1, 4)
    return f"{r} {c}\n" + "\n".join(" ".join(map(str, rl(c, 0, 9))) for _ in range(r)) + "\n"
def b(t):
    l = L(t); r, c = map(int, l[0].split()); a = [list(map(int, x.split())) for x in l[1:1+r]]
    best = [10**9]
    def go(i, j, s):
        s += a[i][j]
        if i == r-1 and j == c-1: best[0] = min(best[0], s); return
        if i+1 < r: go(i+1, j, s)
        if j+1 < c: go(i, j+1, s)
    go(0, 0, 0); return best
check('d072', g, b)
# d073
def g():
    n = R.randint(1, 5); return f"{n}\n{' '.join(map(str, rl(n+1, 1, 9)))}\n"
def b(t):
    p = list(map(int, L(t)[1].split()))
    from functools import lru_cache
    @lru_cache(None)
    def f(i, j):
        if i == j: return 0
        return min(f(i, k)+f(k+1, j)+p[i-1]*p[k]*p[j] for k in range(i, j))
    return [f(1, len(p)-1)]
check('d073', g, b)
# d074
def g():
    n = R.randint(1, 6)
    return f"{n}\n" + "\n".join(" ".join("0" if i == j else str(R.randint(1, 9)) for j in range(n)) for i in range(n)) + "\n"
def b(t):
    l = L(t); n = int(l[0]); d = [list(map(int, x.split())) for x in l[1:1+n]]
    if n == 1: return [0]
    return [min(sum(d[a][b2] for a, b2 in zip((0,)+p, p+(0,))) for p in itertools.permutations(range(1, n)))]
check('d074', g, b)
# d062 字典序最小拓撲
def g():
    n = R.randint(1, 6); m = R.randint(0, 8)
    return f"{n} {m}\n" + "".join(f"{R.randint(1,n)} {R.randint(1,n)}\n" for _ in range(m)) if True else ""
def b(t):
    l = L(t); n, m = map(int, l[0].split()); E = [tuple(map(int, x.split())) for x in l[1:1+m]]
    for p in itertools.permutations(range(1, n+1)):
        pos = {v: i for i, v in enumerate(p)}
        if all(pos[u] < pos[v] for u, v in E): return list(p)
    return [-1]
check('d062', g, b)
# d064 Kruskal vs Prim 暴力：枚舉邊子集
def g():
    n = R.randint(1, 5); m = R.randint(0, 7)
    return f"{n} {m}\n" + "".join(f"{R.randint(1,n)} {R.randint(1,n)} {R.randint(1,9)}\n" for _ in range(m))
def b(t):
    l = L(t); n, m = map(int, l[0].split()); E = [tuple(map(int, x.split())) for x in l[1:1+m]]
    best = None
    for mask in range(1 << m):
        ch = [E[i] for i in range(m) if mask >> i & 1]
        if len(ch) != n-1: continue
        p = list(range(n+1))
        def f(x):
            while p[x] != x: x = p[x]
            return x
        ok = True
        for u, v, w in ch:
            a, c = f(u), f(v)
            if a == c: ok = False; break
            p[a] = c
        if ok:
            s = sum(w for _, _, w in ch); best = s if best is None else min(best, s)
    return [best if best is not None else -1]
check('d064', g, b)
# d063 Dijkstra vs Bellman-Ford
def g():
    n = R.randint(1, 6); m = R.randint(0, 9)
    return f"{n} {m}\n" + "".join(f"{R.randint(1,n)} {R.randint(1,n)} {R.randint(1,9)}\n" for _ in range(m))
def b(t):
    l = L(t); n, m = map(int, l[0].split()); E = [tuple(map(int, x.split())) for x in l[1:1+m]]
    I = 10**9; d = [I]*(n+1); d[1] = 0
    for _ in range(n):
        for u, v, w in E:
            if d[u]+w < d[v]: d[v] = d[u]+w
            if d[v]+w < d[u]: d[u] = d[v]+w
    return [d[n] if d[n] < I else -1]
check('d063', g, b)
# d061 DSU
def g():
    n = R.randint(1, 7); m = R.randint(0, 8)
    return f"{n} {m}\n" + "".join(f"{R.randint(1,n)} {R.randint(1,n)}\n" for _ in range(m))
def b(t):
    l = L(t); n, m = map(int, l[0].split()); comp = {i: {i} for i in range(1, n+1)}
    for x in l[1:1+m]:
        a, c = map(int, x.split())
        if comp[a] is not comp[c]:
            u = comp[a] | comp[c]
            for v in u: comp[v] = u
    sets = {id(s): s for s in comp.values()}
    return [len(sets), max(len(s) for s in sets.values())]
check('d061', g, b)
# d075
def g():
    q = R.randint(1, 4); return f"{q}\n" + "".join(f"{(n:=R.randint(0,30))} {R.randint(0,n+2)}\n" for _ in range(q))
def b(t):
    l = L(t); q = int(l[0]); o = []
    for x in l[1:1+q]:
        n, r = map(int, x.split()); o.append(math.comb(n, r) % M if r <= n else 0)
    return o
check('d075', g, b)
# d060 BFS vs 全路徑暴力（小格子）
def g():
    r, c = R.randint(1, 4), R.randint(2, 4)
    gr = [["#" if R.random() < .3 else "." for _ in range(c)] for _ in range(r)]
    gr[0][0] = "S"; gr[r-1][c-1] = "E"
    return f"{r} {c}\n" + "\n".join("".join(x) for x in gr) + "\n"
def b(t):
    l = L(t); r, c = map(int, l[0].split()); gr = l[1:1+r]
    best = [10**9]
    def go(x, y, seen, s):
        if gr[x][y] == "E": best[0] = min(best[0], s); return
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            a, b2 = x+dx, y+dy
            if 0 <= a < r and 0 <= b2 < c and gr[a][b2] != "#" and (a, b2) not in seen:
                go(a, b2, seen | {(a, b2)}, s+1)
    go(0, 0, {(0,0)}, 0)
    return [best[0] if best[0] < 10**9 else -1]
check('d060', g, b)

# ---------------- 階段 4 ----------------
from fractions import Fraction
# d080 凸包：暴力（點是否為頂點：不在其他點的凸組合內）
def g():
    n = R.randint(1, 8); return f"{n}\n" + "".join(f"{R.randint(0,4)} {R.randint(0,4)}\n" for _ in range(n))
def b(t):
    l = L(t); n = int(l[0]); P = sorted(set(tuple(map(int, x.split())) for x in l[1:1+n]))
    if len(P) <= 2: return [len(P), 0]
    def cr(o, a, c): return (a[0]-o[0])*(c[1]-o[1])-(a[1]-o[1])*(c[0]-o[0])
    # 頂點 = 存在一條過該點的直線使其他點全在嚴格同側（或另一側但該點為極端）→ 用暴力：邊 (a,b) 是凸包邊若所有點在同側
    edges = []
    for a in P:
        for c in P:
            if a == c: continue
            sides = [cr(a, c, p) for p in P if p not in (a, c)]
            if all(s >= 0 for s in sides) or all(s <= 0 for s in sides):
                edges.append((a, c))
    if all(cr(P[0], P[1], p) == 0 for p in P):
        return [2, 0]
    # 取非共線的凸包邊端點，頂點 = 被至少一條「有非零側」的邊使用，且不在邊內部
    verts = set()
    for a, c in edges:
        sides = [cr(a, c, p) for p in P if p not in (a, c)]
        if any(s != 0 for s in sides):
            inside = [p for p in P if p not in (a, c) and cr(a, c, p) == 0 and min(a[0], c[0]) <= p[0] <= max(a[0], c[0]) and min(a[1], c[1]) <= p[1] <= max(a[1], c[1])]
            # a、c 若中間有共線點，則它們仍是更長邊的端點；只收端點本身不被其他共線點「夾住」者
            for v in (a, c):
                others = [p for p in P if p != v and cr(a, c, p) == 0]
                lo = min(P_ for P_ in others + [v]); hi = max(P_ for P_ in others + [v])
                if v in (lo, hi): verts.add(v)
    verts = list(verts)
    cx = sum(v[0] for v in verts)/len(verts); cy = sum(v[1] for v in verts)/len(verts)
    import math
    verts.sort(key=lambda v: math.atan2(v[1]-cy, v[0]-cx))
    a2 = abs(sum(verts[i][0]*verts[(i+1) % len(verts)][1]-verts[(i+1) % len(verts)][0]*verts[i][1] for i in range(len(verts))))
    return [len(verts), a2]
check('d080', g, b, 200)
# d081 線段相交 vs 有理數
def g(): return " ".join(str(R.randint(-3,3)) for _ in range(8)) + "\n"
def b(t):
    x1,y1,x2,y2,x3,y3,x4,y4 = map(int, t.split())
    # 在有理數上用 8x 網格取樣不可靠；改為精確：參數式
    def seg_pts():
        return None
    ax,ay,bx,by,cx,cy,dx,dy = x1,y1,x2,y2,x3,y3,x4,y4
    r = (bx-ax, by-ay); s = (dx-cx, dy-cy)
    den = r[0]*s[1]-r[1]*s[0]
    q = (cx-ax, cy-ay)
    if den != 0:
        tt = Fraction(q[0]*s[1]-q[1]*s[0], den); uu = Fraction(q[0]*r[1]-q[1]*r[0], den)
        return ["YES" if 0 <= tt <= 1 and 0 <= uu <= 1 else "NO"]
    # 平行或有退化
    def pt_on(px, py, a1, a2, b1, b2):
        # 點是否在線段 a-b 上
        if (a1, a2) == (b1, b2): return (px, py) == (a1, a2)
        if (b1-a1)*(py-a2)-(b2-a2)*(px-a1) != 0: return False
        return min(a1,b1) <= px <= max(a1,b1) and min(a2,b2) <= py <= max(a2,b2)
    return ["YES" if (pt_on(ax,ay,cx,cy,dx,dy) or pt_on(bx,by,cx,cy,dx,dy) or pt_on(cx,cy,ax,ay,bx,by) or pt_on(dx,dy,ax,ay,bx,by)) else "NO"]
check('d081', g, b, 400)
# d083
def g(): return "".join(R.choice("ab") for _ in range(R.randint(1, 10))) + "\n"
def b(t):
    s = t.strip()
    for p in range(1, len(s)+1):
        if all(s[i] == s[i % p] for i in range(len(s))): return [p]
check('d083', g, b)
# d084
def g(): return "".join(R.choice("ab") for _ in range(R.randint(1, 12))) + "\n"
def b(t):
    s = t.strip(); return [max(j-i for i in range(len(s)) for j in range(i+1, len(s)+1) if s[i:j] == s[i:j][::-1])]
check('d084', g, b)
# d085 樹 MIS 暴力
def g():
    n = R.randint(1, 8); return f"{n}\n" + "".join(f"{R.randint(1,i-1)} {i}\n" for i in range(2, n+1))
def b(t):
    l = L(t); n = int(l[0]); E = [tuple(map(int, x.split())) for x in l[1:n]]
    return [max(bin(m).count('1') for m in range(1 << n) if all(not (m >> (u-1) & 1 and m >> (v-1) & 1) for u, v in E))]
check('d085', g, b)
# d086
def g():
    n = R.randint(1, 9); return f"{n}\n{' '.join(map(str, rl(n, 1, 5)))}\n"
def b(t):
    a = list(map(int, L(t)[1].split())); return [sum(1 for i in range(len(a)) for j in range(i+1, len(a)) if a[i] > a[j])]
check('d086', g, b)
# d087
def g():
    n = R.randint(1, 9); q = R.randint(1, 5)
    return f"{n} {q}\n{' '.join(map(str, rl(n, -9, 9)))}\n" + "".join(f"{(l:=R.randint(1,n))} {R.randint(l,n)}\n" for _ in range(q))
def b(t):
    l = L(t); n, q = map(int, l[0].split()); a = list(map(int, l[1].split()))
    return [min(a[int(x.split()[0])-1:int(x.split()[1])]) for x in l[2:2+q]]
check('d087', g, b)
# d088 Floyd 判斷
def g():
    n = R.randint(1, 5); m = R.randint(0, 8)
    return f"{n} {m}\n" + "".join(f"{R.randint(1,n)} {R.randint(1,n)} {R.randint(-3,5)}\n" for _ in range(m))
def b(t):
    l = L(t); n, m = map(int, l[0].split()); E = [tuple(map(int, x.split())) for x in l[1:1+m]]
    I = float('inf'); D = [[I]*(n+1) for _ in range(n+1)]
    for i in range(1, n+1): D[i][i] = 0
    for u, v, w in E: D[u][v] = min(D[u][v], w)
    for k in range(1, n+1):
        for i in range(1, n+1):
            for j in range(1, n+1):
                if D[i][k] < I and D[k][j] < I and D[i][k]+D[k][j] < D[i][j]: D[i][j] = D[i][k]+D[k][j]
    # 負環可達：存在 v 使 1->v 可達且 D[v][v]<0（Floyd 會把 D[v][v] 變成負）
    for v in range(1, n+1):
        if D[1][v] < I and D[v][v] < 0: return ["NEGATIVE", "CYCLE"]
    return [D[1][n] if D[1][n] < I else "UNREACHABLE"]
check('d088', g, b, 300)
# d089 SCC
def g():
    n = R.randint(1, 7); m = R.randint(0, 10)
    return f"{n} {m}\n" + "".join(f"{R.randint(1,n)} {R.randint(1,n)}\n" for _ in range(m))
def b(t):
    l = L(t); n, m = map(int, l[0].split()); E = [tuple(map(int, x.split())) for x in l[1:1+m]]
    reach = [[i == j for j in range(n+1)] for i in range(n+1)]
    for u, v in E: reach[u][v] = True
    for k in range(n+1):
        for i in range(n+1):
            for j in range(n+1):
                if reach[i][k] and reach[k][j]: reach[i][j] = True
    seen = set(); sizes = []
    for i in range(1, n+1):
        if i in seen: continue
        c = [j for j in range(1, n+1) if reach[i][j] and reach[j][i]]
        seen |= set(c); sizes.append(len(c))
    return [len(sizes), max(sizes)]
check('d089', g, b)
# d090 最大流 = 最小割
def g():
    n = R.randint(2, 6); m = R.randint(0, 9)
    return f"{n} {m}\n" + "".join(f"{R.randint(1,n)} {R.randint(1,n)} {R.randint(1,6)}\n" for _ in range(m))
def b(t):
    l = L(t); n, m = map(int, l[0].split()); E = [tuple(map(int, x.split())) for x in l[1:1+m]]
    best = 10**9
    for mask in range(1 << n):
        if not mask & 1 or mask >> (n-1) & 1: continue
        best = min(best, sum(c for u, v, c in E if mask >> (u-1) & 1 and not mask >> (v-1) & 1))
    return [best]
check('d090', g, b)
# d091
def g():
    r, c = R.randint(1, 4), R.randint(1, 4)
    return f"{r} {c}\n" + "\n".join("".join(R.choice("..#") for _ in range(c)) for _ in range(r)) + "\n"
def b(t):
    l = L(t); r, c = map(int, l[0].split()); gr = l[1:1+r]
    def go(i, j):
        if i >= r or j >= c or gr[i][j] == '#': return 0
        if i == r-1 and j == c-1: return 1
        return go(i+1, j) + go(i, j+1)
    return [go(0, 0) % M]
check('d091', g, b)
# d092
def g():
    S = sorted(R.sample(range(1, 7), R.randint(1, 3)))
    return f"{len(S)} 4\n{' '.join(map(str, S))}\n" + "".join(f"{R.randint(0,20)}\n" for _ in range(4))
def b(t):
    l = L(t); k, q = map(int, l[0].split()); S = list(map(int, l[1].split()))
    from functools import lru_cache
    @lru_cache(None)
    def win(n): return any(not win(n-s) for s in S if s <= n)
    return ["WIN" if win(int(x)) else "LOSE" for x in l[2:2+q]]
check('d092', g, b)
# d093
def g():
    q = R.randint(1, 4); return f"{q}\n" + "".join(f"{R.randint(1,60)}\n" for _ in range(q))
def b(t):
    l = L(t); q = int(l[0]); return [sum(1 for k in range(1, int(x)+1) if math.gcd(k, int(x)) == 1) for x in l[1:1+q]]
check('d093', g, b)
# d094
def g(): return f"{R.randint(1,3000)} {R.randint(0,20)}\n"
def b(t):
    N, S = map(int, t.split()); return [sum(1 for x in range(1, N+1) if sum(map(int, str(x))) == S)]
check('d094', g, b)
# d095
def gen_expr(d=0):
    if d > 3 or R.random() < .3: return str(R.randint(0, 20))
    op = R.choice("+-*")
    a, c = gen_expr(d+1), gen_expr(d+1)
    e = f"{a} {op} {c}"
    return f"({e})" if R.random() < .5 else e
def g(): return gen_expr() + "\n"
def b(t): return [eval(t)]
check('d095', g, b, 300)
# d076-79：與 d070/d068/d065 同演算法，以小資料交叉檢查
def g():
    return "".join(R.choice("abc") for _ in range(R.randint(1, 9))) + "\n" + "".join(R.choice("abc") for _ in range(R.randint(1, 9))) + "\n"
def b(t): return run('d070', t)
check('d076', g, b, 50)
def g():
    n = R.randint(1, 6); W = R.randint(0, 12)
    return f"{n} {W}\n" + "\n".join(f"{R.randint(1,8)} {R.randint(1,9)}" for _ in range(n)) + "\n"
def b(t): return run('d068', t)
check('d078', g, b, 80)
def g():
    n = R.randint(1, 6); m = R.randint(0, 8)
    return f"{n} {m} 3\n" + "".join(f"{R.randint(1,n)} {R.randint(1,n)} {R.randint(1,9)}\n" for _ in range(m)) + "".join(f"{R.randint(1,n)} {R.randint(1,n)}\n" for _ in range(3))
def b(t): return run('d065', t)
check('d079', g, b, 80)
def g(): return f"{R.randint(1,300)}\n"
def b(t):
    N = int(t); return [sum(1 for k in range(2, N+1) if all(k % i for i in range(2, int(k**.5)+1)))]
check('d077', g, b, 40)
