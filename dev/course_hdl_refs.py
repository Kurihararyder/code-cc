"""Verilog 與 Tcl 軌道的教材指向驗證表（都是實際查過的目錄；產生器會逐項檢查）。

- HDLBits（hdlbits.01xz.net/wiki/Problem_sets）：章節與題目名稱，查自該頁。
- Tcl 官方教學（tcl-lang.org/man/tcl8.5/tutorial/tcltutorial.html）：第 0–48 課，查自該頁（不同版本的課號略有不同，本課綱以 8.5 版為準）。
- Tcl 8.6 內建指令清單（tcl-lang.org/man/tcl8.6/TclCmd/contents.htm）。
- Harris & Harris《Digital Design and Computer Architecture, RISC-V Edition》：9 章的章名，查自出版社目錄。
其他書籍與文件只寫名稱，不寫頁碼或章號（版本不同章號會不同）。
"""

HDLBITS = {
    "Getting Started": ["Getting Started", "Output Zero"],
    "Verilog Language／Basics": ["Simple wire", "Four wires", "Inverter", "AND gate", "NOR gate", "XNOR gate", "Declaring wires", "7458 chip"],
    "Verilog Language／Vectors": ["Vectors", "Vectors in more detail", "Vector part select", "Bitwise operators", "Four-input gates", "Vector concatenation operator",
                                  "Vector reversal 1", "Replication operator", "More replication"],
    "Verilog Language／Modules: Hierarchy": ["Modules", "Connecting ports by position", "Connecting ports by name", "Three modules", "Modules and vectors", "Adder 1",
                                             "Adder 2", "Carry-select adder", "Adder-subtractor"],
    "Verilog Language／Procedures": ["Always blocks (combinational)", "Always blocks (clocked)", "If statement", "If statement latches", "Case statement",
                                     "Priority encoder", "Priority encoder with casez", "Avoiding latches"],
    "Verilog Language／More Verilog Features": ["Conditional ternary operator", "Reduction operators", "Reduction: Even wider gates", "Combinational for-loop: Vector reversal 2",
                                                "Combinational for-loop: 255-bit population count", "Generate for-loop: 100-bit binary adder 2", "Generate for-loop: 100-digit BCD adder"],
    "Circuits／Combinational Logic／Basic Gates": ["Wire", "GND", "NOR", "Another gate", "Two gates", "More logic gates", "7420 chip", "Truth tables", "Two-bit equality",
                                                   "Simple circuit A", "Simple circuit B", "Combine circuits A and B", "Ring or vibrate?", "Thermostat", "3-bit population count",
                                                   "Gates and vectors", "Even longer vectors"],
    "Circuits／Combinational Logic／Multiplexers": ["2-to-1 multiplexer", "2-to-1 bus multiplexer", "9-to-1 multiplexer", "256-to-1 multiplexer", "256-to-1 4-bit multiplexer"],
    "Circuits／Combinational Logic／Arithmetic Circuits": ["Half adder", "Full adder", "3-bit binary adder", "Adder", "Signed addition overflow", "100-bit binary adder", "4-digit BCD adder"],
    "Circuits／Combinational Logic／Karnaugh Map to Circuit": ["3-variable", "4-variable", "Minimum SOP and POS", "Karnaugh map", "K-map implemented with a multiplexer"],
    "Circuits／Sequential Logic／Latches and Flip-Flops": ["D flip-flop", "D flip-flops", "DFF with reset", "DFF with reset value", "DFF with asynchronous reset", "DFF with byte enable", "D Latch",
                                                          "DFF", "DFF+gate", "Mux and DFF", "DFFs and gates", "Create circuit from truth table", "Detect an edge", "Detect both edges",
                                                          "Edge capture register", "Dual-edge triggered flip-flop"],
    "Circuits／Sequential Logic／Counters": ["Four-bit binary counter", "Decade counter", "Decade counter again", "Slow decade counter", "Counter 1-12", "Counter 1000",
                                             "4-digit decimal counter", "12-hour clock"],
    "Circuits／Sequential Logic／Shift Registers": ["4-bit shift register", "Left/right rotator", "Left/right arithmetic shift by 1 or 8", "5-bit LFSR", "3-bit LFSR", "32-bit LFSR",
                                                    "Shift register", "3-input LUT"],
    "Circuits／Sequential Logic／More Circuits": ["Rule 90", "Rule 110", "Conway's Game of Life 16x16"],
    "Circuits／Sequential Logic／Finite State Machines": ["Simple FSM 1 (asynchronous reset)", "Simple FSM 1 (synchronous reset)", "Simple FSM 2 (asynchronous reset)",
                                                         "Simple FSM 2 (synchronous reset)", "Simple state transitions 3", "Simple one-hot state transitions 3",
                                                         "Simple FSM 3 (asynchronous reset)", "Simple FSM 3 (synchronous reset)", "Design a Moore FSM", "Lemmings 1", "Lemmings 2",
                                                         "Lemmings 3", "Lemmings 4", "One-hot FSM", "PS/2 packet parser", "PS/2 packet parser and datapath", "Serial receiver",
                                                         "Serial receiver and datapath", "Serial receiver with parity checking", "Sequence recognition", "Q8: Design a Mealy FSM",
                                                         "Q5a: Serial two's complementer (Moore FSM)", "Q5b: Serial two's complementer (Mealy FSM)"],
    "Circuits／Building Larger Circuits": ["Counter with period 1000", "4-bit shift register and down counter", "FSM: Sequence 1101 recognizer", "FSM: Enable shift register",
                                           "FSM: The complete FSM", "The complete timer", "FSM: One-hot logic equations"],
    "Verification: Reading Simulations": ["Mux", "NAND", "Add/sub", "Case statement", "Combinational circuit 1", "Combinational circuit 2", "Combinational circuit 3",
                                          "Combinational circuit 4", "Combinational circuit 5", "Combinational circuit 6", "Sequential circuit 7", "Sequential circuit 8",
                                          "Sequential circuit 9", "Sequential circuit 10"],
    "Verification: Writing Testbenches": ["Clock", "Testbench1", "AND gate", "Testbench2", "T flip-flop"],
}

TCL_LESSONS = 48          # 第 0–48 課（8.5 版教學）

TCL_CMDS = set("""after append apply array binary break catch cd chan clock close concat continue coroutine dict encoding eof error eval exec exit expr fblocked
fconfigure fcopy file fileevent flush for foreach format gets glob global history http if incr info interp join lappend lassign lindex linsert list llength lmap load
lrange lrepeat lreplace lreverse lsearch lset lsort mathop memory msgcat namespace open package pid platform proc puts pwd read regexp regsub rename return safe scan
seek set socket source split string subst switch tailcall tcltest tell throw time timerate trace try unknown unload unset update uplevel upvar variable vwait while yield
yieldto zlib oo::class oo::define oo::object oo::objdefine oo::copy my self next nextto""".split())

HARRIS = {1: "From Zero to One", 2: "Combinational Logic Design", 3: "Sequential Logic Design", 4: "Hardware Description Languages", 5: "Digital Building Blocks",
          6: "Architecture", 7: "Microarchitecture", 8: "Memory Systems", 9: "I/O Systems"}
