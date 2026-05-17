use crate::ast::*;
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct SemanticError {
    pub message: String,
    pub line: usize,
    pub col: usize,
}

#[derive(Debug, Clone)]
struct VarInfo {
    name: String,
    ty: Type,
    is_initialized: bool,
}

#[derive(Debug, Clone)]
struct FuncInfo {
    name: String,
    params: Vec<Type>,
    return_type: Option<Type>,
}

#[derive(Debug, Clone)]
struct Scope {
    vars: HashMap<String, VarInfo>,
}

pub struct SemanticAnalyzer {
    scopes: Vec<Scope>,
    functions: HashMap<String, FuncInfo>,
    errors: Vec<SemanticError>,
    in_loop: bool,
    current_function: Option<String>,
}

impl SemanticAnalyzer {
    pub fn new() -> Self {
        Self {
            scopes: Vec::new(),
            functions: HashMap::new(),
            errors: Vec::new(),
            in_loop: false,
            current_function: None,
        }
    }

    pub fn analyze(&mut self, program: &Program) -> Vec<SemanticError> {
        self.errors.clear();
        self.scopes.clear();
        self.functions.clear();

        for func in &program.functions {
            self.declare_function(func);
        }

        self.push_scope();
        for decl in &program.globals {
            self.visit_var_decl(decl);
        }

        for func in &program.functions {
            self.visit_function(func);
        }
        self.pop_scope();

        self.errors.clone()
    }

    fn push_scope(&mut self) {
        self.scopes.push(Scope { vars: HashMap::new() });
    }

    fn pop_scope(&mut self) {
        self.scopes.pop();
    }

    fn define_var(&mut self, name: &str, ty: Type, is_initialized: bool) {
        if let Some(scope) = self.scopes.last_mut() {
            scope.vars.insert(name.to_string(), VarInfo {
                name: name.to_string(),
                ty,
                is_initialized,
            });
        }
    }

    fn lookup_var(&self, name: &str) -> Option<&VarInfo> {
        for scope in self.scopes.iter().rev() {
            if let Some(info) = scope.vars.get(name) {
                return Some(info);
            }
        }
        None
    }

    fn declare_function(&mut self, func: &Function) {
        if self.functions.contains_key(&func.name) {
            self.errors.push(SemanticError {
                message: format!("Function '{}' already defined", func.name),
                line: 0,
                col: 0,
            });
            return;
        }
        let params = func.params.iter().map(|p| p.ty.clone()).collect();
        self.functions.insert(func.name.clone(), FuncInfo {
            name: func.name.clone(),
            params,
            return_type: func.return_type.clone(),
        });
    }

    fn visit_function(&mut self, func: &Function) {
        self.current_function = Some(func.name.clone());
        self.push_scope();

        for param in &func.params {
            self.define_var(&param.name, param.ty.clone(), true);
        }

        for stmt in &func.body {
            self.visit_stmt(stmt);
        }

        self.pop_scope();
        self.current_function = None;
    }

    fn visit_stmt(&mut self, stmt: &Stmt) {
        match stmt {
            Stmt::VarDecl(decl) => self.visit_var_decl(decl),
            Stmt::Assign(assign) => self.visit_assign(assign),
            Stmt::If(if_stmt) => self.visit_if(if_stmt),
            Stmt::While(while_stmt) => self.visit_while(while_stmt),
            Stmt::For(for_stmt) => self.visit_for(for_stmt),
            Stmt::DoWhile(dw) => self.visit_do_while(dw),
            Stmt::Match(match_stmt) => self.visit_match(match_stmt),
            Stmt::Break => {
                if !self.in_loop {
                    self.errors.push(SemanticError {
                        message: "'confractus' outside of loop".to_string(),
                        line: 0,
                        col: 0,
                    });
                }
            }
            Stmt::Continue => {
                if !self.in_loop {
                    self.errors.push(SemanticError {
                        message: "'perge' outside of loop".to_string(),
                        line: 0,
                        col: 0,
                    });
                }
            }
            Stmt::Return(expr) => {
                if let Some(e) = expr {
                    self.visit_expr(e);
                }
            }
            Stmt::Expr(expr) => { self.visit_expr(expr); }
        }
    }

    fn visit_var_decl(&mut self, decl: &VarDecl) {
        if let Some(init) = &decl.init {
            let init_ty = self.visit_expr(init);
            if !self.types_compatible(&decl.ty, &init_ty) {
                self.errors.push(SemanticError {
                    message: format!("Type mismatch: expected '{:?}', got '{:?}'", decl.ty, init_ty),
                    line: 0,
                    col: 0,
                });
            }
        }
        self.define_var(&decl.name, decl.ty.clone(), decl.init.is_some());
    }

    fn visit_assign(&mut self, assign: &Assign) {
        self.visit_expr(&assign.value);
        match &assign.target {
            Expr::Ident(name) => {
                if self.lookup_var(name).is_none() {
                    self.errors.push(SemanticError {
                        message: format!("Undefined variable '{}'", name),
                        line: 0,
                        col: 0,
                    });
                }
            }
            Expr::ArrayIndex(arr, idx) => {
                self.visit_expr(arr);
                self.visit_expr(idx);
            }
            Expr::Deref(expr) => {
                self.visit_expr(expr);
            }
            _ => {
                self.errors.push(SemanticError {
                    message: "Invalid assignment target".to_string(),
                    line: 0,
                    col: 0,
                });
            }
        }
    }

    fn visit_if(&mut self, if_stmt: &If) {
        self.visit_expr(&if_stmt.cond);
        self.push_scope();
        for stmt in &if_stmt.then_branch {
            self.visit_stmt(stmt);
        }
        self.pop_scope();
        if let Some(else_branch) = &if_stmt.else_branch {
            self.push_scope();
            for stmt in else_branch {
                self.visit_stmt(stmt);
            }
            self.pop_scope();
        }
    }

    fn visit_while(&mut self, while_stmt: &While) {
        self.visit_expr(&while_stmt.cond);
        let old_in_loop = self.in_loop;
        self.in_loop = true;
        self.push_scope();
        for stmt in &while_stmt.body {
            self.visit_stmt(stmt);
        }
        self.pop_scope();
        self.in_loop = old_in_loop;
    }

    fn visit_for(&mut self, for_stmt: &For) {
        let old_in_loop = self.in_loop;
        self.in_loop = true;
        self.push_scope();
        if let Some(init) = &for_stmt.init {
            self.visit_stmt(init);
        }
        if let Some(cond) = &for_stmt.cond {
            self.visit_expr(cond);
        }
        if let Some(update) = &for_stmt.update {
            self.visit_stmt(update);
        }
        for stmt in &for_stmt.body {
            self.visit_stmt(stmt);
        }
        self.pop_scope();
        self.in_loop = old_in_loop;
    }

    fn visit_do_while(&mut self, dw: &DoWhile) {
        let old_in_loop = self.in_loop;
        self.in_loop = true;
        self.push_scope();
        for stmt in &dw.body {
            self.visit_stmt(stmt);
        }
        self.pop_scope();
        self.in_loop = old_in_loop;
        self.visit_expr(&dw.cond);
    }

    fn visit_match(&mut self, match_stmt: &Match) {
        self.visit_expr(&match_stmt.expr);
        for case in &match_stmt.cases {
            self.visit_expr(&case.value);
            self.push_scope();
            for stmt in &case.body {
                self.visit_stmt(stmt);
            }
            self.pop_scope();
        }
        if let Some(default) = &match_stmt.default {
            self.push_scope();
            for stmt in default {
                self.visit_stmt(stmt);
            }
            self.pop_scope();
        }
    }

    fn visit_expr(&mut self, expr: &Expr) -> Type {
        match expr {
            Expr::IntLit(_) => Type::Integer,
            Expr::FloatLit(_) => Type::Float,
            Expr::StringLit(_) => Type::Filum,
            Expr::BoolLit(_) => Type::Boolean,
            Expr::Ident(name) => {
                if let Some(info) = self.lookup_var(name) {
                    info.ty.clone()
                } else {
                    self.errors.push(SemanticError {
                        message: format!("Undefined variable '{}'", name),
                        line: 0,
                        col: 0,
                    });
                    Type::Integer
                }
            }
            Expr::Binary(op, left, right) => {
                let lty = self.visit_expr(left);
                let rty = self.visit_expr(right);
                self.check_binary_op(op, &lty, &rty);
                lty
            }
            Expr::Unary(op, expr) => {
                let ty = self.visit_expr(expr);
                match op {
                    UnaryOp::Neg => ty,
                    UnaryOp::Not => Type::Boolean,
                }
            }
            Expr::Call(name, args) => {
                self.visit_call(name, args);
                Type::Integer
            }
            Expr::ArrayIndex(arr, idx) => {
                self.visit_expr(arr);
                self.visit_expr(idx);
                Type::Integer
            }
            Expr::ArrayInit(items) => {
                for item in items {
                    self.visit_expr(item);
                }
                Type::Vec(Box::new(Type::Integer))
            }
            Expr::ArrayRange(start, end) => {
                self.visit_expr(start);
                self.visit_expr(end);
                Type::Vec(Box::new(Type::Integer))
            }
            Expr::Ref(expr) => {
                let ty = self.visit_expr(expr);
                Type::Ptr(Box::new(ty))
            }
            Expr::Deref(expr) => {
                let ty = self.visit_expr(expr);
                match ty {
                    Type::Ptr(inner) => *inner,
                    _ => {
                        self.errors.push(SemanticError {
                            message: "Cannot dereference non-pointer".to_string(),
                            line: 0,
                            col: 0,
                        });
                        Type::Integer
                    }
                }
            }
            Expr::Read(_) => Type::Integer,
        }
    }

    fn visit_call(&mut self, name: &str, args: &[Expr]) {
        if name == "imprimo" || name == "legerei" || name == "legeref" || name == "legeres" {
            for arg in args {
                self.visit_expr(arg);
            }
            return;
        }

        if let Some(func) = self.functions.get(name) {
            if func.params.len() != args.len() {
                self.errors.push(SemanticError {
                    message: format!("Function '{}' expects {} arguments, got {}", name, func.params.len(), args.len()),
                    line: 0,
                    col: 0,
                });
            }
            for arg in args {
                self.visit_expr(arg);
            }
        } else {
            self.errors.push(SemanticError {
                message: format!("Undefined function '{}'", name),
                line: 0,
                col: 0,
            });
        }
    }

    fn check_binary_op(&mut self, op: &BinaryOp, lty: &Type, rty: &Type) {
        match op {
            BinaryOp::Add | BinaryOp::Sub | BinaryOp::Mul | BinaryOp::Div | BinaryOp::Mod => {
                if !self.is_numeric(lty) || !self.is_numeric(rty) {
                    if !self.types_compatible(lty, rty) {
                        self.errors.push(SemanticError {
                            message: format!("Cannot apply arithmetic operator to '{:?}' and '{:?}'", lty, rty),
                            line: 0,
                            col: 0,
                        });
                    }
                }
            }
            BinaryOp::Eq | BinaryOp::Ne | BinaryOp::Lt | BinaryOp::Gt | BinaryOp::Le | BinaryOp::Ge => {}
            BinaryOp::And | BinaryOp::Or => {
                if !self.is_boolean(lty) || !self.is_boolean(rty) {
                    self.errors.push(SemanticError {
                        message: format!("Logical operators require boolean operands, got '{:?}' and '{:?}'", lty, rty),
                        line: 0,
                        col: 0,
                    });
                }
            }
        }
    }

    fn is_numeric(&self, ty: &Type) -> bool {
        matches!(ty, Type::Integer | Type::Float)
    }

    fn is_boolean(&self, ty: &Type) -> bool {
        matches!(ty, Type::Boolean)
    }

    fn types_compatible(&self, expected: &Type, actual: &Type) -> bool {
        match (expected, actual) {
            (Type::Integer, Type::Integer) => true,
            (Type::Float, Type::Float) => true,
            (Type::Filum, Type::Filum) => true,
            (Type::Boolean, Type::Boolean) => true,
            (Type::Vec(a), Type::Vec(b)) => self.types_compatible(a, b),
            (Type::Ptr(a), Type::Ptr(b)) => self.types_compatible(a, b),
            (Type::Named(a), Type::Named(b)) => a == b,
            _ => false,
        }
    }
}
