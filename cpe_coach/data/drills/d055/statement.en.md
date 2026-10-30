# d055 Assign Cookies

**Stage 2 · Difficulty ★ · Topic: Greedy + sorting**

There are n children; child i demands a cookie of size at least g[i]. There are m cookies; cookie j has size s[j]. Each cookie goes to at most one child and each child gets at most one cookie. What is the maximum number of satisfied children?

## Input
The first line contains n and m; the second line contains n values g; the third line contains m values s. n, m ≤ 30000.

## Output
One integer.

## Sample Input
```
3 2
1 2 3
1 1
```

## Sample Output
```
1
```

## Notes
Sorting plus two pointers is the most common greedy combination.
