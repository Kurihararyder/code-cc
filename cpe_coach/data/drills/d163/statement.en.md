# d163 Unbounded Knapsack

**Stage 3 · Difficulty ★★★ · Topic: Knapsack, unbounded**

There are n kinds of items; kind i has weight wᵢ and value vᵢ and you have an unlimited number of each. The knapsack holds weight W. Find the maximum total value that fits (total weight at most W).

## Input
The first line has n W (1 ≤ n ≤ 100, 0 ≤ W ≤ 10^4); then n lines `w v` (1 ≤ w ≤ 10^4, 1 ≤ v ≤ 10^9).

## Output
One integer.

## Sample Input
```
2 10
3 5
4 7
```

## Sample Output
```
17
```

## Notes
Same code as 0/1 knapsack except for the direction of the inner loop: unbounded goes from small to large (the same item may be used again).
