"""Native-only R109 inventory and exact task-boundary retirement."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time


ROOTS = {
    'node1': '/localhome/local-rohing/orch_rich_hot_node1_20260915_exhaustion_v1',
    'node2': '/localhome/local-rohing/orch_rich_hot_node2_exhaustion_v3_20260915_attempt1',
}
HOSTS = {'node1': 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b',
         'node2': '0e183169e60b06badac84e0eca6036a53b7ad90c433b8cd69b2a9aaf9159389b'}
DEST = Path('/localhome/local-rohing/orch_r109_l1_20260915')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(document, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def identity(pid):
    directory = Path('/proc') / str(pid)
    fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, uid=directory.stat().st_uid, start_ticks=fields[19],
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def root_for(node, index):
    if node == 'node1' and index == 3:
        return Path('/localhome/local-rohing/orch_rich_hot_node1_20260915_premise_v1')
    return Path(ROOTS[node])


def source_binding(root):
    path = root/'source.tar' if (root/'source.tar').exists() else root/'SOURCE_SHA256.json'
    return dict(path=str(path), sha256=sha(path))


def inventory(node):
    result = dict(node=node, observed_unix=time.time(), host_sha256=HOSTS[node], lanes=[], audit=[])
    for index in range(8):
        root = root_for(node, index)
        launch = read(root / f'LAUNCH_{index}.json')
        expected = launch['identity']
        try:
            alive = identity(expected['pid']) == expected
        except FileNotFoundError:
            alive = False
        paths = sorted((root / f'shard{index}').glob('CALL_*.json')) if node == 'node1' else sorted((root / f'shard{index}').glob('*.json'))
        rows = []
        for path in paths:
            row = read(path)
            if 'response' in row and 'finished_unix' in row:
                rows.append((path, row))
        recent = [row for _, row in rows if row['finished_unix'] >= result['observed_unix'] - 600]
        result['lanes'].append(dict(index=index, root=str(root), identity=expected, alive=alive,
            completed_captures=len(rows), recent600=len(recent), raw_captures_hour=len(recent)*6,
            qualified_rows_hour=None, lifetime=read(root/'LIFETIME.json'),
            source_binding=source_binding(root)))
        if index < 6 and rows:
            path, row = sorted(rows, key=lambda pair: pair[1]['finished_unix'])[-1]
            raw = row['response'].get('raw', '')
            result['audit'].append(dict(index=index, path=str(path), sha256=sha(path),
                task_id=row.get('task_id'), family=row.get('family', 'math'), stage=row.get('stage'),
                source_state=row.get('source_state', row.get('generator_identity',{}).get('state_sha256')),
                outcome=row.get('outcome'), full_text_characters=len(raw), full_text=raw if len(raw)<=10000 else None,
                text_prefix=raw[:10000] if len(raw)>10000 else None,
                partial=len(raw)>10000, messages=row.get('messages'), task=row.get('task')))
    result['gpu'] = subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu',
                                           '--format=csv,noheader,nounits'],text=True).splitlines()
    return result


def retire(node, index):
    root = root_for(node,index)
    expected = read(root/f'LAUNCH_{index}.json')['identity']
    assert identity(expected['pid']) == expected and expected['uid'] == os.getuid()
    if node == 'node2':
        marker = root/f'STOP_AFTER_TASK_{index}.json'
        if not marker.exists():
            write(marker, dict(experiment='R109', reason='parenting_handoff' if index==7 else 'R109_reallocation',
                               identity=expected, observed_unix=time.time()))
        print(json.dumps(dict(node=node,index=index,status='TASK_BOUNDARY_STOP_REQUESTED')),flush=True)
        return
    from gpu import orch_rich_hot_node1_scan as scanner
    from gpu.orch_rich_hot_node1_exhaustion_boundary import complete_tasks
    pid = expected['pid']
    command = (Path('/proc')/str(pid)/'cmdline').read_bytes()
    module = b'gpu.orch_rich_hot_node1_premise_run' if index==3 else b'gpu.orch_rich_hot_node1_exhaustion_run'
    assert module+b'\0run\0' in command
    assert str(root).encode() in command and os.getpgid(pid)==pid
    assert ('CUDA_VISIBLE_DEVICES='+scanner.policy.UUIDS[index]).encode() in (Path('/proc')/str(pid)/'environ').read_bytes().split(b'\0')
    original = Path(read(root/'CONTINUATION.json')['original_root'])
    phase = read(root/f'shard{index}/ACTOR_READY.json')['phase_version']
    until = min(time.time()+1800,read(root/'LIFETIME.json')['native_deadline_unix'])
    while time.time()<until:
        with (original/'CALL_RESERVATIONS.jsonl').open() as ledger:
            fcntl.flock(ledger,fcntl.LOCK_SH)
            assert identity(pid)==expected
            descriptor=os.pidfd_open(pid)
            stopped=False
            try:
                signal.pidfd_send_signal(descriptor,signal.SIGSTOP)
                stopped=True
                reservations=[json.loads(line) for line in ledger if line.strip()]
                reservations=[row for row in reservations if row.get('phase_version')==phase]
                paths=sorted((root/f'shard{index}').glob('CALL_[0-9][0-9][0-9][0-9][0-9].json'))
                rows=[read(path) for path in paths]
                contexts=[read(path) for path in (root/f'shard{index}').glob('CONTEXT_*.json')]
                completed=complete_tasks(rows,reservations,index,contexts)
                if completed is not None:
                    receipt=dict(node=node,index=index,identity=expected,source_root=str(root),
                        completed_calls=len(rows),completed_tasks=completed,pending_calls=[],pending_pairs=[],
                        source_binding=source_binding(root),lifetime_sha256=sha(root/'LIFETIME.json'),
                        files={str(path.relative_to(root)):sha(path) for path in paths},observed_unix=time.time())
                    write(DEST/f'RETIRE_{index}.json',receipt)
                    signal.pidfd_send_signal(descriptor,signal.SIGTERM)
                    print(json.dumps(dict(node=node,index=index,status='BOUNDARY_PRESERVED_TERM_SENT',calls=len(rows))),flush=True)
                    return
            finally:
                if stopped:
                    signal.pidfd_send_signal(descriptor,signal.SIGCONT)
                os.close(descriptor)
        time.sleep(.1)
    raise TimeoutError('No safe task boundary before fixed retirement deadline')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['inventory','retire'])
    parser.add_argument('--node',choices=ROOTS,required=True)
    parser.add_argument('--index',type=int,choices=range(8))
    args=parser.parse_args()
    assert hashlib.sha256(socket.gethostname().encode()).hexdigest()==HOSTS[args.node]
    if args.action=='inventory':
        print(json.dumps(inventory(args.node)))
    else:
        retire(args.node,args.index)


if __name__=='__main__':
    main()
