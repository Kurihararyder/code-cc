# d028 Two Sum

**Stage 0 · Difficulty ★ · Topic: set, performance**

Given n integers and a target T, is there a pair of numbers at **two different positions** whose sum is T? Print `YES` or `NO`.

## Input
The first line contains n and T; the second line contains n integers. n ≤ 50000.

## Output
YES or NO.

## Sample Input
```
5 9
2 7 11 15 1
```

## Sample Output
```
YES
```

## Notes
A double loop in O(n²) times out at n=50000; with a set it is O(n). This is your first encounter with performance.
