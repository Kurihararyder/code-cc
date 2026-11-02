# d189 Pattern Occurrences

**Stage 4 · Difficulty ★★★ · Topic: Strings, KMP**

Given a text T and a pattern P, count how many times P occurs in T (occurrences may overlap: `aa` occurs 3 times in `aaaa`).

## Input
Two lines: T and then P, both lowercase letters only, 1 ≤ |P| ≤ |T| ≤ 2×10^5.

## Output
One integer.

## Sample Input
```
ababab
ab
```

## Sample Output
```
3
```

## Notes
KMP: compute P's failure function, then let each character of T advance the match length; when it reaches |P| count one and fall back along the failure function.
