# d122 Days Between Two Dates

**Stage 1 · Difficulty ★★ · Topic: Date arithmetic**

Each line has six integers `y1 m1 d1 y2 m2 d2` describing two dates (valid, years 1900–2100, ordinary leap-year rules). Print the absolute number of days between them.

## Input
Until EOF.

## Output
One integer per line.

## Sample Input
```
2024 1 1 2024 12 31
```

## Sample Output
```
365
```

## Notes
You may subtract two datetime.date values, but also try it by hand: convert each date to 'days since a fixed base day' and subtract.
