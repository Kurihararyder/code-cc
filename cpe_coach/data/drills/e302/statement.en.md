# e302 Longest Path in a DAG

**Stage 3 · Difficulty ★★★ · Topic: Topological sort + DP**

A directed acyclic graph (guaranteed to have no cycle) has n nodes and m edges. Find the number of edges on a path with the most edges.

## Input
The first line contains n and m (n ≤ 50000, m ≤ 100000); then m lines `u v`.

## Output
One integer.

## Sample Input
```
4 3
1 2
2 3
1 4
```

## Sample Output
```
2
```

## Notes
The longest path is hard in general graphs but O(n+m) in a DAG.
