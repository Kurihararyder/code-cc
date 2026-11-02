# d190 Prefix Similarity Sum

**Stage 4 · Difficulty ★★★ · Topic: Strings, Z function**

For every suffix s[i..] of a string s (i from 0; i = 0 is s itself) compute its longest common prefix with s, and print the sum of these lengths. For `ababa` the lengths are 5, 0, 3, 0, 1, total 9.

## Input
One line of lowercase letters (1 ≤ length ≤ 2×10^5).

## Output
One integer.

## Sample Input
```
ababa
```

## Sample Output
```
9
```

## Notes
The Z function: z[i] is the longest common prefix of s[i..] and s; using the rightmost known interval [l, r] it is computed in O(n), while brute-force comparison is O(n²).
