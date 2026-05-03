# OpenLatinum Architecture

## Overview

OpenLatinum is a statically typed programming language compiler that translates `.lat` source files into stack-based EWVM bytecode. The compiler is organized into distinct phases following a traditional compiler pipeline.

## High-Level Architecture

```
Source (.lat) → Lexer → Parser → AST → Semantic Analyzer → IR (optional) → Code Generator → Bytecode (.vms)
```

## Module Organization

### 1. Lexical Analysis (`lat/lexing/`)
- **`_lexer.py`**: PLY-based lexer with Latin-inspired keywords
- **`tokenizer.py`**: Token definitions and token stream utilities

### 2. Parsing (`lat/parsing/`)
- **`_parser.py`**: PLY-based LR parser (legacy, stable)
- **`ast_parser.py`**: Recursive descent parser producing AST (modern)
- **`rd_parser.py`**: Direct recursive descent parser (experimental)
- **`tokenizer.py`**: Token stream handling

**Parser Selection Strategy:**
- **Legacy parser** (default): Production-ready, well-tested PLY-based parser
- **AST parser** (`--ast`): Modern alternative with explicit AST, preferred for new development
- **RD parser** (`--rd`): Experimental, for teaching and research

### 3. Abstract Syntax Tree (`lat/ast/`)
- **`nodes.py`**: AST node definitions using dataclasses
- **`program.py`**: Program-level AST structures

### 4. Semantic Analysis (`lat/semantic/`, `lat/semantics/`)
- **`analyzer.py`**: Entry point for semantic analysis
- **`_expression.py`**: Expression type checking and validation
- **`_statement.py`**: Statement type checking and validation
- **`_functions.py`**: Function signature validation
- **`_scopes.py`**: Scope and symbol table management
- **`_type_check.py`**: Core type checking logic

### 5. Intermediate Representation (`lat/ir/`)
- **`nodes.py`**: IR node definitions
- **`generator.py`**: AST-to-IR translation
- **`optimizer.py`**: IR-level optimizations (constant folding, dead code elimination)

### 6. Code Generation (`lat/codegen/`)
- **`generator.py`**: AST-to-bytecode compiler
- **`from_ir.py`**: IR-to-bytecode compiler
- **`emitters.py`**: Shared bytecode emission utilities
- **`analyzer.py`**: IR analysis and validation

### 7. Virtual Machine (`lat/vm_interpreter.py`)
- Stack-based bytecode interpreter for EWVM

### 8. CLI (`lat/cli/`)
- **`__init__.py`**: Entry point and mode dispatch
- **`args.py`**: Command-line argument parsing
- **`compiler.py`**: Compilation orchestration
- **`test_runner.py`**: Test execution and verification
- **`utils.py`**: Shared CLI utilities

### 9. Utilities (`lat/utils/`)
- **`errors.py`**: Error handling and reporting
- **`colors.py`**: Terminal color utilities

## Design Principles

1. **Separation of Concerns**: Each phase (lexing, parsing, semantic analysis, codegen) is independent
2. **Multiple Parser Support**: Three parsers coexist for backward compatibility and experimentation
3. **Type Safety**: Strong static typing with comprehensive type annotations
4. **Error Handling**: Centralized error reporting via `CompilationError`
5. **Testability**: Comprehensive test suite with 285+ tests

## Data Flow

```
.lat file
   ↓
Lexer (token stream)
   ↓
Parser (AST)
   ↓
Semantic Analyzer (typed AST)
   ↓
[Optional] IR Generator → IR Optimizer
   ↓
Code Generator (bytecode)
   ↓
.vms file
   ↓
VM Interpreter (execution)
```

## Extension Points

- **New AST nodes**: Add to `lat/ast/nodes.py`
- **New bytecode instructions**: Add to `lat/codegen/emitters.py`
- **New optimizations**: Add to `lat/ir/optimizer.py`
- **New CLI commands**: Add to `lat/cli/__init__.py`
