# d140 Minimum Total Waiting Time

**Stage 2 · Difficulty ★★ · Topic: Greedy, sorting**

One machine processes n jobs one after another; job i takes tᵢ time units and cannot be interrupted. A job's waiting time is the time elapsed before it starts (the first job waits 0). Order the jobs to minimize the sum of all waiting times and print that minimum.

## Input
The first line has n (1 ≤ n ≤ 10^5); the second has n integers (1 ≤ tᵢ ≤ 10^4).

## Output
One integer.

## Sample Input
```
4
3 1 4 2
```

## Sample Output
```
10
```

## Notes
Exchange argument: putting a short job earlier makes every later job wait for it fewer times.
