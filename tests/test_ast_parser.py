import sys
sys.path.insert(0, ".")

from lat.parsing.ast_parser import tokens, literals


def test_tokens_imported():
    assert len(tokens) > 0
    assert "INTEGER" in tokens


def test_literals_imported():
    assert len(literals) > 0
    assert "+" in literals
