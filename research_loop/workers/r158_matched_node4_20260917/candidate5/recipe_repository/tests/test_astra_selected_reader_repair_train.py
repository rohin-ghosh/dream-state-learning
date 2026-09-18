"""CPU-only selected reader-repair schedule and fake-native regressions."""

from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_selected_reader_repair_train as runner
from tests.test_astra_corrective_sleep_train import fake_engine
from tests.test_astra_reader_audit_lesson_train import encoded_fixture


def raw_fixture(memory_count=80):
    return ([dict(messages=['memory%d' % index]) for index in range(memory_count)],
            [dict(cue=index) for index in range(20)], [dict(lesson=index) for index in range(62)],
            [dict(event='event%d' % (index % 4), wrapper='W%d' % (index // 4)) for index in range(32)])


def fake_dispatch(stack, encoded, memory_count=80):
    cue_end = memory_count + 20
    new_offset = cue_end + 62
    memory = stack.enter_context(patch.object(runner.source, 'encode_row', side_effect=encoded[:memory_count]))
    cue = stack.enter_context(patch.object(runner.cue_material, 'encode_cue_rows', return_value=encoded[memory_count:cue_end]))
    lesson = SimpleNamespace(__file__=__file__, encode_rows=MagicMock(return_value=encoded[cue_end:new_offset]))
    stack.enter_context(patch.object(runner, 'import_module', return_value=lesson))
    new = stack.enter_context(patch.object(runner.source, 'encode_rows', return_value=encoded[new_offset:]))
    stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash',
        side_effect=lambda parameters: repr(sorted((name, value.value) for name, value in parameters.items()))))
    return memory, cue, lesson, new


class Tests(unittest.TestCase):
    def test_explicit_80_preserves_legacy_defaults_and_recipe(self):
        self.assertEqual((runner.MEMORY_COUNT, runner.NEW_OFFSET, runner.ENCODED_COUNT), (80, 162, 194))
        for arm in runner.MATERIAL_ARMS:
            selected = [1, 3, 3]
            self.assertEqual(runner.recipe(arm, selected), runner.recipe(arm, selected, memory_count=80))
            config = runner.recipe(arm, selected)
            self.assertEqual(config['row_order'], 'MEMORY80_CUE20_LESSON62_NEW32_WRAPPER_MAJOR')
            self.assertEqual((config['memory_row_count'], config['new_row_offset'], config['encoded_row_count']), (80, 162, 194))
            self.assertEqual(config['schedule']['memory'], '(update-1)%80')
            self.assertEqual(config['schedule']['behavior'], '80+(update-1)%82')
            for update in range(1, 101):
                self.assertEqual(runner.training_batch(encoded_fixture(94), update, arm, selected),
                    runner.training_batch(encoded_fixture(94), update, arm, selected, memory_count=80))

    def test_96_all_four_cells_share_first_100_memory_rows_and_exact_doses(self):
        for selected in ([1, 3, 3], [1]):
            for arm in runner.MATERIAL_ARMS:
                pool = (tuple(range(178, 210)) if arm == 'UNIFORM' else
                        tuple(178 + 4 * view + index for index in selected for view in range(8)))
                self.assertEqual(runner.selected_new_indexes(arm, selected, memory_count=96), pool)
                counts = Counter()
                for update in range(1, 101):
                    offset = update - 1
                    actual, reference = runner.training_indexes(update, arm, selected, memory_count=96)
                    self.assertEqual(actual, (offset % 96, 96 + offset % 82,
                        pool[2 * offset % len(pool)], pool[(2 * offset + 1) % len(pool)]))
                    self.assertEqual(reference, (offset % 96, 96 + offset % 82,
                        178 + 2 * offset % 32, 178 + (2 * offset + 1) % 32))
                    counts.update(actual)
                self.assertEqual([counts[index] for index in range(96)], [2] * 4 + [1] * 92)
                self.assertEqual([counts[index] for index in range(96, 116)], [2] * 18 + [1] * 2)
                self.assertEqual([counts[index] for index in range(116, 178)], [1] * 62)
                self.assertEqual(sum(counts[index] for index in range(178, 210)), 200)
                facts = [sum(counts[index] for index in range(178 + event, 210, 4)) for event in range(4)]
                expected = [50] * 4 if arm == 'UNIFORM' else [0, 72, 0, 128] if len(selected) == 3 else [0, 200, 0, 0]
                self.assertEqual(facts, expected)

    def test_96_reference_denominator_remains_uniform_with_unequal_targets(self):
        encoded = encoded_fixture(110)
        original = deepcopy(encoded)
        scales = []
        for selected in ([1], [1, 3, 3]):
            for update in range(1, 101):
                indexes, reference_indexes, batch, reference, actual, scale = runner.training_batch(
                    encoded, update, 'SELECTED', selected, memory_count=96)
                uniform_indexes, unused, uniform, uniform_reference, uniform_actual, uniform_scale = runner.training_batch(
                    encoded, update, 'UNIFORM', selected, memory_count=96)
                self.assertEqual(reference_indexes, uniform_indexes)
                self.assertEqual((uniform_reference, uniform_actual, uniform_scale), (reference, reference, 1))
                self.assertEqual(reference, sum(label != -100 for labels in uniform['labels'] for label in labels[1:]))
                self.assertEqual(actual, sum(len(encoded[index].target_ids) for index in indexes))
                self.assertEqual(batch, runner.source.native.collate([encoded[index] for index in indexes], pad_id=151643))
                self.assertEqual(scale, actual / reference)
                scales.append(scale)
        self.assertGreater(max(scales), 1)
        self.assertLess(min(scales), 1)
        self.assertEqual(encoded, original)

    def test_memory_count_is_explicit_and_only_80_or_96(self):
        for count in (0, 64, 79, 81, 95, 97, 100, True, 80.0, 96.0, '96', None):
            with self.subTest(memory_count=count):
                with self.assertRaisesRegex(ValueError, 'memory_count_80_or_96'):
                    runner.recipe('SELECTED', [1], memory_count=count)
                with TemporaryDirectory() as temporary, self.assertRaisesRegex(ValueError, 'memory_count_80_or_96'):
                    runner.train(None, *raw_fixture(), Path(temporary), material_arm='SELECTED',
                                 selected_source_indexes=[1], memory_count=count)
        with self.assertRaisesRegex(ValueError, 'exact_80_20_62_32'):
            runner.validate_row_layout(*raw_fixture(96))
        with self.assertRaisesRegex(ValueError, 'exact_96_20_62_32'):
            runner.validate_row_layout(*raw_fixture(), memory_count=96)
        for count, wrong_encoded in ((80, encoded_fixture(110)), (96, encoded_fixture(94))):
            with self.assertRaisesRegex(ValueError, 'encoded_rows_required'):
                runner.training_batch(wrong_encoded, 1, 'SELECTED', [1], memory_count=count)
        runner.validate_row_layout(*raw_fixture(96), memory_count=96)
        for group in range(4):
            rows = list(raw_fixture(96))
            rows[group] = rows[group][:-1]
            with self.assertRaisesRegex(ValueError, 'exact_96_20_62_32'):
                runner.validate_row_layout(*rows, memory_count=96)
        rows = list(raw_fixture(96))
        rows[-1] = sorted(rows[-1], key=lambda row: row['event'])
        with self.assertRaises(ValueError):
            runner.validate_row_layout(*rows, memory_count=96)

    def test_source_major_duplicates_and_original_wrapper_major_reference(self):
        expected = (163, 167, 171, 175, 179, 183, 187, 191,
                    165, 169, 173, 177, 181, 185, 189, 193,
                    165, 169, 173, 177, 181, 185, 189, 193)
        self.assertEqual(runner.selected_new_indexes('SELECTED', [1, 3, 3]), expected)
        self.assertEqual(runner.selected_new_indexes('UNIFORM', [1, 3, 3]), tuple(range(162, 194)))
        self.assertEqual(runner.training_indexes(1, 'SELECTED', [1, 3, 3]), ((0, 80, 163, 167), (0, 80, 162, 163)))
        self.assertEqual(runner.training_indexes(13, 'SELECTED', [1, 3, 3])[0][2:], expected[:2])

    def test_all_four_cells_exact_doses_and_complete_trait_replay(self):
        for selected in ([1, 3, 3], [1]):
            for arm in runner.MATERIAL_ARMS:
                pool = runner.selected_new_indexes(arm, selected)
                counts = Counter()
                for update in range(1, 101):
                    offset = update - 1
                    actual, reference = runner.training_indexes(update, arm, selected)
                    self.assertEqual(actual, (offset % 80, 80 + offset % 82,
                        pool[2 * offset % len(pool)], pool[(2 * offset + 1) % len(pool)]))
                    self.assertEqual(reference, (offset % 80, 80 + offset % 82,
                        162 + 2 * offset % 32, 162 + (2 * offset + 1) % 32))
                    counts.update(actual)
                self.assertEqual(sum(counts[index] for index in range(80)), 100)
                self.assertEqual(sum(counts[index] for index in range(80, 100)), 38)
                self.assertEqual([counts[index] for index in range(100, 162)], [1] * 62)
                self.assertEqual(sum(counts[index] for index in range(162, 194)), 200)
                facts = [sum(counts[index] for index in range(162 + event, 194, 4)) for event in range(4)]
                expected = [50] * 4 if arm == 'UNIFORM' else [0, 72, 0, 128] if len(selected) == 3 else [0, 200, 0, 0]
                self.assertEqual(facts, expected)

    def test_up_to_eight_actual_pointers_keep_all_views_and_duplicates(self):
        for count in range(5, 9):
            selected = ([1, 3] * 4)[:count]
            pool = tuple(162 + 4 * view + index for index in selected for view in range(8))
            self.assertEqual(runner.selected_new_indexes('SELECTED', selected), pool)
            presented = tuple(index for update in range(1, 101)
                              for index in runner.training_indexes(update, 'SELECTED', selected)[0][2:])
            self.assertEqual(presented, tuple(pool[slot % len(pool)] for slot in range(200)))
            self.assertEqual(runner.selected_new_indexes('UNIFORM', selected), tuple(range(162, 194)))

    def test_shared_reference_denominator_unequal_targets_and_no_masking(self):
        encoded = encoded_fixture(94)
        original = deepcopy(encoded)
        scales = []
        for selected in ([1], [1, 3, 3]):
            for update in range(1, 101):
                indexes, reference_indexes, batch, reference, actual, scale = runner.training_batch(encoded, update, 'SELECTED', selected)
                uniform_indexes, unused, uniform, uniform_reference, uniform_actual, uniform_scale = runner.training_batch(encoded, update, 'UNIFORM', selected)
                self.assertEqual(reference_indexes, uniform_indexes)
                self.assertEqual((uniform_reference, uniform_actual, uniform_scale), (reference, reference, 1))
                self.assertEqual(reference, sum(label != -100 for row in uniform['labels'] for label in row[1:]))
                self.assertEqual(actual, sum(len(encoded[index].target_ids) for index in indexes))
                self.assertEqual(batch, runner.source.native.collate([encoded[index] for index in indexes], pad_id=151643))
                self.assertEqual(scale, actual / reference)
                self.assertAlmostEqual(2 * scale, 2 * actual / reference)
                scales.append(scale)
        self.assertGreater(max(scales), 1)
        self.assertLess(min(scales), 1)
        self.assertEqual(encoded, original)

    def test_invalid_bounds_exact_counts_and_wrapper_layout(self):
        for arm in runner.MATERIAL_ARMS:
            for selected in ([], [1] * 9, [-1], [4], [True], [1.0], None):
                with self.assertRaises(ValueError):
                    runner.training_indexes(1, arm, selected)
        for update in (0, 101, True, 1.0):
            with self.assertRaisesRegex(ValueError, 'fixed_100'):
                runner.training_indexes(update, 'SELECTED', [1])
        with self.assertRaisesRegex(ValueError, 'material_arm'):
            runner.training_indexes(1, 'AUDIT_SFT', [1])
        for group in range(4):
            rows = list(raw_fixture())
            rows[group] = rows[group][:-1]
            with self.assertRaisesRegex(ValueError, '80_20_62_32'):
                runner.validate_row_layout(*rows)
        rows = list(raw_fixture())
        rows[-1] = sorted(rows[-1], key=lambda row: row['event'])
        with self.assertRaises(ValueError):
            runner.validate_row_layout(*rows)
        with self.assertRaisesRegex(ValueError, '194'):
            runner.training_batch(encoded_fixture(93), 1, 'SELECTED', [1])
        encoded = list(encoded_fixture(94))
        encoded[162] = replace(encoded[162], labels=(10,) + encoded[162].labels[1:])
        with self.assertRaisesRegex(ValueError, 'first_causal_label'):
            runner.training_batch(encoded, 1, 'SELECTED', [1])

    def test_fake_train_all_cells_dispatch_logs_provenance_exclusive_save(self):
        self.check_fake_train_all_cells(memory_count=80)

    def test_fake_train_96_all_cells_dispatch_logs_provenance_exclusive_save(self):
        self.check_fake_train_all_cells(memory_count=96)

    def check_fake_train_all_cells(self, memory_count):
        options = {} if memory_count == 80 else dict(memory_count=memory_count)
        new_offset = memory_count + 82
        for selected in ([1, 3, 3], [1]):
            for arm in runner.MATERIAL_ARMS:
                with self.subTest(arm=arm, selected=selected), TemporaryDirectory() as temporary, ExitStack() as stack:
                    rows, encoded = raw_fixture(memory_count), encoded_fixture(memory_count + 14)
                    snapshot = deepcopy(rows)
                    engine = fake_engine()
                    engine.tokenizer.eos_token_id = 1
                    memory, cue, lesson, new = fake_dispatch(stack, encoded, memory_count)
                    output = Path(temporary)
                    result = runner.train(engine, *rows, output, material_arm=arm, selected_source_indexes=selected, **options)
                    self.assertEqual(result['schema'], 'DEV_SELECTED_READER_REPAIR_SLEEP_V1')
                    self.assertEqual(result['updates'], 100)
                    self.assertEqual(result['budgets'], dict(memory_presentations=100, behavior_presentations=100,
                        cue_presentations=38, lesson_presentations=62, new_memory_presentations=200))
                    self.assertEqual([call.args[0] for call in memory.call_args_list], [row['messages'] for row in rows[0]])
                    cue.assert_called_once_with(rows[1], engine.tokenizer)
                    lesson.encode_rows.assert_called_once_with(rows[2], engine.tokenizer)
                    new.assert_called_once_with(rows[3], engine.tokenizer)
                    engine.torch.manual_seed.assert_called_once_with(0)
                    engine.torch.optim.AdamW.assert_called_once_with(list(engine.parameters.values())[:2], lr=3e-5, **runner.source.native.OPTIMIZER)
                    self.assertEqual(engine.optimizer.step.call_count, 100)
                    self.assertFalse(engine.parameters['base.weight'].requires_grad)
                    self.assertEqual(engine.parameters['base.weight'].value, 10)
                    losses = [runner.source.json.loads(line) for line in (output / 'LOSSES.jsonl').read_text().splitlines()]
                    self.assertEqual(len(losses), 100)
                    facts = [0] * 4
                    for record, forward, backward in zip(losses, engine.model.call_args_list, engine.backward_losses):
                        indexes, reference_indexes, batch, reference, actual, scale = runner.training_batch(
                            encoded, record['update'], arm, selected, **options)
                        self.assertEqual(record['row_indexes'], list(indexes))
                        self.assertEqual(record['reference_row_indexes'], list(reference_indexes))
                        self.assertEqual((record['actual_label_count'], record['reference_label_count']), (actual, reference))
                        self.assertEqual((record['loss_scale'], record['actual_mean_loss'], record['loss']), (scale, 2, 2 * scale))
                        self.assertEqual(backward, record['loss'])
                        self.assertEqual(forward.kwargs, dict(batch, use_cache=False))
                        for index in indexes[2:]:
                            facts[(index - new_offset) % 4] += 1
                    self.assertEqual(result['new_fact_presentations'], facts)
                    self.assertEqual(result['actual_supervised_tokens'], sum(row['actual_label_count'] for row in losses))
                    self.assertEqual(result['reference_supervised_tokens'], sum(row['reference_label_count'] for row in losses))
                    self.assertEqual([call.args[0] for call in engine.check.call_args_list],
                        ['selected_reader_repair_start'] + ['selected_reader_repair_update'] * 100 + ['selected_reader_repair_checkpoint'])
                    engine.model.save_pretrained.assert_called_once_with(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
                    self.assertEqual(len(runner.source.read(output / 'MASKS.json')), new_offset + 32)
                    config = runner.source.read(output / 'RECIPE.json')
                    self.assertEqual(config['updates'], 100)
                    self.assertEqual((config['memory_row_count'], config['new_row_offset'], config['encoded_row_count']),
                        (memory_count, new_offset, new_offset + 32))
                    self.assertEqual(config['new_source_events'], [row['event'] for row in rows[3][:4]])
                    self.assertEqual(config['row_order'], 'MEMORY%d_CUE20_LESSON62_NEW32_WRAPPER_MAJOR' % memory_count)
                    self.assertEqual(config['schedule']['memory'], '(update-1)%%%d' % memory_count)
                    self.assertEqual(config['schedule']['behavior'], '%d+(update-1)%%82' % memory_count)
                    self.assertNotEqual(result['adapter_state_before'], result['adapter_state_after'])
                    provenance = runner.source.read(output / 'ADAPTER_PROVENANCE.json')
                    for code in provenance['code_provenance'].values():
                        self.assertEqual(code['sha256'], runner.source.file_hash(code['path']))
                        self.assertTrue(code['role'])
                    for name, digest in provenance['adapter_files'].items():
                        self.assertEqual(digest, runner.source.file_hash(output / 'adapter' / name))
                    for name, digest in provenance['training_artifact_sha256'].items():
                        self.assertEqual(digest, runner.source.file_hash(output / name))
                    self.assertEqual(rows, snapshot)
                    with self.assertRaisesRegex(ValueError, 'fresh_training'):
                        runner.train(engine, *rows, output, material_arm=arm, selected_source_indexes=selected, **options)
                    self.assertEqual(engine.model.save_pretrained.call_count, 1)

    def test_encoder_rejection_runtime_and_nonfinite_failure_never_save(self):
        for failure in ('encoder', 'runtime', 'gradient', 'mean_loss', 'parameter_step', 'shape'):
            with self.subTest(failure=failure), TemporaryDirectory() as temporary, ExitStack() as stack:
                engine = fake_engine()
                engine.tokenizer.eos_token_id = 1
                memory, cue, lesson, new = fake_dispatch(stack, encoded_fixture(94))
                if failure == 'encoder':
                    lesson.encode_rows.side_effect = ValueError('parent_safe_encoder_rejected')
                elif failure == 'runtime':
                    engine.check.side_effect = [None, ValueError('expired')]
                elif failure == 'shape':
                    lesson.encode_rows.return_value = encoded_fixture(94)[100:161]
                else:
                    setattr(engine, failure, float('nan'))
                with self.assertRaises(ValueError):
                    runner.train(engine, *raw_fixture(), Path(temporary), material_arm='SELECTED', selected_source_indexes=[1])
                engine.model.save_pretrained.assert_not_called()
                self.assertFalse((Path(temporary) / 'ADAPTER_PROVENANCE.json').exists())


if __name__ == '__main__':
    unittest.main()
