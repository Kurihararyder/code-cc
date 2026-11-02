# d184 Relation of Two Circles

**Stage 4 · Difficulty ★★★ · Topic: Geometry, circles**

Each line has six integers `x1 y1 r1 x2 y2 r2`, two circles (centre and radius). Print their relation: `SAME` (identical), `SEPARATE` (no common point, each outside the other), `EXTERNAL` (externally tangent: exactly one common point, each outside the other), `INTERSECT` (two common points), `INTERNAL` (internally tangent: exactly one common point, one inside the other), `CONTAIN` (no common point, one inside the other).

## Input
Coordinates have absolute value ≤ 10^9, radii 1 ≤ r ≤ 10^9, until EOF, at most 1000 lines.

## Output
One word per line.

## Sample Input
```
0 0 3 5 0 3
```

## Sample Output
```
INTERSECT
```

## Notes
Compare the squared centre distance with (r1+r2)² and (r1−r2)²: pure integer arithmetic. Do not use sqrt or floats (they fail at 10^9).
