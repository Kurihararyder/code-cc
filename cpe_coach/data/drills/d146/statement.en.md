# d146 Number of Islands

**Stage 3 · Difficulty ★★ · Topic: Flood fill, connected regions**

A map of R×C cells: `1` is land and `0` is sea. Land cells adjacent up, down, left or right belong to the same island (diagonal neighbours do not connect). Print the number of islands.

## Input
The first line has R C (1 ≤ R, C ≤ 500), then R lines of C characters (only 0 and 1, no spaces).

## Output
One integer.

## Sample Input
```
4 5
11000
11000
00100
00011
```

## Sample Output
```
3
```

## Notes
Scan every cell: an unvisited land cell starts a new island, and a BFS (or iterative DFS) marks the whole island. Recursive DFS blows the stack on a 250000-cell snake-like island.
