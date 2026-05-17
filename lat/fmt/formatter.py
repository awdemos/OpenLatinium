from typing import List, Optional, Union

import lat.ast.nodes as ast
from lat.parsing.ast_parser import parse


class Formatter:
    def __init__(self, indent_size: int = 4):
        self.indent_size = indent_size
        self.lines: List[str] = []

    def format(self, program: ast.Program) -> str:
        self.lines = []

        for decl in program.globals:
            self._write_stmt(decl, 0)

        for func in program.functions:
            if self.lines and self.lines[-1].strip():
                self.lines.append("")
            self._write_function(func)

        return "\n".join(self.lines) + "\n"

    def _indent(self, level: int) -> str:
        return " " * (self.indent_size * level)

    def _write(self, text: str, level: int = 0) -> None:
        self.lines.append(self._indent(level) + text)

    def _write_function(self, func: ast.Function) -> None:
        params = ", ".join(f"{p.name}: {p.type}" for p in func.params)
        ret = f" -> {func.return_type}" if func.return_type else ""
        self._write(f"munus {func.name}({params}){ret} {{")
        for stmt in func.body:
            self._write_stmt(stmt, 1)
        self._write("}")

    def _write_stmt(self, stmt: ast.Stmt, level: int) -> None:
        if isinstance(stmt, ast.Decl):
            self._write_decl(stmt, level)
        elif isinstance(stmt, ast.Assignment):
            self._write_assignment(stmt, level)
        elif isinstance(stmt, ast.Print):
            self._write_print(stmt, level)
        elif isinstance(stmt, ast.If):
            self._write_if(stmt, level)
        elif isinstance(stmt, ast.Match):
            self._write_match(stmt, level)
        elif isinstance(stmt, ast.While):
            self._write_while(stmt, level)
        elif isinstance(stmt, ast.DoWhile):
            self._write_dowhile(stmt, level)
        elif isinstance(stmt, ast.For):
            self._write_for(stmt, level)
        elif isinstance(stmt, ast.Return):
            self._write_return(stmt, level)
        elif isinstance(stmt, ast.Break):
            self._write("confractus", level)
        elif isinstance(stmt, ast.Continue):
            self._write("pergo", level)
        elif isinstance(stmt, ast.FunctionCall):
            self._write(self._fmt_expr(stmt), level)
        elif isinstance(stmt, ast.Read):
            self._write(self._fmt_expr(stmt), level)
        elif isinstance(stmt, ast.Debug):
            self._write("#debug", level)
        else:
            self._write(f"/* unknown stmt: {type(stmt).__name__} */", level)

    def _write_decl(self, decl: ast.Decl, level: int) -> None:
        init = ""
        if decl.value is not None:
            init = f" = {self._fmt_expr(decl.value)}"
        self._write(f"{decl.name}: {decl.type}{init}", level)

    def _write_assignment(self, assign: ast.Assignment, level: int) -> None:
        target = self._fmt_expr(assign.target)
        value = self._fmt_expr(assign.value)
        self._write(f"{target} = {value}", level)

    def _write_print(self, print_stmt: ast.Print, level: int) -> None:
        args = ", ".join(self._fmt_expr(e) for e in print_stmt.expressions)
        self._write(f"imprimo({args})", level)

    def _write_if(self, if_stmt: ast.If, level: int) -> None:
        cond = self._fmt_expr(if_stmt.condition)
        self._write(f"si {cond} {{", level)
        for stmt in if_stmt.then_body:
            self._write_stmt(stmt, level + 1)
        if if_stmt.else_body:
            self._write("} aliter {", level)
            if isinstance(if_stmt.else_body, list):
                for stmt in if_stmt.else_body:
                    self._write_stmt(stmt, level + 1)
            else:
                self._write_stmt(if_stmt.else_body, level + 1)
            self._write("}", level)
        else:
            self._write("}", level)

    def _write_match(self, match: ast.Match, level: int) -> None:
        expr = self._fmt_expr(match.expression)
        self._write(f"par {expr} {{", level)
        for case in match.cases:
            if isinstance(case, ast.Case):
                val = self._fmt_expr(case.value)
                self._write(f"    {val} -> {{", level)
                for stmt in case.body:
                    self._write_stmt(stmt, level + 2)
                self._write(f"    }}", level)
            elif isinstance(case, ast.Default):
                self._write(f"    defectus -> {{", level)
                for stmt in case.body:
                    self._write_stmt(stmt, level + 2)
                self._write(f"    }}", level)
        self._write("}", level)

    def _write_while(self, while_stmt: ast.While, level: int) -> None:
        cond = self._fmt_expr(while_stmt.condition)
        self._write(f"dum {cond} {{", level)
        for stmt in while_stmt.body:
            self._write_stmt(stmt, level + 1)
        self._write("}", level)

    def _write_dowhile(self, dw: ast.DoWhile, level: int) -> None:
        self._write("facio {", level)
        for stmt in dw.body:
            self._write_stmt(stmt, level + 1)
        cond = self._fmt_expr(dw.condition)
        self._write(f"}} dum ({cond})", level)

    def _write_for(self, for_stmt: ast.For, level: int) -> None:
        inits = []
        for init in for_stmt.init:
            if init is None:
                inits.append("")
            elif isinstance(init, ast.Decl):
                decl = f"{init.name}: {init.type}"
                if init.value:
                    decl += f" = {self._fmt_expr(init.value)}"
                inits.append(decl)
            elif isinstance(init, ast.Assignment):
                inits.append(f"{self._fmt_expr(init.target)} = {self._fmt_expr(init.value)}")
        init_str = ", ".join(inits)

        cond = self._fmt_expr(for_stmt.condition)

        updates = []
        for upd in for_stmt.update:
            updates.append(f"{self._fmt_expr(upd.target)} = {self._fmt_expr(upd.value)}")
        update_str = ", ".join(updates)

        self._write(f"enim({init_str}; {cond}; {update_str}) {{", level)
        for stmt in for_stmt.body:
            self._write_stmt(stmt, level + 1)
        self._write("}", level)

    def _write_return(self, ret: ast.Return, level: int) -> None:
        if ret.value is not None:
            self._write(f"reditus {self._fmt_expr(ret.value)}", level)
        else:
            self._write("reditus", level)

    _OP_MAP = {
        'OR': 'aut',
        'AND': 'et',
        'EQ': '==',
        'NEQ': '!=',
        'LT': '<',
        'GT': '>',
        'LTE': '<=',
        'GTE': '>=',
        'NOT': 'non',
    }

    _PRECEDENCE = {
        '[]': 8,
        '()': 8,
        'NOT': 7,
        '-u': 7,
        '*': 6,
        '/': 6,
        '%': 6,
        '+': 5,
        '-': 5,
        'LT': 4,
        'GT': 4,
        'LTE': 4,
        'GTE': 4,
        'EQ': 3,
        'NEQ': 3,
        'AND': 2,
        'OR': 1,
    }

    def _fmt_op(self, op: str) -> str:
        return self._OP_MAP.get(op, op)

    def _precedence(self, op: str) -> int:
        return self._PRECEDENCE.get(op, 0)

    def _needs_parens(self, child: ast.Expr, parent_op: str, is_right: bool = False) -> bool:
        if not isinstance(child, ast.BinaryOp):
            return False
        child_prec = self._precedence(child.op)
        parent_prec = self._precedence(parent_op)
        if child_prec < parent_prec:
            return True
        if child_prec == parent_prec and is_right:
            if parent_op in ('-', '/') and child.op == parent_op:
                return False
            if parent_op in ('+', '*') and child.op == parent_op:
                return False
            return True
        return False

    def _fmt_expr(self, expr: ast.Expr) -> str:
        if isinstance(expr, ast.IntegerLiteral):
            return str(expr.value)
        elif isinstance(expr, ast.FloatLiteral):
            s = str(expr.value)
            if '.' not in s and 'e' not in s:
                s += ".0"
            return s + "f"
        elif isinstance(expr, ast.StringLiteral):
            val = expr.value
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            return f'"{val}"'
        elif isinstance(expr, ast.BooleanLiteral):
            return "verum" if expr.value else "falsum"
        elif isinstance(expr, ast.Identifier):
            return expr.name
        elif isinstance(expr, ast.BinaryOp):
            left = self._fmt_expr(expr.left)
            if self._needs_parens(expr.left, expr.op, is_right=False):
                left = f"({left})"
            right = self._fmt_expr(expr.right)
            if self._needs_parens(expr.right, expr.op, is_right=True):
                right = f"({right})"
            op = self._fmt_op(expr.op)
            return f"{left} {op} {right}"
        elif isinstance(expr, ast.UnaryOp):
            operand = self._fmt_expr(expr.operand)
            op = self._fmt_op(expr.op)
            if op == 'non':
                return f"non {operand}"
            return f"{op}{operand}"
        elif isinstance(expr, ast.ArrayIndex):
            indices = "".join(f"[{self._fmt_expr(i)}]" for i in expr.indices)
            return f"{expr.name}{indices}"
        elif isinstance(expr, ast.ArrayLiteral):
            items = ", ".join(self._fmt_expr(i) for i in expr.items)
            return f"[{items}]"
        elif isinstance(expr, ast.ArrayRange):
            return f"[{self._fmt_expr(expr.start)} ... {self._fmt_expr(expr.end)}]"
        elif isinstance(expr, ast.Ref):
            return f"&{expr.name}"
        elif isinstance(expr, ast.FunctionCall):
            args = ", ".join(self._fmt_expr(a) for a in expr.args)
            return f"{expr.name}({args})"
        elif isinstance(expr, ast.Read):
            exprs = ", ".join(self._fmt_expr(e) for e in expr.expressions)
            return f"legero({exprs})"
        elif isinstance(expr, ast.IfExpr):
            cond = self._fmt_expr(expr.condition)
            then_expr = self._fmt_expr(expr.then_expr)
            else_expr = self._fmt_expr(expr.else_expr)
            return f"si {cond} tunc {then_expr} aliter {else_expr}"
        else:
            return f"/* unknown expr: {type(expr).__name__} */"


def format_source(source: str) -> str:
    program = parse(source)
    formatter = Formatter()
    return formatter.format(program)


def format_file(filepath: str) -> str:
    with open(filepath, 'r') as f:
        source = f.read()
    return format_source(source)
