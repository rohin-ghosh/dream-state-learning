"""Apply the tested idle-accounting scanner only to recovery custody."""

import argparse
import json
from pathlib import Path
import subprocess
from types import FunctionType, SimpleNamespace

from gpu import orch_r108_code_parent_r115_recover_guard as recovery


def scan(root):
    source = Path(__file__).resolve().parents[1]
    result = subprocess.run(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
        'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(source), 'python3', '-B', '-m',
        'gpu.orch_r108_code_parent_r115_admission', 'scan', '--root', str(root)],
        capture_output=True, text=True, timeout=120, check=True)
    return json.loads(result.stdout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    original = SimpleNamespace(**dict(vars(recovery.original), scan=scan))
    launch = FunctionType(recovery.guard.__code__, dict(recovery.guard.__globals__, original=original), 'guard')
    launch(args.root)
