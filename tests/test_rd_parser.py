import sys
sys.path.insert(0, ".")

from lat.parsing.rd_parser import Parser, parse_text, parse_tokens
from lat.parsing.tokenizer import tokenize


def test_parser_creation():
    tokens = list(tokenize("1"))
    parser = Parser(tokens)
    assert parser is not None


def test_parse_text_exists():
    assert callable(parse_text)


def test_parse_tokens_exists():
    assert callable(parse_tokens)
