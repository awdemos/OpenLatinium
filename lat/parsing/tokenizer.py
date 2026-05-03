import re
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class Token:
    type: str
    value: str
    line: int
    column: int


class TokenizeError(Exception):
    pass


TOKEN_SPEC = [
    ('COMMENT',     r'//[^\n]*'),
    ('MULTICOMMENT', r'/\*[\s\S]*?\*/'),
    ('NEWLINE',     r'\n+'),
    ('SKIP',        r'[ \t]+'),
    ('FLOAT',       r'\d+f|\d+\.\d+(f)?'),
    ('INTEGER',     r'\d+'),
    ('STRING',      r'"[^"]*"'),
    ('GTE',         r'>='),
    ('LTE',         r'<='),
    ('EQ',          r'=='),
    ('NEQ',         r'!='),
    ('RETI',        r'\.\.\.'),
    ('RARROW',      r'->'),
    ('ASSIGN',      r'='),
    ('LT',          r'<'),
    ('GT',          r'>'),
    ('AND',         r'&&'),
    ('OR',          r'\|\|'),
    ('NOT',         r'!'),
    ('LBRACE',      r'\{'),
    ('RBRACE',      r'\}'),
    ('LPAREN',      r'\('),
    ('RPAREN',      r'\)'),
    ('LBRACKET',    r'\['),
    ('RBRACKET',    r'\]'),
    ('PLUS',        r'\+'),
    ('MINUS',       r'-'),
    ('STAR',        r'\*'),
    ('SLASH',       r'/'),
    ('PERCENT',     r'%'),
    ('AMPERSAND',   r'&'),
    ('COMMA',       r','),
    ('COLON',       r':'),
    ('SEMICOLON',   r';'),
    ('ID',          r'[a-zA-Z_][a-zA-Z0-9_]*'),
]

RESERVED = {
    'imprimo': 'PRINT',
    'legerei': 'READ_INT',
    'legeref': 'READ_FLOAT',
    'legeres': 'READ_STRING',
    'integer': 'TYPE_INT',
    'filum': 'TYPE_STRING',
    'float': 'TYPE_FLOAT',
    'vec': 'TYPE_VEC',
    'si': 'IF',
    'aliter': 'ELSE',
    'par': 'MATCH',
    'defectus': 'DEFAULT',
    'dum': 'WHILE',
    'enim': 'FOR',
    'facio': 'DO',
    'confractus': 'BREAK',
    'pergo': 'CONTINUE',
    'munus': 'FUNCTION',
    'reditus': 'RETURN',
    'et': 'AND',
    'aut': 'OR',
    'non': 'NOT',
    'boolean': 'TYPE_BOOL',
    'verum': 'TRUE',
    'falsum': 'FALSE',
    'constans': 'CONST',
}

TOKEN_RE = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)


def tokenize(text: str) -> Iterator[Token]:
    line = 1
    line_start = 0
    for match in re.finditer(TOKEN_RE, text):
        kind = match.lastgroup
        value = match.group()
        column = match.start() - line_start + 1
        if kind == 'NEWLINE':
            line += len(value)
            line_start = match.end()
            continue
        elif kind in ('SKIP', 'COMMENT', 'MULTICOMMENT'):
            if kind == 'MULTICOMMENT':
                line += value.count('\n')
            continue
        elif kind == 'ID':
            kind = RESERVED.get(value, 'ID')
        elif kind == 'FLOAT':
            # Normalize float literal
            if value[-1] == 'f':
                value = value[:-1]
            if '.' not in value:
                value += '.0'
        elif kind == 'STRING':
            # Keep quotes for now, parser will strip them
            pass
        yield Token(kind, value, line, column)
    yield Token('EOF', '', line, 1)


def tokenize_file(path: str) -> list[Token]:
    with open(path, 'r') as f:
        return list(tokenize(f.read()))
