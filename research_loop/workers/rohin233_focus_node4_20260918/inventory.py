"""Bounded read-only node4 census; never imports the learning runtime."""

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import time

BASE = Path('/localhome/local-rohing/orch_r201_node4_20260918/node4/R195_FLEET')
HOST_SHA = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'


def read(path):
    return json.loads(Path(path).read_bytes())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def identity(pid):
    process = Path('/proc', str(pid))
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=pid, start_ticks=fields[19], state=fields[0], parent=int(fields[1]),
        group=int(fields[2]), uid=process.stat().st_uid,
        argv=(process / 'cmdline').read_bytes().decode().strip('\0').split('\0'),
        cwd=os.readlink(process / 'cwd'), cgroup=(process / 'cgroup').read_text().strip(),
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def metadata(path):
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size - 4096))
        ending = stream.read()
    offset = ending.rfind(b',"index":')
    row = json.loads(b'{' + ending[offset + 1:]) if offset >= 0 else read(path)
    return {key: row[key] for key in ('index', 'kind', 'sha256', 'previous_sha256', 'journal_id')}


def main():
    if hashlib.sha256(socket.gethostname().encode()).hexdigest() != HOST_SHA or os.getuid() != 2524:
        raise ValueError('exact_node4_owner_required')
    processes, errors = [], []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != 2524:
                continue
            argv = (process / 'cmdline').read_bytes().decode().strip('\0').split('\0')
            if 'gpu.orch_r125_continual_guard' not in argv or 'native' not in argv or '--config' not in argv:
                continue
            if argv[0].endswith('timeout'):
                continue
            actor = identity(int(process.name))
            guard_path = Path(argv[argv.index('--config') + 1])
            guard = read(guard_path)
            plan_path = Path(guard['plan_path'])
            plan = read(plan_path)
            if BASE not in Path(plan['root']).parents:
                continue
            if hashlib.sha256(plan_path.read_bytes()).hexdigest() != guard['plan_sha256']:
                raise ValueError('guard_plan_binding')
            actor.update(guard=str(guard_path), guard_sha256=hashlib.sha256(guard_path.read_bytes()).hexdigest(),
                plan={key: plan.get(key) for key in ('root', 'source_root', 'physical', 'gpu_uuid', 'hard_end_unix', 'max_sleeps')},
                attempt_dir=guard['attempt_dir'])
            processes.append(actor)
        except (FileNotFoundError, ProcessLookupError):
            continue
        except Exception as error:
            errors.append(dict(pid=int(process.name), error=type(error).__name__ + ':' + str(error)))
    lives = []
    for physical in (0, 1, 2, 3, 5, 6, 7):
        home = BASE / ('MATH_C' if physical == 6 else f'SCALE_physical{physical}')
        root = home / 'life'
        paths = sorted((root / 'stream/records').glob('[0-9]' * 20 + '.json'))
        latest = {}
        for path in reversed(paths):
            header = metadata(path)
            if header['kind'] not in ('LOADED', 'SLEEP_COMPLETE', 'R184_STAGE') or header['kind'] in latest:
                continue
            row = read(path)
            if row['sha256'] != digest({key: value for key, value in row.items() if key != 'sha256'}):
                raise ValueError('canonical_record_hash')
            document = row['document']
            receipt = dict(header, file_mtime_unix=path.stat().st_mtime)
            for key in ('pid', 'loaded_unix', 'cycle', 'status', 'total_optimizer_steps', 'checkpoint_sha256', 'stage'):
                if key in document:
                    receipt[key] = document[key]
            if row['kind'] == 'SLEEP_COMPLETE':
                receipt['checkpoint'] = document['checkpoint']
                receipt['state_sha256'] = document['resume_state']['sha256']
                receipt['state_hash_valid'] = digest(document['resume_state']['state']) == receipt['state_sha256']
            latest[row['kind']] = receipt
            if len(latest) == 3:
                break
        tail = [metadata(path) for path in paths[-5:]]
        lives.append(dict(physical=physical, root=str(root), backing_root=str(root.resolve()),
            native=[actor for actor in processes if actor['plan']['root'] == str(root)], latest=latest,
            tail=tail, record_count=len(paths), inbox_files=len(list((root / 'stream/inbox').glob('*.json')))))
    gpu = subprocess.run(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,process_name,used_memory',
        '--format=csv,noheader'], text=True, capture_output=True, timeout=20)
    print(json.dumps(dict(observed_unix=time.time(), lives=lives, process_errors=errors,
        gpu_processes=gpu.stdout.splitlines(), gpu_query_returncode=gpu.returncode, signals=0, remote_writes=0)))


if __name__ == '__main__':
    main()
