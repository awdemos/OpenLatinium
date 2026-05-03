#!/usr/bin/env python3
import glob
import os
import subprocess
import sys
import tempfile


def compile_file(filepath: str, ast_flag: bool) -> tuple[bool, str, str]:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vms', delete=False) as f:
        out_path = f.name
    
    try:
        cmd = [sys.executable, '-c', f'''
import sys
sys.path.insert(0, ".")
from lat.cli import build_execute
build_execute(
    {{"input": "{filepath}"}},
    {{"-o": "{out_path}", "-v": False, "--ast": {ast_flag}}}
)
''']
        result = subprocess.run(cmd, capture_output=True, text=True)
        compile_ok = result.returncode == 0 and 'Compiler Error' not in result.stderr
        return compile_ok, out_path, result.stderr
    except Exception as e:
        return False, out_path, str(e)


def run_vm(vms_path: str) -> tuple[bool, str, str]:
    vm_path = '/tmp/vms/vms/vms'
    result = subprocess.run([vm_path, vms_path], capture_output=True, text=True)
    ok = 'ERRO' not in result.stderr and 'Error' not in result.stderr and 'error' not in result.stderr.lower()
    return ok, result.stdout, result.stderr


def test_file(filepath: str) -> tuple[bool, str]:
    basename = os.path.splitext(os.path.basename(filepath))[0]
    
    orig_compile_ok, orig_path, orig_compile_err = compile_file(filepath, False)
    ast_compile_ok, ast_path, ast_compile_err = compile_file(filepath, True)
    
    try:
        if not orig_compile_ok and not ast_compile_ok:
            return True, "PASS (both fail compile)"
        
        if orig_compile_ok and not ast_compile_ok:
            return False, f"AST compile fail: {ast_compile_err[:80]}"
        
        if not orig_compile_ok and ast_compile_ok:
            return True, "PASS (AST works where original fails)"
        
        orig_run_ok, orig_stdout, orig_stderr = run_vm(orig_path)
        ast_run_ok, ast_stdout, ast_stderr = run_vm(ast_path)
        
        if not orig_run_ok and not ast_run_ok:
            return True, "PASS (both fail run)"
        
        if orig_run_ok and not ast_run_ok:
            return False, f"AST run fail: {ast_stderr[:80]}"
        
        if not orig_run_ok and ast_run_ok:
            return True, "PASS (AST works where original fails)"
        
        if orig_stdout == ast_stdout:
            return True, "PASS (outputs match)"
        else:
            return False, f"DIFFERENT OUTPUT"
            
    finally:
        if os.path.exists(orig_path):
            os.unlink(orig_path)
        if os.path.exists(ast_path):
            os.unlink(ast_path)


def main():
    test_files = glob.glob('test/*.lat') + glob.glob('examples/*.lat')
    passed = 0
    failed = 0
    
    print("=" * 60)
    print("AST Compilation Path Test Suite")
    print("=" * 60)
    
    for filepath in sorted(test_files):
        basename = os.path.basename(filepath)
        
        with open(filepath) as f:
            if f.read().startswith('//SKIP'):
                print(f"SKIP  {basename}")
                continue
        
        ok, msg = test_file(filepath)
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {basename:<40} {msg}")
        
        if ok:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
