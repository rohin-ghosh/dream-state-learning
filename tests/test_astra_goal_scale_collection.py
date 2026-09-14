"""CPU-only portable shard admission, native bridge and guard tests."""

from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import astra_goal_scale_collection as runner
from tests.test_astra_portable_actor_bundle import fixture as bundle_fixture
from tests.test_astra_goal_pair_collection import CollectionEngine, rehash
from tests.test_astra_event_two_hop_memory import write
from tests.test_experienced_event_two_hop import generation
from tests.test_experienced_event_two_hop_lesson import Tokenizer


def fixture(root, stack):
    options, inputs = bundle_fixture(root)
    adapter = Path(inputs['parent']['trained_adapter_dir'])
    write(adapter / 'adapter_config.json', dict(r=8, fixture_state=runner.PARENT_STATE))
    inputs['parent']['trained_adapter_files']['adapter_config.json'] = runner.source.file_hash(adapter / 'adapter_config.json')
    with patch.object(runner.portable.collector, 'load_inputs', return_value=inputs):
        receipt = runner.portable.export_bundle(options)
    Path(options.output).rename(root / 'bundle')
    Path(options.lesson_root).rename(root / 'unavailable-ancestors')
    Path(options.prior_collection_root).rename(root / 'unavailable-prior')
    forbidden = stack.enter_context(patch.object(runner.portable.collector, 'load_inputs', side_effect=AssertionError('ancestor loader forbidden')))
    stack.enter_context(patch.object(runner.portable.collector.memory, 'load_inputs', side_effect=AssertionError('memory ancestor loader forbidden')))
    protocol = root / 'protocol.md'
    protocol.write_text('synthetic prospective no-fit scale protocol\n')
    stack.enter_context(patch.object(runner, 'PROTOCOL_PATH', str(protocol)))
    stack.enter_context(patch.object(runner, 'PROTOCOL_SHA', runner.source.file_hash(protocol)))
    stack.enter_context(patch.dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='fake-gpu'))
    stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash', side_effect=lambda parameters: next(iter(parameters.values())).state))
    tokenizer = Tokenizer()
    tokenizer.pad_token_id = 151643
    token_loader = stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer', return_value=tokenizer))
    engines = []

    def factory(arguments, tokenizer, *, check):
        engine = CollectionEngine(arguments, tokenizer, check, {})
        engines.append(engine)
        return engine

    engine_factory = stack.enter_context(patch.object(runner.source, 'Engine', side_effect=factory))
    return SimpleNamespace(bundle_sha=receipt['manifest_sha256'], engines=engines, factory=engine_factory,
                           token_loader=token_loader, forbidden=forbidden)


def cli(root, state, phase, shard=0):
    values = ['--phase', phase, '--shard', str(shard), '--bundle', str(root / 'bundle'),
              '--bundle-sha', state.bundle_sha, '--model-dir', str(root / 'model'), '--gpu-uuid', 'fake-gpu',
              '--output', str(root / f'shard-{shard}' / phase)]
    if phase in ('teach', 'baseline'):
        values += ['--exposure', str(root / f'shard-{shard}/expose')]
    if phase == 'baseline':
        values += ['--teaching', str(root / f'shard-{shard}/teach')]
    return values


def replay_inputs(result):
    binding = result['binding']
    return dict(binding=binding, shard=result['shard'], old_ids=binding['old_ids'], worlds=binding['worlds'],
                registry=runner.scale.validate_registry(old_ids=binding['old_ids']))


class ScaleCollectionTests(unittest.TestCase):
    def test_production_protocol_is_bound_to_exact_local_bytes(self):
        path = Path(runner.__file__).resolve().parents[1] / runner.PROTOCOL_PATH
        self.assertEqual(runner.PROTOCOL_SHA, 'dd1d078a01d9f547219afd23790c467ca0ccb413f3148a2af9b963b63e652f24')
        self.assertEqual(runner.source.file_hash(path), runner.PROTOCOL_SHA)

    def test_eight_prepare_shards_no_ancestors_model_or_scores(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            ids = set(['E_A', 'N_B'])
            for worlds in runner.breadth.build_worlds().values():
                for world in worlds:
                    ids.update(runner.breadth.identifiers(world))
            seen = set(ids)
            registry_hashes = set()
            for shard in range(8):
                result = runner.main(cli(root, state, 'prepare', shard))
                self.assertEqual(result['status'], 'PREPARED_NO_MODEL')
                self.assertEqual((result['fits'], result['updates'], result['model_calls']), (0, 0, 0))
                self.assertEqual(set(result['binding']['old_ids']), ids)
                self.assertEqual(result['binding']['bundle_sha256'], state.bundle_sha)
                self.assertTrue(result['base_file_verification']['verified'])
                registry_hashes.add(result['binding']['registry_sha256'])
                for world in result['binding']['worlds']['TRAIN'] + result['binding']['worlds']['PROBE']:
                    current = runner.scale.identifiers(world)
                    self.assertTrue(current.isdisjoint(seen))
                    seen.update(current)
                self.assertNotIn('DO_NOT_EXPORT', runner.source.json.dumps(result))
            self.assertEqual(len(registry_hashes), 1)
            state.factory.assert_not_called()
            state.token_loader.assert_not_called()
            state.forbidden.assert_not_called()

    def test_real_shard_pipeline_80_192_288_same_parent_replay_and_masks(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            results = [runner.main(cli(root, state, phase, 7)) for phase in ('expose', 'teach', 'baseline')]
            self.assertEqual([result['model_calls'] for result in results], [80, 192, 288])
            self.assertEqual(len(state.engines), 3)
            for engine, result in zip(state.engines, results):
                self.assertEqual(Path(engine.arguments.adapter_dir), root / 'bundle/adapter')
                self.assertEqual((engine.steps, engine.optimizers), (0, []))
                self.assertEqual(result['loaded_adapter_state_sha256'], runner.PARENT_STATE)
                self.assertEqual(result['adapter_state_after'], runner.PARENT_STATE)
                self.assertTrue(result['frozen_base_unchanged'])
            inputs = replay_inputs(results[0])
            exposure, exposure_sha = runner.read_stage(root / 'shard-7/expose', 'expose', inputs)
            teaching, teaching_sha = runner.read_stage(root / 'shard-7/teach', 'teach', inputs, exposure,
                dict(exposure_result_sha256=exposure_sha))
            baseline, unused = runner.read_stage(root / 'shard-7/baseline', 'baseline', inputs, exposure,
                dict(exposure_result_sha256=exposure_sha, teaching_result_sha256=teaching_sha))
            self.assertEqual(teaching['row_count'], 192)
            self.assertEqual([len(block['rows']) for block in teaching['lessons']['blocks']], [48] * 4)
            self.assertEqual(Counter(panel['split'] for panel in baseline['panels']), dict(TRAIN=8, PROBE=4))
            self.assertEqual(len(exposure['collections']), 10)
            probe_ids = set().union(*(runner.scale.identifiers(world) for worlds in inputs['registry'].values() for world in worlds['PROBE']))
            rows = teaching['lessons']['rows']
            for index, (row, capture) in enumerate(zip(rows, teaching['lessons']['captures'])):
                native = runner.source.read(root / f'shard-7/teach/CALL_{index:03d}.json')
                self.assertEqual(native['shard'], 7)
                self.assertEqual({key: native[key] for key in ('messages', 'response', 'error')},
                                 {key: capture[key] for key in ('messages', 'response', 'error')})
                self.assertEqual(row['assistant'], native['response']['raw'])
                self.assertTrue(row['assistant'].endswith('\n\n'))
                self.assertFalse(any(identifier in str(native['messages']) for identifier in probe_ids))
            tokenizer = Tokenizer()
            for encoded in runner.scale.runtime(7)['encode_rows'](rows, tokenizer):
                self.assertEqual(tuple(label for label in encoded.labels if label != -100), encoded.target_ids)
                self.assertNotIn('PARENT PROCEDURAL GUIDANCE', tokenizer.decode(encoded.input_ids))
            state.forbidden.assert_not_called()

    def test_partial_source_and_partial_teaching_are_explicit_no_success_subset(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            with patch.object(CollectionEngine, 'generate', side_effect=lambda messages, **kwargs: generation('bad action', messages)):
                partial = runner.main(cli(root, state, 'expose', 1))
            self.assertEqual((partial['data_status'], partial['case_failures'], partial['model_calls']), ('PARTIAL_SOURCE_FAILURES', 40, 40))
            self.assertFalse(partial['source_ready'])
            with self.assertRaisesRegex(ValueError, 'complete_ten_world_exposure'):
                runner.main(cli(root, state, 'teach', 1))
            runner.main(cli(root, state, 'expose', 2))
            normal = CollectionEngine.generate
            count = 0

            def child(engine, messages, **options):
                nonlocal count
                count += 1
                return generation('bad command', messages) if count == 1 else normal(engine, messages, **options)

            with patch.object(CollectionEngine, 'generate', child):
                taught = runner.main(cli(root, state, 'teach', 2))
            self.assertEqual((taught['model_calls'], taught['row_count'], taught['case_failures']), (187, 0, 1))
            self.assertEqual(taught['data_status'], 'PARTIAL_TEACHING_FAILURES')
            with patch.object(CollectionEngine, 'generate', side_effect=lambda messages, **kwargs: generation('invalid route', messages)):
                baseline = runner.main(cli(root, state, 'baseline', 2))
            self.assertEqual((baseline['status'], baseline['model_calls'], baseline['case_failures']), ('COMPLETE', 48, 48))
            self.assertEqual(baseline['data_status'], 'READOUT_RECORDED')

    def test_shard_call_rows_and_dependency_drift_rejected_even_after_rehash(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            exposed = runner.main(cli(root, state, 'expose'))
            taught = runner.main(cli(root, state, 'teach'))
            inputs = replay_inputs(exposed)
            exposure, unused = runner.read_stage(root / 'shard-0/expose', 'expose', inputs)
            for name, change in (
                ('CALL_000.json', lambda document: document.update(shard=1)),
                ('CALL_000.json', lambda document: document['response'].update(raw='replaced')),
                ('LESSONS.json', lambda document: document['rows'][0].update(assistant='teacher target')),
            ):
                path = root / 'shard-0/teach' / name
                original = runner.source.read(path)
                forged = deepcopy(original)
                change(forged)
                write(path, forged)
                rehash(root / 'shard-0/teach')
                with self.assertRaises(ValueError):
                    runner.read_stage(root / 'shard-0/teach', 'teach', inputs, exposure, taught['dependencies'])
                write(path, original)
                write(root / 'shard-0/teach/RESULT.json', taught)
            with self.assertRaisesRegex(ValueError, 'stage_join_drift'):
                runner.read_stage(root / 'shard-0/teach', 'teach', inputs, exposure, {'exposure_result_sha256': 'wrong'})
            with self.assertRaisesRegex(ValueError, 'fresh_immutable'):
                runner.main(cli(root, state, 'expose'))

    def test_bad_bundle_base_and_protocol_stop_before_model(self):
        for failure in ('manifest', 'base', 'protocol'):
            with self.subTest(failure=failure), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = fixture(root, stack)
                if failure == 'manifest':
                    state.bundle_sha = '0' * 64
                elif failure == 'base':
                    (root / 'model/model.safetensors').write_bytes(b'drift')
                else:
                    (root / 'protocol.md').write_text('changed')
                with self.assertRaises(ValueError):
                    runner.main(cli(root, state, 'prepare'))
                state.factory.assert_not_called()
                state.token_loader.assert_not_called()

    def test_native_error_readonly_state_and_call_cap_fail_closed(self):
        for failure in ('native', 'state', 'cap'):
            with self.subTest(failure=failure), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = fixture(root, stack)
                factory = state.factory.side_effect

                def failing(*args, **kwargs):
                    engine = factory(*args, **kwargs)
                    engine.raise_native = failure == 'native'
                    engine.mutate_state = failure == 'state'
                    return engine

                state.factory.side_effect = failing
                if failure == 'cap':
                    stack.enter_context(patch.dict(runner.CAPS, expose=1))
                with self.assertRaises(ValueError):
                    runner.main(cli(root, state, 'expose'))
                failed = runner.source.read(root / 'shard-0/expose/FAILED.json')
                self.assertFalse((root / 'shard-0/expose/RESULT.json').exists())
                if failure == 'native':
                    self.assertEqual(failed['model_calls'], 40)
                    self.assertEqual(runner.source.read(root / 'shard-0/expose/CALL_000.json')['error']['type'], 'RuntimeError')
                if failure == 'cap':
                    self.assertEqual(state.engines[0].native_calls, 1)


class GuardTests(unittest.TestCase):
    def test_no_ml_import_guard_external_scanner_lease_and_bounds(self):
        script = '''
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_goal_scale_collection
'''
        completed = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        guard = Path(runner.__file__).with_name('astra_goal_scale_collection_guard.sh')
        completed = subprocess.run(['bash', '-n', str(guard)], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        text = guard.read_text()
        for fragment in ('test "$#" -eq 12', '"$root/source_commit.txt"', 'int(sys.argv[1])-21600',
                         'seconds=3600', '--kill-after=60', '-gt 300',
                         'python3 "$scanner" "$index" "$uuid" < "$service_exceptions"'):
            self.assertIn(fragment, text)
        self.assertNotIn('1789980180', text)
        self.assertNotIn('/tmp/astra_stage2a', text)
        self.assertNotIn('--phase train ', text)

    def test_supplied_scanner_abort_no_model_or_remote(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / 'source'
            entry = source_dir / 'gpu/astra_goal_scale_collection.py'
            entry.parent.mkdir(parents=True)
            entry.write_bytes(Path(runner.__file__).read_bytes())
            bundle, model = root / 'bundle', root / 'model'
            write(root / 'prepare/RESULT.json', dict(schema=runner.SCHEMA, phase='prepare', status='PREPARED_NO_MODEL',
                expected_train_targets=192, shard=3, binding=dict(bundle_sha256='b' * 64),
                entry_sha256=runner.source.file_hash(entry), arguments=dict(bundle=str(bundle), model_dir=str(model), gpu_uuid='fake-gpu')))
            (root / 'source_commit.txt').write_text('commit\n')
            scanner = root / 'scanner.py'
            scanner.write_text('raise SystemExit(1)\n')
            exceptions = root / 'exceptions.json'
            exceptions.write_text('{}\n')
            binaries = root / 'bin'
            binaries.mkdir()
            (binaries / 'sleep').write_text('#!/bin/bash\nexit 0\n')
            (binaries / 'sleep').chmod(0o700)
            guard = Path(runner.__file__).with_name('astra_goal_scale_collection_guard.sh')
            completed = subprocess.run(['bash', str(guard), str(root), str(source_dir), 'commit', '3', 'fake-gpu', '3',
                str(bundle), 'b' * 64, str(model), str(scanner), str(exceptions), str(int(time.time()) + 86400)],
                env=dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ['PATH']), capture_output=True, text=True, timeout=10)
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertTrue((root / 'launch/GUARD_ABORT.txt').exists())
            self.assertFalse((root / 'expose').exists())


if __name__ == '__main__':
    unittest.main()
