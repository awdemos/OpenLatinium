# OpenLatinum Handbook

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Language Tutorial](#language-tutorial)
5. [Language Reference](#language-reference)
6. [CLI Reference](#cli-reference)
7. [Developer Guide](#developer-guide)
8. [Examples](#examples)

## Introduction

OpenLatinum is a statically typed programming language with Latin-inspired syntax. It compiles to stack-based bytecode. The compiler is written in Python and supports multiple compilation paths for teaching and experimentation.

### Key Features

- Static typing with basic types, pointers, and arrays
- Control flow: if, match, while, do-while, for, break, continue
- Functions with return types
- Recursive descent parser (new) alongside original PLY parser
- AST-based semantic analyzer with error collection
- Intermediate representation with optimizations

## Installation

### Prerequisites

- Python 3.8 or later
- pip

### Local Installation

```bash
git clone https://github.com/awdemos/OpenLatinum.git
cd OpenLatinum
pip install -e .
```

### Docker Installation

```bash
docker build -t openlatinum .
docker run --rm -v $(pwd):/app openlatinum build examples/hello_world.lat
```

## Quick Start

Create a file `hello.lat`:

```
munus main() {
    imprimo("Salve, mundus!\n")
}
```

Compile and run:

```bash
lat run hello.lat
```

Or compile only:

```bash
lat build hello.lat -o hello.vms
```

## Language Tutorial

### Your First Program

Every OpenLatinum program needs a `main` function as entry point:

```
munus main() {
    imprimo("Hello, World!\n")
}
```

Save as `hello.lat` and run with `lat run hello.lat`.

### Variables and Types

OpenLatinum uses ID-first declarations:

```
munus main() {
    count: integer = 10
    price: float = 19.99
    name: filum = "OpenLatinum"
    active: boolean = verum
    
    imprimo(count, "\n")
    imprimo(price, "\n")
    imprimo(name, "\n")
}
```

Types:
- `integer` — whole numbers
- `float` — decimal numbers (use `f` suffix: `3.14f`)
- `filum` — strings in double quotes
- `boolean` — `verum` (true) or `falsum` (false)

### String Operations

Strings support concatenation, subtraction, multiplication, and comparison:

```
munus main() {
    a: filum = "hello"
    b: filum = "world"
    
    // Concatenation
    c: filum = a + b
    imprimo(c, "\n")  // prints "helloworld"
    
    // Subtraction (remove characters)
    d: filum = "hello world"
    e: filum = "o"
    f: filum = d - e
    imprimo(f, "\n")  // prints "hell wrld"
    
    // Multiplication (repeat)
    g: filum = "abc"
    h: integer = 3
    i: filum = g * h
    imprimo(i, "\n")  // prints "abcabcabc"
    
    // Equality (content comparison)
    j: filum = "hello"
    k: filum = "hello"
    si j == k {
        imprimo("Equal!\n")
    }
    
    // Inequality
    si j != b {
        imprimo("Not equal!\n")
    }
}
```

### Reading Input

```
munus main() {
    age: integer = legerei("Enter your age: ")
    imprimo("You are ", age, " years old\n")
}
```

Read functions:
- `legerei("prompt")` — read integer
- `legeref("prompt")` — read float
- `legeres("prompt")` — read string

### Conditionals

If statement:

```
munus main() {
    x: integer = 10
    
    si x > 5 {
        imprimo("x is greater than 5\n")
    } aliter {
        imprimo("x is 5 or less\n")
    }
}
```

If expressions (ternary):

```
munus main() {
    x: integer = 10
    y: integer = si x > 5 { 100 } aliter { 0 }
    imprimo(y, "\n")  // prints 100
}
```

### Loops

While loop:

```
munus main() {
    i: integer = 0
    dum i < 5 {
        imprimo(i, "\n")
        i = i + 1
    }
}
```

For loop:

```
munus main() {
    enim(i: integer = 0; i < 5; i = i + 1) {
        imprimo(i, "\n")
    }
}
```

Do-while loop:

```
munus main() {
    i: integer = 0
    facio {
        imprimo(i, "\n")
        i = i + 1
    } dum(i < 5)
}
```

Break and continue:

```
munus main() {
    enim(i: integer = 0; i < 10; i = i + 1) {
        si i == 3 {
            perge  // skip to next iteration
        }
        si i == 7 {
            confractus  // exit loop
        }
        imprimo(i, "\n")
    }
}
```

### Arrays

Declaration with size:

```
munus main() {
    nums: vec<integer>[10]  // 10 integers, initialized to 0
    nums[0] = 42
    imprimo(nums[0], "\n")
}
```

List initialization:

```
munus main() {
    nums: vec<integer> = [10, 20, 30, 40, 50]
    imprimo(nums[2], "\n")  // prints 30
}
```

Range initialization:

```
munus main() {
    nums: vec<integer> = [1 ... 10]  // [1, 2, 3, ..., 10]
    imprimo(nums[9], "\n")  // prints 10
}
```

Multi-dimensional arrays:

```
munus main() {
    matrix: vec<vec<integer>> = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    imprimo(matrix[1][2], "\n")  // prints 6
}
```

### Functions

```
munus add(a: integer, b: integer) -> integer {
    reditus a + b
}

munus greet(name: filum) {
    imprimo("Hello, ", name, "!\n")
}

munus main() {
    result: integer = add(5, 3)
    imprimo(result, "\n")  // prints 8
    greet("World")
}
```

### Match (Switch)

```
munus main() {
    day: integer = 3
    
    par day {
        1 -> { imprimo("Monday\n") }
        2 -> { imprimo("Tuesday\n") }
        3 -> { imprimo("Wednesday\n") }
        defectus -> { imprimo("Other day\n") }
    }
}
```

Match with expressions:

```
munus main() {
    score: integer = 85
    
    par score {
        90 -> { imprimo("A\n") }
        80 -> { imprimo("B\n") }
        70 -> { imprimo("C\n") }
        60 -> { imprimo("D\n") }
        defectus -> { imprimo("F\n") }
    }
}
```

### Pointers

```
munus main() {
    nums: vec<integer> = [10, 20, 30]
    p: &integer = nums  // pointer to first element
    
    imprimo(p[0], "\n")  // prints 10
    p = p + 1
    imprimo(p[0], "\n")  // prints 20
    p = p + 1
    imprimo(p[0], "\n")  // prints 30
}
```

Pointer arithmetic example:

```
munus sumWithPointer(arr: vec<integer>, n: integer) -> integer {
    p: &integer = arr
    total: integer = 0
    i: integer
    enim(i: integer = 0; i < n; i = i + 1) {
        total = total + p[0]
        p = p + 1
    }
    reditus total
}

munus main() {
    nums: vec<integer> = [10, 20, 30, 40, 50]
    result: integer = sumWithPointer(nums, 5)
    imprimo("Sum: ", result, "\n")  // prints 150
}
```

### Comments

```
// This is a single-line comment

/*
This is a
multi-line comment
*/
```

## Language Reference

### Keywords

| Latin | English | Usage |
|-------|---------|-------|
| `si` | if | Conditional |
| `aliter` | else | Alternative branch |
| `par` | match | Pattern matching |
| `defectus` | default | Default case |
| `dum` | while | While loop |
| `facio` | do | Do-while loop |
| `enim` | for | For loop |
| `confractus` | break | Exit loop |
| `pergo` | continue | Skip iteration |
| `munus` | function | Function declaration |
| `reditus` | return | Return statement |
| `imprimo` | print | Output |
| `legerei` | read int | Read integer |
| `legeref` | read float | Read float |
| `legeres` | read string | Read string |
| `integer` | integer | Type |
| `float` | float | Type |
| `filum` | string | Type |
| `boolean` | boolean | Type |
| `vec` | vector | Array type |
| `verum` | true | Boolean literal |
| `falsum` | false | Boolean literal |
| `et` | and | Logical AND |
| `aut` | or | Logical OR |
| `non` | not | Logical NOT |

### Operators

| Operator | Description |
|----------|-------------|
| `+` | Addition, string concatenation |
| `-` | Subtraction, string character removal, negation |
| `*` | Multiplication, string repetition |
| `/` | Division |
| `%` | Modulo |
| `==` | Equal (value comparison for strings) |
| `!=` | Not equal (value comparison for strings) |
| `<` | Less than |
| `>` | Greater than |
| `<=` | Less or equal |
| `>=` | Greater or equal |
| `=` | Assignment |
| `&&` | Logical AND |
| `||` | Logical OR |
| `!` | Logical NOT |
| `&` | Address-of |

### Type System

Basic types: `integer`, `float`, `filum`, `boolean`

Pointer types: `&integer`, `&float`, `&filum`

Array types: `vec<integer>`, `vec<float>`, `vec<filum>`, `vec<boolean>`

Multi-dimensional arrays: `vec<vec<integer>> = [[1, 2, 3], [4, 5, 6]]`

### Type Compatibility

- `integer` and `float` are compatible in arithmetic (result is `float`)
- `boolean` can be used in conditions
- Arrays must match element type exactly
- Pointers support arithmetic with integers

## CLI Reference

### Commands

```
lat build <file> [options]       Compile .lat to .vms
lat run <file> [options]         Compile and run
lat test [options]               Run test suite
lat semantic_test [options]      Run semantic error tests
lat fmt <file> [options]         Format .lat file
lat examples [options]           Run example programs
```

### Options

| Option | Description |
|--------|-------------|
| `-o, --output <file>` | Output file |
| `-v, --verbose` | Verbose output |
| `--ast` | Use AST compilation path |
| `--ir` | Use IR compilation path |
| `--rd` | Use recursive descent parser |
| `--opt` | Enable IR optimizations |
| `--check` | Semantic analysis only |

### Formatting

Format a source file in place:

```bash
lat fmt program.lat
```

Format with output to a different file:

```bash
lat fmt program.lat -o formatted.lat
```

### Semantic Testing

Run semantic error tests (tests that verify error detection):

```bash
lat semantic_test
```

### Compilation Paths

Original path (default):
```bash
lat build file.lat
```

AST path with semantic analysis:
```bash
lat build file.lat --ast
```

IR path with optimizations:
```bash
lat build file.lat --ir --opt
```

Recursive descent parser:
```bash
lat build file.lat --rd --ir
```

Semantic check only:
```bash
lat build file.lat --check --rd
```

### Examples

```bash
# Build and run
lat run examples/hello_world.lat

# Compile with AST path
lat build program.lat --ast -o program.vms

# Run test suite
lat test -v

# Run example programs
lat examples
```

## Developer Guide

### Project Structure

```
  OpenLatinum/
  lat/
    cli/                # CLI package
      __init__.py       # CLI entry point and dispatch
      args.py           # Argument parsing
      compiler.py       # Compilation orchestration
      runner.py         # Test runner, formatter runner
      utils.py          # CLI utilities
    lexing/
      _lexer.py         # PLY-based lexer
    parsing/
      _parser.py        # Original PLY parser
      ast_parser.py     # AST-building PLY parser
      rd_parser.py      # Recursive descent parser
      tokenizer.py      # Hand-written tokenizer
    ast/
      nodes.py          # AST node classes
    semantic/
      analyzer.py       # Semantic analyzer
    codegen/
      generator.py      # AST-to-bytecode generator
      from_ir.py        # IR-to-bytecode generator
    ir/
      nodes.py          # IR node classes
      generator.py      # AST-to-IR generator
      optimizer.py      # IR optimizer
    fmt/
      formatter.py      # Code formatter (lat fmt)
    utils/
      errors.py         # Error utilities
  examples/             # Example programs
  test/                 # Test programs
  tests/                # Additional tests
  apresentacao/         # Tutorial programs
  docs/                 # Documentation
  Dockerfile
  README.md
  HANDBOOK.md           # This file
  EVOLUTION_ANALYSIS.md # Architecture analysis
  CONTEXT.md            # Development context and ADRs
```

### Compilation Pipeline

Three compilation paths are available:

1. **Original**: PLY parser → direct bytecode emission
2. **AST**: PLY/RD parser → AST → semantic analysis → bytecode
3. **IR**: PLY/RD parser → AST → semantic analysis → IR → bytecode

```
Source (.lat)
    |
    v
[PLY Lexer] or [RD Tokenizer]
    |
    v
[PLY Parser] or [RD Parser]
    |
    v
AST (nodes.py)
    |
    v
[Semantic Analyzer]
    |
    +--> --check (stop here)
    |
    v
AST CodeGen --or--> IR Generator
    |                    |
    v                    v
Bytecode            IR (nodes.py)
    |                    |
    |                    v
    |               [IR Optimizer] (--opt)
    |                    |
    |                    v
    |               IR CodeGen (from_ir.py)
    |                    |
    +--------------------+
    |
    v
Bytecode (.vms)
```

### Adding a New Feature

To add a new statement type:

1. Add AST node to `lat/ast/nodes.py`
2. Add parser support to `lat/parsing/rd_parser.py`
3. Add semantic check to `lat/semantic/analyzer.py`
4. Add code generation to `lat/codegen/generator.py`
5. Add IR generation to `lat/ir/generator.py`
6. Add IR-to-bytecode to `lat/codegen/from_ir.py`

### Testing

Run all tests:

```bash
lat test              # Run full test suite
lat test -v           # Verbose output
```

Run specific test paths:

```bash
python test_ast.py      # AST path validation
python ir_validate.py   # IR path validation
lat semantic_test       # Semantic error detection tests
```

Add a new test:

1. Create `test/my_feature.lat`
2. Create `test/my_feature.ans` with expected output
3. Run `lat test` to verify

### Docker Development

Build the image:
```bash
docker build -t openlatinum .
```

Run with local code:
```bash
docker run --rm -v $(pwd):/app openlatinum build /app/examples/hello_world.lat
```

## Examples

### Hello World

```
munus main() {
    imprimo("Salve, mundus!\n")
}
```

### Fibonacci

```
munus fib(n: integer) -> integer {
    si n <= 1 {
        reditus n
    }
    reditus fib(n - 1) + fib(n - 2)
}

munus main() {
    enim(i: integer = 0; i < 10; i = i + 1) {
        imprimo(fib(i), " ")
    }
    imprimo("\n")
}
```

### Bubble Sort

```
munus bsort(v: vec<integer>, n: integer) {
    enim(i: integer = 0; i < n; i = i + 1) {
        enim(j: integer = 0; j < n - i - 1; j = j + 1) {
            si v[j] > v[j + 1] {
                temp: integer = v[j]
                v[j] = v[j + 1]
                v[j + 1] = temp
            }
        }
    }
}

munus main() {
    nums: vec<integer> = [64, 34, 25, 12, 22, 11, 90]
    bsort(nums, 7)
    enim(i: integer = 0; i < 7; i = i + 1) {
        imprimo(nums[i], " ")
    }
    imprimo("\n")
}
```

### Factorial

```
munus factorial(n: integer) -> integer {
    si n <= 1 {
        reditus 1
    }
    reditus n * factorial(n - 1)
}

munus main() {
    n: integer = 5
    imprimo("Factorial of ", n, " is ", factorial(n), "\n")
}
```

### Array Sum

```
munus sum(v: vec<integer>, n: integer) -> integer {
    total: integer = 0
    enim(i: integer = 0; i < n; i = i + 1) {
        total = total + v[i]
    }
    reditus total
}

munus main() {
    nums: vec<integer> = [10, 20, 30, 40, 50]
    imprimo("Sum: ", sum(nums, 5), "\n")
}
```

### Prime Check

```
munus isPrime(n: integer) -> integer {
    si n <= 1 {
        reditus 0
    }
    si n <= 3 {
        reditus 1
    }
    si n % 2 == 0 {
        reditus 0
    }
    enim(i: integer = 3; i * i <= n; i = i + 2) {
        si n % i == 0 {
            reditus 0
        }
    }
    reditus 1
}

munus main() {
    enim(n: integer = 1; n <= 20; n = n + 1) {
        si isPrime(n) {
            imprimo(n, " is prime\n")
        }
    }
}
```

### String Operations

```
munus main() {
    // Concatenation
    a: filum = "Hello, "
    b: filum = "World!"
    imprimo(a + b, "\n")
    
    // Remove characters
    text: filum = "hello world"
    vowels: filum = "aeiou"
    imprimo(text - vowels, "\n")  // "hll wrld"
    
    // Repeat string
    pattern: filum = "*-"
    imprimo(pattern * 5, "\n")  // "*-*-*-*-*-"
    
    // Compare content
    s1: filum = "test"
    s2: filum = "test"
    si s1 == s2 {
        imprimo("Same content!\n")
    }
}
```

### Array Ranges

```
munus main() {
    // Range initialization [1 ... 10]
    nums: vec<integer> = [1 ... 10]
    imprimo(nums[0], " ")   // 1
    imprimo(nums[9], "\n")  // 10
    
    // Range with different bounds
    squares: vec<integer> = [5 ... 15]
    enim(i: integer = 0; i < 11; i = i + 1) {
        imprimo(squares[i], " ")
    }
    imprimo("\n")
}
```

### Matrix Operations

```
munus main() {
    m: vec<vec<integer>> = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    
    enim(i: integer = 0; i < 3; i = i + 1) {
        enim(j: integer = 0; j < 3; j = j + 1) {
            imprimo(m[i][j], " ")
        }
        imprimo("\n")
    }
}
```

### Rule 110 Cellular Automaton

See `apresentacao/10_rule110.lat` for a complete implementation.

### Quicksort

See `examples/qsort.lat` for a complete implementation.

---

## Appendix: Latin-to-English Quick Reference

| Latin | English |
|-------|---------|
| si | if |
| aliter | else |
| par | match/switch |
| defectus | default |
| dum | while |
| facio | do |
| enim | for |
| confractus | break |
| pergo | continue |
| munus | function |
| reditus | return |
| imprimo | print |
| legerei | read integer |
| legeref | read float |
| legeres | read string |
| integer | integer |
| float | float |
| filum | string |
| boolean | boolean |
| verum | true |
| falsum | false |
| vec | array/vector |
| et | and |
| aut | or |
| non | not |
| Salve, mundus! | Hello, World! |
