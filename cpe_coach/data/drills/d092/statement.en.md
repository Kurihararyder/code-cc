# d092 Stone Game

**Stage 4 · Difficulty ★★★ · Topic: Game DP**

A pile has n stones. Two players alternate; in each move a player must remove a number of stones that belongs to the given set S (a number larger than what remains cannot be chosen). A player who cannot move loses. Print `WIN` if the first player wins, otherwise `LOSE`.

## Input
The first line contains k and q (k ≤ 10, q ≤ 1000); the second line contains k positive integers S; then q lines, each with one n (0 ≤ n ≤ 10^6).

## Output
One line per query.

## Sample Input
```
3 5
1 3 4
0 1 2 3 7
```

## Sample Output
```
LOSE
WIN
LOSE
WIN
LOSE
```

## Notes
Looking for a period is also a valid approach.
