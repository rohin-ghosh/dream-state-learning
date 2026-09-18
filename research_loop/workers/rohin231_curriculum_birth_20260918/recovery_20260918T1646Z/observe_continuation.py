"""Read-only, text-free receipts for the authorized pair continuations."""

from datetime import datetime, timezone
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import time

from extension_spec import ROOT_NAMES, digest


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def process(pid):
    try:
        stat = Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()
        result = dict(pid=pid, state=stat[0], start_ticks=stat[19], user_ticks=int(stat[11]),
            system_ticks=int(stat[12]))
        io = dict(line.split(': ', 1) for line in Path(f'/proc/{pid}/io').read_text().splitlines())
        result['read_characters'] = int(io['rchar'])
        return result
    except FileNotFoundError:
        return None


def observe(physical):
    root = Path('/localhome/local-rohing') / ROOT_NAMES[physical]
    original = root / 'extension_oct01_preview_20260918T1742Z/authorized_continuation_1754Z'
    retry = root / 'extension_oct01_preview_20260918T1742Z/authorized_continuation_sidecar_retry_1811Z'
    control = retry if (retry / 'GUARD.json').exists() else original
    result = dict(physical=physical, observed_utc=utc(time.time()), raw_text_exported=False,
        resident_unsaved_sampling_RNG_continuation_claim=False,
        journal_id=read(root / 'raw/stream/JOURNAL.json')['journal_id'])
    if not control.exists():
        result['status'] = 'NOT_STARTED'
        return result
    for name in ('WAITING_BOUNDARY', 'TERM', 'EXIT_BOUNDARY', 'DISPATCHED', 'OUTER_STARTED', 'LAUNCH'):
        parent = original if name in ('WAITING_BOUNDARY', 'TERM', 'EXIT_BOUNDARY') else control
        path = parent / (name + '.json')
        if path.exists():
            result[name.lower()] = read(path)
    result['active_attempt_name'] = control.name
    if control != original:
        result['prior_failed_attempt'] = dict(exit=read(original / 'EXIT.json'),
            native_log_sha256=sha(original / 'NATIVE.log'),
            reason='Missing required receiving PRESERVATION.json before model construction',
            records_preserved=True, no_signal_for_latency=True)
    if (original / 'SIDECAR_REPAIR.json').exists():
        result['sidecar_repair'] = read(original / 'SIDECAR_REPAIR.json')
    memory_path = root / 'extension_oct01_preview_20260918T1742Z/control/MEMORY.json'
    if memory_path.exists():
        memory = read(memory_path)
        result['receiving_memory_probe'] = dict(receipt_sha256=sha(memory_path), **{key:memory.get(key)
            for key in ('passed', 'optimizer_steps', 'saved_RNG_restored', 'optimizer_step_calls',
                'synthetic_probe_not_child_training', 'adapter_sha256', 'checkpoint_sha256')})
    if (control / 'OUTER_FAILED.json').exists():
        failure = read(control / 'OUTER_FAILED.json')
        result['dispatch_error'] = dict(error_type=failure['error_type'], error_sha256=sha(control / 'OUTER_FAILED.json'))
    if (control / 'PRE_SERVICE_ADMISSION.json').exists():
        admission = read(control / 'PRE_SERVICE_ADMISSION.json')
        result['admission'] = dict(scanner_euid=admission['report']['scanner_euid'],
            clear=admission['report']['clear'], blocking_reasons=admission['report']['blocking_reasons'],
            verified_utc=utc(admission['verified_unix']), receipt_sha256=sha(control / 'PRE_SERVICE_ADMISSION.json'))
    if (original / 'BOUNDARY.json').exists():
        bound = read(original / 'BOUNDARY.json')
        complete = bound['complete']
        checkpoint = complete['document']['checkpoint']
        result['bound_complete'] = dict(index=complete['index'], record_sha256=complete['sha256'],
            cycle=complete['document']['cycle'], optimizer_steps=checkpoint['optimizer_steps'],
            checkpoint_sha256=checkpoint['checkpoint_sha256'], saved_state_sha256=complete['document']['resume_state']['sha256'],
            adapter_state_sha256=checkpoint['adapter_state_sha256'])
    if 'launch' in result:
        timeout_pid = result['launch']['pid']
        children = Path(f'/proc/{timeout_pid}/task/{timeout_pid}/children')
        result['native_processes'] = [process(int(pid)) for pid in children.read_text().split()] if children.exists() else []
        guard_sha = result['launch']['guard_sha256']
        unit = 'orch-r184-c2-explicit-child-' + guard_sha[:16]
        shown = subprocess.check_output(['systemctl', 'show', unit, '--property=ActiveState',
            '--property=RuntimeMaxUSec', '--property=ActiveEnterTimestamp', '--property=TimeoutStopUSec'], text=True)
        result['service'] = dict(line.split('=', 1) for line in shown.splitlines() if '=' in line)
        result['service']['unit'] = unit
        result['wrapper_command'] = Path(f'/proc/{timeout_pid}/cmdline').read_bytes().decode().split('\0') if children.exists() else []
    cut = result.get('term', {}).get('head_index')
    if cut is None:
        result['old_native'] = process(result['waiting_boundary']['native_pid']) if 'waiting_boundary' in result else None
        result['status'] = 'WAITING_COMPLETE_NATIVE_CONTINUES'
        return result
    paths = sorted(path for path in (root / 'raw/stream/records').glob('*.json') if path.stem.isdigit())
    result['head_index'] = int(paths[-1].stem)
    result['loaded'], result['wall_extended'], result['requests'], result['responses'] = [], [], [], []
    result['sleep_complete'], result['recipes'], result['eligibility'], result['sleep_notices'] = [], [], [], []
    for path in reversed(paths):
        if int(path.stem) > cut:
            continue
        record = read(path)
        if record['kind'] == 'RESPONSE':
            result['last_old_response'] = dict(index=record['index'], record_sha256=record['sha256'],
                finished_unix=record['document']['finished_unix'], finished_utc=utc(record['document']['finished_unix']))
            break
    for path in paths:
        if int(path.stem) <= cut:
            continue
        record = read(path)
        document = record['document']
        reference = dict(index=record['index'], record_sha256=record['sha256'], file_sha256=sha(path))
        kind = record['kind']
        if kind == 'LOADED':
            result['loaded'].append(dict(reference, pid=document['pid'], resume=document['resume'],
                loaded_unix=document['loaded_unix'], loaded_utc=utc(document['loaded_unix']),
                optimizer_steps=document['optimizer_steps'], adapter_sha256=document['adapter_sha256']))
        elif kind == 'WALL_EXTENDED':
            restored = deepcopy(document['state']['state'])
            restored['deadline_unix'] = document['authorization']['previous_deadline_unix']
            result['wall_extended'].append(dict(reference, authorization=document['authorization'],
                state_sha256=document['state']['sha256'], file_published_mtime_utc=utc(path.stat().st_mtime),
                all_non_deadline_state_exact=digest(restored) == result['bound_complete']['saved_state_sha256']))
        elif kind == 'REQUEST':
            result['requests'].append(dict(reference, started_unix=document['started_unix'],
                started_utc=utc(document['started_unix']), prompt_tokens=document['prompt_tokens'],
                actual_request_deadline_unix=document['deadline_unix']))
        elif kind == 'RESPONSE':
            result['responses'].append(dict(reference, finished_unix=document['finished_unix'],
                finished_utc=utc(document['finished_unix']), raw_sha256=hashlib.sha256(document['response']['raw'].encode()).hexdigest()))
        elif kind == 'SLEEP_COMPLETE':
            result['sleep_complete'].append(dict(reference, cycle=document['cycle'],
                optimizer_steps=document['checkpoint']['optimizer_steps'],
                before_adapter_sha256=document.get('before_adapter_sha256'),
                after_adapter_sha256=document.get('after_adapter_sha256'), weight_updates_enabled=document.get('weight_updates_enabled')))
        elif kind in ('SLEEP_RECIPE', 'TARGET_ELIGIBILITY'):
            target = 'recipes' if kind == 'SLEEP_RECIPE' else 'eligibility'
            result[target].append(dict(reference, **{key:document.get(key) for key in
                ('learn_row_policy', 'active_semantic_filters', 'semantic_row_exclusion', 'weight_updates_enabled',
                 'new_rows', 'new_presentations', 'selected_old_rows', 'excluded', 'raw_modified')}))
        elif kind == 'R184_SLEEP_NOTICE':
            result['sleep_notices'].append(dict(reference, cycle=document['cycle']))
    result['status'] = 'LOADED' if result['loaded'] else 'REPLACEMENT_DISPATCHED_LOAD_PENDING'
    if result['loaded']:
        result['observed_old_exit_to_LOAD_seconds'] = result['loaded'][0]['loaded_unix'] - result['exit_boundary']['observed_exit_unix']
        result['observed_last_old_response_to_LOAD_seconds'] = result['loaded'][0]['loaded_unix'] - result['last_old_response']['finished_unix']
    return result


if __name__ == '__main__':
    print(json.dumps([observe(physical) for physical in (1, 0)], indent=2, sort_keys=True))
