# d126 Multi-key Ranking

**Stage 2 · Difficulty ★★ · Topic: Custom sort, mixed directions**

n contestants, each line `name age score`. Order them by higher score first; on equal scores younger age first; on equal ages by name in dictionary (ASCII) order. Print `name age score` in that order.

## Input
The first line has n (1 ≤ n ≤ 10^5), then n lines: name is letters without spaces (length ≤ 10), age 1–120, score 0–1000.

## Output
n lines.

## Sample Input
```
4
amy 20 90
bob 19 90
cat 20 95
dan 19 90
```

## Sample Output
```
cat 20 95
bob 19 90
dan 19 90
amy 20 90
```

## Notes
Use a tuple as the key: negate the fields that should be descending and keep the others ascending.
