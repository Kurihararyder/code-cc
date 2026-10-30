# d030 Simple Bank

**Stage 0 · Difficulty ★ · Topic: Parsing, state**

An account starts with balance 0. Each line is one command: `DEPOSIT x` adds x; `WITHDRAW x` removes x, but if the balance is insufficient print `INSUFFICIENT` and leave the balance unchanged; `BALANCE` prints the current balance. Read until EOF.

## Input
x is a positive integer (≤ 10^9). There are at most 1000 commands.

## Output
One line for every BALANCE and for every failed WITHDRAW.

## Sample Input
```
DEPOSIT 100
BALANCE
WITHDRAW 30
BALANCE
WITHDRAW 100
BALANCE
```

## Sample Output
```
100
70
INSUFFICIENT
70
```

## Notes
The core of simulation problems: read a command, change the state, print.
