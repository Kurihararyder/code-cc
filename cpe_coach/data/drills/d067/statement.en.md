# d067 Fewest Coins

**Stage 3 · Difficulty ★★★ · Topic: DP (optimisation)**

There are n distinct denominations, each available in unlimited quantity. What is the minimum number of coins needed to make the amount A? Print -1 if it is impossible.

## Input
The first line contains n and A (n ≤ 100, A ≤ 10^4); the second line contains n denominations.

## Output
One integer.

## Sample Input
```
3 11
1 2 5
```

## Sample Output
```
3
```

## Notes
The data contains cases where greedy fails (6 = 3+3, not 4+1+1).
