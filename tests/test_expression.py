import sys
sys.path.insert(0, ".")

from lat.semantics._expression import Expression


def test_expression_creation():
    expr = Expression()
    assert expr is not None


def test_expression_has_productions():
    expr = Expression()
    assert hasattr(expr, 'productions')
    assert len(expr.productions) > 0
