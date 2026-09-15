import unittest
import json
from pathlib import Path
import tempfile

from gpu.orch_rich_hot_node1_boundary import complete_tasks
from gpu.orch_rich_hot_node1_v2_run import reserve


class BoundaryTests(unittest.TestCase):
    def row(self, stage, number, index=4, task='task'):
        return dict(index=index, task_id=task, stage=stage, global_call=number)

    def test_waits_for_entire_source_second_pass_pair(self):
        source = self.row('source', 1)
        self.assertIsNone(complete_tasks([source], [source], 4))
        second = self.row('own_second_pass', 2)
        self.assertEqual(complete_tasks([source, second], [source, second], 4), ['task'])

    def test_reserved_next_call_prevents_stop(self):
        first = self.row('source', 1, index=0)
        next_call = self.row('source', 2, index=0, task='next')
        self.assertIsNone(complete_tasks([first], [first, next_call], 0))

    def test_other_shards_do_not_prevent_task_boundary(self):
        first = self.row('source', 1, index=0)
        other = self.row('source', 2, index=7)
        self.assertEqual(complete_tasks([first], [first, other], 0), ['task'])

    def test_context_failure_is_preserved_not_retried(self):
        first = self.row('source', 1)
        failure = dict(task_id='task', stage='own_second_pass')
        self.assertEqual(complete_tasks([first], [first], 4, [failure]), ['task'])

    def test_empty_checkpoint_is_not_a_completed_task(self):
        self.assertIsNone(complete_tasks([], [], 0))

    def test_v2_reservation_uses_original_ledger_and_phase(self):
        with tempfile.TemporaryDirectory() as directory:
            original, revised = Path(directory) / 'v1', Path(directory) / 'v2'
            original.mkdir()
            revised.mkdir()
            (original / 'CALL_RESERVATIONS.jsonl').write_text('{"global_call":1,"index":0}\n')
            (revised / 'CONTINUATION.json').write_text(json.dumps(dict(original_root=str(original))))
            result = reserve(revised, dict(index=1))
            self.assertEqual(result['global_call'], 2)
            self.assertIn('V2', result['phase_version'])
            self.assertFalse((revised / 'CALL_RESERVATIONS.jsonl').exists())


if __name__ == '__main__':
    unittest.main()
