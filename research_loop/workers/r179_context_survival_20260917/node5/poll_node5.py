"""Collect only public rollout metadata, never child text or sealed readouts."""

import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


ATTEMPTS = {'C2': 4, 'C5': 3, 'pilot': 5, 'run1': 4, 'C1': 2, 'C3': 3, 'C4': 3, 'repo_reader': 3}
READMISSIONS = {'C1': dict(root='/localhome/local-rohing/orch_r179_C1_readmission_20260917_attempt2',
    receipt_sha256='4a01b78f93ea5ff3bfc80b7ffa1a0e8f4dcde6b973b65900eaeb88515db2fe5c', attribution='MAIN_READMISSION'),
    'C4': dict(root='/localhome/local-rohing/orch_r179_C4_readmission_20260917_attempt1',
    receipt_sha256='63768896c6f946b71589e9dd06671e323c6c3528cb735046c165b9476ff4d077', attribution='NODE5_C4_READMISSION')}


def read(path):
    return json.loads(path.read_bytes())


def reference(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def loaded_metadata(document, proof, own_launch):
    event = {key: document.get(key) for key in ('pid', 'resume', 'optimizer_steps', 'adapter_sha256', 'loaded_unix')}
    event['matches_saved_adapter_and_step'] = (event['adapter_sha256'] == proof['adapter_state_sha256']
        and event['optimizer_steps'] == proof['optimizer_steps'] and event['resume'] is True)
    event['own_attempt_launch_recorded'] = own_launch
    event['attribution'] = ('SUCCESSOR_LOADED' if event['matches_saved_adapter_and_step'] else 'LOAD_BINDING_MISMATCH') \
        if own_launch else 'EXTERNAL_LOAD_OBSERVED_NOT_THIS_ATTEMPT'
    return event


def pre_load_status(row):
    if 'failure' in row or 'watcher_repair' in row:
        return row['status']
    if 'launch' in row:
        return 'SUCCESSOR_LAUNCH_RECORDED_LOAD_UNOBSERVED'
    if 'owner_retired' in row:
        return 'OWNER_RETIRED_ADMISSION_CLEAR' if row.get('admission', {}).get('clear') is True \
            else 'OWNER_RETIRED_ADMISSION_PENDING'
    if 'actual_boundary_ready' in row:
        return 'SAVED_BOUNDARY_READY'
    if 'operator_started' in row:
        return 'WAITING_SAVED_BOUNDARY'
    return 'ACTUAL_SOURCE_CPU_READY_NOT_STARTED'


def apply_readmission(row, receipt, current):
    historical = dict(output=row['output'], status=row['status'])
    for name in ('failure', 'operator_pid', 'operator_live', 'operator_started', 'admission', 'containment', 'launch'):
        if name in row:
            historical[name] = row.pop(name)
    row['historical_attempt'] = historical
    attribution = current.get('attribution', 'MAIN_READMISSION')
    row.update(output=current['output'], status='CURRENT_READMISSION_LOADED' if current['actor_live']
               else 'READMISSION_LOAD_OBSERVED_PROCESS_NOT_LIVE', actor_live=current['actor_live'],
               current_execution_attribution=attribution, readmission=current)
    row['loaded'] = dict(pid=receipt['actor_pid'], start_ticks=receipt['actor_start_ticks'],
        optimizer_steps=receipt['optimizer_steps'], adapter_sha256=receipt['adapter_sha256'],
        loaded_unix=receipt['loaded_unix'], attribution=attribution,
        matches_saved_adapter_and_step=True, loaded_record_sha256=receipt['loaded_record_sha256'])
    row['child_status'] = row['status']


def inspect_readmission(row, registration):
    root = Path(registration['root'])
    path = root / 'LOADED_RECEIPT.json'
    receipt_ref = reference(path)
    if receipt_ref['sha256'] != registration['receipt_sha256']:
        raise ValueError('exact_Main_readmission_receipt_required')
    receipt = read(path)
    if reference(root / 'GUARD.json')['sha256'] != receipt['guard_sha256']:
        raise ValueError('Main_readmission_guard_pin')
    if reference(root / 'attempt/ADMISSION.json')['sha256'] != receipt['admission_sha256'] or \
       reference(root / 'attempt/CONTAINMENT_VERIFIED.json')['sha256'] != receipt['containment_sha256']:
        raise ValueError('Main_readmission_admission_containment_pins')
    if row.get('external_loaded', {}).get('record_sha256') != receipt['loaded_record_sha256'] or \
       row.get('external_loaded', {}).get('matches_saved_adapter_and_step') is not True:
        raise ValueError('Main_readmission_exact_journal_saved_state_binding')
    process = Path('/proc') / str(receipt['actor_pid'])
    live = False
    try:
        fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
        command = (process / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
        live = fields[0] not in ('Z', 'X') and fields[19] == receipt['actor_start_ticks'] and \
            process.stat().st_uid == 2524 and os.readlink(process / 'cwd') == receipt['source_root'] and \
            command == ['/localhome/local-rohing/v2/venv/bin/python', '-B', '-m',
                        'gpu.orch_r125_continual_guard', 'native', '--config', receipt['guard_path']]
    except (FileNotFoundError, ProcessLookupError):
        pass
    current = dict(output=str(root), loaded_receipt=receipt_ref, actor_live=live, attribution=registration['attribution'],
                   source_root=receipt['source_root'], guard_path=receipt['guard_path'])
    if (root / 'attempt/NATIVE_EXIT.json').exists():
        current['native_exit'] = read(root / 'attempt/NATIVE_EXIT.json')
    apply_readmission(row, receipt, current)


def inspect():
    output = []
    for label, attempt in ATTEMPTS.items():
        root = Path('/localhome/local-rohing') / f'orch_r179_context_{label}_20260917_attempt{attempt}'
        row = dict(label=label, output=str(root), observed_unix=time.time(), status='WAITING_SAVED_BOUNDARY')
        sys.path.insert(0, str(root))
        from stage_node5 import tail_metadata
        request = read(root / 'INPUT.json')
        journal = Path(request['storage_root']) / 'stream/records'
        head_paths = sorted(path for path in journal.glob('*.json') if path.stem.isdigit())
        if head_paths:
            row['head'] = tail_metadata(head_paths[-1])
        if (root / 'EXECUTION_FAILED.json').exists():
            row.update(status='FAILED_CLOSED', failure=read(root / 'EXECUTION_FAILED.json'))
        elif (root / 'WATCHER_REPAIR_RETIREMENT.json').exists():
            row.update(status='WATCHER_STOPPED_FOR_REPAIR', watcher_repair=reference(root / 'WATCHER_REPAIR_RETIREMENT.json'))
        for name in ('READY', 'OPERATOR_STARTED', 'ACTUAL_BOUNDARY_READY', 'OWNER_RETIRED'):
            if (root / (name + '.json')).exists():
                row[name.lower()] = reference(root / (name + '.json'))
        row['controller_status'] = 'TRANSFER_NOT_STARTED' if label in ('C2', 'C5') else 'NOT_APPLICABLE'
        for name in ('CONTROLLER_STOP_INTENT', 'CONTROLLER_EXITED', 'CONTROLLER_LOCK_ACQUIRED', 'CONTROLLER_TRANSFER_VERIFIED'):
            if (root / (name + '.json')).exists():
                row[name.lower()] = reference(root / (name + '.json'))
                row['controller_status'] = name
        if (root / 'OPERATOR_STARTED.json').exists():
            process = read(root / 'OPERATOR_STARTED.json')['identity']
            path = Path('/proc') / str(process['pid']) / 'stat'
            row['operator_pid'] = process['pid']
            row['operator_live'] = path.exists() and path.read_text().rsplit(') ', 1)[1].split()[19] == process['start_ticks']
        attempt_root = root / 'attempt'
        row['child_status'] = 'NOT_LAUNCHED'
        if (attempt_root / 'ADMISSION.json').exists():
            admission = read(attempt_root / 'ADMISSION.json')
            row['admission'] = dict(reference=reference(attempt_root / 'ADMISSION.json'),
                clear=admission['clear'], scanner_euid=admission['scanner_euid'], gpu_uuid=admission['gpu']['uuid'])
        if (attempt_root / 'CONTAINMENT_VERIFIED.json').exists():
            row['containment'] = read(attempt_root / 'CONTAINMENT_VERIFIED.json')
        if (attempt_root / 'LAUNCH.json').exists():
            row['child_status'] = 'LAUNCH_RECORDED_LOAD_UNOBSERVED'
            launch = read(attempt_root / 'LAUNCH.json')
            row['launch'] = {key: launch.get(key) for key in ('pid', 'parent_start_ticks', 'plan_sha256', 'gpu_uuid', 'started_unix')}
        row['status'] = pre_load_status(row)
        if (root / 'ACTUAL_BOUNDARY_READY.json').exists():
            boundary = read(root / 'ACTUAL_BOUNDARY_READY.json')
            row['cycle_at_handoff'] = boundary['cycle']
            row['optimizer_steps_at_handoff'] = boundary['proof']['optimizer_steps']
            plan = read(root / 'PLAN.json')
            sys.path.insert(0, str(root))
            from stage_node5 import tail_metadata
            records = Path(read(root / 'INPUT.json')['storage_root']) / 'stream/records'
            after = int(Path(boundary['boundary']['path']).stem)
            paths = sorted(path for path in records.glob('*.json') if path.stem.isdigit() and int(path.stem) > after)
            row['events'] = []
            for path in sorted(set(paths[:32] + paths[-384:])):
                metadata = tail_metadata(path)
                if metadata['kind'] not in ('LOADED', 'COMMITTED', 'CONTEXT_RETAINED', 'COMPACTION', 'SLEEP_COMPLETE'):
                    continue
                event = dict(index=metadata['index'], kind=metadata['kind'], record_sha256=metadata['sha256'])
                if metadata['kind'] == 'LOADED':
                    document = read(path)['document']
                    event.update(loaded_metadata(document, boundary['proof'], 'launch' in row))
                    if event['own_attempt_launch_recorded']:
                        row['status'] = event['attribution']
                        row['loaded'] = event
                        row['child_status'] = row['status']
                    else:
                        row['external_loaded'] = event
                elif metadata['kind'] == 'CONTEXT_RETAINED':
                    document = read(path)['document']
                    event.update({key: document.get(key) for key in ('cycle', 'action', 'visible_prompt_tokens',
                        'threshold_tokens', 'history_sha256_before', 'history_sha256_after')})
                    row['context_retained'] = event
                elif metadata['kind'] == 'SLEEP_COMPLETE':
                    document = read(path)['document']
                    event.update(cycle=document['cycle'], full_history_sha256=document['resume_state']['state']['history']['state_sha256'])
                    row['completed_sleep'] = event
                row['events'].append(event)
        if label in READMISSIONS:
            try:
                inspect_readmission(row, READMISSIONS[label])
            except (OSError, ValueError, KeyError) as error:
                row['readmission_observation_error'] = str(error)
                row['status'] = 'CURRENT_READMISSION_VERIFICATION_UNCERTAIN'
        retained, completed = row.get('context_retained'), row.get('completed_sleep')
        if retained and completed and retained['cycle'] == completed['cycle']:
            row['retained_completed_sleep'] = dict(cycle=completed['cycle'],
                exact_history_preserved=(retained['action'] == 'RETAIN_CONTEXT_ACROSS_SLEEP' and
                    retained['history_sha256_before'] == retained['history_sha256_after'] == completed['full_history_sha256']),
                retention_record_sha256=retained['record_sha256'], sleep_record_sha256=completed['record_sha256'])
        output.append(row)
    return output


def main():
    if '--remote' in sys.argv:
        print(json.dumps(inspect(), sort_keys=True))
        return
    own = Path(__file__).resolve().parent
    command = '/localhome/local-rohing/v2/venv/bin/python -B -c ' + shlex.quote(Path(__file__).read_text()) + ' --remote'
    result = subprocess.run(['bash', 'gpu/ovx3_ssh.sh', command], text=True, capture_output=True, timeout=45)
    if result.returncode:
        raise RuntimeError('metadata_wrapper_failed_no_raw_output_exported')
    rows = json.loads(result.stdout)
    path = own / f'ROLLOUT_METADATA_{time.time_ns()}.json'
    with path.open('x') as handle:
        json.dump(dict(observed_unix=time.time(), rows=rows), handle, sort_keys=True, indent=2)
        handle.write('\n')
    print(path)
    for row in rows:
        print(row['label'], row['status'], 'operator_live', row.get('operator_live'),
              'controller', row['controller_status'],
              'loaded_pid', row.get('loaded', {}).get('pid'), 'sleep', row.get('completed_sleep', {}).get('cycle'),
              'head', row.get('head', {}).get('index'), row.get('head', {}).get('kind'),
              row.get('failure', {}).get('reason', ''))


if __name__ == '__main__':
    main()
