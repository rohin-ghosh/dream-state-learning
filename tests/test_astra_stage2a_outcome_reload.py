"""CPU checkpoint admission, safetensors restore and bounded orchestration tests."""

from contextlib import ExitStack
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gpu import astra_stage2a_outcome_reload as source


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True))
    return sha256(path.read_bytes()).hexdigest()


def fixture(parent):
    root = parent / 'original'
    (root / 'adapter').mkdir(parents=True)
    (root / 'FITTED').mkdir()
    adapter = root / 'adapter'
    write(adapter / 'adapter_config.json', {'r': 8})
    (adapter / 'adapter_model.safetensors').write_bytes(b'synthetic-only')
    files = {path.name: sha256(path.read_bytes()).hexdigest() for path in adapter.iterdir()}
    training = dict(claim=source.pilot.CLAIM, completed_updates=256, seed=0, batch_size=4,
        optimizer=source.pilot.collector.plain(dict(source.pilot.training.OPTIMIZER_RECIPE)), rows_sha256='b' * 64,
        source_label='frozen D2 A3', adapter_sha256='c' * 64, files_sha256=files,
        checkpoint_kind=source.CHECKPOINT_KIND)
    training_hash = write(adapter / 'TRAINING.json', training)
    result = dict(status='DEV_OUTCOME_SFT_COMPLETE', reportable=True, claim=source.pilot.CLAIM,
        completed_updates=256, seed=0, batch_size=4, source_label='frozen D2 A3',
        collection={'rows_sha256': 'b' * 64}, adapter_sha256='c' * 64, adapter_files_sha256=files,
        master_hex=source.pilot.EVAL_MASTER.hex(), base_state_id=source.pilot.BASE_ID,
        fitted_state_id=source.pilot.FITTED_ID, eval_held_sha256='held', finished_unix=50,
        frozen_base_hashes=dict.fromkeys(('before_training', 'after_training',
            'after_base_evaluation', 'after_fitted_evaluation'), 'a' * 64),
        screens={'FITTED': {'accounting': {}, 'issues': [], 'metrics': {}}},
        tokenizer=dict(after_sha256='tokenizer', official_sha256='official', wrapper={}, chat_template_return_dict=False))
    result_hash = write(root / 'RESULT.json', result)
    write(root / 'REQUEST.json', dict(method=source.pilot.CLAIM,
        master_hex=source.pilot.EVAL_MASTER.hex(), base_state_id=source.pilot.BASE_ID,
        atom_state_id=source.pilot.FITTED_ID, expected_base_sha256='a' * 64, model_dir='pinned-model'))
    options = SimpleNamespace(original_run=str(root), output=str(parent / 'reload'), gpu_uuid='GPU-test',
                              result_sha256=result_hash, training_sha256=training_hash, deadline_unix=500)
    return options, result, training


class AdmissionTests(unittest.TestCase):
    def test_import_has_no_native_libraries(self):
        program = ('import sys; from gpu import astra_stage2a_outcome_reload; '
                   'assert not set(("torch", "peft", "transformers", "safetensors")) & set(sys.modules)')
        subprocess.run([sys.executable, '-B', '-c', program], check=True, timeout=30)

    def test_complete_pinned_original(self):
        with tempfile.TemporaryDirectory() as temporary:
            options, result, trained = fixture(Path(temporary))
            evidence = source.load_original(options.original_run, result_sha256=options.result_sha256,
                                            training_sha256=options.training_sha256)
            self.assertEqual(evidence['result']['values'], result)
            self.assertEqual(evidence['training']['values'], trained)

    def test_incomplete_wrong_master_recipe_and_base_rejected(self):
        cases = [('status', 'INCOMPLETE', 'completed_original'), ('master_hex', '00', 'eval_identity'),
                 ('completed_updates', 255, 'training_recipe'), ('frozen_base_hashes', {}, 'frozen_base')]
        for key, value, error in cases:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                options, result, unused = fixture(Path(temporary))
                result[key] = value
                options.result_sha256 = write(Path(options.original_run) / 'RESULT.json', result)
                with self.assertRaisesRegex(ValueError, error):
                    source.load_original(options.original_run, result_sha256=options.result_sha256,
                                         training_sha256=options.training_sha256)

    def test_hash_tampering_missing_files_extra_files_and_symlinks(self):
        for fault in ('result', 'training', 'weights', 'missing', 'extra', 'symlink'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                options, unused, unused_training = fixture(Path(temporary))
                root = Path(options.original_run)
                weights = root / 'adapter' / 'adapter_model.safetensors'
                if fault in ('result', 'training'):
                    path = root / 'RESULT.json' if fault == 'result' else root / 'adapter' / 'TRAINING.json'
                    path.write_text(path.read_text() + ' ')
                elif fault == 'weights':
                    weights.write_bytes(b'changed')
                elif fault == 'extra':
                    (root / 'adapter' / 'unlisted').write_bytes(b'extra')
                else:
                    weights.unlink()
                    if fault == 'symlink':
                        target = Path(temporary) / 'external'
                        target.write_bytes(b'synthetic-only')
                        weights.symlink_to(target)
                with self.assertRaises((ValueError, OSError)):
                    source.load_original(root, result_sha256=options.result_sha256,
                                         training_sha256=options.training_sha256)

    def test_failure_is_retained_before_any_native_loading(self):
        with tempfile.TemporaryDirectory() as temporary:
            options, unused, unused_training = fixture(Path(temporary))
            options.result_sha256 = '0' * 64
            with self.assertRaisesRegex(ValueError, 'document_hash_mismatch'):
                source.run(options, libraries=(), clock=lambda: 100)
            output = Path(options.output)
            self.assertEqual(json.loads((output / 'FAILED.json').read_text())['status'], 'FAILED_NO_COMPLETION')
            self.assertEqual(output.stat().st_mode & 0o222, 0)
            output.chmod(0o755)

    def test_deadline_is_fail_inclusive(self):
        for deadline in (99, 5601, float('inf')):
            with self.subTest(deadline=deadline), tempfile.TemporaryDirectory() as temporary:
                options, unused, unused_training = fixture(Path(temporary))
                options.deadline_unix = deadline
                with self.assertRaisesRegex(ValueError, 'deadline'):
                    source.run(options, libraries=(), clock=lambda: 100)
                output = Path(options.output)
                self.assertTrue((output / 'FAILED.json').exists())
                output.chmod(0o755)

    def test_no_output_reuse_or_input_nesting(self):
        with tempfile.TemporaryDirectory() as temporary:
            options, unused, unused_training = fixture(Path(temporary))
            options.output = str(Path(options.original_run) / 'reload')
            with self.assertRaisesRegex(ValueError, 'separate_output'):
                source.run(options, libraries=(), clock=lambda: 100)
            options.output = str(Path(temporary) / 'existing')
            Path(options.output).mkdir()
            with self.assertRaises(FileExistsError):
                source.run(options, libraries=(), clock=lambda: 100)

    def test_runtime_and_already_initialized_process_are_rejected(self):
        for fault in ('runtime', 'process'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                options, unused, unused_training = fixture(Path(temporary))
                libraries = [SimpleNamespace(__version__=source.pilot.tokens.RUNTIME_VERSIONS[name])
                             for name in ('torch', 'peft', 'transformers')]
                libraries[0].cuda = SimpleNamespace(is_initialized=Mock(return_value=True))
                if fault == 'runtime':
                    libraries[0].__version__ = 'wrong-runtime'
                with patch.dict(os.environ, CUDA_VISIBLE_DEVICES='GPU-test'), \
                        self.assertRaisesRegex(ValueError, 'runtime_changed|fresh_exclusive'):
                    source.run(options, libraries=libraries, clock=lambda: 100)
                output = Path(options.output)
                self.assertTrue((output / 'FAILED.json').is_file())
                output.chmod(0o755)


class ComparisonTests(unittest.TestCase):
    def test_identical_and_changed_captures_and_metrics(self):
        call = SimpleNamespace(state_id=source.pilot.FITTED_ID, slot='slot', physical_call=0,
                               actor_call_index=0, request={'seed': 1}, generation={'raw': 'STOP'})
        original = SimpleNamespace(calls=(call,))
        observed = deepcopy(original)
        kwargs = dict(original_metrics={'metric': 2}, reloaded_metrics={'metric': 2})
        self.assertTrue(source.compare_readouts(original, observed, **kwargs)['exact_captures_equal'])
        observed.calls[0].request['seed'] = 2
        mismatch = source.compare_readouts(original, observed, **kwargs)
        self.assertEqual(mismatch['mismatched_call_indexes'], [0])
        self.assertTrue(mismatch['exact_metrics_accounting_equal'])
        mismatch = source.compare_readouts(original, SimpleNamespace(calls=()),
            original_metrics={'metric': 2}, reloaded_metrics={'metric': 1})
        self.assertFalse(mismatch['exact_metrics_accounting_equal'])
        self.assertEqual(mismatch['mismatched_call_indexes'], [0])


class ConfigOrderTests(unittest.TestCase):
    def test_only_target_module_permutation_is_accepted(self):
        original = dict(r=8, lora_alpha=16, target_modules=[
            'up_proj', 'q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'down_proj'])
        expected = dict(original, target_modules=[
            'v_proj', 'k_proj', 'q_proj', 'up_proj', 'gate_proj', 'o_proj', 'down_proj'])
        faults = [dict(original, target_modules=original['target_modules'][:-1]),
                  dict(original, target_modules=original['target_modules'] + ['up_proj']),
                  dict(original, target_modules=original['target_modules'] + ['extra_proj']),
                  dict(original, target_modules='q_proj'),
                  dict(original, target_modules=original['target_modules'][:-1] + [7]),
                  {key: value for key, value in original.items() if key != 'target_modules'},
                  dict(original, r=16), dict(original, lora_alpha=32), dict(original, extra=True)]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initial, saved = root / 'initial', root / 'saved'
            initial.mkdir()
            saved.mkdir()
            initialized = SimpleNamespace(directory=initial)
            for changed_side in ('saved', 'expected'):
                for candidate in [original] + faults:
                    with self.subTest(side=changed_side, config=candidate):
                        write(initial / 'adapter_config.json', expected if changed_side == 'saved' else candidate)
                        write(saved / 'adapter_config.json', candidate if changed_side == 'saved' else expected)
                        before = [(directory / 'adapter_config.json').read_bytes() for directory in (initial, saved)]
                        loader = Mock(side_effect=RuntimeError('validated_before_tensor_load'))
                        valid = candidate == original
                        with self.assertRaisesRegex(RuntimeError if valid else ValueError,
                                'validated_before_tensor_load' if valid else 'config_mismatch'):
                            source.restore_saved_adapter(initialized, saved, torch=None, peft=None,
                                                          expected_sha256='c' * 64, load_file=loader)
                        self.assertEqual(loader.call_count, int(valid))
                        self.assertEqual(before, [(directory / 'adapter_config.json').read_bytes()
                                                   for directory in (initial, saved)])


@unittest.skipUnless(importlib.util.find_spec('torch'), 'CPU torch unavailable')
class RestoreTests(unittest.TestCase):
    def test_cpu_weights_restored_exactly_without_fit_or_dtype_cast(self):
        import torch
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            initial, saved = root / 'initial', root / 'saved'
            initial.mkdir()
            saved.mkdir()
            for directory in (initial, saved):
                write(directory / 'adapter_config.json', {'r': 8, 'target_modules': list(source.pilot.training.TARGET_MODULES)})
            model = torch.nn.Linear(2, 1, bias=False)
            model.register_buffer('rotary', torch.tensor([0.5], dtype=torch.float32), persistent=False)
            roster = (source.pilot.training.ParameterSpec('weight', (1, 2), 'torch.float32'),)
            initialized = SimpleNamespace(model=model, directory=initial,
                                           observation=SimpleNamespace(trainable_roster=roster))
            state = {'weight': torch.tensor([[2., 3.]])}
            target = torch.nn.Linear(2, 1, bias=False)
            target.load_state_dict(state)
            digest = source.pilot.training.adapter_sha256(target, roster)
            peft = SimpleNamespace(get_peft_model_state_dict=Mock(side_effect=lambda *args, **kwargs:
                                    dict(model.named_parameters())),
                set_peft_model_state_dict=Mock(side_effect=lambda instance, weights, **kwargs:
                                               instance.load_state_dict(weights, strict=False)))
            loader = Mock(return_value=state)
            with patch.object(source.pilot.models, 'verify_retained_base') as verify, \
                    patch.object(source.pilot, 'train_updates', side_effect=AssertionError('no fit')):
                observed = source.restore_saved_adapter(initialized, saved, torch=torch, peft=peft,
                                                        expected_sha256=digest, load_file=loader)
            self.assertEqual(observed, digest)
            self.assertTrue(torch.equal(model.weight, state['weight']))
            self.assertEqual(model.rotary.dtype, torch.float32)
            verify.assert_called_once()
            loader.assert_called_once_with(str(saved / 'adapter_model.safetensors'), device='cpu')
            for bad in ({'other': state['weight']}, {'weight': torch.ones(2, 2)},
                        {'weight': state['weight'].to(torch.bfloat16)},
                        {'weight': torch.tensor([[float('nan'), 0.]])}):
                with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, 'saved_adapter_tensor'):
                    source.restore_saved_adapter(initialized, saved, torch=torch, peft=peft,
                                                  expected_sha256=digest, load_file=Mock(return_value=bad))
            write(saved / 'adapter_config.json', {'r': 16, 'target_modules': list(source.pilot.training.TARGET_MODULES)})
            with self.assertRaisesRegex(ValueError, 'config_mismatch'):
                source.restore_saved_adapter(initialized, saved, torch=torch, peft=peft,
                                              expected_sha256=digest, load_file=loader)


class OrchestrationTests(unittest.TestCase):
    def test_only_fitted_is_evaluated_root_hook_and_device_only_movement(self):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            options, result, unused = fixture(Path(temporary))
            model = Mock()
            initialized = SimpleNamespace(model=model, observation=SimpleNamespace(trainable_roster=(), layer_count=1))
            torch = SimpleNamespace(__version__=source.pilot.tokens.RUNTIME_VERSIONS['torch'],
                bfloat16='bf16', set_num_threads=Mock(), set_num_interop_threads=Mock(),
                cuda=SimpleNamespace(is_initialized=Mock(return_value=False), init=Mock(),
                    device_count=Mock(return_value=1), get_device_properties=Mock(return_value=
                        SimpleNamespace(name='A100', total_memory=80 * 1024 ** 3))))
            peft = SimpleNamespace(__version__=source.pilot.tokens.RUNTIME_VERSIONS['peft'])
            transformers = SimpleNamespace(__version__=source.pilot.tokens.RUNTIME_VERSIONS['transformers'],
                AutoTokenizer=SimpleNamespace(from_pretrained=Mock()),
                AutoModelForCausalLM=SimpleNamespace(from_pretrained=Mock()))
            stack.enter_context(patch.dict(os.environ, CUDA_VISIBLE_DEVICES='GPU-test'))
            stack.enter_context(patch.object(source.pilot.prepare, 'allocate_source'))
            stack.enter_context(patch.object(source.pilot.prepare, 'prepare_reduced_held',
                                              return_value=SimpleNamespace(receipt_sha256='held')))
            observed = SimpleNamespace(calls=())
            stack.enter_context(patch.object(source.replay, 'replay_state', return_value=observed))
            stack.enter_context(patch.object(source, '_reduce', return_value=result['screens']['FITTED']))
            stack.enter_context(patch.object(source.pilot.tokens, 'restore_official_backend', return_value=result['tokenizer']))
            stack.enter_context(patch.object(source.pilot, 'initialize_student', return_value=initialized))
            restore = stack.enter_context(patch.object(source, 'restore_saved_adapter', return_value='c' * 64))
            stack.enter_context(patch.object(source.pilot.training, '_validate_model'))
            stack.enter_context(patch.object(source.pilot.training, 'adapter_sha256', return_value='c' * 64))
            stack.enter_context(patch.object(source.pilot.models, 'verify_retained_base', return_value='a' * 64))
            evaluation = stack.enter_context(patch.object(source.pilot, '_evaluate', return_value=observed))
            train = stack.enter_context(patch.object(source.pilot, 'train_updates', side_effect=AssertionError('no fit')))
            summary = source.run(options, libraries=(torch, peft, transformers), clock=lambda: 100)
            self.assertEqual(summary['status'], 'SAVED_ADAPTER_READOUT_EXACT_MATCH')
            self.assertEqual(summary['new_updates'], 0)
            train.assert_not_called()
            restore.assert_called_once()
            evaluation.assert_called_once()
            self.assertEqual(evaluation.call_args.kwargs['state_id'], source.pilot.FITTED_ID)
            self.assertEqual(evaluation.call_args.kwargs['directory'].name, 'FITTED')
            model.to.assert_called_once_with('cuda:0')
            model.disable_adapter.assert_not_called()
            model.register_forward_pre_hook.assert_called_once()
            model.register_forward_pre_hook.return_value.remove.assert_called_once()
            Path(options.output).chmod(0o755)


if __name__ == '__main__':
    unittest.main()
