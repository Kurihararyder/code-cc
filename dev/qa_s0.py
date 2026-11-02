"""階段 0（d001–d030）的品質檢查登記。"""
import math
import random
from fractions import Fraction

from qa import Q, pt, code, ints, sp, L, word, nums, toks, rows, inrange

UP = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOW = "abcdefghijklmnopqrstuvwxyz"


def lines_of(t):
    return [x for x in t.split("\n")]


def body(t):
    """去掉最後一個換行後的各行（保留空行）。"""
    ls = t.split("\n")
    if ls and ls[-1] == "":
        ls.pop()
    return ls


def mix(r, specials, lo, hi):
    return r.choice(specials) if r.random() < 0.3 else r.randint(lo, hi)


# d001
Q("d001", lambda t: "Hello, " + t.strip() + "!\n",
  lambda r: word(r, 1, 20, LOW + UP) + "\n",
  lambda t: len(body(t)) == 1 and t.strip().isalpha() and len(t.strip()) <= 20 and t.endswith("\n"),
  wrong=[pt("Hello, ", "Hello ,"), pt("!'", "'"), pt("Hello", "hello")])

# d002
def g(r):
    big = [10**18, -10**18, 0, 10**17 + 7]
    return "".join(f"{mix(r, big, -100, 100)} {mix(r, big, -100, 100)}\n" for _ in range(r.randint(1, 6)))
Q("d002", lambda t: "".join(f"{int(a) + int(b)}\n" for a, b in (l.split() for l in body(t))), g,
  lambda t: all(len(l.split()) == 2 and inrange(nums(l), -10**18, 10**18) for l in body(t)) and len(body(t)) >= 1,
  wrong=[pt("int(p[0])+int(p[1])", "int(float(p[0])+float(p[1]))"), pt("int(p[0])+int(p[1])", "abs(int(p[0]))+abs(int(p[1]))")])

# d003
def g(r):
    return f"{mix(r, [1, 10**6], 1, 30)} {mix(r, [1, 10**6], 1, 30)}\n"
Q("d003", lambda t: "{} {}\n".format(nums(t)[0] * nums(t)[1], 2 * (nums(t)[0] + nums(t)[1])), g,
  lambda t: len(nums(t)) == 2 and inrange(nums(t), 1, 10**6) and len(body(t)) == 1,
  wrong=[pt("2*(w+h)", "w+h"), pt("w*h,", "w+h,"), pt("print(w*h,2*(w+h))", "print(w*h);print(2*(w+h))")])

# d004
def g(r):
    return "".join(f"{mix(r, [-100, 100, 0, -40], -100, 100)}\n" for _ in range(r.randint(1, 5)))
Q("d004", lambda t: "".join("%.1f\n" % (int(x) * 1.8 + 32) for x in body(t)), g,
  lambda t: all(l.strip().lstrip("-").isdigit() and -100 <= int(l) <= 100 for l in body(t)) and body(t) != [],
  wrong=[pt("*9/5", "*9//5"), pt(":.1f", ":.0f"), pt("*9/5+32", "*9/5-32")])

# d005
def g(r):
    return "".join(f"{mix(r, [0, -1, 1, 10**9, -10**9, 999999999], -50, 50)}\n" for _ in range(r.randint(1, 6)))
Q("d005", lambda t: "".join(("even\n" if int(x) % 2 == 0 else "odd\n") for x in body(t)), g,
  lambda t: all(inrange(nums(l), -10**9, 10**9) and len(l.split()) == 1 for l in body(t)) and body(t) != [],
  wrong=[pt("int(l)%2==0", "int(l)>0 and int(l)%2==0"), pt("'even' if int(l)%2==0 else 'odd'", "'even' if int(l)%2==0 and int(l)!=0 else 'odd'"), pt("'even' if int(l)%2==0 else 'odd'", "'even' if abs(int(l))%2==0 and int(l)>=0 else 'odd'")])

# d006
def g(r):
    return "".join(sp([mix(r, [0, -10**9, 10**9], -9, 9) for _ in range(3)]) + "\n" for _ in range(r.randint(1, 5)))
Q("d006", lambda t: "".join(f"{max(nums(l))}\n" for l in body(t)), g,
  lambda t: all(len(l.split()) == 3 and inrange(nums(l), -10**9, 10**9) for l in body(t)) and body(t) != [],
  wrong=[pt("max(map(int,p))", "max(0,*map(int,p))"), pt("max(map(int,p))", "max(map(int,p[:2]))"), pt("max(map(int,p))", "int(max(p))")])

# d007
def leap(y):
    return "yes" if (y % 400 == 0) or (y % 4 == 0 and y % 100 != 0) else "no"
def g(r):
    return "".join(f"{mix(r, [4, 100, 400, 1900, 2000, 1, 100000, 99999, 1600, 2100], 1, 3000)}\n" for _ in range(r.randint(1, 6)))
Q("d007", lambda t: "".join(leap(int(x)) + "\n" for x in body(t)), g,
  lambda t: all(len(l.split()) == 1 and 1 <= int(l) <= 10**5 for l in body(t)) and body(t) != [],
  wrong=[pt("y%4==0 and y%100!=0", "y%4==0"), pt("or y%400==0", ""), pt("(y%4==0 and y%100!=0) or y%400==0", "y%4==0 and (y%100!=0 or y%400!=0)"), pt("or y%400==0", "or y%200==0")])

# d008
def grade(s):
    return "A" if s >= 90 else "B" if s >= 80 else "C" if s >= 70 else "D" if s >= 60 else "F"
def g(r):
    return "".join(f"{mix(r, [0, 59, 60, 69, 70, 79, 80, 89, 90, 100], 0, 100)}\n" for _ in range(r.randint(1, 8)))
Q("d008", lambda t: "".join(grade(int(x)) + "\n" for x in body(t)), g,
  lambda t: all(len(l.split()) == 1 and 0 <= int(l) <= 100 for l in body(t)) and body(t) != [],
  wrong=[pt("s>=90", "s>90"), pt("s>=80", "s>80"), pt("s>=70", "s>70"), pt("s>=60", "s>60"), pt("else 'F'", "else 'E'")])

# d009
def g(r):
    return "".join(f"{mix(r, [1, 100000, 99999], 1, 200)}\n" for _ in range(r.randint(1, 5)))
Q("d009", lambda t: "".join(f"{sum(range(1, int(x) + 1))}\n" for x in body(t)), g,
  lambda t: all(len(l.split()) == 1 and 1 <= int(l) <= 10**5 for l in body(t)) and body(t) != [],
  wrong=[pt("n*(n+1)//2", "n*(n-1)//2"), pt("n*(n+1)//2", "(n+1)*n//2+1")])

# d010
def g(r):
    return "".join(f"{mix(r, [0, 1, 20, 19], 0, 20)}\n" for _ in range(r.randint(1, 5)))
Q("d010", lambda t: "".join(f"{math.prod(range(1, int(x) + 1))}\n" for x in body(t)), g,
  lambda t: all(len(l.split()) == 1 and 0 <= int(l) <= 20 for l in body(t)) and body(t) != [],
  wrong=[code("import sys\nfor l in sys.stdin:\n    if l.strip():\n        f=1\n        for i in range(1,int(l)): f*=i\n        print(f)\n"),
         code("import sys\nfor l in sys.stdin:\n    if l.strip():\n        f=0\n        for i in range(1,int(l)+1): f*=i\n        print(f)\n"),
         code("import sys\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l)\n        f=1\n        for i in range(2,n+1): f*=i\n        print(f if n else 0)\n")])

# d011
def g(r):
    return f"{r.randint(1, 9)}\n"
Q("d011", lambda t: "".join(f"{int(t)}*{i}={int(t) * i}\n" for i in range(1, 10)), g,
  lambda t: len(body(t)) == 1 and 1 <= int(t) <= 9,
  wrong=[pt("{n}*{i}={n*i}", "{n} * {i} = {n*i}"), pt("range(1,10)", "range(1,9)"), pt("range(1,10)", "range(0,9)")])

# d012
def g(r):
    return "".join(f"{mix(r, [0, 10**18 - 1, 10**17, 9, 1000], 0, 10**r.randint(1, 17))}\n" for _ in range(r.randint(1, 5)))
Q("d012", lambda t: "".join(f"{sum(int(c) for c in l)}\n" for l in body(t)), g,
  lambda t: all(l.isdigit() and int(l) < 10**18 and (l == "0" or l[0] != "0") for l in body(t)) and body(t) != [],
  wrong=[pt("sum(map(int,l.strip()))", "sum(map(int,l.strip()))%10"), pt("sum(map(int,l.strip()))", "len(l.strip())")])

# d013
def rev(s):
    neg = s.startswith("-")
    v = int((s[1:] if neg else s)[::-1])
    return str(-v if neg else v)
def g(r):
    out = []
    for _ in range(r.randint(1, 5)):
        k = r.choice([0, 1, 1200, -120, -5, 10**17 + 90, -(10**17), 7000, -90010, 123456789012345678 // 10])
        out.append(str(k if r.random() < 0.6 else r.randint(-10**r.randint(1, 17), 10**r.randint(1, 17))))
    return "\n".join(out) + "\n"
Q("d013", lambda t: "".join(rev(l) + "\n" for l in body(t)), g,
  lambda t: all(len(l.split()) == 1 and abs(int(l)) < 10**18 for l in body(t)) and body(t) != [],
  wrong=[pt("print(-r if neg and r else r)", "print(r)"), code("import sys\nfor l in sys.stdin:\n    s=l.strip()\n    if s: print(s[::-1])\n"),
         code("import sys\nfor l in sys.stdin:\n    s=l.strip()\n    if s: print(s[::-1].lstrip('0') or '0')\n")])

# d014
def g(r):
    alpha = "aeiouAEIOUbcdxyz ,.!"
    return "".join("".join(r.choice(alpha) for _ in range(r.randint(0, 12))) + "\n" for _ in range(r.randint(1, 5)))
Q("d014", lambda t: "".join(f"{sum(1 for c in l if c.lower() in 'aeiou')}\n" for l in body(t)), g,
  lambda t: len(body(t)) >= 1 and t.endswith("\n"),
  wrong=[pt("l.lower()", "l"), pt("'aeiou'", "'aeio'"), code("import sys\nfor l in sys.stdin:\n    if l.strip(): print(sum(c in 'aeiou' for c in l.lower()))\n"), pt("'aeiou'", "'aeiouy'")])

# d015
def g(r):
    out = []
    for _ in range(r.randint(1, 5)):
        h = word(r, 1, 6, "aAbB")
        s = h + (word(r, 0, 1, "ab") if r.random() < 0.5 else "") + h[::-1] if r.random() < 0.5 else word(r, 1, 7, "aAb")
        out.append(s)
    return "\n".join(out) + "\n"
Q("d015", lambda t: "".join(("YES\n" if l == l[::-1] else "NO\n") for l in body(t)), g,
  lambda t: all(1 <= len(l) <= 1000 and " " not in l for l in body(t)) and body(t) != [],
  wrong=[pt("s==s[::-1]", "s.lower()==s[::-1].lower()"), pt("s==s[::-1]", "s[:len(s)//2]==s[::-1][:len(s)//2+1]"), pt("s==s[::-1]", "len(s)>1 and s==s[::-1]")])

# d016
def caesar(k, s):
    o = []
    for c in s:
        if c in LOW:
            o.append(LOW[(LOW.index(c) + k) % 26])
        elif c in UP:
            o.append(UP[(UP.index(c) + k) % 26])
        else:
            o.append(c)
    return "".join(o)
def g(r):
    s = "".join(r.choice(LOW + UP + " ,.!0123") for _ in range(r.randint(1, 30)))
    return f"{mix(r, [0, 26, 1000, 25, 52], 0, 1000)}\n{s}\n"
Q("d016", lambda t: caesar(int(body(t)[0]), body(t)[1]) + "\n", g,
  lambda t: len(body(t)) == 2 and 0 <= int(body(t)[0]) <= 1000 and 1 <= len(body(t)[1]) <= 1000,
  wrong=[pt("%26+97", "%26+96"), pt("elif 'A'<=c<='Z': o.append(chr((ord(c)-65+k)%26+65))", "elif 'A'<=c<='Z': o.append(chr((ord(c)-65+k)%26+65).lower())"),
         pt("(ord(c)-97+k)%26+97", "(ord(c)-97+k%26)%27+97"), pt("o.append(c)", "o.append(' ')")])

# d017
def avg_tie(a):
    x = Fraction(sum(a), len(a)) * 100
    return x - (x.numerator // x.denominator) == Fraction(1, 2)
def d017v(t):
    ls = body(t)
    if len(ls) != 2:
        return False
    n = int(ls[0])
    a = nums(ls[1])
    return len(a) == n and 1 <= n <= 1000 and not avg_tie(a) and inrange(a, -10**9, 10**9)
def g(r):
    while True:
        n = r.randint(1, 8)
        a = ints(r, n, -20, 20)
        if not avg_tie(a):
            return f"{n}\n{sp(a)}\n"
def b017(t):
    ls = body(t)
    a = nums(ls[1])
    s = Fraction(sum(a), len(a))
    q = (abs(s) * 100 * 2 + 1) // 2        # 四捨五入（已保證沒有剛好 .5）
    v = ("-" if s < 0 and q else "") + f"{q // 100}.{q % 100:02d}"
    return f"{min(a)} {max(a)} {v}\n"
Q("d017", b017, g, d017v,
  wrong=[pt("f'{sum(a)/n:.2f}'", "f'{sum(a)//n:.2f}'"), pt("min(a),max(a)", "a[0],a[-1]"), pt(":.2f", ":.1f"), pt("min(a),max(a),", "max(a),min(a),")])

# d018
def g(r):
    n = r.randint(1, 10)
    return f"{n}\n{sp(ints(r, n, -9, 9))}\n"
Q("d018", lambda t: sp(sorted(nums(body(t)[1]))) + "\n", g,
  lambda t: len(body(t)) == 2 and int(body(t)[0]) == len(nums(body(t)[1])) and 1 <= int(body(t)[0]) <= 10**5 and inrange(nums(body(t)[1]), -10**9, 10**9),
  wrong=[pt("sorted(map(int,input().split()))", "sorted(input().split())"), pt("sorted(map(int,input().split()))", "sorted(map(abs,map(int,input().split())))"), pt("print(*a)", "print(*a[::-1])")],
  big=[lambda r: f"50000\n{sp(ints(r, 50000, -10**9, 10**9))}\n"])

# d019
def g(r):
    n = r.randint(1, 12)
    return f"{n}\n{sp(ints(r, n, -4, 4))}\n"
def b019(t):
    a = nums(body(t)[1])
    o = []
    for x in a:
        if x not in o:
            o.append(x)
    return sp(o) + "\n"
Q("d019", b019, g,
  lambda t: len(body(t)) == 2 and int(body(t)[0]) == len(nums(body(t)[1])) and 1 <= int(body(t)[0]) <= 10**5,
  slow=[code("n=int(input())\no=[]\nfor x in input().split():\n    x=int(x)\n    if x not in o: o.append(x)\nprint(*o)\n", "list 查詢 O(n²)")],
  wrong=[pt("print(*o)", "print(*sorted(o))"), code("n=int(input())\nprint(*sorted(set(map(int,input().split()))))\n"), code("n=int(input())\na=input().split()\nprint(*[x for i,x in enumerate(a) if x not in a[i+1:]])\n")],
  big=[lambda r: f"50000\n{sp(range(1, 50001))}\n", lambda r: f"30000\n{sp(ints(r, 30000, 1, 20000))}\n"])

# d020
def g(r):
    ws = [word(r, 1, 3, "abAB") for _ in range(r.randint(1, 6))]
    out = []
    for _ in range(r.randint(1, 4)):
        out.append(" ".join(r.choice(ws) for _ in range(r.randint(0, 6))))
    if not any(x.strip() for x in out):
        out.append("a")
    return "\n".join(out) + "\n"
def b020(t):
    d = {}
    for w in t.split():
        d[w] = d.get(w, 0) + 1
    items = sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))
    return "".join(f"{w} {c}\n" for w, c in items)
Q("d020", b020, g,
  lambda t: 1 <= len(t.split()) <= 10**5,
  wrong=[pt("(-kv[1],kv[0])", "(-kv[1],)"), pt("(-kv[1],kv[0])", "(kv[1],kv[0])"), pt("sys.stdin.read().split()", "sys.stdin.read().lower().split()"), pt("(-kv[1],kv[0])", "(-kv[1],kv[0].lower())")],
  big=[lambda r: "\n".join(sp([word(r, 1, 2, "abcAB") for _ in range(20)]) for _ in range(5000)) + "\n"])

# d021
def isprime(n):
    if n < 2:
        return False
    return all(n % p for p in range(2, int(n ** 0.5) + 1))
def g(r):
    return "".join(f"{mix(r, [1, 2, 3, 4, 9, 25, 49, 97, 999999937, 10**9, 1000000007 - 8], 1, 200)}\n" for _ in range(r.randint(1, 6)))
Q("d021", lambda t: "".join(("YES\n" if isprime(int(x)) else "NO\n") for x in body(t)), g,
  lambda t: all(len(l.split()) == 1 and 1 <= int(l) <= 10**9 for l in body(t)) and 1 <= len(body(t)) <= 100,
  wrong=[pt("ok=n>1", "ok=True"), pt("i*i<=n", "i*i<n"), pt("i*i<=n", "i<n//2"), pt("i*i<=n", "i<=int(n**0.5)-1")],
  slow=[code("import sys\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l)\n        ok=n>1\n        for i in range(2,n):\n            if n%i==0: ok=False;break\n        print('YES' if ok else 'NO')\n", "試除到 n-1")],
  big=[lambda r: "".join(f"{p}\n" for p in [999999937, 999999929, 1000000000, 999999000 + 1, 982451653, 999999893] * 10)])

# d022
def g(r):
    return "".join(f"{mix(r, [1, 10**9, 999999937], 1, 40)} {mix(r, [1, 10**9, 999999937], 1, 40)}\n" for _ in range(r.randint(1, 5)))
Q("d022", lambda t: "".join("{} {}\n".format(math.gcd(*nums(l)), math.lcm(*nums(l)) if hasattr(math, "lcm") else nums(l)[0] * nums(l)[1] // math.gcd(*nums(l))) for l in body(t)), g,
  lambda t: all(len(l.split()) == 2 and inrange(nums(l), 1, 10**9) for l in body(t)) and body(t) != [],
  wrong=[pt("a//g*b", "a*b"), pt("print(g,a//g*b)", "print(g,a*b//g+1)"), pt("print(g,a//g*b)", "print(g,max(a,b))")])

# d023
def fibn(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
def g(r):
    return "".join(f"{mix(r, [0, 1, 2, 90, 89], 0, 30)}\n" for _ in range(r.randint(1, 6)))
Q("d023", lambda t: "".join(f"{fibn(int(x))}\n" for x in body(t)), g,
  lambda t: all(len(l.split()) == 1 and 0 <= int(l) <= 90 for l in body(t)) and body(t) != [],
  slow=[code("import sys\ndef f(n): return n if n<2 else f(n-1)+f(n-2)\nfor l in sys.stdin:\n    if l.strip(): print(f(int(l)))\n", "遞迴費氏")],
  wrong=[pt("for _ in range(n)", "for _ in range(n-1)"), pt("a,b=0,1", "a,b=1,1"), pt("for _ in range(n)", "for _ in range(n+1)")],
  big=[lambda r: "90\n89\n88\n87\n86\n85\n"])

# d024
def g(r):
    return f"{mix(r, [1, 50, 2], 1, 12)}\n"
Q("d024", lambda t: "".join(" " * (int(t) - i) + "*" * (2 * i - 1) + "\n" for i in range(1, int(t) + 1)), g,
  lambda t: len(body(t)) == 1 and 1 <= int(t) <= 50,
  wrong=[pt("' '*(n-i)", "' '*(n-i+1)"), pt("'*'*(2*i-1)", "'*'*(2*i)"), pt("' '*(n-i)+'*'*(2*i-1)", "'*'*(2*i-1)")])

# d025
def g(r):
    return "".join(f"{mix(r, [1, 2, 36, 10**6, 999983, 720720, 997 * 997, 9, 16], 1, 100)}\n" for _ in range(r.randint(1, 6)))
Q("d025", lambda t: "".join(f"{sum(1 for d in range(1, int(x) + 1) if int(x) % d == 0)}\n" for x in body(t)), g,
  lambda t: all(len(l.split()) == 1 and 1 <= int(l) <= 10**6 for l in body(t)) and 1 <= len(body(t)) <= 1000,
  wrong=[pt("c+=1 if i*i==n else 2", "c+=2"), pt("i*i<=n", "i*i<n"), pt("i*i<=n", "i<n")],
  slow=[code("import sys\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l)\n        print(sum(1 for d in range(1,n+1) if n%d==0))\n", "逐一試除到 n")],
  big=[lambda r: "".join(f"{x}\n" for x in [10**6, 999983, 720720, 997 * 997, 983 * 1000, 524288, 999999, 999998] * 125)])

# d026
def g(r):
    a, b = r.randint(1, 5), r.randint(1, 5)
    return f"{a} {b}\n" + "".join(sp(ints(r, b, -9, 99)) + "\n" for _ in range(a))
def b026(t):
    ls = body(t)
    r, c = nums(ls[0])
    m = [ls[1 + i].split() for i in range(r)]
    return "".join(" ".join(m[i][j] for i in range(r)) + "\n" for j in range(c))
def v026(t):
    ls = body(t)
    r, c = nums(ls[0])
    return 1 <= r <= 100 and 1 <= c <= 100 and len(ls) == r + 1 and all(len(l.split()) == c for l in ls[1:])
Q("d026", b026, g, v026,
  wrong=[pt("for j in range(c)", "for j in range(r)"), pt("print(*[a[i][j] for i in range(r)])", "print(*[a[i][j] for i in range(r)][::-1])"), pt("print(*[a[i][j] for i in range(r)])", "print(*a[j])")],
  big=[lambda r: "100 100\n" + "".join(sp(ints(r, 100, -10**9, 10**9)) + "\n" for _ in range(100))])

# d027
def g(r):
    return "".join(f"{mix(r, [0, 1, 2, 10**18, 2**59, 2**59 - 1], 0, 300)}\n" for _ in range(r.randint(1, 5)))
Q("d027", lambda t: "".join(format(int(x), "b") + "\n" for x in body(t)), g,
  lambda t: all(len(l.split()) == 1 and 0 <= int(l) <= 10**18 for l in body(t)) and body(t) != [],
  wrong=[pt("bin(int(l))[2:]", "bin(int(l))"), pt("bin(int(l))[2:]", "bin(int(l))[2:] if int(l) else ''"), pt("bin(int(l))[2:]", "bin(int(l))[2:][::-1]")])

# d028
def b028(t):
    ls = body(t)
    n, T = nums(ls[0])
    a = nums(ls[1])
    return ("YES" if any(a[i] + a[j] == T for i in range(n) for j in range(i + 1, n)) else "NO") + "\n"
def g(r):
    n = r.randint(1, 7)
    a = ints(r, n, -5, 9)
    return f"{n} {r.randint(-8, 15)}\n{sp(a)}\n"
Q("d028", b028, g,
  lambda t: len(body(t)) == 2 and nums(body(t)[0])[0] == len(nums(body(t)[1])) and 1 <= nums(body(t)[0])[0] <= 50000,
  wrong=[pt("if t-x in seen: ok=True;break\n    seen.add(x)", "seen.add(x)\n    if t-x in seen: ok=True;break"),
         code("n,t=map(int,input().split())\na=list(map(int,input().split()))\ns=set(a)\nprint('YES' if any(t-x in s for x in a) else 'NO')\n")],
  slow=[code("n,t=map(int,input().split())\na=list(map(int,input().split()))\nok=False\nfor i in range(n):\n    for j in range(i+1,n):\n        if a[i]+a[j]==t: ok=True;break\n    if ok: break\nprint('YES' if ok else 'NO')\n", "雙迴圈 O(n²)")],
  big=[lambda r: "30000 1999999999\n" + sp(ints(r, 30000, -10**9, 10**9)) + "\n", lambda r: "30000 -7\n" + sp([i * 2 for i in range(30000)]) + "\n"])

# d029
def g(r):
    s = word(r, 1, 6, "aAb ")
    t = list(s)
    if r.random() < 0.5:
        r.shuffle(t)
    else:
        t = list(word(r, len(s), len(s), "aAb "))
    return s + "\n" + "".join(t) + "\n"
Q("d029", lambda t: ("YES" if sorted(rows(t)[0]) == sorted(rows(t)[1]) else "NO") + "\n", g,
  lambda t: len(body(t)) == 2 and 1 <= len(rows(t)[0]) <= 1000 and 1 <= len(rows(t)[1]) <= 1000,
  wrong=[pt("sorted(a)==sorted(b)", "set(a)==set(b)"), pt("a=input();b=input()", "a=input().strip();b=input().strip()"), pt("sorted(a)==sorted(b)", "sorted(a.lower())==sorted(b.lower())"), pt("sorted(a)==sorted(b)", "len(a)==len(b)")])

# d030
def b030(t):
    bal = 0
    out = []
    for l in body(t):
        p = l.split()
        if p[0] == "DEPOSIT":
            bal += int(p[1])
        elif p[0] == "WITHDRAW":
            if bal >= int(p[1]):
                bal -= int(p[1])
            else:
                out.append("INSUFFICIENT")
        else:
            out.append(str(bal))
    return "".join(x + "\n" for x in out)
def g(r):
    out = []
    for _ in range(r.randint(1, 10)):
        k = r.choice(["DEPOSIT", "WITHDRAW", "BALANCE"])
        out.append(k if k == "BALANCE" else f"{k} {r.choice([1, 5, 10, 10**9, 7, 3])}")
    return "\n".join(out) + "\n"
def v030(t):
    ls = body(t)
    if not 1 <= len(ls) <= 1000:
        return False
    for l in ls:
        p = l.split()
        if p[0] == "BALANCE" and len(p) == 1:
            continue
        if p[0] in ("DEPOSIT", "WITHDRAW") and len(p) == 2 and 1 <= int(p[1]) <= 10**9:
            continue
        return False
    return True
Q("d030", b030, g, v030,
  wrong=[pt("int(p[1])>b", "int(p[1])>=b"), pt("int(p[1])>b", "int(p[1])<b"), pt("print('INSUFFICIENT')", "print('INSUFFICIENT');b=0"), pt("else: b-=int(p[1])", "else: pass")])
