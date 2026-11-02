# d154 Counting Shortest Paths

**Stage 3 · Difficulty ★★★ · Topic: Shortest paths, counting**

An undirected weighted graph has n vertices and m edges (weights ≥ 1). What is the shortest distance from vertex 1 to vertex n, and how many different shortest paths are there? Print the count modulo 1000000007. If vertex n is unreachable print `-1 0`.

## Input
The first line has n m (1 ≤ n ≤ 10^4, 0 ≤ m ≤ 5×10^4), then m lines `u v w` (1 ≤ w ≤ 1000; multi-edges may occur and count as distinct edges).

## Output
One line: distance count.

## Sample Input
```
4 5
1 2 1
1 3 1
2 4 1
3 4 1
2 3 1
```

## Sample Output
```
2 2
```

## Notes
Run Dijkstra and keep cnt[v] at the same time: when a shorter distance is found set cnt to the source's cnt; when it ties, add the source's cnt.
