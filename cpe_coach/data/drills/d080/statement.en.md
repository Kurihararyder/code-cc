# d080 Convex Hull

**Stage 4 · Difficulty ★★★★ · Topic: Computational geometry**

There are n points with integer coordinates in the plane (possibly duplicated or collinear). Print the number of vertices of the convex hull (collinear points do not count as vertices) and twice the area of the hull (an integer). If all points are collinear, print 2 vertices (the two endpoints) and area 0; if there is only one distinct point, print 1 vertex and area 0.

## Input
The first line contains n (≤ 20000); then n lines `x y` (|x|, |y| ≤ 10^6).

## Output
One line: vertices twice-area.

## Sample Input
```
4
0 0
1 0
1 1
0 1
```

## Sample Output
```
4 2
```

## Notes
The sign of the cross product and 'whether to keep collinear points' are the most common details in geometry problems.
