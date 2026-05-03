from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple


@dataclass
class Value:
    type: str
    val: Any


class VMError(Exception):
    pass


class EWVMPyInterpreter:
    def __init__(self):
        self.stack: List[Value] = []
        self.sp = 0
        self.fp = 0
        self.gp = 0
        self.pc = 0
        self.call_stack: List[Tuple[int, int]] = []
        self.heap: Dict[int, str] = {}
        self.heap_next = 1
        self.labels: Dict[str, int] = {}
        self.code: List[str] = []
        self.running = False
        self.output: List[str] = []
        self.input_lines: List[str] = []
        self.input_idx = 0

    def load(self, source: str):
        self.code = []
        for line in source.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            self.code.append(line)
        self._resolve_labels()

    def _resolve_labels(self):
        self.labels = {}
        for i, line in enumerate(self.code):
            if line.endswith(':'):
                label = line[:-1]
                self.labels[label] = i

    def run(self, input_data: str = '', max_steps: int = 100000) -> str:
        self.input_lines = input_data.split('\n') if input_data else []
        self.input_idx = 0
        self.output = []
        self.sp = 0
        self.fp = 0
        self.gp = 0
        self.pc = 0
        self.call_stack = []
        self.running = True
        steps = 0
        while self.running and self.pc < len(self.code):
            if steps >= max_steps:
                raise VMError(f"Step limit exceeded ({max_steps})")
            steps += 1
            line = self.code[self.pc]
            self.pc += 1
            self._step(line)
        return ''.join(self.output)

    def _step(self, line: str):
        if line.endswith(':'):
            return
        parts = line.split(None, 1)
        op = parts[0].upper()
        arg = parts[1] if len(parts) > 1 else ''
        method = getattr(self, f'_op_{op}', None)
        if method is None:
            raise VMError(f"Unknown instruction: {op}")
        method(arg)

    def _parse_arg(self, arg: str) -> Any:
        arg = arg.strip()
        if not arg:
            return 0
        if arg.startswith('"') and arg.endswith('"'):
            return arg[1:-1].encode('utf-8').decode('unicode_escape')
        if arg.startswith("'") and arg.endswith("'"):
            return arg[1:-1]
        if arg.lower() in ('true', 'verum'):
            return 1
        if arg.lower() in ('false', 'falsum'):
            return 0
        if arg in self.labels:
            return self.labels[arg]
        try:
            return int(arg)
        except ValueError:
            try:
                return float(arg)
            except ValueError:
                return arg

    def _push(self, v: Value):
        if self.sp < len(self.stack):
            self.stack[self.sp] = v
        else:
            self.stack.append(v)
        self.sp += 1

    def _pop(self) -> Value:
        if self.sp == self.fp:
            raise VMError("Stack underflow (fp == sp)")
        self.sp -= 1
        v = self.stack[self.sp]
        return Value(v.type, v.val)

    def _get(self, idx: int) -> Value:
        idx = int(idx)
        if 0 <= idx < len(self.stack):
            v = self.stack[idx]
            return Value(v.type, v.val)
        raise VMError(f"Stack access out of bounds: {idx}")

    def _set(self, idx: int, v: Value):
        idx = int(idx)
        if idx < 0:
            raise VMError(f"Stack access out of bounds: {idx}")
        while len(self.stack) <= idx:
            self.stack.append(Value('int', 0))
        self.stack[idx] = v

    def _read_input(self) -> str:
        if self.input_idx < len(self.input_lines):
            val = self.input_lines[self.input_idx]
            self.input_idx += 1
            return val
        return '0'

    def _op_START(self, _):
        pass

    def _op_STOP(self, _):
        self.running = False

    def _op_NOP(self, _):
        pass

    def _op_PUSHI(self, arg):
        self._push(Value('int', self._parse_arg(arg)))

    def _op_PUSHF(self, arg):
        self._push(Value('float', self._parse_arg(arg)))

    def _op_PUSHS(self, arg):
        s = arg.strip()
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]
        s = s.encode('utf-8').decode('unicode_escape')
        self._push(Value('str', s))

    def _op_PUSHN(self, arg):
        n = int(self._parse_arg(arg))
        for _ in range(n):
            self._push(Value('int', 0))

    def _op_PUSHG(self, arg):
        idx = self.gp + int(self._parse_arg(arg))
        self._push(self._get(idx))

    def _op_PUSHL(self, arg):
        idx = self.fp + int(self._parse_arg(arg))
        self._push(self._get(idx))

    def _op_PUSHFP(self, _):
        self._push(Value('op', self.fp))

    def _op_PUSHGP(self, _):
        self._push(Value('op', self.gp))

    def _op_PUSHSP(self, _):
        self._push(Value('op', self.sp))

    def _op_LOAD(self, arg):
        ptr = self._pop()
        idx = int(self._parse_arg(arg))
        if ptr.type == 'heap':
            addr = ptr.val + idx
            val = self.heap.get(addr, '0')
            try:
                self._push(Value('int', int(val)))
            except ValueError:
                try:
                    self._push(Value('float', float(val)))
                except ValueError:
                    self._push(Value('str', val))
        elif ptr.type in ('op', 'int', 'float'):
            self._push(self._get(ptr.val + idx))
        else:
            raise VMError(f"Invalid type for LOAD: {ptr.type}")

    def _op_LOADN(self, _):
        idx = int(self._pop().val)
        ptr = self._pop()
        if ptr.type == 'heap':
            addr = ptr.val + idx
            val = self.heap.get(addr, '0')
            try:
                self._push(Value('int', int(val)))
            except ValueError:
                try:
                    self._push(Value('float', float(val)))
                except ValueError:
                    self._push(Value('str', val))
        elif ptr.type in ('op', 'int', 'float'):
            self._push(self._get(ptr.val + idx))
        else:
            raise VMError(f"Invalid type for LOADN: {ptr.type}")

    def _op_DUP(self, arg):
        n = int(self._parse_arg(arg))
        base = self.sp - n
        for i in range(n):
            v = self._get(base + i)
            self._push(Value(v.type, v.val))

    def _op_DUPN(self, arg):
        n = int(self._parse_arg(arg))
        base = self.sp - n
        for i in range(n):
            v = self._get(base + i)
            self._push(Value(v.type, v.val))

    def _op_POP(self, arg):
        n = int(self._parse_arg(arg))
        for _ in range(n):
            self._pop()

    def _op_POPN(self, _):
        n = int(self._pop().val)
        for _ in range(n):
            self._pop()

    def _op_STORE(self, arg):
        val = self._pop()
        ptr = self._pop()
        idx = int(self._parse_arg(arg))
        if ptr.type == 'heap':
            self.heap[ptr.val + idx] = str(val.val)
        elif ptr.type in ('op', 'int', 'float'):
            self._set(ptr.val + idx, val)
        else:
            raise VMError(f"Invalid type for STORE: {ptr.type}")

    def _op_STOREN(self, _):
        val = self._pop()
        idx = int(self._pop().val)
        ptr = self._pop()
        if ptr.type == 'heap':
            self.heap[ptr.val + idx] = str(val.val)
        elif ptr.type in ('op', 'int', 'float'):
            self._set(ptr.val + idx, val)
        else:
            raise VMError(f"Invalid type for STOREN: {ptr.type}")

    def _op_STOREL(self, arg):
        val = self._pop()
        idx = self.fp + int(self._parse_arg(arg))
        self._set(idx, val)

    def _op_STOREG(self, arg):
        val = self._pop()
        idx = self.gp + int(self._parse_arg(arg))
        self._set(idx, val)

    def _op_ALLOC(self, arg):
        n = int(self._parse_arg(arg))
        addr = self.heap_next
        self.heap_next += n
        self._push(Value('heap', addr))

    def _op_ALLOCN(self, _):
        n = int(self._pop().val)
        self._op_ALLOC(str(n))

    def _op_FREE(self, _):
        addr = self._pop().val
        if addr in self.heap:
            del self.heap[addr]

    def _op_PADD(self, _):
        offset = self._pop().val
        ptr = self._pop()
        if ptr.type == 'heap':
            self._push(Value('heap', ptr.val + offset))
        elif ptr.type == 'op':
            self._push(Value('op', ptr.val + offset))
        elif ptr.type == 'code':
            self._push(Value('code', ptr.val + offset))
        elif ptr.type == 'int':
            self._push(Value('int', ptr.val + offset))
        elif ptr.type == 'float':
            self._push(Value('float', ptr.val + offset))
        else:
            raise VMError(f"Invalid type for PADD: {ptr.type}")

    def _op_ADD(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', a + b))

    def _op_SUB(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', a - b))

    def _op_MUL(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', a * b))

    def _op_DIV(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', a // b))

    def _op_MOD(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', a % b))

    def _op_FADD(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('float', float(a) + float(b)))

    def _op_FSUB(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('float', float(a) - float(b)))

    def _op_FMUL(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('float', float(a) * float(b)))

    def _op_FDIV(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('float', float(a) / float(b)))

    def _op_INF(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', 1 if a < b else 0))

    def _op_SUP(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', 1 if a > b else 0))

    def _op_INFEQ(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', 1 if a <= b else 0))

    def _op_SUPEQ(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', 1 if a >= b else 0))

    def _op_FINF(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', 1 if float(a) < float(b) else 0))

    def _op_FSUP(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', 1 if float(a) > float(b) else 0))

    def _op_FINFEQ(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', 1 if float(a) <= float(b) else 0))

    def _op_FSUPEQ(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', 1 if float(a) >= float(b) else 0))

    def _op_EQUAL(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', 1 if a == b else 0))

    def _op_NOT(self, _):
        a = self._pop().val
        self._push(Value('int', 1 if not a else 0))

    def _op_AND(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', 1 if a and b else 0))

    def _op_OR(self, _):
        b = self._pop().val
        a = self._pop().val
        self._push(Value('int', 1 if a or b else 0))

    def _op_JUMP(self, arg):
        self.pc = int(self._parse_arg(arg))

    def _op_JZ(self, arg):
        addr = int(self._parse_arg(arg))
        cond = self._pop().val
        if not cond:
            self.pc = addr

    def _op_PUSHA(self, arg):
        label = arg.strip()
        if label in self.labels:
            self._push(Value('code', self.labels[label]))
        else:
            raise VMError(f"Unknown label: {label}")

    def _op_CALL(self, _):
        addr = self._pop().val
        self.call_stack.append((self.pc, self.fp))
        self.fp = self.sp
        self.pc = addr

    def _op_RETURN(self, _):
        if not self.call_stack:
            self.running = False
            return
        pc, fp = self.call_stack.pop()
        n_locals = self.sp - self.fp
        for _ in range(n_locals):
            self._pop()
        self.fp = fp
        self.pc = pc

    def _op_WRITEI(self, _):
        val = self._pop().val
        self.output.append(str(int(val)))

    def _op_WRITEF(self, _):
        val = self._pop().val
        self.output.append(f"{float(val):.6f}")

    def _op_WRITES(self, _):
        val = self._pop().val
        self.output.append(str(val))

    def _op_READ(self, arg):
        val = self._read_input()
        read_type = arg.strip().lower()
        if read_type == 'i':
            try:
                self._push(Value('int', int(val)))
            except ValueError:
                self._push(Value('int', 0))
        elif read_type == 'f':
            try:
                self._push(Value('float', float(val)))
            except ValueError:
                self._push(Value('float', 0.0))
        elif read_type == 's':
            self._push(Value('str', val))
        else:
            try:
                self._push(Value('int', int(val)))
            except ValueError:
                try:
                    self._push(Value('float', float(val)))
                except ValueError:
                    self._push(Value('str', val))

    def _op_READF(self, _):
        self._op_READ('f')

    def _op_READS(self, _):
        self._op_READ('s')

    def _op_ATOI(self, _):
        addr = self._pop().val
        if addr in self.heap:
            try:
                self._push(Value('int', int(self.heap[addr])))
            except ValueError:
                self._push(Value('int', 0))
        else:
            self._push(Value('int', 0))

    def _op_ATOF(self, _):
        addr = self._pop().val
        if addr in self.heap:
            try:
                self._push(Value('float', float(self.heap[addr])))
            except ValueError:
                self._push(Value('float', 0.0))
        else:
            self._push(Value('float', 0.0))

    def _op_ITOF(self, _):
        val = self._pop().val
        self._push(Value('float', float(val)))

    def _op_FTOI(self, _):
        val = self._pop().val
        self._push(Value('int', int(val)))

    def _op_STRI(self, _):
        val = self._pop().val
        self._push(Value('str', str(int(val))))

    def _op_STRF(self, _):
        val = self._pop().val
        self._push(Value('str', f"{float(val):.6f}"))

    def _op_CONCAT(self, _):
        b = str(self._pop().val)
        a = str(self._pop().val)
        self._push(Value('str', a + b))

    def _op_SWAP(self, _):
        a = self._pop()
        b = self._pop()
        self._push(a)
        self._push(b)

    def _op_CHECK(self, _):
        pass

    def _op_ERR(self, arg):
        s = arg.strip()
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]
        s = s.encode('utf-8').decode('unicode_escape')
        self.output.append(s)


def run_bytecode(source: str, input_data: str = '', max_steps: int = 100000) -> str:
    vm = EWVMPyInterpreter()
    vm.load(source)
    return vm.run(input_data, max_steps)


def _main() -> int:
    import sys
    if len(sys.argv) < 2:
        print('Usage: python -m lat.vm_interpreter <file.vms> [input]')
        return 1
    with open(sys.argv[1], 'r') as f:
        source = f.read()
    input_data = sys.argv[2] if len(sys.argv) > 2 else ''
    result = run_bytecode(source, input_data)
    print(result, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
