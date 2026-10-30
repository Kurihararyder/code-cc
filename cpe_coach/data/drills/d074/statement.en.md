# d074 Travelling Salesman (Small)

**Stage 3 · Difficulty ★★★★ · Topic: Bitmask DP**

There are n cities (n ≤ 12) with a distance matrix d[i][j] (possibly asymmetric). Start from city 0, visit every city exactly once and return to city 0. Find the minimum total distance. For n=1 the answer is 0.

## Input
The first line contains n; then n lines with n integers each (0 ≤ d ≤ 1000).

## Output
One integer.

## Sample Input
```
3
0 10 15
10 0 20
15 20 0
```

## Sample Output
```
45
```

## Notes
n ≤ 12–20 usually hints at a bitmask. n=12 needs about 10^7 operations in Python, so watch the constant factor.
