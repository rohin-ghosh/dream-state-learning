import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fleet_gpu_controller as controller


class ControllerTests(unittest.TestCase):
    def fixture(self, root):
        life = root / 'lives' / 'example'
        life.mkdir(parents=True)
        plan = root / 'plan.json'
        controller.protocol.write(plan, dict(first_sleep=11, sleep_count=3))
        controller.protocol.write(life / 'REGISTERED.json', dict(plan=controller.protocol.ref(plan)))
        transfers = root / 'receiving_transfers'
        for sleep in (0, 11, 12, 13):
            directory = transfers / f'example_{sleep:06d}'
            directory.mkdir(parents=True)
            controller.protocol.write(directory / 'COMPLETE.json', dict(sleep=sleep))
        return dict(lives=[dict(life_id='example', status='SOURCE_CANDIDATE'),
            dict(life_id='missing', status='MISSING_CUSTODY_NOT_NEGATIVE')])

    def test_fixed_order_and_separate_conditions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pipeline = self.fixture(root)
            with patch.object(controller, 'ROOT', root):
                for physical in (0, 1):
                    rows = controller.candidates(pipeline, physical)
                    self.assertEqual([row['sleep'] for row in rows], [0, 11, 12, 13])
                    self.assertEqual({row['condition'] for row in rows},
                        {controller.evaluator.queue.CONDITIONS[physical]})

    def test_consumed_and_incomplete_cells_not_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pipeline = self.fixture(root)
            operation = root / 'gpu_operation1'
            operation.mkdir()
            key = controller.evaluator.queue.key('example', 11, controller.evaluator.queue.CONDITIONS[0])
            controller.protocol.write(operation / (key + '.ONCE.json'), dict(status='FAILED'))
            (root / 'receiving_transfers' / 'example_000012' / 'COMPLETE.json').unlink()
            with patch.object(controller, 'ROOT', root):
                self.assertEqual([row['sleep'] for row in controller.candidates(pipeline, 0)], [0, 13])

    def test_wall_prevents_any_admission(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            operation_name = getattr(controller, 'OPERATION_NAME', 'gpu_operation1')
            (root / operation_name).mkdir()
            plan = root / 'plan.json'
            controller.protocol.write(plan, dict(hard_end_unix=1789659000))
            runtime = dict(common=dict(pipeline=controller.protocol.ref(plan)))
            with patch.object(controller, 'ROOT', root), patch.object(controller.time, 'time', return_value=1789659000), \
                    patch.object(controller, 'candidates') as candidates:
                controller.slot(runtime, 0)
            candidates.assert_not_called()
            self.assertTrue((root / operation_name / 'PHYSICAL0.WINDOW_END.json').exists())


if __name__ == '__main__':
    unittest.main()
