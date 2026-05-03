import sys
sys.path.insert(0, ".")

from lat.parsing.tokenizer import tokenize, TokenizeError, Token


def test_tokenize_empty():
    tokens = list(tokenize(""))
    assert len(tokens) == 1
    assert tokens[0].type == "EOF"


def test_tokenize_integer():
    tokens = list(tokenize("42"))
    assert len(tokens) == 2
    assert tokens[0].type == "INTEGER"
    assert tokens[0].value == "42"


def test_tokenize_float():
    tokens = list(tokenize("3.14"))
    assert len(tokens) == 2
    assert tokens[0].type == "FLOAT"
    assert tokens[0].value == "3.14"


def test_tokenize_string():
    tokens = list(tokenize('"hello"'))
    assert len(tokens) == 2
    assert tokens[0].type == "STRING"
    assert tokens[0].value == '"hello"'


def test_tokenize_identifier():
    tokens = list(tokenize("foo"))
    assert len(tokens) == 2
    assert tokens[0].type == "ID"
    assert tokens[0].value == "foo"


def test_tokenize_assignment():
    tokens = list(tokenize("x = 5"))
    assert len(tokens) == 4
    assert tokens[0].type == "ID"
    assert tokens[1].type == "ASSIGN"
    assert tokens[2].type == "INTEGER"


def test_tokenize_operators():
    tokens = list(tokenize("+ - * / %"))
    types = [t.type for t in tokens]
    assert "PLUS" in types
    assert "MINUS" in types
    assert "STAR" in types
    assert "SLASH" in types
    assert "PERCENT" in types


def test_tokenize_comparison():
    tokens = list(tokenize("== != < > <= >="))
    types = [t.type for t in tokens]
    assert "EQ" in types
    assert "NEQ" in types
    assert "LT" in types
    assert "GT" in types
    assert "LTE" in types
    assert "GTE" in types


def test_tokenize_comments_skipped():
    tokens = list(tokenize("x // comment\ny"))
    values = [t.value for t in tokens]
    assert "x" in values
    assert "y" in values
    assert "comment" not in values


def test_tokenize_multiline_comment_skipped():
    tokens = list(tokenize("x /* multiline\ncomment */ y"))
    values = [t.value for t in tokens]
    assert "x" in values
    assert "y" in values
    assert "multiline" not in values


def test_tokenize_newline_skipped():
    tokens = list(tokenize("x\ny"))
    types = [t.type for t in tokens]
    assert "ID" in types
    assert "NEWLINE" not in types
    assert len([t for t in tokens if t.type == "ID"]) == 2


def test_tokenize_reserved_word():
    tokens = list(tokenize("si"))
    assert len(tokens) == 2
    assert tokens[0].type == "IF"
    assert tokens[0].value == "si"


def test_tokenize_line_column():
    tokens = list(tokenize("x\ny"))
    assert tokens[0].line == 1
    assert tokens[0].column == 1
    assert tokens[1].line == 2
    assert tokens[1].column == 1


def test_tokenize_unknown_char_skipped():
    tokens = list(tokenize("$"))
    assert len(tokens) == 1
    assert tokens[0].type == "EOF"
