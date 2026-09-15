"""Retire only an owned admission controller proven never to have launched."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def identity(directory):
    return dict(pid=int(directory.name),uid=directory.stat().st_uid,
        start_ticks=(directory/'stat').read_text().rsplit(')',1)[1].split()[19],
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        command_sha256=hashlib.sha256((directory/'cmdline').read_bytes()).hexdigest())


def matches(arguments,root,lane):
    return arguments[-7:]==['-m','gpu.orch_r109_route_run','guard','--root',str(root),'--lane',lane]


def retire(root,lane,pid):
    campaign=root/('campaign_'+lane)
    assert str(root).startswith('/localhome/local-rohing/orch_r109_route_20260915_')
    assert not (root/'RESERVATIONS.jsonl').exists() and not (campaign/'LAUNCH.json').exists()
    if (campaign/'TERMINAL.json').exists():
        print(json.dumps(dict(already_terminal=True,lane=lane)))
        return
    directory=Path('/proc')/str(pid)
    before=identity(directory)
    arguments=[value.decode() for value in (directory/'cmdline').read_bytes().split(b'\0') if value]
    assert before['uid']==os.getuid() and matches(arguments,root,lane)
    assert before==identity(directory)
    os.kill(pid,signal.SIGSTOP)
    stopped=False
    try:
        for attempt in range(100):
            if (directory/'stat').read_text().rsplit(')',1)[1].split()[0] in ('T','t'):
                stopped=True
                break
            time.sleep(.01)
        assert stopped and before==identity(directory)
        assert not (campaign/'LAUNCH.json').exists() and not (root/'RESERVATIONS.jsonl').exists()
        for process in Path('/proc').glob('[0-9]*'):
            try:
                arguments=[value.decode() for value in (process/'cmdline').read_bytes().split(b'\0') if value]
                assert not ('gpu.orch_r109_route_run' in arguments and 'native' in arguments and str(root) in arguments)
            except (FileNotFoundError,ProcessLookupError,PermissionError):
                continue
        assert before==identity(directory)
        os.kill(pid,signal.SIGTERM)
    finally:
        if directory.exists():
            os.kill(pid,signal.SIGCONT)
    for attempt in range(100):
        if not directory.exists() or (directory/'stat').read_text().rsplit(')',1)[1].split()[0]=='Z':
            break
        time.sleep(.05)
    assert not directory.exists() or (directory/'stat').read_text().rsplit(')',1)[1].split()[0]=='Z'
    receipt=dict(status='FAILED',reason='OWNED_ADMISSION_CONTROLLER_RETIRED_ZERO_NATIVE',
        identity=before,native_calls=0,parent_calls=0,finished_unix=time.time(),source_sha256=SOURCE_SHA)
    for name in ('ADMISSION_RETIRE.json','TERMINAL.json'):
        with (campaign/name).open('x') as stream:
            json.dump(receipt,stream,sort_keys=True,indent=2)
    print(json.dumps(receipt))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--lane',required=True)
    parser.add_argument('--pid',type=int,required=True)
    parser.add_argument('--source-sha',required=True)
    options=vars(parser.parse_args())
    SOURCE_SHA=options.pop('source_sha')
    retire(**options)
