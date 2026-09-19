"""Run only local CPU suites and preserve exact operator/test/source provenance."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[2]
BOUNDARY = HERE.parent / 'post_recovery_retention_boundary_20260918'


def validate(output):
    output = Path(output).absolute()
    if output.resolve() != output or not output.is_relative_to(HERE) or output.exists():
        raise ValueError('new_own_worker_validation_receipt_only')
    files = sorted(HERE.glob('*.py')) + sorted(BOUNDARY.glob('*.py'))
    pins = {str(path.relative_to(REPOSITORY)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    results = []
    for worker in (HERE, BOUNDARY):
        command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(worker), '-p', 'test_*.py', '-q']
        started = time.monotonic()
        result = subprocess.run(command, cwd=REPOSITORY, capture_output=True, text=True, timeout=120,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES=''))
        results.append(dict(command=command, returncode=result.returncode, stdout=result.stdout,
            stderr=result.stderr, elapsed_seconds=time.monotonic() - started))
    if pins != {str(path.relative_to(REPOSITORY)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}:
        raise ValueError('code_changed_during_tests')
    receipt = dict(schema='PAIR_RECEIVER_OPERATOR_CPU_RECEIPT_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        source_pins=pins, results=results, passed=all(result['returncode'] == 0 for result in results),
        native_signals=[], reservations=[], parent_actions=[], remote_actions=[], GPU_dispatches=[],
        synthetic_only=True, actual_live_handoff_authorization=False)
    with output.open('x') as handle:
        handle.write(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
        handle.flush()
        os.fsync(handle.fileno())
    if not receipt['passed']:
        raise ValueError('CPU_tests_failed_see_durable_receipt:' + str(output))
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    arguments = parser.parse_args()
    print(json.dumps(validate(arguments.output), sort_keys=True, indent=2))
