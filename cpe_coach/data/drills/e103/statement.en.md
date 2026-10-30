# e103 Parking Fee

**Stage 1 · Difficulty ★★ · Topic: Time calculation**

Each line contains two times `HH:MM HH:MM` (entry and exit, on the same day, exit not earlier than entry). The first 30 minutes are free; after that every started block of 30 minutes costs 20 dollars; the fee for one visit is at most 200. Print the fee.

## Input
Read until EOF.

## Output
One integer per line.

## Sample Input
```
08:00 09:00
```

## Sample Output
```
20
```

## Notes
30, 31, 60 and 61 minutes are the boundaries.
