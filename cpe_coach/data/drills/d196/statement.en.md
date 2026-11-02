# d196 Point Update, Range Minimum

**Stage 4 · Difficulty ★★★★ · Topic: Data structures, segment tree**

An array of n integers is followed by q operations: `1 i v` sets the i-th number to v; `2 l r` prints the minimum of the l-th through r-th numbers (1-based, inclusive).

## Input
The first line has n q (1 ≤ n, q ≤ 5×10^4); the second has n integers (absolute value ≤ 10^9); then q operation lines (|v| ≤ 10^9).

## Output
One line for every `2` operation.

## Sample Input
```
5 4
5 3 8 1 9
2 1 5
1 4 10
2 1 5
2 3 3
```

## Sample Output
```
1
3
8
```

## Notes
A sparse table (d087) cannot handle updates; a segment tree stores range minima in the nodes of a binary tree, giving O(log n) updates and queries. The bottom-up (non-recursive) version is the shortest.
