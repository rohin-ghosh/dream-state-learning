"""Exact R169 parent-only quiet-boundary custody. Never signal a child."""

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import select
import signal
import time

from inventory_node1 import HERE, REFRESH_SUFFIX, Reader, digest, identity, ledger, require, unchanged
from stage_node1 import reserved_cursor


def write(path, document):
    with Path(path).open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())


def validate_owner(row, current):
    require(row['physical'] in range(0, 2), 'two_explicit_R178_frozen_parents_only')
    expected = row['old_parent']
    require(expected['uid'] == os.getuid() and unchanged(expected, current), 'exact_parent_owner')
    require(any(argument.endswith(REFRESH_SUFFIX) for argument in current['argv'][:5])
            and '--binding' in current['argv'], 'known_actual_r169_parent_only')
    require(current['argv'][current['argv'].index('--binding') + 1] == row['old_parent_binding']['path'],
            'actual_parent_binding_path')
    require(current['state'] not in ('Z', 'X'), 'live_parent_owner')


def transport_children(pid):
    children = set()
    for path in (Path('/proc') / str(pid) / 'task').glob('*/children'):
        children.update(path.read_text().split())
    return sorted(children)


def validate_pins(references):
    reader = Reader()
    for reference in references:
        require(digest(reader.raw(reference['path'])) == reference['sha256'], 'exact_admitted_parent_bytes')


def settled_manifest(row):
    reader = Reader()
    binding, reference = reader.document(row['old_parent_binding']['path'])
    require(reference['sha256'] == row['old_parent_binding']['sha256'], 'unchanged_old_binding')
    config, config_ref = reader.document(binding['config'])
    require(config_ref['sha256'] == binding['config_sha256']
            and config['root'] == row['root'] and binding['output'] == row['old_output'],
            'same_current_parent_life_and_config')
    started, started_ref = reader.document(Path(row['old_output']) / 'STARTED.json')
    require(started['pid'] == row['old_parent']['pid']
            and started['config_sha256'] == config_ref['sha256'], 'actual_old_parent_started')
    attempts = ledger(row['old_output'], reader)
    require(all(attempt['settled'] for attempt in attempts), 'unsettled_parent_attempt')
    cursor = reserved_cursor(dict(reserved_cursor_at_start=binding['cursor'], attempts=attempts))
    pending = [attempt['publication'] for attempt in attempts if attempt.get('status') == 'PUBLISHED'
               and 'DELIVERED.json' not in attempt]
    return dict(reserved_response_count=cursor, pending_publications=pending,
                started=started_ref, attempts=attempts, config=config_ref,
                original_output=row['old_output'], root=row['root'], old_parent=row['old_parent'])


class PausedParent:
    def __init__(self, row, directory, descriptor, manifest, references):
        self.row = row
        self.directory = directory
        self.descriptor = descriptor
        self.manifest = manifest
        self.references = references
        self.terminated = False
        self.stopped = True

    def retire(self):
        require(self.stopped and not self.terminated, 'paused_parent_retirement_once')
        validate_owner(self.row, identity(Path('/proc') / str(self.row['old_parent']['pid'])))
        validate_pins(self.references)
        require(not transport_children(self.row['old_parent']['pid']), 'no_parent_transport_at_retirement')
        require(settled_manifest(self.row) == self.manifest, 'quiet_ledger_still_exact')
        write(self.directory / 'RETIRE_OLD_PARENT_ONCE.json', dict(
            parent_pid=self.row['old_parent']['pid'], parent_ticks=self.row['old_parent']['ticks'],
            observed_unix=time.time(), child_signals=0,
            manifest_sha256=digest(json.dumps(self.manifest, sort_keys=True).encode())))
        signal.pidfd_send_signal(self.descriptor, signal.SIGTERM)
        self.terminated = True
        signal.pidfd_send_signal(self.descriptor, signal.SIGCONT)
        self.stopped = False
        require(bool(select.select([self.descriptor], [], [], 20)[0]), 'old_parent_exit_before_successor')
        write(self.directory / 'OLD_PARENT_EXITED.json', dict(observed_unix=time.time(), child_signals=0))


@contextmanager
def quiet_parent(row, directory, admitted_references, timeout=180):
    directory = Path(directory)
    require(directory.resolve().is_relative_to(HERE.resolve()) and directory.is_dir(), 'own_custody_output')
    require(type(timeout) in (int, float) and 0 < timeout <= 600, 'bounded_parent_quiet_wait')
    require(admitted_references, 'successor_cpu_source_admission_required_before_pause')
    validate_pins(admitted_references)
    process = Path('/proc') / str(row['old_parent']['pid'])
    current = identity(process)
    validate_owner(row, current)
    require(current['state'] not in ('T', 't'), 'do_not_take_over_external_pause')
    lock = os.open(directory / 'CUSTODY.lock', os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    descriptor = None
    handle = None
    stopped = False
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not (directory / 'RETIRE_OLD_PARENT_ONCE.json').exists(), 'never_replay_parent_retirement')
        descriptor = os.pidfd_open(row['old_parent']['pid'])
        deadline = time.monotonic() + timeout
        while True:
            validate_owner(row, identity(process))
            signal.pidfd_send_signal(descriptor, signal.SIGSTOP)
            stopped = True
            try:
                for unused in range(100):
                    if identity(process)['state'] in ('T', 't'):
                        break
                    time.sleep(.01)
                require(identity(process)['state'] in ('T', 't'), 'confirmed_parent_pause')
                require(not transport_children(row['old_parent']['pid']), 'parent_transport_still_running')
                manifest = settled_manifest(row)
                write(directory / 'PRESERVED_PARENT_LEDGER.json', manifest)
                handle = PausedParent(row, directory, descriptor, manifest, admitted_references)
                yield handle
                break
            except (ValueError, FileNotFoundError):
                if handle is not None:
                    raise
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                stopped = False
                require(time.monotonic() < deadline, 'no_quiet_parent_boundary_original_preserved')
                time.sleep(.5)
    finally:
        if descriptor is not None:
            if (handle is None and stopped) or (handle is not None and handle.stopped and not handle.terminated):
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            os.close(descriptor)
        os.close(lock)
