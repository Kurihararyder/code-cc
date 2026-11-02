# d158 Is the MST Unique?

**Stage 3 · Difficulty ★★★ · Topic: MST, uniqueness**

A connected undirected weighted graph has n vertices and m edges (multi-edges and self-loops may occur). Print the total weight of a minimum spanning tree and whether it is unique: `UNIQUE` if there is only one MST, `MULTIPLE` if several MSTs share the minimum weight.

## Input
The first line has n m (1 ≤ n ≤ 10^4, n − 1 ≤ m ≤ 5×10^4, connected is guaranteed); then m lines `u v w` (1 ≤ w ≤ 10^6).

## Output
One line: total_weight UNIQUE or MULTIPLE.

## Sample Input
```
4 5
1 2 1
2 3 2
3 4 3
1 4 4
1 3 5
```

## Sample Output
```
6 UNIQUE
```

## Notes
In Kruskal, process each batch of equal-weight edges together: if more edges in the batch could join different groups (at the start of the batch) than were actually merged, there was an alternative choice.
