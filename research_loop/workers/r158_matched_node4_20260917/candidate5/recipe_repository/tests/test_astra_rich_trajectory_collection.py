"""CPU-only portable rich capture, projection, phase joins and guard tests."""

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

from gpu import astra_rich_trajectory_collection as runner
from tests.test_astra_portable_actor_bundle import fixture as bundle_fixture
from tests.test_astra_goal_pair_collection import CollectionEngine, rehash
from tests.test_astra_event_two_hop_memory import write
from tests.test_experienced_event_two_hop import generation
from tests.test_experienced_event_two_hop_lesson import Tokenizer
from tests.test_experienced_event_rich_trajectory import rich_child, critic_child


class RichEngine(CollectionEngine):
    def generate(self, messages, *, max_new_tokens):
        if max_new_tokens == 160:
            response = super().generate(messages, max_new_tokens=max_new_tokens)
        else:
            assert max_new_tokens == 512
            self.native_calls += 1
            if self.raise_native:
                raise RuntimeError('retained native failure')
            if self.mutate_state:
                self.parameter.state = 'd' * 64
            response = (generation('invalid rich envelope\n\n', messages) if self.invalid else
                        critic_child(messages) if messages[0]['content'] == runner.rich.CRITIQUE_SYSTEM else rich_child(messages))
        response['token_ids'] = self.tokenizer.encode(response['raw']) + [self.tokenizer.eos_token_id]
        response['prompt_tokens'] = len(self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True))
        return response


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
    stack.enter_context(patch.object(runner.portable.collector.memory, 'load_inputs', side_effect=AssertionError('ancestor loader forbidden')))
    stack.enter_context(patch.dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', CUDA_VISIBLE_DEVICES='fake-gpu'))
    stack.enter_context(patch('organism_v6.pcfl_vertical_train._state_hash', side_effect=lambda parameters: next(iter(parameters.values())).state))
    tokenizer = Tokenizer()
    tokenizer.pad_token_id = 151643
    token_loader = stack.enter_context(patch.object(runner.source.native, 'load_local_tokenizer', return_value=tokenizer))
    engines = []

    def factory(arguments, tokenizer, *, check):
        engine = RichEngine(arguments, tokenizer, check, {})
        engines.append(engine)
        return engine

    engine_factory = stack.enter_context(patch.object(runner.source, 'Engine', side_effect=factory))
    return SimpleNamespace(bundle_sha=receipt['manifest_sha256'], engines=engines, factory=engine_factory,
                           token_loader=token_loader, forbidden=forbidden)


def cli(root, state, phase, shard=0):
    directory = root / f'shard-{shard}'
    values = ['--phase', phase, '--shard', str(shard), '--bundle', str(root / 'bundle'),
        '--bundle-sha', state.bundle_sha, '--model-dir', str(root / 'model'), '--gpu-uuid', 'fake-gpu',
        '--output', str(directory / phase)]
    if phase in ('teach', 'critique', 'baseline'):
        values += ['--exposure', str(directory / 'expose')]
    if phase in ('critique', 'baseline'):
        values += ['--teaching', str(directory / 'teach')]
    if phase == 'baseline':
        values += ['--critique', str(directory / 'critique')]
    return values


def replay_inputs(result):
    binding = result['binding']
    return dict(binding=binding, shard=result['shard'], old_ids=binding['old_ids'], worlds=binding['worlds'],
                registry=runner.rich.validate_registry(old_ids=binding['old_ids']))


class RichCollectionTests(unittest.TestCase):
    def test_production_protocol_exact_bytes_and_caps(self):
        self.assertEqual(runner.PROTOCOL_SHA, '339c25c05cdb1bd6ba07bfd22520c68df6f23117fed0627cb245e23c6ba2bd2f')
        self.assertEqual(runner.source.file_hash(Path(runner.__file__).resolve().parents[1] / runner.PROTOCOL_PATH), runner.PROTOCOL_SHA)
        self.assertEqual(runner.CAPS, dict(prepare=0, expose=40, teach=96, critique=16, baseline=144))
        self.assertEqual(sum(runner.CAPS.values()), 296)

    def test_prepare_all_shards_no_model_no_ancestors_prior_namespaces_excluded(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            seen = set()
            for shard in range(4):
                result = runner.main(cli(root, state, 'prepare', shard))
                self.assertEqual(result['status'], 'PREPARED_NO_MODEL')
                self.assertEqual((result['fits'], result['updates'], result['model_calls']), (0, 0, 0))
                old_ids = set(result['binding']['old_ids'])
                for registry in (runner.breadth.build_worlds(),):
                    for worlds in registry.values():
                        for world in worlds:
                            self.assertTrue(runner.rich.identifiers(world) <= old_ids)
                for worlds in runner.scale.validate_registry().values():
                    for world in worlds['TRAIN'] + worlds['PROBE']:
                        self.assertTrue(runner.rich.identifiers(world) <= old_ids)
                for world in result['binding']['worlds']['TRAIN'] + result['binding']['worlds']['PROBE']:
                    identifiers = runner.rich.identifiers(world)
                    self.assertTrue(identifiers.isdisjoint(seen | old_ids))
                    seen.update(identifiers)
            state.factory.assert_not_called()
            state.token_loader.assert_not_called()
            state.forbidden.assert_not_called()

    def test_four_fresh_phases_actual_rich_projection_masks_and_replay(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            results = [runner.main(cli(root, state, phase)) for phase in ('expose', 'teach', 'critique', 'baseline')]
            self.assertEqual([result['model_calls'] for result in results], [40, 96, 16, 144])
            for engine, result in zip(state.engines, results):
                self.assertEqual((engine.steps, engine.optimizers), (0, []))
                self.assertGreater(engine.base_checks, 0)
                self.assertEqual(result['adapter_state_after'], runner.PARENT_STATE)
                self.assertEqual(result['loaded_adapter_state_sha256'], runner.PARENT_STATE)
                self.assertFalse(result['trainingAllowed'])
            inputs = replay_inputs(results[0])
            directory = root / 'shard-0'
            exposure, exposed_sha = runner.read_stage(directory / 'expose', 'expose', inputs)
            teaching, taught_sha = runner.read_stage(directory / 'teach', 'teach', inputs, exposure,
                dependencies=dict(exposure_result_sha256=exposed_sha))
            critique, critique_sha = runner.read_stage(directory / 'critique', 'critique', inputs, exposure, teaching,
                dependencies=dict(exposure_result_sha256=exposed_sha, teaching_result_sha256=taught_sha))
            baseline, unused_sha = runner.read_stage(directory / 'baseline', 'baseline', inputs, exposure, teaching,
                dependencies=dict(exposure_result_sha256=exposed_sha, teaching_result_sha256=taught_sha, critique_result_sha256=critique_sha))
            self.assertEqual(len(baseline['panels']), 6)
            self.assertTrue(critique['candidate_only'])
            self.assertFalse(critique['reviewed'])
            rows = runner.rich.replay_teaching(teaching['lessons'])
            for index, capture in enumerate(teaching['lessons']['captures']):
                native = runner.source.read(directory / f'teach/CALL_{index:03d}.json')
                self.assertEqual({key: native[key] for key in ('messages', 'response', 'error')},
                                 {key: capture[key] for key in ('messages', 'response', 'error')})
                raw = native['response']['raw']
                self.assertEqual(rows['RICH'][index]['assistant'], raw)
                self.assertEqual(rows['TERSE'][index]['assistant'], raw[slice(*capture['projection']['action_span'])])
                self.assertNotIn(runner.rich.PARENT_GUIDANCE, str(rows['RICH'][index]['prefix']))
                self.assertNotIn('RATIONALE\n', str([message['content'] for message in rows['RICH'][index]['prefix'] if message['role'] == 'assistant']))
            tokenizer = Tokenizer()
            paired = runner.rich.encode_paired_rows(rows, tokenizer)
            for index in range(96):
                full, masked = [paired['encoded'][form][index] for form in ('RICH', 'RICH_ACTION_ONLY')]
                self.assertEqual(full.input_ids, masked.input_ids)
                self.assertEqual(masked.target_ids, tuple(tokenizer.encode(rows['TERSE'][index]['assistant']) + [tokenizer.eos_token_id]))
                self.assertEqual(masked.labels[-1], -100)
                self.assertLessEqual(len(full.input_ids), 2048)
            self.assertTrue(results[1]['encoded_pairs_ready'])
            self.assertTrue(results[1]['complete_corpus'])
            self.assertFalse(results[1]['fit_ready'])
            metrics = runner.source.read(directory / 'teach/NATIVE_METRICS.json')
            self.assertEqual(metrics['missing_token_counts'], 0)
            self.assertGreater(metrics['totals']['generated_tokens'], 96)
            projections = runner.source.read(directory / 'teach/ACTION_PROJECTIONS.json')
            projections[0]['projection']['action'] = 'ROUTE invented'
            write(directory / 'teach/ACTION_PROJECTIONS.json', projections)
            rehash(directory / 'teach')
            with self.assertRaisesRegex(ValueError, 'artifact_drift'):
                runner.read_stage(directory / 'teach', 'teach', inputs, exposure,
                    dependencies=dict(exposure_result_sha256=exposed_sha))

    def test_partial_teaching_still_attempts_sixteen_critiques_and_baseline(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            runner.main(cli(root, state, 'expose'))
            with patch(__name__ + '.rich_child', side_effect=lambda messages: generation('not an envelope\n\n', messages)):
                taught = runner.main(cli(root, state, 'teach'))
            self.assertFalse(taught['curriculum_ready'])
            self.assertFalse(taught['encoded_pairs_ready'])
            self.assertEqual((taught['row_count'], taught['case_failures']), (0, 16))
            with patch(__name__ + '.critic_child', side_effect=lambda messages: generation('', messages)):
                critiqued = runner.main(cli(root, state, 'critique'))
            self.assertEqual((critiqued['model_calls'], critiqued['case_failures']), (16, 16))
            self.assertEqual(critiqued['fit_targets'], 0)
            baseline = runner.main(cli(root, state, 'baseline'))
            self.assertEqual(baseline['status'], 'COMPLETE')
            self.assertEqual(baseline['model_calls'], 144)
            self.assertEqual(runner.source.read(root / 'shard-0/teach/CALL_000.json')['response']['raw'], 'not an envelope\n\n')

    def test_partial_source_prevents_unsourced_teaching(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            with patch.object(RichEngine, 'generate', side_effect=lambda messages, **kwargs: generation('bad action', messages)):
                exposed = runner.main(cli(root, state, 'expose'))
            self.assertFalse(exposed['source_ready'])
            self.assertEqual((exposed['model_calls'], exposed['case_failures']), (20, 20))
            with self.assertRaisesRegex(ValueError, 'complete_five_world_exposure_required'):
                runner.main(cli(root, state, 'teach'))
            self.assertEqual(len(state.engines), 1)

    def test_one_failed_episode_keeps_ninety_matched_candidates(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            runner.main(cli(root, state, 'expose'))
            calls = []
            original_child = rich_child

            def one_failure(messages):
                calls.append(deepcopy(messages))
                return generation('invalid first episode\n\n', messages) if len(calls) == 1 else original_child(messages)

            with patch(__name__ + '.rich_child', side_effect=one_failure):
                taught = runner.main(cli(root, state, 'teach'))
            self.assertEqual(taught['candidate_count'], 90)
            self.assertEqual(taught['row_counts'], {form: 90 for form in runner.rich.FORMS})
            self.assertFalse(taught['complete_corpus'])
            self.assertFalse(taught['fit_ready'])
            self.assertTrue(taught['encoded_pairs_ready'])
            self.assertEqual(taught['case_failures'], 1)
            lessons = runner.source.read(root / 'shard-0/teach/LESSONS.json')
            rows = runner.rich.replay_teaching(lessons)
            self.assertTrue(all((row['world_index'], row['task_index']) != (0, 0)
                                for form in runner.rich.FORMS for row in rows[form]))
            self.assertEqual(lessons['captures'][0]['response']['raw'], 'invalid first episode\n\n')
            critiqued = runner.main(cli(root, state, 'critique'))
            self.assertEqual(critiqued['model_calls'], 16)

    def test_forged_native_cross_shard_and_state_rejected(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack)
            result = runner.main(cli(root, state, 'expose'))
            inputs = replay_inputs(result)
            directory = root / 'shard-0/expose'
            original = runner.source.read(directory / 'CALL_000.json')
            for field in ('messages', 'response', 'shard'):
                forged = deepcopy(original)
                if field == 'messages':
                    forged[field][-1]['content'] += ' drift'
                elif field == 'response':
                    forged[field]['raw'] += ' drift'
                else:
                    forged[field] = 1
                write(directory / 'CALL_000.json', forged)
                rehash(directory)
                with self.assertRaises(ValueError):
                    runner.read_stage(directory, 'expose', inputs)
            write(directory / 'CALL_000.json', original)
            write(directory / 'STATES.json', dict(before=runner.PARENT_STATE, after='d' * 64))
            rehash(directory)
            with self.assertRaisesRegex(ValueError, 'state_drift'):
                runner.read_stage(directory, 'expose', inputs)

    def test_native_errors_and_call_cap_fail_closed(self):
        for failure in ('native', 'cap', 'state'):
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
                self.assertEqual(failed['status'], 'FAILED')
                self.assertFalse((root / 'shard-0/expose/RESULT.json').exists())
                if failure == 'cap':
                    self.assertEqual(state.engines[0].native_calls, 1)


class GuardTests(unittest.TestCase):
    def test_no_ml_import_guard_syntax_lease_caps_and_scanner(self):
        script = '''
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_rich_trajectory_collection
'''
        completed = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        guard = Path(runner.__file__).with_name('astra_rich_trajectory_collection_guard.sh')
        completed = subprocess.run(['bash', '-n', str(guard)], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        text = guard.read_text()
        for fragment in ('test "$#" -eq 12', 'admission_started + 15000', 'int(sys.argv[1])-21600',
                         'seconds=3600', '--kill-after=60', '-gt 300', '--phase critique',
                         'python3 "$scanner" "$index" "$uuid" < "$service_exceptions"'):
            self.assertIn(fragment, text)
        self.assertNotIn('--phase train ', text)
        self.assertNotIn('curriculum_ready', text)

    def test_supplied_scanner_abort_no_launch(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / 'source'
            entry = source_dir / 'gpu/astra_rich_trajectory_collection.py'
            entry.parent.mkdir(parents=True)
            entry.write_bytes(Path(runner.__file__).read_bytes())
            bundle, model = root / 'bundle', root / 'model'
            write(root / 'prepare/RESULT.json', dict(schema=runner.SCHEMA, phase='prepare', status='PREPARED_NO_MODEL',
                expected_paired_targets=96, shard=3, binding=dict(bundle_sha256='b' * 64),
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
            guard = Path(runner.__file__).with_name('astra_rich_trajectory_collection_guard.sh')
            completed = subprocess.run(['bash', str(guard), str(root), str(source_dir), 'commit', '3', 'fake-gpu', '3',
                str(bundle), 'b' * 64, str(model), str(scanner), str(exceptions), str(int(time.time()) + 86400)],
                env=dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ['PATH']), capture_output=True, text=True, timeout=10)
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertTrue((root / 'launch/GUARD_ABORT.txt').exists())
            self.assertFalse((root / 'expose').exists())


if __name__ == '__main__':
    unittest.main()
