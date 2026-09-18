"""Exact-PID CPU enrollment handoff; no native, scorer or probe controls."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from research_loop.workers.rohin233_ovx4_recovery_20260918 import lease_admission_enroll as successor


WORKER = Path(__file__).resolve().parent
REPO = WORKER.parents[2]
PREVIOUS = WORKER.parent/'rohin233_kept_age_probe_20260918'
RUNTIME = Path('/tmp/r233-enrollment-admission-20260918T1909Z')
OLD_PID = 3046824
OLD_START = 186067621
OLD_ARGS = ['python3','-B','-m','research_loop.workers.rohin233_ovx4_recovery_20260918.lease_enroll']


def process(pid):
    root = Path('/proc',str(pid))
    tail = (root/'stat').read_text().rsplit(')',1)[1].split()
    command = (root/'cmdline').read_bytes()
    return dict(pid=pid,ppid=int(tail[1]),state=tail[0],start_ticks=int(tail[19]),
                args=[value.decode() for value in command.split(b'\0') if value],
                command_sha256=hashlib.sha256(command).hexdigest())


def verify_old(item):
    if item['pid'] != OLD_PID or item['start_ticks'] != OLD_START or item['args'] != OLD_ARGS:
        raise ValueError('only_exact_previous_cpu_enrollment_may_be_replaced')


def write_once(path, payload):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    with path.open('xb') as stream:
        os.fchmod(stream.fileno(),0o600)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return dict(path=str(path.resolve()),sha256=hashlib.sha256(payload).hexdigest())


def document(path, value):
    return write_once(path,(json.dumps(value,sort_keys=True,indent=2)+'\n').encode())


def main():
    os.umask(0o077)
    RUNTIME.mkdir(mode=0o700,exist_ok=False)
    verify_old(process(OLD_PID))
    driver = write_once(RUNTIME/'source/driver.py',Path(successor.__file__).read_bytes())
    reader = write_once(RUNTIME/'source/enroll.py',(PREVIOUS/'enroll.py').read_bytes())
    compile(Path(driver['path']).read_bytes(),driver['path'],'exec')
    compile(Path(reader['path']).read_bytes(),reader['path'],'exec')
    definitions = [('enrollment','REGISTRATION.json'),('extra_enrollment','EXTRA_REGISTRATION.json')]
    for directory, filename in definitions:
        registration = json.loads((PREVIOUS/'private'/filename).read_bytes())
        for target in registration['targets']:
            successor.admission(target,time.time())
        json.loads((PREVIOUS/directory/'private/STATE.json').read_bytes())
    until = time.time()+50
    while True:
        verify_old(process(OLD_PID))
        children = Path('/proc',str(OLD_PID),'task',str(OLD_PID),'children').read_text().strip()
        sleeping = Path('/proc',str(OLD_PID),'wchan').read_text().strip() == 'hrtimer_nanosleep'
        if not children and sleeping:
            break
        if time.time() >= until:
            raise TimeoutError('leave_existing_enrollment_running_if_not_quiescent')
        time.sleep(.05)
    descriptor = os.pidfd_open(OLD_PID)
    try:
        old = process(OLD_PID)
        verify_old(old)
        terminated = time.time()
        signal.pidfd_send_signal(descriptor,signal.SIGTERM)
    finally:
        os.close(descriptor)
    until = time.time()+10
    while Path('/proc',str(OLD_PID)).exists():
        if time.time() >= until:
            raise TimeoutError('prior_enrollment_not_exited_no_second_writer')
        time.sleep(.05)
    old_exit = time.time()
    locks, ledgers = [], []
    for directory, filename in definitions:
        output = PREVIOUS/directory
        lock = (output/'ENROLL.lock').open('a')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        locks.append(lock)
        state = write_once(RUNTIME/'preserved'/f'{directory}.private.json',
                           (output/'private/STATE.json').read_bytes())
        registration_path = PREVIOUS/'private'/filename
        registration = dict(path=str(registration_path),sha256=successor.checksum(registration_path))
        ledgers.append(dict(output=str(output),state_sha256=state['sha256'],
                            state_snapshot=state,registration=registration))
    config = dict(repo=str(REPO),support_root=str(WORKER),receipt_root=str(RUNTIME/'receipts'),
                  deadline_unix=successor.SERVICE_END,driver_sha256=driver['sha256'],reader=reader,
                  ledgers=ledgers,wrappers_sha256={wrapper:successor.checksum(REPO/'gpu'/wrapper)
                                                for wrapper in successor.SOURCE_DAYS})
    config_ref = document(RUNTIME/'CONFIG.private.json',config)
    (RUNTIME/'receipts').mkdir(mode=0o700)
    document(RUNTIME/'PREDECESSOR_EXIT.json',dict(unix=old_exit,old_pid=OLD_PID,
        old_start_ticks=OLD_START,old_command_sha256=old['command_sha256'],signal='SIGTERM_TO_EXACT_CPU_ENROLLER_ONLY',
        quiescent_no_children=True,signal_unix=terminated,ledgers=ledgers,native_signals=[],probe_dispatches=0))
    for lock in locks:
        lock.close()
    with (RUNTIME/'enrollment.log').open('ab') as log:
        command = ['timeout','--signal=TERM','--kill-after=5',str(int(successor.SERVICE_END-time.time())),
                   'python3','-B',driver['path'],'--config',config_ref['path']]
        child = subprocess.Popen(command,cwd=REPO,stdin=subprocess.DEVNULL,
                                 stdout=log,stderr=log,start_new_session=True)
    document(RUNTIME/'DISPATCHED.json',dict(unix=time.time(),outer_pid=child.pid,
        outer_start_ticks=process(child.pid)['start_ticks'],deadline_unix=successor.SERVICE_END,
        config_sha256=config_ref['sha256'],driver_sha256=driver['sha256'],reader_sha256=reader['sha256'],
        predecessor_pid=OLD_PID,predecessor_exit_unix=old_exit,native_signals=[],new_evaluations=0))
    until = time.time()+60
    while not (RUNTIME/'receipts/FIRST_CYCLE.json').exists():
        if child.poll() is not None:
            raise RuntimeError('successor_exited_inspect_preserved_local_log')
        if time.time() >= until:
            raise TimeoutError('successor_dispatched_first_cycle_not_yet_observed')
        time.sleep(.1)
    loaded = json.loads((RUNTIME/'receipts/LOADED.json').read_bytes())
    first = json.loads((RUNTIME/'receipts/FIRST_CYCLE.json').read_bytes())
    current = process(loaded['pid'])
    receipt = dict(unix=time.time(),schema='R233_ENROLLMENT_SOURCE_LEASE_REPAIR_V1',
        status='ACTUAL_LOADED_AND_FIRST_CYCLE_VERIFIED',actual_host_alias='operator_vm',
        predecessor_pid=OLD_PID,predecessor_start_ticks=OLD_START,predecessor_exit_unix=old_exit,
        actual_pid=loaded['pid'],actual_start_ticks=current['start_ticks'],actual_state=current['state'],
        outer_pid=child.pid,loaded_unix=loaded['unix'],metadata_handoff_gap_seconds=loaded['unix']-old_exit,
        actual_deadline_utc=successor.utc(successor.SERVICE_END),config_sha256=config_ref['sha256'],
        driver_sha256=driver['sha256'],reader_sha256=reader['sha256'],
        preserved_state_sha256=loaded['preserved_state_sha256'],preserved_entries=loaded['preserved_entries'],
        current_enrolled=first['enrolled'],same_registered_roots=16,
        registration_sha256=[ledger['registration']['sha256'] for ledger in ledgers],
        historical_entries_unchanged=first['historical_entries_unchanged'],cursor_regressions=first['cursor_regressions'],
        source_admission_policy=successor.POLICY,target_admission=loaded['target_admission'],
        first_cycle_rows=first['rows'],native_signals=[],scorer_signals=[],new_evaluations=0,
        backlog_dispatcher_started=False,preserved_snapshots_private=True)
    document(RUNTIME/'VERIFIED.json',receipt)
    document(WORKER/'LEASE_ADMISSION_RENEWED.json',receipt)
    print(json.dumps({key:receipt[key] for key in ['status','actual_pid','outer_pid','loaded_unix',
        'metadata_handoff_gap_seconds','preserved_entries','current_enrolled','historical_entries_unchanged',
        'cursor_regressions','new_evaluations']}))


if __name__ == '__main__':
    main()
