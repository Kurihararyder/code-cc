# d160 Maximum Sum Without Neighbours

**Stage 3 · Difficulty ★★ · Topic: 1D DP, take or skip**

n non-negative integers are in a row. Choose some of them so that no two chosen numbers are adjacent, maximizing the sum. Print the maximum sum (choosing nothing gives 0).

## Input
The first line has n (1 ≤ n ≤ 10^5); the second has n integers (0 ≤ aᵢ ≤ 10^4).

## Output
One integer.

## Sample Input
```
4
1 2 3 1
```

## Sample Output
```
4
```

## Notes
dp[i] = max(dp[i−1], dp[i−2] + a[i]): skip the i-th, or take it (then the previous one cannot be taken).
