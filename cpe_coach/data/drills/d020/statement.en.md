# d020 Word Frequency

**Stage 0 · Difficulty ★ · Topic: dict, sorting**

Read several lines of text. Words are separated by whitespace (case-sensitive). Print every distinct word and how many times it occurs, ordered by count from large to small; words with the same count are ordered alphabetically (by code point). Each line has the form: `word count`.

## Input
Read until EOF. The total number of words is ≤ 10^5.

## Output
One line per distinct word.

## Sample Input
```
a b a
c b a
```

## Sample Output
```
a 3
b 2
c 1
```

## Notes
Counting with a dict and sorting with a key function: the basics of every later problem.
