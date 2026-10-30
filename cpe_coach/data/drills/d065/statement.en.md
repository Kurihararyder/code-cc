# d065 Floyd–Warshall All-Pairs Shortest Paths

**Stage 3 · Difficulty ★★★ · Topic: Shortest paths**

An undirected weighted graph has n ≤ 100 nodes and m edges. Answer q queries `a b` with the shortest distance from a to b; print -1 if they are not connected.

## Input
The first line contains n, m and q; then m lines `u v w`; then q lines of queries.

## Output
q lines.

## Sample Input
```
3 2 3
1 2 4
2 3 5
1 3
3 1
1 1
```

## Sample Output
```
9
9
0
```

## Notes
Getting the loop order wrong (k must be the outermost loop) is the classic Floyd mistake.
