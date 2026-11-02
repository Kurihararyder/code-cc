# d102 Reverse Each Word

**Stage 0 · Difficulty ★ · Topic: Strings, split and join**

Each line is a text made of words separated by exactly one space (no leading or trailing spaces). Reverse every word individually; the order of the words and the spaces stay the same.

## Input
Each line has length ≤ 1000 and contains only letters, digits and single spaces, until EOF.

## Output
One result per line.

## Sample Input
```
hello world
```

## Sample Output
```
olleh dlrow
```

## Notes
Split the line with `line.split()` and join the words back with `' '.join(...)`.
