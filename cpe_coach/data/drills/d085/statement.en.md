# d085 Maximum Independent Set in a Tree

**Stage 4 · Difficulty ★★★★ · Topic: Tree DP**

A tree has n nodes. Choose as many nodes as possible so that no two chosen nodes are joined by an edge. Print the maximum number of nodes that can be chosen.

## Input
The first line contains n (≤ 25000); then n-1 lines `u v`.

## Output
One integer.

## Sample Input
```
5
1 2
1 3
3 4
3 5
```

## Sample Output
```
3
```

## Notes
A path-shaped tree makes naive recursion blow the stack — a Python limitation.
