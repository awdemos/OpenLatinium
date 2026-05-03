"""Semantic analyzer for OpenLatinum AST. Collects all errors instead of exiting on first error."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Union
import sys

from lat.ast.nodes import *
from lat.utils.errors import std_message, compiler_error, compiler_note


@dataclass
class SemanticError:
    message: str
    line: int = 0
    column: int = 0
    notes: List[str] = field(default_factory=list)


@dataclass
class VarInfo:
    name: str
    type: str
    is_global: bool
    is_initialized: bool = True
    array_shape: Optional[List[int]] = None
    is_const: bool = False


@dataclass
class Scope:
    name: str
    level: int
    parent: Optional['Scope'] = None
    in_function: bool = False
    in_loop: bool = False
    variables: Dict[str, VarInfo] = field(default_factory=dict)

    def define(self, name: str, type: str, is_global: bool = False,
               is_initialized: bool = True, array_shape: Optional[List[int]] = None,
               is_const: bool = False) -> None:
        self.variables[name] = VarInfo(name, type, is_global, is_initialized, array_shape, is_const)

    def lookup(self, name: str) -> Optional[VarInfo]:
        if name in self.variables:
            return self.variables[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        return None

    def is_defined_locally(self, name: str) -> bool:
        return name in self.variables


@dataclass
class FuncInfo:
    name: str
    param_types: List[str]
    return_type: Optional[str]


class SemanticAnalyzer:

    def __init__(self):
        self.errors: List[SemanticError] = []
        self.warnings: List[SemanticError] = []
        self.scope: Optional[Scope] = None
        self.functions: Dict[str, FuncInfo] = {}
        self.current_function: Optional[FuncInfo] = None

    def analyze(self, program: Program) -> Tuple[bool, List[SemanticError], List[SemanticError]]:
        self.errors = []
        self.warnings = []
        self.scope = Scope(name="global", level=0)
        self.functions = {}
        self.current_function = None

        for func in program.functions:
            self._declare_function(func)
        for decl in program.globals:
            self.visit_decl(decl, is_global=True)
        for func in program.functions:
            self.visit_function(func)

        return len(self.errors) == 0, self.errors, self.warnings

    def _declare_function(self, func: Function) -> None:
        if func.name in self.functions:
            self.error(f"Redefinition of function '{func.name}'")
            return

        param_types = [p.type for p in func.params]
        self.functions[func.name] = FuncInfo(func.name, param_types, func.return_type)

    def error(self, message: str, notes: Optional[List[str]] = None) -> None:
        self.errors.append(SemanticError(message, notes=notes or []))

    def warn(self, message: str, notes: Optional[List[str]] = None) -> None:
        self.warnings.append(SemanticError(message, notes=notes or []))

    def push_scope(self, name: str, in_function: bool = False, in_loop: bool = False) -> None:
        self.scope = Scope(
            name=name,
            level=self.scope.level + 1 if self.scope else 0,
            parent=self.scope,
            in_function=in_function,
            in_loop=in_loop
        )

    def pop_scope(self) -> None:
        if self.scope is not None:
            self.scope = self.scope.parent

    def visit_function(self, func: Function) -> None:
        func_info = self.functions.get(func.name)
        if func_info is None:
            self.error(f"Internal error: function '{func.name}' not found in function table")
            return

        self.current_function = func_info
        self.push_scope(name=f"func_{func.name}", in_function=True)

        for param in func.params:
            if self.scope.is_defined_locally(param.name):
                self.error(f"Parameter '{param.name}' is already defined")
            else:
                self.scope.define(param.name, param.type, is_global=False)

        for stmt in func.body:
            self.visit_stmt(stmt)

        self.pop_scope()
        self.current_function = None

    def visit_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, Decl):
            self.visit_decl(stmt)
        elif isinstance(stmt, Assignment):
            self.visit_assignment(stmt)
        elif isinstance(stmt, Print):
            self.visit_print(stmt)
        elif isinstance(stmt, If):
            self.visit_if(stmt)
        elif isinstance(stmt, Match):
            self.visit_match(stmt)
        elif isinstance(stmt, While):
            self.visit_while(stmt)
        elif isinstance(stmt, DoWhile):
            self.visit_dowhile(stmt)
        elif isinstance(stmt, For):
            self.visit_for(stmt)
        elif isinstance(stmt, Return):
            self.visit_return(stmt)
        elif isinstance(stmt, Break):
            self.visit_break(stmt)
        elif isinstance(stmt, Continue):
            self.visit_continue(stmt)
        elif isinstance(stmt, FunctionCall):
            self.visit_function_call(stmt)
        elif isinstance(stmt, Read):
            self.visit_read(stmt)
        elif isinstance(stmt, Debug):
            pass  # Debug is a no-op
        else:
            self.error(f"Unknown statement type: {type(stmt).__name__}")

    def visit_decl(self, decl: Decl, is_global: bool = False) -> None:
        if self.scope.is_defined_locally(decl.name):
            self.error(f"Variable '{decl.name}' is already defined")
            return

        decl_type = decl.type.replace(" ", "")

        if not self._is_valid_type(decl_type):
            self.error(f"Invalid type '{decl_type}'")
            return

        if decl.value is not None:
            init_type = self.visit_expr(decl.value)
            if init_type is not None and not self._types_compatible(decl_type, init_type):
                self.error(f"Cannot initialize variable of type '{decl_type}' with value of type '{init_type}'")
                return

        self.scope.define(decl.name, decl_type, is_global=is_global, is_const=decl.is_const)

    def visit_assignment(self, assign: Assignment) -> None:
        value_type = self.visit_expr(assign.value)

        if isinstance(assign.target, Identifier):
            var = self.scope.lookup(assign.target.name)
            if var is None:
                self.error(f"Assignment to undeclared variable '{assign.target.name}'")
                return
            if var.is_const:
                self.error(f"Cannot assign to constant variable '{assign.target.name}'")
                return
            if var.type.startswith("vec"):
                self.error("Assignment to array not allowed. Use indexing instead.")
                return
            if not self._types_compatible(var.type, value_type):
                self.error(f"Cannot assign value of type '{value_type}' to variable of type '{var.type}'")
        elif isinstance(assign.target, ArrayIndex):
            var = self.scope.lookup(assign.target.name)
            if var is None:
                self.error(f"Assignment to undeclared variable '{assign.target.name}'")
                return
            if not var.type.startswith("vec") and not var.type.startswith("&"):
                self.error(f"Indexing not allowed on variable of type '{var.type}'")
                return
            if var.array_shape and len(assign.target.indices) != len(var.array_shape):
                self.error(f"Assignment to arrays only allowed with the same number of dimensions. Expected {len(var.array_shape)} got {len(assign.target.indices)}")
                return
            for idx in assign.target.indices:
                idx_type = self.visit_expr(idx)
                if idx_type is not None and idx_type != "integer":
                    self.error(f"Array index must be of type 'integer', got '{idx_type}'")
            if var.type.startswith("vec"):
                elem_type = self._extract_vec_inner(var.type)
                if value_type is not None and value_type != elem_type:
                    self.error(f"Cannot assign value of type '{value_type}' to array element of type '{elem_type}'")
            elif var.type.startswith("&"):
                elem_type = var.type[1:]
                if value_type is not None and value_type != elem_type:
                    self.error(f"Cannot assign value of type '{value_type}' to pointer element of type '{elem_type}'")

    def visit_print(self, print_stmt: Print) -> None:
        for expr in print_stmt.expressions:
            expr_type = self.visit_expr(expr)
            if expr_type is not None and expr_type not in ("integer", "float", "filum"):
                if expr_type.startswith("vec"):
                    self.error("Can't print array. Not implemented yet.")
                else:
                    self.error(f"Can't print expression of type '{expr_type}'")

    def visit_if(self, if_stmt: If) -> None:
        cond_type = self.visit_expr(if_stmt.condition)
        if cond_type is not None and cond_type not in ("integer", "boolean"):
            self.error(f"Condition must be of type 'integer' or 'boolean', got '{cond_type}'")

        self.push_scope(name="if")
        for stmt in if_stmt.then_body:
            self.visit_stmt(stmt)
        self.pop_scope()

        if if_stmt.else_body is not None:
            self.push_scope(name="else")
            if isinstance(if_stmt.else_body, list):
                for stmt in if_stmt.else_body:
                    self.visit_stmt(stmt)
            else:
                self.visit_stmt(if_stmt.else_body)
            self.pop_scope()

    def visit_match(self, match_stmt: Match) -> None:
        expr_type = self.visit_expr(match_stmt.expression)
        for case in match_stmt.cases:
            if isinstance(case, Default):
                self.push_scope(name="match_default")
                for stmt in case.body:
                    self.visit_stmt(stmt)
                self.pop_scope()
            elif isinstance(case, Case):
                case_type = self.visit_expr(case.value)
                if expr_type is not None and case_type is not None and expr_type != case_type:
                    self.error(f"Case value type '{case_type}' doesn't match match expression type '{expr_type}'")
                self.push_scope(name="match_case")
                for stmt in case.body:
                    self.visit_stmt(stmt)
                self.pop_scope()

    def visit_while(self, while_stmt: While) -> None:
        self.push_scope(name="while", in_loop=True)
        cond_type = self.visit_expr(while_stmt.condition)
        if cond_type is not None and cond_type not in ("integer", "boolean"):
            self.error(f"Condition must be of type 'integer' or 'boolean', got '{cond_type}'")

        self.push_scope(name="while", in_loop=True)
        for stmt in while_stmt.body:
            self.visit_stmt(stmt)
        self.pop_scope()

    def visit_dowhile(self, dowhile_stmt: DoWhile) -> None:
        self.push_scope(name="dowhile", in_loop=True)
        for stmt in dowhile_stmt.body:
            self.visit_stmt(stmt)
        self.pop_scope()

        cond_type = self.visit_expr(dowhile_stmt.condition)
        if cond_type is not None and cond_type not in ("integer", "boolean"):
            self.error(f"Condition must be of type 'integer' or 'boolean', got '{cond_type}'")

    def visit_for(self, for_stmt: For) -> None:
        self.push_scope(name="for", in_loop=True)

        for init in for_stmt.init:
            if init is not None:
                if isinstance(init, Decl):
                    self.visit_decl(init)
                elif isinstance(init, Assignment):
                    self.visit_assignment(init)

        cond_type = self.visit_expr(for_stmt.condition)
        if cond_type is not None and cond_type not in ("integer", "boolean"):
            self.error(f"Condition must be of type 'integer' or 'boolean', got '{cond_type}'")

        for update in for_stmt.update:
            self.visit_assignment(update)

        for stmt in for_stmt.body:
            self.visit_stmt(stmt)

        self.pop_scope()

    def visit_return(self, ret: Return) -> None:
        if self.current_function is None:
            self.error("Return statement outside of function")
            return

        if ret.value is not None:
            expr_type = self.visit_expr(ret.value)
            expected = self.current_function.return_type
            if expected is None:
                self.error(f"Function '{self.current_function.name}' does not return a value")
            elif expr_type is not None and expr_type != expected:
                self.error(f"Return type '{expr_type}' doesn't match function output type '{expected}'")
        else:
            if self.current_function.return_type is not None:
                self.error(f"Function '{self.current_function.name}' must return a value of type '{self.current_function.return_type}'")

    def visit_break(self, brk: Break) -> None:
        if not self._in_loop():
            self.error("Break statement outside of loop")

    def visit_continue(self, cont: Continue) -> None:
        if not self._in_loop():
            self.error("Continue statement outside of loop")

    def visit_read(self, read_stmt: Read) -> None:
        for expr in read_stmt.expressions:
            self.visit_expr(expr)

    def visit_expr(self, expr: Expr) -> Optional[str]:
        if isinstance(expr, IntegerLiteral):
            return "integer"
        elif isinstance(expr, FloatLiteral):
            return "float"
        elif isinstance(expr, StringLiteral):
            return "filum"
        elif isinstance(expr, BooleanLiteral):
            return "boolean"
        elif isinstance(expr, Identifier):
            return self.visit_identifier(expr)
        elif isinstance(expr, BinaryOp):
            return self.visit_binary_op(expr)
        elif isinstance(expr, UnaryOp):
            return self.visit_unary_op(expr)
        elif isinstance(expr, ArrayIndex):
            return self.visit_array_index(expr)
        elif isinstance(expr, ArrayLiteral):
            return self.visit_array_literal(expr)
        elif isinstance(expr, ArrayRange):
            return self.visit_array_range(expr)
        elif isinstance(expr, Ref):
            return self.visit_ref(expr)
        elif isinstance(expr, FunctionCall):
            return self.visit_function_call(expr)
        elif isinstance(expr, Read):
            return self.visit_read_expr(expr)
        elif isinstance(expr, IfExpr):
            return self.visit_if_expr(expr)
        else:
            self.error(f"Unknown expression type: {type(expr).__name__}")
            return None

    def visit_identifier(self, ident: Identifier) -> Optional[str]:
        var = self.scope.lookup(ident.name)
        if var is None:
            self.error(f"Undeclared variable '{ident.name}'")
            return None
        return var.type

    def visit_binary_op(self, op: BinaryOp) -> Optional[str]:
        left_type = self.visit_expr(op.left)
        right_type = self.visit_expr(op.right)

        if left_type is None or right_type is None:
            return None

        op_map = {
            '+': self._check_add, 'ADD': self._check_add,
            '-': self._check_sub, 'SUB': self._check_sub,
            '*': self._check_mul, 'MUL': self._check_mul,
            '/': self._check_div, 'DIV': self._check_div,
            '%': self._check_mod, 'MOD': self._check_mod,
            '<': self._check_lt, 'LT': self._check_lt,
            '<=': self._check_lte, 'LTE': self._check_lte,
            '>': self._check_gt, 'GT': self._check_gt,
            '>=': self._check_gte, 'GTE': self._check_gte,
            '==': self._check_eq, 'EQ': self._check_eq,
            '!=': self._check_neq, 'NEQ': self._check_neq,
            '&&': self._check_and, 'AND': self._check_and,
            '||': self._check_or, 'OR': self._check_or,
        }

        check = op_map.get(op.op)
        if check is None:
            self.error(f"Unknown binary operator '{op.op}'")
            return None

        return check(left_type, right_type)

    def visit_unary_op(self, op: UnaryOp) -> Optional[str]:
        operand_type = self.visit_expr(op.operand)
        if operand_type is None:
            return None

        if op.op == '!':
            if operand_type in ("integer", "float"):
                return "integer"
            self.error(f"Operation 'not' not supported for type '{operand_type}'")
            return None
        elif op.op == '-':
            if operand_type == "integer":
                return "integer"
            elif operand_type == "float":
                return "float"
            self.error(f"Operation 'neg' not supported for type '{operand_type}'")
            return None
        else:
            self.error(f"Unknown unary operator '{op.op}'")
            return None

    def visit_array_index(self, idx: ArrayIndex) -> Optional[str]:
        var = self.scope.lookup(idx.name)
        if var is None:
            self.error(f"Undeclared variable '{idx.name}'")
            return None

        if not var.type.startswith("vec") and not var.type.startswith("&"):
            self.error(f"Indexing not allowed on variable of type '{var.type}'")
            return None

        if var.type.startswith("&") and len(idx.indices) > 1:
            self.error("Can't index pointer with more than one dimension")
            return None

        if var.array_shape and len(idx.indices) != len(var.array_shape):
            self.error(f"Array access requires {len(var.array_shape)} dimensions, got {len(idx.indices)}")
            return None

        for index in idx.indices:
            index_type = self.visit_expr(index)
            if index_type is not None and index_type != "integer":
                self.error(f"Array index must be of type 'integer', got '{index_type}'")

        if var.type.startswith("vec"):
            return self._extract_vec_inner(var.type)
        elif var.type.startswith("&"):
            return var.type[1:]
        return None

    def visit_array_literal(self, lit: ArrayLiteral) -> Optional[str]:
        if not lit.items:
            self.error("Empty array literal")
            return None

        first_type = self.visit_expr(lit.items[0])
        if first_type is None:
            return None

        for item in lit.items[1:]:
            item_type = self.visit_expr(item)
            if item_type is not None and item_type != first_type:
                self.error(f"Array literal has mixed types: '{first_type}' and '{item_type}'")
                return None

        return f"vec<{first_type}>"

    def visit_array_range(self, rng: ArrayRange) -> Optional[str]:
        return "vec<integer>"

    def visit_if_expr(self, expr: IfExpr) -> Optional[str]:
        cond_type = self.visit_expr(expr.condition)
        if cond_type is not None and cond_type != "boolean":
            self.error(f"If expression condition must be 'boolean', got '{cond_type}'")
        then_type = self.visit_expr(expr.then_expr)
        else_type = self.visit_expr(expr.else_expr)
        if then_type is not None and else_type is not None and then_type != else_type:
            self.error(f"If expression branches have different types: '{then_type}' and '{else_type}'")
        return then_type or else_type

    def visit_ref(self, ref: Ref) -> Optional[str]:
        var = self.scope.lookup(ref.name)
        if var is None:
            self.error(f"Undeclared variable '{ref.name}'")
            return None
        return f"&{var.type}"

    def visit_function_call(self, call: FunctionCall) -> Optional[str]:
        func = self.functions.get(call.name)
        if func is None:
            self.error(f"Function '{call.name}' not declared")
            return None

        if len(func.param_types) != len(call.args):
            self.error(f"Function '{call.name}' expects {len(func.param_types)} arguments but got {len(call.args)}")
            return func.return_type

        for i, (expected, arg) in enumerate(zip(func.param_types, call.args)):
            arg_type = self.visit_expr(arg)
            if arg_type is not None and not self._types_compatible(expected, arg_type):
                self.error(f"Function '{call.name}' argument {i+1}: expected '{expected}' but got '{arg_type}'")

        return func.return_type

    def visit_read_expr(self, read_expr: Read) -> Optional[str]:
        if read_expr.read_type == "read_int":
            return "integer"
        elif read_expr.read_type == "read_float":
            return "float"
        elif read_expr.read_type == "read_string":
            return "filum"
        else:
            self.error(f"Unknown read type '{read_expr.read_type}'")
            return None

    def _extract_vec_inner(self, type_str: str) -> str:
        if type_str.startswith("vec<") and ">" in type_str:
            return type_str[4:type_str.index(">")]
        return type_str

    def _is_valid_type(self, type_str: str) -> bool:
        base_types = {"integer", "float", "filum", "boolean"}
        if type_str in base_types:
            return True
        if type_str.startswith("&") and type_str[1:] in base_types:
            return True
        if type_str.startswith("vec<") and type_str.endswith(">"):
            inner = type_str[4:-1]
            return inner in base_types
        if type_str.startswith("vec<") and ">" in type_str:
            inner = type_str[4:type_str.index(">")]
            if inner in base_types:
                return True
        return False

    def _types_compatible(self, target: str, source: str) -> bool:
        if target == source:
            return True
        if target.startswith("&") and source.startswith("vec<"):
            if target[1:] == self._extract_vec_inner(source):
                return True
        if target.startswith("vec<") and source.startswith("vec<"):
            if self._extract_vec_inner(target) == self._extract_vec_inner(source):
                return True
        return False

    def _in_loop(self) -> bool:
        scope = self.scope
        while scope is not None:
            if scope.in_loop:
                return True
            scope = scope.parent
        return False

    def _to_ptr(self, type_str: str) -> str:
        if type_str.startswith("vec<"):
            return "&" + self._extract_vec_inner(type_str)
        return type_str

    def _check_add(self, left: str, right: str) -> Optional[str]:
        if left == right == "integer":
            return "integer"
        elif left == right == "float":
            return "float"
        elif left.startswith("&") and right == "integer":
            return left
        elif left.startswith("vec<") and right == "integer":
            return self._to_ptr(left)
        elif left == right == "filum":
            return "filum"
        self.error(f"Operation 'add' not supported for types '{left}' and '{right}'")
        return None

    def _check_sub(self, left: str, right: str) -> Optional[str]:
        if left == right == "integer":
            return "integer"
        elif left == right == "float":
            return "float"
        elif left.startswith("&") and right == "integer":
            return left
        elif left.startswith("vec<") and right == "integer":
            return self._to_ptr(left)
        elif left == right == "&integer":
            return "integer"
        elif left.startswith("vec<") and right.startswith("vec<"):
            return "integer"
        self.error(f"Operation 'sub' not supported for types '{left}' and '{right}'")
        return None

    def _check_mul(self, left: str, right: str) -> Optional[str]:
        if left == right == "integer":
            return "integer"
        elif left == right == "float":
            return "float"
        self.error(f"Operation 'mul' not supported for types '{left}' and '{right}'")
        return None

    def _check_div(self, left: str, right: str) -> Optional[str]:
        if left == right == "integer":
            return "integer"
        elif left == right == "float":
            return "float"
        self.error(f"Operation 'div' not supported for types '{left}' and '{right}'")
        return None

    def _check_mod(self, left: str, right: str) -> Optional[str]:
        if left == right == "integer":
            return "integer"
        self.error(f"Operation 'mod' not supported for types '{left}' and '{right}'")
        return None

    def _is_ptr_like(self, type_str: str) -> bool:
        return type_str.startswith("&") or type_str.startswith("vec<")

    def _check_lt(self, left: str, right: str) -> Optional[str]:
        if left == right and left not in ("filum", "float"):
            return "integer"
        elif left == right == "float":
            return "integer"
        elif self._is_ptr_like(left) and self._is_ptr_like(right):
            return "integer"
        self.error(f"Operation 'lt' not supported for types '{left}' and '{right}'")
        return None

    def _check_lte(self, left: str, right: str) -> Optional[str]:
        if left == right and left not in ("filum", "float"):
            return "integer"
        elif left == right == "float":
            return "integer"
        elif self._is_ptr_like(left) and self._is_ptr_like(right):
            return "integer"
        self.error(f"Operation 'lte' not supported for types '{left}' and '{right}'")
        return None

    def _check_gt(self, left: str, right: str) -> Optional[str]:
        if left == right and left not in ("filum", "float"):
            return "integer"
        elif left == right == "float":
            return "integer"
        elif self._is_ptr_like(left) and self._is_ptr_like(right):
            return "integer"
        self.error(f"Operation 'gt' not supported for types '{left}' and '{right}'")
        return None

    def _check_gte(self, left: str, right: str) -> Optional[str]:
        if left == right and left not in ("filum", "float"):
            return "integer"
        elif left == right == "float":
            return "integer"
        elif self._is_ptr_like(left) and self._is_ptr_like(right):
            return "integer"
        self.error(f"Operation 'gte' not supported for types '{left}' and '{right}'")
        return None

    def _check_eq(self, left: str, right: str) -> Optional[str]:
        if left == right and left != "filum":
            return "integer"
        self.error(f"Operation 'eq' not supported for types '{left}' and '{right}'")
        return None

    def _check_neq(self, left: str, right: str) -> Optional[str]:
        if left == right and left != "filum":
            return "integer"
        self.error(f"Operation 'neq' not supported for types '{left}' and '{right}'")
        return None

    def _check_and(self, left: str, right: str) -> Optional[str]:
        if left == right == "integer":
            return "integer"
        self.error(f"Operation 'and' not supported for types '{left}' and '{right}'")
        return None

    def _check_or(self, left: str, right: str) -> Optional[str]:
        if left == right == "integer":
            return "integer"
        self.error(f"Operation 'or' not supported for types '{left}' and '{right}'")
        return None


def analyze_program(program: Program) -> Tuple[bool, List[SemanticError], List[SemanticError]]:
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(program)
