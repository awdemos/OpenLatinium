import sys
sys.path.insert(0, ".")

from lat.ast.nodes import (
    Param, Function, Program, IntegerLiteral, FloatLiteral,
    StringLiteral, BooleanLiteral, Identifier, Decl, Assignment,
    BinaryOp, UnaryOp, FunctionCall, ArrayIndex, Read, ArrayLiteral, ArrayRange
)


def test_param_creation():
    p = Param(name="x", type="integer")
    assert p.name == "x"
    assert p.type == "integer"


def test_integer_literal():
    lit = IntegerLiteral(value=42)
    assert lit.value == 42


def test_float_literal():
    lit = FloatLiteral(value=3.14)
    assert lit.value == 3.14


def test_string_literal():
    lit = StringLiteral(value="hello")
    assert lit.value == "hello"


def test_boolean_literal():
    lit = BooleanLiteral(value=True)
    assert lit.value is True


def test_identifier():
    ident = Identifier(name="foo")
    assert ident.name == "foo"


def test_program_creation():
    prog = Program(globals=[], functions=[])
    assert prog.globals == []
    assert prog.functions == []


def test_binary_op():
    left = IntegerLiteral(value=1)
    right = IntegerLiteral(value=2)
    op = BinaryOp(left=left, op="+", right=right)
    assert op.op == "+"
    assert op.left.value == 1
    assert op.right.value == 2


def test_unary_op():
    operand = IntegerLiteral(value=5)
    op = UnaryOp(op="-", operand=operand)
    assert op.op == "-"
    assert op.operand.value == 5


def test_decl():
    decl = Decl(name="x", type="integer", value=IntegerLiteral(value=10))
    assert decl.name == "x"
    assert decl.type == "integer"
    assert decl.value.value == 10
    assert decl.is_const is False


def test_assignment():
    target = Identifier(name="x")
    value = IntegerLiteral(value=20)
    assign = Assignment(target=target, value=value)
    assert assign.target.name == "x"
    assert assign.value.value == 20


def test_function_call():
    call = FunctionCall(name="print", args=[IntegerLiteral(value=1)])
    assert call.name == "print"
    assert len(call.args) == 1


def test_array_literal():
    vec = ArrayLiteral(items=[IntegerLiteral(value=1), IntegerLiteral(value=2)])
    assert len(vec.items) == 2


def test_array_range():
    vec = ArrayRange(start=0, end=10)
    assert vec.start == 0
    assert vec.end == 10
