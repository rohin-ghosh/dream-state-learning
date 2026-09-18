"""Actual receiving validator diagnostic, never an execution authorization.

Only authorization inputs and ledger writes are in-memory fixtures. The frozen
validator, receiving source/configs, Reader caps, and filesystem reads are real.
"""

import hashlib
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path('/localhome/local-rohing/orch_r176_retelling_retention_20260917_generation1')
GO_PATH = Path('/__r179_in_memory_go_fixture_never_written__')
REVIEW_PATH = '/__r179_in_memory_review_fixture_never_written__'


def guard(event, arguments):
    if event in {'os.mkdir', 'os.remove', 'os.rename', 'os.rmdir', 'os.chmod', 'os.chown',
                 'os.truncate', 'os.kill', 'os.killpg', 'subprocess.Popen', 'os.system',
                 'socket.connect', 'socket.bind'}:
        raise RuntimeError('review_readonly_guard')
    if event == 'open' and len(arguments) >= 3:
        mode, flags = arguments[1:3]
        if isinstance(mode, str) and any(marker in mode for marker in 'wax+'):
            raise RuntimeError('review_write_forbidden')
        if isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise RuntimeError('review_write_forbidden')


class NoModelImports:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'torch', 'transformers', 'peft', 'tensorflow', 'jax'}:
            raise RuntimeError('review_model_import_forbidden')
        return None


def main():
    sys.addaudithook(guard)
    sys.meta_path.insert(0, NoModelImports())
    runner_source = ROOT / 'runner_candidate1/source'
    model_source = ROOT / 'receiving_source1/source'
    sys.path[:0] = [str(runner_source), str(model_source)]
    import r176_runner as runner
    import preparation_io as common

    public = json.loads((ROOT / 'runner_candidate1/PUBLIC_METADATA.json').read_bytes())
    config_path = Path(public['executions'][0]['path'])
    config = json.loads(config_path.read_bytes())
    config['execution'] = runner.reference(config_path)
    go = {field: public[field] for field in (
        'executions', 'source', 'runner_sha256', 'cpu_gate', 'runner_cpu_gate', 'old_release')}
    go.update(status='MAIN_R176_EXECUTION_GO', no_reset=True, call_cap=72, token_cap=36864,
        process_cap=24, physical_slots=[0, 1], absolute_end_unix=common.END, active_seconds_max=5400,
        gpu_slot_seconds_max=10800, provider_calls=0, baseline_new_calls=0,
        independent_review={'path': REVIEW_PATH, 'sha256': 'in-memory-diagnostic-only'})
    review = dict(go, status='APPROVE', independent=True, reviewer='R179_IN_MEMORY_FIXTURE_ONLY')
    original_bound = runner.bound
    original_read_bytes = Path.read_bytes
    original_charge = common.Reader.charge
    writes = []
    attempts = []

    def memory_bound(reference):
        if reference['path'] == REVIEW_PATH:
            return review
        return original_bound(reference)

    def memory_read_bytes(path):
        if path == GO_PATH:
            return common.canonical(go)
        return original_read_bytes(path)

    def memory_write(path, value):
        writes.append({'kind': value.get('kind'), 'bytes': value.get('bytes', 0)})
        return {'path': str(path), 'sha256': common.digest(value), 'bytes': len(common.canonical(value))}

    def observed_charge(reader, path, kind, amount):
        category = 'interpreter' if Path(path) == Path(config['python']).resolve() else 'other_bound_metadata'
        attempts.append({'category': category, 'kind': kind, 'bytes': amount})
        return original_charge(reader, path, kind, amount)

    runner.bound = memory_bound
    Path.read_bytes = memory_read_bytes
    common.write = memory_write
    common.Reader.charge = observed_charge
    reader = runner.phase_reader(config, 'preflight', ROOT / '__r179_no_directory_created__')
    runner.charge_open_reads(reader, model_source, config)
    try:
        runner.validate(config, GO_PATH)
        status, reason = 'VALIDATOR_RETURNED', None
    except Exception as error:
        status = 'VALIDATOR_REFUSED'
        reason = str(error) if str(error) in {'delegated_read_cap', 'review_readonly_guard',
            'review_model_import_forbidden', 'review_write_forbidden'} else type(error).__name__
    result = {
        'schema': 'R179_ACTUAL_RECEIVING_VALIDATOR_READONLY_DIAGNOSTIC_V1',
        'observed_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'status': status, 'reason': reason, 'last_attempted_charge': attempts[-1] if attempts else None,
        'metadata_cap_bytes': reader.authority['metadata']['document']['bytes'],
        'metadata_attempted_bytes': reader.charged['metadata'],
        'metadata_successfully_charged_bytes': sum(entry['bytes'] for entry in writes if entry['kind'] == 'metadata'),
        'adapter_attempted_bytes': reader.charged['adapter'],
        'runner_sha256': public['runner_sha256'], 'source': public['source'],
        'both_authorization_inputs_synthetic_in_memory_only': True,
        'ledger_writes_in_memory_only': True, 'receiving_writes': 0,
        'scanner_invocations': 0, 'gpu_model_provider_calls': 0, 'signals': 0,
        'private_content_exported': False, 'execution_authorized': False,
    }
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status': 'DIAGNOSTIC_ERROR', 'error_type': type(error).__name__,
            'execution_authorized': False, 'private_content_exported': False}))
        sys.exit(2)
