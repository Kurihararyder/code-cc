# d123 Clock Angle

**Stage 1 · Difficulty ★★ · Topic: Time and angles**

Each line is a 24-hour time `hh:mm`. Viewed on an analog 12-hour clock, what is the smaller angle between the hour hand and the minute hand, in degrees, printed with exactly one decimal digit? The hour hand moves 0.5° per minute and the minute hand 6° per minute; at 12:00 the hands coincide.

## Input
Each line `hh:mm` (00:00–23:59), until EOF.

## Output
One number per line with exactly one digit after the decimal point (always x.0 or x.5).

## Sample Input
```
03:00
```

## Sample Output
```
90.0
```

## Notes
Compute each hand's angle from 12 o'clock, take the absolute difference, and if it exceeds 180° use 360 minus it.
