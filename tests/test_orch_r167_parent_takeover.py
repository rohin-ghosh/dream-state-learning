"""CPU-only mocked pidfds and temporary ledger fixtures; never signals live parents."""

import copy
import hashlib
import json
import signal

import pytest

from gpu import orch_r167_parent_takeover as takeover


def binding():
    return dict(branch='C1', pid=101, start_ticks='123', root='/life', output='/old',
        config=dict(path='/config', sha256='a'*64), source=dict(path='/source', sha256='b'*64),
        argv=['python', '-m', 'gpu.orch_r153_community_parents', '--config', '/config', '--output', '/old'])


class FakeOperations:
    def __init__(self):
        self.binding = binding()
        self.state = 'S'
        self.signals = []
        self.busy = False
        self.closed = False
        self.exit_ready = True

    def read_identity(self, pid):
        return dict(pid=pid, start_ticks=self.binding['start_ticks'], argv=self.binding['argv'], state=self.state)

    def check_files(self, expected):
        pass

    def open(self, pid):
        return 42

    def close(self, descriptor):
        assert descriptor == 42
        self.closed = True

    def signal(self, descriptor, sig):
        assert descriptor == 42
        self.signals.append(sig)
        self.state = 'T' if sig == signal.SIGSTOP else 'S'

    def stopped_and_childless(self, pid):
        assert self.state == 'T'
        if self.busy:
            raise ValueError('owned_task_has_child_defer')

    def exited(self, descriptor, timeout):
        return self.exit_ready


def test_clean_order_same_pidfd_no_kill():
    operations = FakeOperations()
    with takeover.quiesce(binding(), operations=operations) as handle:
        handle.terminate()
    assert operations.signals == [signal.SIGSTOP, signal.SIGTERM, signal.SIGCONT]
    assert operations.closed


@pytest.mark.parametrize('failure', ['busy', 'ledger', 'copy'])
def test_deferral_and_error_resume_without_termination(failure):
    operations = FakeOperations()
    operations.busy = failure == 'busy'
    with pytest.raises(ValueError):
        with takeover.quiesce(binding(), operations=operations):
            raise ValueError(failure)
    assert operations.signals == [signal.SIGSTOP, signal.SIGCONT]
    assert operations.closed


@pytest.mark.parametrize('change', ['pid_reuse', 'native', 'wrong_branch', 'already_stopped'])
def test_no_signal_for_unverified_or_unowned_process(change):
    operations = FakeOperations()
    expected = binding()
    if change == 'pid_reuse':
        operations.binding['start_ticks'] = '999'
    elif change == 'native':
        expected['argv'][2] = 'gpu.orch_r125_continual_guard'
        operations.binding = copy.deepcopy(expected)
    elif change == 'wrong_branch':
        expected['branch'] = 'kernel0'
    else:
        operations.state = 'T'
    with pytest.raises(ValueError):
        with takeover.quiesce(expected, operations=operations):
            pytest.fail('must not quiesce')
    assert not operations.signals


def ledger(tmp_path, status='SILENT'):
    root = tmp_path/'old'
    directory = root/'parent_000000000003'
    directory.mkdir(parents=True)
    raw = json.dumps(dict(journal_id='a'*32, response_count=3)).encode()
    (directory/'SOURCE.json').write_bytes(raw)
    (directory/'RESULT.json').write_text(json.dumps(dict(status=status,
        source_sha256=hashlib.sha256(raw).hexdigest())))
    (directory/'DISPATCH_INTENT.json').write_text('{}')
    return root, directory


def test_copy_preserves_every_byte_and_reservation_without_old_binding(tmp_path):
    root, directory = ledger(tmp_path)
    (root/'BINDING.json').write_text('old identity retained')
    manifest = takeover.settled_attempts(root)
    assert manifest['reserved_response_count'] == 3
    target = tmp_path/'new'
    target.mkdir()
    takeover.copy_attempts(root, target, manifest)
    assert takeover.settled_attempts(target) == manifest
    assert not (target/'BINDING.json').exists()
    assert (root/'BINDING.json').read_text() == 'old identity retained'


@pytest.mark.parametrize('kind', ['missing', 'unknown', 'intent', 'tamper', 'symlink'])
def test_uncertain_or_changed_ledger_refused(tmp_path, kind):
    root, directory = ledger(tmp_path, 'PUBLICATION_UNKNOWN' if kind == 'unknown' else 'SILENT')
    if kind == 'missing':
        (directory/'RESULT.json').unlink()
    elif kind == 'intent':
        (directory/'PUBLISH_INTENT.json').write_text('{}')
    elif kind == 'tamper':
        (directory/'SOURCE.json').write_text('{}')
    elif kind == 'symlink':
        (directory/'linked').symlink_to(directory/'SOURCE.json')
    with pytest.raises((ValueError, KeyError)):
        takeover.settled_attempts(root)


def test_unconfirmed_exit_does_not_claim_terminated():
    operations = FakeOperations()
    operations.exit_ready = False
    with pytest.raises(ValueError, match='exit_unconfirmed'):
        with takeover.quiesce(binding(), operations=operations) as handle:
            handle.terminate()
    assert not handle.terminated and operations.closed
