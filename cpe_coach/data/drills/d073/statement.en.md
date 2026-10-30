# d073 Matrix Chain Multiplication

**Stage 3 · Difficulty ★★★ · Topic: Interval DP**

n matrices are multiplied; matrix i has size p[i-1]×p[i]. Find the parenthesisation that minimises the number of scalar multiplications and print that number.

## Input
The first line contains n (≤ 100); the second line contains n+1 integers p[0..n] (≤ 100).

## Output
One integer.

## Sample Input
```
3
10 30 5 60
```

## Sample Output
```
4500
```

## Notes
The loop order of interval DP: enumerate the *length* first.
