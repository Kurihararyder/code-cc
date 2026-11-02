# d117 Perfect, Abundant and Deficient

**Stage 1 · Difficulty ★★ · Topic: Math, divisors**

The proper divisors of a positive integer n are all its positive divisors except n itself (1 has proper-divisor sum 0). Let s be their sum: print `PERFECT` if s = n, `ABUNDANT` if s > n, and `DEFICIENT` if s < n.

## Input
One integer n per line (1 ≤ n ≤ 10^6), at most 2000 lines, until EOF.

## Output
One word per line.

## Sample Input
```
28
```

## Sample Output
```
PERFECT
```

## Notes
Find divisors in pairs: if i divides n then n // i does too; go only up to √n; for a perfect square i and n // i coincide and must be added once.
