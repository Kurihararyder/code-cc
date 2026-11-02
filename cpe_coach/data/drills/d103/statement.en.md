# d103 Second Largest

**Stage 0 · Difficulty ★★ · Topic: Lists and sets**

Given n integers, print the second largest distinct value (for 5 5 3 the answer is 3). If there are fewer than two distinct values, print `NONE`.

## Input
The first line has n (1 ≤ n ≤ 10^5); the second line has n integers (absolute value ≤ 10^9).

## Output
One integer, or `NONE`.

## Sample Input
```
5
3 1 4 1 5
```

## Sample Output
```
4
```

## Notes
Remove duplicates with a set, then sort; do not forget the case where all numbers are equal or there is only one number.
