# d083 Shortest Period

**Stage 4 · Difficulty ★★★ · Topic: Strings (KMP failure function)**

Given a string s, find the smallest p (1 ≤ p ≤ |s|) such that s is obtained by repeating s[0:p] (the last repetition may be incomplete).

## Input
One lowercase string per line (length ≤ 2×10^5), until EOF, at most 5 lines.

## Output
One integer per line.

## Sample Input
```
abcabcab
```

## Sample Output
```
3
```

## Notes
Trying every p by brute force is O(n²). This is a classic application of KMP.
