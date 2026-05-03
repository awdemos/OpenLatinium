import sys
sys.path.insert(0, ".")

from lat.codegen.from_ir import IRCodeGenerator


def test_from_ir_generator_creation():
    gen = IRCodeGenerator()
    assert gen is not None


def test_from_ir_has_methods():
    gen = IRCodeGenerator()
    assert hasattr(gen, 'generate')
