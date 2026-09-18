import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gpu import orch_math_feedback_uptake_node5_broker as broker
from gpu import orch_math_feedback_uptake_node5_run as runner
from organism_v6 import orch_math_feedback_uptake_node5 as policy
import orch_math_feedback_uptake_base_test as fixture


class Node5Tests(unittest.TestCase):
    def setUp(self):
        document = b'Shared principles: add stop shift behavior, pure metacognition, no outcome selection. ' * 3
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'principles'
            path.write_bytes(document)
            policy.bind_principles(path, hashlib.sha256(document).hexdigest())

    def test_only_allocated_physical_devices(self):
        self.assertEqual(set(policy.DEVICES), {2, 3})
        for index in (0, 1, 4, 5, 6, 7):
            with self.assertRaises(ValueError):
                policy.due(index, 1)

    def test_exact_additive_budgets_and_cadence(self):
        self.assertEqual(sum(policy.budget(index)['native_calls'] for index in policy.DEVICES), 3072)
        for index, count in ((2, 768), (3, 288)):
            self.assertEqual(sum(policy.due(index, turn) for turn in range(1, 769)), count)
            self.assertEqual(policy.budget(index)['parent_calls'], count)
            self.assertEqual(policy.budget(index)['sequential_episodes_per_cycle'], 2)

    def test_deadline_and_pure_base(self):
        self.assertEqual(runner.HARD, 1789491720)
        self.assertEqual(runner.HARD - runner.NATIVE, 180)
        for index in policy.DEVICES:
            self.assertIsNone(policy.budget(index)['optimizer'])
            self.assertIsNone(policy.budget(index)['adapter'])
            self.assertEqual(policy.budget(index)['weight_writes'], 0)

    def test_fresh_disjoint_namespace_cohorts(self):
        identifiers, questions = {'PRIOR'}, {'a' * 64}
        for index in policy.DEVICES:
            cohort = policy.make_cohort(index, identifiers, questions)
            for group in cohort['train'] + cohort['held']:
                for task in group:
                    self.assertIn(f'R110_NODE5_{index}_', task['id'])
                    self.assertNotIn(task['id'], identifiers)
                    self.assertNotIn(task['question_sha256'], questions)
                    identifiers.add(task['id'])
                    questions.add(task['question_sha256'])
        self.assertEqual(len(identifiers), 1921)

    def test_negative_outcomes_preserved_and_parent_blind(self):
        task = fixture.tasks()[0]
        record = policy.record(task, 'experience', dict(fixture.response(), raw='FINAL: 999999'))
        payload = policy.parent_payload(2, 1, 1, task, [record])
        self.assertFalse(payload['episodes'][0]['records'][0]['outcome']['correct'])
        self.assertIn('never an intervention trigger', payload['instruction'])
        altered = copy.deepcopy(payload)
        altered['sealed_scores'] = [1]
        with self.assertRaises(ValueError):
            policy.validate_parent_payload(altered)

    def test_parent_free_held_and_mandatory_metacognition(self):
        task = fixture.tasks('HELD')[0]
        self.assertEqual(policy.messages(task, purpose='held'), policy.base.messages(task, purpose='held'))
        with self.assertRaises(ValueError):
            policy.messages(task, purpose='held', teacher='private')
        for index in policy.DEVICES:
            self.assertTrue(all(policy.due(index, turn) for turn in range(7, 769, 8)))

    def test_wrong_root_rejected_before_any_scan(self):
        with self.assertRaises(ValueError):
            runner.configure(Path('/tmp/not-the-owned-root'))

    def test_transport_uses_trusted_node5_wrapper_only(self):
        store = broker.Store(Path('/repository'), runner.ROOT)
        with patch.object(broker.subprocess, 'run') as execute:
            store.shell('true')
            self.assertEqual(execute.call_args.args[0], ['bash', '/repository/gpu/ovx3_ssh.sh', 'true'])
            self.assertNotIn('StrictHostKeyChecking', str(execute.call_args))


if __name__ == '__main__':
    unittest.main()
