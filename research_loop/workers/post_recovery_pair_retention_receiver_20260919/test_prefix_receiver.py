from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

import prefix_receiver as implementation
from prefix_authority import reference
from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import Refusal, digest, read, sha
from receiver import write_once
import test_receiver as baseline


class PrefixReceivingTests(unittest.TestCase):
    def setUp(self):
        fixture = baseline.PairReceiverTests('test_all_seven_hooks_are_concrete_and_preparation_never_dispatches')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.approved = dict(path=str(fixture.root / 'SYNTHETIC_AUTHORITY.json'), sha256='a' * 64)
        cpu = read(fixture.cpu)
        cpu['pair_prefix_authority'] = self.approved
        fixture.cpu.write_text(json.dumps(cpu))
        self.receiver = implementation.PrefixPairReceiver(fixture.binding, fixture.staged,
            prefix_authority=self.approved, cpu_receipt_path=fixture.cpu,
            consumed_wall_receipt=fixture.receiving.consumed, python_executable=sys.executable,
            parent_dependency_receipt_path=str(fixture.parent_proof), parent_owner=fixture.receiving.parent_owner,
            checkpoint_probe=self.probe)
        plan = fixture.prepared['new_plan']
        self.authority = dict(proof=dict(path=str(fixture.root / 'proof.json'), sha256='b' * 64),
            namespace_policy='SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE',
            selection_policy=dict(policy='R233_PINNED_COMPLETE_TAIL_V1', root=fixture.binding['journal_root'],
                journal_id=fixture.binding['journal_id'], life_id=plan['think_act_learn']['trial_id'],
                max_tail_records=2048, max_tail_bytes=1024**3, sidecars=[], persist_complete_anchors=False))
        self.load = patch.object(implementation, 'load_authority', return_value=(self.authority, {})).start()
        self.addCleanup(patch.stopall)
        self.calls = []
        self.mutate = None

    def probe(self, mode, candidate, plan, specification):
        fixture = self.fixture
        self.calls.append(mode)
        if mode == 'prefix-admission':
            guard_path = fixture.root / 'SELECTED_GUARD.json'
            write_once(guard_path, dict(synthetic_only=True, complete_index=candidate['complete_index']))
            self.binding = dict(schema='PAIR_PREFIX_SELECTION_BINDING_V1', authority=self.approved,
                selection_guard=reference(guard_path), selection_sha256=digest(specification['selection']))
            cpu = dict(read(fixture.cpu), pair_prefix_cpu_parent=reference(fixture.cpu),
                pair_prefix_selection=self.binding, pair_prefix_admission=dict(synthetic_only=True))
            write_once(specification['cpu_path'], cpu)
            self.cpu_reference = reference(specification['cpu_path'])
            return dict(prefix_binding=self.binding, cpu=self.cpu_reference,
                admission_granted=False, checkpoint_tail_validated=False)
        if mode == 'guard':
            self.assertEqual(self.calls, ['prefix-admission', 'guard'])
            guard = read(specification['guard_path'])
            allocation = read(guard['allocation_path'])
            self.assertEqual(allocation['cpu_receipt_sha256'], self.cpu_reference['sha256'])
            self.assertNotIn('pair_prefix_authority', guard)
            return fixture.probe(mode, candidate, plan, specification)
        self.assertEqual(mode, 'tail')
        self.assertEqual(self.calls, ['prefix-admission', 'guard', 'tail'])
        self.assertEqual(specification['prefix_binding'], self.binding)
        prefix = dict(guard_path=self.binding['selection_guard']['path'],
            guard_sha256=self.binding['selection_guard']['sha256'], proof_path=self.authority['proof']['path'],
            proof_sha256=self.authority['proof']['sha256'], full_raw_extension_verified=True,
            full_raw_tail_verified=True, implicit_fallback=False, consumer_context=dict(
                mode=self.authority['namespace_policy'], producer_environment=dict(boot_id='synthetic-boot'),
                consumer_environment=dict(boot_id='synthetic-boot'),
                admission=dict(self.cpu_reference, field_path=['pair_prefix_admission'])))
        result = dict(fixture.probe(mode, candidate, plan, specification), prefix_proof=prefix,
            prefix_binding=self.binding, prefix_work='EXTERNALLY_PINNED_PREHASH_PLUS_METADATA_AND_RAW_EXTENSION')
        if self.mutate:
            self.mutate(result)
        return result

    def prepare(self):
        return self.receiver.prepare_receiver(self.fixture.candidate, self.fixture.prepared, {})

    def test_original_chain_precedes_tail_and_seven_hooks_keep_pending_parent_contract(self):
        receiver = self.prepare()
        self.receiver.verify_receiver(receiver, self.fixture.candidate)
        self.assertEqual(len(self.receiver.hooks().__dataclass_fields__), 7)
        self.assertFalse(receiver['parent_rebind_allowed'])
        self.assertEqual(receiver['deadline_unix'], self.fixture.binding['hard_end_unix'])
        parent = read(receiver['parent_handoff_path'])
        self.assertFalse(parent['automatic_pid_adoption'])
        self.assertIsNone(parent['new_native'])
        self.assertEqual(read(self.fixture.ledger)['delivered_ids'], ['preserved-message'])
        self.fixture.popen.assert_not_called()

    def test_wrong_scan_admission_refuses_without_preservation_or_dispatch(self):
        self.mutate = lambda result: result['prefix_proof']['consumer_context'].update(admission=None)
        with self.assertRaisesRegex(Refusal, 'exact_original_admission'):
            self.prepare()
        self.assertFalse((self.receiver.control / 'PRESERVATION.json').exists())
        self.fixture.popen.assert_not_called()

    def test_wrong_selected_guard_refuses_without_fallback(self):
        self.mutate = lambda result: result['prefix_proof'].update(guard_sha256='0' * 64)
        with self.assertRaisesRegex(Refusal, 'same_approved_proof'):
            self.prepare()
        self.fixture.popen.assert_not_called()

    def test_wrong_state_refuses_before_handoff(self):
        self.mutate = lambda result: result.update(restored_state_sha256='0' * 64)
        with self.assertRaisesRegex(Refusal, 'actual_bound_prefix'):
            self.prepare()

    def test_missing_parent_owner_or_unapproved_CPU_has_no_probe(self):
        self.receiver.parent_owner = None
        with self.assertRaisesRegex(Refusal, 'fresh_CPU_owner_bridge'):
            self.prepare()
        self.assertEqual(self.calls, [])

    def test_helper_deadline_expiry_has_no_retry_or_native_signals(self):
        self.receiver.verify_prepared(self.fixture.prepared)
        self.receiver.probe_override = None
        budget = Mock()
        budget.timeout.return_value = 0.01
        self.receiver.reservation_budget = budget
        error = subprocess.TimeoutExpired(['CPU-helper'], 0.01)
        with patch.object(implementation.subprocess, 'run', side_effect=error) as run:
            with self.assertRaisesRegex(Refusal, 'no_replay_fallback_or_automatic_retry'):
                self.receiver._probe('tail', self.fixture.candidate, dict(selection={}))
        self.assertEqual(run.call_count, 1)
        self.assertTrue(run.call_args.kwargs['close_fds'])
        self.assertEqual(run.call_args.kwargs['timeout'], 0.01)
        self.assertEqual(run.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'], '')
        self.assertTrue(list(self.receiver.control.glob('cpu_requests/*.failure.*.json')))
        self.fixture.popen.assert_not_called()

    def test_expiry_after_successful_helper_still_refuses(self):
        self.receiver.verify_prepared(self.fixture.prepared)
        self.receiver.probe_override = None
        budget = Mock()
        budget.timeout.return_value = 0.1
        budget.check.side_effect = Refusal('synthetic_guard_expired')
        self.receiver.reservation_budget = budget
        with patch.object(implementation.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '{}', '')):
            with self.assertRaisesRegex(Refusal, 'synthetic_guard_expired'):
                self.receiver._probe('tail', self.fixture.candidate, dict(selection={}))
        self.fixture.popen.assert_not_called()

    def test_reserved_static_requires_actual_confined_route_not_host_observer(self):
        instance = object.__new__(implementation.PrefixReservedOperations)
        instance.receiving = self.receiver
        policy = dict(static_receipt_path=str(self.fixture.root / 'STATIC.json'), static_receipt_sha256='0' * 64)
        for check in (False, None):
            receipt = dict(pair_prefix_authority=self.approved, checks=dict(actual_confined_prefix_route_CPU=check))
            with patch.object(implementation.ReservedPairLinuxOperations, 'verify_static'), \
                    patch.object(implementation, 'document', return_value=receipt), \
                    self.assertRaisesRegex(Refusal, 'real_confined_route'):
                instance.verify_static(self.fixture.prepared, policy)


if __name__ == '__main__':
    unittest.main()
