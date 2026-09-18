"""Add the journal-only private mount to the existing R181 boundary operator."""

import argparse
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import time

import r181_boundary as original

JOURNAL = 'gpu/orch_r125_stream_journal.py'
original_command = original.command
original_cpu = original.cpu
original_write = original.write


def command(folder, action, *, cpu=False):
    result = original_command(folder, action, cpu=cpu)
    plan = original.read(folder / 'PLAN.json')
    prefix = '--property=BindReadOnlyPaths='
    position = next(index for index, value in enumerate(result) if value.startswith(prefix))
    result[position] += ' ' + str(folder / 'new_journal.py') + ':' + str(Path(plan['source_root']) / JOURNAL)
    position = result.index(str(Path(original.__file__).resolve()))
    result[position] = str(Path(__file__).resolve())
    return result


def cpu(folder):
    original_cpu(folder)
    from gpu import orch_r125_stream_journal as journal
    original.require(original.sha(journal.__file__) == original.sha(folder / 'new_journal.py'), 'actual_journal_overlay')
    print(json.dumps(dict(status='PASS', actual_journal=journal.__file__, source_sha256=original.sha(journal.__file__))))


def preserved_write(path, document):
    path = Path(path)
    if path.name == 'WAIT_STARTED.json':
        path = path.with_name('JOURNAL_WAIT_STARTED.json')
        document = dict(document, journal_wrapper_sha256=original.sha(__file__),
            actual_guard_sha256=original.sha(path.parent / 'GUARD.json'))
    original_write(path, document)


def retire(folder):
    original.require(not (folder / 'BOUNDARY.json').exists(), 'no_claimed_native_boundary')
    spec = original.read(folder / 'LIVE_HANDOFF.json')
    spawned = original.read(folder / 'WAITER_SPAWNED.json')
    expected = original.identity(spawned['pid'])
    original.require(expected['argv'] == [original.PYTHON, '-B', str(Path(original.__file__).resolve()),
        'wait', '--physical', str(spec['physical'])] and expected['uid'] == os.getuid(), 'exact_old_owned_waiter')
    descriptor = os.pidfd_open(expected['pid'])
    stopped = False
    retired = False
    try:
        original.exact(expected)
        signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
        stopped = True
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            state = Path('/proc', str(expected['pid']), 'stat').read_text().rsplit(') ', 1)[1].split()[0]
            if state in ('T', 't'):
                break
            time.sleep(.01)
        else:
            raise ValueError('waiter_pause_confirmation')
        original.exact(spec['identity'])
        actor_state = Path('/proc', str(spec['identity']['pid']), 'stat').read_text().rsplit(') ', 1)[1].split()[0]
        original.require(actor_state not in ('T', 't', 'Z', 'X') and not (folder / 'BOUNDARY.json').exists()
            and original.head(spec['backing_root'])['kind'] == 'UPDATE', 'native_continues_unsaved_no_handoff_race')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        original.require(bool(select.select([descriptor], [], [], 20)[0]), 'old_waiter_exited')
        retired = True
        original_write(folder / 'NATIVE_ONLY_WAITER_RETIRED.json', dict(identity=expected,
            observed_unix=time.time(), native_signals=0, reason='add_Main_journal_cache_to_unlaunched_successor'))
    finally:
        if stopped and not retired:
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
        os.close(descriptor)


def validate(folder):
    original.require((folder / 'NATIVE_ONLY_WAITER_RETIRED.json').exists(), 'quiet_staged_configuration')
    config = original.read(folder / 'GUARD.json')
    previous = original.read(folder / 'GUARD_NATIVE_ONLY.json')
    normalized = dict(config, source_pins=dict(config['source_pins']))
    normalized['source_pins'][JOURNAL] = previous['source_pins'][JOURNAL]
    original.require(normalized == previous and config['source_pins'][JOURNAL] == original.sha(folder / 'new_journal.py'),
        'one_journal_pin_only_native_plan_guard_preserved')
    result = subprocess.run(command(folder, 'cpu', cpu=True), capture_output=True, text=True, timeout=90)
    original.require(result.returncode == 0, 'actual_two_file_overlay_guard:' + result.stderr[-500:])
    original_write(folder / 'JOURNAL_SOURCE_BOUND.json', dict(status='ACTUAL_TWO_FILE_OVERLAY_GUARD_VALIDATED',
        guard_sha256=original.sha(folder / 'GUARD.json'), native_sha256=original.sha(folder / 'new_native.py'),
        journal_sha256=original.sha(folder / 'new_journal.py'), wrapper_sha256=original.sha(__file__),
        observed_unix=time.time(), output=result.stdout, native_signals=0))


def wait(folder):
    bound = original.read(folder / 'JOURNAL_SOURCE_BOUND.json')
    original.require(bound['guard_sha256'] == original.sha(folder / 'GUARD.json')
        and bound['wrapper_sha256'] == original.sha(__file__), 'exact_next_boundary_binding')

    def interrupted(signum, frame):
        raise SystemExit('owned_waiter_interrupted_restore_quiesced_native')

    handlers = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGTERM, signal.SIGHUP)}
    try:
        original.wait(folder)
    finally:
        for signum, handler in handlers.items():
            signal.signal(signum, handler)


def install():
    original.command = command
    original.cpu = cpu
    original.write = preserved_write


if __name__ == '__main__':
    install()
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('retire', 'validate', 'wait', 'cpu', 'contained'))
    parser.add_argument('--physical', type=int, choices=(0, 1, 2, 3, 4, 7), required=True)
    args = parser.parse_args()
    original.require(socket.gethostname() == '[REDACTED_HOST]', 'node3_only')
    folder = original.HERE / 'r181' / ('physical' + str(args.physical))
    try:
        if args.action == 'contained':
            original.contained(folder)
        else:
            globals()[args.action](folder)
    except BaseException as error:
        name = args.action.upper() + '_FAILED.json'
        if not (folder / name).exists():
            original_write(folder / name, dict(error_type=type(error).__name__, reason=str(error)[:500], observed_unix=time.time()))
        raise
