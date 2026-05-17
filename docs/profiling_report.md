# OpenLatinum Performance Profiling Report

Date: 2026-05-16

## Compilation Performance

### Test Setup
- Program: `/tmp/large_test.lat` (~100 lines, 10 functions)
- Measurements: Average of 10 runs after 3 warm-up iterations

### Results

| Path | Time | Notes |
|------|------|-------|
| AST (no IR) | 9.40ms | Parser dominates (~7.4ms) |
| IR | 11.47ms | +22% overhead vs AST |
| Legacy | N/A | Does not support vec<> syntax |

### Breakdown (AST path)
1. **Parser (PLY)**: ~7.4ms (79%) - LALR table generation + tokenization
2. **Semantic Analysis**: ~0.9ms (9%) - Type checking, scope resolution
3. **Code Generation**: ~1.3ms (12%) - Bytecode emission

### Bottlenecks
- PLY parser initialization is expensive (LALR table generation)
- `isinstance()` checks are frequent (~58K calls)
- List `append()` operations dominate (~54K calls)

## VM Execution Performance

### Test Setup
- Program: Same large test compiled to bytecode
- Measurements: Average of 100 runs after 3 warm-up iterations
- Bytecode size: 710 instructions

### Results (Before Optimization)
- **Execution time**: 26.00ms per run
- **Time per instruction**: 36.62 µs

### Results (After Optimization)
- **Execution time**: 13.72ms per run
- **Time per instruction**: 19.32 µs
- **Improvement**: 47% faster

### Optimization Applied
**Pre-parsed instructions**: Modified `load()` to pre-parse bytecode into `(method, arg)` tuples, eliminating per-step string operations:
- Removed `line.split(None, 1)` per instruction
- Removed `parts[0].upper()` per instruction
- Removed `getattr()` lookup per instruction
- Removed label checks per instruction

### Remaining Bottlenecks
1. **Value object creation**: `Value` dataclass instantiation (~759K calls)
2. **Stack operations**: `_push()` and `_pop()` with bounds checking
3. **Heap access**: String-based dictionary lookups in `self.heap`

## Recommendations

### Short Term
1. **Cache PLY parser**: PLY regenerates LALR tables on every invocation. Cache to disk.
2. **Use tuples instead of Value dataclass**: `(type, val)` tuples are faster than dataclasses.
3. **Pre-allocate stack**: Use a list of fixed size instead of dynamic growth.

### Long Term
1. **Replace PLY with handwritten parser**: Recursive descent parsers are faster to initialize.
2. **Compile to Python bytecode**: Generate Python bytecode for even faster execution.
3. **JIT compilation**: Hot paths could be compiled to native code.

## Files Modified
- `lat/vm_interpreter.py`: Added instruction pre-parsing
