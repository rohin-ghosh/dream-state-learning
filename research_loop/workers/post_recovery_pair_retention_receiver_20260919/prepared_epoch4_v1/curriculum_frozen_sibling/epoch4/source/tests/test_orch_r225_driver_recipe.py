"""Synthetic CPU-only V2 driver opt-in and candidate-recipe provenance."""

from copy import deepcopy
import unittest

import test_orch_r205_reading_policy as reading_fixture
from gpu.orch_r125_continual_native import NativeChild
from gpu.orch_r127_pilot_console import publish_parent
from gpu.orch_r184_think_act_learn import validate_config
from organism_v6.orch_r194_code_target_filter import REVIEW_POLICY
from organism_v6.orch_r213_content_target_filter import POLICY as ORIGINAL_POLICY
from organism_v6.orch_r220_question_target_filter import POLICY as QUESTION_POLICY
from organism_v6.orch_r220_speaker_target_filter import POLICY as SPEAKER_POLICY
from organism_v6.orch_r225_content_target_filter import POLICY as REVISED_POLICY


class DriverPolicyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = reading_fixture.ReadingPolicyTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.config = dict(self.fixture.config, learn_review_filter=REVIEW_POLICY,
            content_target_filter=REVISED_POLICY, question_target_filter=QUESTION_POLICY,
            fabricated_speaker_filter=SPEAKER_POLICY)

    def test_v1_and_v2_require_review_and_reject_unknown_policy(self):
        for policy in (ORIGINAL_POLICY, REVISED_POLICY):
            with self.subTest(policy=policy):
                config = dict(self.config, content_target_filter=policy)
                self.assertIs(validate_config(config), config)
                config.pop('learn_review_filter')
                with self.assertRaisesRegex(ValueError, 'content_targets_require_review_filter'):
                    validate_config(config)
        with self.assertRaisesRegex(ValueError, 'content_targets_require_review_filter'):
            validate_config(dict(self.config, content_target_filter='UNKNOWN'))

    def test_v2_tags_only_new_rows_and_preserves_v1_history(self):
        self.fixture.driver(['An earlier own explanation.'],
            dict(self.config, content_target_filter=ORIGINAL_POLICY)).generate_stage('THINK')
        historical = deepcopy(self.fixture.stream.rows)
        driver = self.fixture.driver(['A concrete thought.', 'A concrete artifact.',
            'My own bounded review.'], self.config)
        for stage in ('THINK', 'ACT', 'LEARN'):
            driver.generate_stage(stage)
        self.assertEqual(self.fixture.stream.rows[:len(historical)], historical)
        for row in self.fixture.stream.rows[len(historical):]:
            self.assertEqual(row['content_target_filter'], REVISED_POLICY)
            self.assertEqual(row['question_target_filter'], QUESTION_POLICY)
            self.assertEqual(row['fabricated_speaker_filter'], SPEAKER_POLICY)
            self.assertEqual(row['actor'], 'child')
            self.assertFalse(row['prefix_loss'])
            self.assertTrue(row['target_loss'])
        self.assertEqual(self.fixture.records('COMMITTED')[-1]['state']['state']['rows'],
            self.fixture.stream.rows)

    def test_v2_console_reply_tags_child_only_and_preserves_human_source(self):
        publication = publish_parent(self.fixture.root, 'Rohin', 'Explain your next step.')
        source = self.fixture.root / 'stream/inbox' / (publication['id'] + '.json')
        original_source = source.read_bytes()
        driver = self.fixture.driver(['My own reply.', 'My independent thought.'], self.config)
        driver.generate_stage('THINK')
        self.assertEqual(source.read_bytes(), original_source)
        self.assertEqual(len(self.fixture.records('R205_CONSOLE_REPLY')), 1)
        self.assertEqual([row['target'] for row in self.fixture.stream.rows],
            ['My own reply.', 'My independent thought.'])
        for row in self.fixture.stream.rows:
            self.assertEqual(row['content_target_filter'], REVISED_POLICY)
            self.assertEqual(row['actor'], 'child')
        self.assertEqual(self.fixture.records('COMMITTED')[-1]['state']['state']['rows'],
            self.fixture.stream.rows)


class RecipeCaptured(Exception):
    pass


class RecipePolicyTests(unittest.TestCase):
    def recipe(self, new_rows, old_rows, *, rehearsal=0, presentations=16, plasticity=None):
        child = NativeChild.__new__(NativeChild)
        child.plan = dict(new_presentations=presentations, rehearsal_presentations=rehearsal)
        child.plasticity = plasticity
        records = []

        def record(kind, document):
            self.assertEqual(kind, 'SLEEP_RECIPE')
            records.append(deepcopy(document))
            raise RecipeCaptured()

        with self.assertRaises(RecipeCaptured):
            child.sleep(new_rows, old_rows, [], record)
        self.assertEqual(len(records), 1)
        return records[0]

    def test_actual_candidate_policies_are_sorted_unique_and_nonmutating(self):
        new_rows = [dict(content_target_filter=REVISED_POLICY, question_target_filter=QUESTION_POLICY),
            dict(content_target_filter=ORIGINAL_POLICY, fabricated_speaker_filter=SPEAKER_POLICY),
            dict(content_target_filter=REVISED_POLICY), dict(target='Unannotated historical text.')]
        old_rows = [dict(content_target_filter=ORIGINAL_POLICY)]
        original = deepcopy((new_rows, old_rows))
        recipe = self.recipe(new_rows, old_rows, rehearsal=1)
        policies = recipe['candidate_row_filter_policies']
        self.assertEqual(policies['NEW'], dict(content_target_filter=sorted([ORIGINAL_POLICY,
            REVISED_POLICY]), question_target_filter=[QUESTION_POLICY],
            fabricated_speaker_filter=[SPEAKER_POLICY]))
        self.assertEqual(policies['REHEARSAL'], dict(content_target_filter=[ORIGINAL_POLICY],
            question_target_filter=[], fabricated_speaker_filter=[]))
        self.assertEqual((new_rows, old_rows), original)
        self.assertEqual(recipe['new_rows'], 4)
        self.assertEqual(recipe['selected_old_rows'], 1)

    def test_new_only_recipe_does_not_report_unselected_rehearsal_policies(self):
        recipe = self.recipe([dict(content_target_filter=REVISED_POLICY)],
            [dict(content_target_filter=ORIGINAL_POLICY)])
        self.assertEqual(recipe['available_old_rows'], 1)
        self.assertEqual(recipe['selected_old_rows'], 0)
        self.assertTrue(all(not policies
            for policies in recipe['candidate_row_filter_policies']['REHEARSAL'].values()))

    def test_unannotated_rows_do_not_invent_any_filter_policy(self):
        recipe = self.recipe([dict(target='An older own row.')], [])
        self.assertTrue(all(not policies for cohort in recipe['candidate_row_filter_policies'].values()
            for policies in cohort.values()))

    def test_metadata_does_not_change_dose_or_learning_rate(self):
        plasticity = dict(schema='R186_PLASTICITY_V1', learning_rate_multiplier=1)
        for presentations in (4, 16, 32):
            with self.subTest(presentations=presentations):
                recipe = self.recipe([dict(content_target_filter=REVISED_POLICY)], [],
                    presentations=presentations, plasticity=plasticity)
                self.assertEqual(recipe['new_presentations'], presentations)
                self.assertEqual(recipe['selected_old_rows'], 0)
                self.assertEqual(recipe['anchor_lambda'], 0.25)
                self.assertEqual(recipe['plasticity'], plasticity)


if __name__ == '__main__':
    unittest.main()
