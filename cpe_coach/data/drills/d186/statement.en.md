# d186 Tree Diameter

**Stage 4 · Difficulty ★★★ · Topic: Trees, diameter**

A tree has n vertices (n−1 unweighted edges). The distance between two vertices is the number of edges on the path between them. Print the distance between the two farthest vertices (the diameter). For n = 1 the answer is 0.

## Input
The first line has n (1 ≤ n ≤ 10^5), then n−1 lines `u v`.

## Output
One integer.

## Sample Input
```
5
1 2
2 3
3 4
2 5
```

## Sample Output
```
3
```

## Notes
BFS from any vertex to find the farthest vertex a; BFS again from a — the largest distance is the diameter. A long chain breaks recursive DFS, so iterate.
