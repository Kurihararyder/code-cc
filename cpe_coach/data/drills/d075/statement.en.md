# d075 Binomial Coefficient Modulo p

**Stage 3 · Difficulty ★★★ · Topic: Number theory, precomputation**

There are q queries `n r`. For each, print C(n, r) modulo 1000000007 (0 when r > n).

## Input
The first line contains q (≤ 20000); then q lines; n ≤ 10^6.

## Output
One line per query.

## Sample Input
```
3
5 2
10 0
4 5
```

## Sample Output
```
10
1
0
```

## Notes
Modular arithmetic: you cannot divide directly; multiply by the modular inverse.
