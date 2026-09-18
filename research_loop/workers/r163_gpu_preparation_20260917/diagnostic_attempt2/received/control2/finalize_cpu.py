"""Metadata-only final pins; no model/anchor rows or service actions."""

import hashlib
import json
from pathlib import Path
import time


ROOT = Path('/localhome/local-rohing/orch_r163_numerical_diagnostic_20260917_attempt2')
OLD = Path('/localhome/local-rohing/orch_r163_numerical_preparation_20260917_attempt1')
CONTROL = ROOT / 'control2'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prior = json.loads((OLD / 'CPU_PREPARATION.json').read_bytes())
    assets = {}
    metadata_bytes = 0
    for name, expected in prior['model_assets'].items():
        if 'sha256' not in expected:
            continue
        path = Path(expected['path'])
        assert path.stat().st_size <= 16*1024**2
        actual = sha(path)
        assert actual == expected['sha256']
        metadata_bytes += path.stat().st_size
        assets[name] = dict(path=str(path), sha256=actual, bytes=path.stat().st_size)
    anchor = Path(prior['anchors']['manifest_path'])
    assert sha(anchor) == prior['anchors']['manifest_sha256']
    prepared = json.loads((CONTROL / 'PREPARED_EXECUTION.json').read_bytes())
    manifest = json.loads((CONTROL / 'SOURCE_PINS.json').read_bytes())
    assert len(manifest['files']) == 2158
    for name, expected in manifest['files'].items():
        path = Path(name)
        assert sha(path) == expected and path.stat().st_mode & 0o222 == 0
    for reference in prepared['required_GO_binding'].values():
        if isinstance(reference, dict) and 'sha256' in reference:
            assert sha(Path(reference['path'])) == reference['sha256']
    assert not (ROOT / 'validation_run1').exists()
    assert not (ROOT / 'attempt1').exists()
    assert not (CONTROL / 'MAIN_GO.json').exists()
    tests = (CONTROL / 'RECEIVING_CPU_TESTS_with_support.log').read_text()
    assert '24 passed' in tests and 'failed' not in tests
    result = dict(schema='R163_DIAGNOSTIC_ATTEMPT2_CPU_READY_V1',
        status='CPU_PREPARED_NO_GPU_GO', observed_unix=time.time(),
        required_GO_binding=prepared['required_GO_binding'],
        prepared_execution_sha256=sha(CONTROL / 'PREPARED_EXECUTION.json'),
        receiving_tests=dict(path=str(CONTROL / 'RECEIVING_CPU_TESTS_with_support.log'),
            sha256=sha(CONTROL / 'RECEIVING_CPU_TESTS_with_support.log'), passed=24,
            subtests_passed=12, cuda_visible_devices='', cache_disabled=True),
        model_metadata=assets, metadata_bytes_read=metadata_bytes,
        anchor_manifest=dict(path=str(anchor), sha256=sha(anchor)),
        weights_read=False, checkpoints_read=False, anchor_rows_read=False,
        held_data_read=False, source_files_reverified=2158,
        no_service_created=True, no_gpu_dispatched=True,
        earliest_dispatch_unix=1789630200, hard_end_unix=1789632000,
        maximum_runtime_seconds=1800,
        lease_end_unix=1789689600, existing_lease_hardwall_unix=1789668000,
        hardwall_margin_seconds=1789668000-1789632000,
        provider_booking_verified=False,
        source_copy_independent=True, old_attempts_untouched=True)
    with (CONTROL / 'FINAL_CPU_RECEIPT.json').open('x') as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write('\n')
    for path in CONTROL.iterdir():
        if path.is_file():
            path.chmod(0o444)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
