"""Synthetic offline prefix/admission tests on a disposable copy of exact source."""

import argparse
from copy import deepcopy
import importlib
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import source_checks as baseline


SOURCE = None
OPERATOR = Path(__file__).resolve().parent


class PrefixSourceTests(unittest.TestCase):
    def setUp(self):
        baseline.SOURCE = SOURCE
        self.fixture = baseline.PairSourceTests('test_exact_source_imports_and_single_r232_binding')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.approval = importlib.import_module('gpu.pair_prefix_authority')
        self.helper = importlib.import_module('gpu.immutable_prefix_proof')
        self.pins = {str(path.relative_to(SOURCE)): baseline.raw_sha(path) for path in SOURCE.rglob('*.py')}

    def create(self, physical=0):
        fixture = self.fixture
        fixture.boundary(physical)
        fixture.plan.update(source_root=str(SOURCE), root=str(fixture.journal.root.parent))
        fixture.control = SOURCE.parent / 'control'
        fixture.control.mkdir(exist_ok=True)
        epoch_path = fixture.root / 'SOURCE_EPOCH.json'
        baseline.put(epoch_path, dict(schema='PAIR_PREFIX_SOURCE_EPOCH_V1', epoch_id='synthetic-epoch4',
            source_root=str(SOURCE), source_pins_sha256=self.approval.digest(self.pins), deadline_unix=10000))
        source = dict(root=str(SOURCE), pins=self.pins, epoch=self.approval.reference(epoch_path))
        journal_type = fixture.base.__module__ + ':' + fixture.base.__qualname__
        time.sleep(self.helper.MINIMUM_QUIET_NS / 10**9 + 0.05)
        self.proof = self.helper.produce(fixture.journal, fixture.selection, source, journal_type)
        proof_path = fixture.root / 'PREFIX_PROOF.json'
        baseline.put(proof_path, self.proof)
        proof_ref = self.approval.reference(proof_path)
        producer = fixture.root / 'operator_only_prefix_producer.py'
        producer.write_text('raise RuntimeError("synthetic provenance only; not executable approval")\n')
        produced = fixture.root / 'PRODUCED.json'
        baseline.put(produced, dict(status='CANDIDATE_NOT_AUTHORIZATION', proof_path=str(proof_path),
            proof_sha256=proof_ref['sha256'], journal_writes=0, writer_lock_acquired=False))
        attempt = fixture.root / 'receiving'
        self.guard = dict(schema='R125_CONTINUAL_GUARD_V1', resume=True, copy_raw=str(fixture.journal.root.parent),
            source_pins=self.pins, attempt_dir=str(attempt), plan_path=str(attempt / 'PLAN.json'),
            plan_sha256='a' * 64, allocation_path=str(attempt / 'ALLOCATION.json'), allocation_sha256='b' * 64,
            physical=physical, hard_end_unix=10000, host_sha256='c' * 64)
        self.authority = dict(schema=self.approval.SCHEMA, status='MAIN_APPROVED_IMMUTABLE_PREFIX',
            epoch_id='synthetic-epoch4', life_binding_sha256='d' * 64, deadline_unix=10000, physical=physical,
            source=source, proof=proof_ref, producer=self.approval.reference(producer),
            producer_receipt=self.approval.reference(produced),
            selection_policy={key: value for key, value in fixture.selection.items()
                if key not in ('complete_index', 'complete_sha256')}, max_advance_records=2048,
            max_advance_bytes=1024**3, confinement_sha256=self.approval.confinement_digest(self.guard),
            namespace_policy='SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE',
            admission_derivation=self.approval.DERIVATION)
        self.authority_path = fixture.root / 'MAIN_APPROVED.json'
        baseline.put(self.authority_path, self.authority)
        self.approved = self.approval.reference(self.authority_path)
        self.finish_binding()

    def finish_binding(self):
        fixture = self.fixture
        guard = self.approval.selection_guard(self.approved, fixture.plan, self.pins, fixture.selection)
        path = fixture.root / 'SELECTED_GUARD.json'
        baseline.put(path, guard)
        self.binding = dict(schema='PAIR_PREFIX_SELECTION_BINDING_V1', authority=self.approved,
            selection_guard=self.approval.reference(path), selection_sha256=self.approval.digest(fixture.selection))
        cpu_path = fixture.root / 'CPU.json'
        self.base_cpu = fixture.root / 'BASE_CPU.json'
        baseline.put(self.base_cpu, dict(passed=True, source_pins=self.pins, pair_prefix_authority=self.approved,
            actual_namespace_route_tested=False, synthetic_only=True))
        baseline.put(cpu_path, self.approval.derive_cpu_receipt(self.approval.reference(self.base_cpu), self.approved,
            fixture.plan, self.pins, fixture.selection, self.binding))
        allocation = dict(plan_sha256=self.guard['plan_sha256'], cpu_receipt_path=str(cpu_path),
            cpu_receipt_sha256=baseline.raw_sha(cpu_path))
        baseline.put(Path(self.guard['allocation_path']), allocation)
        self.guard['allocation_sha256'] = baseline.raw_sha(self.guard['allocation_path'])
        self.guard_path = fixture.root / 'GUARD.json'
        baseline.put(self.guard_path, self.guard)
        fixture.token.update(epoch_id='synthetic-epoch4', life_binding_sha256='d' * 64,
            new_source_pins=self.pins)
        fixture.token['receiver'].update(plan=fixture.plan, plan_sha256=self.approval.digest(fixture.plan),
            prefix_binding=self.binding, guard_path=str(self.guard_path),
            artifact_pins={str(self.guard_path): baseline.raw_sha(self.guard_path)})
        fixture.save_token()

    def scan(self):
        fixture = self.fixture
        with self.approval.admitted_prefix(self.guard, fixture.plan, guard_path=self.guard_path):
            return fixture.tail.scan(fixture.journal, fixture.selection,
                prefix_proof=self.approval.reader_argument(fixture.plan, fixture.token, fixture.selection),
                prefix_admission=self.approval.admission_argument(fixture.plan, fixture.token, fixture.selection))

    def open(self):
        fixture = self.fixture
        fixture.journal.close()
        with self.approval.admitted_prefix(self.guard, fixture.plan, guard_path=self.guard_path):
            received = fixture.runtime.bind_journal(fixture.base, fixture.plan)(fixture.journal.root)
        self.addCleanup(received.close)
        return received

    def test_pair_preflight_and_startup_same_selected_proof(self):
        self.create()
        fixture = self.fixture
        argument = self.approval.verify_selection_binding(self.binding, self.approved,
            fixture.plan, self.pins, fixture.selection)
        expected = self.scan()
        received = self.open()
        self.assertEqual(received._state['latest'], expected['latest'])
        self.assertEqual(received.checkpoint_tail_receipt['prefix_proof']['guard_sha256'], argument['guard_sha256'])
        self.assertEqual(received.checkpoint_tail_receipt['prefix_proof']['consumer_context']['mode'],
            self.helper.CROSS_NAMESPACE)

    def test_frozen_control_stays_zero_update(self):
        self.create(1)
        received = self.open()
        self.assertEqual(self.fixture.candidate['checkpoint']['optimizer_steps'], 0)
        self.assertEqual(received._state['latest']['expected_sha256'], self.fixture.candidate['resume_state']['sha256'])

    def test_changed_namespace_requires_explicit_original_admission_and_exact_fs(self):
        self.create()
        fixture = self.fixture
        environment = self.helper.environment()
        environment['mount_namespace']['ino'] += 7
        argument = dict(guard_path=self.binding['selection_guard']['path'],
            guard_sha256=self.binding['selection_guard']['sha256'])
        with patch.object(self.helper, 'environment', return_value=environment):
            with self.assertRaisesRegex(ValueError, 'independent_original_admission_required'):
                fixture.tail.scan(fixture.journal, fixture.selection, prefix_proof=argument)
            received = self.open()
        receipt = received.checkpoint_tail_receipt['prefix_proof']['consumer_context']
        self.assertNotEqual(receipt['producer_environment'], receipt['consumer_environment'])

    def test_new_boot_even_with_main_approval_refuses(self):
        self.create()
        environment = self.helper.environment()
        environment['boot_id'] = 'other-boot'
        with patch.object(self.helper, 'environment', return_value=environment), \
                self.assertRaisesRegex(ValueError, 'same_kernel_boot'):
            self.open()

    def test_no_child_or_arbitrary_guard_field_authority(self):
        self.create()
        fixture = self.fixture
        with self.assertRaisesRegex(ValueError, 'original_validated_admission_context'):
            fixture.runtime.bind_journal(fixture.base, fixture.plan)
        with self.assertRaisesRegex(ValueError, 'arbitrary_guard_field'):
            with self.approval.admitted_prefix(dict(self.guard, pair_prefix_authority=self.approved),
                    fixture.plan, guard_path=self.guard_path):
                pass

    def test_source_file_replaced_with_identical_bytes_refuses(self):
        self.create()
        path = SOURCE / 'gpu/pair_prefix_authority.py'
        temporary = path.with_suffix('.swap')
        temporary.write_bytes(path.read_bytes())
        os.replace(temporary, path)
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.open()

    def test_prefix_record_or_intent_mutation_refuses(self):
        self.create()
        path = self.fixture.journal.root / 'records/00000000000000000000.intent.json'
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'prefix_record_or_intent_changed'):
            self.open()

    def test_registered_and_unregistered_new_INBOX_survive_startup(self):
        self.create()
        fixture = self.fixture
        registered = fixture.inbox('registered-after-prehash')
        fixture.journal.read_inbox()
        unregistered = fixture.inbox('unregistered-before-open')
        received = self.open()
        self.assertIn('registered-after-prehash', received._state['inbox'])
        self.assertTrue(registered.exists() and unregistered.exists())
        self.assertIn('parent:inbox:unregistered-before-open', {message.event_id for message in received.read_inbox()})

    def test_forward_complete_new_INBOX_raw_extension_and_exact_state(self):
        self.create()
        fixture = self.fixture
        origin = fixture.selection['complete_index']
        between = fixture.inbox('between-A-and-B')
        fixture.journal.read_inbox()
        fixture.step()
        fixture.step()
        checkpoint = deepcopy(fixture.candidate['checkpoint'])
        receipt = dict(status='COMPLETE', cycle=2, optimizer_steps=checkpoint['optimizer_steps'],
            new_row_sha256=[row['source_sha256'] for row in fixture.stream.pending_rows()],
            checkpoint=checkpoint, checkpoint_sha256=checkpoint['checkpoint_sha256'])
        fixture.stream.pending = 'sleep:' + fixture.digest(receipt['new_row_sha256'])
        fixture.journal.record('SLEEP_REQUEST', dict(cycle=2, resume_state=fixture.stream.checkpoint()))
        fixture.stream.pending = None
        fixture.stream.commit_sleep(receipt, fixture.journal.record)
        fixture.selection.update(complete_index=fixture.journal._state['index'] - 1,
            complete_sha256=fixture.journal._state['previous'])
        learned = fixture.journal.record('R184_LEARN_COMPLETE', dict(cycle=2, status='COMPLETE',
            checkpoint_sha256=checkpoint['checkpoint_sha256']))
        fixture.candidate.update(resume_state=fixture.stream.checkpoint(),
            complete_index=fixture.selection['complete_index'], complete_sha256=fixture.selection['complete_sha256'],
            learn_sha256=learned['sha256'])
        fixture.preservation.update(coherent_state=fixture.candidate['resume_state'])
        self.finish_binding()
        new = fixture.inbox('new-after-B')
        fixture.journal.read_inbox()
        unregistered = fixture.inbox('unregistered-after-B')
        expected = fixture.tail.scan(fixture.journal, fixture.selection)
        with patch.object(fixture.tail, 'hash_record', wraps=fixture.tail.hash_record) as hashed:
            actual = self.scan()
        self.assertEqual(actual, expected)
        self.assertEqual([call.args[1] for call in hashed.call_args_list], list(range(origin + 1, actual['index'])))
        received = self.open()
        self.assertEqual(received._state['latest'], actual['latest'])
        self.assertTrue(all(path.exists() for path in (between, new, unregistered)))
        self.assertIn('parent:inbox:unregistered-after-B', {event.event_id for event in received.read_inbox()})

    def test_changed_B_clause_or_test_evidence_cannot_be_resealed_as_derivation(self):
        self.create()
        fixture = self.fixture
        allocation_path = Path(self.guard['allocation_path'])
        allocation = json.loads(allocation_path.read_bytes())
        cpu_path = Path(allocation['cpu_receipt_path'])
        original = json.loads(cpu_path.read_bytes())
        for field, value in (('pair_prefix_admission', {}), ('synthetic_only', False),
                ('pair_prefix_selection', {}), ('extra_unapproved_CPU_fact', True)):
            baseline.put(cpu_path, dict(original, **{field: value}))
            allocation['cpu_receipt_sha256'] = baseline.raw_sha(cpu_path)
            baseline.put(allocation_path, allocation)
            self.guard['allocation_sha256'] = baseline.raw_sha(allocation_path)
            baseline.put(self.guard_path, self.guard)
            fixture.token['receiver']['artifact_pins'][str(self.guard_path)] = baseline.raw_sha(self.guard_path)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'only_approved_B_clause_derivation'):
                self.scan()

    def test_default_helper_remains_same_namespace_only(self):
        self.create()
        fixture = self.fixture
        default = self.helper.guard_candidate(self.proof, str(fixture.root / 'PREFIX_PROOF.json'),
            baseline.raw_sha(fixture.root / 'PREFIX_PROOF.json'))
        self.assertEqual(default['consumer_context_mode'], self.helper.SAME_NAMESPACE)
        path = fixture.root / 'DEFAULT_GUARD.json'
        baseline.put(path, default)
        argument = dict(guard_path=str(path), guard_sha256=baseline.raw_sha(path))
        expected = fixture.tail.scan(fixture.journal, fixture.selection)
        self.assertEqual(fixture.tail.scan(fixture.journal, fixture.selection, prefix_proof=argument), expected)
        environment = self.helper.environment()
        environment['mount_namespace']['ino'] += 1
        with patch.object(self.helper, 'environment', return_value=environment), \
                self.assertRaisesRegex(ValueError, 'same_trusted_environment'):
            fixture.tail.scan(fixture.journal, fixture.selection, prefix_proof=argument)

    def test_cloned_journal_at_original_path_is_not_original_objects(self):
        self.create()
        fixture = self.fixture
        fixture.journal.close()
        saved = fixture.root / 'original-stream'
        fixture.journal.root.rename(saved)
        shutil.copytree(saved, fixture.journal.root)
        with self.assertRaisesRegex(ValueError, 'original_directories_or_manifest_changed'):
            self.open()

    def test_raw_new_tail_corruption_refuses(self):
        self.create()
        fixture = self.fixture
        path = fixture.journal.root / 'records' / f'{fixture.selection["complete_index"] + 1:020d}.json'
        path.write_bytes(path.read_bytes().replace(b'R184_LEARN_COMPLETE', b'R184_LEARN_CORRUPT!'))
        with self.assertRaises(ValueError):
            self.scan()

    def test_source_epoch_same_bytes_new_inode_refuses(self):
        self.create()
        path = self.fixture.root / 'SOURCE_EPOCH.json'
        replacement = path.with_suffix('.replacement')
        replacement.write_bytes(path.read_bytes())
        replacement.replace(path)
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.scan()

    def test_mutation_during_raw_tail_scan_refuses(self):
        self.create()
        fixture = self.fixture
        original = fixture.tail.hash_record
        changed = False

        def mutate(journal, index):
            nonlocal changed
            result = original(journal, index)
            if not changed:
                changed = True
                path = journal.root / 'records/00000000000000000000.intent.json'
                path.write_bytes(path.read_bytes() + b' ')
            return result

        with patch.object(fixture.tail, 'hash_record', side_effect=mutate), \
                self.assertRaisesRegex(ValueError, 'prefix_record_or_intent_changed'):
            self.scan()

    def test_new_unselected_current_sidecar_is_not_silently_ignored(self):
        self.create()
        baseline.put(self.fixture.journal.root / 'correction_ledger.json', {'invalid': 'must-refuse'})
        with self.assertRaisesRegex(ValueError, 'current_sidecars'):
            self.open()

    def test_approval_and_guard_chain_tampering_refuse(self):
        self.create()
        self.authority_path.write_bytes(self.authority_path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'reference_bytes'):
            self.open()

    def test_unchanged_writer_lock_blocks_open_before_any_adoption(self):
        self.create()
        fixture = self.fixture
        with self.approval.admitted_prefix(self.guard, fixture.plan, guard_path=self.guard_path):
            receiving = fixture.runtime.bind_journal(fixture.base, fixture.plan)
            with self.assertRaises(BlockingIOError):
                receiving(fixture.journal.root)

    def test_original_guard_validation_and_confinement_remain_in_source(self):
        content = (SOURCE / 'gpu/r205_runtime.py').read_text()
        self.assertIn('config, plan = guard.validate(args.config)', content)
        self.assertIn('with admitted_prefix(config, plan, guard_path=args.config)', content)
        self.assertIn('guard.native_entry(args.config)', content)
        self.assertIn('fresh_privileged_admission', content)
        self.assertIn('--property=DevicePolicy=strict', content)


def main():
    global SOURCE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    args = parser.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU_only_prefix_source_checks_required')
    with tempfile.TemporaryDirectory(prefix='pair-prefix-cpu-') as temporary:
        SOURCE = Path(temporary) / 'epoch/source'
        shutil.copytree(args.source, SOURCE)
        for path in SOURCE.rglob('*'):
            path.chmod(0o755 if path.is_dir() else 0o644)
        SOURCE.chmod(0o755)
        sys.path.insert(0, str(SOURCE))
        with patch('subprocess.Popen', side_effect=AssertionError('no_dispatch')), \
                patch('os.kill', side_effect=AssertionError('no_native_signals')):
            result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(
                unittest.defaultTestLoader.loadTestsFromTestCase(PrefixSourceTests))
    print(json.dumps(dict(passed=result.wasSuccessful(), tests_run=result.testsRun, errors=len(result.errors),
        failures=len(result.failures), synthetic_only=True, no_GPU_calls=True, native_signals=[],
        actual_namespace_route_tested=False, live_handoff_authorization=False), sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
