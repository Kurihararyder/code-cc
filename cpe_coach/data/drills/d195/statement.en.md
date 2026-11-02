# d195 Dynamic Range Sums

**Stage 4 · Difficulty ★★★ · Topic: Data structures, Fenwick tree**

An array of n integers is followed by q operations: `1 i v` adds v to the i-th number; `2 l r` prints the sum of the l-th through r-th numbers (1-based, inclusive).

## Input
The first line has n q (1 ≤ n, q ≤ 5×10^4); the second has n integers (absolute value ≤ 10^9); then q operation lines (|v| ≤ 10^9).

## Output
One line for every `2` operation.

## Sample Input
```
5 4
1 2 3 4 5
2 1 5
1 3 10
2 1 3
2 3 3
```

## Sample Output
```
15
16
13
```

## Notes
Prefix sums cannot handle updates: recomputing after every update is O(n). A Fenwick tree (BIT) gives O(log n) for both updates and queries.
