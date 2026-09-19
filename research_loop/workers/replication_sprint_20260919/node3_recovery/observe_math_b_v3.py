"""Bounded read-only observation of the single V3 recovery, never a retry."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path('/localhome/local-rohing/orch_r205_node3_20260918/r213_math_b_fork')
CONTROL = ROOT / 'control_ws6_pending_math_b_20260919T144429Z'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def observe():
    result = dict(utc=datetime.now(timezone.utc).isoformat(), host=os.uname().nodename,
        control=str(CONTROL), read_only=True, files={}, records=[], processes=[])
    names = ('BUILDER1450_PUBLICATION.json', 'ALLOCATION_BUILDER1450.json', 'GUARD_BUILDER1450.json',
        'OUTER_STARTED.json', 'PRE_SERVICE_ADMISSION.json', 'CONFINEMENT_CPU.json',
        'CONFINEMENT_CHILD.json', 'ADMISSION.json', 'LAUNCH.json', 'EXIT.json',
        'OUTER_FAILED.json', 'OUTER_EXIT.json', 'SERVICE_IDENTITY.json')
    for name in names:
        path = CONTROL / name
        if not path.exists():
            continue
        raw = path.read_bytes()
        value = json.loads(raw)
        item = dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        if name in ('PRE_SERVICE_ADMISSION.json', 'ADMISSION.json'):
            report = value.get('report', value)
            item['summary'] = {key: report.get(key) for key in ('scanner_euid', 'clear',
                'blocking_reasons', 'created_utc', 'gpu', 'target_device_ownership_checks_unchanged')}
        elif name == 'GUARD_BUILDER1450.json':
            item['summary'] = {key: value[key] for key in ('plan_sha256', 'allocation_sha256',
                'hard_end_unix', 'pending_sleep_recovery')}
        elif name == 'BUILDER1450_PUBLICATION.json':
            item['summary'] = {key: value[key] for key in ('git_commit', 'entry_sha256', 'document_sha256')}
        else:
            item['summary'] = value
        result['files'][name] = item
    records = ROOT / 'raw' / 'stream' / 'records'
    paths = sorted(path for path in records.iterdir() if re.fullmatch(r'\d{20}\.json', path.name))
    result['record_count'] = len(paths)
    result['head_index'] = int(paths[-1].stem)
    candidates = [path for path in paths if int(path.stem) > 9555]
    result['new_record_count'] = len(candidates)
    result['record_window_truncated'] = len(candidates) > 160
    read_bytes = 0
    for path in candidates[:160]:
        size = path.stat().st_size
        if size > 64 * 1024**2 or read_bytes + size > 512 * 1024**2:
            result['byte_bound_reached'] = True
            break
        raw = path.read_bytes()
        read_bytes += len(raw)
        record = json.loads(raw)
        document = record['document']
        summary = {key: record[key] for key in ('index', 'kind', 'sha256', 'previous_sha256')}
        summary['path'] = str(path)
        summary['mtime_unix'] = path.stat().st_mtime
        summary['digest_valid'] = record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'})
        intent = path.with_name(path.stem + '.intent.json')
        expected = {key: record[key] for key in ('schema', 'journal_id', 'index', 'previous_sha256')}
        expected['record_sha256'] = record['sha256']
        summary['intent_valid'] = intent.exists() and json.loads(intent.read_bytes()) == expected
        summary['fields'] = {key: value for key, value in document.items()
            if isinstance(value, (int, float, bool)) or value is None
            or isinstance(value, str) and len(value) <= 300}
        summary['document_keys'] = sorted(document)
        for key in ('request', 'receipt'):
            nested = document.get(key)
            if isinstance(nested, dict):
                summary[key] = {field: value for field, value in nested.items()
                    if isinstance(value, (int, float, bool)) or value is None
                    or isinstance(value, str) and len(value) <= 300}
        checkpoint = document.get('checkpoint')
        if isinstance(checkpoint, dict):
            summary['checkpoint'] = {key: checkpoint.get(key) for key in ('optimizer_steps',
                'adapter_state_sha256', 'adapter_path', 'optimizer_rng_path', 'checkpoint_sha256')}
        state = document.get('state', document.get('resume_state'))
        if isinstance(state, dict):
            state = state.get('state', state)
            summary['state'] = dict(rows=len(state.get('rows', [])), frontier=state.get('sleep_frontier'),
                pending=state.get('pending') is not None)
        result['records'].append(summary)
    result['decoded_new_bytes'] = read_bytes
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            arguments = (process / 'cmdline').read_bytes().decode(errors='replace').split('\0')
            if 'gpu.ws6_math_b_pending_entry' not in arguments:
                continue
            fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
            result['processes'].append(dict(pid=int(process.name), argv=arguments, start_ticks=fields[19],
                status=fields[0], parent_pid=fields[1], cpu_ticks=int(fields[11]) + int(fields[12])))
        except FileNotFoundError:
            continue
    result['compute_apps'] = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,gpu_uuid,process_name',
        '--format=csv,noheader'], capture_output=True, text=True, check=True, timeout=20).stdout
    capacity = os.statvfs(ROOT)
    result['owner_available_bytes'] = capacity.f_bavail * capacity.f_frsize
    result['owner_available_blocks'] = capacity.f_bavail
    for name in ('NATIVE.log', 'BUILDER1450_DISPATCH.log'):
        path = CONTROL / name
        if path.exists():
            with path.open('rb') as source:
                source.seek(max(0, path.stat().st_size - 5000))
                result[name] = source.read().decode(errors='replace')
    print(json.dumps(result, sort_keys=True), flush=True)


def main():
    here = Path(__file__).resolve().parent
    source = Path(__file__).read_text().rsplit("if __name__ == '__main__':", 1)[0] + '\nobserve()\n'
    response = subprocess.run(['bash', 'gpu/ovx2_ssh.sh', 'env PYTHONDONTWRITEBYTECODE=1 python3 -B -'],
        cwd=here.parents[3], input=source, capture_output=True, text=True, timeout=120)
    response.check_returncode()
    value = json.loads(response.stdout)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = here / ('MATH_B_V3_OBSERVATION_' + stamp + '.json')
    with destination.open('x') as output:
        output.write(response.stdout)
        output.flush()
        os.fsync(output.fileno())
    updates = [record for record in value['records'] if record['kind'] == 'UPDATE']
    print(json.dumps(dict(receipt=str(destination), utc=value['utc'], head=value['head_index'],
        update_count=len(updates), last_optimizer_step=updates[-1]['fields']['optimizer_step'] if updates else None,
        records=[dict(index=record['index'], kind=record['kind'], fields=record['fields'])
            for record in value['records'] if record['kind'] in ('SLEEP_COMPLETE', 'LOADED',
                'NODE3_PENDING_SLEEP_STARTUP_COMPLETE', 'REQUEST', 'RESPONSE', 'R184_STAGE', 'R184_ACT')],
        record_count=value['record_count'], compute_apps=value['compute_apps'],
        processes=[{key: process[key] for key in ('pid', 'start_ticks', 'status', 'cpu_ticks')}
            for process in value['processes']], failures={key: value['files'][key]
            for key in ('EXIT.json', 'OUTER_FAILED.json', 'OUTER_EXIT.json') if key in value['files']},
        native_log_tail=value.get('NATIVE.log'), owner_available_bytes=value['owner_available_bytes']), sort_keys=True))


if __name__ == '__main__':
    main()
