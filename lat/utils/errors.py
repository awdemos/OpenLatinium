from typing import List, Any

import sys

from lat.utils.colors import COLOR_RED, COLOR_YELLOW, COLOR_GREEN, RESET_COLOR, COLOR_BLUE


class CompilationError(Exception):
    """Raised when the compiler encounters a fatal error."""

    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(message)


def find_column(input: str, token: Any) -> int:
    """
    Compute the column of a given token.
    """
    last_cr = input.rfind("\n", 0, token.lexpos) + 1
    return (token.lexpos - last_cr) + 1


def find_column_comp(input: str, token: Any, n: int) -> int:
    """
    Compute the column of a given token.
    """
    last_cr = input.rfind("\n", 0, token.lexpos(n)) + 1
    return (token.lexpos(n) - last_cr) + 1


def lex_error(p: Any, msg: str) -> None:
    """
    Report a lex error.
    """
    sys.stderr.write(f"{COLOR_RED}Lex Error:{COLOR_YELLOW}{p.lineno}:{COLOR_GREEN}{find_column(p.lexer.lexdata, p)}:{RESET_COLOR} {msg}\n")


def syntax_error(p: Any, msg: str) -> None:
    """
    Report a syntax error with source context.
    """
    line_no = p.lineno
    col = find_column(p.lexer.lexdata, p)
    lines = p.lexer.lexdata.split('\n')
    source_line = lines[line_no - 1] if line_no <= len(lines) else ""
    
    output = []
    output.append(f"{COLOR_RED}Syntax Error:{COLOR_YELLOW}{line_no}:{COLOR_GREEN}{col}:{RESET_COLOR} {msg}")
    if source_line:
        output.append(f"   {COLOR_BLUE}|{RESET_COLOR}")
        output.append(f"{COLOR_YELLOW}{line_no:3}{RESET_COLOR} {COLOR_BLUE}|{RESET_COLOR} {source_line}")
        caret = " " * (col - 1) + "^"
        output.append(f"   {COLOR_BLUE}|{RESET_COLOR} {COLOR_RED}{caret}{RESET_COLOR}")
    
    sys.stderr.write("\n".join(output) + "\n")


def compiler_error(p: Any, n: int, msg: str) -> None:
    """
    Report a compiler error.
    """
    if p is None:
        sys.stderr.write(f"{COLOR_RED}Compiler Error:{RESET_COLOR} {msg}\n")
    else:
        sys.stderr.write(f"{COLOR_RED}Compiler Error:{COLOR_YELLOW}{p.lineno(n)}:{COLOR_GREEN}{find_column_comp(p.parser.input, p, n)}:{RESET_COLOR} {msg}\n")


def compiler_warning(p: Any, n: int, msg: str) -> None:
    """
    Report a compiler warning.
    """
    sys.stderr.write(f"{COLOR_YELLOW}Compiler Warning:{COLOR_YELLOW}{p.lineno(n)}:{COLOR_GREEN}{find_column_comp(p.parser.input, p, n)}:{RESET_COLOR} {msg}\n")


def compiler_note(msg: str) -> None:
    """
    Report a compiler note.
    """
    sys.stderr.write(f"{COLOR_BLUE}Compiler Note:{RESET_COLOR} {msg}\n")


def std_message(msg: List[str]) -> str:
    """
    Helper function to print an operation message.
    """
    return "\n".join(msg) + "\n"
