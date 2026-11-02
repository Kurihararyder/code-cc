# d161 Integer Break

**Stage 3 · Difficulty ★★ · Topic: DP, splitting**

Split a positive integer n into at least two positive integers summing to n so that their product is as large as possible, and print that maximum product (it can be a very large integer).

## Input
One integer n per line (2 ≤ n ≤ 1000), at most 20 lines, until EOF.

## Output
One integer per line.

## Sample Input
```
10
```

## Sample Output
```
36
```

## Notes
dp[n] = max over k of k × max(n−k, dp[n−k]); you may also notice the 'use as many 3s as possible' pattern, but first get the DP right.
