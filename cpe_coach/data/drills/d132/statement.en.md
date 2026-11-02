# d132 Longest Substring Without Repeats

**Stage 2 · Difficulty ★★ · Topic: Sliding window, sets**

For each line, print the length of the longest contiguous substring that contains no repeated character.

## Input
One string per line (1 ≤ length ≤ 10^5, visible ASCII characters without spaces), until EOF, at most 10 lines.

## Output
One integer per line.

## Sample Input
```
abcabcbb
```

## Sample Output
```
3
```

## Notes
Window [l, r]: add the character at r; if it is already inside the window, move l to just after its previous position.
