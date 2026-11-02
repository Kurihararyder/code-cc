# d179 Many Factorizations

**Stage 3 · Difficulty ★★★ · Topic: Number theory, sieve**

Given many integers n, print the prime factorization of each (primes ascending, written `p^e` and separated by spaces; write the exponent even when it is 1).

## Input
The first line has q (1 ≤ q ≤ 10^5); then q lines each with an integer n (2 ≤ n ≤ 10^6).

## Output
One line per query.

## Sample Input
```
3
12
97
1000000
```

## Sample Output
```
2^2 3^1
97^1
2^6 5^6
```

## Notes
Trial division per number is too slow: precompute the smallest prime factor spf[n] with a sieve, then each number is factored by repeatedly dividing by its spf.
