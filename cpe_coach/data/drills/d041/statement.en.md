# d041 Robot on a Grid

**Stage 1 · Difficulty ★ · Topic: Simulation, coordinates**

A robot stands at the bottom-left corner (0,0) of an N×N grid (coordinates 0..N-1). The first line contains N; the second line is a command string made of `U` (y+1), `D` (y-1), `L` (x-1) and `R` (x+1). If a move would leave the grid, **ignore that command**. Print the final coordinates `x y`.

## Input
N ≤ 100, the command string has length ≤ 10^5.

## Output
One line: x y.

## Sample Input
```
3
UURR
```

## Sample Output
```
2 2
```

## Notes
The standard pattern for simulation: a direction table plus a bounds check.
