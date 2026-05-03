"""Tests for lat.cli.compiler module."""

import os
import tempfile

import pytest

from lat.cli.compiler import (
    _compile_ast,
    _compile_rd,
    _compile_legacy,
    build_execute,
    check_execute,
)


SIMPLE_PROGRAM = '''munus main() {
    imprimo("hello")
}
'''

INVALID_PROGRAM = '''munus main() {
    x: integer = "string"
}
'''


def test_compile_ast_valid():
    """AST compilation produces bytecode for a valid program."""
    opt_args = {}
    result = _compile_ast(SIMPLE_PROGRAM, opt_args)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "start" in result


def test_compile_rd_valid():
    """RD compilation produces bytecode for a valid program."""
    opt_args = {}
    result = _compile_rd(SIMPLE_PROGRAM, opt_args)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "start" in result


def test_compile_legacy_valid():
    """Legacy compilation produces bytecode for a valid program."""
    opt_args = {}
    result = _compile_legacy(SIMPLE_PROGRAM, opt_args)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "start" in result


def test_compile_ast_ir():
    """AST compilation with --ir flag produces bytecode."""
    opt_args = {"--ir": True}
    result = _compile_ast(SIMPLE_PROGRAM, opt_args)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "start" in result


def test_compile_ast_ir_opt():
    """AST compilation with --ir and --opt flags produces bytecode."""
    opt_args = {"--ir": True, "--opt": True}
    result = _compile_ast(SIMPLE_PROGRAM, opt_args)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "start" in result


def test_compile_ast_semantic_error():
    """AST compilation raises SystemExit on semantic error."""
    opt_args = {}
    with pytest.raises(SystemExit):
        _compile_ast(INVALID_PROGRAM, opt_args)


def test_compile_rd_semantic_error():
    """RD compilation raises SystemExit on semantic error."""
    opt_args = {}
    with pytest.raises(SystemExit):
        _compile_rd(INVALID_PROGRAM, opt_args)


def test_build_execute_creates_output():
    """build_execute writes bytecode to the output file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lat', delete=False) as f:
        f.write(SIMPLE_PROGRAM)
        input_path = f.name

    output_path = input_path.replace('.lat', '.vms')

    try:
        req_args = {"input": input_path}
        opt_args = {"-o": output_path, "-v": False, "--ast": True}
        build_execute(req_args, opt_args)
        assert os.path.exists(output_path)
        with open(output_path) as f:
            content = f.read()
        assert "start" in content
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_check_execute_valid():
    """check_execute passes for a valid program."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lat', delete=False) as f:
        f.write(SIMPLE_PROGRAM)
        input_path = f.name

    try:
        req_args = {"input": input_path}
        opt_args = {"-v": False, "--ast": True}
        check_execute(req_args, opt_args)
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)


def test_check_execute_invalid():
    """check_execute raises SystemExit for an invalid program."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lat', delete=False) as f:
        f.write(INVALID_PROGRAM)
        input_path = f.name

    try:
        req_args = {"input": input_path}
        opt_args = {"-v": False, "--ast": True}
        with pytest.raises(SystemExit):
            check_execute(req_args, opt_args)
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)


def test_build_execute_skip():
    """build_execute raises SystemExit(2) for //SKIP files."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lat', delete=False) as f:
        f.write("//SKIP\n" + SIMPLE_PROGRAM)
        input_path = f.name

    output_path = input_path.replace('.lat', '.vms')

    try:
        req_args = {"input": input_path}
        opt_args = {"-o": output_path, "-v": False, "--ast": True}
        with pytest.raises(SystemExit) as exc_info:
            build_execute(req_args, opt_args)
        assert exc_info.value.code == 2
    finally:
        if os.path.exists(input_path):
            os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)
