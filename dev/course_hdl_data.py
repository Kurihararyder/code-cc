"""Verilog 與 Tcl 軌道共用的資料建構工具與教材清單。"""

RES = {
    "hdlbits": ("HDLBits（線上 Verilog 練習與判題，免費）", "https://hdlbits.01xz.net/wiki/Problem_sets"),
    "harris": ("Digital Design and Computer Architecture, RISC-V Edition（Harris & Harris）", "https://shop.elsevier.com/books/digital-design-and-computer-architecture-risc-v-edition/harris/978-0-12-820064-3"),
    "iverilog": ("Icarus Verilog（開源模擬器）", "https://steveicarus.github.io/iverilog/"),
    "verilator": ("Verilator 使用指南", "https://verilator.org/guide/latest/"),
    "yosys": ("Yosys 文件（開源合成）", "https://yosyshq.readthedocs.io/projects/yosys/en/latest/"),
    "sby": ("SymbiYosys 文件（形式驗證）", "https://yosyshq.readthedocs.io/projects/sby/en/latest/"),
    "cocotb": ("cocotb 文件（用 Python 驗證硬體）", "https://docs.cocotb.org/en/stable/"),
    "gtkwave": ("GTKWave（波形檢視）", "https://gtkwave.sourceforge.net/"),
    "opensta": ("OpenSTA（開源靜態時序分析）", "https://github.com/The-OpenROAD-Project/OpenSTA"),
    "openroad": ("OpenROAD 文件", "https://openroad.readthedocs.io/en/latest/"),
    "openlane": ("OpenLane 2 文件", "https://openlane2.readthedocs.io/"),
    "sky130": ("SkyWater SKY130 PDK 文件", "https://skywater-pdk.readthedocs.io/"),
    "nextpnr": ("nextpnr（開源 FPGA 擺置繞線）", "https://github.com/YosysHQ/nextpnr"),
    "tinytapeout": ("Tiny Tapeout（小型晶片共乘下線）", "https://tinytapeout.com/"),
    "riscv_spec": ("RISC-V 規格文件", "https://riscv.org/specifications/"),
    "riscv_gnu": ("RISC-V GNU 工具鏈", "https://github.com/riscv-collab/riscv-gnu-toolchain"),
    "amba": ("Arm AMBA 規格（AXI、APB）", "https://developer.arm.com/architectures/system-architectures/amba/specifications"),
    "wishbone": ("Wishbone 匯流排規格（OpenCores）", "https://opencores.org/howto/wishbone"),
    "sunburst": ("Sunburst Design：Clifford Cummings 的論文", "https://www.sunburst-design.com/papers/"),
    "bergeron": ("Writing Testbenches: Functional Verification of HDL Models（Bergeron）", ""),
    "spear": ("SystemVerilog for Verification（Spear & Tumbush）", ""),
    "bening": ("Principles of Verifiable RTL Design（Bening & Foster）", ""),
    "weste": ("CMOS VLSI Design: A Circuits and Systems Perspective（Weste & Harris）", ""),
    "patterson": ("Computer Organization and Design, RISC-V Edition（Patterson & Hennessy）", ""),
    "sta_book": ("Static Timing Analysis for Nanometer Designs（Bhasker & Chadha）", ""),
    "bushnell": ("Essentials of Electronic Testing（Bushnell & Agrawal）", ""),
    "hennessy": ("Computer Architecture: A Quantitative Approach（Hennessy & Patterson）", ""),
    "uvm_ug": ("UVM 1.2 User's Guide（Accellera）", "https://www.accellera.org/downloads/standards/uvm"),
    # ---- Tcl ----
    "tcltut": ("Tcl 官方教學（8.5 版，第 0–48 課）", "https://tcl-lang.org/man/tcl8.5/tutorial/tcltutorial.html"),
    "tclman": ("Tcl 8.6 指令手冊", "https://www.tcl-lang.org/man/tcl8.6/TclCmd/contents.htm"),
    "tclwiki": ("Tcler's Wiki", "https://wiki.tcl-lang.org/"),
    "welch": ("Practical Programming in Tcl and Tk（Welch、Jones、Hobbs）", "https://www.beedub.com/book/"),
    "ousterhout": ("Tcl and the Tk Toolkit（Ousterhout & Jones）", ""),
    "nagelfar": ("Nagelfar（Tcl 的靜態語法檢查器）", "https://nagelfar.sourceforge.net/"),
    "tcllib": ("Tcllib（Tcl 標準模組庫）", "https://core.tcl-lang.org/tcllib/doc/trunk/embedded/index.md"),
    "vivado_tcl": ("Vivado Design Suite Tcl 指令參考（AMD／Xilinx；需註冊）", ""),
}


class _R:
    """閱讀項目建構器：回傳 (來源, 範圍, 重點, 頁碼=None)。"""

    @staticmethod
    def hdlbits(section, names, focus):
        return ("hdlbits", f"{section}｜{names}", focus, None)

    @staticmethod
    def harris(ch, focus):
        return ("harris", f"第 {ch} 章", focus, ch)

    @staticmethod
    def doc(key, where, focus):
        return (key, where, focus, None)

    book = doc
    paper = doc

    @staticmethod
    def tcltut(lessons, focus):
        return ("tcltut", lessons, focus, None)

    @staticmethod
    def tclman(cmds, focus):
        return ("tclman", cmds, focus, None)


R = _R()


def PL(id_, title, topic):
    return dict(id=id_, title=title, topic=topic)


def H(problems, need):
    return {"type": "hdlbits", "problems": list(problems), "need": need}


def PRJ(criteria, days=7):
    return {"type": "project", "criteria": list(criteria), "days": days}


def PLG(problems, minutes, need):
    """新增題目的限時檢核（題目還沒有）。"""
    return {"type": "planned", "problems": list(problems), "minutes": minutes, "need": need}


def U_(stage, weeks, title, goal, learn, planned=(), build=(), readings=(), pitfalls=(), check=(), gate=None):
    return dict(stage=stage, weeks=weeks, title=title, goal=goal, learn=list(learn), planned=list(planned), build=list(build),
                readings=list(readings), pitfalls=list(pitfalls), check=list(check), gate=gate)
