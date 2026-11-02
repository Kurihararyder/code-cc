# d150 First Edge Forming a Cycle

**Stage 3 · Difficulty ★★ · Topic: Union-find, cycle detection**

An undirected graph starts with no edges and edges are added in input order. Print the index (from 1) of the edge whose addition first creates a cycle (self-loops and repeated edges count as cycles); print 0 if no cycle ever appears.

## Input
The first line has n m (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2×10^5), then m lines `u v`.

## Output
One integer.

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
4
```

## Notes
If u and v are already connected before an edge (u, v) is added, that edge closes a cycle.
