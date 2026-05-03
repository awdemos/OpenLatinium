import sys
sys.path.insert(0, ".")

from lat.semantics._statement import IO, Assignment, Declaration


def test_io_creation():
    io = IO()
    assert io is not None


def test_io_has_productions():
    io = IO()
    assert hasattr(io, 'productions')
    assert len(io.productions) > 0


def test_assignment_creation():
    assign = Assignment()
    assert assign is not None


def test_declaration_creation():
    decl = Declaration()
    assert decl is not None
