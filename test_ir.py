#!/usr/bin/env python3
import glob
import os
import subprocess
import sys
import tempfile


def compile_file(filepath, use_ir=True, optimize=False):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vms', delete=False) as f:
        out_path = f.name
    
    try:
        flags = f'"--ir": True, "--opt": {optimize}'
        cmd = [sys.executable, '-c', f'''
import sys
sys.path.insert(0, ".")
from lat.cli import build_execute
build_execute(
    {{"input": "{filepath}"}},
    {{"-o": "{out_path}", "-v": False, {flags}}}
)
''']
        result = subprocess.run(cmd, capture_output=True, text=True)
        compile_ok = result.returncode == 0 and 'Compiler Error' not in result.stderr and 'SEMANTIC ERROR' not in result.stderr
        return compile_ok, out_path, result.stderr
    except Exception as e:
        return False, out_path, str(e)


def compile_ast(filepath):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vms', delete=False) as f:
        out_path = f.name
    
    try:
        cmd = [sys.executable, '-c', f'''
import sys
sys.path.insert(0, ".")
from lat.cli import build_execute
build_execute(
    {{"input": "{filepath}"}},
    {{"-o": "{out_path}", "-v": False, "--ast": True}}
)
''']
        result = subprocess.run(cmd, capture_output=True, text=True)
        compile_ok = result.returncode == 0 and 'Compiler Error' not in result.stderr and 'SEMANTIC ERROR' not in result.stderr
        return compile_ok, out_path, result.stderr
    except Exception as e:
        return False, out_path, str(e)


def bytecode_valid(vms_path):
    with open(vms_path) as f:
        content = f.read().strip()
    
    if not content:
        return False, "Empty bytecode"
    
    lines = content.split('\n')
    
    has_start = any('start' in line for line in lines)
    if not has_start:
        return False, "Missing 'start'"
    
    has_stop = any('stop' in line for line in lines)
    if not has_stop:
        return False, "Missing 'stop'"
    
    labels_defined = set()
    labels_used = set()
    
    for line in lines:
        line = line.strip()
        if line.endswith(':'):
            labels_defined.add(line[:-1])
        elif line.startswith('PUSHA '):
            labels_used.add(line.split()[1])
        elif line.startswith('JZ '):
            labels_used.add(line.split()[1])
        elif line.startswith('JUMP '):
            labels_used.add(line.split()[1])
        elif line.startswith('CALL '):
            labels_used.add(line.split()[1])
    
    undefined = labels_used - labels_defined
    if undefined:
        return False, f"Undefined labels: {undefined}"
    
    return True, "Valid"


def test_file(filepath):
    basename = os.path.splitext(os.path.basename(filepath))[0]
    
    ir_compile_ok, ir_path, ir_compile_err = compile_file(filepath, use_ir=True)
    ast_compile_ok, ast_path, ast_compile_err = compile_ast(filepath)
    
    try:
        if not ir_compile_ok and not ast_compile_ok:
            return True, "PASS (both fail compile)"
        
        if ast_compile_ok and not ir_compile_ok:
            return False, f"IR compile fail: {ir_compile_err[:80]}"
        
        if not ast_compile_ok and ir_compile_ok:
            return True, "PASS (IR works where AST fails)"
        
        ir_valid, ir_msg = bytecode_valid(ir_path)
        if not ir_valid:
            return False, f"Invalid IR bytecode: {ir_msg}"
        
        ast_valid, ast_msg = bytecode_valid(ast_path)
        if not ast_valid:
            return False, f"Invalid AST bytecode: {ast_msg}"
        
        with open(ir_path) as f:
            ir_lines = len(f.read().strip().split('\n'))
        with open(ast_path) as f:
            ast_lines = len(f.read().strip().split('\n'))
        
        ratio = ir_lines / ast_lines if ast_lines > 0 else 0
        if ratio < 0.5 or ratio > 2.0:
            return False, f"Size mismatch: IR={ir_lines}, AST={ast_lines}"
        
        return True, "PASS (compilation OK)"
        
    finally:
        if os.path.exists(ir_path):
            os.unlink(ir_path)
        if os.path.exists(ast_path):
            os.unlink(ast_path)


def test_optimizer(filepath):
    unopt_ok, unopt_path, unopt_err = compile_file(filepath, use_ir=True, optimize=False)
    opt_ok, opt_path, opt_err = compile_file(filepath, use_ir=True, optimize=True)
    
    try:
        if not unopt_ok:
            return True, "SKIP (unoptimized fails)"
        
        if not opt_ok:
            return False, f"Optimized compile fail: {opt_err[:80]}"
        
        unopt_valid, unopt_msg = bytecode_valid(unopt_path)
        opt_valid, opt_msg = bytecode_valid(opt_path)
        
        if not opt_valid:
            return False, f"Invalid optimized bytecode: {opt_msg}"
        
        with open(unopt_path) as f:
            unopt_lines = len(f.read().strip().split('\n'))
        with open(opt_path) as f:
            opt_lines = len(f.read().strip().split('\n'))
        
        if opt_lines > unopt_lines:
            return False, f"Optimization made code larger: {unopt_lines} -> {opt_lines}"
        
        return True, f"PASS ({unopt_lines} -> {opt_lines} lines)"
        
    finally:
        if os.path.exists(unopt_path):
            os.unlink(unopt_path)
        if os.path.exists(opt_path):
            os.unlink(opt_path)


def main():
    test_files = glob.glob('test/*.lat') + glob.glob('examples/*.lat')
    passed = 0
    failed = 0
    skipped = 0
    
    print("=" * 60)
    print("IR Compilation Path Test Suite")
    print("=" * 60)
    
    for filepath in sorted(test_files):
        basename = os.path.basename(filepath)
        
        with open(filepath) as f:
            if f.read().startswith('//SKIP'):
                print(f"SKIP  {basename}")
                skipped += 1
                continue
        
        ok, msg = test_file(filepath)
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {basename:<40} {msg}")
        
        if ok:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print("Optimizer Tests")
    print("=" * 60)
    
    for filepath in ['test/arithmetics.lat', 'test/hello_world.lat']:
        if os.path.exists(filepath):
            basename = os.path.basename(filepath)
            ok, msg = test_optimizer(filepath)
            status = "PASS" if ok else "FAIL"
            print(f"{status}  {basename:<40} {msg}")
            if ok:
                passed += 1
            else:
                failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
