# d097 Making Change

**Stage 0 · Difficulty ★ · Topic: Arithmetic, greedy change**

You have unlimited coins of 50, 10, 5 and 1. For each amount n, pay it with the fewest coins and print how many coins of each kind you use as `a b c d` (in the order 50, 10, 5, 1).

## Input
One integer n per line (1 ≤ n ≤ 10^6), until EOF.

## Output
Four integers per line.

## Sample Input
```
68
```

## Sample Output
```
1 1 1 3
```

## Notes
Always take the largest coin you can. For this coin system greedy is correct (later, in coin-change DP, you will meet systems where greedy fails).
