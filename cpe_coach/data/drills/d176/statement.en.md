# d176 Hamiltonian Paths

**Stage 3 · Difficulty ★★★ · Topic: Bitmask DP, counting paths**

A directed graph has n vertices (n ≤ 15) and m edges (no repeated edges, no self-loops). Count the paths that start at vertex 1 and visit every vertex exactly once (the endpoint may be any vertex; for n = 1 there is exactly one). Print the count modulo 1000000007.

## Input
The first line has n m (1 ≤ n ≤ 15, 0 ≤ m ≤ n(n−1)); then m lines `u v`.

## Output
One integer.

## Sample Input
```
4 5
1 2
2 3
3 4
1 3
2 4
```

## Sample Output
```
1
```

## Notes
dp[mask][v] = number of paths that have visited exactly the set mask and are now at v; extend by one edge to an unvisited vertex. 2^n × n states with n transitions each: about 7×10^6 for n = 15.
