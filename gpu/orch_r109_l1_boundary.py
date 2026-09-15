"""Non-signalling reservation interlock for an already-authorized node1 roll."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import time


def read(path):
    return json.loads(Path(path).read_text())


def boundary(reservations,rows,index):
    own={row['global_call'] for row in reservations if row['index']==index}
    captures=[row for row in rows if row['index']==index]
    if own!={row['global_call'] for row in captures}:
        return 'PENDING_CALL'
    tasks={}
    for row in captures:
        tasks.setdefault(row['task_id'],set()).add(row['stage'])
    if tasks and all(stages=={'source','own_second_pass'} for stages in tasks.values()):
        return 'COMPLETE_PAIR_BOUNDARY'
    return 'ALLOW_REQUIRED_SECOND_PASS'


def hold(index):
    assert index==5,'only_remaining_owned_two_pass_roll'
    assert hashlib.sha256(socket.gethostname().encode()).hexdigest()=='e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
    root=Path('/localhome/local-rohing/orch_rich_hot_node1_20260915_exhaustion_v1')
    output=Path('/localhome/local-rohing/orch_r109_l1_20260915')
    expected=read(root/f'LAUNCH_{index}.json')['identity']
    original=Path(read(root/'CONTINUATION.json')['original_root'])
    ledger_path=original/'CALL_RESERVATIONS.jsonl'
    phase=read(root/f'shard{index}/ACTOR_READY.json')['phase_version']
    until=min(time.time()+900,read(root/'LIFETIME.json')['native_deadline_unix'])
    def alive():
        directory=Path('/proc')/str(expected['pid'])
        if not directory.exists():
            return False
        fields=(directory/'stat').read_text().rsplit(')',1)[1].split()
        assert directory.stat().st_uid==expected['uid']==os.getuid() and fields[19]==expected['start_ticks']
        assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==expected['boot_id']
        return fields[0]!='Z'
    while time.time()<until and alive():
        with ledger_path.open() as ledger:
            fcntl.flock(ledger,fcntl.LOCK_SH)
            while time.time()<until and alive():
                ledger.seek(0)
                reservations=[json.loads(line) for line in ledger if line.strip()]
                reservations=[row for row in reservations if row.get('phase_version')==phase]
                paths=list((root/f'shard{index}').glob('CALL_[0-9][0-9][0-9][0-9][0-9].json'))
                rows=[read(path) for path in paths]
                state=boundary(reservations,rows,index)
                if state=='ALLOW_REQUIRED_SECOND_PASS':
                    previous_count=sum(row['index']==index for row in reservations)
                    break
                if state=='COMPLETE_PAIR_BOUNDARY':
                    receipt=dict(index=index,identity=expected,non_signalling_interlock=True,
                        state=state,calls=len(rows),observed_unix=time.time(),
                        action='HOLD_NEXT_RESERVATION_FOR_EXISTING_AUTHORIZED_BOUNDARY_CONTROLLER')
                    (output/'INTERLOCK5_READY.json').write_text(json.dumps(receipt,indent=2))
                    while time.time()<until and alive():
                        time.sleep(.1)
                    print(json.dumps(dict(receipt,old_worker_exited=not alive())))
                    return
                time.sleep(.1)
            else:
                return
        while time.time()<until and alive():
            rows=[json.loads(line) for line in ledger_path.read_text().splitlines()]
            count=sum(row.get('phase_version')==phase and row['index']==index for row in rows)
            if count>previous_count:
                break
            time.sleep(.1)
    print(json.dumps(dict(index=index,status='EXITED_OR_FIXED_INTERLOCK_TIMEOUT',no_signals_sent=True)))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--index',type=int,required=True)
    hold(parser.parse_args().index)
