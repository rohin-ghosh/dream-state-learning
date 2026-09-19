"""Bounded driver opt-ins apply only to newly committed own rows."""

from copy import deepcopy
import json
import unittest

import test_orch_r205_reading_policy as reading_fixture
from gpu.orch_r127_pilot_console import publish_parent
from gpu.orch_r184_think_act_learn import pending_console_sources, validate_config
from organism_v6.orch_r194_code_target_filter import REVIEW_POLICY
from organism_v6.orch_r213_content_target_filter import POLICY as CONTENT_POLICY
from organism_v6.orch_r220_question_target_filter import POLICY as QUESTION_POLICY
from organism_v6.orch_r220_speaker_target_filter import POLICY as SPEAKER_POLICY


class NewOwnRowPolicyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = reading_fixture.ReadingPolicyTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.config = dict(self.fixture.config, learn_review_filter=REVIEW_POLICY,
            content_target_filter=CONTENT_POLICY, question_target_filter=QUESTION_POLICY,
            fabricated_speaker_filter=SPEAKER_POLICY)

    def complete_boundary(self):
        self.fixture.driver(['Earlier synthetic experience.']).generate_stage('THINK')
        receipt = dict(status='COMPLETE', optimizer_steps=1,
            new_row_sha256=[row['source_sha256'] for row in self.fixture.stream.pending_rows()],
            checkpoint_sha256=dict(adapter='a' * 64, optimizer='b' * 64, rng='c' * 64))
        self.fixture.stream.commit_sleep(receipt, self.fixture.journal.record)

    def test_exact_opt_ins_require_content_and_review(self):
        validate_config(self.config)
        for policy in ('question_target_filter', 'fabricated_speaker_filter'):
            for missing in ('content_target_filter', 'learn_review_filter'):
                with self.subTest(policy=policy, missing=missing):
                    invalid = dict(self.config)
                    invalid.pop(missing)
                    with self.assertRaises(ValueError):
                        validate_config(invalid)
            invalid = dict(self.config)
            invalid[policy] = 'UNKNOWN'
            with self.assertRaises(ValueError):
                validate_config(invalid)

    def test_deep_work_requires_reading_and_known_policy(self):
        valid = dict(self.config, deep_work_policy='R222_DEEP_WORK_DISCUSSION_V1')
        validate_config(valid)
        invalid = dict(valid)
        invalid.pop('reading_reply_policy')
        with self.assertRaises(ValueError):
            validate_config(invalid)
        invalid = dict(valid, deep_work_policy='UNKNOWN')
        with self.assertRaises(ValueError):
            validate_config(invalid)

    def test_prior_rows_unchanged_new_think_act_learn_annotated(self):
        prior = self.fixture.driver(['An earlier own explanation.'])
        prior.generate_stage('THINK')
        historical = deepcopy(self.fixture.stream.rows)
        driver = self.fixture.driver(['A concrete thought.', 'A concrete artifact.',
            'My own bounded review.'], self.config)
        for stage in ('THINK', 'ACT', 'LEARN'):
            driver.generate_stage(stage)
        self.assertEqual(self.fixture.stream.rows[:len(historical)], historical)
        for row in self.fixture.stream.rows[len(historical):]:
            self.assertEqual(row['question_target_filter'], QUESTION_POLICY)
            self.assertEqual(row['fabricated_speaker_filter'], SPEAKER_POLICY)
            self.assertEqual(row['content_target_filter'], CONTENT_POLICY)
            self.assertEqual(row['actor'], 'child')
            self.assertFalse(row['prefix_loss'])
            self.assertTrue(row['target_loss'])

    def test_console_own_row_tagged_never_human_or_parent_text(self):
        human = publish_parent(self.fixture.root, 'Rohin', 'Explain your own next step.')['id']
        publish_parent(self.fixture.root, 'Astra', 'Parent context is not your training target.')
        driver = self.fixture.driver(['My own reply.', 'My independent thought.'], self.config)
        driver.generate_stage('THINK')
        replies = self.fixture.records('R205_CONSOLE_REPLY')
        self.assertEqual(len(replies), 1)
        self.assertEqual(replies[0]['source_inbox_events'][0]['event_id'], 'parent:inbox:' + human)
        self.assertEqual([row['target'] for row in self.fixture.stream.rows],
            ['My own reply.', 'My independent thought.'])
        for row in self.fixture.stream.rows:
            self.assertEqual(row['fabricated_speaker_filter'], SPEAKER_POLICY)
            self.assertEqual(row['question_target_filter'], QUESTION_POLICY)
        committed = self.fixture.records('COMMITTED')[-1]['state']['state']['rows']
        self.assertEqual(committed, self.fixture.stream.rows)

    def test_post_complete_console_rows_survive_next_wake_without_replay(self):
        self.complete_boundary()
        publish_parent(self.fixture.root, 'Rohin', 'What happened?')
        driver = self.fixture.driver(['My genuine reply.', 'A new thought.', 'A concrete artifact.'], self.config)
        driver.drain_console('POST_COMPLETE_OPTIMIZER_BOUNDARY')
        before = deepcopy(self.fixture.stream.rows)
        self.assertEqual(len(pending_console_sources(self.fixture.stream, self.fixture.journal)), 1)
        driver.wake()
        self.assertEqual(self.fixture.stream.rows[:len(before)], before)
        self.assertEqual(len(self.fixture.records('R205_CONSOLE_REPLY')), 1)
        self.assertEqual(len(self.fixture.records('R205_CONSOLE_ROWS_CARRIED')), 1)

    def test_nonconsole_pending_row_cannot_bypass_saved_boundary(self):
        self.complete_boundary()
        driver = self.fixture.driver(['An ordinary untrained thought.'], self.config)
        driver.generate_stage('THINK')
        self.assertEqual(pending_console_sources(self.fixture.stream, self.fixture.journal), [])
        with self.assertRaisesRegex(ValueError, 'copy_starts_at_completed_sleep_boundary'):
            driver.wake()

    def test_console_resume_rejects_training_started_or_tampered_receipt(self):
        self.complete_boundary()
        publish_parent(self.fixture.root, 'Rohin', 'State your uncertainty.')
        driver = self.fixture.driver(['My reply.'], self.config)
        driver.drain_console('POST_COMPLETE_OPTIMIZER_BOUNDARY')
        reference = self.fixture.records('R205_CONSOLE_REPLY')[0]
        self.assertTrue(pending_console_sources(self.fixture.stream, self.fixture.journal))
        for path in (self.fixture.root / 'stream/records').glob('*.json'):
            record = json.loads(path.read_bytes())
            if record.get('kind') == 'R205_CONSOLE_REPLY':
                record['document']['segment'] = reference['segment'] + 1
                path.write_text(json.dumps(record, sort_keys=True, separators=(',', ':')))
                break
        with self.assertRaisesRegex(ValueError, 'pending_console_receipt_integrity'):
            pending_console_sources(self.fixture.stream, self.fixture.journal)

    def test_console_resume_rejects_inflight_optimizer(self):
        self.complete_boundary()
        publish_parent(self.fixture.root, 'Rohin', 'State your uncertainty.')
        driver = self.fixture.driver(['My reply.'], self.config)
        driver.drain_console('POST_COMPLETE_OPTIMIZER_BOUNDARY')
        self.fixture.journal.record('UPDATE', dict(synthetic_inflight=True))
        self.assertEqual(pending_console_sources(self.fixture.stream, self.fixture.journal), [])


if __name__ == '__main__':
    unittest.main()
