# d138 Interval Cover

**Stage 2 · Difficulty ★★★ · Topic: Greedy, interval cover**

There are n closed intervals [lᵢ, rᵢ] on a line. Choose the fewest intervals so that every point of the segment [0, L] is covered by at least one chosen interval (touching endpoints count as covering). Print the minimum number, or -1 if impossible.

## Input
The first line has L n (1 ≤ L ≤ 10^9, 1 ≤ n ≤ 10^5); then n lines `l r` (0 ≤ l < r ≤ 10^9).

## Output
One integer.

## Sample Input
```
10 3
0 5
4 10
3 7
```

## Sample Output
```
2
```

## Notes
Greedy: with everything up to cur covered, among all intervals with l ≤ cur pick the one with the largest r; sort the intervals by l first.
