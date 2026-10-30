# e401 Subarrays With Sum K

**Stage 4 · Difficulty ★★ · Topic: Prefix sums + dict**

Given n integers (possibly negative) and K, count the contiguous subarrays whose sum is exactly K.

## Input
The first line contains n and K (n ≤ 20000); the second line contains n integers (|a| ≤ 1000).

## Output
One integer.

## Sample Input
```
5 5
1 2 3 -1 4
```

## Sample Output
```
2
```

## Notes
Negative numbers break two pointers; use prefix sums with a hash map.
