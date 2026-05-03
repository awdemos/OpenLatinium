from typing import Dict, Set
from lat.ir.nodes import (
    IRProgram, IRFunction, BasicBlock, Instruction,
    BinOp, UnaryOp, Const, Temp, Var, Operand,
    Load, Store, ArrayLoad, ArrayStore, Call, Return,
    Jump, Branch, Label, Read, Write, Alloc
)


class IROptimizer:
    def __init__(self):
        self.constants: Dict[int, Const] = {}
    
    def optimize(self, program: IRProgram) -> IRProgram:
        for func in program.functions:
            self._optimize_function(func)
        return program
    
    def _optimize_function(self, func: IRFunction):
        for block in func.blocks:
            self._constant_fold_block(block)
        
        for block in func.blocks:
            self._propagate_constants_block(block)
        
        for block in func.blocks:
            self._dead_code_elimination_block(block)
        
        for block in func.blocks:
            self._cse_block(block)
    
    def _constant_fold_block(self, block: BasicBlock):
        new_instructions = []
        
        for instr in block.instructions:
            if isinstance(instr, BinOp):
                folded = self._try_fold_binop(instr)
                if folded:
                    self.constants[instr.result.id] = folded
                    continue
            elif isinstance(instr, UnaryOp):
                folded = self._try_fold_unary(instr)
                if folded:
                    self.constants[instr.result.id] = folded
                    continue
            
            new_instructions.append(instr)
        
        block.instructions = new_instructions
    
    def _try_fold_binop(self, instr: BinOp) -> Const:
        left = self._resolve_const(instr.left)
        right = self._resolve_const(instr.right)
        
        if not left or not right:
            return None
        
        if instr.op == "+" and left.type == "filum":
            return Const(left.value + right.value, "filum")
        
        if left.type == "integer" and right.type == "integer":
            lv = left.value
            rv = right.value
            
            if instr.op == "+":
                return Const(lv + rv, "integer")
            elif instr.op == "-":
                return Const(lv - rv, "integer")
            elif instr.op == "*":
                return Const(lv * rv, "integer")
            elif instr.op == "/":
                if rv == 0:
                    return None
                return Const(lv // rv, "integer")
            elif instr.op == "%":
                if rv == 0:
                    return None
                return Const(lv % rv, "integer")
            elif instr.op == "<":
                return Const(1 if lv < rv else 0, "integer")
            elif instr.op == ">":
                return Const(1 if lv > rv else 0, "integer")
            elif instr.op == "<=":
                return Const(1 if lv <= rv else 0, "integer")
            elif instr.op == ">=":
                return Const(1 if lv >= rv else 0, "integer")
            elif instr.op == "==":
                return Const(1 if lv == rv else 0, "integer")
            elif instr.op == "!=":
                return Const(1 if lv != rv else 0, "integer")
            elif instr.op == "&&":
                return Const(1 if (lv and rv) else 0, "integer")
            elif instr.op == "||":
                return Const(1 if (lv or rv) else 0, "integer")
        
        if left.type == "float" and right.type == "float":
            lv = left.value
            rv = right.value
            
            if instr.op == "+":
                return Const(lv + rv, "float")
            elif instr.op == "-":
                return Const(lv - rv, "float")
            elif instr.op == "*":
                return Const(lv * rv, "float")
            elif instr.op == "/":
                if rv == 0:
                    return None
                return Const(lv / rv, "float")
            elif instr.op == "%":
                if rv == 0:
                    return None
                return Const(lv % rv, "float")
            elif instr.op == "<":
                return Const(1 if lv < rv else 0, "integer")
            elif instr.op == ">":
                return Const(1 if lv > rv else 0, "integer")
            elif instr.op == "<=":
                return Const(1 if lv <= rv else 0, "integer")
            elif instr.op == ">=":
                return Const(1 if lv >= rv else 0, "integer")
            elif instr.op == "==":
                return Const(1 if lv == rv else 0, "integer")
            elif instr.op == "!=":
                return Const(1 if lv != rv else 0, "integer")
        
        return None
    
    def _try_fold_unary(self, instr: UnaryOp) -> Const:
        operand = self._resolve_const(instr.operand)
        
        if not operand:
            return None
        
        if instr.op == "-" and operand.type in ("integer", "float"):
            return Const(-operand.value, operand.type)
        
        if instr.op == "!" and operand.type == "integer":
            return Const(1 if operand.value == 0 else 0, "integer")
        
        return None
    
    def _resolve_const(self, op: Operand) -> Const:
        if isinstance(op, Const):
            return op
        if isinstance(op, Temp) and op.id in self.constants:
            return self.constants[op.id]
        return None
    
    def _propagate_constants_block(self, block: BasicBlock):
        for instr in block.instructions:
            self._substitute_constants(instr)
    
    def _substitute_constants(self, instr: Instruction):
        if isinstance(instr, BinOp):
            instr.left = self._resolve_const(instr.left) or instr.left
            instr.right = self._resolve_const(instr.right) or instr.right
        elif isinstance(instr, UnaryOp):
            instr.operand = self._resolve_const(instr.operand) or instr.operand
        elif isinstance(instr, Store):
            instr.value = self._resolve_const(instr.value) or instr.value
        elif isinstance(instr, ArrayLoad):
            instr.base = self._resolve_const(instr.base) or instr.base
            instr.index = self._resolve_const(instr.index) or instr.index
        elif isinstance(instr, ArrayStore):
            instr.base = self._resolve_const(instr.base) or instr.base
            instr.index = self._resolve_const(instr.index) or instr.index
            instr.value = self._resolve_const(instr.value) or instr.value
        elif isinstance(instr, Call):
            for i, arg in enumerate(instr.args):
                instr.args[i] = self._resolve_const(arg) or arg
        elif isinstance(instr, Return):
            if instr.value:
                instr.value = self._resolve_const(instr.value) or instr.value
        elif isinstance(instr, Branch):
            instr.cond = self._resolve_const(instr.cond) or instr.cond
        elif isinstance(instr, Write):
            instr.value = self._resolve_const(instr.value) or instr.value
        elif isinstance(instr, Alloc):
            instr.size = self._resolve_const(instr.size) or instr.size
    
    def _dead_code_elimination_block(self, block: BasicBlock):
        used_temps: Set[int] = set()
        
        for instr in block.instructions:
            self._collect_used_temps(instr, used_temps)
        
        new_instructions = []
        for instr in block.instructions:
            if self._is_dead_assignment(instr, used_temps):
                continue
            new_instructions.append(instr)
        
        block.instructions = new_instructions
    
    def _collect_used_temps(self, instr: Instruction, used: Set[int]):
        if isinstance(instr, BinOp):
            if isinstance(instr.left, Temp):
                used.add(instr.left.id)
            if isinstance(instr.right, Temp):
                used.add(instr.right.id)
        elif isinstance(instr, UnaryOp):
            if isinstance(instr.operand, Temp):
                used.add(instr.operand.id)
        elif isinstance(instr, Store):
            if isinstance(instr.value, Temp):
                used.add(instr.value.id)
        elif isinstance(instr, ArrayLoad):
            if isinstance(instr.base, Temp):
                used.add(instr.base.id)
            if isinstance(instr.index, Temp):
                used.add(instr.index.id)
        elif isinstance(instr, ArrayStore):
            if isinstance(instr.base, Temp):
                used.add(instr.base.id)
            if isinstance(instr.index, Temp):
                used.add(instr.index.id)
            if isinstance(instr.value, Temp):
                used.add(instr.value.id)
        elif isinstance(instr, Call):
            for arg in instr.args:
                if isinstance(arg, Temp):
                    used.add(arg.id)
        elif isinstance(instr, Return):
            if instr.value and isinstance(instr.value, Temp):
                used.add(instr.value.id)
        elif isinstance(instr, Branch):
            if isinstance(instr.cond, Temp):
                used.add(instr.cond.id)
        elif isinstance(instr, Write):
            if isinstance(instr.value, Temp):
                used.add(instr.value.id)
        elif isinstance(instr, Alloc):
            if isinstance(instr.size, Temp):
                used.add(instr.size.id)
    
    def _is_dead_assignment(self, instr: Instruction, used_temps: Set[int]) -> bool:
        if isinstance(instr, BinOp):
            return instr.result.id not in used_temps
        elif isinstance(instr, UnaryOp):
            return instr.result.id not in used_temps
        elif isinstance(instr, Load):
            return instr.result.id not in used_temps
        elif isinstance(instr, ArrayLoad):
            return instr.result.id not in used_temps
        elif isinstance(instr, Read):
            return instr.result.id not in used_temps
        elif isinstance(instr, Alloc):
            return instr.result.id not in used_temps
        return False
    
    def _cse_block(self, block: BasicBlock):
        expr_map: Dict[tuple, Temp] = {}
        
        new_instructions = []
        for instr in block.instructions:
            if isinstance(instr, BinOp):
                key = (instr.op, self._operand_key(instr.left), self._operand_key(instr.right))
                if key in expr_map:
                    prev = expr_map[key]
                    self.constants[instr.result.id] = self._resolve_const(prev) or prev
                    continue
                else:
                    expr_map[key] = instr.result
            new_instructions.append(instr)
        
        block.instructions = new_instructions
    
    def _operand_key(self, op: Operand) -> tuple:
        if isinstance(op, Const):
            return ("const", op.value, op.type)
        elif isinstance(op, Var):
            return ("var", op.name, op.type)
        elif isinstance(op, Temp):
            return ("temp", op.id, op.type)
        return ("unknown",)
