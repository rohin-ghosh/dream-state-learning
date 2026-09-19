from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import math_b_startup as startup
import math_b_runtime_candidate as kernel
import pending_sleep_contract as contract
import test_math_b_runtime_candidate as fixture_tests
from research_loop.workers.post_recovery_node2_sleep_20260919.runtime_candidate import receiving_fixture


class MathBStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(receiving_fixture, 'EVIDENCE', fixture_tests.HERE / 'source_evidence'), \
                patch.dict(receiving_fixture.SOURCE_PINS, fixture_tests.SOURCE_PINS, clear=True):
            cls.sources = receiving_fixture.load_receiving_sources('.')

    def setUp(self):
        fixture_tests.MathBRuntimeTests.setUp(self)
        self.fixture.plan.update(source_root=str(self.root / 'r213_math_b_fork' / 'original_source'),
            anchors=str(self.root / 'original_anchors.json'), context_limit=2048,
            authorized_wall_extension=dict(new_deadline_unix=contract.HARD_END))
        self.fixture.plan['think_act_learn'].update(trial_id='R213_NEW_MATH_B',
            correction_ledger='R197_CORRECTION_LEDGER_V1')
        self.fixture.plan_bytes = json.dumps(self.fixture.plan).encode()
        document = deepcopy(self.fixture.complete['document'])
        state = document['resume_state']['state']
        receipt = {key: value for key, value in document.items() if key != 'resume_state'}
        state['sleep_receipts'][-1] = receipt
        document['resume_state']['sha256'] = contract.digest(state)
        self.journal_root = self.root / 'stream'
        self.journal_root.mkdir()
        (self.journal_root / 'records').mkdir()
        (self.journal_root / 'inbox').mkdir()
        (self.journal_root / 'WRITER.lock').touch()
        manifest = dict(schema=self.sources.journal.SCHEMA, journal_id='a' * 32)
        (self.journal_root / 'JOURNAL.json').write_bytes(self.sources.journal._encoded(manifest) + b'\n')
        complete = dict(schema=self.sources.journal.SCHEMA, journal_id='a' * 32, index=0,
            kind='SLEEP_COMPLETE', previous_sha256=contract.digest(manifest), document=document)
        complete['sha256'] = contract.digest(complete)
        self.write_record(complete)
        self.selection = dict(policy=startup.tail.POLICY, root=str(self.journal_root),
            journal_id='a' * 32, complete_index=0, complete_sha256=complete['sha256'],
            life_id='R213_NEW_MATH_B', max_tail_records=200, max_tail_bytes=100_000_000,
            sidecars=[dict(name='correction_ledger.json', kind='R197_CORRECTION_CYCLE', required=False)],
            persist_complete_anchors=True)
        self.journal_class = startup.make_journal_class(self.sources.journal.StreamJournal, self.selection)
        stream = self.sources.stream.ContinualStream.restore(document['resume_state'],
            expected_sha256=document['resume_state']['sha256'])
        with self.journal_class(self.journal_root, create=False) as journal:
            ledger = journal.record('R197_CORRECTION_CYCLE', dict(ledger=dict(
                schema='R197_CORRECTION_LEDGER_V1', life_id='R213_NEW_MATH_B', cycles=[])))
            (self.journal_root / 'correction_ledger.json').write_text(json.dumps(dict(
                record_index=ledger['index'], record_sha256=ledger['sha256'])))
            for number in range(3):
                stream.step(lambda *args, **kwargs: dict(raw=f'checked answer {number}',
                    token_ids=[number + 1], terminal=True, truncated=False),
                    lambda messages: 10, journal.record, now=lambda: 1000)
            pending_state = stream.checkpoint()
            sources = [row['source_sha256'] for row in stream.pending_rows()]
            pending_state['state']['pending'] = 'sleep:' + contract.digest(sources)
            pending_state['sha256'] = contract.digest(pending_state['state'])
            pending_ref = journal.record('SLEEP_REQUEST', dict(cycle=receipt['cycle'] + 1,
                resume_state=pending_state))
            recipe = deepcopy(self.fixture.recipe['document'])
            eligibility = dict(deepcopy(self.fixture.eligibility['document']), new_row_sha256=sources)
            recipe_ref = journal.record('SLEEP_RECIPE', recipe)
            eligibility_ref = journal.record('TARGET_ELIGIBILITY', eligibility)
            for number in range(48):
                journal.record('UPDATE', dict(optimizer_step=self.fixture.checkpoint['optimizer_steps'] + number + 1,
                    source_sha256=sources[number % 3], losses=[], finished_unix=1000 + number))
            head = journal._state['index'] - 1
        self.selection['sidecars'][0]['required'] = True
        self.fixture.complete = complete
        self.fixture.pending = self.read_record(pending_ref['index'])
        self.fixture.recipe = self.read_record(recipe_ref['index'])
        self.fixture.eligibility = self.read_record(eligibility_ref['index'])
        self.suffix = [self.read_record(number) for number in range(pending_ref['index'] + 1, head + 1)]
        self.envelope = kernel.prepare_candidate(complete, self.fixture.pending, self.suffix,
            plan_bytes=self.fixture.plan_bytes,
            expected_plan_sha256=hashlib.sha256(self.fixture.plan_bytes).hexdigest())
        self.native = receiving_fixture.make_native(self.fixture)
        self.native.NativeChild.tokenizer = 'synthetic CPU tokenizer'
        self.native.NativeChild.engine = SimpleNamespace(runtime='CPU fixture, no GPU execution')
        self.native.BASE_SHA256 = 'f' * 64
        self.native.validate_plan = lambda plan: plan
        self.execution = dict(self.fixture.plan, source_root=str(self.root / 'r213_math_b_fork'
            / 'source_ws6_pending_math_b_cpu_test'))
        self.plan_path = self.root / 'PLAN.json'
        self.plan_path.write_text(json.dumps(self.execution))
        self.manifest = dict(schema=startup.SCHEMA, life='r213_math_b_fork',
            original_plan=self.file_binding('ORIGINAL_PLAN.json', self.fixture.plan_bytes),
            candidate=self.file_binding('CANDIDATE.json', json.dumps(self.envelope).encode()),
            execution_plan_sha256=hashlib.sha256(self.plan_path.read_bytes()).hexdigest(),
            staged_source_root=self.execution['source_root'], selection=self.selection)

    def file_binding(self, name, raw):
        path = self.root / name
        path.write_bytes(raw)
        return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())

    def write_record(self, record):
        directory = self.journal_root / 'records'
        (directory / f'{record["index"]:020d}.json').write_bytes(self.sources.journal._encoded(record) + b'\n')
        intent = self.sources.journal.StreamJournal._intent(record)
        (directory / f'{record["index"]:020d}.intent.json').write_bytes(self.sources.journal._encoded(intent) + b'\n')

    def read_record(self, number):
        return json.loads((self.journal_root / 'records' / f'{number:020d}.json').read_bytes())

    def invoke(self, run_loop=None):
        with patch.dict(os.environ, R125_ADMISSION_PLAN_SHA256=self.manifest['execution_plan_sha256']), \
                patch.object(startup.signal, 'signal'), patch.object(startup.signal, 'setitimer'):
            return startup.resume(self.plan_path, resume=True, manifest=self.manifest,
                native=self.native, journal_class=self.journal_class,
                build_inventory=lambda *args: (['original anchors'], dict(original_inventory=True)),
                run_loop=run_loop or Mock(return_value='original_loop_reached'), clock=lambda: 1000)

    def test_real_journal_startup_preserves_pending_then_runs_resident_loop(self):
        before = {path.name: path.read_bytes() for path in (self.journal_root / 'records').iterdir()}
        def run_loop(child, stream, journal, anchors, plan, root, plan_path, cycle):
            self.assertEqual(child.optimizer_steps, self.fixture.checkpoint['optimizer_steps'] + 48)
            self.assertEqual(len(stream.rows), len(self.fixture.pending['document']['resume_state']['state']['rows']))
            self.assertIsNone(stream.pending)
            self.assertEqual(plan, self.execution)
            stream.step(lambda *args, **kwargs: dict(raw='actual next artifact', token_ids=[4],
                terminal=True, truncated=False), lambda messages: 10, journal.record, now=lambda: 1000)
            journal.record('R184_ACT', dict(cpu_fixture=True, no_gpu_claim=True))
            return 'synthetic_REQUEST_RESPONSE_ACT_after_LOADED'

        self.assertEqual(self.invoke(run_loop), 'synthetic_REQUEST_RESPONSE_ACT_after_LOADED')
        for name, raw in before.items():
            self.assertEqual((self.journal_root / 'records' / name).read_bytes(), raw)
        with self.journal_class(self.journal_root, create=False) as journal:
            audit = journal.checkpoint_tail_audit()
            self.assertEqual(audit['prefix_work'], kernel.FAST_AUDIT_POLICY)
            self.assertEqual(audit['decoded_prefix_indices'], [0])
            kinds = [self.read_record(number)['kind'] for number in range(audit['record_count'])]
            self.assertEqual(kinds[-4:], ['REQUEST', 'RESPONSE', 'COMMITTED', 'R184_ACT'])
            self.assertNotIn('WALL_EXTENDED', kinds)
            self.assertLess(kinds.index('LOADED'), len(kinds) - 4)
        self.assertEqual(len(list((self.journal_root / 'checkpoint_tail_anchors').glob('*.json'))), 1)

    def test_full_replay_audit_is_not_mislabelled(self):
        with self.journal_class(self.journal_root, create=False) as journal:
            with self.assertRaisesRegex(ValueError, 'not_full_semantic_replay_claim'):
                journal.audit()

    def test_changed_launch_training_parameter_rejected(self):
        self.execution['new_presentations'] = 8
        self.plan_path.write_text(json.dumps(self.execution))
        self.manifest['execution_plan_sha256'] = hashlib.sha256(self.plan_path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'only_source_location_delta'):
            self.invoke()

    def test_missing_admission_environment_stops_before_child(self):
        with patch.dict(os.environ, clear=True), self.assertRaisesRegex(ValueError, 'admitted_plan_environment'):
            startup.resume(self.plan_path, resume=True, manifest=self.manifest, native=self.native,
                journal_class=self.journal_class, build_inventory=Mock(), run_loop=Mock(), clock=lambda: 1000)

    def test_partial_intent_not_removed_or_ignored(self):
        partial = self.journal_root / 'records' / '00000000000000000099.intent.json.partial'
        partial.touch()
        with self.assertRaisesRegex(ValueError, 'incomplete_or_unexpected_journal_tail'):
            self.invoke()
        self.assertTrue(partial.exists())

    def test_prefix_corruption_caught_before_model_load(self):
        path = self.journal_root / 'records' / '00000000000000000000.json'
        raw = path.read_bytes()
        path.write_bytes(raw.replace(b'fixture system', b'broken! system', 1))
        with self.assertRaisesRegex(ValueError, 'raw_record_integrity'):
            self.invoke()

    def test_tail_bound_remains_enforced(self):
        limited = dict(self.selection, max_tail_records=1)
        self.journal_class = startup.make_journal_class(self.sources.journal.StreamJournal, limited)
        with self.assertRaisesRegex(ValueError, 'record_bound_exceeded'):
            self.invoke()

    def test_correction_sidecar_remains_bound_and_unchanged(self):
        path = self.journal_root / 'correction_ledger.json'
        raw = path.read_bytes()
        self.invoke()
        self.assertEqual(path.read_bytes(), raw)

    def test_wrong_correction_sidecar_is_not_silently_replaced(self):
        path = self.journal_root / 'correction_ledger.json'
        path.write_text(json.dumps(dict(record_index=1, record_sha256='0' * 64)))
        before = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'sidecar_source_binding'):
            self.invoke()
        self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
