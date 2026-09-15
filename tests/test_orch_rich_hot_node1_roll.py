import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from gpu import orch_rich_hot_node1_roll as controller


class RollingRecoveryTests(unittest.TestCase):
    def test_floor_deduplicates_route_batches(self):
        node1 = [dict(index=index, ready=True, failed=False) for index in range(8)]
        route = [dict(index=index, ready=True, failed=False) for index in (3, 4, 5)]
        with patch.object(controller, 'query', side_effect=[node1, node1, route + route]):
            observed = controller.floor()
        self.assertEqual(observed['active_generators'], 19)
        self.assertEqual(observed['minimum_during_one_gpu_roll'], 18)

    def test_completed_or_failed_workers_not_counted(self):
        with patch.object(controller, 'query', side_effect=[[], [], [dict(index=3, ready=True, failed=True)]]):
            self.assertEqual(controller.floor()['active_generators'], 0)

    def test_resume_checks_native_and_preserves_old_indices(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'resume'
            with patch.object(controller, 'status', return_value=dict(failed=False, ready=True, progress={'calls': 1})) as status:
                with patch.object(controller, 'floor', return_value=dict(active_generators=16)):
                    with self.assertRaisesRegex(RuntimeError, 'generation_floor'):
                        controller.roll(output, start_index=4)
            self.assertEqual([call.args[0] for call in status.call_args_list], [0, 1, 2, 3])
            self.assertTrue((output / 'FLOOR_BEFORE_4.json').exists())
            self.assertFalse((output / 'BOUNDARY_0.json').exists())
