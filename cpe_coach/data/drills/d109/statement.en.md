# d109 Minesweeper

**Stage 0 · Difficulty ★★ · Topic: 2D lists, simulation**

The first line has r c, followed by r lines of c characters: `*` is a mine and `.` is an empty cell. Print a board of the same size in which mines stay `*` and every empty cell becomes the number (0–8) of mines among its eight neighbours (including diagonals).

## Input
1 ≤ r, c ≤ 100.

## Output
r lines of c characters.

## Sample Input
```
3 4
*...
....
.*..
```

## Sample Output
```
*100
2210
1*10
```

## Notes
Check the bounds for all eight directions; a direction table such as `[(-1,-1),(-1,0),...]` is the least error-prone.
