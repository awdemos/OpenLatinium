import sys
sys.path.insert(0, ".")

from lat.semantics._functions import FunctionData, Functions


def test_function_data_creation():
    fd = FunctionData(name="foo")
    assert fd.name == "foo"
    assert fd.input_types == []
    assert fd.output_type is None


def test_function_data_with_types():
    fd = FunctionData(name="bar", input_types=["integer", "float"], output_type="integer")
    assert fd.name == "bar"
    assert fd.input_types == ["integer", "float"]
    assert fd.output_type == "integer"


def test_functions_creation():
    fh = Functions()
    assert fh.Table == {}
    assert fh.current_function is None


def test_functions_add():
    fh = Functions()
    fh.add("foo")
    assert "foo" in fh.Table
    assert fh.Table["foo"].name == "foo"


def test_functions_get_exists():
    fh = Functions()
    fh.add("foo")
    result = fh.get("foo")
    assert result is not None
    assert result.name == "foo"


def test_functions_get_missing():
    fh = Functions()
    result = fh.get("bar")
    assert result is None


def test_functions_handle_exists():
    fh = Functions()
    assert "call" in fh.productions
    assert "header" in fh.productions
    assert "id" in fh.productions
    assert "body" in fh.productions
    assert "parameter" in fh.productions
    assert "out_type" in fh.productions
    assert "argument" in fh.productions
    assert "return" in fh.productions


def test_multiple_functions():
    fh = Functions()
    fh.add("foo")
    fh.add("bar")
    assert "foo" in fh.Table
    assert "bar" in fh.Table
    assert fh.get("foo").name == "foo"
    assert fh.get("bar").name == "bar"
