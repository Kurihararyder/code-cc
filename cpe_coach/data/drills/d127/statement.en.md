# d127 Meeting Rooms

**Stage 2 · Difficulty ★★ · Topic: Heap, sweep line**

There are n meetings; meeting i starts at sᵢ and ends at eᵢ (sᵢ < eᵢ). A room can host one meeting at a time, and it becomes free the moment a meeting ends, so a meeting ending at eᵢ may share a room with one starting at sⱼ = eᵢ. What is the minimum number of rooms?

## Input
The first line has n (1 ≤ n ≤ 10^5); then n lines `s e` (0 ≤ s < e ≤ 10^9).

## Output
One integer.

## Sample Input
```
3
0 30
5 10
15 20
```

## Sample Output
```
2
```

## Notes
Sort by start time; keep a min-heap of the end times of rooms in use: when a meeting starts and the heap top is ≤ its start time, reuse that room (pop). The final heap size is the answer.
