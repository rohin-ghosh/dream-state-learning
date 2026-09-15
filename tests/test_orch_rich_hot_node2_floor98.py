import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from gpu import orch_rich_hot_node2_floor98 as runner
from organism_v6 import orch_rich_hot_node2_floor98 as policy


class Floor98Tests(unittest.TestCase):
    def document(self):
        records = [dict(question=f'Unseen task {index}', answer='work #### 42') for index in range(12)]
        return policy.cohort(records, dict(tasks=[], excluded_ids=[], excluded_question_hashes=[]))

    def test_code_first_on_both_parities_with_balanced_families(self):
        document = self.document()
        for parity in (0, 1):
            tasks = [policy.task_at(document, 0, position) for position in range(parity, 24, 2)]
            self.assertEqual(tasks[0]['family'], 'code')
            self.assertEqual(Counter(task['family'] for task in tasks), dict(code=4, math=4, route=4))
            self.assertEqual(len({task['id'] for task in tasks}), 12)

    def test_relevant_alternative_requested_not_keyword_certified(self):
        task = policy.task_at(self.document(), 0, 2)
        self.assertIn('When relevant', str(policy.messages(task, 'ORIGINAL_RICH')))
        self.assertIn('do not invent', str(policy.messages(task, 'LIGHT_BRANCH')))
        for length in (30, 900):
            response = dict(raw='FINAL: 42', terminal=True, truncated=False, token_ids=[1] * length + [2])
            result = policy.outcome(task, response)
            self.assertTrue(result['correct'])
            self.assertFalse(result['admitted'])
            self.assertFalse(result['first_person_gate'])
            self.assertFalse(result['length_150_400_gate'])
            self.assertEqual(result['branching_semantic_annotation'], 'UNREVIEWED')

    def test_lane_release_does_not_require_other_lanes_to_finish(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertFalse(runner.ready_lane(root, 0))
            (root / 'shard0').mkdir()
            (root / 'reservations').mkdir()
            (root / 'shard0/TERMINAL.json').write_text('{"status":"COMPLETE"}')
            (root / 'shard0/AFTER.json').write_text('{"unchanged":true}')
            (root / 'LAUNCH_0.json').write_text(json.dumps(dict(identity=dict(pid=2000000000, uid=0, start_ticks='1'))))
            self.assertTrue(runner.ready_lane(root, 0))
            self.assertFalse(runner.ready_lane(root, 1))
            (root / 'reservations/0_task_final.json').write_text(json.dumps(dict(index=0, task_id='task', stage='final')))
            with self.assertRaisesRegex(ValueError, 'unresolved_original_lane_request'):
                runner.ready_lane(root, 0)
            (root / 'shard0/task_final.json').write_text('{"index":0}')
            self.assertTrue(runner.ready_lane(root, 0))

    def test_failed_original_not_replayed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'shard0').mkdir()
            (root / 'shard0/TERMINAL.json').write_text('{"status":"FAILED"}')
            with self.assertRaisesRegex(ValueError, 'no_auto_replay'):
                runner.ready_lane(root, 0)


if __name__ == '__main__':
    unittest.main()
