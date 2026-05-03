from typing import Any

from ply import yacc

from lat.lexing._lexer import *
from lat.semantics._scopes import Scope, MetaData
from lat.semantics._functions import Functions, FunctionData
from lat.semantics._type_check import TypeCheck
from lat.utils.errors import syntax_error, compiler_error, compiler_note, CompilationError
from lat.semantics._expression import Primary, Unary, Factor, Term, Comparison, Condition, SubExpression, Expression
from lat.semantics._statement import IO, Assignment, Declaration, DeclarationAssignment, If, Match, Loop, BreakContinue


def p_prog(p: Any) -> None:
    """
    prog : global_declarations function_declarations
    """
    parser.global_count = 0
    parser.loop_count = 0
    parser.logic_count = 0
    parser.if_count = 0
    if not parser.type_checker.is_empty():
        compiler_error(p, 1, f"Leftover types in type checker. {p.parser.type_checker}")
        raise CompilationError("Leftover types in type checker")

    if parser.functions_handler.get("main") is None:
        compiler_error(p, 0, "Did not find main function")
        compiler_note("Called from p_prog.")
        raise CompilationError("Did not find main function")

    p[0] = p[1]
    p[0] += "start\n"
    p[0] += f"PUSHA main\n"
    p[0] += f"CALL\n"
    p[0] += "stop\n"
    p[0] += p[2]


######################
##   GLOBAL RULES   ##
######################


def p_global_declarations(p: Any) -> None:
    """
    global_declarations : global_declaration global_declarations
    """
    p[0] = p[1] + p[2]


def p_global_declarations_empty(p: Any) -> None:
    """
    global_declarations :
    """
    p[0] = ""


def p_global_declaration(p: Any) -> None:
    """
    global_declaration : declaration_assignment
                    | declaration
    """
    p[0] = p[1]


######################
##   FUNCS RULES    ##
######################


def p_function_declarations(p: Any) -> None:
    """
    function_declarations : function_declaration function_declarations
    """
    p[0] = p[1] + p[2]


def p_function_declarations_empty(p: Any) -> None:
    """
    function_declarations :
    """
    p[0] = ""


def p_function_declaration(p: Any) -> None:
    """
    function_declaration : function_header function_body
    """
    p[0] = p[1] + p[2]


def p_function_header(p: Any) -> None:
    """
    function_header : function_id ss '(' params ')' out_type
    """
    p[0] = parser.functions_handler.handle(p, "header")


def p_function_id(p: Any) -> None:
    """
    function_id : FUNCTION ID
    """
    p[0] = parser.functions_handler.handle(p, "id")


def p_function_body(p: Any) -> None:
    """
    function_body : '{' stmts '}' es
    """
    p[0] = parser.functions_handler.handle(p, "body")


def p_function_call(p: Any) -> None:
    """
    function_call : f_call '(' args ')'
    """
    p[0] = parser.functions_handler.handle(p, "call")


def p_f_call(p: Any) -> None:
    """
    f_call : ID
    """
    p.parser.num_args.append(0)
    p[0] = p[1]


def p_params(p: Any) -> None:
    """
    params : params ',' param
    """
    p[0] = p[1] + p[3]


def p_params_empty(p: Any) -> None:
    """
    params :
    """
    p[0] = ""


def p_single_param(p: Any) -> None:
    """
    params : param
    """
    p[0] = p[1]


def p_param(p: Any) -> None:
    """
    param : ID ':' type
        |   ID ':' Ptype
    """
    p[0] = parser.functions_handler.handle(p, "parameter")


def p_out_type(p: Any) -> None:
    """
    out_type : RARROW type
            | RARROW Ptype
            |
    """
    p[0] = parser.functions_handler.handle(p, "out_type")


def p_args(p: Any) -> None:
    """
    args : args ',' arg
    """
    p[0] = p[3] + p[1]


def p_args_empty(p: Any) -> None:
    """
    args :
        | arg
    """
    if len(p) == 1:
        p[0] = ""
    else:
        p[0] = p[1]


def p_single_arg(p: Any) -> None:
    """
    arg : expression
    """
    p[0] = parser.functions_handler.handle(p, "argument")


######################
##    STMTS RULE    ##
######################


def p_stmts(p: Any) -> None:
    """
    stmts : stmt stmts
    """
    p[0] = p[1] + p[2]


def p_stmts_empty(p: Any) -> None:
    """
    stmts :
    """
    p[0] = ""


def p_stmt(p: Any) -> None:
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
        | break
        | continue
        | return
        | debug
    """
    p[0] = p[1]


def p_debug(p: Any) -> None:
    """
    debug : DEBUG
    """
    p[0] = ""
    p.parser.current_scope.debug()


######################
##    SCOPE RULE    ##
######################


def p_start_scope(p: Any) -> None:
    """
    ss :
    """
    p.parser.current_scope.handle(p, "start_scope")


def p_end_scope(p: Any) -> None:
    """
    es :
    """
    p[0] = p.parser.current_scope.handle(p, "end_scope")


######################
##   RETURN STMT    ##
######################


def p_return(p: Any) -> None:
    """
    return : RETURN expression
            | RETURN ';'
    """
    p[0] = parser.functions_handler.handle(p, "return")


######################
##    BREAK STMT    ##
######################


def p_break(p: Any) -> None:
    """
    break : BREAK
    """
    p[0] = parser.loop_break_handler.handle(p, "break")


def p_continue(p: Any) -> None:
    """
    continue : CONTINUE
    """
    p[0] = parser.loop_break_handler.handle(p, "continue")


######################
##    LOOPS STMT    ##
######################


def p_for(p: Any) -> None:
    """
    for : loop_for ss '(' for_inits ';' expression ';' for_updates ')' ss '{' stmts  '}' es es
    """
    p[0] = parser.loop_handler.handle(p, "for")


def p_for_inits(p: Any) -> None:
    """
    for_inits : for_inits ',' for_init
            | for_init
    """
    p[0] = parser.loop_handler.handle(p, "for_inits")


def p_for_init(p: Any) -> None:
    """
    for_init : declaration_assignment
            | declaration
            | assignment
            |
    """
    p[0] = parser.loop_handler.handle(p, "for_init")


def p_for_updates(p: Any) -> None:
    """
    for_updates : for_updates ',' for_update
            | for_update
    """
    p[0] = parser.loop_handler.handle(p, "for_updates")


def p_for_update(p: Any) -> None:
    """
    for_update : assignment
    """
    p[0] = parser.loop_handler.handle(p, "for_update")


def p_do_while(p: Any) -> None:
    """
    do_while : loop_do ss '{' stmts '}' es WHILE '(' expression ')'
    """
    p[0] = parser.loop_handler.handle(p, "do_while")


def p_while(p: Any) -> None:
    """
    while : loop_while expression ss '{' stmts '}' es
    """
    p[0] = parser.loop_handler.handle(p, "while")


# This functions append the loop type to the loop list
def p_loop_for(p: Any) -> None:
    """
    loop_for : FOR
    """
    parser.current_loops.append("FOR")


def p_loop_do(p: Any) -> None:
    """
    loop_do : DO
    """
    parser.current_loops.append("DO")


def p_loop_while(p: Any) -> None:
    """
    loop_while : WHILE
    """
    parser.current_loops.append("WHILE")


######################
##     IF STMT      ##
######################


def p_if(p: Any) -> None:
    """
    if : IF expression ss '{' stmts '}' es else_if
    """
    p[0] = parser.if_handler.handle(p, "if")


def p_else_if(p: Any) -> None:
    """
    else_if : ELSE IF expression ss '{' stmts '}' es else_if
            | else
    """
    p[0] = parser.if_handler.handle(p, "else_if")


def p_else(p: Any) -> None:
    """
    else : ELSE ss '{' stmts '}' es
        |
    """
    p[0] = parser.if_handler.handle(p, "else")


######################
##   SWITCH STMT    ##
######################


def p_match(p: Any) -> None:
    """
    match : match_start expression '{' cases '}'
    """
    p[0] = parser.match_handler.handle(p, "match")


def p_match_start(p: Any) -> None:
    """
    match_start : MATCH
    """
    p.parser.frame_count += 1  # Increment the global count aas to prevent shadowing of variables declared in the match statement


def p_cases(p: Any) -> None:
    """
    cases : expression RARROW ss '{' stmts '}' es cases
        | default
    """
    p[0] = parser.match_handler.handle(p, "cases")


def p_default(p: Any) -> None:
    """
    default : DEFAULT RARROW ss '{' stmts '}' es
    """
    p[0] = parser.match_handler.handle(p, "default")


######################
##    INIT STMT     ##
######################


def p_variable_init(p: Any) -> None:
    """
    declaration_assignment : ID ':' type ASSIGN expression
    """
    p[0] = parser.declaration_assignment_handler.handle(p, "variable_init")


def p_pointer_init(p: Any) -> None:
    """
    declaration_assignment : ID ':' Ptype ASSIGN expression
    """
    p[0] = parser.declaration_assignment_handler.handle(p, "pointer_init")


def p_array_literal_init(p: Any) -> None:
    """
    declaration_assignment : ID ':' Vtype ndim ASSIGN '[' arrayitems ']'
                            | ID ':' Vtype ASSIGN '[' arrayitems ']'
    """
    p[0] = parser.declaration_assignment_handler.handle(p, "array_literal_init")


def p_array_range_init(p: Any) -> None:
    """
    declaration_assignment : ID ':' Vtype ASSIGN '['  INTEGER  RETI   INTEGER ']'
    """
    p[0] = parser.declaration_assignment_handler.handle(p, "array_range_init")


def p_array_items(p: Any) -> None:
    """
    arrayitems : arrayitems ',' expression
        | expression
    """
    p[0] = parser.declaration_assignment_handler.handle(p, "array_items")


######################
##   DECLARE STMT   ##
######################


def p_variable_declaration(p: Any) -> None:
    """
    declaration : ID ':' type
    """
    p[0] = p.parser.declaration_handler.handle(p, "variable_declaration")


def p_pointer_declaration(p: Any) -> None:
    """
    declaration : ID ':' Ptype
    """
    p[0] = p.parser.declaration_handler.handle(p, "pointer_declaration")


def p_array_declaration(p: Any) -> None:
    """
    declaration : ID ':' Vtype ndim
    """
    p[0] = p.parser.declaration_handler.handle(p, "array_declaration")


def p_array_dimension(p: Any) -> None:
    """
    ndim : ndim '[' INTEGER  ']'
        | '[' INTEGER ']'
    """
    p[0] = p.parser.declaration_handler.handle(p, "array_dimension")


######################
##   ASSIGN STMT    ##
######################


def p_assignment_indexing(p: Any) -> None:
    """
    assignment : ID ndepth ASSIGN expression
    """
    p[0] = parser.assignment_handler.handle(p, "indexing")


def p_assignment_expression(p: Any) -> None:
    """
    assignment : ID ASSIGN expression
    """
    p[0] = parser.assignment_handler.handle(p, "variable")


######################
##    READ  STMT    ##
######################


def p_read(p: Any) -> None:
    """
    read : read_type '(' multiple_prints ')'
    """
    p[0] = parser.io_handler.handle(p, "read")


def p_read_type(p: Any) -> None:
    """
    read_type : READ_INT
            | READ_FLOAT
            | READ_STRING
    """
    p[0] = parser.io_handler.handle(p, "read_type")


######################
##    PRINT STMT    ##
######################


def p_print(p: Any) -> None:
    """
    print : PRINT '(' multiple_prints ')'
    """
    p[0] = parser.io_handler.handle(p, "print")


def p_print_multiple(p: Any) -> None:
    """
    multiple_prints : multiple_prints ',' expression
    """
    p[0] = parser.io_handler.handle(p, "multiple")


def p_print_single(p: Any) -> None:
    """
    multiple_prints : expression
    """
    p[0] = parser.io_handler.handle(p, "single")


def p_print_empty(p: Any) -> None:
    """
    multiple_prints :
    """
    p[0] = parser.io_handler.handle(p, "empty")


######################
## TYPES INITAL IMP ##
######################


def p_type(p: Any) -> None:
    """
    type : TYPE_INT
        | TYPE_STRING
        | TYPE_FLOAT
    """
    p[0] = p[1]


def p_vtype(p: Any) -> None:
    """
    Vtype : TYPE_VEC LT type GT
    """
    p[0] = p[1] + p[2] + p[3] + p[4]


def p_ptype(p: Any) -> None:
    """
    Ptype : '&' TYPE_INT
        | '&' TYPE_STRING
        | '&' TYPE_FLOAT
    """
    p[0] = p[1] + p[2]


######################
## EXPRESSION RULES ##
######################


def p_expression_or(p: Any) -> None:
    """
    expression : expression OR subexpression
    """
    p[0] = parser.expression_handler.handle(p, "or")


def p_expression_subexpression(p: Any) -> None:
    """
    expression : subexpression
    """
    p[0] = parser.expression_handler.handle(p, "subexpression")


def p_subexpression_and(p: Any) -> None:
    """
    subexpression : subexpression AND condition
    """
    p[0] = parser.subexpression_handler.handle(p, "and")


def p_subexpression_condition(p: Any) -> None:
    """
    subexpression : condition
    """
    p[0] = parser.subexpression_handler.handle(p, "condition")


def p_condition_eq(p: Any) -> None:
    """
    condition : condition EQ comparison
    """
    p[0] = parser.condition_handler.handle(p, "eq")


def p_condition_neq(p: Any) -> None:
    """
    condition : condition NEQ comparison
    """
    p[0] = parser.condition_handler.handle(p, "neq")


def p_condition_comparison(p: Any) -> None:
    """
    condition : comparison
    """
    p[0] = parser.condition_handler.handle(p, "comparison")


def p_comparison_lt(p: Any) -> None:
    """
    comparison : comparison LT term
    """
    p[0] = parser.comparison_handler.handle(p, "lt")


def p_comparison_gt(p: Any) -> None:
    """
    comparison : comparison GT term
    """
    p[0] = parser.comparison_handler.handle(p, "gt")


def p_comparison_lte(p: Any) -> None:
    """
    comparison : comparison LTE term
    """
    p[0] = parser.comparison_handler.handle(p, "lte")


def p_comparison_gte(p: Any) -> None:
    """
    comparison : comparison GTE term
    """
    p[0] = parser.comparison_handler.handle(p, "gte")


def p_comparison_term(p: Any) -> None:
    """
    comparison : term
    """
    p[0] = parser.comparison_handler.handle(p, "term")


def p_term_sub(p: Any) -> None:
    """
    term : term '-' factor
    """
    p[0] = parser.term_handler.handle(p, "sub")


def p_term_add(p: Any) -> None:
    """
    term : term '+' factor
    """
    p[0] = parser.term_handler.handle(p, "add")


def p_term_factor(p: Any) -> None:
    """
    term : factor
    """
    p[0] = parser.term_handler.handle(p, "factor")


def p_factor_mul(p: Any) -> None:
    """
    factor : factor '*' unary
    """
    p[0] = parser.factor_handler.handle(p, "mul")


def p_factor_div(p: Any) -> None:
    """
    factor : factor '/' unary
    """
    p[0] = parser.factor_handler.handle(p, "div")


def p_factor_mod(p: Any) -> None:
    """
    factor : factor '%' unary
    """
    p[0] = parser.factor_handler.handle(p, "mod")


def p_factor_unary(p: Any) -> None:
    """
    factor : unary
    """
    p[0] = parser.factor_handler.handle(p, "unary")


def p_unary_not(p: Any) -> None:
    """
    unary : NOT unary
    """
    p[0] = parser.unary_handler.handle(p, "not")


def p_unary_neg(p: Any) -> None:
    """
    unary : '-' unary
    """
    p[0] = parser.unary_handler.handle(p, "neg")


def p_unary_primary(p: Any) -> None:
    """
    unary : primary
    """
    p[0] = parser.unary_handler.handle(p, "primary")


def p_primary_indexing(p: Any) -> None:
    """
    primary : ID ndepth
    """
    p[0] = parser.primary_handler.handle(p, "indexing")


def p_array_indexing_depth(p: Any) -> None:
    """
    ndepth : ndepth '[' expression ']'
        | '[' expression ']'
    """
    p[0] = p.parser.primary_handler.handle(p, "array_indexing_depth")


def p_primary_ref(p: Any) -> None:
    """
    primary : '&' ID
    """
    p[0] = parser.primary_handler.handle(p, "ref")


def p_primary_int(p: Any) -> None:
    """
    primary : INTEGER
    """
    p[0] = parser.primary_handler.handle(p, "integer")


def p_primary_float(p: Any) -> None:
    """
    primary : FLOAT
    """
    p[0] = parser.primary_handler.handle(p, "float")


def p_primary_string(p: Any) -> None:
    """
    primary : FILUM
    """
    p[0] = parser.primary_handler.handle(p, "filum")


def p_primary_id(p: Any) -> None:
    """
    primary : ID
    """
    p[0] = parser.primary_handler.handle(p, "id")


def p_primary_function(p: Any) -> None:
    """
    primary : function_call
    """
    p[0] = p[1]


def p_primary_read(p: Any) -> None:
    """
    primary : read
    """
    p[0] = p[1]


def p_primary_new(p: Any) -> None:
    """
    primary : '(' expression ')'
    """
    p[0] = parser.primary_handler.handle(p, "new")


def p_error(p: Any) -> None:
    if p is None:
        raise CompilationError("Syntax Error: Unexpected end of file")
    else:
        syntax_error(p, f"Invalid syntax '{p.value}'")
        raise CompilationError(f"Invalid syntax '{p.value}'")


# Inicializar yacc
parser = yacc.yacc()

# Inicializar handlers
# Cada handler é uma classe que implementa os métodos de cada produção
# e cria o código de máquina correspondente
parser.primary_handler = Primary()
parser.unary_handler = Unary()
parser.factor_handler = Factor()
parser.term_handler = Term()
parser.comparison_handler = Comparison()
parser.condition_handler = Condition()
parser.subexpression_handler = SubExpression()
parser.expression_handler = Expression()
parser.io_handler = IO()
parser.assignment_handler = Assignment()
parser.declaration_handler = Declaration()
parser.declaration_assignment_handler = DeclarationAssignment()
parser.if_handler = If()
parser.match_handler = Match()
parser.loop_handler = Loop()
parser.loop_break_handler = BreakContinue()
parser.functions_handler = Functions()

# Inicializar variáveis
parser.num_params = 0
parser.num_args = []
parser.frame_count = 0
parser.global_count = 0
parser.if_count = 0
parser.rel_if_count = 0
parser.match_count = 0
parser.rel_match_count = 0
parser.loop_count = 0
parser.logic_count = 0
parser.current_loops = []  # This is needed for break and continue statements to be checked
parser.array_assign_items = 0
parser.indexing_depth = []
parser.arr_dim = []

# Inicializar Scope
parser.current_scope: Scope = Scope(name="Global Scope", level=0, parent=None)

# Inicializar type checker
parser.type_checker = TypeCheck()


if __name__ == "__main__":
    for line in sys.stdin:
        parser.parse(line)
