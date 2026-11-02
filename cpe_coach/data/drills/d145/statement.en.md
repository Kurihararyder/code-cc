# d145 Listing Subsets

**Stage 2 · Difficulty ★★ · Topic: Bitmasks, subsets**

Read n and print all subsets of {1,2,…,n} in increasing order of their bitmask: bit i−1 (counting from the lowest bit) of mask m being 1 means element i belongs to the subset. One subset per line, written `{a,b,c}` (elements ascending, no spaces after the commas); the empty set is `{}`.

## Input
One integer n (0 ≤ n ≤ 10).

## Output
2ⁿ lines.

## Sample Input
```
3
```

## Sample Output
```
{}
{1}
{2}
{1,2}
{3}
{1,3}
{2,3}
{1,2,3}
```

## Notes
`for m in range(1 << n)`, and test bit i with `m >> i & 1`.
