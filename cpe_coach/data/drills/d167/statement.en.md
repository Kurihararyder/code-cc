# d167 Edit Distance

**Stage 3 · Difficulty ★★★ · Topic: String DP, edit distance**

Given strings a and b, one operation on a is inserting a character, deleting a character, or replacing a character by another. What is the minimum number of operations to turn a into b?

## Input
Two lines, each a string of lowercase letters (length 1 to 1000).

## Output
One integer.

## Sample Input
```
horse
ros
```

## Sample Output
```
3
```

## Notes
dp[i][j] = fewest operations turning the first i characters of a into the first j of b; equal last characters give dp[i−1][j−1], otherwise take the minimum of the three operations plus 1.
