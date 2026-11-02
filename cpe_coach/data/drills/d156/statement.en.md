# d156 Minimum Bottleneck Path

**Stage 3 · Difficulty ★★★ · Topic: MST, bottleneck paths**

An undirected weighted graph has n vertices and m edges. The bottleneck of a path is the weight of its heaviest edge. For each query `a b` find a path from a to b with the smallest bottleneck and print that value; print 0 when a = b and -1 when a and b are not connected.

## Input
The first line has n m q (1 ≤ n ≤ 1000, 0 ≤ m ≤ 5000, 1 ≤ q ≤ 1000), then m lines `u v w` (1 ≤ w ≤ 10^6; multi-edges and self-loops may occur), then q lines `a b`.

## Output
One line per query.

## Sample Input
```
4 4 3
1 2 5
2 3 3
1 3 9
3 4 1
1 4
1 3
2 2
```

## Sample Output
```
5
5
0
```

## Notes
A minimum-bottleneck path always exists inside the minimum spanning tree: run Kruskal, then answer each query by the heaviest edge on the tree path from a to b.
