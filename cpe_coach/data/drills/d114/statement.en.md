# d114 Carries in an Addition

**Stage 1 · Difficulty ★★ · Topic: Digit-by-digit simulation**

Each line has two non-negative integers a b (no leading zeros, at most 30 digits). Add them like long addition, from the units digit leftwards, and print how many digit positions produce a carry (carries propagate, so 999 + 1 has 3 carries).

## Input
Each line `a b`, until EOF.

## Output
One integer per line.

## Sample Input
```
123 456
```

## Sample Output
```
0
```

## Notes
In column addition each column sums the two digits plus the carry from the previous column; ≥ 10 produces a carry. Simulate digit by digit instead of adding the big integers directly.
