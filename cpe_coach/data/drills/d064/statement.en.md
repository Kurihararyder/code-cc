# d064 Minimum Spanning Tree

**Stage 3 · Difficulty ★★★ · Topic: MST**

Given a connected undirected weighted graph, print the total weight of a minimum spanning tree; print -1 if the graph is not connected.

## Input
The first line contains n and m (1 ≤ n ≤ 5000, 0 ≤ m ≤ 2×10^4), followed by m lines `u v w` (1 ≤ w ≤ 10^6, multi-edges possible).

## Output
One integer.

## Sample Input
```
3 3
1 2 1
2 3 2
1 3 3
```

## Sample Output
```
3
```

## Notes
Know both Kruskal and Prim; learn Kruskal first because it only needs sorting and union-find.
