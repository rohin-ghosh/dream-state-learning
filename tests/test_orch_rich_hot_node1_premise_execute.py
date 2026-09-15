import json
import unittest
from unittest.mock import MagicMock, patch

from gpu import orch_rich_hot_node1_premise_execute as execute


class PremiseExecutionTests(unittest.TestCase):
    def test_census_counts_only_compute_resident_generator_uuids(self):
        response = dict(observed_unix=100, apps=[
            dict(uuid='one', module='gpu.orch_rich_hot_node1_premise_run'),
            dict(uuid='one', module='gpu.orch_rich_hot_node1_premise_run'),
            dict(uuid='two', module='gpu.parent_train')])
        with patch.object(execute, 'remote', return_value=json.dumps(response)) as remote:
            result = execute.census()
        self.assertEqual(result['active_generators'], 4)
        self.assertEqual(result['minimum_during_one_gpu_roll'], 3)
        self.assertEqual(remote.call_count, 4)
        self.assertTrue(all(call.args[1].startswith('sudo -n python3 -c ') for call in remote.call_args_list))

    def test_insufficient_floor_never_starts_boundary(self):
        with patch.object(execute, 'write'), patch.object(execute, 'census', return_value={
                'minimum_during_one_gpu_roll': 15}), patch.object(execute.subprocess, 'Popen') as start:
            with self.assertRaisesRegex(ValueError, 'generation_floor_below_16'):
                execute.execute()
        start.assert_not_called()

    def test_missing_unhinted_slot_never_starts_boundary(self):
        receipt = dict(minimum_during_one_gpu_roll=18, nodes=dict(node1=dict(apps=[])))
        with patch.object(execute, 'write'), patch.object(execute, 'census', return_value=receipt), \
                patch.object(execute.subprocess, 'Popen') as start:
            with self.assertRaisesRegex(ValueError, 'unhinted_or_selected_identity_missing'):
                execute.execute()
        start.assert_not_called()

    def test_only_physical_three_is_rolled_and_launched(self):
        receipt = dict(minimum_during_one_gpu_roll=18, active_generators=19,
            nodes=dict(node1=dict(apps=[dict(uuid=execute.policy.UUIDS[index], root=execute.OLD)
                                      for index in (0, 1, 3)])))
        boundary = MagicMock(pid=123, returncode=0)
        boundary.poll.return_value = 0
        boundary.communicate.return_value = ('{"index": 3}', '')
        with patch.object(execute, 'write'), patch.object(execute, 'census', return_value=receipt), \
                patch.object(execute, 'send_floor'), \
                patch.object(execute.subprocess, 'Popen', return_value=boundary) as start, \
                patch.object(execute, 'remote', return_value='SUBMITTED') as remote:
            execute.execute()
        self.assertEqual(start.call_count, 1)
        self.assertIn('--index 3', start.call_args.args[0][2])
        self.assertIn('premise_boundary', start.call_args.args[0][2])
        self.assertEqual(remote.call_count, 1)
        self.assertIn('premise_run supervise', remote.call_args.args[1])
        self.assertIn('--index 3', remote.call_args.args[1])


if __name__ == '__main__':
    unittest.main()
