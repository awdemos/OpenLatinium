import sys
sys.path.insert(0, ".")

from lat.ir.generator import IRGenerator


def test_ir_generator_creation():
    gen = IRGenerator()
    assert gen is not None


def test_ir_generator_has_methods():
    gen = IRGenerator()
    assert hasattr(gen, 'generate')
