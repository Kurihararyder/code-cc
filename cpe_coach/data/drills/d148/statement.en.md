# d148 Bipartite Check

**Stage 3 · Difficulty ★★ · Topic: Graphs, bipartite check**

An undirected graph has n vertices and m edges. Can all vertices be colored black or white so that the two ends of every edge have different colors? Print `YES` or `NO`. A self-loop makes the answer `NO`; the graph may be disconnected.

## Input
The first line has n m (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2×10^5), then m lines `u v` (1 ≤ u, v ≤ n; multi-edges and self-loops may occur).

## Output
`YES` or `NO`.

## Sample Input
```
4 4
1 2
2 3
3 4
4 1
```

## Sample Output
```
YES
```

## Notes
BFS-color each connected component; an edge whose ends share a color reveals an odd cycle.
