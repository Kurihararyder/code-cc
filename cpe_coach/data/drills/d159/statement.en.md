# d159 Climbing Stairs

**Stage 3 · Difficulty ★ · Topic: DP basics, counting**

A staircase has n steps and each move climbs 1, 2 or 3 steps. How many different ways are there to reach step n (different orders count as different)? Print the answer modulo 1000000007. For n = 0 there is 1 way (stay where you are).

## Input
One integer n per line (0 ≤ n ≤ 10^6), at most 100 lines, until EOF.

## Output
One integer per line.

## Sample Input
```
4
```

## Sample Output
```
7
```

## Notes
dp[i] = dp[i−1] + dp[i−2] + dp[i−3]; precompute up to the largest n.
