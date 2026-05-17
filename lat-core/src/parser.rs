use crate::ast::*;
use crate::lexer::{Lexer, SpannedToken, Token, LexError};

#[derive(Debug, Clone)]
pub struct ParseError {
    pub message: String,
    pub line: usize,
    pub col: usize,
}

impl std::fmt::Display for ParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Parse error at {}:{}: {}", self.line, self.col, self.message)
    }
}

impl std::error::Error for ParseError {}

#[derive(Clone)]
pub struct Parser<'a> {
    lexer: Lexer<'a>,
    current: SpannedToken,
}

impl<'a> Parser<'a> {
    pub fn new(source: &'a str) -> Result<Self, ParseError> {
        let mut lexer = Lexer::new(source);
        let current = lexer.next_token().map_err(|e| ParseError {
            message: e.to_string(),
            line: 0,
            col: 0,
        })?;
        Ok(Self { lexer, current })
    }

    pub fn save_checkpoint(&self) -> Self {
        self.clone()
    }

    pub fn restore_checkpoint(&mut self, checkpoint: Self) {
        *self = checkpoint;
    }

    fn advance(&mut self) -> Result<(), ParseError> {
        self.current = self.lexer.next_token().map_err(|e| ParseError {
            message: e.to_string(),
            line: self.current.line,
            col: self.current.col,
        })?;
        Ok(())
    }

    fn expect(&mut self, token: Token) -> Result<(), ParseError> {
        if self.current.token == token {
            self.advance()
        } else {
            Err(ParseError {
                message: format!("Expected '{}', got '{}'", token, self.current.token),
                line: self.current.line,
                col: self.current.col,
            })
        }
    }

    fn match_token(&mut self, token: Token) -> bool {
        if self.current.token == token {
            let _ = self.advance();
            true
        } else {
            false
        }
    }

    fn is_eof(&self) -> bool {
        self.current.token == Token::Eof
    }

    fn skip_newlines(&mut self) -> Result<(), ParseError> {
        while self.current.token == Token::Newline {
            self.advance()?;
        }
        Ok(())
    }

    pub fn parse(&mut self) -> Result<Program, ParseError> {
        let mut functions = Vec::new();
        let mut globals = Vec::new();

        self.skip_newlines()?;

        while !self.is_eof() {
            self.skip_newlines()?;
            if self.is_eof() {
                break;
            }
            if self.current.token == Token::Munus {
                functions.push(self.parse_function()?);
            } else {
                globals.push(self.parse_var_decl()?);
            }
        }

        Ok(Program { functions, globals })
    }

    fn parse_function(&mut self) -> Result<Function, ParseError> {
        self.expect(Token::Munus)?;
        let name = self.expect_ident()?;
        self.expect(Token::LParen)?;
        let params = self.parse_params()?;
        self.expect(Token::RParen)?;

        let return_type = if self.match_token(Token::Arrow) {
            Some(self.parse_type()?)
        } else {
            None
        };

        let body = self.parse_block()?;
        Ok(Function { name, params, return_type, body })
    }

    fn parse_params(&mut self) -> Result<Vec<Param>, ParseError> {
        let mut params = Vec::new();
        if self.current.token != Token::RParen {
            loop {
                let name = self.expect_ident()?;
                self.expect(Token::Colon)?;
                let ty = self.parse_type()?;
                params.push(Param { name, ty });
                if !self.match_token(Token::Comma) {
                    break;
                }
            }
        }
        Ok(params)
    }

    fn parse_block(&mut self) -> Result<Vec<Stmt>, ParseError> {
        self.expect(Token::LBrace)?;
        let mut stmts = Vec::new();
        while self.current.token != Token::RBrace && !self.is_eof() {
            self.skip_newlines()?;
            if self.current.token == Token::RBrace || self.is_eof() {
                break;
            }
            stmts.push(self.parse_stmt()?);
        }
        self.expect(Token::RBrace)?;
        Ok(stmts)
    }

    fn parse_stmt(&mut self) -> Result<Stmt, ParseError> {
        match &self.current.token {
            Token::Constans => {
                let mut decl = self.parse_var_decl()?;
                decl.is_const = true;
                Ok(Stmt::VarDecl(decl))
            }
            Token::Ident(name) if self.peek_is_colon() => {
                Ok(Stmt::VarDecl(self.parse_var_decl()?))
            }
            Token::Ident(_) => {
                let checkpoint = self.save_checkpoint();
                let target = self.parse_expr()?;
                if self.match_token(Token::Eq) {
                    let value = self.parse_expr()?;
                    Ok(Stmt::Assign(Assign { target, value }))
                } else {
                    self.restore_checkpoint(checkpoint);
                    let expr = self.parse_expr()?;
                    Ok(Stmt::Expr(expr))
                }
            }
            Token::Si => self.parse_if(),
            Token::Dum => self.parse_while(),
            Token::Enim => self.parse_for(),
            Token::Facio => self.parse_do_while(),
            Token::Par => self.parse_match(),
            Token::Confractus => {
                self.advance()?;
                Ok(Stmt::Break)
            }
            Token::Perge => {
                self.advance()?;
                Ok(Stmt::Continue)
            }
            Token::Reditus => self.parse_return(),
            Token::Imprimo => self.parse_print(),
            Token::Legerei | Token::Legeref | Token::Legeres => {
                let expr = self.parse_expr()?;
                Ok(Stmt::Expr(expr))
            }
            _ => {
                let expr = self.parse_expr()?;
                Ok(Stmt::Expr(expr))
            }
        }
    }

    fn parse_var_decl(&mut self) -> Result<VarDecl, ParseError> {
        if self.current.token == Token::Constans {
            self.advance()?;
        }
        let name = self.expect_ident()?;
        self.expect(Token::Colon)?;
        let ty = self.parse_type()?;
        let size = if self.match_token(Token::LBracket) {
            let s = self.parse_expr()?;
            self.expect(Token::RBracket)?;
            Some(s)
        } else {
            None
        };
        let init = if self.match_token(Token::Eq) {
            Some(self.parse_expr()?)
        } else {
            None
        };
        Ok(VarDecl { name, ty, init, size, is_const: false })
    }

    fn parse_type(&mut self) -> Result<Type, ParseError> {
        match &self.current.token {
            Token::Integer => { self.advance()?; Ok(Type::Integer) }
            Token::Float => { self.advance()?; Ok(Type::Float) }
            Token::Filum => { self.advance()?; Ok(Type::Filum) }
            Token::Boolean => { self.advance()?; Ok(Type::Boolean) }
            Token::Vec => {
                self.advance()?;
                self.expect(Token::Lt)?;
                let inner = self.parse_type()?;
                self.expect(Token::Gt)?;
                Ok(Type::Vec(Box::new(inner)))
            }
            Token::Ampersand => {
                self.advance()?;
                let inner = self.parse_type()?;
                Ok(Type::Ptr(Box::new(inner)))
            }
            Token::Ident(name) => {
                let n = name.clone();
                self.advance()?;
                Ok(Type::Named(n))
            }
            _ => Err(ParseError {
                message: format!("Expected type, got '{}'", self.current.token),
                line: self.current.line,
                col: self.current.col,
            }),
        }
    }

    fn parse_if(&mut self) -> Result<Stmt, ParseError> {
        self.expect(Token::Si)?;
        let cond = self.parse_expr()?;
        let then_branch = self.parse_block()?;
        let else_branch = if self.match_token(Token::Aliter) {
            Some(self.parse_block()?)
        } else {
            None
        };
        Ok(Stmt::If(If { cond, then_branch, else_branch }))
    }

    fn parse_while(&mut self) -> Result<Stmt, ParseError> {
        self.expect(Token::Dum)?;
        let cond = self.parse_expr()?;
        let body = self.parse_block()?;
        Ok(Stmt::While(While { cond, body }))
    }

    fn parse_for(&mut self) -> Result<Stmt, ParseError> {
        self.expect(Token::Enim)?;
        self.expect(Token::LParen)?;

        let init = if self.current.token == Token::Semi {
            None
        } else {
            if self.peek_is_colon() {
                Some(Box::new(Stmt::VarDecl(self.parse_var_decl()?)))
            } else {
                let target = self.parse_expr()?;
                self.expect(Token::Eq)?;
                let value = self.parse_expr()?;
                Some(Box::new(Stmt::Assign(Assign { target, value })))
            }
        };
        self.expect(Token::Semi)?;

        let cond = if self.current.token == Token::Semi {
            None
        } else {
            Some(self.parse_expr()?)
        };
        self.expect(Token::Semi)?;

        let update = if self.current.token == Token::RParen {
            None
        } else {
            let target = self.parse_expr()?;
            self.expect(Token::Eq)?;
            let value = self.parse_expr()?;
            Some(Box::new(Stmt::Assign(Assign { target, value })))
        };
        self.expect(Token::RParen)?;

        let body = self.parse_block()?;
        Ok(Stmt::For(For { init, cond, update, body }))
    }

    fn parse_do_while(&mut self) -> Result<Stmt, ParseError> {
        self.expect(Token::Facio)?;
        let body = self.parse_block()?;
        self.expect(Token::Dum)?;
        self.expect(Token::LParen)?;
        let cond = self.parse_expr()?;
        self.expect(Token::RParen)?;
        Ok(Stmt::DoWhile(DoWhile { body, cond }))
    }

    fn parse_match(&mut self) -> Result<Stmt, ParseError> {
        self.expect(Token::Par)?;
        self.expect(Token::LParen)?;
        let expr = self.parse_expr()?;
        self.expect(Token::RParen)?;
        self.expect(Token::LBrace)?;

        let mut cases = Vec::new();
        let mut default = None;

        while self.current.token != Token::RBrace && !self.is_eof() {
            self.skip_newlines()?;
            if self.current.token == Token::RBrace || self.is_eof() {
                break;
            }
            if self.match_token(Token::Defectus) {
                self.expect(Token::FatArrow)?;
                default = Some(self.parse_block()?);
            } else {
                let value = self.parse_expr()?;
                self.expect(Token::FatArrow)?;
                let body = self.parse_block()?;
                cases.push(MatchCase { value, body });
            }
        }

        self.expect(Token::RBrace)?;
        Ok(Stmt::Match(Match { expr, cases, default }))
    }

    fn parse_return(&mut self) -> Result<Stmt, ParseError> {
        self.expect(Token::Reditus)?;
        let value = if self.current.token == Token::Newline || self.current.token == Token::RBrace {
            None
        } else {
            Some(self.parse_expr()?)
        };
        Ok(Stmt::Return(value))
    }

    fn parse_print(&mut self) -> Result<Stmt, ParseError> {
        self.expect(Token::Imprimo)?;
        self.expect(Token::LParen)?;
        let mut args = Vec::new();
        if self.current.token != Token::RParen {
            loop {
                args.push(self.parse_expr()?);
                if !self.match_token(Token::Comma) {
                    break;
                }
            }
        }
        self.expect(Token::RParen)?;
        let call = Expr::Call("imprimo".to_string(), args);
        Ok(Stmt::Expr(call))
    }

    fn parse_expr(&mut self) -> Result<Expr, ParseError> {
        self.parse_or()
    }

    fn parse_or(&mut self) -> Result<Expr, ParseError> {
        let mut left = self.parse_and()?;
        while self.match_token(Token::Aut) {
            let right = self.parse_and()?;
            left = Expr::Binary(BinaryOp::Or, Box::new(left), Box::new(right));
        }
        Ok(left)
    }

    fn parse_and(&mut self) -> Result<Expr, ParseError> {
        let mut left = self.parse_equality()?;
        while self.match_token(Token::Et) {
            let right = self.parse_equality()?;
            left = Expr::Binary(BinaryOp::And, Box::new(left), Box::new(right));
        }
        Ok(left)
    }

    fn parse_equality(&mut self) -> Result<Expr, ParseError> {
        let mut left = self.parse_comparison()?;
        loop {
            if self.match_token(Token::EqEq) {
                let right = self.parse_comparison()?;
                left = Expr::Binary(BinaryOp::Eq, Box::new(left), Box::new(right));
            } else if self.match_token(Token::NotEq) {
                let right = self.parse_comparison()?;
                left = Expr::Binary(BinaryOp::Ne, Box::new(left), Box::new(right));
            } else {
                break;
            }
        }
        Ok(left)
    }

    fn parse_comparison(&mut self) -> Result<Expr, ParseError> {
        let mut left = self.parse_additive()?;
        loop {
            if self.match_token(Token::Lt) {
                let right = self.parse_additive()?;
                left = Expr::Binary(BinaryOp::Lt, Box::new(left), Box::new(right));
            } else if self.match_token(Token::Gt) {
                let right = self.parse_additive()?;
                left = Expr::Binary(BinaryOp::Gt, Box::new(left), Box::new(right));
            } else if self.match_token(Token::LtEq) {
                let right = self.parse_additive()?;
                left = Expr::Binary(BinaryOp::Le, Box::new(left), Box::new(right));
            } else if self.match_token(Token::GtEq) {
                let right = self.parse_additive()?;
                left = Expr::Binary(BinaryOp::Ge, Box::new(left), Box::new(right));
            } else {
                break;
            }
        }
        Ok(left)
    }

    fn parse_additive(&mut self) -> Result<Expr, ParseError> {
        let mut left = self.parse_multiplicative()?;
        loop {
            if self.match_token(Token::Plus) {
                let right = self.parse_multiplicative()?;
                left = Expr::Binary(BinaryOp::Add, Box::new(left), Box::new(right));
            } else if self.match_token(Token::Minus) {
                let right = self.parse_multiplicative()?;
                left = Expr::Binary(BinaryOp::Sub, Box::new(left), Box::new(right));
            } else {
                break;
            }
        }
        Ok(left)
    }

    fn parse_multiplicative(&mut self) -> Result<Expr, ParseError> {
        let mut left = self.parse_unary()?;
        loop {
            if self.match_token(Token::Star) {
                let right = self.parse_unary()?;
                left = Expr::Binary(BinaryOp::Mul, Box::new(left), Box::new(right));
            } else if self.match_token(Token::Slash) {
                let right = self.parse_unary()?;
                left = Expr::Binary(BinaryOp::Div, Box::new(left), Box::new(right));
            } else if self.match_token(Token::Percent) {
                let right = self.parse_unary()?;
                left = Expr::Binary(BinaryOp::Mod, Box::new(left), Box::new(right));
            } else {
                break;
            }
        }
        Ok(left)
    }

    fn parse_unary(&mut self) -> Result<Expr, ParseError> {
        if self.match_token(Token::Minus) {
            let expr = self.parse_unary()?;
            Ok(Expr::Unary(UnaryOp::Neg, Box::new(expr)))
        } else if self.match_token(Token::Non) {
            let expr = self.parse_unary()?;
            Ok(Expr::Unary(UnaryOp::Not, Box::new(expr)))
        } else {
            self.parse_postfix()
        }
    }

    fn parse_postfix(&mut self) -> Result<Expr, ParseError> {
        let mut expr = self.parse_primary()?;
        loop {
            if self.match_token(Token::LBracket) {
                let index = self.parse_expr()?;
                self.expect(Token::RBracket)?;
                expr = Expr::ArrayIndex(Box::new(expr), Box::new(index));
            } else {
                break;
            }
        }
        Ok(expr)
    }

    fn parse_primary(&mut self) -> Result<Expr, ParseError> {
        match &self.current.token {
            Token::IntLit(n) => {
                let v = *n;
                self.advance()?;
                Ok(Expr::IntLit(v))
            }
            Token::FloatLit(n) => {
                let v = *n;
                self.advance()?;
                Ok(Expr::FloatLit(v))
            }
            Token::StringLit(s) => {
                let v = s.clone();
                self.advance()?;
                Ok(Expr::StringLit(v))
            }
            Token::Verum => {
                self.advance()?;
                Ok(Expr::BoolLit(true))
            }
            Token::Falsum => {
                self.advance()?;
                Ok(Expr::BoolLit(false))
            }
            Token::Ident(name) => {
                let n = name.clone();
                self.advance()?;
                if self.match_token(Token::LParen) {
                    let mut args = Vec::new();
                    if self.current.token != Token::RParen {
                        loop {
                            args.push(self.parse_expr()?);
                            if !self.match_token(Token::Comma) {
                                break;
                            }
                        }
                    }
                    self.expect(Token::RParen)?;
                    Ok(Expr::Call(n, args))
                } else {
                    Ok(Expr::Ident(n))
                }
            }
            Token::LParen => {
                self.advance()?;
                let expr = self.parse_expr()?;
                self.expect(Token::RParen)?;
                Ok(expr)
            }
            Token::LBracket => {
                self.advance()?;
                let mut items = Vec::new();
                if self.current.token != Token::RBracket {
                    loop {
                        items.push(self.parse_expr()?);
                        if !self.match_token(Token::Comma) {
                            break;
                        }
                    }
                }
                self.expect(Token::RBracket)?;
                Ok(Expr::ArrayInit(items))
            }
            Token::Ampersand => {
                self.advance()?;
                let expr = self.parse_primary()?;
                Ok(Expr::Ref(Box::new(expr)))
            }
            Token::Legerei => {
                self.advance()?;
                if self.current.token == Token::LParen {
                    self.advance()?;
                    self.expect(Token::RParen)?;
                }
                Ok(Expr::Read(ReadType::Int))
            }
            Token::Legeref => {
                self.advance()?;
                if self.current.token == Token::LParen {
                    self.advance()?;
                    self.expect(Token::RParen)?;
                }
                Ok(Expr::Read(ReadType::Float))
            }
            Token::Legeres => {
                self.advance()?;
                if self.current.token == Token::LParen {
                    self.advance()?;
                    self.expect(Token::RParen)?;
                }
                Ok(Expr::Read(ReadType::String))
            }
            _ => Err(ParseError {
                message: format!("Unexpected token '{}' in expression", self.current.token),
                line: self.current.line,
                col: self.current.col,
            }),
        }
    }

    fn expect_ident(&mut self) -> Result<String, ParseError> {
        match &self.current.token {
            Token::Ident(name) => {
                let n = name.clone();
                self.advance()?;
                Ok(n)
            }
            _ => Err(ParseError {
                message: format!("Expected identifier, got '{}'", self.current.token),
                line: self.current.line,
                col: self.current.col,
            }),
        }
    }

    fn peek_is_colon(&self) -> bool {
        let mut chars = self.lexer.chars.clone();
        let mut current = self.lexer.current;
        let mut found_colon = false;
        while let Some(c) = current {
            if c.is_whitespace() {
                current = chars.next();
            } else if c == ':' {
                found_colon = true;
                break;
            } else {
                break;
            }
        }
        found_colon
    }

    fn peek_is_eq(&self) -> bool {
        let mut chars = self.lexer.chars.clone();
        let mut current = self.lexer.current;
        let mut found_eq = false;
        while let Some(c) = current {
            if c.is_whitespace() {
                current = chars.next();
            } else if c == '=' {
                found_eq = true;
                break;
            } else {
                break;
            }
        }
        found_eq
    }
}

pub fn parse(source: &str) -> Result<Program, ParseError> {
    let mut parser = Parser::new(source)?;
    parser.parse()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_hello_world() {
        let source = r#"munus main() {
    imprimo("Hello, World!")
}"#;
        let prog = parse(source).unwrap();
        assert_eq!(prog.functions.len(), 1);
        assert_eq!(prog.functions[0].name, "main");
        assert!(prog.functions[0].return_type.is_none());
        assert_eq!(prog.functions[0].body.len(), 1);
    }

    #[test]
    fn parse_variable_decl() {
        let source = "x: integer = 42";
        let prog = parse(source).unwrap();
        assert_eq!(prog.globals.len(), 1);
        assert_eq!(prog.globals[0].name, "x");
        assert_eq!(prog.globals[0].ty, Type::Integer);
    }

    #[test]
    fn parse_function_with_params() {
        let source = r#"munus add(a: integer, b: integer) -> integer {
    reditus a + b
}"#;
        let prog = parse(source).unwrap();
        assert_eq!(prog.functions[0].name, "add");
        assert_eq!(prog.functions[0].params.len(), 2);
        assert_eq!(prog.functions[0].return_type, Some(Type::Integer));
    }

    #[test]
    fn parse_if_else() {
        let source = r#"munus main() {
    si x > 0 {
        imprimo("positive")
    } aliter {
        imprimo("non-positive")
    }
}"#;
        let prog = parse(source).unwrap();
        assert_eq!(prog.functions.len(), 1);
        assert_eq!(prog.globals.len(), 0);
    }
}
