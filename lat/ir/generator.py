from typing import List, Optional

from lat.ast import nodes as ast
from lat.ir.nodes import (
    Alloc, ArrayLoad, ArrayStore, BasicBlock, BinOp, Branch, Call,
    Const, IRFunction, IRProgram, Jump, Label, Load, Push, Read, Return,
    Store, Temp, UnaryOp, Var, Write
)


class IRGenerator:
    def __init__(self):
        self.temp_count = 0
        self.label_count = 0
        self.globals: List[Var] = []
        self.locals: List[Var] = []
        self.params: List[Var] = []
        self.current_blocks: List[BasicBlock] = []
        self.current_function: Optional[str] = None

    def _new_temp(self, type: str) -> Temp:
        self.temp_count += 1
        return Temp(self.temp_count, type)

    def _new_label(self, prefix: str = "L") -> str:
        self.label_count += 1
        return f"{prefix.upper()}{self.label_count}"

    def _emit(self, instr):
        if self.current_blocks:
            self.current_blocks[-1].instructions.append(instr)

    def _current_block(self) -> BasicBlock:
        return self.current_blocks[-1]

    def _add_block(self, label: str) -> BasicBlock:
        block = BasicBlock(label)
        self.current_blocks.append(block)
        return block

    def generate(self, program: ast.Program) -> IRProgram:
        functions = []
        for decl in program.globals:
            self.globals.append(Var(decl.name, decl.type))
        for func in program.functions:
            functions.append(self._gen_function(func))
        return IRProgram(globals=self.globals, functions=functions)

    def _gen_function(self, func: ast.Function) -> IRFunction:
        self.temp_count = 0
        self.label_count = 0
        self.locals = []
        self.params = [Var(p.name, p.type) for p in func.params]
        self.current_function = func.name
        self.current_blocks = []

        entry_label = self._new_label("entry")
        self._add_block(entry_label)

        for stmt in func.body:
            self._gen_stmt(stmt)

        if not self._current_block().instructions or not isinstance(
            self._current_block().instructions[-1], (Return, Jump, Branch)
        ):
            self._emit(Return(None))

        blocks = self.current_blocks
        self.current_blocks = []
        self.current_function = None

        return IRFunction(
            name=func.name,
            params=self.params,
            return_type=func.return_type,
            locals=self.locals,
            blocks=blocks,
            entry_block=entry_label,
        )

    def _gen_stmt(self, stmt):
        if isinstance(stmt, ast.Decl):
            self._gen_decl(stmt)
        elif isinstance(stmt, ast.Assignment):
            self._gen_assignment(stmt)
        elif isinstance(stmt, ast.Print):
            self._gen_print(stmt)
        elif isinstance(stmt, ast.If):
            self._gen_if(stmt)
        elif isinstance(stmt, ast.Match):
            self._gen_match(stmt)
        elif isinstance(stmt, ast.While):
            self._gen_while(stmt)
        elif isinstance(stmt, ast.DoWhile):
            self._gen_dowhile(stmt)
        elif isinstance(stmt, ast.For):
            self._gen_for(stmt)
        elif isinstance(stmt, ast.Return):
            self._gen_return(stmt)
        elif isinstance(stmt, ast.Break):
            self._gen_break()
        elif isinstance(stmt, ast.Continue):
            self._gen_continue()
        elif isinstance(stmt, ast.FunctionCall):
            self._gen_call(stmt)
        elif isinstance(stmt, ast.Read):
            self._gen_read(stmt)

    def _gen_decl(self, decl: ast.Decl):
        self.locals.append(Var(decl.name, decl.type))
        if decl.value is not None:
            if isinstance(decl.value, ast.IfExpr):
                cond = self._gen_expr(decl.value.condition)
                then_label = self._new_label("ifexprthen")
                else_label = self._new_label("ifexprelse")
                end_label = self._new_label("ifexprend")
                self._emit(Branch(cond, then_label, else_label))
                self._add_block(then_label)
                then_val = self._gen_expr(decl.value.then_expr)
                if isinstance(then_val, Const):
                    self._emit(Push(then_val))
                self._emit(Jump(end_label))
                self._add_block(else_label)
                else_val = self._gen_expr(decl.value.else_expr)
                if isinstance(else_val, Const):
                    self._emit(Push(else_val))
                self._emit(Jump(end_label))
                self._add_block(end_label)
            else:
                val = self._gen_expr(decl.value)
                if isinstance(val, Const):
                    self._emit(Push(val))
        else:
            if decl.type == "integer" or decl.type == "boolean":
                self._emit(Push(Const(0, "integer")))
            elif decl.type == "float":
                self._emit(Push(Const(0.0, "float")))
            elif decl.type == "filum":
                self._emit(Push(Const("", "filum")))
            else:
                self._emit(Push(Const(0, "integer")))

    def _gen_assignment(self, stmt: ast.Assignment):
        val = self._gen_expr(stmt.value)
        if isinstance(stmt.target, ast.Identifier):
            scope = self._resolve_scope(stmt.target.name)
            self._emit(Store(stmt.target.name, scope, val))
        elif isinstance(stmt.target, ast.ArrayIndex):
            base = self._gen_expr(ast.Identifier(stmt.target.name))
            for idx in stmt.target.indices:
                index = self._gen_expr(idx)
                t = self._new_temp("integer")
                self._emit(ArrayLoad(base, index, "integer", t))
                base = t
            self._emit(ArrayStore(base, Const(0, "integer"), val))

    def _gen_print(self, stmt: ast.Print):
        for expr in stmt.expressions:
            val = self._gen_expr(expr)
            self._emit(Write(val))

    def _gen_if(self, stmt: ast.If):
        cond = self._gen_expr(stmt.condition)
        then_label = self._new_label("then")
        else_label = self._new_label("else")
        end_label = self._new_label("end")

        if stmt.else_body is not None:
            self._emit(Branch(cond, then_label, else_label))
        else:
            self._emit(Branch(cond, then_label, end_label))

        self._add_block(then_label)
        for s in stmt.then_body:
            self._gen_stmt(s)
        self._emit(Jump(end_label))

        if stmt.else_body is not None:
            self._add_block(else_label)
            if isinstance(stmt.else_body, list):
                for s in stmt.else_body:
                    self._gen_stmt(s)
            else:
                self._gen_stmt(stmt.else_body)
            self._emit(Jump(end_label))

        self._add_block(end_label)

    def _gen_match(self, stmt: ast.Match):
        expr = self._gen_expr(stmt.expression)
        end_label = self._new_label("endmatch")

        for i, case in enumerate(stmt.cases):
            if isinstance(case, ast.Case):
                case_val = self._gen_expr(case.value)
                t = self._new_temp("integer")
                self._emit(BinOp("==", expr, case_val, t))
                next_label = self._new_label("nextcase")
                case_label = f"CASE{i}"
                self._emit(Branch(t, case_label, next_label))
                self._add_block(case_label)
                for s in case.body:
                    self._gen_stmt(s)
                self._emit(Jump(end_label))
                self._add_block(next_label)
            elif isinstance(case, ast.Default):
                self._add_block(self._new_label("default"))
                for s in case.body:
                    self._gen_stmt(s)
                self._emit(Jump(end_label))

        self._add_block(end_label)

    def _gen_while(self, stmt: ast.While):
        start_label = self._new_label("whilestart")
        body_label = self._new_label("whilebody")
        end_label = self._new_label("whileend")

        self._emit(Jump(start_label))
        self._add_block(start_label)
        cond = self._gen_expr(stmt.condition)
        self._emit(Branch(cond, body_label, end_label))

        self._add_block(body_label)
        for s in stmt.body:
            self._gen_stmt(s)
        self._emit(Jump(start_label))

        self._add_block(end_label)

    def _gen_dowhile(self, stmt: ast.DoWhile):
        body_label = self._new_label("dobody")
        cond_label = self._new_label("docond")
        end_label = self._new_label("doend")

        self._emit(Jump(body_label))
        self._add_block(body_label)
        for s in stmt.body:
            self._gen_stmt(s)
        self._emit(Jump(cond_label))

        self._add_block(cond_label)
        cond = self._gen_expr(stmt.condition)
        self._emit(Branch(cond, body_label, end_label))

        self._add_block(end_label)

    def _gen_for(self, stmt: ast.For):
        init_label = self._new_label("forinit")
        cond_label = self._new_label("forcond")
        body_label = self._new_label("forbody")
        update_label = self._new_label("forupdate")
        end_label = self._new_label("forend")

        self._add_block(init_label)
        for init in stmt.init:
            if init is not None:
                if isinstance(init, ast.Decl):
                    self._gen_decl(init)
                elif isinstance(init, ast.Assignment):
                    self._gen_assignment(init)

        self._emit(Jump(cond_label))
        self._add_block(cond_label)
        cond = self._gen_expr(stmt.condition)
        self._emit(Branch(cond, body_label, end_label))

        self._add_block(body_label)
        for s in stmt.body:
            self._gen_stmt(s)
        self._emit(Jump(update_label))

        self._add_block(update_label)
        for update in stmt.update:
            self._gen_assignment(update)
        self._emit(Jump(cond_label))

        self._add_block(end_label)

    def _gen_return(self, stmt: ast.Return):
        if stmt.value is not None:
            val = self._gen_expr(stmt.value)
            self._emit(Return(val))
        else:
            self._emit(Return(None))

    def _gen_break(self):
        pass

    def _gen_continue(self):
        pass

    def _gen_call(self, stmt: ast.FunctionCall):
        args = [self._gen_expr(a) for a in stmt.args]
        self._emit(Call(stmt.name, args, None))

    def _gen_read(self, stmt: ast.Read):
        for expr in stmt.expressions:
            val = self._gen_expr(expr)
            t = self._new_temp("integer")
            self._emit(Read(stmt.read_type, t))
            self._emit(Store(val.name, self._resolve_scope(val.name), t))

    def _gen_expr(self, expr) -> Operand:
        if isinstance(expr, ast.IntegerLiteral):
            return Const(expr.value, "integer")
        elif isinstance(expr, ast.FloatLiteral):
            return Const(expr.value, "float")
        elif isinstance(expr, ast.StringLiteral):
            return Const(expr.value, "filum")
        elif isinstance(expr, ast.BooleanLiteral):
            return Const(1 if expr.value else 0, "integer")
        elif isinstance(expr, ast.IfExpr):
            result_name = f"ifexpr_result_{self.temp_count}"
            self.temp_count += 1
            then_type = self._infer_expr_type(expr.then_expr)
            self.locals.append(Var(result_name, then_type))
            if then_type == "integer" or then_type == "boolean":
                self._emit(Push(Const(0, "integer")))
            elif then_type == "float":
                self._emit(Push(Const(0.0, "float")))
            elif then_type == "filum":
                self._emit(Push(Const("", "filum")))
            else:
                self._emit(Push(Const(0, "integer")))
            t = self._new_temp(then_type)
            then_label = self._new_label("ifexprthen")
            else_label = self._new_label("ifexprelse")
            end_label = self._new_label("ifexprend")
            cond = self._gen_expr(expr.condition)
            self._emit(Branch(cond, then_label, else_label))
            self._add_block(then_label)
            then_val = self._gen_expr(expr.then_expr)
            self._emit(Store(result_name, "local", then_val))
            self._emit(Jump(end_label))
            self._add_block(else_label)
            else_val = self._gen_expr(expr.else_expr)
            self._emit(Store(result_name, "local", else_val))
            self._emit(Jump(end_label))
            self._add_block(end_label)
            self._emit(Load(result_name, "local", then_type, t))
            return t
        elif isinstance(expr, ast.Identifier):
            scope = self._resolve_scope(expr.name)
            type = self._resolve_type(expr.name)
            t = self._new_temp(type)
            self._emit(Load(expr.name, scope, type, t))
            return t
        elif isinstance(expr, ast.BinaryOp):
            left = self._gen_expr(expr.left)
            right = self._gen_expr(expr.right)
            type = self._infer_binop_type(expr.op, left, right)
            t = self._new_temp(type)
            self._emit(BinOp(expr.op, left, right, t))
            return t
        elif isinstance(expr, ast.UnaryOp):
            operand = self._gen_expr(expr.operand)
            type = operand.type
            t = self._new_temp(type)
            self._emit(UnaryOp(expr.op, operand, t))
            return t
        elif isinstance(expr, ast.ArrayIndex):
            base = self._gen_expr(ast.Identifier(expr.name))
            for idx in expr.indices:
                index = self._gen_expr(idx)
                t = self._new_temp("integer")
                self._emit(ArrayLoad(base, index, "integer", t))
                base = t
            return base
        elif isinstance(expr, ast.FunctionCall):
            args = [self._gen_expr(a) for a in expr.args]
            t = self._new_temp("integer")
            self._emit(Call(expr.name, args, t))
            return t
        elif isinstance(expr, ast.Read):
            t = self._new_temp("integer")
            self._emit(Read(expr.read_type, t))
            return t
        elif isinstance(expr, ast.ArrayLiteral):
            return Const(0, "integer")
        elif isinstance(expr, ast.Ref):
            return Const(0, "integer")
        return Const(0, "integer")

    def _resolve_scope(self, name: str) -> str:
        for p in self.params:
            if p.name == name:
                return "param"
        for l in self.locals:
            if l.name == name:
                return "local"
        for g in self.globals:
            if g.name == name:
                return "global"
        return "local"

    def _resolve_type(self, name: str) -> str:
        for p in self.params:
            if p.name == name:
                return p.type
        for l in self.locals:
            if l.name == name:
                return l.type
        for g in self.globals:
            if g.name == name:
                return g.type
        return "integer"

    def _infer_binop_type(self, op: str, left: Operand, right: Operand) -> str:
        if op in ("+", "-", "*", "/", "%"):
            if left.type == "float" or right.type == "float":
                return "float"
            return "integer"
        if op in ("<", ">", "<=", ">=", "==", "!="):
            return "integer"
        if op in ("&&", "||"):
            return "integer"
        return "integer"

    def _infer_expr_type(self, expr) -> str:
        if isinstance(expr, ast.IntegerLiteral):
            return "integer"
        elif isinstance(expr, ast.FloatLiteral):
            return "float"
        elif isinstance(expr, ast.StringLiteral):
            return "filum"
        elif isinstance(expr, ast.BooleanLiteral):
            return "boolean"
        elif isinstance(expr, ast.Identifier):
            return self._resolve_type(expr.name)
        elif isinstance(expr, ast.BinaryOp):
            left = self._infer_expr_type(expr.left)
            right = self._infer_expr_type(expr.right)
            if expr.op in ("+", "-", "*", "/", "%"):
                if left == "float" or right == "float":
                    return "float"
                return "integer"
            return "integer"
        elif isinstance(expr, ast.UnaryOp):
            return self._infer_expr_type(expr.operand)
        elif isinstance(expr, ast.ArrayIndex):
            base_type = self._resolve_type(expr.name)
            if base_type.startswith("vec<"):
                return base_type[4:-1]
            elif base_type.startswith("&"):
                return base_type[1:]
            return "integer"
        elif isinstance(expr, ast.FunctionCall):
            return "integer"
        elif isinstance(expr, ast.Read):
            return expr.read_type
        return "integer"
