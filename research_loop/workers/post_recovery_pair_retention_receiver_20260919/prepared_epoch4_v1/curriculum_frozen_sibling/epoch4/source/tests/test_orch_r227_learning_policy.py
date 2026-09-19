"""Synthetic CPU regressions for prospective all-authentic-child-row learning."""

from copy import deepcopy
import unittest
from unittest.mock import patch

import test_orch_r194_code_target_filter as sleep_fixture
import test_orch_r205_reading_policy as driver_fixture
from test_orch_r125_continual_native import make_plan
from gpu import orch_r125_continual_native as native
from gpu.orch_r127_pilot_console import publish_parent
from gpu.orch_r184_think_act_learn import validate_config
from organism_v6.orch_r125_plain_context import VERSION, eligible_rows
from organism_v6.orch_r194_code_target_filter import POLICY as CODE_POLICY, REVIEW_POLICY
from organism_v6.orch_r213_content_target_filter import POLICY as CONTENT_POLICY
from organism_v6.orch_r227_learning_policy import (
    POLICY, SEMANTIC_FILTER_FIELDS, all_child_rows, effective_config,
)


class LearningPolicyTests(unittest.TestCase):
    def test_explicit_policy_only_and_no_config_mutation(self):
        legacy = dict(content_target_filter=CONTENT_POLICY)
        self.assertFalse(all_child_rows(legacy))
        self.assertIs(effective_config(legacy), legacy)
        config = dict(legacy, learn_row_policy=POLICY, learn_review_filter=REVIEW_POLICY)
        before = deepcopy(config)
        self.assertEqual(effective_config(config), dict(learn_row_policy=POLICY))
        self.assertEqual(config, before)
        for unknown in (None, '', False, 'R225_CONTENT_BEARING_TARGETS_V2'):
            with self.subTest(unknown=unknown), self.assertRaisesRegex(ValueError, 'known_learn_row_policy'):
                all_child_rows(dict(learn_row_policy=unknown))

    def test_driver_and_trainer_must_agree(self):
        plan = make_plan('/tmp/synthetic-r227')
        plan.update(learn_row_policy=POLICY, rehearsal_presentations=0,
            think_act_learn=dict(schema='R184_THINK_ACT_LEARN_V1', trial_id='r227',
                reflection_policy='explicit', think_segments=1,
                cpu_gate_root='/tmp/synthetic-r227/gate', cpu_gate_sha256='a' * 64))
        with self.assertRaisesRegex(ValueError, 'same_learn_row_policy'):
            native.validate_plan(plan)
        plan['think_act_learn']['learn_row_policy'] = POLICY
        self.assertIs(native.validate_plan(plan), plan)

    def test_every_semantic_class_trains_without_rewriting_pending_rows(self):
        child, anchors = sleep_fixture.child_fixture()
        child.plan.update(learn_row_policy=POLICY, learn_review_filter=REVIEW_POLICY,
            presentation_version=VERSION, system_prompt=native.SYSTEM, birth_prompt=native.BIRTH)
        texts = ['I believe that is adequate and will proceed.', '中文也是自己的话。',
            '```python\nprint(１ + ２)\n```', '```python\nprint("I have verified it.")\n```',
            'word word word word word word', 'Rohin: Imagined speech by the child.',
            'source_sha256: an ordinary child-authored string', 'Do not train: self - a request',
            'Fable, which observation would distinguish these two explanations?']
        rows = [sleep_fixture.row(str(index), text, content_target_filter=CONTENT_POLICY)
            for index, text in enumerate(texts)]
        before = deepcopy(rows)
        with patch('organism_v6.orch_r194_code_target_filter.filter_learn_review_targets',
                side_effect=AssertionError('semantic review must not run')), patch(
                'organism_v6.orch_r194_code_target_filter.filter_sleep_targets',
                side_effect=AssertionError('fullwidth exclusion must not run')):
            receipt, records = sleep_fixture.run_sleep(child, anchors, rows)
        self.assertEqual(rows, before)
        self.assertEqual(receipt['optimizer_steps'], 16 * len(rows))
        self.assertEqual(receipt['excluded_rows'], [])
        self.assertEqual(receipt['active_semantic_filters'], [])
        self.assertEqual(receipt['presentations'], {row['source_sha256']: 16 for row in rows})
        recipe = next(document for kind, document in records if kind == 'SLEEP_RECIPE')
        self.assertEqual(recipe['learn_row_policy'], POLICY)
        self.assertEqual(recipe['active_semantic_filters'], [])
        self.assertFalse(recipe['semantic_row_exclusion'])
        self.assertNotIn('code_target_filter', recipe)
        self.assertNotIn('learn_review_filter', recipe)
        self.assertEqual(recipe['anchor_lambda'], 0.25)
        self.assertEqual(recipe['candidate_row_filter_policies']['NEW']['content_target_filter'],
            [CONTENT_POLICY])
        self.assertEqual(recipe['historical_row_annotations'], 'PRESERVED_NOT_APPLIED')

    def test_rehearsal_dose_and_history_are_not_expanded(self):
        child, anchors = sleep_fixture.child_fixture(enabled=False)
        child.plan['learn_row_policy'] = POLICY
        new_row = sleep_fixture.row('new', 'I believe this is adequate.')
        old_row = sleep_fixture.row('old', 'A historical excluded row must not be replayed.')
        receipt, records = sleep_fixture.run_sleep(child, anchors, [new_row], [old_row])
        self.assertEqual(receipt['presentations'], {new_row['source_sha256']: 16})
        self.assertEqual(receipt['optimizer_steps'], 16)
        self.assertEqual(next(document for kind, document in records if kind == 'SLEEP_RECIPE')
            ['selected_old_rows'], 0)

    def test_parent_rows_and_target_mutation_still_fail_provenance(self):
        for changes, expected in ((dict(actor='parent'), 'child_targets_only'),
                (dict(prefix_loss=True), 'child_targets_only'),
                (dict(target='Changed after generation.'), 'native_target_roundtrip')):
            with self.subTest(changes=changes):
                child, anchors = sleep_fixture.child_fixture(enabled=False)
                child.plan['learn_row_policy'] = POLICY
                row = sleep_fixture.row('bad', 'Original raw text.')
                row.update(changes)
                with self.assertRaisesRegex(ValueError, expected):
                    sleep_fixture.run_sleep(child, anchors, [row])
                self.assertEqual(child.optimizer.step.call_count, 0)

    def test_special_token_encoding_protection_is_not_a_semantic_filter(self):
        child, anchors = sleep_fixture.child_fixture(enabled=False)
        child.plan['learn_row_policy'] = POLICY
        safe = sleep_fixture.row('safe', 'Ordinary own text.')
        malformed = sleep_fixture.row('special', 'A special token.', token_ids=[1, 2])
        receipt, unused = sleep_fixture.run_sleep(child, anchors, [safe, malformed])
        self.assertEqual(receipt['optimizer_steps'], 16)
        self.assertEqual(receipt['excluded_rows'][0]['reason'], 'no_special_token_target_injection')
        self.assertFalse(receipt['semantic_row_exclusion'])

    def test_prefix_masking_survives_scaffolding_admission(self):
        row = sleep_fixture.row('literal', 'source_sha256: child-authored text')
        presentation = dict(version=VERSION, system_prompt=native.SYSTEM, birth_prompt=native.BIRTH)
        legacy, rejected = eligible_rows([row], presentation)
        self.assertEqual(legacy, [])
        self.assertEqual(len(rejected), 1)
        before = deepcopy(row)
        retained, rejected = eligible_rows([row], presentation, exclude_scaffolding=False)
        self.assertEqual(rejected, [])
        self.assertEqual(row, before)
        sample = native.encode_own(retained[0], sleep_fixture.Tokenizer(), 8192)
        self.assertEqual(sample.labels[-len(row['token_ids']):], tuple(row['token_ids']))
        self.assertTrue(all(label == -100 for label in sample.labels[:-len(row['token_ids'])]))


class DriverLearningPolicyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = driver_fixture.ReadingPolicyTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.config = dict(self.fixture.config, learn_row_policy=POLICY,
            learn_review_filter=REVIEW_POLICY, content_target_filter=CONTENT_POLICY)

    def test_stage_rows_are_not_tagged_and_review_exclusion_prompt_is_gone(self):
        original = deepcopy(self.config)
        effective = validate_config(self.config)
        self.assertEqual(self.config, original)
        self.assertFalse(set(SEMANTIC_FILTER_FIELDS).intersection(effective))
        driver = self.fixture.driver(['I believe this is adequate.', '中文。', 'Do not train: self - request'],
            self.config)
        for stage in ('THINK', 'ACT', 'LEARN'):
            driver.generate_stage(stage)
        self.assertFalse(self.fixture.records('R195_LEARN_REVIEW'))
        for row in self.fixture.stream.rows:
            self.assertFalse(set(SEMANTIC_FILTER_FIELDS).intersection(row))
            self.assertNotIn('learn_review', row)
            self.assertFalse(row['prefix_loss'])
            self.assertTrue(row['target_loss'])
        self.assertFalse(any('excludes the row from training' in message['content']
            for messages in driver.child.calls for message in messages))

    def test_console_routing_and_human_source_preserved(self):
        publication = publish_parent(self.fixture.root, 'Rohin', 'Tell me your actual answer.')
        source = self.fixture.root / 'stream/inbox' / (publication['id'] + '.json')
        original_source = source.read_bytes()
        driver = self.fixture.driver(['My actual response.', 'My next thought.'], self.config)
        driver.generate_stage('THINK')
        self.assertEqual(len(self.fixture.records('R205_CONSOLE_REPLY')), 1)
        self.assertEqual(source.read_bytes(), original_source)
        self.assertEqual([row['target'] for row in self.fixture.stream.rows],
            ['My actual response.', 'My next thought.'])
        self.assertTrue(all(row['actor'] == 'child' for row in self.fixture.stream.rows))


if __name__ == '__main__':
    unittest.main()
