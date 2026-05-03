import unittest
import sys
import importlib
sys.path.insert(0, '/var/home/a/code/OpenLatinum')

from lat.parsing import ast_parser
from lat.ast.nodes import *


def parse_source(source):
    importlib.reload(ast_parser)
    return ast_parser.parser.parse(source)


class TestParserBasics(unittest.TestCase):
    def parse(self, source):
        return parse_source(source)

    def test_integer_literal(self):
        tree = self.parse('munus main() { x: integer = 42 }')
        self.assertEqual(len(tree.functions), 1)
        func = tree.functions[0]
        self.assertEqual(len(func.body), 1)
        decl = func.body[0]
        self.assertIsInstance(decl, Decl)
        self.assertIsInstance(decl.value, IntegerLiteral)
        self.assertEqual(decl.value.value, 42)

    def test_float_literal(self):
        tree = self.parse('munus main() { x: float = 3.14 }')
        decl = tree.functions[0].body[0]
        self.assertIsInstance(decl.value, FloatLiteral)
        self.assertEqual(decl.value.value, 3.14)

    def test_string_literal(self):
        tree = self.parse('munus main() { x: filum = "hello" }')
        decl = tree.functions[0].body[0]
        self.assertIsInstance(decl.value, StringLiteral)
        self.assertEqual(decl.value.value, '"hello"')


class TestParserDeclarations(unittest.TestCase):
    def parse(self, source):
        return parse_source(source)

    def test_scalar_declaration(self):
        tree = self.parse('munus main() { x: integer = 5 }')
        decl = tree.functions[0].body[0]
        self.assertEqual(decl.name, 'x')
        self.assertEqual(decl.type, 'integer')
        self.assertEqual(decl.value.value, 5)

    def test_array_declaration_with_size(self):
        tree = self.parse('munus main() { arr: vec<integer>[10] }')
        decl = tree.functions[0].body[0]
        self.assertEqual(decl.name, 'arr')
        self.assertEqual(decl.type, 'vec<integer>[10]')
        self.assertIsNone(decl.value)

    def test_array_declaration_with_literal(self):
        tree = self.parse('munus main() { arr: vec<integer> = [1, 2, 3] }')
        decl = tree.functions[0].body[0]
        self.assertEqual(decl.type, 'vec<integer>')
        self.assertIsInstance(decl.value, ArrayLiteral)
        self.assertEqual(len(decl.value.items), 3)

    def test_array_declaration_with_range(self):
        tree = self.parse('munus main() { arr: vec<integer> = [1 ... 5] }')
        decl = tree.functions[0].body[0]
        self.assertIsInstance(decl.value, ArrayRange)
        self.assertEqual(decl.value.start, 1)
        self.assertEqual(decl.value.end, 5)

    def test_pointer_declaration(self):
        tree = self.parse('munus main() { p: &integer }')
        decl = tree.functions[0].body[0]
        self.assertEqual(decl.type, '&integer')


class TestParserExpressions(unittest.TestCase):
    def parse(self, source):
        return parse_source(source)

    def test_binary_op(self):
        tree = self.parse('munus main() { x: integer = 1 + 2 }')
        decl = tree.functions[0].body[0]
        self.assertIsInstance(decl.value, BinaryOp)
        self.assertEqual(decl.value.op, '+')
        self.assertEqual(decl.value.left.value, 1)
        self.assertEqual(decl.value.right.value, 2)

    def test_unary_op(self):
        tree = self.parse('munus main() { x: integer = -5 }')
        decl = tree.functions[0].body[0]
        self.assertIsInstance(decl.value, UnaryOp)
        self.assertEqual(decl.value.op, '-')
        self.assertEqual(decl.value.operand.value, 5)

    def test_logical_and(self):
        tree = self.parse('munus main() { x: integer = 1 et 0 }')
        decl = tree.functions[0].body[0]
        self.assertIsInstance(decl.value, BinaryOp)
        self.assertEqual(decl.value.op, 'AND')

    def test_logical_or(self):
        tree = self.parse('munus main() { x: integer = 1 aut 0 }')
        decl = tree.functions[0].body[0]
        self.assertIsInstance(decl.value, BinaryOp)
        self.assertEqual(decl.value.op, 'OR')

    def test_comparison(self):
        tree = self.parse('munus main() { x: integer = 1 < 2 }')
        decl = tree.functions[0].body[0]
        self.assertIsInstance(decl.value, BinaryOp)
        self.assertEqual(decl.value.op, 'LT')

    def test_array_index(self):
        tree = self.parse('munus main() { x: integer = arr[0] }')
        decl = tree.functions[0].body[0]
        self.assertIsInstance(decl.value, ArrayIndex)
        self.assertEqual(decl.value.name, 'arr')
        self.assertEqual(len(decl.value.indices), 1)
        self.assertEqual(decl.value.indices[0].value, 0)

    def test_function_call(self):
        tree = self.parse('munus main() { x: integer = foo(1, 2) }')
        decl = tree.functions[0].body[0]
        self.assertIsInstance(decl.value, FunctionCall)
        self.assertEqual(decl.value.name, 'foo')
        self.assertEqual(len(decl.value.args), 2)


class TestParserControlFlow(unittest.TestCase):
    def parse(self, source):
        return parse_source(source)

    def test_if_statement(self):
        tree = self.parse('munus main() { si 1 == 1 { x: integer = 1 } }')
        stmt = tree.functions[0].body[0]
        self.assertIsInstance(stmt, If)
        self.assertIsInstance(stmt.condition, BinaryOp)
        self.assertEqual(len(stmt.then_body), 1)

    def test_if_else_statement(self):
        tree = self.parse('munus main() { si 1 == 1 { x: integer = 1 } aliter { x: integer = 2 } }')
        stmt = tree.functions[0].body[0]
        self.assertIsInstance(stmt, If)
        self.assertIsNotNone(stmt.else_body)

    def test_while_loop(self):
        tree = self.parse('munus main() { dum 1 == 1 { imprimo(1) } }')
        stmt = tree.functions[0].body[0]
        self.assertIsInstance(stmt, While)
        self.assertEqual(stmt.condition.op, 'EQ')

    def test_do_while_loop(self):
        tree = self.parse('munus main() { facio { imprimo(1) } dum(1 == 1) }')
        stmt = tree.functions[0].body[0]
        self.assertIsInstance(stmt, DoWhile)

    def test_for_loop(self):
        tree = self.parse('munus main() { enim(x: integer = 0; x < 10; x = x + 1) { imprimo(x) } }')
        stmt = tree.functions[0].body[0]
        self.assertIsInstance(stmt, For)
        self.assertEqual(len(stmt.init), 1)
        self.assertEqual(len(stmt.update), 1)

    def test_break_statement(self):
        tree = self.parse('munus main() { dum 1 == 1 { confractus } }')
        loop = tree.functions[0].body[0]
        self.assertIsInstance(loop.body[0], Break)

    def test_continue_statement(self):
        tree = self.parse('munus main() { dum 1 == 1 { pergo } }')
        func = tree.functions[0]
        loop = func.body[0]
        self.assertIsInstance(loop, While)
        self.assertIsInstance(loop.body[0], Continue)

    def test_match_statement(self):
        tree = self.parse('munus main() { par x % 2 { 0 -> { imprimo(1) } defectus -> { imprimo(0) } } }')
        stmt = tree.functions[0].body[0]
        self.assertIsInstance(stmt, Match)
        self.assertEqual(len(stmt.cases), 2)


class TestParserFunctions(unittest.TestCase):
    def parse(self, source):
        return parse_source(source)

    def test_function_declaration(self):
        tree = self.parse('munus add(x: integer, y: integer) -> integer { reditus x + y }')
        func = tree.functions[0]
        self.assertEqual(func.name, 'add')
        self.assertEqual(len(func.params), 2)
        self.assertEqual(func.return_type, 'integer')

    def test_function_no_params(self):
        tree = self.parse('munus main() { imprimo("hello") }')
        func = tree.functions[0]
        self.assertEqual(len(func.params), 0)

    def test_return_statement(self):
        tree = self.parse('munus main() -> integer { reditus 42 }')
        func = tree.functions[0]
        self.assertIsInstance(func.body[0], Return)
        self.assertEqual(func.body[0].value.value, 42)

    def test_void_return(self):
        tree = self.parse('munus main() { reditus }')
        func = tree.functions[0]
        self.assertIsInstance(func.body[0], Return)
        self.assertIsNone(func.body[0].value)


class TestParserGlobals(unittest.TestCase):
    def parse(self, source):
        return parse_source(source)

    def test_global_declaration(self):
        tree = self.parse('x: integer = 5 munus main() { }')
        self.assertEqual(len(tree.globals), 1)
        self.assertEqual(tree.globals[0].name, 'x')


if __name__ == '__main__':
    unittest.main()
