# d078 Knapsack (Large)

**Stage 4 · Difficulty ★★★ · Topic: DP, performance**

The same 0/1 knapsack as d068, but n ≤ 1000 and W ≤ 50000.

## Input
The first line contains n and W; then n lines `w v`.

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
Number of states × number of transitions = amount of work. Up to about 10^8 is safe in C++; in Python 10^7 is already risky.
