# d128 Rectangle Sums

**Stage 2 · Difficulty ★★★ · Topic: Prefix sums, 2D**

Given an R×C grid of integers and q queries `r1 c1 r2 c2` (rows and columns are 1-based, r1 ≤ r2, c1 ≤ c2), print the sum of all numbers inside the rectangle from (r1,c1) to (r2,c2).

## Input
The first line has R C q (1 ≤ R, C ≤ 500, 1 ≤ q ≤ 10^5); then R lines of C integers (absolute value ≤ 1000); then q query lines.

## Output
One line per query.

## Sample Input
```
3 3 2
1 2 3
4 5 6
7 8 9
1 1 3 3
2 2 3 3
```

## Sample Output
```
45
28
```

## Notes
2D prefix sums: `S[i][j] = a[i][j] + S[i-1][j] + S[i][j-1] - S[i-1][j-1]`; answer a query by inclusion–exclusion.
