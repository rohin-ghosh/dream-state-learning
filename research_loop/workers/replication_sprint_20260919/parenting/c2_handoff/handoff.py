"""One-shot, CPU-only handoff of the exact September 19 C2 publisher."""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import time
import types


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
REFINEMENT = HERE.parent / 'c2_refinement'
SERVICE = REPO / 'research_loop/workers/post_reboot_c2_p7_20260919'
SEED = REFINEMENT / 'SUPERVISOR_SEED_MANIFEST.json'
INSTALL = REFINEMENT / 'INSTALL_NEXT_SESSION.patch'
CANDIDATE = REFINEMENT / 'candidate.py'
SEED_SHA256 = '14b4a285dda3abcb7ccd9421ccbd8135bd26883cde7cead410e52a56cd073330'
INSTALL_SHA256 = '5a42f5a572b2cdd3bcd80a8d4f43b7c5d1fab8b30b5c93f45eb6c55e45e20c96'
CANDIDATE_SHA256 = '272a614160bf0d15349cf5b8362ef86eb3c3f3900d5f204181ec24a554a63761'
TARGET_RELATIVE = ('research_loop/workers/post_reboot_c2_p7_20260919/'
                   'c2_session_refinement_seed_20260919/MANIFEST.json')
TARGET = REPO / TARGET_RELATIVE
IDENTITY_FIELDS = ('pid', 'start_ticks', 'cwd', 'argv')
PUBLISHER = dict(pid=325487, start_ticks='753205', cwd=str(REPO), argv=[
    '/usr/bin/python3', '-B', str(REPO / 'research_loop/workers/'
    'rohin233_recovery_node4_20260918/checkpoint_tail_parent_strong.py'),
    '--manifest', str(SERVICE / 'c2_session1/MANIFEST.json'), '--manifest-sha256',
    'e633ecae3b71e2e4e901c2f7eceece0374c8190f5c859ab300ee449daa80e753'])
SUPERVISOR = dict(pid=361010, start_ticks='822432', cwd=str(REPO), argv=[
    '/usr/bin/python3', '-B', str(SERVICE / 'c2_service.py')])


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checked_bytes(path, expected):
    content = path.read_bytes()
    require(hashlib.sha256(content).hexdigest() == expected, 'changed_pinned_file:' + str(path))
    return content


def load_bundle():
    seed_bytes = checked_bytes(SEED, SEED_SHA256)
    install_bytes = checked_bytes(INSTALL, INSTALL_SHA256)
    expected_patch = ('*** Begin Patch\n*** Add File: ' + TARGET_RELATIVE + '\n'
                      + ''.join('+' + line + '\n' for line in seed_bytes.decode().splitlines())
                      + '*** End Patch\n').encode()
    require(install_bytes == expected_patch, 'only_exact_seed_addition_allowed')
    seed = json.loads(seed_bytes)
    for key, expected in (('old_parent_must_be_drained_by_owner', PUBLISHER),
                          ('active_CPU_supervisor_must_remain', SUPERVISOR)):
        require(all(seed[key][field] == expected[field] for field in IDENTITY_FIELDS),
                'seed_process_identity_mismatch:' + key)
    validator = types.ModuleType('c2_handoff_pinned_candidate')
    validator.__file__ = str(CANDIDATE)
    exec(compile(checked_bytes(CANDIDATE, CANDIDATE_SHA256), str(CANDIDATE), 'exec'),
         validator.__dict__)
    return seed, seed_bytes, install_bytes, validator


def process_identity(expected):
    process = Path('/proc') / str(expected['pid'])
    before = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    argv = (process / 'cmdline').read_bytes().decode().rstrip('\0').split('\0')
    cwd = os.readlink(process / 'cwd')
    children = (process / 'task' / str(expected['pid']) / 'children').read_text().split()
    after = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    require(before[19] == after[19], 'process_changed_during_proc_read')
    return dict(pid=expected['pid'], start_ticks=after[19], state=after[0],
                cwd=cwd, argv=argv, threads=int(after[17]), children=children)


def exited(descriptor, timeout_ms=0):
    poller = select.poll()
    poller.register(descriptor, select.POLLIN)
    events = poller.poll(timeout_ms)
    require(all(not flags & select.POLLNVAL for _, flags in events), 'invalid_pidfd')
    return bool(events)


def check_process(descriptor, expected, states):
    require(not exited(descriptor), 'bound_process_exited')
    actual = process_identity(expected)
    require(all(actual[field] == expected[field] for field in IDENTITY_FIELDS),
            'process_identity_mismatch:' + str(expected['pid']))
    require(not exited(descriptor), 'bound_process_exited_during_proc_read')
    require(actual['state'] in states, 'process_not_in_required_state:' + str(expected['pid']))
    return actual


@contextmanager
def bound_process(expected):
    descriptor = os.pidfd_open(expected['pid'], 0)
    try:
        check_process(descriptor, expected, ('R', 'S'))
        yield descriptor
    finally:
        os.close(descriptor)


def require_idle(actual):
    require(actual['threads'] == 1 and not actual['children'],
            'publisher_has_threads_or_inflight_child_do_not_handoff')


@contextmanager
def paused_publisher(descriptor):
    """Arm cleanup before STOP, including syscall/interruption uncertainty."""
    handlers = {}
    armed = False
    cleaning = False
    require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'existing_alarm_not_supported')

    def interrupted(number, frame):
        if not cleaning:
            raise InterruptedError('handoff_interrupted_or_stop_budget_expired:' + str(number))

    try:
        for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGALRM):
            handlers[number] = signal.signal(number, interrupted)
        signal.setitimer(signal.ITIMER_REAL, 10.0)
        armed = True
        signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
        yield
    finally:
        cleaning = True
        try:
            if armed:
                try:
                    signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                except ProcessLookupError:
                    pass
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
            for number, handler in handlers.items():
                signal.signal(number, handler)


def wait_stopped(descriptor):
    deadline = time.monotonic() + 1.0
    while True:
        actual = check_process(descriptor, PUBLISHER, ('R', 'S', 'T'))
        if actual['state'] == 'T':
            require_idle(actual)
            return
        require(time.monotonic() < deadline, 'publisher_stop_not_observed')
        time.sleep(0.02)


def check_target(*, installed=False):
    require(not any(path.is_symlink() for path in (TARGET, *TARGET.parents)),
            'seed_install_path_must_not_follow_symlinks')
    if not installed:
        require(not TARGET.exists(), 'seed_already_exists_owner_must_reconcile')


def settled(ledger):
    return not ledger['pending'] and ledger['last_status'] in ('PUBLISHED', 'SILENT')


def inspect_ledger(seed, validator):
    validator.no_question_bank(seed)
    require(time.time() < seed['hard_end_unix'], 'existing_C2_wall_expired')
    return validator.seed_preflight(seed)


def run(*, execute=False, seed_sha256=None, install_sha256=None):
    if execute:
        require(seed_sha256 == SEED_SHA256 and install_sha256 == INSTALL_SHA256,
                'execute_requires_both_exact_approved_hashes')
    require(hasattr(os, 'pidfd_open') and hasattr(signal, 'pidfd_send_signal'),
            'linux_pidfd_required_no_numeric_pid_fallback')
    with Path(__file__).open('rb') as own_lock:
        fcntl.flock(own_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        seed, seed_bytes, install_bytes, validator = load_bundle()
        check_target()
        ledger = inspect_ledger(seed, validator)
        with bound_process(PUBLISHER) as publisher, bound_process(SUPERVISOR) as supervisor:
            require_idle(check_process(publisher, PUBLISHER, ('S',)))
            report = dict(status='DRY_RUN_NOT_AUTHORIZATION' if not execute else 'NOT_READY',
                          settled_current_ledger=settled(ledger), ledger=ledger,
                          seed_sha256=SEED_SHA256, install_sha256=INSTALL_SHA256,
                          native_checked=False, supervisor_signals=[], native_signals=[],
                          older_ledger_reconciliation='still_owned_by_Main')
            if not execute or not settled(ledger):
                return report
            patch_tool = shutil.which('apply_patch')
            require(patch_tool is not None, 'apply_patch_required_no_write_fallback')
            with paused_publisher(publisher):
                wait_stopped(publisher)
                checked_bytes(SEED, SEED_SHA256)
                checked_bytes(INSTALL, INSTALL_SHA256)
                ledger = inspect_ledger(seed, validator)
                require(settled(ledger), 'frozen_ledger_not_settled_no_install_or_term')
                check_process(supervisor, SUPERVISOR, ('R', 'S'))
                require_idle(check_process(publisher, PUBLISHER, ('T',)))
                check_target()
                subprocess.run([patch_tool], input=install_bytes, cwd=REPO, check=True,
                               capture_output=True, timeout=3.0, env={'PATH': '/usr/bin:/bin'})
                check_target(installed=True)
                require(TARGET.read_bytes() == seed_bytes, 'installed_seed_bytes_mismatch')
                after = inspect_ledger(seed, validator)
                require(settled(after) and after['signature'] == ledger['signature'],
                        'frozen_ledger_changed_after_install_owner_must_reconcile')
                check_process(supervisor, SUPERVISOR, ('R', 'S'))
                require_idle(check_process(publisher, PUBLISHER, ('T',)))
                signal.pidfd_send_signal(publisher, signal.SIGTERM)
            report.update(status='OLD_PUBLISHER_TERM_REQUESTED', ledger=after,
                          old_publisher_exit_observed=exited(publisher, 2000),
                          successor_verified=False)
            return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--execute', action='store_true')
    mode.add_argument('--dry-run', action='store_true')
    parser.add_argument('--seed-sha256', choices=[SEED_SHA256])
    parser.add_argument('--install-sha256', choices=[INSTALL_SHA256])
    arguments = parser.parse_args(argv)
    if arguments.execute and not (arguments.seed_sha256 and arguments.install_sha256):
        parser.error('--execute requires both exact reviewed --seed-sha256 and --install-sha256')
    try:
        report = run(execute=arguments.execute, seed_sha256=arguments.seed_sha256,
                     install_sha256=arguments.install_sha256)
    except (Exception, KeyboardInterrupt) as error:
        print(json.dumps(dict(status='REFUSED_OR_INTERRUPTED', error=str(error),
                              error_type=type(error).__name__,
                              inspect_seed_install_before_any_retry=True)))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0 if report['settled_current_ledger'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
