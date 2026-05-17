//! OpenLatinum lexer
//!
//! Tokenizes `.lat` source code into a stream of [`Token`]s.

use std::fmt;

/// A token in the OpenLatinum language.
#[derive(Debug, Clone, PartialEq)]
pub enum Token {
    // Keywords
    Munus,      // function
    Reditus,    // return
    Si,         // if
    Aliter,     // else
    Dum,        // while
    Enim,       // for
    Facio,      // do-while
    Par,        // match
    Defectus,   // default
    Confractus, // break
    Perge,      // continue
    Et,         // and
    Aut,        // or
    Non,        // not
    Imprimo,    // print
    Legerei,    // read int
    Legeref,    // read float
    Legeres,    // read string
    Verum,      // true
    Falsum,     // false
    Constans,   // const

    // Types
    Integer,
    Float,
    Filum,
    Boolean,
    Vec,

    // Literals
    IntLit(i64),
    FloatLit(f32),
    StringLit(String),

    // Identifiers
    Ident(String),

    // Operators
    Plus,
    Minus,
    Star,
    Slash,
    Percent,
    EqEq,
    NotEq,
    Lt,
    Gt,
    LtEq,
    GtEq,
    Eq,
    Arrow,      // ->
    FatArrow,   // =>
    Ampersand,  // &

    // Delimiters
    LParen,
    RParen,
    LBrace,
    RBrace,
    LBracket,
    RBracket,
    Comma,
    Semi,
    Colon,

    // Special
    Eof,
    Newline,
}

impl fmt::Display for Token {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Token::Munus => write!(f, "munus"),
            Token::Reditus => write!(f, "reditus"),
            Token::Si => write!(f, "si"),
            Token::Aliter => write!(f, "aliter"),
            Token::Dum => write!(f, "dum"),
            Token::Enim => write!(f, "enim"),
            Token::Facio => write!(f, "facio"),
            Token::Par => write!(f, "par"),
            Token::Defectus => write!(f, "defectus"),
            Token::Confractus => write!(f, "confractus"),
            Token::Perge => write!(f, "perge"),
            Token::Et => write!(f, "et"),
            Token::Aut => write!(f, "aut"),
            Token::Non => write!(f, "non"),
            Token::Imprimo => write!(f, "imprimo"),
            Token::Legerei => write!(f, "legerei"),
            Token::Legeref => write!(f, "legeref"),
            Token::Legeres => write!(f, "legeres"),
            Token::Verum => write!(f, "verum"),
            Token::Falsum => write!(f, "falsum"),
            Token::Constans => write!(f, "constans"),
            Token::Integer => write!(f, "integer"),
            Token::Float => write!(f, "float"),
            Token::Filum => write!(f, "filum"),
            Token::Boolean => write!(f, "boolean"),
            Token::Vec => write!(f, "vec"),
            Token::IntLit(n) => write!(f, "{}", n),
            Token::FloatLit(n) => write!(f, "{}", n),
            Token::StringLit(s) => write!(f, "\"{}\"", s),
            Token::Ident(s) => write!(f, "{}", s),
            Token::Plus => write!(f, "+"),
            Token::Minus => write!(f, "-"),
            Token::Star => write!(f, "*"),
            Token::Slash => write!(f, "/"),
            Token::Percent => write!(f, "%"),
            Token::EqEq => write!(f, "=="),
            Token::NotEq => write!(f, "!="),
            Token::Lt => write!(f, "<"),
            Token::Gt => write!(f, ">"),
            Token::LtEq => write!(f, "<="),
            Token::GtEq => write!(f, ">="),
            Token::Eq => write!(f, "="),
            Token::Arrow => write!(f, "->"),
            Token::FatArrow => write!(f, "=>"),
            Token::Ampersand => write!(f, "&"),
            Token::LParen => write!(f, "("),
            Token::RParen => write!(f, ")"),
            Token::LBrace => write!(f, "{{"),
            Token::RBrace => write!(f, "}}"),
            Token::LBracket => write!(f, "["),
            Token::RBracket => write!(f, "]"),
            Token::Comma => write!(f, ","),
            Token::Semi => write!(f, ";"),
            Token::Colon => write!(f, ":"),
            Token::Eof => write!(f, "<EOF>"),
            Token::Newline => write!(f, "<NL>"),
        }
    }
}

/// Lexical error.
#[derive(Debug, Clone, PartialEq)]
pub enum LexError {
    UnexpectedChar(char, usize, usize),
    UnterminatedString(usize, usize),
    InvalidNumber(String, usize, usize),
}

impl fmt::Display for LexError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            LexError::UnexpectedChar(c, line, col) => {
                write!(f, "Unexpected character '{}' at {}:{}", c, line, col)
            }
            LexError::UnterminatedString(line, col) => {
                write!(f, "Unterminated string at {}:{}", line, col)
            }
            LexError::InvalidNumber(s, line, col) => {
                write!(f, "Invalid number '{}' at {}:{}", s, line, col)
            }
        }
    }
}

impl std::error::Error for LexError {}

/// A token with its position in the source.
#[derive(Debug, Clone, PartialEq)]
pub struct SpannedToken {
    pub token: Token,
    pub line: usize,
    pub col: usize,
}

/// The OpenLatinum lexer.
#[derive(Clone)]
pub struct Lexer<'a> {
    source: &'a str,
    pub(crate) chars: std::str::Chars<'a>,
    line: usize,
    col: usize,
    pub(crate) current: Option<char>,
}

impl<'a> Lexer<'a> {
    pub fn new(source: &'a str) -> Self {
        let mut chars = source.chars();
        let current = chars.next();
        Self {
            source,
            chars,
            line: 1,
            col: 1,
            current,
        }
    }

    fn advance(&mut self) -> Option<char> {
        let ch = self.current;
        self.current = self.chars.next();
        if let Some(c) = ch {
            if c == '\n' {
                self.line += 1;
                self.col = 1;
            } else {
                self.col += 1;
            }
        }
        ch
    }

    fn peek(&self) -> Option<char> {
        self.current
    }

    fn skip_whitespace(&mut self) {
        while let Some(c) = self.peek() {
            if c.is_whitespace() && c != '\n' {
                self.advance();
            } else {
                break;
            }
        }
    }

    fn skip_comment(&mut self) {
        if self.peek() == Some('/') && self.chars.clone().next() == Some('/') {
            while let Some(c) = self.peek() {
                if c == '\n' {
                    break;
                }
                self.advance();
            }
        }
    }

    pub fn next_token(&mut self) -> Result<SpannedToken, LexError> {
        loop {
            self.skip_whitespace();
            self.skip_comment();
            self.skip_whitespace();

            let line = self.line;
            let col = self.col;

            match self.peek() {
                None => return Ok(SpannedToken { token: Token::Eof, line, col }),
                Some('\n') => {
                    self.advance();
                    return Ok(SpannedToken { token: Token::Newline, line, col });
                }
                Some('+') => { self.advance(); return Ok(SpannedToken { token: Token::Plus, line, col }); }
                Some('-') => {
                    self.advance();
                    if self.peek() == Some('>') {
                        self.advance();
                        return Ok(SpannedToken { token: Token::Arrow, line, col });
                    }
                    return Ok(SpannedToken { token: Token::Minus, line, col });
                }
                Some('*') => { self.advance(); return Ok(SpannedToken { token: Token::Star, line, col }); }
                Some('/') => { self.advance(); return Ok(SpannedToken { token: Token::Slash, line, col }); }
                Some('%') => { self.advance(); return Ok(SpannedToken { token: Token::Percent, line, col }); }
                Some('(') => { self.advance(); return Ok(SpannedToken { token: Token::LParen, line, col }); }
                Some(')') => { self.advance(); return Ok(SpannedToken { token: Token::RParen, line, col }); }
                Some('{') => { self.advance(); return Ok(SpannedToken { token: Token::LBrace, line, col }); }
                Some('}') => { self.advance(); return Ok(SpannedToken { token: Token::RBrace, line, col }); }
                Some('[') => { self.advance(); return Ok(SpannedToken { token: Token::LBracket, line, col }); }
                Some(']') => { self.advance(); return Ok(SpannedToken { token: Token::RBracket, line, col }); }
                Some(',') => { self.advance(); return Ok(SpannedToken { token: Token::Comma, line, col }); }
                Some(';') => { self.advance(); return Ok(SpannedToken { token: Token::Semi, line, col }); }
                Some(':') => { self.advance(); return Ok(SpannedToken { token: Token::Colon, line, col }); }
                Some('&') => { self.advance(); return Ok(SpannedToken { token: Token::Ampersand, line, col }); }
                Some('=') => {
                    self.advance();
                    if self.peek() == Some('=') {
                        self.advance();
                        return Ok(SpannedToken { token: Token::EqEq, line, col });
                    } else if self.peek() == Some('>') {
                        self.advance();
                        return Ok(SpannedToken { token: Token::FatArrow, line, col });
                    }
                    return Ok(SpannedToken { token: Token::Eq, line, col });
                }
                Some('!') => {
                    self.advance();
                    if self.peek() == Some('=') {
                        self.advance();
                        return Ok(SpannedToken { token: Token::NotEq, line, col });
                    }
                    return Ok(SpannedToken { token: Token::Non, line, col });
                }
                Some('<') => {
                    self.advance();
                    if self.peek() == Some('=') {
                        self.advance();
                        return Ok(SpannedToken { token: Token::LtEq, line, col });
                    }
                    return Ok(SpannedToken { token: Token::Lt, line, col });
                }
                Some('>') => {
                    self.advance();
                    if self.peek() == Some('=') {
                        self.advance();
                        return Ok(SpannedToken { token: Token::GtEq, line, col });
                    }
                    return Ok(SpannedToken { token: Token::Gt, line, col });
                }
                Some('"') => return self.read_string(line, col),
                Some(c) if c.is_ascii_digit() => return self.read_number(line, col),
                Some(c) if c.is_alphabetic() || c == '_' => return self.read_identifier(line, col),
                Some(c) => {
                    self.advance();
                    return Err(LexError::UnexpectedChar(c, line, col));
                }
            }
        }
    }

    fn read_string(&mut self, line: usize, col: usize) -> Result<SpannedToken, LexError> {
        self.advance();
        let mut s = String::new();
        while let Some(c) = self.peek() {
            if c == '"' {
                self.advance();
                return Ok(SpannedToken { token: Token::StringLit(s), line, col });
            }
            if c == '\n' {
                return Err(LexError::UnterminatedString(line, col));
            }
            s.push(c);
            self.advance();
        }
        Err(LexError::UnterminatedString(line, col))
    }

    fn read_number(&mut self, line: usize, col: usize) -> Result<SpannedToken, LexError> {
        let mut s = String::new();
        while let Some(c) = self.peek() {
            if c.is_ascii_digit() {
                s.push(c);
                self.advance();
            } else {
                break;
            }
        }
        if self.peek() == Some('.') {
            s.push('.');
            self.advance();
            while let Some(c) = self.peek() {
                if c.is_ascii_digit() {
                    s.push(c);
                    self.advance();
                } else {
                    break;
                }
            }
            match s.parse::<f32>() {
                Ok(n) => Ok(SpannedToken { token: Token::FloatLit(n), line, col }),
                Err(_) => Err(LexError::InvalidNumber(s, line, col)),
            }
        } else {
            match s.parse::<i64>() {
                Ok(n) => Ok(SpannedToken { token: Token::IntLit(n), line, col }),
                Err(_) => Err(LexError::InvalidNumber(s, line, col)),
            }
        }
    }

    fn read_identifier(&mut self, line: usize, col: usize) -> Result<SpannedToken, LexError> {
        let mut s = String::new();
        while let Some(c) = self.peek() {
            if c.is_alphanumeric() || c == '_' {
                s.push(c);
                self.advance();
            } else {
                break;
            }
        }
        let token = match s.as_str() {
            "munus" => Token::Munus,
            "reditus" => Token::Reditus,
            "si" => Token::Si,
            "aliter" => Token::Aliter,
            "dum" => Token::Dum,
            "enim" => Token::Enim,
            "facio" => Token::Facio,
            "par" => Token::Par,
            "defectus" => Token::Defectus,
            "confractus" => Token::Confractus,
            "perge" => Token::Perge,
            "et" => Token::Et,
            "aut" => Token::Aut,
            "non" => Token::Non,
            "imprimo" => Token::Imprimo,
            "legerei" => Token::Legerei,
            "legeref" => Token::Legeref,
            "legeres" => Token::Legeres,
            "verum" => Token::Verum,
            "falsum" => Token::Falsum,
            "constans" => Token::Constans,
            "integer" => Token::Integer,
            "float" => Token::Float,
            "filum" => Token::Filum,
            "boolean" => Token::Boolean,
            "vec" => Token::Vec,
            _ => Token::Ident(s),
        };
        Ok(SpannedToken { token, line, col })
    }
}

/// Convenience: tokenize an entire source string.
pub fn tokenize(source: &str) -> Result<Vec<SpannedToken>, LexError> {
    let mut lexer = Lexer::new(source);
    let mut tokens = Vec::new();
    loop {
        let t = lexer.next_token()?;
        if t.token == Token::Eof {
            tokens.push(t);
            break;
        }
        tokens.push(t);
    }
    Ok(tokens)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lex_hello_world() {
        let source = r#"munus main() {
    imprimo("Hello, World!")
}"#;
        let tokens = tokenize(source).unwrap();
        let kinds: Vec<_> = tokens.iter().map(|t| t.token.clone()).collect();
        assert_eq!(kinds, vec![
            Token::Munus,
            Token::Ident("main".to_string()),
            Token::LParen,
            Token::RParen,
            Token::LBrace,
            Token::Newline,
            Token::Imprimo,
            Token::LParen,
            Token::StringLit("Hello, World!".to_string()),
            Token::RParen,
            Token::Newline,
            Token::RBrace,
            Token::Eof,
        ]);
    }

    #[test]
    fn lex_arithmetic() {
        let source = "x: integer = 42 + 3.14";
        let tokens = tokenize(source).unwrap();
        let kinds: Vec<_> = tokens.iter().map(|t| t.token.clone()).collect();
        assert_eq!(kinds, vec![
            Token::Ident("x".to_string()),
            Token::Colon,
            Token::Integer,
            Token::Eq,
            Token::IntLit(42),
            Token::Plus,
            Token::FloatLit(3.14),
            Token::Eof,
        ]);
    }

    #[test]
    fn lex_operators() {
        let source = "== != <= >= ->";
        let tokens = tokenize(source).unwrap();
        let kinds: Vec<_> = tokens.iter().map(|t| t.token.clone()).collect();
        assert_eq!(kinds, vec![
            Token::EqEq,
            Token::NotEq,
            Token::LtEq,
            Token::GtEq,
            Token::Arrow,
            Token::Eof,
        ]);
    }
}
