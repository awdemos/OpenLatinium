from typing import List, Any
from dataclasses import dataclass, field

from lat.utils.errors import compiler_error, std_message, CompilationError


@dataclass
class TypeCheck:
    stack: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.productions = {
            "not": self._not,
            "neg": self._neg,
            "mul": self._mul,
            "div": self._div,
            "mod": self._mod,
            "add": self._add,
            "sub": self._sub,
            "lt": self._lt,
            "lte": self._lte,
            "gt": self._gt,
            "gte": self._gte,
            "eq": self._eq,
            "neq": self._neq,
            "and": self._and,
            "or": self._or,
        }

    def handle(self, p: Any, production: str) -> str:
        return self.productions[production](p)

    def push(self, type: str) -> None:
        self.stack.append(type)

    def pop(self) -> str:
        if len(self.stack) == 0:
            return "None"
        return self.stack.pop()

    def is_empty(self) -> bool:
        return len(self.stack) == 0

    def _not(self, p: Any) -> str:
        """
        unary : '!' unary
        """
        right_operand = self.stack.pop()
        if right_operand in ("integer", "float"):
            self.stack.append(right_operand)
            return p[2] + std_message(["NOT"])
        else:
            raise CompilationError(f"Operation 'not' not supported for type '{right_operand}'")

    def _neg(self, p: Any) -> str:
        """
        unary : '-' unary
        """
        right_operand = self.stack.pop()
        if right_operand == "integer":
            self.stack.append("integer")
            return p[2] + std_message(["PUSHI -1", "MUL"])
        elif right_operand == "float":
            self.stack.append("float")
            return p[2] + std_message(["PUSHF -1.0", "FMUL"])
        else:
            raise CompilationError(f"Operation 'neg' not supported for type '{right_operand}'")

    def _mul(self, p: Any) -> str:
        """
        factor : factor '*' unary
        """
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        if right_operand == left_operand == "integer":
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["MUL"])
        elif right_operand == left_operand == "float":
            self.stack.append("float")
            return p[1] + p[3] + std_message(["FMUL"])
        else:
            raise CompilationError(f"Operation 'mul' not supported for types '{left_operand}' and '{right_operand}'")

    def _div(self, p: Any) -> str:
        """
        factor : factor '/' unary
        """
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        if right_operand == left_operand == "integer":
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["DIV"])
        elif right_operand == left_operand == "float":
            self.stack.append("float")
            return p[1] + p[3] + std_message(["FDIV"])
        else:
            raise CompilationError(f"Operation 'div' not supported for types '{left_operand}' and '{right_operand}'")

    def _mod(self, p: Any) -> str:
        """
        factor : factor '%' unary
        """
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        if right_operand == left_operand == "integer":
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["MOD"])
        else:
            raise CompilationError(f"Operation 'mod' not supported for types '{left_operand}' and '{right_operand}'")

    def _add(self, p: Any) -> str:
        """
        term : term '+' factor
        """
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        if left_operand.startswith("vec"):
            raise CompilationError("vector type cannot appear in this stage")
        if right_operand == left_operand == "integer":
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["ADD"])
        elif right_operand == left_operand == "float":
            self.stack.append("float")
            return p[1] + p[3] + std_message(["FADD"])
        elif left_operand.startswith("&") and right_operand == "integer":
            self.stack.append(left_operand)
            return p[1] + p[3] + std_message(["PADD"])
        elif right_operand == left_operand == "filum":
            self.stack.append("filum")
            return p[3] + p[1] + std_message(["CONCAT"])
        else:
            raise CompilationError(f"Operation 'add' not supported for types '{left_operand}' and '{right_operand}'")

    def _sub(self, p: Any) -> str:
        """
        term : term '-' factor
        """
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        if left_operand.startswith("vec"):
            raise CompilationError("vector type cannot appear in this stage")
        if (right_operand, left_operand) in [("integer", "integer"), ("&integer", "&integer")]:
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["SUB"])
        elif right_operand == left_operand == "float":
            self.stack.append("float")
            return p[1] + p[3] + std_message(["FSUB"])
        elif left_operand.startswith("&") and right_operand == "integer":
            self.stack.append(left_operand)
            return p[1] + p[3] + std_message(["PUSHI -1", "MUL", "PADD"])
        else:
            raise CompilationError(f"Operation 'sub' not supported for types '{left_operand}' and '{right_operand}'")

    def _lt(self, p: Any) -> str:
        """
        comparison : comparison LT term
        """
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        if left_operand.startswith("vec"):
            raise CompilationError("vector type cannot appear in this stage")
        if right_operand == left_operand and left_operand not in ("filum", "float"):
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["INF"])
        elif right_operand == left_operand == "float":
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["FINF", "FTOI"])
        else:
            raise CompilationError(f"Operation 'lt' not supported for types '{left_operand}' and '{right_operand}'")

    def _gt(self, p: Any) -> str:
        """
        comparison : comparison GT term
        """
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        if left_operand.startswith("vec"):
            raise CompilationError("vector type cannot appear in this stage")
        if right_operand == left_operand and left_operand not in ("filum", "float"):
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["SUP"])
        elif right_operand == left_operand == "float":
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["FSUP", "FTOI"])
        else:
            raise CompilationError(f"Operation 'gt' not supported for types '{left_operand}' and '{right_operand}'")

    def _lte(self, p: Any) -> str:
        """
        comparison : comparison LTE term
        """
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        if left_operand.startswith("vec"):
            raise CompilationError("vector type cannot appear in this stage")
        if right_operand == left_operand and left_operand not in ("filum", "float"):
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["INFEQ"])
        elif right_operand == left_operand == "float":
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["FINFEQ", "FTOI"])
        else:
            raise CompilationError(f"Operation 'lte' not supported for types '{left_operand}' and '{right_operand}'")

    def _gte(self, p: Any) -> str:
        """
        comparison : comparison GTE term
        """
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        if left_operand.startswith("vec"):
            raise CompilationError("vector type cannot appear in this stage")
        if right_operand == left_operand and left_operand not in ("filum", "float"):
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["SUPEQ"])
        elif right_operand == left_operand == "float":
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["FSUPEQ", "FTOI"])
        else:
            raise CompilationError(f"Operation 'gte' not supported for types '{left_operand}' and '{right_operand}'")

    def _eq(self, p: Any) -> str:
        """
        condition : condition EQ comparison
        """
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        if left_operand.startswith("vec"):
            raise CompilationError("vector type cannot appear in this stage")
        if right_operand == left_operand and left_operand != "filum":
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["EQUAL"])
        else:
            raise CompilationError(f"Operation 'eq' not supported for types '{left_operand}' and '{right_operand}'")

    def _neq(self, p: Any) -> str:
        """
        condition : condition NEQ comparison
        """
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        if left_operand.startswith("vec"):
            raise CompilationError("vector type cannot appear in this stage")
        if right_operand == left_operand and left_operand != "filum":
            self.stack.append("integer")
            return p[1] + p[3] + std_message(["EQUAL", "NOT"])
        else:
            raise CompilationError(f"Operation 'neq' not supported for types '{left_operand}' and '{right_operand}'")

    def _and(self, p: Any) -> str:
        """
        subexpression : subexpression AND condition
        """
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        if left_operand.startswith("vec"):
            raise CompilationError("vector type cannot appear in this stage")
        if right_operand == left_operand == "integer":
            self.stack.append("integer")
            count = p.parser.logic_count
            p.parser.logic_count += 1
            return p[1] + std_message(["DUP 1", f"JZ LOGL{count}END", "POP 1"]) + p[3] + std_message([f"LOGL{count}END:"])
        else:
            raise CompilationError(f"Operation 'and' not supported for types '{left_operand}' and '{right_operand}'")

    def _or(self, p: Any) -> str:
        right_operand = self.stack.pop()
        left_operand = self.stack.pop()
        if left_operand.startswith("vec"):
            raise CompilationError("vector type cannot appear in this stage")
        if right_operand == left_operand == "integer":
            self.stack.append("integer")
            count = p.parser.logic_count
            p.parser.logic_count += 1
            return p[1] + std_message(["DUP 1", "NOT", f"JZ LOGL{count}END", "POP 1"]) + p[3] + std_message([f"LOGL{count}END:"])
        else:
            raise CompilationError(f"Operation 'or' not supported for types '{left_operand}' and '{right_operand}'")
