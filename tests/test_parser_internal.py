"""Tests for lat.parsing._parser internal module."""

from lat.parsing import _parser


def test_parser_module_exists():
    """The _parser module loads without errors."""
    assert _parser is not None


def test_parser_has_parser_object():
    """The parser module exposes a parser object."""
    assert hasattr(_parser, 'parser')
    assert _parser.parser is not None


def test_parser_has_tokens():
    """The parser module defines token list."""
    assert hasattr(_parser, 'tokens')
    assert isinstance(_parser.tokens, list)
    assert len(_parser.tokens) > 0


def test_parser_has_reserved_words():
    """The parser module defines reserved words."""
    assert hasattr(_parser, 'reserved')
    assert isinstance(_parser.reserved, dict)
    assert len(_parser.reserved) > 0
