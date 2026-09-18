"""Verify only public C4 load/state identity; export no child or sealed text."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


BASE = Path('/localhome/local-rohing')
ORIGINAL = BASE / 'orch_r179_context_C4_20260917_attempt3'
RECOVERY = BASE / 'orch_r179_C4_readmission_20260917_attempt1'
ROOT = BASE / 'orch_r153_community_C4_20260916_attempt1/life'
BOUNDARY_SHA = '6f9cc2fdd4fbb032e07886c059f2075bdf2209da20fcd391702d0995e0df00b3'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(path):
    record = read(path)
    document = record['document']
    expected = read(ORIGINAL / 'ACTUAL_4182_CPU.json')
    require(record['kind'] == 'LOADED' and document['resume'] is True
            and record['previous_sha256'] == BOUNDARY_SHA, 'first_load_directly_after_exact_saved_boundary')
    canonical = json.dumps({key: value for key, value in record.items() if key != 'sha256'},
                           sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    require(hashlib.sha256(canonical).hexdigest() == record['sha256'], 'actual_loaded_record_hash')
    require(document['adapter_sha256'] == expected['adapter_state_sha256']
            and document['optimizer_steps'] == expected['optimizer_steps'] == 3618, 'same_C4_adapter_and_optimizer_step')
    config = read(RECOVERY / 'GUARD.json')
    plan = read(Path(config['plan_path']))
    process = Path('/proc') / str(document['pid'])
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[0] not in ('Z', 'X') and process.stat().st_uid == 2524, 'loaded_C4_native_live')
    require(os.readlink(process / 'cwd') == plan['source_root'] == str(ORIGINAL / 'source'), 'actual_unchanged_C4_source')
    require((process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0') == [
        str(BASE / 'v2/venv/bin/python'), '-B', '-m', 'gpu.orch_r125_continual_guard',
        'native', '--config', str(RECOVERY / 'GUARD.json')], 'exact_current_readmission_guard')
    launch = read(RECOVERY / 'attempt/LAUNCH.json')
    timer = Path('/proc') / str(int(fields[1]))
    timer_fields = (timer / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(int(fields[1]) == launch['pid'] and timer_fields[19] == launch['parent_start_ticks']
            and launch['guard_sha256'] == sha(RECOVERY / 'GUARD.json'), 'actual_timeout_launch_binding')
    require((RECOVERY / 'attempt/DISPATCH_ONCE').is_dir(), 'actual_required_dispatch_marker')
    admission = read(RECOVERY / 'attempt/ADMISSION.json')
    containment = read(RECOVERY / 'attempt/CONTAINMENT_VERIFIED.json')
    require(admission['clear'] is True and admission['scanner_euid'] == 0 and not admission['blocking_reasons']
            and admission['gpu']['uuid'] == plan['gpu_uuid'] and plan['physical'] == 4, 'actual_strict_C4_admission')
    require(containment['denied_foreign_minors'] == [0, 1, 2, 3, 5, 6, 7], 'actual_foreign_devices_denied')
    return dict(schema='R179_C4_EXACT_READMISSION_LOADED_V1', status='LOADED_EXACT_SAVED_STATE',
        saved_sleep=36, optimizer_steps=3618, adapter_sha256=document['adapter_sha256'],
        full_state_sha256=expected['full_state_sha256'], full_history_sha256=expected['full_history_sha256'],
        actor_pid=document['pid'], actor_start_ticks=fields[19], loaded_unix=document['loaded_unix'],
        source_root=plan['source_root'], guard_path=str(RECOVERY / 'GUARD.json'),
        guard_sha256=sha(RECOVERY / 'GUARD.json'), loaded_record_sha256=record['sha256'],
        loaded_record_path=str(path), admission_sha256=sha(RECOVERY / 'attempt/ADMISSION.json'),
        containment_sha256=sha(RECOVERY / 'attempt/CONTAINMENT_VERIFIED.json'),
        unchanged_wall=plan['hard_end_unix'], child_text_exported=False, sealed_readout_files_opened=0,
        new_completed_sleep_claimed=False, observed_unix=time.time())


def inspect(seconds):
    deadline = time.monotonic() + seconds
    path = ROOT / 'stream/records/00000000000000004183.json'
    while time.monotonic() < deadline:
        if path.exists():
            receipt = verify(path)
            destination = RECOVERY / 'LOADED_RECEIPT.json'
            if not destination.exists():
                with destination.open('x') as handle:
                    json.dump(receipt, handle, sort_keys=True, indent=2)
                    handle.write('\n')
                    handle.flush()
                    os.fsync(handle.fileno())
                    os.fchmod(handle.fileno(), 0o444)
            else:
                require(read(destination)['loaded_record_sha256'] == receipt['loaded_record_sha256'],
                        'same_preserved_load_receipt_no_rewrite')
            return dict(path=str(destination), sha256=sha(destination), receipt=read(destination))
        if (RECOVERY / 'FAILED.json').exists() or (RECOVERY / 'attempt/NATIVE_EXIT.json').exists():
            return dict(status='READMISSION_FAILED_BEFORE_VERIFIED_LOAD', output=str(RECOVERY),
                        observed_unix=time.time())
        time.sleep(0.5)
    return dict(status='LOAD_NOT_YET_OBSERVED', output=str(RECOVERY), observed_unix=time.time())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote', action='store_true')
    parser.add_argument('--seconds', type=int, default=120)
    arguments = parser.parse_args()
    if arguments.remote:
        print(json.dumps(inspect(arguments.seconds), sort_keys=True))
        return
    command = '/localhome/local-rohing/v2/venv/bin/python -B -c ' + shlex.quote(Path(__file__).read_text()) + \
        ' --remote --seconds ' + str(arguments.seconds)
    result = subprocess.run(['bash', 'gpu/ovx3_ssh.sh', command], capture_output=True, text=True,
                            timeout=arguments.seconds + 20)
    if result.returncode:
        raise RuntimeError('C4_load_verification_failed: ' + result.stderr[-2000:])
    document = json.loads(result.stdout)
    path = Path(__file__).parent / f'C4_READMISSION_LOAD_OBSERVATION_{time.time_ns()}.json'
    with path.open('x') as handle:
        json.dump(document, handle, sort_keys=True, indent=2)
        handle.write('\n')
    print(path)
    print(json.dumps(document, sort_keys=True))


if __name__ == '__main__':
    main()
