# d142 Enumerating Combinations

**Stage 2 · Difficulty ★★ · Topic: Recursion, combinations**

Given n and k, print all combinations of k distinct numbers chosen from 1..n in lexicographic order (numbers inside a combination ascending, separated by spaces, one combination per line).

## Input
One line with two integers n k (1 ≤ k ≤ n ≤ 10).

## Output
C(n,k) lines.

## Sample Input
```
4 2
```

## Sample Output
```
1 2
1 3
1 4
2 3
2 4
3 4
```

## Notes
Pass 'the smallest number you may still choose' down the recursion so that no combination is produced twice in different orders.
