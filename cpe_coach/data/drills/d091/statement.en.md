# d091 Grid Paths With Obstacles

**Stage 4 · Difficulty ★★★ · Topic: DP (counting)**

An R×C grid: `#` is an obstacle and `.` is free. Moving only right or down, how many ways are there to go from the top-left to the bottom-right corner? Print the answer modulo 1000000007. (If the start or the end is an obstacle the answer is 0.)

## Input
The first line contains R and C (≤ 400), followed by R lines.

## Output
One integer.

## Sample Input
```
3 3
...
.#.
...
```

## Sample Output
```
2
```

## Notes
The answer is huge: take the remainder at every step.
