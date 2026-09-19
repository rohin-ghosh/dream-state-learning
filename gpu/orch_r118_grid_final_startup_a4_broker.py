"""Final bounded A4 recovery terminal; historical P1-P40 are never redispatched."""

import argparse
from pathlib import Path
from types import FunctionType

from gpu import orch_r118_grid_parallel_a4_broker as original


TERMINAL = 'R118_GRID_PARALLEL_RECOVERY_V2_TERMINAL.json'


def serve(*args):
    namespace = dict(original.serve.__globals__, TERMINAL=TERMINAL)
    return FunctionType(original.serve.__code__, namespace, 'A4_failed_startup_recovery_broker',
                        original.serve.__defaults__)(*args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--launch-receipt', type=Path, required=True)
    parser.add_argument('--prompt-root', type=Path, required=True)
    parser.add_argument('--principles', type=Path, required=True)
    parser.add_argument('--handoff', type=Path, required=True)
    parser.add_argument('--handoff-sha256', required=True)
    args = parser.parse_args()
    serve(args.config, args.launch_receipt, args.prompt_root, args.principles, args.handoff, args.handoff_sha256)


if __name__ == '__main__':
    main()
