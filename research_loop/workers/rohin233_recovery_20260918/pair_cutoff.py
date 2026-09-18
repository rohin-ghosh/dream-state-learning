"""Enforce the existing learner lease cutoff without pausing or editing its state."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import time


PID = 399101
START_TICKS = '9637168'
OWNER_UID = 1352
SAFE_END = 1789754400
TERM_AT = SAFE_END - 20
GRACE = 5
ROOT = Path('/localhome/local-rohing/orch_r231_curriculum_birth_20260918')
GUARD = ROOT / 'recovery_20260918T1646Z/control/GUARD.json'
GUARD_SHA = 'e7b8fe9f94329ca41738fb843291ba06e108ed7846cb27316c144aa56979b539'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate_policy(plan, now):
    require(plan['physical'] == 0 and plan['root'] == str(ROOT / 'raw'), 'exact_learner_only')
    require(plan['lease_end_unix'] - SAFE_END >= 21600, 'six_hour_margin_required')
    require(now < TERM_AT and TERM_AT + GRACE < SAFE_END, 'guard_armed_before_cutoff')


def identity():
    process = Path('/proc') / str(PID)
    require(process.stat().st_uid == OWNER_UID, 'exact_native_owner')
    require(process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()[19]
            == START_TICKS, 'exact_native_start')
    command = process.joinpath('cmdline').read_bytes().split(b'\0')
    require(b'gpu.r232_recovery' in command and b'native' in command
            and str(GUARD).encode() in command, 'exact_native_guard_command')


def wait_and_finish(descriptor, deadline, emit, clock=time.time, sleeper=time.sleep,
                    sender=signal.pidfd_send_signal, waiter=select.select):
    while clock() < deadline:
        if waiter([descriptor], [], [], 0)[0]:
            emit(dict(kind='NATIVE_EXITED_BEFORE_CUTOFF', observed_unix=clock()))
            return
        sleeper(min(2, max(0, deadline - clock())))
    if waiter([descriptor], [], [], 0)[0]:
        emit(dict(kind='NATIVE_EXITED_BEFORE_CUTOFF', observed_unix=clock()))
        return
    try:
        sender(descriptor, signal.SIGTERM)
    except ProcessLookupError:
        emit(dict(kind='NATIVE_EXITED_BEFORE_CUTOFF', observed_unix=clock()))
        return
    emit(dict(kind='LEASE_CUTOFF_TERM', observed_unix=clock(), signal='SIGTERM'))
    exited = bool(waiter([descriptor], [], [], GRACE)[0])
    if not exited:
        try:
            sender(descriptor, signal.SIGKILL)
            emit(dict(kind='LEASE_CUTOFF_KILL', observed_unix=clock(), signal='SIGKILL'))
        except ProcessLookupError:
            pass
        exited = bool(waiter([descriptor], [], [], 10)[0])
    emit(dict(kind='LEASE_CUTOFF_ENFORCED' if exited else 'SIGNALS_SENT_EXIT_UNCONFIRMED',
              observed_unix=clock(), exit_confirmed=exited,
              resident_unsaved_state_retention_claim=False))


def main():
    os.umask(0o077)
    require(sha(GUARD) == GUARD_SHA, 'unchanged_admitted_guard')
    guard = json.loads(GUARD.read_text())
    require(sha(guard['plan_path']) == guard['plan_sha256'], 'unchanged_admitted_plan')
    plan = json.loads(Path(guard['plan_path']).read_text())
    validate_policy(plan, time.time())
    identity()
    output = ROOT / 'r233_main_cutoff'
    output.mkdir(exist_ok=True)
    lock = (output / 'WRITER.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    descriptor = os.pidfd_open(PID)
    identity()
    os.kill(PID, 0)

    def emit(event):
        with (output / 'EVENTS.jsonl').open('a') as stream:
            stream.write(json.dumps(event, sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())

    receipt = dict(kind='ARMED_NO_PAUSE', observed_unix=time.time(),
        guard_pid=os.getpid(), guard_start_ticks=Path('/proc/self/stat').read_text().rsplit(') ', 1)[1].split()[19],
        native_pid=PID, native_start_ticks=START_TICKS, source_sha256=sha(__file__),
        admitted_guard_sha256=GUARD_SHA, term_at_unix=TERM_AT,
        kill_grace_seconds=GRACE, safe_end_unix=SAFE_END,
        required_lease_margin_seconds=21600, runtime_or_journal_writes=False,
        native_signals_at_arming=[], checkpoints_untouched=True)
    with (output / 'ARMED.json').open('x') as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    emit(receipt)
    try:
        wait_and_finish(descriptor, TERM_AT, emit)
    finally:
        os.close(descriptor)


if __name__ == '__main__':
    main()
