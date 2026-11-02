# d108 Diagonal Sums

**Stage 0 · Difficulty ★ · Topic: 2D lists**

Given an n×n integer matrix, print the sum of the main diagonal (top-left to bottom-right) and the sum of the anti-diagonal (top-right to bottom-left). For odd n the centre cell belongs to both diagonals.

## Input
The first line has n (1 ≤ n ≤ 100), then n lines of n integers (absolute value ≤ 10^4).

## Output
One line: main_sum anti_sum.

## Sample Input
```
3
1 2 3
4 5 6
7 8 9
```

## Sample Output
```
15 15
```

## Notes
The main diagonal is a[i][i]; the anti-diagonal is a[i][n-1-i].
