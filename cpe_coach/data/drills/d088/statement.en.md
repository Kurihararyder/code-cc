# d088 Negative Edges and Negative Cycles

**Stage 4 · Difficulty ★★★★ · Topic: Bellman-Ford**

A directed graph has n nodes and m edges whose weights may be negative. If a negative cycle is reachable from node 1, print `NEGATIVE CYCLE`; otherwise print the shortest distance from node 1 to node n, or `UNREACHABLE` if it cannot be reached.

## Input
The first line contains n and m (n ≤ 500, m ≤ 3000); then m lines `u v w` (|w| ≤ 1000).

## Output
One line.

## Sample Input
```
3 3
1 2 4
2 3 -2
1 3 5
```

## Sample Output
```
2
```

## Notes
The condition 'reachable from 1' is easy to forget: an unreachable negative cycle does not count.
