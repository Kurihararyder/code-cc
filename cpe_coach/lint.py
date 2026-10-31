"""靜態分析（只看程式碼，不執行）：找常見的慢寫法與新手錯誤。Python 用 ast；C++ 只做少數文字規則。

每一條都是「提示」不是判決：可能誤報，也不保證找得出所有問題。
"""
from __future__ import annotations

import ast
import re
from typing import Any, Dict, List

BUILTINS_SHADOW = {"list", "dict", "set", "sum", "max", "min", "len", "input", "str", "int", "map", "sorted", "range", "id", "all", "any", "abs", "round", "print", "type", "next", "iter"}


def _f(line: int, code: str, msg: str, level: str = "hint") -> Dict[str, Any]:
    return {"line": line, "code": code, "msg": msg, "level": level}


class _V(ast.NodeVisitor):
    def __init__(self) -> None:
        self.out: List[Dict[str, Any]] = []
        self.loop_depth = 0
        self.max_depth = 0
        self.func_stack: List[str] = []
        self.calls_self = False
        self.has_setrec = False
        self.list_names: set = set()
        self.print_in_loop = False

    def visit_FunctionDef(self, n: ast.FunctionDef) -> None:
        for d in n.args.defaults + [x for x in n.args.kw_defaults if x]:
            if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                self.out.append(_f(n.lineno, "mutable-default", f"函式 {n.name} 的預設參數是可變物件（list／dict／set）：它會在多次呼叫之間共用，幾乎一定是 bug；改用 None 再在函式內建立。", "warn"))
        self.func_stack.append(n.name)
        used = {x.id for x in ast.walk(n) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)}
        assigned: Dict[str, int] = {}
        for x in ast.walk(n):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store):
                assigned.setdefault(x.id, x.lineno)
        for name, ln in assigned.items():
            if name not in used and not name.startswith("_"):
                self.out.append(_f(ln, "unused-var", f"變數 {name} 被指定了但從沒用到：是不是打錯名稱、或忘了用它？"))
        self.generic_visit(n)
        self.func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def _loop(self, n: ast.AST) -> None:
        self.loop_depth += 1
        self.max_depth = max(self.max_depth, self.loop_depth)
        if self.loop_depth == 3:
            self.out.append(_f(getattr(n, "lineno", 0), "deep-loop", "三層以上的巢狀迴圈：如果每層都跑到 n（n 很大），大約是 O(n³)；想想前綴和、排序加雙指標、雜湊能不能少一層。", "warn"))
        self.generic_visit(n)
        self.loop_depth -= 1

    visit_For = visit_While = _loop

    def visit_Call(self, n: ast.Call) -> None:
        f = n.func
        if isinstance(f, ast.Attribute) and self.loop_depth:
            if f.attr == "pop" and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == 0:
                self.out.append(_f(n.lineno, "pop0", "list.pop(0) 在迴圈裡是 O(n)：整個迴圈變成 O(n²)；改用 collections.deque.popleft()。", "warn"))
            if f.attr == "insert" and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == 0:
                self.out.append(_f(n.lineno, "insert0", "list.insert(0, x) 在迴圈裡是 O(n)；改用 deque.appendleft，或先 append 最後再反轉。", "warn"))
            if f.attr == "index":
                self.out.append(_f(n.lineno, "index-in-loop", "list.index() 每次都從頭找，在迴圈裡是 O(n)；可以先建一個 dict 記下每個值的位置。"))
        if isinstance(f, ast.Name):
            if f.id == "input" and self.loop_depth:
                self.out.append(_f(n.lineno, "input-loop", "大量輸入時 input() 很慢：改成 import sys 後用 sys.stdin.readline()，或一次 sys.stdin.read().split()。"))
            if f.id == "print" and self.loop_depth:
                self.print_in_loop = True
            if f.id == "setrecursionlimit":
                self.has_setrec = True
            if self.func_stack and f.id == self.func_stack[-1]:
                self.calls_self = True
        if isinstance(f, ast.Attribute) and f.attr == "setrecursionlimit":
            self.has_setrec = True
        self.generic_visit(n)

    def visit_AugAssign(self, n: ast.AugAssign) -> None:
        if self.loop_depth and isinstance(n.op, ast.Add) and isinstance(n.target, ast.Name) and isinstance(n.value, (ast.Constant, ast.JoinedStr)) and \
                (isinstance(n.value, ast.JoinedStr) or isinstance(n.value.value, str)):
            self.out.append(_f(n.lineno, "str-concat", f"在迴圈裡用 {n.target.id} += 字串 逐步組字串：字串很長時會變慢；改成 list.append 最後 ''.join。"))
        self.generic_visit(n)

    def visit_Assign(self, n: ast.Assign) -> None:
        for t in n.targets:
            if isinstance(t, ast.Name):
                if t.id in BUILTINS_SHADOW:
                    self.out.append(_f(n.lineno, "shadow-builtin", f"變數名稱 {t.id} 蓋掉了內建函式 {t.id}()：之後再呼叫它會出現 'not callable' 之類的錯；換個名字。", "warn"))
                if isinstance(n.value, (ast.List, ast.ListComp)) or (isinstance(n.value, ast.Call) and getattr(n.value.func, "id", "") == "list"):
                    self.list_names.add(t.id)
        self.generic_visit(n)

    def visit_Compare(self, n: ast.Compare) -> None:
        for op, cmp in zip(n.ops, n.comparators):
            if isinstance(op, (ast.In, ast.NotIn)) and self.loop_depth and isinstance(cmp, ast.Name) and cmp.id in self.list_names:
                self.out.append(_f(n.lineno, "in-list", f"在迴圈裡對 list {cmp.id} 用 in：每次是 O(n)；如果只是查有沒有，改用 set。"))
            if isinstance(op, (ast.Eq, ast.NotEq)):
                for side in (n.left, cmp):
                    if isinstance(side, ast.Constant) and isinstance(side.value, float):
                        self.out.append(_f(n.lineno, "float-eq", "用 == 比較小數很容易因為浮點誤差出錯；改成 abs(a - b) < 1e-9，或盡量用整數運算。"))
        self.generic_visit(n)

    def visit_ExceptHandler(self, n: ast.ExceptHandler) -> None:
        if n.type is None:
            self.out.append(_f(n.lineno, "bare-except", "裸的 except: 會吞掉所有錯誤（包含你的 bug），本機測不出問題；指定要抓的例外種類。"))
        self.generic_visit(n)


def lint_python(code: str) -> List[Dict[str, Any]]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [_f(e.lineno or 1, "syntax", f"語法錯誤：{e.msg}", "error")]
    v = _V()
    v.visit(tree)
    if v.calls_self and not v.has_setrec:
        v.out.append(_f(1, "recursion", "有遞迴但沒有 sys.setrecursionlimit：Python 預設深度約 1000，輸入大時會 RecursionError；深度很大就改成迴圈。"))
    if v.print_in_loop and v.max_depth >= 1 and not any(x["code"] == "input-loop" for x in v.out):
        pass
    return sorted(v.out, key=lambda x: (x["line"], x["code"]))


def lint_cpp(code: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    lines = code.splitlines()
    uses_cin = "cin" in code
    if uses_cin and "sync_with_stdio" not in code and "scanf" not in code:
        out.append(_f(1, "cin-sync", "用 cin／cout 處理大量輸入時，加上 ios::sync_with_stdio(false); cin.tie(nullptr); 會快很多。"))
    for i, ln in enumerate(lines, 1):
        if "endl" in ln and re.search(r"\b(for|while)\b", "\n".join(lines[max(0, i - 6):i])):
            out.append(_f(i, "endl-loop", "迴圈裡的 endl 會每次清空輸出緩衝，很慢；改用 '\\n'。"))
        if re.search(r"\bint\b[^;=]*=\s*[^;]*\*[^;]*;", ln) and "long long" not in ln:
            out.append(_f(i, "int-overflow", "int 相乘可能超過 約 2.1×10⁹ 而溢位；數值大時改用 long long。"))
    return out


def lint(code: str, lang: str) -> List[Dict[str, Any]]:
    return lint_cpp(code) if lang == "cpp" else lint_python(code)
