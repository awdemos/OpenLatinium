import sys
sys.path.insert(0, ".")

from lat.codegen.generator import CodeGenerator


def test_generator_creation():
    gen = CodeGenerator()
    assert gen is not None


def test_generator_has_methods():
    gen = CodeGenerator()
    assert hasattr(gen, 'generate')
