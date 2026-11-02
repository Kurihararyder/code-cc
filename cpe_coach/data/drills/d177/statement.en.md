# d177 Fast Modular Exponentiation

**Stage 3 · Difficulty ★★ · Topic: Number theory, fast exponentiation**

For each triple a b m print aᵇ mod m. b can be huge (up to 10^18) so you cannot multiply one by one. When m = 1 the answer is 0.

## Input
Each line has three integers a b m (0 ≤ a ≤ 10^9, 0 ≤ b ≤ 10^18, 1 ≤ m ≤ 10^9), at most 1000 lines, until EOF. By convention 0⁰ = 1 (then reduced mod m).

## Output
One integer per line.

## Sample Input
```
2 10 1000
```

## Sample Output
```
24
```

## Notes
Split b in binary: square a at every step and multiply it into the answer on 1 bits, reducing mod m each time. Write the loop yourself (do not use the built-in three-argument pow) for practice.
