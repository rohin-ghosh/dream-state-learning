from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import c0_startup as startup
import c0_kernel as kernel
import test_support as support


class StopAfterActualAct(Exception):
    pass


class C0StartupTests(unittest.TestCase):
    def setUp(self):
        self.stack = self.enterContext(ExitStack())
        self.sources = support.load_originals(self.stack)
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory(dir=support.HERE)))
        self.fixture = support.build(self.root, self.sources, self.stack)
        self.enterContext(patch.object(startup.signal, 'signal'))
        self.enterContext(patch.object(startup.signal, 'setitimer'))
        self.enterContext(patch.dict(os.environ,
            R125_ADMISSION_PLAN_SHA256=self.fixture.manifest['execution_plan_sha256']))

    def invoke(self, run_loop=None):
        return startup.resume(self.fixture.plan_path, resume=True, manifest=self.fixture.manifest,
            native=self.sources.native, journal_class=self.fixture.journal_class,
            build_inventory=lambda *args: (['CPU original-anchor stand-in'], dict(cpu_fixture=True)),
            run_loop=run_loop or Mock(return_value='resident_loop_reached'), clock=lambda: 1000)

    def records(self):
        return [json.loads(path.read_bytes()) for path in sorted(
            self.fixture.journal_root.joinpath('records').glob('*.json')) if '.intent.' not in path.name]

    def test_actual_original_driver_think_act_after_pending_sleep(self):
        before = {path.name: path.read_bytes() for path in (self.fixture.journal_root / 'records').iterdir()}
        old_plan = self.fixture.plan_path.read_bytes()
        failed = self.root / 'checkpoints/sleep_000146'
        failed.mkdir()
        artifact = failed / 'optimizer_rng.pt'
        artifact.write_bytes(b'failed old truncated optimizer: must stay byte-identical')
        old_identity = (artifact.stat().st_ino, artifact.read_bytes())
        with patch.object(self.sources.driver.time, 'time', return_value=1000), \
                patch.object(self.sources.driver.ThinkActLearn, 'prepare_sleep', side_effect=StopAfterActualAct):
            with self.assertRaises(StopAfterActualAct):
                self.invoke(self.sources.driver.run_loop)
        records = self.records()
        kinds = [record['kind'] for record in records]
        new = records[self.fixture.head + 1:]
        updates = [record for record in new if record['kind'] == 'UPDATE']
        self.assertEqual([record['document']['optimizer_step'] for record in updates], list(range(8413, 8461)))
        self.assertEqual(kinds.count('R184_LEARN_COMPLETE'), 1)
        self.assertIn('R184_ACT', kinds)
        self.assertLess(kinds.index('LOADED'), kinds.index('R184_ACT'))
        self.assertTrue(any(record['kind'] == 'R184_STAGE' and record['document']['stage'] == 'THINK' for record in new))
        self.assertTrue(any(record['kind'] == 'R184_STAGE' and record['document']['stage'] == 'ACT' for record in new))
        self.assertNotIn('WALL_EXTENDED', kinds)
        self.assertNotIn('RESET', kinds)
        child = self.fixture.fake.instances[0]
        self.assertEqual(child.optimizer_steps, 8460)
        self.assertEqual(len(child.calls[0]['new_rows']), 3)
        self.assertEqual(len(child.calls[0]['old_rows']), 441)
        self.assertEqual(child.plan, self.fixture.execution)
        self.assertEqual(self.fixture.plan_path.read_bytes(), old_plan)
        self.assertEqual((artifact.stat().st_ino, artifact.read_bytes()), old_identity)
        for name, raw in before.items():
            self.assertEqual((self.fixture.journal_root / 'records' / name).read_bytes(), raw)
        receipt = next(record['document'] for record in new if record['kind'] == 'C0_PENDING_SLEEP_STARTUP_COMPLETE')
        self.assertEqual(receipt['rng_origin'], 'DURABLE_COMPLETE_NOT_UNSAVED_POST_GENERATION_STATE')
        self.assertFalse(receipt['exact_resident_continuity_claimed'])
        self.assertEqual(receipt['audit']['decoded_prefix_indices'], [1])

    def test_raw_prefix_corruption_rejected_before_model(self):
        path = self.fixture.journal_root / 'records/00000000000000000000.json'
        path.write_bytes(path.read_bytes().replace(b'hash this prefix', b'HASH this prefix'))
        with self.assertRaisesRegex(ValueError, 'raw_record_integrity'):
            self.invoke()
        self.assertFalse(self.fixture.fake.instances)

    def test_changed_head_is_not_ignored(self):
        with self.fixture.journal_class(self.fixture.journal_root, create=False) as journal:
            journal.record('LATER_NOTE', dict(test=True))
        with self.assertRaisesRegex(ValueError, 'exact_old_head'):
            self.invoke()
        self.assertFalse(self.fixture.fake.instances)

    def test_missing_record_intent_pair_rejected(self):
        path = self.fixture.journal_root / 'records/00000000000000000000.intent.json'
        path.rename(path.with_suffix('.preserved'))
        with self.assertRaises(ValueError):
            self.invoke()

    def test_no_partial_intent_reconciliation_for_C0(self):
        path = self.fixture.journal_root / 'records/00000000000000006711.intent.json.partial'
        path.touch()
        with self.assertRaisesRegex(ValueError, 'incomplete_or_unexpected'):
            self.invoke()
        self.assertTrue(path.exists())

    def test_admission_required(self):
        with patch.dict(os.environ, clear=True), self.assertRaisesRegex(ValueError, 'admitted_execution_plan'):
            self.invoke()
        self.assertFalse(self.fixture.fake.instances)

    def test_actual_exclusive_WRITER_required(self):
        with self.fixture.journal_class(self.fixture.journal_root, create=False):
            with self.assertRaises((ValueError, BlockingIOError)):
                self.invoke()
        self.assertFalse(self.fixture.fake.instances)

    def test_only_source_root_plan_delta(self):
        for mutation in [dict(hard_end_unix=1789927201), dict(physical=1),
                dict(root='/tmp/new-birth'), dict(authorized_wall_extension=None),
                dict(new_presentations=8), dict(lease_end_unix=1789980181), dict(preupdate_recovery={})]:
            with self.subTest(mutation=mutation):
                raw = json.dumps(dict(self.fixture.execution, **mutation)).encode()
                manifest = dict(self.fixture.manifest, execution_plan_sha256=hashlib.sha256(raw).hexdigest())
                with self.assertRaisesRegex(ValueError, 'only_source_location_delta'):
                    startup.validate_manifest(manifest, raw)

    def test_original_plan_whitespace_not_canonicalized(self):
        path = Path(self.fixture.manifest['original_plan']['path'])
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'receipt_bytes_changed'):
            self.invoke()

    def test_new_authorization_rejected_even_rehashed(self):
        manifest = deepcopy(self.fixture.manifest)
        path = Path(manifest['original_plan']['path'])
        plan = json.loads(path.read_bytes())
        plan['authorized_wall_extension']['new_deadline_unix'] += 1
        raw = json.dumps(plan).encode()
        path.write_bytes(raw)
        manifest['original_plan']['sha256'] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, 'exact_observed_wall_authorization'):
            startup.validate_manifest(manifest, self.fixture.plan_path.read_bytes())

    def test_failure_preserves_pending_and_consumes_attempt(self):
        self.fixture.fake.behavior.fail_save = True
        loop = Mock()
        with self.assertRaisesRegex(OSError, 'ENOSPC'):
            self.invoke(loop)
        loop.assert_not_called()
        with self.fixture.journal_class(self.fixture.journal_root, create=False) as journal:
            self.assertIsNotNone(journal.latest_checkpoint()['document']['state']['pending'])
        self.fixture.fake.behavior.fail_save = False
        with self.assertRaisesRegex(ValueError, 'never_overwrite|attempt_consumed'):
            self.invoke()
        self.assertEqual(len(self.fixture.fake.instances), 1)

    def test_LEARN_failure_does_not_enter_loop_or_repeat_complete(self):
        original = self.fixture.journal_class.record
        def fail_learn(journal, kind, document):
            if kind == 'R184_LEARN_COMPLETE':
                raise OSError('synthetic paired LEARN failure')
            return original(journal, kind, document)
        loop = Mock()
        with patch.object(self.fixture.journal_class, 'record', fail_learn):
            with self.assertRaisesRegex(OSError, 'paired LEARN'):
                self.invoke(loop)
        loop.assert_not_called()
        self.assertEqual(sum(record['kind'] == 'SLEEP_COMPLETE' for record in self.records()), 2)
        self.assertFalse(any(record['kind'] == 'LOADED' for record in self.records()))

    def test_sidecar_and_tail_bounds_stay_strict(self):
        bad = dict(self.fixture.manifest['selection'], max_tail_records=1)
        self.fixture.journal_class = startup.make_journal_class(self.sources.journal.StreamJournal, bad)
        with self.assertRaisesRegex(ValueError, 'record_bound_exceeded'):
            self.invoke()

    def test_audit_is_explicit_not_full_semantic_replay(self):
        with self.fixture.journal_class(self.fixture.journal_root, create=False) as journal:
            with self.assertRaisesRegex(ValueError, 'not_full_JSON_replay'):
                journal.audit()
            audit = journal.checkpoint_tail_audit()
            self.assertEqual(audit['decoded_prefix_indices'], [1])
            self.assertTrue(audit['pending_preserved'])
            self.assertEqual(audit['prefix_work'], kernel.FAST_AUDIT_POLICY)


if __name__ == '__main__':
    unittest.main()
