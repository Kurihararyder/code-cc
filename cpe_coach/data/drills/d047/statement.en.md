# d047 First Position Not Less Than x

**Stage 2 · Difficulty ★★ · Topic: Binary search**

Given an array sorted in non-decreasing order, for each query x print the smallest position i (1-indexed) such that a[i] ≥ x; if there is none, print n+1.

## Input
The first line contains n and q; the second line contains n non-decreasing integers; the third line contains q queries. n, q ≤ 20000.

## Output
q numbers separated by spaces, on one line.

## Sample Input
```
5 4
1 3 3 5 8
3 4 9 0
```

## Sample Output
```
2 4 6 1
```

## Notes
A linear scan is O(nq) and times out; binary search is O(q log n).
