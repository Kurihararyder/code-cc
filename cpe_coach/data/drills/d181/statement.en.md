# d181 Triangle Area and Type

**Stage 4 · Difficulty ★★ · Topic: Geometry, triangles**

Each line has six integers `x1 y1 x2 y2 x3 y3`, three points of the plane. Print `twice_area TYPE`: if the points are collinear (including coincident) the type is `DEGENERATE` (area 0); otherwise by the largest interior angle: `ACUTE` (all angles below 90°), `RIGHT` (one right angle), `OBTUSE` (one obtuse angle).

## Input
Coordinates have absolute value ≤ 10^6, until EOF, at most 1000 lines.

## Output
One `integer word` per line.

## Sample Input
```
0 0 4 0 0 3
```

## Sample Output
```
12 RIGHT
```

## Notes
Use integers only: twice the area is the absolute cross product; decide the angle type by the sign of dot products (> 0 acute, = 0 right, < 0 obtuse) — no trigonometry needed.
