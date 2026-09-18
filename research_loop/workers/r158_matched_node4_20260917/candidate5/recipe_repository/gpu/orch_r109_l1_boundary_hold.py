"""Hold an observed complete generation boundary for its existing owner guard."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time


ROOT=Path('/localhome/local-rohing/orch_r109_l1_20260915')


def complete(directory):
    progress=json.loads((directory/'PROGRESS.json').read_text())
    count=progress['calls']
    return (not (directory/f'INTENT_{count+1:06d}.json').exists()
            and (directory/f'CALL_{count:06d}.json').exists()
            and not list(directory.glob('FAILED_*.json'))),progress


def hold(index):
    from gpu.orch_r109_l1_ops import identity
    from gpu.orch_r109_l1_train import write
    assert index in (5,6)
    launch=json.loads((ROOT/f'generation_{index}_LAUNCH.json').read_text())
    expected=launch['identity']
    assert expected['uid']==os.getuid() and identity(expected['pid'])==expected
    directory=ROOT/'generation'/f'gpu{index}'
    release=ROOT/'experience_c1'/f'RELEASE_{index}.json'
    output=ROOT/'experience_c1'/f'BOUNDARY_HOLD_{index}.json'
    deadline=min(time.time()+120,1789490460)
    descriptor=os.pidfd_open(expected['pid'])
    holding=False
    try:
        while time.time()<deadline and not release.exists():
            assert identity(expected['pid'])==expected
            candidate,progress=complete(directory)
            if candidate:
                signal.pidfd_send_signal(descriptor,signal.SIGSTOP)
                holding=True
                candidate,after=complete(directory)
                if candidate and after==progress:
                    write(output,dict(identity=expected,index=index,progress=progress,
                        only_observed_complete_boundary_paused=True,owner_guard_performs_retirement=True,
                        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),observed_unix=time.time()))
                    while time.time()<deadline and not release.exists():
                        assert identity(expected['pid'])==expected
                        candidate,current=complete(directory)
                        if not candidate or current!=progress:break
                        signal.pidfd_send_signal(descriptor,signal.SIGSTOP)
                        time.sleep(.002)
                    if release.exists():return
                signal.pidfd_send_signal(descriptor,signal.SIGCONT)
                holding=False
            time.sleep(.0005)
    except (FileNotFoundError,ProcessLookupError):
        assert release.exists(),'unexpected_owned_generator_exit'
    finally:
        if holding and not release.exists():
            try:signal.pidfd_send_signal(descriptor,signal.SIGCONT)
            except ProcessLookupError:pass
        os.close(descriptor)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--index',type=int,required=True)
    hold(parser.parse_args().index)
