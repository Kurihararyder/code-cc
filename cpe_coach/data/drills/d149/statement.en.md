# d149 Is It a Tree?

**Stage 3 · Difficulty ★★ · Topic: Graphs, tree test**

An undirected graph has n vertices and m edges. Is it a tree (connected and without cycles)? Print `YES` or `NO`. A single vertex (n = 1, m = 0) is a tree; multi-edges and self-loops count as cycles.

## Input
The first line has n m (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2×10^5), then m lines `u v`.

## Output
`YES` or `NO`.

## Sample Input
```
4 3
1 2
2 3
3 4
```

## Sample Output
```
YES
```

## Notes
A graph is a tree iff m = n − 1 and it is connected. With union–find: m = n−1 and every edge merges two different components.
