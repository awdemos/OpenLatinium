use crate::lexer::SpannedToken;

#[derive(Debug, Clone, PartialEq)]
pub struct Program {
    pub functions: Vec<Function>,
    pub globals: Vec<VarDecl>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Function {
    pub name: String,
    pub params: Vec<Param>,
    pub return_type: Option<Type>,
    pub body: Vec<Stmt>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Param {
    pub name: String,
    pub ty: Type,
}

#[derive(Debug, Clone, PartialEq)]
pub struct VarDecl {
    pub name: String,
    pub ty: Type,
    pub init: Option<Expr>,
    pub size: Option<Expr>,
    pub is_const: bool,
}

#[derive(Debug, Clone, PartialEq)]
pub enum Type {
    Integer,
    Float,
    Filum,
    Boolean,
    Vec(Box<Type>),
    Ptr(Box<Type>),
    Named(String),
}

#[derive(Debug, Clone, PartialEq)]
pub enum Stmt {
    VarDecl(VarDecl),
    Assign(Assign),
    If(If),
    While(While),
    For(For),
    DoWhile(DoWhile),
    Match(Match),
    Break,
    Continue,
    Return(Option<Expr>),
    Expr(Expr),
}

#[derive(Debug, Clone, PartialEq)]
pub struct Assign {
    pub target: Expr,
    pub value: Expr,
}

#[derive(Debug, Clone, PartialEq)]
pub struct If {
    pub cond: Expr,
    pub then_branch: Vec<Stmt>,
    pub else_branch: Option<Vec<Stmt>>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct While {
    pub cond: Expr,
    pub body: Vec<Stmt>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct For {
    pub init: Option<Box<Stmt>>,
    pub cond: Option<Expr>,
    pub update: Option<Box<Stmt>>,
    pub body: Vec<Stmt>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct DoWhile {
    pub body: Vec<Stmt>,
    pub cond: Expr,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Match {
    pub expr: Expr,
    pub cases: Vec<MatchCase>,
    pub default: Option<Vec<Stmt>>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct MatchCase {
    pub value: Expr,
    pub body: Vec<Stmt>,
}

#[derive(Debug, Clone, PartialEq)]
pub enum Expr {
    IntLit(i64),
    FloatLit(f32),
    StringLit(String),
    BoolLit(bool),
    Ident(String),
    Binary(BinaryOp, Box<Expr>, Box<Expr>),
    Unary(UnaryOp, Box<Expr>),
    Call(String, Vec<Expr>),
    ArrayIndex(Box<Expr>, Box<Expr>),
    ArrayInit(Vec<Expr>),
    ArrayRange(Box<Expr>, Box<Expr>),
    Ref(Box<Expr>),
    Deref(Box<Expr>),
    Read(ReadType),
}

#[derive(Debug, Clone, PartialEq)]
pub enum BinaryOp {
    Add, Sub, Mul, Div, Mod,
    Eq, Ne, Lt, Gt, Le, Ge,
    And, Or,
}

#[derive(Debug, Clone, PartialEq)]
pub enum UnaryOp {
    Neg, Not,
}

#[derive(Debug, Clone, PartialEq)]
pub enum ReadType {
    Int,
    Float,
    String,
}
