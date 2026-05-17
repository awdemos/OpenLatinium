"""Shared bytecode emission utilities for the OpenLatinum compiler.

This module provides reusable helpers for generating EWVM bytecode,
eliminating duplication between the AST-based generator and the IR-based
from_ir generator.
"""

from typing import Dict, List, Optional


#: Mapping from source operator to VM opcode.
BINARY_OPS: Dict[str, str] = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
    "%": "MOD",
    "<": "INF",
    ">": "SUP",
    "<=": "INFEQ",
    ">=": "SUPEQ",
    "==": "EQUAL",
    "!=": "EQUAL\nNOT",
    "&&": "AND",
    "||": "OR",
    "EQ": "EQUAL",
    "NEQ": "EQUAL\nNOT",
    "LT": "INF",
    "GT": "SUP",
    "LTE": "INFEQ",
    "GTE": "SUPEQ",
    "AND": "AND",
    "OR": "OR",
}

#: Mapping from unary operator to VM opcode sequence.
UNARY_OPS: Dict[str, List[str]] = {
    "-": ["PUSHI -1", "MUL"],
    "!": ["NOT"],
    "++": ["PUSHI 1", "ADD"],
    "--": ["PUSHI 1", "SUB"],
}

#: Read instructions per type.
READ_OPS: Dict[str, str] = {
    "integer": "READI",
    "float": "READF",
    "filum": "READS",
}

#: Write instructions per type.
WRITE_OPS: Dict[str, str] = {
    "integer": "WRITEI",
    "float": "WRITEF",
    "filum": "WRITES",
}


class BytecodeEmitter:
    """Helper for accumulating VM bytecode instructions."""

    def __init__(self) -> None:
        self.output: List[str] = []
        self.label_counter = 0

    def emit(self, line: str) -> None:
        """Append a single instruction or label."""
        self.output.append(line)

    def emit_lines(self, lines: str) -> None:
        """Append multiple lines (e.g. from a helper that returns a block)."""
        for line in lines.strip().splitlines():
            self.emit(line)

    def new_label(self, prefix: str = "L") -> str:
        """Generate a fresh label."""
        self.label_counter += 1
        return f"{prefix}{self.label_counter}"

    def emit_push(self, value_type: str, value) -> None:
        """Emit a push instruction for a constant value."""
        if value_type == "integer":
            self.emit(f"PUSHI {value}")
        elif value_type == "float":
            self.emit(f"PUSHF {value}")
        elif value_type == "filum":
            val = str(value)
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            self.emit(f'PUSHS "{val}"')
        else:
            self.emit("PUSHI 0")

    def emit_load(self, scope: str, pos: int) -> None:
        """Emit a load for a variable in *scope* at *pos*."""
        if scope == "global":
            self.emit("PUSHGP")
        elif scope in ("local", "param"):
            self.emit("PUSHFP")
        else:
            raise ValueError(f"Unknown scope: {scope}")
        self.emit(f"LOAD {pos}")

    def emit_store(self, scope: str, pos: int) -> None:
        """Emit a store for a variable in *scope* at *pos*."""
        if scope == "global":
            self.emit(f"STOREG {pos}")
        elif scope == "local":
            self.emit(f"STOREL {pos}")
        elif scope == "param":
            self.emit("PUSHFP")
            self.emit(f"STORE {pos}")
        else:
            raise ValueError(f"Unknown scope: {scope}")

    def emit_binop(self, op: str) -> None:
        """Emit a binary operator instruction."""
        vm_op = BINARY_OPS.get(op, op.upper())
        if "\n" in vm_op:
            self.emit_lines(vm_op)
        else:
            self.emit(vm_op)

    def emit_unaryop(self, op: str) -> None:
        """Emit a unary operator instruction sequence."""
        for line in UNARY_OPS.get(op, []):
            self.emit(line)

    def emit_read(self, t: str) -> None:
        """Emit a read instruction for type *t*."""
        op = READ_OPS.get(t, "READI")
        self.emit(op)

    def emit_write(self, t: str) -> None:
        """Emit a write instruction for type *t*."""
        op = WRITE_OPS.get(t, "WRITEI")
        self.emit(op)

    def emit_main_entry(self) -> None:
        """Emit the standard program entry sequence."""
        self.emit("start")
        self.emit("PUSHI 0")
        self.emit("PUSHA main")
        self.emit("CALL")
        self.emit("POP 1")
        self.emit("stop")

    def emit_function_prologue(
        self,
        name: str,
        local_count: int,
        param_count: int = 0,
        params_to_locals: bool = False,
    ) -> None:
        """Emit the start of a function definition.

        If *params_to_locals* is ``True``, each parameter is copied from its
        negative frame offset to a positive local slot so that later code can
        treat parameters uniformly as locals.
        """
        self.emit(f"{name}:")
        if local_count:
            self.emit(f"PUSHN {local_count}")
        if params_to_locals:
            for i in range(param_count):
                self.emit("PUSHI 0")
                self.emit("PUSHFP")
                self.emit(f"LOAD {-(param_count - i)}")
                self.emit(f"STOREL {i}")

    def to_string(self) -> str:
        """Return the accumulated bytecode as a single string."""
        return "\n".join(self.output) + "\n"
