# d152 Minimum Semesters

**Stage 3 · Difficulty ★★ · Topic: Topological sort, layers**

There are n courses and m prerequisites `a b` meaning a must be finished before b (not in the same semester). In each semester you may take any number of courses whose prerequisites were all completed in earlier semesters. What is the minimum number of semesters to finish everything? Print -1 if the prerequisites contain a cycle (a course being its own prerequisite counts as a cycle).

## Input
The first line has n m (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2×10^5), then m lines `a b` (repeats may occur).

## Output
One integer.

## Sample Input
```
4 3
1 2
2 3
1 4
```

## Sample Output
```
3
```

## Notes
The answer is the number of vertices on the longest path of the DAG; Kahn's algorithm processed layer by layer counts the semesters.
