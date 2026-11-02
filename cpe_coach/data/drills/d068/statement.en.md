# d068 0/1 Knapsack

**Stage 3 · Difficulty ★★★ · Topic: DP (knapsack)**

There are n items; item i has weight w and value v. The knapsack has capacity W. Each item can be taken at most once. Find the maximum total value.

## Input
The first line contains n and W (1 ≤ n ≤ 100, 0 ≤ W ≤ 10^4); then n lines `w v` (1 ≤ w ≤ 10^4, 1 ≤ v ≤ 10^9).

## Output
One integer.

## Sample Input
```
3 50
10 60
20 100
30 120
```

## Sample Output
```
220
```

## Notes
Iterating the inner loop from large to small is the only difference between 0/1 and unbounded knapsack.
