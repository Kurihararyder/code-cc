# d099 Parcel Shipping Fee

**Stage 0 · Difficulty ★ · Topic: Conditions, tiered pricing**

A parcel weighs w grams. Up to and including 1000 grams the fee is 60. For the weight above 1000 grams, charge 25 for every 500 grams, and a partial block of less than 500 grams is charged as a full block. Print the fee.

## Input
One integer w per line (1 ≤ w ≤ 10^6), until EOF.

## Output
One integer per line.

## Sample Input
```
1500
```

## Sample Output
```
85
```

## Notes
'A partial block counts as a whole one' means rounding up: `(x + 499) // 500`.
