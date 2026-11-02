# d130 Range Add

**Stage 2 · Difficulty ★★★ · Topic: Difference arrays**

An array of length n starts as all zeros. Then m operations `l r v` follow: add v to positions l through r (inclusive, 1-based). After all operations print the whole array.

## Input
The first line has n m (1 ≤ n, m ≤ 2×10^5); then m lines `l r v` (1 ≤ l ≤ r ≤ n, |v| ≤ 10^4).

## Output
One line of n integers separated by spaces.

## Sample Input
```
5 3
1 3 2
2 5 -1
3 3 10
```

## Sample Output
```
2 1 11 -1 -1
```

## Notes
Do not loop for each operation (O(nm)): on a difference array do `d[l] += v; d[r+1] -= v`, then take one prefix sum at the end.
