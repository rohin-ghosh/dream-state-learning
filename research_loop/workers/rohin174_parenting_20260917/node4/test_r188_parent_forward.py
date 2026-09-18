"""CPU regressions for scoped parent recovery without publication replay."""

import ast
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest


HOME = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('r188_forward_tests', HOME / 'r188_parent_forward.py')
forward = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(forward)
MESSAGE = ('Reported example (Rohin; C2): Compare differing predictions, calculate a separating case, then revise.\n'
    '1. What would more thinking resolve here?\n2. What would you try or keep doing?\n'
    '3. What observation would change your choice?')


class ParentRecoveryTests(unittest.TestCase):
    def test_reported_example_and_three_questions(self):
        forward.question_shape(MESSAGE)
        self.assertIn('R188_REPORTED_WORKED_EXAMPLES_V1', forward.POLICY)
        self.assertIn('explicit English release', forward.POLICY)
        self.assertIn('continuity.chosen_object.quote', forward.POLICY)

    def test_unattributed_example_answer_and_baseline_refused(self):
        for message in (MESSAGE.replace('Reported example (Rohin; C2):', 'Here is the answer:'),
                        MESSAGE + '\nDo this answer.', forward.raw.BASELINE_END,
                        '\n'.join(MESSAGE.splitlines()[1:])):
            with self.assertRaises(ValueError):
                forward.question_shape(message)

    def test_private_validation_remains_first(self):
        def reject(*arguments):
            raise ValueError('original_private_object_rule')
        policy = SimpleNamespace(prompt=lambda *arguments: ('private rules', {}), decision=reject)
        forward.bind(policy)
        with self.assertRaisesRegex(ValueError, 'original_private_object_rule'):
            policy.decision({'message': MESSAGE}, {}, {})

    def test_silence_and_original_payload_remain_unchanged(self):
        payload = {'synthetic': True}
        policy = SimpleNamespace(prompt=lambda *arguments: ('private rules', payload), decision=lambda *arguments: None)
        forward.bind(policy)
        instruction, returned = policy.prompt({}, {}, {})
        self.assertIs(returned, payload)
        self.assertIn('private rules', instruction)
        self.assertIsNone(policy.decision({'speak': False}, {}, {}))

    def test_raw1_and_cadences_unchanged(self):
        self.assertEqual(forward.ARMS, {0: ('B', 2), 3: ('D', 3), 4: ('A', 1)})
        with self.assertRaisesRegex(ValueError, 'raw1_untouched'):
            forward.stage(HOME / 'activation_r188_test/physical1', 1)

    def test_existing_sleep_withdrawal_remains(self):
        for physical in forward.ARMS:
            self.assertTrue(forward.phase_hold(physical, {'baseline_completed_sleeps': 40},
                {'delivered': {}, 'sleep_count': 43}))
            self.assertFalse(forward.phase_hold(physical, {'baseline_completed_sleeps': 40},
                {'delivered': {}, 'sleep_count': 44}))

    def failure_fixture(self, root, status='VALIDATION_FAILED'):
        state = dict(request_count=12, response_count=11, head_sha256='synthetic-head')
        attempt = root / 'parent_000000000012'
        attempt.mkdir()
        forward.base.write(attempt / 'SOURCE.json', state)
        result = dict(status=status, source_sha256=forward.base.sha(attempt / 'SOURCE.json'), error='explicit_English_release')
        forward.base.write(attempt / 'RESULT.json', result)
        return state, attempt

    def test_known_prepublication_failure_gets_fresh_source_wait(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state, attempt = self.failure_fixture(root)
            receipt = forward.validation_recovery(root, state)
            self.assertFalse(receipt['same_source_retry'])
            self.assertFalse(receipt['publication_attempted'])
            self.assertEqual(receipt['failed_response_count'], 11)
            self.assertEqual(receipt['error'], 'explicit_English_release')

    def test_any_publish_intent_blocks_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state, attempt = self.failure_fixture(root)
            forward.base.write(attempt / 'PUBLISH_INTENT.json', {'synthetic': True})
            with self.assertRaisesRegex(ValueError, 'only_known_prepublication'):
                forward.validation_recovery(root, state)

    def test_published_unknown_and_wrong_source_never_retried(self):
        for status in ('PUBLISHED', 'PUBLICATION_UNKNOWN'):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                state, attempt = self.failure_fixture(root, status)
                with self.assertRaisesRegex(ValueError, 'only_known_prepublication'):
                    forward.validation_recovery(root, state)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state, attempt = self.failure_fixture(root)
            with self.assertRaisesRegex(ValueError, 'exact_failed_source'):
                forward.validation_recovery(root, dict(state, head_sha256='changed'))

    def test_worker_continues_validation_failure_but_stops_unknown(self):
        tree = ast.parse((HOME / 'r188_parent_forward.py').read_text())
        serve = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'serve')
        rendered = ast.unparse(serve)
        self.assertIn("('PUBLICATION_UNKNOWN', 'PROVIDER_FAILED')", rendered)
        self.assertNotIn("('PUBLICATION_UNKNOWN', 'VALIDATION_FAILED', 'PROVIDER_FAILED')", rendered)
        self.assertIn('validation_recovery(output, state)', rendered)
        self.assertIn('policy.tick(base.REPO, config, output, seed, state)', rendered)

    def test_actual_bound_tick_does_not_repeat_failed_response(self):
        source = HOME / 'activation_r184_20260917T2248Z/physical3/source/gpu/orch_r166_parent_policy.py'
        node = next(node for node in ast.parse(source.read_text()).body if isinstance(node, ast.FunctionDef) and node.name == 'tick')
        calls = []
        def strong(*arguments, **options):
            calls.append(True)
            return {'synthetic': True}, 'synthetic', {}
        def decision(*arguments):
            raise ValueError('explicit_English_release')
        def local_attempts(output):
            return [json.loads(path.read_text()) for path in sorted(output.glob('parent_*/SOURCE.json'))]
        def memory(seed, attempts, state):
            return dict(awaiting_render=False, last_response_count=max([0] + [item['response_count'] for item in attempts]),
                last_request_count=0, grammar_delivered=True, relapses=[])
        namespace = dict(validate=lambda config: None, require=forward.base.require,
            memory=memory, local_attempts=local_attempts, bind_watcher_audits=lambda *arguments: None,
            Path=Path, time=SimpleNamespace(time=lambda: 1), prompt=lambda *arguments: ('synthetic', {}),
            community=SimpleNamespace(write=forward.base.write), decision=decision,
            parent=SimpleNamespace(strong=strong, sha=forward.base.sha))
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<bound_tick>', 'exec'), namespace)
        config = dict(r175_schema='ROHIN175_PARENT_ARMS_V1', r175_arm='D', schedule_on='response',
            cadence_responses=3, r175_word_limit=90, hard_end_unix=100, community_learner=False)
        state = dict(caught_up=True, request_count=12, response_count=11,
            head_sha256='first', events=[{'actor': 'child'}])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.assertEqual(namespace['tick'](HOME, config, output, {}, state)['status'], 'VALIDATION_FAILED')
            self.assertEqual(namespace['tick'](HOME, config, output, {}, dict(state, head_sha256='new-journal-only'))['status'],
                'WAITING_FOR_NEW_CHILD_BOUNDARY')
            next_state = dict(state, response_count=14, request_count=15, head_sha256='new-child-response')
            self.assertEqual(namespace['tick'](HOME, config, output, {}, next_state)['status'], 'VALIDATION_FAILED')
            self.assertEqual(len(calls), 2)


if __name__ == '__main__':
    unittest.main()
