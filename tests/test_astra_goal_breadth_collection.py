"""CPU-only breadth native bridge, namespace, source and no-fit stage tests."""

from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from gpu import astra_goal_breadth_collection as runner
from tests.test_astra_goal_pair_collection import CollectionEngine, cli as old_cli, fixture as old_fixture, rehash
from tests.test_astra_event_two_hop_memory import material_fixture, write
from tests.test_experienced_event_two_hop import generation
from tests.test_experienced_event_two_hop_lesson import Tokenizer


def cli(root, phase):
    return old_cli(root, phase) + ['--prior-collection-root', str(root / 'prior')]


def fixture(root, stack, material):
    state = old_fixture(root, stack, material)
    values = old_cli(root, 'expose')
    values[values.index('--output') + 1] = str(root / 'prior/expose')
    runner.prior.main(values)
    state.engines.clear()
    state.factory.reset_mock()
    state.token_loader.reset_mock()
    return state


def replay_inputs(result):
    binding = result['binding']
    return dict(binding=binding, worlds=binding['worlds'], old_ids=binding['old_ids'])


class BreadthCollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.material = material_fixture()

    def test_prepare_no_model_binds_old255_namespace_and_not_its_targets(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)
            result = runner.main(cli(root, 'prepare'))
            state.factory.assert_not_called()
            state.token_loader.assert_not_called()
            self.assertEqual(result['status'], 'PREPARED_NO_MODEL')
            self.assertEqual((result['fits'], result['updates'], result['model_calls']), (0, 0, 0))
            self.assertEqual((result['expected_train_targets'], result['prior_seq255_targets']), (192, 0))
            self.assertFalse((root / 'prior/teach').exists())
            self.assertEqual(result['binding']['memory']['transfer'], state.binding)
            original = runner.source.read(root / 'prior/expose/DATA.json')
            known = set(result['binding']['prior_collection']['old_ids'])
            for collection in original['collections']:
                known.update(runner.goal.identifiers(collection['world']))
            self.assertEqual(known, set(result['binding']['old_ids']))
            self.assertEqual(result['binding']['prior_exposure_result_sha256'],
                             runner.source.file_hash(root / 'prior/expose/RESULT.json'))
            worlds = result['binding']['worlds']
            self.assertEqual((len(worlds['TRAIN']), len(worlds['PROBE'])), (8, 2))
            for world in worlds['TRAIN'] + worlds['PROBE']:
                ids = runner.goal.identifiers(world)
                self.assertTrue(ids.isdisjoint(known))
                known.update(ids)
            self.assertEqual(result['protocol_sha256'], runner.PROTOCOL_SHA)

    def test_complete_pipeline_80_192_288_calls_four_blocks_and_train_baselines(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)
            exposed = runner.main(cli(root, 'expose'))
            taught = runner.main(cli(root, 'teach'))
            baseline = runner.main(cli(root, 'baseline'))
            self.assertEqual([item['model_calls'] for item in (exposed, taught, baseline)], [80, 192, 288])
            self.assertEqual(len(state.engines), 3)
            for engine, result in zip(state.engines, (exposed, taught, baseline)):
                self.assertEqual((engine.steps, engine.optimizers), (0, []))
                self.assertEqual(Path(engine.arguments.adapter_dir), root / 'lesson/train/adapter')
                self.assertEqual(result['loaded_adapter_state_sha256'], runner.PARENT_STATE)
                self.assertEqual(result['adapter_state_after'], runner.PARENT_STATE)
                self.assertGreater(engine.base_checks, 0)
            inputs = replay_inputs(exposed)
            exposure, exposure_sha = runner.read_stage(root / 'expose', 'expose', inputs)
            teaching, teaching_sha = runner.read_stage(root / 'teach', 'teach', inputs, exposure,
                dict(exposure_result_sha256=exposure_sha))
            measured, unused = runner.read_stage(root / 'baseline', 'baseline', inputs, exposure,
                dict(exposure_result_sha256=exposure_sha, teaching_result_sha256=teaching_sha))
            self.assertEqual(sum(len(item['records']) for item in exposure['collections']), 40)
            self.assertTrue(all(item['ready'] for item in exposure['collections']))
            self.assertEqual(teaching['row_count'], 192)
            self.assertTrue(teaching['curriculum_ready'])
            self.assertEqual([len(block['rows']) for block in teaching['lessons']['blocks']], [48] * 4)
            self.assertEqual(Counter((panel['split'], panel['condition']) for panel in measured['panels']),
                             {('TRAIN', 'OWN_TEXT'): 8, ('PROBE', 'OWN_TEXT'): 2, ('PROBE', 'UNAVAILABLE'): 2})
            self.assertEqual(sum(len(panel['episodes']) for panel in measured['panels']), 48)
            calls = [runner.source.read(path) for path in sorted((root / 'baseline').glob('CALL_*.json'))]
            self.assertEqual(Counter(call['graph'] for call in calls), dict(TRAIN=192, PROBE=96))
            self.assertTrue(all(call['role'] == 'actor' and 'PARENT PROCEDURAL GUIDANCE' not in str(call['messages']) for call in calls))

    def test_actual_raw_coached_bridge_192_masks_no_probe_or_prior_targets(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            fixture(root, stack, self.material)
            runner.main(cli(root, 'expose'))
            runner.main(cli(root, 'teach'))
            document = runner.source.read(root / 'teach/LESSONS.json')
            rows = runner.goal.replay_lessons(document)
            self.assertEqual(Counter(row['master'] for row in rows), dict.fromkeys(runner.goal.TRAIN_MASTERS, 24))
            probe_ids = set().union(*(runner.goal.identifiers(world) for world in runner.goal.build_worlds()['PROBE']))
            self.assertFalse(any(identifier in runner.source.json.dumps(rows) for identifier in probe_ids))
            self.assertTrue(set(row['master'] for row in rows).isdisjoint(runner.prior.goal.MASTERS))
            for index, (row, capture) in enumerate(zip(rows, document['captures'])):
                saved = runner.source.read(root / f'teach/CALL_{index:03d}.json')
                self.assertEqual({key: saved[key] for key in ('messages', 'response', 'error')},
                                 {key: capture[key] for key in ('messages', 'response', 'error')})
                self.assertEqual(saved['response']['messages'], saved['messages'])
                self.assertEqual(row['assistant'], saved['response']['raw'])
                self.assertTrue(row['assistant'].endswith('\n\n'))
                self.assertNotIn('PARENT PROCEDURAL GUIDANCE', str(row['prefix']))
                self.assertFalse(any(identifier in str(saved['messages']) for identifier in probe_ids))
            tokenizer = Tokenizer()
            for encoded in runner.goal.encode_rows(rows, tokenizer):
                self.assertEqual(tuple(label for label in encoded.labels if label != -100), encoded.target_ids)
                self.assertNotIn('PARENT PROCEDURAL GUIDANCE', tokenizer.decode(encoded.input_ids))

    def test_bad_sources_all_retained_and_never_feed_teaching(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)
            with patch.object(CollectionEngine, 'generate', side_effect=lambda messages, **unused: generation('bad action', messages)):
                result = runner.main(cli(root, 'expose'))
            self.assertEqual(result['model_calls'], 40)
            self.assertFalse(result['source_ready'])
            collections = runner.source.read(root / 'expose/DATA.json')['collections']
            self.assertEqual(len(collections), 10)
            self.assertTrue(all(record['transition'] is None and record['event'] is None for item in collections for record in item['records']))
            with self.assertRaisesRegex(ValueError, 'complete_ten_world_exposure'):
                runner.main(cli(root, 'teach'))
            self.assertEqual(len(state.engines), 1)

    def test_single_failed_block_emits_no_subset_but_does_not_score_gate_baseline(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            fixture(root, stack, self.material)
            runner.main(cli(root, 'expose'))
            normal = CollectionEngine.generate
            index = 0

            def child(engine, messages, **options):
                nonlocal index
                index += 1
                return generation('bad command\n', messages) if index == 1 else normal(engine, messages, **options)

            with patch.object(CollectionEngine, 'generate', child):
                result = runner.main(cli(root, 'teach'))
            self.assertEqual((result['model_calls'], result['row_count']), (187, 0))
            self.assertFalse(result['curriculum_ready'])
            document = runner.source.read(root / 'teach/LESSONS.json')
            self.assertEqual(len(document['blocks']), 4)
            self.assertEqual(document['captures'][0]['response']['raw'], 'bad command\n')
            self.assertEqual([len(block['rows']) for block in document['blocks']], [0, 48, 48, 48])
            with patch.object(CollectionEngine, 'generate', side_effect=lambda messages, **unused: generation('bad route', messages)):
                baseline = runner.main(cli(root, 'baseline'))
            self.assertEqual((baseline['status'], baseline['model_calls']), ('COMPLETE', 48))
            self.assertEqual(len(baseline['summaries']), 12)
            self.assertTrue(all(panel['summary']['paired']['correct'] == 0 for panel in baseline['summaries']))

    def test_capture_row_and_prior_source_drift_rejected(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)
            exposed = runner.main(cli(root, 'expose'))
            taught = runner.main(cli(root, 'teach'))
            inputs = replay_inputs(exposed)
            exposure, unused = runner.read_stage(root / 'expose', 'expose', inputs)
            for filename, mutate in (
                ('CALL_000.json', lambda document: document['response'].update(raw='teacher replacement')),
                ('LESSONS.json', lambda document: document['rows'][0].update(master=runner.goal.PROBE_MASTERS[0])),
            ):
                path = root / 'teach' / filename
                original = runner.source.read(path)
                document = deepcopy(original)
                mutate(document)
                write(path, document)
                rehash(root / 'teach')
                with self.assertRaises(ValueError):
                    runner.read_stage(root / 'teach', 'teach', inputs, exposure, taught['dependencies'])
                write(path, original)
                write(root / 'teach/RESULT.json', taught)
            path = root / 'prior/expose/CALL_000.json'
            document = runner.source.read(path)
            document['response']['raw'] = 'forged original source'
            write(path, document)
            rehash(root / 'prior/expose')
            with self.assertRaises(ValueError):
                runner.main(cli(root, 'prepare'))
            self.assertEqual(len(state.engines), 2)

    def test_native_error_state_drift_and_cap_fail_closed(self):
        for failure in ('native', 'state', 'cap'):
            with self.subTest(failure=failure), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = fixture(root, stack, self.material)
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
                    runner.main(cli(root, 'expose'))
                self.assertFalse((root / 'expose/RESULT.json').exists())
                failed = runner.source.read(root / 'expose/FAILED.json')
                self.assertEqual(failed['status'], 'FAILED')
                if failure == 'native':
                    self.assertEqual(failed['model_calls'], 40)
                    self.assertEqual(runner.source.read(root / 'expose/CALL_000.json')['error']['type'], 'RuntimeError')
                if failure == 'cap':
                    self.assertEqual(state.engines[0].native_calls, 1)


class GuardTests(unittest.TestCase):
    def test_import_without_ml_guard_interface_bounds_and_no_fit(self):
        script = '''
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_goal_breadth_collection
'''
        completed = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        guard = Path(runner.__file__).with_name('astra_goal_breadth_collection_guard.sh')
        completed = subprocess.run(['bash', '-n', str(guard)], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        text = guard.read_text()
        for expected in ('"$root/source_commit.txt"', 'CUDA_VISIBLE_DEVICES= python3', '"$index" "$uuid"',
                         'time.time()+11280 < 1789980180-21600', 'seconds=3600', '--kill-after=60',
                         'admission_started + 11280', '-gt 300', '--prior-collection-root'):
            self.assertIn(expected, text)
        self.assertLess(text.index('run_stage --phase teach'), text.index('run_stage --phase baseline'))
        self.assertNotIn('--phase train ', text)
        self.assertEqual(runner.CAPS, dict(prepare=0, expose=80, teach=192, baseline=288))

    def test_stub_scanner_abort_without_gpu_or_git(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / 'source'
            entry = source_dir / 'gpu/astra_goal_breadth_collection.py'
            entry.parent.mkdir(parents=True)
            entry.write_bytes(Path(runner.__file__).read_bytes())
            write(root / 'prepare/RESULT.json', dict(schema=runner.SCHEMA, phase='prepare',
                status='PREPARED_NO_MODEL', entry_sha256=runner.source.file_hash(entry),
                expected_train_targets=192, prior_seq255_targets=0))
            commit = 'a' * 40
            (root / 'source_commit.txt').write_text(commit + '\n')
            binaries = root / 'bin'
            binaries.mkdir()
            for name, content in dict(timeout='#!/bin/bash\nexit 1\n', sleep='#!/bin/bash\nexit 0\n',
                    python3='#!/bin/bash\nif [[ "$2" == "import time;"* ]]; then exit 0; fi\nexec '
                            + sys.executable + ' "$@"\n').items():
                path = binaries / name
                path.write_text(content)
                path.chmod(0o700)
            completed = subprocess.run(['bash', str(Path(runner.__file__).with_name('astra_goal_breadth_collection_guard.sh')),
                str(root), str(source_dir), commit, '0', 'fake-gpu'], capture_output=True, text=True, timeout=10,
                env=dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ['PATH']))
            self.assertEqual(completed.returncode, 1)
            self.assertTrue((root / 'launch/GUARD_ABORT.txt').exists())
            self.assertFalse((root / 'expose').exists())
            self.assertFalse((source_dir / '.git').exists())


if __name__ == '__main__':
    unittest.main()
