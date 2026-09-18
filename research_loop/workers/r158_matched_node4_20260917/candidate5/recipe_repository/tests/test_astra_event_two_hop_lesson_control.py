"""CPU fixtures only: exact counterfactual masks, provenance and saved reload."""

from contextlib import ExitStack, nullcontext
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_event_two_hop_lesson_control as runner
from tests.test_astra_event_two_hop import arguments as old_arguments
from tests.test_astra_event_two_hop_transfer import setup as transfer_setup, arguments as transfer_arguments
from tests.test_astra_selected_reader_repair import write
from tests.test_astra_corrective_sleep_train import fake_engine
from tests.test_experienced_event_two_hop import generation
from tests.test_experienced_event_two_hop_lesson import coached_child


CONTROL_STATE = 'c' * 64


def encoded_fixture():
    rows = []
    for index in range(222):
        length = 265 if index == 0 else 20
        target = (42,) * (length - 1) + (151645,)
        rows.append(runner.source.native.EncodedRow((10,) + target + (11,),
            (-100,) + target + (-100,), target))
    return tuple(rows)


def reference_fixture(encoded):
    rows = dict(memory_rows=[dict(messages=[{'fixture': index}]) for index in range(128)],
        cue_rows=[dict(cue=index) for index in range(20)], audit_rows=[dict(audit=index) for index in range(62)],
        trajectory_rows=[dict(trajectory=index) for index in range(12)])
    schedule = [list(runner.lesson_driver.training_indexes(update)) for update in range(1, 101)]
    recipe = dict(updates=100, learning_rate=3e-5, optimizer='FRESH_ADAMW', seed=0, batch_size=4,
        loss='MEAN_CAUSAL_CE', schedule=schedule, group_sizes=[128, 20, 62, 12],
        trajectory_target_source='ACTUAL_COACHED_CHILD_COMMANDS_PARENT_HINTS_REMOVED')
    losses, doses = [], [0] * 12
    for update, indexes in enumerate(schedule, 1):
        losses.append(dict(update=update, row_indexes=indexes, loss=1.0,
            active_label_count=sum(label != -100 for index in indexes for label in encoded[index].labels[1:])))
        for index in indexes[2:]:
            doses[index - 210] += 1
    trained = dict(actual_supervised_tokens=8245, trajectory_presentations=doses)
    return rows, recipe, losses, trained


def arguments(root, phase, output=None):
    result = old_arguments(root, 'prepare' if phase == 'prepare' else 'collect', output or root / ('control-' + phase))
    result[result.index('--phase') + 1] = phase
    result += ['--lesson-root', str(root / 'lesson'), '--transfer-root', str(root / 'transfer')]
    if phase == 'after':
        result += ['--training', str(root / 'control-train')]
    return result


def setup(root, stack):
    state = transfer_setup(root, stack)
    encoded = encoded_fixture()
    raw_rows, recipe, losses, dose = reference_fixture(encoded)
    state.previous.update(memory_rows=raw_rows['memory_rows'][:96], cue_rows=raw_rows['cue_rows'],
        lesson_rows=raw_rows['audit_rows'], old_episodes=[dict(event=dict(raw=runner.source.material._event(fact)))
            for fact in state.previous['old_bank']])
    state.current['episodes'] = [dict(event=dict(raw=runner.source.material._event(fact))) for fact in state.current['bank']]
    fresh_rows = raw_rows['memory_rows'][96:]
    runner.prior.previous.read_collection.return_value = (state.current, fresh_rows, 'actual-a3')
    events = [dict(event=fact['event'], raw=runner.source.material._event(fact)) for fact in state.current['bank']]
    state.previous['held'] = runner.audit_lesson.build_cases(events, runner.audit_lesson.HELD)
    runner.prior.main(old_arguments(root, 'collect', root / 'old-collect'))
    runner.prior.main(old_arguments(root, 'readout', root / 'baseline')[:-2] + [
        '--collection', str(root / 'old-collect'), '--protocol', 'turnbound'])
    collection = runner.source.read(root / 'old-collect/COLLECTION.json')
    document = runner.lesson_driver.lesson.collect_lessons(collection, coached_child)
    raw_rows['trajectory_rows'] = runner.lesson_driver.lesson.replay_lessons(document)
    lesson = root / 'lesson'
    trained = runner.source.read(lesson / 'train/RESULT.json')
    recorded = trained['binding']
    recorded.update(collection_result_sha256=runner.source.file_hash(root / 'old-collect/RESULT.json'),
        baseline_result_sha256=runner.source.file_hash(root / 'baseline/RESULT.json'),
        memory_rows_sha256=runner.source.native._digest(raw_rows['memory_rows']),
        cue_rows_sha256=runner.source.native._digest(raw_rows['cue_rows']),
        audit_rows_sha256=runner.source.native._digest(raw_rows['audit_rows']))
    write(lesson / 'collect/LESSONS.json', document)
    collected = runner.source.read(lesson / 'collect/RESULT.json')
    collected.update(binding=recorded, phase='collect', model_calls=12,
                     lessons_sha256=runner.source.file_hash(lesson / 'collect/LESSONS.json'))
    write(lesson / 'collect/RESULT.json', collected)
    for index, capture in enumerate(document['captures']):
        write(lesson / ('collect/CALL_%03d.json' % index), capture)
    write(lesson / 'train/TRAINING_ROWS.json', raw_rows)
    write(lesson / 'train/MASKS.json', [asdict(row) for row in encoded])
    write(lesson / 'train/RECIPE.json', recipe)
    (lesson / 'train/LOSSES.jsonl').write_text(''.join(runner.source.json.dumps(row) + '\n' for row in losses))
    trained.update(dose, binding=recorded, arguments=dict(event_collection=str(root / 'old-collect'), baseline=str(root / 'baseline')),
        lessons_result_sha256=runner.source.file_hash(lesson / 'collect/RESULT.json'),
        training_files={name: runner.source.file_hash(lesson / 'train' / name)
                        for name in ('TRAINING_ROWS.json', 'MASKS.json', 'RECIPE.json', 'LOSSES.jsonl')})
    write(lesson / 'train/RESULT.json', trained)
    after = runner.source.read(lesson / 'after/RESULT.json')
    engine = state.factory.side_effect(SimpleNamespace(adapter_dir=str(lesson / 'train/adapter')), 'fixture', check=lambda label: None)
    calls = []

    def generate(messages, *, role='actor', condition=None, task_index=None, adapter_off=False):
        with engine.model.disable_adapter() if adapter_off else nullcontext():
            response = engine.generate(messages, max_new_tokens=160)
        capture = dict(call_index=len(calls), role=role, messages=messages, response=response, error=None,
                       condition=condition, task_index=task_index, adapter_off=adapter_off)
        write(lesson / ('after/CALL_%03d.json' % len(calls)), capture)
        calls.append(capture)
        return response

    after.update(binding=recorded, lessons_result_sha256=trained['lessons_result_sha256'],
        training_result_sha256=runner.source.file_hash(lesson / 'train/RESULT.json'),
        panels=runner.prior.evaluate(runner.hop.build_world(), collection, generate, lesson / 'after', protocol='turnbound'))
    after['model_calls'] = len(calls)
    write(lesson / 'after/RESULT.json', after)
    for phase, arm in (('collect', 'TRAINED'), ('readout', 'TRAINED'), ('readout', 'ORIGINAL')):
        target = root / 'transfer' / ('collect' if phase == 'collect' else arm)
        argv = transfer_arguments(root, phase, arm, target)
        if phase == 'readout':
            argv[argv.index('--collection') + 1] = str(root / 'transfer/collect')
        runner.transfer.main(argv)
    state.factory.reset_mock()
    state.tokenizer.reset_mock()
    state.encoded = encoded
    return state


class ControlTests(unittest.TestCase):
    def test_exact_mask_schedule_denominator_and_doses(self):
        encoded = encoded_fixture()
        original = deepcopy(encoded)
        controlled = runner.control_masks(encoded)
        self.assertEqual(controlled[:210], encoded[:210])
        for index in range(210, 222):
            self.assertEqual(controlled[index].input_ids, encoded[index].input_ids)
            self.assertEqual(controlled[index].target_ids, encoded[index].target_ids)
            self.assertEqual(set(controlled[index].labels), {-100})
        rows, recipe, losses, trained = reference_fixture(encoded)
        preflight = runner.validate_reference(rows, encoded, recipe, losses, trained)
        self.assertEqual(preflight['reference_tokens'], 8245)
        self.assertEqual(preflight['active_control_tokens'], 4245)
        self.assertEqual(sum(preflight['row_presentations'][210:]), 200)
        for update in range(1, 101):
            indexes, batch, reference, active, scale = runner.training_batch(encoded, update)
            offset = update - 1
            self.assertEqual(indexes, (offset % 128, 128 + offset % 82, 210 + 2 * offset % 12, 210 + (2 * offset + 1) % 12))
            self.assertEqual(batch['labels'][:2], runner.source.native.collate([encoded[index] for index in indexes], pad_id=151643)['labels'][:2])
            self.assertAlmostEqual((7.0 / active) * scale, 7.0 / reference)
        self.assertEqual(encoded, original)

    def test_reference_recipe_tokens_inputs_and_eot_fail_closed(self):
        encoded = encoded_fixture()
        rows, recipe, losses, trained = reference_fixture(encoded)
        for mutation in ('schedule', 'tokens', 'first_label', 'eot', 'old_rows'):
            with self.subTest(mutation=mutation):
                changed_rows, changed_recipe, changed_losses = deepcopy(rows), deepcopy(recipe), deepcopy(losses)
                changed_encoded = list(encoded)
                if mutation == 'schedule':
                    changed_recipe['schedule'][0][2] = 211
                elif mutation == 'tokens':
                    changed_losses[0]['active_label_count'] -= 1
                elif mutation == 'first_label':
                    changed_encoded[0] = replace(encoded[0], labels=(10,) + encoded[0].labels[1:])
                elif mutation == 'eot':
                    changed_encoded[0] = replace(encoded[0], target_ids=(42,))
                else:
                    changed_rows['memory_rows'].pop()
                with self.assertRaises(ValueError):
                    runner.validate_reference(changed_rows, changed_encoded, changed_recipe, changed_losses, trained)

    def test_prepare_full_provenance_without_model_or_reference_writes(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            before = {str(path): runner.source.file_hash(path) for folder in ('lesson', 'transfer')
                      for path in (root / folder).rglob('*') if path.is_file()}
            result = runner.main(arguments(root, 'prepare'))
            self.assertEqual(result['status'], 'PREPARED_NO_MODEL')
            self.assertEqual(result['fits'], 0)
            state.factory.assert_not_called()
            state.tokenizer.assert_not_called()
            self.assertEqual(before, {path: runner.source.file_hash(path) for path in before})
            with self.assertRaisesRegex(ValueError, 'reference_output_overlap_forbidden'):
                runner.main(arguments(root, 'prepare', root / 'lesson/new-control'))
            with self.assertRaises(FileExistsError):
                runner.main(arguments(root, 'prepare'))

    def test_parent_completed_arm_and_native_capture_joins(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            changes = [('lesson/train/RESULT.json', 'loaded_adapter_state_sha256', 'wrong'),
                ('lesson/after/RESULT.json', 'training_result_sha256', 'wrong'),
                ('transfer/ORIGINAL/RESULT.json', 'status', 'STARTED'),
                ('transfer/TRAINED/CALL_000.json', 'messages', []),
                ('lesson/collect/CALL_000.json', 'messages', [])]
            for index, (relative, field, value) in enumerate(changes):
                path = root / relative
                original = runner.source.read(path)
                write(path, dict(original, **{field: value}))
                with self.assertRaises(ValueError):
                    runner.main(arguments(root, 'prepare', root / ('rejected-' + str(index))))
                write(path, original)
            state.factory.assert_not_called()
            state.tokenizer.assert_not_called()

    def test_fake_optimizer_scales_loss_before_backward_no_reencode_drift(self):
        encoded = encoded_fixture()
        rows, recipe, losses, trained = reference_fixture(encoded)
        inputs = dict(rows=rows, encoded=encoded, preflight=runner.validate_reference(rows, encoded, recipe, losses, trained))
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            engine = fake_engine()
            engine.tokenizer.eos_token_id = 151645
            stack.enter_context(patch.object(runner.source, 'encode_row', side_effect=encoded[:128]))
            stack.enter_context(patch.object(runner.cues, 'encode_cue_rows', return_value=encoded[128:148]))
            stack.enter_context(patch.object(runner.audit_lesson, 'encode_rows', return_value=encoded[148:210]))
            stack.enter_context(patch.object(runner.lesson_driver.lesson, 'encode_rows', return_value=encoded[210:]))
            stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash', side_effect=lambda parameters:
                runner.prior.PARENT_STATE if parameters['layer.lora_A.default.weight'].value == 1.0 else CONTROL_STATE))
            output = Path(temporary)
            result = runner.train(engine, inputs, output)
            self.assertEqual(result['adapter_state_after'], CONTROL_STATE)
            self.assertEqual(result['reference_supervised_tokens'], 8245)
            self.assertEqual(result['actual_supervised_tokens'], 4245)
            self.assertEqual(engine.optimizer.step.call_count, 100)
            self.assertEqual(engine.backward_losses, [2.0 * batch['loss_scale'] for batch in inputs['preflight']['batches']])
            self.assertFalse(engine.parameters['base.weight'].requires_grad)
            self.assertEqual(engine.parameters['base.weight'].value, 10.0)
            engine.torch.manual_seed.assert_called_once_with(0)
            self.assertEqual(engine.torch.optim.AdamW.call_args.kwargs, dict(lr=3e-5, **runner.source.native.OPTIMIZER))
            self.assertEqual(runner.source.read(output / 'TRAINING_ROWS.json'), rows)

    def test_reencoding_mismatch_prevents_optimizer(self):
        encoded = encoded_fixture()
        rows, recipe, losses, trained = reference_fixture(encoded)
        inputs = dict(rows=rows, encoded=encoded, preflight=runner.validate_reference(rows, encoded, recipe, losses, trained))
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            engine = fake_engine()
            engine.tokenizer.eos_token_id = 151645
            changed = replace(encoded[0], input_ids=(99,) + encoded[0].input_ids[1:])
            stack.enter_context(patch.object(runner.source, 'encode_row', side_effect=(changed,) + encoded[1:128]))
            stack.enter_context(patch.object(runner.cues, 'encode_cue_rows', return_value=encoded[128:148]))
            stack.enter_context(patch.object(runner.audit_lesson, 'encode_rows', return_value=encoded[148:210]))
            stack.enter_context(patch.object(runner.lesson_driver.lesson, 'encode_rows', return_value=encoded[210:]))
            with self.assertRaisesRegex(ValueError, 'reencoded_reference_masks_must_match_exactly'):
                runner.train(engine, inputs, Path(temporary))
            engine.torch.optim.AdamW.assert_not_called()

    def test_saved_control_state_reload_after_not_reference_state(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            runner.main(arguments(root, 'prepare'))
            binding = runner.source.read(root / 'control-prepare/INPUTS.json')
            preflight = runner.source.read(root / 'control-prepare/PREFLIGHT.json')
            directory = root / 'control-train'
            write(directory / 'adapter/adapter_config.json', {'r': 8})
            (directory / 'adapter/adapter_model.safetensors').write_text('fake control adapter')
            write(directory / 'TRAINING_ROWS.json', runner.source.read(root / 'lesson/train/TRAINING_ROWS.json'))
            write(directory / 'REFERENCE_MASKS.json', [asdict(row) for row in state.encoded])
            write(directory / 'MASKS.json', [asdict(row) for row in runner.control_masks(state.encoded)])
            write(directory / 'PREFLIGHT.json', preflight)
            write(directory / 'RECIPE.json', runner.control_recipe(preflight))
            (directory / 'LOSSES.jsonl').write_text(''.join(runner.source.json.dumps(row) + '\n' for row in preflight['batches']))
            receipt = dict(schema=runner.SCHEMA, phase='train', arm=runner.ARM, status='COMPLETE',
                binding=binding, fits=1, updates=100, loaded_adapter_state_sha256=runner.prior.PARENT_STATE,
                adapter_state_after=CONTROL_STATE, parent_present=False, frozen_base_unchanged=True,
                reference_supervised_tokens=8245, actual_supervised_tokens=preflight['active_control_tokens'],
                trajectory_presentations=preflight['row_presentations'][210:],
                trajectory_supervised_presentations=[0] * 12,
                training_files={name: runner.source.file_hash(directory / name) for name in runner.TRAINING_FILES},
                adapter_files={path.name: runner.source.file_hash(path) for path in (directory / 'adapter').iterdir()})
            write(directory / 'RESULT.json', receipt)
            original_factory = state.factory.side_effect

            def factory(*args, **kwargs):
                engine = original_factory(*args, **kwargs)
                engine.state = CONTROL_STATE
                for fact in state.previous['old_bank'] + state.current['bank']:
                    engine.store[fact['event']] = runner.source.material._event(fact)
                original_generate = engine.generate

                def generate(messages, **options):
                    if messages[0]['content'] == runner.audit_lesson.SYSTEM:
                        return generation('NONE', messages)
                    return original_generate(messages, **options)

                engine.generate = generate
                return engine

            state.factory.side_effect = factory
            with patch.object(runner, 'train') as train:
                after = runner.main(arguments(root, 'after'))
            train.assert_not_called()
            self.assertEqual(after['loaded_adapter_state_sha256'], CONTROL_STATE)
            self.assertEqual(after['adapter_state_after'], CONTROL_STATE)
            self.assertEqual(after['fits'], 0)
            self.assertLessEqual(after['model_calls'], 208)
            self.assertEqual(after['held_audit']['overall']['denominator'], 16)
            self.assertEqual(after['retention']['0']['denominator'], 16)
            self.assertEqual(after['retention']['8']['denominator'], 16)
            self.assertEqual(len(list((root / 'control-after/old').glob('*_EPISODE_*.json'))), 16)
            self.assertEqual(len(list((root / 'control-after/fresh').glob('EPISODE_*.json'))), 8)
            self.assertEqual(state.engines[-1].arguments.adapter_dir, str(directory / 'adapter'))
            (directory / 'adapter/adapter_model.safetensors').write_text('tampered')
            state.factory.reset_mock()
            with self.assertRaises(ValueError):
                runner.main(arguments(root, 'after', root / 'bad-after'))
            state.factory.assert_not_called()

    def test_import_and_archive_guard_no_native_execution(self):
        script = """
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_event_two_hop_lesson_control
"""
        result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        guard = Path(runner.__file__).with_name('astra_event_two_hop_lesson_control_guard.sh')
        result = subprocess.run(['bash', '-n', str(guard)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = guard.read_text()
        self.assertNotIn('git -C', text)
        self.assertIn('cat "$root/source_commit.txt"', text)
        self.assertEqual(text.count('--kill-after=60 3600'), 2)
        for fragment in ('CUDA_VISIBLE_DEVICES= python3', '"$index" "$uuid"', 'service_exceptions.json',
                'time.time()+7320 < 1789980180-21600', 'OMP_NUM_THREADS=1', '--phase after --training'):
            self.assertIn(fragment, text)


if __name__ == '__main__':
    unittest.main()
