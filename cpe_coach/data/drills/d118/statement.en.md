# d118 Twin Prime Pairs

**Stage 1 · Difficulty ★★ · Topic: Primes, precomputation**

Twin primes are two primes that differ by 2, written (p, p+2). For each query n print the number of twin pairs with p + 2 ≤ n (for n = 13 there are (3,5), (5,7), (11,13): 3 pairs).

## Input
The first line has q (1 ≤ q ≤ 10^5); then q lines each with one n (1 ≤ n ≤ 10^6).

## Output
One line per query.

## Sample Input
```
3
13
5
100
```

## Sample Output
```
3
1
8
```

## Notes
Like 'Prime Counting Queries': precompute once and answer each query in O(1) — this time accumulate twin *pairs*.
