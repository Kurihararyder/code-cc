# d129 Cutting Ropes

**Stage 2 · Difficulty ★★★ · Topic: Binary search on the answer**

There are n ropes with integer lengths a₁…aₙ. You must cut k pieces of the same integer length (each rope may give several pieces; leftovers are discarded). What is the largest possible common length? If not even length 1 gives k pieces, print 0.

## Input
The first line has n k (1 ≤ n ≤ 10^5, 1 ≤ k ≤ 10^9); the second has n integers (1 ≤ aᵢ ≤ 10^9).

## Output
One integer.

## Sample Input
```
4 11
802 743 457 539
```

## Sample Output
```
200
```

## Notes
The larger the length L, the fewer pieces you can cut (monotone), so binary search on L; the check is `sum(a // L) >= k`.
