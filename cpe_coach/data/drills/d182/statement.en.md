# d182 Point in Polygon

**Stage 4 · Difficulty ★★★ · Topic: Geometry, point in polygon**

Given a simple polygon (vertices listed clockwise or counter-clockwise; edges do not cross or touch each other) and q points, print for each point `INSIDE`, `BOUNDARY` (exactly on an edge, vertices included) or `OUTSIDE`.

## Input
The first line has n (3 ≤ n ≤ 1000); then n lines `x y`; then a line q (1 ≤ q ≤ 1000); then q lines `x y`. All coordinates are integers with absolute value ≤ 10^4.

## Output
One line per point.

## Sample Input
```
4
0 0
4 0
4 4
0 4
5
2 2
0 0
2 0
5 2
-1 -1
```

## Sample Output
```
INSIDE
BOUNDARY
BOUNDARY
OUTSIDE
OUTSIDE
```

## Notes
First check whether the point lies on an edge (cross product 0 and inside the segment's range); otherwise shoot a ray to the right and count crossings (odd means inside). Handle rays through vertices with the half-open rule 'one end above, the other not above'.
