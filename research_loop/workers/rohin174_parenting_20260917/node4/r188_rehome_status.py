"""Read actual receiving journals and process identities; never dispatch or publish."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

import r188_receive as receiving


NAMES = {0: 'support_free', 2: 'brain_free', 3: 'brain_guided'}


def identity(pid):
    directory = Path('/proc', str(pid))
    try:
        fields = (directory / 'stat').read_text().rsplit(') ', 1)[1].split()
        argv = (directory / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
        return dict(pid=pid, start_ticks=fields[19], state=fields[0], argv=argv,
            uid=directory.stat().st_uid, alive=fields[0] not in ('Z', 'X'),
            cgroup=(directory / 'cgroup').read_text().strip())
    except FileNotFoundError:
        return dict(pid=pid, alive=False)


def collect(physical):
    output = receiving.HOME / f'receiving{physical}v2'
    ready = receiving.read(output / 'PREPARED.json')
    control = output / ('control_admission2' if physical == 3 else 'control')
    guard = receiving.read(control / 'GUARD.json')
    plan = receiving.read(guard['plan_path'])
    admission_path = control / 'ADMISSION.json'
    admission = receiving.read(admission_path) if admission_path.exists() else None
    row = dict(life=NAMES[physical], original_physical=physical, physical=plan['physical'],
        gpu_uuid=plan['gpu_uuid'], wrapper='gpu/a40r_ssh.sh', root=ready['root'],
        backing_root=ready['backing_root'], source_root=ready['source_root'], control=str(control),
        hard_end_unix=plan['hard_end_unix'], status='WAITING_FOR_ACTUAL_LOADED',
        packet_sha256=ready['packet_sha256'], final_overlay_sha256=ready['final_overlay_sha256'],
        saved_cycle=ready['saved_cycle'], saved_state_sha256=ready['saved_state_sha256'],
        preserved_suffix_accounting=ready['preserved_suffix_accounting'],
        parent_owner='Tesla', parent_rebind_required=True, publish_not_executed=True,
        automatic_publication_retry_prohibited=True)
    if admission is not None:
        row['admission'] = dict(clear=admission['clear'], blocking_reasons=admission['blocking_reasons'],
            scanner_euid=admission['scanner_euid'], file_sha256=receiving.sha(admission_path))
        if not admission['clear']:
            row['status'] = 'ADMISSION_BLOCKED_NO_NATIVE'
    new_records = []
    index = ready['saved_index'] + 1
    while True:
        path = Path(ready['root']) / f'stream/records/{index:020d}.json'
        if not path.exists():
            break
        record = receiving.read(path)
        if record['kind'] in ('LOADED', 'WALL_EXTENDED', 'SLEEP_RECIPE', 'SLEEP_COMPLETE', 'CONTEXT_RETAINED'):
            entry = dict(kind=record['kind'], index=index, record_sha256=record['sha256'],
                file_sha256=receiving.sha(path))
            document = record['document']
            if record['kind'] == 'LOADED':
                entry.update({key: document[key] for key in ('pid', 'loaded_unix', 'optimizer_steps', 'resume')})
                actor = identity(document['pid'])
                receiving.require(admission is not None and admission['clear'] and not admission['blocking_reasons']
                    and admission['scanner_euid'] == 0 and admission['gpu']['uuid'] == plan['gpu_uuid'],
                    'actual_unchanged_admission')
                confinement = receiving.read(control / 'CONTAINMENT_VERIFIED.json')
                receiving.require(confinement['denied_foreign_minors'] == [minor for minor in range(8)
                    if minor != guard['device_containment']['minor']], 'seven_foreign_minors_denied')
                receiving.require(actor['alive'] and actor['uid'] == 2524
                    and actor['argv'] == [str(receiving.PYTHON), '-B', '-m',
                        'gpu.orch_r125_continual_guard', 'native', '--config', str(control / 'GUARD.json')]
                    and actor['cgroup'] == '0::/system.slice/' + guard['device_containment']['unit'] + '.service',
                    'exact_live_contained_native')
                row.update(status='ACTUAL_RECEIVING_LOADED', native=actor, loaded=entry,
                    confinement_sha256=receiving.sha(control / 'CONTAINMENT_VERIFIED.json'),
                    guard_sha256=receiving.sha(control / 'GUARD.json'))
            elif record['kind'] == 'SLEEP_RECIPE':
                entry['document'] = document
            elif record['kind'] in ('SLEEP_COMPLETE', 'CONTEXT_RETAINED'):
                entry['cycle'] = document.get('cycle')
            new_records.append(entry)
        index += 1
    row['new_record_evidence'] = new_records
    row['last_record_index'] = index - 1
    if (control / 'EXIT.json').exists():
        row['exit'] = receiving.read(control / 'EXIT.json')
        row['status'] = 'NATIVE_EXIT_REQUIRES_INSPECTION'
    prefix = ['env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH=' + ready['source_root'], str(receiving.PYTHON), '-B', '-m']
    console = Path(ready['source_root']) / 'gpu/orch_r127_pilot_console.py'
    if console.is_file():
        row['pilot_console_sha256'] = receiving.sha(console)
        follow = prefix + ['gpu.orch_r125_stream_console', '--root', ready['root'], '--follow']
        publish = prefix + ['gpu.orch_r127_pilot_console', 'parent', '--root', ready['root'],
            '--speaker', 'Rohin', '--text', 'REPLACE_WITH_EXACT_ROHIN_TEXT']
        row['follow_command'] = 'bash gpu/a40r_ssh.sh ' + shlex.quote(shlex.join(follow))
        row['rohin_publish_template'] = 'bash gpu/a40r_ssh.sh ' + shlex.quote(shlex.join(publish))
    return row


def main():
    receiving.check_host()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--minutes', type=int, default=0)
    args = parser.parse_args()
    receiving.require(0 <= args.minutes <= 90, 'bounded_readonly_observer')
    output = receiving.HOME / 'observations'
    output.mkdir(exist_ok=True)
    deadline = time.monotonic() + args.minutes * 60
    while True:
        rows = []
        for physical in receiving.TARGETS:
            try:
                rows.append(collect(physical))
            except Exception as error:
                rows.append(dict(original_physical=physical, status='OBSERVATION_ERROR',
                    error_type=type(error).__name__, reason=str(error)))
        document = dict(observed_unix=time.time(), observer=identity(os.getpid()),
            loaded_count=sum(row['status'] == 'ACTUAL_RECEIVING_LOADED' for row in rows), rows=rows)
        path = output / f'REHOME_{time.time_ns()}.json'
        receiving.write(path, document)
        print(json.dumps(dict(path=str(path), loaded_count=document['loaded_count'],
            rows=[{key: row.get(key) for key in ('life', 'status', 'loaded', 'admission', 'reason')}
                for row in rows])), flush=True)
        if time.monotonic() >= deadline:
            return
        time.sleep(20)


if __name__ == '__main__':
    main()
