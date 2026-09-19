"""Mocked CPU watchdog/signal tests. No live parent or native signals."""

import signal
import time
from unittest.mock import Mock, patch

import pytest

from gpu import orch_r167_parent_watchdog as watchdog
from tests.test_orch_r167_parent_takeover import FakeOperations, binding


class FakeWatchdog:
    def __init__(self, descriptor, seconds):
        self.released = False

    def release(self):
        self.released = True


@pytest.mark.parametrize('error', [ValueError, InterruptedError, KeyboardInterrupt, SystemExit])
def test_all_operator_error_paths_CONT_before_disarm(error):
    operations = FakeOperations()
    guard = FakeWatchdog(42, 15)
    with pytest.raises(error):
        with watchdog.quiesce(binding(), scope_verifier=lambda expected, observed: None,
            operations=operations, watchdog_factory=lambda descriptor, seconds: guard):
            raise error()
    assert operations.signals == [signal.SIGSTOP, signal.SIGCONT]
    assert guard.released and operations.closed


def test_scope_rejection_never_arms_or_signals():
    operations = FakeOperations()
    factory = Mock()
    def reject(expected, observed):
        raise ValueError('not Main-approved parent')
    with pytest.raises(ValueError):
        with watchdog.quiesce(binding(), scope_verifier=reject, operations=operations, watchdog_factory=factory):
            pass
    factory.assert_not_called()
    assert operations.signals == []


def test_watchdog_arm_failure_never_stops_parent():
    operations = FakeOperations()
    with pytest.raises(RuntimeError):
        with watchdog.quiesce(binding(), scope_verifier=lambda expected, observed: None,
            operations=operations, watchdog_factory=Mock(side_effect=RuntimeError('not ready'))):
            pass
    assert not operations.signals and operations.closed


def test_interruption_at_STOP_return_still_CONT_before_disarm():
    operations = FakeOperations()
    original_signal = operations.signal
    def interrupted_signal(descriptor, sig):
        original_signal(descriptor, sig)
        if sig == signal.SIGSTOP:
            raise InterruptedError('signal delivered before Python return')
    operations.signal = interrupted_signal
    with pytest.raises(InterruptedError):
        with watchdog.quiesce(binding(), scope_verifier=lambda expected, observed: None,
            operations=operations, watchdog_factory=FakeWatchdog):
            pass
    assert operations.signals == [signal.SIGSTOP, signal.SIGCONT]


def test_expiring_stop_resumes_instead_of_termination():
    operations = FakeOperations()
    with pytest.raises(ValueError, match='expiring'):
        with watchdog.quiesce(binding(), scope_verifier=lambda expected, observed: None,
            operations=operations, watchdog_factory=FakeWatchdog) as handle:
            handle.deadline = time.monotonic()
            handle.terminate()
    assert operations.signals == [signal.SIGSTOP, signal.SIGCONT]


@pytest.mark.parametrize('events,read_value,continued', [([], b'', True),
    ([(11, 1)], b'', True), ([(12, 16)], b'', True), ([(12, 1)], b'D', False), ([(10, 1)], b'', False)])
def test_independent_watchdog_timeout_operator_death_pipe_eof_or_completed_release(events, read_value, continued):
    poller = Mock()
    poller.poll.return_value = events
    with patch.object(watchdog.select, 'poll', return_value=poller), \
        patch.object(watchdog.os, 'write'), patch.object(watchdog.os, 'read', return_value=read_value), \
        patch.object(watchdog.os, 'close'), patch.object(watchdog.signal, 'pidfd_send_signal') as send:
        watchdog.watch(10, 11, 12, 13, 15)
    if continued:
        send.assert_called_once_with(10, signal.SIGCONT)
    else:
        send.assert_not_called()
