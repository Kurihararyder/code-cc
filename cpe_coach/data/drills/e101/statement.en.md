# e101 Score Ranking

**Stage 1 · Difficulty ★★ · Topic: Sorting, output format**

The first line contains t. Each case starts with n, followed by n lines `name score`. Sort by score from high to low, ties by name in lexicographic order, and print the rank: students with equal scores share a rank, and the next rank skips numbers (for example 1, 1, 3).

For every case first print a line `Case #k:`, then one line per student: `rank name score`. **Print one blank line between consecutive cases, but none after the last case.**

## Input
t ≤ 50, n ≤ 100; a name is English letters without whitespace; a score is an integer from 0 to 100.

## Output
See the statement.

## Sample Input
```
2
3
bob 90
alice 90
carol 80
2
z 0
y 100
```

## Sample Output
```
Case #1:
1 alice 90
1 bob 90
3 carol 80

Case #2:
1 y 100
2 z 0
```

## Notes
Combines I/O formats, sorting and counting from the earlier problems.
