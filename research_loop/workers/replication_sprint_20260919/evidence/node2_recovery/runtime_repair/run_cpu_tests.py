"""Bounded local CPU suites; receipts and temporary files stay in this directory."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
WORKER = REPO / 'research_loop/workers/post_recovery_node2_sleep_20260919'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_originals():
    provenance = json.loads((HERE / 'COPY_PROVENANCE.json').read_bytes())
    expected = dict(provenance['originals'])
    expected[provenance['inventory']['path']] = provenance['inventory']['sha256']
    actual = {name: sha256(REPO / name) for name in expected}
    return dict(all_unchanged=actual == expected, actual_sha256=actual,
        mismatches=[name for name, value in expected.items() if actual[name] != value])


def local_sources():
    paths = list(HERE.glob('*.py')) + list((HERE / 'fixtures').glob('*.json'))
    paths.append(HERE / 'COPY_PROVENANCE.json')
    paths.extend((WORKER / 'replay_validation/source_evidence_1789790199409689539').glob('*/*/*.py'))
    return {str(path.relative_to(REPO)): sha256(path) for path in sorted(paths)}


def main():
    started = time.time()
    originals_before = verify_originals()
    sources_before = local_sources()
    results = []
    logs = []
    suites = ((HERE, 'test_interrupted_sleep.py', 39), (HERE, 'test_applied_wall.py', 20),
        (WORKER, 'test_restart_contract.py', 18),
        (WORKER / 'replay_validation', 'test_strict_replay.py', 22))
    if originals_before['all_unchanged']:
        with tempfile.TemporaryDirectory(dir=HERE, prefix='.cpu-run-') as temporary:
            environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TMPDIR=temporary)
            for directory, pattern, expected_count in suites:
                command = [sys.executable, '-B', '-m', 'unittest', 'discover',
                    '-s', str(directory), '-p', pattern, '-v']
                before = time.monotonic()
                try:
                    process = subprocess.run(command, cwd=REPO, env=environment, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120, check=False)
                    output, returncode = process.stdout, process.returncode
                except subprocess.TimeoutExpired as error:
                    output = error.stdout or b''
                    if isinstance(output, bytes):
                        output = output.decode(errors='replace')
                    output += '\nCPU_SUITE_TIMEOUT\n'
                    returncode = 124
                counts = re.findall(r'^Ran (\d+) tests? in ', output, flags=re.MULTILINE)
                count = int(counts[-1]) if counts else 0
                results.append(dict(argv=command, returncode=returncode, tests_run=count,
                    expected_tests=expected_count, count_matches=count == expected_count,
                    elapsed_seconds=time.monotonic() - before))
                logs.append('$ ' + ' '.join(command) + '\n' + output)
    originals_after = verify_originals()
    sources_after = local_sources()
    output = ('\n'.join(logs)).encode()
    identifier = time.time_ns()
    output_path = HERE / f'TEST_OUTPUT_{identifier}.txt'
    with output_path.open('xb') as target:
        target.write(output)
    passed = (originals_before['all_unchanged'] and originals_after['all_unchanged']
        and sources_before == sources_after and len(results) == len(suites)
        and all(result['returncode'] == 0 and result['count_matches'] for result in results))
    receipt = dict(schema='NODE2_OBSERVED_APPLIED_WALL_CPU_TESTS_V1', started_unix=started,
        finished_unix=time.time(), finished_utc=datetime.now(timezone.utc).isoformat(),
        commands=results, all_passed=passed, tests_run=sum(result['tests_run'] for result in results),
        originals_before=originals_before, originals_after=originals_after,
        source_sha256_before=sources_before, source_sha256_after=sources_after,
        sources_unchanged_during_tests=sources_before == sources_after,
        tests_use_exact_observed_plan_bytes=True, tests_use_synthetic_state_and_training_child=True,
        test_path_mapping_only=True, original_validation_code_hash_pinned=True,
        full_real_journals_audited=False, real_checkpoint_tensors_loaded=False,
        historical_WALL_EXTENDED_event_located=False, model_loaded=False, GPU_called=False,
        remote_calls=False, native_signals=False, execution_authorized=False,
        runtime_installed=False, live_files_modified=False, original_candidate_modified=False,
        partial_intent_reconciled=False, deadline_extended=False,
        output_path=str(output_path.relative_to(REPO)), output_sha256=hashlib.sha256(output).hexdigest())
    receipt_path = HERE / f'TEST_RECEIPT_{identifier}.json'
    with receipt_path.open('x') as target:
        json.dump(receipt, target, indent=2, sort_keys=True)
        target.write('\n')
    print(json.dumps(dict(all_passed=passed, tests_run=receipt['tests_run'],
        originals_unchanged=originals_before['all_unchanged'] and originals_after['all_unchanged'],
        receipt=str(receipt_path.relative_to(REPO)), output=str(output_path.relative_to(REPO)),
        elapsed_seconds=receipt['finished_unix'] - started), indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
