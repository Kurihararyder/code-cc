# d136 K-th Largest in a Stream

**Stage 2 · Difficulty ★★ · Topic: Heaps**

Numbers arrive one by one. Starting from the k-th number, after each arrival print the k-th largest value among all numbers received so far (duplicates count separately: in 5 5 3 the 2nd largest is 5).

## Input
The first line has n k (1 ≤ k ≤ n ≤ 2×10^5); the second has n integers (absolute value ≤ 10^9).

## Output
One line of n−k+1 integers separated by spaces.

## Sample Input
```
6 3
4 5 8 2 9 1
```

## Sample Output
```
4 4 5 5
```

## Notes
Keep a min-heap of size k: its top is the k-th largest. Replace the top only when the new number is larger.
