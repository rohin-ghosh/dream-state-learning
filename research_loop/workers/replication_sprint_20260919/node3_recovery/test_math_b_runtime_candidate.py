from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import math_b_runtime_candidate as candidate
import pending_sleep_contract as contract
from research_loop.workers.post_recovery_node2_sleep_20260919.runtime_candidate import receiving_fixture


HERE = Path(__file__).resolve().parent
SOURCE_PINS = {
    'organism_v6/orch_r124_train_history.py': '1211c8f312f8572dd51938ffde4806f7171e6368f1c5ea12a296ff02567e4625',
    'organism_v6/orch_r125_continual_stream.py': 'baf6cc915dd430db580a28f9e6a21678c5a90ba59a9fd4b5651943cc3db6484e',
    'gpu/orch_r125_stream_journal.py': '08dab0bb84596b522fc08db8cdb2c4a26db9e416acfcf9cc35bacdd233d924a4',
    'gpu/orch_r125_continual_native.py': '4092dd4355dbb4c6d2ecbcb2f48ad08b23af4e37817b949c54ad31d6f5bc03c0',
}


class MathBRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(receiving_fixture, 'EVIDENCE', HERE / 'source_evidence'), \
                patch.dict(receiving_fixture.SOURCE_PINS, SOURCE_PINS, clear=True):
            cls.sources = receiving_fixture.load_receiving_sources('.')

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='cpu-runtime-', dir=HERE)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = receiving_fixture.build_fixture(self.root, 'C0', self.sources)
        self.fixture.plan.update(hard_end_unix=contract.HARD_END,
            lease_end_unix=1790391780, physical=2,
            gpu_uuid=contract.ORIGINAL_GPUS['r213_math_b_fork'][1])
        self.fixture.plan_bytes = json.dumps(self.fixture.plan).encode()
        for record in (self.fixture.complete, self.fixture.pending):
            saved = record['document']['resume_state']
            saved['state']['deadline_unix'] = contract.HARD_END
            saved['sha256'] = contract.digest(saved['state'])
            record['sha256'] = contract.digest({key: value for key, value in record.items()
                if key != 'sha256'})
        previous = self.fixture.pending
        self.suffix = [self.fixture.recipe, self.fixture.eligibility, *self.fixture.updates]
        for record in self.suffix:
            record['previous_sha256'] = previous['sha256']
            record['sha256'] = contract.digest({key: value for key, value in record.items()
                if key != 'sha256'})
            previous = record
        self.fixture.journal = receiving_fixture.ReceivingJournal(self.sources,
            self.fixture.pending, self.fixture.updates[-1])
        journal = self.fixture.journal
        journal.checkpoint_tail_audit = Mock(side_effect=lambda: dict(
            record_count=journal.state['index'], head_sha256=journal.state['previous'],
            prefix_work=candidate.FAST_AUDIT_POLICY, pending_preserved=True))
        journal.audit = Mock(side_effect=AssertionError('full historical replay forbidden'))
        self.native = receiving_fixture.make_native(self.fixture)
        self.envelope = candidate.prepare_candidate(self.fixture.complete,
            self.fixture.pending, self.suffix, plan_bytes=self.fixture.plan_bytes,
            expected_plan_sha256=hashlib.sha256(self.fixture.plan_bytes).hexdigest())

    def invoke(self, **overrides):
        arguments = dict(expected_sha256=self.envelope['sha256'], native=self.native,
            journal=self.fixture.journal, plan_bytes=self.fixture.plan_bytes,
            anchor_factory=lambda child: ['original anchors'], clock=lambda: 1000)
        arguments.update(overrides)
        return candidate.finish_pending_sleep(self.envelope, **arguments)

    def attempt(self):
        return self.root / 'interrupted_sleep_restarts' / self.envelope['candidate']['attempt_key']

    def test_full_48_updates_commit_and_paired_learn_with_original_transition(self):
        result = self.invoke()
        self.assertEqual(result['accounting']['recovery_updates'], 48)
        self.assertEqual(result['accounting']['recovery_start_steps'], 8412)
        self.assertEqual(result['accounting']['recovery_end_steps'], 8460)
        self.assertEqual(self.fixture.journal.records[-2]['kind'], 'SLEEP_COMPLETE')
        self.assertEqual(self.fixture.journal.records[-1]['kind'], 'R184_LEARN_COMPLETE')
        self.assertEqual(result['paired_LEARN']['index'], result['complete']['index'] + 1)
        self.assertIsNone(result['stream'].pending)
        self.assertEqual(result['stream'].sleep_frontier, len(result['stream'].rows))

    def test_preserves_rows_context_working_state_and_saved_rng_input(self):
        before = deepcopy(self.fixture.pending['document']['resume_state']['state'])
        result = self.invoke()
        after = result['stream'].checkpoint()['state']
        self.assertEqual(set(before), set(after))
        for field in before:
            if field not in ('pending', 'sleep_frontier', 'sleep_receipts', 'model_state_sha256'):
                self.assertEqual(before[field], after[field], field)
        self.assertEqual(result['child'].rng_source_bytes,
            Path(self.fixture.checkpoint['optimizer_rng_path']).read_bytes())
        self.assertEqual(result['child'].input_checkpoint, self.fixture.checkpoint)

    def test_no_fullstream_audit_or_generation(self):
        result = self.invoke()
        self.fixture.journal.checkpoint_tail_audit.assert_called_once()
        self.fixture.journal.audit.assert_not_called()
        self.assertEqual(len(result['child'].calls), 1)
        self.assertEqual(len(result['child'].calls[0]['new_rows']), 3)
        self.assertEqual(len(result['child'].calls[0]['old_rows']), 441)

    def test_original_partial_checkpoint_is_preserved(self):
        partial = self.root / 'checkpoints' / 'sleep_000146'
        partial.mkdir()
        (partial / 'optimizer_rng.pt').write_bytes(b'preserved interrupted bytes')
        result = self.invoke()
        self.assertEqual((partial / 'optimizer_rng.pt').read_bytes(), b'preserved interrupted bytes')
        self.assertNotEqual(Path(result['checkpoint']['optimizer_rng_path']).parent, partial)

    def test_no_automatic_retry_after_failed_training(self):
        self.native.behavior.fail_at_step = 1
        with self.assertRaises(Exception):
            self.invoke()
        self.assertTrue((self.attempt() / 'STARTED.json').exists())
        self.assertTrue((self.attempt() / 'FAILED.json').exists())
        with self.assertRaisesRegex(ValueError, 'consumed_attempt_no_retry'):
            self.invoke()
        self.assertEqual(len(self.native.instances), 1)

    def test_no_adoption_of_saved_but_unpublished_checkpoint(self):
        self.fixture.journal.fail_kind = 'SLEEP_COMPLETE'
        with self.assertRaises(OSError):
            self.invoke()
        destination = self.root / 'checkpoints' / self.envelope['candidate']['checkpoint_name']
        self.assertTrue((destination / 'COMMIT.json').exists())
        self.assertIsNotNone(self.fixture.journal.latest_checkpoint()['document']['state']['pending'])
        with self.assertRaisesRegex(ValueError, 'never_overwrite_or_adopt_checkpoint'):
            self.invoke()

    def test_no_sleep_reexecution_after_complete_when_paired_learn_fails(self):
        self.fixture.journal.fail_kind = 'R184_LEARN_COMPLETE'
        with self.assertRaises(OSError):
            self.invoke()
        failure = json.loads((self.attempt() / 'FAILED.json').read_text())
        self.assertIsNotNone(failure['complete'])
        self.assertIsNone(failure['paired_LEARN'])
        self.assertIsNone(self.fixture.journal.latest_checkpoint()['document']['state']['pending'])
        with self.assertRaisesRegex(ValueError, 'never_overwrite_or_adopt_checkpoint'):
            self.invoke()

    def test_no_complete_without_durable_commit(self):
        self.native.behavior.missing_commit = True
        with self.assertRaises(FileNotFoundError):
            self.invoke()
        self.assertNotIn('SLEEP_COMPLETE', [record['kind'] for record in self.fixture.journal.records])

    def test_wrong_restored_counter_does_not_train(self):
        self.native.behavior.init_step_delta = 48
        with self.assertRaisesRegex(ValueError, 'restored_durable_child'):
            self.invoke()
        self.assertEqual(self.native.instances[0].calls, [])

    def test_all_rows_and_all_presentations_required(self):
        self.native.behavior.steps = 47
        with self.assertRaisesRegex(ValueError, 'full_pending_sleep_without_exclusions'):
            self.invoke()
        self.assertNotIn('SLEEP_COMPLETE', [record['kind'] for record in self.fixture.journal.records])

    def test_changed_sleep_recipe_is_rejected(self):
        self.native.behavior.recipe_change = dict(new_presentations=8)
        with self.assertRaisesRegex(ValueError, 'unchanged_original_sleep_recipe'):
            self.invoke()

    def test_expired_original_wall_refuses_before_new_attempt(self):
        with self.assertRaisesRegex(ValueError, 'original_hard_end_expired'):
            self.invoke(clock=lambda: contract.HARD_END)
        self.assertFalse(self.attempt().exists())
        self.assertFalse(self.native.instances)

    def test_non_fast_audit_is_not_claimed_as_safe_startup(self):
        self.fixture.journal.checkpoint_tail_audit.side_effect = None
        self.fixture.journal.checkpoint_tail_audit.return_value = dict(
            record_count=self.fixture.updates[-1]['index'] + 1,
            head_sha256=self.fixture.updates[-1]['sha256'],
            prefix_work='FULL_JSON_REPLAY', pending_preserved=True)
        with self.assertRaisesRegex(ValueError, 'fresh_verified_checkpoint_tail'):
            self.invoke()
        self.assertFalse(self.native.instances)

    def test_tampered_plan_refused(self):
        with self.assertRaisesRegex(ValueError, 'unchanged_original_plan_bytes'):
            self.invoke(plan_bytes=self.fixture.plan_bytes + b' ')

    def test_original_checkpoint_tamper_refused_before_model_load(self):
        Path(self.fixture.checkpoint['optimizer_rng_path']).write_bytes(b'not the original state')
        with self.assertRaisesRegex(ValueError, 'binary_file_binding'):
            self.invoke()
        self.assertFalse(self.native.instances)


if __name__ == '__main__':
    unittest.main()
