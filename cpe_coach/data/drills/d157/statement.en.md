# d157 Minimum Spanning Forest

**Stage 3 · Difficulty ★★ · Topic: MST, spanning forest**

An undirected weighted graph has n vertices and m edges and may be disconnected. Taking a minimum spanning tree in every connected component gives a minimum spanning forest. Print the total weight of the forest and the number of connected components.

## Input
The first line has n m (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2×10^5), then m lines `u v w` (1 ≤ w ≤ 10^6; multi-edges and self-loops may occur).

## Output
One line: total_weight components.

## Sample Input
```
4 3
1 2 1
2 3 2
1 3 3
```

## Sample Output
```
3 2
```

## Notes
Kruskal does not need connectivity: edges that merge are the forest edges, and the number of groups left is the number of components.
