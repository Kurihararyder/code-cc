# d194 Maximum Weight Path in a Tree

**Stage 4 · Difficulty ★★★★ · Topic: Tree DP, maximum path sum**

A tree has n vertices, each with a weight (possibly negative). Find a path (at least one vertex, any two endpoints, no repeated vertices) maximizing the sum of the vertex weights on it, and print that sum.

## Input
The first line has n (1 ≤ n ≤ 10^5); the second has n integers (absolute value ≤ 10^9); then n−1 lines `u v`.

## Output
One integer.

## Sample Input
```
5
1 2 3 4 5
1 2
2 3
2 4
4 5
```

## Sample Output
```
14
```

## Notes
Tree DP: down[u] = w[u] + max(0, best down[child]); the best path through u = w[u] plus the two largest max(0, down[child]). Process vertices in an iterative order to avoid deep recursion.
