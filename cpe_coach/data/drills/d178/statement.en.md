# d178 Modular Inverse

**Stage 3 · Difficulty ★★★ · Topic: Number theory, modular inverse**

For each pair a m find x (0 ≤ x < m) with a·x ≡ 1 (mod m), or print -1 if none exists (a and m are not coprime).

## Input
Each line has two integers a m (1 ≤ a ≤ 10^9, 2 ≤ m ≤ 10^9), at most 1000 lines, until EOF. m need not be prime.

## Output
One integer per line.

## Sample Input
```
3 11
```

## Sample Output
```
4
```

## Notes
Use the extended Euclidean algorithm: find x, y with a·x + m·y = gcd(a, m); when gcd = 1, x mod m is the answer.
