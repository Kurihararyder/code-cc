# d135 Train Shunting

**Stage 2 · Difficulty ★★★ · Topic: Stack, simulation**

n cars enter a dead-end siding (a single entrance, last in first out) in the order 1, 2, …, n. Each step you may either push the next car into the siding or pop the outermost (most recently pushed) car out. Given a required departure order, decide whether it is possible. There are t test cases.

## Input
The first line has t (1 ≤ t ≤ 100); each case has two lines: n (1 ≤ n ≤ 10^5) and a permutation of 1..n (the departure order). The sum of n over all cases is ≤ 2×10^5.

## Output
Per case print `YES` or `NO`.

## Sample Input
```
3
5
5 4 3 2 1
5
1 2 3 4 5
5
3 1 2 4 5
```

## Sample Output
```
YES
YES
NO
```

## Notes
Simulate: to output x, push cars until x has entered, then check that the outermost one is x.
