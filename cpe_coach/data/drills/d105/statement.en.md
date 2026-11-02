# d105 Grade Summary

**Stage 0 · Difficulty ★★ · Topic: Dictionaries, aggregation**

The first line has n; then n lines `name subject score` (name and subject are letters without spaces, score is an integer in 0–100). A student can appear many times (different subjects). Print `name total number_of_subjects` for each student, ordered by name in dictionary (ASCII) order, uppercase before lowercase.

## Input
The first line has n (1 ≤ n ≤ 10^5), then n lines. A student never has the same subject twice.

## Output
One line per student.

## Sample Input
```
5
amy math 90
bob math 80
amy art 70
cat math 100
bob art 60
```

## Sample Output
```
amy 160 2
bob 140 2
cat 100 1
```

## Notes
Accumulate in a dict keyed by name; use sorted(d) when printing.
