# d187 Lowest Common Ancestor

**Stage 4 · Difficulty ★★★★ · Topic: Trees, LCA**

A tree rooted at vertex 1 has n vertices and n−1 edges (given undirected). For each of q queries `a b` print the lowest common ancestor of a and b (the deepest vertex that is an ancestor of both; a vertex counts as its own ancestor).

## Input
The first line has n q (1 ≤ n, q ≤ 5×10^4); then n−1 lines `u v`; then q lines `a b`.

## Output
One line per query.

## Sample Input
```
7 3
1 2
1 3
2 4
2 5
3 6
3 7
4 5
4 6
7 7
```

## Sample Output
```
2
1
7
```

## Notes
Binary lifting: up[k][v] is the 2^k-th ancestor of v. Lift the deeper vertex to the same depth, then jump both upwards together. Build depth and parents with BFS to avoid recursion.
