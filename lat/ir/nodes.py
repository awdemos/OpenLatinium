from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class Const:
    value: Union[int, float, str]
    type: str


@dataclass
class Var:
    name: str
    type: str


@dataclass
class Temp:
    id: int
    type: str


Operand = Union[Const, Var, Temp]


@dataclass
class BinOp:
    op: str
    left: Operand
    right: Operand
    result: Temp


@dataclass
class UnaryOp:
    op: str
    operand: Operand
    result: Temp


@dataclass
class Load:
    name: str
    scope: str
    type: str
    result: Temp


@dataclass
class Store:
    name: str
    scope: str
    value: Operand


@dataclass
class ArrayLoad:
    base: Operand
    index: Operand
    type: str
    result: Temp


@dataclass
class ArrayStore:
    base: Operand
    index: Operand
    value: Operand


@dataclass
class Call:
    name: str
    args: List[Operand]
    result: Optional[Temp]


@dataclass
class Return:
    value: Optional[Operand]


@dataclass
class Jump:
    label: str


@dataclass
class Branch:
    cond: Operand
    true_label: str
    false_label: str


@dataclass
class Label:
    name: str


@dataclass
class Read:
    read_type: str
    result: Temp


@dataclass
class Write:
    value: Operand


@dataclass
class Alloc:
    size: Operand
    type: str
    result: Temp


Instruction = Union[
    BinOp, UnaryOp, Load, Store, ArrayLoad, ArrayStore,
    Call, Return, Jump, Branch, Label, Read, Write, Alloc
]


@dataclass
class BasicBlock:
    label: str
    instructions: List[Instruction] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)


@dataclass
class IRFunction:
    name: str
    params: List[Var]
    return_type: Optional[str]
    locals: List[Var]
    blocks: List[BasicBlock]
    entry_block: str


@dataclass
class IRProgram:
    globals: List[Var]
    functions: List[IRFunction]
