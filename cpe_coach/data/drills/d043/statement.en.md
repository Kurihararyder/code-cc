# d043 Run-Length Compression

**Stage 1 · Difficulty ★ · Topic: Strings**

Compress each line (no whitespace inside): a run of equal characters is written as `character+count`, for example `aaabcc` → `a3b1c2`.

## Input
Each line has length ≤ 10^5, until EOF.

## Output
One compressed string per line.

## Sample Input
```
aaabcc
```

## Sample Output
```
a3b1c2
```

## Notes
Forgetting the last run after the loop ends is the most common off-by-one error.
