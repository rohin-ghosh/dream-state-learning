"""Foreground CPU complement: feedback for confirmed undispatched bound failures."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from transport_preflight import HERE, remote
from restore_transport import DEADLINE, identity, put


def failure_call(path, started, mode):
    raw = path.read_bytes()
    transport = json.loads(raw)
    baseline = json.loads((HERE/'BINDINGS.json').read_bytes())
    source = 'import sys,json\n' + (HERE/'node_bridge.py').read_text().split("if __name__ == '__main__':")[0]
    source += '\nbridge_functions=globals().copy()\n'
    source += (HERE/'bounded_failure.py').read_text()
    source += '\nfailure_functions=globals().copy()\n'
    source += (HERE/'error_bridge.py').read_text()
    source += '\nprint(json.dumps(handle_failure(json.load(sys.stdin),bridge_functions,failure_functions)))\n'
    value = remote('ovx2_ssh.sh',source,dict(bindings=baseline['bindings'],
        mode=mode,transport_raw=raw.decode(),transport_file_sha256=hashlib.sha256(raw).hexdigest(),
        restored_unix=started['unix']))
    return dict(life=transport['session_id'],transport_path=str(path),transport_failure=transport,result=value)


def run(mode, once):
    if mode=='publish' and (os.uname().nodename!='nvl-ai' or Path('/proc/1/comm').read_text().strip()!='systemd'):
        raise ValueError('real_VM_host_required_for_persistent_reporter')
    lock = (HERE/'locks/OPERATIONAL_ERRORS.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    output = HERE/'private/operational_errors'
    output.mkdir(mode=0o700,parents=True,exist_ok=True)
    if mode=='publish':
        put(HERE/'OPERATIONAL_ERRORS_STARTED.json',dict(unix=time.time(),process=identity(os.getpid()),
            boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),deadline_unix=DEADLINE,
            schema='R233_UNSCORED_TRANSPORT_ERROR_FEEDBACK_V1',no_scorer_dispatch=True))
    complete = set()
    while time.time()<DEADLINE:
        started = json.loads((HERE/'TRANSPORT_STARTED.json').read_bytes())
        rows=[]
        paths=sorted(Path(started['output']).glob('TRANSPORT_*.json'))
        for path in paths:
            transport=json.loads(path.read_bytes())
            if (transport.get('dispatched') is not False or transport.get('receipt_sha256') is not None
                    or transport.get('error')!='ORIGIN_TRANSPORT_NOT_DISPATCHED'):
                continue
            key=transport['origin']['record_sha256']
            saved_path=output/(key+'.json')
            if key in complete:
                rows.append(json.loads(saved_path.read_bytes()))
                continue
            try:
                value=failure_call(path,started,mode)
                put(saved_path,value)
                rows.append(value)
                if value['result']['status']=='OPERATIONAL_ERROR_INBOX_VERIFIED':
                    complete.add(key)
            except Exception as error:
                value=dict(life=transport['session_id'],origin=transport['origin'],
                    status='REPORTER_FAILURE_NOT_FEEDBACK_SUCCESS',error_type=type(error).__name__,
                    error=str(error)[-1000:],stderr=getattr(error,'stderr','')[-2000:])
                put(output/(key+'.error.json'),value)
                rows.append(value)
        result=dict(unix=time.time(),mode=mode,rows=rows,byte_bound_unchanged=True,
            no_scorer_requests=True,no_target_row_writes=True)
        put(HERE/('BOUNDED_DIAGNOSTICS.json' if mode=='diagnose' else 'OPERATIONAL_ERRORS_LATEST.json'),result)
        print(json.dumps(result),flush=True)
        if once:return
        time.sleep(10)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--diagnose',action='store_true')
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    run('diagnose' if args.diagnose else 'publish',args.once)
