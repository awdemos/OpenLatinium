import sys
sys.path.insert(0, ".")

from lat.semantics._type_check import TypeCheck


def test_type_check_creation():
    tc = TypeCheck()
    assert tc.stack == []
    assert tc.is_empty()


def test_push_pop():
    tc = TypeCheck()
    tc.push("integer")
    assert not tc.is_empty()
    assert tc.pop() == "integer"
    assert tc.is_empty()


def test_pop_empty():
    tc = TypeCheck()
    assert tc.pop() == "None"


def test_multiple_push_pop():
    tc = TypeCheck()
    tc.push("integer")
    tc.push("float")
    tc.push("filum")
    assert tc.pop() == "filum"
    assert tc.pop() == "float"
    assert tc.pop() == "integer"
    assert tc.is_empty()


def test_handle_exists():
    tc = TypeCheck()
    assert "not" in tc.productions
    assert "neg" in tc.productions
    assert "mul" in tc.productions
    assert "div" in tc.productions
    assert "mod" in tc.productions
    assert "add" in tc.productions
    assert "sub" in tc.productions
    assert "lt" in tc.productions
    assert "lte" in tc.productions
    assert "gt" in tc.productions
    assert "gte" in tc.productions
    assert "eq" in tc.productions
    assert "neq" in tc.productions
    assert "and" in tc.productions
    assert "or" in tc.productions
