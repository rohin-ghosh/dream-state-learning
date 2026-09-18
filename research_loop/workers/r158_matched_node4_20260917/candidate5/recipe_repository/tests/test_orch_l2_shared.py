import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from organism_v6 import orch_l2_shared as shared
from organism_v6 import orch_l2_guided as guided
from organism_v6 import orch_full_rich as rich
from organism_v6.experienced_event_goal_replay_layout import GoalReplayLayout
from gpu import orch_l2_shared_run as run
from gpu import orch_l2_shared_guard as guard


class SharedTests(unittest.TestCase):
    def test_only_transient_transport_scans_are_retryable(self):
        result = SimpleNamespace(returncode=1, stdout=json.dumps(dict(owners=[],
            unresolved=[dict(comm='sshd'), dict(comm='sftp-server')])))
        self.assertTrue(guard.transient_transport_scan(result))
        for report in (dict(owners=[1], unresolved=[dict(comm='sshd')]),
                       dict(owners=[], unresolved=[dict(comm='python')]),
                       dict(owners=[], unresolved=[])):
            result.stdout = json.dumps(report)
            self.assertFalse(guard.transient_transport_scan(result))
        result.stdout = 'not json'
        self.assertFalse(guard.transient_transport_scan(result))

    def setUp(self):
        self.cohort = shared.cohort([])
        self.world = self.cohort['train'][0][0]
        self.task = shared.tasks(self.world)[0]

    def test_fixed_disjoint_denominators(self):
        self.assertEqual(len(shared.MASTERS), 56)
        self.assertEqual([len(group) for group in self.cohort['train']], [8] * 3)
        self.assertEqual([len(group) for group in self.cohort['held']], [8] * 4)
        self.assertEqual(len(shared.tasks(self.world)), 2)

    def test_release_collision_fails(self):
        with self.assertRaisesRegex(ValueError, 'release_namespace_collision'):
            shared.cohort([self.world['edges'][0]['event']])

    def test_unknown_world_rejected(self):
        with self.assertRaises(ValueError):
            shared.runtime('held266')

    def test_call_and_update_caps(self):
        self.assertEqual(shared.CAPS['all_calls'], 448 + 4 * 1600 + 3 * 600)
        self.assertLessEqual(shared.CAPS['all_calls'], 20000)
        self.assertEqual(GoalReplayLayout(96, 4).updates, 216)
        self.assertEqual(shared.RECIPE['learning_rate'], 3e-5)
        self.assertEqual(run.DEVICES['LONG'][0], 1)

    def test_source_cohort_hash_required(self):
        with self.assertRaisesRegex(ValueError, 'cohort_drift'):
            shared.verify_source(self.cohort, {'cohort_sha256': 'bad'})

    def test_no_parent_at_readout(self):
        prompts = []

        def generate(messages):
            prompts.append(messages)
            return dict(raw='invalid', terminal=True, truncated=False)

        guided.episode(self.world, self.task, generate, {}, rich_contract=False)
        self.assertNotIn(rich.GUIDANCE, str(prompts))
        self.assertNotIn('PARENT LEARNING COACH', str(prompts))

    def test_full_parent_visible_but_neutral_prefix_clean(self):
        text = 'Please explain what you need to learn, and ask me a question.'
        payloads = []

        def parent(payload):
            payloads.append(payload)
            return dict(speak=True, message=text, rationale='coach')

        result = guided.episode(self.world, self.task,
            lambda messages: dict(raw='invalid', terminal=True, truncated=False), {}, parent=parent)
        capture = result['captures'][0]
        self.assertIn(text, capture['messages'][-1]['content'])
        self.assertNotIn(text, str(capture['student_prefix']))
        self.assertNotIn('held', payloads[0])
        self.assertEqual(set(payloads[0]), {'kind', 'turn', 'task', 'public_messages', 'prior_parent_messages', 'learner'})

    def test_parent_decline_not_replaced(self):
        result = guided.episode(self.world, self.task,
            lambda messages: dict(raw='invalid', terminal=True, truncated=False), {},
            parent=lambda payload: dict(speak=False, message='', rationale='decline'))
        self.assertEqual(result['parent_messages'][0]['rationale'], 'decline')
        self.assertNotIn('PARENT LEARNING COACH', str(result['captures'][0]['messages']))

    def test_correct_transition_score_and_raw_preservation(self):
        first = next(edge for edge in self.world['edges'] if edge['outcome'] == self.task['goal'])
        root = next(edge for edge in self.world['edges'] if edge['outcome'] == first['node'])
        responses = iter(['I will follow the actual evidence.\nROUTE ' + root['port'],
                          'Now I can revise.\nROUTE ' + first['port']])
        result = guided.episode(self.world, self.task,
            lambda messages: dict(raw=next(responses), terminal=True, truncated=False), {})
        self.assertTrue(result['correct'])
        self.assertEqual(result['actor_calls'], 2)
        self.assertEqual(result['captures'][1]['student_prefix'][2]['content'], result['captures'][0]['response']['raw'])

    def test_failures_preserve_episode_and_zero_rows(self):
        def generate(messages):
            raise ValueError('native_failed')

        result = guided.episode(self.world, self.task, generate, {})
        self.assertFalse(result['correct'])
        self.assertEqual(result['actor_calls'], 1)
        self.assertFalse(guided.admitted_captures(result, [])[0]['gate']['admitted'])

    def test_parent_telemetry_is_training_only(self):
        value = guided.learner_telemetry([], 1)
        self.assertEqual(value['readout_visibility'], 'NO_READOUT_DATA')
        self.assertEqual(value['completed_experience_episodes'], 0)

    def test_pre_dispatch_budget_records_errors_too(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(run.spend(root, 'SHORT', 1, {'phase': 'test'}), 0)
            with self.assertRaisesRegex(ValueError, 'call_budget_exhausted'):
                run.spend(root, 'SHORT', 1, {'phase': 'test'})
            self.assertEqual(len((root / 'CALLS_SHORT.jsonl').read_text().splitlines()), 1)

    def test_null_receipt_can_preserve_prior_actual_child(self):
        from tests.test_orch_guided_native import adapter

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = adapter(root / 'initial', 'child')
            run.write(root / 'SHORT/cycle1/sleep/COMPLETE.json', dict(status='COMPLETE', arm='SHORT', cycle=1,
                output_adapter=identity.document(), process=['boot', 1, 2], updates=0, unchanged=True))
            actual, processes = run.input_identity(root, 'SHORT', 2, 'experience')
            self.assertEqual(actual, identity)
            self.assertEqual(processes, [('boot', 1, 2)])

    def test_previous_child_wrong_arm_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run.write(root / 'SHORT/cycle1/sleep/COMPLETE.json', dict(status='COMPLETE', arm='LONG', cycle=1))
            with self.assertRaisesRegex(ValueError, 'previous_actual_child'):
                run.input_identity(root, 'SHORT', 2, 'experience')

    def test_partial_source_rejects_different_world(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self.cohort['train'][0][0]
            run.write(root / 'source_capture' / (first['master'] + '.json'), dict(world=self.cohort['held'][0][0]))
            with self.assertRaisesRegex(ValueError, 'partial_source_world_drift'):
                run.experience_store(root, self.cohort, 1, lambda phase: None)

    def test_native_legacy_tuples_match_identical_json_lists(self):
        from dataclasses import asdict

        row = run.source.native.EncodedRow((1, 2, 3), (-100, 2, -100), (2,))
        encoded = (row,) * 222
        reference = json.loads(json.dumps([asdict(item) for item in encoded]))
        self.assertNotEqual([asdict(item) for item in encoded], reference)
        run.verify_legacy_reference(encoded, reference)
        reference[0]['labels'][1] = 99
        with self.assertRaisesRegex(ValueError, 'legacy_reference_drift'):
            run.verify_legacy_reference(encoded, reference)


if __name__ == '__main__':
    unittest.main()
