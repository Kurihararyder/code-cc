# e301 Nearest Exit

**Stage 3 · Difficulty ★★ · Topic: Multi-source BFS**

An R×C grid: `#` wall, `.` open cell, `X` exit. From an open cell you may move up, down, left or right (not through walls). For every open cell find the number of steps to the nearest exit. Print the sum of the steps over all open cells that can reach an exit, and the number of open cells that cannot reach any exit.

## Input
The first line contains R and C (≤ 300), followed by R lines. There is at least one exit.

## Output
One line: total unreachable-count.

## Sample Input
```
3 3
X..
.#.
...
```

## Sample Output
```
16 0
```

## Notes
Running a search from every start is O(N²·E); a multi-source BFS needs only O(N).
