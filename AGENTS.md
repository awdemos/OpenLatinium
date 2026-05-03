# OpenLatinum Compiler — Agent Guide

## Quick Start

```bash
pip install -e .                    # Install compiler + `lat` CLI
# OR
docker build -t openlatinum .           # Build compiler + VM in container
```

## Build the VM (Required)

The VM is **not** shipped as a binary. Build from source before running compiled programs:

```bash
unzip vms-source.zip -d /tmp/vms
cd /tmp/vms/vms
make
# Binary will be at /tmp/vms/vms/vms
```

The VM requires: `gcc`, `make`, `flex`, `bison`, `glib-dev`, `readline-dev`.

## CLI Commands

```bash
lat build file.lat                   # Compile to file.vms
lat build file.lat -o out.vms        # Specify output
lat build file.lat --ast             # Use AST-based compiler path
lat build file.lat --check           # Semantic analysis only (no codegen)
lat build file.lat --ir              # Use IR pipeline (AST → IR → bytecode)
lat run file.lat                     # Compile + run on VM
lat test                             # Run full test suite (test/*.lat)
lat test -v                          # Verbose test output
lat examples                         # Run example programs
```

## Test Structure

- **Test files**: `test/*.lat` with expected outputs in `test/*.ans`
- **Examples**: `examples/*.lat` with `examples/*.ans`
- Files starting with `//SKIP` are excluded from test runs
- Tests compile .lat → .vms, run on VM, and diff stdout against .ans
- Some tests require stdin (files starting with `read` get `'3.14\n314\n314'`)

## Architecture

The compiler has **three compilation paths**:

1. **Original**: `lat/lexing/_lexer.py` → `lat/parsing/_parser.py` → `lat/semantics/*` → bytecode (single-pass, syntax-directed)
2. **AST path** (`--ast`): `lat/parsing/ast_parser.py` → `lat/semantic/analyzer.py` → `lat/codegen/generator.py` → bytecode
3. **IR path** (`--ir`): AST → `lat/ir/generator.py` → `lat/ir/nodes.py` → `lat/codegen/from_ir.py` → bytecode

Key modules:
- `lat/cli.py` — Entry point, argument parsing, test runner
- `lat/parsing/ast_parser.py` — PLY-based parser that builds AST (`lat/ast/nodes.py`)
- `lat/semantic/analyzer.py` — Visitor-based semantic analyzer with error collection
- `lat/codegen/generator.py` — AST-to-bytecode generator (produces EWVM instructions)
- `lat/ir/generator.py` — AST-to-IR converter (three-address code)
- `lat/codegen/from_ir.py` — IR-to-bytecode generator

## VM Quirks

- Stack-based VM with instructions: `PUSHI`, `PUSHF`, `PUSHS`, `ADD`, `SUB`, `MUL`, `DIV`, `MOD`, `INF`, `SUP`, `INFEQ`, `SUPEQ`, `EQUAL`, `NOT`, `JZ`, `JUMP`, `CALL`, `RETURN`, `READ`, `READF`, `READS`, `WRITEI`, `PUSHN`, `PUSHFP`, `PUSHGP`, `LOAD`, `LOADL`, `STORE`, `STOREL`, `PADD`, `ALLOC`
- **No AND/OR instructions** — boolean logic must use short-circuit jumps (`JZ`/`JUMP`)
- **No LOADL/LOADG** — use `PUSHFP; LOAD n` for locals, `PUSHGP; LOAD n` for globals
- Labels cannot match instruction names (e.g., `add:` conflicts with `ADD`)

## Language Features

- Types: `integer`, `float`, `filum` (string), `&T` (pointer), `vec<T>` (array)
- Declaration syntax: `name: type = value` (ID-first, not type-first)
- Arrays: `vec<integer>[10]` or `vec<integer> = [1, 2, 3]` or `vec<integer> = [1 ... 10]`
- Control flow: `si` (if), `aliter` (else), `dum` (while), `pro` (for), `fac` (do-while), `collige` (match), `finis` (break), `perge` (continue)
- Functions: `fun name(param: type) -> return_type { ... }`
- Logical: `et` (&&), `aut` (||), `non` (!)

## Common Issues

- **Parser state**: PLY parser has global state. Use subprocess when testing multiple files to avoid parser pollution.
- **VM binary missing**: If `/tmp/vms/vms/vms` doesn't exist, rebuild from `vms-source.zip`.
- **Test comparisons**: AST path may produce slightly different but semantically equivalent bytecode. Tests check VM output identity, not bytecode identity.

## Development Workflow

```bash
python test_ast.py                   # Run AST path validation (compares original vs AST)
lat test                             # Run full test suite against expected outputs
```

## Files to Know

| File | Purpose |
|------|---------|
| `lat/cli.py` | CLI entry point, all commands |
| `lat/parsing/ast_parser.py` | AST parser (PLY-based) |
| `lat/ast/nodes.py` | AST node dataclasses |
| `lat/semantic/analyzer.py` | Semantic analyzer (visitor pattern) |
| `lat/codegen/generator.py` | AST → bytecode generator |
| `lat/ir/nodes.py` | IR node classes (three-address code) |
| `lat/ir/generator.py` | AST → IR converter |
| `lat/codegen/from_ir.py` | IR → bytecode generator |
| `test/*.lat` | Test programs |
| `test/*.ans` | Expected outputs |
| `examples/*.lat` | Example programs |
| `vms-source.zip` | VM source code (must be built) |
| `Dockerfile` | Multi-stage build (Chainguard images) |
