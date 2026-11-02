# d193 Nim Game

**Stage 4 · Difficulty ★★ · Topic: Games, Nim**

There are t games. In each game there are n piles of stones; two players alternately take at least 1 stone from a single pile (possibly the whole pile) and whoever takes the last stone wins. Both play optimally; print `FIRST` if the first player wins, otherwise `SECOND`.

## Input
The first line has t (1 ≤ t ≤ 1000); each game has two lines: n (1 ≤ n ≤ 1000) and n non-negative integers (≤ 10^9).

## Output
One line per game.

## Sample Input
```
3
3
1 2 3
2
3 4
1
5
```

## Sample Output
```
SECOND
FIRST
FIRST
```

## Notes
The first player wins exactly when the XOR of all pile sizes is non-zero (Bouton's theorem). Verify it by brute force on small examples yourself.
