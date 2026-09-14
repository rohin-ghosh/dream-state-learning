"""CPU-only checks for the bounded adult-cycle native integration."""

from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gpu import astra_experienced_event_adult_cycle as runner
from test_astra_experienced_event_microloop import fixture
from test_astra_experienced_event_cue_sleep import PublicEngine


class Tests(unittest.TestCase):
    def test_adult_mask_intervention_matches_input_and_replay_schedule(self):
        encoded = tuple(runner.source.native.EncodedRow((1, 2, 3), (-100, 2, 3), (2, 3))
                        for unused in range(84))
        counts = Counter()
        for update in range(1, 401):
            indexes, replay, original, active, scale = runner.training_batch(encoded, update, 20, 'CUE_REPLAY')
            off_indexes, off, off_original, off_active, off_scale = runner.training_batch(encoded, update, 20, 'CUE_LOSS_OFF')
            self.assertEqual(indexes, off_indexes)
            self.assertEqual(replay['input_ids'], off['input_ids'])
            self.assertEqual(replay['attention_mask'], off['attention_mask'])
            for slot in (0, 2, 3):
                self.assertEqual(replay['labels'][slot], off['labels'][slot])
            self.assertTrue(all(label == -100 for label in off['labels'][1]))
            self.assertEqual((original, active, scale), (8, 8, 1))
            self.assertEqual((off_original, off_active, off_scale), (8, 6, 0.75))
            counts.update('OLD' if index < 32 else 'CUE' if index < 52 else 'NEW' for index in indexes)
        self.assertEqual(counts, dict(OLD=400, CUE=400, NEW=800))

    def test_new_task_readout_and_old_memory_retention_are_separate(self):
        old_bank, old_episodes = fixture()
        bank = runner.adult.build_bank()
        episodes = [dict(fact=fact, event=dict(raw=runner.source.material._event(fact), terminal=True, truncated=False))
                    for fact in bank]
        engine = PublicEngine(old_bank + bank)
        with TemporaryDirectory() as directory:
            result = runner.evaluate(engine, dict(bank=bank, episodes=episodes), old_bank, old_episodes, Path(directory))
        self.assertEqual(result['panels']['OWN_PARAMETRIC']['reached_goal'], 4)
        self.assertEqual(result['panels']['RECALL_W8']['correct'], 4)
        self.assertEqual(result['panels']['OLD_RECALL_W0']['correct'], 4)
        self.assertEqual(result['panels']['OLD_RECALL_W8']['correct'], 4)
        self.assertLessEqual(result['model_calls'], 84)
        self.assertFalse(result['parent_present'])

    def test_failed_or_other_child_collection_cannot_train(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            runner.source.write(root / 'RESULT.json', dict(schema=runner.SCHEMA, status='COLLECTION_COMPLETE',
                initial_training_result_sha256='other', frozen_base_unchanged=True))
            with self.assertRaisesRegex(ValueError, 'same_child_complete'):
                runner.read_adult_collection(root, 'expected')

    def test_reader_variant_changes_only_reader_prompts(self):
        old_bank, old_episodes = fixture()
        bank = runner.adult.build_bank()
        episodes = [dict(fact=fact, event=dict(raw=runner.source.material._event(fact), terminal=True, truncated=False))
                    for fact in bank]
        results = []
        for wrapper in (0, 8):
            engine = PublicEngine(old_bank + bank)
            with TemporaryDirectory() as directory:
                root = Path(directory)
                result = runner.evaluate(engine, dict(bank=bank, episodes=episodes), old_bank, old_episodes,
                                         root, reader_wrapper=wrapper)
                self.assertEqual(result['reader_wrapper'], wrapper)
                calls = [runner.source.read(path) for path in sorted((root / 'new_task').glob('CALL_*.json'))]
                for call in calls:
                    if call['role'] == 'reader':
                        message = call['generation']['messages'][-1]['content']
                        address = message.split('READ EVENT ')[-1].splitlines()[0].strip()
                        self.assertEqual(message, runner.source.world.WRAPPERS[wrapper].replace(
                            '{REQUEST}', 'READ EVENT ' + address))
                results.append([(call['panel'], call['role'], call['generation']['raw'],
                                 None if call['role'] == 'reader' else call['generation']['messages'])
                                for call in calls])
        self.assertEqual(results[0], results[1])


if __name__ == '__main__':
    unittest.main()
