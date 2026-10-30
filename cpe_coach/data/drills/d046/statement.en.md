# d046 Range Sum Queries

**Stage 2 · Difficulty ★★ · Topic: Prefix sums**

Given an array of length n and q queries, each query is l r (1-indexed); print a[l]+…+a[r].

## Input
The first line contains n and q; the second line contains n integers; then q lines l r. n, q ≤ 20000, |a| ≤ 10^6.

## Output
One line per query.

## Sample Input
```
5 3
1 2 3 4 5
1 5
2 3
5 5
```

## Sample Output
```
15
5
5
```

## Notes
Summing with a hand-written loop for every query is O(nq) and times out here (the built-in sum(a[l-1:r]) barely passes at this size, but not if n and q grow five-fold — real exams do that).
