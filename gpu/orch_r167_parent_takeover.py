"""Scoped local R153 parent pidfd handoff; never signals a native or provider."""

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import stat
import time

from gpu.orch_r125_stream_journal import require


ALLOWED_BRANCHES = ('C1', 'C2', 'C3', 'C4', 'C5')
MAX_BYTES = 256 * 1024 * 1024
MAX_FILE = 16 * 1024 * 1024


def read_file(path, limit=MAX_FILE):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= limit, 'bounded_regular_file')
        raw = stream.read(before.st_size+1)
        after = os.fstat(stream.fileno())
    current = os.stat(path, follow_symlinks=False)
    require(len(raw) == before.st_size and len({(entry.st_dev, entry.st_ino, entry.st_size,
        entry.st_mtime_ns) for entry in (before, after, current)}) == 1, 'file_changed')
    return raw


def sha(path):
    return hashlib.sha256(read_file(path)).hexdigest()


def identity(pid):
    root = Path('/proc')/str(pid)
    fields = (root/'stat').read_text().rsplit(')', 1)[1].split()
    argv = (root/'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
    require(len(argv) <= 128 and sum(map(len, argv)) <= 65536, 'bounded_argv')
    return dict(pid=pid, start_ticks=fields[19], state=fields[0], argv=argv)


def verify_identity(binding, observed):
    require(binding['branch'] in ALLOWED_BRANCHES and observed['pid'] == binding['pid']
        and observed['start_ticks'] == binding['start_ticks'] and observed['argv'] == binding['argv'],
        'exact_scoped_parent_identity')
    require('-m' in observed['argv'] and observed['argv'][observed['argv'].index('-m')+1]
        == 'gpu.orch_r153_community_parents', 'parent_module_only')
    require(observed['argv'][observed['argv'].index('--config')+1] == binding['config']['path']
        and observed['argv'][observed['argv'].index('--output')+1] == binding['output'], 'exact_parent_paths')
    require(observed['state'] not in ('Z', 'X'), 'parent_still_live')


def verify_files(binding):
    for reference in (binding['source'], binding['config']):
        require(sha(reference['path']) == reference['sha256'], 'parent_source_config_pin')
    config = json.loads(read_file(binding['config']['path']))
    require(config['branch'] == binding['branch'] and config['root'] == binding['root']
        and time.time() < config['hard_end_unix'], 'same_parent_root_wall')


class PidfdOperations:
    read_identity = staticmethod(identity)
    check_files = staticmethod(verify_files)
    open = staticmethod(os.pidfd_open)
    close = staticmethod(os.close)
    signal = staticmethod(signal.pidfd_send_signal)

    @staticmethod
    def stopped_and_childless(pid):
        tasks = list((Path('/proc')/str(pid)/'task').iterdir())
        require(0 < len(tasks) <= 128, 'bounded_owned_tasks')
        for task in tasks:
            fields = (task/'stat').read_text().rsplit(')', 1)[1].split()
            require(fields[0] in ('T', 't'), 'all_parent_tasks_stopped')
            require(not (task/'children').read_text().strip(), 'owned_task_has_child_defer')

    @staticmethod
    def exited(descriptor, timeout):
        poller = select.poll()
        poller.register(descriptor, select.POLLIN)
        return bool(poller.poll(int(timeout*1000)))


class QuiescedParent:
    def __init__(self, binding, operations):
        self.binding, self.operations = binding, operations
        self.descriptor = None
        self.stopped = False
        self.terminated = False

    def terminate(self):
        self.operations.stopped_and_childless(self.binding['pid'])
        self.operations.signal(self.descriptor, signal.SIGTERM)
        self.operations.signal(self.descriptor, signal.SIGCONT)
        self.stopped = False
        require(self.operations.exited(self.descriptor, 5), 'parent_exit_unconfirmed_no_successor')
        self.terminated = True


@contextmanager
def quiesce(binding, *, operations=None):
    operations = operations or PidfdOperations()
    handle = QuiescedParent(binding, operations)
    observed = operations.read_identity(binding['pid'])
    verify_identity(binding, observed)
    require(observed['state'] not in ('T', 't'), 'preexisting_stop_not_owned')
    operations.check_files(binding)
    handle.descriptor = operations.open(binding['pid'])
    try:
        verify_identity(binding, operations.read_identity(binding['pid']))
        operations.signal(handle.descriptor, signal.SIGSTOP)
        handle.stopped = True
        for attempt in range(100):
            if operations.read_identity(binding['pid'])['state'] in ('T', 't'):
                break
            time.sleep(0.01)
        verify_identity(binding, operations.read_identity(binding['pid']))
        operations.stopped_and_childless(binding['pid'])
        operations.check_files(binding)
        yield handle
    finally:
        if handle.stopped:
            operations.signal(handle.descriptor, signal.SIGCONT)
        operations.close(handle.descriptor)


def settled_attempts(output):
    """All attempt files and reservation identities; unknown/missing results refuse."""
    output = Path(output)
    directories = sorted(output.glob('parent_*'))
    require(len(directories) <= 10000, 'attempt_count_limit')
    manifest, summaries, used = {}, [], 0
    journal_id = None
    for directory in directories:
        require(directory.is_dir() and not directory.is_symlink(), 'regular_attempt_directory')
        source_path, result_path = directory/'SOURCE.json', directory/'RESULT.json'
        require(source_path.is_file() and result_path.is_file(), 'unfinished_attempt_defer')
        source_raw, result_raw = read_file(source_path), read_file(result_path)
        source, result = json.loads(source_raw), json.loads(result_raw)
        require(result['source_sha256'] == hashlib.sha256(source_raw).hexdigest(), 'source_result_binding')
        require(result['status'] in ('PUBLISHED', 'SILENT', 'PROVIDER_FAILED'), 'publication_uncertain_defer')
        require(not (directory/'PUBLISH_INTENT.json').exists() or result['status'] == 'PUBLISHED',
                'publication_intent_unsettled')
        require(journal_id in (None, source['journal_id']), 'one_journal_only')
        journal_id = source['journal_id']
        summaries.append(dict(attempt=directory.name, source_response_count=source['response_count'],
            status=result['status'], object_id=result.get('object_id'), publication=result.get('publication')))
        files = list(directory.iterdir())
        require(len(files) <= 128, 'attempt_file_count_limit')
        for path in files:
            require(not path.is_symlink() and path.is_file(), 'flat_regular_attempt_files')
            raw = read_file(path)
            used += len(raw)
            require(used <= MAX_BYTES, 'attempt_copy_byte_limit')
            manifest[str(path.relative_to(output))] = dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    return dict(files=manifest, attempts=summaries, journal_id=journal_id, bytes=used,
                reserved_response_count=max((entry['source_response_count'] for entry in summaries), default=0))


def copy_attempts(old_output, new_output, manifest):
    new_output = Path(new_output)
    require(new_output.is_dir() and not any(new_output.iterdir()), 'empty_new_output_only')
    for relative, expected in manifest['files'].items():
        path = Path(relative)
        require(len(path.parts) == 2 and path.parts[0].startswith('parent_')
            and '..' not in path.parts and not path.is_absolute(), 'relative_attempt_file')
        raw = read_file(Path(old_output)/path)
        require(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'],
                'predecessor_changed_during_copy')
        destination = new_output/path
        destination.parent.mkdir(mode=0o700, exist_ok=True)
        with destination.open('xb') as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        require(sha(destination) == expected['sha256'], 'copy_exact_hash')
    require(settled_attempts(new_output) == manifest, 'exact_ledger_transfer')
