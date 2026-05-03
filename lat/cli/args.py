"""CLI argument parsing for the OpenLatinum compiler."""

from typing import Tuple, Dict, Union, Optional
import sys

from lat.utils.colors import COLOR_BLUE, COLOR_GREEN, COLOR_RED, RESET_COLOR
from lat.utils.errors import CompilationError
from lat.cli.utils import warn_cmd


OptArgs = Dict[str, Union[str, bool]]
ReqArgs = Dict[str, Union[str, bool]]

POSSIBLE_EXEC_MODES = ["run", "build", "test", "euler", "examples"]
POSSIBLE_OPT_ARGS = [
    "-o", "--output", "-v", "--verbose", "-rec", "--record",
    "-clc", "--clean-up", "--ast", "--check", "--ir", "--opt", "--rd"
]
RECOGNIZED_ARGS = POSSIBLE_EXEC_MODES + POSSIBLE_OPT_ARGS


def print_help() -> None:
    """Print the CLI help message."""
    print(f"{COLOR_BLUE}Usage{RESET_COLOR}: lat [EXECUTION MODE] [ARGUMENTS] [OPTIONS]")
    print()
    print(f"{COLOR_BLUE}ARGUMENTS{RESET_COLOR}:")
    print(f"  {COLOR_GREEN}input{RESET_COLOR}  The input file. Must be a '.lat' file.")
    print()
    print(f"{COLOR_BLUE}EXECUTION MODES{RESET_COLOR}:")
    print(f"  {COLOR_GREEN}run{RESET_COLOR}        Compiles and runs the program.")
    print(f"  {COLOR_GREEN}build{RESET_COLOR}      Compile the program to bytecode.")
    print(f"  {COLOR_GREEN}euler{RESET_COLOR}      Check the solutions of the Euler problems.")
    print(f"  {COLOR_GREEN}test{RESET_COLOR}       Compile and run the test programs. Compare the outputs with the expected outputs.")
    print(f"  {COLOR_GREEN}examples{RESET_COLOR}   Compile and run the example programs. Compare the outputs with the expected outputs.")
    print()
    print(f"{COLOR_BLUE}OPTIONS{RESET_COLOR}:")
    print(f"  {COLOR_GREEN}-h{RESET_COLOR}, {COLOR_GREEN}--help{RESET_COLOR}" + " " * 10 + "Show this help message and exit.")
    print(f"  {COLOR_GREEN}-o{RESET_COLOR}, {COLOR_GREEN}--output{RESET_COLOR}" + " " * 8 + "Specify the output file.")
    print(f"  {COLOR_GREEN}-rec{RESET_COLOR}, {COLOR_GREEN}--record{RESET_COLOR}" + " " * 6 + "Record the output of the executed programs.")
    print(f"  {COLOR_GREEN}-clc{RESET_COLOR}, {COLOR_GREEN}--clean-up{RESET_COLOR}" + " " * 4 + "Clear the output of the executed programs.")
    print(f"  {COLOR_GREEN}-v{RESET_COLOR}, {COLOR_GREEN}--verbose{RESET_COLOR}" + " " * 7 + "Show verbose output.")


def error(msg: str) -> None:
    """Print an error message and raise CompilationError."""
    print(f"{COLOR_RED}[ERROR]{RESET_COLOR}", msg)
    raise CompilationError(msg)


def prepare_cmd_args() -> Tuple[Optional[OptArgs], Optional[ReqArgs]]:
    """Parse and return command-line arguments.
    
    Returns (None, None) if --help was requested.
    """
    if "-h" in sys.argv or "--help" in sys.argv:
        print_help()
        return None, None

    # Handle Optional Arguments
    input_file: Optional[str] = None
    for arg in sys.argv[1:]:
        if arg.endswith(".lat"):
            input_file = arg
            continue
        if arg not in RECOGNIZED_ARGS:
            if "-o" in sys.argv and sys.argv.index("-o") == sys.argv.index(arg) - 1:
                continue
            error(f"Unrecognized argument: {arg}. Use -h or --help to see the help message.")

    output_file = sys.argv[sys.argv.index("-o") + 1] if "-o" in sys.argv else None
    rec = "-rec" in sys.argv
    clc = "-clc" in sys.argv
    verbose = "-v" in sys.argv
    use_ast = "--ast" in sys.argv
    check_only = "--check" in sys.argv
    use_ir = "--ir" in sys.argv
    use_opt = "--opt" in sys.argv
    use_rd = "--rd" in sys.argv

    if verbose:
        warn_cmd("Verbose output is not implemented yet.")

    opt_args: OptArgs = {
        "-o": output_file,
        "-v": verbose,
        "-rec": rec,
        "-clc": clc,
        "--ast": use_ast,
        "--check": check_only,
        "--ir": use_ir,
        "--opt": use_opt,
        "--rd": use_rd,
    }

    # Handle Required Arguments
    run = "run" in sys.argv
    build = "build" in sys.argv
    test = "test" in sys.argv
    euler = "euler" in sys.argv
    examples = "examples" in sys.argv
    modes = [run, build, test, euler, examples]
    active_modes = [m for m in modes if m]
    if len(active_modes) == 0:
        error("No execution mode specified. (run, build, test, euler, examples)")
    if len(active_modes) > 1:
        error("Multiple execution modes specified.")

    req_args: ReqArgs = {
        "input": input_file,
        "run": run,
        "build": build,
        "test": test,
        "euler": euler,
        "examples": examples,
    }

    return opt_args, req_args
