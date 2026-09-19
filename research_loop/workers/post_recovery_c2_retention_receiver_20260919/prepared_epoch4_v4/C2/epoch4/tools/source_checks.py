"""Standalone synthetic tests importing only one exact C2 epoch2 closure."""

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import time
import types
import unittest
from unittest.mock import patch


SOURCE = None
PINS = None
FIXTURE = None
METRICS = []
TRIAL = 'C2_R216_current_conversation_maintenance'
DEADLINE = 1789927200


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + '\n')


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


class ExactSourceTests(unittest.TestCase):
    def setUp(self):
        self.journal_module = importlib.import_module('gpu.orch_r125_stream_journal')
        self.runtime = importlib.import_module('gpu.c2_retention_runtime')
        self.reader = importlib.import_module('gpu.checkpoint_tail_runtime')
        self.digest = self.runtime.digest
        FIXTURE.StreamJournalTests.setUp(self)
        self.journal.close()
        self.root = self.root.parent / 'life/stream'
        self.root.parent.mkdir()
        self.journal = self.journal_module.StreamJournal(self.root, create=True)
        self.addCleanup(self.journal.close)
        self.stream.deadline_unix = DEADLINE
        self.parent()
        self.step(incoming=self.journal.read_inbox())
        self.step()
        ledger = self.journal.record('R197_CORRECTION_CYCLE', dict(ledger=dict(
            schema='R197_CORRECTION_LEDGER_V1', life_id=TRIAL, cycles=[])))
        self.journal_module.StreamJournal._publish(self.journal._root_fd, 'correction_ledger.json',
            dict(record_index=ledger['index'], record_sha256=ledger['sha256']))
        checkpoint = dict(optimizer_steps=8, checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64))
        receipt = self.receipt()
        receipt.update(checkpoint=checkpoint, cycle=1)
        self.stream.commit_sleep(receipt, self.journal.record)
        complete_index = self.journal._state['index'] - 1
        complete_sha = self.journal._state['previous']
        learned = self.journal.record('R184_LEARN_COMPLETE', dict(cycle=1, checkpoint=checkpoint))
        records = [json.loads((self.root / 'records' / f'{index:020d}.json').read_bytes())
            for index in range(complete_index, learned['index'] + 1)]
        self.candidate = dict(journal_id=self.journal._manifest['journal_id'],
            complete_index=complete_index, complete_sha256=complete_sha, learn_index=learned['index'],
            learn_sha256=learned['sha256'], head_index=learned['index'], head_sha256=learned['sha256'],
            resume_state=self.stream.checkpoint(), checkpoint=checkpoint, records=records,
            mailbox={str(path): dict(sha256=sha(path)) for path in (self.root / 'inbox').iterdir()})
        self.selection = dict(policy=self.reader.POLICY, root=str(self.root),
            journal_id=self.candidate['journal_id'], complete_index=complete_index,
            complete_sha256=complete_sha, life_id=TRIAL, max_tail_records=2048,
            max_tail_bytes=1073741824, persist_complete_anchors=True,
            sidecars=[dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=True)])
        self.mirror = self.root.parent.parent / 'receiving/source'
        shutil.copytree(SOURCE, self.mirror)
        self.plan = dict(source_root=str(self.mirror), root=str(self.root.parent), hard_end_unix=DEADLINE,
            physical=1, gpu_uuid='GPU-7fc4e5b2-060c-ada8-8f91-3fe262c3573c',
            think_act_learn=dict(trial_id=TRIAL), checkpoint_tail_recovery=self.selection)
        receiver = dict(plan=self.plan, plan_sha256=self.digest(self.plan), source_epoch='synthetic-C2',
            dispatcher_module='gpu.r188_node5_confinement', same_journal_root=str(self.root))
        self.token = dict(schema='RETENTION_HANDOFF_TOKEN_V1', old_native_exited=True,
            deadline_unix=DEADLINE, no_cold_start=True, no_unresolved_work_replayed=True,
            epoch_record_required_before_first_THINK=True, epoch_id='synthetic-C2',
            exact_complete=self.candidate, receiver=receiver, new_source_pins=PINS)
        self.token_path = self.mirror.parent / 'control/RETENTION_HANDOFF.json'
        self.save_token()

    def step(self, *arguments, **keywords):
        return FIXTURE.StreamJournalTests.step(self, *arguments, **keywords)

    def receipt(self):
        return FIXTURE.StreamJournalTests.receipt(self)

    def parent(self, *arguments, **keywords):
        return FIXTURE.StreamJournalTests.parent(self, *arguments, **keywords)

    def save_token(self):
        self.token['sha256'] = self.digest({key: value for key, value in self.token.items() if key != 'sha256'})
        put(self.token_path, self.token)

    def snapshot(self):
        return {str(path.relative_to(self.root)): sha(path) for path in self.root.rglob('*') if path.is_file()}

    def open_receiver(self, close=True):
        if close:
            self.journal.close()
        wrapper = self.runtime.bind_journal(self.journal_module.StreamJournal, self.plan)
        journal = wrapper(self.root, checkpoint_tail=self.selection)
        self.addCleanup(journal.close)
        return journal

    def test_before_model_source_adoption_same_saved_state_and_old_bytes(self):
        before = self.snapshot()
        started = time.monotonic()
        journal = self.open_receiver()
        METRICS.append(dict(kind='synthetic_actual_source_open', elapsed_seconds=time.monotonic() - started,
            raw_record_bytes_hashed=journal.checkpoint_tail_receipt['raw_record_bytes_hashed']))
        record = json.loads((self.root / 'records' / f"{journal._state['index'] - 1:020d}.json").read_bytes())
        self.assertEqual(record['kind'], 'RETENTION_SOURCE_ADOPTED')
        self.assertEqual(record['document']['handoff_sha256'], self.token['sha256'])
        self.assertEqual(journal.latest_checkpoint()['expected_sha256'], self.candidate['resume_state']['sha256'])
        after = self.snapshot()
        self.assertTrue(all(after[name] == value for name, value in before.items()))
        self.assertEqual(len(after), len(before) + 2)

    def test_retains_exclusive_writer_lock(self):
        before = self.snapshot()
        with self.assertRaises((BlockingIOError, ValueError)):
            self.open_receiver(close=False)
        self.assertEqual(before, self.snapshot())

    def test_no_duplicate_source_adoption(self):
        self.open_receiver().close()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'no_work_before_C2_source_adoption'):
            self.open_receiver()
        self.assertEqual(before, self.snapshot())

    def test_wrong_LEARN_refuses(self):
        self.candidate['learn_sha256'] = '0' * 64
        self.save_token()
        with self.assertRaisesRegex(ValueError, 'same_C2_driver_LEARN_completion'):
            self.open_receiver()

    def test_pending_tail_cannot_adopt(self):
        def fail(*arguments, **keywords):
            raise RuntimeError('synthetic-interruption')
        with self.assertRaises(RuntimeError):
            self.step(generate_call=fail)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'exact_resolved_C2_saved_state'):
            self.open_receiver()
        self.assertEqual(before, self.snapshot())

    def test_new_INBOX_preserved(self):
        path = self.parent(name='queued.json', identifier='queued-parent', text='Keep this message.')
        self.journal.record('INBOX', dict(message=json.loads(path.read_bytes()), source_id=str(path), source_sha256=sha(path)))
        self.assertEqual(len(self.open_receiver().read_inbox()), 2)

    def test_original_mailbox_rewrite_refuses(self):
        Path(next(iter(self.candidate['mailbox']))).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'preserve_C2_original_parent_mailbox_bytes'):
            self.open_receiver()

    def test_source_tampering_refuses(self):
        path = self.mirror / 'gpu/c2_retention_runtime.py'
        path.chmod(0o600)
        path.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'exact_adopted_receiving_source_closure'):
            self.open_receiver()

    def test_old_native_alive_and_wall_reapply_refuse(self):
        self.token['old_native_exited'] = False
        self.save_token()
        with self.assertRaisesRegex(ValueError, 'exact_exited_C2_handoff_token'):
            self.open_receiver()
        self.plan['authorized_wall_extension'] = {}
        with self.assertRaisesRegex(ValueError, 'no_reapplied_wall_authorization'):
            self.open_receiver()

    def test_exact_native_entry_seam_and_learned_not_frozen(self):
        data = (SOURCE / 'gpu/orch_r125_continual_native.py').read_bytes()
        added = b'    from gpu.c2_retention_runtime import bind_journal\n    StreamJournal = bind_journal(StreamJournal, plan)\n'
        self.assertEqual(data.count(added), 1)
        self.assertEqual(hashlib.sha256(data.replace(added, b'')).hexdigest(),
            '1bf18d5f34d2f027be1c79120ec654afe9869e647150245a29c8a19ebda81ff6')
        self.assertEqual(self.plan['physical'], 1)
        self.assertGreater(self.candidate['checkpoint']['optimizer_steps'], 0)

    def test_old_r188_and_bridge_exact_pins(self):
        expected = {'gpu/r188_node5_confinement.py': '75eed0e5e57cd7463e46fa10adeeebdb80b9ef1ce5e76a9b527c034d1e8e6481',
            'gpu/r184_cpu_bridge.py': '63100f72a00fedc20c609a250b399eec4874b5380a9638157a63e4fe50531a3c',
            'gpu/checkpoint_tail_runtime.py': '4e7746a8da7f99cb0354beb8d489a92e8fcb387e1409256901d1a9b0a033803c'}
        for name, value in expected.items():
            self.assertEqual(sha(SOURCE / name), value)

    def test_readonly_probe_uses_same_scope_reader_no_writer_lock(self):
        probe = load('c2_same_scope_probe', Path(__file__).with_name('cpu_probe.py'))
        before = self.snapshot()
        with patch('fcntl.flock', side_effect=AssertionError('readonly_probe_no_writer_lock')):
            result = probe.readonly_tail(SOURCE, self.candidate, self.selection)
        self.assertEqual(before, self.snapshot())
        self.assertTrue(result['inbox_preserved'] and result['sidecars_verified'])
        self.assertEqual(result['journal_writes'], 0)

    def test_prefix_request_response_bodies_not_replayed(self):
        original = self.journal_module.StreamJournal._read_json
        decoded = []
        def observe(directory, name):
            decoded.append(name)
            return original(directory, name)
        with patch.object(self.journal_module.StreamJournal, '_read_json', side_effect=observe):
            journal = self.open_receiver()
        receipt = journal.checkpoint_tail_receipt
        allowed = set(receipt['decoded_prefix_indices']) | {entry['record_index'] for entry in receipt['sidecars']}
        for name in decoded:
            if name[:20].isdigit() and not name.endswith('.intent.json') and int(name[:20]) <= self.selection['complete_index']:
                self.assertIn(int(name[:20]), allowed)
        self.assertEqual(receipt['prefix_work'], 'ALL_RETAINED_BYTES_HASHED_NO_HISTORICAL_BODY_JSON_REPLAY')

    def test_explicit_full_audit_still_available(self):
        journal = self.open_receiver()
        with patch.object(self.reader, 'scan', side_effect=AssertionError('explicit_audit_must_be_full')):
            journal.audit()


def retention_suite(path):
    tree = ast.parse(path.read_bytes(), filename=str(path))
    body = []
    copying = False
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'event':
            copying = True
        if isinstance(node, (ast.Import, ast.ImportFrom)) or copying and isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            body.append(node)
    module = types.ModuleType('c2_exact_retention_cases')
    module.__file__ = str(path)
    module.history_module = importlib.import_module('organism_v6.orch_r124_train_history')
    module.stream_module = importlib.import_module('organism_v6.orch_r125_continual_stream')
    module.driver_module = importlib.import_module('gpu.orch_r184_think_act_learn')
    sys.modules[module.__name__] = module
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), module.__dict__)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(module.RetentionTests)
    if suite.countTestCases() != 17:
        raise ValueError('exact_seventeen_unchanged_retention_case_bodies')
    return suite


def legacy_suite():
    choices = {'test_orch_r125_continual_stream.py': (
        'test_threshold_compaction_precedes_generation_and_preserves_raw_input',
        'test_threshold_reuses_prior_child_distillation_not_later_failed_code',
        'test_threshold_never_silently_drops_oversized_fresh_input'),
        'test_orch_r124_train_history.py': (
        'test_pinned_parent_is_verbatim_masked_once_across_compaction_eviction_and_restore',
        'test_child_cannot_be_pinned_and_pins_cannot_be_silently_truncated')}
    suite = unittest.TestSuite()
    for filename, names in choices.items():
        module = load('c2_legacy_' + filename.removesuffix('.py'), SOURCE / 'tests' / filename)
        for candidate in vars(module).values():
            if isinstance(candidate, type) and issubclass(candidate, unittest.TestCase):
                for name in names:
                    if hasattr(candidate, name):
                        suite.addTest(candidate(name))
    if suite.countTestCases() != 5:
        raise ValueError('five_original_retention_contracts_required')
    return suite


def main():
    global SOURCE, PINS, FIXTURE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU_only_environment_required')
    SOURCE = args.source.resolve()
    manifest = json.loads(args.manifest.read_bytes())
    checker = load('c2_portable_checker', Path(__file__).with_name('cpu_check.py'))
    PINS = checker.verify_source(SOURCE, manifest)
    sys.path.insert(0, str(SOURCE))
    FIXTURE = load('c2_exact_source_fixture', SOURCE / 'tests/test_orch_r125_stream_journal.py')
    groups = [('retention_cases', retention_suite(Path(__file__).with_name('retention_cases.py'))),
        ('existing_contracts', legacy_suite()),
        ('receiving_integration', unittest.defaultTestLoader.loadTestsFromTestCase(ExactSourceTests))]
    results = {}
    with patch('subprocess.Popen', side_effect=AssertionError('no_process_launch_from_source_tests')), \
            patch('os.kill', side_effect=AssertionError('no_native_signals')), \
            patch.object(signal, 'pidfd_send_signal', side_effect=AssertionError('no_pidfd_signals')):
        for name, suite in groups:
            result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
            results[name] = dict(passed=result.wasSuccessful(), tests=result.testsRun,
                failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped))
    origins = {}
    for name, module in tuple(sys.modules.items()):
        if name.startswith(('gpu.', 'organism_v6.')) and getattr(module, '__file__', None):
            path = Path(module.__file__).resolve()
            if not path.is_relative_to(SOURCE):
                raise ValueError('source_import_escaped_exact_closure:' + name)
            origins[name] = dict(path=str(path), sha256=sha(path))
    checker.verify_source(SOURCE, manifest)
    passed = all(result['passed'] for result in results.values())
    print(json.dumps(dict(passed=passed, source=str(SOURCE), source_pins=PINS, groups=results,
        tests_run=sum(result['tests'] for result in results.values()), imported_source_modules=origins,
        unchanged_retention_case_file_sha256=sha(Path(__file__).with_name('retention_cases.py')),
        retention_bootstrap_rebased_only=True, synthetic_only=True, actual_checkpoint_validated=False,
        actual_guard_validated=False, live_handoff_authorization=False, GPU_calls=0, native_signals=0,
        dispatches=0, prefix_cost_samples=METRICS), sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
