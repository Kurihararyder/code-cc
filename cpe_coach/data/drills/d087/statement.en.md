# d087 Range Minimum

**Stage 4 · Difficulty ★★★ · Topic: Sparse table / segment tree**

Given an array of length n and q queries `l r` (1-indexed), print min(a[l..r]).

## Input
The first line contains n and q (≤ 15000); the second line contains n integers; then q lines.

## Output
One line per query.

## Sample Input
```
5 3
5 2 4 7 1
1 3
2 5
4 4
```

## Sample Output
```
2
1
7
```

## Notes
Here n is small, so brute-force min(a[l-1:r]) passes; real exams scale n and q to 10^5 and beyond, so practise an O(1)-query method.
