# OpenLatinum

A statically typed programming language with Latin-inspired syntax that compiles to stack-based EWVM bytecode. The compiler supports multiple compilation paths for teaching and experimentation.

## Language

**.lat**:
A source file containing OpenLatinum program code.
_Avoid_: Source file, program file

**.vms**:
The bytecode file produced by compiling a `.lat` file. Executed by the EWVM virtual machine.
_Avoid_: Binary, executable, compiled file

**.ans**:
An expected-output file used by the test suite to verify that a `.lat` program produces correct output when executed.
_Avoid_: Expected output, golden file

**EWVM**:
The target virtual machine that executes `.vms` bytecode. Available as both a C implementation and a Python interpreter.
_Avoid_: VM, runtime

**filum**:
The string type in OpenLatinum. Declared as `name: filum = "value"`.
_Avoid_: string, str

**vec**:
The array type constructor in OpenLatinum. Used as `vec<integer>[10]` for sized arrays or `vec<integer> = [1, 2, 3]` for initialized arrays.
_Avoid_: array, list, vector

**munus**:
The keyword for declaring a function. Example: `munus sum(a: integer) -> integer { ... }`.
_Avoid_: fun, function, def, proc

**reditus**:
The keyword for returning a value from a function. Example: `reditus a + b`.
_Avoid_: return, ret

**si / aliter**:
The keywords for if/else conditional branching. Example: `si x > 0 { ... } aliter { ... }`.
_Avoid_: if / else

**par / defectus**:
The keywords for match/switch pattern matching. `par` introduces the expression to match; `defectus` is the default case.
_Avoid_: match / default, switch / case, collige

**dum**:
The keyword for while loops. Example: `dum x < 10 { ... }`.
_Avoid_: while

**facio**:
The keyword for do-while loops. Example: `facio { ... } dum(x > 0)`.
_Avoid_: do, fac

**enim**:
The keyword for for loops. Example: `enim(i: integer = 0; i < 10; i = i + 1) { ... }`.
_Avoid_: for, pro

**confractus**:
The keyword for breaking out of a loop.
_Avoid_: break, finis

**perge**:
The keyword for continuing to the next loop iteration.
_Avoid_: continue

**et / aut / non**:
The keywords for logical AND, OR, and NOT respectively. Example: `si et x > 0 aut y < 10 { ... }`.
_Avoid_: &&, ||, !, and, or, not

**imprimo**:
The keyword for printing output. Example: `imprimo("Hello")`.
_Avoid_: print, output, write

**legerei / legeref / legeres**:
The keywords for reading integer, float, and string input from stdin respectively.
_Avoid_: read, input, scan

**boolean / verum / falsum**:
The boolean type and its literal values. `boolean` declares a boolean variable; `verum` is true; `falsum` is false.
_Avoid_: bool, true, false

**constans**:
The keyword for declaring a constant variable.
_Avoid_: const, let, final

## Relationships

- A **.lat** file compiles to exactly one **.vms** file
- A **.vms** file runs on the **EWVM** to produce output
- The test suite compares EWVM output against **.ans** files
- **si** / **aliter** form conditional branches
- **par** / **defectus** form pattern-matching cases
- **dum**, **facio**, and **enim** are three distinct loop constructs
- **confractus** and **perge** only operate within loop bodies
- **munus** declares functions; **reditus** returns from them
- **et** / **aut** / **non** operate on boolean expressions
- **imprimo** outputs values; **legerei** / **legeref** / **legeres** read input
- **vec** constructs array types; **filum** is the string type

## Example dialogue

> **Dev:** "Can I declare a **boolean** variable in a **.lat** file?"
>
> **Domain expert:** "That depends on which compilation path you use. The RD tokenizer recognizes **boolean**, **verum**, and **falsum**, but the main lexer doesn't. So you can only use booleans with the `--rd` path, not `--ast` or the default path."
>
> **Dev:** "What about **constans**?"
>
> **Domain expert:** "Same situation — it's in the RD tokenizer but missing from the main lexer. For now, stick to `munus` for functions and mutable variables with the standard paths."

## Flagged ambiguities

- `AGENTS.md` uses `fun` instead of **munus**, `pro` instead of **enim**, `fac` instead of **facio**, `collige` instead of **par**, and `finis` instead of **confractus**. These are incorrect — the actual keywords in the lexer are **munus**, **enim**, **facio**, **par**, and **confractus**.
- `boolean`, `verum`, `falsum`, and `constans` are recognized by the RD tokenizer but absent from the main PLY lexer. This means they only work with the `--rd` compilation path, creating a language dialect split.
- The README correctly documents the keywords but `AGENTS.md` does not.
