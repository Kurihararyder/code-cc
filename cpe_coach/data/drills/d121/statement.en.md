# d121 Diagonal Fill

**Stage 1 · Difficulty ★ · Topic: 2D arrays, filling**

Read n and print an n×n matrix filled with 1 to n² along anti-diagonals: first the top-left cell, then each following anti-diagonal in turn, where the cells of one diagonal are filled from the smaller row number to the larger one, until the bottom-right corner. For n = 3 the result is
`1 2 4`
`3 5 7`
`6 8 9`

## Input
One integer n (1 ≤ n ≤ 50).

## Output
n lines of n numbers separated by spaces.

## Sample Input
```
3
```

## Sample Output
```
1 2 4
3 5 7
6 8 9
```

## Notes
All cells on one anti-diagonal have the same row + column.
