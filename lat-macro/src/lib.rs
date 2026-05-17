use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, LitStr};

/// Compile OpenLatinum code embedded in a Rust program.
///
/// # Example
/// ```rust,ignore
/// use lat::lat;
///
/// lat! { r#"
/// munus main() {
///     imprimo("Hello from OpenLatinum!")
/// }
/// "# }
/// ```
#[proc_macro]
pub fn lat(input: TokenStream) -> TokenStream {
    let lit = parse_macro_input!(input as LitStr);
    let source = lit.value();

    let program = match lat_core::parser::parse(&source) {
        Ok(p) => p,
        Err(e) => {
            return syn::Error::new(lit.span(), format!("OpenLatinum parse error: {}", e))
                .to_compile_error()
                .into();
        }
    };

    let generated = codegen::generate_program(&program);
    generated.into()
}

mod codegen {
    use lat_core::ast::*;
    use proc_macro2::TokenStream;
    use quote::{quote, format_ident};

    pub fn generate_program(program: &Program) -> TokenStream {
        let globals: Vec<_> = program.globals.iter().map(generate_global).collect();

        let global_inits: Vec<_> = program.globals.iter().filter_map(|decl| {
            let name = format_ident!("{}", decl.name);
            match &decl.ty {
                Type::Vec(_) => {
                    if let Some(init) = &decl.init {
                        let expr = generate_expr(init);
                        Some(quote! { #name = #expr; })
                    } else if let Some(size) = &decl.size {
                        let s = generate_expr(size);
                        Some(quote! { #name = vec![0; #s as usize]; })
                    } else {
                        None
                    }
                }
                _ => None,
            }
        }).collect();

        let functions: Vec<_> = program.functions.iter().map(|f| {
            if f.name == "main" {
                generate_main_function(f, &global_inits)
            } else {
                generate_function(f)
            }
        }).collect();

        quote! {
            #(#globals)*
            #(#functions)*
        }
    }

    fn generate_main_function(func: &Function, global_inits: &[TokenStream]) -> TokenStream {
        let name = format_ident!("{}", func.name);
        let params: Vec<_> = func.params.iter().map(|p| {
            let name = format_ident!("{}", p.name);
            let ty = generate_type(&p.ty);
            quote! { #name: #ty }
        }).collect();

        let ret = func.return_type.as_ref().map(generate_type);
        let ret_ty = match ret {
            Some(ty) => quote! { -> #ty },
            None => quote! {},
        };

        let body = generate_stmts(&func.body);

        quote! {
            fn #name(#(#params),*) #ret_ty {
                unsafe {
                    #(#global_inits)*
                    #body
                }
            }
        }
    }

    fn generate_global(decl: &VarDecl) -> TokenStream {
        let name = format_ident!("{}", decl.name);
        let ty = generate_type(&decl.ty);

        match &decl.ty {
            Type::Vec(_) => {
                quote! { static mut #name: #ty = Vec::new(); }
            }
            _ => {
                let init = decl.init.as_ref().map(generate_expr).unwrap_or_else(|| default_value(&decl.ty));
                if decl.is_const {
                    quote! { const #name: #ty = #init; }
                } else {
                    quote! { static mut #name: #ty = #init; }
                }
            }
        }
    }

    fn generate_type(ty: &Type) -> TokenStream {
        match ty {
            Type::Integer => quote! { i64 },
            Type::Float => quote! { f32 },
            Type::Filum => quote! { String },
            Type::Boolean => quote! { bool },
            Type::Vec(inner) => {
                let inner_ty = generate_type(inner);
                quote! { Vec<#inner_ty> }
            }
            Type::Ptr(inner) => {
                let inner_ty = generate_type(inner);
                quote! { *mut #inner_ty }
            }
            Type::Named(name) => {
                let ident = format_ident!("{}", name);
                quote! { #ident }
            }
        }
    }

    fn generate_function(func: &Function) -> TokenStream {
        let name = format_ident!("{}", func.name);
        let params: Vec<_> = func.params.iter().map(|p| {
            let name = format_ident!("{}", p.name);
            let ty = generate_type(&p.ty);
            quote! { #name: #ty }
        }).collect();

        let ret = func.return_type.as_ref().map(generate_type);
        let ret_ty = match ret {
            Some(ty) => quote! { -> #ty },
            None => quote! {},
        };

        let body = generate_stmts(&func.body);

        quote! {
            fn #name(#(#params),*) #ret_ty {
                unsafe {
                    #body
                }
            }
        }
    }

    fn generate_stmts(stmts: &[Stmt]) -> TokenStream {
        let items: Vec<_> = stmts.iter().map(generate_stmt).collect();
        quote! { #(#items)* }
    }

    fn generate_stmt(stmt: &Stmt) -> TokenStream {
        match stmt {
            Stmt::VarDecl(decl) => {
                let name = format_ident!("{}", decl.name);
                let ty = generate_type(&decl.ty);
                match &decl.init {
                    Some(init) => {
                        let expr = generate_expr(init);
                        quote! { let mut #name: #ty = #expr; }
                    }
                    None => {
                        match (&decl.ty, &decl.size) {
                            (Type::Vec(_), Some(size)) => {
                                let s = generate_expr(size);
                                quote! { let mut #name: #ty = vec![0; #s as usize]; }
                            }
                            _ => {
                                let default = default_value(&decl.ty);
                                quote! { let mut #name: #ty = #default; }
                            }
                        }
                    }
                }
            }
            Stmt::Assign(assign) => {
                let target = generate_expr(&assign.target);
                let value = generate_expr(&assign.value);
                quote! { #target = #value; }
            }
            Stmt::If(if_stmt) => {
                let cond = generate_expr(&if_stmt.cond);
                let then_branch = generate_stmts(&if_stmt.then_branch);
                match &if_stmt.else_branch {
                    Some(else_branch) => {
                        let else_stmts = generate_stmts(else_branch);
                        quote! {
                            if #cond {
                                #then_branch
                            } else {
                                #else_stmts
                            }
                        }
                    }
                    None => {
                        quote! {
                            if #cond {
                                #then_branch
                            }
                        }
                    }
                }
            }
            Stmt::While(while_stmt) => {
                let cond = generate_expr(&while_stmt.cond);
                let body = generate_stmts(&while_stmt.body);
                quote! {
                    while #cond {
                        #body
                    }
                }
            }
            Stmt::For(for_stmt) => {
                let init = for_stmt.init.as_ref().map(|i| generate_stmt(i));
                let cond = for_stmt.cond.as_ref().map(generate_expr);
                let update = for_stmt.update.as_ref().map(|u| generate_stmt(u));
                let body = generate_stmts(&for_stmt.body);

                quote! {
                    {
                        #init
                        while #cond {
                            #body
                            #update
                        }
                    }
                }
            }
            Stmt::DoWhile(dw) => {
                let cond = generate_expr(&dw.cond);
                let body = generate_stmts(&dw.body);
                quote! {
                    loop {
                        #body
                        if !#cond {
                            break;
                        }
                    }
                }
            }
            Stmt::Match(match_stmt) => {
                let expr = generate_expr(&match_stmt.expr);
                let cases: Vec<_> = match_stmt.cases.iter().map(|c| {
                    let val = generate_expr(&c.value);
                    let body = generate_stmts(&c.body);
                    quote! { #val => { #body } }
                }).collect();
                let default = match_stmt.default.as_ref().map(|d| {
                    let body = generate_stmts(d);
                    quote! { _ => { #body } }
                });

                quote! {
                    match #expr {
                        #(#cases)*
                        #default
                    }
                }
            }
            Stmt::Break => quote! { break; },
            Stmt::Continue => quote! { continue; },
            Stmt::Return(expr) => match expr {
                Some(e) => {
                    let val = generate_expr(e);
                    quote! { return #val; }
                }
                None => quote! { return; },
            },
            Stmt::Expr(expr) => {
                let e = generate_expr(expr);
                quote! { #e; }
            }
        }
    }

    fn generate_expr(expr: &Expr) -> TokenStream {
        match expr {
            Expr::IntLit(n) => quote! { #n },
            Expr::FloatLit(n) => quote! { #n },
            Expr::StringLit(s) => quote! { #s.to_string() },
            Expr::BoolLit(b) => quote! { #b },
            Expr::Ident(name) => {
                let ident = format_ident!("{}", name);
                quote! { #ident }
            }
            Expr::Binary(op, left, right) => {
                let l = generate_expr(left);
                let r = generate_expr(right);
                match op {
                    BinaryOp::Add => quote! { ::lat::LatAdd::lat_add(#l, #r) },
                    BinaryOp::Sub => quote! { (#l - #r) },
                    BinaryOp::Mul => quote! { (#l * #r) },
                    BinaryOp::Div => quote! { (#l / #r) },
                    BinaryOp::Mod => quote! { (#l % #r) },
                    BinaryOp::Eq => quote! { (#l == #r) },
                    BinaryOp::Ne => quote! { (#l != #r) },
                    BinaryOp::Lt => quote! { (#l < #r) },
                    BinaryOp::Gt => quote! { (#l > #r) },
                    BinaryOp::Le => quote! { (#l <= #r) },
                    BinaryOp::Ge => quote! { (#l >= #r) },
                    BinaryOp::And => quote! { (#l && #r) },
                    BinaryOp::Or => quote! { (#l || #r) },
                }
            }
            Expr::Unary(op, expr) => {
                let e = generate_expr(expr);
                match op {
                    UnaryOp::Neg => quote! { (-#e) },
                    UnaryOp::Not => quote! { (!#e) },
                }
            }
            Expr::Call(name, args) => {
                let ident = format_ident!("{}", name);
                let args: Vec<_> = args.iter().map(generate_expr).collect();
                if name == "imprimo" {
                    if args.is_empty() {
                        quote! { println!() }
                    } else {
                        quote! { println!("{}", #(#args),*) }
                    }
                } else if name == "stri" {
                    quote! { (#(#args),*).to_string() }
                } else {
                    quote! { #ident(#(#args),*) }
                }
            }
            Expr::ArrayIndex(arr, idx) => {
                let a = generate_expr(arr);
                let i = generate_expr(idx);
                quote! { #a[#i as usize] }
            }
            Expr::ArrayInit(items) => {
                let items: Vec<_> = items.iter().map(generate_expr).collect();
                quote! { vec![#(#items),*] }
            }
            Expr::Ref(expr) => {
                let e = generate_expr(expr);
                quote! { &mut #e }
            }
            Expr::Deref(expr) => {
                let e = generate_expr(expr);
                quote! { *#e }
            }
            Expr::Read(rt) => {
                match rt {
                    ReadType::Int => {
                        quote! {
                            {
                                let mut line = String::new();
                                std::io::stdin().read_line(&mut line).unwrap();
                                line.trim().parse::<i64>().unwrap_or(0)
                            }
                        }
                    }
                    ReadType::Float => {
                        quote! {
                            {
                                let mut line = String::new();
                                std::io::stdin().read_line(&mut line).unwrap();
                                line.trim().parse::<f32>().unwrap_or(0.0)
                            }
                        }
                    }
                    ReadType::String => {
                        quote! {
                            {
                                let mut line = String::new();
                                std::io::stdin().read_line(&mut line).unwrap();
                                line.trim().to_string()
                            }
                        }
                    }
                }
            }
            _ => panic!("Unsupported expression in OpenLatinum codegen"),
        }
    }

    fn default_value(ty: &Type) -> TokenStream {
        match ty {
            Type::Integer => quote! { 0 },
            Type::Float => quote! { 0.0 },
            Type::Filum => quote! { String::new() },
            Type::Boolean => quote! { false },
            Type::Vec(inner) => {
                let _ = generate_type(inner);
                quote! { Vec::new() }
            }
            _ => quote! { Default::default() },
        }
    }
}
