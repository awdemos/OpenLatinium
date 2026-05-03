import sys
sys.path.insert(0, ".")

from lat.ir.optimizer import IROptimizer
from lat.ir.nodes import IRProgram, IRFunction, BasicBlock


def test_optimizer_creation():
    opt = IROptimizer()
    assert opt.constants == {}


def test_optimize_empty_program():
    opt = IROptimizer()
    program = IRProgram(globals=[], functions=[])
    result = opt.optimize(program)
    assert result == program


def test_optimize_function_with_empty_blocks():
    opt = IROptimizer()
    func = IRFunction(name="main", params=[], return_type="void", locals=[], blocks=[BasicBlock(label="entry")], entry_block="entry")
    program = IRProgram(globals=[], functions=[func])
    result = opt.optimize(program)
    assert len(result.functions) == 1
    assert len(result.functions[0].blocks) == 1
