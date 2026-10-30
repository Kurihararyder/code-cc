# d053 Sliding Window Maximum

**Stage 2 · Difficulty ★★★ · Topic: deque, monotonic queue**

Given an array of length n and a window size k, print the maximum of every window of k consecutive elements (n-k+1 values), separated by spaces.

## Input
The first line contains n and k; the second line contains n integers. n ≤ 40000.

## Output
One line.

## Sample Input
```
8 3
1 3 -1 -3 5 3 6 7
```

## Sample Output
```
3 3 5 5 6 7
```

## Notes
The O(nk) brute force times out when k is large. Each element enters and leaves the deque at most once → O(n).
