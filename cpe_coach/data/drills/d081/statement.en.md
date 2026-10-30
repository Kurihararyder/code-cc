# d081 Segment Intersection

**Stage 4 · Difficulty ★★★★ · Topic: Computational geometry**

Each line has 8 integers `x1 y1 x2 y2 x3 y3 x4 y4`, describing segments AB and CD (endpoints may coincide; a segment may degenerate to a point). Print `YES` if the two segments share any point (touching at an endpoint and collinear overlap both count), otherwise `NO`.

## Input
Absolute values of coordinates ≤ 10^9, at most 1000 lines, until EOF.

## Output
YES or NO per line.

## Sample Input
```
0 0 2 2 0 2 2 0
```

## Sample Output
```
YES
```

## Notes
There are many edge cases: build 10 test cases of your own before submitting.
