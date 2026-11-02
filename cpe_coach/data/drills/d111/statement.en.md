# d111 BMI

**Stage 1 · Difficulty ★★ · Topic: Float formatting, classification**

Each line has two integers w h (weight w kg, height h cm); BMI = w ÷ (h/100)². Print `BMI category`: the BMI rounded to one decimal place, and a category based on the BMI *before* rounding: below 18.5 is `UNDER`, from 18.5 up to below 24 is `NORMAL`, from 24 up to below 27 is `OVER`, 27 or more is `OBESE`. The data guarantees no BMI falls exactly on a rounding boundary of the second decimal digit.

## Input
Each line `w h` (30 ≤ w ≤ 200, 100 ≤ h ≤ 220), until EOF.

## Output
One `BMI category` per line, e.g. `22.9 NORMAL`.

## Sample Input
```
70 175
```

## Sample Output
```
22.9 NORMAL
```

## Notes
The category uses the raw value while the display uses the rounded one — they can disagree (a BMI of 23.96 prints as 24.0 but is still NORMAL).
