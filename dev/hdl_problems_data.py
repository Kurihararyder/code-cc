"""Verilog／Tcl 題庫資料。每題有：參考解 ref、故意寫錯的 bad（必須被判失敗），產生器逐題驗證。"""
from __future__ import annotations

import random
from typing import Dict, List, Tuple

Port = Tuple[str, int]


def _decl(direction: str, ports: List[Port]) -> List[str]:
    return [f"{direction} {'[%d:0] ' % (w - 1) if w > 1 else ''}{n}" for n, w in ports]


def template(ins: List[Port], outs: List[Port], clk: bool = False) -> str:
    items = (["input clk"] if clk else []) + _decl("input", ins) + _decl("output", outs)
    return "module top_module(\n    " + ",\n    ".join(items) + "\n);\n    // 在這裡寫你的設計\n\nendmodule\n"


def _wires(prefix_ports: List[Port], suf: str) -> str:
    return "\n".join(f"  wire {'[%d:0] ' % (w - 1) if w > 1 else ''}{n}_{suf};" for n, w in prefix_ports)


def _conn(ports: List[Port], extra: str = "") -> str:
    return ", ".join(f".{n}({n})" for n, _ in ports)


def comb_tb(ins: List[Port], outs: List[Port], n_random: int = 4000) -> str:
    bits = sum(w for _, w in ins)
    regs = "\n".join(f"  reg {'[%d:0] ' % (w - 1) if w > 1 else ''}{n};" for n, w in ins)
    cat_in = ", ".join(n for n, _ in ins)
    cat_d = ", ".join(f"{n}_d" for n, _ in outs)
    cat_r = ", ".join(f"{n}_r" for n, _ in outs)
    dut = ", ".join([f".{n}({n})" for n, _ in ins] + [f".{n}({n}_d)" for n, _ in outs])
    ref = ", ".join([f".{n}({n})" for n, _ in ins] + [f".{n}({n}_r)" for n, _ in outs])
    show_in = " ".join(f"{n}=%h" for n, _ in ins)
    show_o = " ".join(f"{n}=%h" for n, _ in outs)
    if bits <= 16:
        loop = f"for (i = 0; i < {1 << bits}; i = i + 1) begin {{{cat_in}}} = i[{bits - 1}:0]; chk; end"
    else:
        assigns = " ".join(f"{n} = $random;" for n, _ in ins)
        loop = (f"{{{cat_in}}} = 0; chk;  {{{cat_in}}} = ~0; chk;\n"
                f"    for (i = 0; i < {n_random}; i = i + 1) begin {assigns} chk; end")
    return f"""`timescale 1ns/1ps
module tb;
{regs}
{_wires(outs, 'd')}
{_wires(outs, 'r')}
  top_module dut({dut});
  ref_top refm({ref});
  integer i, errs;
  task chk; begin
    #1;
    if ({{{cat_d}}} !== {{{cat_r}}}) begin
      errs = errs + 1;
      if (errs <= 5) $display("MISMATCH 輸入 {show_in}  期望 {show_o}  你的 {show_o}", {cat_in}, {cat_r}, {cat_d});
    end
  end endtask
  initial begin
    errs = 0;
    {loop}
    if (errs == 0) $display("ALL PASS"); else $display("共 %0d 筆不符", errs);
    $finish;
  end
endmodule
"""


def seq_tb(ins: List[Port], outs: List[Port], cycles: int = 4000, bias: Dict[str, str] = None, rst_pulse: int = 60) -> str:
    """同步重置 rst（高電位有效）；每個負緣換新輸入、#1 後比對輸出。"""
    bias = bias or {}
    regs = "\n".join(f"  reg {'[%d:0] ' % (w - 1) if w > 1 else ''}{n};" for n, w in ins)
    cat_d = ", ".join(f"{n}_d" for n, _ in outs)
    cat_r = ", ".join(f"{n}_r" for n, _ in outs)
    dut = ", ".join([".clk(clk)", ".rst(rst)"] + [f".{n}({n})" for n, _ in ins] + [f".{n}({n}_d)" for n, _ in outs])
    ref = ", ".join([".clk(clk)", ".rst(rst)"] + [f".{n}({n})" for n, _ in ins] + [f".{n}({n}_r)" for n, _ in outs])
    show_in = " ".join(f"{n}=%h" for n, _ in ins)
    show_o = " ".join(f"{n}=%h" for n, _ in outs)
    assigns = " ".join(f"{n} = {bias.get(n, '$random')};" for n, _ in ins)
    zero = " ".join(f"{n} = 0;" for n, _ in ins)
    cat_in = ", ".join(n for n, _ in ins) or "1'b0"
    return f"""`timescale 1ns/1ps
module tb;
  reg clk, rst;
{regs}
{_wires(outs, 'd')}
{_wires(outs, 'r')}
  top_module dut({dut});
  ref_top refm({ref});
  integer i, errs;
  always #5 clk = ~clk;
  initial begin
    clk = 0; rst = 1; errs = 0; {zero}
    repeat (3) @(negedge clk);
    rst = 0;
    for (i = 0; i < {cycles}; i = i + 1) begin
      @(negedge clk);
      rst = ($random % {rst_pulse}) == 0;
      {assigns}
      #1;
      if ({{{cat_d}}} !== {{{cat_r}}}) begin
        errs = errs + 1;
        if (errs <= 5) $display("MISMATCH 週期 %0d 輸入 rst=%b {show_in}  期望 {show_o}  你的 {show_o}", i, rst, {cat_in}, {cat_r}, {cat_d});
      end
    end
    if (errs == 0) $display("ALL PASS"); else $display("共 %0d 週期不符", errs);
    $finish;
  end
endmodule
"""


V: Dict[str, dict] = {}


def vprob(pid, unit, title, statement, ins, outs, ref, bad, seq=False, bias=None, require=None, n_random=4000):
    import re
    tbref = ref
    for m in re.findall(r"^module\s+(\w+)", ref, re.M):          # 輔助模組改名，避免和學生定義的同名模組衝突
        tbref = re.sub(r"\b%s\b" % m, "ref_top" if m == "top_module" else "ref_" + m, tbref)
    tb = (seq_tb(ins, outs, bias=bias) if seq else comb_tb(ins, outs, n_random)) + "\n" + tbref
    V[pid] = dict(track="verilog", unit=unit, title=title, statement=statement, template=template(ins, outs, clk=seq and True).replace("input clk", "input clk,\n    input rst") if seq else template(ins, outs),
                  testbench=tb, ref=ref, bad=bad, require=require or [])


# ---------------- Verilog ----------------
vprob("v002", 2, "二補數加減與溢位",
      "輸入兩個 8 位元有號數 `a`、`b` 與 `sub`。`sub=0` 輸出 `y = a + b`，`sub=1` 輸出 `y = a - b`（8 位元，溢出時環繞）。`ovf` 在**有號**結果溢位時為 1。\n\n"
      "提示：加法溢位 = 兩輸入同號、結果變號；減法 `a-b` 等於 `a+(~b)+1`。",
      [("a", 8), ("b", 8), ("sub", 1)], [("y", 8), ("ovf", 1)],
      """module top_module(input [7:0] a, input [7:0] b, input sub, output [7:0] y, output ovf);
  wire [7:0] bb = sub ? ~b : b;
  assign y = a + bb + sub;
  assign ovf = (a[7] == bb[7]) && (y[7] != a[7]);
endmodule""",
      """module top_module(input [7:0] a, input [7:0] b, input sub, output [7:0] y, output ovf);
  assign y = sub ? a - b : a + b;
  assign ovf = 1'b0;
endmodule""")

vprob("v004", 3, "位元組反轉與位元反轉",
      "輸入 32 位元 `in`。`swap` 把四個位元組的順序反轉（`{in[7:0], in[15:8], in[23:16], in[31:24]}`），`rev` 把 32 個位元的順序整個反轉（第 0 位與第 31 位互換……）。\n\n練習：向量選取、串接 `{}`。不要手寫 32 個 assign（可用 `generate`/`for` 或一次串接）。",
      [("in", 32)], [("swap", 32), ("rev", 32)],
      """module top_module(input [31:0] in, output [31:0] swap, output reg [31:0] rev);
  assign swap = {in[7:0], in[15:8], in[23:16], in[31:24]};
  integer i;
  always @* for (i = 0; i < 32; i = i + 1) rev[i] = in[31 - i];
endmodule""",
      """module top_module(input [31:0] in, output [31:0] swap, output [31:0] rev);
  assign swap = {in[7:0], in[15:8], in[23:16], in[31:24]};
  assign rev = swap;
endmodule""")

vprob("v005", 3, "階層式 8 位元加法器",
      "先寫一個 1 位元全加器模組 `full_adder(a, b, cin, sum, cout)`，再在 `top_module` 裡把 8 個 `full_adder` 串成漣波進位加法器：`{cout, sum} = a + b + cin`。\n\n"
      "你的程式必須定義 `full_adder` 並至少實例化它（判題會檢查名稱出現至少兩次）。",
      [("a", 8), ("b", 8), ("cin", 1)], [("sum", 8), ("cout", 1)],
      """module full_adder(input a, input b, input cin, output sum, output cout);
  assign sum = a ^ b ^ cin;
  assign cout = (a & b) | (cin & (a ^ b));
endmodule
module top_module(input [7:0] a, input [7:0] b, input cin, output [7:0] sum, output cout);
  wire [8:0] c;
  assign c[0] = cin;
  genvar i;
  generate for (i = 0; i < 8; i = i + 1) begin : g
    full_adder fa(a[i], b[i], c[i], sum[i], c[i+1]);
  end endgenerate
  assign cout = c[8];
endmodule""",
      """module full_adder(input a, input b, input cin, output sum, output cout);
  assign sum = a ^ b ^ cin;
  assign cout = a & b;
endmodule
module top_module(input [7:0] a, input [7:0] b, input cin, output [7:0] sum, output cout);
  wire [8:0] c;
  assign c[0] = cin;
  genvar i;
  generate for (i = 0; i < 8; i = i + 1) begin : g
    full_adder fa(a[i], b[i], c[i], sum[i], c[i+1]);
  end endgenerate
  assign cout = c[8];
endmodule""", require=[(r"\bfull_adder\b", "必須定義並實例化 full_adder 模組")])

vprob("v006", 4, "8 位元 ALU",
      "`op` 選運算（3 位元）：0 加、1 減、2 AND、3 OR、4 XOR、5 `a` 邏輯左移 `b[2:0]`、6 `a` 邏輯右移 `b[2:0]`、7 `a < b`（無號比較，結果為 0 或 1 放在最低位）。\n\n"
      "旗標：`z` = 結果為 0；`n` = 結果最高位；`c` = 加法的進位輸出／減法的『借位取反』（即 `a>=b` 為 1）；其他運算 `c=0`；`v` = 加減法的有號溢位，其他運算為 0。",
      [("a", 8), ("b", 8), ("op", 3)], [("y", 8), ("z", 1), ("n", 1), ("c", 1), ("v", 1)],
      """module top_module(input [7:0] a, input [7:0] b, input [2:0] op, output reg [7:0] y, output z, output n, output reg c, output reg v);
  wire [8:0] add = {1'b0, a} + {1'b0, b};
  wire [8:0] sub = {1'b0, a} + {1'b0, ~b} + 9'd1;
  always @* begin
    c = 0; v = 0;
    case (op)
      0: begin y = add[7:0]; c = add[8]; v = (a[7] == b[7]) && (y[7] != a[7]); end
      1: begin y = sub[7:0]; c = sub[8]; v = (a[7] != b[7]) && (y[7] != a[7]); end
      2: y = a & b;
      3: y = a | b;
      4: y = a ^ b;
      5: y = a << b[2:0];
      6: y = a >> b[2:0];
      default: y = {7'b0, a < b};
    endcase
  end
  assign z = (y == 0);
  assign n = y[7];
endmodule""",
      """module top_module(input [7:0] a, input [7:0] b, input [2:0] op, output reg [7:0] y, output z, output n, output reg c, output reg v);
  wire [8:0] add = {1'b0, a} + {1'b0, b};
  wire [8:0] sub = {1'b0, a} - {1'b0, b};
  always @* begin
    c = 0; v = 0;
    case (op)
      0: begin y = add[7:0]; c = add[8]; v = (a[7] == b[7]) && (y[7] != a[7]); end
      1: begin y = sub[7:0]; c = sub[8]; v = (a[7] != b[7]) && (y[7] != a[7]); end
      2: y = a & b;
      3: y = a | b;
      4: y = a ^ b;
      5: y = a << b[2:0];
      6: y = a >> b[2:0];
      default: y = {7'b0, a < b};
    endcase
  end
  assign z = (y == 0);
  assign n = y[7];
endmodule""")

vprob("v007", 4, "優先權編碼器",
      "8 位元請求向量 `req`。`valid` 表示至少有一個 1；`idx` 是**最高位**為 1 的位元索引（沒有請求時 `idx=0`）。\n\n"
      "練習：`casez` 或 `for` 迴圈；注意避免產生閂鎖。",
      [("req", 8)], [("idx", 3), ("valid", 1)],
      """module top_module(input [7:0] req, output reg [2:0] idx, output valid);
  integer i;
  always @* begin
    idx = 0;
    for (i = 0; i < 8; i = i + 1) if (req[i]) idx = i[2:0];
  end
  assign valid = |req;
endmodule""",
      """module top_module(input [7:0] req, output reg [2:0] idx, output valid);
  integer i;
  always @* begin
    idx = 0;
    for (i = 7; i >= 0; i = i - 1) if (req[i]) idx = i[2:0];
  end
  assign valid = |req;
endmodule""")

vprob("v010", 5, "上下數計數器（模 10）",
      "同步重置 `rst`（高電位有效，重置為 0）。每個時脈正緣：`load=1` 時載入 `d`（只取 0–9，輸入保證 `d<=9`）；否則 `en=1` 時依 `up` 上數（9 之後回 0）或下數（0 之後回 9）；`en=0` 保持。\n\n"
      "輸出 `count`（4 位元）與組合輸出 `carry`：`en=1`、`load=0` 且計數值正要從 9（上數）或 0（下數）環繞時為 1。\n\n注意：`rst` 在題目模板中已經宣告。",
      [("load", 1), ("en", 1), ("up", 1), ("d", 4)], [("count", 4), ("carry", 1)],
      """module top_module(input clk, input rst, input load, input en, input up, input [3:0] d, output reg [3:0] count, output carry);
  assign carry = en & ~load & (up ? count == 9 : count == 0);
  always @(posedge clk) begin
    if (rst) count <= 0;
    else if (load) count <= d;
    else if (en) begin
      if (up) count <= (count == 9) ? 4'd0 : count + 1;
      else count <= (count == 0) ? 4'd9 : count - 1;
    end
  end
endmodule""",
      """module top_module(input clk, input rst, input load, input en, input up, input [3:0] d, output reg [3:0] count, output carry);
  assign carry = en & (up ? count == 9 : count == 0);
  always @(posedge clk) begin
    if (rst) count <= 0;
    else if (load) count <= d;
    else if (en) begin
      if (up) count <= (count == 9) ? 4'd0 : count + 1;
      else count <= (count == 0) ? 4'd9 : count - 1;
    end
  end
endmodule""", seq=True, bias={"d": "$urandom % 10", "load": "($urandom % 6) == 0", "en": "($urandom % 4) != 0"})

vprob("v011", 5, "8 位元 LFSR",
      "多項式 x⁸ + x⁶ + x⁵ + x⁴ + 1 的 Fibonacci LFSR：同步重置 `rst` 時 `q = 8'h01`；`en=1` 的正緣更新 `q <= {q[6:0], q[7]^q[5]^q[4]^q[3]}`，`en=0` 保持。輸出 `q`。",
      [("en", 1)], [("q", 8)],
      """module top_module(input clk, input rst, input en, output reg [7:0] q);
  always @(posedge clk) begin
    if (rst) q <= 8'h01;
    else if (en) q <= {q[6:0], q[7] ^ q[5] ^ q[4] ^ q[3]};
  end
endmodule""",
      """module top_module(input clk, input rst, input en, output reg [7:0] q);
  always @(posedge clk) begin
    if (rst) q <= 8'h01;
    else if (en) q <= {q[6:0], q[7] ^ q[5] ^ q[4] ^ q[2]};
  end
endmodule""", seq=True)

vprob("v012", 6, "序列偵測器 1101（Mealy、可重疊）",
      "每個時脈取樣串列輸入 `x`。偵測到 `1101`（可重疊，例如 `1101101` 會偵測兩次）時，**在最後一個 1 輸入的那個週期**讓 `z=1`（Mealy：輸出同時取決於目前狀態與輸入）。同步重置 `rst` 回到初始狀態。",
      [("x", 1)], [("z", 1)],
      """module top_module(input clk, input rst, input x, output z);
  localparam S0 = 0, S1 = 1, S11 = 2, S110 = 3;
  reg [1:0] s, ns;
  always @* case (s)
    S0:   ns = x ? S1 : S0;
    S1:   ns = x ? S11 : S0;
    S11:  ns = x ? S11 : S110;
    default: ns = x ? S1 : S0;
  endcase
  assign z = (s == S110) & x;
  always @(posedge clk) s <= rst ? S0 : ns;
endmodule""",
      """module top_module(input clk, input rst, input x, output z);
  localparam S0 = 0, S1 = 1, S11 = 2, S110 = 3;
  reg [1:0] s, ns;
  always @* case (s)
    S0:   ns = x ? S1 : S0;
    S1:   ns = x ? S11 : S0;
    S11:  ns = x ? S11 : S110;
    default: ns = x ? S1 : S0;
  endcase
  assign z = (s == S110) & x;
  always @(posedge clk) s <= rst ? S0 : (z ? S0 : ns);
endmodule""", seq=True)

vprob("v023", 11, "同步 FIFO（深度 8）",
      "8 位元資料、深度 8 的同步 FIFO。同步重置 `rst`。`wr_en` 且未滿時寫入 `din`；`rd_en` 且非空時讀出；同一週期可同時讀寫。**滿時的寫入、空時的讀取一律忽略。**\n\n"
      "輸出：`full`、`empty`（皆為目前狀態，組合輸出）、`dout`＝目前最舊的資料（first-word-fall-through，組合輸出）；空的時候 `dout` 必須是 0。\n\n提示：指針多留 1 位元來分辨空與滿。",
      [("wr_en", 1), ("rd_en", 1), ("din", 8)], [("dout", 8), ("full", 1), ("empty", 1)],
      """module top_module(input clk, input rst, input wr_en, input rd_en, input [7:0] din, output [7:0] dout, output full, output empty);
  reg [7:0] mem [0:7];
  reg [3:0] wp, rp;
  assign empty = (wp == rp);
  assign full = (wp[2:0] == rp[2:0]) && (wp[3] != rp[3]);
  assign dout = empty ? 8'd0 : mem[rp[2:0]];
  always @(posedge clk) begin
    if (rst) begin wp <= 0; rp <= 0; end
    else begin
      if (wr_en && !full) begin mem[wp[2:0]] <= din; wp <= wp + 1; end
      if (rd_en && !empty) rp <= rp + 1;
    end
  end
endmodule""",
      """module top_module(input clk, input rst, input wr_en, input rd_en, input [7:0] din, output [7:0] dout, output full, output empty);
  reg [7:0] mem [0:7];
  reg [3:0] wp, rp;
  assign empty = (wp == rp);
  assign full = (wp[2:0] == rp[2:0]) && (wp[3] != rp[3]);
  assign dout = empty ? 8'd0 : mem[rp[2:0]];
  always @(posedge clk) begin
    if (rst) begin wp <= 0; rp <= 0; end
    else begin
      if (wr_en) begin mem[wp[2:0]] <= din; wp <= wp + 1; end
      if (rd_en && !empty) rp <= rp + 1;
    end
  end
endmodule""", seq=True, bias={"wr_en": "($urandom % 3) != 0", "rd_en": "($urandom % 3) == 0"})

vprob("v024", 11, "暫存器堆（2 讀 1 寫）",
      "RISC-V 風格：32 個 32 位元暫存器。兩個**組合**讀埠 `ra1`、`ra2` 輸出 `rd1`、`rd2`；一個**同步**寫埠：`we=1` 時在時脈正緣把 `wd` 寫入 `wa`。**x0 永遠讀到 0，寫入 x0 無效。** 不需要繞道（同週期讀到的是舊值）。`rst` 不需處理（模板中保留此腳位，可忽略）；為了讓判題一致，請不要依賴未初始化的暫存器——判題只會讀取已被寫入過的暫存器或 x0。",
      [("ra1", 5), ("ra2", 5), ("wa", 5), ("wd", 32), ("we", 1)], [("rd1", 32), ("rd2", 32)],
      """module top_module(input clk, input rst, input [4:0] ra1, input [4:0] ra2, input [4:0] wa, input [31:0] wd, input we, output [31:0] rd1, output [31:0] rd2);
  reg [31:0] r [0:31];
  integer i;
  initial for (i = 0; i < 32; i = i + 1) r[i] = 0;
  assign rd1 = (ra1 == 0) ? 32'd0 : r[ra1];
  assign rd2 = (ra2 == 0) ? 32'd0 : r[ra2];
  always @(posedge clk) if (we && wa != 0) r[wa] <= wd;
endmodule""",
      """module top_module(input clk, input rst, input [4:0] ra1, input [4:0] ra2, input [4:0] wa, input [31:0] wd, input we, output [31:0] rd1, output [31:0] rd2);
  reg [31:0] r [0:31];
  integer i;
  initial for (i = 0; i < 32; i = i + 1) r[i] = 0;
  assign rd1 = r[ra1];
  assign rd2 = r[ra2];
  always @(posedge clk) if (we) r[wa] <= wd;
endmodule""", seq=True, bias={"we": "($urandom % 2)"})


# ---------------- Tcl ----------------
T: Dict[str, dict] = {}


def tprob(pid, unit, title, statement, ref, bad, sample, inputs, harness="", template="# 從標準輸入讀資料，用 puts 輸出\n"):
    """sample=(stdin, 手寫期望輸出)；inputs=其他測資的 stdin（期望輸出由參考解產生）。"""
    T[pid] = dict(track="tcl", unit=unit, title=title, statement=statement, template=template, ref=ref, bad=bad, sample=sample, inputs=list(inputs), harness=harness)


tprob("t001", 1, "Hello 與字串長度",
      "讀一行姓名 `name`，輸出兩行：`Hello, <name>!` 與 `length: <字元數>`。",
      """gets stdin name
puts "Hello, $name!"
puts "length: [string length $name]"
""",
      """gets stdin name
puts "Hello, $name!"
puts "length: [llength $name]"
""",
      ("Ada\n", "Hello, Ada!\nlength: 3"),
      ["Grace Hopper\n", "林\n", "a b  c\n"])

tprob("t005", 3, "費氏數與質數判斷（proc）",
      "輸入一行 `n m`。定義 `proc fib {n}`（`fib 0 = 0`、`fib 1 = 1`）與 `proc isprime {m}`（回傳 1 或 0；`m<2` 不是質數），輸出 `fib n` 與 `isprime m` 各一行。",
      """proc fib {n} {
    set a 0; set b 1
    for {set i 0} {$i < $n} {incr i} { lassign [list $b [expr {$a + $b}]] a b }
    return $a
}
proc isprime {m} {
    if {$m < 2} { return 0 }
    for {set i 2} {$i * $i <= $m} {incr i} { if {$m % $i == 0} { return 0 } }
    return 1
}
lassign [gets stdin] n m
puts [fib $n]
puts [isprime $m]
""",
      """proc fib {n} {
    if {$n < 2} { return $n }
    return [expr {[fib [expr {$n-1}]] + [fib [expr {$n-2}]]}]
}
proc isprime {m} {
    for {set i 2} {$i < $m} {incr i} { if {$m % $i == 0} { return 0 } }
    return 1
}
lassign [gets stdin] n m
puts [fib $n]
puts [isprime $m]
""",
      ("10 7\n", "55\n1"), ["0 1\n", "1 91\n", "30 97\n", "20 2\n", "25 0\n"])

tprob("t006", 3, "swap：用 upvar 交換呼叫端變數",
      "寫 `proc swap {x y}`，交換**呼叫端**兩個變數的值。判題會用不同變數名稱呼叫（包含 `swap b a`），所以不能假設變數名字。",
      """proc swap {x y} {
    upvar 1 $x lx $y ly
    set t $lx; set lx $ly; set ly $t
}
""",
      """proc swap {x y} {
    set t $x; set x $y; set y $t
}
""",
      ("1\n2\n", "2 1\n6 5\n1 2"),
      ["hello\nworld\n", "7\n7\n", "x y\nz w\n"],
      harness="""
gets stdin a; gets stdin b
swap a b
puts "$a $b"
set p 5; set q 6
swap p q
puts "$p $q"
swap b a
puts "$a $b"
""", template="# 只需定義 swap；判題會自己呼叫\n")

tprob("t007", 3, "自訂控制結構 repeat",
      "寫 `proc repeat {n body}`：把 `body` 在**呼叫端的層級**執行 `n` 次（要能存取呼叫端的區域變數，所以要用 `uplevel`）。`n=0` 不執行。",
      """proc repeat {n body} {
    for {set i 0} {$i < $n} {incr i} { uplevel 1 $body }
}
""",
      """proc repeat {n body} {
    for {set i 0} {$i < $n} {incr i} { eval $body }
}
""",
      ("3\n", "6\n444\n4"),
      ["0\n", "5\n", "1\n"],
      harness="""
gets stdin n
set c 0
repeat $n {incr c 2}
puts $c
set s ""
repeat 3 {append s [expr {$n + 1}]}
puts $s
proc t {} { set k 0; repeat 4 {incr k}; return $k }
puts [t]
""", template="# 只需定義 repeat；判題會自己呼叫\n")

tprob("t008", 4, "詞頻統計",
      "讀入全部文字（標準輸入到結尾）。把字母轉小寫，單字由英文字母與撇號 `'` 組成，其餘字元都是分隔。輸出每個單字與次數 `word count`，依次數遞減、同次數依字典序遞增。",
      """set text [read stdin]
foreach w [regexp -all -inline {[a-z']+} [string tolower $text]] { dict incr cnt $w }
set rows {}
if {[info exists cnt]} { dict for {w c} $cnt { lappend rows [list $w $c] } }
foreach r [lsort -integer -decreasing -index 1 [lsort -index 0 $rows]] { puts "[lindex $r 0] [lindex $r 1]" }
""",
      """set text [read stdin]
foreach w [regexp -all -inline {[A-Za-z']+} $text] { dict incr cnt $w }
set rows {}
dict for {w c} $cnt { lappend rows [list $w $c] }
foreach r [lsort -integer -decreasing -index 1 [lsort -index 0 $rows]] { puts "[lindex $r 0] [lindex $r 1]" }
""",
      ("the cat the dog\nThe end\n", "the 3\ncat 1\ndog 1\nend 1"),
      ["It's a test. It's only a test!\n", "b a b a c\n", "Hello, hello; HELLO... world\n"])

tprob("t009", 4, "矩陣乘法與轉置",
      "第一行 `n`，接著 n 行矩陣 A（每行 n 個整數）、n 行矩陣 B。先輸出 `A×B` 的 n 行（數字以空格分隔），再輸出一行 `--`，再輸出 A 的轉置的 n 行。",
      """set n [gets stdin]
for {set i 0} {$i < $n} {incr i} { lappend A [gets stdin] }
for {set i 0} {$i < $n} {incr i} { lappend B [gets stdin] }
for {set i 0} {$i < $n} {incr i} {
    set row {}
    for {set j 0} {$j < $n} {incr j} {
        set s 0
        for {set k 0} {$k < $n} {incr k} { incr s [expr {[lindex $A $i $k] * [lindex $B $k $j]}] }
        lappend row $s
    }
    puts $row
}
puts "--"
for {set j 0} {$j < $n} {incr j} {
    set row {}
    for {set i 0} {$i < $n} {incr i} { lappend row [lindex $A $i $j] }
    puts $row
}
""",
      """set n [gets stdin]
for {set i 0} {$i < $n} {incr i} { lappend A [gets stdin] }
for {set i 0} {$i < $n} {incr i} { lappend B [gets stdin] }
for {set i 0} {$i < $n} {incr i} {
    set row {}
    for {set j 0} {$j < $n} {incr j} {
        set s 0
        for {set k 0} {$k < $n} {incr k} { incr s [expr {[lindex $A $i $k] * [lindex $B $k $j]}] }
        lappend row $s
    }
    puts $row
}
puts "--"
for {set i 0} {$i < $n} {incr i} { puts [lindex $A $i] }
""",
      ("2\n1 2\n3 4\n5 6\n7 8\n", "19 22\n43 50\n--\n1 3\n2 4"),
      ["1\n7\n-3\n", "3\n1 0 0\n0 1 0\n0 0 1\n1 2 3\n4 5 6\n7 8 9\n", "3\n1 2 3\n4 5 6\n7 8 9\n-1 0 1\n2 -2 0\n3 3 3\n"])

tprob("t012", 5, "日誌解析",
      "每行格式 `YYYY-MM-DD HH:MM:SS [LEVEL] 訊息`。格式不符的行略過。輸出每個等級的行數 `LEVEL count`（等級依字母序），最後一行 `first_error: <第一個 ERROR 的日期 時間>`，沒有 ERROR 就印 `first_error: none`。",
      """while {[gets stdin line] >= 0} {
    if {[regexp {^(\\S+ \\S+) \\[(\\w+)\\] (.*)$} $line -> ts lv msg]} {
        dict incr cnt $lv
        if {$lv eq "ERROR" && ![info exists first]} { set first $ts }
    }
}
if {[info exists cnt]} { foreach lv [lsort [dict keys $cnt]] { puts "$lv [dict get $cnt $lv]" } }
puts "first_error: [expr {[info exists first] ? $first : {none}}]"
""",
      """while {[gets stdin line] >= 0} {
    if {[regexp {^(\\S+ \\S+) \\[(\\w+)\\] (.*)$} $line -> ts lv msg]} {
        dict incr cnt $lv
        if {$lv eq "ERROR"} { set first $ts }
    }
}
if {[info exists cnt]} { foreach lv [lsort [dict keys $cnt]] { puts "$lv [dict get $cnt $lv]" } }
puts "first_error: [expr {[info exists first] ? $first : {none}}]"
""",
      ("2024-01-02 10:00:01 [INFO] start\n2024-01-02 10:00:05 [ERROR] boom\n2024-01-02 10:00:09 [ERROR] again\n", "ERROR 2\nINFO 1\nfirst_error: 2024-01-02 10:00:05"),
      ["2024-01-02 10:00:01 [INFO] a\ngarbage line\n2024-01-02 10:00:02 [WARN] b\n", "", "x\n2024-05-05 00:00:00 [DEBUG] z [ERROR] inner\n"])

tprob("t014", 5, "格式化報表",
      "每行 `name value`（value 為小數）。每行輸出 `format \"%-10s %8.2f\"`；最後再輸出一行同格式的總和，名稱為 `total`。",
      """set sum 0.0
while {[gets stdin line] >= 0} {
    lassign $line name v
    puts [format "%-10s %8.2f" $name $v]
    set sum [expr {$sum + $v}]
}
puts [format "%-10s %8.2f" total $sum]
""",
      """set sum 0
while {[gets stdin line] >= 0} {
    lassign $line name v
    puts [format "%-10s %8.1f" $name $v]
    set sum [expr {$sum + $v}]
}
puts [format "%-10s %8.1f" total $sum]
""",
      ("apple 1.5\npear 22.257\n", "apple          1.50\npear          22.26\ntotal         23.76".replace("pear          22.26", "pear          22.26")),
      ["x 0\n", "a 100.005\nb 0.004\nc 12345.678\n", "long_name_ 1\n"])

tprob("t021", 9, "stack ensemble",
      "用 `namespace ensemble` 做出 `stack` 指令，子指令：`push v`（無回傳）、`pop`、`peek`、`size`。空堆疊 `pop`／`peek` 要丟出錯誤（判題會把錯誤印成 `error`）。判題會逐行讀入指令並執行 `stack {*}$line`。",
      """namespace eval stack {
    variable items {}
    proc push {v} { variable items; lappend items $v; return }
    proc pop {} { variable items; if {![llength $items]} { error "empty" }; set v [lindex $items end]; set items [lrange $items 0 end-1]; return $v }
    proc peek {} { variable items; if {![llength $items]} { error "empty" }; return [lindex $items end] }
    proc size {} { variable items; return [llength $items] }
    namespace export push pop peek size
    namespace ensemble create
}
""",
      """namespace eval stack {
    variable items {}
    proc push {v} { variable items; lappend items $v; return }
    proc pop {} { variable items; set v [lindex $items end]; set items [lrange $items 0 end-1]; return $v }
    proc peek {} { variable items; return [lindex $items end] }
    proc size {} { variable items; return [llength $items] }
    namespace export push pop peek size
    namespace ensemble create
}
""",
      ("push 1\npush 2\npeek\nsize\npop\npop\npop\nsize\n", "\n\n2\n2\n2\n1\nerror\n0"),
      ["size\npop\npeek\n", "push a\npush b c\nsize\nbogus\npop\n"],
      harness="""
while {[gets stdin line] >= 0} { if {[catch {stack {*}$line} r]} { puts "error" } else { puts $r } }
""", template="# 只需定義 stack ensemble；判題會自己呼叫\n")

tprob("t023", 10, "樣板展開",
      "第一行是 dict（Tcl 清單，如 `name World n 3`）。其餘每行是樣板：把 `${key}` 換成 dict 中的值；沒有該 key 就換成 `<?key?>`。其餘字元原樣輸出（包含單獨的 `$`、方括號與反斜線，**不可以讓它們被當成 Tcl 指令執行**）。",
      """set d [gets stdin]
while {[gets stdin line] >= 0} {
    set out ""
    while {[regexp -indices {\\$\\{(\\w+)\\}} $line m k]} {
        lassign $m ms me; lassign $k ks ke
        set key [string range $line $ks $ke]
        append out [string range $line 0 [expr {$ms - 1}]]
        if {[dict exists $d $key]} { append out [dict get $d $key] } else { append out "<?$key?>" }
        set line [string range $line [expr {$me + 1}] end]
    }
    puts $out$line
}
""",
      """set d [gets stdin]
dict for {k v} $d { set $k $v }
while {[gets stdin line] >= 0} {
    puts [subst -nocommands -nobackslashes [string map {\\$\\{ \\$\\{} $line]]
}
""",
      ("name World n 3\nHi ${name}, ${n} times\nmissing ${zzz}!\n", "Hi World, 3 times\nmissing <?zzz?>!"),
      ["a 1\ncost $5 [ls] ${a}${a}\n", "x y\n${x} ${x}\\n done\n"])

tprob("t026", 12, "時序報告解析",
      "輸入是簡化的時序報告：以 `Startpoint:`／`Endpoint:` 開頭的行略過；每個路徑級是一行 `pin incr arrival`（後兩欄為數字，可為負）；最後一行 `slack MET|VIOLATED value`。輸出四行：`stages: N`（路徑級數）、`arrival: X`（最後一級的 arrival，原樣輸出）、`slack: V`、`status: S`。",
      """set n 0; set arr 0; set sl ""; set st ""
while {[gets stdin line] >= 0} {
    if {[regexp {^\\S+ -?[0-9.]+ (-?[0-9.]+)$} $line -> a]} { incr n; set arr $a } \\
    elseif {[regexp {^slack (MET|VIOLATED) (-?[0-9.]+)$} $line -> st sl]} {}
}
puts "stages: $n"
puts "arrival: $arr"
puts "slack: $sl"
puts "status: $st"
""",
      """set n 0; set arr 0; set sl ""; set st ""
while {[gets stdin line] >= 0} {
    if {[regexp {^\\S+ ([0-9.]+) ([0-9.]+)$} $line -> i a]} { incr n; set arr $a } \\
    elseif {[regexp {^slack (MET|VIOLATED) (-?[0-9.]+)$} $line -> st sl]} {}
}
puts "stages: $n"
puts "arrival: $arr"
puts "slack: $sl"
puts "status: $st"
""",
      ("Startpoint: a_reg\nEndpoint: b_reg\nu1/Z 0.12 0.12\nu2/Z 0.30 0.42\nb_reg/D 0.05 0.47\nslack MET 0.53\n", "stages: 3\narrival: 0.47\nslack: 0.53\nstatus: MET"),
      ["Startpoint: x\nEndpoint: y\nu1/Z -0.10 1.00\nu2/Z 1.20 2.20\nslack VIOLATED -0.35\n", "Startpoint: q\nslack MET 9.99\n"])

tprob("t028", 12, "CSV 讀取",
      "讀入 CSV（每行一筆記錄）：欄位以逗號分隔；欄位可用雙引號包住，引號內可含逗號，且 `\"\"` 代表一個雙引號字元。每筆輸出各欄位以 `|` 連接。（不需處理跨行欄位。）",
      """proc parse_line {line} {
    set fields {}; set cur ""; set inq 0; set n [string length $line]
    for {set i 0} {$i < $n} {incr i} {
        set ch [string index $line $i]
        if {$inq} {
            if {$ch eq "\\""} {
                if {[string index $line [expr {$i + 1}]] eq "\\""} { append cur "\\""; incr i } else { set inq 0 }
            } else { append cur $ch }
        } else {
            if {$ch eq "\\""} { set inq 1 } elseif {$ch eq ","} { lappend fields $cur; set cur "" } else { append cur $ch }
        }
    }
    lappend fields $cur
    return $fields
}
while {[gets stdin line] >= 0} { puts [join [parse_line $line] "|"] }
""",
      """while {[gets stdin line] >= 0} { puts [join [split $line ","] "|"] }
""",
      ("a,b,c\n1,\"x,y\",3\n", "a|b|c\n1|x,y|3"),
      ["\"he said \"\"hi\"\"\",2\n", ",,\n", "plain\n\"q\",\"\",z\n"])
