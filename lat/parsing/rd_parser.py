from lat.ast.nodes import *
from lat.parsing.tokenizer import Token


class ParseError(Exception):
    def __init__(self, msg: str, line: int = 0, column: int = 0):
        self.msg = msg
        self.line = line
        self.column = column
        super().__init__(f"{msg} at line {line}, column {column}")


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def advance(self) -> Token:
        tok = self.peek()
        self.pos += 1
        return tok

    def expect(self, *types: str) -> Token:
        tok = self.peek()
        if tok.type not in types:
            types_str = " or ".join(types)
            raise ParseError(f"Expected {types_str} but found '{tok.value}'", tok.line, tok.column)
        return self.advance()

    def match(self, *types: str) -> bool:
        return self.peek().type in types

    def consume(self, *types: str) -> Token | None:
        if self.match(*types):
            return self.advance()
        return None

    def parse(self) -> Program:
        globals_list = []
        while self.match("CONST", "ID") and self._is_global_decl():
            globals_list.append(self.parse_global())
        functions = []
        while not self.match("EOF"):
            functions.append(self.parse_function())
        return Program(globals=globals_list, functions=functions)

    def _is_global_decl(self) -> bool:
        idx = 0
        if self.peek(idx).type == "CONST":
            idx += 1
        if self.peek(idx).type != "ID":
            return False
        idx += 1
        return self.peek(idx).type == "COLON"

    def parse_global(self) -> Decl:
        is_const = self.consume("CONST") is not None
        name = self.expect("ID").value
        self.expect("COLON")
        type_str = self.parse_type()
        if self.consume("ASSIGN"):
            value = self.parse_expr()
            return Decl(name=name, type=type_str, value=value, is_const=is_const)
        if "vec<" in type_str and self.consume("LBRACKET"):
            dims = []
            while True:
                dims.append(int(self.expect("INTEGER").value))
                self.expect("RBRACKET")
                if not self.consume("LBRACKET"):
                    break
            return Decl(name=name, type=type_str + "".join(f"[{d}]" for d in dims), is_const=is_const)
        return Decl(name=name, type=type_str, is_const=is_const)

    def parse_function(self) -> Function:
        self.expect("FUNCTION")
        name = self.expect("ID").value
        self.expect("LPAREN")
        params = self.parse_params()
        self.expect("RPAREN")
        return_type = None
        if self.consume("RARROW"):
            return_type = self.parse_type()
        self.expect("LBRACE")
        body = self.parse_stmts()
        self.expect("RBRACE")
        return Function(name=name, params=params, return_type=return_type, body=body)

    def parse_params(self) -> list[Param]:
        params = []
        if not self.match("RPAREN"):
            params.append(self.parse_param())
            while self.consume("COMMA"):
                params.append(self.parse_param())
        return params

    def parse_param(self) -> Param:
        name = self.expect("ID").value
        self.expect("COLON")
        type_str = self.parse_type()
        return Param(name=name, type=type_str)

    def parse_type(self) -> str:
        if self.consume("AMPERSAND"):
            return "&" + self.parse_type()
        if self.consume("TYPE_VEC"):
            self.expect("LT")
            inner = self.parse_type()
            self.expect("GT")
            return f"vec<{inner}>"
        tok = self.consume("TYPE_INT", "TYPE_STRING", "TYPE_FLOAT", "TYPE_BOOL")
        if tok:
            return tok.value
        raise ParseError(f"Expected type but found '{self.peek().value}'", self.peek().line, self.peek().column)

    def parse_stmts(self) -> list[Stmt]:
        stmts = []
        while not self.match("RBRACE", "EOF"):
            stmts.append(self.parse_stmt())
        return stmts

    def parse_stmt(self) -> Stmt:
        if self.match("PRINT"):
            return self.parse_print()
        if self.match("READ_INT", "READ_FLOAT", "READ_STRING"):
            return self.parse_read()
        if self.match("IF"):
            return self.parse_if()
        if self.match("MATCH"):
            return self.parse_match()
        if self.match("WHILE"):
            return self.parse_while()
        if self.match("FOR"):
            return self.parse_for()
        if self.match("DO"):
            return self.parse_do_while()
        if self.match("BREAK"):
            self.advance()
            return Break()
        if self.match("CONTINUE"):
            self.advance()
            return Continue()
        if self.match("RETURN"):
            return self.parse_return()
        if self.match("CONST"):
            return self.parse_decl_or_assign()
        if self.match("ID"):
            if self._is_assignment():
                return self.parse_assignment()
            if self._is_declaration():
                return self.parse_decl_or_assign()
            expr = self.parse_expr()
            if isinstance(expr, FunctionCall):
                return expr
            raise ParseError(f"Expected function call, assignment, or declaration", self.peek().line, self.peek().column)
        raise ParseError(f"Unexpected token '{self.peek().value}'", self.peek().line, self.peek().column)

    def _is_assignment(self) -> bool:
        idx = 0
        if self.peek(idx).type == "CONST":
            idx += 1
        if self.peek(idx).type != "ID":
            return False
        idx += 1
        while self.peek(idx).type == "LBRACKET":
            idx += 1
            bracket_depth = 1
            while bracket_depth > 0 and idx < len(self.tokens):
                if self.peek(idx).type == "LBRACKET":
                    bracket_depth += 1
                elif self.peek(idx).type == "RBRACKET":
                    bracket_depth -= 1
                idx += 1
        return self.peek(idx).type == "ASSIGN"

    def _is_declaration(self) -> bool:
        idx = 0
        if self.peek(idx).type == "CONST":
            idx += 1
        if self.peek(idx).type != "ID":
            return False
        idx += 1
        return self.peek(idx).type == "COLON"

    def parse_print(self) -> Print:
        self.expect("PRINT")
        self.expect("LPAREN")
        exprs = self.parse_expr_list()
        self.expect("RPAREN")
        return Print(expressions=exprs)

    def parse_read(self) -> Read:
        tok = self.advance()
        self.expect("LPAREN")
        exprs = self.parse_expr_list()
        self.expect("RPAREN")
        return Read(read_type=tok.type, expressions=exprs)

    def parse_expr_list(self) -> list[Expr]:
        exprs = []
        if not self.match("RPAREN"):
            exprs.append(self.parse_expr())
            while self.consume("COMMA"):
                exprs.append(self.parse_expr())
        return exprs

    def parse_if(self) -> If:
        self.expect("IF")
        cond = self.parse_expr()
        self.expect("LBRACE")
        then_body = self.parse_stmts()
        self.expect("RBRACE")
        else_body = None
        while self.consume("ELSE"):
            if self.consume("IF"):
                elif_cond = self.parse_expr()
                self.expect("LBRACE")
                elif_body = self.parse_stmts()
                self.expect("RBRACE")
                else_body = If(condition=elif_cond, then_body=elif_body, else_body=else_body)
            else:
                self.expect("LBRACE")
                else_stmts = self.parse_stmts()
                self.expect("RBRACE")
                else_body = else_stmts
                break
        return If(condition=cond, then_body=then_body, else_body=else_body)

    def parse_match(self) -> Match:
        self.expect("MATCH")
        expr_val = self.parse_expr()
        self.expect("LBRACE")
        cases = []
        while not self.match("DEFAULT", "RBRACE"):
            case_val = self.parse_expr()
            self.expect("RARROW")
            self.expect("LBRACE")
            case_body = self.parse_stmts()
            self.expect("RBRACE")
            cases.append(Case(value=case_val, body=case_body))
        if self.consume("DEFAULT"):
            self.expect("RARROW")
            self.expect("LBRACE")
            default_body = self.parse_stmts()
            self.expect("RBRACE")
            cases.append(Default(body=default_body))
        self.expect("RBRACE")
        return Match(expression=expr_val, cases=cases)

    def parse_while(self) -> While:
        self.expect("WHILE")
        cond = self.parse_expr()
        self.expect("LBRACE")
        body = self.parse_stmts()
        self.expect("RBRACE")
        return While(condition=cond, body=body)

    def parse_do_while(self) -> DoWhile:
        self.expect("DO")
        self.expect("LBRACE")
        body = self.parse_stmts()
        self.expect("RBRACE")
        self.expect("WHILE")
        self.expect("LPAREN")
        cond = self.parse_expr()
        self.expect("RPAREN")
        return DoWhile(condition=cond, body=body)

    def parse_for(self) -> For:
        self.expect("FOR")
        self.expect("LPAREN")
        inits = []
        if not self.match("SEMICOLON"):
            inits.append(self.parse_for_init())
            while self.consume("COMMA"):
                inits.append(self.parse_for_init())
        self.expect("SEMICOLON")
        cond = self.parse_expr()
        self.expect("SEMICOLON")
        updates = []
        if not self.match("RPAREN"):
            updates.append(self.parse_assignment())
            while self.consume("COMMA"):
                updates.append(self.parse_assignment())
        self.expect("RPAREN")
        self.expect("LBRACE")
        body = self.parse_stmts()
        self.expect("RBRACE")
        return For(init=inits, condition=cond, update=updates, body=body)

    def parse_for_init(self) -> Decl | Assignment:
        saved_pos = self.pos
        is_const = self.consume("CONST") is not None
        if not self.match("ID"):
            self.pos = saved_pos
            raise ParseError(f"Expected identifier in for init", self.peek().line, self.peek().column)
        name = self.advance().value
        if not self.match("COLON"):
            self.pos = saved_pos
            return self.parse_assignment()
        self.advance()
        type_str = self.parse_type()
        if self.consume("ASSIGN"):
            value = self.parse_expr()
            return Decl(name=name, type=type_str, value=value, is_const=is_const)
        return Decl(name=name, type=type_str, is_const=is_const)

    def parse_return(self) -> Return:
        self.expect("RETURN")
        if self.consume("SEMICOLON"):
            return Return()
        value = self.parse_expr()
        return Return(value=value)

    def parse_decl_or_assign(self) -> Decl:
        is_const = self.consume("CONST") is not None
        name = self.expect("ID").value
        self.expect("COLON")
        type_str = self.parse_type()
        if self.consume("ASSIGN"):
            if "vec<" in type_str and self.match("LBRACKET"):
                return self._parse_vec_init(name, type_str, is_const)
            value = self.parse_expr()
            return Decl(name=name, type=type_str, value=value, is_const=is_const)
        if "vec<" in type_str:
            dims = []
            while self.consume("LBRACKET"):
                dims.append(int(self.expect("INTEGER").value))
                self.expect("RBRACKET")
            if dims:
                type_str = type_str + "".join(f"[{d}]" for d in dims)
            if self.consume("ASSIGN"):
                return self._parse_vec_init(name, type_str, is_const)
        return Decl(name=name, type=type_str, is_const=is_const)

    def _parse_vec_init(self, name: str, type_str: str, is_const: bool) -> Decl:
        self.expect("LBRACKET")
        items = []
        if not self.match("RBRACKET"):
            first_expr = self.parse_expr()
            if self.consume("RETI"):
                second_expr = self.parse_expr()
                self.expect("RBRACKET")
                return Decl(name=name, type=type_str, value=ArrayRange(start=first_expr, end=second_expr), is_const=is_const)
            items.append(first_expr)
            while self.consume("COMMA"):
                items.append(self.parse_expr())
        self.expect("RBRACKET")
        return Decl(name=name, type=type_str, value=ArrayLiteral(items=items), is_const=is_const)

    def parse_assignment(self) -> Assignment:
        name = self.expect("ID").value
        indices = []
        while self.consume("LBRACKET"):
            indices.append(self.parse_expr())
            self.expect("RBRACKET")
        self.expect("ASSIGN")
        value = self.parse_expr()
        target = ArrayIndex(name=name, indices=indices) if indices else Identifier(name=name)
        return Assignment(target=target, value=value)

    def parse_expr(self) -> Expr:
        return self.parse_or()

    def parse_or(self) -> Expr:
        left = self.parse_and()
        while self.consume("OR"):
            right = self.parse_and()
            left = BinaryOp(left=left, op="||", right=right)
        return left

    def parse_and(self) -> Expr:
        left = self.parse_eq()
        while self.consume("AND"):
            right = self.parse_eq()
            left = BinaryOp(left=left, op="&&", right=right)
        return left

    def parse_eq(self) -> Expr:
        left = self.parse_comp()
        while True:
            tok = self.consume("EQ", "NEQ")
            if not tok:
                break
            right = self.parse_comp()
            left = BinaryOp(left=left, op=tok.value, right=right)
        return left

    def parse_comp(self) -> Expr:
        left = self.parse_add()
        while True:
            tok = self.consume("LT", "GT", "LTE", "GTE")
            if not tok:
                break
            right = self.parse_add()
            left = BinaryOp(left=left, op=tok.value, right=right)
        return left

    def parse_add(self) -> Expr:
        left = self.parse_mul()
        while True:
            tok = self.consume("PLUS", "MINUS")
            if not tok:
                break
            right = self.parse_mul()
            left = BinaryOp(left=left, op=tok.value, right=right)
        return left

    def parse_mul(self) -> Expr:
        left = self.parse_unary()
        while True:
            tok = self.consume("STAR", "SLASH", "PERCENT")
            if not tok:
                break
            right = self.parse_unary()
            left = BinaryOp(left=left, op=tok.value, right=right)
        return left

    def parse_unary(self) -> Expr:
        if self.consume("NOT"):
            return UnaryOp(op="!", operand=self.parse_unary())
        if self.consume("MINUS"):
            return UnaryOp(op="-", operand=self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self) -> Expr:
        expr = self.parse_primary()
        while self.consume("LBRACKET"):
            idx = self.parse_expr()
            self.expect("RBRACKET")
            if isinstance(expr, Identifier):
                expr = ArrayIndex(name=expr.name, indices=[idx])
            elif isinstance(expr, ArrayIndex):
                expr.indices.append(idx)
            else:
                raise ParseError("Cannot index non-array", self.peek().line, self.peek().column)
        return expr

    def parse_primary(self) -> Expr:
        if self.consume("TRUE"):
            return BooleanLiteral(value=True)
        if self.consume("FALSE"):
            return BooleanLiteral(value=False)
        if self.consume("INTEGER"):
            return IntegerLiteral(value=int(self.peek(-1).value))
        if self.consume("FLOAT"):
            return FloatLiteral(value=float(self.peek(-1).value))
        if self.consume("STRING"):
            val = self.peek(-1).value
            return StringLiteral(value=val[1:-1])
        if self.consume("IF"):
            cond = self.parse_expr()
            self.expect("LBRACE")
            then_expr = self.parse_expr()
            self.expect("RBRACE")
            self.expect("ELSE")
            self.expect("LBRACE")
            else_expr = self.parse_expr()
            self.expect("RBRACE")
            return IfExpr(condition=cond, then_expr=then_expr, else_expr=else_expr)
        if self.consume("AMPERSAND"):
            name = self.expect("ID").value
            return Ref(name=name)
        if self.match("READ_INT", "READ_FLOAT", "READ_STRING"):
            return self.parse_read()
        if self.match("ID"):
            name = self.advance().value
            if self.match("LPAREN"):
                self.advance()
                args = self.parse_expr_list()
                self.expect("RPAREN")
                return FunctionCall(name=name, args=args)
            return Identifier(name=name)
        if self.consume("LBRACKET"):
            items = []
            if not self.match("RBRACKET"):
                items.append(self.parse_expr())
                while self.consume("COMMA"):
                    items.append(self.parse_expr())
            self.expect("RBRACKET")
            return ArrayLiteral(items=items)
        if self.consume("LPAREN"):
            expr = self.parse_expr()
            self.expect("RPAREN")
            return expr
        raise ParseError(f"Unexpected token '{self.peek().value}' in expression", self.peek().line, self.peek().column)


def parse_tokens(tokens: list[Token]) -> Program:
    parser = Parser(tokens)
    return parser.parse()


def parse_file(path: str) -> Program:
    from lat.parsing.tokenizer import tokenize_file
    return parse_tokens(tokenize_file(path))


def parse_text(text: str) -> Program:
    from lat.parsing.tokenizer import tokenize
    return parse_tokens(list(tokenize(text)))
