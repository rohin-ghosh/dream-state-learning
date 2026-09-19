from copy import deepcopy
import json
from pathlib import Path
import signal
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

WORKER = Path(__file__).parent
sys.path.insert(0, str(WORKER.parent / 'post_recovery_retention_boundary_20260918'))
from test_boundary import JournalFixture, append_record
from test_plan_metadata import metadata_inputs
from research_loop.workers.post_recovery_retention_boundary_20260918.boundary import digest, read, read_boundary, sha
from receiver import PairReceiver, parent_handoff_contract, preservation, write_once
from ports import SEAM, proposed_ports
from pair_retention_runtime import bind_journal


class PairReceiverTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=WORKER)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fixture = JournalFixture(self.root)
        self.binding, self.prepared, self.authority, records, _, self.consumed = metadata_inputs(tail=False)
        self.fixture.records = records
        self.fixture.publish()
        self.binding['journal_root'] = str(self.fixture.root)
        self.candidate = read_boundary(self.binding)
        self.source = self.root / 'epoch' / 'source'
        (self.source / 'gpu').mkdir(parents=True)
        (self.source / 'gpu/r232_recovery.py').write_text('def install(plan):\n    if True:\n' + SEAM)
        runtime = WORKER.parent / 'rohin233_recovery_node4_20260918/checkpoint_tail_runtime.py'
        ports, _ = proposed_ports(self.source, runtime)
        for name, content in ports.items():
            (self.source / name).write_bytes(content)
        pins = {str(path.relative_to(self.source)): sha(path) for path in self.source.rglob('*.py')}
        for plan in (self.prepared['old_plan'], self.prepared['new_plan']):
            plan.update(root=str(self.root), physical=0, gpu_uuid='synthetic-device', lease_end_unix=20000,
                think_act_learn=dict(trial_id='same-life'))
        self.prepared['new_plan']['source_root'] = str(self.source)
        self.prepared['new_plan']['startup_context']['path'] = str(self.source / 'startup.json')
        self.prepared['new_source_pins'] = pins
        self.old = self.root / 'old_control'
        self.old.mkdir()
        write_once(self.old / 'PLAN.json', self.prepared['old_plan'])
        write_once(self.old / 'LEASE.json', dict(lease_end_unix=20000, hard_end_unix=10000))
        write_once(self.old / 'ALLOCATION.json', dict(physical=0, gpu_uuid='synthetic-device',
            builder_entry_pushed=True, builder_entry_logged=True, cpu_tests_passed=True))
        guard = dict(plan_path=str(self.old / 'PLAN.json'), plan_sha256=sha(self.old / 'PLAN.json'),
            lease_path=str(self.old / 'LEASE.json'), lease_sha256=sha(self.old / 'LEASE.json'),
            allocation_path=str(self.old / 'ALLOCATION.json'), allocation_sha256=sha(self.old / 'ALLOCATION.json'),
            copy_raw=str(self.root), hard_end_unix=10000, resume=True, host_sha256=digest('host'),
            next_reserved_unix=20000, source_pins=self.prepared['old_source_pins'], attempt_dir=str(self.old))
        write_once(self.old / 'GUARD.json', guard)
        self.binding['guard_path'] = str(self.old / 'GUARD.json')
        self.binding['guard_sha256'] = sha(self.old / 'GUARD.json')
        changes = {name: dict(before=self.prepared['old_source_pins'].get(name), after=pins.get(name))
            for name in set(pins) | set(self.prepared['old_source_pins'])
            if pins.get(name) != self.prepared['old_source_pins'].get(name)}
        self.staged = dict(new_source=str(self.source), old_guard_sha256=self.binding['guard_sha256'],
            new_source_pins=pins, changed=changes)
        self.cpu = self.root / 'CPU.json'
        write_once(self.cpu, dict(passed=True, source_pins=pins, no_GPU_calls=True,
            checkpoint_tail_port_passed=True, pair_controls_passed=True, synthetic_test_only=True))
        self.ledger = self.root / 'delivery_ledger.json'
        write_once(self.ledger, dict(delivered_ids=['preserved-message']))
        self.parent_proof = self.root / 'PARENT_DEPENDENCIES.json'
        write_once(self.parent_proof, dict(schema='PAIR_RETENTION_PARENT_DEPENDENCIES_V1',
            life_binding_sha256=digest(self.binding), source_epoch=self.prepared['epoch_id'], owner='synthetic-owner',
            delivery_fenced=True, inflight_deliveries=0, durable=True, preserve_existing_ledgers=True,
            automatic_pid_adoption=False, replay_delivered_messages=False, ledger_pins={str(self.ledger): sha(self.ledger)}))
        self.receiving = PairReceiver(self.binding, self.staged, cpu_receipt_path=self.cpu,
            consumed_wall_receipt=dict(record=self.consumed,
                intent=__import__('test_boundary').intents_for([self.consumed])[self.consumed['index']]),
            python_executable=sys.executable, checkpoint_probe=self.probe)
        self.receiving.parent_dependency_receipt_path = str(self.parent_proof)
        self.receiving.parent_owner = Mock(check=self.owner_check)
        self.receiving.verify_prepared(self.prepared)
        self.addCleanup(patch.stopall)
        patch.object(signal, 'pidfd_send_signal', side_effect=AssertionError('no live signals')).start()
        self.popen = patch('receiver.subprocess.Popen', side_effect=AssertionError('no live dispatch')).start()

    def owner_check(self, binding, epoch):
        receipt = read(self.parent_proof)
        if not all(sha(path) == expected for path, expected in receipt['ledger_pins'].items()):
            raise ValueError('unchanged_parent_ledgers_and_delivery_ids')
        return dict(path=str(self.parent_proof), sha256=sha(self.parent_proof), receipt=receipt)

    def test_missing_fresh_owner_bridge_refuses_before_preparation(self):
        self.receiving.parent_owner = None
        with self.assertRaisesRegex(ValueError, 'fresh_CPU_owner_bridge_required'):
            self.receiving.verify_prepared(self.prepared)
        self.popen.assert_not_called()

    def probe(self, mode, candidate, plan, selection):
        if mode == 'guard':
            return dict(validated=True, admission_bypassed=False, guard_sha256=sha(selection['guard_path']))
        return dict(restored_state_sha256=candidate['resume_state']['sha256'], head_sha256=candidate['head_sha256'],
            complete_index=candidate['complete_index'], complete_sha256=candidate['complete_sha256'],
            prefix_work='ALL_RETAINED_BYTES_HASHED_NO_HISTORICAL_BODY_JSON_REPLAY', read_only=True, journal_writes=0)

    def prepare(self, candidate=None):
        return self.receiving.prepare_receiver(candidate or self.candidate, self.prepared, {})

    def test_all_seven_hooks_are_concrete_and_preparation_never_dispatches(self):
        hooks = self.receiving.hooks()
        self.assertEqual(len(hooks.__dataclass_fields__), 7)
        receiver = self.prepare()
        self.receiving.verify_receiver(receiver, self.candidate)
        self.popen.assert_not_called()

    def test_local_epoch2_source_receipt_cannot_authorize_live_handoff(self):
        cpu = read(self.cpu)
        cpu['live_handoff_authorization'] = False
        self.cpu.write_text(json.dumps(cpu))
        with self.assertRaisesRegex(ValueError, 'local_source_CPU_is_not_live_handoff_proof'):
            self.receiving.verify_prepared(self.prepared)
        self.popen.assert_not_called()

    def test_parent_owner_proof_is_mandatory_and_never_auto_adopts_pid(self):
        contract = parent_handoff_contract(self.binding, self.prepared['epoch_id'])
        self.assertIsNone(contract['new_native'])
        self.assertFalse(contract['parent_rebind_allowed'])
        self.receiving.parent_dependency_receipt_path = None
        with self.assertRaisesRegex(ValueError, 'parent_owner_dependency_proof_required'):
            self.prepare()
        self.popen.assert_not_called()

    def test_parent_handoff_receipt_preserves_delivery_ledger_and_blocks_drift(self):
        receiver = self.prepare()
        handoff = read(receiver['parent_handoff_path'])
        self.assertEqual(handoff['old_native']['pid'], self.binding['pid'])
        self.assertIsNone(handoff['new_native'])
        self.assertFalse(handoff['parent_rebind_allowed'])
        self.assertEqual(read(self.ledger)['delivered_ids'], ['preserved-message'])
        self.ledger.write_text('{"delivered_ids": []}')
        with self.assertRaisesRegex(ValueError, 'unchanged_parent_ledgers'):
            self.receiving.verify_receiver(receiver, self.candidate)

    def test_plan_deadline_prompt_rows_and_copy_mapping_preserved(self):
        receiver = self.prepare()
        self.assertEqual(receiver['plan'], self.prepared['new_plan'])
        self.assertNotIn('authorized_wall_extension', receiver['plan'])
        self.assertNotIn('checkpoint_tail_recovery', receiver['plan'])
        guard = read(receiver['guard_path'])
        old = read(self.binding['guard_path'])
        for key in ('copy_raw', 'hard_end_unix', 'host_sha256', 'next_reserved_unix', 'resume'):
            self.assertEqual(guard[key], old[key])

    def test_exact_preservation_at_required_constructor_path(self):
        receiver = self.prepare()
        saved = read(self.source.parent / 'control/PRESERVATION.json')
        self.assertEqual(saved['checkpoint'], self.candidate['checkpoint'])
        self.assertEqual(saved['coherent_state'], self.candidate['resume_state'])
        self.assertEqual(saved['checkpoint_tail_selection']['complete_index'], self.candidate['complete_index'])
        self.assertEqual(receiver['preservation_sha256'], sha(self.source.parent / 'control/PRESERVATION.json'))

    def test_new_candidate_reanchors_and_preserves_prior_sidecar_evidence(self):
        old_receiver = self.prepare()
        append_record(self.fixture.records, self.binding, 'SLEEP_COMPLETE', deepcopy(self.fixture.records[-2]['document']))
        append_record(self.fixture.records, self.binding, 'R184_LEARN_COMPLETE', deepcopy(self.fixture.records[-2]['document']))
        self.fixture.publish()
        candidate = read_boundary(self.binding)
        receiver = self.prepare(candidate)
        self.assertEqual(read(self.source.parent / 'control/PRESERVATION.json')['complete_index'], 4)
        self.assertEqual(len(list(self.receiving.control.glob('PRESERVATION.*.json'))), 2)
        self.assertNotEqual(receiver['preservation_sha256'], old_receiver['preservation_sha256'])

    def test_unknown_source_or_cpu_provenance_refuses_before_sidecar(self):
        (self.source / 'gpu/extra.py').write_text('extra = True\n')
        with self.assertRaisesRegex(ValueError, 'source_closure'):
            self.prepare()
        self.assertFalse((self.receiving.control / 'PRESERVATION.json').exists())

    def test_full_replay_probe_or_guard_bypass_refuses(self):
        self.receiving.probe_override = lambda *args: dict(self.probe(*args), prefix_work='FULL_REPLAY')
        with self.assertRaisesRegex(ValueError, 'fast_checkpoint_tail'):
            self.prepare()
        self.receiving.probe_override = lambda *args: dict(self.probe(*args), admission_bypassed=True)
        with self.assertRaisesRegex(ValueError, 'guard_CPU_validation'):
            self.prepare()

    def test_guard_confinement_or_preservation_tamper_refuses(self):
        receiver = self.prepare()
        path = Path(receiver['guard_path'])
        changed = read(path)
        changed['host_sha256'] = digest('other-host')
        path.write_text(json.dumps(changed))
        with self.assertRaisesRegex(ValueError, 'immutable_receiving_artifacts'):
            self.receiving.verify_receiver(receiver, self.candidate)

    def test_unexited_token_cannot_dispatch(self):
        token = dict(old_native_exited=False)
        with self.assertRaisesRegex(ValueError, 'exited_handoff_token'):
            self.receiving.dispatch_once(token)
        self.popen.assert_not_called()

    def test_atomic_claim_prevents_duplicate_dispatch_even_after_launch_failure(self):
        receiver = self.prepare()
        token = dict(old_native_exited=True, life_binding_sha256=digest(self.binding), deadline_unix=10000,
            receiver=receiver, exact_complete=self.candidate, epoch_id=self.prepared['epoch_id'],
            new_source_pins=self.prepared['new_source_pins'])
        token['sha256'] = digest(token)
        with patch('receiver.time.time', return_value=1):
            with self.assertRaisesRegex(AssertionError, 'no live dispatch'):
                self.receiving.dispatch_once(token)
            with self.assertRaisesRegex(ValueError, 'dispatch_claim_exists'):
                self.receiving.dispatch_once(token)
        self.assertEqual(self.popen.call_count, 1)

    def test_source_port_has_one_narrow_runtime_seam_and_returns_separate_delta(self):
        base = self.root / 'port_base'
        (base / 'gpu').mkdir(parents=True)
        original = 'def install(plan):\n    if True:\n' + SEAM
        (base / 'gpu/r232_recovery.py').write_text(original)
        tail = WORKER.parent / 'rohin233_recovery_node4_20260918/checkpoint_tail_runtime.py'
        proposed, delta = proposed_ports(base, tail)
        self.assertEqual(set(delta), {'gpu/r232_recovery.py', 'gpu/pair_retention_runtime.py', 'gpu/checkpoint_tail_runtime.py'})
        self.assertEqual((base / 'gpu/r232_recovery.py').read_text(), original)
        for name, content in proposed.items():
            compile(content, name, 'exec')
        self.assertIsNone(delta['gpu/checkpoint_tail_runtime.py']['before'])

    def test_checkpoint_payloads_are_fsynced_bound_and_rechecked(self):
        directory = self.root / 'checkpoints/sleep_000004'
        (directory / 'adapter').mkdir(parents=True)
        (directory / 'adapter/adapter.bin').write_bytes(b'synthetic-adapter')
        (directory / 'optimizer_rng.pt').write_bytes(b'synthetic-optimizer-rng')
        candidate = deepcopy(self.candidate)
        candidate['checkpoint'].update(adapter_path=str(directory / 'adapter'),
            optimizer_rng_path=str(directory / 'optimizer_rng.pt'))
        write_once(directory / 'COMMIT.json', candidate['checkpoint'])
        self.receiving.probe_override = lambda *args: dict(adapter_verified=True, optimizer_verified=True,
            python_cpu_cuda_rng_verified=True, working_state_verified=True, no_GPU_calls=True)
        proof = self.receiving.verify_checkpoint(candidate)
        self.receiving.recheck_checkpoint(proof, candidate)
        self.assertTrue(proof['durable_files_and_directories'])
        (directory / 'optimizer_rng.pt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'unchanged_checkpoint_files'):
            self.receiving.recheck_checkpoint(proof, candidate)

    def test_runtime_uses_tail_scanner_and_records_epoch_under_original_writer_lock(self):
        receiver = self.prepare()
        token = dict(old_native_exited=True, receiver=receiver, exact_complete=self.candidate,
            epoch_id=self.prepared['epoch_id'], new_source_pins=self.prepared['new_source_pins'], deadline_unix=10000)
        token['sha256'] = digest(token)
        write_once(self.receiving.control / 'RETENTION_HANDOFF.json', token)
        candidate = self.candidate
        events = []

        class BaseJournal:
            def __init__(self, root, *, create=False):
                events.append('original_writer_lock_acquired')
                self._root_fd = root
                self._manifest = dict(journal_id=candidate['journal_id'])
                self._records_fd = 123
                self._state = self._scan()

            def _read_json(self, descriptor, name):
                if name == 'JOURNAL.json':
                    return self._manifest
                return next(record for record in candidate['records'] if record['index'] == int(name[:20]))

            def _ensure_open(self):
                pass

            def record(self, kind, document):
                events.append(kind)
                return document

            def close(self):
                events.append('closed')

        scanner = Mock(return_value=dict(index=candidate['head_index'] + 1, request=None, response=None,
            sleep_request=None, latest=dict(expected_sha256=candidate['resume_state']['sha256'])))
        module = types.ModuleType('gpu.checkpoint_tail_runtime')
        module.scan = scanner
        module.validate_selection = lambda selection, root, life: selection
        with patch.dict(sys.modules, {'gpu.checkpoint_tail_runtime': module}):
            journal_class = bind_journal(BaseJournal, receiver['plan'])
            journal_class(self.binding['journal_root'])
            self.assertEqual(events, ['original_writer_lock_acquired', 'RETENTION_SOURCE_ADOPTED'])
            self.assertEqual(scanner.call_count, 1)
            scanner.return_value['request'] = dict(pending=True)
            with self.assertRaisesRegex(ValueError, 'resolved_saved_state'):
                journal_class(self.binding['journal_root'])
            self.assertEqual(events[-1], 'closed')


if __name__ == '__main__':
    unittest.main()
