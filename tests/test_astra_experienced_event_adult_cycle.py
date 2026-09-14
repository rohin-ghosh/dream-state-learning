"""CPU-only checks for the bounded adult-cycle native integration."""

from collections import Counter
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_experienced_event_adult_cycle as runner
from test_astra_experienced_event_microloop import fixture
from test_astra_experienced_event_cue_sleep import PublicEngine


class Tests(unittest.TestCase):
    def test_recollection_is_one_captured_call_without_training_admission(self):
        from organism_v6 import experienced_event_sleep_recollection as recollection

        collection = self.cycle_record(2)
        original = deepcopy(collection)
        engine = MagicMock()
        engine.generate.return_value = dict(raw='NONE', terminal=True, truncated=False)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            result = runner.recollect(engine, collection, root)
            engine.generate.assert_called_once_with(recollection.build_messages(collection), max_new_tokens=768)
            self.assertEqual(runner.source.read(root / 'SLEEP_NOTE.json'), engine.generate.return_value)
            self.assertEqual(result['note_sha256'], runner.source.file_hash(root / 'SLEEP_NOTE.json'))
            self.assertEqual((result['model_calls'], result['fits'], result['training_admission']),
                             (1, 0, 'UNREVIEWED_NO_FIT'))
            self.assertFalse((root / 'adapter').exists())
        self.assertEqual(collection, original)

    def cycle_record(self, cycle):
        bank = runner.adult.build_bank(cycle)

        def generate(messages):
            fact = next(fact for fact in bank if fact['port'] in messages[1]['content'])
            raw = ('EXPLORE ' + fact['node'] + ' ' + fact['port'] if len(messages) == 2
                   else runner.source.material._event(fact))
            return dict(raw=raw, terminal=True, truncated=False, messages=deepcopy(messages))

        return runner.adult.collect(generate, cycle=cycle)

    def cycle1_artifacts(self, root):
        prior = root / 'collect'
        prior.mkdir()
        adapter = root / 'train' / 'adapter'
        adapter.mkdir(parents=True)
        (adapter / 'adapter_model.safetensors').write_bytes(b'synthetic-cycle1-adapter')
        memory_source, cue_source = {'memory': 'original32'}, {'cue': 'original20'}
        collection = dict(schema=runner.SCHEMA, status='COLLECTION_COMPLETE', phase='collect',
            master=runner.adult.MASTER, development_arm='CUE_REPLAY', frozen_base_unchanged=True,
            initial_training_result_sha256='a' * 64, memory_source=memory_source, cue_source=cue_source,
            arguments=dict(expected_base_sha256='b' * 64))
        runner.source.write(prior / 'COLLECTION.json', self.cycle_record(1))
        collection['collection_sha256'] = runner.source.file_hash(prior / 'COLLECTION.json')
        runner.source.write(prior / 'RESULT.json', collection)
        record, rows, provenance = runner.read_adult_collection(prior, 'a' * 64)
        trained = dict(collection, status='COMPLETE', phase='train', updates=400, adult_source=provenance,
            adapter_state_after='c' * 64,
            adapter_files={'adapter_model.safetensors': runner.source.file_hash(adapter / 'adapter_model.safetensors')})
        runner.source.write(adapter.parent / 'RESULT.json', trained)
        return adapter, prior, trained, memory_source, cue_source

    def test_cycle2_initial_requires_own_completed_cycle1_lineage(self):
        with TemporaryDirectory() as temporary:
            adapter, prior, trained, memory_source, cue_source = self.cycle1_artifacts(Path(temporary))
            arguments = dict(arm='CUE_REPLAY', expected_base_sha256='b' * 64,
                             memory_source=memory_source, cue_source=cue_source)
            receipt, record, rows, provenance = runner.load_cycle2_initial(adapter, prior, **arguments)
            self.assertEqual(receipt, runner.source.file_hash(adapter.parent / 'RESULT.json'))
            self.assertEqual(len(rows), 32)
            self.assertEqual(provenance, trained['adult_source'])
            faults = [dict(cycle=2), dict(status='FAILED'), dict(updates=200), dict(phase='readout'),
                      dict(schema=runner.development.SCHEMA), dict(development_arm='CUE_LOSS_OFF'),
                      dict(memory_source={}), dict(cue_source={}), dict(adult_source={}),
                      dict(initial_training_result_sha256='d' * 64),
                      dict(arguments=dict(expected_base_sha256='e' * 64))]
            for fault in faults:
                with self.subTest(fault=fault):
                    (adapter.parent / 'RESULT.json').write_bytes(runner.source.native._json_bytes(dict(trained, **fault)))
                    with self.assertRaises(ValueError):
                        runner.load_cycle2_initial(adapter, prior, **arguments)
            (adapter.parent / 'RESULT.json').write_bytes(runner.source.native._json_bytes(trained))
            (adapter / 'adapter_model.safetensors').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'adult_saved_adapter_drift'):
                runner.load_cycle2_initial(adapter, prior, **arguments)

    def test_cycle2_collection_requires_prior_source_and_current_child(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner.source.write(root / 'COLLECTION.json', self.cycle_record(2))
            prior = {'prior': 'bound-own-A1'}
            receipt = dict(schema=runner.SCHEMA, status='COLLECTION_COMPLETE', cycle=2,
                master=runner.adult.SECOND_MASTER, initial_training_result_sha256='a' * 64,
                frozen_base_unchanged=True, prior_adult_source=prior,
                collection_sha256=runner.source.file_hash(root / 'COLLECTION.json'))
            runner.source.write(root / 'RESULT.json', receipt)
            record, rows, provenance = runner.read_adult_collection(root, 'a' * 64, cycle=2, prior_adult_source=prior)
            self.assertEqual(len(rows), 32)
            for source in (None, {'prior': 'other'}):
                with self.assertRaises(ValueError):
                    runner.read_adult_collection(root, 'a' * 64, cycle=2, prior_adult_source=source)
            with self.assertRaises(ValueError):
                runner.read_adult_collection(root, 'different-child', cycle=2, prior_adult_source=prior)
            with self.assertRaises(ValueError):
                runner.read_adult_collection(root, 'a' * 64)

    def test_cycle2_masks_and_old_row_encoding_preserve_layout(self):
        encoded = tuple(runner.source.native.EncodedRow((1, 2, 3), (-100, 2, 3), (2, 3)) for unused in range(116))
        for update in range(1, 401):
            indexes, replay, original, active, scale = runner.training_batch(encoded, update, 20, 'CUE_REPLAY', old_count=64)
            off_indexes, off, off_original, off_active, off_scale = runner.training_batch(encoded, update, 20, 'CUE_LOSS_OFF', old_count=64)
            self.assertEqual(indexes, off_indexes)
            self.assertEqual(replay['input_ids'], off['input_ids'])
            self.assertEqual(replay['attention_mask'], off['attention_mask'])
            self.assertEqual((original, active, scale, off_original, off_active, off_scale), (8, 8, 1, 8, 6, .75))
            self.assertEqual(off['labels'][1], [-100] * 3)
            for slot in (0, 2, 3):
                self.assertEqual(off['labels'][slot], replay['labels'][slot])
        rows = list(range(64))
        with patch.object(runner.source, 'encode_rows', side_effect=lambda rows, tokenizer: tuple(rows)) as encode:
            self.assertEqual(runner.encode_old_rows(rows, None), tuple(rows))
            self.assertEqual([call.args[0] for call in encode.call_args_list], [rows[:32], rows[32:]])

    def test_cycle2_retention_eight_old_facts_new_four_and_wrappers(self):
        old_bank, old_episodes = fixture()
        prior, current = self.cycle_record(1), self.cycle_record(2)
        old_bank += prior['bank']
        old_episodes += prior['episodes']
        for wrapper in (0, 8):
            engine = PublicEngine(old_bank + current['bank'])
            with TemporaryDirectory() as temporary:
                root = Path(temporary)
                result = runner.evaluate(engine, current, old_bank, old_episodes, root, reader_wrapper=wrapper)
                for view in (0, 8):
                    old = result['panels']['OLD_RECALL_W%d' % view]
                    new = result['panels']['RECALL_W%d' % view]
                    self.assertEqual((old['denominator'], old['correct'], len(old['rows'])), (8, 8, 8))
                    self.assertEqual((new['denominator'], new['correct']), (4, 4))
                    self.assertEqual(len(list(root.glob('OLD_RECALL_W%d_*.json' % view))), 8)
                calls = len(list((root / 'new_task').glob('CALL_*.json'))) + len(list(root.glob('OLD_RECALL_W*.json')))
                self.assertEqual(result['model_calls'], calls)
                self.assertLessEqual(calls, 92)
                self.assertEqual(result['reader_wrapper'], wrapper)

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
