# d137 Running Median

**Stage 2 · Difficulty ★★★ · Topic: Two heaps, running median**

Numbers arrive one by one. After each arrival print the median of all numbers so far, where for an even count the lower median is used (the ⌈i/2⌉-th smallest of the first i numbers).

## Input
The first line has n (1 ≤ n ≤ 10^5); the second has n integers (absolute value ≤ 10^9).

## Output
One line of n integers separated by spaces.

## Sample Input
```
5
5 2 8 1 9
```

## Sample Output
```
5 2 5 2 5
```

## Notes
Keep the smaller half in a max-heap and the larger half in a min-heap, with the max-heap never smaller than the min-heap.
