# d120 Word Search

**Stage 1 · Difficulty ★★ · Topic: Grid scanning, 8 directions**

The first line has r c, followed by r lines of c lowercase letters, and finally a word w (length at least 2). Count the (start cell, direction) pairs that spell w when read in a straight line, in any of the eight directions (including diagonals) without leaving the grid. The same start with different directions counts separately; when w is a palindrome both opposite directions count.

## Input
1 ≤ r, c ≤ 50, 2 ≤ |w| ≤ 50.

## Output
One integer.

## Sample Input
```
3 4
abca
bcab
cabc
abc
```

## Sample Output
```
4
```

## Notes
Try every cell and every direction; stop at the first mismatch or when leaving the grid.
