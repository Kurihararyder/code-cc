# d169 Number Triangle

**Stage 3 · Difficulty ★★ · Topic: Grid DP, triangle**

Numbers form a triangle: row i has i numbers. Starting from the top, each step goes to an adjacent number directly below or below-right in the next row, down to the bottom row. Find the maximum possible sum of the numbers visited.

## Input
The first line has n (1 ≤ n ≤ 1000, the number of rows); then row i has i integers (absolute value ≤ 10^4).

## Output
One integer.

## Sample Input
```
5
7
3 8
8 1 0
2 7 4 4
4 5 2 6 5
```

## Sample Output
```
30
```

## Notes
Work bottom-up: the best value at each position is itself plus the larger of the two positions below.
