# e402 Largest Rectangle in a Histogram

**Stage 4 · Difficulty ★★★ · Topic: Monotonic stack**

A histogram has n bars of width 1 and heights h[i]. Find the largest rectangle area (the rectangle must consist of consecutive bars; its height is limited by the lowest bar).

## Input
The first line contains n (≤ 20000); the second line contains n integers (0 ≤ h ≤ 10^9).

## Output
One integer.

## Sample Input
```
6
2 1 5 6 2 3
```

## Sample Output
```
10
```

## Notes
Each bar enters and leaves the stack at most once, so it is O(n).
