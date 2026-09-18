"""Preserve failed pre-model admission receipts while obtaining a fresh scan."""

import argparse
import fcntl
import importlib
from pathlib import Path
import sys


def validate_attempt(handoff, root, proc_root=Path('/proc')):
    handoff.require(not (root / 'LAUNCH.json').exists(), 'no_model_retry')
    prior = handoff.read(root / 'GUARD_STARTED.json')['identity']
    handoff.require(not (proc_root / str(prior['pid'])).exists(), 'old_guard_still_present')
    report = handoff.read(root / 'ADMISSION.json')
    handoff.require(report['clear'] is False and report['scanner_euid'] == 0, 'failed_privileged_prescan_only')
    reasons = report['blocking_reasons']
    handoff.require(reasons and all(reason.startswith('process_identity_drift:') for reason in reasons),
                    'only_transient_process_drift')
    handoff.require(not (root / 'native.log').exists(), 'no_native_attempt')


def receipt_writer(original, root, attempt):
    def write(path, value, *args, **kwargs):
        path = Path(path)
        if path.parent == root and path.name in ('GUARD_STARTED.json', 'ADMISSION.json'):
            path = attempt / path.name
        return original(path, value, *args, **kwargs)
    return write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source))
    handoff = importlib.import_module('gpu.orch_r139_math_astra_handoff')
    handoff.require(Path(handoff.__file__).resolve() == args.source / 'gpu/orch_r139_math_astra_handoff.py',
                    'exact_frozen_source')
    handoff.authorize()
    root = handoff.ROOT
    with (root / 'READMIT.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        validate_attempt(handoff, root)
        attempt = root / 'readmit_attempt2'
        attempt.mkdir()
        run, _ = handoff.native_modules()
        run.old.write = receipt_writer(run.old.write, root, attempt)
        handoff.run_native('guard')


if __name__ == '__main__':
    main()
