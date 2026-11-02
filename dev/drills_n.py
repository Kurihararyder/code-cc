"""課程重審（2.8.0）新增的練習題：補齊每個單元的難度階梯。每題同時登記中文與英文敘述（EN）。
參考解只用來產生期望輸出；每一題都要通過 dev/qa.py 的檢查（獨立解對拍、輸入限制、錯誤解、效能）才算數。"""
from common import D, lines, rng

EN = {}


def N(id, stage, diff, topic, topic_en, zh, en, cat, insight, ref, cases, timeout=10, reserve=False):
    """zh／en：(標題, 敘述, 輸入, 輸出, 說明)。"""
    D(id, zh[0], stage, topic, zh[1], zh[2], zh[3], cat, insight, ref, cases, note=zh[4], diff=diff, timeout=timeout, reserve=reserve)
    EN[id] = (en[0], en[1], en[2], en[3], en[4], topic_en)


def R(seed):
    return rng(seed)


def _lt(i):
    """把整數 i 換成只含小寫字母的字串（科目名稱不能有數字）。"""
    return "".join(chr(97 + (i // 26 ** k) % 26) for k in range(3))


# ======================= 階段 0 =======================
N("d096", 0, 1, "運算／整除與餘數", "Arithmetic, // and %",
  ("秒數換算", "每行一個秒數 s，輸出它等於幾小時幾分幾秒，格式 `h m s`（以一個空格隔開；m、s 都在 0–59，h 沒有上限）。",
   "每行一個整數 s（0 ≤ s ≤ 10^9），讀到 EOF。", "每行一個結果。", "`//` 取商、`%` 取餘數；先算小時，再處理剩下的秒數。"),
  ("Seconds to H M S", "For each number of seconds s, print it as hours, minutes and seconds in the form `h m s` separated by single spaces (m and s are in 0–59; h has no upper limit).",
   "One integer s per line (0 ≤ s ≤ 10^9), until EOF.", "One result per line.", "`//` gives the quotient and `%` the remainder; handle hours first, then the remaining seconds."),
  "整除與餘數", "h = s // 3600；剩下 r = s % 3600；m = r // 60；s = r % 60。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        s=int(l);print(s//3600,s%3600//60,s%60)",
  ["3661\n", "0\n59\n60\n3599\n3600\n86399\n86400\n", "1000000000\n359999\n360000\n"])

N("d097", 0, 1, "運算／貪心找零", "Arithmetic, greedy change",
  ("找零", "有 50、10、5、1 元的硬幣，每種都有無限多個。對每個金額 n，用『最少的硬幣數』湊出 n，輸出四種硬幣各用幾枚，格式 `a b c d`（依序是 50、10、5、1 元）。",
   "每行一個整數 n（1 ≤ n ≤ 10^6），讀到 EOF。", "每行 4 個整數。", "每次先拿能拿的最大面額。這組面額剛好讓貪心是對的（之後的零錢 DP 會遇到貪心失敗的面額）。"),
  ("Making Change", "You have unlimited coins of 50, 10, 5 and 1. For each amount n, pay it with the fewest coins and print how many coins of each kind you use as `a b c d` (in the order 50, 10, 5, 1).",
   "One integer n per line (1 ≤ n ≤ 10^6), until EOF.", "Four integers per line.", "Always take the largest coin you can. For this coin system greedy is correct (later, in coin-change DP, you will meet systems where greedy fails)."),
  "整除與餘數", "n // 50 是 50 元的枚數，餘數再除 10，依此類推。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l);o=[]\n        for c in (50,10,5,1): o.append(n//c);n%=c\n        print(*o)",
  ["68\n", "1\n4\n5\n9\n10\n49\n50\n99\n", "1000000\n999999\n"])

N("d098", 0, 1, "條件判斷", "Conditions",
  ("三角形種類", "每行三個正整數 a b c 代表三條邊長。若這三條邊不能圍成三角形（兩短邊之和 ≤ 最長邊，退化成線段也算不能），輸出 `NOT`；否則依序判斷：三邊都相等輸出 `EQUILATERAL`，恰有兩邊相等輸出 `ISOSCELES`，否則輸出 `SCALENE`。",
   "每行三個整數（1–10^9），讀到 EOF。", "每行一個單字。", "先判斷能不能成立，再判斷種類；『兩短邊之和等於長邊』是最常漏掉的邊界。"),
  ("Triangle Types", "Each line has three positive integers a b c, the lengths of three sides. If they cannot form a triangle (the sum of the two shorter sides ≤ the longest side; a degenerate segment does not count), print `NOT`. Otherwise print `EQUILATERAL` if all three are equal, `ISOSCELES` if exactly two are equal, and `SCALENE` otherwise.",
   "Three integers (1–10^9) per line, until EOF.", "One word per line.", "Decide whether a triangle exists first, then its type. 'Two short sides sum to exactly the long side' is the boundary people forget."),
  "條件判斷／邊界", "排序後 s[0]+s[1] > s[2] 才是三角形；再數相等的邊數。",
  "import sys\nfor l in sys.stdin:\n    p=l.split()\n    if len(p)<3: continue\n    s=sorted(map(int,p))\n    if s[0]+s[1]<=s[2]: print('NOT')\n    elif s[0]==s[2]: print('EQUILATERAL')\n    elif s[0]==s[1] or s[1]==s[2]: print('ISOSCELES')\n    else: print('SCALENE')",
  ["3 4 5\n", "1 1 2\n2 2 3\n5 5 5\n3 3 6\n1 2 3\n7 10 5\n1000000000 1000000000 1000000000\n", "1 1 1\n2 3 4\n10 5 5\n1 1000000000 1000000000\n"])

N("d099", 0, 1, "條件判斷／分段計費", "Conditions, tiered pricing",
  ("快遞運費", "包裹重量 w 公克。重量在 1000 公克以內（含）一律收 60 元；超過 1000 公克的部分，每 500 公克收 25 元，不足 500 公克也以 500 公克計。輸出運費。",
   "每行一個整數 w（1 ≤ w ≤ 10^6），讀到 EOF。", "每行一個整數。", "『不足也算一整份』就是無條件進位：`(x + 499) // 500`。"),
  ("Parcel Shipping Fee", "A parcel weighs w grams. Up to and including 1000 grams the fee is 60. For the weight above 1000 grams, charge 25 for every 500 grams, and a partial block of less than 500 grams is charged as a full block. Print the fee.",
   "One integer w per line (1 ≤ w ≤ 10^6), until EOF.", "One integer per line.", "'A partial block counts as a whole one' means rounding up: `(x + 499) // 500`."),
  "條件／無條件進位", "w ≤ 1000 → 60；否則 60 + ceil((w-1000)/500)*25，ceil 用 (x+499)//500。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        w=int(l);print(60 if w<=1000 else 60+((w-1000+499)//500)*25)",
  ["1500\n", "1\n1000\n1001\n1500\n1501\n2000\n2001\n", "1000000\n999999\n"])

N("d100", 0, 1, "迴圈／while", "Loops, while",
  ("3n+1 的步數", "從正整數 n 開始重複：n 是偶數就變成 n/2，是奇數就變成 3n+1，直到 n 變成 1。對每個 n 輸出需要幾步（n = 1 時是 0 步）。過程中的數字可能超過 32 位元整數。",
   "每行一個整數 n（1 ≤ n ≤ 10^6），讀到 EOF，最多 1000 行。", "每行一個整數。", "while 迴圈的標準練習：條件、更新、計數。"),
  ("Steps of 3n+1", "Start from a positive integer n and repeat: if n is even replace it by n/2, if n is odd replace it by 3n+1, until n becomes 1. For every n print the number of steps needed (0 steps when n = 1). The numbers on the way may exceed 32-bit integers.",
   "One integer n per line (1 ≤ n ≤ 10^6), until EOF, at most 1000 lines.", "One integer per line.", "The standard while-loop exercise: condition, update, counter."),
  "while 迴圈", "用 while n != 1 迴圈，每次依奇偶更新並讓計數 +1。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l);c=0\n        while n!=1:\n            n=n//2 if n%2==0 else 3*n+1;c+=1\n        print(c)",
  ["6\n", "1\n2\n3\n7\n27\n97\n", "837799\n999999\n1000000\n"])

N("d101", 0, 1, "迴圈／條件", "Loops, conditions",
  ("Fizz Buzz", "輸入 n，輸出 n 行：第 i 行（i 從 1 開始）若 i 同時是 3 和 5 的倍數輸出 `FizzBuzz`，只是 3 的倍數輸出 `Fizz`，只是 5 的倍數輸出 `Buzz`，否則輸出 i 本身。",
   "一個整數 n（1 ≤ n ≤ 100）。", "n 行。", "先判斷『同時』的情況（15 的倍數），否則會被前面的條件吃掉。"),
  ("Fizz Buzz", "Read n and print n lines: on line i (starting from 1) print `FizzBuzz` if i is a multiple of both 3 and 5, `Fizz` if it is only a multiple of 3, `Buzz` if it is only a multiple of 5, and i itself otherwise.",
   "One integer n (1 ≤ n ≤ 100).", "n lines.", "Test the 'both' case (multiples of 15) first, otherwise an earlier condition swallows it."),
  "條件順序", "先判斷 i % 15 == 0，再 3，再 5。",
  "n=int(input())\nfor i in range(1,n+1):\n    print('FizzBuzz' if i%15==0 else 'Fizz' if i%3==0 else 'Buzz' if i%5==0 else i)",
  ["15\n", "1\n", "3\n", "5\n", "100\n"])

N("d102", 0, 1, "字串／split 與 join", "Strings, split and join",
  ("單字反轉", "每行是由若干單字組成的文字，單字之間恰好一個空格，行首行尾沒有空格。把每個單字各自前後反轉，單字的順序和空格不變。",
   "每行長度 ≤ 1000，只含英文字母、數字與單一空格，讀到 EOF。", "每行一個結果。", "`line.split()` 切成單字、`' '.join(...)` 接回去。"),
  ("Reverse Each Word", "Each line is a text made of words separated by exactly one space (no leading or trailing spaces). Reverse every word individually; the order of the words and the spaces stay the same.",
   "Each line has length ≤ 1000 and contains only letters, digits and single spaces, until EOF.", "One result per line.", "Split the line with `line.split()` and join the words back with `' '.join(...)`."),
  "字串切割", "split() → 每個單字 [::-1] → ' '.join。",
  "import sys\nfor l in sys.stdin:\n    l=l.rstrip('\\n')\n    if l: print(' '.join(w[::-1] for w in l.split()))",
  ["hello world\n", "a\nab cd\nabc def ghi\nx y z\n", "Python3 is fun\n12345 6789\npalindrome level\n"])

N("d103", 0, 2, "list／集合", "Lists and sets",
  ("第二大的數", "給 n 個整數，輸出第二大的『相異數值』（例如 5 5 3 的答案是 3）。如果不同的數值不到兩種，輸出 `NONE`。",
   "第一行 n（1 ≤ n ≤ 10^5），第二行 n 個整數（絕對值 ≤ 10^9）。", "一個整數或 `NONE`。", "set 去重再排序；別忘了全部相同或只有一個數的情況。"),
  ("Second Largest", "Given n integers, print the second largest distinct value (for 5 5 3 the answer is 3). If there are fewer than two distinct values, print `NONE`.",
   "The first line has n (1 ≤ n ≤ 10^5); the second line has n integers (absolute value ≤ 10^9).", "One integer, or `NONE`.", "Remove duplicates with a set, then sort; do not forget the case where all numbers are equal or there is only one number."),
  "去重與排序", "s = sorted(set(a))；len(s) < 2 輸出 NONE，否則 s[-2]。",
  "n=int(input())\ns=sorted(set(map(int,input().split())))\nprint(s[-2] if len(s)>=2 else 'NONE')",
  ["5\n3 1 4 1 5\n", "1\n7\n", "3\n5 5 5\n", "4\n-3 -3 -5 -5\n", "2\n1 2\n"])

N("d104", 0, 1, "set 集合運算", "Set operations",
  ("交集與聯集", "輸入兩行，每行是一個整數集合（可能有重複的數字，以空格分隔，每行 1–100 個整數，絕對值 ≤ 1000）。第一行輸出兩個集合的交集（由小到大，空格分隔；沒有共同元素就輸出 `EMPTY`），第二行輸出聯集（由小到大）。",
   "兩行，各是一個整數集合。", "兩行。", "set 的 `&`、`|` 運算與 sorted。"),
  ("Intersection and Union", "The input has two lines, each an integer set (digits may repeat; separated by spaces; 1–100 integers per line with absolute value ≤ 1000). On the first output line print the intersection (ascending, space-separated; print `EMPTY` if there is no common element); on the second print the union (ascending).",
   "Two lines, each an integer set.", "Two lines.", "The set operators `&` and `|`, then sorted."),
  "集合運算", "a = set(...)；b = set(...)；sorted(a & b)、sorted(a | b)。",
  "a=set(map(int,input().split()));b=set(map(int,input().split()))\nx=sorted(a&b)\nprint(*x if x else ['EMPTY'])\nprint(*sorted(a|b))",
  ["1 2 3 4\n3 4 5 6\n", "1 2\n3 4\n", "5 5 5\n5\n", "-1 0 1\n1 0 -1 -1\n", "1000\n-1000\n"])

N("d105", 0, 2, "dict／彙總", "Dictionaries, aggregation",
  ("成績總表", "第一行 n，接著 n 行 `姓名 科目 分數`（姓名、科目是不含空白的英文字母，分數是 0–100 的整數）。同一位學生可能出現很多次（不同科目）。依姓名的字典序（ASCII 順序，大寫在小寫之前）輸出每位學生的 `姓名 總分 科目數`。",
   "第一行 n（1 ≤ n ≤ 10^5），之後 n 行。同一位學生的同一科目不會重複出現。", "每位學生一行。", "dict 以姓名為 key 累加；輸出前 sorted(d)。"),
  ("Grade Summary", "The first line has n; then n lines `name subject score` (name and subject are letters without spaces, score is an integer in 0–100). A student can appear many times (different subjects). Print `name total number_of_subjects` for each student, ordered by name in dictionary (ASCII) order, uppercase before lowercase.",
   "The first line has n (1 ≤ n ≤ 10^5), then n lines. A student never has the same subject twice.", "One line per student.", "Accumulate in a dict keyed by name; use sorted(d) when printing."),
  "dict 累加", "用 d[name] = [總分, 次數]。",
  "import sys\nd=sys.stdin.read().split()\nn=int(d[0]);m={}\nfor i in range(n):\n    a=d[1+3*i];s=int(d[3+3*i]);t=m.setdefault(a,[0,0]);t[0]+=s;t[1]+=1\nfor a in sorted(m): print(a,m[a][0],m[a][1])",
  ["5\namy math 90\nbob math 80\namy art 70\ncat math 100\nbob art 60\n", "1\nzed math 0\n", "4\nBob a 1\nbob b 2\nAlice c 3\nbob c 4\n",
   (lambda r: lines(2000, *[f"{r.choice(['a', 'b', 'C', 'dd', 'Ee'])} {_lt(i)} {r.randint(0, 100)}" for i in range(2000)]))(R(105))])

N("d106", 0, 2, "數學／質因數分解", "Prime factorization",
  ("質因數分解", "對每個整數 n，輸出它的質因數分解：質因數由小到大，每個寫成 `p^e`，之間用一個空格隔開（指數是 1 也要寫，例如 12 輸出 `2^2 3^1`）。",
   "每行一個整數 n（2 ≤ n ≤ 10^12），最多 10 行，讀到 EOF。", "每行一個結果。", "試除到 √n：一邊除一邊記錄次數；最後剩下的大於 1 的數本身就是質數。"),
  ("Prime Factorization", "For each integer n print its prime factorization: prime factors in ascending order, each written as `p^e` and separated by single spaces (write the exponent even when it is 1, e.g. 12 → `2^2 3^1`).",
   "One integer n per line (2 ≤ n ≤ 10^12), at most 10 lines, until EOF.", "One result per line.", "Trial division up to √n: divide out each factor while counting; whatever remains above 1 at the end is itself prime."),
  "試除法", "i 從 2 開始，能整除就一直除並計次；結束後 n > 1 表示還剩一個大質因數。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l);o=[];i=2\n        while i*i<=n:\n            if n%i==0:\n                e=0\n                while n%i==0: n//=i;e+=1\n                o.append(f'{i}^{e}')\n            i+=1\n        if n>1: o.append(f'{n}^1')\n        print(' '.join(o))",
  ["12\n", "2\n3\n4\n6\n49\n97\n100\n1024\n", "999999999989\n1000000000000\n999999000001\n600851475143\n"], timeout=30)

N("d107", 0, 1, "迴圈／數字", "Loops, digits",
  ("數根", "對每個非負整數 n（十進位，沒有前導 0），重複『把各位數字加起來』直到只剩一位數，輸出最後的個位數，以及總共加了幾次（n 本來就是一位數時是 0 次）。輸出格式 `根 次數`。",
   "每行一個整數 n，最多 1000 位數，讀到 EOF。", "每行 `根 次數`。", "n 可能很長，用字串處理最方便。"),
  ("Digital Root", "For each non-negative integer n (decimal, no leading zeros), repeatedly replace it by the sum of its digits until a single digit remains. Print that digit and how many replacements were made (0 if n already has one digit), as `root count`.",
   "One integer n per line with at most 1000 digits, until EOF.", "`root count` per line.", "n can be very long, so treat it as a string."),
  "迴圈／數字拆解", "s = 字串；while len(s) > 1: s = str(各位和)；次數 +1。",
  "import sys\nfor l in sys.stdin:\n    s=l.strip()\n    if not s: continue\n    c=0\n    while len(s)>1: s=str(sum(map(int,s)));c+=1\n    print(s,c)",
  ["38\n", "0\n9\n10\n99\n199\n", "9"*1000+"\n"+"1"+"0"*999+"\n"+"123456789"*100+"\n"])

N("d108", 0, 1, "二維 list", "2D lists",
  ("對角線和", "給 n×n 的整數方陣。輸出主對角線（左上到右下）的總和與副對角線（右上到左下）的總和。n 是奇數時中心格兩條對角線都算。",
   "第一行 n（1 ≤ n ≤ 100），接著 n 行各 n 個整數（絕對值 ≤ 10^4）。", "一行：主對角線和 副對角線和。", "主對角線是 a[i][i]，副對角線是 a[i][n-1-i]。"),
  ("Diagonal Sums", "Given an n×n integer matrix, print the sum of the main diagonal (top-left to bottom-right) and the sum of the anti-diagonal (top-right to bottom-left). For odd n the centre cell belongs to both diagonals.",
   "The first line has n (1 ≤ n ≤ 100), then n lines of n integers (absolute value ≤ 10^4).", "One line: main_sum anti_sum.", "The main diagonal is a[i][i]; the anti-diagonal is a[i][n-1-i]."),
  "二維索引", "同一個 i 迴圈同時加兩個位置。",
  "n=int(input())\na=[list(map(int,input().split())) for _ in range(n)]\nprint(sum(a[i][i] for i in range(n)),sum(a[i][n-1-i] for i in range(n)))",
  ["3\n1 2 3\n4 5 6\n7 8 9\n", "1\n5\n", "2\n1 2\n3 4\n", "4\n-1 0 0 2\n0 -3 4 0\n0 5 -6 0\n7 0 0 -8\n",
   (lambda r: lines(100, *[" ".join(str(r.randint(-10000, 10000)) for _ in range(100)) for _ in range(100)]))(R(108))])

N("d109", 0, 2, "二維 list／模擬", "2D lists, simulation",
  ("掃雷", "第一行 r c，接著 r 行各 c 個字元：`*` 是地雷，`.` 是空地。輸出同樣大小的盤面：地雷仍然是 `*`，每個空地換成它周圍八格（上下左右與四個斜角）裡的地雷數（0–8 的數字）。",
   "1 ≤ r, c ≤ 100。", "r 行，每行 c 個字元。", "走訪八個方向時要檢查邊界；用方向表 `[(-1,-1),(-1,0),...]` 最不容易寫錯。"),
  ("Minesweeper", "The first line has r c, followed by r lines of c characters: `*` is a mine and `.` is an empty cell. Print a board of the same size in which mines stay `*` and every empty cell becomes the number (0–8) of mines among its eight neighbours (including diagonals).",
   "1 ≤ r, c ≤ 100.", "r lines of c characters.", "Check the bounds for all eight directions; a direction table such as `[(-1,-1),(-1,0),...]` is the least error-prone."),
  "八方向掃描", "對每個空地，用 8 個方向偏移量數 `*`，注意邊界。",
  "r,c=map(int,input().split())\ng=[input() for _ in range(r)]\nfor i in range(r):\n    o=[]\n    for j in range(c):\n        if g[i][j]=='*': o.append('*');continue\n        k=0\n        for di in (-1,0,1):\n            for dj in (-1,0,1):\n                if (di or dj) and 0<=i+di<r and 0<=j+dj<c and g[i+di][j+dj]=='*': k+=1\n        o.append(str(k))\n    print(''.join(o))",
  ["3 4\n*...\n....\n.*..\n", "1 1\n.\n", "1 1\n*\n", "2 3\n***\n***\n", "1 5\n.*.*.\n", "4 1\n.\n*\n.\n*\n",
   (lambda r: "100 100\n" + "\n".join("".join("*" if r.random() < 0.3 else "." for _ in range(100)) for _ in range(100)) + "\n")(R(109))])

N("d110", 0, 2, "二維 list／旋轉", "2D lists, rotation",
  ("旋轉矩陣", "第一行 r c，接著 r 行各 c 個整數。把矩陣順時針旋轉 90 度後輸出（旋轉後是 c 行、每行 r 個數，以空格隔開）。",
   "1 ≤ r, c ≤ 100，數字絕對值 ≤ 10^9。", "c 行。", "旋轉後的第 j 行，是原來第 j 欄『由下往上』讀。"),
  ("Rotate a Matrix", "The first line has r c, followed by r lines of c integers. Print the matrix rotated 90 degrees clockwise (c lines of r numbers separated by spaces).",
   "1 ≤ r, c ≤ 100, absolute values ≤ 10^9.", "c lines.", "Line j of the result is column j of the original, read from bottom to top."),
  "二維索引轉換", "新矩陣第 j 行第 i 個 = 原矩陣 a[r-1-i][j]。",
  "r,c=map(int,input().split())\na=[input().split() for _ in range(r)]\nfor j in range(c): print(*[a[r-1-i][j] for i in range(r)])",
  ["2 3\n1 2 3\n4 5 6\n", "1 1\n7\n", "1 4\n1 2 3 4\n", "4 1\n1\n2\n3\n4\n", "3 3\n1 2 3\n4 5 6\n7 8 9\n"])


# ======================= 階段 1 =======================
MORSE = {"A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-",
         "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-", "U": "..-", "V": "...-",
         "W": ".--", "X": "-..-", "Y": "-.--", "Z": "--..", "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
         "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----."}
MORSE_TABLE = "　".join(f"{k} {v}" for k, v in MORSE.items()).replace("　", "，")
MORSE_REF = "M=" + repr({v: k for k, v in MORSE.items()}) + "\n"

N("d111", 1, 2, "浮點數輸出／分級", "Float formatting, classification",
  ("BMI", "每行兩個整數 w h（體重 w 公斤、身高 h 公分），BMI = w ÷ (h/100)²。輸出 `BMI 類別`：BMI 四捨五入到小數點後 1 位；類別看『四捨五入前』的 BMI：小於 18.5 是 `UNDER`，18.5 以上小於 24 是 `NORMAL`，24 以上小於 27 是 `OVER`，27 以上是 `OBESE`。測資保證 BMI 不會剛好落在『第二位小數是 5 的進位邊界』。",
   "每行 `w h`（30 ≤ w ≤ 200，100 ≤ h ≤ 220），讀到 EOF。", "每行 `BMI 類別`，例如 `22.9 NORMAL`。", "類別的邊界看原始值、顯示看四捨五入後的值——兩者不一定一致（例如 BMI 23.96 顯示成 24.0，類別卻是 NORMAL）。"),
  ("BMI", "Each line has two integers w h (weight w kg, height h cm); BMI = w ÷ (h/100)². Print `BMI category`: the BMI rounded to one decimal place, and a category based on the BMI *before* rounding: below 18.5 is `UNDER`, from 18.5 up to below 24 is `NORMAL`, from 24 up to below 27 is `OVER`, 27 or more is `OBESE`. The data guarantees no BMI falls exactly on a rounding boundary of the second decimal digit.",
   "Each line `w h` (30 ≤ w ≤ 200, 100 ≤ h ≤ 220), until EOF.", "One `BMI category` per line, e.g. `22.9 NORMAL`.", "The category uses the raw value while the display uses the rounded one — they can disagree (a BMI of 23.96 prints as 24.0 but is still NORMAL)."),
  "格式化與邊界", "BMI = w*10000/h²；分類用整數比較（例如 w*10000*2 < 37*h*h 表示小於 18.5）避免浮點誤差。",
  "import sys\nfor l in sys.stdin:\n    p=l.split()\n    if len(p)<2: continue\n    w,h=int(p[0]),int(p[1]);h2=h*h\n    c='UNDER' if w*20000<37*h2 else 'NORMAL' if w*10000<24*h2 else 'OVER' if w*10000<27*h2 else 'OBESE'\n    print(f'{w*10000/h2:.1f}',c)",
  ["70 175\n", "74 200\n96 200\n108 200\n50 160\n60 160\n70 160\n81 160\n45 137\n47 132\n56 174\n", "30 100\n200 100\n200 220\n54 170\n64 163\n", "100 200\n61 160\n"])

N("d112", 1, 2, "字串映射／dict", "String mapping, dict",
  ("摩斯電碼解碼", "把摩斯電碼訊息翻回文字。每行一則訊息：字母與數字的編碼以一個空格隔開，單字與單字之間用 ` / `（空格、斜線、空格）隔開。輸出翻譯後的文字（大寫英文字母與數字），單字之間一個空格。編碼表：" + MORSE_TABLE + "。",
   "每行一則訊息（不會有空行；每行最多 1000 個符號），讀到 EOF。", "每行一個結果。", "先把編碼表做成 dict（編碼 → 字元），再切割訊息。"),
  ("Morse Decoder", "Translate Morse messages back into text. Each line is one message: the codes of letters and digits are separated by one space, and words are separated by ` / ` (space, slash, space). Print the decoded text (uppercase letters and digits) with a single space between words. Code table: " + ", ".join(f"{k} {v}" for k, v in MORSE.items()) + ".",
   "One message per line (never empty; at most 1000 symbols per line), until EOF.", "One result per line.", "Build the code table as a dict (code → character) first, then split the message."),
  "dict 查表", "line.split(' / ') 切單字，每個單字再 split() 切字母，查表後 join。",
  "import sys\n" + MORSE_REF + "for l in sys.stdin:\n    l=l.rstrip('\\n')\n    if l: print(' '.join(''.join(M[c] for c in w.split()) for w in l.split(' / ')))",
  [".... . .-.. .-.. --- / .-- --- .-. .-.. -..\n", ".-\n... --- ...\n.---- ..--- ...-- / ....- ..... -....\n----- / ----.\n", "-- --- .-. ... . / -.-. --- -.. .\n.- -... -.-. -.. . ..-. --. .... .. .--- -.- .-.. -- -. --- .--. --.- .-. ... - ..- ...- .-- -..- -.-- --..\n----- .---- ..--- ...-- ....- ..... -.... --... ---.. ----.\n"])

N("d113", 1, 2, "大整數", "Big integers",
  ("階乘的位數和", "對每個 n，計算 n! 的十進位各位數字總和。",
   "每行一個整數 n（0 ≤ n ≤ 1000），最多 100 行，讀到 EOF。", "每行一個整數。", "1000! 有 2568 位數，C++ 的 long long 完全放不下，Python 的 int 直接就能算。"),
  ("Digit Sum of a Factorial", "For each n, compute the sum of the decimal digits of n!.",
   "One integer n per line (0 ≤ n ≤ 1000), at most 100 lines, until EOF.", "One integer per line.", "1000! has 2568 digits and cannot fit in a C++ long long, but a Python int handles it directly."),
  "大整數運算", "f = 1；for i in range(2, n+1): f *= i；再 sum(map(int, str(f)))。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        f=1\n        for i in range(2,int(l)+1): f*=i\n        print(sum(map(int,str(f))))",
  ["5\n", "0\n1\n2\n10\n20\n", "100\n1000\n999\n500\n", "0\n"])

N("d114", 1, 2, "大數／逐位模擬", "Digit-by-digit simulation",
  ("加法的進位次數", "每行兩個非負整數 a b（沒有前導 0，最多 30 位數）。像直式加法一樣由個位數往左逐位相加，輸出『有幾個位數產生了進位』（進位會一路傳下去，例如 999 + 1 有 3 次進位）。",
   "每行 `a b`，讀到 EOF。", "每行一個整數。", "直式加法：每位的和 = 兩個數字 + 前一位的進位，≥ 10 就進位。不要用 Python 大數直接加，要逐位模擬。"),
  ("Carries in an Addition", "Each line has two non-negative integers a b (no leading zeros, at most 30 digits). Add them like long addition, from the units digit leftwards, and print how many digit positions produce a carry (carries propagate, so 999 + 1 has 3 carries).",
   "Each line `a b`, until EOF.", "One integer per line.", "In column addition each column sums the two digits plus the carry from the previous column; ≥ 10 produces a carry. Simulate digit by digit instead of adding the big integers directly."),
  "逐位模擬", "把兩個字串補齊長度，從右往左：s = x + y + carry；carry = s >= 10；累計次數。",
  "import sys\nfor l in sys.stdin:\n    p=l.split()\n    if len(p)<2: continue\n    a,b=p[0][::-1],p[1][::-1];n=max(len(a),len(b));c=k=0\n    for i in range(n):\n        s=(int(a[i]) if i<len(a) else 0)+(int(b[i]) if i<len(b) else 0)+c\n        c=1 if s>=10 else 0;k+=c\n    print(k)",
  ["123 456\n", "999 1\n1 999\n0 0\n5 5\n55 55\n99999999999999999999999999999 1\n", "123456789 987654321\n19 91\n1000 9\n"])

N("d115", 1, 2, "字串／回文", "Strings, palindromes",
  ("下一個回文數", "對每個正整數 n，輸出『嚴格大於 n 的最小回文數』（回文：由左往右和由右往左讀都一樣，如 121、7、1331）。",
   "每行一個整數 n（1 ≤ n ≤ 10^18），讀到 EOF，最多 1000 行。", "每行一個整數。", "不要一個一個加 1 去試（n 到 10^18 會跑不完）：只需要用 n 的『左半邊』去鏡射。"),
  ("Next Palindrome", "For each positive integer n print the smallest palindrome that is strictly greater than n (a palindrome reads the same forwards and backwards, e.g. 121, 7, 1331).",
   "One integer n per line (1 ≤ n ≤ 10^18), until EOF, at most 1000 lines.", "One integer per line.", "Do not try n+1, n+2, … one by one (it would never finish for n up to 10^18): mirror the *left half* of the number instead."),
  "字串／鏡射", "x = n+1；用 x 的左半邊鏡射成回文 cand；cand ≥ x 就是答案，否則左半邊加 1 後再鏡射。",
  "import sys\nfor l in sys.stdin:\n    if not l.strip(): continue\n    x=int(l)+1;s=str(x);L=len(s);h=s[:(L+1)//2]\n    c=h+h[:L//2][::-1]\n    if int(c)<x:\n        h=str(int(h)+1)\n        if len(h)>(L+1)//2: c='1'+'0'*(L-1)+'1'\n        else: c=h+h[:L//2][::-1]\n    print(c)",
  ["120\n", "1\n8\n9\n10\n11\n98\n99\n100\n101\n999\n1000\n12921\n12931\n", "999999999999999999\n1000000000000000000\n123456789012345678\n99999\n"])

N("d116", 1, 2, "質數／篩法", "Primes, sieve",
  ("哥德巴赫分拆", "對每個偶數 n，找出兩個質數 p ≤ q 使得 p + q = n，若有多組取 p 最小的那組，輸出 `n = p + q`。保證一定有解。",
   "每行一個偶數 n（4 ≤ n ≤ 10^6），最多 10000 行，讀到 EOF。", "每行 `n = p + q`。", "先用篩法標出 10^6 以內的質數，之後每個查詢從小到大試 p，只要檢查 n−p 是不是質數。"),
  ("Goldbach Partition", "For each even number n, find two primes p ≤ q with p + q = n; if there are several, take the one with the smallest p, and print `n = p + q`. A solution is guaranteed to exist.",
   "One even integer n per line (4 ≤ n ≤ 10^6), at most 10000 lines, until EOF.", "`n = p + q` per line.", "Sieve all primes up to 10^6 once; for each query try p from small to large and only check whether n − p is prime."),
  "篩法預處理", "預先篩出 is_prime[]；for p in 2..n/2: 若 p 與 n-p 都是質數就輸出。",
  "import sys\nN=10**6\nsv=bytearray([1])*(N+1);sv[0]=sv[1]=0\nfor i in range(2,int(N**.5)+1):\n    if sv[i]: sv[i*i::i]=bytearray(len(range(i*i,N+1,i)))\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l)\n        for p in range(2,n//2+1):\n            if sv[p] and sv[n-p]: print(f'{n} = {p} + {n-p}');break",
  ["4\n", "4\n6\n8\n10\n12\n100\n1000\n", "1000000\n999998\n999996\n"], timeout=20)

N("d117", 1, 2, "數學／因數", "Math, divisors",
  ("完全數、盈數與虧數", "一個正整數 n 的『真因數』是 n 的所有正因數但不含 n 自己（1 的真因數總和是 0）。設真因數總和為 s：s = n 輸出 `PERFECT`，s > n 輸出 `ABUNDANT`，s < n 輸出 `DEFICIENT`。",
   "每行一個整數 n（1 ≤ n ≤ 10^6），最多 2000 行，讀到 EOF。", "每行一個單字。", "成對找因數：i 整除 n 時，n // i 也是因數；i 到 √n 就夠了；平方數的 i 與 n // i 相同，只能加一次。"),
  ("Perfect, Abundant and Deficient", "The proper divisors of a positive integer n are all its positive divisors except n itself (1 has proper-divisor sum 0). Let s be their sum: print `PERFECT` if s = n, `ABUNDANT` if s > n, and `DEFICIENT` if s < n.",
   "One integer n per line (1 ≤ n ≤ 10^6), at most 2000 lines, until EOF.", "One word per line.", "Find divisors in pairs: if i divides n then n // i does too; go only up to √n; for a perfect square i and n // i coincide and must be added once."),
  "成對找因數", "i 從 1 到 √n：i 整除就加 i 與 n//i（相同只加一次），最後減掉 n 本身。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l);s=0;i=1\n        while i*i<=n:\n            if n%i==0:\n                s+=i\n                if i!=n//i: s+=n//i\n            i+=1\n        s-=n\n        print('PERFECT' if s==n else 'ABUNDANT' if s>n else 'DEFICIENT')",
  ["28\n", "1\n2\n6\n12\n16\n28\n196\n496\n8128\n", "999999\n1000000\n997\n720720\n524288\n"], timeout=20)

N("d118", 1, 2, "質數／預處理", "Primes, precomputation",
  ("孿生質數對", "孿生質數是相差 2 的兩個質數 (p, p+2)。對每個查詢 n，輸出滿足 p + 2 ≤ n 的孿生質數對有幾組（例如 n = 13 時有 (3,5)、(5,7)、(11,13) 共 3 組）。",
   "第一行 q（1 ≤ q ≤ 10^5），接下來 q 行各一個 n（1 ≤ n ≤ 10^6）。", "每個查詢一行。", "和『質數個數查詢』一樣：預處理一次、之後 O(1) 回答。這次要累計的是『孿生對』的個數。"),
  ("Twin Prime Pairs", "Twin primes are two primes that differ by 2, written (p, p+2). For each query n print the number of twin pairs with p + 2 ≤ n (for n = 13 there are (3,5), (5,7), (11,13): 3 pairs).",
   "The first line has q (1 ≤ q ≤ 10^5); then q lines each with one n (1 ≤ n ≤ 10^6).", "One line per query.", "Like 'Prime Counting Queries': precompute once and answer each query in O(1) — this time accumulate twin *pairs*."),
  "篩法＋前綴和", "tw[k] = 到 k 為止的孿生對數；當 k 與 k-2 都是質數時 +1。",
  "import sys\nN=10**6\nsv=bytearray([1])*(N+1);sv[0]=sv[1]=0\nfor i in range(2,int(N**.5)+1):\n    if sv[i]: sv[i*i::i]=bytearray(len(range(i*i,N+1,i)))\ntw=[0]*(N+1)\nfor k in range(1,N+1): tw[k]=tw[k-1]+(1 if k>=2 and sv[k] and sv[k-2] else 0)\nd=sys.stdin.read().split()\nfor x in d[1:1+int(d[0])]: print(tw[int(x)])",
  ["3\n13\n5\n100\n", "6\n1\n2\n3\n4\n5\n7\n", "5\n1000000\n999999\n999000\n10\n11\n"], timeout=20)

N("d119", 1, 2, "網格模擬／狀態", "Simulation, state",
  ("骰子滾動", "一顆骰子（相對的兩面和為 7）的初始狀態：上面 1、北面 2、東面 3、西面 4、南面 5、下面 6。每行一串指令，由 `N` `S` `E` `W` 組成，表示依序把骰子向北、南、東、西『翻滾』一格（向北翻滾時，原本的上面轉到北面，原本的南面轉到上面；其他方向以此類推）。輸出每行指令做完之後的上面點數。空行代表一次也不滾動，答案是 1。",
   "每行一串指令（長度 ≤ 10^5，可能是空行），讀到 EOF。", "每行一個整數。", "只要追蹤『上、北、東』三個面（其餘由 7 減），每次翻滾就是換值。"),
  ("Rolling a Die", "A die (opposite faces sum to 7) starts with top 1, north 2, east 3, west 4, south 5, bottom 6. Each line is a string of commands made of `N`, `S`, `E`, `W`, rolling the die one cell to the north, south, east or west in order (rolling north moves the old top face to the north side and brings the old south face to the top; other directions work the same way). Print the top face after the commands of each line. An empty line means no rolls: the answer is 1.",
   "Each line is a command string (length ≤ 10^5, possibly empty), until EOF.", "One integer per line.", "Track three faces (top, north, east); the other three are 7 minus them. Each roll just reassigns the values."),
  "狀態更新", "向北：新上=舊南(7-北)、新北=舊上；向東：新上=舊西(7-東)、新東=舊上；向南、向西同理。",
  "import sys\nfor l in sys.stdin:\n    t,n,e=1,2,3\n    for c in l.strip():\n        if c=='N': t,n=7-n,t\n        elif c=='S': t,n=n,7-t\n        elif c=='E': t,e=7-e,t\n        elif c=='W': t,e=e,7-t\n    print(t)",
  ["N\n", "NNNN\nEEEE\nSSSS\nWWWW\n\nNE\nEN\nNESW\n", "N"*99999+"E\n"+"NESW"*25000+"\n"+"NNEESSWW"*12500+"\n"])

N("d120", 1, 2, "網格掃描／八方向", "Grid scanning, 8 directions",
  ("字母方陣找單字", "第一行 r c，接著 r 行各 c 個小寫字母，最後一行是單字 w（長度 2 以上）。數有幾組『起點格 + 方向』能依序讀出 w：八個方向（上下左右與四個斜向）都可以，讀的過程不能超出方陣。起點相同但方向不同算不同組；單字是回文時，正反兩個方向各算一組。",
   "1 ≤ r, c ≤ 50，2 ≤ |w| ≤ 50。", "一個整數。", "對每個格子、每個方向各檢查一次；提早在第一個不符或超出邊界時停止。"),
  ("Word Search", "The first line has r c, followed by r lines of c lowercase letters, and finally a word w (length at least 2). Count the (start cell, direction) pairs that spell w when read in a straight line, in any of the eight directions (including diagonals) without leaving the grid. The same start with different directions counts separately; when w is a palindrome both opposite directions count.",
   "1 ≤ r, c ≤ 50, 2 ≤ |w| ≤ 50.", "One integer.", "Try every cell and every direction; stop at the first mismatch or when leaving the grid."),
  "八方向掃描", "8 個方向偏移量；對每個起點、每個方向逐字比對。",
  "r,c=map(int,input().split())\ng=[input() for _ in range(r)]\nw=input().strip();L=len(w);k=0\nfor i in range(r):\n    for j in range(c):\n        for di in (-1,0,1):\n            for dj in (-1,0,1):\n                if not(di or dj): continue\n                ei,ej=i+di*(L-1),j+dj*(L-1)\n                if not(0<=ei<r and 0<=ej<c): continue\n                if all(g[i+di*t][j+dj*t]==w[t] for t in range(L)): k+=1\nprint(k)",
  ["3 4\nabca\nbcab\ncabc\nabc\n", "1 1\na\naa\n", "2 2\naa\naa\naa\n", "3 3\nabc\ndef\nghi\nec\n", "1 5\nabcba\nabcba\n", "4 4\nabab\nbaba\nabab\nbaba\nab\n",
   (lambda r: "50 50\n" + "\n".join("".join(r.choice("ab") for _ in range(50)) for _ in range(50)) + "\nabab\n")(R(120)), "50 50\n" + "\n".join("a" * 50 for _ in range(50)) + "\n" + "a" * 50 + "\n"])

N("d121", 1, 1, "二維陣列／填數", "2D arrays, filling",
  ("斜線填數", "輸入 n，輸出 n×n 的方陣，把 1 到 n² 沿著『斜線』依序填入：先填左上角的 1；接著填第一條斜線（右上到左下方向，也就是由列號小的格子往列號大的格子填）的所有格子，再填下一條，直到右下角。n = 3 的結果為\n`1 2 4`\n`3 5 7`\n`6 8 9`",
   "一個整數 n（1 ≤ n ≤ 50）。", "n 行，每行 n 個數字，以空格隔開。", "同一條斜線上的格子，列號加行號是固定值。"),
  ("Diagonal Fill", "Read n and print an n×n matrix filled with 1 to n² along anti-diagonals: first the top-left cell, then each following anti-diagonal in turn, where the cells of one diagonal are filled from the smaller row number to the larger one, until the bottom-right corner. For n = 3 the result is\n`1 2 4`\n`3 5 7`\n`6 8 9`",
   "One integer n (1 ≤ n ≤ 50).", "n lines of n numbers separated by spaces.", "All cells on one anti-diagonal have the same row + column."),
  "二維座標規律", "第 k 條斜線上的格子 (i, k-i)，i 從小到大；用計數器依序填。",
  "n=int(input())\na=[[0]*n for _ in range(n)];k=1\nfor s in range(2*n-1):\n    for i in range(n):\n        j=s-i\n        if 0<=j<n: a[i][j]=k;k+=1\nfor r in a: print(*r)",
  ["3\n", "1\n", "2\n", "4\n", "50\n"])

N("d122", 1, 2, "日期計算", "Date arithmetic",
  ("兩個日期差幾天", "每行六個整數 `y1 m1 d1 y2 m2 d2`，代表兩個日期（保證合法，年份 1900–2100，閏年規則同一般曆法）。輸出兩個日期相差幾天（取絕對值）。",
   "讀到 EOF。", "每行一個整數。", "可以用 datetime.date 相減；也練習看看自己算：把日期換成『距離某個基準日幾天』再相減。"),
  ("Days Between Two Dates", "Each line has six integers `y1 m1 d1 y2 m2 d2` describing two dates (valid, years 1900–2100, ordinary leap-year rules). Print the absolute number of days between them.",
   "Until EOF.", "One integer per line.", "You may subtract two datetime.date values, but also try it by hand: convert each date to 'days since a fixed base day' and subtract."),
  "日期", "datetime.date(y,m,d) 相減取 abs(days)。",
  "import sys,datetime\nfor l in sys.stdin:\n    p=list(map(int,l.split()))\n    if len(p)==6: print(abs((datetime.date(*p[:3])-datetime.date(*p[3:])).days))",
  ["2024 1 1 2024 12 31\n", "2000 2 28 2000 3 1\n1900 2 28 1900 3 1\n2100 2 28 2100 3 1\n2024 3 1 2024 3 1\n2024 12 31 2024 1 1\n", "1900 1 1 2100 12 31\n2100 12 31 1900 1 1\n1999 12 31 2000 1 1\n"])

N("d123", 1, 2, "時間／角度", "Time and angles",
  ("時鐘的夾角", "每行一個 24 小時制的時間 `hh:mm`。把它看成類比時鐘（12 小時制）時，時針與分針之間較小的那個夾角是幾度？輸出到小數點後 1 位。時針每分鐘走 0.5 度、分針每分鐘走 6 度；12:00 時兩針重合。",
   "每行 `hh:mm`（00:00–23:59），讀到 EOF。", "每行一個數字，小數點後恰好 1 位（結果一定是 x.0 或 x.5）。", "先算兩針各自離 12 點的角度，相減取絕對值；若超過 180 度，改取 360 減它。"),
  ("Clock Angle", "Each line is a 24-hour time `hh:mm`. Viewed on an analog 12-hour clock, what is the smaller angle between the hour hand and the minute hand, in degrees, printed with exactly one decimal digit? The hour hand moves 0.5° per minute and the minute hand 6° per minute; at 12:00 the hands coincide.",
   "Each line `hh:mm` (00:00–23:59), until EOF.", "One number per line with exactly one digit after the decimal point (always x.0 or x.5).", "Compute each hand's angle from 12 o'clock, take the absolute difference, and if it exceeds 180° use 360 minus it."),
  "數學／格式化", "時針角度 = (h % 12) * 30 + m * 0.5；分針角度 = m * 6。",
  "import sys\nfor l in sys.stdin:\n    s=l.strip()\n    if not s: continue\n    h,m=int(s[:2]),int(s[3:])\n    d=abs((h%12)*60+m-12*m)\n    d=min(d,720-d)\n    print(f'{d/2:.1f}')",
  ["03:00\n", "00:00\n12:00\n06:00\n09:00\n12:30\n03:15\n23:59\n11:59\n", "15:45\n20:20\n01:05\n07:07\n"])

N("d124", 1, 2, "stack／運算式", "Stack, expressions",
  ("後序運算式求值", "每行是一個後序（postfix）運算式：整數與 `+` `-` `*` 以空格隔開。依序處理每個符號，遇到數字就放進堆疊，遇到運算子就取出最上面兩個數 a（先放入的）與 b（後放入的），計算 a 運算子 b 再放回去。最後輸出堆疊裡唯一剩下的數。保證運算式合法。",
   "每行最多 1000 個符號，整數 0–10^9，讀到 EOF。", "每行一個整數（可能是負數或很大的整數）。", "『先放入的是左運算元』這個順序對減法很重要。"),
  ("Postfix Evaluation", "Each line is a postfix expression: integers and `+` `-` `*` separated by spaces. Process the symbols in order: push numbers on a stack; for an operator pop the top two values b (pushed later) and a (pushed earlier), compute a op b and push the result. Print the single value left on the stack. The expression is guaranteed to be valid.",
   "At most 1000 symbols per line, integers 0–10^9, until EOF.", "One integer per line (possibly negative or very large).", "The order 'the earlier pushed one is the left operand' matters for subtraction."),
  "stack", "list 當堆疊：append 放入，pop 取出；b = pop() 先取，再 a = pop()。",
  "import sys\nfor l in sys.stdin:\n    t=l.split()\n    if not t: continue\n    st=[]\n    for x in t:\n        if x in '+-*' and len(x)==1:\n            b=st.pop();a=st.pop();st.append(a+b if x=='+' else a-b if x=='-' else a*b)\n        else: st.append(int(x))\n    print(st[0])",
  ["3 4 + 2 *\n", "5\n1 2 -\n10 2 3 * -\n2 3 4 * +\n0 0 -\n", "1000000000 1000000000 * 1000000000 *\n3 4 - 5 -\n9 8 7 - -\n"])


# ======================= 階段 2 =======================
N("d125", 2, 2, "排序／統計", "Sorting, statistics",
  ("中位數", "給 n 個整數，輸出它們的中位數。n 是奇數時是排序後正中間的那個數；n 是偶數時是中間兩個數的平均——如果平均值是整數就輸出整數，否則輸出到小數點後恰好 1 位（結果一定是 x.5，負數寫成 -2.5）。",
   "第一行 n（1 ≤ n ≤ 2×10^5），第二行 n 個整數（絕對值 ≤ 10^9）。", "一個數。", "平均值如果用 `/` 會變成浮點數，整數答案要自己判斷奇偶後用 `//`。"),
  ("Median", "Given n integers, print their median. For odd n it is the middle number after sorting; for even n it is the average of the two middle numbers — print an integer if the average is an integer, otherwise print it with exactly one decimal digit (it is always x.5; write negatives as -2.5).",
   "The first line has n (1 ≤ n ≤ 2×10^5); the second line has n integers (absolute value ≤ 10^9).", "One number.", "Dividing with `/` gives a float; decide parity yourself and use `//` for integer answers."),
  "排序／奇偶分流", "排序後 n 奇數取 a[n//2]；偶數取 a[n//2-1] 與 a[n//2]，和為偶數就整除 2，否則輸出 s/2 的 .1f。",
  "n=int(input());a=sorted(map(int,input().split()))\nif n%2: print(a[n//2])\nelse:\n    s=a[n//2-1]+a[n//2]\n    print(s//2 if s%2==0 else f'{s/2:.1f}')",
  ["5\n3 1 4 1 5\n", "1\n7\n", "2\n1 2\n", "2\n-3 0\n", "4\n-1 -1 -1 -2\n", "4\n2 4 6 8\n", "6\n1000000000 1000000000 -1000000000 -1000000000 5 6\n"])

N("d126", 2, 2, "自訂排序／混合方向", "Custom sort, mixed directions",
  ("多條件排名", "n 位選手，每行 `姓名 年齡 分數`。排序規則：分數高的在前；分數相同時，年齡小的在前；年齡也相同時，姓名字典序（ASCII）小的在前。依序輸出 `姓名 年齡 分數`。",
   "第一行 n（1 ≤ n ≤ 10^5），之後 n 行：姓名是不含空白的英文字母（長度 ≤ 10），年齡 1–120，分數 0–1000。", "n 行。", "key 可以用 tuple：要『降序』的欄位取負號，其他欄位維持升序。"),
  ("Multi-key Ranking", "n contestants, each line `name age score`. Order them by higher score first; on equal scores younger age first; on equal ages by name in dictionary (ASCII) order. Print `name age score` in that order.",
   "The first line has n (1 ≤ n ≤ 10^5), then n lines: name is letters without spaces (length ≤ 10), age 1–120, score 0–1000.", "n lines.", "Use a tuple as the key: negate the fields that should be descending and keep the others ascending."),
  "key 函式", "rows.sort(key=lambda r: (-分數, 年齡, 姓名))。",
  "import sys\nd=sys.stdin.read().split()\nn=int(d[0])\nrows=[(d[1+3*i],int(d[2+3*i]),int(d[3+3*i])) for i in range(n)]\nrows.sort(key=lambda r:(-r[2],r[1],r[0]))\nfor a,b,c in rows: print(a,b,c)",
  ["4\namy 20 90\nbob 19 90\ncat 20 95\ndan 19 90\n", "1\nzed 1 0\n", "3\nBob 30 50\nbob 30 50\nAlice 30 50\n",
   (lambda r: lines(20000, *[f"{''.join(r.choice('abcAB') for _ in range(r.randint(1,4)))} {r.randint(18,22)} {r.randint(0,5)}" for _ in range(20000)]))(R(126))])

N("d128", 2, 3, "前綴和／二維", "Prefix sums, 2D",
  ("矩形區域和", "給 R×C 的整數方格與 q 個詢問，每個詢問 `r1 c1 r2 c2`（列、行都從 1 算起，r1 ≤ r2、c1 ≤ c2），輸出左上角 (r1,c1) 到右下角 (r2,c2) 這個矩形內所有數字的總和。",
   "第一行 R C q（1 ≤ R, C ≤ 500，1 ≤ q ≤ 10^5）；接著 R 行各 C 個整數（絕對值 ≤ 1000）；再接著 q 行詢問。", "每個詢問一行。", "二維前綴和：`S[i][j] = a[i][j] + S[i-1][j] + S[i][j-1] - S[i-1][j-1]`，詢問用『大減小再補回重疊』的容斥。"),
  ("Rectangle Sums", "Given an R×C grid of integers and q queries `r1 c1 r2 c2` (rows and columns are 1-based, r1 ≤ r2, c1 ≤ c2), print the sum of all numbers inside the rectangle from (r1,c1) to (r2,c2).",
   "The first line has R C q (1 ≤ R, C ≤ 500, 1 ≤ q ≤ 10^5); then R lines of C integers (absolute value ≤ 1000); then q query lines.", "One line per query.", "2D prefix sums: `S[i][j] = a[i][j] + S[i-1][j] + S[i][j-1] - S[i-1][j-1]`; answer a query by inclusion–exclusion."),
  "二維前綴和", "預處理 S；每個詢問 S[r2][c2]-S[r1-1][c2]-S[r2][c1-1]+S[r1-1][c1-1]。",
  "import sys\nd=sys.stdin.read().split()\nR,C,q=int(d[0]),int(d[1]),int(d[2]);p=3\nS=[[0]*(C+1) for _ in range(R+1)]\nfor i in range(1,R+1):\n    for j in range(1,C+1):\n        S[i][j]=int(d[p])+S[i-1][j]+S[i][j-1]-S[i-1][j-1];p+=1\nfor _ in range(q):\n    a,b,c,e=int(d[p]),int(d[p+1]),int(d[p+2]),int(d[p+3]);p+=4\n    print(S[c][e]-S[a-1][e]-S[c][b-1]+S[a-1][b-1])",
  ["3 3 2\n1 2 3\n4 5 6\n7 8 9\n1 1 3 3\n2 2 3 3\n", "1 1 1\n5\n1 1 1 1\n", "2 3 4\n-1 0 1\n2 -2 3\n1 1 1 1\n1 3 2 3\n2 1 2 3\n1 1 2 3\n"], timeout=20)

N("d129", 2, 3, "二分搜尋／答案二分", "Binary search on the answer",
  ("切繩子", "有 n 條繩子，長度分別是 a₁…aₙ（整數）。要切出 k 段『長度相同的整數長度』繩子（每條繩子可以切成好幾段，剩下的零頭不用），這個共同長度最大是多少？如果連長度 1 都切不出 k 段，輸出 0。",
   "第一行 n k（1 ≤ n ≤ 10^5，1 ≤ k ≤ 10^9），第二行 n 個整數（1 ≤ aᵢ ≤ 10^9）。", "一個整數。", "答案長度 L 越大，能切出的段數越少（單調），所以可以對 L 做二分搜尋；檢查函式是 `sum(a // L) >= k`。"),
  ("Cutting Ropes", "There are n ropes with integer lengths a₁…aₙ. You must cut k pieces of the same integer length (each rope may give several pieces; leftovers are discarded). What is the largest possible common length? If not even length 1 gives k pieces, print 0.",
   "The first line has n k (1 ≤ n ≤ 10^5, 1 ≤ k ≤ 10^9); the second has n integers (1 ≤ aᵢ ≤ 10^9).", "One integer.", "The larger the length L, the fewer pieces you can cut (monotone), so binary search on L; the check is `sum(a // L) >= k`."),
  "答案二分", "check(L) = sum(x//L) >= k；lo=0, hi=max(a)；找最大的 L 使 check 成立。",
  "n,k=map(int,input().split());a=list(map(int,input().split()))\nlo,hi=0,max(a)\nwhile lo<hi:\n    m=(lo+hi+1)//2\n    if sum(x//m for x in a)>=k: lo=m\n    else: hi=m-1\nprint(lo)",
  ["4 11\n802 743 457 539\n", "1 1\n5\n", "1 6\n5\n", "3 1000000000\n1000000000 1000000000 1000000000\n", "2 3\n7 7\n", "5 10\n1 1 1 1 1\n"])

N("d130", 2, 3, "差分陣列", "Difference arrays",
  ("區間加值", "一個長度 n 的陣列一開始全是 0。接著有 m 個操作 `l r v`：把第 l 到第 r 個位置（含，1 起算）都加上 v。做完所有操作後，輸出整個陣列。",
   "第一行 n m（1 ≤ n, m ≤ 2×10^5）；接著 m 行 `l r v`（1 ≤ l ≤ r ≤ n，|v| ≤ 10^4）。", "一行 n 個整數，以空格隔開。", "不要每次操作都跑迴圈（O(nm)）：在差分陣列 `d[l] += v; d[r+1] -= v`，最後做一次前綴和。"),
  ("Range Add", "An array of length n starts as all zeros. Then m operations `l r v` follow: add v to positions l through r (inclusive, 1-based). After all operations print the whole array.",
   "The first line has n m (1 ≤ n, m ≤ 2×10^5); then m lines `l r v` (1 ≤ l ≤ r ≤ n, |v| ≤ 10^4).", "One line of n integers separated by spaces.", "Do not loop for each operation (O(nm)): on a difference array do `d[l] += v; d[r+1] -= v`, then take one prefix sum at the end."),
  "差分", "d[l]+=v；d[r+1]-=v；最後累加。",
  "import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1]);df=[0]*(n+2)\nfor i in range(m):\n    l,r,v=int(d[2+3*i]),int(d[3+3*i]),int(d[4+3*i]);df[l]+=v;df[r+1]-=v\no=[];s=0\nfor i in range(1,n+1): s+=df[i];o.append(s)\nprint(*o)",
  ["5 3\n1 3 2\n2 5 -1\n3 3 10\n", "1 1\n1 1 5\n", "3 2\n1 3 1\n1 3 -1\n", "4 3\n4 4 7\n1 1 -7\n2 3 3\n"], timeout=20)

N("d131", 2, 2, "雙指標／滑動視窗", "Two pointers, sliding window",
  ("最短的連續區間", "給 n 個正整數與目標 S，找出總和至少是 S 的『最短連續區間』，輸出它的長度；如果整個陣列的總和都不到 S，輸出 0。",
   "第一行 n S（1 ≤ n ≤ 10^5，1 ≤ S ≤ 10^9）；第二行 n 個正整數（1 ≤ aᵢ ≤ 10^4）。", "一個整數。", "全是正數，所以右端點右移會讓總和變大、左端點右移會讓總和變小——這就是雙指標能成立的原因。"),
  ("Shortest Subarray", "Given n positive integers and a target S, find the shortest contiguous subarray whose sum is at least S and print its length; if even the whole array sums to less than S, print 0.",
   "The first line has n S (1 ≤ n ≤ 10^5, 1 ≤ S ≤ 10^9); the second has n positive integers (1 ≤ aᵢ ≤ 10^4).", "One integer.", "All numbers are positive, so moving the right end right increases the sum and moving the left end right decreases it — that is why two pointers work."),
  "雙指標", "右指標一路加；總和 ≥ S 時就縮左端並更新最短長度。",
  "n,S=map(int,input().split());a=list(map(int,input().split()))\nl=s=0;best=n+1\nfor r in range(n):\n    s+=a[r]\n    while s>=S:\n        best=min(best,r-l+1);s-=a[l];l+=1\nprint(best if best<=n else 0)",
  ["6 7\n2 3 1 2 4 3\n", "1 5\n5\n", "1 6\n5\n", "3 100\n1 2 3\n", "5 5\n1 1 1 1 1\n", "4 3\n10 1 1 1\n"])

N("d132", 2, 2, "滑動視窗／集合", "Sliding window, sets",
  ("最長不重複子字串", "對每一行字串，輸出『不含重複字元』的最長連續子字串的長度。",
   "每行一個字串（1 ≤ 長度 ≤ 10^5，只含可見 ASCII 字元，不含空白），讀到 EOF，最多 10 行。", "每行一個整數。", "視窗 [l, r]：右端點加入字元；若這個字元已在視窗裡，就把左端點推到它上次出現位置的下一格。"),
  ("Longest Substring Without Repeats", "For each line, print the length of the longest contiguous substring that contains no repeated character.",
   "One string per line (1 ≤ length ≤ 10^5, visible ASCII characters without spaces), until EOF, at most 10 lines.", "One integer per line.", "Window [l, r]: add the character at r; if it is already inside the window, move l to just after its previous position."),
  "滑動視窗", "last[c] 記每個字元最後出現位置；l = max(l, last[c]+1)。",
  "import sys\nfor line in sys.stdin:\n    s=line.strip()\n    if not s: continue\n    last={};l=best=0\n    for r,c in enumerate(s):\n        if c in last and last[c]>=l: l=last[c]+1\n        last[c]=r;best=max(best,r-l+1)\n    print(best)",
  ["abcabcbb\n", "a\naa\nab\nabba\ndvdf\nabcdefg\npwwkew\n", "tmmzuxt\nabcabcabcabc\n!@#$%^&*()!@#\n"])

N("d133", 2, 2, "單調 stack", "Monotonic stack",
  ("下一個更大的數", "給 n 個整數。對每個位置 i，找出右邊第一個『嚴格大於』aᵢ 的數的值；如果右邊沒有，輸出 -1。",
   "第一行 n（1 ≤ n ≤ 2×10^5），第二行 n 個整數（絕對值 ≤ 10^9）。", "一行 n 個整數，以空格隔開。", "由右往左掃，stack 裡維持『還可能成為答案』的候選（由下往上遞減）。"),
  ("Next Greater Element", "Given n integers, for every position i find the value of the first number to its right that is strictly greater than aᵢ; print -1 if none exists.",
   "The first line has n (1 ≤ n ≤ 2×10^5); the second has n integers (absolute value ≤ 10^9).", "One line of n integers separated by spaces.", "Scan from right to left, keeping a stack of candidates that could still be an answer (decreasing from bottom to top)."),
  "單調 stack", "從右往左：while stack 且 stack[-1] <= a[i]: pop；答案是 stack[-1] 或 -1；再把 a[i] 推入。",
  "n=int(input());a=list(map(int,input().split()))\nst=[];res=[0]*n\nfor i in range(n-1,-1,-1):\n    while st and st[-1]<=a[i]: st.pop()\n    res[i]=st[-1] if st else -1\n    st.append(a[i])\nprint(*res)",
  ["5\n2 1 2 4 3\n", "1\n5\n", "4\n3 3 3 3\n", "5\n5 4 3 2 1\n", "5\n1 2 3 4 5\n", "6\n-1 -2 0 -3 -4 1\n"])

N("d135", 2, 3, "stack／模擬", "Stack, simulation",
  ("火車調度", "n 節車廂依編號 1, 2, …, n 的順序開進一條死巷（只有一個出入口，後進先出）。每次可以把下一節車廂開進去，或把巷子裡最外面（最後進去）的車廂開出來。給定一個『開出的順序』，問是否能做到。有 t 組測資。",
   "第一行 t（1 ≤ t ≤ 100）；每組兩行：第一行 n（1 ≤ n ≤ 10^5），第二行是 1..n 的一個排列（開出的順序）。所有組的 n 總和 ≤ 2×10^5。", "每組輸出 `YES` 或 `NO`。", "模擬：想要輸出 x，就把還沒進去的車廂依序推進去直到 x 進入，再看最外面是不是 x。"),
  ("Train Shunting", "n cars enter a dead-end siding (a single entrance, last in first out) in the order 1, 2, …, n. Each step you may either push the next car into the siding or pop the outermost (most recently pushed) car out. Given a required departure order, decide whether it is possible. There are t test cases.",
   "The first line has t (1 ≤ t ≤ 100); each case has two lines: n (1 ≤ n ≤ 10^5) and a permutation of 1..n (the departure order). The sum of n over all cases is ≤ 2×10^5.", "Per case print `YES` or `NO`.", "Simulate: to output x, push cars until x has entered, then check that the outermost one is x."),
  "stack 模擬", "next 指向下一個要進的車廂；對每個目標 x：while 巷子最外面不是 x 且 next ≤ n: 推入；最後最外面不是 x 就 NO。",
  "import sys\nd=sys.stdin.read().split()\nt=int(d[0]);p=1\nfor _ in range(t):\n    n=int(d[p]);p+=1;order=d[p:p+n];p+=n\n    st=[];nxt=1;ok=True\n    for x in order:\n        x=int(x)\n        while nxt<=n and (not st or st[-1]!=x) and nxt<=x: st.append(nxt);nxt+=1\n        if st and st[-1]==x: st.pop()\n        else: ok=False;break\n    print('YES' if ok else 'NO')",
  ["3\n5\n5 4 3 2 1\n5\n1 2 3 4 5\n5\n3 1 2 4 5\n", "2\n1\n1\n3\n2 3 1\n", "2\n3\n3 1 2\n4\n4 3 2 1\n"], timeout=20)

N("d136", 2, 2, "heap", "Heaps",
  ("資料流的第 k 大", "數字一個接一個進來。從第 k 個數開始，每進來一個數，就輸出『目前已進來的所有數中第 k 大的值』（有重複時重複的數各算一個，例如 5 5 3 的第 2 大是 5）。",
   "第一行 n k（1 ≤ k ≤ n ≤ 2×10^5）；第二行 n 個整數（絕對值 ≤ 10^9）。", "一行 n−k+1 個整數，以空格隔開。", "維持一個大小為 k 的最小堆：堆頂就是第 k 大。新數比堆頂大才換掉堆頂。"),
  ("K-th Largest in a Stream", "Numbers arrive one by one. Starting from the k-th number, after each arrival print the k-th largest value among all numbers received so far (duplicates count separately: in 5 5 3 the 2nd largest is 5).",
   "The first line has n k (1 ≤ k ≤ n ≤ 2×10^5); the second has n integers (absolute value ≤ 10^9).", "One line of n−k+1 integers separated by spaces.", "Keep a min-heap of size k: its top is the k-th largest. Replace the top only when the new number is larger."),
  "heap／固定大小", "heapq 最小堆保留最大的 k 個；堆頂 = 第 k 大。",
  "import heapq\nn,k=map(int,input().split());a=list(map(int,input().split()))\nh=a[:k];heapq.heapify(h);o=[h[0]]\nfor x in a[k:]:\n    if x>h[0]: heapq.heapreplace(h,x)\n    o.append(h[0])\nprint(*o)",
  ["6 3\n4 5 8 2 9 1\n", "1 1\n7\n", "3 2\n5 5 3\n", "5 5\n1 2 3 4 5\n", "5 1\n3 1 4 1 5\n", "5 2\n-1 -2 -3 -4 -5\n"])

N("d137", 2, 3, "雙 heap／中位數", "Two heaps, running median",
  ("動態中位數", "數字一個接一個進來。每進來一個數，就輸出目前所有數的中位數，其中『偶數個數時取較小的那個中位數』（也就是目前 i 個數排序後的第 ⌈i/2⌉ 小）。",
   "第一行 n（1 ≤ n ≤ 10^5），第二行 n 個整數（絕對值 ≤ 10^9）。", "一行 n 個整數，以空格隔開。", "用一個最大堆放較小的一半、一個最小堆放較大的一半，並維持最大堆的大小不小於最小堆。"),
  ("Running Median", "Numbers arrive one by one. After each arrival print the median of all numbers so far, where for an even count the lower median is used (the ⌈i/2⌉-th smallest of the first i numbers).",
   "The first line has n (1 ≤ n ≤ 10^5); the second has n integers (absolute value ≤ 10^9).", "One line of n integers separated by spaces.", "Keep the smaller half in a max-heap and the larger half in a min-heap, with the max-heap never smaller than the min-heap."),
  "雙 heap", "新數先進較小堆（取負號做最大堆），再把堆頂搬到較大堆，平衡大小後輸出較小堆頂。",
  "import heapq\nn=int(input());a=list(map(int,input().split()))\nlo=[];hi=[];o=[]\nfor x in a:\n    heapq.heappush(lo,-x)\n    heapq.heappush(hi,-heapq.heappop(lo))\n    if len(hi)>len(lo): heapq.heappush(lo,-heapq.heappop(hi))\n    o.append(-lo[0])\nprint(*o)",
  ["5\n5 2 8 1 9\n", "1\n3\n", "4\n1 1 1 1\n", "6\n6 5 4 3 2 1\n", "6\n1 2 3 4 5 6\n", "5\n-5 5 -5 5 0\n"])

N("d138", 2, 3, "貪心／區間覆蓋", "Greedy, interval cover",
  ("區間覆蓋", "數線上有 n 個閉區間 [lᵢ, rᵢ]。要選出最少的區間，讓線段 [0, L] 上的每一點都至少被一個選到的區間蓋住（區間端點相接視為蓋住）。輸出最少需要幾個，做不到就輸出 -1。",
   "第一行 L n（1 ≤ L ≤ 10^9，1 ≤ n ≤ 10^5）；接著 n 行 `l r`（0 ≤ l < r ≤ 10^9）。", "一個整數。", "貪心：目前已蓋到 cur，在所有 l ≤ cur 的區間中挑 r 最大的；這需要先把區間依 l 排序。"),
  ("Interval Cover", "There are n closed intervals [lᵢ, rᵢ] on a line. Choose the fewest intervals so that every point of the segment [0, L] is covered by at least one chosen interval (touching endpoints count as covering). Print the minimum number, or -1 if impossible.",
   "The first line has L n (1 ≤ L ≤ 10^9, 1 ≤ n ≤ 10^5); then n lines `l r` (0 ≤ l < r ≤ 10^9).", "One integer.", "Greedy: with everything up to cur covered, among all intervals with l ≤ cur pick the one with the largest r; sort the intervals by l first."),
  "貪心／掃描", "依 l 排序；cur=0；每輪在 l ≤ cur 的區間中找最大 r，若沒有推進就 -1。",
  "import sys\nd=sys.stdin.read().split()\nL,n=int(d[0]),int(d[1])\niv=sorted((int(d[2+2*i]),int(d[3+2*i])) for i in range(n))\ncur=0;i=0;c=0\nwhile cur<L:\n    best=cur\n    while i<n and iv[i][0]<=cur:\n        best=max(best,iv[i][1]);i+=1\n    if best==cur: c=-1;break\n    cur=best;c+=1\nprint(c)",
  ["10 3\n0 5\n4 10\n3 7\n", "5 1\n0 5\n", "5 1\n1 6\n", "10 2\n0 4\n5 10\n", "10 2\n0 5\n5 10\n", "10 3\n0 5\n3 10\n4 6\n", "1 2\n0 1\n0 1\n", "10 4\n0 3\n2 5\n4 8\n7 12\n"])

N("d139", 2, 2, "貪心／雙指標", "Greedy, two pointers",
  ("救生艇", "n 個人要過河，第 i 個人重 wᵢ。每艘船最多載 2 個人，且總重不能超過 W（保證每個人單獨都載得動）。最少需要幾艘船？",
   "第一行 n W（1 ≤ n ≤ 10^5，1 ≤ W ≤ 10^9）；第二行 n 個整數（1 ≤ wᵢ ≤ W）。", "一個整數。", "排序後讓最重的人配最輕的人：配得上就一起走，配不上最重的人自己搭一艘。"),
  ("Lifeboats", "n people cross a river, person i weighs wᵢ. Each boat carries at most 2 people with a total weight not exceeding W (everyone can be carried alone). What is the minimum number of boats?",
   "The first line has n W (1 ≤ n ≤ 10^5, 1 ≤ W ≤ 10^9); the second has n integers (1 ≤ wᵢ ≤ W).", "One integer.", "Sort, then pair the heaviest with the lightest: if they fit together they leave together, otherwise the heaviest goes alone."),
  "貪心＋雙指標", "排序；l=0, r=n-1；a[l]+a[r] ≤ W 就 l+=1；不論如何 r-=1，船數 +1。",
  "n,W=map(int,input().split());a=sorted(map(int,input().split()))\nl,r,c=0,n-1,0\nwhile l<=r:\n    if a[l]+a[r]<=W and l<r: l+=1\n    r-=1;c+=1\nprint(c)",
  ["4 5\n3 2 2 1\n", "1 10\n10\n", "2 10\n5 5\n", "2 9\n5 5\n", "5 10\n1 1 1 1 1\n", "3 3\n3 3 3\n", "4 100\n50 50 50 50\n"])

N("d140", 2, 2, "貪心／排序", "Greedy, sorting",
  ("最小總等待時間", "一台機器依序處理 n 個工作，第 i 個工作需要 tᵢ 單位時間，一次只能做一個，中間不能中斷。一個工作的『等待時間』是它開始前已經過的時間（第一個工作等待 0）。安排順序使所有工作等待時間的總和最小，輸出這個最小總和。",
   "第一行 n（1 ≤ n ≤ 10^5），第二行 n 個整數（1 ≤ tᵢ ≤ 10^4）。", "一個整數。", "交換論證：把短的工作排前面，它的時間會被後面的每一個工作『等待』更少次。"),
  ("Minimum Total Waiting Time", "One machine processes n jobs one after another; job i takes tᵢ time units and cannot be interrupted. A job's waiting time is the time elapsed before it starts (the first job waits 0). Order the jobs to minimize the sum of all waiting times and print that minimum.",
   "The first line has n (1 ≤ n ≤ 10^5); the second has n integers (1 ≤ tᵢ ≤ 10^4).", "One integer.", "Exchange argument: putting a short job earlier makes every later job wait for it fewer times."),
  "貪心／交換論證", "由小到大排序；累計已經過的時間，每個工作的等待時間就是累計值。",
  "n=int(input());a=sorted(map(int,input().split()))\ncur=tot=0\nfor x in a: tot+=cur;cur+=x\nprint(tot)",
  ["4\n3 1 4 2\n", "1\n5\n", "2\n1 1\n", "5\n5 4 3 2 1\n", "3\n10000 10000 10000\n"])

N("d141", 2, 2, "遞迴", "Recursion",
  ("河內塔", "n 個大小不同的圓盤由小到大疊在 A 柱上（小的在上），要全部移到 C 柱，每次只能移一個，且大盤不能壓在小盤上，B 柱可以暫放。輸出最少移動次數，以及每一步移動的『從哪根柱子 到哪根柱子』，格式 `X Y`（最少步數的走法是唯一的）。",
   "一個整數 n（1 ≤ n ≤ 10）。", "第一行是最少步數 m（= 2ⁿ − 1），接著 m 行各一步，例如 `A C`。", "遞迴想法：先把上面 n−1 個移到 B，再移最大的到 C，最後把 n−1 個從 B 移到 C。"),
  ("Tower of Hanoi", "n discs of different sizes are stacked on peg A (smaller on top) and must all be moved to peg C, one disc at a time, never placing a larger disc on a smaller one; peg B may be used as temporary storage. Print the minimum number of moves and every move as `X Y` (from peg X to peg Y). The shortest solution is unique.",
   "One integer n (1 ≤ n ≤ 10).", "The first line is the minimum number of moves m (= 2ⁿ − 1), followed by m lines, one move each, such as `A C`.", "Recursive idea: move the top n−1 discs to B, move the largest to C, then move the n−1 discs from B to C."),
  "遞迴", "hanoi(n, 起, 終, 暫)：n==0 回傳；hanoi(n-1, 起, 暫, 終)；記錄 起→終；hanoi(n-1, 暫, 終, 起)。",
  "import sys\nsys.setrecursionlimit(10000)\nn=int(input());mv=[]\ndef h(k,a,c,b):\n    if k==0: return\n    h(k-1,a,b,c);mv.append(a+' '+c);h(k-1,b,c,a)\nh(n,'A','C','B')\nprint(len(mv))\nprint('\\n'.join(mv))",
  ["3\n", "1\n", "2\n", "4\n", "5\n", "6\n", "7\n", "8\n", "10\n"])

N("d142", 2, 2, "遞迴／組合", "Recursion, combinations",
  ("組合列舉", "輸入 n 和 k，依字典序輸出從 1..n 中選 k 個不同數字的所有組合（每個組合內部由小到大，數字以空格隔開，一個組合一行）。",
   "一行兩個整數 n k（1 ≤ k ≤ n ≤ 10）。", "C(n,k) 行。", "遞迴參數帶『下一個可選的最小數字』，就不會產生重複或順序不同的同一組合。"),
  ("Enumerating Combinations", "Given n and k, print all combinations of k distinct numbers chosen from 1..n in lexicographic order (numbers inside a combination ascending, separated by spaces, one combination per line).",
   "One line with two integers n k (1 ≤ k ≤ n ≤ 10).", "C(n,k) lines.", "Pass 'the smallest number you may still choose' down the recursion so that no combination is produced twice in different orders."),
  "遞迴／回溯", "go(start, 目前選的)：長度 = k 就輸出；否則 for x in start..n：選 x，go(x+1, …)。",
  "n,k=map(int,input().split())\ndef go(s,cur):\n    if len(cur)==k: print(*cur);return\n    for x in range(s,n+1): go(x+1,cur+[x])\ngo(1,[])",
  ["4 2\n", "1 1\n", "3 3\n", "5 1\n", "6 3\n", "10 5\n"])

N("d143", 2, 3, "回溯／剪枝", "Backtracking, pruning",
  ("質數環", "把 1 到 n 這 n 個數排成一個圓環（n = 1 時只有一個數，它和自己相鄰、和是 2 是質數，答案是 1；n ≥ 3 的奇數答案是 0），要求圓環上每相鄰兩數（包括最後一個和第一個）的和都是質數。固定 1 放在第一個位置，數有幾種排法（順時針與逆時針的鏡像算不同的排法）。",
   "每行一個整數 n（1 ≤ n ≤ 14），最多 14 行，讀到 EOF。", "每行一個整數。", "逐個位置放數字，放不下就立刻回頭（剪枝）：新放的數必須和前一個的和是質數，最後還要檢查和 1 的和。"),
  ("Prime Ring", "Arrange the n numbers 1 to n in a circle so that the sum of every two neighbours (including the last and the first) is prime. For n = 1 the single number is its own neighbour (sum 2, prime), so the answer is 1; for odd n ≥ 3 the answer is 0. Fix 1 in the first position and count the arrangements (mirror images in clockwise/counter-clockwise order count as different).",
   "One integer n per line (1 ≤ n ≤ 14), at most 14 lines, until EOF.", "One integer per line.", "Place numbers position by position and back up as soon as it fails (pruning): the new number must sum to a prime with the previous one, and finally the last must also sum to a prime with 1."),
  "回溯／剪枝", "go(位置)：試每個沒用過的 x，若 x + 前一個是質數就放；放滿後檢查 x + 1。",
  "import sys\nP={2,3,5,7,11,13,17,19,23,29}\ndef cnt(n):\n    if n==1: return 1\n    if n%2: return 0\n    used=[False]*(n+1);used[1]=True;c=0\n    def go(prev,k):\n        nonlocal c\n        if k==n:\n            if prev+1 in P: c+=1\n            return\n        for x in range(2,n+1):\n            if not used[x] and prev+x in P:\n                used[x]=True;go(x,k+1);used[x]=False\n    go(1,1)\n    return c\nfor l in sys.stdin:\n    if l.strip(): print(cnt(int(l)))",
  ["4\n", "1\n2\n3\n4\n5\n6\n7\n8\n", "10\n12\n14\n", "6\n", "12\n", "13\n", "9\n", "8\n"], timeout=30)

N("d144", 2, 3, "位元運算／數學", "Bit operations, math",
  ("1 到 n 的位元 1 總數", "對每個 n，求 1, 2, …, n 這 n 個數的二進位表示裡，所有「1」的個數總和（例如 n = 3：1=1、2=10、3=11，共 4 個）。",
   "每行一個整數 n（1 ≤ n ≤ 10^18），最多 1000 行，讀到 EOF。", "每行一個整數。", "逐位看：第 i 位（從 0 起）的 1 每 2^(i+1) 個數出現一段、每段長 2^i——用『完整週期數 × 2^i 加上最後不完整的部分』計算。"),
  ("Total Set Bits up to n", "For each n, count the total number of 1 bits in the binary representations of 1, 2, …, n (for n = 3: 1=1, 2=10, 3=11, total 4).",
   "One integer n per line (1 ≤ n ≤ 10^18), at most 1000 lines, until EOF.", "One integer per line.", "Look at one bit position at a time: bit i (from 0) is 1 for a run of 2^i numbers in every period of 2^(i+1) — use 'full periods × 2^i plus the partial last period'."),
  "位元計數／週期", "對每個 i：period = 2^(i+1)；full = (n+1)//period；ans += full * 2^i + max(0, (n+1) % period - 2^i)。",
  "import sys\nfor l in sys.stdin:\n    if l.strip():\n        n=int(l);tot=0;i=0\n        while (1<<i)<=n:\n            p=1<<(i+1);tot+=((n+1)//p)*(1<<i)+max(0,(n+1)%p-(1<<i));i+=1\n        print(tot)",
  ["3\n", "1\n2\n3\n4\n7\n8\n15\n16\n100\n", "1000000000000000000\n576460752303423487\n576460752303423488\n999999999999999999\n"])

N("d145", 2, 2, "位元運算／子集合", "Bitmasks, subsets",
  ("子集合列舉", "輸入 n，依『位元遮罩由小到大』輸出 {1,2,…,n} 的所有子集合：遮罩 m 的第 i−1 位（從最低位算起）是 1，代表元素 i 在子集合裡。每個子集合一行，寫成 `{a,b,c}`（元素由小到大，逗號後沒有空格），空集合寫成 `{}`。",
   "一個整數 n（0 ≤ n ≤ 10）。", "2ⁿ 行。", "`for m in range(1 << n)`，再用 `m >> i & 1` 判斷第 i 位。"),
  ("Listing Subsets", "Read n and print all subsets of {1,2,…,n} in increasing order of their bitmask: bit i−1 (counting from the lowest bit) of mask m being 1 means element i belongs to the subset. One subset per line, written `{a,b,c}` (elements ascending, no spaces after the commas); the empty set is `{}`.",
   "One integer n (0 ≤ n ≤ 10).", "2ⁿ lines.", "`for m in range(1 << n)`, and test bit i with `m >> i & 1`."),
  "位元遮罩", "對每個 m，收集 m>>i&1 為真的 i+1，格式化成 {…}。",
  "n=int(input())\nfor m in range(1<<n): print('{'+','.join(str(i+1) for i in range(n) if m>>i&1)+'}')",
  ["3\n", "0\n", "1\n", "2\n", "4\n", "10\n"])


# ======================= 階段 3 =======================
def grid01(r, R, C, p):
    return f"{R} {C}\n" + "\n".join("".join("1" if r.random() < p else "0" for _ in range(C)) for _ in range(R)) + "\n"


N("d146", 3, 2, "DFS／BFS 連通區域", "Flood fill, connected regions",
  ("島嶼數量", "R×C 的地圖，`1` 是陸地、`0` 是海。上下左右相鄰的陸地屬於同一座島（斜角不算相連）。輸出島嶼的數量。",
   "第一行 R C（1 ≤ R, C ≤ 500），接著 R 行，每行 C 個字元（只有 0 和 1，沒有空格）。", "一個整數。", "掃描每個格子：遇到沒走過的陸地就算一座新島，並用 BFS（或迭代的 DFS）把整座島標記起來。遞迴 DFS 在 250000 格的長條島上會爆掉。"),
  ("Number of Islands", "A map of R×C cells: `1` is land and `0` is sea. Land cells adjacent up, down, left or right belong to the same island (diagonal neighbours do not connect). Print the number of islands.",
   "The first line has R C (1 ≤ R, C ≤ 500), then R lines of C characters (only 0 and 1, no spaces).", "One integer.", "Scan every cell: an unvisited land cell starts a new island, and a BFS (or iterative DFS) marks the whole island. Recursive DFS blows the stack on a 250000-cell snake-like island."),
  "flood fill", "for 每個格子: 若是 '1' 且沒走過 → 島數 +1，BFS 標記整座島。",
  "from collections import deque\nR,C=map(int,input().split());g=[list(input()) for _ in range(R)];k=0\nfor i in range(R):\n    for j in range(C):\n        if g[i][j]=='1':\n            k+=1;g[i][j]='0';q=deque([(i,j)])\n            while q:\n                x,y=q.popleft()\n                for a,b in((x+1,y),(x-1,y),(x,y+1),(x,y-1)):\n                    if 0<=a<R and 0<=b<C and g[a][b]=='1': g[a][b]='0';q.append((a,b))\nprint(k)",
  ["4 5\n11000\n11000\n00100\n00011\n", "1 1\n0\n", "1 1\n1\n", "3 3\n101\n010\n101\n", "2 2\n11\n11\n", "3 4\n0000\n0000\n0000\n", "1 7\n1011101\n"])

N("d147", 3, 2, "BFS／最短步數", "BFS, minimum moves",
  ("騎士的最少步數", "N×N 的棋盤（行列都從 1 算起），西洋棋騎士每步走『日』字（水平 2 格垂直 1 格，或水平 1 格垂直 2 格）。有 t 個詢問，每個給棋盤大小與起點、終點，輸出最少步數；走不到輸出 -1。",
   "第一行 t（1 ≤ t ≤ 100）；之後 t 行，每行 `N r1 c1 r2 c2`（1 ≤ N ≤ 50，座標都在棋盤內）。", "每個詢問一行。", "BFS 求最少步數；N 很小的棋盤（如 2×2、3×3）會有走不到的格子。"),
  ("Knight's Shortest Path", "On an N×N board (rows and columns from 1) a chess knight moves in an L-shape (2 squares horizontally and 1 vertically, or 1 horizontally and 2 vertically). For each of t queries (board size, start, target) print the minimum number of moves, or -1 if the target is unreachable.",
   "The first line has t (1 ≤ t ≤ 100); then t lines `N r1 c1 r2 c2` (1 ≤ N ≤ 50, coordinates inside the board).", "One line per query.", "BFS gives the fewest moves; tiny boards (such as 2×2 and 3×3) have unreachable squares."),
  "BFS", "八個方向 (±1,±2)、(±2,±1)；dist 陣列；到達終點就輸出。",
  "from collections import deque\nt=int(input())\nfor _ in range(t):\n    n,r1,c1,r2,c2=map(int,input().split())\n    d={(r1,c1):0};q=deque([(r1,c1)])\n    while q:\n        x,y=q.popleft()\n        for dx,dy in((1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)):\n            a,b=x+dx,y+dy\n            if 1<=a<=n and 1<=b<=n and (a,b) not in d: d[(a,b)]=d[(x,y)]+1;q.append((a,b))\n    print(d.get((r2,c2),-1))",
  ["3\n8 1 1 8 8\n3 1 1 3 3\n3 2 2 1 1\n", "4\n1 1 1 1 1\n2 1 1 2 2\n3 1 1 2 3\n8 1 1 1 2\n", "3\n50 1 1 50 50\n5 3 3 3 3\n4 1 1 4 4\n"])

N("d148", 3, 2, "圖／二分圖", "Graphs, bipartite check",
  ("二分圖判斷", "無向圖 n 個點 m 條邊。能不能把所有點塗成黑白兩色，使每條邊兩端的顏色都不同？能輸出 `YES`，不能輸出 `NO`。自己連到自己的邊（自環）會讓答案變成 `NO`；圖可能不連通。",
   "第一行 n m（1 ≤ n ≤ 10^5，0 ≤ m ≤ 2×10^5），接著 m 行 `u v`（1 ≤ u, v ≤ n，可能有重邊與自環）。", "`YES` 或 `NO`。", "對每個連通塊 BFS 塗色；遇到兩端同色的邊就是奇環。"),
  ("Bipartite Check", "An undirected graph has n vertices and m edges. Can all vertices be colored black or white so that the two ends of every edge have different colors? Print `YES` or `NO`. A self-loop makes the answer `NO`; the graph may be disconnected.",
   "The first line has n m (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2×10^5), then m lines `u v` (1 ≤ u, v ≤ n; multi-edges and self-loops may occur).", "`YES` or `NO`.", "BFS-color each connected component; an edge whose ends share a color reveals an odd cycle."),
  "BFS 塗色", "color[]= -1；BFS 時鄰居必須是相反色。",
  "import sys\nfrom collections import deque\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1]);adj=[[] for _ in range(n+1)]\nfor i in range(m):\n    u,v=int(d[2+2*i]),int(d[3+2*i]);adj[u].append(v);adj[v].append(u)\ncol=[-1]*(n+1);ok=True\nfor s in range(1,n+1):\n    if col[s]>=0 or not ok: continue\n    col[s]=0;q=deque([s])\n    while q and ok:\n        u=q.popleft()\n        for v in adj[u]:\n            if col[v]<0: col[v]=col[u]^1;q.append(v)\n            elif col[v]==col[u]: ok=False;break\nprint('YES' if ok else 'NO')",
  ["4 4\n1 2\n2 3\n3 4\n4 1\n", "3 3\n1 2\n2 3\n3 1\n", "1 0\n", "1 1\n1 1\n", "4 2\n1 2\n3 4\n", "5 5\n1 2\n2 3\n3 4\n4 5\n5 2\n", "2 3\n1 2\n1 2\n2 1\n", "5 4\n1 2\n3 4\n4 5\n5 3\n"])

N("d149", 3, 2, "圖／樹的判斷", "Graphs, tree test",
  ("這是一棵樹嗎", "無向圖 n 個點 m 條邊。它是不是一棵『樹』（連通且沒有環）？是輸出 `YES`，否則輸出 `NO`。n = 1 且 m = 0 的單一點算樹；重邊與自環都算環。",
   "第一行 n m（1 ≤ n ≤ 10^5，0 ≤ m ≤ 2×10^5），接著 m 行 `u v`。", "`YES` 或 `NO`。", "樹的充要條件：m = n − 1 且連通。可以用並查集：m = n−1 且每條邊都能成功合併。"),
  ("Is It a Tree?", "An undirected graph has n vertices and m edges. Is it a tree (connected and without cycles)? Print `YES` or `NO`. A single vertex (n = 1, m = 0) is a tree; multi-edges and self-loops count as cycles.",
   "The first line has n m (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2×10^5), then m lines `u v`.", "`YES` or `NO`.", "A graph is a tree iff m = n − 1 and it is connected. With union–find: m = n−1 and every edge merges two different components."),
  "並查集", "m != n-1 → NO；否則每條邊 union，遇到已同組的邊就 NO。",
  "import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\nif m!=n-1: print('NO')\nelse:\n    p=list(range(n+1))\n    def f(x):\n        while p[x]!=x: p[x]=p[p[x]];x=p[x]\n        return x\n    ok=True\n    for i in range(m):\n        a,b=f(int(d[2+2*i])),f(int(d[3+2*i]))\n        if a==b: ok=False;break\n        p[a]=b\n    print('YES' if ok else 'NO')",
  ["4 3\n1 2\n2 3\n3 4\n", "1 0\n", "2 1\n1 1\n", "4 3\n1 2\n1 2\n3 4\n", "3 3\n1 2\n2 3\n3 1\n", "3 1\n1 2\n", "5 4\n1 2\n1 3\n1 4\n1 5\n"])

N("d150", 3, 2, "並查集／偵測環", "Union-find, cycle detection",
  ("第一條形成環的邊", "無向圖一開始沒有任何邊，依輸入順序一條一條加入。輸出『加入後第一次讓圖出現環』的那條邊是第幾條（從 1 算起；自環與重邊也算環）；如果全部加完都沒有環，輸出 0。",
   "第一行 n m（1 ≤ n ≤ 10^5，0 ≤ m ≤ 2×10^5），接著 m 行 `u v`。", "一個整數。", "加入 (u, v) 前它們已經連通，這條邊就會形成環。"),
  ("First Edge Forming a Cycle", "An undirected graph starts with no edges and edges are added in input order. Print the index (from 1) of the edge whose addition first creates a cycle (self-loops and repeated edges count as cycles); print 0 if no cycle ever appears.",
   "The first line has n m (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2×10^5), then m lines `u v`.", "One integer.", "If u and v are already connected before an edge (u, v) is added, that edge closes a cycle."),
  "並查集", "find(u) == find(v) 就是答案。",
  "import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1]);p=list(range(n+1))\ndef f(x):\n    while p[x]!=x: p[x]=p[p[x]];x=p[x]\n    return x\nans=0\nfor i in range(m):\n    a,b=f(int(d[2+2*i])),f(int(d[3+2*i]))\n    if a==b: ans=i+1;break\n    p[a]=b\nprint(ans)",
  ["4 4\n1 2\n2 3\n3 4\n4 1\n", "3 2\n1 2\n2 3\n", "3 3\n1 2\n1 2\n2 3\n", "2 1\n2 2\n", "1 0\n", "5 5\n1 2\n3 4\n2 3\n4 1\n5 5\n"])

N("d152", 3, 2, "拓撲排序／分層", "Topological sort, layers",
  ("最少學期數", "n 門課，m 個先修限制 `a b` 表示 a 要在 b 之前修完（不能同一學期）。每學期可以修任意多門『先修課都已經在之前的學期修完』的課。最少要幾個學期才能修完全部？如果先修限制有環（永遠修不完；自己是自己的先修也算環）輸出 -1。",
   "第一行 n m（1 ≤ n ≤ 10^5，0 ≤ m ≤ 2×10^5），接著 m 行 `a b`（可能有重複的限制）。", "一個整數。", "答案就是 DAG 上『最長路徑的點數』；Kahn 演算法一層一層處理就是在數學期。"),
  ("Minimum Semesters", "There are n courses and m prerequisites `a b` meaning a must be finished before b (not in the same semester). In each semester you may take any number of courses whose prerequisites were all completed in earlier semesters. What is the minimum number of semesters to finish everything? Print -1 if the prerequisites contain a cycle (a course being its own prerequisite counts as a cycle).",
   "The first line has n m (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2×10^5), then m lines `a b` (repeats may occur).", "One integer.", "The answer is the number of vertices on the longest path of the DAG; Kahn's algorithm processed layer by layer counts the semesters."),
  "拓撲排序／BFS 分層", "每輪取出所有入度為 0 的課，學期數 +1，並更新後續課的入度。",
  "import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1]);adj=[[] for _ in range(n+1)];ind=[0]*(n+1)\nfor i in range(m):\n    a,b=int(d[2+2*i]),int(d[3+2*i]);adj[a].append(b);ind[b]+=1\ncur=[i for i in range(1,n+1) if ind[i]==0];sem=done=0\nwhile cur:\n    sem+=1;nxt=[]\n    for u in cur:\n        done+=1\n        for v in adj[u]:\n            ind[v]-=1\n            if ind[v]==0: nxt.append(v)\n    cur=nxt\nprint(sem if done==n else -1)",
  ["4 3\n1 2\n2 3\n1 4\n", "1 0\n", "3 0\n", "2 2\n1 2\n2 1\n", "3 3\n1 2\n1 2\n2 3\n", "5 4\n1 5\n2 5\n3 5\n4 5\n", "3 1\n2 2\n"])

N("d154", 3, 3, "最短路徑／計數", "Shortest paths, counting",
  ("最短路徑有幾條", "無向加權圖 n 個點 m 條邊（邊權 ≥ 1）。從點 1 到點 n 的最短路徑長度是多少、總共有幾條不同的最短路徑？路徑數對 1000000007 取餘數。到不了點 n 時輸出 `-1 0`。",
   "第一行 n m（1 ≤ n ≤ 10^4，0 ≤ m ≤ 5×10^4），接著 m 行 `u v w`（1 ≤ w ≤ 1000，可能有重邊；重邊算不同的邊）。", "一行：最短距離 路徑數。", "Dijkstra 的過程中同時記 cnt[v]：找到更短的距離就把 cnt 設為來源的 cnt，距離相等就把來源的 cnt 加進去。"),
  ("Counting Shortest Paths", "An undirected weighted graph has n vertices and m edges (weights ≥ 1). What is the shortest distance from vertex 1 to vertex n, and how many different shortest paths are there? Print the count modulo 1000000007. If vertex n is unreachable print `-1 0`.",
   "The first line has n m (1 ≤ n ≤ 10^4, 0 ≤ m ≤ 5×10^4), then m lines `u v w` (1 ≤ w ≤ 1000; multi-edges may occur and count as distinct edges).", "One line: distance count.", "Run Dijkstra and keep cnt[v] at the same time: when a shorter distance is found set cnt to the source's cnt; when it ties, add the source's cnt."),
  "Dijkstra＋計數", "dist 更短 → cnt[v]=cnt[u]；相等 → cnt[v]+=cnt[u]（取模）。",
  "import heapq,sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1]);M=10**9+7;adj=[[] for _ in range(n+1)]\nfor i in range(m):\n    u,v,w=int(d[2+3*i]),int(d[3+3*i]),int(d[4+3*i]);adj[u].append((v,w));adj[v].append((u,w))\nINF=float('inf');dist=[INF]*(n+1);cnt=[0]*(n+1);dist[1]=0;cnt[1]=1;h=[(0,1)]\nwhile h:\n    du,u=heapq.heappop(h)\n    if du>dist[u]: continue\n    for v,w in adj[u]:\n        nd=du+w\n        if nd<dist[v]: dist[v]=nd;cnt[v]=cnt[u];heapq.heappush(h,(nd,v))\n        elif nd==dist[v]: cnt[v]=(cnt[v]+cnt[u])%M\nprint(dist[n],cnt[n]%M) if dist[n]<INF else print(-1,0)",
  ["4 5\n1 2 1\n1 3 1\n2 4 1\n3 4 1\n2 3 1\n", "1 0\n", "3 1\n1 2 5\n", "2 3\n1 2 4\n1 2 4\n1 2 5\n", "3 3\n1 2 1\n2 3 1\n1 3 2\n", "5 8\n1 2 1\n1 3 1\n2 4 1\n3 4 1\n4 5 1\n2 3 1\n1 4 2\n4 5 1\n"])

N("d156", 3, 3, "最小生成樹／瓶頸路", "MST, bottleneck paths",
  ("最小瓶頸路徑", "無向加權圖 n 個點 m 條邊。一條路徑的『瓶頸』是路徑上最重的那條邊的權重。對每個詢問 `a b`，找一條從 a 到 b 的路徑使瓶頸最小，輸出這個最小瓶頸；a = b 時輸出 0，a 與 b 不連通時輸出 -1。",
   "第一行 n m q（1 ≤ n ≤ 1000，0 ≤ m ≤ 5000，1 ≤ q ≤ 1000），接著 m 行 `u v w`（1 ≤ w ≤ 10^6，可能有重邊與自環），再接著 q 行 `a b`。", "每個詢問一行。", "最小瓶頸路徑一定出現在最小生成樹上：先做 Kruskal，之後每個詢問在樹上找 a 到 b 的路徑最大邊。"),
  ("Minimum Bottleneck Path", "An undirected weighted graph has n vertices and m edges. The bottleneck of a path is the weight of its heaviest edge. For each query `a b` find a path from a to b with the smallest bottleneck and print that value; print 0 when a = b and -1 when a and b are not connected.",
   "The first line has n m q (1 ≤ n ≤ 1000, 0 ≤ m ≤ 5000, 1 ≤ q ≤ 1000), then m lines `u v w` (1 ≤ w ≤ 10^6; multi-edges and self-loops may occur), then q lines `a b`.", "One line per query.", "A minimum-bottleneck path always exists inside the minimum spanning tree: run Kruskal, then answer each query by the heaviest edge on the tree path from a to b."),
  "MST 的性質", "Kruskal 建樹；每個詢問從 a 在樹上 DFS/BFS 記錄到各點的路徑最大邊。",
  "import sys\nd=sys.stdin.read().split()\nn,m,q=int(d[0]),int(d[1]),int(d[2])\nE=sorted((int(d[5+3*i]),int(d[3+3*i]),int(d[4+3*i])) for i in range(m))\np=list(range(n+1))\ndef f(x):\n    while p[x]!=x: p[x]=p[p[x]];x=p[x]\n    return x\nadj=[[] for _ in range(n+1)]\nfor w,u,v in E:\n    a,b=f(u),f(v)\n    if a!=b: p[a]=b;adj[u].append((v,w));adj[v].append((u,w))\ni=3+3*m\nfor _ in range(q):\n    a,b=int(d[i]),int(d[i+1]);i+=2\n    best={a:0};st=[a]\n    while st:\n        u=st.pop()\n        for v,w in adj[u]:\n            if v not in best: best[v]=max(best[u],w);st.append(v)\n    print(best.get(b,-1))",
  ["4 4 3\n1 2 5\n2 3 3\n1 3 9\n3 4 1\n1 4\n1 3\n2 2\n", "3 1 2\n1 2 7\n1 3\n2 1\n", "1 0 1\n1 1\n", "3 4 2\n1 2 4\n1 2 2\n2 2 1\n2 3 8\n1 3\n3 1\n"])

N("d157", 3, 2, "最小生成樹／森林", "MST, spanning forest",
  ("最小生成森林", "無向加權圖 n 個點 m 條邊，圖可能不連通。對每個連通塊都選出最小生成樹，合起來叫最小生成森林。輸出森林的總權重以及連通塊的個數。",
   "第一行 n m（1 ≤ n ≤ 10^5，0 ≤ m ≤ 2×10^5），接著 m 行 `u v w`（1 ≤ w ≤ 10^6，可能有重邊與自環）。", "一行：總權重 連通塊數。", "Kruskal 本來就不要求連通：成功合併的邊就是森林的邊，最後的組數就是連通塊數。"),
  ("Minimum Spanning Forest", "An undirected weighted graph has n vertices and m edges and may be disconnected. Taking a minimum spanning tree in every connected component gives a minimum spanning forest. Print the total weight of the forest and the number of connected components.",
   "The first line has n m (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2×10^5), then m lines `u v w` (1 ≤ w ≤ 10^6; multi-edges and self-loops may occur).", "One line: total_weight components.", "Kruskal does not need connectivity: edges that merge are the forest edges, and the number of groups left is the number of components."),
  "Kruskal", "排序後依序合併；組數 = n − 成功合併次數。",
  "import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\nE=sorted((int(d[4+3*i]),int(d[2+3*i]),int(d[3+3*i])) for i in range(m))\np=list(range(n+1))\ndef f(x):\n    while p[x]!=x: p[x]=p[p[x]];x=p[x]\n    return x\nt=0;c=n\nfor w,u,v in E:\n    a,b=f(u),f(v)\n    if a!=b: p[a]=b;t+=w;c-=1\nprint(t,c)",
  ["4 3\n1 2 1\n2 3 2\n1 3 3\n", "1 0\n", "3 0\n", "4 5\n1 2 5\n1 2 1\n3 4 2\n3 3 1\n2 1 9\n", "5 6\n1 2 3\n2 3 1\n3 1 2\n4 5 7\n4 5 6\n5 5 1\n"])

N("d159", 3, 1, "DP 入門／計數", "DP basics, counting",
  ("爬樓梯", "樓梯有 n 階，每次可以爬 1 階、2 階或 3 階，爬到第 n 階有幾種不同的爬法（順序不同算不同）？答案對 1000000007 取餘數。n = 0 時有 1 種（原地不動）。",
   "每行一個整數 n（0 ≤ n ≤ 10^6），最多 100 行，讀到 EOF。", "每行一個整數。", "dp[i] = dp[i−1] + dp[i−2] + dp[i−3]；只要預先算到最大的 n。"),
  ("Climbing Stairs", "A staircase has n steps and each move climbs 1, 2 or 3 steps. How many different ways are there to reach step n (different orders count as different)? Print the answer modulo 1000000007. For n = 0 there is 1 way (stay where you are).",
   "One integer n per line (0 ≤ n ≤ 10^6), at most 100 lines, until EOF.", "One integer per line.", "dp[i] = dp[i−1] + dp[i−2] + dp[i−3]; precompute up to the largest n."),
  "一維 DP", "dp[0]=1；dp[i] = (dp[i-1]+dp[i-2]+dp[i-3]) % M。",
  "import sys\nM=10**9+7\nq=[int(x) for x in sys.stdin.read().split()]\nN=max(q+[3]);dp=[0]*(N+1);dp[0]=1\nfor i in range(1,N+1): dp[i]=(dp[i-1]+(dp[i-2] if i>=2 else 0)+(dp[i-3] if i>=3 else 0))%M\nfor n in q: print(dp[n])",
  ["4\n", "0\n1\n2\n3\n4\n5\n10\n", "1000000\n999999\n"], timeout=20)

N("d160", 3, 2, "一維 DP／選或不選", "1D DP, take or skip",
  ("不能相鄰的最大和", "n 個非負整數排成一列，選出一些數，任兩個被選的數不能相鄰，使總和最大。輸出最大總和（什麼都不選的總和是 0）。",
   "第一行 n（1 ≤ n ≤ 10^5），第二行 n 個整數（0 ≤ aᵢ ≤ 10^4）。", "一個整數。", "dp[i] = max(dp[i−1], dp[i−2] + a[i])：不選第 i 個，或選第 i 個（那前一個就不能選）。"),
  ("Maximum Sum Without Neighbours", "n non-negative integers are in a row. Choose some of them so that no two chosen numbers are adjacent, maximizing the sum. Print the maximum sum (choosing nothing gives 0).",
   "The first line has n (1 ≤ n ≤ 10^5); the second has n integers (0 ≤ aᵢ ≤ 10^4).", "One integer.", "dp[i] = max(dp[i−1], dp[i−2] + a[i]): skip the i-th, or take it (then the previous one cannot be taken)."),
  "選或不選", "只需要保留前兩個狀態。",
  "n=int(input());a=list(map(int,input().split()))\np2=p1=0\nfor x in a: p2,p1=p1,max(p1,p2+x)\nprint(p1)",
  ["4\n1 2 3 1\n", "1\n5\n", "2\n3 7\n", "5\n2 7 9 3 1\n", "3\n0 0 0\n", "6\n10 1 1 10 1 1\n"])

N("d161", 3, 2, "DP／拆分", "DP, splitting",
  ("整數拆分的最大乘積", "把正整數 n 拆成『至少兩個』正整數的和，使這些數的乘積最大，輸出最大乘積（可能是很大的整數）。",
   "每行一個整數 n（2 ≤ n ≤ 1000），最多 20 行，讀到 EOF。", "每行一個整數。", "dp[n] = max over k of k × max(n−k, dp[n−k])；也可以觀察『多拆成 3』的規律，但先把 DP 寫對。"),
  ("Integer Break", "Split a positive integer n into at least two positive integers summing to n so that their product is as large as possible, and print that maximum product (it can be a very large integer).",
   "One integer n per line (2 ≤ n ≤ 1000), at most 20 lines, until EOF.", "One integer per line.", "dp[n] = max over k of k × max(n−k, dp[n−k]); you may also notice the 'use as many 3s as possible' pattern, but first get the DP right."),
  "DP／拆分", "dp[i] = max(k * max(i-k, dp[i-k]) for k in 1..i-1)。",
  "import sys\nN=1000;dp=[0]*(N+1)\nfor i in range(2,N+1): dp[i]=max(k*max(i-k,dp[i-k]) for k in range(1,i))\nfor l in sys.stdin:\n    if l.strip(): print(dp[int(l)])",
  ["10\n", "2\n3\n4\n5\n6\n7\n8\n9\n", "1000\n999\n998\n100\n"], timeout=20)

N("d163", 3, 3, "背包／完全背包", "Knapsack, unbounded",
  ("完全背包", "n 種物品，第 i 種重量 wᵢ、價值 vᵢ，每種都有『無限多個』。背包容量 W，求能裝進背包（總重量不超過 W）的最大總價值。",
   "第一行 n W（1 ≤ n ≤ 100，0 ≤ W ≤ 10^4）；接著 n 行 `w v`（1 ≤ w ≤ 10^4，1 ≤ v ≤ 10^9）。", "一個整數。", "和 0/1 背包的程式只差內層迴圈的方向：完全背包由小到大（同一物品可以重複用）。"),
  ("Unbounded Knapsack", "There are n kinds of items; kind i has weight wᵢ and value vᵢ and you have an unlimited number of each. The knapsack holds weight W. Find the maximum total value that fits (total weight at most W).",
   "The first line has n W (1 ≤ n ≤ 100, 0 ≤ W ≤ 10^4); then n lines `w v` (1 ≤ w ≤ 10^4, 1 ≤ v ≤ 10^9).", "One integer.", "Same code as 0/1 knapsack except for the direction of the inner loop: unbounded goes from small to large (the same item may be used again)."),
  "完全背包", "for 每個物品: for j in range(w, W+1): dp[j] = max(dp[j], dp[j-w]+v)。",
  "n,W=map(int,input().split());dp=[0]*(W+1)\nfor _ in range(n):\n    w,v=map(int,input().split())\n    for j in range(w,W+1):\n        if dp[j-w]+v>dp[j]: dp[j]=dp[j-w]+v\nprint(dp[W])",
  ["2 10\n3 5\n4 7\n", "1 0\n1 5\n", "1 5\n10 100\n", "3 7\n2 3\n3 5\n7 10\n", "2 100\n1 1\n99 200\n"])

N("d164", 3, 3, "背包／恰好裝滿", "Knapsack, exact fill",
  ("恰好裝滿的背包", "n 個物品（每個最多選一次），第 i 個重量 wᵢ、價值 vᵢ。選出一些物品使總重量『恰好等於』W，求最大總價值；如果無法恰好裝滿輸出 -1。",
   "第一行 n W（1 ≤ n ≤ 100，0 ≤ W ≤ 10^4）；接著 n 行 `w v`（1 ≤ w ≤ 10^4，1 ≤ v ≤ 10^9）。", "一個整數。", "和一般背包的差別在初值：dp[0] = 0，其餘設成 −∞（代表『還湊不出這個重量』）。"),
  ("Exact-Fill Knapsack", "There are n items (each usable at most once); item i has weight wᵢ and value vᵢ. Choose items whose total weight is exactly W and maximize the total value; print -1 if W cannot be filled exactly.",
   "The first line has n W (1 ≤ n ≤ 100, 0 ≤ W ≤ 10^4); then n lines `w v` (1 ≤ w ≤ 10^4, 1 ≤ v ≤ 10^9).", "One integer.", "The difference from the ordinary knapsack is the initial values: dp[0] = 0 and every other entry is −∞ (meaning 'this weight cannot be reached yet')."),
  "背包／初值", "NEG = -1；dp[0]=0；轉移時只從有效狀態轉。",
  "n,W=map(int,input().split());NEG=-1;dp=[NEG]*(W+1);dp[0]=0\nfor _ in range(n):\n    w,v=map(int,input().split())\n    for j in range(W,w-1,-1):\n        if dp[j-w]>=0 and dp[j-w]+v>dp[j]: dp[j]=dp[j-w]+v\nprint(dp[W])",
  ["3 5\n2 3\n3 4\n4 10\n", "1 0\n5 5\n", "2 5\n2 3\n2 4\n", "3 6\n1 1\n2 5\n3 10\n", "4 10\n5 1\n5 2\n3 100\n7 50\n"])

N("d166", 3, 3, "序列 DP／計數", "Sequence DP, counting",
  ("最長遞增子序列的個數", "給長度 n 的整數序列。『最長嚴格遞增子序列』可能有很多條（用位置不同就算不同的子序列）。輸出最長長度，以及長度達到最長的子序列有幾條，個數對 1000000007 取餘數。",
   "第一行 n（1 ≤ n ≤ 2000），第二行 n 個整數（絕對值 ≤ 10^9）。", "一行：長度 個數。", "每個位置 i 記錄 (以 i 結尾的最長長度 L[i], 這種長度的方法數 C[i])，轉移時長度更長就取代、長度相同就累加。"),
  ("Number of Longest Increasing Subsequences", "Given a sequence of n integers there may be many longest strictly increasing subsequences (subsequences with different positions are different). Print the longest length and the number of subsequences achieving it, modulo 1000000007.",
   "The first line has n (1 ≤ n ≤ 2000); the second has n integers (absolute value ≤ 10^9).", "One line: length count.", "For every position i keep (the longest length ending at i: L[i], the number of ways: C[i]); a longer candidate replaces, an equal-length candidate adds."),
  "DP／計數", "對 j<i 且 a[j]<a[i]：L[j]+1 > L[i] → 取代；相等 → C[i]+=C[j]。",
  "n=int(input());a=list(map(int,input().split()));M=10**9+7\nL=[1]*n;C=[1]*n\nfor i in range(n):\n    for j in range(i):\n        if a[j]<a[i]:\n            if L[j]+1>L[i]: L[i]=L[j]+1;C[i]=C[j]\n            elif L[j]+1==L[i]: C[i]=(C[i]+C[j])%M\nm=max(L);print(m,sum(C[i] for i in range(n) if L[i]==m)%M)",
  ["5\n1 3 5 4 7\n", "1\n5\n", "5\n2 2 2 2 2\n", "4\n4 3 2 1\n", "6\n1 2 4 3 5 4\n", "3\n1 2 3\n"], timeout=20)

N("d167", 3, 3, "字串 DP／編輯距離", "String DP, edit distance",
  ("編輯距離", "兩個字串 a、b。每次可以對 a 做一個操作：插入一個字元、刪除一個字元、或把一個字元換成另一個字元。最少幾次操作可以把 a 變成 b？",
   "兩行，各是一個只含小寫英文字母的字串（長度 1 到 1000）。", "一個整數。", "dp[i][j] = a 的前 i 個變成 b 的前 j 個的最少操作數；最後一個字元相同就是 dp[i−1][j−1]，否則取三種操作的最小值加 1。"),
  ("Edit Distance", "Given strings a and b, one operation on a is inserting a character, deleting a character, or replacing a character by another. What is the minimum number of operations to turn a into b?",
   "Two lines, each a string of lowercase letters (length 1 to 1000).", "One integer.", "dp[i][j] = fewest operations turning the first i characters of a into the first j of b; equal last characters give dp[i−1][j−1], otherwise take the minimum of the three operations plus 1."),
  "編輯距離", "dp[i][j] = dp[i-1][j-1] if 相同 else 1 + min(刪, 插, 換)。",
  "a=input();b=input();n,m=len(a),len(b)\nprev=list(range(m+1))\nfor i in range(1,n+1):\n    cur=[i]+[0]*m\n    for j in range(1,m+1):\n        cur[j]=prev[j-1] if a[i-1]==b[j-1] else 1+min(prev[j],cur[j-1],prev[j-1])\n    prev=cur\nprint(prev[m])",
  ["horse\nros\n", "a\na\n", "a\nb\n", "abc\nabc\n", "abc\n\n"[:0] + "abc\nxyz\n", "intention\nexecution\n", "kitten\nsitting\n", "abc\nabcdef\n"],
  timeout=20)

N("d168", 3, 3, "區間 DP／回文", "Interval DP, palindromes",
  ("最長回文子序列", "給一個字串，從中刪掉一些字元（剩下的字元保持原本的相對順序）使它變成回文，最多可以留下幾個字元？",
   "一行，只含小寫英文字母（長度 1 到 1000）。", "一個整數。", "dp[i][j] = 區間 s[i..j] 的答案：兩端字元相同就是 dp[i+1][j−1] + 2，否則取 dp[i+1][j] 與 dp[i][j−1] 的較大者。"),
  ("Longest Palindromic Subsequence", "Given a string, delete some characters (the remaining ones keep their relative order) so that the rest is a palindrome. What is the largest number of characters that can remain?",
   "One line of lowercase letters (length 1 to 1000).", "One integer.", "dp[i][j] = answer for the interval s[i..j]: equal end characters give dp[i+1][j−1] + 2, otherwise the larger of dp[i+1][j] and dp[i][j−1]."),
  "區間 DP", "長度由短到長填表；單一字元 dp[i][i] = 1。",
  "s=input();n=len(s);dp=[[0]*n for _ in range(n)]\nfor i in range(n-1,-1,-1):\n    dp[i][i]=1\n    for j in range(i+1,n):\n        dp[i][j]=dp[i+1][j-1]+2 if s[i]==s[j] else max(dp[i+1][j],dp[i][j-1])\nprint(dp[0][n-1])",
  ["bbbab\n", "a\n", "ab\n", "aa\n", "abcba\n", "abcd\n", "character\n", "agbdba\n"], timeout=20)

N("d169", 3, 2, "網格 DP／三角形", "Grid DP, triangle",
  ("數字三角形", "數字排成三角形：第 i 列有 i 個數。從最上面的數出發，每一步走到下一列『正下方』或『右下方』的相鄰數，一路走到最底列，求經過的數字總和最大是多少。",
   "第一行 n（1 ≤ n ≤ 1000，列數）；接著第 i 行有 i 個整數（絕對值 ≤ 10^4）。", "一個整數。", "由下往上做：每個位置的最佳值 = 自己 + 下方兩個位置較大者。"),
  ("Number Triangle", "Numbers form a triangle: row i has i numbers. Starting from the top, each step goes to an adjacent number directly below or below-right in the next row, down to the bottom row. Find the maximum possible sum of the numbers visited.",
   "The first line has n (1 ≤ n ≤ 1000, the number of rows); then row i has i integers (absolute value ≤ 10^4).", "One integer.", "Work bottom-up: the best value at each position is itself plus the larger of the two positions below."),
  "網格 DP", "從倒數第二列往上：a[i][j] += max(a[i+1][j], a[i+1][j+1])。",
  "n=int(input());a=[list(map(int,input().split())) for _ in range(n)]\nfor i in range(n-2,-1,-1):\n    for j in range(i+1): a[i][j]+=max(a[i+1][j],a[i+1][j+1])\nprint(a[0][0])",
  ["5\n7\n3 8\n8 1 0\n2 7 4 4\n4 5 2 6 5\n", "1\n-5\n", "2\n1\n-5 -6\n", "3\n1\n2 3\n-1 -2 -3\n", "4\n0\n0 0\n0 0 0\n0 0 0 9\n"], timeout=20)

N("d170", 3, 1, "網格 DP／計數", "Grid DP, counting paths",
  ("格子路徑數", "R×C 的格子，從左上角出發，每步只能往右或往下，走到右下角有幾種走法？答案對 1000000007 取餘數。",
   "每行兩個整數 R C（1 ≤ R, C ≤ 1000），最多 10 行，讀到 EOF。", "每行一個整數。", "dp[i][j] = dp[i−1][j] + dp[i][j−1]；第一列和第一行都只有 1 種走法。"),
  ("Grid Paths", "In an R×C grid, starting at the top-left corner and moving only right or down, how many ways are there to reach the bottom-right corner? Print the answer modulo 1000000007.",
   "Each line has two integers R C (1 ≤ R, C ≤ 1000), at most 10 lines, until EOF.", "One integer per line.", "dp[i][j] = dp[i−1][j] + dp[i][j−1]; the first row and first column each have exactly 1 way."),
  "網格 DP", "用一維陣列滾動：row[j] += row[j-1]。",
  "import sys\nM=10**9+7\nfor l in sys.stdin:\n    p=l.split()\n    if len(p)<2: continue\n    R,C=int(p[0]),int(p[1]);row=[1]*C\n    for _ in range(R-1):\n        for j in range(1,C): row[j]=(row[j]+row[j-1])%M\n    print(row[C-1])",
  ["3 7\n", "1 1\n1 5\n5 1\n2 2\n3 3\n10 10\n", "1000 1000\n1000 1\n999 1000\n"], timeout=20)

N("d171", 3, 3, "網格 DP／正方形", "Grid DP, squares",
  ("最大的全 1 正方形", "R×C 的 0/1 方陣。找出最大的『全部都是 1』的正方形（邊與格線平行），輸出它的邊長；沒有 1 時輸出 0。",
   "第一行 R C（1 ≤ R, C ≤ 500），接著 R 行，每行 C 個字元（只有 0 和 1，沒有空格）。", "一個整數。", "dp[i][j] = 以 (i,j) 為右下角的最大正方形邊長 = 1 + min(上, 左, 左上)（該格是 1 時）。"),
  ("Largest All-Ones Square", "Given an R×C 0/1 matrix, find the largest square (sides parallel to the grid) consisting only of 1s and print its side length; print 0 if there is no 1.",
   "The first line has R C (1 ≤ R, C ≤ 500), then R lines of C characters (only 0 and 1, no spaces).", "One integer.", "dp[i][j] = side of the largest square with bottom-right corner (i,j) = 1 + min(up, left, up-left) when the cell is 1."),
  "網格 DP", "dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1；取全域最大。",
  "R,C=map(int,input().split());g=[input() for _ in range(R)]\ndp=[[0]*(C+1) for _ in range(R+1)];best=0\nfor i in range(1,R+1):\n    for j in range(1,C+1):\n        if g[i-1][j-1]=='1':\n            dp[i][j]=min(dp[i-1][j],dp[i][j-1],dp[i-1][j-1])+1;best=max(best,dp[i][j])\nprint(best)",
  ["4 5\n10100\n10111\n11111\n10010\n", "1 1\n1\n", "1 1\n0\n", "3 3\n111\n111\n111\n", "3 3\n101\n010\n101\n", "2 5\n11111\n11111\n", "5 2\n11\n11\n11\n11\n11\n"])

N("d172", 3, 3, "區間 DP／合併", "Interval DP, merging",
  ("石子合併", "n 堆石子排成一列，第 i 堆有 aᵢ 顆。每次只能把『相鄰的兩堆』合併成一堆，成本是這兩堆的石子數總和。把全部合併成一堆，最少的總成本是多少？",
   "第一行 n（1 ≤ n ≤ 100），第二行 n 個整數（1 ≤ aᵢ ≤ 1000）。", "一個整數（n = 1 時是 0）。", "dp[i][j] = 合併第 i 到 j 堆的最少成本 = min over k of (dp[i][k] + dp[k+1][j]) + sum(i..j)；注意和『合併成本（d052）』不同，這裡只能合併相鄰的堆。"),
  ("Stone Merging", "n piles of stones are in a row, pile i having aᵢ stones. Each move merges two adjacent piles into one at a cost equal to the total number of stones in the two piles. What is the minimum total cost to merge everything into one pile?",
   "The first line has n (1 ≤ n ≤ 100); the second has n integers (1 ≤ aᵢ ≤ 1000).", "One integer (0 when n = 1).", "dp[i][j] = minimum cost to merge piles i..j = min over k of (dp[i][k] + dp[k+1][j]) + sum(i..j); unlike 'Merge Cost' (d052) only adjacent piles may be merged."),
  "區間 DP", "前綴和求區間和；長度由小到大枚舉分割點。",
  "n=int(input());a=list(map(int,input().split()))\npre=[0]\nfor x in a: pre.append(pre[-1]+x)\nINF=10**18;dp=[[0]*n for _ in range(n)]\nfor L in range(2,n+1):\n    for i in range(n-L+1):\n        j=i+L-1;dp[i][j]=min(dp[i][k]+dp[k+1][j] for k in range(i,j))+pre[j+1]-pre[i]\nprint(dp[0][n-1])",
  ["4\n4 1 1 4\n", "1\n5\n", "2\n3 4\n", "3\n1 2 3\n", "5\n1 1 1 1 1\n", "4\n1000 1 1 1000\n"], timeout=20)

N("d173", 3, 3, "DP／字串切割", "DP, string partition",
  ("最少回文切割", "把字串切成若干段（連續的片段），使每一段本身都是回文。最少要切幾刀？一整個字串本身就是回文時是 0 刀。",
   "一行，只含小寫英文字母（長度 1 到 1000）。", "一個整數。", "先用 O(n²) 預處理『s[i..j] 是否為回文』，再做 dp[j] = 切到前 j 個字元的最少刀數。"),
  ("Minimum Palindrome Cuts", "Cut a string into contiguous pieces so that every piece is a palindrome. What is the minimum number of cuts? A string that is itself a palindrome needs 0 cuts.",
   "One line of lowercase letters (length 1 to 1000).", "One integer.", "First precompute in O(n²) whether s[i..j] is a palindrome, then dp[j] = minimum cuts for the first j characters."),
  "DP／回文表", "is_pal[i][j]；dp[j] = min(dp[i-1] + 1 for i 使 s[i..j] 是回文)。",
  "s=input();n=len(s)\npal=[[False]*n for _ in range(n)]\nfor i in range(n-1,-1,-1):\n    for j in range(i,n):\n        pal[i][j]=s[i]==s[j] and (j-i<2 or pal[i+1][j-1])\ndp=[0]*n\nfor j in range(n):\n    if pal[0][j]: dp[j]=0\n    else: dp[j]=min(dp[i-1]+1 for i in range(1,j+1) if pal[i][j])\nprint(dp[n-1])",
  ["aab\n", "a\n", "ab\n", "aa\n", "abcba\n", "abcd\n", "aabaa\n", "abacabadabacaba\n"], timeout=20)

N("d175", 3, 3, "位元遮罩 DP／指派", "Bitmask DP, assignment",
  ("指派工作", "n 個人要做 n 件工作，每人恰好做一件、每件工作恰好一個人做。第 i 個人做第 j 件工作的成本是 c[i][j]。求最小的總成本。",
   "第一行 n（1 ≤ n ≤ 12），接著 n 行各 n 個整數（0 ≤ c ≤ 1000）。", "一個整數。", "dp[mask] = 前 popcount(mask) 個人已經做完 mask 這些工作的最小成本；下一個人試每一件還沒被選的工作。"),
  ("Assignment Problem", "n people must do n jobs, each person doing exactly one job and each job done by exactly one person. The cost of person i doing job j is c[i][j]. Find the minimum total cost.",
   "The first line has n (1 ≤ n ≤ 12), then n lines of n integers (0 ≤ c ≤ 1000).", "One integer.", "dp[mask] = minimum cost when the first popcount(mask) people have taken exactly the jobs in mask; the next person tries every job not yet taken."),
  "位元遮罩 DP", "dp[0]=0；對每個 mask，i = popcount(mask)，試每個沒用過的 j。",
  "n=int(input());c=[list(map(int,input().split())) for _ in range(n)]\nI=10**18;dp=[I]*(1<<n);dp[0]=0\nfor m in range(1<<n):\n    if dp[m]>=I: continue\n    i=bin(m).count('1')\n    if i>=n: continue\n    for j in range(n):\n        if not m>>j&1:\n            v=dp[m]+c[i][j]\n            if v<dp[m|1<<j]: dp[m|1<<j]=v\nprint(dp[(1<<n)-1])",
  ["3\n9 2 7\n6 4 3\n5 8 1\n", "1\n5\n", "2\n1 2\n3 4\n", "3\n0 0 0\n0 0 0\n0 0 0\n", "4\n1 2 3 4\n2 3 4 1\n3 4 1 2\n4 1 2 3\n",
   (lambda r: lines(12, *[" ".join(str(r.randint(0, 1000)) for _ in range(12)) for _ in range(12)]))(R(175))], timeout=30)

N("d177", 3, 2, "數論／快速冪", "Number theory, fast exponentiation",
  ("快速冪取模", "對每組 a b m，輸出 aᵇ mod m。b 可以非常大（到 10^18），不能一個一個乘。m = 1 時答案是 0。",
   "每行三個整數 a b m（0 ≤ a ≤ 10^9，0 ≤ b ≤ 10^18，1 ≤ m ≤ 10^9），最多 1000 行，讀到 EOF。a = 0 且 b = 0 時，約定 0⁰ = 1（再對 m 取餘數）。", "每行一個整數。", "把 b 用二進位拆開：每次平方 a、遇到 1 的位元就乘進答案，每一步都對 m 取餘數。請自己寫迴圈（不要直接用內建的三參數 pow）練習。"),
  ("Fast Modular Exponentiation", "For each triple a b m print aᵇ mod m. b can be huge (up to 10^18) so you cannot multiply one by one. When m = 1 the answer is 0.",
   "Each line has three integers a b m (0 ≤ a ≤ 10^9, 0 ≤ b ≤ 10^18, 1 ≤ m ≤ 10^9), at most 1000 lines, until EOF. By convention 0⁰ = 1 (then reduced mod m).", "One integer per line.", "Split b in binary: square a at every step and multiply it into the answer on 1 bits, reducing mod m each time. Write the loop yourself (do not use the built-in three-argument pow) for practice."),
  "快速冪", "res=1；while b: if b&1: res=res*a%m；a=a*a%m；b>>=1。最後 res % m。",
  "import sys\nfor l in sys.stdin:\n    p=l.split()\n    if len(p)<3: continue\n    a,b,m=map(int,p);r=1%m;a%=m\n    while b:\n        if b&1: r=r*a%m\n        a=a*a%m;b>>=1\n    print(r)",
  ["2 10 1000\n", "0 0 7\n0 5 7\n5 0 7\n5 0 1\n7 3 1\n2 62 998244353\n", "123456789 987654321987654321 998244353\n10 1000000000000000000 1000000000\n1 1000000000000000000 2\n"])

N("d178", 3, 3, "數論／模逆元", "Number theory, modular inverse",
  ("模逆元", "對每組 a m，找出 x（0 ≤ x < m）使得 a·x ≡ 1 (mod m)。如果不存在（a 與 m 不互質），輸出 -1。",
   "每行兩個整數 a m（1 ≤ a ≤ 10^9，2 ≤ m ≤ 10^9），最多 1000 行，讀到 EOF。m 不一定是質數。", "每行一個整數。", "擴展歐幾里得算法：求出 x、y 使 a·x + m·y = gcd(a, m)；gcd = 1 時 x mod m 就是答案。"),
  ("Modular Inverse", "For each pair a m find x (0 ≤ x < m) with a·x ≡ 1 (mod m), or print -1 if none exists (a and m are not coprime).",
   "Each line has two integers a m (1 ≤ a ≤ 10^9, 2 ≤ m ≤ 10^9), at most 1000 lines, until EOF. m need not be prime.", "One integer per line.", "Use the extended Euclidean algorithm: find x, y with a·x + m·y = gcd(a, m); when gcd = 1, x mod m is the answer."),
  "擴展歐幾里得", "迭代版 egcd，追蹤係數 (x0,x1)。",
  "import sys\ndef inv(a,m):\n    r0,r1,s0,s1=m,a%m,0,1\n    while r1:\n        q=r0//r1;r0,r1=r1,r0-q*r1;s0,s1=s1,s0-q*s1\n    return s0%m if r0==1 else -1\nfor l in sys.stdin:\n    p=l.split()\n    if len(p)>=2: print(inv(int(p[0]),int(p[1])))",
  ["3 11\n", "1 2\n2 4\n6 9\n10 17\n4 7\n", "999999937 1000000000\n123456789 987654321\n1000000000 999999999\n2 3\n"])

N("d179", 3, 3, "數論／篩法", "Number theory, sieve",
  ("大量質因數分解", "有很多個整數 n，對每個輸出質因數分解（質因數由小到大，格式 `p^e`，以空格隔開，指數是 1 也要寫）。",
   "第一行 q（1 ≤ q ≤ 10^5），接著 q 行各一個整數 n（2 ≤ n ≤ 10^6）。", "每個詢問一行。", "對每個數各自試除太慢：先用篩法預處理『最小質因數 spf[n]』，之後每個數只要不斷除以 spf 就好。"),
  ("Many Factorizations", "Given many integers n, print the prime factorization of each (primes ascending, written `p^e` and separated by spaces; write the exponent even when it is 1).",
   "The first line has q (1 ≤ q ≤ 10^5); then q lines each with an integer n (2 ≤ n ≤ 10^6).", "One line per query.", "Trial division per number is too slow: precompute the smallest prime factor spf[n] with a sieve, then each number is factored by repeatedly dividing by its spf."),
  "最小質因數篩", "spf[] 篩一次；while n>1: p=spf[n]，數指數。",
  "import sys\nN=10**6;spf=list(range(N+1))\nfor i in range(2,int(N**.5)+1):\n    if spf[i]==i:\n        for j in range(i*i,N+1,i):\n            if spf[j]==j: spf[j]=i\nd=sys.stdin.read().split();o=[]\nfor x in d[1:1+int(d[0])]:\n    n=int(x);f=[]\n    while n>1:\n        p=spf[n];e=0\n        while n%p==0: n//=p;e+=1\n        f.append(f'{p}^{e}')\n    o.append(' '.join(f))\nprint('\\n'.join(o))",
  ["3\n12\n97\n1000000\n", "1\n2\n", "5\n4\n6\n8\n9\n10\n", "4\n999983\n720720\n524288\n999998\n"], timeout=30)


# ======================= 階段 4 =======================
N("d181", 4, 2, "計算幾何／三角形", "Geometry, triangles",
  ("三角形的面積與種類", "每行六個整數 `x1 y1 x2 y2 x3 y3`，是平面上三個點。輸出 `面積的兩倍 種類`：三點共線（含重合）時種類是 `DEGENERATE`（面積 0）；否則依最大的內角分成 `ACUTE`（三個內角都小於 90 度）、`RIGHT`（有一個直角）、`OBTUSE`（有一個鈍角）。",
   "每行座標絕對值 ≤ 10^6，讀到 EOF，最多 1000 行。", "每行 `整數 單字`。", "全部用整數：面積的兩倍是叉積的絕對值；角度用內積的正負判斷（內積 > 0 銳角、= 0 直角、< 0 鈍角），完全不需要三角函數。"),
  ("Triangle Area and Type", "Each line has six integers `x1 y1 x2 y2 x3 y3`, three points of the plane. Print `twice_area TYPE`: if the points are collinear (including coincident) the type is `DEGENERATE` (area 0); otherwise by the largest interior angle: `ACUTE` (all angles below 90°), `RIGHT` (one right angle), `OBTUSE` (one obtuse angle).",
   "Coordinates have absolute value ≤ 10^6, until EOF, at most 1000 lines.", "One `integer word` per line.", "Use integers only: twice the area is the absolute cross product; decide the angle type by the sign of dot products (> 0 acute, = 0 right, < 0 obtuse) — no trigonometry needed."),
  "叉積與內積", "A2 = |cross|；對每個頂點算兩邊向量的內積，最小的內積決定最大角。",
  "import sys\nfor l in sys.stdin:\n    v=list(map(int,l.split()))\n    if len(v)!=6: continue\n    (ax,ay),(bx,by),(cx,cy)=(v[0],v[1]),(v[2],v[3]),(v[4],v[5])\n    cr=(bx-ax)*(cy-ay)-(by-ay)*(cx-ax)\n    if cr==0: print(0,'DEGENERATE');continue\n    d=[(bx-ax)*(cx-ax)+(by-ay)*(cy-ay),(ax-bx)*(cx-bx)+(ay-by)*(cy-by),(ax-cx)*(bx-cx)+(ay-cy)*(by-cy)]\n    m=min(d)\n    print(abs(cr),'RIGHT' if m==0 else 'OBTUSE' if m<0 else 'ACUTE')",
  ["0 0 4 0 0 3\n", "0 0 1 0 2 0\n0 0 0 0 0 0\n0 0 1 0 0 1\n0 0 4 0 2 1\n0 0 4 0 2 4\n1 1 1 1 5 7\n", "-1000000 -1000000 1000000 -1000000 0 1000000\n0 0 1000000 0 1000000 1000000\n"])

N("d182", 4, 3, "計算幾何／點與多邊形", "Geometry, point in polygon",
  ("點在多邊形內嗎", "給一個簡單多邊形（頂點依順時針或逆時針順序給出，邊不會互相交叉，也不會自己接觸）與 q 個點，對每個點輸出它在多邊形的 `INSIDE`（內部）、`BOUNDARY`（剛好在邊上，包含頂點）或 `OUTSIDE`（外部）。",
   "第一行 n（3 ≤ n ≤ 1000）；接著 n 行 `x y`；再來一行 q（1 ≤ q ≤ 1000）；接著 q 行 `x y`。所有座標是絕對值 ≤ 10^4 的整數。", "每個點一行。", "先檢查是否在某條邊上（叉積為 0 且在線段範圍內）；否則從點往右射一條射線，數它穿過幾條邊（奇數次在內部）。注意射線剛好經過頂點的處理：用『一端在上、一端不在上』的半開區間規則。"),
  ("Point in Polygon", "Given a simple polygon (vertices listed clockwise or counter-clockwise; edges do not cross or touch each other) and q points, print for each point `INSIDE`, `BOUNDARY` (exactly on an edge, vertices included) or `OUTSIDE`.",
   "The first line has n (3 ≤ n ≤ 1000); then n lines `x y`; then a line q (1 ≤ q ≤ 1000); then q lines `x y`. All coordinates are integers with absolute value ≤ 10^4.", "One line per point.", "First check whether the point lies on an edge (cross product 0 and inside the segment's range); otherwise shoot a ray to the right and count crossings (odd means inside). Handle rays through vertices with the half-open rule 'one end above, the other not above'."),
  "射線法", "boundary 優先；(a.y > p.y) != (b.y > p.y) 且交點 x > p.x 才計一次穿越。",
  "import sys\nd=sys.stdin.read().split()\nn=int(d[0]);P=[(int(d[1+2*i]),int(d[2+2*i])) for i in range(n)];q=int(d[1+2*n]);p0=2+2*n\nfor k in range(q):\n    x,y=int(d[p0+2*k]),int(d[p0+2*k+1]);on=False;c=False\n    for i in range(n):\n        (ax,ay),(bx,by)=P[i],P[(i+1)%n]\n        cr=(bx-ax)*(y-ay)-(by-ay)*(x-ax)\n        if cr==0 and min(ax,bx)<=x<=max(ax,bx) and min(ay,by)<=y<=max(ay,by): on=True;break\n        if (ay>y)!=(by>y):\n            t=(bx-ax)*(y-ay)-(x-ax)*(by-ay)\n            if (t>0)==(by>ay): c=not c\n    print('BOUNDARY' if on else 'INSIDE' if c else 'OUTSIDE')",
  ["4\n0 0\n4 0\n4 4\n0 4\n5\n2 2\n0 0\n2 0\n5 2\n-1 -1\n", "3\n0 0\n4 0\n0 4\n4\n1 1\n2 2\n3 3\n-1 0\n", "6\n0 0\n6 0\n6 6\n3 3\n0 6\n0 3\n6\n3 3\n3 2\n3 4\n1 5\n5 5\n0 4\n"])

N("d183", 4, 2, "計算幾何／矩形", "Geometry, rectangles",
  ("兩個矩形的交集面積", "每行八個整數 `x1 y1 x2 y2 x3 y3 x4 y4`：第一個矩形的左下角 (x1,y1) 與右上角 (x2,y2)，第二個矩形的左下角 (x3,y3) 與右上角 (x4,y4)（邊都與座標軸平行，保證 x1<x2、y1<y2、x3<x4、y3<y4）。輸出兩個矩形重疊部分的面積；只有邊或角碰在一起時面積是 0。",
   "座標絕對值 ≤ 10^9，讀到 EOF，最多 1000 行。", "每行一個整數（可能超過 64 位元範圍的一半，Python 不用擔心）。", "水平方向的重疊長度 = max(0, min(x2,x4) − max(x1,x3))；垂直方向同理；兩者相乘。"),
  ("Intersection Area of Two Rectangles", "Each line has eight integers `x1 y1 x2 y2 x3 y3 x4 y4`: the bottom-left (x1,y1) and top-right (x2,y2) corners of the first rectangle and likewise (x3,y3), (x4,y4) for the second (axis-parallel; x1<x2, y1<y2, x3<x4, y3<y4 are guaranteed). Print the area of their overlap; rectangles that only share an edge or a corner overlap in area 0.",
   "Coordinates have absolute value ≤ 10^9, until EOF, at most 1000 lines.", "One integer per line (it may exceed 63 bits halved, but Python does not care).", "Horizontal overlap length = max(0, min(x2,x4) − max(x1,x3)); the vertical one is similar; multiply them."),
  "區間重疊", "兩個方向各算重疊長度（負數取 0）後相乘。",
  "import sys\nfor l in sys.stdin:\n    v=list(map(int,l.split()))\n    if len(v)==8:\n        w=max(0,min(v[2],v[6])-max(v[0],v[4]));h=max(0,min(v[3],v[7])-max(v[1],v[5]))\n        print(w*h)",
  ["0 0 4 4 2 2 6 6\n", "0 0 1 1 1 1 2 2\n0 0 1 1 2 2 3 3\n0 0 4 4 1 1 2 2\n0 0 2 2 0 0 2 2\n0 0 5 1 2 -3 3 4\n", "-1000000000 -1000000000 1000000000 1000000000 -1000000000 -1000000000 1000000000 1000000000\n0 0 10 10 5 -5 15 5\n"])

N("d184", 4, 3, "計算幾何／圓", "Geometry, circles",
  ("兩圓的關係", "每行六個整數 `x1 y1 r1 x2 y2 r2`，是平面上兩個圓（圓心與半徑）。輸出它們的關係：`SAME`（完全重合）、`SEPARATE`（相離，沒有公共點且互相在對方外面）、`EXTERNAL`（外切，恰好一個公共點且互相在對方外面）、`INTERSECT`（相交於兩點）、`INTERNAL`（內切，恰好一個公共點且其中一個在另一個裡面）、`CONTAIN`（內含，沒有公共點且其中一個在另一個裡面）。",
   "座標絕對值 ≤ 10^9，半徑 1 ≤ r ≤ 10^9，讀到 EOF，最多 1000 行。", "每行一個單字。", "用『圓心距離的平方』和 (r1+r2)²、(r1−r2)² 比較，全部是整數運算，不要用 sqrt 與浮點數（座標 10^9 時浮點數會算錯）。"),
  ("Relation of Two Circles", "Each line has six integers `x1 y1 r1 x2 y2 r2`, two circles (centre and radius). Print their relation: `SAME` (identical), `SEPARATE` (no common point, each outside the other), `EXTERNAL` (externally tangent: exactly one common point, each outside the other), `INTERSECT` (two common points), `INTERNAL` (internally tangent: exactly one common point, one inside the other), `CONTAIN` (no common point, one inside the other).",
   "Coordinates have absolute value ≤ 10^9, radii 1 ≤ r ≤ 10^9, until EOF, at most 1000 lines.", "One word per line.", "Compare the squared centre distance with (r1+r2)² and (r1−r2)²: pure integer arithmetic. Do not use sqrt or floats (they fail at 10^9)."),
  "整數幾何", "d2 = dx²+dy²；與 (r1+r2)² 和 (r1-r2)² 比大小；圓心相同另外處理。",
  "import sys\nfor l in sys.stdin:\n    v=list(map(int,l.split()))\n    if len(v)!=6: continue\n    x1,y1,r1,x2,y2,r2=v;d2=(x1-x2)**2+(y1-y2)**2;s=(r1+r2)**2;t=(r1-r2)**2\n    if d2==0 and r1==r2: print('SAME')\n    elif d2>s: print('SEPARATE')\n    elif d2==s: print('EXTERNAL')\n    elif d2>t: print('INTERSECT')\n    elif d2==t: print('INTERNAL')\n    else: print('CONTAIN')",
  ["0 0 3 5 0 3\n", "0 0 1 0 0 1\n0 0 1 3 0 1\n0 0 1 2 0 1\n0 0 2 1 0 1\n0 0 3 1 0 1\n0 0 5 1 0 1\n0 0 5 0 0 2\n", "1000000000 1000000000 1000000000 -1000000000 -1000000000 1000000000\n0 0 1000000000 1000000000 0 1\n0 0 1 1000000000 1000000000 1000000000\n0 0 500000000 1000000000 1 500000000\n0 0 1000000000 999999999 0 1\n"])

N("d186", 4, 3, "樹／直徑", "Trees, diameter",
  ("樹的直徑", "一棵有 n 個點的樹（n−1 條邊，無權重）。樹上任兩點之間的距離是它們之間路徑的邊數。輸出最遠的兩點之間的距離（直徑）。n = 1 時答案是 0。",
   "第一行 n（1 ≤ n ≤ 10^5），接著 n−1 行 `u v`。", "一個整數。", "從任意點 BFS 找到最遠的點 a；再從 a 做一次 BFS，最遠的距離就是直徑。長鏈狀的樹用遞迴 DFS 會爆掉，請用迭代。"),
  ("Tree Diameter", "A tree has n vertices (n−1 unweighted edges). The distance between two vertices is the number of edges on the path between them. Print the distance between the two farthest vertices (the diameter). For n = 1 the answer is 0.",
   "The first line has n (1 ≤ n ≤ 10^5), then n−1 lines `u v`.", "One integer.", "BFS from any vertex to find the farthest vertex a; BFS again from a — the largest distance is the diameter. A long chain breaks recursive DFS, so iterate."),
  "雙 BFS", "第一次 BFS 找最遠點 a，第二次從 a BFS 取最大距離。",
  "import sys\nfrom collections import deque\nd=sys.stdin.read().split()\nn=int(d[0]);adj=[[] for _ in range(n+1)]\nfor i in range(n-1):\n    u,v=int(d[1+2*i]),int(d[2+2*i]);adj[u].append(v);adj[v].append(u)\ndef bfs(s):\n    dist=[-1]*(n+1);dist[s]=0;q=deque([s]);last=s\n    while q:\n        u=q.popleft();last=u\n        for v in adj[u]:\n            if dist[v]<0: dist[v]=dist[u]+1;q.append(v)\n    return last,dist[last]\na,_=bfs(1);print(bfs(a)[1])",
  ["5\n1 2\n2 3\n3 4\n2 5\n", "1\n", "2\n1 2\n", "7\n1 2\n1 3\n2 4\n2 5\n3 6\n3 7\n", "6\n1 2\n1 3\n1 4\n1 5\n1 6\n"], timeout=20)

N("d187", 4, 4, "樹／最近共同祖先", "Trees, LCA",
  ("最近共同祖先", "一棵以 1 號點為根的樹（n 個點、n−1 條邊，邊是無向給出的）。有 q 個詢問 `a b`，輸出 a 和 b 的最近共同祖先（同時是兩者祖先、且深度最大的點；一個點算自己的祖先）。",
   "第一行 n q（1 ≤ n, q ≤ 5×10^4）；接著 n−1 行 `u v`；再接著 q 行 `a b`。", "每個詢問一行。", "倍增法：up[k][v] 是 v 往上 2^k 層的祖先。先把兩點拉到同一深度，再一起往上跳。用 BFS 建立深度與父節點，避免遞迴。"),
  ("Lowest Common Ancestor", "A tree rooted at vertex 1 has n vertices and n−1 edges (given undirected). For each of q queries `a b` print the lowest common ancestor of a and b (the deepest vertex that is an ancestor of both; a vertex counts as its own ancestor).",
   "The first line has n q (1 ≤ n, q ≤ 5×10^4); then n−1 lines `u v`; then q lines `a b`.", "One line per query.", "Binary lifting: up[k][v] is the 2^k-th ancestor of v. Lift the deeper vertex to the same depth, then jump both upwards together. Build depth and parents with BFS to avoid recursion."),
  "倍增 LCA", "up 表 LOG=17；先對齊深度，再從大到小嘗試跳躍。",
  "import sys\nfrom collections import deque\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1]);adj=[[] for _ in range(n+1)]\nfor i in range(n-1):\n    u,v=int(d[2+2*i]),int(d[3+2*i]);adj[u].append(v);adj[v].append(u)\nLOG=17;up=[[0]*(n+1) for _ in range(LOG)];dep=[0]*(n+1);seen=[False]*(n+1);seen[1]=True;up[0][1]=1;Q=deque([1])\nwhile Q:\n    u=Q.popleft()\n    for v in adj[u]:\n        if not seen[v]: seen[v]=True;dep[v]=dep[u]+1;up[0][v]=u;Q.append(v)\nfor k in range(1,LOG):\n    for v in range(1,n+1): up[k][v]=up[k-1][up[k-1][v]]\np=2+2*(n-1)\nfor _ in range(q):\n    a,b=int(d[p]),int(d[p+1]);p+=2\n    if dep[a]<dep[b]: a,b=b,a\n    df=dep[a]-dep[b]\n    for k in range(LOG):\n        if df>>k&1: a=up[k][a]\n    if a==b: print(a);continue\n    for k in range(LOG-1,-1,-1):\n        if up[k][a]!=up[k][b]: a=up[k][a];b=up[k][b]\n    print(up[0][a])",
  ["7 3\n1 2\n1 3\n2 4\n2 5\n3 6\n3 7\n4 5\n4 6\n7 7\n", "1 1\n1 1\n", "5 4\n1 2\n2 3\n3 4\n4 5\n5 1\n1 5\n3 5\n2 4\n", "6 3\n3 1\n1 2\n2 4\n4 5\n4 6\n5 6\n6 3\n2 6\n"], timeout=30)

N("d189", 4, 3, "字串／KMP", "Strings, KMP",
  ("樣式出現次數", "給文字 T 和樣式 P，數 P 在 T 中出現幾次（可以重疊，例如 `aaaa` 中 `aa` 出現 3 次）。",
   "兩行：第一行 T，第二行 P，都只含小寫英文字母，1 ≤ |P| ≤ |T| ≤ 2×10^5。", "一個整數。", "KMP：先算 P 的失敗函數，再讓 T 的每個字元去推進匹配長度；匹配長度到 |P| 就算一次，並退回失敗函數的位置繼續。"),
  ("Pattern Occurrences", "Given a text T and a pattern P, count how many times P occurs in T (occurrences may overlap: `aa` occurs 3 times in `aaaa`).",
   "Two lines: T and then P, both lowercase letters only, 1 ≤ |P| ≤ |T| ≤ 2×10^5.", "One integer.", "KMP: compute P's failure function, then let each character of T advance the match length; when it reaches |P| count one and fall back along the failure function."),
  "KMP", "對 P + '#' + T 算前綴函數，值等於 |P| 的位置數。",
  "T=input();P=input();s=P+'#'+T;n=len(s);pi=[0]*n;k=0;c=0;m=len(P)\nfor i in range(1,n):\n    while k and s[i]!=s[k]: k=pi[k-1]\n    if s[i]==s[k]: k+=1\n    pi[i]=k\n    if k==m: c+=1\nprint(c)",
  ["ababab\nab\n", "a\na\n", "aaaa\naa\n", "abc\nabcd\n"[:0] + "abcabc\nabc\n", "aaaaa\naaaaa\n", "abababab\nabab\n", "abcdef\nxyz\n"], timeout=20)

N("d190", 4, 3, "字串／Z 函數", "Strings, Z function",
  ("前綴相似度總和", "對字串 s 的每個後綴 s[i..]（i 從 0 起，i = 0 是整個 s），計算它和 s 的『最長共同前綴長度』，輸出這些長度的總和。例如 `ababa` 的各後綴共同前綴長度是 5, 0, 3, 0, 1，總和 9。",
   "一行小寫英文字母字串（1 ≤ 長度 ≤ 2×10^5）。", "一個整數。", "Z 函數：z[i] 就是 s[i..] 與 s 的最長共同前綴；利用已知的最右區間 [l, r] 可以在 O(n) 內算完，暴力比對是 O(n²)。"),
  ("Prefix Similarity Sum", "For every suffix s[i..] of a string s (i from 0; i = 0 is s itself) compute its longest common prefix with s, and print the sum of these lengths. For `ababa` the lengths are 5, 0, 3, 0, 1, total 9.",
   "One line of lowercase letters (1 ≤ length ≤ 2×10^5).", "One integer.", "The Z function: z[i] is the longest common prefix of s[i..] and s; using the rightmost known interval [l, r] it is computed in O(n), while brute-force comparison is O(n²)."),
  "Z 函數", "維護 [l, r]；z[i] = min(r-i+1, z[i-l]) 起算再往右擴。",
  "s=input();n=len(s);z=[0]*n;z[0]=n;l=r=0\nfor i in range(1,n):\n    if i<=r: z[i]=min(r-i+1,z[i-l])\n    while i+z[i]<n and s[z[i]]==s[i+z[i]]: z[i]+=1\n    if i+z[i]-1>r: l,r=i,i+z[i]-1\nprint(sum(z))",
  ["ababa\n", "a\n", "aaaaa\n", "abcde\n", "abcabcabc\n", "aabaabaab\n"], timeout=20)

N("d191", 4, 3, "字串／前綴查詢", "Strings, prefix queries",
  ("前綴計數", "給 n 個單字（可能重複，重複的各算一個）與 q 個查詢字串，對每個查詢輸出有幾個單字是以它開頭的（單字本身等於查詢也算）。",
   "第一行 n q（1 ≤ n, q ≤ 5×10^4）；接著 n 行各一個單字、再接著 q 行各一個查詢字串，皆為小寫英文字母；所有單字長度總和與所有查詢長度總和各 ≤ 2×10^5。", "每個查詢一行。", "把單字排序後，以某前綴開頭的單字是連續的一段，用二分搜尋找出這一段的兩端；或建立字典樹（trie）並在每個節點記錄經過的單字數。"),
  ("Prefix Counting", "Given n words (duplicates count separately) and q query strings, print for each query how many words start with it (a word equal to the query counts too).",
   "The first line has n q (1 ≤ n, q ≤ 5×10^4); then n lines with one word each and q lines with one query string each, all lowercase letters; the total length of all words and the total length of all queries are each ≤ 2×10^5.", "One line per query.", "After sorting the words, those starting with a given prefix form one contiguous block; binary-search its two ends. Or build a trie and store at every node how many words pass through it."),
  "排序＋二分／字典樹", "words 排序；左端 bisect_left(prefix)；右端 bisect_left(prefix + '{')（'{' 在 'z' 後面）。",
  "import sys,bisect\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1]);W=sorted(d[2:2+n])\nfor x in d[2+n:2+n+q]: print(bisect.bisect_left(W,x+'{')-bisect.bisect_left(W,x))",
  ["4 3\napple\napp\napply\nbanana\napp\nb\nc\n", "5 3\naz\nazz\nb\nza\nzz\na\naz\nz\n", "1 1\na\na\n", "3 2\nab\nab\nabc\na\nabc\n", "2 2\nz\nzz\nzz\nzzz\n"], timeout=20)

N("d193", 4, 2, "博弈／Nim", "Games, Nim",
  ("Nim 遊戲", "有 t 局遊戲。每局有 n 堆石頭，兩人輪流取，每次選一堆取走至少 1 顆（可以取光），最後一個取走石頭的人獲勝。兩人都用最佳策略，先手必勝輸出 `FIRST`，否則輸出 `SECOND`。",
   "第一行 t（1 ≤ t ≤ 1000）；每局兩行：n（1 ≤ n ≤ 1000）與 n 個非負整數（≤ 10^9）。", "每局一行。", "所有堆大小的 XOR 不為 0 時先手必勝（Bouton 定理）；為 0 時後手必勝。可以自己用小範例窮舉驗證這個結論。"),
  ("Nim Game", "There are t games. In each game there are n piles of stones; two players alternately take at least 1 stone from a single pile (possibly the whole pile) and whoever takes the last stone wins. Both play optimally; print `FIRST` if the first player wins, otherwise `SECOND`.",
   "The first line has t (1 ≤ t ≤ 1000); each game has two lines: n (1 ≤ n ≤ 1000) and n non-negative integers (≤ 10^9).", "One line per game.", "The first player wins exactly when the XOR of all pile sizes is non-zero (Bouton's theorem). Verify it by brute force on small examples yourself."),
  "XOR／博弈", "x = 全部 XOR；x != 0 → FIRST。",
  "import sys\nd=sys.stdin.read().split();t=int(d[0]);p=1\nfor _ in range(t):\n    n=int(d[p]);p+=1;x=0\n    for v in d[p:p+n]: x^=int(v)\n    p+=n;print('FIRST' if x else 'SECOND')",
  ["3\n3\n1 2 3\n2\n3 4\n1\n5\n", "2\n1\n0\n3\n0 0 0\n", "4\n2\n1 1\n3\n1 2 4\n4\n7 7 7 7\n2\n1000000000 1000000000\n"])

N("d194", 4, 4, "樹 DP／最大路徑和", "Tree DP, maximum path sum",
  ("樹上最大點權路徑", "一棵 n 個點的樹，每個點有權重（可能是負數）。找一條路徑（至少包含一個點，兩端可以是任何點，路徑上的點不重複），使路徑上點的權重總和最大，輸出這個最大總和。",
   "第一行 n（1 ≤ n ≤ 10^5）；第二行 n 個整數（絕對值 ≤ 10^9）；接著 n−1 行 `u v`。", "一個整數。", "樹 DP：down[u] = w[u] + max(0, 最大的 down[child])；經過 u 的最佳路徑 = w[u] + 最大兩個 max(0, down[child]) 的和。用迭代順序處理（避免遞迴過深）。"),
  ("Maximum Weight Path in a Tree", "A tree has n vertices, each with a weight (possibly negative). Find a path (at least one vertex, any two endpoints, no repeated vertices) maximizing the sum of the vertex weights on it, and print that sum.",
   "The first line has n (1 ≤ n ≤ 10^5); the second has n integers (absolute value ≤ 10^9); then n−1 lines `u v`.", "One integer.", "Tree DP: down[u] = w[u] + max(0, best down[child]); the best path through u = w[u] plus the two largest max(0, down[child]). Process vertices in an iterative order to avoid deep recursion."),
  "樹 DP", "BFS 序反向處理；維護每個點最大與第二大的正向貢獻。",
  "import sys\nd=sys.stdin.read().split()\nn=int(d[0]);w=[0]+[int(x) for x in d[1:1+n]];adj=[[] for _ in range(n+1)]\nfor i in range(n-1):\n    u,v=int(d[1+n+2*i]),int(d[2+n+2*i]);adj[u].append(v);adj[v].append(u)\npar=[0]*(n+1);order=[];st=[1];par[1]=-1\nwhile st:\n    u=st.pop();order.append(u)\n    for v in adj[u]:\n        if v!=par[u]: par[v]=u;st.append(v)\nm1=[0]*(n+1);m2=[0]*(n+1);down=[0]*(n+1);best=-10**30\nfor u in reversed(order):\n    down[u]=w[u]+m1[u];best=max(best,w[u]+m1[u]+m2[u])\n    p=par[u]\n    if p>0:\n        c=max(0,down[u])\n        if c>m1[p]: m2[p]=m1[p];m1[p]=c\n        elif c>m2[p]: m2[p]=c\nprint(best)",
  ["5\n1 2 3 4 5\n1 2\n2 3\n2 4\n4 5\n", "1\n-7\n", "3\n-1 -2 -3\n1 2\n2 3\n", "4\n5 -10 5 5\n1 2\n2 3\n2 4\n", "3\n5 -10 5\n1 2\n1 3\n", "6\n2 -5 9 7 -7 8\n5 1\n1 4\n5 6\n6 3\n1 2\n", "6\n1 -1 1 -1 1 -1\n1 2\n2 3\n3 4\n4 5\n5 6\n"], timeout=20)

N("d195", 4, 3, "資料結構／樹狀陣列", "Data structures, Fenwick tree",
  ("動態區間和", "長度 n 的整數陣列，之後有 q 個操作：`1 i v` 把第 i 個數加上 v；`2 l r` 輸出第 l 到第 r 個數的總和（都是 1 起算，含兩端）。",
   "第一行 n q（1 ≤ n, q ≤ 5×10^4）；第二行 n 個整數（絕對值 ≤ 10^9）；接著 q 行操作（|v| ≤ 10^9）。", "每個 `2` 操作輸出一行。", "前綴和不能處理『修改』：每次修改都重算是 O(n)。樹狀陣列（Fenwick tree / BIT）讓修改與查詢都是 O(log n)。"),
  ("Dynamic Range Sums", "An array of n integers is followed by q operations: `1 i v` adds v to the i-th number; `2 l r` prints the sum of the l-th through r-th numbers (1-based, inclusive).",
   "The first line has n q (1 ≤ n, q ≤ 5×10^4); the second has n integers (absolute value ≤ 10^9); then q operation lines (|v| ≤ 10^9).", "One line for every `2` operation.", "Prefix sums cannot handle updates: recomputing after every update is O(n). A Fenwick tree (BIT) gives O(log n) for both updates and queries."),
  "Fenwick tree", "update: i += i & -i；query: i -= i & -i。區間和 = query(r) − query(l−1)。",
  "import sys\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1]);T=[0]*(n+1)\ndef add(i,v):\n    while i<=n: T[i]+=v;i+=i&-i\ndef qs(i):\n    s=0\n    while i>0: s+=T[i];i-=i&-i\n    return s\nfor i in range(1,n+1): add(i,int(d[1+i]))\np=2+n\nfor _ in range(q):\n    t=int(d[p])\n    if t==1: add(int(d[p+1]),int(d[p+2]))\n    else: print(qs(int(d[p+2]))-qs(int(d[p+1])-1))\n    p+=3",
  ["5 4\n1 2 3 4 5\n2 1 5\n1 3 10\n2 1 3\n2 3 3\n", "1 2\n5\n2 1 1\n1 1 -5\n", "3 5\n0 0 0\n1 1 1\n1 2 2\n1 3 3\n2 1 3\n2 2 3\n"], timeout=20)

N("d196", 4, 4, "資料結構／線段樹", "Data structures, segment tree",
  ("單點修改區間最小值", "長度 n 的整數陣列，之後有 q 個操作：`1 i v` 把第 i 個數改成 v；`2 l r` 輸出第 l 到第 r 個數中的最小值（1 起算，含兩端）。",
   "第一行 n q（1 ≤ n, q ≤ 5×10^4）；第二行 n 個整數（絕對值 ≤ 10^9）；接著 q 行操作（|v| ≤ 10^9）。", "每個 `2` 操作輸出一行。", "稀疏表（d087）處理不了修改；線段樹把區間最小值存在二元樹的節點上，修改與查詢都是 O(log n)。非遞迴（bottom-up）寫法最短。"),
  ("Point Update, Range Minimum", "An array of n integers is followed by q operations: `1 i v` sets the i-th number to v; `2 l r` prints the minimum of the l-th through r-th numbers (1-based, inclusive).",
   "The first line has n q (1 ≤ n, q ≤ 5×10^4); the second has n integers (absolute value ≤ 10^9); then q operation lines (|v| ≤ 10^9).", "One line for every `2` operation.", "A sparse table (d087) cannot handle updates; a segment tree stores range minima in the nodes of a binary tree, giving O(log n) updates and queries. The bottom-up (non-recursive) version is the shortest."),
  "線段樹", "大小 N 的陣列 t[N:2N] 放葉子；修改後往上更新 t[i>>1]；查詢用左右邊界收縮。",
  "import sys\nd=sys.stdin.read().split()\nn,q=int(d[0]),int(d[1]);INF=10**30;N=1\nwhile N<n: N*=2\nt=[INF]*(2*N)\nfor i in range(n): t[N+i]=int(d[2+i])\nfor i in range(N-1,0,-1): t[i]=min(t[2*i],t[2*i+1])\np=2+n\nfor _ in range(q):\n    o=int(d[p]);a=int(d[p+1]);b=int(d[p+2]);p+=3\n    if o==1:\n        i=N+a-1;t[i]=b\n        while i>1: i>>=1;t[i]=min(t[2*i],t[2*i+1])\n    else:\n        l=N+a-1;r=N+b;m=INF\n        while l<r:\n            if l&1: m=min(m,t[l]);l+=1\n            if r&1: r-=1;m=min(m,t[r])\n            l>>=1;r>>=1\n        print(m)",
  ["5 4\n5 3 8 1 9\n2 1 5\n1 4 10\n2 1 5\n2 3 3\n", "1 2\n7\n2 1 1\n1 1 -7\n", "4 5\n4 3 2 1\n2 1 2\n2 3 4\n1 1 -1\n2 1 4\n2 2 3\n"], timeout=20)



# ======================= 補強：題數偏少的單元 =======================
N("d127", 2, 2, "heap／掃描線", "Heap, sweep line",
  ("會議室數量", "有 n 場會議，第 i 場從時間 sᵢ 開始、到 eᵢ 結束（sᵢ < eᵢ）。一間會議室同一時間只能開一場會；一場會結束的那一刻會議室就空出來，所以 eᵢ 等於另一場的 sⱼ 時可以共用。最少需要幾間會議室？",
   "第一行 n（1 ≤ n ≤ 10^5）；接著 n 行 `s e`（0 ≤ s < e ≤ 10^9）。", "一個整數。", "按開始時間排序；用最小堆放『正在使用的會議室的結束時間』：新會議開始時，堆頂結束時間 ≤ 開始時間就重用（pop），最後堆的大小就是答案。"),
  ("Meeting Rooms", "There are n meetings; meeting i starts at sᵢ and ends at eᵢ (sᵢ < eᵢ). A room can host one meeting at a time, and it becomes free the moment a meeting ends, so a meeting ending at eᵢ may share a room with one starting at sⱼ = eᵢ. What is the minimum number of rooms?",
   "The first line has n (1 ≤ n ≤ 10^5); then n lines `s e` (0 ≤ s < e ≤ 10^9).", "One integer.", "Sort by start time; keep a min-heap of the end times of rooms in use: when a meeting starts and the heap top is ≤ its start time, reuse that room (pop). The final heap size is the answer."),
  "最小堆", "排序後依序處理；heap 放各會議室的結束時間。",
  "import heapq,sys\nd=sys.stdin.read().split()\nn=int(d[0]);iv=sorted((int(d[1+2*i]),int(d[2+2*i])) for i in range(n));h=[]\nfor s,e in iv:\n    if h and h[0]<=s: heapq.heapreplace(h,e)\n    else: heapq.heappush(h,e)\nprint(len(h))",
  ["3\n0 30\n5 10\n15 20\n", "1\n0 1\n", "2\n0 5\n5 10\n", "3\n0 5\n0 5\n0 5\n", "4\n1 10\n2 3\n3 4\n4 5\n", "5\n0 100\n10 20\n20 30\n30 40\n15 35\n"], timeout=20)

N("d151", 3, 2, "並查集／維護群組大小", "Union-find, group sizes",
  ("最大的朋友圈", "一開始有 n 個人，每個人自己一個群組。依序發生 m 次『a 和 b 變成朋友』（他們所在的兩個群組合併成一個；已經在同一群組就什麼都不變）。每次操作之後，輸出目前最大的群組有幾個人。",
   "第一行 n m（1 ≤ n ≤ 10^5，1 ≤ m ≤ 10^5）；接著 m 行 `a b`（1 ≤ a, b ≤ n，可能 a = b）。", "m 行，每次操作後各一個整數。", "並查集同時維護每個根的群組大小與全域最大值；合併時只可能讓最大值變大，不需要重算。"),
  ("Largest Friend Circle", "At first there are n people, each in a group of their own. Then m events happen in order: 'a and b become friends' (their two groups merge into one; if they are already in the same group nothing changes). After every event print the size of the largest group so far.",
   "The first line has n m (1 ≤ n ≤ 10^5, 1 ≤ m ≤ 10^5); then m lines `a b` (1 ≤ a, b ≤ n, a = b possible).", "m lines, one integer after each event.", "Union-find with the size of every root and a global maximum; a merge can only increase the maximum, so nothing needs to be recomputed."),
  "並查集", "union by size；best = max(best, 新群組大小)。",
  "import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1]);p=list(range(n+1));sz=[1]*(n+1);best=1\ndef f(x):\n    while p[x]!=x: p[x]=p[p[x]];x=p[x]\n    return x\nfor i in range(m):\n    a,b=f(int(d[2+2*i])),f(int(d[3+2*i]))\n    if a!=b:\n        if sz[a]<sz[b]: a,b=b,a\n        p[b]=a;sz[a]+=sz[b];best=max(best,sz[a])\n    print(best)",
  ["5 4\n1 2\n3 4\n2 3\n5 5\n", "1 1\n1 1\n", "3 3\n1 2\n1 2\n2 1\n", "4 3\n1 2\n3 4\n1 4\n", "6 5\n1 2\n2 3\n4 5\n5 6\n3 6\n"], timeout=20)

N("d153", 3, 2, "拓撲排序／唯一性", "Topological sort, uniqueness",
  ("拓撲順序唯一嗎", "有向圖 n 個點 m 條邊 `u v`（u 必須排在 v 前面，可能有重複的邊）。如果圖有環輸出 `CYCLE`（自環也算）；否則如果合法的排列順序恰好只有一種輸出 `UNIQUE`，有兩種以上輸出 `MULTIPLE`。",
   "第一行 n m（1 ≤ n ≤ 10^5，0 ≤ m ≤ 2×10^5），接著 m 行 `u v`。", "`CYCLE`、`UNIQUE` 或 `MULTIPLE`。", "Kahn 演算法每一步如果同時有兩個以上入度為 0 的點可以選，順序就不唯一；但要先確認整張圖沒有環。"),
  ("Is the Topological Order Unique?", "A directed graph has n vertices and m edges `u v` (u must come before v; repeated edges may occur). Print `CYCLE` if the graph has a cycle (a self-loop counts); otherwise print `UNIQUE` if there is exactly one valid order and `MULTIPLE` if there are two or more.",
   "The first line has n m (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2×10^5), then m lines `u v`.", "`CYCLE`, `UNIQUE` or `MULTIPLE`.", "In Kahn's algorithm, if at some step two or more vertices have in-degree 0 the order is not unique — but first make sure the whole graph is acyclic."),
  "Kahn", "每輪 queue 大小 > 1 就記 multiple；處理完數量 < n 就是 CYCLE（優先）。",
  "import sys\nfrom collections import deque\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1]);adj=[[] for _ in range(n+1)];ind=[0]*(n+1)\nfor i in range(m):\n    u,v=int(d[2+2*i]),int(d[3+2*i]);adj[u].append(v);ind[v]+=1\nq=deque(i for i in range(1,n+1) if ind[i]==0);multi=False;done=0\nwhile q:\n    if len(q)>1: multi=True\n    u=q.popleft();done+=1\n    for v in adj[u]:\n        ind[v]-=1\n        if ind[v]==0: q.append(v)\nprint('CYCLE' if done<n else 'MULTIPLE' if multi else 'UNIQUE')",
  ["4 3\n1 2\n2 3\n3 4\n", "3 2\n1 2\n1 3\n", "2 2\n1 2\n2 1\n", "1 0\n", "1 1\n1 1\n", "3 3\n1 2\n1 2\n2 3\n", "5 4\n1 2\n2 3\n4 3\n4 5\n"], timeout=20)

N("d158", 3, 3, "最小生成樹／唯一性", "MST, uniqueness",
  ("最小生成樹唯一嗎", "連通的無向加權圖 n 個點 m 條邊（可能有重邊與自環）。輸出最小生成樹的總權重，以及最小生成樹是否唯一：只有一棵輸出 `UNIQUE`，有多棵權重相同的最小生成樹輸出 `MULTIPLE`。",
   "第一行 n m（1 ≤ n ≤ 10^4，n − 1 ≤ m ≤ 5×10^4，保證連通）；接著 m 行 `u v w`（1 ≤ w ≤ 10^6）。", "一行：總權重 UNIQUE 或 MULTIPLE。", "Kruskal 時把『權重相同的一批邊』一起處理：這批裡在批次開始時能連接不同群組的邊數，如果比實際成功合併的邊數多，就代表有替代的選擇。"),
  ("Is the MST Unique?", "A connected undirected weighted graph has n vertices and m edges (multi-edges and self-loops may occur). Print the total weight of a minimum spanning tree and whether it is unique: `UNIQUE` if there is only one MST, `MULTIPLE` if several MSTs share the minimum weight.",
   "The first line has n m (1 ≤ n ≤ 10^4, n − 1 ≤ m ≤ 5×10^4, connected is guaranteed); then m lines `u v w` (1 ≤ w ≤ 10^6).", "One line: total_weight UNIQUE or MULTIPLE.", "In Kruskal, process each batch of equal-weight edges together: if more edges in the batch could join different groups (at the start of the batch) than were actually merged, there was an alternative choice."),
  "Kruskal 批次", "同權重一批：先數能連不同群組的邊數 cand，再實際合併數 used；cand > used → MULTIPLE。",
  "import sys\nd=sys.stdin.read().split()\nn,m=int(d[0]),int(d[1])\nE=sorted((int(d[4+3*i]),int(d[2+3*i]),int(d[3+3*i])) for i in range(m))\np=list(range(n+1))\ndef f(x):\n    while p[x]!=x: p[x]=p[p[x]];x=p[x]\n    return x\nt=0;uniq=True;i=0\nwhile i<m:\n    j=i\n    while j<m and E[j][0]==E[i][0]: j+=1\n    cand=sum(1 for k in range(i,j) if f(E[k][1])!=f(E[k][2]));used=0\n    for k in range(i,j):\n        w,u,v=E[k];a,b=f(u),f(v)\n        if a!=b: p[a]=b;t+=w;used+=1\n    if cand!=used: uniq=False\n    i=j\nprint(t,'UNIQUE' if uniq else 'MULTIPLE')",
  ["4 5\n1 2 1\n2 3 2\n3 4 3\n1 4 4\n1 3 5\n", "3 3\n1 2 1\n2 3 1\n1 3 1\n", "1 0\n", "2 2\n1 2 5\n1 2 5\n", "4 4\n1 2 1\n2 3 1\n3 4 1\n1 4 2\n", "3 3\n1 2 1\n2 3 2\n1 3 2\n", "2 3\n1 2 3\n1 1 1\n2 2 1\n"], timeout=20)

N("d174", 3, 3, "區間 DP／切割", "Interval DP, cutting",
  ("切木棒", "一根長度 L 的木棒，要在 k 個指定的位置各切一刀（位置是離左端的距離，彼此不同，都在 0 和 L 之間）。每切一刀的成本是『被切的那一段目前的長度』，切的順序可以自己決定。求最小的總成本。有 t 組測資。",
   "第一行 t（1 ≤ t ≤ 20）；每組兩行：`L k`（1 ≤ k ≤ 100，k < L ≤ 10^6），以及 k 個遞增的位置。", "每組一行。", "把兩端 0 和 L 也當成切點，dp[i][j] = 切掉 i 到 j 之間所有切點的最小成本 = min over m of (dp[i][m] + dp[m][j]) + (位置[j] − 位置[i])。"),
  ("Cutting Sticks", "A stick of length L must be cut at k given positions (distances from the left end, pairwise different, strictly between 0 and L). Each cut costs the current length of the piece being cut, and you choose the order of the cuts. Find the minimum total cost. There are t test cases.",
   "The first line has t (1 ≤ t ≤ 20); each case has two lines: `L k` (1 ≤ k ≤ 100, k < L ≤ 10^6) and k increasing positions.", "One line per case.", "Treat the two ends 0 and L as cut points as well; dp[i][j] = minimum cost to cut everything between points i and j = min over m of (dp[i][m] + dp[m][j]) + (pos[j] − pos[i])."),
  "區間 DP", "pos = [0] + cuts + [L]；依區間長度由小到大填表。",
  "import sys\nd=sys.stdin.read().split();t=int(d[0]);p=1\nfor _ in range(t):\n    L,k=int(d[p]),int(d[p+1]);p+=2;pos=[0]+[int(x) for x in d[p:p+k]]+[L];p+=k\n    n=len(pos);dp=[[0]*n for _ in range(n)]\n    for ln in range(2,n):\n        for i in range(n-ln):\n            j=i+ln;dp[i][j]=min(dp[i][m]+dp[m][j] for m in range(i+1,j))+pos[j]-pos[i]\n    print(dp[0][n-1])",
  ["2\n10 3\n2 4 7\n100 3\n25 50 75\n", "1\n5 1\n3\n", "2\n2 1\n1\n10 4\n1 2 3 4\n", "1\n1000000 5\n1 2 3 999998 999999\n"], timeout=20)

N("d176", 3, 3, "位元遮罩 DP／路徑計數", "Bitmask DP, counting paths",
  ("漢米爾頓路徑數", "有向圖 n 個點（n ≤ 15）、m 條邊（沒有重複的邊，也沒有自環）。數有幾條『從點 1 出發、每個點恰好經過一次』的路徑（終點可以是任何點；n = 1 時只有一條）。答案對 1000000007 取餘數。",
   "第一行 n m（1 ≤ n ≤ 15，0 ≤ m ≤ n(n−1)）；接著 m 行 `u v`。", "一個整數。", "dp[mask][v] = 走過 mask 這些點、目前在 v 的路徑數；轉移是再走一條邊到沒走過的點。狀態 2^n × n，轉移 n，n = 15 時約 7×10^6。"),
  ("Hamiltonian Paths", "A directed graph has n vertices (n ≤ 15) and m edges (no repeated edges, no self-loops). Count the paths that start at vertex 1 and visit every vertex exactly once (the endpoint may be any vertex; for n = 1 there is exactly one). Print the count modulo 1000000007.",
   "The first line has n m (1 ≤ n ≤ 15, 0 ≤ m ≤ n(n−1)); then m lines `u v`.", "One integer.", "dp[mask][v] = number of paths that have visited exactly the set mask and are now at v; extend by one edge to an unvisited vertex. 2^n × n states with n transitions each: about 7×10^6 for n = 15."),
  "位元遮罩 DP", "dp[1][0]=1；對每個 mask、v、w（w 不在 mask 且有邊 v→w）累加。",
  "n,m=map(int,input().split());M=10**9+7;adj=[0]*n\nfor _ in range(m):\n    u,v=map(int,input().split());adj[u-1]|=1<<(v-1)\ndp=[[0]*n for _ in range(1<<n)];dp[1][0]=1\nfor mask in range(1<<n):\n    if not mask&1: continue\n    row=dp[mask]\n    for v in range(n):\n        c=row[v]\n        if not c: continue\n        nxt=adj[v]&~mask\n        while nxt:\n            low=nxt&-nxt;w=low.bit_length()-1;dp[mask|low][w]=(dp[mask|low][w]+c)%M;nxt^=low\nprint(sum(dp[(1<<n)-1])%M)",
  ["4 5\n1 2\n2 3\n3 4\n1 3\n2 4\n", "1 0\n", "2 1\n1 2\n", "3 2\n1 2\n3 1\n", "4 12\n"+"".join(f"{u} {v}\n" for u in range(1,5) for v in range(1,5) if u!=v), "15 210\n"+"".join(f"{u} {v}\n" for u in range(1,16) for v in range(1,16) if u!=v)], timeout=60)

# 每題的知識點（知識追蹤用）。不靠關鍵字猜：關鍵字比對會把『list』誤判成 LIS 之類。
CONCEPTS = {
    "d096": ["arith"], "d097": ["arith"], "d098": ["cond"], "d099": ["cond"], "d100": ["loop"], "d101": ["loop", "cond"],
    "d102": ["string"], "d103": ["list", "dict_set"], "d104": ["dict_set"], "d105": ["dict_set"], "d106": ["numtheory"],
    "d107": ["loop", "arith"], "d108": ["list"], "d109": ["list"], "d110": ["list"],
    "d111": ["io", "cond"], "d112": ["string", "dict_set"], "d113": ["bignum"], "d114": ["bignum"], "d115": ["string"],
    "d116": ["numtheory"], "d117": ["numtheory"], "d118": ["numtheory"], "d119": ["loop"], "d120": ["list"], "d121": ["list"],
    "d122": ["datetime"], "d123": ["datetime"], "d124": ["stack_q"],
    "d125": ["sorting"], "d126": ["sorting"], "d128": ["prefix_bs"], "d129": ["prefix_bs"], "d130": ["prefix_bs"],
    "d131": ["two_ptr"], "d132": ["two_ptr", "dict_set"], "d133": ["stack_q"], "d135": ["stack_q"], "d136": ["heap"], "d137": ["heap"],
    "d127": ["heap"], "d151": ["dsu"], "d153": ["graph"], "d158": ["shortest", "dsu"], "d174": ["dp"], "d176": ["dp", "bitmask"],
    "d138": ["greedy"], "d139": ["greedy", "two_ptr"], "d140": ["greedy", "sorting"], "d141": ["recursion"], "d142": ["recursion"],
    "d143": ["recursion"], "d144": ["bitmask"], "d145": ["bitmask"],
    "d146": ["graph"], "d147": ["graph"], "d148": ["graph"], "d149": ["dsu", "graph"], "d150": ["dsu"], "d152": ["graph"],
    "d154": ["shortest"], "d156": ["shortest"], "d157": ["shortest", "dsu"],
    "d159": ["dp"], "d160": ["dp"], "d161": ["dp"], "d163": ["dp"], "d164": ["dp"], "d166": ["dp"], "d167": ["dp"], "d168": ["dp"],
    "d169": ["dp"], "d170": ["dp"], "d171": ["dp"], "d172": ["dp"], "d173": ["dp"], "d175": ["dp", "bitmask"],
    "d177": ["numtheory"], "d178": ["numtheory"], "d179": ["numtheory"],
    "d181": ["geometry"], "d182": ["geometry"], "d183": ["geometry"], "d184": ["geometry"],
    "d186": ["tree"], "d187": ["tree"], "d189": ["str_adv"], "d190": ["str_adv"], "d191": ["str_adv"],
    "d193": ["tree"], "d194": ["tree", "dp"], "d195": ["tree"], "d196": ["tree"],
}
assert set(CONCEPTS) == set(EN), set(CONCEPTS) ^ set(EN)
