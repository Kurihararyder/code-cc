# d191 Prefix Counting

**Stage 4 · Difficulty ★★★ · Topic: Strings, prefix queries**

Given n words (duplicates count separately) and q query strings, print for each query how many words start with it (a word equal to the query counts too).

## Input
The first line has n q (1 ≤ n, q ≤ 5×10^4); then n lines with one word each and q lines with one query string each, all lowercase letters; the total length of all words and the total length of all queries are each ≤ 2×10^5.

## Output
One line per query.

## Sample Input
```
4 3
apple
app
apply
banana
app
b
c
```

## Sample Output
```
3
1
0
```

## Notes
After sorting the words, those starting with a given prefix form one contiguous block; binary-search its two ends. Or build a trie and store at every node how many words pass through it.
