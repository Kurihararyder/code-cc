# d089 Strongly Connected Components

**Stage 4 · Difficulty ★★★★ · Topic: SCC**

A directed graph has n nodes and m edges. Print the number of strongly connected components and the size of the largest one.

## Input
The first line contains n and m (n ≤ 10000, m ≤ 30000); then m lines `u v`.

## Output
One line: count largest-size.

## Sample Input
```
5 5
1 2
2 3
3 1
3 4
4 5
```

## Sample Output
```
3 3
```

## Notes
Large cyclic graphs make a recursive DFS crash in Python.
