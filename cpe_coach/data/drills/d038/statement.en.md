# d038 Prime Counting Queries

**Stage 1 · Difficulty ★ · Topic: Sieve of primes**

The first line contains q; then q lines follow, each containing an integer n. Print how many primes there are among 1..n.

## Input
q ≤ 30000, n ≤ 10^6.

## Output
One line per query.

## Sample Input
```
5
1
2
10
100
1000000
```

## Sample Output
```
0
1
4
25
78498
```

## Notes
'Precompute once, answer in O(1)' is one of the most important ideas in contests.
