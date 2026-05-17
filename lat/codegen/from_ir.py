import re
from typing import List, Optional, Dict

from lat.ir.nodes import (
    Alloc, ArrayLoad, ArrayStore, BasicBlock, BinOp, Branch, Call,
    Const, IRFunction, IRProgram, Jump, Label, Load, Push, Read, Return,
    Store, Temp, UnaryOp, Var, Write
)
from lat.codegen.emitters import BytecodeEmitter
from lat.utils.errors import compiler_error


class IRCodeGenerator:
    def __init__(self):
        self.emitter = BytecodeEmitter()
        self.global_count = 0
        self.globals: Dict[str, int] = {}
        self.current_function: Optional[str] = None
        self.frame_count = 0
        self.locals: Dict[str, int] = {}
        self.params: Dict[str, int] = {}
        self.functions: Dict[str, IRFunction] = {}

    def generate(self, program: IRProgram) -> str:
        self.emitter = BytecodeEmitter()
        self.globals = {}
        self.global_count = 0

        for g in program.globals:
            self.globals[g.name] = self.global_count
            self.global_count += 1
            self.emitter.emit("PUSHN 1")
            # Initialize global arrays with heap allocation
            if g.type.startswith("vec<"):
                m = re.search(r'\[(\d+)\]', g.type)
                size = int(m.group(1)) if m else 1
                self.emitter.emit(f"PUSHI {size}")
                self.emitter.emit("ALLOCN")
                self.emitter.emit(f"STOREG {self.globals[g.name]}")

        self.emitter.emit_main_entry()

        for func in program.functions:
            self._gen_function(func)

        return self.emitter.to_string()

    def _gen_function(self, func: IRFunction):
        self.current_function = func.name
        self.functions[func.name] = func
        self.frame_count = 0
        self.locals = {}
        self.params = {}

        for i, param in enumerate(func.params):
            self.params[param.name] = -(len(func.params) - i)

        for local in func.locals:
            self.locals[local.name] = self.frame_count
            self.frame_count += 1

        label = func.name.replace('_', '')
        self.emitter.emit_function_prologue(
            label,
            self.frame_count,
            len(func.params),
            params_to_locals=False,
        )

        for block in func.blocks:
            self._gen_block(block)

    def _gen_block(self, block: BasicBlock):
        self.emitter.emit(f"{block.label}:")
        for instr in block.instructions:
            self._gen_instruction(instr)

    def _gen_instruction(self, instr):
        if isinstance(instr, Const):
            self._gen_const(instr)
        elif isinstance(instr, Load):
            self._gen_load(instr)
        elif isinstance(instr, Store):
            self._gen_store(instr)
        elif isinstance(instr, BinOp):
            self._gen_binop(instr)
        elif isinstance(instr, UnaryOp):
            self._gen_unaryop(instr)
        elif isinstance(instr, ArrayLoad):
            self._gen_arrayload(instr)
        elif isinstance(instr, ArrayStore):
            self._gen_arraystore(instr)
        elif isinstance(instr, Call):
            self._gen_call(instr)
        elif isinstance(instr, Return):
            self._gen_return(instr)
        elif isinstance(instr, Jump):
            self.emitter.emit(f"JUMP {instr.label}")
        elif isinstance(instr, Branch):
            self._gen_branch(instr)
        elif isinstance(instr, Label):
            self.emitter.emit(f"{instr.name}:")
        elif isinstance(instr, Read):
            self._gen_read(instr)
        elif isinstance(instr, Write):
            self._gen_write(instr)
        elif isinstance(instr, Alloc):
            self._gen_alloc(instr)
        elif isinstance(instr, Push):
            self._gen_push(instr)

    def _gen_const(self, instr: Const):
        self.emitter.emit_push(instr.type, instr.value)

    def _gen_load(self, instr: Load):
        if instr.scope == "global":
            pos = self.globals.get(instr.name, 0)
        elif instr.scope == "local":
            pos = self.locals.get(instr.name, 0)
        elif instr.scope == "param":
            pos = self.params.get(instr.name, 0)
        else:
            pos = 0
        self.emitter.emit_load(instr.scope, pos)

    def _gen_store(self, instr: Store):
        self._gen_operand(instr.value)
        if instr.scope == "global":
            pos = self.globals.get(instr.name, 0)
        elif instr.scope == "local":
            pos = self.locals.get(instr.name, 0)
        elif instr.scope == "param":
            pos = self.params.get(instr.name, 0)
        else:
            pos = 0
        self.emitter.emit_store(instr.scope, pos)

    def _gen_binop(self, instr: BinOp):
        def is_ptr_type(t):
            return isinstance(t, str) and (t.startswith('vec<') or t.startswith('&'))
        
        left_is_ptr = isinstance(instr.left, (Var, Temp)) and is_ptr_type(getattr(instr.left, 'type', ''))
        right_is_ptr = isinstance(instr.right, (Var, Temp)) and is_ptr_type(getattr(instr.right, 'type', ''))
        
        if instr.op == '+' and left_is_ptr and not right_is_ptr:
            self._gen_operand(instr.left)
            self._gen_operand(instr.right)
            self.emitter.emit("PADD")
        elif instr.op == '-' and left_is_ptr and not right_is_ptr:
            self._gen_operand(instr.left)
            self._gen_operand(instr.right)
            self.emitter.emit("PUSHI -1")
            self.emitter.emit("MUL")
            self.emitter.emit("PADD")
        elif instr.op == '+' and hasattr(instr.result, 'type') and instr.result.type == 'filum':
            self._gen_operand(instr.left)
            self._gen_operand(instr.right)
            if isinstance(instr.left, Const) and isinstance(instr.right, Temp):
                self.emitter.emit("SWAP")
            self.emitter.emit("CONCAT")
        elif instr.op == '-' and hasattr(instr.result, 'type') and instr.result.type == 'filum':
            self._gen_operand(instr.left)
            self._gen_operand(instr.right)
            if isinstance(instr.left, Const) and isinstance(instr.right, Temp):
                self.emitter.emit("SWAP")
            self.emitter.emit("SSUB")
        elif instr.op == '*' and hasattr(instr.result, 'type') and instr.result.type == 'filum':
            self._gen_operand(instr.left)
            self._gen_operand(instr.right)
            if isinstance(instr.left, Const) and isinstance(instr.right, Temp):
                self.emitter.emit("SWAP")
            self.emitter.emit("SMUL")
        elif instr.op == '==' and hasattr(instr.result, 'type') and instr.result.type == 'filum':
            self._gen_operand(instr.left)
            self._gen_operand(instr.right)
            if isinstance(instr.left, Const) and isinstance(instr.right, Temp):
                self.emitter.emit("SWAP")
            self.emitter.emit("SEQ")
        else:
            self._gen_operand(instr.left)
            self._gen_operand(instr.right)
            if isinstance(instr.right, Temp) and not isinstance(instr.left, Temp):
                self.emitter.emit("SWAP")
            self.emitter.emit_binop(instr.op)

    def _gen_unaryop(self, instr: UnaryOp):
        self._gen_operand(instr.operand)
        self.emitter.emit_unaryop(instr.op)

    def _gen_arrayload(self, instr: ArrayLoad):
        self._gen_operand(instr.base)
        if isinstance(instr.index, Temp):
            self.emitter.emit("SWAP")
        self._gen_operand(instr.index)
        self.emitter.emit("PADD")
        self.emitter.emit("LOAD 0")

    def _gen_arraystore(self, instr: ArrayStore):
        self._gen_operand(instr.base)
        if isinstance(instr.index, Temp):
            self.emitter.emit("SWAP")
        self._gen_operand(instr.index)
        self.emitter.emit("PADD")
        if isinstance(instr.value, Temp):
            self.emitter.emit("SWAP")
        self._gen_operand(instr.value)
        self.emitter.emit("STORE 0")

    def _gen_call(self, instr: Call):
        func = self.functions.get(instr.name)
        if func and func.return_type:
            self.emitter.emit("PUSHI -69")
        for arg in instr.args:
            self._gen_operand(arg)
        label = instr.name.replace('_', '')
        self.emitter.emit(f"PUSHA {label}")
        self.emitter.emit("CALL")
        if func and func.params:
            self.emitter.emit(f"POP {len(func.params)}")

    def _gen_return(self, instr: Return):
        if instr.value is not None:
            self._gen_operand(instr.value)
            func = self.functions.get(self.current_function)
            if func and func.params:
                self.emitter.emit(f"STOREL -{len(func.params) + 1}")
            else:
                self.emitter.emit("STOREL -1")
        self.emitter.emit("RETURN")

    def _gen_branch(self, instr: Branch):
        self._gen_operand(instr.cond)
        self.emitter.emit(f"JZ {instr.false_label}")
        self.emitter.emit(f"JUMP {instr.true_label}")

    def _gen_read(self, instr: Read):
        self.emitter.emit_read(instr.read_type)

    def _gen_write(self, instr: Write):
        self._gen_operand(instr.value)
        op_type = getattr(instr.value, 'type', 'integer')
        self.emitter.emit_write(op_type)

    def _gen_alloc(self, instr: Alloc):
        self._gen_operand(instr.size)
        self.emitter.emit("ALLOCN")

    def _gen_push(self, instr: Push):
        self._gen_operand(instr.value)

    def _gen_operand(self, operand):
        if isinstance(operand, Const):
            self._gen_const(operand)
        elif isinstance(operand, Var):
            scope = self._resolve_scope(operand.name)
            t = Temp(0, operand.type)
            self._gen_load(Load(operand.name, scope, operand.type, t))
        elif isinstance(operand, Temp):
            pass

    def _resolve_scope(self, name: str) -> str:
        if name in self.params:
            return "param"
        if name in self.locals:
            return "local"
        if name in self.globals:
            return "global"
        return "local"
