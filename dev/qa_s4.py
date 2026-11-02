"""階段 4（d076–d095、e401–e403）的品質檢查登記。"""
import itertools
import math
import random
from collections import deque
from fractions import Fraction

from qa import Q, pt, code, ints, sp, L, word, nums, toks, rows, inrange
from qa_s0 import body, mix
from qa_s3 import b070, g070, b068, g068, rand_graph, M, gridtxt


def conn_tree(r, n):
    return [(r.randint(1, v - 1), v) for v in range(2, n + 1)]


# d076：同 d070，字串長度到 3000（給 C++ 用）
Q("d076", b070, g070,
  lambda t: len(body(t)) == 2 and all(1 <= len(x) <= 3000 and x.islower() and x.isalpha() for x in body(t)),
  wrong=[pt("cur[j]=prev[j-1]+1 if x==b[j-1] else (prev[j] if prev[j]>cur[j-1] else cur[j-1])", "cur[j]=prev[j-1]+1 if x==b[j-1] else prev[j]")],
  big=[lambda r: "".join(r.choice("abcd") for _ in range(3000)) + "\n" + "".join(r.choice("abcd") for _ in range(3000)) + "\n", lambda r: "a" * 3000 + "\n" + "a" * 3000 + "\n"], cpp=True)

# d077
def prime_count(n):
    return sum(1 for k in range(2, n + 1) if all(k % p for p in range(2, int(k ** 0.5) + 1)))
def g077(r):
    return "".join(f"{mix(r, [1, 2, 3, 4, 97, 100, 101], 1, 300)}\n" for _ in range(r.randint(1, 3)))
Q("d077", lambda t: "".join(f"{prime_count(int(x))}\n" for x in body(t)), g077,
  lambda t: all(1 <= int(l) <= 3 * 10**7 for l in body(t)) and 1 <= len(body(t)) <= 3,
  wrong=[pt("for i in range(2,int(N**.5)+1):", "for i in range(2,int(N**.5)):"), pt("sv[0:2]=b'\\0\\0'[:min(2,N+1)]", "sv[0]=0")],
  big=[lambda r: "30000000\n29999999\n1\n", lambda r: "9999991\n10000000\n999999\n"], cpp=True)

# d078：同 d068 的大版本
Q("d078", b068, g068,
  lambda t: len(body(t)) == 1 + nums(body(t)[0])[0] and 1 <= nums(body(t)[0])[0] <= 1000 and 1 <= nums(body(t)[0])[1] <= 50000 and all(len(l.split()) == 2 and 1 <= nums(l)[0] <= 50000 and 1 <= nums(l)[1] <= 10**9 for l in body(t)[1:]),
  wrong=[pt("if w<=W:", "if w<W:")],
  big=[lambda r: "1000 50000\n" + "".join(f"{r.randint(1, 5000)} {r.randint(1, 10**6)}\n" for _ in range(1000)), lambda r: "1000 50000\n" + "".join(f"{r.randint(25000, 50000)} {r.randint(1, 10**6)}\n" for _ in range(1000))], cpp=True)

# d079
from qa_s3 import b065
def g079(r):
    n = r.randint(1, 6)
    m = r.randint(0, 8) if n > 1 else 0
    q = r.randint(1, 5)
    es = rand_graph(r, n, m, 9) if n > 1 else []
    return f"{n} {len(es)} {q}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in es) + "".join(f"{r.randint(1, n)} {r.randint(1, n)}\n" for _ in range(q))
Q("d079", b065, g079,
  lambda t: (lambda ls, n, m, q: 1 <= n <= 400 and 0 <= m <= 80000 and 1 <= q <= 10**5 and len(ls) == 1 + m + q and all(1 <= nums(l)[0] <= n and 1 <= nums(l)[1] <= n and (len(l.split()) == 2 or 1 <= nums(l)[2] <= 1000) for l in ls[1:]))(body(t), *nums(body(t)[0])),
  wrong=[pt("if w<D[u][v]: D[u][v]=D[v][u]=w", "D[u][v]=D[v][u]=w")],
  big=[lambda r: "400 20000 20000\n" + "".join(f"{u} {v} {w}\n" for u, v, w in rand_graph(r, 400, 20000, 1000)) + "".join(f"{r.randint(1, 400)} {r.randint(1, 400)}\n" for _ in range(20000))], cpp=True)

# d080
def jarvis(P):
    P = sorted(set(P))
    if len(P) <= 2:
        return len(P), 0
    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    start = P[0]
    hull = [start]
    cur = start
    while True:
        nxt = None
        for p in P:
            if p == cur:
                continue
            if nxt is None:
                nxt = p
                continue
            c = cr(cur, nxt, p)
            far = (p[0] - cur[0]) ** 2 + (p[1] - cur[1]) ** 2 > (nxt[0] - cur[0]) ** 2 + (nxt[1] - cur[1]) ** 2
            if c < 0 or (c == 0 and far):
                nxt = p
        if nxt == start:
            break
        hull.append(nxt)
        cur = nxt
        if len(hull) > len(P) + 1:
            break
    if len(hull) == 1:
        return 1, 0
    a = sum(hull[i][0] * hull[(i + 1) % len(hull)][1] - hull[(i + 1) % len(hull)][0] * hull[i][1] for i in range(len(hull)))
    return len(hull), abs(a)
def g080(r):
    n = r.randint(1, 9)
    k = r.choice([2, 3, 5, 8])
    pts = [(r.randint(-k, k), r.randint(-k, k)) for _ in range(n)]
    return f"{n}\n" + "".join(f"{x} {y}\n" for x, y in pts)
def b080(t):
    ls = body(t)
    n = int(ls[0])
    a, b = jarvis([tuple(nums(x)) for x in ls[1:1 + n]])
    return f"{a} {b}\n"
Q("d080", b080, g080,
  lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 20000 and all(len(l.split()) == 2 and inrange(nums(l), -10**6, 10**6) for l in body(t)[1:]),
  wrong=[pt("cr(lo[-2],lo[-1],p)<=0", "cr(lo[-2],lo[-1],p)<0"), pt("cr(up[-2],up[-1],p)<=0", "cr(up[-2],up[-1],p)<0"), pt("P=sorted(set(", "P=sorted(("), pt("print(len(H),abs(a))", "print(len(H),abs(a)//2)")],
  big=[lambda r: "20000\n" + "".join(f"{r.randint(-10**6, 10**6)} {r.randint(-10**6, 10**6)}\n" for _ in range(20000)),
       lambda r: "20000\n" + "".join(f"{i} {i}\n" for i in range(20000)),
       lambda r: "20000\n" + "".join(f"{(x := r.randint(-1000, 1000))} {r.choice([-1000, 1000, x])}\n" for _ in range(20000)),
       lambda r: "5\n0 0\n0 0\n0 0\n0 0\n0 0\n"])

# d081
def seg_inter(p1, p2, p3, p4):
    F = Fraction
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = p1, p2, p3, p4
    def pt_on_seg(p, a, b):
        cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        return cross == 0 and min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
    if p1 == p2:
        return pt_on_seg(p1, p3, p4)
    if p3 == p4:
        return pt_on_seg(p3, p1, p2)
    dx1, dy1, dx2, dy2 = x2 - x1, y2 - y1, x4 - x3, y4 - y3
    den = dx1 * dy2 - dy1 * dx2
    if den != 0:
        t = F((x3 - x1) * dy2 - (y3 - y1) * dx2, den)
        u = F((x3 - x1) * dy1 - (y3 - y1) * dx1, den)
        return 0 <= t <= 1 and 0 <= u <= 1
    if (x3 - x1) * dy1 - (y3 - y1) * dx1 != 0:
        return False
    return pt_on_seg(p3, p1, p2) or pt_on_seg(p4, p1, p2) or pt_on_seg(p1, p3, p4) or pt_on_seg(p2, p3, p4)
def g081(r):
    k = r.choice([2, 3, 5])
    out = []
    for _ in range(r.randint(1, 5)):
        v = [r.randint(-k, k) for _ in range(8)]
        if r.random() < 0.15:
            v[2:4] = v[0:2]
        out.append(sp(v))
    return "\n".join(out) + "\n"
def b081(t):
    o = ""
    for l in body(t):
        v = nums(l)
        o += ("YES" if seg_inter(tuple(v[0:2]), tuple(v[2:4]), tuple(v[4:6]), tuple(v[6:8])) else "NO") + "\n"
    return o
Q("d081", b081, g081,
  lambda t: all(len(l.split()) == 8 and inrange(nums(l), -10**9, 10**9) for l in body(t)) and 1 <= len(body(t)) <= 1000,
  wrong=[pt("if d1*d2<0 and d3*d4<0: return True", "if d1*d2<=0 and d3*d4<=0: return True"), pt("if d4==0 and on(c,d,b): return True", ""), pt("def on(p,q,r): return min(p[0],q[0])<=r[0]<=max(p[0],q[0]) and min(p[1],q[1])<=r[1]<=max(p[1],q[1])", "def on(p,q,r): return min(p[0],q[0])<=r[0]<=max(p[0],q[0])"), pt("if d1*d2<0 and d3*d4<0: return True", "if d1*d2<0 and d3*d4<0: return True\n    if d1==d2==d3==d4==0: return False")],
  big=[lambda r: "".join(sp([r.randint(-10**9, 10**9) for _ in range(8)]) + "\n" for _ in range(1000)), lambda r: "".join(sp([(c := r.randint(-10**9, 10**9)) % 7 * 100 + r.randint(0, 3), 0, c % 5 * 100, 0, r.randint(0, 600), 0, r.randint(0, 600), 0]) + "\n" for _ in range(1000))])

# d082
def g082(r):
    n = r.randint(3, 8)
    pts = set()
    while len(pts) < n:
        pts.add((r.randint(-6, 6), r.randint(-6, 6)))
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    pts = sorted(pts, key=lambda p: (math.atan2(p[1] - cy, p[0] - cx), (p[0] - cx) ** 2 + (p[1] - cy) ** 2))
    if r.random() < 0.5:
        pts.reverse()
    return f"{len(pts)}\n" + "".join(f"{x} {y}\n" for x, y in pts)
def b082(t):
    ls = body(t)
    n = int(ls[0])
    P = [tuple(nums(x)) for x in ls[1:1 + n]]
    s = 0
    for i in range(1, n - 1):
        s += (P[i][0] - P[0][0]) * (P[i + 1][1] - P[0][1]) - (P[i][1] - P[0][1]) * (P[i + 1][0] - P[0][0])
    return f"{abs(s)}\n"
def simple_poly(P):
    n = len(P)
    if n > 60:
        return True
    segs = [(P[i], P[(i + 1) % n]) for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if j == i + 1 or (i == 0 and j == n - 1):
                continue
            if seg_inter(*segs[i], *segs[j]):
                return False
    return True
def v082(t):
    ls = body(t)
    n = int(ls[0])
    P = [tuple(nums(x)) for x in ls[1:]]
    return 3 <= n <= 10**5 and len(P) == n and len(set(P)) == n and all(inrange(p, -10**6, 10**6) for p in P) and simple_poly(P)
def big082(r):
    n = 30000
    ang = sorted(r.random() * 2 * math.pi for _ in range(n))
    pts = [(round(10**6 * math.cos(a)), round(10**6 * math.sin(a))) for a in ang]
    out, seen = [], set()
    for p in pts:
        if p not in seen:
            seen.add(p); out.append(p)
    return f"{len(out)}\n" + "".join(f"{x} {y}\n" for x, y in out)
Q("d082", b082, g082, v082,
  wrong=[pt("print(abs(sum(", "print((sum("), pt("for i in range(n)))", "for i in range(n-1)))"), pt("P[i][0]*P[(i+1)%n][1]-P[(i+1)%n][0]*P[i][1]", "P[i][0]*P[(i+1)%n][1]+P[(i+1)%n][0]*P[i][1]")],
  big=[big082, lambda r: "4\n-1000000 -1000000\n1000000 -1000000\n1000000 1000000\n-1000000 1000000\n"])

# d083
def g083(r):
    return "".join(((lambda p, k: (p * (k + 1))[:r.randint(1, len(p) * (k + 1))])(word(r, 1, 4, "ab"), r.randint(0, 3)) if r.random() < 0.7 else word(r, 1, 7, "abc")) + "\n" for _ in range(r.randint(1, 4)))
def b083(t):
    o = ""
    for s in body(t):
        n = len(s)
        for p in range(1, n + 1):
            if all(s[i] == s[i % p] for i in range(n)):
                o += f"{p}\n"
                break
    return o
Q("d083", b083, g083,
  lambda t: all(1 <= len(l) <= 2 * 10**5 and l.islower() and l.isalpha() for l in body(t)) and 1 <= len(body(t)) <= 5,
  wrong=[pt("print(n-pi[-1])", "print(pi[-1])"), pt("while k and s[i]!=s[k]: k=pi[k-1]", "while k and s[i]!=s[k]: k=0"), pt("print(n-pi[-1])", "print(n-pi[-1] if n%(n-pi[-1])==0 else n)")],
  slow=[code("import sys\nfor l in sys.stdin:\n    s=l.strip()\n    if not s: continue\n    n=len(s)\n    for p in range(1,n+1):\n        if all(s[i]==s[i%p] for i in range(n)):\n            print(p);break\n", "逐一試每個 p（O(n²)）")],
  big=[lambda r: "a" * 199999 + "b\n" + "ab" * 99999 + "a\n", lambda r: "".join(r.choice("ab") for _ in range(100000)) + "\n", lambda r: ("abcab" * 20000) + "\n" + "a" * 100000 + "\n"])

# d084
def g084(r):
    return "".join(word(r, 1, 9, "ab" if r.random() < 0.5 else "abc") + "\n" for _ in range(r.randint(1, 4)))
def b084(t):
    o = ""
    for s in body(t):
        best = 1
        for i in range(len(s)):
            for j in range(i + 1, len(s) + 1):
                u = s[i:j]
                if u == u[::-1]:
                    best = max(best, j - i)
        o += f"{best}\n"
    return o
Q("d084", b084, g084,
  lambda t: all(1 <= len(l) <= 5000 and l.islower() and l.isalpha() for l in body(t)) and 1 <= len(body(t)) <= 5,
  wrong=[pt("max(P)", "max(P)-1"), pt("if i<R: P[i]=min(R-i,P[2*C-i])", "if i<R: P[i]=P[2*C-i]")],
  slow=[code("import sys\nfor l in sys.stdin:\n    s=l.strip()\n    if not s: continue\n    best=1\n    for i in range(len(s)):\n        for j in range(i+best+1,len(s)+1):\n            u=s[i:j]\n            if u==u[::-1]: best=max(best,j-i)\n    print(best)\n", "枚舉全部子字串 O(n³)")],
  big=[lambda r: "a" * 5000 + "\n" + "ab" * 2500 + "\n", lambda r: "".join(r.choice("ab") for _ in range(5000)) + "\n" + ("abc" * 1666 + "ab") + "\n"])

# d085
def g085(r):
    n = r.randint(1, 9)
    es = conn_tree(r, n)
    perm = list(range(1, n + 1)); r.shuffle(perm)
    return f"{n}\n" + "".join(f"{perm[u - 1]} {perm[v - 1]}\n" for u, v in es)
def b085(t):
    ls = body(t)
    n = int(ls[0])
    es = [tuple(nums(x)) for x in ls[1:n]]
    best = 0
    for m in range(1 << n):
        if all(not (m >> (u - 1) & 1 and m >> (v - 1) & 1) for u, v in es):
            best = max(best, bin(m).count("1"))
    return f"{best}\n"
def v085(t):
    ls = body(t)
    n = int(ls[0])
    if not (1 <= n <= 25000 and len(ls) == n):
        return False
    par = list(range(n + 1))
    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for l in ls[1:]:
        u, v = nums(l)
        if not (1 <= u <= n and 1 <= v <= n) or f(u) == f(v):
            return False
        par[f(u)] = f(v)
    return True
Q("d085", b085, g085, v085,
  wrong=[pt("b[p]+=a[u]", "b[p]+=b[u]"), pt("a[p]+=max(a[u],b[u])", "a[p]+=a[u]"), pt("print(max(a[1],b[1]))", "print(b[1])")],
  big=[lambda r: "25000\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 25000)), lambda r: "25000\n" + "".join(f"1 {i}\n" for i in range(2, 25001)), lambda r: "25000\n" + "".join(f"{r.randint(1, i - 1)} {i}\n" for i in range(2, 25001))])

# d086
def g086(r):
    n = r.randint(1, 9)
    return f"{n}\n{sp(ints(r, n, -5, 5))}\n"
Q("d086", lambda t: f"{(lambda a: sum(1 for i in range(len(a)) for j in range(i + 1, len(a)) if a[i] > a[j]))(nums(body(t)[1]))}\n", g086,
  lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 30000 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), -10**9, 10**9),
  wrong=[pt("if l[i]<=r[j]:", "if l[i]<r[j]:"), pt("c+=len(l)-i", "c+=1"), pt("c+=len(l)-i", "c+=len(l)-i-1")],
  slow=[code("n=int(input());a=list(map(int,input().split()))\nc=0\nfor i in range(n):\n    for j in range(i+1,n):\n        if a[i]>a[j]: c+=1\nprint(c)\n", "O(n²)")],
  big=[lambda r: "30000\n" + sp(range(30000, 0, -1)) + "\n", lambda r: "30000\n" + sp(ints(r, 30000, 0, 3)) + "\n"])

# d087
def g087(r):
    n, q = r.randint(1, 8), r.randint(1, 6)
    qs = []
    for _ in range(q):
        l = r.randint(1, n); qs.append((l, r.randint(l, n)))
    return f"{n} {q}\n{sp(ints(r, n, -9, 9))}\n" + "".join(f"{l} {rr}\n" for l, rr in qs)
def b087(t):
    ls = body(t)
    n, q = nums(ls[0])
    a = nums(ls[1])
    return "".join(f"{min(a[l - 1:rr])}\n" for l, rr in (nums(x) for x in ls[2:2 + q]))
def big087(r):
    n = q = 40000
    a = ints(r, n, -10**9, 10**9)
    qs = []
    for _ in range(q):
        l = r.randint(1, n // 5); qs.append(f"{l} {r.randint(n - n // 5, n)}")
    return f"{n} {q}\n{sp(a)}\n" + "\n".join(qs) + "\n"
Q("d087", b087, g087,
  lambda t: len(body(t)) == 2 + nums(body(t)[0])[1] and 1 <= nums(body(t)[0])[0] <= 5 * 10**4 and 1 <= nums(body(t)[0])[1] <= 5 * 10**4 and len(nums(body(t)[1])) == nums(body(t)[0])[0] and inrange(nums(body(t)[1]), -10**9, 10**9) and all(1 <= nums(l)[0] <= nums(l)[1] <= nums(body(t)[0])[0] for l in body(t)[2:]),
  wrong=[pt("j=(r-l+1).bit_length()-1", "j=(r-l+1).bit_length()"), pt("min(st[j][l],st[j][r-(1<<j)+1])", "st[j][l]")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1]);a=list(map(int,d[2:2+n]))\ni=2+n\nfor _ in range(q):\n    l,r=int(d[i])-1,int(d[i+1])-1;i+=2\n    m=a[l]\n    for k in range(l,r+1):\n        if a[k]<m: m=a[k]\n    print(m)\n", "每次查詢掃一遍"), code("import sys\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1]);a=list(map(int,d[2:2+n]))\ni=2+n\nfor _ in range(q):\n    l,r=int(d[i])-1,int(d[i+1])-1;i+=2\n    print(min(a[l:r+1]))\n", "每次 min(切片)")],
  big=[big087], nrand=6)

# d088
def g088(r):
    n = r.randint(1, 6)
    m = r.randint(0, 9)
    es = [(r.randint(1, n), r.randint(1, n), r.randint(-4, 6)) for _ in range(m)]
    return f"{n} {m}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in es)
def b088(t):
    ls = body(t)
    n, m = nums(ls[0])
    es = [tuple(nums(x)) for x in ls[1:1 + m]]
    reach = {1}
    ch = True
    while ch:
        ch = False
        for u, v, w in es:
            if u in reach and v not in reach:
                reach.add(v); ch = True
    es2 = [(u, v, w) for u, v, w in es if u in reach]
    INF = 10**18
    d = {v: INF for v in reach}
    d[1] = 0
    for it in range(len(reach) + 2):
        upd = False
        for u, v, w in es2:
            if d[u] + w < d[v]:
                d[v] = d[u] + w
                upd = True
        if not upd:
            break
    else:
        return "NEGATIVE CYCLE\n"
    if upd:
        return "NEGATIVE CYCLE\n"
    return (f"{d[n]}\n" if n in reach else "UNREACHABLE\n")
def v088(t):
    ls = body(t)
    n, m = nums(ls[0])
    return 1 <= n <= 500 and 0 <= m <= 3000 and len(ls) == 1 + m and all(len(l.split()) == 3 and 1 <= nums(l)[0] <= n and 1 <= nums(l)[1] <= n and -1000 <= nums(l)[2] <= 1000 for l in ls[1:])
Q("d088", b088, g088, v088,
  wrong=[pt("if it==n-1: neg=True", "if it==n-1: neg=False"), pt("print('NEGATIVE CYCLE' if neg else (D[n] if D[n]<I else 'UNREACHABLE'))", "print('NEGATIVE CYCLE' if neg else D[n])"), pt("for it in range(n):", "for it in range(n-1):")],
  big=[lambda r: "500 3000\n" + "".join(f"{u} {v} {w}\n" for u, v, w in [(r.randint(1, 499), r.randint(2, 500), r.randint(0, 1000)) for _ in range(3000)]),
       lambda r: "500 3000\n" + "".join(f"{i} {i + 1} {-1 if i % 2 else 2}\n" for i in range(1, 500)) + "".join(f"{r.randint(1, 499)} {r.randint(2, 500)} {r.randint(1, 1000)}\n" for _ in range(2501)),
       lambda r: "500 500\n" + "".join(f"{i} {i + 1} -1\n" for i in range(1, 500)) + "500 1 1\n"], nrand=6)

# d089
def g089(r):
    n = r.randint(1, 6)
    m = r.randint(0, 9)
    return f"{n} {m}\n" + "".join(f"{r.randint(1, n)} {r.randint(1, n)}\n" for _ in range(m))
def b089(t):
    ls = body(t)
    n, m = nums(ls[0])
    reach = [[i == j for j in range(n + 1)] for i in range(n + 1)]
    for l in ls[1:1 + m]:
        u, v = nums(l)
        reach[u][v] = True
    for k in range(1, n + 1):
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                if reach[i][k] and reach[k][j]:
                    reach[i][j] = True
    seen, comps = set(), []
    for i in range(1, n + 1):
        if i in seen:
            continue
        c = [j for j in range(1, n + 1) if reach[i][j] and reach[j][i]]
        seen.update(c)
        comps.append(len(c))
    return f"{len(comps)} {max(comps)}\n"
Q("d089", b089, g089,
  lambda t: (lambda ls, n, m: 1 <= n <= 10000 and 0 <= m <= 30000 and len(ls) == 1 + m and all(1 <= x <= n for l in ls[1:] for x in nums(l)))(body(t), *nums(body(t)[0])),
  wrong=[pt("for s in reversed(order):", "for s in order:"), pt("g[u].append(v);h[v].append(u)", "g[u].append(v);h[u].append(v)"), pt("print(c,max(sizes))", "print(c,sizes[0])")],
  big=[lambda r: "10000 10000\n" + "".join(f"{i} {i % 10000 + 1}\n" for i in range(1, 10001)), lambda r: "10000 30000\n" + "".join(f"{r.randint(1, 10000)} {r.randint(1, 10000)}\n" for _ in range(30000)), lambda r: "10000 9999\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 10000))])

# d090
def g090(r):
    n = r.randint(2, 6)
    m = r.randint(0, 10)
    return f"{n} {m}\n" + "".join(f"{r.randint(1, n)} {r.randint(1, n)} {r.randint(1, 9)}\n" for _ in range(m))
def b090(t):
    ls = body(t)
    n, m = nums(ls[0])
    es = [tuple(nums(x)) for x in ls[1:1 + m]]
    best = 10**18
    for mask in range(1 << n):
        if not (mask & 1) or (mask >> (n - 1) & 1):
            continue
        cut = sum(c for u, v, c in es if (mask >> (u - 1) & 1) and not (mask >> (v - 1) & 1))
        best = min(best, cut)
    return f"{best}\n"
Q("d090", b090, g090,
  lambda t: (lambda ls, n, m: 2 <= n <= 50 and 0 <= m <= 300 and len(ls) == 1 + m and all(len(l.split()) == 3 and 1 <= nums(l)[0] <= n and 1 <= nums(l)[1] <= n and 1 <= nums(l)[2] <= 1000 for l in ls[1:]))(body(t), *nums(body(t)[0])),
  wrong=[pt("cap[v][par[v]]+=b", "pass"), pt("cap[u][v]+=c", "cap[u][v]=c"), pt("f+=b", "f+=1")],
  big=[lambda r: "50 300\n" + "".join(f"{r.randint(1, 49)} {r.randint(2, 50)} {r.randint(1, 1000)}\n" for _ in range(300)), lambda r: "50 98\n" + "".join(f"{i} {i + 1} {r.randint(1, 1000)}\n" for i in range(1, 50)) + "".join(f"{i} {i + 1} {r.randint(1, 1000)}\n" for i in range(1, 50))])

# d091
def g091(r):
    R, C = r.randint(1, 4), r.randint(1, 4)
    return gridtxt(["".join("#" if r.random() < 0.25 else "." for _ in range(C)) for _ in range(R)])
def b091(t):
    ls = body(t)
    R, C = nums(ls[0])
    g = ls[1:1 + R]
    from functools import lru_cache
    @lru_cache(None)
    def f(i, j):
        if i >= R or j >= C or g[i][j] == "#":
            return 0
        if i == R - 1 and j == C - 1:
            return 1
        return f(i + 1, j) + f(i, j + 1)
    return f"{f(0, 0) % M}\n"
Q("d091", b091, g091,
  lambda t: (lambda ls, R, C: 1 <= R <= 400 and 1 <= C <= 400 and len(ls) == R + 1 and all(len(x) == C and set(x) <= set("#.") for x in ls[1:]))(body(t), *nums(body(t)[0])),
  wrong=[pt("%M", ""), pt("print(dp[R-1][C-1])", "print(dp[R-1][C-1]+1 if g[0][0]=='#' else dp[R-1][C-1])")],
  big=[lambda r: "400 400\n" + "\n".join("." * 400 for _ in range(400)) + "\n", lambda r: "400 400\n" + "\n".join("".join("#" if r.random() < 0.05 else "." for _ in range(400)) for _ in range(399)) + "\n" + "." * 399 + "#\n", lambda r: "400 400\n#" + "." * 399 + "\n" + "\n".join("." * 400 for _ in range(399)) + "\n"])

# d092
def g092(r):
    k = r.randint(1, 3)
    S = r.sample(range(1, 7), k)
    q = r.randint(1, 5)
    return f"{k} {q}\n{sp(S)}\n" + "".join(f"{r.randint(0, 25)}\n" for _ in range(q))
def b092(t):
    ls = body(t)
    k, q = nums(ls[0])
    S = nums(ls[1])
    from functools import lru_cache
    @lru_cache(None)
    def win(n):
        return any(s <= n and not win(n - s) for s in S)
    return "".join(("WIN" if win(int(x)) else "LOSE") + "\n" for x in ls[2:2 + q])
Q("d092", b092, g092,
  lambda t: (lambda ls, k, q: 1 <= k <= 10 and 1 <= q <= 1000 and len(ls) == 2 + q and len(set(nums(ls[1]))) == k == len(nums(ls[1])) and inrange(nums(ls[1]), 1, 10**6) and all(0 <= int(x) <= 10**6 for x in ls[2:]))(body(t), *nums(body(t)[0])),
  wrong=[pt("for n in range(1,N+1):", "for n in range(2,N+1):"), pt("if s>n: break", "if s>=n: break"), pt("'WIN' if w[n] else 'LOSE'", "'LOSE' if w[n] else 'WIN'")],
  big=[lambda r: "10 1000\n1 2 3 4 5 6 7 8 9 10\n" + "".join(f"{r.randint(0, 10**6)}\n" for _ in range(1000)), lambda r: "3 1000\n4 7 10\n" + "".join(f"{r.randint(900000, 10**6)}\n" for _ in range(1000)), lambda r: "1 5\n1000000\n0\n999999\n1000000\n1000000\n3\n"], cpp=True)

# d093
def g093(r):
    q = r.randint(1, 5)
    return f"{q}\n" + "".join(f"{r.randint(1, 60)}\n" for _ in range(q))
Q("d093", lambda t: "".join(f"{sum(1 for k in range(1, int(x) + 1) if math.gcd(k, int(x)) == 1)}\n" for x in body(t)[1:]), g093,
  lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 20000 and all(1 <= int(x) <= 10**6 for x in body(t)[1:]),
  wrong=[pt("phi[m]-=phi[m]//p", "phi[m]-=m//p"), pt("for p in range(2,N+1):", "for p in range(2,N):"), pt("phi=list(range(N+1))", "phi=[1]*(N+1)")],
  big=[lambda r: "20000\n" + "".join(f"{r.randint(1, 10**6)}\n" for _ in range(20000)), lambda r: "20000\n" + "".join(f"{r.choice([10**6, 999983, 720720, 1, 2])}\n" for _ in range(20000))], cpp=True)

# d094
def g094(r):
    return "".join(f"{r.randint(1, 300)} {r.randint(0, 20)}\n" for _ in range(r.randint(1, 4)))
Q("d094", lambda t: "".join(f"{sum(1 for k in range(1, nums(l)[0] + 1) if sum(map(int, str(k))) == nums(l)[1])}\n" for l in body(t)), g094,
  lambda t: all(len(l.split()) == 2 and 1 <= nums(l)[0] <= 10**18 and 0 <= nums(l)[1] <= 162 for l in body(t)) and 1 <= len(body(t)) <= 100,
  wrong=[pt("return r-(1 if S==0 else 0)", "return r"), pt("top=ds[i] if t else 9", "top=9"), pt("t and x==top", "x==top")],
  big=[lambda r: "".join(f"{r.randint(10**17, 10**18)} {r.randint(0, 162)}\n" for _ in range(100)), lambda r: "10000000000000000 1\n1000000000000000000 1\n999999999999999999 162\n1000000000000000000 0\n999999999999999999 0\n"])

# d095
def gen_expr(r, depth=0):
    t = r.random()
    if depth > 2 or t < 0.4:
        return str(r.randint(0, 20))
    if t < 0.55:
        return "(" + gen_expr(r, depth + 1) + ")"
    a, b = gen_expr(r, depth + 1), gen_expr(r, depth + 1)
    return a + r.choice([" + ", "+", " - ", "*", " * "]) + b
def g095(r):
    return "".join(gen_expr(r) + "\n" for _ in range(r.randint(1, 4)))
Q("d095", lambda t: "".join(f"{eval(l)}\n" for l in body(t)), g095,
  lambda t: all(1 <= len(l) <= 1000 and set(l) <= set("0123456789+-*() ") and not any(tok.startswith("0") and len(tok) > 1 for tok in __import__("re").findall(r"\d+", l)) for l in body(t)) and 1 <= len(body(t)) <= 100,
  wrong=[pt("while i[0]<len(t) and t[i[0]]=='*': i[0]+=1;v*=fc()", "if i[0]<len(t) and t[i[0]]=='*': i[0]+=1;v*=fc()"), pt("v=v+x if o=='+' else v-x", "v=v+x if o=='+' else x-v"), pt("v=tm()\n        while i[0]<len(t) and t[i[0]] in '+-':", "v=tm()\n        while False:")],
  big=[lambda r: "(" * 400 + "1" + ")" * 400 + "\n" + "+".join(["9"] * 300) + "\n" + "*".join(["99"] * 300) + "\n", lambda r: "".join("(" + str(r.randint(0, 10**6)) + "+" + str(r.randint(0, 10**6)) + ")*" + str(r.randint(1, 99)) + "-" + str(r.randint(1, 99)) + "\n" for _ in range(100))])

# e401
def g_e401(r):
    n = r.randint(1, 8)
    return f"{n} {r.randint(-6, 6)}\n{sp(ints(r, n, -4, 4))}\n"
def b_e401(t):
    ls = body(t)
    n, k = nums(ls[0])
    a = nums(ls[1])
    return f"{sum(1 for i in range(n) for j in range(i, n) if sum(a[i:j + 1]) == k)}\n"
Q("e401", b_e401, g_e401,
  lambda t: len(body(t)) == 2 and 1 <= nums(body(t)[0])[0] <= 20000 and len(nums(body(t)[1])) == nums(body(t)[0])[0] and inrange(nums(body(t)[1]), -1000, 1000),
  wrong=[pt("c={0:1}", "c={}"), pt("t+=c.get(s-k,0);c[s]=c.get(s,0)+1", "c[s]=c.get(s,0)+1;t+=c.get(s-k,0)")],
  slow=[code("n,k=map(int,input().split());a=list(map(int,input().split()))\nt=0\nfor i in range(n):\n    s=0\n    for j in range(i,n):\n        s+=a[j]\n        if s==k: t+=1\nprint(t)\n", "O(n²)")],
  big=[lambda r: "20000 0\n" + sp(ints(r, 20000, -1000, 1000)) + "\n", lambda r: "20000 0\n" + sp([0] * 20000) + "\n", lambda r: "20000 5\n" + sp([1, -1] * 10000) + "\n"])

# e402
def g_e402(r):
    n = r.randint(1, 8)
    return f"{n}\n{sp(ints(r, n, 0, 6))}\n"
Q("e402", lambda t: f"{(lambda h: max(min(h[i:j + 1]) * (j - i + 1) for i in range(len(h)) for j in range(i, len(h))))(nums(body(t)[1]))}\n", g_e402,
  lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 20000 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), 0, 10**9),
  wrong=[pt("W=i-st[-1]-1 if st else i", "W=i-st[-1] if st else i"), pt("+[0]", "")],
  slow=[code("n=int(input());h=list(map(int,input().split()))\nbest=0\nfor i in range(n):\n    m=h[i]\n    for j in range(i,n):\n        m=min(m,h[j])\n        best=max(best,m*(j-i+1))\nprint(best)\n", "O(n²)")],
  big=[lambda r: "20000\n" + sp(ints(r, 20000, 0, 10**9)) + "\n", lambda r: "20000\n" + sp(range(20000)) + "\n", lambda r: "20000\n" + sp([10**9] * 20000) + "\n"])

# e403
def g_e403(r):
    n = r.randint(2, 6)
    m = r.randint(1, 8)
    es = [(r.randint(1, n - 1 if i % 2 else n), r.randint(2, n), r.randint(1, 9)) for i in range(m)]
    es = [(u, v, w) for u, v, w in es if u != v] or [(1, n, 5)]
    return f"{n} {len(es)} {r.randint(0, 3)}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in es)
def b_e403(t):
    ls = body(t)
    n, m, K = nums(ls[0])
    es = [tuple(nums(x)) for x in ls[1:1 + m]]
    adj = {i: [] for i in range(1, n + 1)}
    for u, v, w in es:
        adj[u].append((v, w)); adj[v].append((u, w))
    best = None
    def go(u, seen, ws):
        nonlocal best
        if u == n:
            c = sum(ws) - sum(sorted(ws, reverse=True)[:K])
            if best is None or c < best:
                best = c
            return
        for v, w in adj[u]:
            if v not in seen:
                go(v, seen | {v}, ws + [w])
    go(1, {1}, [])
    return f"{-1 if best is None else best}\n"
Q("e403", b_e403, g_e403,
  lambda t: (lambda ls, n, m, K: 1 <= n <= 1000 and 0 <= m <= 5000 and 0 <= K <= 5 and len(ls) == 1 + m and all(len(l.split()) == 3 and 1 <= nums(l)[0] <= n and 1 <= nums(l)[1] <= n and 1 <= nums(l)[2] <= 10**6 for l in ls[1:]))(body(t), *nums(body(t)[0])),
  wrong=[pt("if j<K and c<D[v][j+1]:", "if j<K-1 and c<D[v][j+1]:"), pt("r=min(D[n])", "r=D[n][K]"), pt("D[1][0]=0", "D[1][0]=1")],
  big=[lambda r: "1000 5000 5\n" + "".join(f"{u} {v} {w}\n" for u, v, w in rand_graph(r, 1000, 5000, 10**6, connected=True)), lambda r: "1000 999 5\n" + "".join(f"{i} {i + 1} {r.randint(1, 10**6)}\n" for i in range(1, 1000)), lambda r: "1000 5000 0\n" + "".join(f"{u} {v} {w}\n" for u, v, w in rand_graph(r, 1000, 5000, 10**6, connected=True))])
