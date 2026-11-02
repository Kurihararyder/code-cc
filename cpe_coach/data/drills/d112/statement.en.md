# d112 Morse Decoder

**Stage 1 · Difficulty ★★ · Topic: String mapping, dict**

Translate Morse messages back into text. Each line is one message: the codes of letters and digits are separated by one space, and words are separated by ` / ` (space, slash, space). Print the decoded text (uppercase letters and digits) with a single space between words. Code table: A .-, B -..., C -.-., D -.., E ., F ..-., G --., H ...., I .., J .---, K -.-, L .-.., M --, N -., O ---, P .--., Q --.-, R .-., S ..., T -, U ..-, V ...-, W .--, X -..-, Y -.--, Z --.., 0 -----, 1 .----, 2 ..---, 3 ...--, 4 ....-, 5 ....., 6 -...., 7 --..., 8 ---.., 9 ----..

## Input
One message per line (never empty; at most 1000 symbols per line), until EOF.

## Output
One result per line.

## Sample Input
```
.... . .-.. .-.. --- / .-- --- .-. .-.. -..
```

## Sample Output
```
HELLO WORLD
```

## Notes
Build the code table as a dict (code → character) first, then split the message.
