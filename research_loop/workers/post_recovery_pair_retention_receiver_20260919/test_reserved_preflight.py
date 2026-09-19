from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from reserved_preflight import (BudgetExpired, ReservationBudget, ReservedPairLinuxOperations,
    coordinate_reserved, execution_digest, validate_policy, verify_static_receipt)
from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import ObservationRace, Refusal, digest, sha
from research_loop.workers.post_recovery_pair_retention_receiver_20260919.receiver import PairReceiver, write_once


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / 'post_recovery_retention_boundary_20260918'))
from test_boundary import append_record, inputs, records_for, selected
from test_coordinator import FakeOperations


def policy():
    return dict(schema='PAIR_RESERVED_PREFLIGHT_POLICY_V1', stop_seconds=30,
        commit_margin_seconds=2, static_receipt_path='/review/STATIC.json', static_receipt_sha256='a' * 64)


class MovingOperations(FakeOperations):
    def __init__(self, binding, observations=None):
        super().__init__(binding, observations)
        self.clock = 0
        self.proof_seconds = 0
        self.receiver_seconds = 0
        self.gate = False
        self.active_budget = None
        self.require_held = True

    def monotonic(self):
        return self.clock

    def verify_static(self, prepared, reviewed_policy):
        self.event('static')
        if self.gate:
            raise Refusal('no_blind_reserved_attempt_retry')
        self.verify_prepared(prepared)

    def verify_candidate_family(self, candidate):
        self.event('family')
        assert not self.stopped

    def begin_reserved_attempt(self, candidate):
        self.event('gate')
        assert not self.gate
        self.gate = True

    def finish_early_race(self):
        self.event('clear_gate')
        assert not self.stopped and not self.exited
        self.gate = False

    @contextmanager
    def preflight_budget(self, budget):
        assert self.stopped
        self.active_budget = budget
        try:
            yield
        finally:
            self.active_budget = None

    def verify_checkpoint(self, candidate):
        if self.require_held:
            assert self.stopped
        self.clock += self.proof_seconds
        if self.clock >= 30:
            self.stopped = False
        return super().verify_checkpoint(candidate)

    def prepare_receiver(self, candidate, prepared, proof):
        assert self.stopped
        self.clock += self.receiver_seconds
        if self.clock >= 30:
            self.stopped = False
        return super().prepare_receiver(candidate, prepared, proof)


class ReservedCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.binding, self.prepared, self.authority = inputs()
        self.operations = MovingOperations(self.binding)
        self.addCleanup(patch.stopall)
        patch.object(signal, 'pidfd_send_signal', side_effect=AssertionError('no native signals')).start()
        patch.object(os, 'fork', side_effect=AssertionError('no live guardian')).start()
        patch.object(subprocess, 'Popen', side_effect=AssertionError('no GPU dispatch')).start()

    def run_reserved(self, attempts=4):
        return coordinate_reserved(self.binding, self.prepared, self.authority, self.operations,
            policy=policy(), max_attempts=attempts)

    def assert_no_commit(self):
        self.assertNotIn('commit', self.operations.names())
        self.assertNotIn('dispatch', self.operations.names())
        self.assertFalse(self.operations.stopped)

    def test_live_like_boundary_moves_on_unreserved_work_but_reserved_preflight_succeeds(self):
        original = self.operations.verify_checkpoint

        def moving(candidate):
            if not self.operations.stopped:
                self.operations.observations = [None]
            return original(candidate)

        self.operations.verify_checkpoint = moving
        self.operations.proof_seconds, self.operations.receiver_seconds = 2, 19
        result = self.run_reserved()
        names = self.operations.names()
        self.assertLess(names.index('static'), names.index('stop'))
        self.assertLess(names.index('family'), names.index('stop'))
        self.assertLess(names.index('stop'), names.index('checkpoint'))
        self.assertLess(names.index('checkpoint'), names.index('commit'))
        self.assertEqual(names.count('dispatch'), 1)
        self.assertTrue(result['no_cold_start'])
        self.assertEqual(result['deadline_unix'], self.binding['hard_end_unix'])

    def test_static_or_family_refusal_never_reserves(self):
        for phase in ('static', 'family'):
            self.operations = MovingOperations(self.binding)
            self.operations.failures[phase] = Refusal('not_ready')
            with self.assertRaises(Refusal):
                self.run_reserved()
            self.assertNotIn('stop', self.operations.names())
            self.assert_no_commit()

    def test_pending_request_observation_never_reserves(self):
        self.operations.observations = [None] * 4
        with self.assertRaisesRegex(Refusal, 'bounded_observation'):
            self.run_reserved()
        self.assertNotIn('stop', self.operations.names())

    def test_early_race_resumes_and_waits_for_new_complete_on_same_handle(self):
        first = deepcopy(self.operations.candidate)
        newer = deepcopy(first)
        newer.update(complete_index=10, complete_sha256=digest('new-COMPLETE'))
        self.operations.candidate = newer
        self.operations.observations = [first, None, first, newer]
        self.run_reserved()
        names = self.operations.names()
        self.assertEqual(names.count('open'), 1)
        self.assertEqual(names.count('close'), 1)
        self.assertEqual(names.count('stop'), 2)
        self.assertEqual(names.count('resume'), 1)
        self.assertEqual(names.count('checkpoint'), 1)
        self.assertEqual(names.count('clear_gate'), 1)

    def test_guardian_expiry_during_preflight_is_terminal_and_gate_blocks_reentry(self):
        self.operations.proof_seconds = 31
        with self.assertRaises(BudgetExpired):
            self.run_reserved()
        self.assert_no_commit()
        self.assertTrue(self.operations.gate)
        with self.assertRaisesRegex(Refusal, 'no_blind_reserved_attempt_retry'):
            self.run_reserved()
        self.assertEqual(self.operations.names().count('stop'), 1)

    def test_initial_observer_race_resumes_same_handle_before_any_payload_work(self):
        first = deepcopy(self.operations.candidate)
        newer = dict(first, complete_index=10, complete_sha256=digest('new-COMPLETE'))
        self.operations.candidate = newer
        self.operations.observations = [first, ObservationRace('concurrent_publication'), newer]
        self.run_reserved()
        self.assertEqual(self.operations.names().count('open'), 1)
        self.assertEqual(self.operations.names().count('stop'), 2)
        self.assertEqual(self.operations.names().count('checkpoint'), 1)
        self.assertEqual(self.operations.names().count('resume'), 1)

    def test_margin_exhaustion_does_not_need_guardian_expiry_to_refuse(self):
        self.operations.proof_seconds, self.operations.receiver_seconds = 2, 26
        with self.assertRaises(BudgetExpired):
            self.run_reserved()
        self.assert_no_commit()
        self.assertTrue(self.operations.gate)

    def test_commit_guardian_rejects_late_command_without_second_reservation(self):
        self.operations.commits = [False]
        with self.assertRaisesRegex(BudgetExpired, 'guardian_expired'):
            self.run_reserved()
        self.assertEqual(self.operations.names().count('stop'), 1)
        self.assertNotIn('dispatch', self.operations.names())
        self.assertFalse(self.operations.exited)
        self.assertFalse(self.operations.stopped)

    def test_corruption_owner_failure_and_changed_receiver_are_terminal_resumptions(self):
        for phase in ('checkpoint', 'receiver', 'recheck', 'verify_receiver'):
            self.operations = MovingOperations(self.binding)
            self.operations.failures[phase] = Refusal('corruption_or_owner_refusal')
            with self.subTest(phase=phase), self.assertRaises(Refusal):
                self.run_reserved()
            self.assert_no_commit()
            self.assertTrue(self.operations.gate)

    def test_missing_full_optimizer_proof_is_never_a_commit(self):
        original = self.operations.verify_checkpoint
        self.operations.verify_checkpoint = lambda candidate: dict(original(candidate), optimizer_verified=False)
        with self.assertRaisesRegex(Refusal, 'full_actual_saved_state'):
            self.run_reserved()
        self.assert_no_commit()

    def test_moved_boundary_after_proof_and_mailbox_rewrite_refuse(self):
        first = deepcopy(self.operations.candidate)
        for changed in (None, dict(first, complete_sha256='f' * 64)):
            self.operations = MovingOperations(self.binding, [first, first, changed])
            with self.assertRaises(Refusal):
                self.run_reserved()
            self.assert_no_commit()
        first['mailbox'] = {'message': {'sha256': 'a' * 64}}
        altered = dict(first, mailbox={})
        self.operations = MovingOperations(self.binding, [first, first, altered])
        with self.assertRaisesRegex(Refusal, 'never_delete'):
            self.run_reserved()
        self.assert_no_commit()

    def test_arriving_inbox_survives_durable_final_check(self):
        first = deepcopy(self.operations.candidate)
        records = records_for(self.binding)
        append_record(records, self.binding, 'INBOX', dict(message=dict(id='new-parent-message',
            text='new-parent-message', split='TRAIN', actor='parent'), source_id='/life/stream/inbox/arriving',
            source_sha256=digest('mail')))
        inbox = selected(self.binding, records)
        inbox['mailbox'] = {'arriving': {'sha256': digest('mail')}}
        self.operations.observations = [first, first, inbox]
        self.operations.candidate = inbox
        result = self.run_reserved()
        self.assertEqual(result['exact_complete']['mailbox'], inbox['mailbox'])
        self.assertTrue(result['exact_complete']['durable'])

    def test_slow_final_audit_cannot_commit_after_budget(self):
        original = self.operations.record

        def slow_audit(kind, value):
            if kind == 'RETENTION_HANDOFF_INTENT':
                self.operations.clock += 29
            return original(kind, value)

        self.operations.record = slow_audit
        with self.assertRaises(BudgetExpired):
            self.run_reserved()
        self.assert_no_commit()

    def test_distinct_execution_approval_and_unchanged_cap(self):
        reviewed = policy()
        self.assertNotEqual(execution_digest(self.binding, self.prepared, self.authority, reviewed),
            digest(dict(binding=self.binding, prepared=self.prepared, authority=self.authority)))
        for seconds in (31, 0, True, float('nan'), float('inf')):
            with self.subTest(seconds=seconds), self.assertRaises(Refusal):
                validate_policy(dict(reviewed, stop_seconds=seconds))


class StaticAndHelperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=HERE, prefix='.reserved-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_static_receipt_binds_real_evidence_and_all_overhead_not_only_reader(self):
        binding, prepared, _ = inputs()
        prepared['new_plan']['physical'] = 0
        evidence = self.root / 'evidence.json'
        evidence.write_text('{"fixture":true}')
        path = self.root / 'STATIC.json'
        receipt = dict(schema='PAIR_RESERVED_PREFLIGHT_READINESS_V1', life_binding_sha256=digest(binding),
            prepared_sha256=digest(prepared), source_pins_sha256=digest(prepared['new_source_pins']),
            epoch_id=prepared['epoch_id'], deadline_unix=binding['hard_end_unix'], physical=0,
            checks={name: True for name in ('actual_saved_payload_CPU', 'actual_checkpoint_tail_CPU',
                'exact_source_control_tests', 'original_confinement_admission_available',
                'owner_transport_and_guard_cost_bounded')},
            reserved_total_seconds_upper_bound=25, evidence_pins={str(evidence): sha(evidence)})

        def verify():
            path.write_text(json.dumps(receipt))
            return verify_static_receipt(binding, prepared, dict(policy(),
                static_receipt_path=str(path), static_receipt_sha256=sha(path)))

        self.assertEqual(verify(), receipt)
        receipt['checks']['original_confinement_admission_available'] = False
        with self.assertRaisesRegex(Refusal, 'static_readiness'):
            verify()
        receipt['checks']['original_confinement_admission_available'] = True
        receipt['reserved_total_seconds_upper_bound'] = 28
        with self.assertRaisesRegex(Refusal, 'all_reserved_costs'):
            verify()
        receipt['reserved_total_seconds_upper_bound'] = 25
        evidence.write_text('tampered')
        with self.assertRaisesRegex(Refusal, 'evidence_bytes'):
            verify()

    def test_persistent_gate_only_cleared_for_acknowledged_early_race(self):
        operations = object.__new__(ReservedPairLinuxOperations)
        operations.review_gate = self.root / 'REVIEW.json'
        operations.binding = {'same': 'life'}
        operations.approved_execution_sha256 = 'a' * 64
        operations.attempt_sha256 = None
        operations.begin_reserved_attempt({'complete': 'candidate'})
        with self.assertRaisesRegex(Refusal, 'reconciliation'):
            operations.begin_reserved_attempt({'complete': 'candidate'})
        operations.finish_early_race()
        self.assertFalse(operations.review_gate.exists())

    def test_budget_clips_sequential_helpers_and_rejects_late_success(self):
        receiver = object.__new__(PairReceiver)
        receiver.prepared = {'new_plan': {}}
        clock = [0]
        receiver.reservation_budget = ReservationBudget(5, clock=lambda: clock[0])

        def slow_result(*arguments):
            clock[0] += 3
            return {'passed': True}

        receiver.probe_override = slow_result
        self.assertEqual(receiver._probe('checkpoint', {}), {'passed': True})
        self.assertEqual(receiver.reservation_budget.timeout(120), 2)
        with self.assertRaises(BudgetExpired):
            receiver._probe('tail', {})

    def test_owner_transport_timeout_is_clipped_and_has_no_inherited_handle(self):
        from parent_dependency_bridge import ParentDependencyBridge
        owner = ParentDependencyBridge(['reviewed-read-only-owner'], dependency_path='/cpu/DEPENDENCY.json',
            dependency_sha256='a' * 64, owner_source_pins={'/cpu/owner.py': 'b' * 64})
        owner.reservation_budget = ReservationBudget(.75, clock=lambda: .5)
        with patch('parent_dependency_bridge.subprocess.run',
                side_effect=subprocess.TimeoutExpired(['read-only-owner'], .25)) as run:
            with self.assertRaisesRegex(ValueError, 'owner_fence_recheck_failed'):
                owner.check({}, 'same-epoch')
        self.assertEqual(run.call_args.kwargs['timeout'], .25)
        self.assertTrue(run.call_args.kwargs['close_fds'])
        self.assertNotIn('pass_fds', run.call_args.kwargs)

    def test_probe_timeout_is_capped_helper_reaped_and_no_native_handle_inherited(self):
        receiver = object.__new__(PairReceiver)
        receiver.source = self.root
        receiver.control = self.root / 'control'
        receiver.prepared = {'new_plan': {}, 'new_source_pins': {}}
        receiver.probe_override = None
        receiver.python = sys.executable
        receiver.probe_timeout_seconds = 120
        receiver.reservation_budget = ReservationBudget(time.monotonic() + .5)
        descriptor = os.open(self.root / 'native-handle-sentinel', os.O_CREAT | os.O_RDWR, 0o600)
        self.addCleanup(os.close, descriptor)
        os.set_inheritable(descriptor, True)
        pidfile = self.root / 'helper.pid'
        helper = ('import os,pathlib,time; '
            f'pathlib.Path({str(pidfile)!r}).write_text(str(os.getpid())); '
            f'assert not pathlib.Path("/proc/self/fd/{descriptor}").exists(); time.sleep(30)')
        actual_run = subprocess.run

        def cpu_only(command, **arguments):
            self.assertLessEqual(arguments['timeout'], .5)
            self.assertTrue(arguments['close_fds'])
            self.assertNotIn('pass_fds', arguments)
            return actual_run([sys.executable, '-B', '-c', helper], **arguments)

        module = 'research_loop.workers.post_recovery_pair_retention_receiver_20260919.receiver'
        with patch(module + '.subprocess.run', side_effect=cpu_only), \
                patch.object(signal, 'pidfd_send_signal', side_effect=AssertionError('no native signals')):
            with self.assertRaisesRegex(Refusal, 'CPU_probe_timeout'):
                receiver._probe('checkpoint', {})
        self.assertTrue(pidfile.exists())
        self.assertFalse(Path('/proc', pidfile.read_text()).exists())
        failures = list(receiver.control.rglob('*.timeout.*.json'))
        self.assertEqual(len(failures), 1)
        self.assertTrue(json.loads(failures[0].read_text())['helper_killed_and_waited'])

    def test_default_builder_remains_unreserved_and_reserved_digest_is_required(self):
        from research_loop.workers.post_recovery_pair_retention_receiver_20260919.integration import build_operations
        binding, prepared, authority = inputs()
        module = 'research_loop.workers.post_recovery_pair_retention_receiver_20260919.integration'
        arguments = dict(cpu_receipt_path='/cpu', consumed_wall_receipt={}, python_executable=sys.executable,
            control_root=str(self.root), parent_owner_config={}, approved_execution_sha256=digest(
                dict(binding=binding, prepared=prepared, authority=authority)))
        with patch(module + '.ParentDependencyBridge'), patch(module + '.PairReceiver'), \
                patch(module + '.PairLinuxOperations') as default, patch(module + '.ReservedPairLinuxOperations') as reserved:
            build_operations(binding, prepared, authority, {}, **arguments)
            default.assert_called_once()
            reserved.assert_not_called()
            with self.assertRaisesRegex(Refusal, 'explicit_exact_execution'):
                build_operations(binding, prepared, authority, {}, **arguments, reserved_preflight_policy=policy())
            arguments['approved_execution_sha256'] = execution_digest(binding, prepared, authority, policy())
            build_operations(binding, prepared, authority, {}, **arguments, reserved_preflight_policy=policy())
            reserved.assert_called_once()


if __name__ == '__main__':
    unittest.main()
