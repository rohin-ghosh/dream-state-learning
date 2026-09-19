from contextlib import contextmanager
from copy import deepcopy
import json
import signal
import unittest
from unittest.mock import Mock, patch

from boundary import ObservationRace, Refusal, digest
import coordinator
from coordinator import PidfdReservation, coordinate, validate_prepared
from test_boundary import append_record, inputs, records_for, selected


class FakeOperations:
    def __init__(self, binding, observations=None):
        self.binding = binding
        self.observations = list(observations or [])
        self.candidate = selected(binding)
        self.events = []
        self.handle = object()
        self.stopped = False
        self.exited = False
        self.writer_locked = False
        self.commits = []
        self.failures = {}
        self.now = 1
        self.clear = True

    def event(self, name, value=None):
        self.events.append((name, value))
        if name in self.failures:
            raise self.failures[name]

    def require_execution_approval(self, expected):
        self.event('approval', expected)

    @contextmanager
    def exclusive_life_lock(self, binding):
        self.event('life_lock')
        yield
        self.event('life_unlock')

    def open_exact_handle(self, binding):
        self.event('open', self.handle)
        return self.handle

    def close_handle(self, handle):
        assert handle is self.handle
        self.event('close', handle)

    def require_exact_identity(self, handle, binding, *, stopped=False):
        assert handle is self.handle
        self.event('identity', stopped)
        if stopped:
            assert self.stopped

    def verify_prepared(self, prepared):
        self.event('prepared')

    def observe(self, binding, *, durable=False):
        self.event('observe', durable)
        result = self.observations.pop(0) if self.observations else deepcopy(self.candidate)
        if isinstance(result, BaseException):
            raise result
        if result is not None:
            result = deepcopy(result)
            result['durable'] = durable
        return result

    def dependents_clear(self, handle):
        assert handle is self.handle
        self.event('dependents')
        return self.clear

    def verify_checkpoint(self, candidate):
        self.event('checkpoint')
        return dict(complete_sha256=candidate['complete_sha256'], checkpoint_sha256=digest(candidate['checkpoint']),
            adapter_verified=True, optimizer_verified=True, python_cpu_cuda_rng_verified=True,
            working_state_verified=True, durable_files_and_directories=True)

    def prepare_receiver(self, candidate, prepared, proof):
        self.event('receiver')
        return dict(source_epoch=prepared['epoch_id'], resume_state_sha256=candidate['resume_state']['sha256'],
            checkpoint_sha256=digest(candidate['checkpoint']), same_journal_root=self.binding['journal_root'],
            rescans_original_inbox=True, no_model_load_before_writer_lock=True,
            deadline_unix=self.binding['hard_end_unix'], source_adoption_not_wall_extension=True)

    @contextmanager
    def reserve(self, handle, seconds):
        assert handle is self.handle
        self.event('stop', handle)
        self.stopped = True
        try:
            yield self
        finally:
            if not self.exited:
                self.event('resume', handle)
            self.stopped = False

    def recheck_checkpoint(self, proof, frozen):
        self.event('recheck')

    def verify_receiver(self, receiver, frozen):
        self.event('verify_receiver')

    def record(self, kind, document):
        self.event(kind, deepcopy(document))

    def commit_and_wait_exit(self):
        self.event('commit')
        result = self.commits.pop(0) if self.commits else True
        if isinstance(result, BaseException):
            raise result
        self.exited = result
        return result

    def require_handle_exited(self, handle):
        assert handle is self.handle and self.exited
        self.event('exited')

    @contextmanager
    def exclusive_writer_check(self, binding):
        assert self.exited
        self.event('writer_lock')
        self.writer_locked = True
        try:
            yield
        finally:
            self.writer_locked = False
            self.event('writer_unlock')

    def dispatch_once(self, token):
        assert self.exited and not self.writer_locked
        self.event('dispatch', token)

    def wall_time(self):
        return self.now

    def wait(self):
        assert not self.stopped
        self.event('wait')

    def names(self):
        return [name for name, _ in self.events]


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.binding, self.prepared, self.authority = inputs()
        self.operations = FakeOperations(self.binding)
        forbidden = Mock(side_effect=AssertionError('no live signals in CPU tests'))
        self.signal_patch = patch.object(signal, 'pidfd_send_signal', forbidden)
        self.signal_patch.start()
        self.addCleanup(self.signal_patch.stop)

    def run_coordinate(self, **kwargs):
        return coordinate(self.binding, self.prepared, self.authority, self.operations, max_attempts=3, **kwargs)

    def test_success_order_and_bound_token(self):
        token = self.run_coordinate()
        names = self.operations.names()
        expected = ['approval', 'life_lock', 'open', 'checkpoint', 'receiver', 'stop',
            'RETENTION_HANDOFF_INTENT', 'commit', 'exited', 'writer_lock',
            'RETENTION_HANDOFF_READY', 'writer_unlock', 'dispatch', 'close', 'life_unlock']
        self.assertEqual(sorted(expected, key=names.index), expected)
        self.assertEqual(token['deadline_unix'], self.binding['hard_end_unix'])
        self.assertEqual(token['sha256'], digest({key: value for key, value in token.items() if key != 'sha256'}))
        self.assertEqual(names.count('dispatch'), 1)
        self.assertTrue(token['exact_complete']['durable'])
        self.assertNotIn('resume', names)

    def test_pending_request_never_stops_or_dispatches(self):
        self.operations.observations = [None] * 3
        with self.assertRaisesRegex(Refusal, 'bounded_observation'):
            self.run_coordinate()
        self.assertNotIn('stop', self.operations.names())
        self.assertNotIn('commit', self.operations.names())
        self.assertNotIn('dispatch', self.operations.names())
        self.assertEqual(self.operations.names().count('close'), 1)

    def test_partial_publication_retries_before_stop(self):
        self.operations.observations = [ObservationRace('intent only'), FileNotFoundError('rename'),
            json.JSONDecodeError('partial', '', 0)]
        with self.assertRaisesRegex(Refusal, 'bounded_observation'):
            self.run_coordinate()
        self.assertEqual(self.operations.names().count('wait'), 3)
        self.assertNotIn('stop', self.operations.names())

    def test_corrupt_preobservation_refuses_without_stop(self):
        self.operations.observations = [Refusal('record_hash')]
        with self.assertRaisesRegex(Refusal, 'record_hash'):
            self.run_coordinate()
        self.assertNotIn('stop', self.operations.names())

    def test_request_raced_while_stopping_resumes_same_handle(self):
        self.operations.observations = [self.operations.candidate, None]
        self.run_coordinate()
        names = self.operations.names()
        self.assertEqual(names.count('open'), 1)
        self.assertEqual(names.count('stop'), 2)
        self.assertEqual(names.count('commit'), 1)
        self.assertEqual(names.count('resume'), 1)
        self.assertLess(names.index('resume'), names.index('commit'))
        self.assertIs(next(value for name, value in self.operations.events if name == 'resume'), self.operations.handle)

    def test_request_raced_after_receiver_check_resumes_without_commit(self):
        self.operations.observations = [self.operations.candidate, self.operations.candidate, None] * 3
        with self.assertRaisesRegex(Refusal, 'bounded_observation'):
            self.run_coordinate()
        self.assertEqual(self.operations.names().count('resume'), 3)
        self.assertNotIn('commit', self.operations.names())

    def test_inbox_arrives_during_reservation_and_after_exit(self):
        records = records_for(self.binding)
        receipt = dict(message=dict(id='new', text='keep', split='TRAIN', actor='parent'),
            source_id='/life/stream/inbox/new.json', source_sha256=digest('new'))
        append_record(records, self.binding, 'INBOX', receipt)
        frozen = selected(self.binding, records)
        frozen['mailbox'] = {receipt['source_id']: dict(id='new', sha256=receipt['source_sha256'])}
        exited = deepcopy(frozen)
        exited['mailbox']['/life/stream/inbox/late.json'] = dict(id='late', sha256=digest('late'))
        self.operations.observations = [self.operations.candidate, frozen, frozen, exited]
        token = self.run_coordinate()
        self.assertEqual(len(token['exact_complete']['mailbox']), 2)
        self.assertEqual(len(token['exact_complete']['preserved_INBOX_records']), 1)

    def test_expired_reservation_retries_same_handle(self):
        self.operations.commits = [False, True]
        self.run_coordinate()
        names = self.operations.names()
        self.assertEqual(names.count('open'), 1)
        self.assertEqual(names.count('resume'), 1)
        self.assertEqual(names.count('dispatch'), 1)

    def test_unconfirmed_exit_never_dispatches(self):
        self.operations.commits = [Refusal('old_exit_unconfirmed')]
        with self.assertRaisesRegex(Refusal, 'old_exit_unconfirmed'):
            self.run_coordinate()
        self.assertNotIn('dispatch', self.operations.names())

    def test_checkpoint_or_receiver_failure_before_stop_is_safe(self):
        for name in ('checkpoint', 'receiver'):
            with self.subTest(name=name):
                self.operations = FakeOperations(self.binding)
                self.operations.failures[name] = RuntimeError(name)
                with self.assertRaisesRegex(RuntimeError, name):
                    self.run_coordinate()
                self.assertNotIn('stop', self.operations.names())

    def test_failures_inside_reservation_always_resume(self):
        for name in ('recheck', 'verify_receiver', 'RETENTION_HANDOFF_INTENT'):
            with self.subTest(name=name):
                self.operations = FakeOperations(self.binding)
                self.operations.failures[name] = RuntimeError(name)
                with self.assertRaisesRegex(RuntimeError, name):
                    self.run_coordinate()
                self.assertIn('resume', self.operations.names())
                self.assertNotIn('commit', self.operations.names())

    def test_guard_change_while_stopped_never_commits(self):
        original = self.operations.verify_prepared

        def raced(prepared):
            original(prepared)
            if self.operations.stopped:
                raise Refusal('guard_changed')

        self.operations.verify_prepared = raced
        with self.assertRaisesRegex(Refusal, 'bounded_observation'):
            self.run_coordinate()
        self.assertNotIn('commit', self.operations.names())
        self.assertEqual(self.operations.names().count('resume'), 3)

    def test_no_active_dependents_or_short_deadline_stop(self):
        self.operations.clear = False
        with self.assertRaisesRegex(Refusal, 'bounded_observation'):
            self.run_coordinate()
        self.assertNotIn('stop', self.operations.names())
        self.operations = FakeOperations(self.binding)
        self.operations.now = self.binding['hard_end_unix'] - 40
        with self.assertRaisesRegex(Refusal, 'deadline_margin'):
            self.run_coordinate()
        self.assertNotIn('stop', self.operations.names())

    def test_deadline_consumed_by_receiver_staging_never_commits(self):
        original = self.operations.prepare_receiver

        def slow(*args):
            result = original(*args)
            self.operations.now = self.binding['hard_end_unix'] - 1
            return result

        self.operations.prepare_receiver = slow
        with self.assertRaisesRegex(Refusal, 'deadline_margin'):
            self.run_coordinate()
        self.assertNotIn('commit', self.operations.names())

    def test_after_exit_boundary_change_or_writer_conflict_never_dispatches(self):
        self.operations.observations = [self.operations.candidate] * 3 + [None]
        with self.assertRaisesRegex(Refusal, 'raced_past_COMPLETE'):
            self.run_coordinate()
        self.assertNotIn('dispatch', self.operations.names())
        self.operations = FakeOperations(self.binding)
        self.operations.failures['writer_lock'] = BlockingIOError('another writer')
        with self.assertRaises(BlockingIOError):
            self.run_coordinate()
        self.assertNotIn('dispatch', self.operations.names())

    def test_deadline_expiry_after_exit_does_not_dispatch(self):
        original = self.operations.verify_receiver

        def slow(*args):
            original(*args)
            if self.operations.exited:
                self.operations.now = self.binding['hard_end_unix']

        self.operations.verify_receiver = slow
        with self.assertRaisesRegex(Refusal, 'same_deadline_not_expired'):
            self.run_coordinate()
        self.assertNotIn('dispatch', self.operations.names())

    def test_wrong_proof_or_receiver_deadline_never_stops(self):
        original = self.operations.verify_checkpoint
        self.operations.verify_checkpoint = lambda candidate: dict(original(candidate), optimizer_verified=False)
        with self.assertRaisesRegex(Refusal, 'saved_state_proof'):
            self.run_coordinate()
        self.assertNotIn('stop', self.operations.names())
        self.operations = FakeOperations(self.binding)
        original_receiver = self.operations.prepare_receiver
        self.operations.prepare_receiver = lambda *args: dict(original_receiver(*args), deadline_unix=20000)
        with self.assertRaisesRegex(Refusal, 'receiver_exact_saved_state'):
            self.run_coordinate()
        self.assertNotIn('stop', self.operations.names())

    def test_exact_per_file_authority_and_non_extension_required(self):
        validate_prepared(self.binding, self.prepared, self.authority)
        for key, value in (('wall_extension_authorized', True), ('approved_source_changes', {}),
                ('life_binding_sha256', 'f' * 64), ('epoch_id', 'another')):
            wrong = dict(self.authority, **{key: value})
            with self.subTest(key=key), self.assertRaises(Refusal):
                validate_prepared(self.binding, self.prepared, wrong)


class GuardianTests(unittest.TestCase):
    def setUp(self):
        self.reservation = PidfdReservation(321, 10)
        self.connection = Mock()
        self.signals = patch.object(coordinator.signal, 'pidfd_send_signal').start()
        self.addCleanup(patch.stopall)
        self.clock = patch.object(coordinator.time, 'monotonic', return_value=100).start()
        self.select = patch.object(coordinator.select, 'select', return_value=([], [], [])).start()
        patch.object(coordinator.os, 'fork', side_effect=AssertionError('no live fork in CPU tests')).start()

    def sent_signals(self):
        return [arguments.args for arguments in self.signals.call_args_list]

    def test_watchdog_timeout_resumes_same_pidfd_without_term(self):
        self.reservation._guard(self.connection)
        self.assertEqual(self.sent_signals(), [(321, signal.SIGSTOP), (321, signal.SIGCONT)])

    def test_disconnect_resumes_same_pidfd(self):
        self.select.return_value = ([self.connection], [], [])
        self.connection.recv.return_value = b''
        self.reservation._guard(self.connection)
        self.assertEqual(self.sent_signals(), [(321, signal.SIGSTOP), (321, signal.SIGCONT)])

    def test_late_commit_is_not_a_term(self):
        self.select.return_value = ([self.connection], [], [])
        self.connection.recv.return_value = b'"COMMIT"'
        self.clock.side_effect = [100, 100, 110]
        self.reservation._guard(self.connection)
        self.assertNotIn((321, signal.SIGTERM), self.sent_signals())

    def test_timely_commit_terms_only_exact_handle_then_confirms_exit(self):
        self.select.side_effect = [([self.connection], [], []), ([321], [], [])]
        self.connection.recv.return_value = b'"COMMIT"'
        self.reservation._guard(self.connection)
        self.assertEqual(self.sent_signals(), [(321, signal.SIGSTOP), (321, signal.SIGTERM), (321, signal.SIGCONT)])
        self.assertEqual(json.loads(self.connection.send.call_args.args[0])['status'], 'EXITED')

    def test_exit_unconfirmed_and_already_exited_are_not_success(self):
        self.select.side_effect = [([self.connection], [], []), ([], [], [])]
        self.connection.recv.return_value = b'"COMMIT"'
        self.reservation._guard(self.connection)
        self.assertEqual(json.loads(self.connection.send.call_args.args[0])['status'], 'EXIT_UNCONFIRMED')
        self.signals.reset_mock()
        self.select.side_effect = None
        self.select.return_value = ([self.connection, 321], [], [])
        self.reservation._guard(self.connection)
        self.assertNotIn((321, signal.SIGTERM), self.sent_signals())

    def test_unexpected_error_after_stop_resumes(self):
        self.connection.send.side_effect = RuntimeError('audit transport')
        with self.assertRaisesRegex(RuntimeError, 'audit transport'):
            self.reservation._guard(self.connection)
        self.assertEqual(self.sent_signals(), [(321, signal.SIGSTOP), (321, signal.SIGCONT)])

    def test_parent_consumes_resume_ack_even_if_commit_send_hits_closed_socket(self):
        self.reservation.connection = self.connection
        self.connection.send.side_effect = BrokenPipeError()
        self.connection.recv.return_value = json.dumps(dict(status='RESUMED_SAME_PIDFD', irreversible=False)).encode()
        self.assertFalse(self.reservation.commit_and_wait_exit())
        self.signals.assert_not_called()

    def test_parent_refuses_unconfirmed_commit_exit(self):
        self.reservation.connection = self.connection
        self.connection.recv.return_value = b'{"status":"EXIT_UNCONFIRMED","irreversible":true}'
        with self.assertRaisesRegex(Refusal, 'exit_unconfirmed'):
            self.reservation.commit_and_wait_exit()

    def test_failed_enter_closes_connection_and_reaps_guardian(self):
        parent, guardian = Mock(), Mock()
        parent.recv.return_value = b''
        with patch.object(coordinator.socket, 'socketpair', return_value=(parent, guardian)), \
                patch.object(coordinator.os, 'fork', return_value=888), \
                patch.object(coordinator.os, 'waitpid', return_value=(888, 0)) as reaped:
            with self.assertRaisesRegex(Refusal, 'guardian_stop_acknowledged'):
                self.reservation.__enter__()
        parent.close.assert_called_once()
        guardian.close.assert_called_once()
        reaped.assert_called_once_with(888, 0)
        self.signals.assert_not_called()


if __name__ == '__main__':
    unittest.main()
