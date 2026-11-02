# d096 Seconds to H M S

**Stage 0 · Difficulty ★ · Topic: Arithmetic, // and %**

For each number of seconds s, print it as hours, minutes and seconds in the form `h m s` separated by single spaces (m and s are in 0–59; h has no upper limit).

## Input
One integer s per line (0 ≤ s ≤ 10^9), until EOF.

## Output
One result per line.

## Sample Input
```
3661
```

## Sample Output
```
1 1 1
```

## Notes
`//` gives the quotient and `%` the remainder; handle hours first, then the remaining seconds.
