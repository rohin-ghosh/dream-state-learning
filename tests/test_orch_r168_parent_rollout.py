"""CPU-only mocked lifecycle; no actual processes, signals, or provider calls."""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from gpu import orch_r168_parent_rollout as rollout
from gpu import orch_r153_community_parents as community


class Operations:
    def __init__(self, failure=None):
        self.failure = failure
        self.calls = []
        self.handle = SimpleNamespace(terminated=False, terminate=self.terminate)

    def call(self, name):
        self.calls.append(name)
        if self.failure == name:
            raise InterruptedError(name)

    def preflight(self):
        self.call('preflight')

    @contextmanager
    def quiesce(self):
        self.call('quiesce')
        try:
            yield self.handle
        finally:
            self.call('continue_or_exited')

    def settled(self):
        self.call('settled')
        return 'exact_ledger'

    def preserve(self, manifest):
        assert manifest == 'exact_ledger'
        self.call('preserve')

    def terminate(self):
        self.call('terminate')
        self.handle.terminated = True

    @contextmanager
    def old_lock(self):
        self.call('old_lock')
        try:
            yield
        finally:
            self.call('unlock')

    def confirm_exit(self, manifest):
        self.call('confirm_exit')

    def start_successor(self):
        self.call('start')
        return 'successor'

    def verify_successor(self, successor):
        assert successor == 'successor'
        self.call('verify')

    def record_started(self, successor):
        self.call('record')

    def reconcile_failed_handoff(self, successor):
        self.call('reconcile_'+str(successor))


def test_exact_custody_order():
    operations = Operations()
    assert rollout.handoff(operations) == 'successor'
    assert operations.calls == ['preflight', 'quiesce', 'settled', 'preserve', 'terminate',
        'continue_or_exited', 'old_lock', 'confirm_exit', 'start', 'verify', 'record', 'unlock']


@pytest.mark.parametrize('failure', ['preflight', 'quiesce', 'settled', 'preserve', 'terminate'])
def test_deferral_never_starts_or_reconciles(failure):
    operations = Operations(failure)
    with pytest.raises(InterruptedError):
        rollout.handoff(operations)
    assert 'start' not in operations.calls
    assert not any(name.startswith('reconcile') for name in operations.calls)
    if failure in ('settled', 'preserve', 'terminate'):
        assert 'continue_or_exited' in operations.calls


@pytest.mark.parametrize('failure', ['continue_or_exited', 'old_lock', 'confirm_exit', 'start', 'verify', 'record'])
def test_post_exit_failure_reconciled_never_repeated(failure):
    operations = Operations(failure)
    with pytest.raises(InterruptedError):
        rollout.handoff(operations)
    assert operations.calls[-1].startswith('reconcile_')
    assert operations.calls.count('start') <= 1


@pytest.mark.parametrize('keyword', ['final', 'held', 'readout', 'sealed'])
def test_keyword_staging_paths_still_rejected(tmp_path, keyword):
    directory = tmp_path/('r168_'+keyword+'_staging')
    directory.mkdir()
    path = directory/'CONFIG.json'
    path.write_text('{}')
    with pytest.raises(ValueError, match='no_evaluation_input'):
        community.local_file(path.resolve())


def test_neutral_engagement_path_allowed_without_guard_change(tmp_path):
    directory = tmp_path/'r168_community_engagement_20260917'
    directory.mkdir()
    path = directory/'CONFIG.json'
    path.write_text('{}')
    assert community.local_file(path.resolve()) == path.resolve()
