# d174 Cutting Sticks

**Stage 3 · Difficulty ★★★ · Topic: Interval DP, cutting**

A stick of length L must be cut at k given positions (distances from the left end, pairwise different, strictly between 0 and L). Each cut costs the current length of the piece being cut, and you choose the order of the cuts. Find the minimum total cost. There are t test cases.

## Input
The first line has t (1 ≤ t ≤ 20); each case has two lines: `L k` (1 ≤ k ≤ 100, k < L ≤ 10^6) and k increasing positions.

## Output
One line per case.

## Sample Input
```
2
10 3
2 4 7
100 3
25 50 75
```

## Sample Output
```
20
200
```

## Notes
Treat the two ends 0 and L as cut points as well; dp[i][j] = minimum cost to cut everything between points i and j = min over m of (dp[i][m] + dp[m][j]) + (pos[j] − pos[i]).
