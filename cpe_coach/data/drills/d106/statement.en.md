# d106 Prime Factorization

**Stage 0 · Difficulty ★★ · Topic: Prime factorization**

For each integer n print its prime factorization: prime factors in ascending order, each written as `p^e` and separated by single spaces (write the exponent even when it is 1, e.g. 12 → `2^2 3^1`).

## Input
One integer n per line (2 ≤ n ≤ 10^12), at most 10 lines, until EOF.

## Output
One result per line.

## Sample Input
```
12
```

## Sample Output
```
2^2 3^1
```

## Notes
Trial division up to √n: divide out each factor while counting; whatever remains above 1 at the end is itself prime.
