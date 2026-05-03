# OpenLatinum

## Overview

OpenLatinum is a statically typed programming language with Latin-inspired syntax. It compiles `.lat` source files to stack-based bytecode. The compiler is written in Python and supports multiple compilation paths for teaching and experimentation.

This project is a community-driven evolution of the original OpenLatinum compiler (University of Minho, 2022).

## Installation

### Local Install

```bash
git clone https://github.com/awdemos/OpenLatinum.git
cd OpenLatinum
pip install -e .
```

### Docker (Recommended)

```bash
docker build -t latinium .
docker run --rm -v $(pwd):/app latinium build examples/hello_world.lat
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

`par` (switch):
```rust
par expression {
    expression -> {
        // code
    }
    default -> {
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
  -rec, --record  Record program outputs
  -clc, --clean-up  Clean generated files
```
