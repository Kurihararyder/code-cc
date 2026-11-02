"""階段 1（d031–d045、e101–e103）的品質檢查登記。"""
import datetime
import math
import random

from qa import Q, pt, code, ints, sp, L, word, nums, toks, rows, inrange
from qa_s0 import body, mix, LOW, UP

# d031
def g(r):
    out = []
    for _ in range(r.randint(0, 5)):
        a, b = r.randint(-9, 9), r.randint(-9, 9)
        if (a, b) == (0, 0):
            b = 1
        out.append(f"{a} {b}")
    out.append("0 0")
    for _ in range(r.randint(0, 2)):
        out.append(f"{r.randint(-9, 9)} {r.randint(-9, 9)}")
    return "\n".join(out) + "\n"
def b031(t):
    o = []
    for l in body(t):
        a, b = map(int, l.split())
        if a == 0 and b == 0:
            break
        o.append(f"{abs(a - b)}\n")
    return "".join(o)
Q("d031", b031, g,
  lambda t: all(len(l.split()) == 2 and inrange(nums(l), -10**9, 10**9) for l in body(t)) and "0 0" in body(t),
  wrong=[pt("if a==0 and b==0: break", "if a==0 or b==0: break"), pt("if a==0 and b==0: break", "if a==0 and b==0: continue"), pt("abs(a-b)", "a-b"), pt("if a==0 and b==0: break", "if a+b==0: break")])

# d032
def g(r):
    t = r.randint(1, 4)
    out = [str(t)]
    for _ in range(t):
        n = r.choice([0, 1, 2, 3, 5])
        out.append(str(n))
        out.append(sp(ints(r, n, -20, 20)))
    return "\n".join(out) + "\n"
def b032(t):
    ls = body(t)
    T = int(ls[0])
    o = []
    for k in range(T):
        o.append(f"{sum(nums(ls[2 + 2 * k]))}\n")
    return "".join(o)
def v032(t):
    ls = body(t)
    if len(ls) != 1 + 2 * int(ls[0]) or not 1 <= int(ls[0]) <= 100:
        return False
    for k in range(int(ls[0])):
        n = int(ls[1 + 2 * k])
        if not (0 <= n <= 1000 and len(nums(ls[2 + 2 * k])) == n):
            return False
    return True
Q("d032", b032, g, v032,
  wrong=[code("t=int(input())\nfor _ in range(t):\n    n=int(input())\n    a=list(map(int,input().split()))\n    print(sum(a[:max(n-1,0)]) if n else 0)\n"),
         code("t=int(input())\nfor _ in range(t):\n    n=int(input())\n    a=list(map(int,input().split()))\n    print(max(a))\n"),
         code("import sys\nd=sys.stdin.read().split()\nt=int(d[0])\nprint(*[sum(map(int,d[2+2*i:3+2*i])) for i in range(t)],sep='\\n')\n")])

# d033
def g(r):
    gs = []
    for _ in range(r.randint(1, 4)):
        gs.append("\n".join(str(r.randint(-9, 9)) for _ in range(r.randint(1, 4))))
    return "\n\n".join(gs) + "\n"
def b033(t):
    return "".join(f"{sum(int(x) for x in grp.split())}\n" for grp in t.strip("\n").split("\n\n"))
def v033(t):
    if t.endswith("\n\n") or t.startswith("\n") or "\n\n\n" in t:
        return False
    gs = t.strip("\n").split("\n\n")
    return 1 <= len(gs) <= 100 and all(1 <= len(g.split("\n")) <= 100 and all(x.lstrip("-").isdigit() for x in g.split("\n")) for g in gs)
Q("d033", b033, g, v033,
  wrong=[pt("if has: print(s)", "pass"), pt("    if l=='':\n        print(s);s=0;has=False", "    if l=='':\n        print(s);has=False"), pt("s+=int(l);has=True", "s=int(l);has=True")])

# d034
def g(r):
    t = r.randint(1, 4)
    return f"{t}\n" + "".join(f"{mix(r, [0, 1, 10**6], 0, 50)}\n" for _ in range(t))
def b034(t):
    ls = body(t)
    T = int(ls[0])
    blocks = []
    for k in range(T):
        n = int(ls[1 + k])
        blocks.append(f"Case #{k + 1}:\n{n * (n + 1) // 2}\n")
    return "\n".join(blocks)
Q("d034", b034, g,
  lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 100 and all(0 <= int(x) <= 10**6 for x in body(t)[1:]),
  wrong=[pt("if k>1: print()", "print()"), pt("Case #{k}:", "Case {k}:"), pt("n*(n+1)//2", "n*(n-1)//2"), pt("if k>1: print()", "if k>2: print()")])

# d035
def exact_tie4(a, b):
    x = (a * 10**4 * 2) % (2 * b)           # 乘以 10^4 後小數部分恰為 1/2 的條件：2a·10^4 mod 2b == b
    return (a * 10**4 * 2) % (2 * b) == b
def g(r):
    out = []
    for _ in range(r.randint(1, 5)):
        while True:
            a, b = r.randint(1, 30), r.randint(1, 30)
            if not exact_tie4(a, b):
                break
        out.append(f"{a} {b}")
    return "\n".join(out) + "\n"
def b035(t):
    from fractions import Fraction
    o = []
    for l in body(t):
        a, b = map(int, l.split())
        q = (Fraction(a, b) * 10**4 * 2 + 1) // 2      # 四捨五入
        o.append(f"{q // 10**4}.{q % 10**4:04d}\n")
    return "".join(o)
Q("d035", b035, g,
  lambda t: all(len(l.split()) == 2 and inrange(nums(l), 1, 10**6) and not exact_tie4(*nums(l)) for l in body(t)) and body(t) != [],
  wrong=[pt(":.4f", ":.3f"), pt("int(p[0])/int(p[1])", "int(p[0])//int(p[1])"), pt("f'{int(p[0])/int(p[1]):.4f}'", "round(int(p[0])/int(p[1]),4)")])

# d036
def g(r):
    out = []
    for _ in range(r.randint(1, 3)):
        out.append(f"{r.randint(0, 10**r.randint(1, 30))} {r.randint(0, 10**r.randint(1, 30))}")
    return "\n".join(out) + "\n"
Q("d036", lambda t: "".join(f"{int(a) + int(b)}\n{int(a) * int(b)}\n" for a, b in (l.split() for l in body(t))), g,
  lambda t: all(len(l.split()) == 2 and all(x.isdigit() and len(x) <= 500 for x in l.split()) for l in body(t)) and 1 <= len(body(t)) <= 20,
  wrong=[pt("print(a+b);print(a*b)", "print(a+b);print(float(a)*b)"), pt("print(a+b);print(a*b)", "print(a+b);print(a*b%(10**18))"), pt("print(a+b);print(a*b)", "print(a*b);print(a+b)")])

# d037
DIG = "0123456789ABCDEF"
def conv(s, a, b):
    n = 0
    for c in s:
        n = n * a + DIG.index(c)
    if n == 0:
        return "0"
    o = ""
    while n:
        o = DIG[n % b] + o
        n //= b
    return o
def g(r):
    out = []
    for _ in range(r.randint(1, 4)):
        a, b = r.randint(2, 16), r.randint(2, 16)
        n = r.choice([0, 1, 255, 10**18, r.randint(0, 10**r.randint(1, 18))])
        s = "0"
        if n:
            s = ""
            while n:
                s = DIG[n % a] + s
                n //= a
        out.append(f"{s} {a} {b}")
    return "\n".join(out) + "\n"
def v037(t):
    for l in body(t):
        p = l.split()
        if len(p) != 3:
            return False
        s, a, b = p[0], int(p[1]), int(p[2])
        if not (2 <= a <= 16 and 2 <= b <= 16) or not all(c in DIG[:a] for c in s):
            return False
        if int(s, a) > 10**18:
            return False
    return body(t) != []
Q("d037", lambda t: "".join(conv(*[x if i == 0 else int(x) for i, x in enumerate(l.split())]) + "\n" for l in body(t)), g, v037,
  wrong=[pt("print(o or '0')", "print(o)"), pt("D='0123456789ABCDEF'", "D='0123456789abcdef'"), pt("n=int(p[0],int(p[1]))", "n=int(p[0],10)"), pt("o=D[n%b]+o", "o=o+D[n%b]")])

# d038
def pi_naive(n):
    return sum(1 for k in range(2, n + 1) if all(k % p for p in range(2, int(k ** 0.5) + 1)))
def g(r):
    q = r.randint(1, 5)
    return f"{q}\n" + "".join(f"{mix(r, [1, 2, 3, 100], 1, 150)}\n" for _ in range(q))
Q("d038", lambda t: "".join(f"{pi_naive(int(x))}\n" for x in body(t)[1:]), g,
  lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 30000 and all(1 <= int(x) <= 10**6 for x in body(t)[1:]),
  wrong=[pt("pi[i]=pi[i-1]+sv[i]", "pi[i]=pi[i-1]+sv[i-1]"), pt("sv[0]=sv[1]=0", "sv[0]=0")],
  slow=[code("import sys\nd=sys.stdin.read().split()\ndef p(n):\n    c=0\n    for k in range(2,n+1):\n        i=2\n        while i*i<=k:\n            if k%i==0: break\n            i+=1\n        else: c+=1\n    return c\nfor x in d[1:1+int(d[0])]: print(p(int(x)))\n", "每個查詢重算")],
  big=[lambda r: "30000\n" + "".join(f"{r.randint(1, 10**6)}\n" for _ in range(30000)), lambda r: "30000\n" + "".join(f"{10**6 - r.randint(0, 5)}\n" for _ in range(30000))])

# d039
ROM = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
def roman(n):
    o = ""
    for v, s in ROM:
        o += s * (n // v)
        n %= v
    return o
def g(r):
    return "".join(f"{mix(r, [1, 4, 9, 14, 40, 90, 400, 900, 3999, 3888, 1994], 1, 3999)}\n" for _ in range(r.randint(1, 6)))
Q("d039", lambda t: "".join(roman(int(x)) + "\n" for x in body(t)), g,
  lambda t: all(len(l.split()) == 1 and 1 <= int(l) <= 3999 for l in body(t)) and body(t) != [],
  wrong=[pt("(4,'IV')", "(4,'IIII')"), pt("(9,'IX')", "(9,'VIIII')"), pt("(900,'CM'),", ""), pt("(40,'XL'),", ""), pt("(90,'XC'),", "")])

# d040
def g(r):
    return "".join("{} {} {}\n".format(*[(d.year, d.month, d.day) for d in [datetime.date(1900, 1, 1) + datetime.timedelta(days=r.randint(0, 73000))]][0]) for _ in range(r.randint(1, 5)))
def b040(t):
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    o = ""
    for l in body(t):
        y, m, d = map(int, l.split())
        # Zeller（和 datetime 不同做法）
        if m < 3:
            m += 12
            y -= 1
        K, J = y % 100, y // 100
        h = (d + 13 * (m + 1) // 5 + K + K // 4 + J // 4 + 5 * J) % 7      # 0=Saturday
        o += names[(h + 5) % 7] + "\n"
    return o
def v040(t):
    for l in body(t):
        p = l.split()
        if len(p) != 3:
            return False
        try:
            d = datetime.date(*map(int, p))
        except ValueError:
            return False
        if not 1900 <= d.year <= 2100:
            return False
    return body(t) != []
Q("d040", b040, g, v040,
  wrong=[pt("datetime.date(int(p[0]),int(p[1]),int(p[2])).weekday()", "(datetime.date(int(p[0]),int(p[1]),int(p[2])).weekday()+1)%7"),
         code("import sys\nN=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']\nfor l in sys.stdin:\n    p=l.split()\n    if p:\n        y,m,d=map(int,p)\n        days=sum(365+(1 if i%4==0 else 0) for i in range(1900,y))\n        M=[31,28+(1 if y%4==0 else 0),31,30,31,30,31,31,30,31,30,31]\n        days+=sum(M[:m-1])+d-1\n        print(N[days%7])\n")])

# d041
def g(r):
    n = r.randint(1, 5)
    return f"{n}\n{''.join(r.choice('UDLR') for _ in range(r.randint(1, 15)))}\n"
def b041(t):
    ls = body(t)
    n = int(ls[0])
    x = y = 0
    for c in ls[1]:
        nx, ny = x + (c == "R") - (c == "L"), y + (c == "U") - (c == "D")
        if 0 <= nx < n and 0 <= ny < n:
            x, y = nx, ny
    return f"{x} {y}\n"
Q("d041", b041, g,
  lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 100 and 1 <= len(body(t)[1]) <= 10**5 and set(body(t)[1]) <= set("UDLR"),
  wrong=[pt("0<=x+dx<n and 0<=y+dy<n", "0<=x+dx<n or 0<=y+dy<n"), pt("0<=x+dx<n and 0<=y+dy<n", "0<=x+dx<=n and 0<=y+dy<=n"), pt("0<=x+dx<n and 0<=y+dy<n", "0<x+dx<n and 0<y+dy<n"), pt("'U':(0,1),'D':(0,-1)", "'U':(0,-1),'D':(0,1)")],
  big=[lambda r: "100\n" + "".join(r.choice("UDLR") for _ in range(100000)) + "\n", lambda r: "7\n" + "".join(r.choice("UUUURRRDL") for _ in range(100000)) + "\n"])

# d042
def b042(t):
    n = int(t)
    a = [[0] * n for _ in range(n)]
    top, bot, lft, rgt, k = 0, n - 1, 0, n - 1, 1
    while top <= bot and lft <= rgt:
        for j in range(lft, rgt + 1):
            a[top][j] = k; k += 1
        top += 1
        for i in range(top, bot + 1):
            a[i][rgt] = k; k += 1
        rgt -= 1
        if top <= bot:
            for j in range(rgt, lft - 1, -1):
                a[bot][j] = k; k += 1
            bot -= 1
        if lft <= rgt:
            for i in range(bot, top - 1, -1):
                a[i][lft] = k; k += 1
            lft += 1
    return "".join(sp(r) + "\n" for r in a)
def g(r):
    return f"{r.randint(1, 8)}\n"
Q("d042", b042, g, lambda t: len(body(t)) == 1 and 1 <= int(t) <= 30,
  wrong=[pt("D=[(0,1),(1,0),(0,-1),(-1,0)]", "D=[(1,0),(0,1),(-1,0),(0,-1)]"), pt("for k in range(1,n*n+1)", "for k in range(0,n*n)")])

# d043
def rle(s):
    o, i = "", 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        o += s[i] + str(j - i)
        i = j
    return o
def g(r):
    return "".join(word(r, 1, 12, "aab") + "\n" for _ in range(r.randint(1, 4)))
Q("d043", lambda t: "".join(rle(l) + "\n" for l in body(t)), g,
  lambda t: all(1 <= len(l) <= 10**5 and " " not in l for l in body(t)) and body(t) != [],
  wrong=[pt("    o.append(f'{c}{k}');print(''.join(o))", "    print(''.join(o))"), pt("o.append(f'{c}{k}');c=ch;k=1", "o.append(f'{c}{k}');c=ch;k=0"), pt("f'{c}{k}');c=ch", "f'{c}{k}' if k>1 else c);c=ch")],
  big=[lambda r: "a" * 100000 + "\n", lambda r: "ab" * 50000 + "\n", lambda r: "".join(r.choice("abc") * r.randint(1, 30) for _ in range(5000))[:100000] + "\n"])

# d044
def g(r):
    out = []
    for _ in range(r.randint(1, 4)):
        k = r.randint(1, 6)
        t = [str(r.randint(0, 20))]
        for _ in range(k - 1):
            t += [r.choice("+-*"), str(r.randint(0, 20))]
        out.append(" ".join(t))
    return "\n".join(out) + "\n"
def b044(t):
    o = ""
    for l in body(t):
        tk = l.split()
        v = int(tk[0])
        for i in range(1, len(tk), 2):
            x = int(tk[i + 1])
            v = {"+": v + x, "-": v - x, "*": v * x}[tk[i]]
        o += f"{v}\n"
    return o
def v044(t):
    for l in body(t):
        tk = l.split()
        if len(tk) % 2 == 0 or len(tk) > 39:
            return False
        for i, x in enumerate(tk):
            if i % 2 == 0 and not (x.isdigit() and 0 <= int(x) <= 1000):
                return False
            if i % 2 == 1 and x not in "+-*":
                return False
    return body(t) != []
Q("d044", b044, g, v044,
  wrong=[code("import sys\nfor l in sys.stdin:\n    if l.strip(): print(eval(l))\n"), pt("o=='+'", "o=='-'")])

# d045
def g(r):
    return "".join(f"{r.choice([0, 1, 11, 12, 13, 23, r.randint(0, 23)]):02d}:{r.randint(0, 59):02d}:{r.randint(0, 59):02d}\n" for _ in range(r.randint(1, 5)))
def b045(t):
    o = ""
    for l in body(t):
        h, m, s = l.split(":")
        h = int(h)
        suf = "AM" if h < 12 else "PM"
        hh = h % 12 or 12
        o += f"{hh:02d}:{m}:{s} {suf}\n"
    return o
Q("d045", b045, g,
  lambda t: all(len(l) == 8 and l[2] == ":" and l[5] == ":" and 0 <= int(l[:2]) <= 23 and 0 <= int(l[3:5]) <= 59 and 0 <= int(l[6:]) <= 59 for l in body(t)) and body(t) != [],
  wrong=[pt("(h%12) or 12", "h%12"), pt("'AM' if h<12 else 'PM'", "'AM' if h<=12 else 'PM'"), pt(":02d}", "}")])

# e101
def g(r):
    t = r.randint(1, 3)
    out = [str(t)]
    for _ in range(t):
        n = r.randint(1, 5)
        out.append(str(n))
        names = sorted({word(r, 1, 3, "abc") for _ in range(n)})        # 集合的順序會隨雜湊種子改變，要先排序才能讓測資可重現
        n = len(names)
        out[-1] = str(n)
        for nm in names:
            out.append(f"{nm} {r.choice([0, 50, 90, 100, r.randint(0, 100)])}")
    return "\n".join(out) + "\n"
def b_e101(t):
    ls = body(t)
    T = int(ls[0])
    i = 1
    blocks = []
    for k in range(T):
        n = int(ls[i]); i += 1
        rs = [(l.split()[0], int(l.split()[1])) for l in ls[i:i + n]]; i += n
        rs.sort(key=lambda x: (-x[1], x[0]))
        o = f"Case #{k + 1}:\n"
        for nm, sc in rs:
            o += f"{1 + sum(1 for _, s2 in rs if s2 > sc)} {nm} {sc}\n"
        blocks.append(o)
    return "\n".join(blocks)
def v_e101(t):
    ls = body(t)
    T = int(ls[0])
    i = 1
    if not 1 <= T <= 50:
        return False
    for _ in range(T):
        n = int(ls[i]); i += 1
        if not 1 <= n <= 100:
            return False
        for l in ls[i:i + n]:
            p = l.split()
            if len(p) != 2 or not p[0].isalpha() or not 0 <= int(p[1]) <= 100:
                return False
        i += n
    return i == len(ls)
Q("e101", b_e101, g, v_e101,
  wrong=[pt("sum(1 for x in rows if x[1]>b)+1", "rows.index((a,b))+1"), pt("if k>1: print()", "print()"), pt("key=lambda r:(-r[1],r[0])", "key=lambda r:(-r[1])")])

# e102
def score(s):
    return (len(s) >= 8) + any(c.islower() for c in s) + any(c.isupper() for c in s) + any(c.isdigit() for c in s) + any(c in "!@#$%^&*" for c in s)
def g(r):
    pool = LOW + UP + "0123456789" + "!@#$%^&*" + "-_~"
    return "".join("".join(r.choice(r.choice([LOW, UP, "01", "!@", pool])) for _ in range(r.randint(1, 12))) + "\n" for _ in range(r.randint(1, 5)))
def b_e102(t):
    o = ""
    for l in body(t):
        sc = score(l)
        o += f"{sc} {'STRONG' if sc == 5 else 'MEDIUM' if sc >= 3 else 'WEAK'}\n"
    return o
Q("e102", b_e102, g,
  lambda t: all(1 <= len(l) <= 50 and " " not in l for l in body(t)) and body(t) != [],
  wrong=[pt("len(s)>=8", "len(s)>8"), pt("sc>=3", "sc>3"), pt("'!@#$%^&*'", "'!@#$%^&'"), pt("c.isdigit()", "c.isalnum()")])

# e103
def b_e103(t):
    o = ""
    for l in body(t):
        a, b = l.split()
        f = lambda s: int(s[:2]) * 60 + int(s[3:])
        d = f(b) - f(a)
        fee = 0 if d <= 30 else min(200, 20 * math.ceil((d - 30) / 30))
        o += f"{fee}\n"
    return o
def g(r):
    out = []
    for _ in range(r.randint(1, 5)):
        a = r.randint(0, 23 * 60)
        d = r.choice([0, 1, 30, 31, 60, 61, 90, 91, 300, 600, 1000, r.randint(0, 600)])
        b = min(a + d, 24 * 60 - 1)
        out.append(f"{a // 60:02d}:{a % 60:02d} {b // 60:02d}:{b % 60:02d}")
    return "\n".join(out) + "\n"
Q("e103", b_e103, g,
  lambda t: all(len(l.split()) == 2 and all(len(x) == 5 and x[2] == ":" for x in l.split()) for l in body(t)) and body(t) != [] and all(l.split()[0] <= l.split()[1] for l in body(t)),
  wrong=[pt("((d-30+29)//30)*20", "((d-30)//30)*20"), pt("min(200,", "min(220,"), pt("((d-30+29)//30)*20", "((d+29)//30)*20")])
