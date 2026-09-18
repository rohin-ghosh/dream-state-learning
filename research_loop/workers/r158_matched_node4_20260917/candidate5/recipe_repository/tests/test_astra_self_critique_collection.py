"""CPU-only fake-engine phase/source/state joins, with no native execution."""

from contextlib import ExitStack
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

from gpu import astra_self_critique_collection as runner
from tests.test_astra_rich_trajectory_collection import fixture, cli
from tests.test_experienced_event_self_critique import synthetic_actor


def arguments(root, state, phase, name=None, initial=False):
    values = ['--bundle', str(root/'bundle'), '--bundle-sha', state.bundle_sha,
              '--model-dir', str(root/'model'), '--exposure', str(root/'shard-0/expose'),
              '--gpu-uuid', 'fake-gpu', '--phase', phase, '--output', str(root/(name or phase)),
              '--deadline-epoch', str(time.time()+600)]
    if initial:
        values += ['--initial', str(root/runner.lesson.INITIAL)]
    return values


def setup(root, stack, *, actor_format='LF'):
    state = fixture(root, stack)
    runner.reuse.original.main(cli(root, state, 'expose'))
    stack.enter_context(patch.object(runner.reuse, 'V1_RICH_SHA', runner.source.file_hash(runner.lesson.rich.__file__)))
    data = runner.source.read(root/'shard-0/expose/DATA.json')
    actor = synthetic_actor(data['collections'][:4])
    worlds = [item['world'] for item in data['collections'][:4]]

    def factory(options, tokenizer, *, check):
        engine = state.factory.side_effect_original(options, tokenizer, check=check)

        def generate(messages, *, max_new_tokens):
            self_role = 'intervention' if messages[0]['content'] == runner.lesson.INTERVENTION_SYSTEM else 'actor'
            if self_role == 'intervention':
                world_index, task_index = 0, 0
            else:
                first = messages[1]['content']
                world_index = next(index for index, world in enumerate(worlds)
                                   if 'CURRENT ' + world['nodes'][0] in first)
                tasks = runner.lesson.rich.runtime(0)['build_tasks'](worlds[world_index])
                task_index = next(index for index, task in enumerate(tasks)
                                  if 'GOAL ' + task['goal'] in first
                                  and 'EVENTS ' + ','.join(task['events']) in first
                                  and 'PORTS ' + ','.join(task['ports']) in first)
            response = actor(messages, role=self_role, world_index=world_index, task_index=task_index)
            if self_role == 'actor' and actor_format == 'COLON':
                response['raw'] = response['raw'].replace('RATIONALE\n', 'RATIONALE: ', 1)
            elif self_role == 'actor' and actor_format == 'PLAIN':
                response['raw'] = response['raw'].split('\nACTION\n')[1]
            return response
        engine.generate = generate
        return engine

    state.factory.side_effect_original = state.factory.side_effect
    state.factory.side_effect = factory
    return state


class NativeSelfCritiqueTests(unittest.TestCase):
    def test_prepare_and_complete_three_phase_fake_lifecycle(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            with patch.object(runner.source, 'Engine', side_effect=AssertionError('no model in prepare')):
                result = runner.main(arguments(root, state, 'prepare'))
            self.assertEqual(result['status'], 'PREPARED_NO_MODEL')
            for phase in (runner.lesson.INITIAL, *runner.lesson.ARMS):
                result = runner.main(arguments(root, state, phase, initial=phase in runner.lesson.ARMS))
                self.assertEqual(result['status'], 'COMPLETE')
                self.assertEqual(result['model_calls'], runner.lesson.CAPS[phase])
                self.assertEqual(result['summary']['goals'], 16)
                self.assertEqual(result['summary']['pairs'], 8)
                self.assertEqual(result['adapter_state_after'], runner.PARENT_STATE)
                self.assertFalse(result['fit_ready'])
                self.assertFalse(result['parent_present'])
                self.assertEqual(result['fits'], 0)
            with self.assertRaises(FileExistsError):
                runner.main(arguments(root, state, runner.lesson.INITIAL))

    def test_exposure_and_shared_capture_drift_fail_before_engine(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            runner.main(arguments(root, state, runner.lesson.INITIAL))
            capture = root/runner.lesson.INITIAL/'CALL_000.json'
            capture.write_text(capture.read_text()+' ')
            with patch.object(runner.source, 'Engine', side_effect=AssertionError('no model before joins')):
                with self.assertRaises(ValueError):
                    runner.main(arguments(root, state, runner.lesson.ARMS[0], initial=True))
                original = root/'shard-0/expose/CALL_000.json'
                original.write_text(original.read_text()+' ')
                with self.assertRaises(ValueError):
                    runner.main(arguments(root, state, 'prepare', name='bad_source'))

    def test_wrong_mounted_and_changed_state_are_failures(self):
        for state_values in (['0'*64], [runner.PARENT_STATE, '0'*64]):
            with self.subTest(state_values=state_values), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = setup(root, stack)
                with patch('organism_v6.pcfl_vertical_train._state_hash', side_effect=state_values):
                    with self.assertRaisesRegex(ValueError, 'mounted_37ec|readonly_state_drift'):
                        runner.main(arguments(root, state, runner.lesson.INITIAL))
                self.assertTrue((root/runner.lesson.INITIAL/'FAILED.json').is_file())

    def test_protocol_hash_and_phase_deadline_gate(self):
        self.assertEqual(runner.source.file_hash(Path(runner.__file__).resolve().parents[1]/runner.PROTOCOL_PATH),
                         runner.PROTOCOL_SHA)
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            values = arguments(root, state, runner.lesson.INITIAL)
            values[-1] = str(time.time()-1)
            with patch.object(runner.source, 'Engine', side_effect=AssertionError('expired')):
                with self.assertRaisesRegex(ValueError, 'bounded_native_deadline'):
                    runner.main(values)

    def test_guard_is_syntactic_and_rejects_unreserved_gpu(self):
        guard = Path(runner.__file__).with_name('astra_self_critique_collection_guard.sh')
        self.assertEqual(subprocess.run(['bash', '-n', str(guard)], capture_output=True).returncode, 0)
        result = subprocess.run(['bash', str(guard), '/absent', '/absent', 'a'*40,
                                 '0', 'fake-gpu', runner.lesson.ARMS[0], '/absent', '/absent',
                                 '/absent', '0', '/absent', '/absent'], capture_output=True)
        self.assertEqual(result.returncode, 2)
        text = guard.read_text()
        self.assertIn('started + 7200', text)
        self.assertIn('--kill-after=60', text)
        self.assertNotIn('git rev-parse', text)

    def test_changed_base_blocks_complete_receipt(self):
        with TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            state = setup(root, stack)
            factory = state.factory.side_effect

            def broken_base(*args, **kwargs):
                engine = factory(*args, **kwargs)
                engine.verify_base = lambda: (_ for _ in ()).throw(ValueError('changed base'))
                return engine

            state.factory.side_effect = broken_base
            with self.assertRaisesRegex(ValueError, 'changed base'):
                runner.main(arguments(root, state, runner.lesson.INITIAL))
            self.assertTrue((root/runner.lesson.INITIAL/'FAILED.json').exists())
            self.assertFalse((root/runner.lesson.INITIAL/'RESULT.json').exists())

    def test_v3_colon_and_plain_native_capture_replay_joins(self):
        for actor_format in ('COLON', 'PLAIN'):
            with self.subTest(actor_format=actor_format), TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary)
                state = setup(root, stack, actor_format=actor_format)
                for phase in (runner.lesson.INITIAL, *runner.lesson.ARMS):
                    result = runner.main(arguments(root, state, phase, initial=phase in runner.lesson.ARMS))
                    self.assertEqual(result['status'], 'COMPLETE')
                    self.assertEqual(result['projection_policy'], runner.lesson.PROJECTION_POLICY)
                    self.assertEqual(result['summary']['goals'], 16)
                    self.assertEqual(result['model_calls'], runner.lesson.CAPS[phase])
                    self.assertFalse(result['fit_ready'])
                    self.assertFalse(result['semantic_pass'])
                    document = runner.source.read(root/phase/'DATA.json')
                    for capture in document['captures']:
                        if capture['role'] == 'actor':
                            expected = 'RATIONALE: ' if actor_format == 'COLON' else 'READ EVENT '
                            if capture['response']['raw'].startswith('ROUTE '):
                                expected = 'ROUTE '
                            self.assertTrue(capture['response']['raw'].startswith(expected))


if __name__ == '__main__':
    unittest.main()
