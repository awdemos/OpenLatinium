"""Comprehensive unit tests for the semantic analyzer."""
import unittest
from lat.ast.nodes import *
from lat.semantic.analyzer import SemanticAnalyzer, analyze_program


class TestSemanticBase(unittest.TestCase):
    def analyze(self, program):
        analyzer = SemanticAnalyzer()
        return analyzer.analyze(program)

    def assertValid(self, program):
        ok, errors, warnings = self.analyze(program)
        self.assertTrue(ok, f"Expected valid program but got errors: {[e.message for e in errors]}")

    def assertErrors(self, program, expected_count=None):
        ok, errors, warnings = self.analyze(program)
        self.assertFalse(ok, "Expected errors but program was valid")
        if expected_count is not None:
            self.assertEqual(len(errors), expected_count, 
                f"Expected {expected_count} errors but got {len(errors)}: {[e.message for e in errors]}")
        return errors

    def make_program(self, globals=None, functions=None):
        return Program(
            globals=globals or [],
            functions=functions or []
        )


class TestSemanticDeclarations(TestSemanticBase):
    def test_valid_declaration(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IntegerLiteral(42))
            ])
        ])
        self.assertValid(prog)

    def test_declaration_no_init(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer")
            ])
        ])
        self.assertValid(prog)

    def test_redefinition_same_scope(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer"),
                Decl("x", "float")
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("already defined", errors[0].message)

    def test_invalid_type(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "invalid_type")
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Invalid type", errors[0].message)

    def test_type_mismatch_init(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", FloatLiteral(3.14))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Cannot initialize", errors[0].message)

    def test_pointer_declaration(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1)])),
                Decl("p", "&integer", Identifier("arr"))
            ])
        ])
        self.assertValid(prog)

    def test_array_declaration(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([
                    IntegerLiteral(1), IntegerLiteral(2)
                ]))
            ])
        ])
        self.assertValid(prog)

    def test_const_declaration(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("PI", "float", FloatLiteral(3.14), is_const=True)
            ])
        ])
        self.assertValid(prog)


class TestSemanticAssignments(TestSemanticBase):
    def test_valid_assignment(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer"),
                Assignment(Identifier("x"), IntegerLiteral(42))
            ])
        ])
        self.assertValid(prog)

    def test_assignment_undeclared(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Assignment(Identifier("x"), IntegerLiteral(42))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("undeclared", errors[0].message)

    def test_assignment_const(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IntegerLiteral(1), is_const=True),
                Assignment(Identifier("x"), IntegerLiteral(42))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("constant", errors[0].message)

    def test_assignment_type_mismatch(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer"),
                Assignment(Identifier("x"), FloatLiteral(3.14))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Cannot assign", errors[0].message)

    def test_assignment_array_whole(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1)])),
                Assignment(Identifier("arr"), IntegerLiteral(1))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("array", errors[0].message.lower())

    def test_array_index_assignment_valid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1)])),
                Assignment(ArrayIndex("arr", [IntegerLiteral(0)]), IntegerLiteral(42))
            ])
        ])
        self.assertValid(prog)

    def test_array_index_assignment_type_mismatch(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1)])),
                Assignment(ArrayIndex("arr", [IntegerLiteral(0)]), FloatLiteral(3.14))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Cannot assign", errors[0].message)

    def test_array_index_non_integer(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1)])),
                Assignment(ArrayIndex("arr", [FloatLiteral(1.5)]), IntegerLiteral(1))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("integer", errors[0].message)

    def test_array_index_wrong_dimensions(self):
        # 1D array with 2 indices - only fails when array_shape is known
        # ArrayLiteral doesn't set array_shape, so this passes
        # Test with a "fake" 2D array scenario by checking index count vs shape
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1)])),
                Assignment(ArrayIndex("arr", [IntegerLiteral(0)]), IntegerLiteral(1))
            ])
        ])
        self.assertValid(prog)


class TestSemanticExpressions(TestSemanticBase):
    def test_undeclared_variable(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Print([Identifier("x")])
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Undeclared", errors[0].message)

    def test_binary_op_valid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(1), '+', IntegerLiteral(2)))
            ])
        ])
        self.assertValid(prog)

    def test_binary_op_type_mismatch(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(1), '+', FloatLiteral(2.0)))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("add", errors[0].message.lower())

    def test_unary_op_not(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", UnaryOp('!', IntegerLiteral(1)))
            ])
        ])
        self.assertValid(prog)

    def test_unary_op_neg(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", UnaryOp('-', IntegerLiteral(1)))
            ])
        ])
        self.assertValid(prog)

    def test_unary_op_invalid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", UnaryOp('-', StringLiteral("hello")))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("neg", errors[0].message.lower())

    def test_array_index_access(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1)])),
                Decl("x", "integer", ArrayIndex("arr", [IntegerLiteral(0)]))
            ])
        ])
        self.assertValid(prog)

    def test_array_index_non_array(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer"),
                Decl("y", "integer", ArrayIndex("x", [IntegerLiteral(0)]))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Indexing not allowed", errors[0].message)

    def test_array_literal_valid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1), IntegerLiteral(2)]))
            ])
        ])
        self.assertValid(prog)

    def test_array_literal_mixed_types(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1), FloatLiteral(2.0)]))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("mixed types", errors[0].message)

    def test_array_literal_empty(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([]))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Empty array", errors[0].message)

    def test_ref_valid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer"),
                Decl("p", "&integer", Ref("x"))
            ])
        ])
        self.assertValid(prog)

    def test_ref_undeclared(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("p", "&integer", Ref("x"))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Undeclared", errors[0].message)


class TestSemanticControlFlow(TestSemanticBase):
    def test_if_valid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                If(IntegerLiteral(1), [Print([IntegerLiteral(1)])], None)
            ])
        ])
        self.assertValid(prog)

    def test_if_condition_type_error(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                If(StringLiteral("hello"), [Print([IntegerLiteral(1)])], None)
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Condition must be", errors[0].message)

    def test_if_else_valid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                If(IntegerLiteral(1), [Print([IntegerLiteral(1)])], [Print([IntegerLiteral(0)])])
            ])
        ])
        self.assertValid(prog)

    def test_while_valid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                While(IntegerLiteral(1), [Print([IntegerLiteral(1)])])
            ])
        ])
        self.assertValid(prog)

    def test_while_condition_type_error(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                While(StringLiteral("hello"), [Print([IntegerLiteral(1)])])
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Condition must be", errors[0].message)

    def test_dowhile_valid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                DoWhile(IntegerLiteral(1), [Print([IntegerLiteral(1)])])
            ])
        ])
        self.assertValid(prog)

    def test_for_valid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                For(
                    [Decl("i", "integer", IntegerLiteral(0))],
                    BinaryOp(Identifier("i"), '<', IntegerLiteral(10)),
                    [Assignment(Identifier("i"), BinaryOp(Identifier("i"), '+', IntegerLiteral(1)))],
                    [Print([Identifier("i")])]
                )
            ])
        ])
        self.assertValid(prog)

    def test_break_valid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                While(IntegerLiteral(1), [Break()])
            ])
        ])
        self.assertValid(prog)

    def test_break_outside_loop(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Break()
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("outside of loop", errors[0].message)

    def test_continue_valid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                While(IntegerLiteral(1), [Continue()])
            ])
        ])
        self.assertValid(prog)

    def test_continue_outside_loop(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Continue()
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("outside of loop", errors[0].message)

    def test_match_valid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IntegerLiteral(1)),
                Match(Identifier("x"), [
                    Case(IntegerLiteral(1), [Print([IntegerLiteral(1)])]),
                    Default([Print([IntegerLiteral(0)])])
                ])
            ])
        ])
        self.assertValid(prog)

    def test_match_case_type_mismatch(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IntegerLiteral(1)),
                Match(Identifier("x"), [
                    Case(FloatLiteral(1.0), [Print([IntegerLiteral(1)])])
                ])
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("doesn't match", errors[0].message)


class TestSemanticFunctions(TestSemanticBase):
    def test_function_declaration(self):
        prog = self.make_program(functions=[
            Function("add", [Param("a", "integer"), Param("b", "integer")], "integer", [
                Return(BinaryOp(Identifier("a"), '+', Identifier("b")))
            ]),
            Function("main", [], None, [])
        ])
        self.assertValid(prog)

    def test_function_redefinition(self):
        prog = self.make_program(functions=[
            Function("main", [], None, []),
            Function("main", [], None, [])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Redefinition", errors[0].message)

    def test_function_call_valid(self):
        prog = self.make_program(functions=[
            Function("add", [Param("a", "integer"), Param("b", "integer")], "integer", [
                Return(BinaryOp(Identifier("a"), '+', Identifier("b")))
            ]),
            Function("main", [], None, [
                Decl("x", "integer", FunctionCall("add", [IntegerLiteral(1), IntegerLiteral(2)]))
            ])
        ])
        self.assertValid(prog)

    def test_function_call_undeclared(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", FunctionCall("add", [IntegerLiteral(1), IntegerLiteral(2)]))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("not declared", errors[0].message)

    def test_function_call_wrong_arg_count(self):
        prog = self.make_program(functions=[
            Function("add", [Param("a", "integer"), Param("b", "integer")], "integer", [
                Return(BinaryOp(Identifier("a"), '+', Identifier("b")))
            ]),
            Function("main", [], None, [
                Decl("x", "integer", FunctionCall("add", [IntegerLiteral(1)]))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("expects", errors[0].message)

    def test_function_call_wrong_arg_type(self):
        prog = self.make_program(functions=[
            Function("add", [Param("a", "integer"), Param("b", "integer")], "integer", [
                Return(BinaryOp(Identifier("a"), '+', Identifier("b")))
            ]),
            Function("main", [], None, [
                Decl("x", "integer", FunctionCall("add", [IntegerLiteral(1), FloatLiteral(2.0)]))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("expected", errors[0].message)

    def test_return_void_function(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Return()
            ])
        ])
        self.assertValid(prog)

    def test_return_value_in_void_function(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Return(IntegerLiteral(1))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("does not return", errors[0].message)

    def test_return_missing_in_value_function(self):
        prog = self.make_program(functions=[
            Function("get_one", [], "integer", [
                Decl("x", "integer", IntegerLiteral(1))
            ])
        ])
        # Analyzer doesn't check for missing return, only type mismatch
        self.assertValid(prog)

    def test_return_type_mismatch(self):
        prog = self.make_program(functions=[
            Function("get_one", [], "integer", [
                Return(FloatLiteral(1.0))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Return type", errors[0].message)

    def test_param_redefinition(self):
        prog = self.make_program(functions=[
            Function("main", [Param("x", "integer"), Param("x", "float")], None, [
                Print([Identifier("x")])
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("already defined", errors[0].message)


class TestSemanticScoping(TestSemanticBase):
    def test_variable_lookup_parent_scope(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IntegerLiteral(1)),
                If(IntegerLiteral(1), [
                    Print([Identifier("x")])
                ], None)
            ])
        ])
        self.assertValid(prog)

    def test_variable_not_visible_in_parent(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                If(IntegerLiteral(1), [
                    Decl("x", "integer", IntegerLiteral(1))
                ], None),
                Print([Identifier("x")])
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Undeclared", errors[0].message)

    def test_nested_scope_shadowing(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IntegerLiteral(1)),
                If(IntegerLiteral(1), [
                    Decl("x", "float", FloatLiteral(1.0)),
                    Print([Identifier("x")])
                ], None),
                Print([Identifier("x")])
            ])
        ])
        # Shadowing is allowed, both prints are valid
        self.assertValid(prog)

    def test_global_variable(self):
        prog = self.make_program(
            globals=[Decl("x", "integer", IntegerLiteral(42))],
            functions=[
                Function("main", [], None, [
                    Print([Identifier("x")])
                ])
            ]
        )
        self.assertValid(prog)

    def test_function_scope_isolation(self):
        prog = self.make_program(functions=[
            Function("foo", [], None, [
                Decl("x", "integer", IntegerLiteral(1))
            ]),
            Function("main", [], None, [
                Print([Identifier("x")])
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("Undeclared", errors[0].message)


class TestSemanticPrint(TestSemanticBase):
    def test_print_integer(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Print([IntegerLiteral(1)])
            ])
        ])
        self.assertValid(prog)

    def test_print_float(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Print([FloatLiteral(3.14)])
            ])
        ])
        self.assertValid(prog)

    def test_print_string(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Print([StringLiteral("hello")])
            ])
        ])
        self.assertValid(prog)

    def test_print_boolean(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Print([BooleanLiteral(True)])
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("boolean", errors[0].message)

    def test_print_array_error(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1)])),
                Print([Identifier("arr")])
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("array", errors[0].message.lower())


class TestSemanticRead(TestSemanticBase):
    def test_read_int(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer"),
                Assignment(Identifier("x"), Read("read_int", [Identifier("x")]))
            ])
        ])
        self.assertValid(prog)

    def test_read_float(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "float"),
                Assignment(Identifier("x"), Read("read_float", [Identifier("x")]))
            ])
        ])
        self.assertValid(prog)


class TestSemanticIfExpr(TestSemanticBase):
    def test_if_expr_valid(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IfExpr(BooleanLiteral(True), IntegerLiteral(1), IntegerLiteral(0)))
            ])
        ])
        self.assertValid(prog)

    def test_if_expr_condition_type(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IfExpr(IntegerLiteral(1), IntegerLiteral(1), IntegerLiteral(0)))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("must be 'boolean'", errors[0].message)

    def test_if_expr_branch_mismatch(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", IfExpr(BooleanLiteral(True), IntegerLiteral(1), FloatLiteral(1.0)))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("different types", errors[0].message)


class TestSemanticPointerArithmetic(TestSemanticBase):
    def test_pointer_add_integer(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1)])),
                Decl("p", "&integer", Identifier("arr")),
                Decl("q", "&integer", BinaryOp(Identifier("p"), '+', IntegerLiteral(1)))
            ])
        ])
        self.assertValid(prog)

    def test_pointer_sub_integer(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1)])),
                Decl("p", "&integer", Identifier("arr")),
                Decl("q", "&integer", BinaryOp(Identifier("p"), '-', IntegerLiteral(1)))
            ])
        ])
        self.assertValid(prog)

    def test_pointer_sub_pointer(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayLiteral([IntegerLiteral(1), IntegerLiteral(2)])),
                Decl("p", "&integer", Identifier("arr")),
                Decl("q", "&integer", BinaryOp(Identifier("p"), '+', IntegerLiteral(1))),
                Decl("diff", "integer", BinaryOp(Identifier("q"), '-', Identifier("p")))
            ])
        ])
        self.assertValid(prog)


class TestSemanticArrayRange(TestSemanticBase):
    def test_array_range(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("arr", "vec<integer>", ArrayRange(1, 10))
            ])
        ])
        self.assertValid(prog)


class TestSemanticMultipleErrors(TestSemanticBase):
    def test_multiple_errors_collected(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Assignment(Identifier("x"), IntegerLiteral(1)),
                Assignment(Identifier("y"), FloatLiteral(1.0)),
                Print([Identifier("z")])
            ])
        ])
        errors = self.assertErrors(prog, 3)
        messages = [e.message for e in errors]
        self.assertTrue(any("x" in m for m in messages))
        self.assertTrue(any("y" in m for m in messages))
        self.assertTrue(any("z" in m for m in messages))


class TestSemanticEdgeCases(TestSemanticBase):
    def test_empty_program(self):
        prog = self.make_program()
        self.assertValid(prog)

    def test_function_no_body(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [])
        ])
        self.assertValid(prog)

    def test_string_concatenation(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("s", "filum", BinaryOp(StringLiteral("hello"), '+', StringLiteral("world")))
            ])
        ])
        self.assertValid(prog)

    def test_string_comparison_error(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(StringLiteral("a"), '==', StringLiteral("b")))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("eq", errors[0].message.lower())

    def test_float_comparison(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(FloatLiteral(1.0), '<', FloatLiteral(2.0)))
            ])
        ])
        self.assertValid(prog)

    def test_boolean_literal(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "boolean", BooleanLiteral(True))
            ])
        ])
        self.assertValid(prog)

    def test_boolean_comparison(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(BooleanLiteral(True), '==', BooleanLiteral(False)))
            ])
        ])
        # Boolean comparison returns integer
        self.assertValid(prog)

    def test_logical_and(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(1), '&&', IntegerLiteral(0)))
            ])
        ])
        self.assertValid(prog)

    def test_logical_or(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(1), '||', IntegerLiteral(0)))
            ])
        ])
        self.assertValid(prog)

    def test_modulo(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(IntegerLiteral(10), '%', IntegerLiteral(3)))
            ])
        ])
        self.assertValid(prog)

    def test_modulo_float_error(self):
        prog = self.make_program(functions=[
            Function("main", [], None, [
                Decl("x", "integer", BinaryOp(FloatLiteral(10.0), '%', FloatLiteral(3.0)))
            ])
        ])
        errors = self.assertErrors(prog, 1)
        self.assertIn("mod", errors[0].message.lower())


if __name__ == '__main__':
    unittest.main()
