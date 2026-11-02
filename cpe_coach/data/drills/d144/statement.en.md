# d144 Total Set Bits up to n

**Stage 2 · Difficulty ★★★ · Topic: Bit operations, math**

For each n, count the total number of 1 bits in the binary representations of 1, 2, …, n (for n = 3: 1=1, 2=10, 3=11, total 4).

## Input
One integer n per line (1 ≤ n ≤ 10^18), at most 1000 lines, until EOF.

## Output
One integer per line.

## Sample Input
```
3
```

## Sample Output
```
4
```

## Notes
Look at one bit position at a time: bit i (from 0) is 1 for a run of 2^i numbers in every period of 2^(i+1) — use 'full periods × 2^i plus the partial last period'.
