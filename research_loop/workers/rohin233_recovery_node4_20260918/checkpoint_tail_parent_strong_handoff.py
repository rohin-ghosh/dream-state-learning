"""Exact idle CPU-only R233 parent handoff, with a preserved predecessor."""

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

from checkpoint_tail_parent_current import refresh
from checkpoint_tail_parent_strong import STYLE, validate_manifest
from deadline_resume import identity, read, sha, write
from renew_c2_cpu import remote, PYTHON


OWN = Path(__file__).resolve().parent
REPO = OWN.parents[2]
OLD_MANIFEST = OWN / 'private/checkpoint_tail_v_correction/CHECKPOINT_TAIL_PARENT_MANIFEST.json'
PREPARED = OWN / 'private/checkpoint_tail_parent_r233_control'
OUTPUT = OWN / 'private/checkpoint_tail_parent_r233'
PID = 4078280
START_TICKS = '187226679'


def prepare():
    previous = read(OLD_MANIFEST)
    old_config = read(previous['config_path'])
    old_output = Path(previous['output'])
    if read(old_output / 'STARTED.json')['pid'] != PID:
        raise ValueError('bound_predecessor_started_identity')
    PREPARED.mkdir(exist_ok=False)
    config = dict(old_config, parent_style=STYLE, cadence_label='PERSISTENT', minimum_duration_seconds=3600,
        predecessor_output=str(old_output), predecessor_started_sha256=sha(old_output / 'STARTED.json'))
    config_path = PREPARED / 'CONFIG.json'
    write(config_path, config)
    brief = OWN / 'CHECKPOINT_TAIL_PARENT_R233_BRIEF.md'
    pins = dict(previous['local_source_sha256'])
    for path in (config_path, brief, Path(__file__), OWN / 'checkpoint_tail_parent_strong.py',
            OWN / 'checkpoint_tail_parent_current.py'):
        pins[str(path)] = sha(path)
    manifest = dict(previous, config_path=str(config_path), predecessor_config_path=previous['config_path'],
        output=str(OUTPUT), policy_addendum=str(brief), local_source_sha256=pins,
        status='PREPARED_R233_PARENT_ONLY_NOT_ACTIVATED', explicit_parent_treatment='R233_STRONG_ARTIFACT',
        source_transform='pinned r202 source: remove only obsolete V=3 publication prohibition',
        old_parent_must_be_drained_by_owner=dict(pid=PID, start_ticks=START_TICKS))
    path = PREPARED / 'MANIFEST.json'
    write(path, manifest)
    validate_manifest(manifest)
    return path


def stop_idle():
    manifest = read(OLD_MANIFEST)
    output = Path(manifest['output'])
    expected = ['/usr/bin/python3', '-B', str(OWN / 'checkpoint_tail_parent_continue.py'),
        '--manifest', str(OLD_MANIFEST), '--manifest-sha256', sha(OLD_MANIFEST)]
    descriptor = os.pidfd_open(PID)
    try:
        until = time.monotonic() + 120
        while time.monotonic() < until:
            actual = identity(PID)
            if (actual['start_ticks'] != START_TICKS or actual['argv'] != expected
                    or actual['uid'] != os.getuid() or actual['cwd'] != str(REPO)):
                raise ValueError('exact_idle_owned_CPU_parent_only')
            process = Path('/proc') / str(PID)
            attempts = sorted(output.glob('parent_*/SOURCE.json'))
            settled = not attempts or (attempts[-1].parent / 'RESULT.json').exists()
            children = (process / 'task' / str(PID) / 'children').read_text().strip()
            if settled and not children and (process / 'wchan').read_text().strip() == 'hrtimer_nanosleep':
                signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                poller = select.poll()
                poller.register(descriptor, select.POLLIN)
                if not poller.poll(10000):
                    raise RuntimeError('owned_CPU_parent_exit_not_confirmed_no_successor')
                return dict(identity=actual, exited_unix=time.time(), signal='EXACT_IDLE_CPU_PIDFD_SIGTERM',
                    settled=True, native_signals=[])
            time.sleep(.1)
        raise TimeoutError('CPU_parent_not_idle_no_signal')
    finally:
        os.close(descriptor)


def activate(path):
    manifest = read(path)
    config = validate_manifest(manifest)
    verify = ('import sys;sys.path.insert(0,' + repr(manifest['remote_operator']) + ');'
        'from checkpoint_tail_parent_binding import verify;verify(' + repr(config['native_binding_path'])
        + ',' + repr(config['native_binding_sha256']) + ');')
    remote(PYTHON + ' -B -', verify)
    write(PREPARED / 'INTENT.json', dict(observed_unix=time.time(), manifest_sha256=sha(path),
        exact_CPU_predecessor=dict(pid=PID, start_ticks=START_TICKS), native_signals=[], retry=False))
    retired = stop_idle()
    write(PREPARED / 'PREDECESSOR_DRAINED.json', retired)
    with (OWN / 'private/C2_WAIT_CONTROLLER.lock').open('a') as controller:
        fcntl.flock(controller.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    with (PREPARED / 'CPU_PARENT.log').open('x') as log:
        child = subprocess.Popen([sys.executable, '-B', str(OWN / 'checkpoint_tail_parent_strong.py'),
            '--manifest', str(path), '--manifest-sha256', sha(path)], cwd=REPO,
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    write(PREPARED / 'SPAWNED.json', dict(pid=child.pid, observed_unix=time.time(), native_signals=[]))
    until = time.monotonic() + 60
    while not (OUTPUT / 'STARTED.json').exists():
        if child.poll() is not None or time.monotonic() > until:
            raise RuntimeError('START_not_confirmed_inspect_log_no_automatic_retry')
        time.sleep(.25)
    started = read(OUTPUT / 'STARTED.json')
    if started['pid'] != child.pid:
        raise ValueError('actual_new_parent_START')
    actual = identity(child.pid)
    write(OWN / 'CHECKPOINT_TAIL_PARENT_R233_STARTED.public.json', dict(
        observed_utc=datetime.now(timezone.utc).isoformat(),
        parent=dict(pid=actual['pid'], start_ticks=actual['start_ticks']),
        started_utc=datetime.fromtimestamp(started['started_unix'], timezone.utc).isoformat(),
        started_receipt_sha256=sha(OUTPUT / 'STARTED.json'), config_sha256=sha(Path(manifest['config_path'])),
        manifest_sha256=sha(path), policy_sha256=sha(Path(manifest['policy_addendum'])),
        hard_end_unix=config['hard_end_unix'], cadence_responses=config['cadence_responses'],
        explicit_treatment='R233_STRONG_ARTIFACT', predecessor=dict(pid=PID, start_ticks=START_TICKS,
            exited_unix=retired['exited_unix']), original_provider_ledger_cursor_preserved=True,
        correction_already_queued_no_duplicate=True, native_signals=[], new_render_pending=True))
    print(json.dumps(refresh(path, 'R233_CPU_PARENT_ACTUAL_START_CORRECTION_RENDER_PENDING'), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--activate', action='store_true')
    options = parser.parse_args()
    path = PREPARED / 'MANIFEST.json'
    if options.activate:
        activate(path)
    else:
        print(prepare())
