# OpenLatinum

## Overview

OpenLatinum is a statically typed programming language with Latin-inspired syntax. It compiles `.lat` source files to stack-based bytecode. The compiler is available in both **Python** and **Rust** and supports multiple compilation paths for teaching and experimentation.

This project is a community-driven evolution of the original OpenLatinum compiler (University of Minho, 2022).

## Installation

### Local Install (Python)

```bash
git clone https://github.com/awdemos/OpenLatinium.git
cd OpenLatinum
pip install -e .
```

### Local Install (Rust)

```bash
git clone https://github.com/awdemos/OpenLatinium.git
cd OpenLatinum
cargo build --workspace
cargo test --workspace
```

### Docker (Recommended)

```bash
docker build -t openlatinum .
docker run --rm -v $(pwd):/app openlatinum build examples/hello_world.lat
```

## Quick Start

```bash
lat build examples/hello_world.lat
```

## Features

### Comments

Single-line comments with `//`:
```rust
// This is a comment
```

Multiline comments with `/* */`:
```rust
/*
This is a multiline comment
*/
```

### Data Types

- `integer`, `float`, `filum`: Basic types
- `&integer`, `&float`, `&filum`: Pointer types
- `vec<integer>`, `vec<float>`, `vec<filum>`: Array types

### Arithmetics

- `+`, `-`, `*`, `/` operators
- `==`, `!=`, `<`, `>`, `<=`, `>=` operators
- `et`, `aut` (logical AND, OR)
- `non` (logical NOT)

Pointer arithmetic:
- `+` adds an integer to a pointer
- `-` subtracts an integer from a pointer
- `>`, `<`, `>=`, `<=` compare two pointers

### Variables

Declare and initialize:
```rust
a: integer = 10
```

Declare only (initialized to 0):
```rust
a: integer
```

Reassign:
```rust
a = 20
```

### Arrays

```rust
a: vec<integer>[10]        // Size-based declaration
a: vec<integer> = [10, 20, 30]  // List initialization
a: vec<integer> = [1 ... 10]    // Range initialization
```

Access:
```rust
a[0]
```

### Control Flow

`si` (if):
```rust
si expression {
    // code
} aliter {
    // code
}
```

`par` (match):
```rust
par expression {
    expression -> {
        // code
    }
    defectus -> {
        // code
    }
}
```

`dum` (while):
```rust
dum expression {
    // code
}
```

`facio dum` (do-while):
```rust
facio {
    // code
} dum(expression)
```

`enim` (for):
```rust
enim(i: integer = 0; i < 10; i = i + 1) {
    // code
}
```

### Functions

```rust
munus sum(a: integer, b: integer) -> integer {
    reditus a + b
}
```

Call:
```rust
sum(10, 20)
```

## CLI Usage

```
lat [MODE] [INPUT] [OPTIONS]

Modes:
  run       Compile and run the program
  build     Compile the program to bytecode
  test      Compile and run test programs
  euler     Check Euler problem solutions
  examples  Compile and run example programs

Options:
  -h, --help      Show help
  -o, --output    Specify output file
  -v, --verbose   Show verbose output
  --ast           Use AST-based compiler path
  --ir            Use IR pipeline (AST → IR → bytecode)
  --check         Semantic analysis only (no codegen)
  -rec, --record  Record program outputs
  -clc, --clean-up  Clean generated files
```

## Testing

### Unit Tests

Run all unit tests:
```bash
python -m pytest tests/ -v
```

Run specific test files:
```bash
python -m pytest tests/test_parser.py -v
python -m pytest tests/test_semantic.py -v
python -m pytest tests/test_codegen.py -v
```

### Rust Tests

Run the Rust workspace tests:
```bash
cargo test --workspace
```

Run with output:
```bash
cargo test --workspace -- --nocapture
```

### Integration Tests

Run the full test suite against `.lat` programs:
```bash
lat test
```

Run with verbose output:
```bash
lat test -v
```

Run with AST compiler path:
```bash
lat test --ast
```

## VM and Execution

OpenLatinum has two execution backends:

1. **C VM** (original): The bytecode runs on a C-based stack VM. Build from `vms-source.zip`:
   ```bash
   unzip vms-source.zip -d /tmp/vms
   cd /tmp/vms/vms
   make
   ```

2. **Python Interpreter** (new): The bytecode can also run on a pure Python interpreter included in the compiler. This eliminates the C VM dependency for development and testing.

The Python interpreter is transparent to the user - the same `.vms` bytecode files work with both backends.

## Architecture

The compiler has **three Python compilation paths** and a **Rust compiler frontend**:

### Python Paths

1. **Original**: `lat/lexing/_lexer.py` → `lat/parsing/_parser.py` → `lat/semantics/*` → bytecode (single-pass, syntax-directed)
2. **AST path** (`--ast`): `lat/parsing/ast_parser.py` → `lat/semantic/analyzer.py` → `lat/codegen/generator.py` → bytecode
3. **IR path** (`--ir`): AST → `lat/ir/generator.py` → `lat/ir/nodes.py` → `lat/codegen/from_ir.py` → bytecode

### Rust Compiler Frontend

A Rust implementation of the compiler frontend (lexer → parser → AST → semantic analysis) is available in the `lat-core` crate. It can be used as a library or via the `lat!` procedural macro for embedding OpenLatinum code in Rust programs.

**Workspace crates:**
- `lat-core` — Lexer, parser, AST, and semantic analyzer (Rust)
- `lat-macro` — Procedural macros (the `lat!` macro)
- `lat` — Integration tests and CLI bindings

Key modules:
- `lat/cli.py` — Entry point, argument parsing, test runner
- `lat/parsing/ast_parser.py` — PLY-based parser that builds AST (`lat/ast/nodes.py`)
- `lat/semantic/analyzer.py` — Visitor-based semantic analyzer with error collection
- `lat/codegen/generator.py` — AST-to-bytecode generator (produces EWVM instructions)
- `lat/vm_interpreter.py` — Python bytecode interpreter for executing `.vms` files
- `lat/ir/generator.py` — AST-to-IR converter (three-address code)
- `lat/codegen/from_ir.py` — IR-to-bytecode generator
- `lat-core/src/` — Rust lexer, parser, AST, and semantic analysis

## Language Keywords

| Latin | English | Purpose |
|-------|---------|---------|
| `si` | if | Conditional |
| `aliter` | else | Alternative branch |
| `par` | match | Pattern matching |
| `casus` | case | Match case |
| `defectus` | default | Default case |
| `dum` | while | While loop |
| `facio` | do | Do-while loop |
| `enim` | for | For loop |
| `confractus` | break | Break out of loop |
| `pergo` | continue | Continue to next iteration |
| `munus` | function | Function declaration |
| `reditus` | return | Return from function |
| `et` | and | Logical AND |
| `aut` | or | Logical OR |
| `non` | not | Logical NOT |
| `imprimo` | print | Print statement |
| `legerei` | read_int | Read integer |
| `legeref` | read_float | Read float |
| `legeres` | read_string | Read string |
| `integer` | int | Integer type |
| `float` | float | Float type |
| `filum` | string | String type |
| `vec` | array | Array type |

## Contributing

This is an open-source community project. Contributions welcome!

## License

MIT License - See LICENSE file for details.
