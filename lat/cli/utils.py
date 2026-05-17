"""CLI utilities for the OpenLatinum compiler."""

from typing import Tuple
import os
import subprocess  # nosec: B404 - subprocess used safely with shell=False
import shlex
import sys

from lat.utils.colors import COLOR_BLUE, COLOR_RED, COLOR_YELLOW, RESET_COLOR
from lat.vm_interpreter import run_bytecode


def echo_cmd(cmd: str, verbose: bool = False) -> Tuple[int, str]:
    """Execute a shell command and return (returncode, output)."""
    if verbose:
        print(f"{COLOR_BLUE}[CMD]{RESET_COLOR} {cmd}")
    args = shlex.split(cmd)
    if args[0] == "diff":
        result = subprocess.run(  # nosec: B603 - args are from shlex.split, not user input
            args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.stdout:
            return 1, result.stdout
    elif args[0] == "rm":
        result = subprocess.run(  # nosec: B603 - args are from shlex.split, not user input
            args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return result.returncode, result.stderr
    else:
        result = subprocess.run(  # nosec: B603 - args are from shlex.split, not user input
            args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 1:
            return 1, result.stderr
        elif result.returncode == 2:
            return 2, "The program was skipped."
    return 0, ""


def run_vms_py(output_file: str, input_data: str = '', verbose: bool = False) -> Tuple[int, str]:
    """Run a compiled .vms file through the VM interpreter."""
    if not input_data and not sys.stdin.isatty():
        input_data = sys.stdin.read()
    
    c_vm_path = '/tmp/vms/vms/vms'
    if os.path.exists(c_vm_path):
        if verbose:
            print(f"{COLOR_BLUE}[CMD]{RESET_COLOR} {c_vm_path} {output_file}")
        try:
            if sys.stdin.isatty():
                result = subprocess.run(
                    [c_vm_path, output_file],
                    shell=False,
                    timeout=300,
                )
                return result.returncode, ""
            else:
                result = subprocess.run(
                    [c_vm_path, output_file],
                    input=input_data,
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return 0, result.stdout
            if verbose:
                print(f"{COLOR_YELLOW}[WARN]{RESET_COLOR} C VM failed: {result.stderr.strip() if hasattr(result, 'stderr') else 'unknown'}")
        except Exception as e:
            if verbose:
                print(f"{COLOR_YELLOW}[WARN]{RESET_COLOR} C VM error: {e}")
    
    if verbose:
        print(f"{COLOR_BLUE}[CMD]{RESET_COLOR} python vm {output_file}")
    try:
        with open(output_file, 'r') as f:
            source = f.read()
        result = run_bytecode(source, input_data)
        return 0, result
    except Exception as e:
        return 1, str(e)


def warn_cmd(msg: str, verbose: bool = False):
    """Print a warning message if verbose mode is on."""
    if verbose:
        print(f"{COLOR_YELLOW}[WARN]{RESET_COLOR} {msg}")


def info_cmd(msg: str, verbose: bool = False):
    """Print an info message if verbose mode is on."""
    if verbose:
        print(f"{COLOR_BLUE}[INFO]{RESET_COLOR} {msg}")


def _remove_files(pattern: str, verbose: bool = False) -> int:
    """Remove files matching a glob pattern. Returns count of removed files."""
    import glob as glob_module
    import logging
    logger = logging.getLogger(__name__)
    files = glob_module.glob(pattern)
    removed = 0
    for f in files:
        try:
            os.remove(f)
            removed += 1
        except OSError as exc:
            logger.warning("Failed to remove %s: %s", f, exc)
            raise
    if verbose and files:
        print(f"{COLOR_BLUE}[INFO]{RESET_COLOR} Removed {removed} files matching {pattern}")
    return removed
