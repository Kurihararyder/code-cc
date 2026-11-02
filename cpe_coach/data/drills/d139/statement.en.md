# d139 Lifeboats

**Stage 2 · Difficulty ★★ · Topic: Greedy, two pointers**

n people cross a river, person i weighs wᵢ. Each boat carries at most 2 people with a total weight not exceeding W (everyone can be carried alone). What is the minimum number of boats?

## Input
The first line has n W (1 ≤ n ≤ 10^5, 1 ≤ W ≤ 10^9); the second has n integers (1 ≤ wᵢ ≤ W).

## Output
One integer.

## Sample Input
```
4 5
3 2 2 1
```

## Sample Output
```
2
```

## Notes
Sort, then pair the heaviest with the lightest: if they fit together they leave together, otherwise the heaviest goes alone.
