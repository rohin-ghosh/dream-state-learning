"""CPU-only second-sleep evaluator tests, not native learning evidence."""

from contextlib import contextmanager, nullcontext
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_experienced_event_cue_sleep as runner
from organism_v6 import experienced_event_cue_collection as cue
from test_astra_experienced_event_microloop import fixture


class Model:
    disabled = False

    @contextmanager
    def disable_adapter(self):
        self.disabled = True
        try:
            yield
        finally:
            self.disabled = False


class PublicEngine:
    def __init__(self, bank):
        self.model = Model()
        self.bank = {fact['event']: fact for fact in bank}
        self.messages = []

    def generate(self, messages):
        self.messages.append(messages)
        if messages[0]['content'] == runner.source.world.MEMORY_SYSTEM:
            address = messages[-1]['content'].split('READ EVENT ')[-1].splitlines()[0].strip()
            raw = runner.source.material._event(self.bank[address]) if address in self.bank and not self.model.disabled else 'MISS\n'
        else:
            task = dict(line.split(' ', 1) for line in messages[1]['content'].splitlines()[1:])
            read = {message['content'].strip().split(' ')[2] for message in messages
                    if message['role'] == 'assistant' and message['content'].startswith('READ EVENT ')}
            raw = None
            for message in messages:
                if message['role'] == 'user' and message['content'].startswith('MEMORY RESULT\nEVENT '):
                    event = runner.source.material.parse_event_line(
                        runner.source.material.canonical_event(message['content'][14:]))
                    if event['source'] == task['NODE'] and event['destination'] == task['GOAL']:
                        raw = 'ROUTE ' + event['port']
            if raw is None:
                unread = [address for address in task['EVENTS'].split(',') if address not in read]
                raw = 'READ EVENT ' + unread[0] if unread else 'ROUTE ' + task['PORTS'].split(',')[0]
        return dict(raw=raw, terminal=True, truncated=False, messages=messages)


class Tests(unittest.TestCase):
    def encoded_fixture(self):
        return tuple(runner.source.native.EncodedRow(
            tuple(range(index % 5 + 3)), (-100,) + tuple(range(index % 5 + 2)),
            tuple(range(index % 5 + 2))) for index in range(52))

    def test_loss_off_masks_only_cue_slots_preserving_full_schedule(self):
        encoded = self.encoded_fixture()
        original = deepcopy(encoded)
        totals = dict(CUE_REPLAY=0, CUE_LOSS_OFF=0)
        expected_memory = expected_cue = 0
        for update in range(1, 201):
            indexes, replay = runner.training_batch(encoded, update, 20, 999)
            off_indexes, off = runner.training_batch(encoded, update, 20, 999, 'CUE_LOSS_OFF')
            self.assertEqual(indexes, runner.material.mixed_indexes(update, 20))
            self.assertEqual(indexes, off_indexes)
            self.assertEqual(replay, runner.source.native.collate([encoded[index] for index in indexes], pad_id=999))
            for key in ('input_ids', 'attention_mask'):
                self.assertEqual(replay[key], off[key])
            self.assertEqual(replay['labels'][:2], off['labels'][:2])
            self.assertTrue(all(label == -100 for labels in off['labels'][2:] for label in labels))
            self.assertEqual([len(labels) for labels in replay['labels']], [len(labels) for labels in off['labels']])
            totals['CUE_REPLAY'] += runner.supervised_token_count(replay)
            totals['CUE_LOSS_OFF'] += runner.supervised_token_count(off)
            original_count, active_count, scale = runner.loss_normalization(encoded, indexes, off)
            self.assertEqual(original_count, runner.supervised_token_count(replay))
            self.assertEqual(active_count, runner.supervised_token_count(off))
            self.assertEqual(runner.loss_normalization(encoded, indexes, replay),
                             (original_count, original_count, 1.0))
            memory_loss_sum = 7.25
            self.assertAlmostEqual(memory_loss_sum / active_count * scale, memory_loss_sum / original_count)
            expected_memory += sum(len(encoded[index].target_ids) for index in indexes[:2])
            expected_cue += sum(len(encoded[index].target_ids) for index in indexes[2:])
        self.assertEqual(totals['CUE_REPLAY'], expected_memory + expected_cue)
        self.assertEqual(totals['CUE_LOSS_OFF'], expected_memory)
        self.assertEqual(encoded, original)

    def test_known_recorded_choices_and_legacy_defaults(self):
        self.assertEqual(runner.recorded_training_choice({}), ('CUE_REPLAY', 0))
        for arm in runner.TRAINING_ARMS:
            for seed in runner.TRAIN_SEEDS:
                self.assertEqual(runner.recorded_training_choice(dict(training_arm=arm, train_seed=seed)), (arm, seed))
        for seed in (-1, 3, True, 0.0, '0', None):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                runner.recorded_training_choice(dict(train_seed=seed))
        for receipt in (dict(training_arm='UNKNOWN'), dict(training_arm=None),
                        dict(train_seed=1, arguments=dict(train_seed=2)),
                        dict(arguments=dict(training_arm='CUE_LOSS_OFF'))):
            with self.subTest(receipt=receipt), self.assertRaises(ValueError):
                runner.recorded_training_choice(receipt)

    def test_training_seed_receipt_and_actual_supervised_tokens(self):
        encoded = self.encoded_fixture()
        for arm in runner.TRAINING_ARMS:
            for seed in runner.TRAIN_SEEDS:
                with self.subTest(arm=arm, seed=seed), TemporaryDirectory() as temporary:
                    output = Path(temporary)
                    (output / 'adapter').mkdir()
                    engine = MagicMock()
                    engine.tokenizer = SimpleNamespace(pad_token_id=999)
                    engine.torch.autocast.side_effect = lambda **kwargs: nullcontext()
                    engine.model.return_value.loss.item.return_value = 1.0
                    engine.model.return_value.loss.__mul__.return_value = engine.model.return_value.loss
                    with patch.object(runner.source, 'encode_rows', return_value=encoded[:32]), \
                         patch.object(runner.material, 'encode_cue_rows', return_value=encoded[32:]), \
                         patch.object(runner, 'enable_existing_adapter', return_value={'lora': MagicMock()}), \
                         patch('organism_v6.pcfl_vertical_train._state_hash', side_effect=['before', 'after']):
                        result = runner.train(engine, [None] * 32, [None] * 20, output,
                                              training_arm=arm, train_seed=seed)
                    engine.torch.manual_seed.assert_called_once_with(seed)
                    expected = sum(runner.supervised_token_count(runner.training_batch(
                        encoded, update, 20, 999, arm)[1]) for update in range(1, 201))
                    self.assertEqual(result['actual_supervised_tokens'], expected)
                    self.assertEqual(result['supervised_tokens'], expected)
                    self.assertEqual(result['cue_forward_presentations'], 400)
                    self.assertEqual(result['cue_supervised_presentations'], 400 if arm == 'CUE_REPLAY' else 0)
                    self.assertEqual(result['memory_presentations'], 400)
                    self.assertEqual((result['training_arm'], result['train_seed']), (arm, seed))
                    self.assertEqual(engine.torch.optim.AdamW.return_value.step.call_count, 200)
                    self.assertEqual(engine.model.return_value.loss.__mul__.call_count,
                                     200 if arm == 'CUE_LOSS_OFF' else 0)
                    losses = [runner.source.json.loads(line) for line in (output / 'LOSSES.jsonl').read_text().splitlines()]
                    self.assertEqual(sum(row['active_label_count'] for row in losses), expected)
                    self.assertEqual(sum(row['original_label_count'] for row in losses), result['original_supervised_tokens'])
                    for row in losses:
                        self.assertEqual(row['loss_scale'], row['active_label_count'] / row['original_label_count'])

    def test_second_sleep_checks_recorded_choices_and_legacy_receipt(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            adapter = root / 'adapter'
            adapter.mkdir()
            (adapter / 'adapter.bin').write_bytes(b'unchanged-synthetic-adapter')
            receipt = dict(schema=runner.SCHEMA, status='COMPLETE', phase='train', updates=200,
                frozen_base_unchanged=True, memory_source={'memory': 'original'}, cue_source={'cue': 'own'},
                initial_artifact_sha256='c42010e12efed8a06c1e98901f09d576cf0c568175e837fa66255138e3c8a40f',
                adapter_files={'adapter.bin': runner.source.file_hash(adapter / 'adapter.bin')})
            runner.source.write(root / 'RESULT.json', receipt)
            runner.check_second_sleep(adapter, receipt['memory_source'], receipt['cue_source'],
                                      training_arm='CUE_REPLAY', train_seed=0)
            receipt.update(training_arm='CUE_LOSS_OFF', train_seed=2)
            (root / 'RESULT.json').write_bytes(runner.source.native._json_bytes(receipt))
            runner.check_second_sleep(adapter, receipt['memory_source'], receipt['cue_source'],
                                      training_arm='CUE_LOSS_OFF', train_seed=2)
            for arm, seed in (('CUE_REPLAY', 2), ('CUE_LOSS_OFF', 0)):
                with self.assertRaisesRegex(ValueError, 'requested_training_choice_mismatch'):
                    runner.check_second_sleep(adapter, receipt['memory_source'], receipt['cue_source'],
                                              training_arm=arm, train_seed=seed)
            receipt['train_seed'] = 3
            (root / 'RESULT.json').write_bytes(runner.source.native._json_bytes(receipt))
            with self.assertRaisesRegex(ValueError, 'known_train_seed_required'):
                runner.check_second_sleep(adapter, receipt['memory_source'], receipt['cue_source'])

    def test_causal_count_rejects_unmasked_first_position(self):
        encoded = list(self.encoded_fixture())
        row = encoded[0]
        encoded[0] = runner.source.native.EncodedRow(row.input_ids, (1,) + row.labels[1:], row.target_ids)
        indexes, batch = runner.training_batch(encoded, 1, 20, 999)
        with self.assertRaisesRegex(ValueError, 'first_causal_label'):
            runner.loss_normalization(encoded, indexes, batch)

    def test_base_identity_must_agree_across_all_stages(self):
        receipt = dict(arguments=dict(expected_base_sha256='a' * 64))
        runner.validate_base_sources('a' * 64, receipt, receipt, receipt)
        for other in ({}, dict(arguments={}), dict(arguments=dict(expected_base_sha256='b' * 64))):
            with self.assertRaisesRegex(ValueError, 'same_frozen_base'):
                runner.validate_base_sources('a' * 64, receipt, other)

    def test_stage_deadlines_are_fixed_before_engine_phase_changes(self):
        self.assertEqual(runner.stage_seconds('train'), 3600)
        self.assertEqual(runner.stage_seconds('readout'), 1800)
        with self.assertRaises(ValueError):
            runner.stage_seconds('unknown')

    def test_parent_free_conditional_policy_and_reader_intervention(self):
        bank, episodes = fixture()
        engine = PublicEngine(bank)
        with TemporaryDirectory() as directory:
            report = runner.evaluate(engine, bank, episodes, Path(directory))
            self.assertLessEqual(report['model_calls'], 76)
            self.assertEqual(len(list(Path(directory).glob('CALL_*.json'))), report['model_calls'])
        panels = report['panels']
        self.assertEqual(panels['OWN_PARAMETRIC']['reached_goal'], 4)
        self.assertEqual(panels['OWN_READER_OFF']['reached_goal'], 2)
        self.assertEqual(panels['RECALL_W0']['correct'], 4)
        self.assertEqual(panels['RECALL_W8']['correct'], 4)
        self.assertEqual(panels['UNSEEN_MISS']['correct'], 4)
        for name in ('HELD_TEXT_0', 'HELD_TEXT_1'):
            self.assertEqual(panels[name]['reached_goal'], 4)
            self.assertEqual(panels[name]['second_reads'], 2)
        self.assertFalse(report['parent_present'])
        for messages in engine.messages:
            self.assertTrue(all(cue.PUBLIC_FEEDBACK_PREFIX not in message['content']
                                and 'Teacher strategy' not in message['content'] for message in messages))

    def test_actual_callback_error_is_not_reported_as_policy_failure(self):
        bank, episodes = fixture()
        engine = PublicEngine(bank)

        def fail(messages):
            raise RuntimeError('synthetic callback failure')

        engine.generate = fail
        with TemporaryDirectory() as directory, self.assertRaisesRegex(ValueError, 'infrastructure'):
            runner.evaluate(engine, bank, episodes, Path(directory))

    def test_nonterminal_outputs_remain_failure_inclusive(self):
        bank, episodes = fixture()
        engine = PublicEngine(bank)
        engine.generate = lambda messages: dict(raw='MISS\n', terminal=False, truncated=True)
        with TemporaryDirectory() as directory:
            result = runner.evaluate(engine, bank, episodes, Path(directory))
        self.assertEqual(result['panels']['OWN_PARAMETRIC']['reached_goal'], 0)
        self.assertEqual(result['panels']['UNSEEN_MISS']['correct'], 0)
        self.assertEqual(result['panels']['HELD_TEXT_0']['denominator'], 4)


if __name__ == '__main__':
    unittest.main()
