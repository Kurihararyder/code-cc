# d131 Shortest Subarray

**Stage 2 · Difficulty ★★ · Topic: Two pointers, sliding window**

Given n positive integers and a target S, find the shortest contiguous subarray whose sum is at least S and print its length; if even the whole array sums to less than S, print 0.

## Input
The first line has n S (1 ≤ n ≤ 10^5, 1 ≤ S ≤ 10^9); the second has n positive integers (1 ≤ aᵢ ≤ 10^4).

## Output
One integer.

## Sample Input
```
6 7
2 3 1 2 4 3
```

## Sample Output
```
2
```

## Notes
All numbers are positive, so moving the right end right increases the sum and moving the left end right decreases it — that is why two pointers work.
