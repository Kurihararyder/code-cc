# d048 Pairs With Sum at Most K

**Stage 2 · Difficulty ★★ · Topic: Sorting + two pointers**

Given n integers and K, count the pairs i<j with a[i]+a[j] ≤ K.

## Input
The first line contains n and K; the second line contains n integers. n ≤ 40000, |a|, |K| ≤ 10^9.

## Output
One integer.

## Sample Input
```
5 6
1 2 3 4 5
```

## Sample Output
```
6
```

## Notes
Checking all pairs in O(n²) needs 8×10^8 operations at n=40000, which always times out in Python.
