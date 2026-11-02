# d066 Coin Combinations

**Stage 3 · Difficulty ★★★ · Topic: DP (counting)**

There are n distinct denominations, each available in unlimited quantity. How many combinations (order does not matter) make the amount A? Print the answer modulo 1000000007.

## Input
The first line contains n and A (1 ≤ n ≤ 50, 0 ≤ A ≤ 10^4); the second line contains n distinct denominations (1–10^4).

## Output
One integer.

## Sample Input
```
3 4
1 2 3
```

## Sample Output
```
4
```

## Notes
The loop order decides between 'combinations' and 'permutations' — one of the most important observations in DP.
