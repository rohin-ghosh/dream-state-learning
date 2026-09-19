"""Run isolated CPU suites and emit bounded receipts, never stage or launch."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
NAMES = ['c0_kernel.py', 'c0_applied_wall_validation.py', 'c0_restart_contract.py',
    'c0_tail.py', 'c0_startup.py', 'gpu/c0_pending_entry.py']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    stamp = str(time.time_ns())
    trace = HERE / ('SYNTHETIC_TRACE_' + stamp + '.json')
    output = HERE / ('CPU_TESTS_' + stamp + '.txt')
    original = json.loads((HERE / 'fixtures/ORIGINAL_GUARD.json').read_bytes())
    originals = {str(path.relative_to(HERE / 'source_evidence')): sha(path)
        for path in (HERE / 'source_evidence').rglob('*.py')}
    assert all(original['source_pins'][name] == value for name, value in originals.items())
    protected = json.loads((HERE / 'COPY_PROVENANCE.json').read_bytes())['untouched_pins']
    repo = HERE.parents[5] if len(HERE.parents) > 5 else HERE
    checked = {name: value for name, value in protected.items() if (repo / name).is_file()}
    assert all(sha(repo / name) == value for name, value in checked.items())
    started = time.time()
    process = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(HERE),
        '-p', 'test_*.py', '-v'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='', C0_CPU_TRACE=str(trace)))
    output.write_text(process.stdout)
    assert all(sha(repo / name) == value for name, value in checked.items())
    assert all(sha(HERE / 'source_evidence' / name) == value for name, value in originals.items())
    receiving = os.environ.get('C0_TEST_SOURCE_ROOT')
    receiving_pins = None
    if receiving:
        source = Path(receiving)
        receiving_pins = {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}
        expected = dict(original['source_pins'], **{name: sha(HERE / Path(name).name) for name in NAMES})
        assert receiving_pins == expected, 'actual_receiving_source_closure'
        original_source = Path('/localhome/local-rohing/orch_r216_C0_20260918_attempt2/source_r233_lease_continuation')
        assert {str(path.relative_to(original_source)): sha(path)
            for path in original_source.rglob('*.py')} == original['source_pins'], 'original_live_source_unchanged'
        import c0_kernel
        c0_kernel.observed_wall_compatibility((original_source.parent /
            'control_r233_lease_continuation/PLAN.json').read_bytes(), 'C0')
        assert sha(original_source.parent / 'control_r233_lease_continuation/GUARD.json') == sha(
            HERE / 'fixtures/ORIGINAL_GUARD.json'), 'original_live_guard_unchanged'
    receipt = dict(schema='C0_STARTUP_CPU_TEST_RECEIPT_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        passed=process.returncode == 0, returncode=process.returncode, elapsed_seconds=time.time() - started,
        tests_passed_lines=process.stdout.count(' ... ok\n'), output=dict(path=str(output), sha256=sha(output)),
        synthetic_trace=dict(path=str(trace), sha256=sha(trace)) if trace.exists() else None,
        runtime_additions={name: sha(HERE / Path(name).name) for name in NAMES},
        tested_source_files={str(path.relative_to(HERE)): sha(path) for path in HERE.rglob('*.py')},
        copied_original_sources=originals, existing_protected_files_checked=len(checked), originals_unchanged=True,
        receiving_source_root=receiving, receiving_source_pins=receiving_pins,
        model_or_GPU_execution=False, remote_mutations=False, staging_or_launch=False,
        live_recovery_readiness=False,
        limitations=['Synthetic journal, adapter and optimizer/RNG; no real model computation.',
            'External OS launch/namespace and anchor inventory are mocked in CPU chain.',
            'Main-host tests are not node2 receiving admission or evidence of restored C0.'])
    path = HERE / ('TEST_RECEIPT_' + stamp + '.json')
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(str(path))
    print(process.stdout[-2000:])
    raise SystemExit(process.returncode)


if __name__ == '__main__':
    main()
