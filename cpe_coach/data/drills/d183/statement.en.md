# d183 Intersection Area of Two Rectangles

**Stage 4 · Difficulty ★★ · Topic: Geometry, rectangles**

Each line has eight integers `x1 y1 x2 y2 x3 y3 x4 y4`: the bottom-left (x1,y1) and top-right (x2,y2) corners of the first rectangle and likewise (x3,y3), (x4,y4) for the second (axis-parallel; x1<x2, y1<y2, x3<x4, y3<y4 are guaranteed). Print the area of their overlap; rectangles that only share an edge or a corner overlap in area 0.

## Input
Coordinates have absolute value ≤ 10^9, until EOF, at most 1000 lines.

## Output
One integer per line (it may exceed 63 bits halved, but Python does not care).

## Sample Input
```
0 0 4 4 2 2 6 6
```

## Sample Output
```
4
```

## Notes
Horizontal overlap length = max(0, min(x2,x4) − max(x1,x3)); the vertical one is similar; multiply them.
