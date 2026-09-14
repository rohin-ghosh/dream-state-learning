"""CPU-only reader-audit trainer tests, not evidence of native learning."""

from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from gpu import astra_reader_audit_lesson_train as runner
from tests.test_astra_corrective_sleep_train import fake_engine
from tests.test_astra_pchain2_native import FakeTokenizer
from tests.test_experienced_event_cue_sleep import Tokenizer


def encoded_fixture(lesson_count):
    rows = []
    for index in range(100 + lesson_count):
        prefix = (10,) * (index % 4 + 1)
        target = tuple(range(20, 20 + index % 7 + 1)) + (1,)
        rows.append(runner.source.native.EncodedRow(prefix + target + (11,),
            (-100,) * len(prefix) + target + (-100,), target))
    return tuple(rows)


def raw_fixture(lesson_count):
    return ([dict(messages=['memory%d' % index]) for index in range(80)],
            [dict(cue=index) for index in range(20)], [dict(lesson=index) for index in range(lesson_count)])


def fake_dispatch(stack, encoded):
    memory = stack.enter_context(patch.object(runner.source, 'encode_rows', side_effect=[encoded[:32], encoded[32:64]]))
    tail = stack.enter_context(patch.object(runner.source, 'encode_row', side_effect=encoded[64:80]))
    cue = stack.enter_context(patch.object(runner.cue_material, 'encode_cue_rows', return_value=encoded[80:100]))
    lesson = SimpleNamespace(__file__=__file__, encode_rows=MagicMock(return_value=encoded[100:]))
    importer = stack.enter_context(patch.object(runner, 'import_module', return_value=lesson))
    stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash',
        side_effect=lambda parameters: repr(sorted((name, value.value) for name, value in parameters.items()))))
    return memory, tail, cue, lesson, importer


class Tests(unittest.TestCase):
    def test_exact_schedule_all_lesson_lengths_and_group_doses(self):
        for lesson_count in range(1, 65):
            counts = Counter()
            for update in range(1, 201):
                offset = update - 1
                indexes = runner.training_indexes(update, lesson_count)
                self.assertEqual(indexes, (offset % 80, 80 + offset % 20,
                    100 + 2 * offset % lesson_count, 100 + (2 * offset + 1) % lesson_count))
                counts.update(indexes)
            self.assertEqual(sum(counts[index] for index in range(80)), 200)
            self.assertEqual(sum(counts[index] for index in range(80, 100)), 200)
            self.assertEqual(sum(counts[index] for index in range(100, 100 + lesson_count)), 400)
            self.assertEqual(sum(counts[index] for index in range(64)), 168)
            self.assertEqual(sum(counts[index] for index in range(64, 80)), 32)
            self.assertEqual({counts[index] for index in range(80, 100)}, {10})

    def test_control_only_masks_lessons_and_uses_treatment_denominator(self):
        for lesson_count in (1, 16, 17, 64):
            encoded = encoded_fixture(lesson_count)
            original = deepcopy(encoded)
            for update in range(1, 201):
                indexes, treatment, reference, actual, scale = runner.training_batch(encoded, update, lesson_count, 'AUDIT_SFT')
                off_indexes, control, off_reference, off_actual, off_scale = runner.training_batch(encoded, update, lesson_count, 'AUDIT_LOSS_OFF')
                self.assertEqual(indexes, off_indexes)
                self.assertEqual(treatment['input_ids'], control['input_ids'])
                self.assertEqual(treatment['attention_mask'], control['attention_mask'])
                self.assertEqual(treatment['labels'][:2], control['labels'][:2])
                self.assertTrue(all(label == -100 for labels in control['labels'][2:] for label in labels))
                self.assertEqual((reference, actual, scale), (off_reference, off_reference, 1))
                self.assertEqual(reference, sum(len(encoded[index].target_ids) for index in indexes))
                self.assertEqual(off_actual, sum(len(encoded[index].target_ids) for index in indexes[:2]))
                self.assertEqual(off_scale, off_actual / reference)
                self.assertAlmostEqual((7.0 / off_actual) * off_scale, 7.0 / reference)
                self.assertGreater(off_actual, 0)
                self.assertLess(off_actual, reference)
            self.assertEqual(encoded, original)

    def test_invalid_arms_bounds_and_shapes(self):
        for count in (0, 65, -1, True, 16.0, None):
            with self.assertRaises(ValueError):
                runner.training_indexes(1, count)
        for update in (0, 201, -1, True, 1.0):
            with self.assertRaisesRegex(ValueError, 'fixed_200'):
                runner.training_indexes(update, 16)
        with self.assertRaisesRegex(ValueError, 'known_reader_audit'):
            runner.training_batch(encoded_fixture(16), 1, 16, 'CHILD_CORRECTIVE')
        with self.assertRaisesRegex(ValueError, 'encoded_layout'):
            runner.training_batch(encoded_fixture(16)[:-1], 1, 16, 'AUDIT_SFT')
        for which, count in ((0, 64), (1, 19), (2, 0), (2, 65)):
            rows = list(raw_fixture(65))
            rows[which] = rows[which][:count]
            if which != 2:
                rows[2] = rows[2][:16]
            with TemporaryDirectory() as temporary, self.assertRaises(ValueError):
                runner.train(None, *rows, Path(temporary), arm='AUDIT_SFT')

    def test_memory_tail_uses_exact_row_encoder_without_expanding_selected_content(self):
        bank = runner.source.material.build_bank(runner.source.MASTER)
        episodes = [dict(fact=fact,
            exploration=dict(raw='EXPLORE ' + fact['node'] + ' ' + fact['port'], terminal=True, truncated=False),
            event=dict(raw=runner.source.material._event(fact), terminal=True, truncated=False)) for fact in bank]
        original = runner.source.material.compile_rows(bank, episodes)
        selected = [row for row in original if row['event'] in (bank[0]['event'], bank[2]['event'])]
        rows = original + original + selected
        snapshot = deepcopy(rows)
        tokenizer = FakeTokenizer()
        encoded = runner.encode_memory_rows(rows, tokenizer)
        self.assertEqual(len(encoded), 80)
        runner.validate_masks(encoded, tokenizer.eos_token_id)
        for raw, row in zip(rows, encoded):
            self.assertEqual(row.target_ids, tuple(tokenizer.encode(raw['messages'][-1]['content']) + [1]))
            self.assertEqual(row.labels[-1], -100)
        self.assertEqual(rows, snapshot)
        self.assertEqual(encoded[64:], tuple(runner.source.encode_row(row['messages'], tokenizer) for row in selected))

    def test_parent_safe_lesson_encoder_and_target_eot_masks(self):
        lesson = runner.import_module(runner.LESSON_MODULE)
        facts = [fact for master in ('audit-cpu-fixture-a', 'audit-cpu-fixture-b')
                 for fact in runner.source.material.build_bank(master)]
        events = [dict(event=fact['event'], raw=runner.source.material._event(fact)) for fact in facts]
        cases = lesson.build_cases(events, lesson.DEV)
        responses = iter(case['expected'] for case in cases['cases'])
        collection = lesson.collect_cases(cases, lambda messages: dict(raw=next(responses), terminal=True, truncated=False), True)
        rows = collection['rows'][:16]
        tokenizer = Tokenizer()
        encoded = lesson.encode_rows(rows, tokenizer)
        runner.validate_masks(encoded, tokenizer.eos_token_id)
        for raw, row in zip(rows, encoded):
            self.assertTrue(any(lesson.PARENT_GUIDANCE in message['content'] for message in raw['capture']['messages']))
            self.assertFalse(any(lesson.PARENT_GUIDANCE in message['content'] for message in raw['prefix']))
            self.assertNotIn(lesson.PARENT_GUIDANCE, tokenizer.decode(row.input_ids))
            self.assertEqual(tokenizer.decode(row.target_ids), raw['assistant'] + tokenizer.eos_token)
        changed = deepcopy(rows)
        changed[0]['prefix'][0]['content'] += lesson.PARENT_GUIDANCE
        with self.assertRaises(ValueError):
            lesson.encode_rows(changed, tokenizer)

    def test_mask_validation_rejects_prefix_eot_and_label_drift(self):
        encoded = encoded_fixture(16)
        row = encoded[0]
        for invalid in (replace(row, labels=(10,) + row.labels[1:]),
                        replace(row, target_ids=row.target_ids[:-1]),
                        replace(row, input_ids=(10,) * len(row.input_ids)),
                        replace(row, labels=row.labels[:-1])):
            with self.assertRaises(ValueError):
                runner.validate_masks((invalid,), 1)
        altered = list(encoded)
        altered[0] = replace(row, labels=(10,) + row.labels[1:])
        with self.assertRaisesRegex(ValueError, 'first_causal_label'):
            runner.training_batch(altered, 1, 16, 'AUDIT_SFT')

    def test_fake_train_dispatch_receipts_and_fixed_endpoint(self):
        for arm in runner.ARMS:
            with self.subTest(arm=arm), TemporaryDirectory() as temporary, ExitStack() as stack:
                output = Path(temporary)
                rows, encoded = raw_fixture(17), encoded_fixture(17)
                snapshot = deepcopy(rows)
                engine = fake_engine()
                engine.tokenizer.eos_token_id = 1
                memory, tail, cue, lesson, importer = fake_dispatch(stack, encoded)
                result = runner.train(engine, *rows, output, arm=arm)
                importer.assert_called_once_with(runner.LESSON_MODULE)
                self.assertEqual([call.args[0] for call in memory.call_args_list], [rows[0][:32], rows[0][32:64]])
                self.assertEqual([call.args[0] for call in tail.call_args_list], [row['messages'] for row in rows[0][64:]])
                cue.assert_called_once_with(rows[1], engine.tokenizer)
                lesson.encode_rows.assert_called_once_with(rows[2], engine.tokenizer)
                self.assertEqual(result['schema'], 'DEV_READER_AUDIT_LESSON_SLEEP_V1')
                self.assertEqual(result['updates'], 200)
                self.assertEqual((result['memory_presentations'], result['cue_presentations'], result['lesson_presentations']), (200, 200, 400))
                self.assertEqual(result['lesson_supervised_presentations'], 400 if arm == 'AUDIT_SFT' else 0)
                engine.torch.manual_seed.assert_called_once_with(0)
                engine.torch.optim.AdamW.assert_called_once_with(list(engine.parameters.values())[:2], lr=3e-5, **runner.source.native.OPTIMIZER)
                self.assertEqual(engine.optimizer.step.call_count, 200)
                self.assertEqual(engine.model.call_count, 200)
                self.assertFalse(engine.parameters['base.weight'].requires_grad)
                self.assertEqual(engine.parameters['base.weight'].value, 10)
                self.assertNotEqual(result['adapter_state_before'], result['adapter_state_after'])
                losses = [runner.source.json.loads(line) for line in (output / 'LOSSES.jsonl').read_text().splitlines()]
                self.assertEqual(len(losses), 200)
                for record, forward, backward in zip(losses, engine.model.call_args_list, engine.backward_losses):
                    indexes, batch, reference, actual, scale = runner.training_batch(encoded, record['update'], 17, arm)
                    self.assertEqual(record['row_indexes'], list(indexes))
                    self.assertEqual(record['reference_row_indexes'], list(indexes))
                    self.assertEqual((record['actual_label_count'], record['reference_label_count'], record['loss_scale']), (actual, reference, scale))
                    self.assertEqual(record['loss'], 2 * scale)
                    self.assertEqual(backward, record['loss'])
                    self.assertEqual(forward.kwargs, dict(batch, use_cache=False))
                self.assertEqual(result['actual_supervised_tokens'], sum(record['actual_label_count'] for record in losses))
                self.assertEqual(result['reference_supervised_tokens'], sum(record['reference_label_count'] for record in losses))
                self.assertEqual([call.args[0] for call in engine.check.call_args_list],
                    ['reader_audit_train_start'] + ['reader_audit_update'] * 200 + ['reader_audit_checkpoint'])
                engine.model.save_pretrained.assert_called_once_with(output / 'adapter', safe_serialization=True, save_embedding_layers=False)
                masks = runner.source.read(output / 'MASKS.json')
                self.assertEqual(len(masks), 117)
                self.assertTrue(all(any(label != -100 for label in row['labels']) for row in masks))
                self.assertEqual(runner.source.read(output / 'RECIPE.json')['updates'], 200)
                provenance = runner.source.read(output / 'ADAPTER_PROVENANCE.json')
                for code in provenance['code_provenance'].values():
                    self.assertEqual(code['sha256'], runner.source.file_hash(code['path']))
                    self.assertTrue(code['role'])
                for name, digest in provenance['training_artifact_sha256'].items():
                    self.assertEqual(digest, runner.source.file_hash(output / name))
                for name, digest in provenance['adapter_files'].items():
                    self.assertEqual(digest, runner.source.file_hash(output / 'adapter' / name))
                self.assertEqual(rows, snapshot)
                with self.assertRaisesRegex(ValueError, 'fresh_training'):
                    runner.train(engine, *rows, output, arm=arm)

    def test_parent_safe_encoder_rejection_and_runtime_expiry_do_not_fit_or_save(self):
        for failure in ('encoder', 'runtime', 'shape'):
            with self.subTest(failure=failure), TemporaryDirectory() as temporary, ExitStack() as stack:
                engine = fake_engine()
                engine.tokenizer.eos_token_id = 1
                memory, tail, cue, lesson, importer = fake_dispatch(stack, encoded_fixture(16))
                if failure == 'encoder':
                    lesson.encode_rows.side_effect = ValueError('parent_safe_encoder_rejection')
                elif failure == 'shape':
                    lesson.encode_rows.return_value = encoded_fixture(16)[100:115]
                else:
                    engine.check.side_effect = [None, ValueError('expired')]
                with self.assertRaises(ValueError):
                    runner.train(engine, *raw_fixture(16), Path(temporary), arm='AUDIT_LOSS_OFF')
                engine.model.assert_not_called()
                engine.model.save_pretrained.assert_not_called()


if __name__ == '__main__':
    unittest.main()
