# d168 Longest Palindromic Subsequence

**Stage 3 · Difficulty ★★★ · Topic: Interval DP, palindromes**

Given a string, delete some characters (the remaining ones keep their relative order) so that the rest is a palindrome. What is the largest number of characters that can remain?

## Input
One line of lowercase letters (length 1 to 1000).

## Output
One integer.

## Sample Input
```
bbbab
```

## Sample Output
```
4
```

## Notes
dp[i][j] = answer for the interval s[i..j]: equal end characters give dp[i+1][j−1] + 2, otherwise the larger of dp[i+1][j] and dp[i][j−1].
