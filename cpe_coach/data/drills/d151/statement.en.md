# d151 Largest Friend Circle

**Stage 3 · Difficulty ★★ · Topic: Union-find, group sizes**

At first there are n people, each in a group of their own. Then m events happen in order: 'a and b become friends' (their two groups merge into one; if they are already in the same group nothing changes). After every event print the size of the largest group so far.

## Input
The first line has n m (1 ≤ n ≤ 10^5, 1 ≤ m ≤ 10^5); then m lines `a b` (1 ≤ a, b ≤ n, a = b possible).

## Output
m lines, one integer after each event.

## Sample Input
```
5 4
1 2
3 4
2 3
5 5
```

## Sample Output
```
2
2
4
4
```

## Notes
Union-find with the size of every root and a global maximum; a merge can only increase the maximum, so nothing needs to be recomputed.
