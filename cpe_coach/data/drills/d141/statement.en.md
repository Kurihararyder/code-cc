# d141 Tower of Hanoi

**Stage 2 · Difficulty ★★ · Topic: Recursion**

n discs of different sizes are stacked on peg A (smaller on top) and must all be moved to peg C, one disc at a time, never placing a larger disc on a smaller one; peg B may be used as temporary storage. Print the minimum number of moves and every move as `X Y` (from peg X to peg Y). The shortest solution is unique.

## Input
One integer n (1 ≤ n ≤ 10).

## Output
The first line is the minimum number of moves m (= 2ⁿ − 1), followed by m lines, one move each, such as `A C`.

## Sample Input
```
3
```

## Sample Output
```
7
A C
A B
C B
A C
B A
B C
A C
```

## Notes
Recursive idea: move the top n−1 discs to B, move the largest to C, then move the n−1 discs from B to C.
