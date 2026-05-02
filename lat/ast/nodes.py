from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class Param:
    name: str
    type: str


@dataclass
class Function:
    name: str
    params: List[Param]
    return_type: Optional[str]
    body: List['Stmt']


@dataclass
class Program:
    globals: List['Decl']
    functions: List[Function]


@dataclass
class IntegerLiteral:
    value: int


@dataclass
class FloatLiteral:
    value: float


@dataclass
class StringLiteral:
    value: str


@dataclass
class Identifier:
    name: str


@dataclass
class BinaryOp:
    left: 'Expr'
    op: str
    right: 'Expr'


@dataclass
class UnaryOp:
    op: str
    operand: 'Expr'


@dataclass
class ArrayIndex:
    name: str
    indices: List['Expr']


@dataclass
class ArrayLiteral:
    items: List['Expr']


@dataclass
class ArrayRange:
    start: int
    end: int


@dataclass
class Ref:
    name: str


@dataclass
class FunctionCall:
    name: str
    args: List['Expr']


@dataclass
class Read:
    read_type: str
    expressions: List['Expr']


Expr = Union[
    IntegerLiteral, FloatLiteral, StringLiteral, Identifier,
    BinaryOp, UnaryOp, ArrayIndex, ArrayLiteral, ArrayRange,
    Ref, FunctionCall, Read
]


@dataclass
class Decl:
    name: str
    type: str
    value: Optional[Expr] = None


@dataclass
class Assignment:
    target: Union[Identifier, ArrayIndex]
    value: Expr


@dataclass
class Print:
    expressions: List[Expr]


@dataclass
class If:
    condition: Expr
    then_body: List['Stmt']
    else_body: Optional['Stmt'] = None


@dataclass
class Case:
    value: Expr
    body: List['Stmt']


@dataclass
class Default:
    body: List['Stmt']


@dataclass
class Match:
    expression: Expr
    cases: List[Union[Case, Default]]


@dataclass
class While:
    condition: Expr
    body: List['Stmt']


@dataclass
class DoWhile:
    condition: Expr
    body: List['Stmt']


@dataclass
class For:
    init: List[Optional[Union[Decl, Assignment]]]
    condition: Expr
    update: List[Assignment]
    body: List['Stmt']


@dataclass
class Return:
    value: Optional[Expr] = None


@dataclass
class Break:
    pass


@dataclass
class Continue:
    pass


@dataclass
class Debug:
    pass


Stmt = Union[
    Decl, Assignment, Print, If, Match, While, DoWhile, For,
    Return, Break, Continue, Debug, FunctionCall, Read
]
