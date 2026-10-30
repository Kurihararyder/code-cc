# d063 Dijkstra Shortest Path

**Stage 3 · Difficulty ★★★ · Topic: Shortest paths**

An undirected weighted graph has n nodes and m edges. Find the shortest distance from node 1 to node n; print -1 if they are not connected.

## Input
The first line contains n and m (n ≤ 5000, m ≤ 2×10^4), followed by m lines `u v w` (1 ≤ w ≤ 1000).

## Output
One integer.

## Sample Input
```
3 3
1 2 5
2 3 5
1 3 20
```

## Sample Output
```
10
```

## Notes
An O(n²) Dijkstra at n=5000 needs 2.5×10^7 steps, which is heavy for Python; the heap version is much faster.
