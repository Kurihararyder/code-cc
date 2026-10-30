# d052 Merge Cost

**Stage 2 · Difficulty ★★ · Topic: heap, greedy**

There are n positive integers. In each step pick two numbers and merge them into their sum; the cost of the step is that sum. Repeat until one number is left. Find the minimum total cost.

## Input
The first line contains n (≤ 50000); the second line contains n positive integers (≤ 10^9). For n=1 the cost is 0.

## Output
One integer.

## Sample Input
```
4
1 2 3 4
```

## Sample Output
```
19
```

## Notes
Sorting before every step is O(n² log n). UVA 10954 is the same problem.
