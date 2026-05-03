import sys
sys.path.insert(0, ".")

from lat.semantics._scopes import MetaData, Scope


def test_metadata_creation():
    meta = MetaData(type="integer", stack_position=(0, 0))
    assert meta.type == "integer"
    assert meta.stack_position == (0, 0)
    assert meta.array_shape is None
    assert meta.p_init is True


def test_metadata_size_single_cell():
    meta = MetaData(type="integer", stack_position=(0, 0))
    assert meta.size_in_cells == 1


def test_metadata_size_multiple_cells():
    meta = MetaData(type="vec<integer>", stack_position=(0, 4))
    assert meta.size_in_cells == 5


def test_metadata_with_array_shape():
    meta = MetaData(type="vec<integer>", stack_position=(0, 9), array_shape=[2, 5])
    assert meta.array_shape == [2, 5]


def test_scope_creation():
    scope = Scope(name="global", level=0)
    assert scope.name == "global"
    assert scope.level == 0
    assert scope.parent is None
    assert scope.in_function is False
    assert scope.Table == {}


def test_scope_add_variable():
    scope = Scope(name="global", level=0)
    scope.add("x", "integer", (0, 0))
    assert "x" in scope.Table
    assert scope.Table["x"].type == "integer"


def test_scope_get_local():
    scope = Scope(name="global", level=0)
    scope.add("x", "integer", (0, 0))
    meta, in_func, scope_name = scope.get("x")
    assert meta is not None
    assert meta.type == "integer"
    assert in_func is False


def test_scope_get_missing():
    scope = Scope(name="global", level=0)
    meta, in_func, scope_name = scope.get("y")
    assert meta is None


def test_scope_get_from_parent():
    parent = Scope(name="global", level=0)
    parent.add("x", "integer", (0, 0))
    child = Scope(name="local", level=1, parent=parent)
    meta, in_func, scope_name = child.get("x")
    assert meta is not None
    assert meta.type == "integer"


def test_scope_num_alloced():
    scope = Scope(name="global", level=0)
    scope.add("x", "integer", (0, 0))
    scope.add("y", "float", (1, 1))
    assert scope.num_alloced() == 2


def test_scope_num_alloced_array():
    scope = Scope(name="global", level=0)
    scope.add("arr", "vec<integer>", (0, 9))
    assert scope.num_alloced() == 10


def test_nested_scope_chain():
    root = Scope(name="global", level=0)
    child1 = Scope(name="scope1", level=1, parent=root)
    child2 = Scope(name="scope2", level=2, parent=child1)
    root.add("global_var", "integer", (0, 0))
    child1.add("local1", "integer", (0, 0))
    child2.add("local2", "integer", (0, 0))
    
    meta, _, _ = child2.get("global_var")
    assert meta is not None
    meta, _, _ = child2.get("local1")
    assert meta is not None
    meta, _, _ = child2.get("local2")
    assert meta is not None
