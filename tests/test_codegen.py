"""Comprehensive unit tests for the AST-to-bytecode code generator."""
import unittest
from lat.ast.nodes import *
from lat.codegen.generator import CodeGenerator, generate


class TestCodegenBase(unittest.TestCase):
    def generate(self, program):
        return generate(program)

    def assertInBytecode(self, program, instruction):
        code = self.generate(program)
        self.assertIn(instruction, code, f"Expected '{instruction}' in generated code:\n{code}")

    def assertNotInBytecode(self, program, instruction):
        code = self.generate(program)
        self.assertNotIn(instruction, code, f"Did not expect '{instruction}' in generated code:\n{code}")

    def make_program(self, globals=None, functions=None):
        return Program(
            globals=globals or [],
            functions=functions or []
        )


class TestCodegenLiterals(TestCodegenBase):
    def test_integer_literal(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IntegerLiteral(42))
            ])
        ])
        self.assertInBytecode(prog, "PUSHI 42")

    def test_float_literal(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "float", FloatLiteral(3.14))
            ])
        ])
        self.assertInBytecode(prog, "PUSHF 3.14")

    def test_string_literal(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("s", "filum", StringLiteral("hello"))
            ])
        ])
        self.assertInBytecode(prog, "PUSHS hello")

    def test_boolean_true(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("b", "boolean", BooleanLiteral(True))
            ])
        ])
        self.assertInBytecode(prog, "PUSHI 1")

    def test_boolean_false(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("b", "boolean", BooleanLiteral(False))
            ])
        ])
        self.assertInBytecode(prog, "PUSHI 0")


class TestCodegenVariables(TestCodegenBase):
    def test_global_variable(self):
        prog = self.make_program(
            globals=[Decl("x", "integer", IntegerLiteral(42))],
            functions=[Function("main", [], None, [])]
        )
        code = self.generate(prog)
        self.assertIn("PUSHI 42", code)
        self.assertIn("STOREG 0", code)

    def test_local_variable(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IntegerLiteral(42))
            ])
        ])
        code = self.generate(prog)
        self.assertIn("PUSHI 42", code)
        self.assertIn("STOREL 0", code)

    def test_variable_load(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IntegerLiteral(42)),
                Print([Identifier("x")])
            ])
        ])
        self.assertInBytecode(prog, "PUSHFP")
        self.assertInBytecode(prog, "LOAD 0")

    def test_global_load(self):
        prog = self.make_program(
            globals=[Decl("x", "integer", IntegerLiteral(42))],
            functions=[Function("main", [], None, [
                Print([Identifier("x")])
            ])]
        )
        self.assertInBytecode(prog, "PUSHGP")
        self.assertInBytecode(prog, "LOAD 0")

    def test_assignment(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer"),
                Assignment(Identifier("x"), IntegerLiteral(100))
            ])
        ])
        self.assertInBytecode(prog, "PUSHI 100")
        self.assertInBytecode(prog, "STOREL 0")


class TestCodegenBinaryOps(TestCodegenBase):
    def test_integer_add(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(1), '+', IntegerLiteral(2)))
            ])
        ])
        self.assertInBytecode(prog, "ADD")

    def test_float_add(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "float", BinaryOp(FloatLiteral(1.0), '+', FloatLiteral(2.0)))
            ])
        ])
        self.assertInBytecode(prog, "FADD")

    def test_string_concat(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("s", "filum", BinaryOp(StringLiteral("a"), '+', StringLiteral("b")))
            ])
        ])
        self.assertInBytecode(prog, "CONCAT")

    def test_integer_sub(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(5), '-', IntegerLiteral(3)))
            ])
        ])
        self.assertInBytecode(prog, "SUB")

    def test_integer_mul(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(2), '*', IntegerLiteral(3)))
            ])
        ])
        self.assertInBytecode(prog, "MUL")

    def test_integer_div(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(6), '/', IntegerLiteral(2)))
            ])
        ])
        self.assertInBytecode(prog, "DIV")

    def test_integer_mod(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(10), '%', IntegerLiteral(3)))
            ])
        ])
        self.assertInBytecode(prog, "MOD")

    def test_equal(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(1), 'EQ', IntegerLiteral(2)))
            ])
        ])
        self.assertInBytecode(prog, "EQUAL")

    def test_not_equal(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(1), 'NEQ', IntegerLiteral(2)))
            ])
        ])
        self.assertInBytecode(prog, "EQUAL")
        self.assertInBytecode(prog, "NOT")

    def test_less_than(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(1), 'LT', IntegerLiteral(2)))
            ])
        ])
        self.assertInBytecode(prog, "INF")

    def test_greater_than(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(2), 'GT', IntegerLiteral(1)))
            ])
        ])
        self.assertInBytecode(prog, "SUP")

    def test_less_equal(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(1), 'LTE', IntegerLiteral(2)))
            ])
        ])
        self.assertInBytecode(prog, "INFEQ")

    def test_greater_equal(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(2), 'GTE', IntegerLiteral(1)))
            ])
        ])
        self.assertInBytecode(prog, "SUPEQ")

    def test_pointer_add_integer(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1)])),
                Decl("p", "&integer", Identifier("arr")),
                Decl("q", "&integer", BinaryOp(Identifier("p"), '+', IntegerLiteral(1)))
            ])
        ])
        self.assertInBytecode(prog, "PADD")

    def test_and_short_circuit(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(1), 'AND', IntegerLiteral(0)))
            ])
        ])
        code = self.generate(prog)
        self.assertIn("DUP 1", code)
        self.assertIn("JZ", code)

    def test_or_short_circuit(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(1), 'OR', IntegerLiteral(0)))
            ])
        ])
        code = self.generate(prog)
        self.assertIn("DUP 1", code)
        self.assertIn("JZ", code)


class TestCodegenUnaryOps(TestCodegenBase):
    def test_not_integer(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", UnaryOp('NOT', IntegerLiteral(1)))
            ])
        ])
        self.assertInBytecode(prog, "NOT")

    def test_negate_integer(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", UnaryOp('-', IntegerLiteral(5)))
            ])
        ])
        self.assertInBytecode(prog, "PUSHI -1")
        self.assertInBytecode(prog, "MUL")

    def test_negate_float(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "float", UnaryOp('-', FloatLiteral(3.14)))
            ])
        ])
        self.assertInBytecode(prog, "PUSHF -1.0")
        self.assertInBytecode(prog, "FMUL")


class TestCodegenControlFlow(TestCodegenBase):
    def test_if(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                If(IntegerLiteral(1), [Print([IntegerLiteral(1)])], None)
            ])
        ])
        code = self.generate(prog)
        self.assertIn("JZ", code)
        self.assertIn("JUMP", code)

    def test_if_else(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                If(IntegerLiteral(1), [Print([IntegerLiteral(1)])], [Print([IntegerLiteral(0)])])
            ])
        ])
        code = self.generate(prog)
        self.assertIn("JZ", code)
        self.assertIn("JUMP", code)

    def test_while(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                While(IntegerLiteral(1), [Print([IntegerLiteral(1)])])
            ])
        ])
        code = self.generate(prog)
        self.assertIn("LOOP1START:", code)
        self.assertIn("JZ", code)
        self.assertIn("JUMP LOOP1START", code)
        self.assertIn("LOOP1END:", code)

    def test_do_while(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                DoWhile(IntegerLiteral(1), [Print([IntegerLiteral(1)])])
            ])
        ])
        code = self.generate(prog)
        self.assertIn("LOOP1START:", code)
        self.assertIn("JZ", code)
        self.assertIn("JUMP LOOP1START", code)

    def test_for(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                For(
                    [Decl("i", "integer", IntegerLiteral(0))],
                    BinaryOp(Identifier("i"), 'LT', IntegerLiteral(10)),
                    [Assignment(Identifier("i"), BinaryOp(Identifier("i"), '+', IntegerLiteral(1)))],
                    [Print([Identifier("i")])]
                )
            ])
        ])
        code = self.generate(prog)
        self.assertIn("LOOP1START:", code)
        self.assertIn("JZ", code)
        self.assertIn("JUMP LOOP1START", code)

    def test_break(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                While(IntegerLiteral(1), [Break()])
            ])
        ])
        code = self.generate(prog)
        self.assertIn("JUMP LOOP1END", code)

    def test_continue(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                While(IntegerLiteral(1), [Continue()])
            ])
        ])
        code = self.generate(prog)
        self.assertIn("JUMP NEXTLOOP1", code)

    def test_match(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IntegerLiteral(1)),
                Match(Identifier("x"), [
                    Case(IntegerLiteral(1), [Print([IntegerLiteral(1)])]),
                    Default([Print([IntegerLiteral(0)])])
                ])
            ])
        ])
        code = self.generate(prog)
        self.assertIn("DUP 1", code)
        self.assertIn("EQUAL", code)
        self.assertIn("JZ", code)
        self.assertIn("JUMP", code)


class TestCodegenFunctions(TestCodegenBase):
    def test_function_declaration(self):
        prog = self.make_program(functions=[
            Function("add", [Param("a", "integer"), Param("b", "integer")], "integer", [
                Return(BinaryOp(Identifier("a"), '+', Identifier("b")))
            ]),
            Function("main", [], None, [])
        ])
        code = self.generate(prog)
        self.assertIn("add:", code)
        self.assertIn("PUSHN 2", code)
        self.assertIn("RETURN", code)

    def test_function_call(self):
        prog = self.make_program(functions=[
            Function("getone", [], "integer", [
                Return(IntegerLiteral(1))
            ]),
            Function("main", [], None, [
                Decl("x", "integer", FunctionCall("getone", []))
            ])
        ])
        code = self.generate(prog)
        self.assertIn("PUSHA getone", code)
        self.assertIn("CALL", code)

    def test_function_call_with_args(self):
        prog = self.make_program(functions=[
            Function("add", [Param("a", "integer"), Param("b", "integer")], "integer", [
                Return(BinaryOp(Identifier("a"), '+', Identifier("b")))
            ]),
            Function("main", [], None, [
                Decl("x", "integer", FunctionCall("add", [IntegerLiteral(1), IntegerLiteral(2)]))
            ])
        ])
        code = self.generate(prog)
        self.assertIn("PUSHI 1", code)
        self.assertIn("PUSHI 2", code)
        self.assertIn("PUSHA add", code)
        self.assertIn("CALL", code)
        self.assertIn("POP 2", code)

    def test_main_entry_point(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [])
        ])
        code = self.generate(prog)
        self.assertIn("start", code)
        self.assertIn("PUSHA main", code)
        self.assertIn("CALL", code)
        self.assertIn("stop", code)

    def test_return_value(self):
        prog = self.make_program(functions=[
            Function("getone", [], "integer", [
                Return(IntegerLiteral(1))
            ]),
            Function("main", [], None, [])
        ])
        code = self.generate(prog)
        self.assertIn("PUSHI 1", code)
        self.assertIn("STOREL -1", code)
        self.assertIn("RETURN", code)

    def test_void_return(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Return()
            ])
        ])
        code = self.generate(prog)
        self.assertIn("RETURN", code)
        self.assertNotIn("STOREL", code)


class TestCodegenArrays(TestCodegenBase):
    def test_array_literal(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1), IntegerLiteral(2)]))
            ])
        ])
        code = self.generate(prog)
        self.assertIn("PUSHFP", code)
        self.assertIn("PADD", code)
        self.assertIn("STORE 0", code)

    def test_array_range(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayRange(1, 3))
            ])
        ])
        code = self.generate(prog)
        # Should generate 3 elements (1, 2, 3)
        self.assertIn("PUSHI 1", code)
        self.assertIn("PUSHI 2", code)
        self.assertIn("PUSHI 3", code)

    def test_array_index_read(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(10)])),
                Decl("x", "integer", ArrayIndex("arr", [IntegerLiteral(0)]))
            ])
        ])
        code = self.generate(prog)
        self.assertIn("PADD", code)
        self.assertIn("LOAD 0", code)

    def test_array_index_write(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(10)])),
                Assignment(ArrayIndex("arr", [IntegerLiteral(0)]), IntegerLiteral(20))
            ])
        ])
        code = self.generate(prog)
        self.assertIn("PADD", code)
        self.assertIn("STORE 0", code)

    def test_pointer_declaration(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1)])),
                Decl("p", "&integer", Identifier("arr"))
            ])
        ])
        code = self.generate(prog)
        self.assertIn("PUSHFP", code)
        self.assertIn("PADD", code)

    def test_pointer_array_assignment(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1)])),
                Decl("p", "&integer", Identifier("arr")),
                Assignment(ArrayIndex("p", [IntegerLiteral(0)]), IntegerLiteral(42))
            ])
        ])
        code = self.generate(prog)
        # Pointer var is at position 1, loads with LOAD 1
        self.assertIn("LOAD 1", code)
        self.assertIn("PADD", code)
        self.assertIn("STORE 0", code)

    def test_ref_expression(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IntegerLiteral(42)),
                Decl("p", "&integer", Ref("x"))
            ])
        ])
        code = self.generate(prog)
        self.assertIn("PUSHFP", code)
        self.assertIn("PADD", code)


class TestCodegenPrint(TestCodegenBase):
    def test_print_integer(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Print([IntegerLiteral(42)])
            ])
        ])
        self.assertInBytecode(prog, "WRITEI")

    def test_print_float(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Print([FloatLiteral(3.14)])
            ])
        ])
        self.assertInBytecode(prog, "WRITEF")

    def test_print_string(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Print([StringLiteral("hello")])
            ])
        ])
        self.assertInBytecode(prog, "WRITES")

    def test_print_multiple(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Print([IntegerLiteral(1), IntegerLiteral(2)])
            ])
        ])
        code = self.generate(prog)
        self.assertEqual(code.count("WRITEI"), 2)


class TestCodegenRead(TestCodegenBase):
    def test_read_int(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer"),
                Read("legerei", [Identifier("x")])
            ])
        ])
        self.assertInBytecode(prog, "READI")

    def test_read_float(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "float"),
                Read("legeref", [Identifier("x")])
            ])
        ])
        self.assertInBytecode(prog, "READF")

    def test_read_string(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("s", "filum"),
                Read("legeres", [Identifier("s")])
            ])
        ])
        self.assertInBytecode(prog, "READS")


class TestCodegenIfExpr(TestCodegenBase):
    def test_if_expr(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IfExpr(BooleanLiteral(True), IntegerLiteral(1), IntegerLiteral(0)))
            ])
        ])
        code = self.generate(prog)
        self.assertIn("IFEXPR", code)
        self.assertIn("JZ", code)
        self.assertIn("JUMP", code)


class TestCodegenEdgeCases(TestCodegenBase):
    def test_empty_program(self):
        prog = self.make_program()
        code = self.generate(prog)
        self.assertIn("start", code)
        self.assertIn("stop", code)

    def test_no_main_function(self):
        prog = self.make_program(functions=[
            Function("foo", [], None, [])
        ])
        code = self.generate(prog)
        self.assertIn("start", code)
        self.assertIn("PUSHA main", code)
        # Will fail at runtime but codegen succeeds

    def test_uninitialized_variable(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer")
            ])
        ])
        code = self.generate(prog)
        self.assertIn("PUSHI 0", code)
        self.assertIn("STOREL 0", code)

    def test_uninitialized_float(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "float")
            ])
        ])
        code = self.generate(prog)
        self.assertIn("PUSHF 0.0", code)

    def test_uninitialized_string(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("s", "filum")
            ])
        ])
        code = self.generate(prog)
        self.assertIn("PUSHS ''", code)

    def test_function_params(self):
        prog = self.make_program(functions=[
            Function("main", [Param("argc", "integer"), Param("argv", "&filum")], "integer", [
                Return(IntegerLiteral(0))
            ])
        ])
        code = self.generate(prog)
        self.assertIn("PUSHN 2", code)
        self.assertIn("PUSHFP", code)
        self.assertIn("LOAD -2", code)
        self.assertIn("STOREL 0", code)
        self.assertIn("LOAD -1", code)
        self.assertIn("STOREL 1", code)


if __name__ == '__main__':
    unittest.main()
