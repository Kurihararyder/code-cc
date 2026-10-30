# d019 Remove Duplicates

**Stage 0 · Difficulty ★ · Topic: Lists, sets**

Given n integers, keep the first occurrence of every number, delete the later duplicates, and print the rest in the original order.

## Input
The first line contains n (≤ 10^5); the second line contains n integers.

## Output
One line.

## Sample Input
```
7
1 2 1 3 2 4 4
```

## Sample Output
```
1 2 3 4
```

## Notes
Lookup in a set is O(1); with a list it becomes very slow for large inputs.
