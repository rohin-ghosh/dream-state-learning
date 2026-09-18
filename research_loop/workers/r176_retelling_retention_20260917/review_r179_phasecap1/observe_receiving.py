"""Read-only metadata and source binding audit of the append-only cap repair."""

import hashlib
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1')
CANDIDATE = ROOT / 'runner_candidate3_metadata_repair2'
EXPECTED_PUBLIC = 'ed43eeca656d826c600bdc112ae1da7cbb8e28630bb79881edef0a8b190ee14c'
PROOFS = {
    '6d4f77f44546739b06691f5cd869d25872be1a1086fd2d1cf7c8eb6350c756d8_native':
        '45dee816a7f349d5f545fe8c3468030776ddf7c878d96bdf9ef985c90a39463e',
    '6d4f77f44546739b06691f5cd869d25872be1a1086fd2d1cf7c8eb6350c756d8_preflight':
        'c0e396635271bedf5307c4f37e022a8fa5a8974f7313e4332174e3231be00f64',
    '83d09ddf7ff9adababd87d0d4ef12a54617aa413522fd5948aff4f5b5d590bf5_native':
        '3f827c1b5b08e6c1de6647f38952782b3ebcf6b7387c46eaa5536b2191b19189',
    '83d09ddf7ff9adababd87d0d4ef12a54617aa413522fd5948aff4f5b5d590bf5_preflight':
        'dabc08b587450df998a235b9480cbf77021101532245958a98a9403895c34ac4',
}
READ_LIMIT = 64 * 1024 ** 2
READ_BYTES = 0
READ_COUNT = 0


def guard(event, arguments):
    if event in {'os.mkdir', 'os.remove', 'os.rename', 'os.rmdir', 'os.chmod', 'os.chown',
                 'os.truncate', 'os.kill', 'os.killpg', 'subprocess.Popen', 'os.system',
                 'os.exec', 'os.posix_spawn', 'socket.connect', 'socket.bind'}:
        raise RuntimeError('review_readonly_guard')
    if event == 'open' and len(arguments) >= 3:
        mode, flags = arguments[1:3]
        if isinstance(mode, str) and any(marker in mode for marker in 'wax+'):
            raise RuntimeError('review_write_forbidden')
        if isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise RuntimeError('review_write_forbidden')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def read(path, expected=None):
    global READ_BYTES, READ_COUNT
    path = Path(path)
    assert path.is_file() and path == path.resolve(), 'exact_regular_file'
    assert '/payload/adapter/' not in str(path), 'no_new_adapter_read'
    before = path.stat()
    assert before.st_size < 32 * 1024 ** 2 and READ_BYTES + before.st_size <= READ_LIMIT, 'review_read_cap'
    READ_BYTES += before.st_size
    READ_COUNT += 1
    with path.open('rb') as stream:
        raw = stream.read(before.st_size + 1)
        after = os.fstat(stream.fileno())
    current = path.stat()
    assert len(raw) == before.st_size and all(
        getattr(before, field) == getattr(after, field) == getattr(current, field)
        for field in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')), 'stable_read'
    assert expected is None or sha(raw) == expected, 'exact_expected_hash'
    return raw


def bound(reference):
    return json.loads(read(reference['path'], reference['sha256']))


def main():
    sys.addaudithook(guard)
    public_raw = read(CANDIDATE / 'PUBLIC_METADATA.json', EXPECTED_PUBLIC)
    public = json.loads(public_raw)
    request_raw = read(CANDIDATE / 'REQUEST.json')
    request = json.loads(request_raw)
    original = bound(public['superseded_public_receipt'])
    assert original['executions'] == public['superseded_execution_refs'], 'original_opaque_references_preserved'
    old_configs = [bound(reference) for reference in original['executions']]
    new_configs = [bound(reference) for reference in public['executions']]
    checks = {}
    restored = []
    for config in new_configs:
        previous = next(value for value in old_configs if value['condition'] == config['condition'])
        value = json.loads(canonical(config))
        for phase, expected in (('preflight', 32 * 1024 ** 2), ('native', 48 * 1024 ** 2)):
            allowance = value['allowances'][phase]['metadata']
            assert allowance == request['new_metadata_allowances'][config['condition']][phase], 'new_authority_join'
            assert sha(canonical(allowance['document'])) == allowance['reference']['sha256'], 'new_authority_pin'
            assert allowance['document']['bytes'] == expected, 'fixed_repaired_cap'
            value['allowances'][phase]['metadata'] = previous['allowances'][phase]['metadata']
        restored.append(value == previous)
    checks['only_two_metadata_authority_fields_changed'] = all(restored)
    checks['original_fixed_pair_preserved'] = len(new_configs) == 2 and all(
        config['life_id'] == 'C2' and config['sleep'] == 33 for config in new_configs)
    checks['pair_conditions_unchanged'] = {config['condition'] for config in new_configs} == {'LORA_ON', 'LORA_OFF'}
    checks['new_config_permissions_private'] = all(
        Path(reference['path']).stat().st_mode & 0o077 == 0 for reference in public['executions'])
    checks['public_runtime_joins_unchanged'] = all(public[field] == original[field] for field in (
        'source', 'cpu_gate', 'runner_cpu_gate', 'runner_sha256', 'runner_path', 'old_release'))
    source = bound(public['source'])
    cpu = bound(public['cpu_gate'])
    narrow_cpu = bound(public['runner_cpu_gate'])
    assert cpu['source_freeze'] == source['source_pins'], 'source_CPU_pin_set'
    for name, expected in source['source_pins'].items():
        read(ROOT / 'receiving_source1/source' / name, expected)
    for name, expected in narrow_cpu['source_pins'].items():
        read(ROOT / 'runner_candidate1/source' / name, expected)
    checks['receiving_source_and_runner_closures_unchanged'] = True
    interpreter = read(Path(source['runtime']['python']).resolve(), source['runtime']['python_sha256'])
    read(source['runtime']['service_path'], source['runtime']['service_sha256'])
    bound(source['runtime']['lease'])
    release = bound(public['old_release'])
    checks['runtime_interpreter_service_lease_bytes_match'] = True
    checks['old_release_receipt_clear'] = release['live_bound_owners'] == 0 and not release['matching_old_root_live_processes']
    proof_results = []
    for name, expected in PROOFS.items():
        proof_root = ROOT / 'metadata_repair_actual_proof1' / name
        receipt_path = proof_root / 'PUBLIC_METADATA.json'
        receipt = json.loads(read(receipt_path, expected))
        proof_request_raw = read(proof_root / 'REQUEST.private.json')
        proof_request = json.loads(proof_request_raw)
        assert receipt['status'] == 'COMPLETE_ACTUAL_VALIDATOR_PASS', 'complete_validator_proof'
        assert receipt['execution'] in public['executions'] and proof_request['execution'] == receipt['execution'], 'proof_exact_config'
        assert receipt['candidate_public'] == {'path': str(CANDIDATE / 'PUBLIC_METADATA.json'), 'sha256': EXPECTED_PUBLIC}, 'proof_exact_candidate'
        assert proof_request['proof_script_sha256'] == '2a0285b765a5162379b2990ca037f8425c220175f9e92f72697f1ad9b29bf4ad', 'proof_script_pin'
        assert all(receipt[field] == public[field] for field in ('source', 'cpu_gate', 'runner_cpu_gate', 'runner_sha256')), 'proof_runtime_joins'
        rows_path = Path(receipt['read_ledger_path'])
        assert rows_path.is_relative_to(proof_root), 'proof_local_ledger'
        paths = sorted(rows_path.glob('*.json'))
        assert [path.name for path in paths] == [f'{sequence:06d}.json' for sequence in range(receipt['persisted_read_records'])], 'complete_read_sequence'
        totals = {'metadata': 0, 'adapter': 0, 'discovery': 0}
        for path in paths:
            row = json.loads(read(path))
            assert row['status'] == 'CHARGED_BEFORE_READ_NO_REFUND', 'actual_precharged_read'
            assert row['authority'] == proof_request['proof_allowances'][row['kind']]['reference'], 'read_authority_join'
            totals[row['kind']] += row['bytes']
        assert totals == receipt['phase_charge_counters_bytes'], 'persisted_read_totals'
        for kind in ('metadata', 'adapter'):
            allowance = proof_request['proof_allowances'][kind]
            assert sha(canonical(allowance['document'])) == allowance['reference']['sha256'], 'supplemental_authority_pin'
            assert totals[kind] <= allowance['document']['bytes'] == receipt['proof_cap_bytes'][kind], 'proof_finite_cap'
            assert allowance['reference'] == receipt['separate_supplemental_proof_authorities'][kind], 'public_proof_authority'
        assert receipt['proof_cap_bytes']['metadata'] == receipt['phase_cap_bytes']['metadata'], 'unrelaxed_metadata_cap'
        assert receipt['proof_cap_bytes']['adapter'] <= receipt['phase_cap_bytes']['adapter'], 'unrelaxed_adapter_cap'
        assert receipt['model_calls'] == receipt['provider_calls'] == receipt['scanner_invocations'] == receipt['execution_attempts_consumed'] == 0, 'no_science_or_admission'
        assert not receipt['production_allowances_consumed'] and not receipt['authorization_fixtures_written_to_disk'], 'execution_state_untouched'
        proof_results.append({'phase': receipt['phase'], 'receipt': {'path': str(receipt_path), 'sha256': expected},
            'request': {'path': str(proof_root / 'REQUEST.private.json'), 'sha256': sha(proof_request_raw)},
            'rows': len(paths), 'charged_bytes': totals, 'phase_cap_bytes': receipt['phase_cap_bytes'],
            'metadata_headroom_bytes': receipt['metadata_headroom_bytes']})
    checks['all_four_persisted_actual_phase_proofs_exact'] = True
    checks['no_production_attempts_or_reservations'] = not (ROOT / 'attempts').exists() and not list((ROOT / 'ledger').glob('*.RESERVED.json'))
    assert all(checks.values()), 'review_equality_check_failed'
    print(json.dumps({'schema': 'R179_PHASE_CAP1_INDEPENDENT_RECEIVING_OBSERVATION_V1',
        'observed_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'checks': checks,
        'candidate_public': {'path': str(CANDIDATE / 'PUBLIC_METADATA.json'), 'sha256': EXPECTED_PUBLIC},
        'candidate_request': {'path': str(CANDIDATE / 'REQUEST.json'), 'sha256': sha(request_raw)},
        'executions': public['executions'], 'runner_sha256': public['runner_sha256'],
        'source': public['source'], 'cpu_gate': public['cpu_gate'], 'runner_cpu_gate': public['runner_cpu_gate'],
        'config_bytes_unmapped': sorted(Path(reference['path']).stat().st_size for reference in public['executions']),
        'proofs': proof_results, 'source_file_count': len(source['source_pins']), 'interpreter_bytes': len(interpreter),
        'read_bytes': READ_BYTES, 'read_count': READ_COUNT, 'read_limit_bytes': READ_LIMIT,
        'new_adapter_reads': 0, 'receiving_writes': 0, 'signals': 0, 'gpu_model_provider_calls': 0,
        'scanner_calls': 0, 'private_content_exported': False, 'execution_authorized': False}, sort_keys=True, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status': 'REVIEW_OBSERVATION_ERROR', 'error_type': type(error).__name__,
            'read_bytes': READ_BYTES, 'read_count': READ_COUNT, 'private_content_exported': False}))
        sys.exit(2)
