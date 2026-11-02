"""階段 2（d046–d059、e201–e203）的品質檢查登記。"""
import itertools
import math
import random
from functools import cmp_to_key

from qa import Q, pt, code, ints, sp, L, word, nums, toks, rows, inrange
from qa_s0 import body, mix, LOW, UP

# d046
def g(r):
    n, q = r.randint(1, 8), r.randint(1, 6)
    a = ints(r, n, -9, 9)
    qs = []
    for _ in range(q):
        l = r.randint(1, n)
        qs.append((l, r.randint(l, n)))
    return f"{n} {q}\n{sp(a)}\n" + "".join(f"{l} {rr}\n" for l, rr in qs)
def b046(t):
    ls = body(t)
    n, q = nums(ls[0])
    a = nums(ls[1])
    return "".join(f"{sum(a[l - 1:rr])}\n" for l, rr in (nums(x) for x in ls[2:2 + q]))
def v046(t):
    ls = body(t)
    n, q = nums(ls[0])
    a = nums(ls[1])
    return 1 <= n <= 5 * 10**4 and 1 <= q <= 5 * 10**4 and len(a) == n and inrange(a, -10**6, 10**6) and len(ls) == 2 + q and all(1 <= nums(x)[0] <= nums(x)[1] <= n for x in ls[2:])
def big046(r, n=40000, q=40000):
    a = ints(r, n, -1000, 1000)
    lines = []
    for _ in range(q):
        l = r.randint(1, n // 10)
        lines.append(f"{l} {r.randint(n - n // 10, n)}")
    return f"{n} {q}\n{sp(a)}\n" + "\n".join(lines) + "\n"
Q("d046", b046, g, v046,
  wrong=[pt("pre[r]-pre[l-1]", "pre[r]-pre[l]"), pt("pre[r]-pre[l-1]", "pre[r-1]-pre[l-1]"), pt("pre.append(pre[-1]+int(x))", "pre.append(int(x))")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1])\na=[int(x) for x in d[2:2+n]]\ni=2+n\nfor _ in range(q):\n    l,r=int(d[i]),int(d[i+1]);i+=2\n    s=0\n    for j in range(l-1,r): s+=a[j]\n    print(s)\n", "每次查詢都迴圈加總"),
        code("import sys\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1])\na=[int(x) for x in d[2:2+n]]\ni=2+n\nfor _ in range(q):\n    l,r=int(d[i]),int(d[i+1]);i+=2\n    print(sum(a[l-1:r]))\n", "每次查詢 sum(切片)")],
  big=[big046])

# d047
def g(r):
    n, q = r.randint(1, 8), r.randint(1, 6)
    a = sorted(ints(r, n, -6, 6))
    return f"{n} {q}\n{sp(a)}\n{sp(ints(r, q, -8, 8))}\n"
def b047(t):
    ls = body(t)
    n, q = nums(ls[0])
    a = nums(ls[1])
    o = []
    for x in nums(ls[2]):
        i = 0
        while i < n and a[i] < x:
            i += 1
        o.append(i + 1)
    return sp(o) + "\n"
def v047(t):
    ls = body(t)
    n, q = nums(ls[0])
    a = nums(ls[1])
    return 1 <= n <= 5 * 10**4 and 1 <= q <= 5 * 10**4 and len(a) == n and a == sorted(a) and len(nums(ls[2])) == q and len(ls) == 3 and inrange(a, -10**9, 10**9) and inrange(nums(ls[2]), -10**9, 10**9)
def big047(r):
    n = q = 30000
    a = sorted(ints(r, n, -10**9, 10**9))
    return f"{n} {q}\n{sp(a)}\n{sp(ints(r, q, -10**9, 10**9))}\n"
Q("d047", b047, g, v047,
  wrong=[pt("bisect.bisect_left(a,int(x))+1", "bisect.bisect_right(a,int(x))+1"), pt("bisect.bisect_left(a,int(x))+1", "bisect.bisect_left(a,int(x))"), pt("print(*[bisect.bisect_left(a,int(x))+1 for x in input().split()])", "print(*[min(bisect.bisect_left(a,int(x))+1,n) for x in input().split()])")],
  slow=[code("n,q=map(int,input().split())\na=list(map(int,input().split()))\no=[]\nfor x in map(int,input().split()):\n    i=0\n    while i<n and a[i]<x: i+=1\n    o.append(i+1)\nprint(*o)\n", "線性掃描")],
  big=[big047])

# d048
def g(r):
    n = r.randint(1, 8)
    return f"{n} {r.randint(-12, 12)}\n{sp(ints(r, n, -6, 6))}\n"
def b048(t):
    ls = body(t)
    n, k = nums(ls[0])
    a = nums(ls[1])
    return f"{sum(1 for i in range(n) for j in range(i + 1, n) if a[i] + a[j] <= k)}\n"
def big048(r):
    n = 40000
    return f"{n} {r.randint(-10**8, 10**8)}\n{sp(ints(r, n, -10**9, 10**9))}\n"
Q("d048", b048, g,
  lambda t: len(body(t)) == 2 and 1 <= nums(body(t)[0])[0] <= 40000 and len(nums(body(t)[1])) == nums(body(t)[0])[0] and inrange(nums(body(t)[1]), -10**9, 10**9) and abs(nums(body(t)[0])[1]) <= 10**9,
  wrong=[pt("if a[l]+a[r]<=k: c+=r-l;l+=1", "if a[l]+a[r]<=k: c+=r-l+1;l+=1"), pt("a=sorted(map(int,input().split()))", "a=list(map(int,input().split()))")],
  slow=[code("n,k=map(int,input().split())\na=list(map(int,input().split()))\nc=0\nfor i in range(n):\n    for j in range(i+1,n):\n        if a[i]+a[j]<=k: c+=1\nprint(c)\n", "雙迴圈 O(n²)")],
  big=[big048, lambda r: f"20000 0\n{sp(ints(r, 20000, -10**9, 10**9))}\n"])

# d049
def g(r):
    n = r.randint(1, 7)
    return f"{n}\n" + "".join(f"{word(r, 1, 3, 'abAB')} {r.randint(0, 5)}\n" for _ in range(n))
def b049(t):
    ls = body(t)
    n = int(ls[0])
    rs = [(l.split()[0], int(l.split()[1])) for l in ls[1:1 + n]]
    def cmp(x, y):
        if x[1] != y[1]:
            return -1 if x[1] > y[1] else 1
        return -1 if x[0] < y[0] else (1 if x[0] > y[0] else 0)
    rs.sort(key=cmp_to_key(cmp))
    return "".join(f"{a} {b}\n" for a, b in rs)
Q("d049", b049, g,
  lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 10**5 and all(len(l.split()) == 2 and l.split()[0].isalpha() and l.split()[1].lstrip("-").isdigit() for l in body(t)[1:]),
  wrong=[pt("(-r[1],r[0])", "(-r[1],)"), pt("(-r[1],r[0])", "(r[1],r[0])"), pt("(-r[1],r[0])", "(-r[1],r[0].lower())"), pt("(-r[1],r[0])", "(-r[1],-ord(r[0][0]))")],
  big=[lambda r: "40000\n" + "".join(f"{word(r, 1, 6, 'abcdefghAB')} {r.randint(0, 100)}\n" for _ in range(40000))])

# d050
def balanced(s):
    prev = None
    while prev != s:
        prev = s
        s = s.replace("()", "").replace("[]", "").replace("{}", "")
    return s == ""
def g(r):
    out = []
    for _ in range(r.randint(1, 5)):
        if r.random() < 0.5:
            s = ""
            for _ in range(r.randint(0, 4)):
                a, b = r.choice(["()", "[]", "{}"])
                s = s + a + (word(r, 0, 2, "()[]{}") if r.random() < 0.3 else "") + b if r.random() < 0.5 else a + s + b
            out.append(s)
        else:
            out.append("".join(r.choice("()[]{}") for _ in range(r.randint(0, 8))))
    return "\n".join(out) + "\n"
Q("d050", lambda t: "".join(("YES\n" if balanced(l) else "NO\n") for l in body(t)), g,
  lambda t: all(len(l) <= 10**5 and set(l) <= set("()[]{}") for l in body(t)) and body(t) != [],
  wrong=[pt("elif not st or st.pop()!=P[c]: ok=False;break", "elif st and st.pop()!=P[c]: ok=False;break"), pt("print('YES' if ok and not st else 'NO')", "print('YES' if ok else 'NO')"), pt("P={')':'(',']':'[','}':'{'}", "P={')':'(',']':'[','}':'['}"), pt("s=l.strip()", "s=l.strip() or '('")],
  big=[lambda r: "(" * 50000 + ")" * 50000 + "\n", lambda r: "([{" * 16666 + "}])" * 16666 + "\n", lambda r: "()" * 49999 + ")(\n"])

# d051
def jos_sim(n, k):
    people = list(range(1, n + 1))
    i = 0
    while len(people) > 1:
        i = (i + k - 1) % len(people)
        people.pop(i)
    return people[0]
def g(r):
    return "".join(f"{r.randint(1, 12)} {mix(r, [1, 2, 10**9], 1, 12)}\n" for _ in range(r.randint(1, 4)))
Q("d051", lambda t: "".join(f"{jos_sim(*nums(l))}\n" for l in body(t)), g,
  lambda t: all(len(l.split()) == 2 and 1 <= nums(l)[0] <= 10**6 and 1 <= nums(l)[1] <= 10**9 for l in body(t)) and 1 <= len(body(t)) <= 10,
  wrong=[pt("print(f+1)", "print(f)"), pt("f=(f+k)%i", "f=(f+k-1)%i"), pt("range(2,n+1)", "range(2,n)")],
  slow=[code("import sys\nfor l in sys.stdin:\n    p=l.split()\n    if p:\n        n,k=int(p[0]),int(p[1])\n        a=list(range(1,n+1));i=0\n        while len(a)>1:\n            i=(i+k-1)%len(a);a.pop(i)\n        print(a[0])\n", "直接模擬（list.pop）")],
  big=[lambda r: "".join(f"{n} {k}\n" for n, k in [(10**6, 10**9), (10**6, 1), (999999, 7), (500000, 123456789), (10**6, 2), (10**6, 999999999)])])

# d052
def b052(t):
    a = nums(body(t)[1])
    tot = 0
    while len(a) > 1:
        a.sort()
        x = a[0] + a[1]
        tot += x
        a = a[2:] + [x]
    return f"{tot}\n"
def g(r):
    n = r.randint(1, 8)
    return f"{n}\n{sp(ints(r, n, 1, 20))}\n"
Q("d052", b052, g,
  lambda t: len(body(t)) == 2 and int(body(t)[0]) == len(nums(body(t)[1])) and 1 <= int(body(t)[0]) <= 50000 and inrange(nums(body(t)[1]), 1, 10**9),
  wrong=[code("n=int(input());a=sorted(map(int,input().split()));t=0;s=0\nfor x in a[:1]:\n    s=x\nfor x in a[1:]:\n    s+=x;t+=s\nprint(t)\n"), pt("x=heapq.heappop(a)+heapq.heappop(a);t+=x;heapq.heappush(a,x)", "x=heapq.heappop(a)+heapq.heappop(a);t=max(t,x);heapq.heappush(a,x)"), pt("heapq.heapify(a);t=0", "t=0")],
  slow=[code("n=int(input());a=list(map(int,input().split()));t=0\nwhile len(a)>1:\n    a.sort()\n    x=a[0]+a[1];t+=x;a=a[2:]+[x]\nprint(t)\n", "每次排序 O(n² log n)")],
  big=[lambda r: "50000\n" + sp(ints(r, 50000, 1, 10**9)) + "\n", lambda r: "20000\n" + sp([10**9] * 20000) + "\n"])

# d053
def g(r):
    n = r.randint(1, 9)
    k = r.randint(1, n)
    return f"{n} {k}\n{sp(ints(r, n, -5, 5))}\n"
def b053(t):
    ls = body(t)
    n, k = nums(ls[0])
    a = nums(ls[1])
    return sp([max(a[i:i + k]) for i in range(n - k + 1)]) + "\n"
Q("d053", b053, g,
  lambda t: len(body(t)) == 2 and 1 <= nums(body(t)[0])[1] <= nums(body(t)[0])[0] <= 5 * 10**4 and len(nums(body(t)[1])) == nums(body(t)[0])[0] and inrange(nums(body(t)[1]), -10**9, 10**9),
  wrong=[pt("if q[0]<=i-k: q.popleft()", "if q[0]<i-k: q.popleft()"), pt("if i>=k-1: o.append(a[q[0]])", "if i>=k: o.append(a[q[0]])")],
  slow=[code("n,k=map(int,input().split())\na=list(map(int,input().split()))\nprint(*[max(a[i:i+k]) for i in range(n-k+1)])\n", "每個視窗重算 max")],
  big=[lambda r: "50000 25000\n" + sp(ints(r, 50000, -10**9, 10**9)) + "\n", lambda r: "30000 9000\n" + sp(range(30000)) + "\n"])

# d054
def b054(t):
    ls = body(t)
    n = int(ls[0])
    iv = [tuple(nums(x)) for x in ls[1:1 + n]]
    best = 0
    for m in range(1 << n):
        ch = sorted(iv[i] for i in range(n) if m >> i & 1)
        if all(ch[i][1] <= ch[i + 1][0] for i in range(len(ch) - 1)):
            best = max(best, len(ch))
    return f"{best}\n"
def g(r):
    n = r.randint(1, 8)
    iv = []
    for _ in range(n):
        s = r.randint(0, 8)
        iv.append((s, s + r.randint(1, 4)))
    return f"{n}\n" + "".join(f"{s} {e}\n" for s, e in iv)
Q("d054", b054, g,
  lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 30000 and all(len(l.split()) == 2 and 0 <= nums(l)[0] < nums(l)[1] <= 10**9 for l in body(t)[1:]),
  wrong=[pt("iv=sorted(((int(d[2+2*i]),int(d[1+2*i])) for i in range(n)))", "iv=sorted(((int(d[1+2*i]),int(d[2+2*i])) for i in range(n)))"), pt("if s>=t:", "if s>t:"), pt("iv=sorted(((int(d[2+2*i]),int(d[1+2*i])) for i in range(n)))", "iv=sorted(((int(d[2+2*i])-int(d[1+2*i]),int(d[1+2*i])) for i in range(n)))")],
  big=[lambda r: "30000\n" + "".join(f"{s} {s + r.randint(1, 1000)}\n" for s in (r.randint(0, 10**7) for _ in range(30000))), lambda r: "10000\n" + "".join(f"{i} {i + 1}\n" for i in range(10000))])

# d055
def b055(t):
    ls = body(t)
    n, m = nums(ls[0])
    g, s = nums(ls[1]), nums(ls[2])
    best = 0
    def go(i, used, cnt):
        nonlocal best
        best = max(best, cnt)
        if i == n:
            return
        go(i + 1, used, cnt)
        for j in range(m):
            if not used >> j & 1 and s[j] >= g[i]:
                go(i + 1, used | 1 << j, cnt + 1)
    go(0, 0, 0)
    return f"{best}\n"
def g(r):
    n, m = r.randint(1, 5), r.randint(1, 5)
    return f"{n} {m}\n{sp(ints(r, n, 1, 8))}\n{sp(ints(r, m, 1, 8))}\n"
Q("d055", b055, g,
  lambda t: len(body(t)) == 3 and 1 <= nums(body(t)[0])[0] <= 30000 and 1 <= nums(body(t)[0])[1] <= 30000 and len(nums(body(t)[1])) == nums(body(t)[0])[0] and len(nums(body(t)[2])) == nums(body(t)[0])[1],
  wrong=[pt("if i<n and x>=g[i]: i+=1", "if i<n and x>g[i]: i+=1"), pt("g=sorted(map(int,input().split()));s=sorted(map(int,input().split()))", "g=list(map(int,input().split()));s=sorted(map(int,input().split()))"), pt("print(i)", "print(min(n,m))")],
  big=[lambda r: "20000 20000\n" + sp(ints(r, 20000, 1, 10**9)) + "\n" + sp(ints(r, 20000, 1, 10**9)) + "\n"])

# d056
def perm_rec(n):
    out = []
    def go(cur, rest):
        if not rest:
            out.append(cur)
            return
        for x in rest:
            go(cur + [x], [y for y in rest if y != x])
    go([], list(range(1, n + 1)))
    return "".join(sp(p) + "\n" for p in out)
Q("d056", lambda t: perm_rec(int(t)), lambda r: f"{r.randint(1, 7)}\n", lambda t: len(body(t)) == 1 and 1 <= int(t) <= 7, space=7,
  wrong=[pt("itertools.permutations(range(1,n+1))", "reversed(list(itertools.permutations(range(1,n+1))))"), pt("range(1,n+1)", "range(n)")], nrand=4)

# d057
NQ = {1: 1, 2: 0, 3: 0, 4: 2, 5: 10, 6: 4, 7: 40, 8: 92, 9: 352}
def g(r):
    return "".join(f"{r.randint(1, 9)}\n" for _ in range(r.randint(1, 4)))
Q("d057", lambda t: "".join(f"{NQ[int(x)]}\n" for x in body(t)), g,
  lambda t: all(1 <= int(l) <= 9 for l in body(t)) and 1 <= len(body(t)) <= 9,
  space=500, wrong=[pt("r+c in d2", "r-c in d2"), pt("if c in cols or r-c in d1 or r+c in d2: continue", "if c in cols or r-c in d1: continue"), pt("if r==n: return 1", "if r==n: return 1 if n>1 else 0")], nrand=6)

# d058
def b058(t):
    ls = body(t)
    n, T = nums(ls[0])
    a = nums(ls[1])
    return f"{sum(1 for m in range(1 << n) if sum(a[i] for i in range(n) if m >> i & 1) == T)}\n"
def g(r):
    n = r.randint(1, 8)
    return f"{n} {r.randint(0, 20)}\n{sp(ints(r, n, 1, 8))}\n"
Q("d058", b058, g,
  lambda t: len(body(t)) == 2 and 1 <= nums(body(t)[0])[0] <= 18 and len(nums(body(t)[1])) == nums(body(t)[0])[0] and inrange(nums(body(t)[1]), 1, 1000) and nums(body(t)[0])[1] >= 0,
  wrong=[pt("dp={0:1}", "dp={}"), pt("nd=dict(dp)", "nd={}")],
  big=[lambda r: "18 9\n" + sp([1] * 18) + "\n", lambda r: "18 500\n" + sp(ints(r, 18, 1, 100)) + "\n", lambda r: "18 0\n" + sp(ints(r, 18, 1, 1000)) + "\n"])

# d059
def g(r):
    n = r.choice([1, 3, 5, 7])
    vals = r.sample(range(-9, 10), (n - 1) // 2 + 1)
    xs, lone = vals[:-1], vals[-1]
    a = xs + xs + [lone]
    r.shuffle(a)
    return f"{n}\n{sp(a)}\n"
def b059(t):
    from collections import Counter
    c = Counter(nums(body(t)[1]))
    return f"{[k for k, v in c.items() if v == 1][0]}\n"
def v059(t):
    ls = body(t)
    n = int(ls[0])
    a = nums(ls[1])
    from collections import Counter
    c = Counter(a)
    return n % 2 == 1 and 1 <= n <= 30001 and len(a) == n and sorted(c.values()).count(1) == 1 and all(v in (1, 2) for v in c.values()) and inrange(a, -10**9, 10**9)
Q("d059", b059, g, v059,
  wrong=[pt("x^=v", "x+=v"), pt("x=0", "x=1"), pt("x^=v", "x|=v")],
  big=[lambda r: (lambda xs: f"29999\n{sp(r.sample(xs + xs + [7], 29999))}\n")(r.sample(range(-10**9, 10**9), 14999))])

# e201
def g(r):
    n = r.randint(2, 8)
    return f"{n}\n{sp(ints(r, n, -9, 9))}\n"
def b_e201(t):
    a = sorted(nums(body(t)[1]))
    gaps = [a[i + 1] - a[i] for i in range(len(a) - 1)]
    m = min(gaps)
    return f"{m} {gaps.count(m)}\n"
Q("e201", b_e201, g,
  lambda t: len(body(t)) == 2 and 2 <= int(body(t)[0]) <= 30000 and len(nums(body(t)[1])) == int(body(t)[0]),
  wrong=[pt("print(m,d.count(m))", "print(m,1)"), pt("a=sorted(map(int,input().split()))", "a=list(map(int,input().split()))"), pt("print(m,d.count(m))", "print(m,len(set(d)))")],
  big=[lambda r: "30000\n" + sp(r.sample(range(-10**9, 10**9), 30000)) + "\n", lambda r: "10000\n" + sp([5] * 10000) + "\n"])

# e202
def b_e202(t):
    ls = body(t)
    n = int(ls[0])
    J = [tuple(nums(x)) for x in ls[1:1 + n]]
    best = 0
    for m in range(1 << n):
        ch = sorted((J[i] for i in range(n) if m >> i & 1))
        ok = all(i + 1 <= ch[i][0] for i in range(len(ch)))
        if ok:
            best = max(best, sum(p for _, p in ch))
    return f"{best}\n"
def g(r):
    n = r.randint(1, 8)
    return f"{n}\n" + "".join(f"{r.randint(1, 5)} {r.randint(1, 20)}\n" for _ in range(n))
Q("e202", b_e202, g,
  lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 30000 and all(len(l.split()) == 2 and 1 <= nums(l)[0] <= 10**9 and 1 <= nums(l)[1] <= 10**9 for l in body(t)[1:]),
  wrong=[pt("if len(h)>dl: heapq.heappop(h)", "if len(h)>=dl: heapq.heappop(h)"), pt("J=sorted((int(d[1+2*i]),int(d[2+2*i])) for i in range(n))", "J=sorted(((int(d[1+2*i]),int(d[2+2*i])) for i in range(n)),key=lambda x:-x[1])"), code("import sys\nd=sys.stdin.read().split()\nn=int(d[0]);J=sorted(((int(d[2+2*i]),int(d[1+2*i])) for i in range(n)),reverse=True)\nt=0\nslots=0\nfor p,dl in J:\n    if slots<dl: slots+=1;t+=p\nprint(t)\n")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nn=int(d[0]);J=sorted(((int(d[2+2*i]),int(d[1+2*i])) for i in range(n)),reverse=True)\nused=[0]*(n+2);t=0\nfor p,dl in J:\n    s=min(dl,n)\n    while s>0 and used[s]: s-=1\n    if s>0: used[s]=1;t+=p\nprint(t)\n", "依報酬由大到小、往前找空位（最壞 O(n²)）")],
  big=[lambda r: "30000\n" + "".join(f"{r.randint(1, 30000)} {r.randint(1, 10**9)}\n" for _ in range(30000)), lambda r: "15000\n" + "".join(f"15000 {10**9 - i}\n" for i in range(15000))])

# e203
def b_e203(t):
    n = int(t)
    ok = []
    for bits in itertools.product("()", repeat=2 * n):
        s = "".join(bits)
        d = 0
        good = True
        for c in s:
            d += 1 if c == "(" else -1
            if d < 0:
                good = False
                break
        if good and d == 0:
            ok.append(s)
    return "".join(s + "\n" for s in sorted(ok))
Q("e203", b_e203, lambda r: f"{r.randint(1, 4)}\n", lambda t: len(body(t)) == 1 and 1 <= int(t) <= 8, space=8,
  wrong=[pt("if r<l: go(s+')',l,r+1)", "if r<=l: go(s+')',l,r+1)"), pt("if l<n: go(s+'(',l+1,r)\n    if r<l: go(s+')',l,r+1)", "if r<l: go(s+')',l,r+1)\n    if l<n: go(s+'(',l+1,r)")])
