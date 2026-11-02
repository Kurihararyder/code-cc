# d173 Minimum Palindrome Cuts

**Stage 3 · Difficulty ★★★ · Topic: DP, string partition**

Cut a string into contiguous pieces so that every piece is a palindrome. What is the minimum number of cuts? A string that is itself a palindrome needs 0 cuts.

## Input
One line of lowercase letters (length 1 to 1000).

## Output
One integer.

## Sample Input
```
aab
```

## Sample Output
```
1
```

## Notes
First precompute in O(n²) whether s[i..j] is a palindrome, then dp[j] = minimum cuts for the first j characters.
