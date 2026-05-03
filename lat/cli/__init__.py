"""OpenLatinum CLI package."""

import sys
from typing import Optional

from lat.utils.errors import CompilationError
from lat.cli.args import prepare_cmd_args, OptArgs, ReqArgs
from lat.cli.compiler import build_execute, check_execute, run_execute
from lat.cli.runner import test_execute, euler_execute, examples_execute
from lat.cli.utils import echo_cmd, run_vms_py, warn_cmd, info_cmd


def execute(opt_args: OptArgs, req_args: ReqArgs) -> None:
    """Dispatch to the appropriate execution handler."""
    if opt_args.get("--check"):
        check_execute(req_args, opt_args)
        return
    if req_args.get("run"):
        run_execute(req_args, opt_args)
    elif req_args.get("build"):
        build_execute(req_args, opt_args)
    elif req_args.get("test"):
        test_execute(req_args, opt_args)
    elif req_args.get("euler"):
        euler_execute(req_args, opt_args)
    elif req_args.get("examples"):
        examples_execute(req_args, opt_args)


def cli() -> None:
    """Main CLI entry point."""
    try:
        opt_args, req_args = prepare_cmd_args()
        if opt_args is None or req_args is None:
            sys.exit(0)
        execute(opt_args, req_args)
    except CompilationError:
        sys.exit(1)


__all__ = [
    "cli",
    "execute",
    "prepare_cmd_args",
    "build_execute",
    "check_execute",
    "run_execute",
    "test_execute",
    "euler_execute",
    "examples_execute",
    "echo_cmd",
    "run_vms_py",
    "warn_cmd",
    "info_cmd",
]
