# d054 Activity Selection

**Stage 2 · Difficulty ★★ · Topic: Greedy**

There are n activities; activity [s, e) has a start and an end time (the resource is free at time e, so an activity starting exactly at e is allowed). You can attend only one activity at a time. What is the maximum number of activities you can attend?

## Input
The first line contains n (≤ 30000); then n lines `s e` (0 ≤ s < e ≤ 10^9).

## Output
One integer.

## Sample Input
```
4
1 3
2 4
3 5
0 1
```

## Sample Output
```
3
```

## Notes
The key to a greedy solution is *what to sort by*. A wrong choice (for example the start time) gives wrong answers.
