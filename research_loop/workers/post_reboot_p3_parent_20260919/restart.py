"""Foreground supervisor restart: fresh binding, existing ledger, then exec."""

import fcntl
import json
import os
from pathlib import Path
import sys
import time

import preflight
import runner


SOURCE_PINS = {
    'runner.py': 'f459b8eba126b4d0c8b595f2e48fa12e39ebff08cdbf84ef718b1d15236808d2',
    'preflight.py': '7a1ffe365d6ec57b3832db17487c3a45e472fefdc4f7269a8b5f52399a415c0b',
    'P3_RETRY_PARENT_MANIFEST.json': 'b30d289ff597286563de3e4f8037af47fa8500cc6961fc4f1a7048a6f3c989ca',
}
UNTIL = 1790359200


def active_parent():
    path = runner.HERE / 'PROCESS.json'
    if not path.exists():
        return False
    expected = json.loads(path.read_text())['process']
    actual = runner.process(expected['pid'])
    return bool(actual and actual['state'] not in {'Z', 'X'} and all(
        actual[field] == expected[field] for field in ('boot_id', 'pid', 'start_ticks')))


def validate_prior():
    if time.time() >= UNTIL:
        raise ValueError('existing_lease_expired')
    for name, checksum in SOURCE_PINS.items():
        if runner.sha(runner.HERE / name) != checksum:
            raise ValueError('restart_source_pin_changed')
    manifest = json.loads((runner.HERE / 'P3_RETRY_PARENT_MANIFEST.json').read_text())
    if manifest['hard_end_unix'] != UNTIL:
        raise ValueError('original_horizon_required')
    previous = json.loads((runner.HERE / 'PREFLIGHT.json').read_text())
    pins = json.loads((runner.HERE / 'private/PRIOR_LEDGER_PINS.json').read_text())
    if any(runner.sha(runner.LEDGER / name) != checksum for name, checksum in pins.items()):
        raise ValueError('previous_attempt_artifacts_changed')
    if runner.sha(runner.LEDGER / 'SEED.json') != previous['seed_sha256']:
        raise ValueError('original_seed_changed')
    if not os.environ.get('NVIDIA_API_KEY'):
        raise ValueError('inherited_provider_credential_required')


def preserve_previous():
    archive = runner.HERE / 'receipts' / ('restart_' + str(time.time_ns()))
    for name in ('PREFLIGHT.json', 'PROCESS.json', 'VERIFIED_PROCESS.json', 'EXIT.json',
                 'private/PRIOR_LEDGER_PINS.json', 'operator/RATE_LIMIT.json'):
        source = runner.HERE / name
        if source.exists():
            runner.save(archive / name, json.loads(source.read_text()))


def main():
    os.umask(0o077)
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    phase = 'SINGLE_OWNER_CHECK'
    lock_path = runner.HERE / 'operator/RESTART.lock'
    lock_path.parent.mkdir(exist_ok=True)
    with lock_path.open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if active_parent():
                print(json.dumps(dict(status='EXACT_PARENT_ALREADY_ALIVE_NO_ACTION', provider_calls=0)))
                return 75
            phase = 'PRIOR_EVIDENCE_VALIDATION'
            validate_prior()
            preserve_previous()
            phase = 'FRESH_NATIVE_LEDGER_PREFLIGHT'
            preflight.main()
            if time.time() >= UNTIL:
                raise ValueError('existing_lease_expired')
            argv = ['/usr/bin/python3', '-B', str(runner.HERE / 'runner.py')]
            runner.save(runner.HERE / 'RESTART_LAST_RESULT.json', dict(
                observed_utc=runner.utc(time.time()), status='FRESH_PREFLIGHT_PASSED_EXEC_PENDING',
                process=runner.process(os.getpid()), argv=argv,
                preflight_sha256=runner.sha(runner.HERE / 'PREFLIGHT.json'),
                provider_calls=0, native_signals=0, until_unix=UNTIL))
            phase = 'EXEC_ORIGINAL_GATED_RUNNER'
            os.execv(argv[0], argv)
        except Exception as error:
            runner.save(runner.HERE / 'RESTART_LAST_RESULT.json', dict(
                observed_utc=runner.utc(time.time()), status='RESTART_REFUSED_NO_PROVIDER_CALL',
                phase=phase, error_type=type(error).__name__, native_signals=0, provider_calls=0))
            return 75 if isinstance(error, BlockingIOError) else 1


if __name__ == '__main__':
    sys.exit(main())
