import sys
sys.path.insert(0, ".")

from lat.semantic.analyzer import SemanticError, VarInfo, Scope


def test_semantic_error_creation():
    err = SemanticError(message="test error", line=1, column=5)
    assert err.message == "test error"
    assert err.line == 1
    assert err.column == 5
    assert err.notes == []


def test_var_info_creation():
    info = VarInfo(name="x", type="integer", is_global=False)
    assert info.name == "x"
    assert info.type == "integer"
    assert info.is_global is False
    assert info.is_initialized is True
    assert info.array_shape is None


def test_scope_creation():
    scope = Scope(name="global", level=0)
    assert scope.name == "global"
    assert scope.level == 0
    assert scope.parent is None
    assert scope.in_function is False
    assert scope.in_loop is False
    assert scope.variables == {}


def test_scope_define():
    scope = Scope(name="global", level=0)
    scope.define("x", "integer")
    assert "x" in scope.variables
    assert scope.variables["x"].type == "integer"


def test_scope_lookup_local():
    scope = Scope(name="global", level=0)
    scope.define("x", "integer")
    result = scope.lookup("x")
    assert result is not None
    assert result.name == "x"


def test_scope_lookup_missing():
    scope = Scope(name="global", level=0)
    result = scope.lookup("y")
    assert result is None


def test_scope_lookup_parent():
    parent = Scope(name="global", level=0)
    parent.define("x", "integer")
    child = Scope(name="local", level=1, parent=parent)
    result = child.lookup("x")
    assert result is not None
    assert result.name == "x"


def test_scope_is_defined_locally():
    scope = Scope(name="global", level=0)
    scope.define("x", "integer")
    assert scope.is_defined_locally("x") is True
    assert scope.is_defined_locally("y") is False
