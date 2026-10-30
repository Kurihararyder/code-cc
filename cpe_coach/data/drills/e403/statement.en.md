# e403 Roads That May Be Free

**Stage 4 · Difficulty ★★★★ · Topic: Layered shortest path**

An undirected weighted graph has n nodes and m edges. You may make the cost of up to K edges zero (you choose which). Find the minimum total cost from node 1 to node n; print -1 if they are not connected.

## Input
The first line contains n, m and K (n ≤ 1000, m ≤ 5000, K ≤ 5); then m lines `u v w` (1 ≤ w ≤ 10^6).

## Output
One integer.

## Sample Input
```
3 3 1
1 2 5
2 3 7
1 3 20
```

## Sample Output
```
0
```

## Notes
The same node reached after using a different number of free edges is a different state.
