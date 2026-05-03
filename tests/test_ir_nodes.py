import sys
sys.path.insert(0, ".")

from lat.ir.nodes import (
    Const, Var, Temp, BinOp, UnaryOp, Load, Store, Label,
    Jump, Branch, Return, Call, BasicBlock, IRFunction, IRProgram
)


def test_const_creation():
    c = Const(value=42, type="integer")
    assert c.value == 42
    assert c.type == "integer"


def test_var_creation():
    v = Var(name="x", type="integer")
    assert v.name == "x"
    assert v.type == "integer"


def test_temp_creation():
    t = Temp(id=1, type="float")
    assert t.id == 1
    assert t.type == "float"


def test_bin_op():
    left = Const(value=1, type="integer")
    right = Const(value=2, type="integer")
    result = Temp(id=0, type="integer")
    op = BinOp(op="+", left=left, right=right, result=result)
    assert op.op == "+"
    assert op.result.id == 0


def test_unary_op():
    operand = Const(value=5, type="integer")
    result = Temp(id=1, type="integer")
    op = UnaryOp(op="-", operand=operand, result=result)
    assert op.op == "-"
    assert op.operand.value == 5


def test_load():
    load = Load(name="x", scope="local", type="integer", result=Temp(id=2, type="integer"))
    assert load.name == "x"
    assert load.scope == "local"


def test_store():
    store = Store(name="x", scope="global", value=Const(value=10, type="integer"))
    assert store.name == "x"
    assert store.scope == "global"
    assert store.value.value == 10


def test_label():
    label = Label(name="L1")
    assert label.name == "L1"


def test_jump():
    jump = Jump(label="L1")
    assert jump.label == "L1"


def test_branch():
    branch = Branch(cond=Const(value=True, type="boolean"), true_label="L1", false_label="L2")
    assert branch.true_label == "L1"
    assert branch.false_label == "L2"


def test_return_stmt():
    ret = Return(value=Const(value=42, type="integer"))
    assert ret.value.value == 42


def test_call():
    call = Call(name="print", args=[Const(value=1, type="integer")], result=Temp(id=3, type="void"))
    assert call.name == "print"
    assert len(call.args) == 1


def test_basic_block():
    block = BasicBlock(label="entry")
    assert block.label == "entry"
    assert block.instructions == []
    assert block.successors == []


def test_ir_function():
    func = IRFunction(name="main", params=[], return_type="integer", locals=[], blocks=[], entry_block="entry")
    assert func.name == "main"
    assert func.return_type == "integer"
    assert func.blocks == []
    assert func.entry_block == "entry"


def test_ir_program():
    program = IRProgram(globals=[], functions=[])
    assert program.globals == []
    assert program.functions == []
