# Verilog／SystemVerilog 軌道：從數位邏輯到 RTL、驗證與實體流程（75 週，39 個單元）

> 由 `dev/gen_course_hdl.py` 產生，不要手改；修改請編輯 `dev/course_verilog_data.py`。

這條軌道的終點是**能在公司擔任數位 IC 的設計或驗證工程師**：寫得出可合成的 RTL、做得出有覆蓋與形式證明的驗證、看得懂時序與實體報告、做過一次從 RTL 到版圖（或 FPGA）的完整流程。 每週約 10–12 小時；75 週約 17 個月。週數是估計，請依自己的進度調整。

## 狀態（誠實版）

- 練習題：本軌道用 HDLBits（外部、免費、線上判題）；25 題以名稱引用（名稱已逐一核對）。另有 **67** 題標為 *待新增*（用 iverilog 編譯＋vvp 執行測試台、比對輸出；判題器尚未實作）。
- 判題的可行性：我在開發環境實測過 iverilog 能編譯、vvp 能執行測試台，並分辨出正確與錯誤的設計；Yosys 也能執行。學員需要自己安裝這些工具。
- 作品驗收（type=project）是**人工對照驗收標準**：效能、設計品質與驗證完整度沒辦法只靠輸入輸出判斷。
- 商用 EDA（Design Compiler、PrimeTime、Innovus、Questa、VCS、Xcelium）需要授權，無法在這裡驗證；本課綱改用開源工具（Yosys、OpenSTA、OpenROAD、OpenLane、Verilator、iverilog、cocotb、SymbiYosys），概念可遷移，指令不同。完整的 UVM 需要支援它的模擬器（多為商用），UVM 單元以閱讀與對照為主。
- 介面還沒有『切換軌道』，也還沒有各自的進度；目前是課綱與驗證過的資料。

## 階段總覽

| 階段 | 週 | 名稱 | 目標 |
|---|---|---|---|
| V0 | 1–13 | 數位邏輯與第一個電路 | 能獨立寫出、模擬並除錯一個小型數位設計，並知道它能不能合成。 |
| V1 | 14–31 | RTL 設計 | 能設計資料路徑與控制、FIFO、算術電路、跨時脈域與一顆 RISC-V 處理器，寫出模擬與合成一致的程式。 |
| V2 | 32–44 | 驗證 | 能做驗證計畫、自我檢查環境、cocotb 與 SystemVerilog 驗證、斷言與形式驗證、覆蓋率與回歸。 |
| V3 | 45–59 | 合成、時序與實體流程 | 能合成、讀寫 SDC、做時序分析與收斂、低功耗與 DFT 概念，並用開源流程做到版圖或 FPGA。 |
| V4 | 60–75 | SoC、專題與職涯 | 能整合 SoC、完成處理器、加速器與下線流程三個專題，並通過面試等級的說明。 |

## 每週節奏

- **第 1 天（新概念）**：讀教材；每個概念先在紙上畫出電路，再寫 Verilog；用模擬器跑一個最小範例。
- **第 2 天（概念練習）**：做本單元前半的 HDLBits 題目；卡住先看波形，不要先看答案。
- **第 3 天（鞏固）**：做後半的題目；每題通過後用 Verilator lint 與 Yosys 再檢查一次可合成性。
- **第 4 天（實作）**：做本單元的 build 作業；先寫 testbench 再寫設計。
- **第 5 天（重寫日）**：把用過提示的題目關掉資料，從空白檔重寫；試著換一種寫法再通過。
- **第 6 天（檢核）**：單元最後一週做檢核（作品單元逐條驗收）。
- **第 7 天（休息）**：不寫程式。

## 能力標準（各階段結束時）

| 階段 | 你應該能 |
|---|---|
| V0 | 寫出並模擬組合與序列電路、狀態機與自我檢查的 testbench；知道什麼寫法不能合成 |
| V1 | 設計資料路徑與控制、FIFO、算術電路、CDC 與 RISC-V 單週期與管線處理器；通過 lint 與合成 |
| V2 | 替設計建立驗證計畫與環境（SV 或 cocotb）、斷言與形式驗證、覆蓋率與回歸；能讀懂 UVM 環境 |
| V3 | 用 Yosys 合成、寫 SDC、讀時序報告並收斂、低功耗與 DFT 的概念；用 OpenLane 走完到 GDS 或實作到 FPGA |
| V4 | 整合 SoC 與韌體、完成核心與加速器專題、走完下線流程、面試與作品集 |

## 單元

### 階段 V0：數位邏輯與第一個電路

能獨立寫出、模擬並除錯一個小型數位設計，並知道它能不能合成。

#### 單元 1：工具鏈與設計流程（第 1 週）

**目標**：能在自己的電腦上編譯、模擬、看波形，並說得出 RTL 到晶片的整條流程。

**學什麼**
- 模擬器：iverilog（事件驅動、四值邏輯 0／1／X／Z）編譯後用 vvp 執行；Verilator（週期式、預設兩值）把 RTL 轉成 C++；波形用 GTKWave 看 VCD
- 晶片設計流程：規格→架構→RTL→功能驗證→邏輯合成→擺置繞線→時序簽核→下線；每一步都有『驗證前一步』的方法
- 『模擬』與『合成』是兩件事：同一份 Verilog 可以模擬得出來卻無法合成成電路；從第一天就要用『我在畫電路』的角度寫
- 用 `verilator --lint-only -Wall` 與 `yosys` 檢查可合成性；用 git 管理每個設計與 testbench

**待新增題目**：
- `v001` 第一個模擬：給一個 AND 閘與它的測試台，讀懂輸出並修正一個故意放的錯誤

**實作作業**：
- 安裝 iverilog、Verilator、Yosys、GTKWave；寫一個 AND 閘與 testbench，產生 VCD，在 GTKWave 截圖並標出一個時間點的輸入輸出

**常見陷阱**：
- 把 Verilog 當成軟體程式：每一行都同時存在
- 只在模擬通過就以為設計正確（沒有檢查可合成性）

**自我檢查**：
- iverilog 與 Verilator 在 X／Z 的處理上差在哪？
- 為什麼『模擬通過』不代表『可以合成』？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **HDLBits：Getting Started｜Getting Started、Output Zero**
  - 熟悉網頁的編輯、提交與模擬流程
- **Harris & Harris《From Zero to One》（第 1 章）**
  - 數位系統的抽象層次、邏輯閘、電晶體層級的直覺
- **iverilog 使用說明（Getting Started）**
  - 編譯指令 `iverilog -g2012 -o sim a.v b.v`，執行 `vvp sim`
- **Verilator 使用指南：Overview 與 Lint**
  - Verilator 與事件驅動模擬器的差別；`--lint-only` 的警告類別

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 1 | HDLBits：Getting Started｜Getting Started、Output Zero<br>Harris & Harris《From Zero to One》（第 1 章）<br>iverilog 使用說明（Getting Started）<br>Verilator 使用指南：Overview 與 Lint | 模擬器：iverilog（事件驅動、四值邏輯 0／1／X／Z）編譯後用 vvp 執行；Verilator（週期式、預設兩值）把 RTL 轉成 C++；波形用 GTKWave 看 VCD<br>晶片設計流程：規格→架構→RTL→功能驗證→邏輯合成→擺置繞線→時序簽核→下線；每一步都有『驗證前一步』的方法<br>『模擬』與『合成』是兩件事：同一份 Verilog 可以模擬得出來卻無法合成成電路；從第一天就要用『我在畫電路』的角度寫<br>用 `verilator --lint-only -Wall` 與 `yosys` 檢查可合成性；用 git 管理每個設計與 testbench | `v001` | 安裝 iverilog、Verilator、Yosys、GTKWave；寫一個 AND 閘與 testbench，產生 VCD，在 GTKWave 截圖並標出一個時間點的輸入輸出<br>**單元檢核** |

**檢核**：完成這些 HDLBits 題目（1／2 題以上）：`Getting Started`、`Output Zero`

#### 單元 2：布林代數、數字系統與卡諾圖（第 2–3 週）

**目標**：能用布林代數與卡諾圖化簡邏輯，並正確處理二補數與進位制。

**學什麼**
- 布林代數定理：狄摩根、吸收、一致性；SOP／POS；真值表⇄布林式⇄邏輯閘圖
- 進位制轉換、二補數：範圍、取負、符號擴展、溢位的判斷（兩個同號相加得異號）
- 卡諾圖：2–4 變數、無關項（don't care）、質蘊含項與必要質蘊含項；化簡成最小 SOP／POS
- 組合邏輯的延遲與毛刺（glitch）的直覺：為什麼同一個函數的兩種實作時序不同

**待新增題目**：
- `v002` 二補數運算：輸入位元寬度與兩數，輸出和、差與是否溢位（測試台比對）
- `v003` 卡諾圖化簡：給真值表，輸出最小 SOP 的項數（用程式窮舉驗證答案）

**實作作業**：
- 手算並用 Verilog 驗證 5 個 4 變數函數的最小 SOP；寫一個窮舉所有輸入的 testbench 證明兩種寫法等價

**常見陷阱**：
- 卡諾圖圈群時漏掉環繞的相鄰格
- 忘了無關項可以當 0 也可以當 1

**自我檢查**：
- `~(a & b)` 與 `~a | ~b` 為什麼等價？
- 8 位元二補數能表示的範圍？–128 取負會怎樣？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Harris & Harris《Combinational Logic Design》（第 2 章）**
  - 布林方程式、化簡、組合電路的建構區塊（多工器、解碼器）、時序與毛刺
- **Harris & Harris《From Zero to One》（第 1 章）**
  - 數字系統、二補數、進位制轉換
- **HDLBits：Circuits／Combinational Logic／Basic Gates｜Wire、GND、NOR、Another gate、Two gates、More logic gates、7420 chip、Truth tables、Two-bit equality**
  - 把真值表直接寫成 assign
- **HDLBits：Circuits／Combinational Logic／Karnaugh Map to Circuit｜3-variable、4-variable、Minimum SOP and POS、Karnaugh map**
  - 卡諾圖到電路；無關項的利用

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 2 | Harris & Harris《Combinational Logic Design》（第 2 章）<br>Harris & Harris《From Zero to One》（第 1 章） | 布林代數定理：狄摩根、吸收、一致性；SOP／POS；真值表⇄布林式⇄邏輯閘圖<br>進位制轉換、二補數：範圍、取負、符號擴展、溢位的判斷（兩個同號相加得異號） | `v002` | — |
| 3 | HDLBits：Circuits／Combinational Logic／Basic Gates｜Wire、GND、NOR、Another gate、Two gates、More logic gates、7420 chip、Truth tables、Two-bit equality<br>HDLBits：Circuits／Combinational Logic／Karnaugh Map to Circuit｜3-variable、4-variable、Minimum SOP and POS、Karnaugh map | 卡諾圖：2–4 變數、無關項（don't care）、質蘊含項與必要質蘊含項；化簡成最小 SOP／POS<br>組合邏輯的延遲與毛刺（glitch）的直覺：為什麼同一個函數的兩種實作時序不同 | `v003` | 手算並用 Verilog 驗證 5 個 4 變數函數的最小 SOP；寫一個窮舉所有輸入的 testbench 證明兩種寫法等價<br>**單元檢核** |

**檢核**：完成這些 HDLBits 題目（4／5 題以上）：`Simple circuit A`、`Simple circuit B`、`Ring or vibrate?`、`Thermostat`、`Karnaugh map`

#### 單元 3：Verilog 基礎語法：線、向量與模組（第 4–5 週）

**目標**：能用 assign 與模組階層描述組合電路，掌握向量與運算子。

**學什麼**
- `wire` 與 `reg`（reg 不一定是暫存器）；SystemVerilog 的 `logic`；向量 `[7:0]`、位元選取、部分選取 `a[3:0]`、`a[i +: 4]`
- 運算子：位元（& | ^ ~）、邏輯（&& || !）、縮減（&a、|a、^a）、串接 `{a, b}`、重複 `{4{a}}`、條件 `? :`；位元與邏輯運算的差別
- 模組：埠宣告（ANSI 風格）、依位置或依名稱連接（優先用名稱）、階層、向量埠
- 隱含宣告陷阱：未宣告的名稱會變成 1 位元的 wire；用 `` `default_nettype none `` 讓錯誤現形

**待新增題目**：
- `v004` 向量重排：輸入 32 位元，輸出位元組反轉（byte swap）與位元反轉
- `v005` 階層加法器：用 1 位元全加器模組串成 N 位元漣波進位加法器

**實作作業**：
- 用名稱連接的方式寫一個三層階層的設計（頂層→子模組→全加器），加上 `` `default_nettype none `` 並用 Verilator lint 無警告

**常見陷阱**：
- 位置連接在改了埠順序後默默接錯
- 把位元運算子 & 當成邏輯運算子 && 用在多位元訊號上

**自我檢查**：
- `a & b` 與 `a && b` 在 a、b 為 4 位元時各得到什麼？
- 什麼是隱含宣告？怎麼讓它變成錯誤？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **HDLBits：Verilog Language／Basics｜Simple wire、Four wires、Inverter、AND gate、NOR gate、XNOR gate、Declaring wires、7458 chip**
  - assign 連續賦值；wire 宣告
- **HDLBits：Verilog Language／Vectors｜Vectors、Vectors in more detail、Vector part select、Bitwise operators、Four-input gates、Vector concatenation operator、Vector reversal 1、Replication operator、More replication**
  - 向量與部分選取；串接與重複運算子；位元運算 vs 邏輯運算
- **HDLBits：Verilog Language／Modules: Hierarchy｜Modules、Connecting ports by position、Connecting ports by name、Three modules、Modules and vectors、Adder 1、Adder 2**
  - 模組實例化與兩種連接方式
- **Harris & Harris《Hardware Description Languages》（第 4 章）**
  - HDL 概論、組合邏輯的 HDL 寫法、位元運算與運算子、階層

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 4 | HDLBits：Verilog Language／Basics｜Simple wire、Four wires、Inverter、AND gate、NOR gate、XNOR gate、Declaring wires、7458 chip<br>HDLBits：Verilog Language／Vectors｜Vectors、Vectors in more detail、Vector part select、Bitwise operators、Four-input gates、Vector concatenation operator、Vector reversal 1、Replication operator、More replication | `wire` 與 `reg`（reg 不一定是暫存器）；SystemVerilog 的 `logic`；向量 `[7:0]`、位元選取、部分選取 `a[3:0]`、`a[i +: 4]`<br>運算子：位元（& | ^ ~）、邏輯（&& || !）、縮減（&a、|a、^a）、串接 `{a, b}`、重複 `{4{a}}`、條件 `? :`；位元與邏輯運算的差別 | `v004` | — |
| 5 | HDLBits：Verilog Language／Modules: Hierarchy｜Modules、Connecting ports by position、Connecting ports by name、Three modules、Modules and vectors、Adder 1、Adder 2<br>Harris & Harris《Hardware Description Languages》（第 4 章） | 模組：埠宣告（ANSI 風格）、依位置或依名稱連接（優先用名稱）、階層、向量埠<br>隱含宣告陷阱：未宣告的名稱會變成 1 位元的 wire；用 `` `default_nettype none `` 讓錯誤現形 | `v005` | 用名稱連接的方式寫一個三層階層的設計（頂層→子模組→全加器），加上 `` `default_nettype none `` 並用 Verilator lint 無警告<br>**單元檢核** |

**檢核**：完成這些 HDLBits 題目（4／5 題以上）：`Vector reversal 1`、`More replication`、`Three modules`、`Modules and vectors`、`Adder 2`

#### 單元 4：組合電路：always 區塊、if／case 與避免閂鎖（第 6–7 週）

**目標**：能用 always @* 寫出正確的組合電路，並避免意外產生閂鎖。

**學什麼**
- `always @*`（SystemVerilog 用 `always_comb`）：敏感清單自動完整；區塊內用阻塞賦值 `=`
- if／else、case、casez、casex（避免 casex）、優先權編碼器；`default` 與預設值寫法
- 閂鎖（latch）怎麼來的：某條路徑沒有給輸出值；防呆寫法：先在區塊開頭給預設值
- 組合電路建構區塊：多工器、解碼器／編碼器、加法器、比較器、ALU；for 迴圈在組合邏輯中是『展開』而不是『執行』

**待新增題目**：
- `v006` ALU：8 種運算的 8 位元 ALU，輸出結果與旗標 Z、N、C、V
- `v007` 優先權編碼器：N 位元請求向量輸出最高（或最低）優先的索引與有效位
- `v008` 找出閂鎖：給 5 段有閂鎖的程式，改成沒有閂鎖（用 Yosys 檢查）

**實作作業**：
- 寫一個 ALU，並用 Yosys `synth; stat` 確認沒有 `$_DLATCH_*` 單元；故意移除 default 看合成報告如何變化

**常見陷阱**：
- case 沒有 default 且沒有預設值 → 閂鎖
- 在 always @* 內對同一個訊號分多處賦值卻漏了某條路徑

**自我檢查**：
- 為什麼先在區塊開頭給預設值能避免閂鎖？
- `casex` 為什麼被很多規範禁止？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **HDLBits：Verilog Language／Procedures｜Always blocks (combinational)、If statement、If statement latches、Case statement、Priority encoder、Priority encoder with casez、Avoiding latches**
  - 什麼寫法會產生閂鎖；怎麼避免
- **HDLBits：Verilog Language／More Verilog Features｜Conditional ternary operator、Reduction operators、Combinational for-loop: Vector reversal 2、Combinational for-loop: 255-bit population count**
  - for 迴圈展開；縮減運算子
- **HDLBits：Circuits／Combinational Logic／Multiplexers｜2-to-1 multiplexer、2-to-1 bus multiplexer、9-to-1 multiplexer、256-to-1 multiplexer**
  - 多工器的各種寫法與向量索引
- **HDLBits：Circuits／Combinational Logic／Arithmetic Circuits｜Half adder、Full adder、3-bit binary adder、Adder、Signed addition overflow、100-bit binary adder**
  - 加法器與溢位判斷
- **Harris & Harris《Digital Building Blocks》（第 5 章）**
  - 數位建構區塊：算術電路（加法器、減法器、比較器、ALU）與移位器
- **Clifford Cummings, "Nonblocking Assignments in Verilog Synthesis, Coding Styles That Kill!"**
  - 阻塞與非阻塞賦值的使用準則：組合用 =，時序用 <=

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 6 | HDLBits：Verilog Language／Procedures｜Always blocks (combinational)、If statement、If statement latches、Case statement、Priority encoder、Priority encoder with casez、Avoiding latches<br>HDLBits：Verilog Language／More Verilog Features｜Conditional ternary operator、Reduction operators、Combinational for-loop: Vector reversal 2、Combinational for-loop: 255-bit population count<br>HDLBits：Circuits／Combinational Logic／Multiplexers｜2-to-1 multiplexer、2-to-1 bus multiplexer、9-to-1 multiplexer、256-to-1 multiplexer | `always @*`（SystemVerilog 用 `always_comb`）：敏感清單自動完整；區塊內用阻塞賦值 `=`<br>if／else、case、casez、casex（避免 casex）、優先權編碼器；`default` 與預設值寫法 | `v006`、`v007` | — |
| 7 | HDLBits：Circuits／Combinational Logic／Arithmetic Circuits｜Half adder、Full adder、3-bit binary adder、Adder、Signed addition overflow、100-bit binary adder<br>Harris & Harris《Digital Building Blocks》（第 5 章）<br>Clifford Cummings, "Nonblocking Assignments in Verilog Synthesis, Coding Styles That Kill!" | 閂鎖（latch）怎麼來的：某條路徑沒有給輸出值；防呆寫法：先在區塊開頭給預設值<br>組合電路建構區塊：多工器、解碼器／編碼器、加法器、比較器、ALU；for 迴圈在組合邏輯中是『展開』而不是『執行』 | `v008` | 寫一個 ALU，並用 Yosys `synth; stat` 確認沒有 `$_DLATCH_*` 單元；故意移除 default 看合成報告如何變化<br>**單元檢核** |

**檢核**：完成這些 HDLBits 題目（4／5 題以上）：`Avoiding latches`、`Priority encoder with casez`、`Combinational for-loop: 255-bit population count`、`256-to-1 4-bit multiplexer`、`4-digit BCD adder`

#### 單元 5：序列電路：正反器、暫存器、計數器與移位暫存器（第 8–9 週）

**目標**：能用 always @(posedge clk) 寫出暫存器電路，分清阻塞與非阻塞，並處理重置。

**學什麼**
- 閂鎖 vs 正反器：位準觸發 vs 邊緣觸發；`always @(posedge clk)`（SystemVerilog 用 `always_ff`）：區塊內一律用非阻塞賦值 `<=`
- 同步重置 vs 非同步重置：寫法、合成結果、優缺點；重置值；啟用（enable）訊號
- 計數器（二進位、十進位、模 N）、移位暫存器、LFSR、邊緣偵測；暫存器傳輸層級（RTL）的思維：下一狀態邏輯＋狀態暫存器
- 非阻塞賦值的語意：右邊在時脈邊緣之前取樣，之後一起更新；為什麼這樣模擬出來和真實電路一致

**待新增題目**：
- `v009` 同步與非同步重置：同一電路兩種重置寫法，測試台在重置期間改變輸入看差異
- `v010` 計數器家族：模 N、可載入、上下數、帶進位輸出
- `v011` LFSR：給多項式與初值，輸出前 N 個狀態

**實作作業**：
- 實作 7 段顯示器用的 4 位數十進位計數器與時鐘分頻，附自我檢查的 testbench（至少 10 個斷言）

**常見陷阱**：
- 時序區塊內用阻塞賦值造成模擬與合成不一致或競爭條件
- 非同步重置的『釋放』與時脈靠太近 → 亞穩態（後面 CDC 單元會處理）

**自我檢查**：
- `a = b; b = a;` 與 `a <= b; b <= a;` 在時脈邊緣各做什麼？
- 同步重置與非同步重置各有什麼代價？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **HDLBits：Circuits／Sequential Logic／Latches and Flip-Flops｜D flip-flop、D flip-flops、DFF with reset、DFF with reset value、DFF with asynchronous reset、DFF with byte enable、D Latch、Mux and DFF、Detect an edge、Detect both edges、Edge capture register**
  - 正反器、重置、致能、邊緣偵測
- **HDLBits：Circuits／Sequential Logic／Counters｜Four-bit binary counter、Decade counter、Decade counter again、Slow decade counter、Counter 1-12、Counter 1000、4-digit decimal counter、12-hour clock**
  - 計數器的各種變化
- **HDLBits：Circuits／Sequential Logic／Shift Registers｜4-bit shift register、Left/right rotator、Left/right arithmetic shift by 1 or 8、5-bit LFSR、3-bit LFSR、32-bit LFSR**
  - 移位與 LFSR
- **Harris & Harris《Sequential Logic Design》（第 3 章）**
  - 閂鎖與正反器、同步序列電路、時序（setup／hold）
- **Harris & Harris《Hardware Description Languages》（第 4 章）**
  - 序列邏輯的 HDL 寫法：暫存器、重置、計數器
- **Clifford Cummings, "Nonblocking Assignments in Verilog Synthesis, Coding Styles That Kill!"**
  - 為什麼時序電路用非阻塞賦值（會示範競爭條件的例子）

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 8 | HDLBits：Circuits／Sequential Logic／Latches and Flip-Flops｜D flip-flop、D flip-flops、DFF with reset、DFF with reset value、DFF with asynchronous reset、DFF with byte enable、D Latch、Mux and DFF、Detect an edge、Detect both edges、Edge capture register<br>HDLBits：Circuits／Sequential Logic／Counters｜Four-bit binary counter、Decade counter、Decade counter again、Slow decade counter、Counter 1-12、Counter 1000、4-digit decimal counter、12-hour clock<br>HDLBits：Circuits／Sequential Logic／Shift Registers｜4-bit shift register、Left/right rotator、Left/right arithmetic shift by 1 or 8、5-bit LFSR、3-bit LFSR、32-bit LFSR | 閂鎖 vs 正反器：位準觸發 vs 邊緣觸發；`always @(posedge clk)`（SystemVerilog 用 `always_ff`）：區塊內一律用非阻塞賦值 `<=`<br>同步重置 vs 非同步重置：寫法、合成結果、優缺點；重置值；啟用（enable）訊號 | `v009`、`v010` | — |
| 9 | Harris & Harris《Sequential Logic Design》（第 3 章）<br>Harris & Harris《Hardware Description Languages》（第 4 章）<br>Clifford Cummings, "Nonblocking Assignments in Verilog Synthesis, Coding Styles That Kill!" | 計數器（二進位、十進位、模 N）、移位暫存器、LFSR、邊緣偵測；暫存器傳輸層級（RTL）的思維：下一狀態邏輯＋狀態暫存器<br>非阻塞賦值的語意：右邊在時脈邊緣之前取樣，之後一起更新；為什麼這樣模擬出來和真實電路一致 | `v011` | 實作 7 段顯示器用的 4 位數十進位計數器與時鐘分頻，附自我檢查的 testbench（至少 10 個斷言）<br>**單元檢核** |

**檢核**：完成這些 HDLBits 題目（4／5 題以上）：`Edge capture register`、`Slow decade counter`、`12-hour clock`、`32-bit LFSR`、`3-input LUT`

#### 單元 6：有限狀態機（第 10–11 週）

**目標**：能把需求畫成狀態圖，並用清楚的 Verilog 寫法實作 Moore 與 Mealy 狀態機。

**學什麼**
- Moore（輸出只看狀態）與 Mealy（輸出看狀態與輸入）；狀態圖→狀態表→編碼→下一狀態與輸出邏輯
- 寫法：兩段式（狀態暫存器＋組合邏輯）為主；一段式、三段式的取捨；`localparam`／`enum` 定義狀態；預設狀態與非法狀態處理
- 狀態編碼：二進位、格雷碼、one-hot（FPGA 常用，因為正反器多、解碼簡單）
- 常見應用：序列偵測、串列接收（含同位檢查）、PS/2 封包解析、簡單協定控制器

**待新增題目**：
- `v012` 序列偵測器：偵測 1101（允許重疊）的 Moore 與 Mealy 版本，與參考模型比對
- `v013` 串列接收器：起始位元、8 資料位元、停止位元、同位檢查
- `v014` 交通號誌：有行人按鈕的路口控制器，含時間計數

**實作作業**：
- 實作 UART 接收器的 FSM（含 16 倍過取樣的位元對齊），畫出狀態圖並附隨機錯誤注入的 testbench

**常見陷阱**：
- 狀態機沒有處理未使用的編碼（非法狀態）
- Mealy 輸出直接接到下一級造成組合路徑變長

**自我檢查**：
- 什麼時候選 one-hot？代價是什麼？
- Moore 與 Mealy 在輸出時序上差幾個週期？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **HDLBits：Circuits／Sequential Logic／Finite State Machines｜Simple FSM 1 (asynchronous reset)、Simple FSM 1 (synchronous reset)、Simple FSM 2 (asynchronous reset)、Simple FSM 2 (synchronous reset)、Simple state transitions 3、Simple one-hot state transitions 3、Simple FSM 3 (asynchronous reset)、Simple FSM 3 (synchronous reset)**
  - 狀態轉移表→程式碼；one-hot 的寫法
- **HDLBits：Circuits／Sequential Logic／Finite State Machines｜Design a Moore FSM、Lemmings 1、Lemmings 2、Lemmings 3、Lemmings 4、One-hot FSM**
  - 由需求建立狀態機
- **HDLBits：Circuits／Sequential Logic／Finite State Machines｜PS/2 packet parser、PS/2 packet parser and datapath、Serial receiver、Serial receiver and datapath、Serial receiver with parity checking、Sequence recognition**
  - 協定解析型的狀態機＋資料路徑
- **Harris & Harris《Sequential Logic Design》（第 3 章）**
  - 有限狀態機的設計方法、狀態編碼、Moore 與 Mealy、因式分解

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 10 | HDLBits：Circuits／Sequential Logic／Finite State Machines｜Simple FSM 1 (asynchronous reset)、Simple FSM 1 (synchronous reset)、Simple FSM 2 (asynchronous reset)、Simple FSM 2 (synchronous reset)、Simple state transitions 3、Simple one-hot state transitions 3、Simple FSM 3 (asynchronous reset)、Simple FSM 3 (synchronous reset)<br>HDLBits：Circuits／Sequential Logic／Finite State Machines｜Design a Moore FSM、Lemmings 1、Lemmings 2、Lemmings 3、Lemmings 4、One-hot FSM | Moore（輸出只看狀態）與 Mealy（輸出看狀態與輸入）；狀態圖→狀態表→編碼→下一狀態與輸出邏輯<br>寫法：兩段式（狀態暫存器＋組合邏輯）為主；一段式、三段式的取捨；`localparam`／`enum` 定義狀態；預設狀態與非法狀態處理 | `v012`、`v013` | — |
| 11 | HDLBits：Circuits／Sequential Logic／Finite State Machines｜PS/2 packet parser、PS/2 packet parser and datapath、Serial receiver、Serial receiver and datapath、Serial receiver with parity checking、Sequence recognition<br>Harris & Harris《Sequential Logic Design》（第 3 章） | 狀態編碼：二進位、格雷碼、one-hot（FPGA 常用，因為正反器多、解碼簡單）<br>常見應用：序列偵測、串列接收（含同位檢查）、PS/2 封包解析、簡單協定控制器 | `v014` | 實作 UART 接收器的 FSM（含 16 倍過取樣的位元對齊），畫出狀態圖並附隨機錯誤注入的 testbench<br>**單元檢核** |

**檢核**：完成這些 HDLBits 題目（4／5 題以上）：`Lemmings 4`、`Serial receiver and datapath`、`Serial receiver with parity checking`、`Sequence recognition`、`Q8: Design a Mealy FSM`

#### 單元 7：Testbench 入門與波形除錯（第 12 週）

**目標**：能為自己的設計寫會自動判斷對錯的 testbench，並用波形找 bug。

**學什麼**
- testbench 結構：宣告、被測設計（DUT）實例、時脈產生（`always #5 clk = ~clk`）、`initial` 激勵、`$display`／`$monitor`／`$finish`
- 自我檢查（self-checking）：把預期值算出來與 DUT 輸出比較，失敗時印出訊息並用 `$fatal` 或計數；不要靠肉眼看波形判斷對錯
- 波形：`$dumpfile`／`$dumpvars` 產生 VCD；在 GTKWave 加訊號、設時間格式、找邊緣
- 常用技巧：`$readmemh` 載入測試向量、`$random` 與 `$urandom`、固定亂數種子讓失敗可重現、時序參數（#delay）只在 testbench 使用

**待新增題目**：
- `v015` 自我檢查測試台：給 4 個 DUT（其中 2 個有 bug），寫 testbench 讓有 bug 的失敗、正確的通過
- `v016` 向量檔測試：用 $readmemh 讀測試向量並比對輸出

**實作作業**：
- 替前面的計數器與 FSM 各寫一個 self-checking testbench，加上 100 組隨機輸入與一個參考模型；用故意放的 bug 驗證 testbench 能抓到它

**常見陷阱**：
- testbench 太弱：全部測試通過但其實沒測到任何東西
- 用 `==` 比較含 X 的值（應用 `!==` 在 testbench 內抓出 X）

**自我檢查**：
- 為什麼要固定亂數種子？
- `===`／`!==` 與 `==`／`!=` 在 X 上有什麼差別？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **HDLBits：Verification: Writing Testbenches｜Clock、Testbench1、AND gate、Testbench2、T flip-flop**
  - testbench 的基本寫法與時脈產生
- **HDLBits：Verification: Reading Simulations｜Mux、NAND、Add/sub、Case statement、Combinational circuit 1、Combinational circuit 2、Combinational circuit 3、Sequential circuit 7、Sequential circuit 8**
  - 從波形反推電路、從波形找 bug
- **GTKWave 使用手冊**
  - 載入 VCD、加訊號群組、儲存視圖
- **Janick Bergeron, Writing Testbenches: Functional Verification of HDL Models**
  - 驗證的基本觀念：testbench 是設計的一半

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 12 | HDLBits：Verification: Writing Testbenches｜Clock、Testbench1、AND gate、Testbench2、T flip-flop<br>HDLBits：Verification: Reading Simulations｜Mux、NAND、Add/sub、Case statement、Combinational circuit 1、Combinational circuit 2、Combinational circuit 3、Sequential circuit 7、Sequential circuit 8<br>GTKWave 使用手冊<br>Janick Bergeron, Writing Testbenches: Functional Verification of HDL Models | testbench 結構：宣告、被測設計（DUT）實例、時脈產生（`always #5 clk = ~clk`）、`initial` 激勵、`$display`／`$monitor`／`$finish`<br>自我檢查（self-checking）：把預期值算出來與 DUT 輸出比較，失敗時印出訊息並用 `$fatal` 或計數；不要靠肉眼看波形判斷對錯<br>波形：`$dumpfile`／`$dumpvars` 產生 VCD；在 GTKWave 加訊號、設時間格式、找邊緣<br>常用技巧：`$readmemh` 載入測試向量、`$random` 與 `$urandom`、固定亂數種子讓失敗可重現、時序參數（#delay）只在 testbench 使用 | `v015`、`v016` | 替前面的計數器與 FSM 各寫一個 self-checking testbench，加上 100 組隨機輸入與一個參考模型；用故意放的 bug 驗證 testbench 能抓到它<br>**單元檢核** |

**檢核**：完成這些 HDLBits 題目（4／5 題以上）：`Testbench2`、`T flip-flop`、`Sequential circuit 9`、`Sequential circuit 10`、`Combinational circuit 6`

#### 單元 8：階段 V0 驗收週（第 13 週）

**目標**：獨立完成一個小型數位設計並附自我檢查的測試台。

**學什麼**
- 整合：一個 UART 發送加接收（回送測試），含計數器分頻、FSM、移位暫存器；所有模組通過 Verilator lint 與 Yosys 合成

**實作作業**：
- 完成 UART 回送設計：發送端與接收端、波特率產生器、self-checking testbench（含錯誤波特率與雜訊）

**自我檢查**：
- 我最常犯的三種 Verilog 錯誤？有什麼檢查清單？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Harris & Harris《Sequential Logic Design》（第 3 章）**
  - 回顧：時序、狀態機與同步設計原則
- **Verilator 使用指南：Lint 與 Warnings**
  - 清掉所有警告，不要用 lint_off 逃避

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 13 | Harris & Harris《Sequential Logic Design》（第 3 章）<br>Verilator 使用指南：Lint 與 Warnings | 整合：一個 UART 發送加接收（回送測試），含計數器分頻、FSM、移位暫存器；所有模組通過 Verilator lint 與 Yosys 合成 | — | 完成 UART 回送設計：發送端與接收端、波特率產生器、self-checking testbench（含錯誤波特率與雜訊）<br>**單元檢核** |

**作品驗收**（5 天內，逐條對照）：
- [ ] UART 發送與接收回送測試：全部位元組正確（含 1000 個隨機位元組）
- [ ] Verilator `-Wall` 無警告；Yosys 合成無閂鎖
- [ ] testbench 能抓到至少 3 個故意放的 bug
- [ ] 能口頭說明每個模組的時序

### 階段 V1：RTL 設計

能設計資料路徑與控制、FIFO、算術電路、跨時脈域與一顆 RISC-V 處理器，寫出模擬與合成一致的程式。

#### 單元 9：資料路徑與控制、握手協定（第 14–15 週）

**目標**：能把設計切成資料路徑與控制器，並寫出正確的 ready／valid 握手。

**學什麼**
- 資料路徑（暫存器、算術單元、多工器）與控制器（FSM 產生控制訊號）的分工；寄存器傳輸表（RTL table）
- ready／valid 握手：valid 與 ready 都為高的那個週期才算傳輸；規則：valid 一旦拉高在 ready 之前不可撤回（依協定）；背壓（backpressure）與 skid buffer
- 管線的基本概念：把長路徑切成多級、用暫存器隔開；吞吐量與延遲；氣泡與停頓
- 介面時序圖要能畫：每個訊號在哪個時脈邊緣改變、何時被取樣

**待新增題目**：
- `v017` 乘加管線：3 級管線的 MAC，ready／valid 介面，隨機背壓測試
- `v018` skid buffer：實作並證明在隨機背壓下不掉資料、不重複
- `v019` 簡單 GCD 引擎：用 FSM＋資料路徑，start／done 握手

**實作作業**：
- 實作 ready／valid 的 N 級管線與 skid buffer，用隨機背壓與隨機 valid 跑 10^5 筆資料，scoreboard 確認順序與內容

**常見陷阱**：
- valid 在沒有 ready 時改變資料
- 背壓沒有被傳遞到上游造成掉資料

**自我檢查**：
- ready／valid 的一次傳輸在什麼條件下發生？
- skid buffer 為什麼能切斷 ready 的組合路徑？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **HDLBits：Circuits／Building Larger Circuits｜Counter with period 1000、4-bit shift register and down counter、FSM: Sequence 1101 recognizer、FSM: Enable shift register、FSM: The complete FSM、The complete timer、FSM: One-hot logic equations**
  - 把計數器、移位暫存器與 FSM 組成較大的電路
- **Harris & Harris《Microarchitecture》（第 7 章）**
  - 資料路徑與控制單元的拆分；單週期處理器的資料路徑畫法
- **Harris & Harris《Digital Building Blocks》（第 5 章）**
  - 資料路徑建構區塊：暫存器、記憶體陣列、邏輯陣列

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 14 | HDLBits：Circuits／Building Larger Circuits｜Counter with period 1000、4-bit shift register and down counter、FSM: Sequence 1101 recognizer、FSM: Enable shift register、FSM: The complete FSM、The complete timer、FSM: One-hot logic equations<br>Harris & Harris《Microarchitecture》（第 7 章） | 資料路徑（暫存器、算術單元、多工器）與控制器（FSM 產生控制訊號）的分工；寄存器傳輸表（RTL table）<br>ready／valid 握手：valid 與 ready 都為高的那個週期才算傳輸；規則：valid 一旦拉高在 ready 之前不可撤回（依協定）；背壓（backpressure）與 skid buffer | `v017`、`v018` | — |
| 15 | Harris & Harris《Digital Building Blocks》（第 5 章） | 管線的基本概念：把長路徑切成多級、用暫存器隔開；吞吐量與延遲；氣泡與停頓<br>介面時序圖要能畫：每個訊號在哪個時脈邊緣改變、何時被取樣 | `v019` | 實作 ready／valid 的 N 級管線與 skid buffer，用隨機背壓與隨機 valid 跑 10^5 筆資料，scoreboard 確認順序與內容<br>**單元檢核** |

**檢核**：完成這些 HDLBits 題目（3／3 題以上）：`The complete timer`、`FSM: The complete FSM`、`FSM: One-hot logic equations`

#### 單元 10：參數化、generate 與 SystemVerilog 設計語法（第 16–17 週）

**目標**：寫出可重用、可設定的模組，並善用 SystemVerilog 的設計語法。

**學什麼**
- `parameter`／`localparam`、模組參數覆寫（`#(...)`）、`$clog2`；`function` 與 `task` 的可合成用法
- `generate for`／`generate if`：由參數產生電路結構（例如 N 位元漣波加法器、樹狀加總）
- SystemVerilog：`logic`、`always_comb`／`always_ff`／`always_latch`（讓工具檢查你的意圖）、`enum`、`struct`（packed）、`typedef`、`package`、`unique`／`priority` case
- 介面（`interface`、`modport`）把一束訊號打包；何時值得用、何時只會增加工具相容問題

**待新增題目**：
- `v020` 參數化加法樹：N 輸入、W 位元的加總樹，用 generate 產生，延遲 O(log N)
- `v021` 參數化 FIFO 骨架：深度與寬度為參數，`$clog2` 計算指標位元

**實作作業**：
- 把前面的 ALU、計數器、FIFO 全部改成參數化＋SystemVerilog 風格；用 Verilator 與 Yosys（`read_verilog -sv`）都通過

**常見陷阱**：
- 使用工具不支援的 SystemVerilog 特性造成可攜性問題
- generate 內的 genvar 範圍寫錯

**自我檢查**：
- `always_comb` 比 `always @*` 多做了什麼檢查？
- `localparam` 與 `parameter` 差在哪？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **HDLBits：Verilog Language／More Verilog Features｜Generate for-loop: 100-bit binary adder 2、Generate for-loop: 100-digit BCD adder**
  - generate for 產生重複結構
- **Harris & Harris《Hardware Description Languages》（第 4 章）**
  - 參數化模組、generate、測試台、SystemVerilog 補充
- **Verilator 使用指南：Language Support（SystemVerilog 支援範圍）**
  - 哪些語法可用、哪些工具不支援
- **Yosys 手冊：Verilog 與 SystemVerilog 支援**
  - `read_verilog -sv` 支援的子集

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 16 | HDLBits：Verilog Language／More Verilog Features｜Generate for-loop: 100-bit binary adder 2、Generate for-loop: 100-digit BCD adder<br>Harris & Harris《Hardware Description Languages》（第 4 章） | `parameter`／`localparam`、模組參數覆寫（`#(...)`）、`$clog2`；`function` 與 `task` 的可合成用法<br>`generate for`／`generate if`：由參數產生電路結構（例如 N 位元漣波加法器、樹狀加總） | `v020` | — |
| 17 | Verilator 使用指南：Language Support（SystemVerilog 支援範圍）<br>Yosys 手冊：Verilog 與 SystemVerilog 支援 | SystemVerilog：`logic`、`always_comb`／`always_ff`／`always_latch`（讓工具檢查你的意圖）、`enum`、`struct`（packed）、`typedef`、`package`、`unique`／`priority` case<br>介面（`interface`、`modport`）把一束訊號打包；何時值得用、何時只會增加工具相容問題 | `v021` | 把前面的 ALU、計數器、FIFO 全部改成參數化＋SystemVerilog 風格；用 Verilator 與 Yosys（`read_verilog -sv`）都通過<br>**單元檢核** |

**作品驗收**（5 天內，逐條對照）：
- [ ] 參數化的 ALU、計數器、加法樹各通過 3 組不同參數的 testbench
- [ ] 全部通過 Verilator lint 與 Yosys 合成
- [ ] 用 `$clog2` 與 generate 的寫法各一處並說明為什麼

#### 單元 11：記憶體與 FIFO（第 18–19 週）

**目標**：會寫可推論出 RAM 的程式，並正確實作同步 FIFO。

**學什麼**
- 暫存器堆（register file）、ROM（`$readmemh`）、同步 RAM：單埠、雙埠、讀寫衝突時的行為（read-first／write-first／no-change）
- FPGA 與 ASIC 的差別：FPGA 的 block RAM 可由 Verilog 推論；ASIC 要用記憶體編譯器（memory compiler）產生的巨集
- 同步 FIFO：讀寫指標、空與滿的判斷（多一個指標位元 vs 計數器）、同時讀寫、FIFO 深度的計算
- 記憶體的驗證：寫入後讀出、位址邊界、同時存取

**待新增題目**：
- `v022` 雙埠 RAM：讀寫同時、同位址的行為，與參考模型比對
- `v023` 同步 FIFO：指標法，覆蓋空／滿／同時讀寫／環繞
- `v024` 暫存器堆：RISC-V 風格的 2 讀 1 寫，x0 恆為 0

**實作作業**：
- 實作同步 FIFO 並用 SVA 風格的檢查（可用 testbench 內斷言）證明：不溢位、不讀空、先進先出；用 Yosys 看是否推論出 RAM 單元

**常見陷阱**：
- 讀寫指標位元數不夠無法區分滿與空
- 讀出資料延遲一個週期沒有被下游考慮

**自我檢查**：
- FIFO 的滿與空如何用指標比較判斷？
- block RAM 推論需要什麼樣的寫法？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Harris & Harris《Memory Systems》（第 8 章）**
  - 記憶體系統：記憶體陣列、暫存器堆、ROM／RAM 的 HDL 寫法
- **Yosys 手冊：Memory 處理（`memory` 指令群）**
  - 如何把陣列推論成記憶體
- **Clifford Cummings, "Simulation and Synthesis Techniques for Asynchronous FIFO Design"**
  - 先讀同步版的指標與空滿判斷，下一單元再讀非同步版

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 18 | Harris & Harris《Memory Systems》（第 8 章）<br>Yosys 手冊：Memory 處理（`memory` 指令群） | 暫存器堆（register file）、ROM（`$readmemh`）、同步 RAM：單埠、雙埠、讀寫衝突時的行為（read-first／write-first／no-change）<br>FPGA 與 ASIC 的差別：FPGA 的 block RAM 可由 Verilog 推論；ASIC 要用記憶體編譯器（memory compiler）產生的巨集 | `v022`、`v023` | — |
| 19 | Clifford Cummings, "Simulation and Synthesis Techniques for Asynchronous FIFO Design" | 同步 FIFO：讀寫指標、空與滿的判斷（多一個指標位元 vs 計數器）、同時讀寫、FIFO 深度的計算<br>記憶體的驗證：寫入後讀出、位址邊界、同時存取 | `v024` | 實作同步 FIFO 並用 SVA 風格的檢查（可用 testbench 內斷言）證明：不溢位、不讀空、先進先出；用 Yosys 看是否推論出 RAM 單元<br>**單元檢核** |

**作品驗收**（5 天內，逐條對照）：
- [ ] 同步 FIFO：全空、全滿、同時讀寫、環繞皆通過隨機測試（10^5 筆）
- [ ] Yosys 報告顯示記憶體被推論為 RAM（附輸出）
- [ ] 附讀寫時序圖

#### 單元 12：算術電路（第 20–21 週）

**目標**：能依時序與面積需求選擇適當的加法器與乘法器，並處理溢位與定點數。

**學什麼**
- 加法器：漣波進位、進位選擇、進位預測（CLA）、前綴加法器（Kogge-Stone、Brent-Kung）的取捨；進位鏈就是關鍵路徑
- 乘法器：陣列、Booth 編碼、Wallace 樹；序列乘法（移位加）省面積；除法器：恢復式、非恢復式、迭代
- 有號與無號：符號擴展、飽和運算、溢位偵測；定點數（Qm.n）與捨入
- 資源共用與時間多工：用一個乘法器在多個週期內完成多個乘法

**待新增題目**：
- `v025` 進位選擇加法器：32 位元，與漣波進位版本比較合成後的延遲與面積（用 Yosys＋OpenSTA）
- `v026` Booth 乘法器：有號 16×16，對拍 `*`
- `v027` 序列除法器：32÷32，多週期，start／done 握手
- `v028` 飽和加法與定點乘法：Q1.15 的飽和運算與捨入

**實作作業**：
- 實作三種加法器（漣波、進位選擇、Kogge-Stone），用 Yosys 合成同一製程庫，比較面積與（用 OpenSTA 算出的）最大延遲，整理成表

**常見陷阱**：
- 有號乘法忘了符號擴展
- 只看邏輯層數不看扇出與線延遲

**自我檢查**：
- 為什麼加法器的最大延遲主要看進位鏈？
- Booth 編碼為什麼能減少部分積的數量？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Harris & Harris《Digital Building Blocks》（第 5 章）**
  - 算術電路：加法器、減法器、比較器、移位器、乘法器與除法器、定點與浮點數
- **HDLBits：Verilog Language／Modules: Hierarchy｜Carry-select adder、Adder-subtractor**
  - 進位選擇與加減法器
- **HDLBits：Circuits／Combinational Logic／Arithmetic Circuits｜Signed addition overflow、4-digit BCD adder**
  - 有號溢位與 BCD
- **Weste & Harris, CMOS VLSI Design：Datapath Subsystems 一章（加法器、乘法器）**
  - 各加法器的延遲與面積推導；前綴加法器

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 20 | Harris & Harris《Digital Building Blocks》（第 5 章）<br>HDLBits：Verilog Language／Modules: Hierarchy｜Carry-select adder、Adder-subtractor | 加法器：漣波進位、進位選擇、進位預測（CLA）、前綴加法器（Kogge-Stone、Brent-Kung）的取捨；進位鏈就是關鍵路徑<br>乘法器：陣列、Booth 編碼、Wallace 樹；序列乘法（移位加）省面積；除法器：恢復式、非恢復式、迭代 | `v025`、`v026` | — |
| 21 | HDLBits：Circuits／Combinational Logic／Arithmetic Circuits｜Signed addition overflow、4-digit BCD adder<br>Weste & Harris, CMOS VLSI Design：Datapath Subsystems 一章（加法器、乘法器） | 有號與無號：符號擴展、飽和運算、溢位偵測；定點數（Qm.n）與捨入<br>資源共用與時間多工：用一個乘法器在多個週期內完成多個乘法 | `v027`、`v028` | 實作三種加法器（漣波、進位選擇、Kogge-Stone），用 Yosys 合成同一製程庫，比較面積與（用 OpenSTA 算出的）最大延遲，整理成表<br>**單元檢核** |

**作品驗收**（6 天內，逐條對照）：
- [ ] 三種加法器對拍 10^6 組隨機輸入全部一致
- [ ] 附合成面積與時序比較表並解釋趨勢
- [ ] Booth 乘法器對拍 `*` 無差異（含極值）

#### 單元 13：可合成寫法與常見陷阱（第 22–23 週）

**目標**：寫出模擬與合成行為一致的程式，並會用工具找出問題。

**學什麼**
- 可合成子集：不可合成的結構（`initial`（多數情況）、`#` 延遲、`fork`、`wait`、`real`、`force`）；`initial` 在 FPGA 可作為初始值但 ASIC 不行
- 模擬與合成不一致的來源：敏感清單不完整、阻塞與非阻塞混用、X 傳播（`if (x)` 走 else）、`casex`、多重驅動、組合迴圈
- 用工具檢查：`verilator --lint-only -Wall`、`yosys -p 'read_verilog; proc; check'`、閘級模擬（合成後網表加上延遲模型）對拍 RTL
- 編碼規範：命名、重置策略、時脈與重置的統一、每個 always 區塊只驅動一類訊號

**待新增題目**：
- `v029` 找出 10 個陷阱：給 10 段程式，每段有一種模擬／合成不一致的 bug，找出並修好
- `v030` X 傳播：預測含 X 的組合與時序電路的輸出

**實作作業**：
- 製作自己的『RTL 檢查清單』（至少 20 條，各附一個壞例子與好例子），並用它審查前面所有設計，記錄修正數量

**常見陷阱**：
- 把 lint 警告關掉而不是修掉
- 只看 RTL 模擬不跑閘級模擬

**自我檢查**：
- `if (a == 1'bx)` 在合成時是什麼意思？
- 為什麼同一個訊號不能在兩個 always 區塊中被賦值？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Clifford Cummings, "Nonblocking Assignments in Verilog Synthesis, Coding Styles That Kill!"**
  - 完整讀完；逐條對照自己過去的寫法
- **Verilator 使用指南：Warnings 列表**
  - 每個警告的意義與修正方式
- **Yosys 手冊：`proc`、`check`、`opt` 指令**
  - 看懂合成日誌裡的警告
- **Bening & Foster, Principles of Verifiable RTL Design**
  - 寫出容易驗證的 RTL 的準則

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 22 | Clifford Cummings, "Nonblocking Assignments in Verilog Synthesis, Coding Styles That Kill!"<br>Verilator 使用指南：Warnings 列表 | 可合成子集：不可合成的結構（`initial`（多數情況）、`#` 延遲、`fork`、`wait`、`real`、`force`）；`initial` 在 FPGA 可作為初始值但 ASIC 不行<br>模擬與合成不一致的來源：敏感清單不完整、阻塞與非阻塞混用、X 傳播（`if (x)` 走 else）、`casex`、多重驅動、組合迴圈 | `v029` | — |
| 23 | Yosys 手冊：`proc`、`check`、`opt` 指令<br>Bening & Foster, Principles of Verifiable RTL Design | 用工具檢查：`verilator --lint-only -Wall`、`yosys -p 'read_verilog; proc; check'`、閘級模擬（合成後網表加上延遲模型）對拍 RTL<br>編碼規範：命名、重置策略、時脈與重置的統一、每個 always 區塊只驅動一類訊號 | `v030` | 製作自己的『RTL 檢查清單』（至少 20 條，各附一個壞例子與好例子），並用它審查前面所有設計，記錄修正數量<br>**單元檢核** |

**作品驗收**（6 天內，逐條對照）：
- [ ] 30 條以上的 RTL 檢查清單，各附壞例子與好例子
- [ ] 用檢查清單審查所有舊設計，記錄發現與修正
- [ ] 合成後閘級模擬與 RTL 對拍一致

#### 單元 14：時脈、重置與跨時脈域（CDC）（第 24–25 週）

**目標**：能辨認跨時脈域路徑，並用正確的同步器與非同步 FIFO 處理它們。

**學什麼**
- 亞穩態：訊號在 setup／hold 窗口內變化；平均失效間隔（MTBF）與同步級數的關係；兩級同步器（2FF）
- 單一位元跨域：電位同步器；脈衝同步（toggle 同步器）；握手同步（多位元但低頻）；多位元資料不能逐位元各自同步
- 非同步 FIFO：格雷碼指標、指標同步、空滿判斷在各自時脈域；Cummings 的經典設計
- 重置：非同步重置同步釋放（reset synchronizer）；多時脈域的重置順序

**待新增題目**：
- `v031` 兩級同步器：用模擬注入亞穩態（隨機延遲）看輸出，說明為什麼需要兩級
- `v032` 脈衝同步器：快時脈域脈衝到慢時脈域，不漏不重
- `v033` 非同步 FIFO：格雷碼指標，兩個不同頻率時脈的隨機測試

**實作作業**：
- 實作非同步 FIFO，用兩個非整數倍頻率的時脈（例如 7 與 11 的週期比）與隨機讀寫速率驗證無掉資料；畫出每條跨域路徑與其同步器

**常見陷阱**：
- 多位元匯流排逐位元各自同步（會得到從未出現過的值）
- 同步器的輸出又被當成時脈或組合邏輯使用後再跨域

**自我檢查**：
- 為什麼格雷碼適合做跨域指標？
- 兩級同步器能把亞穩態的機率降低多少（定性說明）？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Clifford Cummings, "Simulation and Synthesis Techniques for Asynchronous FIFO Design"**
  - 格雷碼指標、空滿旗標在不同時脈域的產生
- **Clifford Cummings, "Synthesis and Scripting Techniques for Designing Multi-Asynchronous Clock Designs"**
  - 多時脈域設計的規則與常見錯誤
- **Harris & Harris《Sequential Logic Design》（第 3 章）**
  - 同步器與亞穩態：正反器的時序參數與同步失敗
- **Weste & Harris, CMOS VLSI Design：Circuit Pitfalls／Synchronizers 相關章節**
  - 亞穩態的電路層級成因

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 24 | Clifford Cummings, "Simulation and Synthesis Techniques for Asynchronous FIFO Design"<br>Clifford Cummings, "Synthesis and Scripting Techniques for Designing Multi-Asynchronous Clock Designs" | 亞穩態：訊號在 setup／hold 窗口內變化；平均失效間隔（MTBF）與同步級數的關係；兩級同步器（2FF）<br>單一位元跨域：電位同步器；脈衝同步（toggle 同步器）；握手同步（多位元但低頻）；多位元資料不能逐位元各自同步 | `v031`、`v032` | — |
| 25 | Harris & Harris《Sequential Logic Design》（第 3 章）<br>Weste & Harris, CMOS VLSI Design：Circuit Pitfalls／Synchronizers 相關章節 | 非同步 FIFO：格雷碼指標、指標同步、空滿判斷在各自時脈域；Cummings 的經典設計<br>重置：非同步重置同步釋放（reset synchronizer）；多時脈域的重置順序 | `v033` | 實作非同步 FIFO，用兩個非整數倍頻率的時脈（例如 7 與 11 的週期比）與隨機讀寫速率驗證無掉資料；畫出每條跨域路徑與其同步器<br>**單元檢核** |

**作品驗收**（7 天內，逐條對照）：
- [ ] 非同步 FIFO 在 10^6 筆資料、隨機頻率與讀寫速率下零錯誤
- [ ] 附所有跨域路徑清單與對應同步器
- [ ] 重置同步釋放電路與波形說明

#### 單元 15：單週期 RISC-V 處理器（第 26–28 週）

**目標**：能獨立設計並驗證一顆執行 RV32I 子集的單週期處理器。

**學什麼**
- 指令集架構：RISC-V RV32I 的格式（R／I／S／B／U／J）、暫存器、載入儲存、分支與跳躍；組合語言與機器碼互相轉換
- 資料路徑：程式計數器、指令記憶體、暫存器堆、ALU、資料記憶體、立即值產生器、控制單元（主解碼＋ALU 解碼）
- 驗證：用 RISC-V 組譯器產生的機器碼（`$readmemh` 載入）跑測試程式；與指令集模擬器（如 Spike 或自己寫的 Python 模型）逐指令比對暫存器變化
- 從一份規格到可運作 CPU 的工作流程：先寫模型、再寫 RTL、最後比對

**待新增題目**：
- `v034` 指令解碼器：給 32 位元指令，輸出欄位與控制訊號
- `v035` 立即值產生器：五種格式的立即值擴展
- `v036` CPU 回歸：跑 20 個小型組合語言程式並與 Python 參考模型比對

**實作作業**：
- 實作支援 RV32I 子集（算術、邏輯、載入儲存、分支、jal／jalr、lui／auipc）的單週期 CPU；用 Python 寫一個簡單的 RV32I 模型做逐指令比對；跑費氏數列與排序程式

**常見陷阱**：
- 分支立即值的位元重排寫錯
- x0 暫存器可以被寫入

**自我檢查**：
- B-type 立即值為什麼位元順序看起來很亂？
- 單週期處理器的時脈週期由哪條路徑決定？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Harris & Harris《Architecture》（第 6 章）**
  - 架構：RISC-V 指令集、機器語言、組合語言、編譯與載入
- **Harris & Harris《Microarchitecture》（第 7 章）**
  - 微架構：單週期處理器的資料路徑與控制；效能分析
- **RISC-V Unprivileged ISA 規格（RV32I 章節）**
  - 指令格式與語意的權威來源

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 26 | Harris & Harris《Architecture》（第 6 章） | 指令集架構：RISC-V RV32I 的格式（R／I／S／B／U／J）、暫存器、載入儲存、分支與跳躍；組合語言與機器碼互相轉換<br>資料路徑：程式計數器、指令記憶體、暫存器堆、ALU、資料記憶體、立即值產生器、控制單元（主解碼＋ALU 解碼） | `v034` | — |
| 27 | Harris & Harris《Microarchitecture》（第 7 章） | 驗證：用 RISC-V 組譯器產生的機器碼（`$readmemh` 載入）跑測試程式；與指令集模擬器（如 Spike 或自己寫的 Python 模型）逐指令比對暫存器變化 | `v035` | — |
| 28 | RISC-V Unprivileged ISA 規格（RV32I 章節） | 從一份規格到可運作 CPU 的工作流程：先寫模型、再寫 RTL、最後比對 | `v036` | 實作支援 RV32I 子集（算術、邏輯、載入儲存、分支、jal／jalr、lui／auipc）的單週期 CPU；用 Python 寫一個簡單的 RV32I 模型做逐指令比對；跑費氏數列與排序程式<br>**單元檢核** |

**作品驗收**（14 天內，逐條對照）：
- [ ] 通過 20 個以上測試程式，逐指令與 Python 模型一致
- [ ] Verilator lint 無警告；Yosys 合成成功並附面積報告
- [ ] 能口頭說明每條指令走的資料路徑
- [ ] 附資料路徑圖

#### 單元 16：管線化處理器（第 29–30 週）

**目標**：把單週期處理器改成五級管線，處理資料、控制與結構危障。

**學什麼**
- 五級管線：IF／ID／EX／MEM／WB；管線暫存器；吞吐量與 CPI
- 危障：資料危障（RAW）用轉送（forwarding）與停頓（stall）；載入使用危障需要一個氣泡；控制危障：分支預測與沖刷（flush）；結構危障
- 冒險偵測單元與轉送單元的設計；為什麼寄存器堆要『前半週期寫、後半週期讀』或內部轉送
- 效能量測：用測試程式量 CPI，與單週期版比較；時脈頻率提升

**待新增題目**：
- `v037` 轉送單元：給指令序列，輸出每級應選哪個轉送來源
- `v038` 冒險偵測：預測停頓與沖刷的週期數
- `v039` CPI 量測：跑基準程式，與參考模型比較週期數

**實作作業**：
- 把單週期 CPU 改成五級管線並加入轉送與停頓；用同樣的 20 個測試程式與 Python 模型比對；比較 CPI 與（合成後估計的）時脈頻率

**常見陷阱**：
- 轉送優先序寫錯（最近的結果要優先）
- 分支沖刷時漏了某一級的暫存器

**自我檢查**：
- 載入使用危障為什麼轉送也解決不了？
- CPI 與時脈頻率如何一起決定效能？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Harris & Harris《Microarchitecture》（第 7 章）**
  - 管線化處理器、危障、轉送、停頓、分支預測、效能分析
- **Patterson & Hennessy, Computer Organization and Design RISC-V Edition：The Processor 一章**
  - 管線化的另一種講法與習題

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 29 | Harris & Harris《Microarchitecture》（第 7 章） | 五級管線：IF／ID／EX／MEM／WB；管線暫存器；吞吐量與 CPI<br>危障：資料危障（RAW）用轉送（forwarding）與停頓（stall）；載入使用危障需要一個氣泡；控制危障：分支預測與沖刷（flush）；結構危障 | `v037`、`v038` | — |
| 30 | Patterson & Hennessy, Computer Organization and Design RISC-V Edition：The Processor 一章 | 冒險偵測單元與轉送單元的設計；為什麼寄存器堆要『前半週期寫、後半週期讀』或內部轉送<br>效能量測：用測試程式量 CPI，與單週期版比較；時脈頻率提升 | `v039` | 把單週期 CPU 改成五級管線並加入轉送與停頓；用同樣的 20 個測試程式與 Python 模型比對；比較 CPI 與（合成後估計的）時脈頻率<br>**單元檢核** |

**作品驗收**（14 天內，逐條對照）：
- [ ] 管線 CPU 通過同一組測試，與參考模型一致
- [ ] 附轉送／停頓／沖刷的時序圖各一個
- [ ] 附 CPI 與時脈估計的比較表

#### 單元 17：階段 V1 驗收週（第 31 週）

**目標**：整合 RTL 設計能力，附完整驗證與合成報告。

**學什麼**
- 整合：把 CPU、記憶體與一個小周邊（UART 或計時器）接成最小系統，在模擬中執行 C 或組合語言寫成的程式輸出文字

**實作作業**：
- 完成最小系統並在模擬中印出 'Hello'（經由 UART）；附驗證計畫與合成報告

**自我檢查**：
- 我的設計中最難驗證的部分是什麼？為什麼？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Harris & Harris《Memory Systems》（第 8 章）**
  - 回顧：記憶體系統與匯流排
- **Harris & Harris《I/O Systems》（第 9 章）**
  - I/O 系統：記憶體映射 I/O、UART、計時器

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 31 | Harris & Harris《Memory Systems》（第 8 章）<br>Harris & Harris《I/O Systems》（第 9 章） | 整合：把 CPU、記憶體與一個小周邊（UART 或計時器）接成最小系統，在模擬中執行 C 或組合語言寫成的程式輸出文字 | — | 完成最小系統並在模擬中印出 'Hello'（經由 UART）；附驗證計畫與合成報告<br>**單元檢核** |

**作品驗收**（7 天內，逐條對照）：
- [ ] 最小系統在模擬中經 UART 印出字串
- [ ] 驗證計畫（要測什麼、怎麼測、覆蓋什麼）
- [ ] Yosys 合成報告（面積與估計時序）

### 階段 V2：驗證

能做驗證計畫、自我檢查環境、cocotb 與 SystemVerilog 驗證、斷言與形式驗證、覆蓋率與回歸。

#### 單元 18：驗證思維與自我檢查環境（第 32–33 週）

**目標**：能設計驗證計畫，並用參考模型與記分板驗證設計。

**學什麼**
- 驗證的目標：找到 bug、並知道何時『夠了』；驗證計畫：功能列表、測試情境、覆蓋準則；驗證通常佔專案一半以上的人力
- 定向測試（directed）與受限隨機測試（constrained random）；參考模型（golden model）與記分板（scoreboard）
- 測試平台架構：激勵產生器、驅動器、監視器、記分板——即使不用 UVM 也應該這樣分層
- 回歸測試：多個測試＋多個隨機種子；失敗時要能用同一個種子重現

**待新增題目**：
- `v040` 有 bug 的 DUT 競賽：給 10 個有隱藏 bug 的設計，寫測試找出越多越好
- `v041` 參考模型比對：給 DUT 與規格，寫 Python 或 SV 參考模型並比對

**實作作業**：
- 替同步 FIFO 與 ALU 各寫分層的驗證環境（driver／monitor／scoreboard），並用 mutation（自己故意改壞設計）驗證環境能抓到至少 90% 的改壞版本

**常見陷阱**：
- 只測『會通過的情境』
- 記分板用 DUT 自己的邏輯算期望值

**自我檢查**：
- 怎麼知道驗證做夠了？
- 為什麼參考模型不應該複製 DUT 的程式碼？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Bergeron, Writing Testbenches：驗證計畫、受限隨機、覆蓋率相關章節**
  - 驗證計畫與測試平台設計的基本觀念
- **HDLBits：Verification: Reading Simulations｜Combinational circuit 4、Combinational circuit 5、Sequential circuit 7、Sequential circuit 8、Sequential circuit 9、Sequential circuit 10**
  - 練習從錯誤行為反推 bug 位置
- **Spear & Tumbush, SystemVerilog for Verification**
  - 分層測試平台的完整範例

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 32 | Bergeron, Writing Testbenches：驗證計畫、受限隨機、覆蓋率相關章節<br>HDLBits：Verification: Reading Simulations｜Combinational circuit 4、Combinational circuit 5、Sequential circuit 7、Sequential circuit 8、Sequential circuit 9、Sequential circuit 10 | 驗證的目標：找到 bug、並知道何時『夠了』；驗證計畫：功能列表、測試情境、覆蓋準則；驗證通常佔專案一半以上的人力<br>定向測試（directed）與受限隨機測試（constrained random）；參考模型（golden model）與記分板（scoreboard） | `v040` | — |
| 33 | Spear & Tumbush, SystemVerilog for Verification | 測試平台架構：激勵產生器、驅動器、監視器、記分板——即使不用 UVM 也應該這樣分層<br>回歸測試：多個測試＋多個隨機種子；失敗時要能用同一個種子重現 | `v041` | 替同步 FIFO 與 ALU 各寫分層的驗證環境（driver／monitor／scoreboard），並用 mutation（自己故意改壞設計）驗證環境能抓到至少 90% 的改壞版本<br>**單元檢核** |

**作品驗收**（7 天內，逐條對照）：
- [ ] FIFO 與 ALU 的分層驗證環境
- [ ] mutation 測試報告：抓到比例與沒抓到的原因
- [ ] 驗證計畫文件

#### 單元 19：SystemVerilog 驗證語言（第 34–35 週）

**目標**：能用 SystemVerilog 的驗證特性寫出受限隨機的測試平台。

**學什麼**
- 類別（class）、繼承、虛擬方法；動態陣列、佇列、關聯陣列；`rand`／`randc`、`constraint`、`randomize()`、`$urandom`
- 介面與 clocking block：避免測試台與 DUT 的競爭條件；`program` 區塊的歷史與現況
- 同步與通訊：`mailbox`、`semaphore`、`event`、`fork…join`／`join_any`／`join_none`
- 覆蓋群組（covergroup、coverpoint、cross）；斷言放在下一單元

**待新增題目**：
- `v042` 隨機交易產生器：有約束的隨機交易（位址範圍、權重分布），統計分布符合預期
- `v043` driver 與 monitor：對一個簡單匯流排介面，monitor 重建交易並與 driver 比對

**實作作業**：
- 用 SystemVerilog 類別重寫 FIFO 的驗證環境（交易類別、產生器、driver、monitor、scoreboard）並加入 covergroup

**常見陷阱**：
- 在 Verilator 或 iverilog 上期待完整的類別與約束隨機支援
- 隨機約束互相矛盾導致 randomize 失敗卻沒檢查回傳值

**自我檢查**：
- `randomize()` 的回傳值要檢查的原因？
- clocking block 解決了什麼競爭條件？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Spear & Tumbush, SystemVerilog for Verification：類別、隨機化、介面、覆蓋率相關章節**
  - 驗證用的語言特性逐項示範
- **Verilator 使用指南：Language Support**
  - Verilator 對驗證用語法（類別、約束隨機）的支援範圍有限；完整 SystemVerilog 驗證通常需要商用模擬器或支援度較高的工具

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 34 | Spear & Tumbush, SystemVerilog for Verification：類別、隨機化、介面、覆蓋率相關章節 | 類別（class）、繼承、虛擬方法；動態陣列、佇列、關聯陣列；`rand`／`randc`、`constraint`、`randomize()`、`$urandom`<br>介面與 clocking block：避免測試台與 DUT 的競爭條件；`program` 區塊的歷史與現況 | `v042` | — |
| 35 | Verilator 使用指南：Language Support | 同步與通訊：`mailbox`、`semaphore`、`event`、`fork…join`／`join_any`／`join_none`<br>覆蓋群組（covergroup、coverpoint、cross）；斷言放在下一單元 | `v043` | 用 SystemVerilog 類別重寫 FIFO 的驗證環境（交易類別、產生器、driver、monitor、scoreboard）並加入 covergroup<br>**單元檢核** |

**作品驗收**（7 天內，逐條對照）：
- [ ] 用類別寫成的驗證環境通過 FIFO 的隨機回歸
- [ ] covergroup 報告：覆蓋達 100% 或說明沒覆蓋的原因
- [ ] 說明哪些特性在自己用的工具上不能用

#### 單元 20：cocotb：用 Python 驗證硬體（第 36–37 週）

**目標**：能用 cocotb 搭配開源模擬器寫出完整的驗證環境。

**學什麼**
- cocotb 的運作：Python 協同模擬（coroutine）、`@cocotb.test()`、觸發器（`RisingEdge`、`Timer`、`ClockCycles`）、存取 DUT 訊號、`await`
- 驅動器與監視器用 Python 類別；隨機化用 `random` 與固定種子；記分板用 Python 容器；與 pytest 整合；Makefile 流程（`SIM=icarus` 或 `verilator`）
- 優點：快速建立參考模型與資料分析；限制：效能（在大量週期時比原生測試台慢）
- 把 cocotb 加進 CI：每次提交跑回歸並輸出 JUnit 報告

**待新增題目**：
- `v044` cocotb 的 FIFO 驗證：以 Python 的驅動器、監視器與記分板驗證 FIFO
- `v045` cocotb 的 UART 驗證：以 Python 模型產生資料並檢查 UART 波形

**實作作業**：
- 用 cocotb 重寫 FIFO 與 UART 的驗證環境（含隨機測試與固定種子重現）；在 GitHub Actions 跑回歸

**常見陷阱**：
- 在 coroutine 中忘了 `await` 導致測試默默通過
- 跨模擬器行為差異（X 值在 Verilator 中不存在）

**自我檢查**：
- cocotb 的 `await RisingEdge(clk)` 之後讀到的值是邊緣前還是邊緣後？
- 什麼時候 cocotb 不適合？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **cocotb 文件：Installation、First Steps、Library Reference**
  - 安裝、第一個測試、觸發器與資料型別的參考
- **iverilog 與 cocotb 搭配的說明**
  - `SIM=icarus` 的 Makefile 寫法與已知限制

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 36 | cocotb 文件：Installation、First Steps、Library Reference | cocotb 的運作：Python 協同模擬（coroutine）、`@cocotb.test()`、觸發器（`RisingEdge`、`Timer`、`ClockCycles`）、存取 DUT 訊號、`await`<br>驅動器與監視器用 Python 類別；隨機化用 `random` 與固定種子；記分板用 Python 容器；與 pytest 整合；Makefile 流程（`SIM=icarus` 或 `verilator`） | `v044` | — |
| 37 | iverilog 與 cocotb 搭配的說明 | 優點：快速建立參考模型與資料分析；限制：效能（在大量週期時比原生測試台慢）<br>把 cocotb 加進 CI：每次提交跑回歸並輸出 JUnit 報告 | `v045` | 用 cocotb 重寫 FIFO 與 UART 的驗證環境（含隨機測試與固定種子重現）；在 GitHub Actions 跑回歸<br>**單元檢核** |

**作品驗收**（7 天內，逐條對照）：
- [ ] FIFO 與 UART 的 cocotb 驗證環境通過隨機回歸
- [ ] CI 綠燈並輸出測試報告
- [ ] 說明 Verilator 與 iverilog 兩種模擬器的結果差異（若有）

#### 單元 21：斷言與形式驗證（第 38–39 週）

**目標**：能寫 SVA 斷言，並用形式驗證工具證明設計性質。

**學什麼**
- 斷言：立即斷言與並行斷言（`assert property`、`assume`、`cover`）；序列運算子 `##`、`|->`、`|=>`、重複 `[*n]`
- 要檢查的性質：安全性（壞事不會發生，例如 FIFO 不溢位）與活性（好事終會發生，例如請求必有回應）
- 形式驗證：有界模型檢查（BMC）、歸納證明（k-induction）、覆蓋（cover）；SymbiYosys（`.sby` 檔：`mode bmc／prove／cover`、`depth`、`engines`）
- 假設（assume）要小心：太強的假設會讓證明失去意義；用 cover 確認情境真的可達

**待新增題目**：
- `v046` FIFO 的性質：寫出 FIFO 的 5 條斷言並用形式驗證證明
- `v047` 仲裁器的公平性：輪詢仲裁器的互斥與無飢餓性質

**實作作業**：
- 用 SymbiYosys 證明同步 FIFO 與輪詢仲裁器的安全性質（無溢位、互斥）；故意放入 bug 看到反例波形，並解釋反例

**常見陷阱**：
- 假設過強，證明在空集合上成立
- BMC 的深度不夠就宣稱證明完成

**自我檢查**：
- BMC 通過與 k-induction 證明有什麼差別？
- 為什麼要用 cover 確認情境可達？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **SymbiYosys 文件：Getting Started、Reference**
  - `.sby` 檔結構與 BMC／prove／cover 模式
- **Yosys 手冊：形式驗證相關指令（`sat`、`async2sync`）**
  - Yosys 支援的立即斷言子集
- **Bening & Foster, Principles of Verifiable RTL Design：斷言與形式的相關章節**
  - 可驗證的設計風格與斷言的放置

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 38 | SymbiYosys 文件：Getting Started、Reference<br>Yosys 手冊：形式驗證相關指令（`sat`、`async2sync`） | 斷言：立即斷言與並行斷言（`assert property`、`assume`、`cover`）；序列運算子 `##`、`|->`、`|=>`、重複 `[*n]`<br>要檢查的性質：安全性（壞事不會發生，例如 FIFO 不溢位）與活性（好事終會發生，例如請求必有回應） | `v046` | — |
| 39 | Bening & Foster, Principles of Verifiable RTL Design：斷言與形式的相關章節 | 形式驗證：有界模型檢查（BMC）、歸納證明（k-induction）、覆蓋（cover）；SymbiYosys（`.sby` 檔：`mode bmc／prove／cover`、`depth`、`engines`）<br>假設（assume）要小心：太強的假設會讓證明失去意義；用 cover 確認情境真的可達 | `v047` | 用 SymbiYosys 證明同步 FIFO 與輪詢仲裁器的安全性質（無溢位、互斥）；故意放入 bug 看到反例波形，並解釋反例<br>**單元檢核** |

**作品驗收**（7 天內，逐條對照）：
- [ ] FIFO 與仲裁器的性質全部證明通過（附 `.sby` 與輸出）
- [ ] 每個性質各附一個放了 bug 後得到的反例波形與說明
- [ ] 說明每個假設的合理性

#### 單元 22：覆蓋率與回歸基礎建設（第 40–41 週）

**目標**：能量測驗證的完整度，並建立可重複的自動化回歸。

**學什麼**
- 程式碼覆蓋率：行、分支、條件、狀態機、翻轉（toggle）；Verilator 的 `--coverage` 與 `verilator_coverage`
- 功能覆蓋率：覆蓋群組與覆蓋點的設計；覆蓋率的『洞』要用新測試去填，而不是為了數字寫無意義的測試
- 回歸：測試清單、多種子、平行執行、結果彙總；失敗時保存種子與波形；與版本控制整合
- 覆蓋率 100% 不代表沒有 bug；它只告訴你哪些地方『肯定沒測到』

**待新增題目**：
- `v048` 找出覆蓋洞：給測試集與覆蓋報告，補測試填洞
- `v049` 回歸彙總：解析多個種子的結果，輸出失敗清單（可用 Tcl 或 Python 實作）

**實作作業**：
- 替最小系統建立回歸：100 個種子、平行執行、覆蓋率彙總、失敗保存波形；週報（HTML 或文字）自動產生

**常見陷阱**：
- 為了衝數字寫沒有檢查的測試
- 合併覆蓋資料時混入不同版本的設計

**自我檢查**：
- 程式碼覆蓋率與功能覆蓋率有什麼不同？
- 覆蓋率到了 100% 之後還能做什麼？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Verilator 使用指南：Coverage 與 verilator_coverage**
  - 產生與合併覆蓋資料
- **Bergeron, Writing Testbenches：覆蓋率相關章節**
  - 覆蓋率驅動的驗證流程

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 40 | Verilator 使用指南：Coverage 與 verilator_coverage | 程式碼覆蓋率：行、分支、條件、狀態機、翻轉（toggle）；Verilator 的 `--coverage` 與 `verilator_coverage`<br>功能覆蓋率：覆蓋群組與覆蓋點的設計；覆蓋率的『洞』要用新測試去填，而不是為了數字寫無意義的測試 | `v048` | — |
| 41 | Bergeron, Writing Testbenches：覆蓋率相關章節 | 回歸：測試清單、多種子、平行執行、結果彙總；失敗時保存種子與波形；與版本控制整合<br>覆蓋率 100% 不代表沒有 bug；它只告訴你哪些地方『肯定沒測到』 | `v049` | 替最小系統建立回歸：100 個種子、平行執行、覆蓋率彙總、失敗保存波形；週報（HTML 或文字）自動產生<br>**單元檢核** |

**作品驗收**（7 天內，逐條對照）：
- [ ] 回歸系統一行指令可執行並產生報告
- [ ] 覆蓋率報告與補洞紀錄
- [ ] 失敗可用種子重現

#### 單元 23：UVM 概念與方法學（第 42–43 週）

**目標**：理解 UVM 的架構與用法，能讀懂並修改現有的 UVM 環境。

**學什麼**
- UVM 的目的：標準化可重用的驗證元件；架構：test→env→agent（sequencer／driver／monitor）、scoreboard、sequence、sequence item、config_db、factory、phase（build／connect／run…）、TLM 埠
- 常見流程：先寫 sequence item 與 sequence，再寫 driver 與 monitor，組成 agent，最後組成 env 與 test
- 與自己寫的分層測試平台的對應：每個 UVM 元件都是前面單元自己寫過的東西的標準化
- 限制（誠實）：完整的 UVM 需要支援它的模擬器（多為商用）；開源工具對它的支援有限；因此本單元以閱讀與小型練習為主

**待新增題目**：
- `v050` 讀懂一個 UVM 環境：給一個小型 UVM 環境與 log，回答每個元件做什麼、log 每行出自哪個 phase

**實作作業**：
- 把前面自己寫的 SV 驗證環境逐元件對應到 UVM 的元件，寫成對照文件；若有可用的模擬器，改寫其中一個 agent 成 UVM 版

**常見陷阱**：
- 把 UVM 當成目的：小設計用 UVM 只是增加負擔
- build_phase 與 connect_phase 的順序弄錯

**自我檢查**：
- config_db 解決什麼問題？
- factory 為什麼能讓你替換元件而不改程式碼？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **UVM 使用者指南（Accellera 的 UVM 1.2 User's Guide）**
  - 架構概觀、元件、sequence、phase、TLM
- **Spear & Tumbush：UVM 相關附錄或章節（若為新版）**
  - 與傳統 SV 測試平台的對照

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 42 | UVM 使用者指南（Accellera 的 UVM 1.2 User's Guide） | UVM 的目的：標準化可重用的驗證元件；架構：test→env→agent（sequencer／driver／monitor）、scoreboard、sequence、sequence item、config_db、factory、phase（build／connect／run…）、TLM 埠<br>常見流程：先寫 sequence item 與 sequence，再寫 driver 與 monitor，組成 agent，最後組成 env 與 test | `v050` | — |
| 43 | Spear & Tumbush：UVM 相關附錄或章節（若為新版） | 與自己寫的分層測試平台的對應：每個 UVM 元件都是前面單元自己寫過的東西的標準化<br>限制（誠實）：完整的 UVM 需要支援它的模擬器（多為商用）；開源工具對它的支援有限；因此本單元以閱讀與小型練習為主 | — | 把前面自己寫的 SV 驗證環境逐元件對應到 UVM 的元件，寫成對照文件；若有可用的模擬器，改寫其中一個 agent 成 UVM 版<br>**單元檢核** |

**作品驗收**（7 天內，逐條對照）：
- [ ] UVM 元件與自己環境的對照文件
- [ ] 能讀懂一份 UVM log 並指出問題所在 phase
- [ ] 說明在什麼規模的專案值得用 UVM

#### 單元 24：階段 V2 驗收週（第 44 週）

**目標**：替一個完整設計建立驗證計畫、環境、覆蓋率與回歸。

**學什麼**
- 整合：替管線 CPU 建立驗證計畫（指令覆蓋、危障覆蓋）、cocotb 或 SV 環境、形式驗證幾個性質、覆蓋率與回歸

**實作作業**：
- 完成管線 CPU 的驗證報告：計畫、環境、覆蓋率、形式證明、已找到的 bug 清單

**自我檢查**：
- 如果只剩一週，我會先驗證什麼？為什麼？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Bergeron：驗證計畫範例**
  - 把計畫寫成可追蹤的清單

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 44 | Bergeron：驗證計畫範例 | 整合：替管線 CPU 建立驗證計畫（指令覆蓋、危障覆蓋）、cocotb 或 SV 環境、形式驗證幾個性質、覆蓋率與回歸 | — | 完成管線 CPU 的驗證報告：計畫、環境、覆蓋率、形式證明、已找到的 bug 清單<br>**單元檢核** |

**作品驗收**（10 天內，逐條對照）：
- [ ] 驗證計畫與追蹤表
- [ ] 指令覆蓋與危障覆蓋的報告
- [ ] 至少 3 個形式證明的性質
- [ ] 找到的 bug 清單（含根因）

### 階段 V3：合成、時序與實體流程

能合成、讀寫 SDC、做時序分析與收斂、低功耗與 DFT 概念，並用開源流程做到版圖或 FPGA。

#### 單元 25：邏輯合成（第 45–46 週）

**目標**：能用 Yosys 把 RTL 合成成閘級網表，並看懂報告。

**學什麼**
- 合成流程：解析→細化（`proc`）→最佳化（`opt`）→技術無關映射→技術映射（`abc` 用 liberty 製程庫）→網表；`synth -top`、`stat -liberty`
- 報告：單元數、面積、關鍵路徑的邏輯層數；約束（時脈週期）如何影響 abc 的最佳化
- 製程庫（liberty）：單元的面積、延遲表（輸入轉換時間×輸出負載）、功耗；開源製程如 SkyWater SKY130、GF180MCU
- 檢查合成結果：與 RTL 做等價性檢查（`equiv_*` 指令）、閘級模擬

**待新增題目**：
- `v051` 讀合成報告：給 Yosys 報告，回答面積來源與可改善之處
- `v052` 約束與面積：同一設計在三種時脈週期下合成，整理面積變化

**實作作業**：
- 用 Yosys 與 SKY130 liberty 合成 CPU，產生面積報告；改變時脈約束 5 次，整理面積與關鍵路徑變化；用 `equiv` 驗證網表與 RTL 等價

**常見陷阱**：
- 把合成面積當成最終面積（還沒有佈線與緩衝）
- 看不懂 liberty 的單位（ns／pF）

**自我檢查**：
- `abc` 的時脈約束會改變什麼？
- 合成與擺置繞線之後的面積為什麼會不同？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Yosys 手冊：合成流程（`synth`）、`abc`、`stat`、`dfflibmap`**
  - 各階段做什麼、怎麼讀 stat 輸出
- **SkyWater SKY130 PDK 文件：標準單元庫**
  - 單元命名與 liberty 檔的位置
- **Weste & Harris, CMOS VLSI Design：邏輯努力（logical effort）相關章節**
  - 為什麼延遲和扇出有關

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 45 | Yosys 手冊：合成流程（`synth`）、`abc`、`stat`、`dfflibmap`<br>SkyWater SKY130 PDK 文件：標準單元庫 | 合成流程：解析→細化（`proc`）→最佳化（`opt`）→技術無關映射→技術映射（`abc` 用 liberty 製程庫）→網表；`synth -top`、`stat -liberty`<br>報告：單元數、面積、關鍵路徑的邏輯層數；約束（時脈週期）如何影響 abc 的最佳化 | `v051` | — |
| 46 | Weste & Harris, CMOS VLSI Design：邏輯努力（logical effort）相關章節 | 製程庫（liberty）：單元的面積、延遲表（輸入轉換時間×輸出負載）、功耗；開源製程如 SkyWater SKY130、GF180MCU<br>檢查合成結果：與 RTL 做等價性檢查（`equiv_*` 指令）、閘級模擬 | `v052` | 用 Yosys 與 SKY130 liberty 合成 CPU，產生面積報告；改變時脈約束 5 次，整理面積與關鍵路徑變化；用 `equiv` 驗證網表與 RTL 等價<br>**單元檢核** |

**作品驗收**（7 天內，逐條對照）：
- [ ] CPU 合成報告與 5 組約束的比較表
- [ ] 等價性檢查通過
- [ ] 能說明報告中面積最大的 3 個來源

#### 單元 26：靜態時序分析與 SDC 約束（第 47–48 週）

**目標**：能讀寫 SDC 約束，看懂時序報告並判斷如何修正。

**學什麼**
- STA 的核心：建立時間（setup）與保持時間（hold）、資料到達時間、需求時間、slack = 需求 − 到達；最大頻率受關鍵路徑與時脈偏斜影響
- SDC（Synopsys Design Constraints，本身是 Tcl 指令）：`create_clock`、`set_input_delay`、`set_output_delay`、`set_clock_uncertainty`、`set_false_path`、`set_multicycle_path`、`set_max_delay`；`get_ports`／`get_clocks`／`get_pins` 取得物件
- 報告怎麼讀：`report_checks`（路徑逐級的延遲、時脈偏斜、slack）、`report_wns`／`report_tns`；hold 違規通常靠插入延遲單元修
- 常見約束錯誤：漏了時脈、漏了 I/O 延遲、過度使用 false path 掩蓋真正的問題

**待新增題目**：
- `v053` 寫 SDC：給設計與時序規格，寫出完整 SDC，用 OpenSTA 檢查沒有未約束路徑
- `v054` 讀時序報告：給 report_checks 輸出，指出違規原因與修正方式

**實作作業**：
- 用 OpenSTA（或 OpenROAD 內的 sta）對 CPU 的合成網表寫 SDC、跑時序分析；找出 5 條最差路徑並解釋；調整約束與 RTL 讓 WNS ≥ 0

**常見陷阱**：
- 把沒約束的路徑當成沒問題
- 只看 setup 不看 hold

**自我檢查**：
- slack 為負的路徑可以怎麼修？hold 違規呢？
- multicycle path 約束要在什麼條件下才安全？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **OpenSTA 文件：SDC 支援與報告指令**
  - `read_liberty`、`read_verilog`、`link_design`、`read_sdc`、`report_checks`
- **Bhasker & Chadha, Static Timing Analysis for Nanometer Designs**
  - 時序檢查、時脈、約束的完整說明
- **Weste & Harris, CMOS VLSI Design：時序相關章節**
  - 延遲模型、偏斜與抖動

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 47 | OpenSTA 文件：SDC 支援與報告指令<br>Bhasker & Chadha, Static Timing Analysis for Nanometer Designs | STA 的核心：建立時間（setup）與保持時間（hold）、資料到達時間、需求時間、slack = 需求 − 到達；最大頻率受關鍵路徑與時脈偏斜影響<br>SDC（Synopsys Design Constraints，本身是 Tcl 指令）：`create_clock`、`set_input_delay`、`set_output_delay`、`set_clock_uncertainty`、`set_false_path`、`set_multicycle_path`、`set_max_delay`；`get_ports`／`get_clocks`／`get_pins` 取得物件 | `v053` | — |
| 48 | Weste & Harris, CMOS VLSI Design：時序相關章節 | 報告怎麼讀：`report_checks`（路徑逐級的延遲、時脈偏斜、slack）、`report_wns`／`report_tns`；hold 違規通常靠插入延遲單元修<br>常見約束錯誤：漏了時脈、漏了 I/O 延遲、過度使用 false path 掩蓋真正的問題 | `v054` | 用 OpenSTA（或 OpenROAD 內的 sta）對 CPU 的合成網表寫 SDC、跑時序分析；找出 5 條最差路徑並解釋；調整約束與 RTL 讓 WNS ≥ 0<br>**單元檢核** |

**作品驗收**（7 天內，逐條對照）：
- [ ] 完整 SDC（無未約束路徑）與 OpenSTA 報告
- [ ] 最差 5 條路徑的逐級分析
- [ ] WNS ≥ 0 的修正紀錄（RTL 與約束各改了什麼）

#### 單元 27：時序收斂與 RTL 最佳化（第 49–50 週）

**目標**：能用 RTL 層級的手法改善時序、面積與功耗。

**學什麼**
- 時序：加管線、重定時（retiming）、降低邏輯層數、降低扇出（複製暫存器）、把進位鏈切短；用 `report_checks` 找下一條路徑
- 面積：資源共用、減少位元寬度、避免不必要的重置（資料路徑暫存器通常不需要重置）
- 取捨：吞吐量、延遲、面積、功耗互相牽制；用實驗數據決定，不要憑感覺
- 實驗方法：自動化掃描參數（時脈週期、管線級數），整理成表格與圖

**待新增題目**：
- `v055` 管線化加深：把乘加改成 N 級管線，量測最大頻率與面積隨 N 的變化

**實作作業**：
- 對 CPU 或乘加單元做 3 輪最佳化（各一個假設、一個修改、前後數據），整理成實驗紀錄；用腳本（Tcl 或 Python）自動掃描時脈週期與管線級數

**常見陷阱**：
- 同時改多個東西導致不知道哪個有效
- 加管線後忘了修正控制訊號的對齊

**自我檢查**：
- 加一級管線一定會讓頻率變高嗎？什麼時候不會？
- 為什麼資料路徑暫存器常不需要重置？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Weste & Harris, CMOS VLSI Design：Datapath、Timing Optimization 相關章節**
  - 縮短關鍵路徑的各種技巧
- **Harris & Harris《Microarchitecture》（第 7 章）**
  - 管線化與效能：吞吐量、延遲與時脈頻率的取捨

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 49 | Weste & Harris, CMOS VLSI Design：Datapath、Timing Optimization 相關章節 | 時序：加管線、重定時（retiming）、降低邏輯層數、降低扇出（複製暫存器）、把進位鏈切短；用 `report_checks` 找下一條路徑<br>面積：資源共用、減少位元寬度、避免不必要的重置（資料路徑暫存器通常不需要重置） | `v055` | — |
| 50 | Harris & Harris《Microarchitecture》（第 7 章） | 取捨：吞吐量、延遲、面積、功耗互相牽制；用實驗數據決定，不要憑感覺<br>實驗方法：自動化掃描參數（時脈週期、管線級數），整理成表格與圖 | — | 對 CPU 或乘加單元做 3 輪最佳化（各一個假設、一個修改、前後數據），整理成實驗紀錄；用腳本（Tcl 或 Python）自動掃描時脈週期與管線級數<br>**單元檢核** |

**作品驗收**（7 天內，逐條對照）：
- [ ] 3 輪最佳化的實驗紀錄（假設、修改、數據、結論）
- [ ] 自動掃描腳本與結果圖表
- [ ] 最佳化後仍通過全部回歸

#### 單元 28：低功耗設計（第 51–52 週）

**目標**：理解功耗的來源，並在 RTL 層級套用常見的降功耗技巧。

**學什麼**
- 功耗來源：動態（切換功耗 ≈ α·C·V²·f、短路）與靜態（漏電）；活動因子 α；電壓與頻率的影響
- RTL 技巧：時脈閘控（clock gating，要用閂鎖式閘控單元避免毛刺）、運算元隔離（operand isolation）、資料閘控、降低不必要的切換
- 架構層技巧：多電壓域、電源閘控（power gating）、動態電壓頻率調整（DVFS）的概念；UPF／CPF 描述電源意圖（概念層級）
- 估算：以模擬產生的切換活動檔（SAIF／VCD）搭配工具估功耗；開源流程中的功耗報告

**待新增題目**：
- `v056` 切換計數：解析 VCD 計算各訊號的活動因子並排序
- `v057` 時脈閘控：實作安全的時脈閘控單元並證明無毛刺

**實作作業**：
- 替乘加單元加入時脈閘控與運算元隔離，用 VCD 活動檔與（OpenSTA 或 OpenROAD 的）功耗報告比較前後；說明犧牲了什麼（面積、時序、複雜度）

**常見陷阱**：
- 不安全的時脈閘控產生毛刺時脈
- 只看平均功耗忽略尖峰電流

**自我檢查**：
- 為什麼降低電壓對功耗的效果特別大？
- 時脈閘控為什麼要用閂鎖？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Weste & Harris, CMOS VLSI Design：Power 相關章節**
  - 動態與靜態功耗的來源與公式
- **OpenSTA 文件：`report_power`**
  - 如何以活動檔估功耗

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 51 | Weste & Harris, CMOS VLSI Design：Power 相關章節 | 功耗來源：動態（切換功耗 ≈ α·C·V²·f、短路）與靜態（漏電）；活動因子 α；電壓與頻率的影響<br>RTL 技巧：時脈閘控（clock gating，要用閂鎖式閘控單元避免毛刺）、運算元隔離（operand isolation）、資料閘控、降低不必要的切換 | `v056` | — |
| 52 | OpenSTA 文件：`report_power` | 架構層技巧：多電壓域、電源閘控（power gating）、動態電壓頻率調整（DVFS）的概念；UPF／CPF 描述電源意圖（概念層級）<br>估算：以模擬產生的切換活動檔（SAIF／VCD）搭配工具估功耗；開源流程中的功耗報告 | `v057` | 替乘加單元加入時脈閘控與運算元隔離，用 VCD 活動檔與（OpenSTA 或 OpenROAD 的）功耗報告比較前後；說明犧牲了什麼（面積、時序、複雜度）<br>**單元檢核** |

**作品驗收**（7 天內，逐條對照）：
- [ ] 閘控前後的功耗與面積／時序比較
- [ ] 閘控單元的毛刺安全性說明與波形
- [ ] 活動因子分析與最耗電的 5 個訊號

#### 單元 29：可測試性設計（DFT）與測試（第 53–54 週）

**目標**：理解掃描鏈、故障模型與測試產生的基本概念。

**學什麼**
- 製造缺陷與故障模型：固定型故障（stuck-at 0／1）、轉換故障；測試覆蓋率與測試向量數
- 掃描設計：把正反器換成掃描正反器（多一個多工器），串成掃描鏈；移入、擷取、移出三階段；掃描致能訊號
- ATPG 的概念：由故障反推輸入向量；BIST（記憶體內建自我測試）；邊界掃描與 JTAG（TCK、TMS、TDI、TDO）
- DFT 的成本：面積、時序（多工器延遲）、腳位；以及為什麼它對良率與量產不可或缺

**待新增題目**：
- `v058` 掃描鏈：把一個計數器改成帶掃描鏈的版本，用測試台移入移出驗證
- `v059` 固定型故障模擬：對小型組合電路窮舉單一故障並算覆蓋率

**實作作業**：
- 替小型設計手動插入掃描鏈（或用開源工具如 Yosys／OpenROAD 的掃描相關功能，若可用），用測試台示範移入、擷取、移出；寫一個窮舉單一固定型故障的小程式算覆蓋率

**常見陷阱**：
- 掃描模式下的時序與功能模式不同
- 沒考慮掃描帶來的保持時間問題

**自我檢查**：
- 固定型故障模型的假設是什麼？
- 掃描鏈如何把循序電路的測試化簡為組合電路的測試？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Bushnell & Agrawal, Essentials of Electronic Testing for Digital, Memory and Mixed-Signal VLSI Circuits**
  - 故障模型、掃描、ATPG、BIST 的完整說明
- **Weste & Harris, CMOS VLSI Design：Testing 一章**
  - 可測試性設計的入門說明

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 53 | Bushnell & Agrawal, Essentials of Electronic Testing for Digital, Memory and Mixed-Signal VLSI Circuits | 製造缺陷與故障模型：固定型故障（stuck-at 0／1）、轉換故障；測試覆蓋率與測試向量數<br>掃描設計：把正反器換成掃描正反器（多一個多工器），串成掃描鏈；移入、擷取、移出三階段；掃描致能訊號 | `v058` | — |
| 54 | Weste & Harris, CMOS VLSI Design：Testing 一章 | ATPG 的概念：由故障反推輸入向量；BIST（記憶體內建自我測試）；邊界掃描與 JTAG（TCK、TMS、TDI、TDO）<br>DFT 的成本：面積、時序（多工器延遲）、腳位；以及為什麼它對良率與量產不可或缺 | `v059` | 替小型設計手動插入掃描鏈（或用開源工具如 Yosys／OpenROAD 的掃描相關功能，若可用），用測試台示範移入、擷取、移出；寫一個窮舉單一固定型故障的小程式算覆蓋率<br>**單元檢核** |

**作品驗收**（7 天內，逐條對照）：
- [ ] 帶掃描鏈的設計與測試台（移入、擷取、移出）
- [ ] 固定型故障覆蓋率程式與結果
- [ ] 說明 DFT 對面積與時序的代價

#### 單元 30：擺置繞線與簽核（開源流程）（第 55–56 週）

**目標**：能用開源流程把 RTL 一路做到版圖，並看懂簽核檢查。

**學什麼**
- 流程：合成→平面規劃（floorplan）→電源網路→擺置（global／detailed）→時脈樹合成（CTS）→繞線（global／detailed）→簽核（寄生萃取、時序、DRC、LVS、天線效應）
- 開源工具：Yosys（合成）、OpenROAD（floorplan、placement、CTS、routing）、OpenSTA、Magic 與 KLayout（版圖檢視與 DRC）、Netgen（LVS）；OpenLane 把它們串成流程
- 設計規則檢查（DRC）：最小寬度、間距；版圖對線路圖比對（LVS）：版圖萃取的網表要與合成網表一致
- 讀報告：利用率、擁塞、時序（含時脈樹偏斜）、天線違規；調整約束與平面規劃來收斂

**待新增題目**：
- `v060` 讀 OpenLane 報告：給一份流程輸出，指出時序、擁塞、DRC 的問題與對策

**實作作業**：
- 用 OpenLane 與 SKY130 把一個小設計（例如計數器或 UART）從 RTL 做到 GDS，通過 DRC 與 LVS；改變利用率與時脈週期各 3 次，整理 QoR（面積、WNS、功耗）表

**常見陷阱**：
- 利用率太高造成繞線擁塞或不收斂
- 沒有檢查 LVS 就以為版圖正確

**自我檢查**：
- CTS 為什麼會影響保持時間？
- LVS 比對的是什麼和什麼？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **OpenLane 文件：Getting Started 與流程說明**
  - 設定檔、各步驟的輸出與常見失敗
- **OpenROAD 文件：Floorplan、Placement、CTS、Routing 各模組**
  - 指令與參數的意義
- **SkyWater SKY130 PDK 文件：設計規則**
  - DRC 規則的來源

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 55 | OpenLane 文件：Getting Started 與流程說明<br>OpenROAD 文件：Floorplan、Placement、CTS、Routing 各模組 | 流程：合成→平面規劃（floorplan）→電源網路→擺置（global／detailed）→時脈樹合成（CTS）→繞線（global／detailed）→簽核（寄生萃取、時序、DRC、LVS、天線效應）<br>開源工具：Yosys（合成）、OpenROAD（floorplan、placement、CTS、routing）、OpenSTA、Magic 與 KLayout（版圖檢視與 DRC）、Netgen（LVS）；OpenLane 把它們串成流程 | `v060` | — |
| 56 | SkyWater SKY130 PDK 文件：設計規則 | 設計規則檢查（DRC）：最小寬度、間距；版圖對線路圖比對（LVS）：版圖萃取的網表要與合成網表一致<br>讀報告：利用率、擁塞、時序（含時脈樹偏斜）、天線違規；調整約束與平面規劃來收斂 | — | 用 OpenLane 與 SKY130 把一個小設計（例如計數器或 UART）從 RTL 做到 GDS，通過 DRC 與 LVS；改變利用率與時脈週期各 3 次，整理 QoR（面積、WNS、功耗）表<br>**單元檢核** |

**作品驗收**（10 天內，逐條對照）：
- [ ] 小設計的 GDS，DRC 與 LVS 皆乾淨（附報告）
- [ ] QoR 變化表（利用率、時脈週期）
- [ ] 能口頭說明流程每一步的輸入與輸出

#### 單元 31：FPGA 實作（第 57–58 週）

**目標**：能把 RTL 實作到 FPGA，處理約束與時序，並在板子上跑起來。

**學什麼**
- FPGA 的資源：LUT、正反器、block RAM、DSP、時脈管理（PLL／MMCM）、I/O 標準；RTL 寫法如何映射到這些資源
- 流程：合成→實作（擺置繞線）→產生位元流→燒錄；約束檔（XDC 或 PCF／LPF）：腳位與時脈
- 開源工具鏈：Yosys＋nextpnr＋位元流工具（Project IceStorm 支援 iCE40、Project Trellis 支援 ECP5）；廠商工具（例如 Vivado）以 Tcl 腳本操作
- 板上除錯：LED、UART 輸出、內嵌邏輯分析儀（廠商提供）；時序報告與實際行為的對照

**待新增題目**：
- `v061` 腳位約束：給板子規格寫腳位約束，檢查是否有未約束的 I/O

**實作作業**：
- 把 UART 回送或最小 SoC 實作到一塊 FPGA 板（開源可支援的板如 iCEBreaker 或 ULX3S，或自己有的板），附時序報告、資源使用量與板上運作的照片或影片

**常見陷阱**：
- 忘了約束時脈導致時序沒有被檢查
- 把模擬用的 initial 當成可靠的初始化

**自我檢查**：
- block RAM 與分散式 RAM（LUT RAM）各適合什麼情況？
- 為什麼要約束時脈？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **nextpnr 文件與範例專案**
  - iCE40 或 ECP5 的完整流程範例
- **Yosys 手冊：`synth_ice40`／`synth_ecp5`**
  - 針對 FPGA 的合成指令

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 57 | nextpnr 文件與範例專案 | FPGA 的資源：LUT、正反器、block RAM、DSP、時脈管理（PLL／MMCM）、I/O 標準；RTL 寫法如何映射到這些資源<br>流程：合成→實作（擺置繞線）→產生位元流→燒錄；約束檔（XDC 或 PCF／LPF）：腳位與時脈 | `v061` | — |
| 58 | Yosys 手冊：`synth_ice40`／`synth_ecp5` | 開源工具鏈：Yosys＋nextpnr＋位元流工具（Project IceStorm 支援 iCE40、Project Trellis 支援 ECP5）；廠商工具（例如 Vivado）以 Tcl 腳本操作<br>板上除錯：LED、UART 輸出、內嵌邏輯分析儀（廠商提供）；時序報告與實際行為的對照 | — | 把 UART 回送或最小 SoC 實作到一塊 FPGA 板（開源可支援的板如 iCEBreaker 或 ULX3S，或自己有的板），附時序報告、資源使用量與板上運作的照片或影片<br>**單元檢核** |

**作品驗收**（10 天內，逐條對照）：
- [ ] FPGA 上可運作的設計（影片或照片）
- [ ] 時序與資源使用報告
- [ ] 腳位與時脈約束檔

#### 單元 32：階段 V3 驗收週（第 59 週）

**目標**：把一個完整設計從 RTL 做到版圖或 FPGA，附完整報告。

**學什麼**
- 整合：選前面做過的 CPU 或加速器，完成『RTL→驗證→合成→STA→實體或 FPGA』的完整流程報告

**實作作業**：
- 完成流程報告：每一步的輸入、工具、指令、輸出與發現的問題

**自我檢查**：
- 如果重做一次，最先會改變哪一步？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **OpenLane 文件：Reproducibility 與設定管理**
  - 讓整個流程可重現

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 59 | OpenLane 文件：Reproducibility 與設定管理 | 整合：選前面做過的 CPU 或加速器，完成『RTL→驗證→合成→STA→實體或 FPGA』的完整流程報告 | — | 完成流程報告：每一步的輸入、工具、指令、輸出與發現的問題<br>**單元檢核** |

**作品驗收**（10 天內，逐條對照）：
- [ ] 可重現的完整流程（一行指令）
- [ ] 每一步的報告與問題紀錄
- [ ] 最終 QoR 表（面積、時序、功耗）

### 階段 V4：SoC、專題與職涯

能整合 SoC、完成處理器、加速器與下線流程三個專題，並通過面試等級的說明。

#### 單元 33：匯流排與周邊介面（第 60–61 週）

**目標**：能設計符合協定的匯流排從裝置與常見周邊控制器。

**學什麼**
- 匯流排協定：APB（簡單）、AXI4-Lite（五個通道 AW／W／B／AR／R）、AXI4-Stream（TVALID／TREADY／TLAST）、Wishbone；各通道獨立的握手
- 記憶體映射暫存器：位址解碼、讀寫、唯讀／唯寫／清除型暫存器、中斷旗標
- 周邊控制器：UART、SPI、I2C、GPIO、計時器；各自的協定時序
- 驗證匯流排：協定檢查器（斷言）、隨機交易、對拍參考模型

**待新增題目**：
- `v062` APB 從裝置：帶 4 個暫存器與中斷旗標，隨機讀寫測試
- `v063` AXI4-Lite 從裝置：五通道握手，含背壓
- `v064` SPI 主控制器：模式 0–3，與模型比對波形

**實作作業**：
- 實作 AXI4-Lite 從裝置（暫存器檔）與 SPI 主控制器，用 cocotb 或 SV 驗證環境加上協定斷言，跑隨機回歸

**常見陷阱**：
- AXI 各通道的相依規則（例如寫位址與寫資料的先後）實作錯誤
- 中斷旗標清除與設置同時發生的競爭

**自我檢查**：
- AXI 為什麼把讀寫位址與資料分成獨立的通道？
- AXI4-Lite 與完整 AXI4 差在哪？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Arm AMBA AXI 與 APB 協定規格（可免費下載）**
  - 通道、握手規則、回應碼
- **Harris & Harris《I/O Systems》（第 9 章）**
  - I/O 系統：記憶體映射 I/O、周邊與匯流排
- **Wishbone B4 規格**
  - 開源 IP 常用的簡單匯流排

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 60 | Arm AMBA AXI 與 APB 協定規格（可免費下載）<br>Harris & Harris《I/O Systems》（第 9 章） | 匯流排協定：APB（簡單）、AXI4-Lite（五個通道 AW／W／B／AR／R）、AXI4-Stream（TVALID／TREADY／TLAST）、Wishbone；各通道獨立的握手<br>記憶體映射暫存器：位址解碼、讀寫、唯讀／唯寫／清除型暫存器、中斷旗標 | `v062`、`v063` | — |
| 61 | Wishbone B4 規格 | 周邊控制器：UART、SPI、I2C、GPIO、計時器；各自的協定時序<br>驗證匯流排：協定檢查器（斷言）、隨機交易、對拍參考模型 | `v064` | 實作 AXI4-Lite 從裝置（暫存器檔）與 SPI 主控制器，用 cocotb 或 SV 驗證環境加上協定斷言，跑隨機回歸<br>**單元檢核** |

**作品驗收**（10 天內，逐條對照）：
- [ ] AXI4-Lite 從裝置與 SPI 主控制器通過隨機回歸
- [ ] 協定斷言無違規
- [ ] 附時序圖

#### 單元 34：SoC 整合與韌體（第 62–63 週）

**目標**：能把 CPU、匯流排、記憶體與周邊整合成最小 SoC，並在上面跑 C 程式。

**學什麼**
- SoC 的組成：CPU、匯流排互連（crossbar 或簡單位址解碼）、ROM／RAM、周邊、中斷控制器；記憶體映射圖
- 韌體：用 RISC-V 的 GCC 工具鏈（riscv32 的 gcc／binutils）編譯 C、連結腳本、啟動程式碼（crt0）、產生 hex 載入模擬
- 聯合模擬：在模擬中執行韌體、透過 UART 輸出、用斷言或暫存器值判斷通過
- 除錯：波形與韌體 log 對照；硬體與軟體分工界線

**待新增題目**：
- `v065` 記憶體映射圖：給周邊清單，產生位址解碼並用測試驗證無重疊

**實作作業**：
- 整合 CPU＋RAM＋UART＋計時器＋GPIO 成最小 SoC，用 riscv32 工具鏈編譯 C 程式（印出費氏數列、跑排序）並在模擬與 FPGA 上執行

**常見陷阱**：
- 連結腳本的位址與硬體記憶體映射不一致
- 韌體與硬體的位元組序或對齊假設不同

**自我檢查**：
- 啟動程式碼（crt0）做了哪些事？
- 怎麼知道 bug 在韌體還是硬體？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Harris & Harris《I/O Systems》（第 9 章）**
  - I/O 與嵌入式系統：記憶體映射與驅動程式
- **RISC-V GNU 工具鏈文件**
  - 交叉編譯、連結腳本、`objcopy` 產生 hex

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 62 | Harris & Harris《I/O Systems》（第 9 章） | SoC 的組成：CPU、匯流排互連（crossbar 或簡單位址解碼）、ROM／RAM、周邊、中斷控制器；記憶體映射圖<br>韌體：用 RISC-V 的 GCC 工具鏈（riscv32 的 gcc／binutils）編譯 C、連結腳本、啟動程式碼（crt0）、產生 hex 載入模擬 | `v065` | — |
| 63 | RISC-V GNU 工具鏈文件 | 聯合模擬：在模擬中執行韌體、透過 UART 輸出、用斷言或暫存器值判斷通過<br>除錯：波形與韌體 log 對照；硬體與軟體分工界線 | — | 整合 CPU＋RAM＋UART＋計時器＋GPIO 成最小 SoC，用 riscv32 工具鏈編譯 C 程式（印出費氏數列、跑排序）並在模擬與 FPGA 上執行<br>**單元檢核** |

**作品驗收**（14 天內，逐條對照）：
- [ ] SoC 在模擬與 FPGA（或僅模擬）上執行 C 程式並經 UART 輸出
- [ ] 記憶體映射圖與連結腳本
- [ ] 整合測試自動化

#### 單元 35：專題一：可合成的 RISC-V 核心（第 64–66 週）

**目標**：完成一顆有完整驗證、合成與報告的 RISC-V 核心。

**學什麼**
- 範圍：RV32I＋（可選）M 擴充（乘除）、五級管線、轉送與停頓；驗證：與參考模型逐指令比對＋官方相容測試（riscv-arch-test 若可用）＋形式驗證關鍵性質
- 合成與實體：Yosys 合成、OpenSTA 時序、OpenLane 至 GDS 或 FPGA 實作
- 文件：架構圖、介面說明、驗證計畫與結果、QoR 表、已知限制

**實作作業**：
- 完成專題並以 README 與報告呈現；公開在版本控制平台並附可重現的指令

**自我檢查**：
- 我的核心與公開的小型核心（例如 PicoRV32、Ibex）相比，差在哪、為什麼？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Harris & Harris《Microarchitecture》（第 7 章）**
  - 回顧：微架構與管線危障
- **RISC-V Unprivileged ISA 規格（M 擴充）**
  - 乘除指令語意

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 64 | Harris & Harris《Microarchitecture》（第 7 章） | 範圍：RV32I＋（可選）M 擴充（乘除）、五級管線、轉送與停頓；驗證：與參考模型逐指令比對＋官方相容測試（riscv-arch-test 若可用）＋形式驗證關鍵性質 | — | — |
| 65 | RISC-V Unprivileged ISA 規格（M 擴充） | 合成與實體：Yosys 合成、OpenSTA 時序、OpenLane 至 GDS 或 FPGA 實作 | — | — |
| 66 | — | 文件：架構圖、介面說明、驗證計畫與結果、QoR 表、已知限制 | — | 完成專題並以 README 與報告呈現；公開在版本控制平台並附可重現的指令<br>**單元檢核** |

**作品驗收**（28 天內，逐條對照）：
- [ ] 通過指令級比對與相容測試（附結果）
- [ ] 至少 3 個形式驗證的性質
- [ ] 合成、時序與（FPGA 或 GDS）報告
- [ ] README：架構、驗證、QoR、限制；他人可一行指令重現

#### 單元 36：專題二：硬體加速器（第 67–69 週）

**目標**：設計一個針對特定運算的加速器，並以數據說明它比軟體快多少。

**學什麼**
- 候選：矩陣乘法／卷積引擎（MAC 陣列）、FFT、CRC／雜湊（SHA-256）、AES、排序網路；選一個有明確參考實作的
- 方法：先寫軟體參考與基準 → 設計架構（資料流、平行度、記憶體頻寬）→ RTL → 驗證 → 合成取得頻率與面積 → 與軟體比較吞吐量與能效
- 記憶體頻寬常是瓶頸：資料搬運比運算更昂貴；用雙緩衝與重用降低搬運
- 報告：PPA（效能、功耗、面積）的取捨與設計空間探索

**實作作業**：
- 完成加速器（含介面：AXI4-Stream 或匯流排從裝置）、驗證環境、PPA 報告與軟體比較

**常見陷阱**：
- 只比較核心運算時間而忽略資料搬運
- 沒有軟體基準就宣稱加速倍數

**自我檢查**：
- 你的加速器的瓶頸是運算還是記憶體頻寬？怎麼證明？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Hennessy & Patterson, Computer Architecture: A Quantitative Approach：領域專用架構相關章節**
  - 為什麼專用加速器能比通用處理器快與省電
- **Weste & Harris, CMOS VLSI Design：Datapath Subsystems**
  - 算術單元的實作選擇

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 67 | Hennessy & Patterson, Computer Architecture: A Quantitative Approach：領域專用架構相關章節 | 候選：矩陣乘法／卷積引擎（MAC 陣列）、FFT、CRC／雜湊（SHA-256）、AES、排序網路；選一個有明確參考實作的<br>方法：先寫軟體參考與基準 → 設計架構（資料流、平行度、記憶體頻寬）→ RTL → 驗證 → 合成取得頻率與面積 → 與軟體比較吞吐量與能效 | — | — |
| 68 | Weste & Harris, CMOS VLSI Design：Datapath Subsystems | 記憶體頻寬常是瓶頸：資料搬運比運算更昂貴；用雙緩衝與重用降低搬運 | — | — |
| 69 | — | 報告：PPA（效能、功耗、面積）的取捨與設計空間探索 | — | 完成加速器（含介面：AXI4-Stream 或匯流排從裝置）、驗證環境、PPA 報告與軟體比較<br>**單元檢核** |

**作品驗收**（28 天內，逐條對照）：
- [ ] 加速器通過與軟體參考的對拍（含極值與隨機）
- [ ] PPA 報告與設計空間探索（至少 3 個設計點）
- [ ] 與軟體實作的吞吐量與能效比較（說明方法與限制）

#### 單元 37：專題三：下線流程（第 70–72 週）

**目標**：走完一次完整的開源下線流程，產出可送製造或可審查的 GDS。

**學什麼**
- 選擇：小型設計（面積限制）；平台選項如 Tiny Tapeout 這類共乘服務（請查證目前的規格、時程與費用）、或教育晶片的多專案晶圓（MPW）計畫
- 流程：RTL→驗證→OpenLane（或 OpenROAD-flow-scripts）→DRC／LVS 乾淨→時序簽核→寄生萃取後模擬（後模擬）→提交所需檔案與文件
- 常見被退回的原因：DRC／天線／密度規則、接腳與框架不符、文件缺漏
- 沒有實際下線時：做到 GDS 與全部簽核報告也是完整訓練；重點是能獨立走完並說明每步

**實作作業**：
- 完成一個小設計的下線流程：RTL 到 GDS、簽核報告、後模擬；若參加共乘服務，附提交證明；否則附完整可重現的流程與報告

**常見陷阱**：
- 到截止日才第一次跑完整流程
- 只在 RTL 通過驗證就送出，沒做後模擬

**自我檢查**：
- 如果 DRC 在最後一天出現新違規，我的備案是什麼？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Tiny Tapeout 網站與文件**
  - 設計規格、提交流程、時程（請查證最新版本）
- **OpenLane 文件**
  - 設定檔、簽核檢查、常見錯誤
- **SkyWater SKY130 PDK 文件**
  - 設計規則與標準單元庫

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 70 | Tiny Tapeout 網站與文件 | 選擇：小型設計（面積限制）；平台選項如 Tiny Tapeout 這類共乘服務（請查證目前的規格、時程與費用）、或教育晶片的多專案晶圓（MPW）計畫<br>流程：RTL→驗證→OpenLane（或 OpenROAD-flow-scripts）→DRC／LVS 乾淨→時序簽核→寄生萃取後模擬（後模擬）→提交所需檔案與文件 | — | — |
| 71 | OpenLane 文件 | 常見被退回的原因：DRC／天線／密度規則、接腳與框架不符、文件缺漏 | — | — |
| 72 | SkyWater SKY130 PDK 文件 | 沒有實際下線時：做到 GDS 與全部簽核報告也是完整訓練；重點是能獨立走完並說明每步 | — | 完成一個小設計的下線流程：RTL 到 GDS、簽核報告、後模擬；若參加共乘服務，附提交證明；否則附完整可重現的流程與報告<br>**單元檢核** |

**作品驗收**（28 天內，逐條對照）：
- [ ] GDS 與簽核報告（DRC、LVS、時序、天線）全部乾淨
- [ ] 後模擬與 RTL 模擬一致
- [ ] 提交所需文件齊全；可重現的完整流程

#### 單元 38：面試與職涯（第 73–74 週）

**目標**：能在面試中清楚說明 RTL、驗證與時序問題，並整理作品集。

**學什麼**
- RTL 面試常見題：同步／非同步重置、閂鎖、阻塞與非阻塞、FSM 設計、FIFO 深度計算、CDC、時序（setup／hold）、除頻器、握手、奇偶檢查、優先權仲裁
- 驗證面試：驗證計畫、覆蓋率、隨機與定向、斷言、除錯流程；形式驗證的用途與限制
- 職涯方向：前端設計、驗證、後端實體設計、DFT、FPGA、類比（另一條線）；各自需要的技能
- 作品集：把三個專題整理成可閱讀的 README 與簡報；準備 5 分鐘與 30 分鐘兩種版本的講解

**待新增題目**：
- `v066` 白板題庫：20 題常見 RTL 題，每題寫出程式並用測試驗證
- `v067` FIFO 深度計算：給讀寫速率與突發長度，計算所需深度並以模擬驗證

**實作作業**：
- 完成 6 次模擬面試（互相或請人當面試官），整理題目與回答；更新作品集與履歷

**常見陷阱**：
- 只會背答案，不會在白板上推導
- 作品集沒有可重現的證據

**自我檢查**：
- 你能在 10 分鐘內向非技術人員說明你的專題嗎？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **Clifford Cummings 的論文集（CDC、FIFO、合成風格）**
  - 面試常考的題目幾乎都出自這些主題
- **HDLBits：Circuits／Sequential Logic／Finite State Machines｜Sequence recognition、Q8: Design a Mealy FSM、Q5a: Serial two's complementer (Moore FSM)**
  - FSM 白板題的練習來源

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 73 | Clifford Cummings 的論文集（CDC、FIFO、合成風格） | RTL 面試常見題：同步／非同步重置、閂鎖、阻塞與非阻塞、FSM 設計、FIFO 深度計算、CDC、時序（setup／hold）、除頻器、握手、奇偶檢查、優先權仲裁<br>驗證面試：驗證計畫、覆蓋率、隨機與定向、斷言、除錯流程；形式驗證的用途與限制 | `v066` | — |
| 74 | HDLBits：Circuits／Sequential Logic／Finite State Machines｜Sequence recognition、Q8: Design a Mealy FSM、Q5a: Serial two's complementer (Moore FSM) | 職涯方向：前端設計、驗證、後端實體設計、DFT、FPGA、類比（另一條線）；各自需要的技能<br>作品集：把三個專題整理成可閱讀的 README 與簡報；準備 5 分鐘與 30 分鐘兩種版本的講解 | `v067` | 完成 6 次模擬面試（互相或請人當面試官），整理題目與回答；更新作品集與履歷<br>**單元檢核** |

**作品驗收**（14 天內，逐條對照）：
- [ ] 6 次模擬面試紀錄與回饋
- [ ] 20 題白板題的程式與測試
- [ ] 作品集（三個專題＋驗證報告＋流程報告）

#### 單元 39：總驗收：作品集與全真測驗（第 75 週）

**目標**：整合驗收：作品集完整，並在限時內完成 RTL 設計與驗證任務。

**學什麼**
- 整理作品集，並做一次 4 小時的限時任務：給規格，從 RTL 到驗證到合成報告

**實作作業**：
- 完成限時任務與作品集整理

**自我檢查**：
- 我能證明自己具備『數位 IC 設計與驗證工程師』的哪些能力？每項的證據在哪？

**閱讀與重點**（課號與題目名稱都已對照來源核對；書籍只寫章名，章號以你的版本為準）
- **HDLBits：Circuits／Sequential Logic／Finite State Machines｜Q8: Design a Mealy FSM、Q5a: Serial two's complementer (Moore FSM)、Q5b: Serial two's complementer (Mealy FSM)**
  - 回顧經典 FSM 題目的設計與驗證

**每週安排**

| 週 | 閱讀 | 學習重點 | 題目 | 作業／檢核 |
|---|---|---|---|---|
| 75 | HDLBits：Circuits／Sequential Logic／Finite State Machines｜Q8: Design a Mealy FSM、Q5a: Serial two's complementer (Moore FSM)、Q5b: Serial two's complementer (Mealy FSM) | 整理作品集，並做一次 4 小時的限時任務：給規格，從 RTL 到驗證到合成報告 | — | 完成限時任務與作品集整理<br>**單元檢核** |

**作品驗收**（14 天內，逐條對照）：
- [ ] 4 小時限時任務：RTL＋測試台＋合成報告，全部通過
- [ ] 作品集四件齊全：核心、加速器、下線流程、驗證報告；各有 README 與可重現指令
- [ ] 10 分鐘專案講解

## 教材總表

- [HDLBits（線上 Verilog 練習與判題，免費）](https://hdlbits.01xz.net/wiki/Problem_sets)
- [Digital Design and Computer Architecture, RISC-V Edition（Harris & Harris）](https://shop.elsevier.com/books/digital-design-and-computer-architecture-risc-v-edition/harris/978-0-12-820064-3)
- [Icarus Verilog（開源模擬器）](https://steveicarus.github.io/iverilog/)
- [Verilator 使用指南](https://verilator.org/guide/latest/)
- [Yosys 文件（開源合成）](https://yosyshq.readthedocs.io/projects/yosys/en/latest/)
- [SymbiYosys 文件（形式驗證）](https://yosyshq.readthedocs.io/projects/sby/en/latest/)
- [cocotb 文件（用 Python 驗證硬體）](https://docs.cocotb.org/en/stable/)
- [GTKWave（波形檢視）](https://gtkwave.sourceforge.net/)
- [OpenSTA（開源靜態時序分析）](https://github.com/The-OpenROAD-Project/OpenSTA)
- [OpenROAD 文件](https://openroad.readthedocs.io/en/latest/)
- [OpenLane 2 文件](https://openlane2.readthedocs.io/)
- [SkyWater SKY130 PDK 文件](https://skywater-pdk.readthedocs.io/)
- [nextpnr（開源 FPGA 擺置繞線）](https://github.com/YosysHQ/nextpnr)
- [Tiny Tapeout（小型晶片共乘下線）](https://tinytapeout.com/)
- [RISC-V 規格文件](https://riscv.org/specifications/)
- [RISC-V GNU 工具鏈](https://github.com/riscv-collab/riscv-gnu-toolchain)
- [Arm AMBA 規格（AXI、APB）](https://developer.arm.com/architectures/system-architectures/amba/specifications)
- [Wishbone 匯流排規格（OpenCores）](https://opencores.org/howto/wishbone)
- [Sunburst Design：Clifford Cummings 的論文](https://www.sunburst-design.com/papers/)
- Writing Testbenches: Functional Verification of HDL Models（Bergeron）
- SystemVerilog for Verification（Spear & Tumbush）
- Principles of Verifiable RTL Design（Bening & Foster）
- CMOS VLSI Design: A Circuits and Systems Perspective（Weste & Harris）
- Computer Organization and Design, RISC-V Edition（Patterson & Hennessy）
- Static Timing Analysis for Nanometer Designs（Bhasker & Chadha）
- Essentials of Electronic Testing（Bushnell & Agrawal）
- Computer Architecture: A Quantitative Approach（Hennessy & Patterson）
- [UVM 1.2 User's Guide（Accellera）](https://www.accellera.org/downloads/standards/uvm)
- [Tcl 官方教學（8.5 版，第 0–48 課）](https://tcl-lang.org/man/tcl8.5/tutorial/tcltutorial.html)
- [Tcl 8.6 指令手冊](https://www.tcl-lang.org/man/tcl8.6/TclCmd/contents.htm)
- [Tcler's Wiki](https://wiki.tcl-lang.org/)
- [Practical Programming in Tcl and Tk（Welch、Jones、Hobbs）](https://www.beedub.com/book/)
- Tcl and the Tk Toolkit（Ousterhout & Jones）
- [Nagelfar（Tcl 的靜態語法檢查器）](https://nagelfar.sourceforge.net/)
- [Tcllib（Tcl 標準模組庫）](https://core.tcl-lang.org/tcllib/doc/trunk/embedded/index.md)
- Vivado Design Suite Tcl 指令參考（AMD／Xilinx；需註冊）

_網址可能變動，失效請自行搜尋名稱。_

