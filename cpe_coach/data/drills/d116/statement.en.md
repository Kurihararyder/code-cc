# d116 Goldbach Partition

**Stage 1 · Difficulty ★★ · Topic: Primes, sieve**

For each even number n, find two primes p ≤ q with p + q = n; if there are several, take the one with the smallest p, and print `n = p + q`. A solution is guaranteed to exist.

## Input
One even integer n per line (4 ≤ n ≤ 10^6), at most 10000 lines, until EOF.

## Output
`n = p + q` per line.

## Sample Input
```
4
```

## Sample Output
```
4 = 2 + 2
```

## Notes
Sieve all primes up to 10^6 once; for each query try p from small to large and only check whether n − p is prime.
