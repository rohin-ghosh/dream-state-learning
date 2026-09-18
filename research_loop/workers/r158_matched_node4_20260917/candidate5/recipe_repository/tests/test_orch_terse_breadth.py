"""Synthetic CPU regression fixtures; never native scientific targets."""

from collections import Counter
from copy import deepcopy
import unittest

from gpu import orch_terse_breadth_fit as fit
from organism_v6 import orch_terse_breadth as design
from tests.test_experienced_event_goal_pairs import coached_child
from tests.test_experienced_event_two_hop import exposed_child
from tests.test_experienced_event_two_hop_lesson import Tokenizer


class TerseBreadthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worlds = design.registry([])
        cls.collection = design.runtime(0).collect_world(cls.worlds[0]['TRAIN'][0], exposed_child)
        cls.document = design.collect_quality(0, cls.collection,
            lambda messages, metadata: design.quality.hop._invoke(coached_child, messages))

    def test_exact_fresh_registry_and_no_global_mutation(self):
        prior = design.quality.scale.runtime(0)['build_worlds']()
        self.assertEqual(sum(len(item['TRAIN']) for item in self.worlds), 128)
        self.assertEqual(sum(len(item['PROBE']) for item in self.worlds), 32)
        seen = set()
        for worlds in self.worlds:
            for world in worlds['TRAIN'] + worlds['PROBE']:
                identifiers = set(design.quality.scale.identifiers(world))
                self.assertFalse(seen.intersection(identifiers))
                seen.update(identifiers)
        self.assertEqual(design.registry([]), self.worlds)
        self.assertEqual(prior, design.quality.scale.runtime(0)['build_worlds']())
        with self.assertRaises(ValueError):
            design.runtime(16)

    def test_native_projection_replay_and_teacher_strip(self):
        self.assertEqual(design.replay_quality(0, self.document), self.document)
        rows = self.document['quality']['rows']
        self.assertEqual(len(rows), 24)
        for row, capture in zip(rows, self.document['evidence']['captures']):
            self.assertEqual(row['assistant'], capture['response']['raw'])
            self.assertEqual(row['prefix'], capture['student_prefix'])
            self.assertTrue(all(design.quality.lesson.PARENT_GUIDANCE not in message['content'] for message in row['prefix']))
        damaged = deepcopy(self.document)
        damaged['quality']['rows'][0]['assistant'] = 'ROUTE SYNTHETIC'
        with self.assertRaises(ValueError):
            design.replay_quality(0, damaged)

    def test_failed_pair_not_repaired_and_held_teaching_rejected(self):
        counter = Counter()

        def invoke(messages, metadata):
            counter['calls'] += 1
            outcome = design.quality.hop._invoke(coached_child, messages)
            if metadata['task_index'] == 0 and metadata['episode_call_index'] == 0:
                outcome['response']['raw'] = 'ROUTE INVALID'
            return outcome

        document = design.collect_quality(0, self.collection, invoke)
        self.assertLessEqual(counter['calls'], 24)
        self.assertLess(len(document['quality']['rows']), 24)
        design.replay_quality(0, document)
        held = design.runtime(0).collect_world(self.worlds[0]['PROBE'][0], exposed_child)
        with self.assertRaises(ValueError):
            design.collect_quality(0, held, invoke)
        with self.assertRaisesRegex(ValueError, 'minimum_thousand'):
            design.qualified_rows([(0, self.document)], self.worlds[0]['PROBE'])

    def test_encoder_matches_original266_projection(self):
        rows = self.document['quality']['rows']
        tokenizer = Tokenizer()
        original_rows = (rows * 61)[:1452]
        expected = fit.original.encode_new_rows(original_rows, tokenizer)
        self.assertEqual(fit.encode_new_rows(original_rows, tokenizer), expected)
        contaminated = deepcopy(rows)
        contaminated[0]['prefix'][0]['content'] += design.quality.lesson.PARENT_GUIDANCE
        with self.assertRaises(ValueError):
            fit.encode_new_rows(contaminated, tokenizer)

    def test_four_sixteen_exposures_seed_batch_and_caps(self):
        for count in (1008, 1452, 3072):
            for dose in (4, 16):
                updates = design.updates(count, dose)
                presentations = Counter(index for update in range(1, updates + 1) for index in design.indexes(update, count, dose))
                self.assertEqual({presentations[index] for index in range(210, 222 + count)}, {dose})
                self.assertEqual(sum(presentations[index] for index in range(128)), updates)
                self.assertEqual(sum(presentations[index] for index in range(128, 210)), updates)
        self.assertEqual(design.updates(3072, 16), 24672)
        recipes = [fit.recipe(1008, arm, seed, 'protocol', dose) for seed, dose in design.SEED_DOSES for arm in design.ARMS]
        self.assertEqual(len(recipes), 6)
        self.assertEqual(len({design.digest(recipe['schedule']) for recipe in recipes}), 2)
        for count in (999, 1000, 3073, True):
            with self.assertRaises(ValueError):
                design.updates(count)
        for seed in (0, 7804, True):
            with self.assertRaises(ValueError):
                fit.recipe(1008, design.ARMS[0], seed, 'protocol')

    def test_control_full_reference_loss_denominators(self):
        encoded = tuple(fit.source.native.EncodedRow((11, 12, 13, 14), (-100, -100, 13, 14), (13, 14))
                        for unused in range(1230))
        full, control = (fit.dose(encoded, arm) for arm in design.ARMS)
        self.assertEqual(full['row_presentations'], control['row_presentations'])
        self.assertEqual(full['reference_supervised_tokens'], control['reference_supervised_tokens'])
        self.assertEqual(full['actual_supervised_tokens'], full['reference_supervised_tokens'])
        self.assertLess(control['actual_supervised_tokens'], control['reference_supervised_tokens'])
        self.assertEqual(fit.controlled_masks(encoded, design.ARMS[1])[:222], encoded[:222])
        for update in (1, 7, 8, design.updates(1008)):
            indexes, baseline, reference, unused, unused_scale = fit.training_batch(encoded, update, design.ARMS[0])
            matched, controlled, denominator, active, scale = fit.training_batch(encoded, update, design.ARMS[1])
            self.assertEqual(indexes, matched)
            self.assertEqual(baseline['input_ids'], controlled['input_ids'])
            self.assertEqual(baseline['attention_mask'], controlled['attention_mask'])
            self.assertEqual(reference, denominator)
            self.assertAlmostEqual(7 / active * scale, 7 / reference)
            for slot, index in enumerate(indexes):
                self.assertEqual(controlled['labels'][slot], baseline['labels'][slot] if index < 222 else [-100] * 4)


if __name__ == '__main__':
    unittest.main()
