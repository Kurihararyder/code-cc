# d172 Stone Merging

**Stage 3 · Difficulty ★★★ · Topic: Interval DP, merging**

n piles of stones are in a row, pile i having aᵢ stones. Each move merges two adjacent piles into one at a cost equal to the total number of stones in the two piles. What is the minimum total cost to merge everything into one pile?

## Input
The first line has n (1 ≤ n ≤ 100); the second has n integers (1 ≤ aᵢ ≤ 1000).

## Output
One integer (0 when n = 1).

## Sample Input
```
4
4 1 1 4
```

## Sample Output
```
18
```

## Notes
dp[i][j] = minimum cost to merge piles i..j = min over k of (dp[i][k] + dp[k+1][j]) + sum(i..j); unlike 'Merge Cost' (d052) only adjacent piles may be merged.
