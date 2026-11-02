# d153 Is the Topological Order Unique?

**Stage 3 · Difficulty ★★ · Topic: Topological sort, uniqueness**

A directed graph has n vertices and m edges `u v` (u must come before v; repeated edges may occur). Print `CYCLE` if the graph has a cycle (a self-loop counts); otherwise print `UNIQUE` if there is exactly one valid order and `MULTIPLE` if there are two or more.

## Input
The first line has n m (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2×10^5), then m lines `u v`.

## Output
`CYCLE`, `UNIQUE` or `MULTIPLE`.

## Sample Input
```
4 3
1 2
2 3
3 4
```

## Sample Output
```
UNIQUE
```

## Notes
In Kahn's algorithm, if at some step two or more vertices have in-degree 0 the order is not unique — but first make sure the whole graph is acyclic.
