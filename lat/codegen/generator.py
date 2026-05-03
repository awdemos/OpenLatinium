import sys
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field

from lat.ast import nodes
from lat.utils.errors import compiler_error, compiler_note
from lat.utils.errors import std_message


@dataclass
class VarInfo:
    name: str
    type: str
    stack_pos: int
    is_global: bool
    array_shape: Optional[List[int]] = None
    p_init: bool = True
    base_pos: int = 0


@dataclass
class Scope:
    variables: Dict[str, VarInfo] = field(default_factory=dict)
    parent: Optional['Scope'] = None
    is_function: bool = False
    function_name: Optional[str] = None
    
    def get(self, name: str) -> Optional[VarInfo]:
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        return None
    
    def add(self, var: VarInfo):
        self.variables[var.name] = var


class CodeGenerator:
    def __init__(self):
        self.global_count = 0
        self.frame_count = 0
        self.current_scope: Optional[Scope] = None
        self.functions: Dict[str, nodes.Function] = {}
        self.type_stack: List[str] = []
        self.label_counter = 0
        self.loop_count = 0
        self.loop_stack: List[str] = []
        self.current_function: Optional[nodes.Function] = None
        
    def new_label(self, prefix: str = "L") -> str:
        self.label_counter += 1
        return f"{prefix}{self.label_counter}"
    
    def new_loop_labels(self) -> Tuple[str, str, str]:
        self.loop_count += 1
        count = self.loop_count
        return (f"LOOP{count}START", f"LOOP{count}END", f"NEXTLOOP{count}")
    
    def push_type(self, t: str):
        self.type_stack.append(t)
    
    def pop_type(self) -> str:
        if not self.type_stack:
            return "None"
        return self.type_stack.pop()
    
    def generate(self, program: nodes.Program) -> str:

        for func in program.functions:
            self.functions[func.name] = func
        

        self.current_scope = Scope()
        

        globals_code = ""
        for decl in program.globals:
            globals_code += self.gen_decl(decl)
        

        funcs_code = ""
        for func in program.functions:
            funcs_code += self.gen_function(func)
        

        main_code = "start\n"
        main_code += "PUSHA main\n"
        main_code += "CALL\n"
        main_code += "stop\n"
        
        return globals_code + main_code + funcs_code
    
    def gen_function(self, func: nodes.Function) -> str:
        self.current_function = func
        label = func.name.replace('_', '')
        

        func_scope = Scope(parent=self.current_scope, is_function=True, function_name=func.name)
        self.current_scope = func_scope
        self.frame_count = 0
        

        param_code = ""
        for i, param in enumerate(func.params):
            orig_pos = -(len(func.params) - i)
            local_pos = i
            var = VarInfo(name=param.name, type=param.type, stack_pos=local_pos, is_global=False, base_pos=orig_pos)
            func_scope.add(var)
            param_code += f"PUSHI 0\nPUSHFP\nLOAD {orig_pos}\nSTOREL {local_pos}\n"
            self.frame_count += 1
        

        body_code = ""
        for stmt in func.body:
            body_code += self.gen_stmt(stmt)
        

        if func.return_type is None:
            if not body_code.strip().endswith("RETURN"):
                body_code += "RETURN\n"
        
        self.current_scope = func_scope.parent
        self.current_function = None
        
        return f"{label}:\n{param_code}{body_code}"
    
    def gen_stmt(self, stmt) -> str:
        if isinstance(stmt, nodes.Decl):
            return self.gen_decl(stmt)
        elif isinstance(stmt, nodes.Assignment):
            return self.gen_assignment(stmt)
        elif isinstance(stmt, nodes.Print):
            return self.gen_print(stmt)
        elif isinstance(stmt, nodes.Read):
            return self.gen_read(stmt)
        elif isinstance(stmt, nodes.If):
            return self.gen_if(stmt)
        elif isinstance(stmt, nodes.While):
            return self.gen_while(stmt)
        elif isinstance(stmt, nodes.DoWhile):
            return self.gen_do_while(stmt)
        elif isinstance(stmt, nodes.For):
            return self.gen_for(stmt)
        elif isinstance(stmt, nodes.Match):
            return self.gen_match(stmt)
        elif isinstance(stmt, nodes.Return):
            return self.gen_return(stmt)
        elif isinstance(stmt, nodes.Break):
            return self.gen_break()
        elif isinstance(stmt, nodes.Continue):
            return self.gen_continue()
        elif isinstance(stmt, nodes.FunctionCall):
            return self.gen_function_call(stmt)
        elif isinstance(stmt, nodes.Debug):
            return "\n"
        else:
            return ""
    
    def gen_decl(self, decl: nodes.Decl) -> str:
        if decl.name in self.current_scope.variables:
            compiler_error(None, 1, f"Variable {decl.name} is already defined")
            compiler_note("Called from CodeGenerator.gen_decl")
            sys.exit(1)
        
        is_global = self.current_scope.parent is None
        
        if decl.type.startswith("vec<"):

            if decl.value and isinstance(decl.value, nodes.ArrayRange):
                size = decl.value.end - decl.value.start
                array_shape = [size]
            elif decl.value and isinstance(decl.value, nodes.ArrayLiteral):
                size = len(decl.value.items)
                array_shape = [size]
            else:
                size = 0
                array_shape = [0]
            
            pos = self.global_count if is_global else self.frame_count
            var = VarInfo(name=decl.name, type=decl.type, stack_pos=pos, is_global=is_global, array_shape=array_shape)
            self.current_scope.add(var)
            
            if is_global:
                self.global_count += size
            else:
                self.frame_count += size
            
            code = ""
            if decl.value and isinstance(decl.value, nodes.ArrayLiteral):
                for item in decl.value.items:
                    code += self.gen_expr(item)
                    self.pop_type()
            elif decl.type == "vec<integer>":
                code += f"PUSHN {size}\n"
            elif decl.type == "vec<float>":
                code += "\n".join(["PUSHF 0.0"] * size) + "\n" if size > 0 else ""
            elif decl.type == "vec<filum>":
                code += "\n".join(["PUSHS ''"] * size) + "\n" if size > 0 else ""
            return code
        
        elif decl.type.startswith("&"):

            pos = self.global_count if is_global else self.frame_count
            var = VarInfo(name=decl.name, type=decl.type, stack_pos=pos, is_global=is_global, p_init=False)
            self.current_scope.add(var)
            
            if is_global:
                self.global_count += 1
            else:
                self.frame_count += 1
            
            push_op = "PUSHGP" if is_global else "PUSHFP"
            return f"{push_op}\nPUSHI {pos}\nPADD\n"
        else:

            pos = self.global_count if is_global else self.frame_count
            var = VarInfo(name=decl.name, type=decl.type, stack_pos=pos, is_global=is_global)
            self.current_scope.add(var)
            
            if is_global:
                self.global_count += 1
            else:
                self.frame_count += 1
            
            code = ""
            if decl.value:
                code += self.gen_expr(decl.value)
                self.pop_type()
            else:
                if decl.type == "integer":
                    code += "PUSHI 0\n"
                elif decl.type == "float":
                    code += "PUSHF 0.0\n"
                elif decl.type == "filum":
                    code += "PUSHS ''\n"
            
            return code
    
    def gen_store(self, var: VarInfo) -> str:
        if var.is_global:
            return f"STOREG {var.stack_pos}\n"
        else:
            return f"STOREL {var.stack_pos}\n"
    
    def gen_load(self, var: VarInfo) -> str:
        if var.is_global:
            return f"PUSHGP\nLOAD {var.stack_pos}\n"
        else:
            return f"PUSHFP\nLOAD {var.stack_pos}\n"
    
    def gen_assignment(self, assign: nodes.Assignment) -> str:
        if isinstance(assign.target, nodes.Identifier):
            code = self.gen_expr(assign.value)
            var = self.current_scope.get(assign.target.name)
            if var is None:
                compiler_error(None, 1, f"Variable {assign.target.name} not declared")
                compiler_note("Called from CodeGenerator.gen_assignment")
                sys.exit(1)
            code += self.gen_store(var)
        elif isinstance(assign.target, nodes.ArrayIndex):
            var = self.current_scope.get(assign.target.name)
            if var is None:
                compiler_error(None, 1, f"Variable {assign.target.name} not declared")
                compiler_note("Called from CodeGenerator.gen_assignment")
                sys.exit(1)
            
            push_op = "PUSHGP" if var.is_global else "PUSHFP"
            code = f"{push_op}\nPUSHI {var.stack_pos}\nPADD\n"
            for idx in assign.target.indices:
                code += self.gen_expr(idx)
                code += "PADD\n"
            code += self.gen_expr(assign.value)
            code += "STORE 0\n"
        else:
            code = self.gen_expr(assign.value)
        
        return code
    
    def gen_print(self, print_stmt: nodes.Print) -> str:
        code = ""
        for expr in print_stmt.expressions:
            code += self.gen_expr(expr)
            t = self.pop_type()
            if t == "integer":
                code += "WRITEI\n"
            elif t == "float":
                code += "WRITEF\n"
            elif t == "filum":
                code += "WRITES\n"
        return code
    
    def gen_read(self, read_stmt: nodes.Read) -> str:
        code = ""
        if read_stmt.read_type == "legerei":
            code += "READI\n"
            self.push_type("integer")
        elif read_stmt.read_type == "legeref":
            code += "READF\n"
            self.push_type("float")
        elif read_stmt.read_type == "legeres":
            code += "READS\n"
            self.push_type("filum")
        

        if read_stmt.expressions:
            for expr in read_stmt.expressions:
                if isinstance(expr, nodes.Identifier):
                    var = self.current_scope.get(expr.name)
                    if var:
                        code += self.gen_store(var)
        
        return code
    
    def gen_if(self, if_stmt: nodes.If) -> str:
        else_label = self.new_label("ELSE")
        end_label = self.new_label("ENDIF")
        
        code = self.gen_expr(if_stmt.condition)
        code += f"JZ {else_label}\n"
        
        then_scope = Scope(parent=self.current_scope)
        self.current_scope = then_scope
        prev_frame = self.frame_count
        
        for stmt in if_stmt.then_body:
            code += self.gen_stmt(stmt)
        
        num_popped = self.frame_count - prev_frame
        if num_popped > 0:
            code += f"POP {num_popped}\n"
        self.frame_count = prev_frame
        self.current_scope = then_scope.parent
        
        code += f"JUMP {end_label}\n"
        code += f"{else_label}:\n"
        
        if if_stmt.else_body:
            else_scope = Scope(parent=self.current_scope)
            self.current_scope = else_scope
            prev_frame = self.frame_count
            
            if isinstance(if_stmt.else_body, list):
                for stmt in if_stmt.else_body:
                    code += self.gen_stmt(stmt)
            elif isinstance(if_stmt.else_body, nodes.If):
                code += self.gen_if(if_stmt.else_body)
            else:
                code += self.gen_stmt(if_stmt.else_body)
            
            num_popped = self.frame_count - prev_frame
            if num_popped > 0:
                code += f"POP {num_popped}\n"
            self.frame_count = prev_frame
            self.current_scope = else_scope.parent
        
        code += f"{end_label}:\n"
        return code
    
    def gen_while(self, while_stmt: nodes.While) -> str:
        start_label, end_label, next_label = self.new_loop_labels()
        self.loop_stack.append(end_label)
        
        loop_scope = Scope(parent=self.current_scope)
        self.current_scope = loop_scope
        prev_frame_count = self.frame_count
        
        code = f"{start_label}:\n"
        code += self.gen_expr(while_stmt.condition)
        code += f"JZ {end_label}\n"
        
        for stmt in while_stmt.body:
            code += self.gen_stmt(stmt)
        
        code += f"NEXTLOOP{self.loop_count}:\n"
        code += f"JUMP {start_label}\n"
        code += f"{end_label}:\n"
        
        num_popped = self.frame_count - prev_frame_count
        if num_popped > 0:
            code += f"POP {num_popped}\n"
        self.frame_count = prev_frame_count
        
        self.current_scope = loop_scope.parent
        self.loop_stack.pop()
        return code
    
    def gen_do_while(self, do_while: nodes.DoWhile) -> str:
        start_label, end_label, next_label = self.new_loop_labels()
        self.loop_stack.append(end_label)
        
        loop_scope = Scope(parent=self.current_scope)
        self.current_scope = loop_scope
        prev_frame_count = self.frame_count
        
        code = f"{start_label}:\n"
        for stmt in do_while.body:
            code += self.gen_stmt(stmt)
        
        code += f"NEXTLOOP{self.loop_count}:\n"
        code += self.gen_expr(do_while.condition)
        code += f"JZ {end_label}\n"
        code += f"JUMP {start_label}\n"
        code += f"{end_label}:\n"
        
        num_popped = self.frame_count - prev_frame_count
        if num_popped > 0:
            code += f"POP {num_popped}\n"
        self.frame_count = prev_frame_count
        
        self.current_scope = loop_scope.parent
        self.loop_stack.pop()
        return code
    
    def gen_for(self, for_stmt: nodes.For) -> str:
        start_label, end_label, next_label = self.new_loop_labels()
        self.loop_stack.append(end_label)
        
        loop_scope = Scope(parent=self.current_scope)
        self.current_scope = loop_scope
        prev_frame_count = self.frame_count
        
        code = ""
        for init in for_stmt.init:
            if init:
                code += self.gen_stmt(init)
        
        code += f"{start_label}:\n"
        code += self.gen_expr(for_stmt.condition)
        code += f"JZ {end_label}\n"
        
        for stmt in for_stmt.body:
            code += self.gen_stmt(stmt)
        
        code += f"NEXTLOOP{self.loop_count}:\n"
        for update in for_stmt.update:
            code += self.gen_stmt(update)
        
        code += f"JUMP {start_label}\n"
        code += f"{end_label}:\n"
        
        num_popped = self.frame_count - prev_frame_count
        if num_popped > 0:
            code += f"POP {num_popped}\n"
        self.frame_count = prev_frame_count
        
        self.current_scope = loop_scope.parent
        self.loop_stack.pop()
        return code
    
    def gen_match(self, match_stmt: nodes.Match) -> str:
        end_label = self.new_label("ENDMATCH")
        code = self.gen_expr(match_stmt.expression)
        
        for case in match_stmt.cases:
            if isinstance(case, nodes.Case):
                case_label = self.new_label("CASE")
                next_case_label = self.new_label("NEXTCASE")
                code += f"DUP 1\n"
                code += self.gen_expr(case.value)
                code += "EQUAL\n"
                code += f"JZ {next_case_label}\n"
                
                case_scope = Scope(parent=self.current_scope)
                self.current_scope = case_scope
                prev_frame = self.frame_count
                
                for stmt in case.body:
                    code += self.gen_stmt(stmt)
                
                num_popped = self.frame_count - prev_frame
                if num_popped > 0:
                    code += f"POP {num_popped}\n"
                self.frame_count = prev_frame
                self.current_scope = case_scope.parent
                
                code += f"JUMP {end_label}\n"
                code += f"{next_case_label}:\n"
            elif isinstance(case, nodes.Default):
                default_scope = Scope(parent=self.current_scope)
                self.current_scope = default_scope
                prev_frame = self.frame_count
                
                for stmt in case.body:
                    code += self.gen_stmt(stmt)
                
                num_popped = self.frame_count - prev_frame
                if num_popped > 0:
                    code += f"POP {num_popped}\n"
                self.frame_count = prev_frame
                self.current_scope = default_scope.parent
        
        code += f"{end_label}:\n"
        return code
    
    def gen_return(self, ret: nodes.Return) -> str:
        code = ""
        if ret.value:
            code += self.gen_expr(ret.value)
            if self.current_function and self.current_function.return_type:
                num_params = len(self.current_function.params)
                code += f"STOREL {-(num_params + 1)}\n"
        code += "RETURN\n"
        return code
    
    def gen_break(self) -> str:
        if not self.loop_stack:
            compiler_error(None, 1, "'break' statement not allowed outside of a loop")
            compiler_note("Called from CodeGenerator.gen_break")
            sys.exit(1)
        return f"JUMP {self.loop_stack[-1]}\n"
    
    def gen_continue(self) -> str:
        if not self.loop_stack:
            compiler_error(None, 1, "'continue' statement not allowed outside of a loop")
            compiler_note("Called from CodeGenerator.gen_continue")
            sys.exit(1)
        return f"JUMP {self.loop_stack[-1]}\n"
    
    def gen_function_call(self, call: nodes.FunctionCall) -> str:
        func = self.functions.get(call.name)
        if func is None:
            compiler_error(None, 1, f"Function {call.name} not declared")
            compiler_note("Called from CodeGenerator.gen_function_call")
            sys.exit(1)
        
        code = ""
        if func.return_type:
            code += "PUSHI -69\n"
        
        for arg in call.args:
            code += self.gen_expr(arg)
        
        label = call.name.replace('_', '')
        code += f"PUSHA {label}\nCALL\n"
        
        if func.params:
            code += f"POP {len(func.params)}\n"
        
        if func.return_type:
            self.push_type(func.return_type)
        
        return code
    
    def gen_expr(self, expr) -> str:
        if isinstance(expr, nodes.IntegerLiteral):
            self.push_type("integer")
            return f"PUSHI {expr.value}\n"
        elif isinstance(expr, nodes.FloatLiteral):
            self.push_type("float")
            return f"PUSHF {expr.value}\n"
        elif isinstance(expr, nodes.StringLiteral):
            self.push_type("filum")
            return f"PUSHS {expr.value}\n"
        elif isinstance(expr, nodes.Identifier):
            var = self.current_scope.get(expr.name)
            if var is None:
                compiler_error(None, 1, f"Variable {expr.name} not declared")
                compiler_note("Called from CodeGenerator.gen_expr")
                sys.exit(1)
            self.push_type(var.type)
            return self.gen_load(var)
        elif isinstance(expr, nodes.BinaryOp):
            return self.gen_binary_op(expr)
        elif isinstance(expr, nodes.UnaryOp):
            return self.gen_unary_op(expr)
        elif isinstance(expr, nodes.ArrayIndex):
            return self.gen_array_index(expr)
        elif isinstance(expr, nodes.Ref):
            return self.gen_ref(expr)
        elif isinstance(expr, nodes.FunctionCall):
            return self.gen_function_call(expr)
        elif isinstance(expr, nodes.Read):
            return self.gen_read(expr)
        elif isinstance(expr, nodes.ArrayLiteral):

            return ""
        else:
            return ""
    
    def gen_binary_op(self, expr: nodes.BinaryOp) -> str:
        code = self.gen_expr(expr.left)
        code += self.gen_expr(expr.right)
        
        left_type = self.pop_type()
        right_type = self.pop_type()
        
        op = expr.op
        if op == '+':
            if left_type == right_type == "integer":
                self.push_type("integer")
                code += "ADD\n"
            elif left_type == right_type == "float":
                self.push_type("float")
                code += "FADD\n"
            elif left_type == right_type == "filum":
                self.push_type("filum")
                code += "CONCAT\n"
            elif left_type.startswith("&") and right_type == "integer":
                self.push_type(left_type)
                code += "PADD\n"
        elif op == '-':
            if left_type == right_type == "integer":
                self.push_type("integer")
                code += "SUB\n"
            elif left_type == right_type == "float":
                self.push_type("float")
                code += "FSUB\n"
            elif left_type.startswith("&") and right_type == "integer":
                self.push_type(left_type)
                code += "PUSHI -1\nMUL\nPADD\n"
        elif op == '*':
            if left_type == right_type == "integer":
                self.push_type("integer")
                code += "MUL\n"
            elif left_type == right_type == "float":
                self.push_type("float")
                code += "FMUL\n"
        elif op == '/':
            if left_type == right_type == "integer":
                self.push_type("integer")
                code += "DIV\n"
            elif left_type == right_type == "float":
                self.push_type("float")
                code += "FDIV\n"
        elif op == '%':
            if left_type == right_type == "integer":
                self.push_type("integer")
                code += "MOD\n"
        elif op == 'EQ':
            if left_type == right_type and left_type != "filum":
                self.push_type("integer")
                code += "EQUAL\n"
        elif op == 'NEQ':
            if left_type == right_type and left_type != "filum":
                self.push_type("integer")
                code += "EQUAL\nNOT\n"
        elif op == 'LT':
            if left_type == right_type and left_type not in ("filum", "float"):
                self.push_type("integer")
                code += "INF\n"
            elif left_type == right_type == "float":
                self.push_type("integer")
                code += "FINF\nFTOI\n"
        elif op == 'GT':
            if left_type == right_type and left_type not in ("filum", "float"):
                self.push_type("integer")
                code += "SUP\n"
            elif left_type == right_type == "float":
                self.push_type("integer")
                code += "FSUP\nFTOI\n"
        elif op == 'LTE':
            if left_type == right_type and left_type not in ("filum", "float"):
                self.push_type("integer")
                code += "INFEQ\n"
            elif left_type == right_type == "float":
                self.push_type("integer")
                code += "FINFEQ\nFTOI\n"
        elif op == 'GTE':
            if left_type == right_type and left_type not in ("filum", "float"):
                self.push_type("integer")
                code += "SUPEQ\n"
            elif left_type == right_type == "float":
                self.push_type("integer")
                code += "FSUPEQ\nFTOI\n"
        elif op == 'AND':
            if left_type == right_type == "integer":
                self.push_type("integer")
                count = self.label_counter
                self.label_counter += 1
                code += f"DUP 1\nJZ AND{count}END\nPOP 1\n"
                code += self.gen_expr(expr.right)
                code += f"AND{count}END:\n"
        elif op == 'OR':
            if left_type == right_type == "integer":
                self.push_type("integer")
                count = self.label_counter
                self.label_counter += 1
                code += f"DUP 1\nJZ OR{count}RIGHT\nJUMP OR{count}END\nOR{count}RIGHT:\nPOP 1\n"
                code += self.gen_expr(expr.right)
                code += f"OR{count}END:\n"
        
        return code
    
    def gen_unary_op(self, expr: nodes.UnaryOp) -> str:
        code = self.gen_expr(expr.operand)
        op_type = self.pop_type()
        
        if expr.op == 'NOT':
            if op_type in ("integer", "float"):
                self.push_type(op_type)
                code += "NOT\n"
        elif expr.op == '-':
            if op_type == "integer":
                self.push_type("integer")
                code += "PUSHI -1\nMUL\n"
            elif op_type == "float":
                self.push_type("float")
                code += "PUSHF -1.0\nFMUL\n"
        
        return code
    
    def gen_array_index(self, expr: nodes.ArrayIndex) -> str:
        var = self.current_scope.get(expr.name)
        if var is None:
            compiler_error(None, 1, f"Variable {expr.name} not declared")
            compiler_note("Called from CodeGenerator.gen_array_index")
            sys.exit(1)
        
        push_op = "PUSHGP" if var.is_global else "PUSHFP"
        
        if var.type.startswith("&"):
            code = f"{push_op}\nLOAD {var.stack_pos}\n"
        else:
            code = f"{push_op}\nPUSHI {var.stack_pos}\nPADD\n"
        
        for idx in expr.indices:
            code += self.gen_expr(idx)
            code += "PADD\n"
        
        if var.type.startswith("vec<"):
            elem_type = var.type[4:-1]
            self.push_type(elem_type)
        elif var.type.startswith("&"):
            elem_type = var.type[1:]
            self.push_type(elem_type)
        else:
            self.push_type(var.type)
        
        code += "LOAD 0\n"
        return code
    
    def gen_ref(self, expr: nodes.Ref) -> str:
        var = self.current_scope.get(expr.name)
        if var is None:
            compiler_error(None, 1, f"Variable {expr.name} not declared")
            compiler_note("Called from CodeGenerator.gen_ref")
            sys.exit(1)
        
        push_op = "PUSHGP" if var.is_global else "PUSHFP"
        self.push_type(f"&{var.type}")
        return f"{push_op}\nPUSHI {var.stack_pos}\nPADD\n"


def generate(program: nodes.Program) -> str:
    gen = CodeGenerator()
    return gen.generate(program)
