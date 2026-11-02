# d164 Exact-Fill Knapsack

**Stage 3 · Difficulty ★★★ · Topic: Knapsack, exact fill**

There are n items (each usable at most once); item i has weight wᵢ and value vᵢ. Choose items whose total weight is exactly W and maximize the total value; print -1 if W cannot be filled exactly.

## Input
The first line has n W (1 ≤ n ≤ 100, 0 ≤ W ≤ 10^4); then n lines `w v` (1 ≤ w ≤ 10^4, 1 ≤ v ≤ 10^9).

## Output
One integer.

## Sample Input
```
3 5
2 3
3 4
4 10
```

## Sample Output
```
7
```

## Notes
The difference from the ordinary knapsack is the initial values: dp[0] = 0 and every other entry is −∞ (meaning 'this weight cannot be reached yet').
