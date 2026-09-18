"""Export verified C1 recovery metadata without responses or readout content."""

import hashlib
import json
import os
from pathlib import Path
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def main():
    base = Path('/localhome/local-rohing')
    original = base / 'orch_r179_context_C1_20260917_attempt2'
    recovery = base / 'orch_r179_C1_readmission_20260917_attempt2'
    root = base / 'orch_r153_community_C1_20260916_attempt1/life/stream/records'
    loaded_path = root / '00000000000000004756.json'
    record = read(loaded_path)
    document = record['document']
    expected = read(original / 'ACTUAL_4755_CPU.json')
    assert record['kind'] == 'LOADED' and document['resume'] is True
    assert record['previous_sha256'] == 'dfd724e34b5660ca1507a619c10af091dbb8d138ce03aacd4d6fa4b5013b0438'
    assert document['adapter_sha256'] == expected['adapter_state_sha256']
    assert document['optimizer_steps'] == expected['optimizer_steps'] == 4095
    canonical = json.dumps({key: value for key, value in record.items() if key != 'sha256'},
                           sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(canonical).hexdigest() == record['sha256']
    config = read(recovery / 'GUARD.json')
    plan = read(config['plan_path'])
    process = Path('/proc') / str(document['pid'])
    process_fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    assert process_fields[0] not in ('Z', 'X')
    assert os.readlink(process / 'cwd') == plan['source_root'] == str(original / 'source')
    assert (process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0') == [
        str(base / 'v2/venv/bin/python'), '-B', '-m', 'gpu.orch_r125_continual_guard',
        'native', '--config', str(recovery / 'GUARD.json')]
    admission = read(recovery / 'attempt/ADMISSION.json')
    containment = read(recovery / 'attempt/CONTAINMENT_VERIFIED.json')
    assert admission['clear'] and admission['scanner_euid'] == 0 and not admission['blocking_reasons']
    assert admission['gpu']['uuid'] == plan['gpu_uuid']
    denied = containment.get('denied_foreign_minors', containment.get('denied_devices'))
    assert isinstance(denied, list) and len(denied) == 7
    receipt = dict(schema='R179_C1_EXACT_READMISSION_LOADED_V1', status='LOADED_EXACT_SAVED_STATE',
        saved_sleep=39, optimizer_steps=4095, adapter_sha256=document['adapter_sha256'],
        full_state_sha256=expected['full_state_sha256'], full_history_sha256=expected['full_history_sha256'],
        actor_pid=document['pid'], actor_start_ticks=process_fields[19], loaded_unix=document['loaded_unix'],
        source_root=plan['source_root'], guard_path=str(recovery / 'GUARD.json'),
        guard_sha256=sha(recovery / 'GUARD.json'), loaded_record_sha256=record['sha256'],
        admission_sha256=sha(recovery / 'attempt/ADMISSION.json'),
        containment_sha256=sha(recovery / 'attempt/CONTAINMENT_VERIFIED.json'),
        unchanged_wall=plan['hard_end_unix'], child_text_exported=False, sealed_readout_files_opened=0,
        new_completed_sleep_claimed=False, observed_unix=time.time())
    destination = recovery / 'LOADED_RECEIPT.json'
    with destination.open('x') as handle:
        json.dump(receipt, handle, sort_keys=True, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    destination.chmod(0o444)
    print(json.dumps(dict(path=str(destination), sha256=sha(destination), receipt=receipt), sort_keys=True))


if __name__ == '__main__':
    main()
