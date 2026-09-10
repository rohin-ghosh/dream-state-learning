"""Argument-free FeltCraft V7 CPU conformance runner."""

import sys

from .test_kernel import run_all


def main():
    if len(sys.argv) != 1:
        return 2
    try:
        output = run_all()
    except BaseException:
        return 1
    sys.stdout.buffer.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
