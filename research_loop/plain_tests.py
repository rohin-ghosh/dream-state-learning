"""Tiny dependency-free runner for this repository's plain test functions."""

from __future__ import annotations

import argparse
import importlib
import inspect
import sys
import traceback


def run_module(name: str) -> tuple[int, int]:
    module = importlib.import_module(name)
    passed = failed = 0
    for test_name, function in sorted(vars(module).items()):
        if not test_name.startswith("test_") or not callable(function):
            continue
        if inspect.signature(function).parameters:
            continue
        try:
            function()
        except BaseException:
            failed += 1
            print(f"FAIL {name}.{test_name}", file=sys.stderr)
            traceback.print_exc()
        else:
            passed += 1
            print(f"ok {name}.{test_name}")
    return passed, failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("modules", nargs="+")
    args = parser.parse_args(argv)
    passed = failed = 0
    for module in args.modules:
        module_passed, module_failed = run_module(module)
        passed += module_passed
        failed += module_failed
    print(f"plain-tests: {passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
