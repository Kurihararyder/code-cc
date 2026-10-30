# e203 Generate Parentheses

**Stage 2 · Difficulty ★★ · Topic: Backtracking**

Given n (1 ≤ n ≤ 8), print all valid strings made of n pairs of parentheses in lexicographic order (`(` is smaller than `)`), one per line.

## Input
One integer.

## Output
One valid string per line.

## Sample Input
```
2
```

## Sample Output
```
(())
()()
```

## Notes
Do not generate all 2^(2n) strings and filter them; prune while generating.
