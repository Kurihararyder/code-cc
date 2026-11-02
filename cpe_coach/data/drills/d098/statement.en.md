# d098 Triangle Types

**Stage 0 · Difficulty ★ · Topic: Conditions**

Each line has three positive integers a b c, the lengths of three sides. If they cannot form a triangle (the sum of the two shorter sides ≤ the longest side; a degenerate segment does not count), print `NOT`. Otherwise print `EQUILATERAL` if all three are equal, `ISOSCELES` if exactly two are equal, and `SCALENE` otherwise.

## Input
Three integers (1–10^9) per line, until EOF.

## Output
One word per line.

## Sample Input
```
3 4 5
```

## Sample Output
```
SCALENE
```

## Notes
Decide whether a triangle exists first, then its type. 'Two short sides sum to exactly the long side' is the boundary people forget.
