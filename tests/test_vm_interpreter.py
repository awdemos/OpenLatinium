import sys
sys.path.insert(0, ".")

from lat.vm_interpreter import EWVMPyInterpreter


def test_interpreter_creation():
    interp = EWVMPyInterpreter()
    assert interp is not None
    assert interp.stack == []
    assert interp.output == []


def test_interpreter_load_empty():
    interp = EWVMPyInterpreter()
    interp.load("")
    assert interp.code == []


def test_interpreter_has_methods():
    interp = EWVMPyInterpreter()
    assert hasattr(interp, 'load')
    assert hasattr(interp, 'run')
