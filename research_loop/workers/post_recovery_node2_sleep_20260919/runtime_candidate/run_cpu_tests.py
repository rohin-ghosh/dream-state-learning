"""Run only local CPU suites and write exclusive receipts in this candidate scope."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
WORKER = HERE.parent
REPO = HERE.parents[3]


def main():
    started = time.time()
    commands = [
        [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(directory), '-p', pattern, '-v']
        for directory, pattern in ((HERE, 'test_interrupted_sleep.py'),
            (WORKER, 'test_restart_contract.py'), (WORKER / 'replay_validation', 'test_strict_replay.py'))]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    results = []
    logs = []
    for command in commands:
        before = time.monotonic()
        process = subprocess.run(command, cwd=REPO, env=environment, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120, check=False)
        results.append(dict(argv=command, returncode=process.returncode,
            elapsed_seconds=time.monotonic() - before))
        logs.append('$ ' + ' '.join(command) + '\n' + process.stdout)
    paths = list(HERE.glob('*.py')) + [WORKER / 'restart_contract.py', WORKER / 'test_restart_contract.py',
        WORKER / 'replay_validation/strict_replay.py', WORKER / 'replay_validation/test_strict_replay.py']
    paths.extend((WORKER / 'replay_validation/source_evidence_1789790199409689539').glob('*/*/*.py'))
    output = ('\n'.join(logs)).encode()
    identifier = time.time_ns()
    output_path = HERE / f'TEST_OUTPUT_{identifier}.txt'
    with output_path.open('xb') as target:
        target.write(output)
    receipt = dict(schema='NODE2_INTERRUPTED_SLEEP_CPU_TESTS_V1', started_unix=started,
        finished_unix=time.time(), commands=results, all_passed=all(result['returncode'] == 0 for result in results),
        model_loaded=False, GPU_called=False, remote_calls=False, native_signals=False,
        execution_authorized=False, full_real_journals_audited=False,
        real_checkpoint_tensors_loaded=False, tests_use_synthetic_training_child=True,
        output_path=str(output_path.relative_to(REPO)), output_sha256=hashlib.sha256(output).hexdigest(),
        source_sha256={str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)})
    receipt_path = HERE / f'TEST_RECEIPT_{identifier}.json'
    with receipt_path.open('x') as target:
        json.dump(receipt, target, indent=2, sort_keys=True)
        target.write('\n')
    print(json.dumps(dict(all_passed=receipt['all_passed'], receipt=str(receipt_path),
        output=str(output_path), elapsed_seconds=receipt['finished_unix'] - started), indent=2))
    return 0 if receipt['all_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
