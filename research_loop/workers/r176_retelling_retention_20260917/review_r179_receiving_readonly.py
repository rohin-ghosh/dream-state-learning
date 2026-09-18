"""Bounded reviewer-only observation; execute over the receiving SSH wrapper."""

import ast
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1')
LIMIT = 192 * 1024 ** 2
READ_BYTES = 0
READ_FILES = 0
SOURCE_BYTES = {}


def guard(event, arguments):
    if event in {'os.mkdir', 'os.remove', 'os.rename', 'os.rmdir', 'os.chmod',
                 'os.chown', 'os.truncate', 'os.kill', 'os.killpg', 'subprocess.Popen',
                 'os.system', 'socket.connect', 'socket.bind'}:
        raise RuntimeError('review_readonly_guard')
    if event == 'open' and len(arguments) >= 3:
        mode, flags = arguments[1:3]
        if isinstance(mode, str) and any(marker in mode for marker in 'wax+'):
            raise RuntimeError('review_write_forbidden')
        if isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise RuntimeError('review_write_forbidden')


def read(path, cap=32 * 1024 ** 2):
    global READ_BYTES, READ_FILES
    path = Path(path)
    assert path.is_file() and not path.is_symlink() and path == path.resolve(), 'exact_regular_path'
    before = path.stat()
    assert before.st_size <= cap and READ_BYTES + before.st_size <= LIMIT, 'review_read_bound'
    READ_BYTES += before.st_size
    READ_FILES += 1
    with path.open('rb') as stream:
        raw = stream.read(before.st_size + 1)
        after = os.fstat(stream.fileno())
    current = path.stat()
    assert len(raw) == before.st_size and all(
        getattr(before, field) == getattr(after, field) == getattr(current, field)
        for field in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    ), 'stable_review_read'
    return raw


def checksum(raw):
    return hashlib.sha256(raw).hexdigest()


def document(path):
    raw = read(path)
    return json.loads(raw), {'path': str(path), 'sha256': checksum(raw)}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def check_reference(reference):
    raw = read(reference['path'])
    assert checksum(raw) == reference['sha256'], 'reference_bytes'
    return json.loads(raw)


def main():
    sys.addaudithook(guard)
    public, public_ref = document(ROOT / 'runner_candidate1/PUBLIC_METADATA.json')
    request, request_ref = document(ROOT / 'runner_candidate1/REQUEST.json')
    source = check_reference(public['source'])
    cpu = check_reference(public['cpu_gate'])
    narrow_cpu = check_reference(public['runner_cpu_gate'])
    checks = {}
    sizes = {}
    for name, expected in source['source_pins'].items():
        path = ROOT / 'receiving_source1/source' / name
        raw = read(path)
        assert checksum(raw) == expected, 'receiving_source_pin'
        sizes[name] = len(raw)
        SOURCE_BYTES[name] = raw
    for name, expected in request['source_pins'].items():
        raw = read(ROOT / 'runner_candidate1/source' / name)
        assert checksum(raw) == expected, 'receiving_runner_pin'
    checks['receiving_source_closure_exact'] = True
    checks['receiving_runner_closure_exact'] = True
    checks['source_cpu_closure_equality'] = cpu['source_freeze'] == source['source_pins']
    checks['narrow_cpu_source_equality'] = narrow_cpu['source_pins'] == request['source_pins']
    configs = [check_reference(reference) for reference in public['executions']]
    checks['fixed_tranche_exact'] = len(configs) == 2 and all(
        config['life_id'] == 'C2' and config['sleep'] == 33 for config in configs)
    checks['condition_pair_exact'] = {config['condition'] for config in configs} == {'LORA_ON', 'LORA_OFF'}
    checks['physical_pair_exact'] = {config['physical'] for config in configs} == {0, 1}
    checks['config_receiving_joins_exact'] = all(all(
        config[field] == public[field] for field in ('source', 'cpu_gate', 'runner_cpu_gate')
    ) for config in configs)
    checks['runtime_joins_exact'] = all(all(
        config[field] == source['runtime'][field] == request['runtime'][field]
        for field in ('python', 'python_sha256', 'model_dir', 'service_path', 'service_sha256', 'lease')
    ) for config in configs)
    checks['runtime_allowances_exact'] = all(
        config['allowances'] == request['execution_read_allowances'][config['condition']]
        for config in configs)
    checks['same_capture_pair'] = configs[0]['capture'] == configs[1]['capture']
    checks['config_permissions_private'] = all(
        Path(reference['path']).stat().st_mode & 0o077 == 0 for reference in public['executions'])
    authorities = []
    for config in configs:
        for phase in ('preflight', 'native'):
            authorities.extend(config['allowances'][phase].values())
        authorities.append(config['allowances']['model_load'])
    checks['authority_document_hashes_exact'] = all(
        checksum(canonical(entry['document'])) == entry['reference']['sha256'] for entry in authorities)
    interpreter_path = Path(configs[0]['python']).resolve()
    interpreter = read(interpreter_path)
    checks['interpreter_pin_exact'] = checksum(interpreter) == configs[0]['python_sha256']
    service_raw = read(configs[0]['service_path'])
    checks['service_pin_exact'] = checksum(service_raw) == configs[0]['service_sha256']
    lease = check_reference(configs[0]['lease'])
    checks['lease_margin_exact'] = lease['hard_deadline_unix'] == lease['lease_end_unix'] - 21600
    release = check_reference(public['old_release'])
    checks['old_release_receipt_clear'] = (release['live_bound_owners'] == 0 and
        release['matching_old_root_live_processes'] == [] and
        release['old_reserved_without_terminal_count'] == 0 and release['missing_controller_launch_records'] == [])
    capture = check_reference(configs[0]['capture'])
    source_complete, source_complete_ref = document(ROOT / 'receiving_transfers/C2_000033/SOURCE_COMPLETE.json')
    checks['source_complete_pin_exact'] = source_complete_ref['sha256'] == capture['source_complete_sha256']
    checks['capture_inventory_exact'] = capture['files'] == source_complete['files']
    payload = Path(capture['payload_path'])
    private_metadata = {}
    adapter_total = 0
    for name, reference in capture['files'].items():
        raw = read(payload / name, 128 * 1024 ** 2)
        assert checksum(raw) == reference['sha256'] and len(raw) == reference['bytes'], 'receiving_payload_pin'
        if name.startswith('adapter/'):
            adapter_total += len(raw)
        else:
            private_metadata[name] = json.loads(raw)
    checks['actual_payload_bytes_match_captured_inventory'] = True
    birth = private_metadata['BIRTH.private.json']
    original = private_metadata['evidence/BIRTH_RECORD.private.json']
    checks['original_birth_empty_history_join'] = (
        set(birth) == {'system_prompt', 'birth_prompt'} and original['index'] == 0 and
        original['kind'] == 'COMMITTED' and original['document']['kind'] == 'BIRTH' and
        not original['document']['state']['state']['rows'] and all(
            original['document']['state']['state']['history'][field] == birth[field] for field in birth))
    checks['private_witness_not_parent_visible'] = private_metadata['TRAIN_WITNESSES.private.json']['parent_access'] is False
    rubric = check_reference(cpu['private_rubric_ref'])
    checks['rubric_private_zero_provider'] = rubric['parent_access'] is False and rubric['provider_calls'] == 0
    generator_tree = ast.parse(SOURCE_BYTES['gpu/orch_r167_fleet_eval.py'])
    generator_methods = next(node.value for node in generator_tree.body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'METHODS' for target in node.targets))
    checks['rubric_method_keys_exact'] = set(rubric['methods']) == {entry.arg for entry in generator_methods.keywords}
    checks['no_execution_reservations'] = not list((ROOT / 'ledger').glob('*.RESERVED.json'))
    checks['no_execution_attempts'] = not (ROOT / 'attempts').exists()
    checks['host_pin_exact'] = checksum(socket.gethostname().encode()) == '0e183169e60b06badac84e0eca6036a53b7ad90c433b8cd69b2a9aaf9159389b'
    result = {
        'schema': 'R179_INDEPENDENT_RECEIVING_READONLY_OBSERVATION_V1',
        'observed_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'public_receipt': public_ref, 'runner_request': request_ref,
        'source': public['source'], 'cpu_gate': public['cpu_gate'], 'runner_cpu_gate': public['runner_cpu_gate'],
        'runner_sha256': public['runner_sha256'], 'source_complete': source_complete_ref,
        'executions': public['executions'], 'source_pin_count': len(sizes),
        'source_bytes_total': sum(sizes.values()), 'interpreter_bytes': len(interpreter),
        'source_request_bytes': Path(public['source']['path']).stat().st_size,
        'cpu_gate_bytes': Path(public['cpu_gate']['path']).stat().st_size,
        'execution_config_bytes_unmapped': sorted(Path(entry['path']).stat().st_size for entry in public['executions']),
        'phase_metadata_caps_unmapped': sorted(config['allowances']['native']['metadata']['document']['bytes'] for config in configs),
        'adapter_total_bytes': adapter_total, 'checks': checks,
        'receiver_read_bytes': READ_BYTES, 'receiver_files_read': READ_FILES, 'reviewer_read_limit_bytes': LIMIT,
        'gpu_model_provider_calls': 0, 'receiving_writes': 0, 'signals': 0,
        'scanner_invocations': 0, 'private_content_exported': False,
    }
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status': 'REVIEW_OBSERVATION_ERROR', 'error_type': type(error).__name__,
            'read_bytes': READ_BYTES, 'read_files': READ_FILES, 'private_content_exported': False}))
        sys.exit(2)
