# d045 24-Hour to 12-Hour Clock

**Stage 1 · Difficulty ★ · Topic: String formatting**

Given `hh:mm:ss` in 24-hour format, convert it to the 12-hour format `hh:mm:ss AM` or `hh:mm:ss PM`. 00:xx:xx becomes `12:xx:xx AM` and 12:xx:xx becomes `12:xx:xx PM`. Keep hh as two digits.

## Input
Read until EOF.

## Output
One result per line.

## Sample Input
```
13:05:09
```

## Sample Output
```
01:05:09 PM
```

## Notes
The boundary times (midnight and noon) are the point of this problem.
