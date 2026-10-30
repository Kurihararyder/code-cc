# d013 Reverse an Integer

**Stage 0 · Difficulty ★ · Topic: Strings, digits**

Given an integer n, print the integer obtained by reversing its digits. Do not keep leading zeros in the result; a negative number keeps its minus sign. For example 1200 → 21, -120 → -21, 0 → 0.

## Input
One integer per line (|n| < 10^18), until EOF.

## Output
One answer per line.

## Sample Input
```
123
```

## Sample Output
```
321
```

## Notes
String slicing [::-1] and int()/str() conversion.
