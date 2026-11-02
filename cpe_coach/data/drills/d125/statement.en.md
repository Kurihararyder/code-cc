# d125 Median

**Stage 2 · Difficulty ★★ · Topic: Sorting, statistics**

Given n integers, print their median. For odd n it is the middle number after sorting; for even n it is the average of the two middle numbers — print an integer if the average is an integer, otherwise print it with exactly one decimal digit (it is always x.5; write negatives as -2.5).

## Input
The first line has n (1 ≤ n ≤ 2×10^5); the second line has n integers (absolute value ≤ 10^9).

## Output
One number.

## Sample Input
```
5
3 1 4 1 5
```

## Sample Output
```
3
```

## Notes
Dividing with `/` gives a float; decide parity yourself and use `//` for integer answers.
