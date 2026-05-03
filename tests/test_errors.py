import sys
sys.path.insert(0, ".")

from lat.utils.errors import find_column, std_message, CompilationError


def test_find_column_basic():
    input_text = "hello\nworld"
    class MockToken:
        lexpos = 7
    token = MockToken()
    result = find_column(input_text, token)
    assert result == 2


def test_find_column_start_of_line():
    input_text = "hello\nworld"
    class MockToken:
        lexpos = 6
    token = MockToken()
    result = find_column(input_text, token)
    assert result == 1


def test_std_message_single():
    result = std_message(["hello"])
    assert result == "hello\n"


def test_std_message_multiple():
    result = std_message(["line1", "line2", "line3"])
    assert result == "line1\nline2\nline3\n"


def test_compilation_error_message():
    error = CompilationError("test error")
    assert str(error) == "test error"


def test_compilation_error_with_location():
    error = CompilationError("test error", line=10, column=5)
    assert error.line == 10
    assert error.column == 5


def test_find_column_empty_input():
    input_text = ""
    class MockToken:
        lexpos = 0
    token = MockToken()
    result = find_column(input_text, token)
    assert result == 1


def test_find_column_out_of_bounds():
    input_text = "hi"
    class MockToken:
        lexpos = 100
    token = MockToken()
    result = find_column(input_text, token)
    assert result == 101


def test_std_message_empty():
    result = std_message([])
    assert result == "\n"


def test_std_message_with_empty_strings():
    result = std_message(["", "line", ""])
    assert result == "\nline\n\n"


def test_compilation_error_raises():
    try:
        raise CompilationError("error msg")
    except CompilationError as e:
        assert str(e) == "error msg"
    else:
        assert False, "Expected CompilationError to be raised"


def test_compilation_error_inheritance():
    error = CompilationError("test")
    assert isinstance(error, Exception)
