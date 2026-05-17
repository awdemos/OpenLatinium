import re
from typing import List, Optional

from lat.ast import nodes as ast


def _const_int_value(expr: ast.Expr) -> Optional[int]:
    if isinstance(expr, ast.IntegerLiteral):
        return expr.value
    return None
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
        self.loop_stack: List[tuple] = []
        self.scope_level = 0
        self.scope_stack: List[dict] = [{}]

    def _enter_scope(self):
        self.scope_level += 1
        self.scope_stack.append({})

    def _exit_scope(self):
        self.scope_stack.pop()
        self.scope_level -= 1

    def _gen_body(self, body):
        self._enter_scope()
        for s in body:
            self._gen_stmt(s)
        self._exit_scope()

    def _gen_loop_body(self, body, end_label, cont_label):
        self._enter_scope()
        self.loop_stack.append((end_label, cont_label))
        for s in body:
            self._gen_stmt(s)
        self.loop_stack.pop()
        self._exit_scope()

    def _resolve_name(self, name: str) -> str:
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return name

    def _new_temp(self, type: str) -> Temp:
        self.temp_count += 1
        return Temp(self.temp_count, type)

    def _new_label(self, prefix: str = "L") -> str:
        self.label_count += 1
        return f"{prefix.upper()}{self.label_count}"

    def _parse_array_size(self, type_str: str) -> int:
        m = re.search(r'\[(\d+)\]', type_str)
        return int(m.group(1)) if m else 0

    def _emit_array_range_loop(self, base: Var, rng: ast.ArrayRange):
        raise NotImplementedError("Expression-based array ranges not yet supported in IR path")

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
        self.scope_level = 0
        self.scope_stack = [{}]
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
        unique_name = decl.name
        if self.scope_level > 0:
            unique_name = f"{decl.name}_{self.scope_level}"
        self.scope_stack[-1][decl.name] = unique_name
        self.locals.append(Var(unique_name, decl.type))
        if decl.type.startswith("vec<"):
            if decl.value and isinstance(decl.value, ast.ArrayLiteral):
                size = len(decl.value.items)
                size_const = Const(size, "integer")
            elif decl.value and isinstance(decl.value, ast.ArrayRange):
                start_val = _const_int_value(decl.value.start)
                end_val = _const_int_value(decl.value.end)
                if start_val is not None and end_val is not None:
                    size = end_val - start_val + 1
                    size_const = Const(size, "integer")
                else:
                    start_ir = self._gen_expr(decl.value.start)
                    end_ir = self._gen_expr(decl.value.end)
                    size_temp = self._new_temp("integer")
                    self._emit(BinOp(end_ir, start_ir, "SUB", size_temp))
                    one = Const(1, "integer")
                    self._emit(BinOp(size_temp, one, "ADD", size_temp))
                    size_const = size_temp
            else:
                size = self._parse_array_size(decl.type)
                size_const = Const(size, "integer")
            
            elem_type = decl.type[4:decl.type.index(">")]
            t = self._new_temp("integer")
            self._emit(Alloc(size_const, elem_type, t))
            
            scope = self._resolve_scope(decl.name)
            self._emit(Store(unique_name, scope, t))
            
            if decl.value and isinstance(decl.value, ast.ArrayLiteral):
                base = Var(unique_name, "integer")
                for i, item in enumerate(decl.value.items):
                    item_val = self._gen_expr(item)
                    index = Const(i, "integer")
                    self._emit(ArrayStore(base, index, item_val))
            elif decl.value and isinstance(decl.value, ast.ArrayRange):
                start_val = _const_int_value(decl.value.start)
                end_val = _const_int_value(decl.value.end)
                base = Var(unique_name, "integer")
                if start_val is not None and end_val is not None:
                    for i in range(size):
                        val = Const(start_val + i, "integer")
                        index = Const(i, "integer")
                        self._emit(ArrayStore(base, index, val))
                else:
                    self._emit_array_range_loop(base, decl.value)
        elif decl.type.startswith("&"):
            if decl.value is not None:
                val = self._gen_expr(decl.value)
                scope = self._resolve_scope(decl.name)
                self._emit(Store(unique_name, scope, val))
            else:
                self._emit(Push(Const(0, "integer")))
        else:
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
                    scope = self._resolve_scope(decl.name)
                    self._emit(Store(unique_name, scope, val))
            else:
                scope = self._resolve_scope(decl.name)
                if decl.type == "float":
                    self._emit(Store(unique_name, scope, Const(0.0, "float")))
                elif decl.type == "filum":
                    self._emit(Store(unique_name, scope, Const("", "filum")))
                else:
                    self._emit(Store(unique_name, scope, Const(0, "integer")))


    def _gen_assignment(self, stmt: ast.Assignment):
        val = self._gen_expr(stmt.value)
        if isinstance(stmt.target, ast.Identifier):
            scope = self._resolve_scope(stmt.target.name)
            unique_name = self._resolve_name(stmt.target.name)
            self._emit(Store(unique_name, scope, val))
        elif isinstance(stmt.target, ast.ArrayIndex):
            base = self._gen_expr(ast.Identifier(stmt.target.name))
            if len(stmt.target.indices) == 1:
                index = self._gen_expr(stmt.target.indices[0])
                self._emit(ArrayStore(base, index, val))
            else:
                for idx in stmt.target.indices[:-1]:
                    index = self._gen_expr(idx)
                    t = self._new_temp("integer")
                    self._emit(ArrayLoad(base, index, "integer", t))
                    base = t
                last_index = self._gen_expr(stmt.target.indices[-1])
                self._emit(ArrayStore(base, last_index, val))

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
        if isinstance(stmt.else_body, list):
            self._gen_body(stmt.then_body)
        else:
            self._gen_body(stmt.then_body)
        self._emit(Jump(end_label))

        if stmt.else_body is not None:
            self._add_block(else_label)
            if isinstance(stmt.else_body, list):
                self._gen_body(stmt.else_body)
            else:
                self._gen_body([stmt.else_body])
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
                case_label = self._new_label("case")
                self._emit(Branch(t, case_label, next_label))
                self._add_block(case_label)
                self._gen_body(case.body)
                self._emit(Jump(end_label))
                self._add_block(next_label)
            elif isinstance(case, ast.Default):
                self._add_block(self._new_label("default"))
                self._gen_body(case.body)
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
        self._gen_loop_body(stmt.body, end_label, start_label)
        self._emit(Jump(start_label))

        self._add_block(end_label)

    def _gen_dowhile(self, stmt: ast.DoWhile):
        body_label = self._new_label("dobody")
        cond_label = self._new_label("docond")
        end_label = self._new_label("doend")

        self._emit(Jump(body_label))
        self._add_block(body_label)
        self._gen_loop_body(stmt.body, end_label, cond_label)
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
        cleanup_label = self._new_label("forcleanup")
        end_label = self._new_label("forend")

        self._add_block(init_label)
        self._enter_scope()
        for init in stmt.init:
            if init is not None:
                if isinstance(init, ast.Decl):
                    self._gen_decl(init)
                elif isinstance(init, ast.Assignment):
                    self._gen_assignment(init)

        self._emit(Jump(cond_label))
        self._add_block(cond_label)
        cond = self._gen_expr(stmt.condition)
        self._emit(Branch(cond, body_label, cleanup_label))

        self._add_block(body_label)
        self._gen_loop_body(stmt.body, cleanup_label, update_label)
        self._emit(Jump(update_label))

        self._add_block(update_label)
        for update in stmt.update:
            self._gen_assignment(update)
        self._emit(Jump(cond_label))

        self._add_block(cleanup_label)
        self._exit_scope()
        self._emit(Jump(end_label))

        self._add_block(end_label)

    def _gen_return(self, stmt: ast.Return):
        if stmt.value is not None:
            val = self._gen_expr(stmt.value)
            self._emit(Return(val))
        else:
            self._emit(Return(None))

    def _gen_break(self):
        if self.loop_stack:
            self._emit(Jump(self.loop_stack[-1][0]))

    def _gen_continue(self):
        if self.loop_stack:
            self._emit(Jump(self.loop_stack[-1][1]))

    def _gen_call(self, stmt: ast.FunctionCall):
        args = [self._gen_expr(a) for a in stmt.args]
        self._emit(Call(stmt.name, args, None))

    def _gen_read(self, stmt: ast.Read):
        for expr in stmt.expressions:
            t = self._new_temp("integer")
            self._emit(Read(stmt.read_type, t))
            if isinstance(expr, ast.Identifier):
                scope = self._resolve_scope(expr.name)
                unique_name = self._resolve_name(expr.name)
                self._emit(Store(unique_name, scope, t))
            elif isinstance(expr, ast.ArrayIndex):
                base = self._gen_expr(ast.Identifier(expr.name))
                if len(expr.indices) == 1:
                    index = self._gen_expr(expr.indices[0])
                    self._emit(ArrayStore(base, index, t))
                else:
                    for idx in expr.indices[:-1]:
                        index = self._gen_expr(idx)
                        t_idx = self._new_temp("integer")
                        self._emit(ArrayLoad(base, index, "integer", t_idx))
                        base = t_idx
                    last_index = self._gen_expr(expr.indices[-1])
                    self._emit(ArrayStore(base, last_index, t))

    def _gen_expr(self, expr) -> Operand:
        if isinstance(expr, ast.IntegerLiteral):
            return self._gen_integer_literal(expr)
        elif isinstance(expr, ast.FloatLiteral):
            return self._gen_float_literal(expr)
        elif isinstance(expr, ast.StringLiteral):
            return self._gen_string_literal(expr)
        elif isinstance(expr, ast.BooleanLiteral):
            return self._gen_boolean_literal(expr)
        elif isinstance(expr, ast.IfExpr):
            return self._gen_if_expr(expr)
        elif isinstance(expr, ast.Identifier):
            return self._gen_identifier_expr(expr)
        elif isinstance(expr, ast.BinaryOp):
            return self._gen_binary_op(expr)
        elif isinstance(expr, ast.UnaryOp):
            return self._gen_unary_op(expr)
        elif isinstance(expr, ast.ArrayIndex):
            return self._gen_array_index_expr(expr)
        elif isinstance(expr, ast.FunctionCall):
            return self._gen_function_call_expr(expr)
        elif isinstance(expr, ast.Read):
            return self._gen_read_expr(expr)
        elif isinstance(expr, ast.ArrayLiteral):
            return self._gen_array_literal_expr(expr)
        elif isinstance(expr, ast.Ref):
            return self._gen_ref_expr(expr)
        return Const(0, "integer")

    def _gen_integer_literal(self, expr: ast.IntegerLiteral) -> Operand:
        return Const(expr.value, "integer")

    def _gen_float_literal(self, expr: ast.FloatLiteral) -> Operand:
        return Const(expr.value, "float")

    def _gen_string_literal(self, expr: ast.StringLiteral) -> Operand:
        return Const(expr.value, "filum")

    def _gen_boolean_literal(self, expr: ast.BooleanLiteral) -> Operand:
        return Const(1 if expr.value else 0, "integer")

    def _gen_if_expr(self, expr: ast.IfExpr) -> Operand:
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

    def _gen_identifier_expr(self, expr: ast.Identifier) -> Operand:
        type = self._resolve_type(expr.name)
        unique_name = self._resolve_name(expr.name)
        return Var(unique_name, type)

    def _gen_binary_op(self, expr: ast.BinaryOp) -> Operand:
        left = self._gen_expr(expr.left)
        right = self._gen_expr(expr.right)
        type = self._infer_binop_type(expr.op, left, right)
        t = self._new_temp(type)
        self._emit(BinOp(expr.op, left, right, t))
        return t

    def _gen_unary_op(self, expr: ast.UnaryOp) -> Operand:
        operand = self._gen_expr(expr.operand)
        type = operand.type
        t = self._new_temp(type)
        self._emit(UnaryOp(expr.op, operand, t))
        return t

    def _gen_array_index_expr(self, expr: ast.ArrayIndex) -> Operand:
        base = self._gen_expr(ast.Identifier(expr.name))
        elem_type = self._infer_elem_type(base.type)
        for idx in expr.indices:
            index = self._gen_expr(idx)
            t = self._new_temp(elem_type)
            self._emit(ArrayLoad(base, index, elem_type, t))
            base = t
        return base

    def _gen_function_call_expr(self, expr: ast.FunctionCall) -> Operand:
        args = [self._gen_expr(a) for a in expr.args]
        t = self._new_temp("integer")
        self._emit(Call(expr.name, args, t))
        return t

    def _gen_read_expr(self, expr: ast.Read) -> Operand:
        t = self._new_temp("integer")
        self._emit(Read(expr.read_type, t))
        return t

    def _gen_array_literal_expr(self, expr: ast.ArrayLiteral) -> Operand:
        size = len(expr.items)
        size_const = Const(size, "integer")
        t = self._new_temp("integer")
        self._emit(Alloc(size_const, "integer", t))
        temp_name = f"_arr_base_{self.temp_count}"
        self.locals.append(Var(temp_name, "integer"))
        self._emit(Store(temp_name, "local", t))
        base = Var(temp_name, "integer")
        for i, item in enumerate(expr.items):
            item_val = self._gen_expr(item)
            index = Const(i, "integer")
            self._emit(ArrayStore(base, index, item_val))
        return base

    def _gen_ref_expr(self, expr: ast.Ref) -> Operand:
        var_type = self._resolve_type(expr.name)
        unique_name = self._resolve_name(expr.name)
        return Var(unique_name, var_type)

    def _resolve_scope(self, name: str) -> str:
        for p in self.params:
            if p.name == name:
                return "param"
        for l in reversed(self.locals):
            if l.name == name:
                return "local"
        for g in self.globals:
            if g.name == name:
                return "global"
        return "local"

    def _resolve_type(self, name: str) -> str:
        # First resolve to unique name using scope stack
        unique_name = self._resolve_name(name)
        for p in self.params:
            if p.name == unique_name:
                return p.type
        for l in reversed(self.locals):
            if l.name == unique_name:
                return l.type
        for g in self.globals:
            if g.name == unique_name:
                return g.type
        return "integer"

    def _infer_binop_type(self, op: str, left: Operand, right: Operand) -> str:
        if op in ("+", "-", "*", "/"):
            if left.type == "float" or right.type == "float":
                return "float"
            if left.type == "filum" and right.type == "filum":
                return "filum"
            if left.type == "filum" and right.type == "integer" and op == "*":
                return "filum"
            if left.type == "integer" and right.type == "filum" and op == "*":
                return "filum"
            return "integer"
        if op in ("<", ">", "<=", ">=", "==", "!="):
            return "integer"
        if op in ("&&", "||"):
            return "integer"
        return "integer"

    def _infer_elem_type(self, type_str: str) -> str:
        if type_str.startswith("vec<"):
            return type_str[4:-1]
        elif type_str.startswith("&"):
            return type_str[1:]
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
            return self._infer_binary_op_type(expr)
        elif isinstance(expr, ast.UnaryOp):
            return self._infer_expr_type(expr.operand)
        elif isinstance(expr, ast.ArrayIndex):
            return self._infer_array_index_type(expr)
        elif isinstance(expr, ast.FunctionCall):
            return "integer"
        elif isinstance(expr, ast.Read):
            return expr.read_type
        return "integer"

    def _infer_binary_op_type(self, expr: ast.BinaryOp) -> str:
        left = self._infer_expr_type(expr.left)
        right = self._infer_expr_type(expr.right)
        if expr.op in ("+", "-", "*", "/", "%"):
            if left == "float" or right == "float":
                return "float"
            return "integer"
        return "integer"

    def _infer_array_index_type(self, expr: ast.ArrayIndex) -> str:
        base_type = self._resolve_type(expr.name)
        if base_type.startswith("vec<"):
            return base_type[4:-1]
        elif base_type.startswith("&"):
            return base_type[1:]
        return "integer"
