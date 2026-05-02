import sys
from ply import yacc
from lat.lexing._lexer import tokens, literals
from lat.ast.nodes import *

def p_prog(p):
    """
    prog : global_declarations function_declarations
    """
    p[0] = Program(globals=p[1], functions=p[2])

def p_global_declarations(p):
    """
    global_declarations : global_declaration global_declarations
    """
    p[0] = [p[1]] + p[2]

def p_global_declarations_empty(p):
    """
    global_declarations :
    """
    p[0] = []

def p_global_declaration(p):
    """
    global_declaration : declaration_assignment
    | declaration
    """
    p[0] = p[1]

def p_function_declarations(p):
    """
    function_declarations : function_declaration function_declarations
    """
    p[0] = [p[1]] + p[2]

def p_function_declarations_empty(p):
    """
    function_declarations :
    """
    p[0] = []

def p_function_declaration(p):
    """
    function_declaration : function_header function_body
    """
    header = p[1]
    p[0] = Function(name=header['name'], params=header['params'], return_type=header['return_type'], body=p[2])

def p_function_header(p):
    """
    function_header : function_id '(' params ')' out_type
    """
    p[0] = {'name': p[1], 'params': p[3], 'return_type': p[5]}

def p_function_id(p):
    """
    function_id : FUNCTION ID
    """
    p[0] = p[2]

def p_function_body(p):
    """
    function_body : '{' stmts '}'
    """
    p[0] = p[2]

def p_params(p):
    """
    params : params ',' param
    """
    p[0] = p[1] + [p[3]]

def p_params_empty(p):
    """
    params :
    """
    p[0] = []

def p_single_param(p):
    """
    params : param
    """
    p[0] = [p[1]]

def p_param(p):
    """
    param : ID ':' type
    | ID ':' Ptype
    """
    p[0] = Param(name=p[1], type=p[3])

def p_out_type(p):
    """
    out_type : RARROW type
    | RARROW Ptype
    |
    """
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = None

def p_stmts(p):
    """
    stmts : stmt stmts
    """
    p[0] = [p[1]] + p[2]

def p_stmts_empty(p):
    """
    stmts :
    """
    p[0] = []

def p_stmt(p):
    """
    stmt : print
    | function_call
    | declaration_assignment
    | assignment
    | declaration
    | if
    | match
    | while
    | for
    | do_while
    | BREAK
    | CONTINUE
    | return
    | debug
    """
    if isinstance(p[1], str) and p[1] in ('BREAK', 'CONTINUE'):
        p[0] = Break() if p[1] == 'BREAK' else Continue()
    else:
        p[0] = p[1]

def p_debug(p):
    """
    debug : DEBUG
    """
    p[0] = Debug()

def p_return(p):
    """
    return : RETURN expression
    | RETURN ';'
    | RETURN
    """
    if len(p) == 3 and p[2] != ';':
        p[0] = Return(value=p[2])
    else:
        p[0] = Return(value=None)

def p_for(p):
    """
    for : FOR '(' for_inits ';' expression ';' for_updates ')' '{' stmts '}'
    """
    p[0] = For(init=p[3], condition=p[5], update=p[7], body=p[10])

def p_for_inits(p):
    """
    for_inits : for_inits ',' for_init
    | for_init
    """
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]] if p[1] else []

def p_for_init(p):
    """
    for_init : declaration_assignment
    | declaration
    | assignment
    |
    """
    p[0] = p[1] if len(p) > 1 else None

def p_for_updates(p):
    """
    for_updates : for_updates ',' for_update
    | for_update
    """
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]] if p[1] else []

def p_for_update(p):
    """
    for_update : assignment
    """
    p[0] = p[1]

def p_do_while(p):
    """
    do_while : DO '{' stmts '}' WHILE '(' expression ')'
    """
    p[0] = DoWhile(condition=p[7], body=p[3])

def p_while(p):
    """
    while : WHILE expression '{' stmts '}'
    """
    p[0] = While(condition=p[2], body=p[4])

def p_if(p):
    """
    if : IF expression '{' stmts '}' else_if
    """
    p[0] = If(condition=p[2], then_body=p[4], else_body=p[5])

def p_else_if(p):
    """
    else_if : ELSE IF expression '{' stmts '}' else_if
    | else
    """
    if len(p) == 8:
        p[0] = If(condition=p[3], then_body=p[5], else_body=p[7])
    else:
        p[0] = p[1]

def p_else(p):
    """
    else : ELSE '{' stmts '}'
    |
    """
    if len(p) == 5:
        p[0] = p[3]
    else:
        p[0] = None

def p_match(p):
    """
    match : MATCH expression '{' cases '}'
    """
    p[0] = Match(expression=p[2], cases=p[4])

def p_cases(p):
    """
    cases : expression RARROW '{' stmts '}' cases
    | default
    """
    if len(p) == 7:
        p[0] = [Case(value=p[1], body=p[4])] + p[6]
    else:
        p[0] = [p[1]] if p[1] else []

def p_default(p):
    """
    default : DEFAULT RARROW '{' stmts '}'
    |
    """
    if len(p) == 6:
        p[0] = Default(body=p[4])
    else:
        p[0] = None

def p_declaration_assignment(p):
    """
    declaration_assignment : ID ':' type ASSIGN expression
    | ID ':' Ptype ASSIGN expression
    | ID ':' Vtype ndim ASSIGN '[' arrayitems ']'
    | ID ':' Vtype ASSIGN '[' arrayitems ']'
    | ID ':' Vtype ASSIGN '[' INTEGER RETI INTEGER ']'
    """
    if len(p) == 6:
        p[0] = Decl(name=p[1], type=p[3], value=p[5])
    elif len(p) == 9:
        p[0] = Decl(name=p[1], type=f"{p[3]}{p[4]}", value=ArrayLiteral(items=p[7]))
    elif len(p) == 8:
        p[0] = Decl(name=p[1], type=p[3], value=ArrayLiteral(items=p[6]))
    elif len(p) == 10:
        p[0] = Decl(name=p[1], type=p[3], value=ArrayRange(start=int(p[6]), end=int(p[8])))

def p_array_items(p):
    """
    arrayitems : arrayitems ',' expression
    | expression
    """
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_declaration(p):
    """
    declaration : ID ':' type
    | ID ':' Ptype
    | ID ':' Vtype ndim
    """
    if len(p) == 4:
        p[0] = Decl(name=p[1], type=p[3], value=None)
    else:
        p[0] = Decl(name=p[1], type=f"{p[3]}{p[4]}", value=None)

def p_array_dimension(p):
    """
    ndim : ndim '[' INTEGER ']'
    | '[' INTEGER ']'
    """
    if len(p) == 5:
        p[0] = p[1] + f"[{p[3]}]"
    else:
        p[0] = f"[{p[2]}]"

def p_assignment_indexing(p):
    """
    assignment : ID ndepth ASSIGN expression
    """
    p[0] = Assignment(target=ArrayIndex(name=p[1], indices=p[2]), value=p[4])

def p_assignment_expression(p):
    """
    assignment : ID ASSIGN expression
    """
    p[0] = Assignment(target=Identifier(name=p[1]), value=p[3])

def p_read(p):
    """
    read : read_type '(' multiple_prints ')'
    """
    p[0] = Read(read_type=p[1], expressions=p[3])

def p_read_type(p):
    """
    read_type : READ_INT
    | READ_FLOAT
    | READ_STRING
    """
    p[0] = p[1]

def p_print(p):
    """
    print : PRINT '(' multiple_prints ')'
    """
    p[0] = Print(expressions=p[3])

def p_print_multiple(p):
    """
    multiple_prints : multiple_prints ',' expression
    """
    p[0] = p[1] + [p[3]]

def p_print_single(p):
    """
    multiple_prints : expression
    """
    p[0] = [p[1]]

def p_print_empty(p):
    """
    multiple_prints :
    """
    p[0] = []

def p_type(p):
    """
    type : TYPE_INT
    | TYPE_STRING
    | TYPE_FLOAT
    """
    p[0] = p[1]

def p_vtype(p):
    """
    Vtype : TYPE_VEC LT type GT
    """
    p[0] = f"vec<{p[3]}>"

def p_ptype(p):
    """
    Ptype : '&' TYPE_INT
    | '&' TYPE_STRING
    | '&' TYPE_FLOAT
    """
    p[0] = f"&{p[2]}"

def p_expression_or(p):
    """
    expression : expression OR subexpression
    """
    p[0] = BinaryOp(left=p[1], op='OR', right=p[3])

def p_expression_subexpression(p):
    """
    expression : subexpression
    """
    p[0] = p[1]

def p_subexpression_and(p):
    """
    subexpression : subexpression AND condition
    """
    p[0] = BinaryOp(left=p[1], op='AND', right=p[3])

def p_subexpression_condition(p):
    """
    subexpression : condition
    """
    p[0] = p[1]

def p_condition_eq(p):
    """
    condition : condition EQ comparison
    """
    p[0] = BinaryOp(left=p[1], op='EQ', right=p[3])

def p_condition_neq(p):
    """
    condition : condition NEQ comparison
    """
    p[0] = BinaryOp(left=p[1], op='NEQ', right=p[3])

def p_condition_comparison(p):
    """
    condition : comparison
    """
    p[0] = p[1]

def p_comparison_lt(p):
    """
    comparison : comparison LT term
    """
    p[0] = BinaryOp(left=p[1], op='LT', right=p[3])

def p_comparison_gt(p):
    """
    comparison : comparison GT term
    """
    p[0] = BinaryOp(left=p[1], op='GT', right=p[3])

def p_comparison_lte(p):
    """
    comparison : comparison LTE term
    """
    p[0] = BinaryOp(left=p[1], op='LTE', right=p[3])

def p_comparison_gte(p):
    """
    comparison : comparison GTE term
    """
    p[0] = BinaryOp(left=p[1], op='GTE', right=p[3])

def p_comparison_term(p):
    """
    comparison : term
    """
    p[0] = p[1]

def p_term_sub(p):
    """
    term : term '-' factor
    """
    p[0] = BinaryOp(left=p[1], op='-', right=p[3])

def p_term_add(p):
    """
    term : term '+' factor
    """
    p[0] = BinaryOp(left=p[1], op='+', right=p[3])

def p_term_factor(p):
    """
    term : factor
    """
    p[0] = p[1]

def p_factor_mul(p):
    """
    factor : factor '*' unary
    """
    p[0] = BinaryOp(left=p[1], op='*', right=p[3])

def p_factor_div(p):
    """
    factor : factor '/' unary
    """
    p[0] = BinaryOp(left=p[1], op='/', right=p[3])

def p_factor_mod(p):
    """
    factor : factor '%' unary
    """
    p[0] = BinaryOp(left=p[1], op='%', right=p[3])

def p_factor_unary(p):
    """
    factor : unary
    """
    p[0] = p[1]

def p_unary_not(p):
    """
    unary : NOT unary
    """
    p[0] = UnaryOp(op='NOT', operand=p[2])

def p_unary_neg(p):
    """
    unary : '-' unary
    """
    p[0] = UnaryOp(op='-', operand=p[2])

def p_unary_primary(p):
    """
    unary : primary
    """
    p[0] = p[1]

def p_primary_indexing(p):
    """
    primary : ID ndepth
    """
    p[0] = ArrayIndex(name=p[1], indices=p[2])

def p_array_indexing_depth(p):
    """
    ndepth : ndepth '[' expression ']'
    | '[' expression ']'
    """
    if len(p) == 5:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[2]]

def p_primary_ref(p):
    """
    primary : '&' ID
    """
    p[0] = Ref(name=p[2])

def p_primary_int(p):
    """
    primary : INTEGER
    """
    p[0] = IntegerLiteral(value=int(p[1]))

def p_primary_float(p):
    """
    primary : FLOAT
    """
    p[0] = FloatLiteral(value=float(p[1]))

def p_primary_string(p):
    """
    primary : FILUM
    """
    p[0] = StringLiteral(value=p[1])

def p_primary_id(p):
    """
    primary : ID
    """
    p[0] = Identifier(name=p[1])

def p_primary_function(p):
    """
    primary : function_call
    """
    p[0] = p[1]

def p_primary_read(p):
    """
    primary : read
    """
    p[0] = p[1]

def p_primary_new(p):
    """
    primary : '(' expression ')'
    """
    p[0] = p[2]

def p_function_call(p):
    """
    function_call : ID '(' args ')'
    """
    p[0] = FunctionCall(name=p[1], args=p[3])

def p_args(p):
    """
    args : args ',' expression
    """
    p[0] = p[1] + [p[3]]

def p_args_empty(p):
    """
    args :
    """
    p[0] = []

def p_single_arg(p):
    """
    args : expression
    """
    p[0] = [p[1]]

def p_error(p):
    if p is None:
        sys.stderr.write("Syntax Error: Unexpected end of file\n")
    else:
        from lat.utils.errors import syntax_error
        syntax_error(p, f"Invalid syntax '{p.value}'")
    sys.exit(1)

parser = yacc.yacc(start='prog')

def parse(source_code):
    return parser.parse(source_code)
