# d175 Assignment Problem

**Stage 3 · Difficulty ★★★ · Topic: Bitmask DP, assignment**

n people must do n jobs, each person doing exactly one job and each job done by exactly one person. The cost of person i doing job j is c[i][j]. Find the minimum total cost.

## Input
The first line has n (1 ≤ n ≤ 12), then n lines of n integers (0 ≤ c ≤ 1000).

## Output
One integer.

## Sample Input
```
3
9 2 7
6 4 3
5 8 1
```

## Sample Output
```
9
```

## Notes
dp[mask] = minimum cost when the first popcount(mask) people have taken exactly the jobs in mask; the next person tries every job not yet taken.
