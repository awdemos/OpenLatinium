import sys

import pytest
from lat.cli.args import prepare_cmd_args, error
from lat.utils.errors import CompilationError


def test_prepare_cmd_args_no_mode():
    """Test that missing execution mode raises CompilationError."""
    original_argv = sys.argv
    try:
        sys.argv = ["lat", "test.lat"]
        with pytest.raises(CompilationError):
            prepare_cmd_args()
    finally:
        sys.argv = original_argv


def test_prepare_cmd_args_multiple_modes():
    """Test that multiple execution modes raise CompilationError."""
    original_argv = sys.argv
    try:
        sys.argv = ["lat", "run", "build", "test.lat"]
        with pytest.raises(CompilationError):
            prepare_cmd_args()
    finally:
        sys.argv = original_argv


def test_prepare_cmd_args_unrecognized():
    """Test that unrecognized arguments raise CompilationError."""
    original_argv = sys.argv
    try:
        sys.argv = ["lat", "run", "test.lat", "--unknown"]
        with pytest.raises(CompilationError):
            prepare_cmd_args()
    finally:
        sys.argv = original_argv


def test_error_raises_compilation_error():
    """Test that error function raises CompilationError."""
    with pytest.raises(CompilationError):
        error("test error")


def test_compilation_error_str():
    """Test CompilationError string representation."""
    err = CompilationError("test message")
    assert str(err) == "test message"


def test_compilation_error_with_line():
    """Test CompilationError with line number."""
    err = CompilationError("test", line=5)
    assert err.line == 5
    assert err.column == 0
