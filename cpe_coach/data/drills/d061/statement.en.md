# d061 Union-Find: Components

**Stage 3 · Difficulty ★★ · Topic: Union-find**

There are n nodes and m operations `a b`, each merging the groups containing a and b. After all operations print the number of groups and the size of the largest group.

## Input
The first line contains n and m (n, m ≤ 50000), followed by m lines.

## Output
One line: number-of-groups largest-size.

## Sample Input
```
5 3
1 2
2 3
4 5
```

## Sample Output
```
2 3
```

## Notes
Learn both path compression and union by size; either one alone is fast enough, but using both is the most robust.
