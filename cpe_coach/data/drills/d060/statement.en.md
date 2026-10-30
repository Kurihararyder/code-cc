# d060 Shortest Path in a Maze

**Stage 3 · Difficulty ★★ · Topic: BFS**

An R×C maze: `#` is a wall, `.` is a free cell, `S` is the start and `E` is the exit. In each step you may move one cell up, down, left or right. Find the minimum number of steps from S to E; print -1 if E cannot be reached.

## Input
The first line contains R and C (≤ 200), followed by R lines of the grid. There is exactly one S and one E.

## Output
One integer.

## Sample Input
```
3 3
S..
.#.
..E
```

## Sample Output
```
4
```

## Notes
BFS guarantees that the first time you reach a cell is along a shortest path. DFS cannot do that.
