# d166 Number of Longest Increasing Subsequences

**Stage 3 · Difficulty ★★★ · Topic: Sequence DP, counting**

Given a sequence of n integers there may be many longest strictly increasing subsequences (subsequences with different positions are different). Print the longest length and the number of subsequences achieving it, modulo 1000000007.

## Input
The first line has n (1 ≤ n ≤ 2000); the second has n integers (absolute value ≤ 10^9).

## Output
One line: length count.

## Sample Input
```
5
1 3 5 4 7
```

## Sample Output
```
4 2
```

## Notes
For every position i keep (the longest length ending at i: L[i], the number of ways: C[i]); a longer candidate replaces, an equal-length candidate adds.
