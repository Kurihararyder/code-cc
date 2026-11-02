# d115 Next Palindrome

**Stage 1 · Difficulty ★★ · Topic: Strings, palindromes**

For each positive integer n print the smallest palindrome that is strictly greater than n (a palindrome reads the same forwards and backwards, e.g. 121, 7, 1331).

## Input
One integer n per line (1 ≤ n ≤ 10^18), until EOF, at most 1000 lines.

## Output
One integer per line.

## Sample Input
```
120
```

## Sample Output
```
121
```

## Notes
Do not try n+1, n+2, … one by one (it would never finish for n up to 10^18): mirror the *left half* of the number instead.
