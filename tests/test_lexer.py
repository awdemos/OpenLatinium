import sys
sys.path.insert(0, ".")

from lat.lexing._lexer import literals, reserved, tokens


def test_literals_defined():
    assert len(literals) > 0
    assert "[" in literals
    assert "]" in literals


def test_reserved_words():
    assert "integer" in reserved
    assert reserved["integer"] == "TYPE_INT"
    assert "filum" in reserved
    assert reserved["filum"] == "TYPE_STRING"
    assert "float" in reserved
    assert reserved["float"] == "TYPE_FLOAT"


def test_tokens_list():
    assert "INTEGER" in tokens
    assert "FLOAT" in tokens
    assert "FILUM" in tokens
    assert "ID" in tokens
    assert "ASSIGN" in tokens


def test_arithmetic_literals():
    assert "+" in literals
    assert "-" in literals
    assert "*" in literals
    assert "/" in literals
    assert "%" in literals


def test_control_flow_reserved():
    assert "si" in reserved
    assert reserved["si"] == "IF"
    assert "aliter" in reserved
    assert reserved["aliter"] == "ELSE"
    assert "dum" in reserved
    assert reserved["dum"] == "WHILE"
