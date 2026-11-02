# d119 Rolling a Die

**Stage 1 · Difficulty ★★ · Topic: Simulation, state**

A die (opposite faces sum to 7) starts with top 1, north 2, east 3, west 4, south 5, bottom 6. Each line is a string of commands made of `N`, `S`, `E`, `W`, rolling the die one cell to the north, south, east or west in order (rolling north moves the old top face to the north side and brings the old south face to the top; other directions work the same way). Print the top face after the commands of each line. An empty line means no rolls: the answer is 1.

## Input
Each line is a command string (length ≤ 10^5, possibly empty), until EOF.

## Output
One integer per line.

## Sample Input
```
N
```

## Sample Output
```
5
```

## Notes
Track three faces (top, north, east); the other three are 7 minus them. Each roll just reassigns the values.
