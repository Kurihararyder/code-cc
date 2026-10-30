# d062 Lexicographically Smallest Topological Order

**Stage 3 · Difficulty ★★★ · Topic: Topological sort**

A directed graph has n nodes and m edges `u v`, meaning u must come before v. Print the lexicographically smallest valid order; print -1 if the graph has a cycle.

## Input
The first line contains n and m (n ≤ 20000, m ≤ 40000), followed by m lines. Multiple edges may occur.

## Output
One line with n numbers, or -1.

## Sample Input
```
4 3
1 2
1 3
3 4
```

## Sample Output
```
1 2 3 4
```

## Notes
An edge with u==v would form a cycle; the data avoids it.
