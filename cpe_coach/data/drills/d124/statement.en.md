# d124 Postfix Evaluation

**Stage 1 · Difficulty ★★ · Topic: Stack, expressions**

Each line is a postfix expression: integers and `+` `-` `*` separated by spaces. Process the symbols in order: push numbers on a stack; for an operator pop the top two values b (pushed later) and a (pushed earlier), compute a op b and push the result. Print the single value left on the stack. The expression is guaranteed to be valid.

## Input
At most 1000 symbols per line, integers 0–10^9, until EOF.

## Output
One integer per line (possibly negative or very large).

## Sample Input
```
3 4 + 2 *
```

## Sample Output
```
14
```

## Notes
The order 'the earlier pushed one is the left operand' matters for subtraction.
