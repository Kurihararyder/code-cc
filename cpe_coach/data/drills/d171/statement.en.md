# d171 Largest All-Ones Square

**Stage 3 · Difficulty ★★★ · Topic: Grid DP, squares**

Given an R×C 0/1 matrix, find the largest square (sides parallel to the grid) consisting only of 1s and print its side length; print 0 if there is no 1.

## Input
The first line has R C (1 ≤ R, C ≤ 500), then R lines of C characters (only 0 and 1, no spaces).

## Output
One integer.

## Sample Input
```
4 5
10100
10111
11111
10010
```

## Sample Output
```
2
```

## Notes
dp[i][j] = side of the largest square with bottom-right corner (i,j) = 1 + min(up, left, up-left) when the cell is 1.
