# d170 Grid Paths

**Stage 3 · Difficulty ★ · Topic: Grid DP, counting paths**

In an R×C grid, starting at the top-left corner and moving only right or down, how many ways are there to reach the bottom-right corner? Print the answer modulo 1000000007.

## Input
Each line has two integers R C (1 ≤ R, C ≤ 1000), at most 10 lines, until EOF.

## Output
One integer per line.

## Sample Input
```
3 7
```

## Sample Output
```
28
```

## Notes
dp[i][j] = dp[i−1][j] + dp[i][j−1]; the first row and first column each have exactly 1 way.
