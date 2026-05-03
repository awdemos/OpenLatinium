"""CLI compilation orchestration for the OpenLatinum compiler.

The compiler supports three parser paths, selected via CLI flags:

1. Legacy parser (default): Uses the original PLY-based parser and lexer.
   Stable and well-tested. Use for production builds.

2. AST parser (--ast): Uses a modern recursive descent parser that builds
   an AST before semantic analysis. More maintainable and extensible.

3. RD parser (--rd): Uses a direct recursive descent parser without an
   explicit AST. Experimental, for teaching and experimentation.

The --ir and --opt flags require --ast or --rd and enable the IR-based
compilation pipeline with optional optimization.
"""

import os

from lat.cli.utils import info_cmd, run_vms_py
from lat.cli.args import error
from lat.utils.colors import COLOR_RED, COLOR_YELLOW, RESET_COLOR


def _compile_rd(content: str, opt_args: OptArgs) -> str:
    """Compile using the RD parser path."""
    from lat.parsing.rd_parser import parse_text
    from lat.semantic.analyzer import analyze_program
    program = parse_text(content)
    success, errors, warnings = analyze_program(program)
    if not success:
        for e in errors:
            print(f"{COLOR_RED}[SEMANTIC ERROR]{RESET_COLOR} {e.message}")
        raise SystemExit(1)
    for w in warnings:
        print(f"{COLOR_YELLOW}[WARNING]{RESET_COLOR} {w.message}")
    if opt_args.get("--ir"):
        from lat.ir.generator import IRGenerator
        from lat.codegen.from_ir import IRCodeGenerator
        ir_gen = IRGenerator()
        ir_program = ir_gen.generate(program)
        if opt_args.get("--opt"):
            from lat.ir.optimizer import IROptimizer
            optimizer = IROptimizer()
            ir_program = optimizer.optimize(ir_program)
        codegen = IRCodeGenerator()
        return codegen.generate(ir_program)
    else:
        from lat.codegen.generator import generate as ast_generate
        return ast_generate(program)


def _compile_ast(content: str, opt_args: OptArgs) -> str:
    """Compile using the AST parser path."""
    from lat.parsing.ast_parser import parse as ast_parse
    from lat.semantic.analyzer import analyze_program
    program = ast_parse(content)
    success, errors, warnings = analyze_program(program)
    if not success:
        for e in errors:
            print(f"{COLOR_RED}[SEMANTIC ERROR]{RESET_COLOR} {e.message}")
        raise SystemExit(1)
    for w in warnings:
        print(f"{COLOR_YELLOW}[WARNING]{RESET_COLOR} {w.message}")
    if opt_args.get("--ir"):
        from lat.ir.generator import IRGenerator
        from lat.codegen.from_ir import IRCodeGenerator
        ir_gen = IRGenerator()
        ir_program = ir_gen.generate(program)
        if opt_args.get("--opt"):
            from lat.ir.optimizer import IROptimizer
            optimizer = IROptimizer()
            ir_program = optimizer.optimize(ir_program)
        codegen = IRCodeGenerator()
        return codegen.generate(ir_program)
    else:
        from lat.codegen.generator import generate as ast_generate
        return ast_generate(program)


def _compile_legacy(content: str, opt_args: OptArgs) -> str:
    """Compile using the legacy parser path."""
    from lat.parsing._parser import parser as legacy_parser
    legacy_parser.input = content
    return legacy_parser.parse(content)


from typing import Dict, Union

OptArgs = Dict[str, Union[str, bool]]
ReqArgs = Dict[str, Union[str, bool]]


def build_execute(req_args: ReqArgs, opt_args: OptArgs) -> None:
    """Build/compile a .lat file to bytecode."""
    if not req_args.get("input"):
        error("No input file specified.")
    with open(req_args["input"], "r") as f:
        info_cmd(f"Compiling {req_args['input']}", verbose=opt_args.get("-v", False))
        content = f.read()
        if content.startswith("//SKIP"):
            raise SystemExit(2)
        if opt_args.get("--rd"):
            output = _compile_rd(content, opt_args)
        elif opt_args.get("--ast") or opt_args.get("--ir"):
            output = _compile_ast(content, opt_args)
        else:
            output = _compile_legacy(content, opt_args)
        if not opt_args.get("-o"):
            opt_args["-o"] = os.path.splitext(req_args["input"])[0] + ".vms"
        with open(opt_args["-o"], "w") as f:
            f.write(output)


def check_execute(req_args: ReqArgs, opt_args: OptArgs) -> None:
    """Run semantic checks on a .lat file."""
    if not req_args.get("input"):
        error("No input file specified.")
    with open(req_args["input"], "r") as f:
        info_cmd(f"Checking {req_args['input']}", verbose=opt_args.get("-v", False))
        content = f.read()
        if content.startswith("//SKIP"):
            raise SystemExit(2)
        if opt_args.get("--rd"):
            from lat.parsing.rd_parser import parse_text
            from lat.semantic.analyzer import analyze_program
            program = parse_text(content)
        else:
            from lat.parsing.ast_parser import parse as ast_parse
            from lat.semantic.analyzer import analyze_program
            program = ast_parse(content)
        success, errors, warnings = analyze_program(program)
        if not success:
            for e in errors:
                print(f"{COLOR_RED}[SEMANTIC ERROR]{RESET_COLOR} {e.message}")
            raise SystemExit(1)
        for w in warnings:
            print(f"{COLOR_YELLOW}[WARNING]{RESET_COLOR} {w.message}")
        info_cmd("Semantic check passed.", verbose=opt_args.get("-v", False))


def run_execute(req_args: ReqArgs, opt_args: OptArgs) -> None:
    """Compile and run a .lat file."""
    if not req_args.get("input"):
        error("No input file specified.")
    if not opt_args.get("-o"):
        opt_args["-o"] = os.path.splitext(req_args["input"])[0] + ".vms"
    build_execute(req_args, opt_args)
    info_cmd(f"Running {opt_args['-o']}", verbose=opt_args.get("-v", False))
    ret = run_vms_py(opt_args['-o'], verbose=opt_args.get("-v", False))
    if ret[0] == 1:
        print(ret[1])
        raise SystemExit(1)
    print(ret[1], end='')
