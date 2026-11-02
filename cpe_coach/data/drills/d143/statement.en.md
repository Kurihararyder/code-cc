# d143 Prime Ring

**Stage 2 · Difficulty ★★★ · Topic: Backtracking, pruning**

Arrange the n numbers 1 to n in a circle so that the sum of every two neighbours (including the last and the first) is prime. For n = 1 the single number is its own neighbour (sum 2, prime), so the answer is 1; for odd n ≥ 3 the answer is 0. Fix 1 in the first position and count the arrangements (mirror images in clockwise/counter-clockwise order count as different).

## Input
One integer n per line (1 ≤ n ≤ 14), at most 14 lines, until EOF.

## Output
One integer per line.

## Sample Input
```
4
```

## Sample Output
```
2
```

## Notes
Place numbers position by position and back up as soon as it fails (pruning): the new number must sum to a prime with the previous one, and finally the last must also sum to a prime with 1.
