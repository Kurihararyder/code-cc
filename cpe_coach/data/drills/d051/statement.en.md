# d051 Josephus Problem

**Stage 2 · Difficulty ★★ · Topic: queue, patterns**

n people numbered 1..n stand in a circle. Counting starts at person 1; the person who counts k leaves the circle, and the next person starts counting from 1 again, until one person remains. Print the number of the last remaining person.

## Input
Each line is `n k` (1 ≤ n ≤ 10^6, 1 ≤ k ≤ 10^9), until EOF, at most 10 lines.

## Output
One number per line.

## Sample Input
```
5 2
```

## Sample Output
```
3
```

## Notes
Direct simulation is O(nk) and times out; with a recurrence it is O(n).
