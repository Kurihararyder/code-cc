# e202 Job Scheduling

**Stage 2 · Difficulty ★★★ · Topic: Greedy + heap**

There are n jobs, each takes 1 unit of time and must be finished no later than the end of time unit d (time starts at 1; the job done in time unit t needs t ≤ d). Finishing it yields profit p. Only one job can be done per time unit. Find the maximum total profit.

## Input
The first line contains n (≤ 30000); then n lines `d p` (1 ≤ d ≤ 10^9, 1 ≤ p ≤ 10^9).

## Output
One integer.

## Sample Input
```
4
2 100
1 19
2 27
1 25
```

## Sample Output
```
127
```

## Notes
A classic of 'greedy with regret'.
