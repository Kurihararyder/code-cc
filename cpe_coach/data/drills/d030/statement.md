# d030 簡易銀行

**階段 0　難度 ★　主題：字串解析／狀態**

帳戶初始餘額 0。每行一個指令：`DEPOSIT x` 存入 x；`WITHDRAW x` 提領 x，若餘額不足則輸出 `INSUFFICIENT` 且餘額不變；`BALANCE` 輸出目前餘額。讀到 EOF。

## 輸入
x 為正整數（≤ 10^9）。指令最多 1000 行。

## 輸出
每個 BALANCE 與每次失敗的 WITHDRAW 輸出一行。

## 範例
輸入：
```
DEPOSIT 100
BALANCE
WITHDRAW 30
BALANCE
WITHDRAW 100
BALANCE
```
輸出：
```
100
70
INSUFFICIENT
70
```

## 這題在練什麼
模擬題的核心：讀指令、改狀態、輸出。
