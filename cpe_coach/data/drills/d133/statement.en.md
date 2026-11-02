# d133 Next Greater Element

**Stage 2 · Difficulty ★★ · Topic: Monotonic stack**

Given n integers, for every position i find the value of the first number to its right that is strictly greater than aᵢ; print -1 if none exists.

## Input
The first line has n (1 ≤ n ≤ 2×10^5); the second has n integers (absolute value ≤ 10^9).

## Output
One line of n integers separated by spaces.

## Sample Input
```
5
2 1 2 4 3
```

## Sample Output
```
4 2 4 -1 -1
```

## Notes
Scan from right to left, keeping a stack of candidates that could still be an answer (decreasing from bottom to top).
