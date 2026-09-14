"""CPU-only no-fit native stage, source replay and bounded guard checks."""

from contextlib import ExitStack
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from gpu import astra_goal_pair_collection as runner
from tests.test_astra_event_two_hop_memory import FakeEngine, actor, arguments, material_fixture, setup, write
from tests.test_experienced_event_two_hop import exposed_child, generation
from tests.test_experienced_event_two_hop_lesson import Tokenizer


class CollectionEngine(FakeEngine):
    def generate(self, messages, *, max_new_tokens):
        assert max_new_tokens == 160
        self.native_calls += 1
        if self.mutate_state:
            self.parameter.state = 'd' * 64
        if self.raise_native:
            raise RuntimeError('retained native failure')
        if self.invalid:
            return generation('not a command\n\n', messages)
        if messages[0]['content'] == runner.goal.hop.COLLECTION_SYSTEM:
            return exposed_child(messages, suffix='\n\n')
        delimiter = 'Execute only this next command, then wait for actual feedback:\n'
        if delimiter in messages[-1]['content']:
            return generation(messages[-1]['content'].split(delimiter)[1] + '\n\n', messages)
        return actor(messages)


def cli(root, phase):
    values = arguments(root, 'prepare')
    values[values.index('--phase') + 1] = phase
    values[values.index('--output') + 1] = str(root / phase)
    if phase in ('teach', 'baseline'):
        values += ['--exposure', str(root / 'expose')]
    if phase == 'baseline':
        values += ['--teaching', str(root / 'teach')]
    return values


def fixture(root, stack, material):
    state = setup(root, stack, material)

    def factory(arguments, tokenizer, *, check):
        engine = CollectionEngine(arguments, tokenizer, check, {})
        state.engines.append(engine)
        return engine

    state.factory.side_effect = factory
    return state


def rehash(directory):
    result = runner.source.read(directory / 'RESULT.json')
    result['output_files'] = {path.name: runner.source.file_hash(path)
                             for path in directory.glob('*.json') if path.name != 'RESULT.json'}
    write(directory / 'RESULT.json', result)


class CollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.material = material_fixture()

    def test_prepare_no_model_explicit_old_ids_and_fixed_disjoint_worlds(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)
            result = runner.main(cli(root, 'prepare'))
            state.factory.assert_not_called()
            state.token_loader.assert_not_called()
            self.assertEqual(result['status'], 'PREPARED_NO_MODEL')
            self.assertEqual((result['fits'], result['updates'], result['model_calls']), (0, 0, 0))
            self.assertFalse(result['trainingAllowed'])
            self.assertEqual(result['binding']['memory']['transfer'], state.binding)
            known = {fact[key] for bank in self.material['banks'] for fact in bank
                     for key in ('event', 'node', 'port', 'outcome', 'receipt')}
            for world in (runner.memory.hop.build_world(), state.world):
                known.update(runner.goal.identifiers(world))
            self.assertEqual(set(result['binding']['old_ids']), known)
            for split in ('TRAIN', 'PROBE'):
                for world in result['binding']['worlds'][split]:
                    identifiers = runner.goal.identifiers(world)
                    self.assertTrue(known.isdisjoint(identifiers))
                    known.update(identifiers)
            self.assertIn('NEW_IDENTIFIER_DEV', result['probe_scope'])

    def test_complete_pipeline_32_48_96_actual_calls_same_readonly_parent(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)
            results = [runner.main(cli(root, phase)) for phase in ('expose', 'teach', 'baseline')]
            self.assertEqual([result['model_calls'] for result in results], [32, 48, 96])
            self.assertEqual(len(state.engines), 3)
            for engine, result in zip(state.engines, results):
                self.assertEqual((engine.steps, engine.optimizers), (0, []))
                self.assertGreater(engine.base_checks, 0)
                self.assertEqual(Path(engine.arguments.adapter_dir), root / 'lesson/train/adapter')
                self.assertEqual(result['loaded_adapter_state_sha256'], runner.PARENT_STATE)
                self.assertEqual(result['adapter_state_after'], runner.PARENT_STATE)
                self.assertEqual((result['fits'], result['updates']), (0, 0))
            self.assertTrue(results[1]['curriculum_ready'])
            self.assertEqual(results[1]['row_count'], 48)
            self.assertEqual(results[2]['dependencies'], dict(
                exposure_result_sha256=runner.source.file_hash(root / 'expose/RESULT.json'),
                teaching_result_sha256=runner.source.file_hash(root / 'teach/RESULT.json')))
            self.assertEqual(results[2]['role_calls'], dict(actor=96))
            for item in results[2]['summaries']:
                self.assertIn(item['master'], runner.goal.PROBE_MASTERS)
                self.assertEqual(item['summary']['individual']['denominator'], 4)
                self.assertEqual(item['summary']['paired']['denominator'], 2)
                if item['condition'] == 'OWN_TEXT':
                    self.assertEqual(item['summary']['paired']['correct'], 2)
            inputs = dict(binding=results[0]['binding'], worlds=results[0]['binding']['worlds'],
                          old_ids=results[0]['binding']['old_ids'])
            exposure, expose_sha = runner.read_stage(root / 'expose', 'expose', inputs)
            teaching, teach_sha = runner.read_stage(root / 'teach', 'teach', inputs, exposure,
                                                   dict(exposure_result_sha256=expose_sha))
            baseline, unused = runner.read_stage(root / 'baseline', 'baseline', inputs, exposure,
                dict(exposure_result_sha256=expose_sha, teaching_result_sha256=teach_sha))
            self.assertEqual(len(baseline['panels']), 4)
            self.assertEqual(teaching['row_count'], 48)
            self.assertEqual(len(state.engines), 3)

    def test_train_only_actual_coached_response_bridge_and_student_masks(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            fixture(root, stack, self.material)
            runner.main(cli(root, 'expose'))
            runner.main(cli(root, 'teach'))
            lessons = runner.source.read(root / 'teach/LESSONS.json')
            probe_ids = set().union(*(runner.goal.identifiers(world)
                for world in runner.source.read(root / 'expose/WORLDS.json')['PROBE']))
            for index, (capture, row) in enumerate(zip(lessons['captures'], lessons['rows'])):
                native = runner.source.read(root / f'teach/CALL_{index:03d}.json')
                self.assertEqual({key: native[key] for key in ('messages', 'response', 'error')},
                                 {key: capture[key] for key in ('messages', 'response', 'error')})
                self.assertEqual(native['response']['messages'], native['messages'])
                self.assertEqual(row['assistant'], native['response']['raw'])
                self.assertTrue(row['assistant'].endswith('\n\n'))
                self.assertIn(capture['master'], runner.goal.TRAIN_MASTERS)
                self.assertNotIn('PARENT PROCEDURAL GUIDANCE', str(row['prefix']))
                self.assertFalse(any(value in str(native['messages']) for value in probe_ids))
            tokenizer = Tokenizer()
            for encoded in runner.goal.encode_rows(lessons['rows'], tokenizer):
                self.assertEqual(tuple(label for label in encoded.labels if label != -100), encoded.target_ids)
                self.assertNotIn('PARENT PROCEDURAL GUIDANCE', tokenizer.decode(encoded.input_ids))

    def test_failed_exposures_retained_no_replacement_or_downstream_model(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)
            with patch.object(CollectionEngine, 'generate', side_effect=lambda messages, **kwargs: generation('bad action', messages)):
                result = runner.main(cli(root, 'expose'))
            self.assertEqual(result['model_calls'], 16)
            self.assertFalse(result['source_ready'])
            document = runner.source.read(root / 'expose/DATA.json')
            self.assertEqual(len(document['collections']), 4)
            self.assertTrue(all(len(item['records']) == 4 and not item['ready'] for item in document['collections']))
            self.assertTrue(all(record['transition'] is None and record['event'] is None
                for item in document['collections'] for record in item['records']))
            with self.assertRaisesRegex(ValueError, 'complete_four_world_exposure'):
                runner.main(cli(root, 'teach'))
            self.assertEqual(len(state.engines), 1)

    def test_unsuccessful_teaching_does_not_gate_probe_baseline(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            fixture(root, stack, self.material)
            runner.main(cli(root, 'expose'))
            with patch.object(CollectionEngine, 'generate', side_effect=lambda messages, **kwargs: generation('bad command\n', messages)):
                result = runner.main(cli(root, 'teach'))
            self.assertEqual((result['model_calls'], result['row_count']), (8, 0))
            self.assertFalse(result['curriculum_ready'])
            lessons = runner.source.read(root / 'teach/LESSONS.json')
            self.assertTrue(all(not episode['complete'] for episode in lessons['episodes']))
            self.assertEqual([capture['response']['raw'] for capture in lessons['captures']], ['bad command\n'] * 8)
            baseline = runner.main(cli(root, 'baseline'))
            self.assertEqual((baseline['status'], baseline['model_calls']), ('COMPLETE', 96))

    def test_native_errors_retained_all_worlds_attempted_no_success_result(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            fixture(root, stack, self.material)
            with patch.object(CollectionEngine, 'generate', side_effect=RuntimeError('native failure')):
                with self.assertRaisesRegex(ValueError, 'native_errors_retained'):
                    runner.main(cli(root, 'expose'))
            failed = runner.source.read(root / 'expose/FAILED.json')
            self.assertEqual(failed['model_calls'], 16)
            self.assertFalse((root / 'expose/RESULT.json').exists())
            for index in range(16):
                capture = runner.source.read(root / f'expose/CALL_{index:03d}.json')
                self.assertEqual(capture['error'], dict(type='RuntimeError', message='native failure'))
                self.assertIsNone(capture['response'])
            self.assertEqual(len(runner.source.read(root / 'expose/DATA.json')['collections']), 4)

    def test_zero_baseline_keeps_every_probe_episode_no_score_gate(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            fixture(root, stack, self.material)
            runner.main(cli(root, 'expose'))
            runner.main(cli(root, 'teach'))
            with patch.object(CollectionEngine, 'generate', side_effect=lambda messages, **kwargs: generation('bad route', messages)):
                result = runner.main(cli(root, 'baseline'))
            self.assertEqual((result['status'], result['model_calls']), ('COMPLETE', 16))
            document = runner.source.read(root / 'baseline/DATA.json')
            self.assertEqual(sum(len(panel['episodes']) for panel in document['panels']), 16)
            for panel in document['panels']:
                self.assertEqual(panel['summary']['individual'], dict(correct=0, denominator=4))
                self.assertEqual(panel['summary']['paired'], dict(correct=0, denominator=2))
                for episode in panel['episodes']:
                    self.assertEqual(episode['terminal_reason'], 'invalid_command')
                    self.assertEqual(episode['traces'][0]['response']['raw'], 'bad route')
                    self.assertNotIn('PARENT PROCEDURAL GUIDANCE', str(episode['messages']))

    def test_capture_and_row_forgery_rejected_even_with_updated_file_hashes(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            fixture(root, stack, self.material)
            exposed = runner.main(cli(root, 'expose'))
            taught = runner.main(cli(root, 'teach'))
            inputs = dict(binding=exposed['binding'], worlds=exposed['binding']['worlds'],
                          old_ids=exposed['binding']['old_ids'])
            exposure, unused = runner.read_stage(root / 'expose', 'expose', inputs)
            for name, change in (
                ('CALL_000.json', lambda item: item['response'].update(raw='ROUTE fabricated')),
                ('CALL_000.json', lambda item: item.update(messages=[dict(role='user', content='forged')])),
                ('LESSONS.json', lambda item: item['rows'][0].update(assistant='teacher replacement')),
                ('DATA.json', lambda item: item.update(row_count=47)),
            ):
                with self.subTest(name=name):
                    path = root / 'teach' / name
                    original = runner.source.read(path)
                    forged = deepcopy(original)
                    change(forged)
                    write(path, forged)
                    rehash(root / 'teach')
                    with self.assertRaises(ValueError):
                        runner.read_stage(root / 'teach', 'teach', inputs, exposure, taught['dependencies'])
                    write(path, original)
                    write(root / 'teach/RESULT.json', taught)

    def test_phase_join_state_and_unknown_call_drift_rejected(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = fixture(root, stack, self.material)
            exposed = runner.main(cli(root, 'expose'))
            inputs = dict(binding=exposed['binding'], worlds=exposed['binding']['worlds'],
                          old_ids=exposed['binding']['old_ids'])
            for key, value in (('adapter_state_after', '9d'), ('dependencies', {'unknown': 'call'}),
                               ('trainingAllowed', True), ('model_calls', 31)):
                with self.subTest(key=key):
                    write(root / 'expose/RESULT.json', dict(exposed, **{key: value}))
                    with self.assertRaises(ValueError):
                        runner.read_stage(root / 'expose', 'expose', inputs)
            write(root / 'expose/RESULT.json', exposed)
            write(root / 'expose/CALL_032.json', runner.source.read(root / 'expose/CALL_000.json'))
            rehash(root / 'expose')
            with self.assertRaisesRegex(ValueError, 'exact_native_call_inventory'):
                runner.read_stage(root / 'expose', 'expose', inputs)
            self.assertEqual(len(state.engines), 1)

    def test_actual_state_mutation_and_call_cap_fail_closed(self):
        for mode in ('state', 'cap'):
            with self.subTest(mode=mode), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = fixture(root, stack, self.material)
                factory = state.factory.side_effect
                if mode == 'state':
                    def mutating(*args, **kwargs):
                        engine = factory(*args, **kwargs)
                        engine.mutate_state = True
                        return engine
                    state.factory.side_effect = mutating
                else:
                    stack.enter_context(patch.dict(runner.CAPS, expose=1))
                with self.assertRaisesRegex(ValueError, 'readonly_goal_state_drift' if mode == 'state' else 'goal_native_call_cap'):
                    runner.main(cli(root, 'expose'))
                self.assertFalse((root / 'expose/RESULT.json').exists())
                self.assertTrue((root / 'expose/FAILED.json').exists())
                if mode == 'cap':
                    self.assertEqual(state.engines[0].native_calls, 1)


class GuardTests(unittest.TestCase):
    def test_import_without_ml_and_guard_fixed_phases_bounds(self):
        script = '''
import builtins
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name.split('.')[0] in ('torch', 'transformers', 'peft', 'tokenizers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
builtins.__import__ = checked
from gpu import astra_goal_pair_collection
'''
        result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        guard = Path(runner.__file__).with_name('astra_goal_pair_collection_guard.sh')
        result = subprocess.run(['bash', '-n', str(guard)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = guard.read_text()
        for expected in ('"$root/source_commit.txt"', 'CUDA_VISIBLE_DEVICES= python3', '"$index" "$uuid"',
                         'time.time()+6060 < 1789980180-21600', 'seconds=1860', '--kill-after=60'):
            self.assertIn(expected, text)
        self.assertLess(text.index('run_stage --phase teach'), text.index('run_stage --phase baseline'))
        self.assertNotIn('--phase train ', text)
        self.assertNotIn('git archive', text)
        self.assertEqual(runner.CAPS, dict(prepare=0, expose=32, teach=48, baseline=96))

    def test_stub_scanner_abort_never_loads_model_or_requires_git(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / 'source'
            entry = source_dir / 'gpu/astra_goal_pair_collection.py'
            entry.parent.mkdir(parents=True)
            entry.write_bytes(Path(runner.__file__).read_bytes())
            write(root / 'prepare/RESULT.json', dict(schema=runner.SCHEMA, phase='prepare',
                status='PREPARED_NO_MODEL', entry_sha256=runner.source.file_hash(entry)))
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
            guard = Path(runner.__file__).with_name('astra_goal_pair_collection_guard.sh')
            completed = subprocess.run(['bash', str(guard), str(root), str(source_dir), commit, '0', 'fake-gpu'],
                env=dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ['PATH']),
                capture_output=True, text=True, timeout=10)
            self.assertEqual(completed.returncode, 1)
            self.assertTrue((root / 'launch/GUARD_ABORT.txt').exists())
            self.assertFalse((root / 'expose').exists())
            self.assertFalse((source_dir / '.git').exists())


if __name__ == '__main__':
    unittest.main()
