# OpenLatinum Evolution Analysis
## A 7-Phase Architectural Audit and Forward Design

---

## Phase 0: System Reconstruction — Full Codebase Archaeology

### 0.1 What OpenLatinum Actually Is

OpenLatinum is a **teaching compiler** for a C-like language, built as a syntax-directed translator using Python PLY (Python Lex-Yacc). It compiles source code directly to bytecode for the EWVM (Easy Virtual Machine), a stack-based VM developed at the University of Minho for compiler construction courses.

**Core philosophy**: Single-pass compilation with immediate code emission. No AST. No IR. Parse → Check → Emit, all in one traversal.

### 0.2 Architecture Overview

```
Source (.lat) → Lexer (PLY) → Parser (PLY) → Semantic Handlers → EWVM Bytecode
                                    ↓
                         All state lives on parser object:
                         - scope_tree (nested dicts)
                         - type_checker.stack (list of type strings)
                         - loop_count, current_loops
                         - num_args, functions_handler
```

**File inventory** (~2,900 lines total):

| File | Lines | Role |
|------|-------|------|
| `lat/parsing/_parser.py` | 896 | 80+ PLY grammar productions; parser action dispatch |
| `lat/semantics/_statement.py` | 772 | Statements: declarations, IO, control flow, loops |
| `lat/semantics/_expression.py` | 370 | Expressions: arithmetic, logical, primary, pointers |
| `lat/semantics/_type_check.py` | 280 | Type checking logic (string-based type system) |
| `lat/semantics/_functions.py` | 166 | Function declaration, calls, returns |
| `lat/semantics/_scopes.py` | 108 | Scope tree management (nested dicts) |
| `lat/lexing/_lexer.py` | 123 | PLY lexer: tokens, regexes, reserved words |
| `lat/cli.py` | 329 | Command-line interface, file I/O, execution |
| `lat/utils/errors.py` | 63 | Error reporting (colored stderr output) |
| `lat/gramatica.txt` | — | Informal grammar specification |

### 0.3 The Type System (String-Based)

```python
"integer"       # 32-bit signed int
"float"         # 32-bit float
"filum"         # string (Latin for "thread/string")
"&integer"      # pointer to integer
"&float"        # pointer to float
"&filum"        # pointer to string
"vec<integer>"  # array of integers
"vec<filum>"    # array of strings
```

Types are **plain strings** compared with `==` and `.startswith()`. No type objects. No type hierarchy. No generics beyond hardcoded `vec<...>`.

### 0.4 The Target VM (EWVM)

> **Note**: The VM is no longer shipped as a prebuilt binary in the repository. It is built from source during the Docker image build process using Chainguard's minimal, security-hardened base images. See the `Dockerfile` for details.

Stack-based instruction set. Key instructions:

```
PUSHI n        # Push integer n
PUSHF f        # Push float f
PUSHS "s"      # Push string s
PUSHA addr     # Push address
ADD/SUB/MUL/DIV/MOD
JZ label       # Jump if zero
JUMP label     # Unconditional jump
READI/READF/READS
WRITEI/WRITEF/WRITES
LOAD/STORE     # Dereference pointers
CALL addr      # Function call
RETURN         # Function return
START          # Program entry
STOP           # Program termination
```

### 0.5 The Parser Actions (Critical Pattern)

Every grammar production has an action that:
1. **Delegates** to a handler class method
2. The handler method **checks semantics** (types, scope, initialization)
3. The handler method **returns a bytecode string**
4. The parser action **concatenates** these strings

Example:
```python
def p_statement_print(p):
    """statement : PRINT '(' multiple_prints ')' ';'"""
    p[0] = IO(p.parser)._multiple(p)  # Returns bytecode string
```

There is **no separation** of concerns. The same method that checks "is this variable initialized?" also emits `PUSHI 42\n`.

### 0.6 State Management (The Parser as God Object)

All mutable state hangs off `p.parser`:

```python
p.parser.scope_tree          # Nested dict: scope_name -> {var_name: Meta}
p.parser.type_checker.stack  # List of type strings (expression types)
p.parser.loop_count          # Counter for unique loop labels
p.parser.current_loops       # Stack of loop types ("WHILE", "FOR", "DO")
p.parser.num_args            # Stack of argument counts for function calls
p.parser.functions_handler   # Functions class instance
p.parser.label_count         # Counter for unique labels
```

The parser object is the **single mutable accumulator** for the entire compilation process.

### 0.7 The Meta Object (Variable Metadata)

```python
class Meta:
    def __init__(self, name, type, scope, declaration_line, is_array, dimensions, p_init):
        self.name = name
        self.type = type          # String type
        self.scope = scope        # Scope name
        self.declaration_line = declaration_line
        self.is_array = is_array
        self.dimensions = dimensions
        self.p_init = p_init      # Has pointer been initialized?
```

Variables are looked up by name in the current scope chain. No symbol table abstraction.

### 0.8 Error Handling Pattern

```python
compiler_error(p, 1, "Variable not declared")
compiler_note("Called from Assignment._assignment")
sys.exit(1)
```

**Immediate termination**. No error recovery. No multiple errors reported. The first error kills the compiler.

---

## Phase 1: Deep Structural Diagnosis — Root-Level Limitations

### 1.1 The No-AST Problem (Most Critical)

**Symptom**: Parser actions emit bytecode directly.
**Root cause**: Single-pass syntax-directed translation was chosen, eliminating the AST/semantic analysis phase.
**Consequences**:
- **No semantic analysis pass** — type checking is interleaved with parsing, making it impossible to report all errors at once
- **No optimization** — there's no IR to optimize (constant folding, dead code elimination, strength reduction)
- **No separate compilation** — modules cannot be compiled independently and linked
- **No IDE support** — no AST means no LSP, no autocomplete, no goto-definition
- **Code generation is tangled** — semantic checks and bytecode emission are in the same method, making both harder to reason about

**Verdict**: The no-AST design is the **fundamental architectural debt** that amplifies every other problem.

### 1.2 The God Parser Anti-Pattern

**Symptom**: All state lives on `p.parser`.
**Root cause**: PLY's design encourages attaching state to the parser object.
**Consequences**:
- **Hidden dependencies** — handler methods access `p.parser.*` everywhere, making data flow invisible
- **No encapsulation** — any method can mutate any state
- **Testing nightmare** — to test a single semantic handler, you must construct a full parser with all its state
- **No reentrancy** — parser cannot be reused for multiple compilations without careful reset

### 1.3 The String Type System

**Symptom**: Types are Python strings compared with `==` and `.startswith()`.
**Root cause**: Quick-and-dirty implementation for a course project.
**Consequences**:
- **No type safety at the compiler level** — `&integer` and `integer` are just strings; typos in type names produce silent bugs
- **No extensibility** — adding a new type requires grep-replacing string literals across the codebase
- **No type inference** — every variable must be explicitly typed; `auto` or `let` would require a real type system
- **No compound types** — structs, unions, tuples are impossible without redesign
- **Pointer decay is ad-hoc** — `&integer` vs `vec<integer>` handling is special-cased everywhere

### 1.4 The Concatenated-String Code Generation

**Symptom**: Bytecode is emitted as concatenated Python strings: `p[1] + p[3] + "PUSHI 1\n"`.
**Root cause**: Simplicity for a teaching compiler.
**Consequences**:
- **O(n²) string concatenation** in deep expressions (though Python's concatenation is optimized, it's still semantically wrong)
- **No code introspection** — you cannot examine generated code before writing it to disk
- **No peephole optimization** — patterns like `PUSHI 0\nADD` cannot be eliminated because code is already a string
- **Label resolution is manual** — forward jumps require emitting placeholder labels and managing counters

### 1.5 The Immediate-Exit Error Handling

**Symptom**: `sys.exit(1)` on first error.
**Root cause**: Simplifies error handling logic.
**Consequences**:
- **User experience is poor** — fixing one error at a time is frustrating
- **No error recovery** — parser cannot skip to next statement and continue
- **No error aggregation** — cannot produce a summary report ("3 errors, 2 warnings")
- **Testing is harder** — each error condition requires a separate compiler invocation

### 1.6 The Scope Implementation

**Symptom**: Scopes are nested Python dicts accessed by string name.
**Root cause**: Simplest possible implementation.
**Consequences**:
- **O(n) lookups** — variable resolution walks the scope chain every time
- **No block scoping** — `if` and `while` bodies share the parent scope; variables declared inside loops leak
- **No name mangling** — no support for namespaces or modules
- **Shadowing is unclear** — the rules for variable shadowing are implicit in the lookup logic

### 1.7 The Grammar-Action Coupling

**Symptom**: 80+ PLY productions with inline Python actions.
**Root cause**: PLY's LALR(1) parser generator embeds actions in the grammar.
**Consequences**:
- **Grammar is not separable** — cannot use the grammar for documentation, other parser generators, or formal analysis
- **Actions are scattered** — understanding what `p_statement_for` does requires reading `_statement.py` while holding the grammar in your head
- **Shift-reduce debugging is hard** — PLY's error messages for grammar conflicts are opaque
- **No grammar testing** — cannot test the parser independently of semantic actions

### 1.8 The Missing Semantic Layers

| Feature | Status | Impact |
|---------|--------|--------|
| Constant folding | Missing | `1 + 2` emits `PUSHI 1\nPUSHI 2\nADD` instead of `PUSHI 3` |
| Dead code elimination | Missing | Unreachable code is emitted |
| Common subexpression elimination | Missing | `a + b` computed twice emits twice |
| Tail call optimization | Missing | Recursive functions blow the stack |
| Register allocation | N/A (stack VM) | — |
| Module system | Missing | Single-file compilation only |
| Standard library | Minimal | Only basic IO |
| Debug info | Missing | No source line mapping in bytecode |

---

## Phase 2: First-Principles Reframing — Ideal Form Derivation

### 2.1 What Is a Compiler, Really?

A compiler is a **function**:
```
compile : SourceCode × Configuration → TargetCode ∪ ErrorReport
```

This function should be:
- **Total** (defined for all inputs, producing errors rather than crashing)
- **Composable** (modules compile independently and link)
- **Verifiable** (each phase has invariants that can be checked)
- **Optimizable** (intermediate representations enable transformations)

OpenLatinum violates all four properties.

### 2.2 The Ideal Pipeline

```
Source Text
    ↓
Lexer → Token Stream
    ↓
Parser → Concrete Syntax Tree (CST)
    ↓
Elaborator → Abstract Syntax Tree (AST)
    ↓
Semantic Analyzer → Typed AST + Symbol Table
    ↓
IR Generator → Intermediate Representation (SSA or CFG)
    ↓
Optimizer → Optimized IR
    ↓
Code Generator → Target Bytecode/Assembly
    ↓
Assembler → Binary / Bytecode File
```

Each arrow is a **pure function** (or close to it). Each intermediate representation is a **data structure** that can be inspected, tested, and serialized.

### 2.3 The Ideal Type System

```
Type := BaseType | PointerType | ArrayType | FunctionType | NamedType
BaseType := Integer(bits) | Float(bits) | Boolean | Void
PointerType := Pointer(to: Type)
ArrayType := Array(of: Type, size: Optional[Expr])
FunctionType := Function(params: List[Type], returns: Type)
NamedType := Name(String) [resolved to concrete type]
```

Properties:
- **Structural equality** for anonymous types
- **Nominal equality** for named types (structs)
- **Subtyping** for pointers (covariant arrays are unsound — don't do it)
- **Type inference** via Hindley-Milner or bidirectional typing

### 2.4 The Ideal Error Model

```
Error := {
    severity: Error | Warning | Note,
    location: SourceRange,
    message: String,
    related: List[Error],
    suggestion: Optional[String]
}

CompilationResult := Success(Program) | Failure(List[Error])
```

Properties:
- **Continue after errors** — report as many as possible
- **Source ranges, not single points** — highlight entire problematic expressions
- **Related information** — "variable declared here" for use-before-def errors
- **Fix suggestions** — "did you mean...?"

### 2.5 The Ideal IR

For a stack VM target, the ideal IR is a **control flow graph (CFG)** with basic blocks:

```
BasicBlock := {
    label: String,
    instructions: List[Instruction],
    terminator: Jump | Branch | Return | Fallthrough
}

Instruction := Push(Value) | Pop | BinaryOp(Op) | UnaryOp(Op) | Load | Store | Call(Function)
Value := Integer(n) | Float(f) | String(s) | Register(id)
```

This enables:
- **Local optimization** within basic blocks (constant folding, CSE, dead store elimination)
- **Global optimization** across blocks (inlining, loop unrolling)
- **Straightforward code generation** — each block maps to labeled bytecode

---

## Phase 3: Radical Redesign — New Architecture Proposal

### 3.1 The Core Redesign: Introduce an AST

**Decision**: Add a full AST layer between parsing and code generation.

**Rationale**: The no-AST design is the root cause of 80% of OpenLatinum's limitations. Every advanced feature (optimization, better errors, IDE support, modules) requires an AST.

**New pipeline**:
```
Source → Tokens → CST → AST → Typed AST → IR → Bytecode
```

### 3.2 The AST Design

```python
from dataclasses import dataclass
from typing import List, Optional, Union

@dataclass
class Program:
    declarations: List[Declaration]

@dataclass
class FunctionDecl:
    name: str
    params: List[Param]
    return_type: Type
    body: Block
    location: SourceRange

@dataclass
class VarDecl:
    name: str
    type: Type
    init: Optional[Expression]
    location: SourceRange

@dataclass
class Block:
    statements: List[Statement]
    location: SourceRange

Expression = Union[BinaryOp, UnaryOp, Literal, Variable, Call, Index, Deref]

@dataclass
class BinaryOp:
    op: str  # '+', '-', '*', '/', etc.
    left: Expression
    right: Expression
    location: SourceRange

@dataclass
class Literal:
    value: Union[int, float, str, bool]
    location: SourceRange

Statement = Union[ExprStmt, VarDecl, Assignment, If, While, For, 
                  DoWhile, Return, Break, Continue, Print, Read]

@dataclass
class If:
    condition: Expression
    then_branch: Block
    else_branch: Optional[Block]
    location: SourceRange
```

**Key property**: Every AST node carries a `SourceRange` (file, start_line, start_col, end_line, end_col) for precise error reporting.

### 3.3 The Type System Redesign

Replace string types with a proper type hierarchy:

```python
class Type:
    pass

@dataclass
class IntType(Type):
    bits: int = 32

@dataclass
class FloatType(Type):
    bits: int = 32

@dataclass
class StringType(Type):
    pass

@dataclass
class PointerType(Type):
    to: Type

@dataclass
class ArrayType(Type):
    of: Type
    size: Optional[int]

@dataclass
class FunctionType(Type):
    params: List[Type]
    returns: Type

@dataclass
class VoidType(Type):
    pass
```

Type equality is now structural and unambiguous.

### 3.4 The Semantic Analyzer

A dedicated pass over the AST:

```python
class SemanticAnalyzer:
    def analyze(self, program: Program) -> Result[TypedProgram, List[Error]]:
        # 1. Build symbol table (first pass)
        # 2. Resolve types (second pass)
        # 3. Check expressions (third pass)
        # 4. Check control flow (return paths, break/continue validity)
        # 5. Collect all errors, return them together
        pass
```

**Key improvement**: All errors are collected and returned together. No `sys.exit(1)`.

### 3.5 The IR Design

Three-address code in SSA form:

```python
@dataclass
class IRProgram:
    functions: List[IRFunction]
    globals: List[IRGlobal]

@dataclass
class IRFunction:
    name: str
    params: List[str]
    blocks: List[BasicBlock]

@dataclass
class BasicBlock:
    label: str
    instructions: List[Instruction]
    terminator: Terminator

Instruction = Union[
    LoadConst,      # reg = const
    BinaryOp,       # reg = reg op reg
    UnaryOp,        # reg = op reg
    Load,           # reg = *reg
    Store,          # *reg = reg
    GetLocal,       # reg = local[name]
    SetLocal,       # local[name] = reg
    Call,           # reg = call func(args)
    Return,         # return reg
]

Terminator = Union[
    Jump,           # goto label
    Branch,         # if reg goto label1 else label2
    RetVoid,        # return
    Unreachable,
]
```

### 3.6 The Code Generator

```python
class CodeGenerator:
    def generate(self, ir: IRProgram) -> str:
        # Walk the IR, emit EWVM bytecode
        # Uses register allocation (stack slots) for temporaries
        pass
```

### 3.7 The Error System Redesign

```python
@dataclass
class SourceRange:
    file: str
    start_line: int
    start_col: int
    end_line: int
    end_col: int

@dataclass
class CompilerError:
    severity: Literal["error", "warning", "note"]
    range: SourceRange
    message: str
    related: List[CompilerError] = field(default_factory=list)

class ErrorCollector:
    def __init__(self):
        self.errors: List[CompilerError] = []
    
    def error(self, range: SourceRange, message: str):
        self.errors.append(CompilerError("error", range, message))
    
    def has_errors(self) -> bool:
        return any(e.severity == "error" for e in self.errors)
```

---

## Phase 4: Adversarial Self-Critique — Attack the Design

### 4.1 Critique: "You're Over-Engineering a Teaching Compiler"

**Attack**: OpenLatinum is a course project. Adding an AST, IR, SSA, and a proper type system turns a 3,000-line teaching compiler into a 30,000-line production compiler. Students won't learn the basics because they'll be lost in abstraction layers.

**Defense**: The critique is partially valid. The full redesign is the **target state**, not the immediate next step. The migration path (see Phase 7) preserves the teaching value by:
- Keeping the first version simple (AST only, no IR)
- Making each phase a standalone, compilable system
- Using the refactor as a teaching opportunity ("why do we need an AST?")

**Revised stance**: Phase 3 describes the **eventual** architecture. The **immediate** next step is smaller: add an AST layer while keeping everything else recognizable.

### 4.2 Critique: "PLY Is the Wrong Foundation"

**Attack**: PLY embeds actions in the grammar, making AST construction awkward. You have to build the AST inside parser actions, which is exactly what you criticized. A proper parser combinator library or a handwritten recursive descent parser would be cleaner.

**Defense**: Valid. PLY's LALR(1) parser with embedded actions is inherently coupled. However:
- **Migration cost**: Rewriting the parser is ~900 lines of working, tested code. Risk of introducing regressions is high.
- **Intermediate solution**: Use PLY's `p_error` and action-less productions to build a CST, then convert to AST in a separate pass. This decouples grammar from semantics while keeping PLY.
- **Long-term**: A handwritten Pratt parser or recursive descent parser would indeed be cleaner and enable better error messages.

**Revised stance**: Keep PLY for now but use it to build a CST, not to emit code directly. Plan parser rewrite for Phase 7.

### 4.3 Critique: "String Concatenation Isn't Actually a Performance Problem"

**Attack**: Python's string concatenation is optimized (C-level buffer reuse for small strings). For a compiler generating <10KB of bytecode, O(n²) string building is negligible. You're optimizing imaginary performance problems.

**Defense**: The performance argument is indeed weak for this scale. The **real** problem with string concatenation is **not performance** but **semantics**:
- You cannot inspect the generated code before emission
- You cannot optimize after generation
- You cannot test code generation independently
- Code generation logic is scattered across 80+ parser actions

**Revised stance**: Agreed — performance isn't the issue. The issue is **architecture**. Code generation should produce a data structure (IR or instruction list), not a string.

### 4.4 Critique: "The Type System Is Fine for the Target Language"

**Attack**: OpenLatinum only has 3 base types + pointers + arrays. A string-based type system with 5 patterns is simpler and sufficient. Adding a type hierarchy is premature abstraction.

**Defense**: The string type system has already caused bugs (the `UnboundLocalError` in IO handlers was triggered by unrecognized type strings). More importantly:
- Adding `boolean` would require touching ~20 locations
- Adding `char` would require similar
- Adding `struct` is effectively impossible
- Type errors produce wrong messages because type strings are manipulated with `.startswith()`

**Revised stance**: A minimal type hierarchy (5-6 classes) is worth it even for 3 types. The cost is low (~50 lines) and the benefit is eliminating an entire class of bugs.

### 4.5 Critique: "Error Recovery Is Hard and Not Worth It for a Teaching Compiler"

**Attack**: Implementing error recovery in a parser (panic mode, phrase-level recovery) is complex and error-prone. For a language with short programs, reporting one error at a time is acceptable.

**Defense**: Error recovery in the **parser** is indeed hard. But error recovery in the **semantic analyzer** is trivial:
- Continue checking after a type mismatch
- Continue checking after an undeclared variable
- Skip the current function body if the signature is invalid

The key insight: **parse first, then collect semantic errors**. The parser can still exit on syntax errors (those are unrecoverable in LALR(1)), but the semantic analyzer can report dozens of errors in one pass.

**Revised stance**: Keep parser error-on-first, but make the semantic analyzer collect-all-errors.

### 4.6 Critique: "You're Proposing a Complete Rewrite, Not an Evolution"

**Attack**: The user asked for an "evolution audit," not a "burn it down and start over" recommendation. A 7-phase analysis ending in "rewrite everything" is useless advice.

**Defense**: This is the strongest critique. The redesign in Phase 3 is the **destination**, but the path matters. Phase 7 (Forward Trajectory) must provide a concrete, incremental migration plan that:
- Preserves working code at each step
- Adds value at each step
- Can be stopped at any point with a working compiler

**Revised stance**: Phase 5 and 7 must focus on incremental evolution, not big-bang rewrite.

---

## Phase 5: Iterative Refinement — Second-Generation Design

### 5.1 The Incremental AST Migration

Instead of rewriting everything at once, add an AST layer **in parallel** with the existing code:

**Step 1: AST Node Classes** (add-only, no changes to existing code)
- Create `lat/ast/nodes.py` with dataclass AST nodes
- Create `lat/ast/cst_builder.py` that converts PLY parse trees to AST
- Create `lat/ast/printer.py` for debugging

**Step 2: Dual-Path Compilation** (feature flag)
- Add `--ast` CLI flag
- When `--ast` is passed: Source → AST → (new semantic checker) → (new code generator)
- When `--ast` is not passed: existing path (Source → Parser → Bytecode)
- Both paths produce identical bytecode for all test cases

**Step 3: Semantic Analyzer on AST** (gradual migration)
- Port one semantic check at a time from parser actions to AST visitor
- Start with variable declaration checking (simplest)
- End with control flow checking (hardest)

**Step 4: Code Generator from AST** (gradual migration)
- Port one statement type at a time
- Maintain a mapping: AST node → bytecode string (initially)
- Eventually: AST → IR → bytecode

**Step 5: Remove Old Path** (once new path is complete and tested)
- Delete parser actions that emit code
- Keep parser for CST → AST conversion only
- Parser becomes a pure syntax recognizer

### 5.2 The Minimal Type System Refactor

Instead of a full type hierarchy, start with a lightweight abstraction:

```python
# lat/types.py
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class Type:
    name: str
    
    def is_pointer(self) -> bool:
        return self.name.startswith("&")
    
    def is_array(self) -> bool:
        return self.name.startswith("vec<")
    
    def pointee(self) -> "Type":
        assert self.is_pointer()
        return Type(self.name[1:])
    
    def array_element(self) -> "Type":
        assert self.is_array()
        return Type(self.name[4:-1])

# Predefined types
INT = Type("integer")
FLOAT = Type("float")
STRING = Type("filum")
```

This is a **shim** over string types. It provides:
- Centralized type definitions
- Encapsulated type operations
- A path to full type hierarchy later

Cost: ~30 lines. Benefit: eliminates string manipulation bugs.

### 5.3 The Error Collector Refactor

Instead of immediate `sys.exit(1)`, introduce an error collector:

```python
# lat/errors.py
class ErrorCollector:
    def __init__(self):
        self.errors = []
    
    def error(self, location, message):
        self.errors.append(("error", location, message))
    
    def report(self):
        for severity, location, message in self.errors:
            print(f"{severity}: {location}: {message}", file=sys.stderr)
        if any(e[0] == "error" for e in self.errors):
            sys.exit(1)
```

**Migration**: 
- Wrap existing `compiler_error` calls to also append to collector
- Change `sys.exit(1)` to `raise CompilationError()` 
- Catch `CompilationError` at top level and call `collector.report()`
- Gradually allow multiple errors per phase

### 5.4 The Test Infrastructure

Before any major refactor, establish a test suite:

```
tests/
  lexer/
    test_tokens.py
  parser/
    test_grammar.py
  semantics/
    test_types.py
    test_scopes.py
  end_to_end/
    test_hello_world.py
    test_bsort.py
    test_qsort.py
    test_rule110.py
  regression/
    test_bug_fixes.py  # Each fixed bug gets a test
```

Each test compiles a `.lat` file and either:
- Asserts successful compilation + expected bytecode output
- Asserts specific error message

**Critical**: Tests must run against the **bytecode output**, not just "doesn't crash."

---

## Phase 6: Convergence and Synthesis — Final Architecture

### 6.1 The Final Architecture (Post-Evolution)

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Entry Point                      │
│                    (lat/cli.py — simplified)                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                         Lexer                                │
│              (PLY → Token Stream)                            │
│         Future: Handwritten lexer for better errors          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                         Parser                               │
│              (PLY → Concrete Syntax Tree)                    │
│         Future: Recursive descent or Pratt parser            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      AST Builder                             │
│              (CST → AST with SourceRanges)                   │
│              Validates syntax-only constraints               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Semantic Analyzer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Name Resolution│  │ Type Checker │  │ Control Flow Checker│ │
│  │  (Scopes)    │  │  (Types)     │  │  (Loops/Returns)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│  Produces: Typed AST + Symbol Table + Error List           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    IR Generator                              │
│              (Typed AST → Three-Address Code)                │
│         Produces: Control Flow Graph (CFG)                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Optimizer (Optional)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Constant Fold│  │ Dead Code   │  │ CSE                │ │
│  │             │  │ Elimination │  │                    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Code Generator                            │
│              (IR → EWVM Bytecode)                            │
│         Stack slot allocation for temporaries              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Assembler/Linker                          │
│              (Byte strings → .ewvm file)                     │
│         Future: Separate compilation + linking             │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| AST is mandatory | Enables all other improvements (errors, optimization, IDE support) |
| Type system is class-based | Prevents string-manipulation bugs; enables extension |
| Error collector pattern | Multiple errors per compilation; better UX |
| IR is CFG-based | Enables local and global optimization |
| Incremental migration | Preserves working compiler at each step |
| PLY retained initially | Minimizes risk; parser rewrite is Phase 7 |

### 6.3 Invariants at Each Boundary

| Boundary | Invariant |
|----------|-----------|
| Token Stream | Every token has a valid token type and source location |
| CST | Conforms to grammar; no semantic meaning |
| AST | Structurally valid; all nodes have source ranges |
| Typed AST | Every expression has a resolved type; every name is resolved |
| IR | SSA form (each variable assigned once); all basic blocks have terminators |
| Bytecode | All labels resolved; stack depth bounded; valid EWVM instructions |

### 6.4 What Is Preserved from OpenLatinum 1.0

- **The language grammar** — `integer`, `float`, `filum`, `vec<>`, functions, pointers, control flow
- **The target VM** — EWVM bytecode format is unchanged; VM is now containerized
- **The CLI interface** — `lat build file.lat -o out.vms`
- **Example programs** — `hello_world`, `bsort`, `qsort`, `rule110` all compile identically
- **The teaching value** — each phase is understandable in isolation
- **VM source** — Original VM source (`vms-source.zip`) preserved for reproducible builds

### 6.5 What Is Eliminated

- **Prebuilt VM binary in repo** — VM is now built from source in Docker (Chainguard images)
- **Parser-action code generation** — parser is pure syntax
- **String-based type system** — replaced with type objects
- **Immediate sys.exit(1)** — replaced with error collection
- **God parser object** — state is encapsulated in phase-specific objects
- **String concatenation for code** — replaced with IR/data structures

---

### 6.6 Containerization Strategy

The VM has been containerized using **Chainguard** minimal images for security and reproducibility:

| Aspect | Before | After |
|--------|--------|-------|
| VM location | `vm/vms` (prebuilt binary in repo) | Built from `vms-source.zip` in Dockerfile |
| Base image | N/A (host OS) | `cgr.dev/chainguard/python:latest` |
| Build stage | N/A | `cgr.dev/chainguard/wolfi-base:latest` with gcc/make/flex/bison |
| Runtime deps | Host-provided glib/readline | Explicitly installed in container |
| Makefile | `make install` copied VM to `/usr/local/bin` | Removed VM install target |
| README | Referenced University of Minho VM | Documents Docker workflow |

**Benefits**:
- **Reproducible builds** — VM is compiled from source every time
- **Security** — Chainguard images have minimal attack surface, no shell by default
- **Portability** — Works identically on any Docker host
- **Clean repo** — No prebuilt binaries checked into git

---

## Phase 7: Forward Trajectory — Evolution Roadmap

### 7.1 Phase 7.1: Foundation (Week 1-2)
**Goal**: Establish testing and minimal infrastructure.

**Tasks**:
1. Create `tests/` directory with end-to-end tests for all example programs
2. Create `lat/types.py` with lightweight Type wrapper (see 5.2)
3. Create `lat/errors.py` with ErrorCollector (see 5.3)
4. Refactor existing code to use Type wrapper and ErrorCollector
5. **Deliverable**: All tests pass; no behavior change

### 7.2 Phase 7.2: AST Introduction (Week 3-4)
**Goal**: Add AST layer in parallel with existing compilation path.

**Tasks**:
1. Design AST node classes in `lat/ast/nodes.py`
2. Create `lat/ast/builder.py` — converts PLY parse trees to AST
3. Add `--ast` flag to CLI for dual-path compilation
4. Implement AST printer for debugging
5. **Deliverable**: `lat compile --ast file.lat` produces identical bytecode

### 7.3 Phase 7.3: Semantic Analyzer on AST (Week 5-6)
**Goal**: Port semantic checking to AST visitor.

**Tasks**:
1. Create `lat/semantic/analyzer.py` with visitor pattern
2. Port variable declaration checking
3. Port type checking
4. Port control flow checking (break/continue, return paths)
5. Port function call validation
6. Collect all errors, don't exit on first
7. **Deliverable**: `--ast` path uses new semantic analyzer; old path still works

### 7.4 Phase 7.4: Code Generation from AST (Week 7-8)
**Goal**: Port code generation to AST visitor.

**Tasks**:
1. Create `lat/codegen/generator.py` — AST → bytecode string (initially)
2. Port each statement type
3. Port each expression type
4. Verify bytecode identity with old path for all tests
5. **Deliverable**: `--ast` path is complete and tested

### 7.5 Phase 7.5: IR Introduction (Week 9-10)
**Goal**: Add intermediate representation.

**Tasks**:
1. Design IR in `lat/ir/` — three-address code, basic blocks, CFG
2. Create `lat/ir/generator.py` — Typed AST → IR
3. Create `lat/ir/verifier.py` — check IR invariants
4. Create `lat/codegen/from_ir.py` — IR → EWVM bytecode
5. **Deliverable**: New pipeline: AST → IR → Bytecode

### 7.6 Phase 7.6: Optimization (Week 11-12)
**Goal**: Add basic optimizations on IR.

**Tasks**:
1. Constant folding pass
2. Dead code elimination pass
3. Common subexpression elimination (local, within basic blocks)
4. Measure improvement on example programs
5. **Deliverable**: Optimized bytecode; smaller/faster for test cases

### 7.7 Phase 7.7: Parser Modernization (Week 13-14)
**Goal**: Replace PLY with a modern parser.

**Tasks**:
1. Design recursive descent parser or Pratt parser
2. Implement in `lat/parsing/parser.py`
3. Produce identical CST/AST for all test cases
4. Better error messages ("expected X, found Y")
5. Remove PLY dependency
6. **Deliverable**: PLY-free parser; better syntax errors

### 7.8 Phase 7.8: Language Extensions (Week 15+)
**Goal**: Add features that the new architecture enables.

**Candidate features**:
- `boolean` type with `true`/`false` literals
- `const` declarations
- `if` expressions (ternary operator)
- `struct` types
- Module system (`import`)
- Standard library (math, string operations)
- Debug info (source line mapping)

### 7.9 Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Regression in working code | Comprehensive test suite before any refactor |
| AST path diverges from old path | Bytecode identity tests; diff old vs new output |
| Performance regression | Benchmark compilation time; IR is typically faster |
| Complexity explosion | Each phase is a standalone, working compiler |
| Student confusion | Document each phase; preserve simple examples |

### 7.10 Success Criteria

| Metric | Current | Target (Phase 7.7) |
|--------|---------|-------------------|
| Lines of code | ~2,900 | ~4,500 (more features, cleaner structure) |
| Test coverage | 0% | >80% |
| Errors reported per run | 1 | All detectable errors |
| Time to add a new type | ~20 files | 3 files (types.py, parser, codegen) |
| Time to add a new statement | ~5 files | 2 files (ast/nodes.py, semantic analyzer + codegen) |
| Syntax error quality | "Invalid syntax 'x'" | "Expected ';' but found 'x' at line 5" |
| Optimization | None | Constant folding + DCE + local CSE |

---

## Summary

OpenLatinum is a **functional teaching compiler** with **deep architectural limitations** that prevent evolution. The core problems are:

1. **No AST** — prevents optimization, good errors, and IDE support
2. **String types** — brittle and unextensible
3. **God parser** — untestable and unencapsulated
4. **Immediate exit** — poor user experience
5. **String code generation** — uninspectable and unoptimizable

The **evolution path** is incremental, not a rewrite:

1. **Foundation** — tests, type wrapper, error collector
2. **AST** — add parallel compilation path
3. **Semantic analyzer** — port checks to AST visitor
4. **Code generation** — port emission to AST visitor
5. **IR** — introduce three-address code
6. **Optimization** — constant fold, DCE, CSE
7. **Parser modernization** — replace PLY
8. **Language extensions** — structs, modules, boolean

Each phase produces a **working compiler** that passes all tests. The migration preserves OpenLatinum's teaching value while transforming it into a **production-quality compiler framework**.

---

*Analysis completed. 7 phases, 14 weeks estimated for full evolution.*
