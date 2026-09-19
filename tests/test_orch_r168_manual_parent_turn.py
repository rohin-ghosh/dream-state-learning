"""CPU-only lifecycle fixtures, never real signals or publication."""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from gpu import orch_r168_manual_parent_turn as manual


class Operations:
    def __init__(self, fail=None):
        self.calls = []
        self.fail = fail
        self.handle = SimpleNamespace(terminated=False, terminate=self.terminate)

    def call(self, name):
        self.calls.append(name)
        if self.fail == name:
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
        return {'reserved': 96}

    def preserve(self, manifest):
        assert manifest == {'reserved': 96}
        self.call('preserve')

    def terminate(self):
        self.call('terminate')
        self.handle.terminated = True

    @contextmanager
    def exclusive_lock(self):
        self.call('lock')
        try:
            yield
        finally:
            self.call('unlock')

    def confirm_exit(self, manifest):
        self.call('confirm_exit')

    def write_intent(self, message):
        assert message == manual.MESSAGE
        self.call('intent')

    def publish(self, message):
        assert message == manual.MESSAGE
        self.call('publish')
        return {'id': 'synthetic-CPU-only'}

    def record_publication(self, publication):
        self.call('record')

    def restart_unchanged(self):
        self.call('restart')


def test_one_publication_after_exclusive_custody_and_restart():
    operations = Operations()
    manual.execute_once(operations)
    assert operations.calls == ['preflight', 'quiesce', 'settled', 'preserve',
        'terminate', 'continue_or_exited', 'lock', 'confirm_exit', 'intent',
        'publish', 'record', 'unlock', 'restart']


@pytest.mark.parametrize('point', ['preflight', 'quiesce', 'settled', 'preserve', 'terminate'])
def test_deferral_never_publishes_or_duplicates_parent(point):
    operations = Operations(point)
    with pytest.raises(InterruptedError):
        manual.execute_once(operations)
    assert 'publish' not in operations.calls and 'restart' not in operations.calls
    if point in ('settled', 'preserve', 'terminate'):
        assert 'continue_or_exited' in operations.calls


@pytest.mark.parametrize('point', ['continue_or_exited', 'lock', 'confirm_exit', 'intent', 'publish', 'record'])
def test_failure_after_exit_restarts_parent_without_retry(point):
    operations = Operations(point)
    with pytest.raises(InterruptedError):
        manual.execute_once(operations)
    assert operations.calls[-1] == 'restart'
    assert operations.calls.count('publish') <= 1


def test_original_text_schema_not_provider_output():
    assert len(manual.MESSAGE.split()) == 72
    assert manual.MESSAGE.startswith('Your last pre-sleep reply was {}.')
    assert manual.MESSAGE.endswith('a proposed action is not an executed result.')
