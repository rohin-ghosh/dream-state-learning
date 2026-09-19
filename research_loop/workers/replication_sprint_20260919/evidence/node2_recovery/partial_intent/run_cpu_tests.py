"""Run bounded CPU suites; save only logs, pins and receipts in this scope."""

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
WALL = HERE.parent / 'runtime_repair'
HISTORICAL = REPO / 'research_loop/workers/post_recovery_node2_sleep_20260919'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_state():
    provenance = json.loads((HERE / 'PROVENANCE.json').read_bytes())
    receipt_path = REPO / provenance['protected_baseline_receipt']
    if sha256(receipt_path) != provenance['protected_baseline_receipt_sha256']:
        raise ValueError('historical_baseline_receipt_changed')
    baseline = json.loads(receipt_path.read_bytes())
    expected = dict(baseline['source_sha256_after'], **baseline['originals_after']['actual_sha256'])
    expected[provenance['protected_baseline_receipt']] = provenance['protected_baseline_receipt_sha256']
    expected[provenance['historical_inventory']] = provenance['historical_inventory_sha256']
    actual = {name: sha256(REPO / name) for name in expected}
    return dict(all_unchanged=actual == expected, actual_sha256=actual,
        mismatches=[name for name, value in expected.items() if actual[name] != value])


def candidate_sources():
    files = sorted(HERE.glob('*.py')) + [HERE / 'PROVENANCE.json', HERE / 'DESIGN_FOR_MAIN_AND_MC.md']
    return {str(path.relative_to(REPO)): sha256(path) for path in files}


def main():
    started = time.time()
    before = protected_state()
    sources_before = candidate_sources()
    commands = []
    logs = []
    suites = ((HERE, 'test_reconcile.py', 33), (WALL, 'test_interrupted_sleep.py', 39),
        (WALL, 'test_applied_wall.py', 20), (HISTORICAL, 'test_restart_contract.py', 18),
        (HISTORICAL / 'replay_validation', 'test_strict_replay.py', 22))
    if before['all_unchanged']:
        with tempfile.TemporaryDirectory(dir=HERE, prefix='.cpu-run-') as temporary:
            environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TMPDIR=temporary,
                CUDA_VISIBLE_DEVICES='')
            for directory, pattern, expected_count in suites:
                argv = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(directory), '-p', pattern, '-v']
                suite_started = time.monotonic()
                try:
                    result = subprocess.run(argv, cwd=REPO, env=environment, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180, check=False)
                    output, returncode = result.stdout, result.returncode
                except subprocess.TimeoutExpired as error:
                    output = error.stdout or b''
                    if isinstance(output, bytes):
                        output = output.decode(errors='replace')
                    output += '\nCPU_SUITE_TIMEOUT\n'
                    returncode = 124
                counts = re.findall(r'^Ran (\d+) tests? in ', output, re.MULTILINE)
                count = int(counts[-1]) if counts else 0
                commands.append(dict(argv=argv, returncode=returncode, tests_run=count,
                    expected_tests=expected_count, count_matches=count == expected_count,
                    elapsed_seconds=time.monotonic() - suite_started))
                logs.append('$ ' + ' '.join(argv) + '\n' + output)
    after = protected_state()
    sources_after = candidate_sources()
    passed = (before['all_unchanged'] and after['all_unchanged'] and sources_before == sources_after
        and len(commands) == len(suites)
        and all(command['returncode'] == 0 and command['count_matches'] for command in commands))
    identifier = time.time_ns()
    output_path = HERE / f'TEST_OUTPUT_{identifier}.txt'
    output = '\n'.join(logs).encode()
    with output_path.open('xb') as target:
        target.write(output)
    receipt = dict(schema='ASTRA7_EMPTY_7808_RECONCILIATION_CPU_TESTS_V1',
        started_unix=started, finished_utc=datetime.now(timezone.utc).isoformat(),
        all_passed=passed, tests_run=sum(command['tests_run'] for command in commands),
        commands=commands, protected_before=before, protected_after=after,
        source_sha256_before=sources_before, source_sha256_after=sources_after,
        sources_unchanged_during_tests=sources_before == sources_after,
        output_path=str(output_path.relative_to(REPO)), output_sha256=hashlib.sha256(output).hexdigest(),
        original_auditor_tests='Full contiguous synthetic 7808-record prefix and three retained pending rows',
        test_model_or_checkpoint_loaded=False, real_journal_read=False, remote_calls=False,
        GPU_called=False, native_process_started=False, staging=False, live_artifact_mutated=False,
        original_history_modified=False, production_prefix_tail_integration_implemented=False,
        runtime_installed=False, C0_or_Astra7_restored=False, execution_authorized=False,
        pending_Main_review_of_link_unlink_semantics=True)
    receipt_path = HERE / f'TEST_RECEIPT_{identifier}.json'
    with receipt_path.open('x') as target:
        json.dump(receipt, target, indent=2, sort_keys=True)
        target.write('\n')
    print(json.dumps(dict(all_passed=passed, tests_run=receipt['tests_run'],
        originals_unchanged=before['all_unchanged'] and after['all_unchanged'],
        receipt=str(receipt_path.relative_to(REPO)), output=str(output_path.relative_to(REPO)),
        elapsed_seconds=time.time() - started), indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
