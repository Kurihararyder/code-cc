# d016 Caesar Cipher

**Stage 0 · Difficulty ★ · Topic: Strings**

The first line contains an integer k (0 ≤ k ≤ 1000); the second line contains a piece of text. Shift every English letter forward by k positions (after z comes a; handle upper and lower case separately); all other characters stay unchanged. Print the result.

## Input
Two lines: k; then the text (length ≤ 1000, may contain spaces).

## Output
One line: the encrypted text.

## Sample Input
```
3
Hello, World!
```

## Sample Output
```
Khoor, Zruog!
```

## Notes
ord/chr and the remainder operator for wrapping around.
