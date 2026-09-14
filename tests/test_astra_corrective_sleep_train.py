"""CPU-only schedule and fake-native checks; no learning or launch evidence."""

from collections import Counter
from contextlib import ExitStack, nullcontext
from copy import deepcopy
from dataclasses import asdict, replace
from itertools import product
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_corrective_sleep_train as runner


def encoded_fixture():
    rows = []
    for index in range(116):
        count = 2 if index < 84 else (1, 3, 7, 11)[(index - 84) % 4] + (index - 84) // 4 % 3
        prefix = (-100,) * (index % 3 + 1)
        targets = tuple(range(1, count + 1))
        labels = prefix + targets + (-100,)
        rows.append(runner.source.native.EncodedRow(tuple(range(len(labels))), labels, targets))
    return tuple(rows)


def source_fixture():
    old = [dict(original_row=index) for index in range(64)]
    cue = [dict(original_cue=index) for index in range(20)]
    new = [dict(event='event%d' % (index % 4), wrapper='W%d' % (index // 4), original_row=index)
           for index in range(32)]
    return old, cue, new


class Finite:
    def __init__(self, value):
        self.value = math.isfinite(value.value if hasattr(value, 'value') else value)

    def __bool__(self):
        return self.value

    def all(self):
        return self.value


class Parameter:
    def __init__(self, value, dtype='float32'):
        self.value = value
        self.dtype = dtype
        self.requires_grad = True
        self.grad = None

    def requires_grad_(self, enabled):
        self.requires_grad = enabled


class Loss:
    requires_grad = True

    def __init__(self, value, engine):
        self.value = value
        self.engine = engine

    def __mul__(self, scale):
        return Loss(self.value * scale, self.engine)

    def item(self):
        return self.value

    def backward(self):
        self.engine.backward_losses.append(self.value)
        for parameter in self.engine.parameters.values():
            if parameter.requires_grad:
                parameter.grad = self.engine.gradient


def fake_engine():
    engine = SimpleNamespace(tokenizer=SimpleNamespace(pad_token_id=151643), device='fake-device',
        check=MagicMock(), model=MagicMock(), mean_loss=2.0, gradient=1.0, parameter_step=0.01,
        backward_losses=[], parameters={'layer.lora_A.default.weight': Parameter(1.0),
            'layer.lora_B.default.weight': Parameter(0.0), 'base.weight': Parameter(10.0, 'bfloat16')})
    engine.model.named_parameters.return_value = list(engine.parameters.items())
    engine.model.side_effect = lambda **kwargs: SimpleNamespace(loss=Loss(engine.mean_loss, engine))
    engine.torch = SimpleNamespace(float32='float32', bfloat16='bfloat16', long='long',
        manual_seed=MagicMock(), tensor=MagicMock(side_effect=lambda value, **kwargs: value),
        autocast=MagicMock(side_effect=lambda **kwargs: nullcontext()), isfinite=Finite,
        optim=SimpleNamespace(AdamW=MagicMock()))

    def make_optimizer(parameters, **kwargs):
        optimizer = MagicMock()

        def zero_grad(**kwargs):
            for parameter in parameters:
                parameter.grad = None

        def step():
            for parameter in parameters:
                parameter.value += engine.parameter_step

        optimizer.zero_grad.side_effect = zero_grad
        optimizer.step.side_effect = step
        engine.optimizer = optimizer
        return optimizer

    def save(directory, **kwargs):
        directory.mkdir()
        (directory / 'adapter_model.safetensors').write_bytes(b'fake adapter, not model weights')
        (directory / 'adapter_config.json').write_text('{}')

    engine.torch.optim.AdamW.side_effect = make_optimizer
    engine.model.save_pretrained.side_effect = save
    return engine


def fake_encoding(stack, encoded):
    encoder = stack.enter_context(patch.object(runner.source, 'encode_rows',
        side_effect=[encoded[:32], encoded[32:64], encoded[84:]]))
    cue_encoder = stack.enter_context(patch.object(runner.cue_material, 'encode_cue_rows', return_value=encoded[64:84]))
    stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash',
        side_effect=lambda parameters: repr(sorted((name, parameter.value) for name, parameter in parameters.items()))))
    return encoder, cue_encoder


class ScheduleTests(unittest.TestCase):
    def test_case_order_original_eight_views_and_duplicate_indexes(self):
        selected = (3, 1, 3)
        expected = (87, 91, 95, 99, 103, 107, 111, 115,
                    85, 89, 93, 97, 101, 105, 109, 113,
                    87, 91, 95, 99, 103, 107, 111, 115)
        self.assertEqual(runner.selected_new_indexes('CHILD_CORRECTIVE', selected), expected)
        self.assertEqual(runner.selected_new_indexes('UNIFORM_REPLAY', selected), tuple(range(84, 116)))
        self.assertEqual(runner.training_indexes(5, 'CHILD_CORRECTIVE', selected), ((4, 68, 85, 89), (4, 68, 92, 93)))
        self.assertEqual(runner.training_indexes(13, 'CHILD_CORRECTIVE', selected)[0][2:], expected[:2])
        layout = runner.selection_layout('CHILD_CORRECTIVE', selected)
        self.assertEqual(layout['arm_new_row_indexes'], list(expected))
        self.assertEqual(layout['selected_case_row_indexes'][0], layout['selected_case_row_indexes'][2])
        self.assertEqual(layout['encoded_row_count'], 116)

    def test_every_bounded_selection_has_exact_indexed_schedule_and_doses(self):
        for length in range(1, 5):
            for selected in product(range(4), repeat=length):
                arm_rows = [84 + view * 4 + event for event in selected for view in range(8)]
                counts = Counter()
                for update in range(1, 101):
                    offset = update - 1
                    actual, reference = runner.training_indexes(update, 'CHILD_CORRECTIVE', selected)
                    self.assertEqual(actual, (offset % 64, 64 + offset % 20,
                        arm_rows[(2 * offset) % len(arm_rows)], arm_rows[(2 * offset + 1) % len(arm_rows)]))
                    uniform, uniform_reference = runner.training_indexes(update, 'UNIFORM_REPLAY', selected)
                    self.assertEqual(reference, (offset % 64, 64 + offset % 20,
                        84 + 2 * offset % 32, 84 + (2 * offset + 1) % 32))
                    self.assertEqual(uniform, reference)
                    self.assertEqual(uniform_reference, reference)
                    counts.update(actual)
                self.assertEqual(sum(counts[index] for index in range(32)), 64)
                self.assertEqual(sum(counts[index] for index in range(32, 64)), 36)
                self.assertEqual(sum(counts[index] for index in range(64, 84)), 100)
                self.assertEqual({counts[index] for index in range(64, 84)}, {5})
                expected_new = Counter(arm_rows[slot % len(arm_rows)] for slot in range(200))
                self.assertEqual(Counter({index: count for index, count in counts.items() if index >= 84}), expected_new)

    def test_normalization_uses_shared_uniform_causal_counts_with_unequal_lengths(self):
        encoded = encoded_fixture()
        original = deepcopy(encoded)
        scales = []
        for selected in ((0,), (3,), (1, 3), (3, 1, 3), (0, 1, 2, 3)):
            for update in range(1, 101):
                indexes, reference_indexes, batch, reference, actual, scale = runner.training_batch(
                    encoded, update, 'CHILD_CORRECTIVE', selected)
                uniform_indexes, unused, uniform, uniform_reference, uniform_actual, uniform_scale = runner.training_batch(
                    encoded, update, 'UNIFORM_REPLAY', selected)
                self.assertEqual(reference_indexes, uniform_indexes)
                self.assertEqual(reference, sum(label != -100 for labels in uniform['labels'] for label in labels[1:]))
                self.assertEqual((uniform_reference, uniform_actual, uniform_scale), (reference, reference, 1.0))
                self.assertEqual(actual, sum(len(encoded[index].target_ids) for index in indexes))
                self.assertEqual(batch, runner.source.native.collate([encoded[index] for index in indexes], pad_id=151643))
                self.assertEqual(scale, actual / reference)
                self.assertAlmostEqual(2.0 * scale, (2.0 * actual) / reference)
                scales.append(scale)
        self.assertGreater(max(scales), 1)
        self.assertLess(min(scales), 1)
        self.assertEqual(encoded, original)

    def test_invalid_bounds_and_empty_selection_are_not_uniform_fallbacks(self):
        for arm in runner.REPLAY_ARMS:
            for selected in ([], (), [0] * 5, [-1], [4], [True], [1.0], ['1'], None, '0', {0}):
                with self.subTest(arm=arm, selected=selected), self.assertRaises(ValueError):
                    runner.selected_new_indexes(arm, selected)
            for update in (0, -1, 101, True, 1.0, '1', None):
                with self.assertRaisesRegex(ValueError, 'fixed_100'):
                    runner.training_indexes(update, arm, [0])
        with self.assertRaisesRegex(ValueError, 'known_corrective'):
            runner.selected_new_indexes('CUE_LOSS_OFF', [0])
        for count in (0, 84, 115, 117):
            with self.assertRaisesRegex(ValueError, '116'):
                runner.training_batch((encoded_fixture() * 2)[:count], 1, 'CHILD_CORRECTIVE', [0])

    def test_causal_first_label_and_positive_denominators(self):
        encoded = list(encoded_fixture())
        indexes, reference_indexes, batch, reference, actual, scale = runner.training_batch(encoded, 1, 'CHILD_CORRECTIVE', [3])
        for change_reference in (True, False):
            changed_encoded, changed_batch = deepcopy(encoded), deepcopy(batch)
            if change_reference:
                row = changed_encoded[reference_indexes[0]]
                changed_encoded[reference_indexes[0]] = replace(row, labels=(999,) + row.labels[1:])
            else:
                changed_batch['labels'][0][0] = 999
            with self.assertRaisesRegex(ValueError, 'first_causal_label'):
                runner.loss_normalization(changed_encoded, reference_indexes, changed_batch)
        masked = deepcopy(batch)
        masked['labels'] = [[-100] * len(labels) for labels in masked['labels']]
        with self.assertRaisesRegex(ValueError, 'positive_matched'):
            runner.loss_normalization(encoded, reference_indexes, masked)
        for index in reference_indexes:
            encoded[index] = replace(encoded[index], labels=(-100,) * len(encoded[index].labels))
        with self.assertRaisesRegex(ValueError, 'positive_matched'):
            runner.loss_normalization(encoded, reference_indexes, batch)
        for bad_indexes in ((-1, 64, 84, 85), (0, 64, 84, 116), (0, 64, 84), (False, 64, 84, 85)):
            with self.assertRaisesRegex(ValueError, 'reference_indexes'):
                runner.loss_normalization(encoded, bad_indexes, batch)

    def test_original_row_layout_is_fixed_without_correctness_filtering(self):
        old, cue, new = source_fixture()
        new[0]['goal_correct'] = False
        runner.validate_row_layout(old, cue, new)
        for rows in ((old[:32], cue, new), (old, cue[:19], new), (old, cue, new[:31])):
            with self.assertRaisesRegex(ValueError, 'old64_cue20_new32'):
                runner.validate_row_layout(*rows)
        for changed in (sorted(new, key=lambda row: row['event']), list(reversed(new))):
            with self.assertRaisesRegex(ValueError, 'wrapper_major|distinct'):
                runner.validate_row_layout(old, cue, changed)


class TrainingTests(unittest.TestCase):
    def test_both_fits_log_actual_and_reference_preserve_sources_and_save_once(self):
        encoded = encoded_fixture()
        rows = source_fixture()
        original = deepcopy(rows)
        for arm in runner.REPLAY_ARMS:
            with self.subTest(arm=arm), TemporaryDirectory() as temporary, ExitStack() as stack:
                engine = fake_engine()
                encoder, cue_encoder = fake_encoding(stack, encoded)
                output = Path(temporary)
                result = runner.train(engine, *rows, output, replay_arm=arm, selected_source_indexes=[3, 1, 3])
                self.assertEqual(result['updates'], 100)
                self.assertEqual(result['budgets'], dict(old_memory_presentations=100, old_cue_presentations=100,
                    new_memory_presentations=200, original_bank_presentations=64, first_adult_presentations=36))
                self.assertEqual((result['old_fact_count'], result['train_seed']), (8, 0))
                self.assertEqual([call.args[0] for call in encoder.call_args_list], [rows[0][:32], rows[0][32:], rows[2]])
                cue_encoder.assert_called_once_with(rows[1], engine.tokenizer)
                engine.torch.manual_seed.assert_called_once_with(0)
                engine.torch.optim.AdamW.assert_called_once_with(list(engine.parameters.values())[:2],
                    lr=3e-5, **runner.source.native.OPTIMIZER)
                self.assertEqual(engine.optimizer.step.call_count, 100)
                self.assertEqual(engine.optimizer.zero_grad.call_count, 100)
                self.assertTrue(all(call.kwargs == dict(set_to_none=True) for call in engine.optimizer.zero_grad.call_args_list))
                self.assertEqual(engine.model.call_count, 100)
                self.assertEqual([call.args[0] for call in engine.check.call_args_list],
                    ['corrective_train_start'] + ['corrective_update'] * 100 + ['corrective_checkpoint'])
                engine.model.gradient_checkpointing_enable.assert_called_once_with(gradient_checkpointing_kwargs={'use_reentrant': False})
                engine.model.enable_input_require_grads.assert_called_once_with()
                self.assertFalse(engine.model.config.use_cache)
                self.assertFalse(engine.parameters['base.weight'].requires_grad)
                self.assertIsNone(engine.parameters['base.weight'].grad)
                self.assertEqual(engine.parameters['base.weight'].value, 10.0)
                self.assertTrue(engine.parameters['layer.lora_A.default.weight'].requires_grad)
                engine.model.save_pretrained.assert_called_once_with(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
                losses = [runner.source.json.loads(line) for line in (output / 'LOSSES.jsonl').read_text().splitlines()]
                self.assertEqual(len(losses), 100)
                for record, forward, backward in zip(losses, engine.model.call_args_list, engine.backward_losses):
                    indexes, reference_indexes, batch, reference, actual, scale = runner.training_batch(encoded,
                        record['update'], arm, [3, 1, 3])
                    self.assertEqual(record['row_indexes'], list(indexes))
                    self.assertEqual(record['reference_row_indexes'], list(reference_indexes))
                    self.assertEqual((record['actual_label_count'], record['reference_label_count']), (actual, reference))
                    self.assertEqual(record['loss_scale'], scale)
                    self.assertEqual(record['actual_mean_loss'], 2.0)
                    self.assertEqual(record['loss'], 2.0 * scale)
                    self.assertEqual(backward, record['loss'])
                    self.assertEqual(forward.kwargs, dict(batch, use_cache=False))
                self.assertEqual(result['actual_supervised_tokens'], sum(record['actual_label_count'] for record in losses))
                self.assertEqual(result['reference_supervised_tokens'], sum(record['reference_label_count'] for record in losses))
                self.assertNotEqual(result['adapter_state_before'], result['adapter_state_after'])
                masks = runner.source.read(output / 'MASKS.json')
                self.assertEqual(masks, runner.source.json.loads(runner.source.json.dumps([asdict(row) for row in encoded])))
                self.assertEqual(runner.source.read(output / 'SELECTION_LAYOUT.json'), runner.selection_layout(arm, [3, 1, 3]))
                provenance = runner.source.read(output / 'ADAPTER_PROVENANCE.json')
                for name, digest in provenance['adapter_files'].items():
                    self.assertEqual(digest, runner.source.file_hash(output / 'adapter' / name))
                for name, digest in provenance['training_artifact_sha256'].items():
                    self.assertEqual(digest, runner.source.file_hash(output / name))
                self.assertEqual(provenance['adapter_state_after'], result['adapter_state_after'])
                self.assertEqual(provenance['runner_sha256'], runner.source.file_hash(runner.__file__))
                with self.assertRaisesRegex(ValueError, 'fresh_training'):
                    runner.train(engine, *rows, output, replay_arm=arm, selected_source_indexes=[3])
                self.assertEqual(engine.model.save_pretrained.call_count, 1)
        self.assertEqual(rows, original)

    def test_failures_never_save_or_claim_a_completed_fit(self):
        for failure, message in (('mean_loss', 'invalid_corrective_loss'), ('gradient', 'invalid_corrective_gradients'),
                                 ('parameter_step', 'nonfinite_corrective_adapter'), ('unchanged', 'no_parameter_update'),
                                 ('runtime', 'runtime_expired')):
            with self.subTest(failure=failure), TemporaryDirectory() as temporary, ExitStack() as stack:
                engine = fake_engine()
                if failure == 'runtime':
                    engine.check.side_effect = [None, ValueError('runtime_expired')]
                elif failure == 'unchanged':
                    engine.parameter_step = 0.0
                else:
                    setattr(engine, failure, float('nan'))
                fake_encoding(stack, encoded_fixture())
                output = Path(temporary)
                with self.assertRaisesRegex(ValueError, message):
                    runner.train(engine, *source_fixture(), output, replay_arm='CHILD_CORRECTIVE', selected_source_indexes=[3])
                engine.model.save_pretrained.assert_not_called()
                self.assertTrue((output / 'MASKS.json').is_file())
                self.assertTrue((output / 'LOSSES.jsonl').is_file())
                self.assertFalse((output / 'ADAPTER_PROVENANCE.json').exists())

    def test_bad_selection_row_counts_and_pad_fail_before_encoding(self):
        for failure in ('selection', 'rows', 'pad'):
            with self.subTest(failure=failure), TemporaryDirectory() as temporary, ExitStack() as stack:
                engine = fake_engine()
                rows = list(source_fixture())
                selected = [] if failure == 'selection' else [0]
                if failure == 'rows':
                    rows[0] = rows[0][:32]
                if failure == 'pad':
                    engine.tokenizer.pad_token_id = 0
                encoder, cue_encoder = fake_encoding(stack, encoded_fixture())
                with self.assertRaises(ValueError):
                    runner.train(engine, *rows, Path(temporary), replay_arm='UNIFORM_REPLAY', selected_source_indexes=selected)
                encoder.assert_not_called()
                cue_encoder.assert_not_called()
                engine.model.assert_not_called()
                engine.torch.optim.AdamW.assert_not_called()

    def test_only_existing_fp32_lora_can_be_enabled(self):
        for failure in ('wrong_dtype', 'no_lora'):
            with self.subTest(failure=failure), TemporaryDirectory() as temporary, ExitStack() as stack:
                engine = fake_engine()
                if failure == 'wrong_dtype':
                    engine.parameters['layer.lora_A.default.weight'].dtype = 'bfloat16'
                else:
                    engine.model.named_parameters.return_value = [('base.weight', engine.parameters['base.weight'])]
                fake_encoding(stack, encoded_fixture())
                with self.assertRaisesRegex(ValueError, 'fp32_existing_lora|existing_adapter_required'):
                    runner.train(engine, *source_fixture(), Path(temporary), replay_arm='CHILD_CORRECTIVE', selected_source_indexes=[0])
                engine.model.assert_not_called()
                engine.model.save_pretrained.assert_not_called()


if __name__ == '__main__':
    unittest.main()
