# d147 Knight's Shortest Path

**Stage 3 · Difficulty ★★ · Topic: BFS, minimum moves**

On an N×N board (rows and columns from 1) a chess knight moves in an L-shape (2 squares horizontally and 1 vertically, or 1 horizontally and 2 vertically). For each of t queries (board size, start, target) print the minimum number of moves, or -1 if the target is unreachable.

## Input
The first line has t (1 ≤ t ≤ 100); then t lines `N r1 c1 r2 c2` (1 ≤ N ≤ 50, coordinates inside the board).

## Output
One line per query.

## Sample Input
```
3
8 1 1 8 8
3 1 1 3 3
3 2 2 1 1
```

## Sample Output
```
6
4
-1
```

## Notes
BFS gives the fewest moves; tiny boards (such as 2×2 and 3×3) have unreachable squares.
