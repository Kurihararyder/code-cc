"""2.8.0 新增練習題（drills_n.py）的品質檢查登記。"""
import itertools
import math
import random
from collections import Counter, deque

from qa import Q, pt, code, ints, sp, L, word, nums, toks, rows, inrange
from qa_s0 import body, mix, LOW, UP


def one_int_lines(t):
    return all(len(l.split()) == 1 for l in body(t)) and body(t) != []


# ---------- d096 ----------
def g(r):
    return "".join(f"{mix(r, [0, 59, 60, 3599, 3600, 10**9], 0, 200000)}\n" for _ in range(r.randint(1, 6)))
def b(t):
    o = ""
    for x in body(t):
        s = int(x)
        h = 0
        while s >= 3600:
            s -= 3600; h += 1
        m = 0
        while s >= 60:
            s -= 60; m += 1
        o += f"{h} {m} {s}\n"
    return o
Q("d096", b, g, lambda t: one_int_lines(t) and all(0 <= int(x) <= 10**9 for x in body(t)),
  wrong=[pt("s%3600//60", "s//60"), pt("s%60", "s%3600"), pt("s//3600,s%3600//60,s%60", "s//3600,s//60%60,s"), pt("s//3600", "s//3600+1")])

# ---------- d097 ----------
def b(t):
    o = ""
    for x in body(t):
        n = int(x)
        best = None
        for a in range(n // 50 + 1):
            for b_ in range((n - 50 * a) // 10 + 1):
                for c in range((n - 50 * a - 10 * b_) // 5 + 1):
                    d = n - 50 * a - 10 * b_ - 5 * c
                    tot = (a + b_ + c + d, -a, -b_, -c)
                    if best is None or tot < best[0]:
                        best = (tot, (a, b_, c, d))
        o += sp(best[1]) + "\n"
    return o
def g(r):
    return "".join(f"{mix(r, [1, 4, 5, 9, 10, 49, 50, 99, 100], 1, 150)}\n" for _ in range(r.randint(1, 5)))
Q("d097", b, g, lambda t: one_int_lines(t) and all(1 <= int(x) <= 10**6 for x in body(t)),
  wrong=[pt("for c in (50,10,5,1)", "for c in (50,5,10,1)"), pt("o.append(n//c);n%=c", "o.append(n//c)"), pt("(50,10,5,1)", "(10,50,5,1)")])

# ---------- d098 ----------
def b(t):
    o = ""
    for l in body(t):
        a, b_, c = nums(l)
        if not (a + b_ > c and a + c > b_ and b_ + c > a):
            o += "NOT\n"
        else:
            o += {1: "EQUILATERAL", 2: "ISOSCELES", 3: "SCALENE"}[len({a, b_, c})] + "\n"
    return o
def g(r):
    return "".join(sp([mix(r, [1, 10**9], 1, 6) for _ in range(3)]) + "\n" for _ in range(r.randint(1, 5)))
Q("d098", b, g, lambda t: all(len(l.split()) == 3 and inrange(nums(l), 1, 10**9) for l in body(t)) and body(t) != [],
  wrong=[pt("s[0]+s[1]<=s[2]", "s[0]+s[1]<s[2]"), pt("s[0]==s[2]", "s[0]==s[1]"), pt("elif s[0]==s[1] or s[1]==s[2]: print('ISOSCELES')", "elif s[0]==s[1]: print('ISOSCELES')"), pt("s=sorted(map(int,p))", "s=list(map(int,p))")])

# ---------- d099 ----------
def b(t):
    o = ""
    for x in body(t):
        w = int(x)
        fee = 60
        rem = w - 1000
        while rem > 0:
            fee += 25
            rem -= 500
        o += f"{fee}\n"
    return o
def g(r):
    return "".join(f"{mix(r, [1, 1000, 1001, 1500, 1501, 2000, 2001], 1, 5000)}\n" for _ in range(r.randint(1, 6)))
Q("d099", b, g, lambda t: one_int_lines(t) and all(1 <= int(x) <= 10**6 for x in body(t)),
  wrong=[pt("w<=1000", "w<=1001"), pt("(w-1000+499)//500", "(w-1000)//500"), pt("(w-1000+499)//500", "(w-1000+500)//500"), pt("60+((", "50+((")])

# ---------- d100 ----------
def steps(n):
    return 0 if n == 1 else 1 + steps(n // 2 if n % 2 == 0 else 3 * n + 1)
def g(r):
    return "".join(f"{mix(r, [1, 2, 3, 27, 97], 1, 300)}\n" for _ in range(r.randint(1, 6)))
Q("d100", lambda t: "".join(f"{steps(int(x))}\n" for x in body(t)), g,
  lambda t: one_int_lines(t) and all(1 <= int(x) <= 10**6 for x in body(t)) and 1 <= len(body(t)) <= 1000,
  wrong=[pt("n//2 if n%2==0 else 3*n+1", "n//2 if n%2==0 else 3*n"), pt("c=0", "c=1"), pt("3*n+1", "3*n+2")])

# ---------- d101 ----------
def b(t):
    n = int(t)
    o = ""
    for i in range(1, n + 1):
        s = ""
        if i % 3 == 0:
            s += "Fizz"
        if i % 5 == 0:
            s += "Buzz"
        o += (s or str(i)) + "\n"
    return o
Q("d101", b, lambda r: f"{r.randint(1, 40)}\n", lambda t: len(body(t)) == 1 and 1 <= int(t) <= 100,
  wrong=[pt("i%15==0", "i%3==0 and i%5==1"), pt("'FizzBuzz' if i%15==0 else 'Fizz' if i%3==0 else 'Buzz' if i%5==0 else i", "'Fizz' if i%3==0 else 'Buzz' if i%5==0 else 'FizzBuzz' if i%15==0 else i"), pt("range(1,n+1)", "range(1,n)")], space=100)

# ---------- d102 ----------
def b(t):
    o = ""
    for l in body(t):
        words = l.split(" ")
        o += " ".join("".join(reversed(w)) for w in words) + "\n"
    return o
def g(r):
    return "".join(" ".join(word(r, 1, 6, LOW + "AB12") for _ in range(r.randint(1, 4))) + "\n" for _ in range(r.randint(1, 4)))
Q("d102", b, g,
  lambda t: all(1 <= len(l) <= 1000 and l == " ".join(l.split(" ")) and "" not in l.split(" ") and all(c.isalnum() or c == " " for c in l) for l in body(t)) and body(t) != [],
  wrong=[pt("' '.join(w[::-1] for w in l.split())", "l[::-1]"), pt("' '.join(w[::-1] for w in l.split())", "' '.join(l.split()[::-1])"), pt("' '.join(w[::-1] for w in l.split())", "''.join(w[::-1] for w in l.split())")])

# ---------- d103 ----------
def b(t):
    a = nums(body(t)[1])
    m1 = max(a)
    rest = [x for x in a if x != m1]
    return (str(max(rest)) if rest else "NONE") + "\n"
def g(r):
    n = r.randint(1, 7)
    return f"{n}\n{sp(ints(r, n, -4, 4))}\n"
Q("d103", b, g, lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 10**5 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), -10**9, 10**9),
  wrong=[pt("s[-2] if len(s)>=2 else 'NONE'", "s[-2] if len(s)>2 else 'NONE'"), pt("sorted(set(", "sorted((")  , pt("'NONE'", "s[-1]")],
  big=[lambda r: "20000\n" + sp(ints(r, 20000, -10**9, 10**9)) + "\n"])

# ---------- d104 ----------
def b(t):
    a, c = body(t)
    A, C = set(map(int, a.split())), set(map(int, c.split()))
    i = sorted(x for x in A if x in C)
    u = sorted(A | C)
    return (sp(i) if i else "EMPTY") + "\n" + sp(u) + "\n"
def g(r):
    return sp(ints(r, r.randint(1, 6), -4, 4)) + "\n" + sp(ints(r, r.randint(1, 6), -4, 4)) + "\n"
Q("d104", b, g, lambda t: len(body(t)) == 2 and all(1 <= len(nums(x)) <= 100 and inrange(nums(x), -1000, 1000) for x in body(t)),
  wrong=[pt("x=sorted(a&b)", "x=sorted(a|b)"), pt("print(*x if x else ['EMPTY'])", "print(*x)"), pt("print(*sorted(a|b))", "print(*sorted(a-b))"), pt("print(*sorted(a|b))", "print(*sorted(a|b)[::-1])")])

# ---------- d105 ----------
def b(t):
    ls = body(t)
    n = int(ls[0])
    tot, cnt = {}, Counter()
    for l in ls[1:1 + n]:
        a, s, sc = l.split()
        tot[a] = tot.get(a, 0) + int(sc)
        cnt[a] += 1
    names = sorted(tot, key=lambda x: [ord(c) for c in x])
    return "".join(f"{a} {tot[a]} {cnt[a]}\n" for a in names)
def g(r):
    n = r.randint(1, 8)
    names = ["amy", "Bob", "bob", "cat", "Amy"]
    used = set()
    out = []
    for i in range(n):
        a = r.choice(names)
        s = word(r, 2, 4, "xyz")
        if (a, s) in used:
            continue
        used.add((a, s))
        out.append(f"{a} {s} {r.randint(0, 100)}")
    return f"{len(out)}\n" + "\n".join(out) + "\n"
def v(t):
    ls = body(t)
    n = int(ls[0])
    seen = set()
    for l in ls[1:]:
        p = l.split()
        if len(p) != 3 or not p[0].isalpha() or not p[1].isalpha() or not 0 <= int(p[2]) <= 100 or (p[0], p[1]) in seen:
            return False
        seen.add((p[0], p[1]))
    return 1 <= n <= 10**5 and len(ls) == n + 1
Q("d105", b, g, v,
  wrong=[pt("sorted(m)", "sorted(m,key=str.lower)"), pt("print(a,m[a][0],m[a][1])", "print(a,m[a][0],m[a][0]//m[a][1])"), pt("t=m.setdefault(a,[0,0]);t[0]+=s;t[1]+=1", "t=m.setdefault(a,[0,0]);t[0]=s;t[1]+=1"), pt("sorted(m)", "sorted(m,reverse=True)")])

# ---------- d106 ----------
def b(t):
    o = ""
    for x in body(t):
        n = int(x)
        fs = []
        p = 2
        while n > 1:
            if n % p == 0:
                e = 0
                while n % p == 0:
                    n //= p; e += 1
                fs.append(f"{p}^{e}")
            p += 1
        o += " ".join(fs) + "\n"
    return o
def g(r):
    return "".join(f"{mix(r, [2, 3, 4, 8, 9, 97, 100, 1024, 9973], 2, 3000)}\n" for _ in range(r.randint(1, 5)))
Q("d106", b, g, lambda t: one_int_lines(t) and all(2 <= int(x) <= 10**12 for x in body(t)) and 1 <= len(body(t)) <= 10,
  wrong=[pt("if n>1: o.append(f'{n}^1')", "pass"), pt("while i*i<=n:", "while i*i<n:"), pt("f'{i}^{e}'", "f'{i}^{e}' if e>1 else str(i)"), pt("print(' '.join(o))", "print(' * '.join(o))")])

# ---------- d107 ----------
def b(t):
    o = ""
    for l in body(t):
        n = int(l)
        c = 0
        while n >= 10:
            tot = 0
            while n:
                tot += n % 10
                n //= 10
            n = tot
            c += 1
        o += f"{n} {c}\n"
    return o
def g(r):
    return "".join(str(r.choice([0, 9, 10, 99, 199, r.randint(0, 10**r.randint(1, 30))])) + "\n" for _ in range(r.randint(1, 4)))
Q("d107", b, g, lambda t: all(l.isdigit() and len(l) <= 1000 and (l == "0" or l[0] != "0") for l in body(t)) and body(t) != [],
  wrong=[pt("while len(s)>1:", "while len(s)>=1 and int(s)>=10 and c<1:"), pt("c=0", "c=1"), pt("print(s,c)", "print(int(l)%9 or 9,c)")],
  big=[lambda r: "9" * 1000 + "\n" + "1" + "0" * 999 + "\n"])

# ---------- d108 ----------
def b(t):
    ls = body(t)
    n = int(ls[0])
    a = [nums(x) for x in ls[1:1 + n]]
    m = a_ = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                m += a[i][j]
            if i + j == n - 1:
                a_ += a[i][j]
    return f"{m} {a_}\n"
def g(r):
    n = r.randint(1, 5)
    return f"{n}\n" + "".join(sp(ints(r, n, -9, 9)) + "\n" for _ in range(n))
Q("d108", b, g, lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 100 and all(len(nums(x)) == int(body(t)[0]) and inrange(nums(x), -10**4, 10**4) for x in body(t)[1:]),
  wrong=[pt("a[i][n-1-i]", "a[i][n-i-2]"), pt("a[i][i] for i in range(n)", "a[i][0] for i in range(n)"), pt("print(sum(a[i][i] for i in range(n)),sum(a[i][n-1-i] for i in range(n)))", "print(sum(a[i][n-1-i] for i in range(n)),sum(a[i][i] for i in range(n)))")])

# ---------- d109 ----------
def b(t):
    ls = body(t)
    r, c = nums(ls[0])
    g = ls[1:1 + r]
    o = ""
    for i in range(r):
        for j in range(c):
            if g[i][j] == "*":
                o += "*"
            else:
                o += str(sum(1 for x in range(r) for y in range(c) if max(abs(x - i), abs(y - j)) == 1 and g[x][y] == "*"))
        o += "\n"
    return o
def g(r):
    R_, C = r.randint(1, 5), r.randint(1, 5)
    return f"{R_} {C}\n" + "".join("".join("*" if r.random() < 0.35 else "." for _ in range(C)) + "\n" for _ in range(R_))
Q("d109", b, g, lambda t: len(body(t)) == 1 + nums(body(t)[0])[0] and 1 <= nums(body(t)[0])[0] <= 100 and 1 <= nums(body(t)[0])[1] <= 100 and all(len(x) == nums(body(t)[0])[1] and set(x) <= set("*.") for x in body(t)[1:]),
  wrong=[pt("for di in (-1,0,1):\n            for dj in (-1,0,1):", "for di in (-1,0,1):\n            for dj in (-1,1):"), pt("0<=i+di<r and 0<=j+dj<c and", "0<=i+di<r and"), pt("(di or dj) and ", "(di or dj) and (di==0 or dj==0) and ")],
  big=[])

# ---------- d110 ----------
def b(t):
    ls = body(t)
    r, c = nums(ls[0])
    a = [ls[1 + i].split() for i in range(r)]
    return "".join(" ".join(x) + "\n" for x in zip(*a[::-1]))
def g(r):
    R_, C = r.randint(1, 4), r.randint(1, 4)
    return f"{R_} {C}\n" + "".join(sp(ints(r, C, -9, 99)) + "\n" for _ in range(R_))
Q("d110", b, g, lambda t: len(body(t)) == 1 + nums(body(t)[0])[0] and 1 <= nums(body(t)[0])[0] <= 100 and 1 <= nums(body(t)[0])[1] <= 100 and all(len(nums(x)) == nums(body(t)[0])[1] and inrange(nums(x), -10**9, 10**9) for x in body(t)[1:]),
  wrong=[pt("a[r-1-i][j]", "a[i][c-1-j]"), pt("print(*[a[r-1-i][j] for i in range(r)])", "print(*[a[i][j] for i in range(r)])"), pt("print(*[a[r-1-i][j] for i in range(r)])", "print(*[a[r-1-i][c-1-j] for i in range(r)])")],
  big=[lambda r: "100 100\n" + "".join(sp(ints(r, 100, -10**9, 10**9)) + "\n" for _ in range(100))])


# =============================== 階段 1 ===============================
from fractions import Fraction
from drills_n import MORSE, grid01

# ---------- d111 ----------
def bmi_tie(w, h):
    x = Fraction(10000 * w, h * h) * 10
    return x - (x.numerator // x.denominator) == Fraction(1, 2)
def b(t):
    o = ""
    for l in body(t):
        w, h = nums(l)
        x = Fraction(10000 * w, h * h)
        q = (x * 10 * 2 + 1) // 2
        c = "UNDER" if x < Fraction(37, 2) else "NORMAL" if x < 24 else "OVER" if x < 27 else "OBESE"
        o += f"{q // 10}.{q % 10} {c}\n"
    return o
def g(r):
    out = []
    while len(out) < r.randint(1, 4):
        w, h = r.choice([74, 96, 108, r.randint(30, 200)]), r.choice([200, 100, r.randint(100, 220)])
        if not bmi_tie(w, h) and 30 <= w <= 200:
            out.append(f"{w} {h}")
    return "\n".join(out) + "\n"
Q("d111", b, g, lambda t: all(len(l.split()) == 2 and 30 <= nums(l)[0] <= 200 and 100 <= nums(l)[1] <= 220 and not bmi_tie(*nums(l)) for l in body(t)) and body(t) != [],
  wrong=[pt("w*20000<37*h2", "w*20000<=37*h2"), pt("w*10000<24*h2", "w*10000<=24*h2"), pt("w*10000<27*h2", "w*10000<=27*h2"), pt(":.1f", ":.2f"),
         pt("c='UNDER' if w*20000<37*h2 else 'NORMAL' if w*10000<24*h2 else 'OVER' if w*10000<27*h2 else 'OBESE'", "c='UNDER' if round(w*10000/h2,1)<18.5 else 'NORMAL' if round(w*10000/h2,1)<24 else 'OVER' if round(w*10000/h2,1)<27 else 'OBESE'")])

# ---------- d112 ----------
def enc(s):
    return " / ".join(" ".join(MORSE[c] for c in w) for w in s.split(" "))
def b(t):
    inv = {v: k for k, v in MORSE.items()}
    o = ""
    for l in body(t):
        words, cur, out = [], "", []
        for tok in l.split(" "):
            if tok == "/":
                words.append("".join(out)); out = []
            else:
                out.append(inv[tok])
        words.append("".join(out))
        o += " ".join(words) + "\n"
    return o
def g(r):
    al = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(enc(" ".join("".join(r.choice(al) for _ in range(r.randint(1, 4))) for _ in range(r.randint(1, 3)))) + "\n" for _ in range(r.randint(1, 3)))
Q("d112", b, g, lambda t: all(0 < len(l) <= 1000 and set(l) <= set(".- /") and "  " not in l and not l.startswith(" ") and not l.endswith(" ") for l in body(t)) and body(t) != [],
  wrong=[pt("''.join(M[c] for c in w.split())", "''.join(M[c] for c in w.split())[::-1]"), pt("' '.join(", "''.join(")],
  nrand=8)

# ---------- d113 ----------
Q("d113", lambda t: "".join(f"{sum(int(c) for c in str(math.factorial(int(x))))}\n" for x in body(t)),
  lambda r: "".join(f"{mix(r, [0, 1, 1000, 999], 0, 60)}\n" for _ in range(r.randint(1, 4))),
  lambda t: one_int_lines(t) and all(0 <= int(x) <= 1000 for x in body(t)) and 1 <= len(body(t)) <= 100,
  wrong=[pt("range(2,int(l)+1)", "range(2,int(l))"), pt("f=1", "f=0"), pt("print(sum(map(int,str(f))))", "print(len(str(f)))")],
  big=[lambda r: "".join(f"{n}\n" for n in range(901, 1001))])

# ---------- d114 ----------
def b(t):
    o = ""
    for l in body(t):
        a, b_ = map(int, l.split())
        c = k = 0
        while a or b_ or c:
            s = a % 10 + b_ % 10 + c
            c = s // 10
            k += c
            a //= 10; b_ //= 10
        o += f"{k}\n"
    return o
def g(r):
    return "".join(f"{r.choice([0, 9, 99, 5, r.randint(0, 10**r.randint(1, 8))])} {r.choice([0, 1, 9, 99, 5, r.randint(0, 10**r.randint(1, 8))])}\n" for _ in range(r.randint(1, 4)))
Q("d114", b, g, lambda t: all(len(l.split()) == 2 and all(x.isdigit() and len(x) <= 30 and (x == "0" or x[0] != "0") for x in l.split()) for l in body(t)) and body(t) != [],
  wrong=[pt("c=1 if s>=10 else 0;k+=c", "c=0;k+=1 if s>=10 else 0"), pt("s>=10", "s>10"), pt("n=max(len(a),len(b))", "n=min(len(a),len(b))"), pt("+c\n", "\n")])

# ---------- d115 ----------
def b(t):
    o = ""
    for l in body(t):
        x = int(l) + 1
        while str(x) != str(x)[::-1]:
            x += 1
        o += f"{x}\n"
    return o
def g(r):
    return "".join(f"{r.choice([1, 9, 10, 11, 99, 100, 998, 999, 1000, r.randint(1, 200000)])}\n" for _ in range(r.randint(1, 5)))
Q("d115", b, g, lambda t: one_int_lines(t) and all(1 <= int(x) <= 10**18 for x in body(t)) and 1 <= len(body(t)) <= 1000,
  wrong=[pt("x=int(l)+1", "x=int(l)"), pt("h=str(int(h)+1)", "h=h"), pt("c=h+h[:L//2][::-1]\n    if", "c=h+h[::-1]\n    if"), pt("x=int(l)+1;s=str(x)", "x=int(l)+2;s=str(x)")],
  big=[lambda r: "".join(f"{x}\n" for x in [10**18, 10**18 - 1, 123456789987654321, 99999999999999999, 12345678901234567, 1000000000000000000, 999999999999999999, 100000000000000000, 8999999999999999])])

# ---------- d116 ----------
def isp(n):
    return n > 1 and all(n % p for p in range(2, int(n ** 0.5) + 1))
def b(t):
    o = ""
    for l in body(t):
        n = int(l)
        p = next(p for p in range(2, n) if isp(p) and isp(n - p))
        o += f"{n} = {p} + {n - p}\n"
    return o
def g(r):
    return "".join(f"{2 * mix(r, [2, 3, 4, 5, 50], 2, 150)}\n" for _ in range(r.randint(1, 5)))
Q("d116", b, g, lambda t: one_int_lines(t) and all(4 <= int(x) <= 10**6 and int(x) % 2 == 0 for x in body(t)) and 1 <= len(body(t)) <= 10000,
  wrong=[pt("range(2,n//2+1)", "range(2,n//2)"), pt("range(2,n//2+1)", "range(n//2,1,-1)"), pt("sv[p] and sv[n-p]", "sv[p] or sv[n-p]")],
  big=[lambda r: "".join(f"{2 * r.randint(2, 500000)}\n" for _ in range(10000)), lambda r: "".join(f"{x}\n" for x in range(999000, 1000001, 2))])

# ---------- d117 ----------
def b(t):
    o = ""
    for l in body(t):
        n = int(l)
        s = sum(d for d in range(1, n) if n % d == 0)
        o += ("PERFECT" if s == n else "ABUNDANT" if s > n else "DEFICIENT") + "\n"
    return o
def g(r):
    return "".join(f"{mix(r, [1, 2, 6, 28, 12, 16, 496], 1, 600)}\n" for _ in range(r.randint(1, 5)))
Q("d117", b, g, lambda t: one_int_lines(t) and all(1 <= int(x) <= 10**6 for x in body(t)) and 1 <= len(body(t)) <= 2000,
  wrong=[pt("s-=n", "pass"), pt("if i!=n//i: s+=n//i", "s+=n//i"), pt("while i*i<=n:", "while i*i<n:")],
  slow=[code("import sys\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l)\n        s=sum(d for d in range(1,n) if n%d==0)\n        print('PERFECT' if s==n else 'ABUNDANT' if s>n else 'DEFICIENT')\n", "逐一試除到 n")],
  big=[lambda r: "".join(f"{r.randint(900000, 10**6)}\n" for _ in range(2000)), lambda r: "".join(f"{x}\n" for x in [720720, 1000000, 999999, 524288, 997, 960960, 999983] * 280)])

# ---------- d118 ----------
def b(t):
    ls = body(t)
    o = ""
    for x in ls[1:]:
        n = int(x)
        o += f"{sum(1 for p in range(2, n - 1) if p + 2 <= n and isp(p) and isp(p + 2))}\n"
    return o
def g(r):
    q = r.randint(1, 5)
    return f"{q}\n" + "".join(f"{mix(r, [1, 2, 4, 5, 7, 13], 1, 200)}\n" for _ in range(q))
Q("d118", b, g, lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 10**5 and all(1 <= int(x) <= 10**6 for x in body(t)[1:]),
  wrong=[pt("sv[k] and sv[k-2]", "sv[k] and sv[k-2] and k>5"), pt("k>=2 and sv[k] and sv[k-2]", "k>=3 and sv[k] and sv[k-1]"), pt("tw[k]=tw[k-1]+(", "tw[k]=tw[k-2 if k>1 else 0]+(")],
  big=[lambda r: "30000\n" + "".join(f"{r.randint(1, 10**6)}\n" for _ in range(30000))])

# ---------- d119 ----------
def roll_full(cmds):
    f = {"T": 1, "B": 6, "N": 2, "S": 5, "E": 3, "W": 4}
    for c in cmds:
        T, B_, N_, S_, E_, W_ = f["T"], f["B"], f["N"], f["S"], f["E"], f["W"]
        if c == "N":
            f.update(T=S_, N=T, B=N_, S=B_)
        elif c == "S":
            f.update(T=N_, S=T, B=S_, N=B_)
        elif c == "E":
            f.update(T=W_, E=T, B=E_, W=B_)
        elif c == "W":
            f.update(T=E_, W=T, B=W_, E=B_)
    return f["T"]
def g(r):
    return "".join("".join(r.choice("NSEW") for _ in range(r.randint(0, 8))) + "\n" for _ in range(r.randint(1, 4)))
Q("d119", lambda t: "".join(f"{roll_full(l)}\n" for l in body(t)), g,
  lambda t: all(len(l) <= 10**5 and set(l) <= set("NSEW") for l in body(t)) and body(t) != [],
  wrong=[pt("if c=='N': t,n=7-n,t", "if c=='N': t,n=n,7-t"), pt("elif c=='E': t,e=7-e,t", "elif c=='E': t,e=e,7-t"), pt("elif c=='W': t,e=e,7-t", "elif c=='W': t,e=7-e,t"), pt("elif c=='S': t,n=n,7-t", "elif c=='S': t,n=7-n,t"), pt("t,n,e=1,2,3", "t,n,e=1,2,4")],
  big=[lambda r: "".join(r.choice("NSEW") for _ in range(100000)) + "\n"], nrand=8)

# ---------- d120 ----------
def b(t):
    ls = body(t)
    r_, c_ = nums(ls[0])
    g_ = ls[1:1 + r_]
    w = ls[1 + r_]
    cnt = 0
    for i in range(r_):
        for j in range(c_):
            for di, dj in itertools.product((-1, 0, 1), repeat=2):
                if (di, dj) == (0, 0):
                    continue
                s = ""
                x, y = i, j
                while 0 <= x < r_ and 0 <= y < c_ and len(s) < len(w):
                    s += g_[x][y]
                    x += di; y += dj
                if s == w:
                    cnt += 1
    return f"{cnt}\n"
def g(r):
    R_, C = r.randint(1, 5), r.randint(1, 5)
    grid = ["".join(r.choice("ab") for _ in range(C)) for _ in range(R_)]
    return f"{R_} {C}\n" + "\n".join(grid) + "\n" + word(r, 2, 4, "ab") + "\n"
def v(t):
    ls = body(t)
    r_, c_ = nums(ls[0])
    return 1 <= r_ <= 50 and 1 <= c_ <= 50 and len(ls) == r_ + 2 and all(len(x) == c_ and x.islower() for x in ls[1:1 + r_]) and 2 <= len(ls[-1]) <= 50 and ls[-1].islower()
Q("d120", b, g, v,
  wrong=[pt("for di in (-1,0,1):\n            for dj in (-1,0,1):", "for di in (0,1):\n            for dj in (-1,0,1):"), pt("ei,ej=i+di*(L-1),j+dj*(L-1)", "ei,ej=i+di*L,j+dj*L"), pt("k+=1\nprint(k)", "k+=1\nprint(k//2 if w==w[::-1] else k)")],
  nrand=8)

# ---------- d121 ----------
def b(t):
    n = int(t)
    cells = sorted(((i, j) for i in range(n) for j in range(n)), key=lambda p: (p[0] + p[1], p[0]))
    a = [[0] * n for _ in range(n)]
    for k, (i, j) in enumerate(cells, 1):
        a[i][j] = k
    return "".join(sp(r_) + "\n" for r_ in a)
Q("d121", b, lambda r: f"{r.randint(1, 8)}\n", lambda t: len(body(t)) == 1 and 1 <= int(t) <= 50,
  wrong=[pt("for i in range(n):\n        j=s-i", "for i in range(n-1,-1,-1):\n        j=s-i"), pt("a[i][j]=k;k+=1", "a[j][i]=k;k+=1"), pt("range(2*n-1)", "range(2*n-2)")], space=50)

# ---------- d122 ----------
def daynum(y, m, d):
    dm = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    leap = lambda yy: (yy % 4 == 0 and yy % 100 != 0) or yy % 400 == 0
    n = sum(366 if leap(yy) else 365 for yy in range(1900, y))
    n += sum(dm[:m - 1]) + (1 if m > 2 and leap(y) else 0) + d
    return n
def b(t):
    return "".join(f"{abs(daynum(*nums(l)[:3]) - daynum(*nums(l)[3:]))}\n" for l in body(t))
def g(r):
    out = []
    for _ in range(r.randint(1, 3)):
        a = datetime_date(r)
        c = datetime_date(r)
        out.append(f"{a[0]} {a[1]} {a[2]} {c[0]} {c[1]} {c[2]}")
    return "\n".join(out) + "\n"
def datetime_date(r):
    import datetime
    d = datetime.date(1900, 1, 1) + datetime.timedelta(days=r.choice([r.randint(0, 73000), r.randint(0, 800), r.randint(36000, 37000)]))
    return d.year, d.month, d.day
def v(t):
    import datetime
    for l in body(t):
        p = nums(l)
        if len(p) != 6:
            return False
        try:
            a, c = datetime.date(*p[:3]), datetime.date(*p[3:])
        except ValueError:
            return False
        if not (1900 <= a.year <= 2100 and 1900 <= c.year <= 2100):
            return False
    return body(t) != []
Q("d122", b, g, v,
  wrong=[pt("print(abs((datetime.date(*p[:3])-datetime.date(*p[3:])).days))", "print((datetime.date(*p[:3])-datetime.date(*p[3:])).days)"), pt("print(abs((datetime.date(*p[:3])-datetime.date(*p[3:])).days))", "print(abs((datetime.date(*p[:3])-datetime.date(*p[3:])).days)+1)"),
         code("import sys\nfor l in sys.stdin:\n    p=list(map(int,l.split()))\n    if len(p)==6:\n        f=lambda y,m,d:y*365+y//4+sum([31,28,31,30,31,30,31,31,30,31,30,31][:m-1])+d\n        print(abs(f(*p[:3])-f(*p[3:])))\n", "閏年規則只看 4 的倍數、而且沒處理當年 2 月")],
  nrand=8)

# ---------- d123 ----------
def b(t):
    o = ""
    for l in body(t):
        h, m = int(l[:2]), int(l[3:])
        ha = Fraction(h % 12) * 30 + Fraction(m, 2)
        ma = Fraction(m * 6)
        d = abs(ha - ma)
        d = min(d, 360 - d)
        o += f"{float(d):.1f}\n"
    return o
def g(r):
    return "".join(f"{r.choice([0, 3, 6, 9, 12, 15, 23, r.randint(0, 23)]):02d}:{r.choice([0, 15, 30, 45, 59, r.randint(0, 59)]):02d}\n" for _ in range(r.randint(1, 5)))
Q("d123", b, g, lambda t: all(len(l) == 5 and l[2] == ":" and 0 <= int(l[:2]) <= 23 and 0 <= int(l[3:]) <= 59 for l in body(t)) and body(t) != [],
  wrong=[pt("d=min(d,720-d)", "pass"), pt("(h%12)*60", "h*60"), pt("f'{d/2:.1f}'", "f'{d//2:.1f}'")],
  space=1440, nrand=12)

# ---------- d124 ----------
def b(t):
    o = ""
    for l in body(t):
        st = []
        for x in l.split():
            if x in "+-*" and len(x) == 1:
                right, left = st.pop(), st.pop()
                st.append(f"({left}{x}{right})")
            else:
                st.append(x)
        o += f"{eval(st[0])}\n"
    return o
def g(r):
    out = []
    for _ in range(r.randint(1, 3)):
        toks = [str(r.randint(0, 9))]
        depth = 1
        for _ in range(r.randint(0, 6)):
            toks += [str(r.randint(0, 9)), r.choice("+-*")]
        out.append(" ".join(toks))
    return "\n".join(out) + "\n"
Q("d124", b, g, lambda t: all(1 <= len(l.split()) <= 1000 for l in body(t)) and body(t) != [],
  wrong=[pt("b=st.pop();a=st.pop();", "a=st.pop();b=st.pop();"), pt("a-b if x=='-'", "b-a if x=='-'")],
  nrand=8)


# =============================== 階段 2 ===============================
from functools import cmp_to_key

# ---------- d125 ----------
def b(t):
    a = sorted(nums(body(t)[1]))
    n = len(a)
    if n % 2:
        return f"{a[n // 2]}\n"
    s = Fraction(a[n // 2 - 1] + a[n // 2], 2)
    return (f"{int(s)}\n" if s.denominator == 1 else f"{'-' if s < 0 else ''}{abs(s.numerator) // 2}.5\n")
def g(r):
    n = r.randint(1, 8)
    return f"{n}\n{sp(ints(r, n, -9, 9))}\n"
Q("d125", b, g, lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 2 * 10**5 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), -10**9, 10**9),
  wrong=[pt("print(s//2 if s%2==0 else f'{s/2:.1f}')", "print(s/2)"), pt("a=sorted(map(int,input().split()))", "a=list(map(int,input().split()))"), pt("a[n//2-1]+a[n//2]", "a[n//2]+a[n//2]"), pt("print(a[n//2])", "print(a[n//2-1])"), pt("s//2 if s%2==0", "s//2 if s%2==0 and s>=0")],
  big=[lambda r: "30000\n" + sp(ints(r, 30000, -10**9, 10**9)) + "\n"])

# ---------- d126 ----------
def b(t):
    ls = body(t)
    n = int(ls[0])
    rs = [(l.split()[0], int(l.split()[1]), int(l.split()[2])) for l in ls[1:1 + n]]
    def cmp(x, y):
        if x[2] != y[2]:
            return -1 if x[2] > y[2] else 1
        if x[1] != y[1]:
            return -1 if x[1] < y[1] else 1
        return -1 if x[0] < y[0] else (1 if x[0] > y[0] else 0)
    rs.sort(key=cmp_to_key(cmp))
    return "".join(f"{a} {b_} {c}\n" for a, b_, c in rs)
def g(r):
    n = r.randint(1, 7)
    return f"{n}\n" + "".join(f"{word(r, 1, 2, 'aAb')} {r.randint(18, 20)} {r.randint(0, 3)}\n" for _ in range(n))
Q("d126", b, g, lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 10**5 and all(len(l.split()) == 3 and l.split()[0].isalpha() and len(l.split()[0]) <= 10 and 1 <= int(l.split()[1]) <= 120 and 0 <= int(l.split()[2]) <= 1000 for l in body(t)[1:]),
  wrong=[pt("(-r[2],r[1],r[0])", "(-r[2],-r[1],r[0])"), pt("(-r[2],r[1],r[0])", "(-r[2],r[1])"), pt("(-r[2],r[1],r[0])", "(r[2],r[1],r[0])"), pt("(-r[2],r[1],r[0])", "(-r[2],r[1],r[0].lower())"), pt("(-r[2],r[1],r[0])", "(-r[2],r[0],r[1])")],
  big=[lambda r: "20000\n" + "".join(f"{word(r, 1, 4, 'abcAB')} {r.randint(18, 25)} {r.randint(0, 10)}\n" for _ in range(20000))])

# ---------- d128 ----------
def g(r):
    R_, C, q = r.randint(1, 4), r.randint(1, 4), r.randint(1, 5)
    qs = []
    for _ in range(q):
        a, c = sorted([r.randint(1, R_), r.randint(1, R_)])
        b_, e = sorted([r.randint(1, C), r.randint(1, C)])
        qs.append(f"{a} {b_} {c} {e}")
    return f"{R_} {C} {q}\n" + "".join(sp(ints(r, C, -9, 9)) + "\n" for _ in range(R_)) + "\n".join(qs) + "\n"
def b(t):
    ls = body(t)
    R_, C, q = nums(ls[0])
    a = [nums(x) for x in ls[1:1 + R_]]
    o = ""
    for l in ls[1 + R_:1 + R_ + q]:
        r1, c1, r2, c2 = nums(l)
        o += f"{sum(a[i][j] for i in range(r1 - 1, r2) for j in range(c1 - 1, c2))}\n"
    return o
def v(t):
    ls = body(t)
    R_, C, q = nums(ls[0])
    return 1 <= R_ <= 500 and 1 <= C <= 500 and 1 <= q <= 10**5 and len(ls) == 1 + R_ + q and all(len(nums(x)) == C and inrange(nums(x), -1000, 1000) for x in ls[1:1 + R_]) and all(len(nums(x)) == 4 and 1 <= nums(x)[0] <= nums(x)[2] <= R_ and 1 <= nums(x)[1] <= nums(x)[3] <= C for x in ls[1 + R_:])
def big128(r):
    R_ = C = 300
    q = 20000
    qs = []
    for _ in range(q):
        a = r.randint(1, 30); c = r.randint(270, 300); b_ = r.randint(1, 30); e = r.randint(270, 300)
        qs.append(f"{a} {b_} {c} {e}")
    return f"{R_} {C} {q}\n" + "".join(sp(ints(r, C, -1000, 1000)) + "\n" for _ in range(R_)) + "\n".join(qs) + "\n"
Q("d128", b, g, v,
  wrong=[pt("S[c][e]-S[a-1][e]-S[c][b-1]+S[a-1][b-1]", "S[c][e]-S[a-1][e]-S[c][b-1]"), pt("S[c][e]-S[a-1][e]-S[c][b-1]+S[a-1][b-1]", "S[c][e]-S[a][e]-S[c][b]+S[a][b]"), pt("S[i][j]=int(d[p])+S[i-1][j]+S[i][j-1]-S[i-1][j-1]", "S[i][j]=int(d[p])+S[i-1][j]+S[i][j-1]")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nR,C,q=int(d[0]),int(d[1]),int(d[2]);p=3\na=[]\nfor i in range(R):\n    a.append([int(x) for x in d[p:p+C]]);p+=C\nfor _ in range(q):\n    r1,c1,r2,c2=int(d[p]),int(d[p+1]),int(d[p+2]),int(d[p+3]);p+=4\n    print(sum(sum(a[i][c1-1:c2]) for i in range(r1-1,r2)))\n", "每個詢問逐列加總")],
  big=[big128])

# ---------- d129 ----------
def g(r):
    n = r.randint(1, 5)
    return f"{n} {r.randint(1, 12)}\n{sp(ints(r, n, 1, 15))}\n"
def b(t):
    ls = body(t)
    n, k = nums(ls[0])
    a = nums(ls[1])
    for L in range(max(a), 0, -1):
        if sum(x // L for x in a) >= k:
            return f"{L}\n"
    return "0\n"
Q("d129", b, g, lambda t: len(body(t)) == 2 and 1 <= nums(body(t)[0])[0] <= 10**5 and 1 <= nums(body(t)[0])[1] <= 10**9 and len(nums(body(t)[1])) == nums(body(t)[0])[0] and inrange(nums(body(t)[1]), 1, 10**9),
  wrong=[pt("lo,hi=0,max(a)", "lo,hi=1,max(a)"), pt("if sum(x//m for x in a)>=k: lo=m", "if sum(x//m for x in a)>k: lo=m"), pt("m=(lo+hi+1)//2", "m=(lo+hi)//2"), pt("lo,hi=0,max(a)", "lo,hi=0,max(a)-1")],
  slow=[code("n,k=map(int,input().split());a=list(map(int,input().split()))\nL=max(a)\nwhile L>0 and sum(x//L for x in a)<k: L-=1\nprint(L)\n", "從最大長度往下逐一試")],
  big=[lambda r: "30000 1000000000\n" + sp(ints(r, 30000, 1, 10**9)) + "\n", lambda r: "1 1\n1000000000\n", lambda r: "5 3\n1000000000 1000000000 1 1 1\n"])

# ---------- d130 ----------
def g(r):
    n, m = r.randint(1, 6), r.randint(1, 5)
    ops = []
    for _ in range(m):
        l = r.randint(1, n)
        ops.append(f"{l} {r.randint(l, n)} {r.randint(-5, 5)}")
    return f"{n} {m}\n" + "\n".join(ops) + "\n"
def b(t):
    ls = body(t)
    n, m = nums(ls[0])
    a = [0] * (n + 1)
    for l in ls[1:1 + m]:
        x, y, v_ = nums(l)
        for i in range(x, y + 1):
            a[i] += v_
    return sp(a[1:]) + "\n"
Q("d130", b, g, lambda t: len(body(t)) == 1 + nums(body(t)[0])[1] and 1 <= nums(body(t)[0])[0] <= 2 * 10**5 and 1 <= nums(body(t)[0])[1] <= 2 * 10**5 and all(len(nums(x)) == 3 and 1 <= nums(x)[0] <= nums(x)[1] <= nums(body(t)[0])[0] and abs(nums(x)[2]) <= 10**4 for x in body(t)[1:]),
  wrong=[pt("df[r+1]-=v", "df[r]-=v"), pt("df=[0]*(n+2)", "df=[0]*(n+1)"), pt("s+=df[i];o.append(s)", "o.append(df[i])")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1]);a=[0]*(n+1)\nfor i in range(m):\n    l,r,v=int(d[2+3*i]),int(d[3+3*i]),int(d[4+3*i])\n    for j in range(l,r+1): a[j]+=v\nprint(*a[1:])\n", "每個操作跑迴圈")],
  big=[lambda r: "30000 15000\n" + "\n".join(f"{r.randint(1, 5000)} {r.randint(25000, 30000)} {r.randint(-10**4, 10**4)}" for _ in range(15000)) + "\n"])

# ---------- d131 ----------
def g(r):
    n = r.randint(1, 8)
    return f"{n} {r.randint(1, 20)}\n{sp(ints(r, n, 1, 6))}\n"
def b(t):
    ls = body(t)
    n, S = nums(ls[0])
    a = nums(ls[1])
    best = 0
    for L in range(1, n + 1):
        if any(sum(a[i:i + L]) >= S for i in range(n - L + 1)):
            best = L
            break
    return f"{best}\n"
Q("d131", b, g, lambda t: len(body(t)) == 2 and 1 <= nums(body(t)[0])[0] <= 10**5 and 1 <= nums(body(t)[0])[1] <= 10**9 and len(nums(body(t)[1])) == nums(body(t)[0])[0] and inrange(nums(body(t)[1]), 1, 10**4),
  wrong=[pt("while s>=S:", "while s>S:"), pt("print(best if best<=n else 0)", "print(best)"), pt("s-=a[l];l+=1", "l+=1")],
  slow=[code("n,S=map(int,input().split());a=list(map(int,input().split()))\nbest=n+1\nfor i in range(n):\n    s=0\n    for j in range(i,n):\n        s+=a[j]\n        if s>=S:\n            best=min(best,j-i+1);break\nprint(best if best<=n else 0)\n", "O(n²) 枚舉")],
  big=[lambda r: "30000 150000000\n" + sp(ints(r, 30000, 1, 10000)) + "\n", lambda r: "30000 30000\n" + sp([1] * 30000) + "\n"])

# ---------- d132 ----------
def g(r):
    return "".join(word(r, 1, 10, "abc!") + "\n" for _ in range(r.randint(1, 4)))
def b(t):
    o = ""
    for s in body(t):
        best = 0
        for i in range(len(s)):
            seen = set()
            for j in range(i, len(s)):
                if s[j] in seen:
                    break
                seen.add(s[j])
                best = max(best, j - i + 1)
        o += f"{best}\n"
    return o
Q("d132", b, g, lambda t: all(1 <= len(l) <= 10**5 and all(33 <= ord(c) <= 126 for c in l) for l in body(t)) and 1 <= len(body(t)) <= 10,
  wrong=[pt("if c in last and last[c]>=l: l=last[c]+1", "if c in last: l=last[c]+1"), pt("l=last[c]+1", "l=last[c]"), pt("best=max(best,r-l+1)", "best=max(best,r-l)")],
  big=[lambda r: "".join(chr(33 + (i * 7) % 90) for i in range(100000)) + "\n" + "".join(r.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(100000)) + "\n"])

# ---------- d133 ----------
def g(r):
    n = r.randint(1, 8)
    return f"{n}\n{sp(ints(r, n, -4, 4))}\n"
def b(t):
    a = nums(body(t)[1])
    return sp([next((y for y in a[i + 1:] if y > a[i]), -1) for i in range(len(a))]) + "\n"
Q("d133", b, g, lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 2 * 10**5 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), -10**9, 10**9),
  wrong=[pt("while st and st[-1]<=a[i]: st.pop()", "while st and st[-1]<a[i]: st.pop()"), pt("res[i]=st[-1] if st else -1", "res[i]=st[-1] if st else 0"), pt("for i in range(n-1,-1,-1):", "for i in range(n):")],
  slow=[code("n=int(input());a=list(map(int,input().split()))\nres=[]\nfor i in range(n):\n    v=-1\n    for j in range(i+1,n):\n        if a[j]>a[i]: v=a[j];break\n    res.append(v)\nprint(*res)\n", "O(n²) 往右找")],
  big=[lambda r: "30000\n" + sp(range(30000, 0, -1)) + "\n", lambda r: "30000\n" + sp(ints(r, 30000, -10**9, 10**9)) + "\n"])

# ---------- d135 ----------
def reachable_orders(n):
    res = set()
    def go(nxt, st, out):
        if len(out) == n:
            res.add(tuple(out))
            return
        if nxt <= n:
            go(nxt + 1, st + [nxt], out)
        if st:
            go(nxt, st[:-1], out + [st[-1]])
    go(1, [], [])
    return res
_RO = {}
def g(r):
    t = r.randint(1, 3)
    out = [str(t)]
    for _ in range(t):
        n = r.randint(1, 6)
        p = list(range(1, n + 1))
        r.shuffle(p)
        out += [str(n), sp(p)]
    return "\n".join(out) + "\n"
def b(t):
    ls = body(t)
    T = int(ls[0])
    o = ""
    for k in range(T):
        n = int(ls[1 + 2 * k])
        p = tuple(nums(ls[2 + 2 * k]))
        if n not in _RO:
            _RO[n] = reachable_orders(n)
        o += ("YES" if p in _RO[n] else "NO") + "\n"
    return o
def v(t):
    ls = body(t)
    T = int(ls[0])
    if not 1 <= T <= 100 or len(ls) != 1 + 2 * T:
        return False
    tot = 0
    for k in range(T):
        n = int(ls[1 + 2 * k])
        tot += n
        if not (1 <= n <= 10**5 and sorted(nums(ls[2 + 2 * k])) == list(range(1, n + 1))):
            return False
    return tot <= 2 * 10**5
Q("d135", b, g, v,
  wrong=[pt("if st and st[-1]==x: st.pop()\n        else: ok=False;break", "if st: st.pop()\n        else: ok=False;break"), pt("print('YES' if ok else 'NO')", "print('YES')")],
  big=[lambda r: "2\n30000\n" + sp(range(1, 30001)) + "\n30000\n" + sp(range(30000, 0, -1)) + "\n", lambda r: "1\n30000\n" + sp((lambda p: (r.shuffle(p), p)[1])(list(range(1, 30001)))) + "\n"], nrand=8)

# ---------- d136 ----------
def g(r):
    n = r.randint(1, 8)
    return f"{n} {r.randint(1, n)}\n{sp(ints(r, n, -5, 5))}\n"
def b(t):
    ls = body(t)
    n, k = nums(ls[0])
    a = nums(ls[1])
    return sp([sorted(a[:i], reverse=True)[k - 1] for i in range(k, n + 1)]) + "\n"
Q("d136", b, g, lambda t: len(body(t)) == 2 and 1 <= nums(body(t)[0])[1] <= nums(body(t)[0])[0] <= 2 * 10**5 and len(nums(body(t)[1])) == nums(body(t)[0])[0] and inrange(nums(body(t)[1]), -10**9, 10**9),
  wrong=[pt("if x>h[0]: heapq.heapreplace(h,x)", "if x>h[0]: heapq.heappush(h,x)"), pt("h=a[:k];heapq.heapify(h)", "h=a[:k]"), pt("o=[h[0]]", "o=[]")],
  slow=[code("n,k=map(int,input().split());a=list(map(int,input().split()))\nprint(*[sorted(a[:i],reverse=True)[k-1] for i in range(k,n+1)])\n", "每次重新排序")],
  big=[lambda r: "30000 500\n" + sp(ints(r, 30000, -10**9, 10**9)) + "\n", lambda r: "30000 15000\n" + sp(range(30000)) + "\n"])

# ---------- d137 ----------
def g(r):
    n = r.randint(1, 8)
    return f"{n}\n{sp(ints(r, n, -5, 5))}\n"
def b(t):
    a = nums(body(t)[1])
    return sp([sorted(a[:i])[(i + 1) // 2 - 1] for i in range(1, len(a) + 1)]) + "\n"
Q("d137", b, g, lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 10**5 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), -10**9, 10**9),
  wrong=[pt("if len(hi)>len(lo): heapq.heappush(lo,-heapq.heappop(hi))", "pass"), pt("o.append(-lo[0])", "o.append(hi[0] if len(hi)>=len(lo) else -lo[0])"), pt("heapq.heappush(hi,-heapq.heappop(lo))", "heapq.heappush(hi,x)")],
  slow=[code("n=int(input());a=list(map(int,input().split()))\nprint(*[sorted(a[:i])[(i+1)//2-1] for i in range(1,n+1)])\n", "每次重新排序")],
  big=[lambda r: "30000\n" + sp(ints(r, 30000, -10**9, 10**9)) + "\n"])

# ---------- d138 ----------
def g(r):
    L = r.randint(1, 8)
    n = r.randint(1, 6)
    ivs = []
    for _ in range(n):
        l = r.randint(0, 8)
        ivs.append((l, r.randint(l + 1, 10)))
    return f"{L} {n}\n" + "".join(f"{l} {rr}\n" for l, rr in ivs)
def b(t):
    ls = body(t)
    L, n = nums(ls[0])
    iv = [tuple(nums(x)) for x in ls[1:1 + n]]
    best = None
    for m in range(1 << n):
        ch = sorted(iv[i] for i in range(n) if m >> i & 1)
        cur = 0
        ok = True
        for l, rr in ch:
            if l > cur:
                break
            cur = max(cur, rr)
        if cur >= L:
            c = len(ch)
            if best is None or c < best:
                best = c
    return f"{-1 if best is None else best}\n"
Q("d138", b, g, lambda t: len(body(t)) == 1 + nums(body(t)[0])[1] and 1 <= nums(body(t)[0])[0] <= 10**9 and 1 <= nums(body(t)[0])[1] <= 10**5 and all(len(nums(x)) == 2 and 0 <= nums(x)[0] < nums(x)[1] <= 10**9 for x in body(t)[1:]),
  wrong=[pt("iv[i][0]<=cur", "iv[i][0]<cur"), pt("if best==cur: c=-1;break", "if best==cur: break"), pt("cur=0;i=0;c=0", "cur=1;i=0;c=0"), pt("best=max(best,iv[i][1]);i+=1", "best=iv[i][1];i+=1")],
  big=[lambda r: "1000000000 20000\n" + "".join(f"{(l := r.randint(0, 10**9 - 2))} {min(10**9, l + r.randint(1, 100000000))}\n" for _ in range(20000)), lambda r: "20000 20000\n" + "".join(f"{i} {min(20000, i + 3)}\n" for i in range(20000))])

# ---------- d139 ----------
def g(r):
    n = r.randint(1, 7)
    W = r.randint(3, 12)
    return f"{n} {W}\n{sp(ints(r, n, 1, W))}\n"
def b(t):
    ls = body(t)
    n, W = nums(ls[0])
    w = nums(ls[1])
    from functools import lru_cache
    @lru_cache(None)
    def f(mask):
        if mask == (1 << n) - 1:
            return 0
        i = next(i for i in range(n) if not mask >> i & 1)
        best = 1 + f(mask | 1 << i)
        for j in range(i + 1, n):
            if not mask >> j & 1 and w[i] + w[j] <= W:
                best = min(best, 1 + f(mask | 1 << i | 1 << j))
        return best
    return f"{f(0)}\n"
Q("d139", b, g, lambda t: len(body(t)) == 2 and 1 <= nums(body(t)[0])[0] <= 10**5 and 1 <= nums(body(t)[0])[1] <= 10**9 and len(nums(body(t)[1])) == nums(body(t)[0])[0] and inrange(nums(body(t)[1]), 1, nums(body(t)[0])[1]),
  wrong=[pt("a[l]+a[r]<=W and l<r", "a[l]+a[r]<W and l<r"), pt("a=sorted(map(int,input().split()))", "a=list(map(int,input().split()))")],
  big=[lambda r: "30000 1000000000\n" + sp(ints(r, 30000, 1, 10**9)) + "\n"])

# ---------- d140 ----------
def g(r):
    n = r.randint(1, 6)
    return f"{n}\n{sp(ints(r, n, 1, 9))}\n"
def b(t):
    a = nums(body(t)[1])
    best = None
    for p in itertools.permutations(a):
        cur = tot = 0
        for x in p:
            tot += cur; cur += x
        if best is None or tot < best:
            best = tot
    return f"{best}\n"
Q("d140", b, g, lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 10**5 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), 1, 10**4),
  wrong=[pt("a=sorted(map(int,input().split()))", "a=sorted(map(int,input().split()),reverse=True)"), pt("for x in a: tot+=cur;cur+=x", "for x in a: cur+=x;tot+=cur"), pt("a=sorted(map(int,input().split()))", "a=list(map(int,input().split()))")],
  big=[lambda r: "30000\n" + sp([10000] * 30000) + "\n"])

# ---------- d141 ----------
def b(t):
    n = int(t)
    start = (tuple(range(n, 0, -1)), (), ())
    goal = ((), (), tuple(range(n, 0, -1)))
    names = "ABC"
    prev = {start: None}
    q = deque([start])
    while q:
        s = q.popleft()
        if s == goal:
            break
        for i in range(3):
            if not s[i]:
                continue
            for j in range(3):
                if i == j or (s[j] and s[j][-1] < s[i][-1]):
                    continue
                ns = list(s)
                ns[j] = s[j] + (s[i][-1],)
                ns[i] = s[i][:-1]
                ns = tuple(ns)
                if ns not in prev:
                    prev[ns] = (s, names[i] + " " + names[j])
                    q.append(ns)
    mv = []
    s = goal
    while prev[s]:
        s, m = prev[s]
        mv.append(m)
    mv.reverse()
    return f"{len(mv)}\n" + "\n".join(mv) + "\n"
Q("d141", b, lambda r: f"{r.randint(1, 4)}\n", lambda t: len(body(t)) == 1 and 1 <= int(t) <= 10,
  wrong=[pt("h(n,'A','C','B')", "h(n,'A','B','C')"), pt("h(k-1,a,b,c);mv.append(a+' '+c);h(k-1,b,c,a)", "h(k-1,a,b,c);mv.append(a+' '+c);h(k-1,a,c,b)"), pt("print(len(mv))\nprint('\\n'.join(mv))", "print(len(mv)+1)\nprint('\\n'.join(mv))")], space=10)

# ---------- d142 ----------
Q("d142", lambda t: "".join(sp(c) + "\n" for c in itertools.combinations(range(1, nums(t)[0] + 1), nums(t)[1])),
  lambda r: (lambda n: f"{n} {r.randint(1, n)}\n")(r.randint(1, 6)),
  lambda t: len(body(t)) == 1 and 1 <= nums(t)[1] <= nums(t)[0] <= 10,
  wrong=[pt("for x in range(s,n+1): go(x+1,cur+[x])", "for x in range(s,n): go(x+1,cur+[x])"), pt("for x in range(s,n+1): go(x+1,cur+[x])", "for x in range(1,n+1): go(x+1,cur+[x])"), pt("for x in range(s,n+1): go(x+1,cur+[x])", "for x in range(n,s-1,-1): go(x+1,cur+[x])")], space=55, nrand=10)

# ---------- d143 ----------
def b(t):
    o = ""
    for l in body(t):
        n = int(l)
        if n == 1:
            o += "1\n"
            continue
        if n % 2:
            o += "0\n"
            continue
        c = 0
        for p in itertools.permutations(range(2, n + 1)):
            seq = (1,) + p
            if all(isp(seq[i] + seq[(i + 1) % n]) for i in range(n)):
                c += 1
        o += f"{c}\n"
    return o
def g(r):
    return "".join(f"{r.randint(1, 8)}\n" for _ in range(r.randint(1, 4)))
Q("d143", b, g, lambda t: one_int_lines(t) and all(1 <= int(x) <= 14 for x in body(t)) and 1 <= len(body(t)) <= 14,
  wrong=[pt("if prev+1 in P: c+=1", "c+=1"), pt("P={2,3,5,7,11,13,17,19,23,29}", "P={2,3,5,7,11,13,17,19,29}"), pt("if n==1: return 1", "if n==1: return 0")], space=14, nrand=4)

# ---------- d144 ----------
def b(t):
    o = ""
    for l in body(t):
        n = int(l)
        o += f"{sum(bin(k).count('1') for k in range(1, n + 1))}\n"
    return o
def g(r):
    return "".join(f"{mix(r, [1, 2, 3, 7, 8, 15, 16], 1, 3000)}\n" for _ in range(r.randint(1, 5)))
Q("d144", b, g, lambda t: one_int_lines(t) and all(1 <= int(x) <= 10**18 for x in body(t)) and 1 <= len(body(t)) <= 1000,
  wrong=[pt("(n+1)//p", "n//p"), pt("max(0,(n+1)%p-(1<<i))", "max(0,n%p-(1<<i))"), pt("while (1<<i)<=n:", "while (1<<i)<n:"), pt("max(0,(n+1)%p-(1<<i))", "((n+1)%p-(1<<i))")],
  big=[lambda r: "".join(f"{r.randint(1, 10**18)}\n" for _ in range(1000))])

# ---------- d145 ----------
def b(t):
    n = int(t)
    subs = [[]]
    for i in range(1, n + 1):
        subs = subs + [s + [i] for s in subs]
    return "".join("{" + ",".join(map(str, s)) + "}\n" for s in subs)
Q("d145", b, lambda r: f"{r.randint(0, 6)}\n", lambda t: len(body(t)) == 1 and 0 <= int(t) <= 10,
  wrong=[pt("range(1<<n)", "range((1<<n)-1,-1,-1)"), pt("m>>i&1", "m>>(n-1-i)&1"), pt("str(i+1)", "str(i)")], space=11)


# =============================== 階段 3 ===============================
from qa_s3 import rand_graph, gridtxt, M as MOD
import sys as _sys

def gedges(r, n, m, wmax=None, loops=True):
    es = []
    for _ in range(m):
        u, v = r.randint(1, n), r.randint(1, n)
        if not loops and u == v:
            continue
        es.append((u, v) + ((r.randint(1, wmax),) if wmax else ()))
    return es

def graph_lines_ok(ls, n, m, ncol=2, wmax=None):
    return len(ls) >= 1 + m and all(len(nums(x)) == ncol and 1 <= nums(x)[0] <= n and 1 <= nums(x)[1] <= n and (wmax is None or 1 <= nums(x)[2] <= wmax) for x in ls[1:1 + m])

# ---------- d146 ----------
def g(r):
    R_, C = r.randint(1, 5), r.randint(1, 5)
    return f"{R_} {C}\n" + "\n".join("".join(r.choice("01") for _ in range(C)) for _ in range(R_)) + "\n"
def b(t):
    _sys.setrecursionlimit(10000)
    ls = body(t)
    R_, C = nums(ls[0])
    gr = [list(x) for x in ls[1:1 + R_]]
    def dfs(i, j):
        if not (0 <= i < R_ and 0 <= j < C) or gr[i][j] != "1":
            return
        gr[i][j] = "x"
        dfs(i + 1, j); dfs(i - 1, j); dfs(i, j + 1); dfs(i, j - 1)
    k = 0
    for i in range(R_):
        for j in range(C):
            if gr[i][j] == "1":
                k += 1
                dfs(i, j)
    return f"{k}\n"
Q("d146", b, g, lambda t: (lambda ls, R_, C: 1 <= R_ <= 500 and 1 <= C <= 500 and len(ls) == R_ + 1 and all(len(x) == C and set(x) <= set("01") for x in ls[1:]))(body(t), *nums(body(t)[0])),
  wrong=[pt("for a,b in((x+1,y),(x-1,y),(x,y+1),(x,y-1)):", "for a,b in((x+1,y),(x-1,y),(x,y+1),(x,y-1),(x+1,y+1),(x-1,y-1),(x+1,y-1),(x-1,y+1)):"), pt("for a,b in((x+1,y),(x-1,y),(x,y+1),(x,y-1)):", "for a,b in((x+1,y),(x,y+1)):"), pt("if g[i][j]=='1':\n            k+=1", "if g[i][j]=='0':\n            k+=1")],
  big=[lambda r: grid01(r, 500, 500, 0.5), lambda r: grid01(r, 500, 500, 1.0), lambda r: "500 500\n" + "\n".join(("1" * 500) if i % 2 == 0 else ("0" * 499 + "1" if (i // 2) % 2 == 0 else "1" + "0" * 499) for i in range(500)) + "\n"])

# ---------- d147 ----------
def g(r):
    t = r.randint(1, 3)
    out = []
    for _ in range(t):
        n = r.randint(1, 6)
        out.append(f"{n} {r.randint(1, n)} {r.randint(1, n)} {r.randint(1, n)} {r.randint(1, n)}")
    return f"{t}\n" + "\n".join(out) + "\n"
def b(t):
    ls = body(t)
    o = ""
    for l in ls[1:1 + int(ls[0])]:
        n, r1, c1, r2, c2 = nums(l)
        INF = 10**9
        d = {(i, j): INF for i in range(1, n + 1) for j in range(1, n + 1)}
        d[(r1, c1)] = 0
        ch = True
        while ch:
            ch = False
            for (i, j), v in list(d.items()):
                if v >= INF:
                    continue
                for dx, dy in itertools.product((-2, -1, 1, 2), repeat=2):
                    if abs(dx) != abs(dy) and (i + dx, j + dy) in d and d[(i + dx, j + dy)] > v + 1:
                        d[(i + dx, j + dy)] = v + 1
                        ch = True
        o += f"{d[(r2, c2)] if d[(r2, c2)] < INF else -1}\n"
    return o
Q("d147", b, g, lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 100 and all(len(nums(x)) == 5 and 1 <= nums(x)[0] <= 50 and all(1 <= c <= nums(x)[0] for c in nums(x)[1:]) for x in body(t)[1:]),
  wrong=[pt("1<=a<=n and 1<=b<=n and (a,b) not in d", "1<=a<n and 1<=b<=n and (a,b) not in d"), pt("(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)", "(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2)"), pt("print(d.get((r2,c2),-1))", "print(d.get((r2,c2),0))"), pt("d={(r1,c1):0}", "d={(r1,c1):1}")],
  big=[lambda r: "100\n" + "".join(f"50 {r.randint(1, 50)} {r.randint(1, 50)} {r.randint(1, 50)} {r.randint(1, 50)}\n" for _ in range(100))], nrand=8)

# ---------- d148 ----------
def g(r):
    n = r.randint(1, 6)
    es = gedges(r, n, r.randint(0, 8), loops=r.random() < 0.2)
    return f"{n} {len(es)}\n" + "".join(f"{u} {v}\n" for u, v in es)
def b(t):
    ls = body(t)
    n, m = nums(ls[0])
    es = [tuple(nums(x)) for x in ls[1:1 + m]]
    for col in itertools.product((0, 1), repeat=n):
        if all(col[u - 1] != col[v - 1] for u, v in es):
            return "YES\n"
    return "NO\n"
Q("d148", b, g, lambda t: (lambda ls, n, m: 1 <= n <= 10**5 and 0 <= m <= 2 * 10**5 and len(ls) == 1 + m and graph_lines_ok(ls, n, m))(body(t), *nums(body(t)[0])),
  wrong=[pt("elif col[v]==col[u]: ok=False;break", "elif col[v]==col[u] and v!=u: ok=False;break"), pt("if col[s]>=0 or not ok: continue", "if s>1: continue"), pt("col[v]=col[u]^1", "col[v]=0")],
  big=[lambda r: "20000 40000\n" + "".join(f"{u} {v}\n" for u, v in [(i, i + 1) for i in range(1, 20000)] + [(r.randint(1, 10000) * 2 - 1, r.randint(1, 10000) * 2) for _ in range(20001)]), lambda r: "20000 20000\n" + "".join(f"{i} {i % 20000 + 1}\n" for i in range(1, 20001)), lambda r: "20000 19999\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 20000))], nrand=8)

# ---------- d149 ----------
def g(r):
    n = r.randint(1, 6)
    if r.random() < 0.5:
        es = conn_tree_edges(r, n)
        if r.random() < 0.4 and es:
            es[r.randrange(len(es))] = (r.randint(1, n), r.randint(1, n))
    else:
        es = gedges(r, n, r.randint(0, 7))
    r.shuffle(es)
    return f"{n} {len(es)}\n" + "".join(f"{u} {v}\n" for u, v in es)
def conn_tree_edges(r, n):
    return [(r.randint(1, v - 1), v) for v in range(2, n + 1)]
def b(t):
    ls = body(t)
    n, m = nums(ls[0])
    es = [tuple(nums(x)) for x in ls[1:1 + m]]
    adj = {i: set() for i in range(1, n + 1)}
    for u, v in es:
        adj[u].add(v); adj[v].add(u)
    seen = {1}
    st = [1]
    while st:
        u = st.pop()
        for v in adj[u]:
            if v not in seen:
                seen.add(v); st.append(v)
    return "YES\n" if len(seen) == n and m == n - 1 else "NO\n"
Q("d149", b, g, lambda t: (lambda ls, n, m: 1 <= n <= 10**5 and 0 <= m <= 2 * 10**5 and len(ls) == 1 + m and graph_lines_ok(ls, n, m))(body(t), *nums(body(t)[0])),
  wrong=[pt("if a==b: ok=False;break", "if a==b: pass"), pt("if m!=n-1: print('NO')", "if m!=n: print('NO')")],
  big=[lambda r: "20000 19999\n" + "".join(f"{r.randint(1, i - 1)} {i}\n" for i in range(2, 20001)), lambda r: "20000 19999\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 19999)) + "5 5\n"], nrand=8)

# ---------- d150 ----------
def g(r):
    n = r.randint(1, 6)
    m = r.randint(0, 7)
    return f"{n} {m}\n" + "".join(f"{u} {v}\n" for u, v in gedges(r, n, m))
def b(t):
    ls = body(t)
    n, m = nums(ls[0])
    es = [tuple(nums(x)) for x in ls[1:1 + m]]
    for i, (u, v) in enumerate(es):
        adj = {k: [] for k in range(1, n + 1)}
        for a, c in es[:i]:
            adj[a].append(c); adj[c].append(a)
        seen = {u}
        st = [u]
        while st:
            x = st.pop()
            for y in adj[x]:
                if y not in seen:
                    seen.add(y); st.append(y)
        if v in seen:
            return f"{i + 1}\n"
    return "0\n"
Q("d150", b, g, lambda t: (lambda ls, n, m: 1 <= n <= 10**5 and 0 <= m <= 2 * 10**5 and len(ls) == 1 + m and graph_lines_ok(ls, n, m))(body(t), *nums(body(t)[0])),
  wrong=[pt("ans=i+1;break", "ans=i;break"), pt("ans=i+1;break", "ans=i+1")],
  big=[lambda r: "20000 20000\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 20000)) + "20000 1\n", lambda r: "20000 40000\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 20000)) + "".join(f"{r.randint(1, 20000)} {r.randint(1, 20000)}\n" for _ in range(20001))])

# ---------- d152 ----------
def g(r):
    n = r.randint(1, 6)
    m = r.randint(0, 8)
    perm = list(range(1, n + 1)); r.shuffle(perm)
    es = []
    for _ in range(m):
        a, b_ = r.randint(0, n - 1), r.randint(0, n - 1)
        if r.random() < 0.85 and a > b_:
            a, b_ = b_, a
        es.append((perm[a], perm[b_]))
    return f"{n} {len(es)}\n" + "".join(f"{u} {v}\n" for u, v in es)
def b(t):
    ls = body(t)
    n, m = nums(ls[0])
    pre = {i: set() for i in range(1, n + 1)}
    for l in ls[1:1 + m]:
        a, c = nums(l)
        pre[c].add(a)
    done, sem = set(), 0
    while len(done) < n:
        cur = [i for i in pre if i not in done and pre[i] <= done]
        if not cur:
            return "-1\n"
        done |= set(cur)
        sem += 1
    return f"{sem}\n"
Q("d152", b, g, lambda t: (lambda ls, n, m: 1 <= n <= 10**5 and 0 <= m <= 2 * 10**5 and len(ls) == 1 + m and graph_lines_ok(ls, n, m))(body(t), *nums(body(t)[0])),
  wrong=[pt("print(sem if done==n else -1)", "print(sem)"), pt("sem+=1;nxt=[]", "sem+=1;nxt=[]\n    if sem==1 and len(cur)==n: sem=0"), pt("print(sem if done==n else -1)", "print(sem-1 if done==n else -1)")],
  big=[lambda r: "20000 39997\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 20000)) + "".join(f"{i} {i + 2}\n" for i in range(1, 19999)), lambda r: "20000 20000\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 20000)) + "20000 1\n"], nrand=8)

# ---------- d154 ----------
def g(r):
    n = r.randint(1, 5)
    es = gedges(r, n, r.randint(0, 7), 3, loops=False)
    return f"{n} {len(es)}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in es)
def b(t):
    ls = body(t)
    n, m = nums(ls[0])
    es = [tuple(nums(x)) for x in ls[1:1 + m]]
    best, cnt = None, 0
    def go(u, vis, dist):
        nonlocal best, cnt
        if u == n:
            if best is None or dist < best:
                best, cnt = dist, 1
            elif dist == best:
                cnt += 1
            return
        for a, c, w in es:
            for x, y in ((a, c), (c, a)):
                if x == u and y not in vis:
                    go(y, vis | {y}, dist + w)
                if a == c:
                    break
    go(1, {1}, 0)
    return "-1 0\n" if best is None else f"{best} {cnt % MOD}\n"
Q("d154", b, g, lambda t: (lambda ls, n, m: 1 <= n <= 10**4 and 0 <= m <= 5 * 10**4 and len(ls) == 1 + m and graph_lines_ok(ls, n, m, 3, 1000))(body(t), *nums(body(t)[0])),
  wrong=[pt("elif nd==dist[v]: cnt[v]=(cnt[v]+cnt[u])%M", "elif nd==dist[v]: cnt[v]=cnt[u]"), pt("if nd<dist[v]: dist[v]=nd;cnt[v]=cnt[u];heapq.heappush(h,(nd,v))", "if nd<dist[v]: dist[v]=nd;cnt[v]=1;heapq.heappush(h,(nd,v))"), pt("print(dist[n],cnt[n]%M) if dist[n]<INF else print(-1,0)", "print(dist[n],cnt[n]%M)")],
  big=[lambda r: "5000 20000\n" + "".join(f"{u} {v} {w}\n" for u, v, w in rand_graph(r, 5000, 20000, 3, connected=True)), lambda r: "5000 9998\n" + "".join(f"{i} {i + 1} 1\n{i} {i + 1} 1\n" for i in range(1, 5000))])

# ---------- d156 ----------
def g(r):
    n = r.randint(1, 5)
    m = r.randint(0, 7)
    q = r.randint(1, 4)
    return f"{n} {m} {q}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in gedges(r, n, m, 9)) + "".join(f"{r.randint(1, n)} {r.randint(1, n)}\n" for _ in range(q))
def b(t):
    ls = body(t)
    n, m, q = nums(ls[0])
    INF = 10**18
    d = [[INF] * (n + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        d[i][i] = 0
    for l in ls[1:1 + m]:
        u, v, w = nums(l)
        if u != v:
            d[u][v] = d[v][u] = min(d[u][v], w)
    for k in range(1, n + 1):
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                d[i][j] = min(d[i][j], max(d[i][k], d[k][j]))
    return "".join(f"{d[a][b_] if d[a][b_] < INF else -1}\n" for a, b_ in (nums(x) for x in ls[1 + m:1 + m + q]))
def v156(t):
    ls = body(t)
    n, m, q = nums(ls[0])
    return 1 <= n <= 1000 and 0 <= m <= 5000 and 1 <= q <= 1000 and len(ls) == 1 + m + q and all(len(nums(x)) == 3 and 1 <= nums(x)[0] <= n and 1 <= nums(x)[1] <= n and 1 <= nums(x)[2] <= 10**6 for x in ls[1:1 + m]) and all(len(nums(x)) == 2 and 1 <= nums(x)[0] <= n and 1 <= nums(x)[1] <= n for x in ls[1 + m:])
Q("d156", b, g, v156,
  wrong=[pt("best[v]=max(best[u],w)", "best[v]=best[u]+w"), pt("print(best.get(b,-1))", "print(best.get(b,0))"), pt("E=sorted((int(d[5+3*i]),int(d[3+3*i]),int(d[4+3*i])) for i in range(m))", "E=sorted((int(d[5+3*i]),int(d[3+3*i]),int(d[4+3*i])) for i in range(m))[::-1]"), pt("best={a:0}", "best={a:1}")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nn,m,q=int(d[0]),int(d[1]),int(d[2])\nI=10**18\nD=[[I]*(n+1) for _ in range(n+1)]\nfor i in range(n+1): D[i][i]=0\nfor i in range(m):\n    u,v,w=int(d[3+3*i]),int(d[4+3*i]),int(d[5+3*i])\n    if u!=v and w<D[u][v]: D[u][v]=D[v][u]=w\nfor k in range(1,n+1):\n    for i in range(1,n+1):\n        for j in range(1,n+1):\n            x=max(D[i][k],D[k][j])\n            if x<D[i][j]: D[i][j]=x\np=3+3*m\nfor _ in range(q):\n    a,b=int(d[p]),int(d[p+1]);p+=2\n    print(D[a][b] if D[a][b]<I else -1)\n", "Floyd 變形 O(n³)")],
  big=[lambda r: "1000 5000 1000\n" + "".join(f"{u} {v} {w}\n" for u, v, w in rand_graph(r, 1000, 5000, 10**6, connected=True)) + "".join(f"{r.randint(1, 1000)} {r.randint(1, 1000)}\n" for _ in range(1000)), lambda r: "1000 999 1000\n" + "".join(f"{i} {i + 1} {r.randint(1, 10**6)}\n" for i in range(1, 1000)) + "".join(f"1 {r.randint(500, 1000)}\n" for _ in range(1000))], nrand=8)

# ---------- d157 ----------
def g(r):
    n = r.randint(1, 6)
    m = r.randint(0, 8)
    return f"{n} {m}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in gedges(r, n, m, 9))
def b(t):
    ls = body(t)
    n, m = nums(ls[0])
    INF = 10**18
    adj = [[INF] * (n + 1) for _ in range(n + 1)]
    for l in ls[1:1 + m]:
        u, v, w = nums(l)
        if u != v:
            adj[u][v] = adj[v][u] = min(adj[u][v], w)
    seen, tot, comps = set(), 0, 0
    for s in range(1, n + 1):
        if s in seen:
            continue
        comps += 1
        best = {s: 0}
        inT = set()
        while True:
            cand = [v for v in best if v not in inT]
            if not cand:
                break
            u = min(cand, key=lambda x: best[x])
            inT.add(u)
            tot += best[u]
            for v in range(1, n + 1):
                if v not in inT and adj[u][v] < INF and adj[u][v] < best.get(v, INF):
                    best[v] = adj[u][v]
        seen |= inT
    return f"{tot} {comps}\n"
Q("d157", b, g, lambda t: (lambda ls, n, m: 1 <= n <= 10**5 and 0 <= m <= 2 * 10**5 and len(ls) == 1 + m and graph_lines_ok(ls, n, m, 3, 10**6))(body(t), *nums(body(t)[0])),
  wrong=[pt("t=0;c=n", "t=0;c=n+1"), pt("p[a]=b;t+=w;c-=1", "p[a]=b;t+=w"), pt("if a!=b: p[a]=b;t+=w;c-=1", "if a!=b: p[a]=b;t+=w;c-=1\n    elif a==b and u==v: t+=w")],
  big=[lambda r: "20000 40000\n" + "".join(f"{u} {v} {w}\n" for u, v, w in rand_graph(r, 20000, 40000, 10**6)), lambda r: "20000 10000\n" + "".join(f"{2 * i + 1} {2 * i + 2} {r.randint(1, 10**6)}\n" for i in range(10000))])

# ---------- d159 ----------
def g(r):
    return "".join(f"{mix(r, [0, 1, 2, 3, 4], 0, 25)}\n" for _ in range(r.randint(1, 4)))
def b(t):
    from functools import lru_cache
    @lru_cache(None)
    def f(n):
        return 1 if n == 0 else sum(f(n - k) for k in (1, 2, 3) if n - k >= 0)
    return "".join(f"{f(int(x)) % MOD}\n" for x in body(t))
Q("d159", b, g, lambda t: one_int_lines(t) and all(0 <= int(x) <= 10**6 for x in body(t)) and 1 <= len(body(t)) <= 100,
  wrong=[pt("dp[0]=1", "dp[0]=0"), pt("(dp[i-3] if i>=3 else 0)", "0"), pt("%M", "")],
  big=[lambda r: "1000000\n999999\n500000\n"])

# ---------- d160 ----------
def g(r):
    n = r.randint(1, 8)
    return f"{n}\n{sp(ints(r, n, 0, 9))}\n"
def b(t):
    a = nums(body(t)[1])
    n = len(a)
    return f"{max(sum(a[i] for i in range(n) if m >> i & 1) for m in range(1 << n) if not (m & (m >> 1)))}\n"
Q("d160", b, g, lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 10**5 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), 0, 10**4),
  wrong=[pt("p2,p1=p1,max(p1,p2+x)", "p2,p1=p1,p2+x"), pt("p2,p1=p1,max(p1,p2+x)", "p2,p1=p1,max(p1,x)"), pt("p2=p1=0", "p2=p1=1")],
  big=[lambda r: "30000\n" + sp(ints(r, 30000, 0, 10000)) + "\n"])

# ---------- d161 ----------
def b(t):
    from functools import lru_cache
    @lru_cache(None)
    def f(n, k):          # 把 n 拆成部分（每部分 ≤ k）的最大乘積
        if n == 0:
            return 1
        return max(i * f(n - i, i) for i in range(1, min(n, k) + 1))
    return "".join(f"{f(int(x), int(x) - 1)}\n" for x in body(t))
def g(r):
    return "".join(f"{r.randint(2, 18)}\n" for _ in range(r.randint(1, 4)))
Q("d161", b, g, lambda t: one_int_lines(t) and all(2 <= int(x) <= 1000 for x in body(t)) and 1 <= len(body(t)) <= 20,
  wrong=[pt("k*max(i-k,dp[i-k])", "k*(i-k)"), pt("for i in range(2,N+1)", "for i in range(3,N+1)")],
  big=[lambda r: "1000\n999\n998\n997\n"], space=999, nrand=6)

# ---------- d163 ----------
def g(r):
    n = r.randint(1, 4)
    return f"{n} {r.randint(0, 15)}\n" + "".join(f"{r.randint(1, 6)} {r.randint(1, 20)}\n" for _ in range(n))
def b(t):
    ls = body(t)
    n, W = nums(ls[0])
    it = [tuple(nums(x)) for x in ls[1:1 + n]]
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w, v_ = it[i - 1]
        for j in range(W + 1):
            dp[i][j] = dp[i - 1][j]
            k = 1
            while k * w <= j:
                dp[i][j] = max(dp[i][j], dp[i - 1][j - k * w] + k * v_)
                k += 1
    return f"{dp[n][W]}\n"
Q("d163", b, g, lambda t: len(body(t)) == 1 + nums(body(t)[0])[0] and 1 <= nums(body(t)[0])[0] <= 100 and 0 <= nums(body(t)[0])[1] <= 10**4 and all(len(nums(x)) == 2 and 1 <= nums(x)[0] <= 10**4 and 1 <= nums(x)[1] <= 10**9 for x in body(t)[1:]),
  wrong=[pt("for j in range(w,W+1):", "for j in range(W,w-1,-1):"), pt("for j in range(w,W+1):", "for j in range(w+1,W+1):")],
  big=[lambda r: "100 10000\n" + "".join(f"{r.randint(1, 3000)} {r.randint(1, 10**9)}\n" for _ in range(100)), lambda r: "100 10000\n" + "".join(f"{r.randint(1, 20)} {r.randint(1, 10**9)}\n" for _ in range(100))])

# ---------- d164 ----------
def g(r):
    n = r.randint(1, 5)
    return f"{n} {r.randint(0, 12)}\n" + "".join(f"{r.randint(1, 6)} {r.randint(1, 20)}\n" for _ in range(n))
def b(t):
    ls = body(t)
    n, W = nums(ls[0])
    it = [tuple(nums(x)) for x in ls[1:1 + n]]
    best = -1
    for m in range(1 << n):
        if sum(it[i][0] for i in range(n) if m >> i & 1) == W:
            best = max(best, sum(it[i][1] for i in range(n) if m >> i & 1))
    return f"{best}\n"
Q("d164", b, g, lambda t: len(body(t)) == 1 + nums(body(t)[0])[0] and 1 <= nums(body(t)[0])[0] <= 100 and 0 <= nums(body(t)[0])[1] <= 10**4 and all(len(nums(x)) == 2 and 1 <= nums(x)[0] <= 10**4 and 1 <= nums(x)[1] <= 10**9 for x in body(t)[1:]),
  wrong=[pt("dp=[NEG]*(W+1);dp[0]=0", "dp=[0]*(W+1)"), pt("if dp[j-w]>=0 and dp[j-w]+v>dp[j]", "if dp[j-w]+v>dp[j]"), pt("for j in range(W,w-1,-1):", "for j in range(w,W+1):")],
  big=[lambda r: "100 10000\n" + "".join(f"{r.randint(50, 200)} {r.randint(1, 10**9)}\n" for _ in range(100))])

# ---------- d166 ----------
def g(r):
    n = r.randint(1, 8)
    return f"{n}\n{sp(ints(r, n, -3, 3))}\n"
def b(t):
    a = nums(body(t)[1])
    n = len(a)
    best, cnt = 0, 0
    for m in range(1, 1 << n):
        s = [a[i] for i in range(n) if m >> i & 1]
        if all(s[i] < s[i + 1] for i in range(len(s) - 1)):
            if len(s) > best:
                best, cnt = len(s), 1
            elif len(s) == best:
                cnt += 1
    return f"{best} {cnt % MOD}\n"
Q("d166", b, g, lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 2000 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), -10**9, 10**9),
  wrong=[pt("elif L[j]+1==L[i]: C[i]=(C[i]+C[j])%M", "elif L[j]+1==L[i]: C[i]=C[j]"), pt("if L[j]+1>L[i]: L[i]=L[j]+1;C[i]=C[j]", "if L[j]+1>L[i]: L[i]=L[j]+1;C[i]+=C[j]"), pt("if a[j]<a[i]:", "if a[j]<=a[i]:"), pt("print(m,sum(C[i] for i in range(n) if L[i]==m)%M)", "print(m,max(C))")],
  big=[lambda r: "2000\n" + sp(range(2000)) + "\n", lambda r: "2000\n" + sp(ints(r, 2000, -10**9, 10**9)) + "\n", lambda r: "2000\n" + sp([i % 3 for i in range(2000)]) + "\n"], nrand=8)

# ---------- d167 ----------
def g(r):
    return word(r, 1, 6, "abc") + "\n" + word(r, 1, 6, "abc") + "\n"
def b(t):
    a, c = body(t)
    from functools import lru_cache
    @lru_cache(None)
    def f(i, j):
        if i == 0:
            return j
        if j == 0:
            return i
        if a[i - 1] == c[j - 1]:
            return f(i - 1, j - 1)
        return 1 + min(f(i - 1, j), f(i, j - 1), f(i - 1, j - 1))
    return f"{f(len(a), len(c))}\n"
Q("d167", b, g, lambda t: len(body(t)) == 2 and all(1 <= len(x) <= 1000 and x.islower() and x.isalpha() for x in body(t)),
  wrong=[pt("1+min(prev[j],cur[j-1],prev[j-1])", "1+min(prev[j],cur[j-1])"), pt("1+min(prev[j],cur[j-1],prev[j-1])", "1+prev[j-1]"), pt("prev=list(range(m+1))", "prev=[0]*(m+1)"), pt("cur=[i]+[0]*m", "cur=[0]+[0]*m")],
  big=[lambda r: "".join(r.choice("abcd") for _ in range(1000)) + "\n" + "".join(r.choice("abcd") for _ in range(1000)) + "\n", lambda r: "a" * 1000 + "\n" + "b" * 1000 + "\n"], nrand=8)

# ---------- d168 ----------
def g(r):
    return word(r, 1, 9, "abc") + "\n"
def b(t):
    s = body(t)[0]
    r_ = s[::-1]
    T = [[0] * (len(s) + 1) for _ in range(len(s) + 1)]
    for i in range(len(s)):
        for j in range(len(s)):
            T[i + 1][j + 1] = T[i][j] + 1 if s[i] == r_[j] else max(T[i][j + 1], T[i + 1][j])
    return f"{T[len(s)][len(s)]}\n"
Q("d168", b, g, lambda t: len(body(t)) == 1 and 1 <= len(body(t)[0]) <= 1000 and body(t)[0].islower() and body(t)[0].isalpha(),
  wrong=[pt("dp[i+1][j-1]+2 if s[i]==s[j] else max(dp[i+1][j],dp[i][j-1])", "dp[i+1][j-1]+2 if s[i]==s[j] else dp[i+1][j]"), pt("dp[i][i]=1", "dp[i][i]=0"), pt("dp[i+1][j-1]+2", "dp[i+1][j-1]+1")],
  big=[lambda r: "".join(r.choice("abc") for _ in range(1000)) + "\n", lambda r: "a" * 1000 + "\n", lambda r: "".join(chr(97 + i % 26) for i in range(1000)) + "\n"], nrand=8)

# ---------- d169 ----------
def g(r):
    n = r.randint(1, 5)
    return f"{n}\n" + "".join(sp(ints(r, i + 1, -9, 9)) + "\n" for i in range(n))
def b(t):
    ls = body(t)
    n = int(ls[0])
    a = [nums(x) for x in ls[1:1 + n]]
    from functools import lru_cache
    @lru_cache(None)
    def f(i, j):
        if i == n - 1:
            return a[i][j]
        return a[i][j] + max(f(i + 1, j), f(i + 1, j + 1))
    return f"{f(0, 0)}\n"
Q("d169", b, g, lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 1000 and all(len(nums(x)) == i + 1 and inrange(nums(x), -10**4, 10**4) for i, x in enumerate(body(t)[1:])),
  wrong=[pt("a[i][j]+=max(a[i+1][j],a[i+1][j+1])", "a[i][j]+=a[i+1][j]"), pt("a[i][j]+=max(a[i+1][j],a[i+1][j+1])", "a[i][j]+=min(a[i+1][j],a[i+1][j+1])"), pt("range(n-2,-1,-1)", "range(n-3,-1,-1)")],
  big=[lambda r: "350\n" + "".join(sp(ints(r, i + 1, -10**4, 10**4)) + "\n" for i in range(350)), lambda r: "300\n" + "".join(sp([10**4] * (i + 1)) + "\n" for i in range(300))])

# ---------- d170 ----------
def g(r):
    return "".join(f"{mix(r, [1], 1, 8)} {mix(r, [1], 1, 8)}\n" for _ in range(r.randint(1, 4)))
Q("d170", lambda t: "".join(f"{math.comb(nums(l)[0] + nums(l)[1] - 2, nums(l)[0] - 1) % MOD}\n" for l in body(t)), g,
  lambda t: all(len(l.split()) == 2 and inrange(nums(l), 1, 1000) for l in body(t)) and 1 <= len(body(t)) <= 10,
  wrong=[pt("row=[1]*C", "row=[0]*C"), pt("for _ in range(R-1):", "for _ in range(R):"), pt("%M", ""), pt("for j in range(1,C): row[j]=(row[j]+row[j-1])%M", "for j in range(1,C): row[j]=(row[j]+row[j-1]+1)%M")],
  big=[lambda r: "1000 1000\n999 1000\n1000 999\n500 500\n1 1000\n1000 1\n"])

# ---------- d171 ----------
def g(r):
    R_, C = r.randint(1, 5), r.randint(1, 5)
    return f"{R_} {C}\n" + "\n".join("".join("1" if r.random() < 0.7 else "0" for _ in range(C)) for _ in range(R_)) + "\n"
def b(t):
    ls = body(t)
    R_, C = nums(ls[0])
    gr = ls[1:1 + R_]
    best = 0
    for i in range(R_):
        for j in range(C):
            for s in range(1, min(R_ - i, C - j) + 1):
                if all(gr[x][y] == "1" for x in range(i, i + s) for y in range(j, j + s)):
                    best = max(best, s)
    return f"{best}\n"
Q("d171", b, g, lambda t: (lambda ls, R_, C: 1 <= R_ <= 500 and 1 <= C <= 500 and len(ls) == R_ + 1 and all(len(x) == C and set(x) <= set("01") for x in ls[1:]))(body(t), *nums(body(t)[0])),
  wrong=[pt("dp[i][j]=min(dp[i-1][j],dp[i][j-1],dp[i-1][j-1])+1", "dp[i][j]=min(dp[i-1][j],dp[i][j-1])+1"), pt("dp[i][j]=min(dp[i-1][j],dp[i][j-1],dp[i-1][j-1])+1;best=max(best,dp[i][j])", "dp[i][j]=min(dp[i-1][j],dp[i][j-1],dp[i-1][j-1])+1;best=dp[i][j]"), pt("g[i-1][j-1]=='1'", "g[i-1][j-1]=='1' and i>1")],
  big=[lambda r: grid01(r, 500, 500, 0.95), lambda r: grid01(r, 500, 500, 1.0), lambda r: grid01(r, 500, 500, 0.5)])

# ---------- d172 ----------
def g(r):
    n = r.randint(1, 6)
    return f"{n}\n{sp(ints(r, n, 1, 9))}\n"
def b(t):
    a = nums(body(t)[1])
    def go(xs):
        if len(xs) == 1:
            return 0
        return min(go(xs[:i] + [xs[i] + xs[i + 1]] + xs[i + 2:]) + xs[i] + xs[i + 1] for i in range(len(xs) - 1))
    return f"{go(a)}\n"
Q("d172", b, g, lambda t: len(body(t)) == 2 and 1 <= int(body(t)[0]) <= 100 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), 1, 1000),
  wrong=[pt("+pre[j+1]-pre[i]", ""), pt("for L in range(2,n+1)", "for L in range(2,n)"), pt("min(dp[i][k]+dp[k+1][j] for k in range(i,j))", "min(dp[i][k]+dp[k+1][j] for k in range(i,j-1) or [i])"), pt("min(dp[i][k]+dp[k+1][j] for k in range(i,j))", "dp[i][i]+dp[i+1][j]")],
  big=[lambda r: "100\n" + sp(ints(r, 100, 1, 1000)) + "\n", lambda r: "100\n" + sp([1000] * 100) + "\n"], nrand=8)

# ---------- d173 ----------
def g(r):
    return word(r, 1, 8, "ab") + "\n"
def b(t):
    s = body(t)[0]
    n = len(s)
    best = n
    for m in range(1 << (n - 1)):
        parts, st = [], 0
        for i in range(n - 1):
            if m >> i & 1:
                parts.append(s[st:i + 1]); st = i + 1
        parts.append(s[st:])
        if all(p == p[::-1] for p in parts):
            best = min(best, len(parts) - 1)
    return f"{best}\n"
Q("d173", b, g, lambda t: len(body(t)) == 1 and 1 <= len(body(t)[0]) <= 1000 and body(t)[0].islower() and body(t)[0].isalpha(),
  wrong=[pt("pal[i][j]=s[i]==s[j] and (j-i<2 or pal[i+1][j-1])", "pal[i][j]=s[i]==s[j]"), pt("if pal[0][j]: dp[j]=0", "if pal[0][j]: dp[j]=1"), pt("dp[i-1]+1 for i in range(1,j+1) if pal[i][j]", "dp[i-1]+1 for i in range(1,j+1)")],
  big=[lambda r: "".join(r.choice("ab") for _ in range(1000)) + "\n", lambda r: "a" * 1000 + "\n", lambda r: "ab" * 500 + "\n", lambda r: "".join(chr(97 + i % 26) for i in range(1000)) + "\n"], nrand=8)

# ---------- d175 ----------
def g(r):
    n = r.randint(1, 5)
    return f"{n}\n" + "".join(sp(ints(r, n, 0, 9)) + "\n" for _ in range(n))
def b(t):
    ls = body(t)
    n = int(ls[0])
    c = [nums(x) for x in ls[1:1 + n]]
    return f"{min(sum(c[i][p[i]] for i in range(n)) for p in itertools.permutations(range(n)))}\n"
Q("d175", b, g, lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 12 and all(len(nums(x)) == int(body(t)[0]) and inrange(nums(x), 0, 1000) for x in body(t)[1:]),
  wrong=[pt("i=bin(m).count('1')", "i=bin(m).count('1')-1 if m else 0"), pt("print(dp[(1<<n)-1])", "print(min(dp[1:]))")],
  big=[lambda r: "12\n" + "".join(sp(ints(r, 12, 0, 1000)) + "\n" for _ in range(12)), lambda r: "12\n" + "".join(sp([1000] * 12) + "\n" for _ in range(12))], nrand=8)

# ---------- d177 ----------
def g(r):
    return "".join(f"{r.randint(0, 9)} {r.randint(0, 30)} {r.randint(1, 20)}\n" for _ in range(r.randint(1, 4)))
def b(t):
    o = ""
    for l in body(t):
        a, b_, m = nums(l)
        r_ = 1 % m
        for _ in range(b_):
            r_ = r_ * a % m
        o += f"{r_}\n"
    return o
Q("d177", b, g, lambda t: all(len(l.split()) == 3 and 0 <= nums(l)[0] <= 10**9 and 0 <= nums(l)[1] <= 10**18 and 1 <= nums(l)[2] <= 10**9 for l in body(t)) and 1 <= len(body(t)) <= 1000,
  wrong=[pt("r=1%m", "r=1"), pt("if b&1: r=r*a%m", "if b&1: r=r*a"), pt("b>>=1", "b>>=2")],
  big=[lambda r: "".join(f"{r.randint(0, 10**9)} {r.randint(0, 10**18)} {r.randint(1, 10**9)}\n" for _ in range(1000))])

# ---------- d178 ----------
def g(r):
    return "".join(f"{r.randint(1, 40)} {r.randint(2, 40)}\n" for _ in range(r.randint(1, 5)))
def b(t):
    o = ""
    for l in body(t):
        a, m = nums(l)
        o += f"{next((x for x in range(m) if a * x % m == 1 % m), -1)}\n"
    return o
Q("d178", b, g, lambda t: all(len(l.split()) == 2 and 1 <= nums(l)[0] <= 10**9 and 2 <= nums(l)[1] <= 10**9 for l in body(t)) and 1 <= len(body(t)) <= 1000,
  wrong=[pt("return s0%m if r0==1 else -1", "return s0 if r0==1 else -1"), pt("return s0%m if r0==1 else -1", "return s0%m")],
  big=[lambda r: "".join(f"{r.randint(1, 10**9)} {r.randint(2, 10**9)}\n" for _ in range(1000))], nrand=8)

# ---------- d179 ----------
def g(r):
    q = r.randint(1, 5)
    return f"{q}\n" + "".join(f"{mix(r, [2, 3, 4, 97, 1000000], 2, 300)}\n" for _ in range(q))
def b(t):
    o = ""
    for x in body(t)[1:]:
        n = int(x)
        fs, p = [], 2
        while n > 1:
            if n % p == 0:
                e = 0
                while n % p == 0:
                    n //= p; e += 1
                fs.append(f"{p}^{e}")
            p += 1
        o += " ".join(fs) + "\n"
    return o
Q("d179", b, g, lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 10**5 and all(2 <= int(x) <= 10**6 for x in body(t)[1:]),
  wrong=[pt("p=spf[n];e=0", "p=spf[n];e=1"), pt("f.append(f'{p}^{e}')", "f.append(f'{p}^{e}' if e>1 else str(p))"), pt("if spf[j]==j: spf[j]=i", "spf[j]=i")],
  slow=[code("import sys\nd=sys.stdin.read().split();o=[]\nfor x in d[1:1+int(d[0])]:\n    n=int(x);f=[];p=2\n    while p*p<=n:\n        if n%p==0:\n            e=0\n            while n%p==0: n//=p;e+=1\n            f.append(f'{p}^{e}')\n        p+=1\n    if n>1: f.append(f'{n}^1')\n    o.append(' '.join(f))\nprint('\\n'.join(o))\n", "每個數各自試除到 √n")],
  big=[lambda r: "50000\n" + "".join(f"{r.choice([999983, 999979, 999961, 999959, 999953, 999931])}\n" for _ in range(50000))], nrand=8)


# =============================== 階段 4 ===============================
from qa_s4 import seg_inter, jarvis

# ---------- d181 ----------
def b(t):
    o = ""
    for l in body(t):
        x1, y1, x2, y2, x3, y3 = nums(l)
        cr = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
        if cr == 0:
            o += "0 DEGENERATE\n"
            continue
        a2 = [(x2 - x1) ** 2 + (y2 - y1) ** 2, (x3 - x2) ** 2 + (y3 - y2) ** 2, (x1 - x3) ** 2 + (y1 - y3) ** 2]
        a2.sort()
        if a2[0] + a2[1] == a2[2]:
            typ = "RIGHT"
        elif a2[0] + a2[1] < a2[2]:
            typ = "OBTUSE"
        else:
            typ = "ACUTE"
        o += f"{abs(cr)} {typ}\n"
    return o
def g(r):
    k = r.choice([2, 3, 5])
    return "".join(sp([r.randint(-k, k) for _ in range(6)]) + "\n" for _ in range(r.randint(1, 4)))
Q("d181", b, g, lambda t: all(len(l.split()) == 6 and inrange(nums(l), -10**6, 10**6) for l in body(t)) and 1 <= len(body(t)) <= 1000,
  wrong=[pt("'RIGHT' if m==0 else 'OBTUSE' if m<0 else 'ACUTE'", "'RIGHT' if m<=0 else 'ACUTE'"), pt("print(abs(cr),", "print(cr,"), pt("if cr==0: print(0,'DEGENERATE');continue", "if cr==0: print(0,'RIGHT');continue"), pt("min(d)", "max(d)")],
  big=[lambda r: "".join(sp([r.randint(-10**6, 10**6) for _ in range(6)]) + "\n" for _ in range(1000))], nrand=10)

# ---------- d182 ----------
def poly_gen(r):
    n = r.randint(3, 7)
    pts = set()
    while len(pts) < n:
        pts.add((r.randint(-5, 5), r.randint(-5, 5)))
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    P = sorted(pts, key=lambda p: (math.atan2(p[1] - cy, p[0] - cx), (p[0] - cx) ** 2 + (p[1] - cy) ** 2))
    return P
def g(r):
    P = poly_gen(r)
    if r.random() < 0.5:
        P.reverse()
    q = r.randint(1, 6)
    return f"{len(P)}\n" + "".join(f"{x} {y}\n" for x, y in P) + f"{q}\n" + "".join(f"{r.randint(-6, 6)} {r.randint(-6, 6)}\n" for _ in range(q))
def b(t):
    ls = body(t)
    n = int(ls[0])
    P = [tuple(nums(x)) for x in ls[1:1 + n]]
    q = int(ls[1 + n])
    o = ""
    for l in ls[2 + n:2 + n + q]:
        px, py = nums(l)
        on = False
        wn = 0
        for i in range(n):
            (ax, ay), (bx, by) = P[i], P[(i + 1) % n]
            cr = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
            if cr == 0 and min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by):
                on = True
            if ay <= py:
                if by > py and cr > 0:
                    wn += 1
            else:
                if by <= py and cr < 0:
                    wn -= 1
        o += ("BOUNDARY" if on else "INSIDE" if wn != 0 else "OUTSIDE") + "\n"
    return o
def v(t):
    ls = body(t)
    n = int(ls[0])
    if not (3 <= n <= 1000 and len(ls) >= 2 + n):
        return False
    P = [tuple(nums(x)) for x in ls[1:1 + n]]
    q = int(ls[1 + n])
    if not (1 <= q <= 1000 and len(ls) == 2 + n + q):
        return False
    from qa_s4 import simple_poly
    return all(inrange(p, -10**4, 10**4) for p in P) and len(set(P)) == n and simple_poly(P) and all(len(nums(x)) == 2 and inrange(nums(x), -10**4, 10**4) for x in ls[2 + n:])
def big182(r):
    n = 1000
    ang = sorted(r.random() * 2 * math.pi for _ in range(n))
    P = []
    for a in ang:
        rad = r.randint(3000, 10000)
        p = (round(rad * math.cos(a)), round(rad * math.sin(a)))
        if p not in P:
            P.append(p)
    return f"{len(P)}\n" + "".join(f"{x} {y}\n" for x, y in P) + "1000\n" + "".join(f"{r.randint(-10000, 10000)} {r.randint(-10000, 10000)}\n" for _ in range(1000))
Q("d182", b, g, v,
  wrong=[pt("if cr==0 and min(ax,bx)<=x<=max(ax,bx) and min(ay,by)<=y<=max(ay,by): on=True;break", "pass"), pt("if (t>0)==(by>ay): c=not c", "if (t>0): c=not c"), pt("print('BOUNDARY' if on else 'INSIDE' if c else 'OUTSIDE')", "print('INSIDE' if c or on else 'OUTSIDE')")],
  big=[big182], nrand=8)

# ---------- d183 ----------
def b(t):
    o = ""
    for l in body(t):
        x1, y1, x2, y2, x3, y3, x4, y4 = nums(l)
        cells = {(i, j) for i in range(x1, x2) for j in range(y1, y2)} & {(i, j) for i in range(x3, x4) for j in range(y3, y4)}
        o += f"{len(cells)}\n"
    return o
def g(r):
    out = []
    for _ in range(r.randint(1, 4)):
        a, c = sorted(r.sample(range(-4, 6), 2))
        b_, e = sorted(r.sample(range(-4, 6), 2))
        a2, c2 = sorted(r.sample(range(-4, 6), 2))
        b2, e2 = sorted(r.sample(range(-4, 6), 2))
        out.append(sp([a, b_, c, e, a2, b2, c2, e2]))
    return "\n".join(out) + "\n"
Q("d183", b, g, lambda t: all(len(l.split()) == 8 and inrange(nums(l), -10**9, 10**9) and nums(l)[0] < nums(l)[2] and nums(l)[1] < nums(l)[3] and nums(l)[4] < nums(l)[6] and nums(l)[5] < nums(l)[7] for l in body(t)) and 1 <= len(body(t)) <= 1000,
  wrong=[pt("w=max(0,min(v[2],v[6])-max(v[0],v[4]));h=max(0,min(v[3],v[7])-max(v[1],v[5]))", "w=min(v[2],v[6])-max(v[0],v[4]);h=min(v[3],v[7])-max(v[1],v[5])"), pt("max(0,min(v[3],v[7])-max(v[1],v[5]))", "max(0,min(v[3],v[7])-max(v[1],v[5])+1)"), pt("min(v[2],v[6])-max(v[0],v[4])", "min(v[2],v[6])-min(v[0],v[4])")],
  big=[lambda r: "".join(sp([-10**9, -10**9, 10**9, 10**9, r.randint(-10**9, 0), r.randint(-10**9, 0), r.randint(1, 10**9), r.randint(1, 10**9)]) + "\n" for _ in range(1000))], nrand=10)

# ---------- d184 ----------
def b(t):
    o = ""
    for l in body(t):
        x1, y1, r1, x2, y2, r2 = nums(l)
        d2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
        if d2 == 0:
            o += ("SAME" if r1 == r2 else "CONTAIN") + "\n"
            continue
        a = d2 + r1 * r1 - r2 * r2
        disc = 4 * d2 * r1 * r1 - a * a
        if disc > 0:
            o += "INTERSECT\n"
        elif disc == 0:
            o += ("INTERNAL" if d2 == (r1 - r2) ** 2 else "EXTERNAL") + "\n"
        else:
            o += ("SEPARATE" if d2 > (r1 + r2) ** 2 else "CONTAIN") + "\n"
    return o
def g(r):
    return "".join(sp([r.randint(-3, 3), r.randint(-3, 3), r.randint(1, 4), r.randint(-3, 3), r.randint(-3, 3), r.randint(1, 4)]) + "\n" for _ in range(r.randint(1, 5)))
Q("d184", b, g, lambda t: all(len(l.split()) == 6 and inrange(nums(l)[:2] + nums(l)[3:5], -10**9, 10**9) and 1 <= nums(l)[2] <= 10**9 and 1 <= nums(l)[5] <= 10**9 for l in body(t)) and 1 <= len(body(t)) <= 1000,
  wrong=[pt("elif d2==s: print('EXTERNAL')", "elif d2==s: print('INTERSECT')"), pt("elif d2==t: print('INTERNAL')", "elif d2==t: print('CONTAIN')"), pt("if d2==0 and r1==r2: print('SAME')", "if d2==0: print('SAME')"), pt("elif d2>t: print('INTERSECT')", "elif d2>=t: print('INTERSECT')"), code("import sys,math\nfor l in sys.stdin:\n    v=list(map(int,l.split()))\n    if len(v)!=6: continue\n    x1,y1,r1,x2,y2,r2=v;d=math.hypot(x1-x2,y1-y2)\n    if d==0 and r1==r2: print('SAME')\n    elif d>r1+r2: print('SEPARATE')\n    elif d==r1+r2: print('EXTERNAL')\n    elif d>abs(r1-r2): print('INTERSECT')\n    elif d==abs(r1-r2): print('INTERNAL')\n    else: print('CONTAIN')\n", "用浮點 hypot（大座標會誤判）")],
  nrand=12)

# ---------- d186 ----------
def g(r):
    n = r.randint(1, 8)
    perm = list(range(1, n + 1)); r.shuffle(perm)
    return f"{n}\n" + "".join(f"{perm[r.randint(0, v - 2)]} {perm[v - 1]}\n" for v in range(2, n + 1))
def b(t):
    ls = body(t)
    n = int(ls[0])
    adj = {i: [] for i in range(1, n + 1)}
    for l in ls[1:n]:
        u, v = nums(l)
        adj[u].append(v); adj[v].append(u)
    best = 0
    for s in range(1, n + 1):
        dist = {s: 0}
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in dist:
                    dist[v] = dist[u] + 1; q.append(v)
        best = max(best, max(dist.values()))
    return f"{best}\n"
Q("d186", b, g, lambda t: len(body(t)) == int(body(t)[0]) and 1 <= int(body(t)[0]) <= 10**5 and (int(body(t)[0]) == 1 or len(set(x for l in body(t)[1:] for x in nums(l))) == int(body(t)[0])),
  wrong=[pt("a,_=bfs(1);print(bfs(a)[1])", "print(bfs(1)[1])"), pt("a,_=bfs(1);print(bfs(a)[1])", "a,_=bfs(1);print(bfs(a)[1]+1)"), pt("u=q.popleft();last=u", "u=q.popleft();last=u if dist[u]<2 else last")],
  big=[lambda r: "20000\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 20000)), lambda r: "20000\n" + "".join(f"{r.randint(1, i - 1)} {i}\n" for i in range(2, 20001)), lambda r: "20000\n" + "".join(f"1 {i}\n" for i in range(2, 20001))])

# ---------- d187 ----------
def g(r):
    n = r.randint(1, 8)
    perm = list(range(1, n + 1)); r.shuffle(perm)
    es = [(perm[r.randint(0, v - 2)], perm[v - 1]) for v in range(2, n + 1)]
    q = r.randint(1, 5)
    return f"{n} {q}\n" + "".join(f"{u} {v}\n" for u, v in es) + "".join(f"{r.randint(1, n)} {r.randint(1, n)}\n" for _ in range(q))
def b(t):
    ls = body(t)
    n, q = nums(ls[0])
    adj = {i: [] for i in range(1, n + 1)}
    for l in ls[1:n]:
        u, v = nums(l)
        adj[u].append(v); adj[v].append(u)
    par, dep = {1: 0}, {1: 0}
    st = [1]
    while st:
        u = st.pop()
        for v in adj[u]:
            if v not in par:
                par[v] = u; dep[v] = dep[u] + 1; st.append(v)
    o = ""
    for l in ls[n:n + q]:
        a, c = nums(l)
        while a != c:
            if dep[a] >= dep[c]:
                a = par[a]
            else:
                c = par[c]
        o += f"{a}\n"
    return o
def v(t):
    ls = body(t)
    n, q = nums(ls[0])
    return 1 <= n <= 5 * 10**4 and 1 <= q <= 5 * 10**4 and len(ls) == n + q and all(len(nums(x)) == 2 and 1 <= nums(x)[0] <= n and 1 <= nums(x)[1] <= n for x in ls[1:])
Q("d187", b, g, v,
  wrong=[pt("if df>>k&1: a=up[k][a]", "if df>>k&1: a=up[0][a]"), pt("if a==b: print(a);continue", "if a==b: print(1);continue"), pt("if up[k][a]!=up[k][b]: a=up[k][a];b=up[k][b]", "if up[k][a]!=up[k][b]: a=up[k][a]"), pt("print(up[0][a])", "print(a)")],
  slow=[code("import sys\nfrom collections import deque\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1]);adj=[[] for _ in range(n+1)]\nfor i in range(n-1):\n    u,v=int(d[2+2*i]),int(d[3+2*i]);adj[u].append(v);adj[v].append(u)\npar=[0]*(n+1);dep=[0]*(n+1);seen=[False]*(n+1);seen[1]=True;Q=deque([1])\nwhile Q:\n    u=Q.popleft()\n    for v in adj[u]:\n        if not seen[v]: seen[v]=True;par[v]=u;dep[v]=dep[u]+1;Q.append(v)\np=2+2*(n-1)\nfor _ in range(q):\n    a,b=int(d[p]),int(d[p+1]);p+=2\n    while a!=b:\n        if dep[a]>=dep[b]: a=par[a]\n        else: b=par[b]\n    print(a)\n", "一步一步往上爬（鏈狀樹 O(nq)）")],
  big=[lambda r: "20000 20000\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 20000)) + "".join(f"{r.randint(1, 20000)} {r.randint(1, 20000)}\n" for _ in range(20000)), lambda r: "20000 20000\n" + "".join(f"{r.randint(1, i - 1)} {i}\n" for i in range(2, 20001)) + "".join(f"{r.randint(1, 20000)} {r.randint(1, 20000)}\n" for _ in range(20000))], nrand=8)

# ---------- d189 ----------
def g(r):
    T_ = word(r, 1, 12, "ab")
    return T_ + "\n" + word(r, 1, min(3, len(T_)), "ab") + "\n"
def b(t):
    T, P = body(t)
    return f"{sum(1 for i in range(len(T) - len(P) + 1) if T[i:i + len(P)] == P)}\n"
Q("d189", b, g, lambda t: len(body(t)) == 2 and all(x.islower() and x.isalpha() for x in body(t)) and 1 <= len(body(t)[1]) <= len(body(t)[0]) <= 2 * 10**5,
  wrong=[pt("while k and s[i]!=s[k]: k=pi[k-1]", "while k and s[i]!=s[k]: k=0"), pt("if k==m: c+=1", "if k==m: c+=1;k=0"), pt("s=P+'#'+T", "s=P+T")],
  slow=[code("T=input();P=input();c=0;m=len(P)\nfor i in range(len(T)-m+1):\n    j=0\n    while j<m and T[i+j]==P[j]: j+=1\n    if j==m: c+=1\nprint(c)\n", "逐位置比對 O(nm)")],
  big=[lambda r: "a" * 200000 + "\n" + "a" * 100000 + "\n", lambda r: "".join(r.choice("ab") for _ in range(50000)) + "\n" + "abab\n", lambda r: "ab" * 25000 + "\n" + "ab" * 10000 + "b\n"], nrand=10)

# ---------- d190 ----------
def g(r):
    return word(r, 1, 12, "ab") + "\n"
def b(t):
    s = body(t)[0]
    tot = 0
    for i in range(len(s)):
        k = 0
        while i + k < len(s) and s[k] == s[i + k]:
            k += 1
        tot += k
    return f"{tot}\n"
Q("d190", b, g, lambda t: len(body(t)) == 1 and body(t)[0].islower() and body(t)[0].isalpha() and 1 <= len(body(t)[0]) <= 2 * 10**5,
  wrong=[pt("z[0]=n", "z[0]=0"), pt("if i<=r: z[i]=min(r-i+1,z[i-l])", "if i<=r: z[i]=z[i-l]"), pt("if i+z[i]-1>r: l,r=i,i+z[i]-1", "if i+z[i]-1>r: l,r=i,i+z[i]")],
  slow=[code("s=input();n=len(s);tot=0\nfor i in range(n):\n    k=0\n    while i+k<n and s[k]==s[i+k]: k+=1\n    tot+=k\nprint(tot)\n", "每個後綴暴力比對 O(n²)")],
  big=[lambda r: "a" * 200000 + "\n", lambda r: "".join(r.choice("ab") for _ in range(50000)) + "\n", lambda r: "ab" * 25000 + "\n"], nrand=8)

# ---------- d191 ----------
def g(r):
    n, q = r.randint(1, 6), r.randint(1, 5)
    return f"{n} {q}\n" + "".join(word(r, 1, 4, "ab") + "\n" for _ in range(n + q))
def b(t):
    ls = body(t)
    n, q = nums(ls[0])
    W = ls[1:1 + n]
    return "".join(f"{sum(1 for w in W if w.startswith(x))}\n" for x in ls[1 + n:1 + n + q])
def v(t):
    ls = body(t)
    n, q = nums(ls[0])
    return 1 <= n <= 5 * 10**4 and 1 <= q <= 5 * 10**4 and len(ls) == 1 + n + q and all(x.islower() and x.isalpha() for x in ls[1:]) and sum(len(x) for x in ls[1:1 + n]) <= 2 * 10**5 and sum(len(x) for x in ls[1 + n:]) <= 2 * 10**5
def big191(r):
    n = q = 20000
    return f"{n} {q}\n" + "".join(word(r, 1, 5, "ab") + "\n" for _ in range(n + q))
Q("d191", b, g, v,
  wrong=[pt("bisect.bisect_left(W,x+'{')", "bisect.bisect_left(W,x+'z')"), pt("bisect.bisect_left(W,x+'{')-bisect.bisect_left(W,x)", "bisect.bisect_right(W,x+'{')-bisect.bisect_right(W,x)"), pt("W=sorted(d[2:2+n])", "W=sorted(set(d[2:2+n]))")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1]);W=d[2:2+n]\nfor x in d[2+n:2+n+q]: print(sum(1 for w in W if w.startswith(x)))\n", "每個查詢掃過全部單字 O(nq)")],
  big=[big191, lambda r: "20000 20000\n" + ("a\n" * 20000) + ("a\n" * 20000)], nrand=8)

# ---------- d193 ----------
def g(r):
    t = r.randint(1, 3)
    out = [str(t)]
    for _ in range(t):
        n = r.randint(1, 3)
        out += [str(n), sp(ints(r, n, 0, 4))]
    return "\n".join(out) + "\n"
def b(t):
    ls = body(t)
    T = int(ls[0])
    from functools import lru_cache
    @lru_cache(None)
    def win(state):
        for i, x in enumerate(state):
            for k in range(1, x + 1):
                ns = tuple(sorted(state[:i] + (x - k,) + state[i + 1:]))
                if not win(ns):
                    return True
        return False
    o = ""
    for k in range(T):
        piles = tuple(sorted(nums(ls[2 + 2 * k])))
        o += ("FIRST" if win(piles) else "SECOND") + "\n"
    return o
def v(t):
    ls = body(t)
    T = int(ls[0])
    if not (1 <= T <= 1000 and len(ls) == 1 + 2 * T):
        return False
    return all(1 <= int(ls[1 + 2 * k]) <= 1000 and len(nums(ls[2 + 2 * k])) == int(ls[1 + 2 * k]) and inrange(nums(ls[2 + 2 * k]), 0, 10**9) for k in range(T))
Q("d193", b, g, v,
  wrong=[pt("print('FIRST' if x else 'SECOND')", "print('FIRST' if x%2 else 'SECOND')"), pt("x^=int(v)", "x+=int(v)"), pt("print('FIRST' if x else 'SECOND')", "print('SECOND' if x else 'FIRST')")],
  big=[lambda r: "1000\n" + "".join(f"1000\n{sp(ints(r, 1000, 0, 10**9))}\n" for _ in range(1))[:0] + "".join(f"{3}\n{sp(ints(r, 3, 0, 10**9))}\n" for _ in range(1000))], nrand=8)

# ---------- d194 ----------
def g(r):
    n = r.randint(1, 7)
    perm = list(range(1, n + 1)); r.shuffle(perm)
    return f"{n}\n{sp(ints(r, n, -9, 9))}\n" + "".join(f"{perm[r.randint(0, v - 2)]} {perm[v - 1]}\n" for v in range(2, n + 1))
def b(t):
    ls = body(t)
    n = int(ls[0])
    w = [0] + nums(ls[1])
    adj = {i: [] for i in range(1, n + 1)}
    for l in ls[2:1 + n]:
        u, v = nums(l)
        adj[u].append(v); adj[v].append(u)
    best = -10**30
    def paths(u, vis, s):
        nonlocal best
        best = max(best, s)
        for v in adj[u]:
            if v not in vis:
                paths(v, vis | {v}, s + w[v])
    for s in range(1, n + 1):
        paths(s, {s}, w[s])
    return f"{best}\n"
Q("d194", b, g, lambda t: len(body(t)) == int(body(t)[0]) + 1 and 1 <= int(body(t)[0]) <= 10**5 and len(nums(body(t)[1])) == int(body(t)[0]) and inrange(nums(body(t)[1]), -10**9, 10**9) and len(set(x for l in body(t)[2:] for x in nums(l))) in (0, int(body(t)[0])),
  wrong=[pt("elif c>m2[p]: m2[p]=c", "pass"), pt("best=max(best,w[u]+m1[u]+m2[u])", "best=max(best,w[u]+m1[u])"), pt("best=-10**30", "best=0"), pt("down[u]=w[u]+m1[u]", "down[u]=w[u]+m1[u]+m2[u]")],
  big=[lambda r: "20000\n" + sp(ints(r, 20000, -10**9, 10**9)) + "\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 20000)), lambda r: "20000\n" + sp(ints(r, 20000, -10**9, 10**9)) + "\n" + "".join(f"{r.randint(1, i - 1)} {i}\n" for i in range(2, 20001)), lambda r: "20000\n" + sp(ints(r, 20000, -10**9, -1)) + "\n" + "".join(f"1 {i}\n" for i in range(2, 20001))], nrand=8)

# ---------- d195 ----------
def g(r):
    n, q = r.randint(1, 6), r.randint(1, 8)
    ops = []
    for _ in range(q):
        if r.random() < 0.5:
            ops.append(f"1 {r.randint(1, n)} {r.randint(-5, 5)}")
        else:
            l = r.randint(1, n)
            ops.append(f"2 {l} {r.randint(l, n)}")
    return f"{n} {q}\n{sp(ints(r, n, -5, 5))}\n" + "\n".join(ops) + "\n"
def b(t):
    ls = body(t)
    n, q = nums(ls[0])
    a = nums(ls[1])
    o = ""
    for l in ls[2:2 + q]:
        c, x, y = nums(l)
        if c == 1:
            a[x - 1] += y
        else:
            o += f"{sum(a[x - 1:y])}\n"
    return o
def v(t):
    ls = body(t)
    n, q = nums(ls[0])
    if not (1 <= n <= 5 * 10**4 and 1 <= q <= 5 * 10**4 and len(ls) == 2 + q and len(nums(ls[1])) == n and inrange(nums(ls[1]), -10**9, 10**9)):
        return False
    for l in ls[2:]:
        c, x, y = nums(l)
        if c == 1 and not (1 <= x <= n and abs(y) <= 10**9):
            return False
        if c == 2 and not (1 <= x <= y <= n):
            return False
        if c not in (1, 2):
            return False
    return True
def big195(r):
    n = q = 40000
    ops = []
    for _ in range(q):
        if r.random() < 0.1:
            ops.append(f"1 {r.randint(1, n)} {r.randint(-10**9, 10**9)}")
        else:
            ops.append(f"2 {r.randint(1, 100)} {r.randint(n - 100, n)}")
    return f"{n} {q}\n{sp(ints(r, n, -10**9, 10**9))}\n" + "\n".join(ops) + "\n"
Q("d195", b, g, v,
  wrong=[pt("while i<=n: T[i]+=v;i+=i&-i", "while i<n: T[i]+=v;i+=i&-i"), pt("print(qs(int(d[p+2]))-qs(int(d[p+1])-1))", "print(qs(int(d[p+2]))-qs(int(d[p+1])))"), pt("while i>0: s+=T[i];i-=i&-i", "while i>0: s+=T[i];i-=1"), pt("if t==1: add(int(d[p+1]),int(d[p+2]))", "if t==1: add(int(d[p+1]),1)")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1]);a=[int(x) for x in d[2:2+n]];p=2+n\nfor _ in range(q):\n    t=int(d[p])\n    if t==1: a[int(d[p+1])-1]+=int(d[p+2])\n    else: print(sum(a[int(d[p+1])-1:int(d[p+2])]))\n    p+=3\n", "每次查詢直接加總")],
  big=[big195], nrand=8)

# ---------- d196 ----------
def g(r):
    n, q = r.randint(1, 6), r.randint(1, 8)
    ops = []
    for _ in range(q):
        if r.random() < 0.4:
            ops.append(f"1 {r.randint(1, n)} {r.randint(-5, 5)}")
        else:
            l = r.randint(1, n)
            ops.append(f"2 {l} {r.randint(l, n)}")
    return f"{n} {q}\n{sp(ints(r, n, -5, 5))}\n" + "\n".join(ops) + "\n"
def b(t):
    ls = body(t)
    n, q = nums(ls[0])
    a = nums(ls[1])
    o = ""
    for l in ls[2:2 + q]:
        c, x, y = nums(l)
        if c == 1:
            a[x - 1] = y
        else:
            o += f"{min(a[x - 1:y])}\n"
    return o
Q("d196", b, g, v,
  wrong=[pt("if l&1: m=min(m,t[l]);l+=1", "if l&1: m=min(m,t[l])"), pt("while i>1: i>>=1;t[i]=min(t[2*i],t[2*i+1])", "pass"), pt("l=N+a-1;r=N+b", "l=N+a-1;r=N+b-1"), pt("i=N+a-1;t[i]=b", "i=N+a-1;t[i]=min(t[i],b)")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1]);a=[int(x) for x in d[2:2+n]];p=2+n\nfor _ in range(q):\n    t=int(d[p])\n    if t==1: a[int(d[p+1])-1]=int(d[p+2])\n    else: print(min(a[int(d[p+1])-1:int(d[p+2])]))\n    p+=3\n", "每次查詢直接 min(切片)")],
  big=[big195], nrand=8)


# =============================== 補強的六題 ===============================
# ---------- d127 ----------
def g(r):
    n = r.randint(1, 7)
    out = []
    for _ in range(n):
        s = r.randint(0, 8)
        out.append(f"{s} {s + r.randint(1, 4)}")
    return f"{n}\n" + "\n".join(out) + "\n"
def b(t):
    ls = body(t)
    n = int(ls[0])
    iv = [tuple(nums(x)) for x in ls[1:1 + n]]
    pts = {s for s, _ in iv}
    return f"{max(sum(1 for s, e in iv if s <= p < e) for p in pts)}\n"
Q("d127", b, g, lambda t: len(body(t)) == 1 + int(body(t)[0]) and 1 <= int(body(t)[0]) <= 10**5 and all(len(nums(x)) == 2 and 0 <= nums(x)[0] < nums(x)[1] <= 10**9 for x in body(t)[1:]),
  wrong=[pt("if h and h[0]<=s:", "if h and h[0]<s:"), pt("print(len(h))", "print(len(h)+1)"), pt("iv=sorted((int(d[1+2*i]),int(d[2+2*i])) for i in range(n))", "iv=sorted((int(d[2+2*i]),int(d[1+2*i])) for i in range(n))"), pt("heapq.heapreplace(h,e)", "heapq.heappush(h,e)")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nn=int(d[0]);iv=sorted((int(d[1+2*i]),int(d[2+2*i])) for i in range(n));rooms=[]\nfor s,e in iv:\n    for k in range(len(rooms)):\n        if rooms[k]<=s: rooms[k]=e;break\n    else: rooms.append(e)\nprint(len(rooms))\n", "線性找空房間 O(n·房間數)")],
  big=[lambda r: "20000\n" + "".join(f"{s} {s + 10**9 // 2}\n" for s in (r.randint(0, 10**9 // 2 - 1) for _ in range(20000))), lambda r: "20000\n" + "".join(f"{i} {i + 1}\n" for i in range(20000))], nrand=8)

# ---------- d151 ----------
def g(r):
    n = r.randint(1, 6)
    m = r.randint(1, 6)
    return f"{n} {m}\n" + "".join(f"{r.randint(1, n)} {r.randint(1, n)}\n" for _ in range(m))
def b(t):
    ls = body(t)
    n, m = nums(ls[0])
    comp = list(range(n + 1))
    o = ""
    for l in ls[1:1 + m]:
        a, c = nums(l)
        ca, cb = comp[a], comp[c]
        if ca != cb:
            comp = [ca if x == cb else x for x in comp]
        o += f"{max(Counter(comp[1:]).values())}\n"
    return o
Q("d151", b, g, lambda t: (lambda ls, n, m: 1 <= n <= 10**5 and 1 <= m <= 10**5 and len(ls) == 1 + m and all(len(nums(x)) == 2 and 1 <= nums(x)[0] <= n and 1 <= nums(x)[1] <= n for x in ls[1:]))(body(t), *nums(body(t)[0])),
  wrong=[pt("p[b]=a;sz[a]+=sz[b];best=max(best,sz[a])", "p[b]=a;sz[a]+=sz[b]"), pt("best=1\n", "best=0\n"), pt("    print(best)", "    print(sz[1])"), pt("if sz[a]<sz[b]: a,b=b,a\n        p[b]=a;sz[a]+=sz[b];best=max(best,sz[a])", "p[b]=a;sz[a]+=1;best=max(best,sz[a])")],
  slow=[code("import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1]);comp=list(range(n+1));cnt=[1]*(n+1);best=1\nfor i in range(m):\n    a,b=comp[int(d[2+2*i])],comp[int(d[3+2*i])]\n    if a!=b:\n        for k in range(1,n+1):\n            if comp[k]==b: comp[k]=a\n        cnt[a]+=cnt[b];best=max(best,cnt[a])\n    print(best)\n", "合併時整個陣列重貼標籤 O(nm)")],
  big=[lambda r: "30000 30000\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 30000)) + "1 1\n", lambda r: "30000 30000\n" + "".join(f"{r.randint(1, 30000)} {r.randint(1, 30000)}\n" for _ in range(30000))], nrand=8)

# ---------- d153 ----------
def g(r):
    n = r.randint(1, 6)
    perm = list(range(1, n + 1)); r.shuffle(perm)
    es = []
    for _ in range(r.randint(0, 7)):
        a, c = r.randint(0, n - 1), r.randint(0, n - 1)
        if r.random() < 0.85 and a > c:
            a, c = c, a
        es.append((perm[a], perm[c]))
    return f"{n} {len(es)}\n" + "".join(f"{u} {v}\n" for u, v in es)
def b(t):
    ls = body(t)
    n, m = nums(ls[0])
    es = [tuple(nums(x)) for x in ls[1:1 + m]]
    cnt = 0
    for p in itertools.permutations(range(1, n + 1)):
        pos = {v: i for i, v in enumerate(p)}
        if all(pos[u] < pos[v] for u, v in es):
            cnt += 1
    return ("CYCLE" if cnt == 0 else "UNIQUE" if cnt == 1 else "MULTIPLE") + "\n"
Q("d153", b, g, lambda t: (lambda ls, n, m: 1 <= n <= 10**5 and 0 <= m <= 2 * 10**5 and len(ls) == 1 + m and graph_lines_ok(ls, n, m))(body(t), *nums(body(t)[0])),
  wrong=[pt("print('CYCLE' if done<n else 'MULTIPLE' if multi else 'UNIQUE')", "print('MULTIPLE' if multi else 'CYCLE' if done<n else 'UNIQUE')"), pt("if len(q)>1: multi=True", "if len(q)>2: multi=True"), pt("print('CYCLE' if done<n else 'MULTIPLE' if multi else 'UNIQUE')", "print('CYCLE' if done<n else 'UNIQUE')")],
  big=[lambda r: "20000 19999\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 20000)), lambda r: "20000 19999\n" + "".join(f"1 {i}\n" for i in range(2, 20001)), lambda r: "20000 20000\n" + "".join(f"{i} {i + 1}\n" for i in range(1, 20000)) + "20000 1\n"], nrand=8)

# ---------- d158 ----------
def g(r):
    n = r.randint(1, 5)
    es = [(r.randint(1, v - 1), v, r.randint(1, 3)) for v in range(2, n + 1)] if n > 1 else []
    for _ in range(r.randint(0, 5)):
        es.append((r.randint(1, n), r.randint(1, n), r.randint(1, 3)))
    r.shuffle(es)
    return f"{n} {len(es)}\n" + "".join(f"{u} {v} {w}\n" for u, v, w in es)
def b(t):
    ls = body(t)
    n, m = nums(ls[0])
    es = [tuple(nums(x)) for x in ls[1:1 + m]]
    best, cnt = None, 0
    for comb in itertools.combinations(range(m), n - 1):
        par = list(range(n + 1))
        def f(x):
            while par[x] != x:
                x = par[x]
            return x
        ok = True
        for k in comb:
            u, v, w = es[k]
            a, c = f(u), f(v)
            if a == c:
                ok = False
                break
            par[a] = c
        if ok:
            tot = sum(es[k][2] for k in comb)
            if best is None or tot < best:
                best, cnt = tot, 1
            elif tot == best:
                cnt += 1
    return f"{best} {'UNIQUE' if cnt == 1 else 'MULTIPLE'}\n"
def v(t):
    ls = body(t)
    n, m = nums(ls[0])
    if not (1 <= n <= 10**4 and n - 1 <= m <= 5 * 10**4 and len(ls) == 1 + m and graph_lines_ok(ls, n, m, 3, 10**6)):
        return False
    par = list(range(n + 1))
    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for l in ls[1:]:
        a, c = f(nums(l)[0]), f(nums(l)[1])
        par[a] = c
    return len({f(i) for i in range(1, n + 1)}) == 1
def big158(r, w=10**6):
    n = 5000
    es = rand_graph(r, n, 15000, w, connected=True)
    return f"{n} {len(es)}\n" + "".join(f"{u} {v} {ww}\n" for u, v, ww in es)
Q("d158", b, g, v,
  wrong=[pt("if cand!=used: uniq=False", "pass"), pt("cand=sum(1 for k in range(i,j) if f(E[k][1])!=f(E[k][2]))", "cand=j-i"), pt("print(t,'UNIQUE' if uniq else 'MULTIPLE')", "print(t,'UNIQUE')"), pt("if cand!=used: uniq=False", "if cand>used+1: uniq=False")],
  big=[big158, lambda r: big158(r, 3), lambda r: "5000 4999\n" + "".join(f"{i} {i + 1} {r.randint(1, 10**6)}\n" for i in range(1, 5000))], nrand=8)

# ---------- d174 ----------
def g(r):
    t = r.randint(1, 3)
    out = [str(t)]
    for _ in range(t):
        k = r.randint(1, 4)
        L_ = r.randint(k + 1, 12)
        pos = sorted(r.sample(range(1, L_), k))
        out += [f"{L_} {k}", sp(pos)]
    return "\n".join(out) + "\n"
def b(t):
    ls = body(t)
    T = int(ls[0])
    o = ""
    for c in range(T):
        L_, k = nums(ls[1 + 2 * c])
        pos = nums(ls[2 + 2 * c])
        best = None
        for order in itertools.permutations(pos):
            pieces = [(0, L_)]
            cost = 0
            for x in order:
                for i, (a, bb) in enumerate(pieces):
                    if a < x < bb:
                        cost += bb - a
                        pieces[i:i + 1] = [(a, x), (x, bb)]
                        break
            if best is None or cost < best:
                best = cost
        o += f"{best}\n"
    return o
def v(t):
    ls = body(t)
    T = int(ls[0])
    if not (1 <= T <= 20 and len(ls) == 1 + 2 * T):
        return False
    for c in range(T):
        L_, k = nums(ls[1 + 2 * c])
        pos = nums(ls[2 + 2 * c])
        if not (1 <= k <= 100 and k < L_ <= 10**6 and len(pos) == k and pos == sorted(set(pos)) and all(0 < p < L_ for p in pos)):
            return False
    return True
Q("d174", b, g, v,
  wrong=[pt("+pos[j]-pos[i]", ""), pt("pos=[0]+[int(x) for x in d[p:p+k]]+[L]", "pos=[int(x) for x in d[p:p+k]]+[L]"), pt("min(dp[i][m]+dp[m][j] for m in range(i+1,j))", "min(dp[i][m]+dp[m][j] for m in range(i+1,j,2) or [i+1])"), pt("for ln in range(2,n):", "for ln in range(2,n-1):")],
  big=[lambda r: "5\n" + "".join(f"1000000 100\n{sp(sorted(r.sample(range(1, 1000000), 100)))}\n" for _ in range(5)), lambda r: "1\n1000000 100\n" + sp(range(1, 101)) + "\n"], nrand=8)

# ---------- d176 ----------
def g(r):
    n = r.randint(1, 5)
    es = [(u, v) for u in range(1, n + 1) for v in range(1, n + 1) if u != v and r.random() < 0.6]
    return f"{n} {len(es)}\n" + "".join(f"{u} {v}\n" for u, v in es)
def b(t):
    ls = body(t)
    n, m = nums(ls[0])
    E = {tuple(nums(x)) for x in ls[1:1 + m]}
    if n == 1:
        return "1\n"
    c = sum(1 for p in itertools.permutations(range(2, n + 1)) if all(((a, b_) in E) for a, b_ in zip((1,) + p, p)))
    return f"{c % MOD}\n"
Q("d176", b, g, lambda t: (lambda ls, n, m: 1 <= n <= 15 and 0 <= m <= n * (n - 1) and len(ls) == 1 + m and len({tuple(nums(x)) for x in ls[1:]}) == m and all(len(nums(x)) == 2 and 1 <= nums(x)[0] <= n and 1 <= nums(x)[1] <= n and nums(x)[0] != nums(x)[1] for x in ls[1:]))(body(t), *nums(body(t)[0])),
  wrong=[pt("dp[1][0]=1", "dp[1][0]=2"), pt("nxt=adj[v]&~mask", "nxt=adj[v]"), pt("print(sum(dp[(1<<n)-1])%M)", "print(max(dp[(1<<n)-1])%M)")],
  big=[lambda r: "15 " + str(15 * 14) + "\n" + "".join(f"{u} {v}\n" for u in range(1, 16) for v in range(1, 16) if u != v)], nrand=8)
