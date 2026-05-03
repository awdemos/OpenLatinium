"""CLI test execution for the OpenLatinum compiler."""

import os
from typing import Tuple, List
import glob

from tqdm import tqdm

from lat.cli.utils import echo_cmd, run_vms_py, info_cmd
from lat.cli.args import error
from lat.utils.colors import COLOR_GREEN, COLOR_RED, COLOR_YELLOW, RESET_COLOR


def _build_flags(opt_args: dict) -> str:
    """Build compilation flags string from opt_args."""
    flags = ""
    if opt_args.get("--ast"):
        flags += " --ast"
    if opt_args.get("--ir"):
        flags += " --ir"
    if opt_args.get("--opt"):
        flags += " --opt"
    if opt_args.get("--rd"):
        flags += " --rd"
    return flags


def _run_test_batch(
    input_files: List[str],
    output_files: List[str],
    opt_args: dict,
    record_mode: bool,
    ans_suffix: str = ".ans",
    out_suffix: str = "_com.out",
) -> Tuple[int, List[Tuple[str, str]], List[str]]:
    """Run a batch of tests and return (passed, failed, skipped)."""
    num_tests = len(input_files)
    failed_tests: List[Tuple[str, str]] = []
    skipped_tests: List[str] = []
    build_flags = _build_flags(opt_args)
    verbose = opt_args.get("-v", False)

    iterable = tqdm(
        zip(input_files, output_files),
        total=len(input_files),
        desc="Testing",
        colour="green",
    ) if not verbose else zip(input_files, output_files)

    if record_mode:
        for input_file, output_file in iterable:
            if verbose:
                print(COLOR_GREEN + "-" * 80 + RESET_COLOR)
            ret = echo_cmd(
                f"lat build {input_file} -o {output_file}{build_flags}",
                verbose=verbose,
            )
            if ret[0] == 2:
                num_tests -= 1
                skipped_tests.append(input_file)
                continue
            ret = run_vms_py(output_file, verbose=verbose)
            if ret[0] == 0:
                with open(os.path.splitext(output_file)[0] + ans_suffix, 'w') as f:
                    f.write(ret[1])
    else:
        for input_file, output_file in iterable:
            if verbose:
                print(COLOR_GREEN + "-" * 80 + RESET_COLOR)
            ret = echo_cmd(
                f"lat build {input_file} -o {output_file}{build_flags}",
                verbose=verbose,
            )
            if ret[0] == 1:
                num_tests -= 1
                failed_tests.append((input_file, ret[1]))
                continue
            elif ret[0] == 2:
                num_tests -= 1
                skipped_tests.append(input_file)
                continue
            input_data = '3.14\n314\n314' if os.path.basename(input_file).startswith("read") else ''
            ret = run_vms_py(output_file, input_data=input_data, verbose=verbose)
            if ret[0] == 1:
                num_tests -= 1
                failed_tests.append((input_file, ret[1]))
                continue
            with open(os.path.splitext(output_file)[0] + out_suffix, 'w') as f:
                f.write(ret[1])
            ret = echo_cmd(
                f"diff {os.path.splitext(output_file)[0]}{ans_suffix} {os.path.splitext(output_file)[0]}{out_suffix}",
                verbose=verbose,
            )
            if ret[0] != 0:
                num_tests -= 1
                failed_tests.append((input_file, ret[1]))

    return num_tests, failed_tests, skipped_tests


def _print_results(
    num_tests: int,
    failed_tests: List[Tuple[str, str]],
    skipped_tests: List[str],
    opt_args: dict,
):
    """Print test results."""
    verbose = opt_args.get("-v", False)
    clc = opt_args.get("-clc", False)
    if clc:
        if verbose:
            print(COLOR_GREEN + "-" * 80 + RESET_COLOR)
        # Cleanup is handled by the caller with specific patterns
    if verbose:
        print(COLOR_GREEN + "-" * 80 + RESET_COLOR)
    for failed_test, error_msg in failed_tests:
        print(f"{COLOR_RED}Failed: {failed_test}.{RESET_COLOR}")
        print(f"{COLOR_RED}{error_msg}{RESET_COLOR}")
    for skipped_test in skipped_tests:
        print(f"{COLOR_YELLOW}Skipped: {skipped_test}.{RESET_COLOR}")
    if verbose:
        print(COLOR_GREEN + "-" * 80 + RESET_COLOR)
    print(f"{COLOR_GREEN}Passed: {num_tests}.{RESET_COLOR}", end=" ")
    print(f"{COLOR_RED}Failed: {len(failed_tests)}.{RESET_COLOR}", end=" ")
    print(f"{COLOR_YELLOW}Skipped: {len(skipped_tests)}.{RESET_COLOR}")


def test_execute(req_args: dict, opt_args: dict):
    """Run the test suite."""
    input_files = glob.glob("test/*.lat")
    output_files = [os.path.splitext(input_file)[0] + ".vms" for input_file in input_files]
    record_mode = opt_args.get("-rec", False)

    num_tests, failed_tests, skipped_tests = _run_test_batch(
        input_files, output_files, opt_args, record_mode,
    )

    if opt_args.get("-clc"):
        echo_cmd("rm test/*.out", verbose=opt_args.get("-v", False))
        echo_cmd("rm test/*.vms", verbose=opt_args.get("-v", False))

    _print_results(num_tests, failed_tests, skipped_tests, opt_args)


def euler_execute(req_args: dict, opt_args: dict):
    """Run the Euler problem suite."""
    input_files = glob.glob("euler/problem*/*.lat")
    output_files = [os.path.splitext(input_file)[0] + ".vms" for input_file in input_files]
    record_mode = opt_args.get("-rec", False)

    num_tests, failed_tests, skipped_tests = _run_test_batch(
        input_files, output_files, opt_args, record_mode,
        ans_suffix=".ans",
        out_suffix=".out",
    )

    if opt_args.get("-clc"):
        echo_cmd("rm euler/problem*/*.out", verbose=opt_args.get("-v", False))
        echo_cmd("rm euler/problem*/*.vms", verbose=opt_args.get("-v", False))

    _print_results(num_tests, failed_tests, skipped_tests, opt_args)


def examples_execute(req_args: dict, opt_args: dict):
    """Run the examples suite."""
    input_files = glob.glob("examples/*.lat")
    output_files = [os.path.splitext(input_file)[0] + ".vms" for input_file in input_files]
    record_mode = opt_args.get("-rec", False)

    num_tests, failed_tests, skipped_tests = _run_test_batch(
        input_files, output_files, opt_args, record_mode,
        ans_suffix=".ans",
        out_suffix=".out",
    )

    if opt_args.get("-clc"):
        echo_cmd("rm examples/*.out", verbose=opt_args.get("-v", False))
        echo_cmd("rm examples/*.vms", verbose=opt_args.get("-v", False))

    _print_results(num_tests, failed_tests, skipped_tests, opt_args)
